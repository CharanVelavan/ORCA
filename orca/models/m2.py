"""M2: how many minutes until this link or site fails, and who goes blind?

Minute tier: LightGBM quantile regression (P10/P50/P90) of minutes-to-failure (link margin < 0 dB
or battery at the 5 % cut-off), horizon 120 min, trained on synthetic simulator episodes (rain
approaching a radio link; mains failure). Split-conformal calibration (CQR) widens the interval to
reach 80 % coverage on a calibration split. A physics/trend baseline (current margin or battery
divided by its slope) is reported next to it. The output names the exposure (dependants of the site)
and the pre-emptive playbook: PB-16 pre-stage a clean backup path (link), PB-15 battery-saving +
PB-10 warn dependants (power).
"""
from __future__ import annotations

import numpy as np
import lightgbm as lgb

from orca.models.features import M2_FEATURES, m2_features, physics_ttf
from orca.sim.topology import SITES

HORIZON = 120


class M2:
    def __init__(self, seed: int = 7):
        self.seed = seed
        self.q = {}
        self.conformal = 0.0

    PHYS = M2_FEATURES.index("physics_ttf_min")

    def fit(self, X, y, X_cal, y_cal):
        """Quantiles of the residual (true - physics), so the physics estimate carries extrapolation."""
        r = y - X[:, self.PHYS]
        for a in (0.1, 0.5, 0.9):
            self.q[a] = lgb.LGBMRegressor(objective="quantile", alpha=a, n_estimators=200, learning_rate=0.05,
                                          num_leaves=15, min_child_samples=40, random_state=self.seed,
                                          deterministic=True, force_row_wise=True, verbose=-1).fit(X, r)
        lo, _, hi = self._raw(X_cal)
        scores = np.maximum(lo - y_cal, y_cal - hi)
        n = len(scores)
        self.conformal = max(0.0, float(np.quantile(scores, min(1.0, np.ceil((n + 1) * 0.8) / n))))
        return self

    def _raw(self, X):
        base = X[:, self.PHYS]
        return tuple(base + self.q[a].predict(X) for a in (0.1, 0.5, 0.9))

    def predict(self, X) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        lo, mid, hi = self._raw(X)
        lo, hi = lo - self.conformal, hi + self.conformal
        clip = lambda a: np.clip(a, 0, HORIZON)  # noqa: E731
        return clip(lo), clip(mid), clip(np.maximum(hi, mid))

    def forecast(self, hist: list[dict], site: str) -> dict:
        x = np.asarray([m2_features(hist)], dtype=float)
        lo, mid, hi = (float(v[0]) for v in self.predict(x))
        f = dict(zip(M2_FEATURES, x[0]))
        cause = "power" if not f["mains_power"] else "link"
        pb = ["PB-15", "PB-10"] if cause == "power" else ["PB-16", "PB-06"]
        return {"site": site, "minutes_to_failure": {"p10": round(lo, 1), "p50": round(mid, 1), "p90": round(hi, 1)},
                "physics_baseline_min": round(physics_ttf(hist), 1), "cause": cause,
                "exposure": SITES.get(site, {}).get("dependants", []), "recommended": pb,
                "horizon_min": HORIZON,
                "why": {"link_margin_db": round(f["link_margin_db"], 2), "margin_slope_db_per_min": round(f["margin_slope5"], 3),
                        "rain_mm_h": round(f["rain_mm_h"], 1), "battery_pct": round(f["battery_pct"], 1),
                        "battery_slope_pct_per_min": round(f["battery_slope5"], 3), "mains_power": int(f["mains_power"])}}
