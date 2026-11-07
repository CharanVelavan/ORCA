"""Online detector: turns a site's minute history into M1/M3/M2 alerts with explanations.

Used by ``orca.sim.scenario.ScenarioRun(detector=Detector.load())``. Alerts are emitted on change
only (rising edge of M1, a new M3 label, an M2 countdown entering 60 minutes), so agents are not
flooded. M1 anomaly + M3 "normal" (not confident) becomes ``abstain``: unusual, but not a known
pattern, so a human decides.
"""
from __future__ import annotations

import numpy as np

from orca.models.features import window_features
from orca.models.m3 import ABSTAIN

QUIET = 10      # minutes without the condition before the same alert can be raised again


class Detector:
    def __init__(self, models: dict):
        self.m1, self.m2, self.m3 = models["m1"], models["m2"], models["m3"]
        self.state: dict[str, dict] = {}

    @classmethod
    def load(cls, quick: bool = False) -> "Detector":
        from orca.models.train import load_or_train
        return cls(load_or_train(quick=quick))

    def assess(self, hist: list[dict], site: str) -> dict:
        """Everything the models say about the latest minute (no change detection)."""
        x = np.asarray(window_features(hist), dtype=float)
        flag = bool(self.m1.flag(x.reshape(1, -1))[0])
        score = float(self.m1.score(x.reshape(1, -1))[0])
        m3 = self.m3.classify(x)
        if flag and m3["label"] == "normal" and m3["confidence"] < 0.99:
            m3 = {**m3, "label": ABSTAIN, "abstained": True,
                  "note": "M1 sees an anomaly that M3 does not recognise; a human decides"}
        return {"m1": {"anomalous": flag, "score": round(score, 4), "threshold": round(self.m1.threshold, 4),
                       "why": self.m1.explain(x)},
                "m3": m3, "m2": self.m2.forecast(hist, site)}

    def observe(self, hist: list[dict], site: str) -> list[dict]:
        if len(hist) < 3:
            return []
        st = self.state.setdefault(site, {"m1": False, "m1_clear": 0, "m3": "normal", "m2": False, "m2_clear": 0})
        a = self.assess(hist, site)
        out = []
        anom = a["m1"]["anomalous"]
        if anom and not st["m1"]:
            out.append({"source": "M1", "label": "anomaly",
                        "detail": f"M1 anomaly at {site}: " + ", ".join(w["plain"] for w in a["m1"]["why"]),
                        "explain": a["m1"]})
            st["m1"] = True
        st["m1_clear"] = 0 if anom else st["m1_clear"] + 1
        if st["m1_clear"] >= QUIET:             # hysteresis: QUIET minutes before M1 can alert again
            st["m1"] = False
        lab = a["m3"]["label"]
        if lab != st["m3"] and (lab != "normal" or st["m1_clear"] >= QUIET):
            if lab != "normal":                 # "back to normal" is not pushed to agents
                out.append({"source": "M3", "label": lab,
                            "detail": f"M3 {lab} at {site} (confidence {a['m3']['confidence']}): "
                                      + ", ".join(f"{w['plain']}={w['value']}" for w in a["m3"]["why"][:3]),
                            "explain": a["m3"]})
            st["m3"] = lab
        p50 = a["m2"]["minutes_to_failure"]["p50"]
        w = a["m2"]["why"]
        evidence = (not w["mains_power"]) or w["margin_slope_db_per_min"] < -0.05 or w["rain_mm_h"] > 1 \
            or w["link_margin_db"] < 3
        soon = p50 < 60 and evidence
        if soon and not st["m2"]:
            out.append({"source": "M2", "label": "forecast",
                        "detail": f"M2: {site} {a['m2']['cause']} fails in ~{p50:.0f} min "
                                  f"(P10 {a['m2']['minutes_to_failure']['p10']:.0f}, P90 {a['m2']['minutes_to_failure']['p90']:.0f}); "
                                  f"exposure {a['m2']['exposure']}; pre-emptive {a['m2']['recommended']}",
                        "explain": a["m2"]})
        if soon:
            st["m2"], st["m2_clear"] = True, 0
        else:
            st["m2_clear"] += 1
            if st["m2_clear"] >= QUIET:
                st["m2"] = False
        return out
