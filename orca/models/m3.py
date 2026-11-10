"""M3: fault or attack, and which kind? LightGBM multiclass + calibrated abstain + SHAP explanations.

Classes (8 outputs): the 7 trained classes plus ``abstain`` when the model is unsure: top
probability below ``tau`` or top-2 margin below ``margin``, both chosen on a validation split so
that accepted predictions reach the target precision. Explanations use LightGBM's native TreeSHAP
(``pred_contrib=True``): per-feature contributions to the predicted class, in plain words.
A wrong call starts or misses the CERT-In/DoT 6-hour clocks, so abstaining beats guessing.
"""
from __future__ import annotations

import numpy as np
import lightgbm as lgb

from orca.models.features import FEATURES, PLAIN
from orca.sim.engine import CLASSES

ABSTAIN = "abstain"
LABELS = CLASSES + [ABSTAIN]


class M3:
    def __init__(self, seed: int = 7):
        self.seed = seed
        self.tau = 0.6
        self.margin = 0.2

    def fit(self, X: np.ndarray, y: np.ndarray, X_val: np.ndarray, y_val: np.ndarray, target_precision: float = 0.99):
        self.model = lgb.LGBMClassifier(n_estimators=200, learning_rate=0.05, num_leaves=31, min_child_samples=20,
                                        subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                                        random_state=self.seed, deterministic=True, force_row_wise=True,
                                        verbose=-1)
        self.model.fit(X, y)
        self._calibrate(X_val, y_val, target_precision)
        return self

    def _calibrate(self, X_val, y_val, target):
        P = self.model.predict_proba(X_val)
        top = P.max(1)
        srt = np.sort(P, 1)
        mar = srt[:, -1] - srt[:, -2]
        pred = P.argmax(1)
        grid = []
        for tau in (0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.97, 0.99, 0.995):
            for m in (0.0, 0.1, 0.2, 0.3, 0.5):
                acc = (top >= tau) & (mar >= m)
                if acc.sum() < 0.5 * len(acc):
                    continue
                grid.append((float((pred[acc] == y_val[acc]).mean()), float(acc.mean()), tau, m))
        ok = [g for g in grid if g[0] >= target]
        # highest coverage that meets the target precision; else the most precise setting
        best = max(ok, key=lambda g: (g[1], g[0])) if ok else max(grid, key=lambda g: (g[0], g[1]))
        self.calibration = {"target_precision": target, "precision": round(best[0], 4), "coverage": round(best[1], 4)}
        self.tau, self.margin = float(best[2]), float(best[3])

    def predict(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Returns (label index into LABELS, confidence). Abstain index = len(CLASSES)."""
        P = self.model.predict_proba(X, num_threads=1)
        srt = np.sort(P, 1)
        top, mar = srt[:, -1], srt[:, -1] - srt[:, -2]
        idx = P.argmax(1)
        idx = np.where((top >= self.tau) & (mar >= self.margin), idx, len(CLASSES))
        return idx, top

    def classify(self, x) -> dict:
        x = np.asarray(x, dtype=float).reshape(1, -1)
        P = self.model.predict_proba(x, num_threads=1)[0]
        top_cls = int(P.argmax())
        conf = float(P[top_cls])
        ranked = np.sort(P)
        label = CLASSES[top_cls] if conf >= self.tau and ranked[-1] - ranked[-2] >= self.margin else ABSTAIN
        return {"label": label, "confidence": round(conf, 3),
                "probabilities": {c: round(float(p), 3) for c, p in zip(CLASSES, P)},
                "abstained": label == ABSTAIN,
                "why": self.explain(x[0], top_cls),
                "note": (f"top probability {conf:.2f} or margin below the abstain threshold "
                         f"(tau {self.tau:.2f}, margin {self.margin:.2f}); a human decides") if label == ABSTAIN else ""}

    def explain(self, x, cls_idx: int, k: int = 4) -> list[dict]:
        contrib = self.model.booster_.predict(np.asarray(x, dtype=float).reshape(1, -1), pred_contrib=True, num_threads=1)[0]
        nf = len(FEATURES)
        c = np.asarray(contrib).reshape(len(CLASSES), nf + 1)[cls_idx][:nf]
        idx = np.argsort(-np.abs(c))[:k]
        return [{"feature": FEATURES[i], "plain": PLAIN.get(FEATURES[i], FEATURES[i]),
                 "value": round(float(x[i]), 3), "contribution": round(float(c[i]), 3),
                 "towards": CLASSES[cls_idx] if c[i] > 0 else f"away from {CLASSES[cls_idx]}"} for i in idx]
