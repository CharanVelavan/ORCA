"""Link physics for the emulated network (stdlib only).

- Rain specific attenuation: ITU-R P.838-3, gamma_R = k * R**alpha, coefficients read from
  data/itu_p838_3_coefficients.csv (extracted from the official PDF, never hand-typed). Frequencies
  between table rows: log-f / log-k interpolation, alpha linear in log-f (P.838-3 text).
  Polarisation and elevation combine kH/kV per P.838-3 eqs. (4)-(5).
- Satellite slant path: SIMPLIFIED P.618 (slant length below the rain height times the horizontal
  reduction factor r0.01; the vertical adjustment and time-percentage scaling are omitted).
- Terrestrial microwave: SIMPLIFIED older P.530 distance factor r = 1 / (1 + d / d0),
  d0 = 35 exp(-0.015 R).
- Jamming: SINR = S / (N + J), i.e. a rise in the noise floor with steady received power.
These are emulation models, labelled as simplified in docs/NETWORK.md.
"""
from __future__ import annotations

import csv
import math
from functools import lru_cache
from pathlib import Path

P838_CSV = Path(__file__).resolve().parents[2] / "data" / "itu_p838_3_coefficients.csv"
RAIN_HEIGHT_KM = 5.0      # ASSUMED effective rain height for Chennai (P.839 h0 + 0.36 km, rounded)
STATION_ALT_KM = 0.01


@lru_cache(maxsize=1)
def p838_table() -> list[tuple[float, float, float, float, float]]:
    rows = []
    with P838_CSV.open() as f:
        for line in f:
            if line.startswith("#") or line.startswith("freq"):
                continue
            r = next(csv.reader([line]))
            rows.append(tuple(float(x) for x in r[:5]))
    rows.sort()
    return rows


def p838_coefficients(f_ghz: float) -> tuple[float, float, float, float]:
    """(kH, alphaH, kV, alphaV) at f_ghz, interpolated per P.838-3."""
    t = p838_table()
    if f_ghz <= t[0][0]:
        return t[0][1:]
    if f_ghz >= t[-1][0]:
        return t[-1][1:]
    for row in t:
        if row[0] == f_ghz:
            return row[1:]
    for lo, hi in zip(t, t[1:]):
        if lo[0] <= f_ghz <= hi[0]:
            if f_ghz == lo[0]:
                return lo[1:]
            w = (math.log10(f_ghz) - math.log10(lo[0])) / (math.log10(hi[0]) - math.log10(lo[0]))
            k = lambda a, b: 10 ** (math.log10(a) + w * (math.log10(b) - math.log10(a)))  # noqa: E731
            lin = lambda a, b: a + w * (b - a)  # noqa: E731
            return k(lo[1], hi[1]), lin(lo[2], hi[2]), k(lo[3], hi[3]), lin(lo[4], hi[4])
    raise ValueError(f_ghz)


def k_alpha(f_ghz: float, elevation_deg: float = 0.0, tilt_deg: float = 45.0) -> tuple[float, float]:
    """Combined k, alpha (P.838-3 eqs. 4-5). tilt 45 deg = circular polarisation, 90 = vertical."""
    kh, ah, kv, av = p838_coefficients(f_ghz)
    c = math.cos(math.radians(elevation_deg)) ** 2 * math.cos(math.radians(2 * tilt_deg))
    k = (kh + kv + (kh - kv) * c) / 2
    a = (kh * ah + kv * av + (kh * ah - kv * av) * c) / (2 * k)
    return k, a


def specific_attenuation(f_ghz: float, rain_mm_h: float, elevation_deg: float = 0.0, tilt_deg: float = 45.0) -> float:
    """gamma_R in dB/km."""
    if rain_mm_h <= 0:
        return 0.0
    k, a = k_alpha(f_ghz, elevation_deg, tilt_deg)
    return k * rain_mm_h ** a


def slant_rain_fade_db(f_ghz: float, rain_mm_h: float, elevation_deg: float) -> float:
    """Simplified P.618 rain fade on an Earth-space path (dB)."""
    if rain_mm_h <= 0:
        return 0.0
    el = math.radians(elevation_deg)
    ls = (RAIN_HEIGHT_KM - STATION_ALT_KM) / math.sin(el)
    lg = ls * math.cos(el)
    g = specific_attenuation(f_ghz, rain_mm_h, elevation_deg, 45.0)
    r = 1.0 / (1 + 0.78 * math.sqrt(lg * g / f_ghz) - 0.38 * (1 - math.exp(-2 * lg)))
    return g * ls * min(r, 1.0)


def terrestrial_rain_fade_db(f_ghz: float, rain_mm_h: float, path_km: float) -> float:
    """Simplified P.530 rain fade on a horizontal microwave hop (dB), vertical polarisation."""
    if rain_mm_h <= 0:
        return 0.0
    d0 = 35 * math.exp(-0.015 * min(rain_mm_h, 100.0))
    return specific_attenuation(f_ghz, rain_mm_h, 0.0, 90.0) * path_km / (1 + path_km / d0)


def rain_fade_db(link: dict, rain_mm_h: float) -> float:
    if link.get("freq_GHz") is None:
        return 0.0      # fibre: no rain fade (floods cut fibre instead)
    if "elevation_deg" in link:
        return slant_rain_fade_db(link["freq_GHz"], rain_mm_h, link["elevation_deg"])
    return terrestrial_rain_fade_db(link["freq_GHz"], rain_mm_h, link.get("path_km", 5.0))


def sinr_db(snr_db: float, j_over_n_db: float) -> float:
    """SINR with a jammer J/N dB above the thermal noise: S/(N+J)."""
    if j_over_n_db is None or j_over_n_db <= -50:
        return snr_db
    return snr_db - 10 * math.log10(1 + 10 ** (j_over_n_db / 10))


def capacity_fraction(sinr: float, req_db: float) -> float:
    """Usable fraction of nominal capacity: 0 below the modcod floor, Shannon-like above it (ASSUMED)."""
    if sinr < req_db:
        return 0.0
    full = math.log2(1 + 10 ** ((req_db + 10) / 10))
    return max(0.0, min(1.0, math.log2(1 + 10 ** (sinr / 10)) / full))
