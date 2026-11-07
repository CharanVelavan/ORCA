"""Window features over a site's minute history (last 10 minutes), shared by M1, M3 and the detector."""
from __future__ import annotations

from orca.sim.topology import LINK_CLASSES

W = 10
FEATURES = [
    "snr_db", "snr_slope5", "rx_delta_db", "noise_rise_db", "fade_residual_db", "rain_mm_h", "expected_fade_db",
    "packet_loss", "loss_mean10", "txn_success", "traffic_load", "mains_power", "battery_pct", "battery_slope5",
    "terminals_frac", "logins10", "anomalous_logins10", "failed_logins10", "cmds10", "wipe10", "cfg10",
    "telemetry_edit10", "telemetry_mismatch", "gnss_cn0_mean", "gnss_cn0_std", "gnss_agc_db",
    "gnss_clock_abs_ns", "gnss_pos_jump_m", "ss7_msg_ratio", "ss7_loc_query_rate", "ss7_loc_share",
    "ss7_foreign_share", "ss7_error_rate", "is_satellite", "is_microwave", "is_fibre",
]
# plain-language names for explanations
PLAIN = {
    "noise_rise_db": "noise floor rise", "fade_residual_db": "signal loss the weather does not explain",
    "rain_mm_h": "rain rate", "expected_fade_db": "rain fade expected from ITU-R P.838",
    "rx_delta_db": "received level change", "anomalous_logins10": "anomalous VPN logins",
    "wipe10": "wipe commands", "cfg10": "configuration changes", "telemetry_mismatch": "reported vs measured mismatch",
    "telemetry_edit10": "telemetry edits", "gnss_cn0_std": "GNSS C/N0 spread", "gnss_agc_db": "GNSS AGC level",
    "gnss_pos_jump_m": "GNSS position jump", "gnss_clock_abs_ns": "GNSS clock offset",
    "ss7_loc_query_rate": "location queries per minute", "ss7_loc_share": "location query share",
    "ss7_foreign_share": "signalling from foreign/unknown sources", "mains_power": "mains power",
    "battery_pct": "battery level", "battery_slope5": "battery trend", "terminals_frac": "terminals online",
    "packet_loss": "packet loss", "snr_db": "SNR", "snr_slope5": "SNR trend", "ss7_msg_ratio": "signalling volume",
}


def window_features(hist: list[dict], i: int | None = None) -> list[float]:
    if i is None:
        i = len(hist) - 1
    h = hist[i]
    win = hist[max(0, i - W + 1): i + 1]
    back5 = hist[max(0, i - 5)]
    link = LINK_CLASSES.get(h["path_kind"], LINK_CLASSES["satellite"])
    s = lambda k: float(sum(x[k] for x in win))  # noqa: E731
    msg = max(h["ss7_msg_rate"], 1e-6)
    return [
        h["snr_db"], h["snr_db"] - back5["snr_db"], h["rx_dbm"] - link["rx_dbm"], h["noise_rise_db"],
        h["fade_residual_db"], h["rain_mm_h"], h["expected_fade_db"],
        h["packet_loss"], s("packet_loss") / len(win), h["txn_success"], h["traffic_load"], h["mains_power"],
        h["battery_pct"], (h["battery_pct"] - back5["battery_pct"]) / max(1, i - max(0, i - 5)),
        h["terminals_up"] / 4.0, s("mgmt_logins"), s("mgmt_login_anomalous"), s("mgmt_failed_logins"),
        s("mgmt_cmds"), s("mgmt_wipe"), s("mgmt_cfg_change"), s("mgmt_telemetry_edit"),
        max(x["telemetry_mismatch"] for x in win), h["gnss_cn0_mean"], h["gnss_cn0_std"], h["gnss_agc_db"],
        abs(h["gnss_clock_offset_ns"]), max(x["gnss_pos_jump_m"] for x in win), h["ss7_msg_rate"] / 200.0,
        h["ss7_loc_query_rate"], h["ss7_loc_query_rate"] / msg, h["ss7_foreign_share"], h["ss7_error_rate"],
        float(h["path_kind"] == "satellite"), float(h["path_kind"] == "microwave"), float(h["path_kind"] == "fibre"),
    ]


M2_BASE = ["link_margin_db", "margin_slope5", "margin_slope10", "rain_mm_h", "rain_slope5", "expected_fade_db",
           "battery_pct", "battery_slope5", "mains_power", "battery_saving", "is_satellite", "is_microwave"]
M2_FEATURES = M2_BASE + ["physics_ttf_min"]     # hybrid: the physics estimate is an input to the ML model


def _m2_base(hist: list[dict], i: int) -> list[float]:
    h, b5, b10 = hist[i], hist[max(0, i - 5)], hist[max(0, i - 10)]
    d5, d10 = max(1, i - max(0, i - 5)), max(1, i - max(0, i - 10))
    return [h["link_margin_db"], (h["link_margin_db"] - b5["link_margin_db"]) / d5,
            (h["link_margin_db"] - b10["link_margin_db"]) / d10, h["rain_mm_h"],
            (h["rain_mm_h"] - b5["rain_mm_h"]) / d5, h["expected_fade_db"], h["battery_pct"],
            (h["battery_pct"] - b5["battery_pct"]) / d5, h["mains_power"], h["battery_saving"],
            float(h["path_kind"] == "satellite"), float(h["path_kind"] == "microwave")]


def _physics(f: dict, horizon: int = 120) -> float:
    if f["link_margin_db"] < 0 or f["battery_pct"] <= 5:
        return 0.0
    cands = [horizon]
    if f["margin_slope5"] < -1e-3:
        cands.append(f["link_margin_db"] / -f["margin_slope5"])
    if not f["mains_power"] and f["battery_slope5"] < -1e-3:
        cands.append((f["battery_pct"] - 5) / -f["battery_slope5"])
    return float(min(min(cands), horizon))


def m2_features(hist: list[dict], i: int | None = None) -> list[float]:
    if i is None:
        i = len(hist) - 1
    base = _m2_base(hist, i)
    return base + [_physics(dict(zip(M2_BASE, base)))]


def physics_ttf(hist: list[dict], i: int | None = None, horizon: int = 120) -> float:
    """Physics/trend baseline: minutes until margin < 0 or battery <= 5 % at the current slope."""
    if i is None:
        i = len(hist) - 1
    return _physics(dict(zip(M2_BASE, _m2_base(hist, i))), horizon)
