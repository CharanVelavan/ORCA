"""M1: is anything unusual happening? Isolation Forest on window features (unsupervised), ECOD as comparison.

Trained on NORMAL windows only (including benign surges), so it can flag attacks M3 never saw.
It never acts alone: it only triggers M3 and the agents. Flag = Isolation Forest OR ECOD, each
above the 99.75th percentile of its normal validation scores (about 0.5 % false alarms per
site-minute in distribution).
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest

from orca.models.features import FEATURES, PLAIN


class ECOD:
    """Empirical-CDF outlier detection (Li et al. 2022), numpy only: sum of -log tail probabilities."""

    def fit(self, X: np.ndarray) -> "ECOD":
        self.sorted = np.sort(X, axis=0)
        self.n = X.shape[0]
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        out = np.zeros(X.shape[0])
        for j in range(X.shape[1]):
            col = self.sorted[:, j]
            left = (np.searchsorted(col, X[:, j], side="right") + 1) / (self.n + 2)
            right = (self.n - np.searchsorted(col, X[:, j], side="left") + 1) / (self.n + 2)
            out += np.maximum(-np.log(left), -np.log(right))
        return out


class M1:
    def __init__(self, seed: int = 7):
        self.seed = seed

    def fit(self, X_normal: np.ndarray, X_val_normal: np.ndarray) -> "M1":
        self.mu = X_normal.mean(axis=0)
        self.sd = X_normal.std(axis=0) + 1e-6
        self.iforest = IsolationForest(n_estimators=200, random_state=self.seed, contamination="auto").fit(X_normal)
        self.ecod = ECOD().fit(X_normal)
        self.threshold = float(np.quantile(self.score(X_val_normal), 0.9975))
        self.ecod_threshold = float(np.quantile(self.ecod.score(X_val_normal), 0.9975))
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        """Isolation Forest score; higher = more anomalous."""
        return -self.iforest.score_samples(X)

    def flag(self, X: np.ndarray) -> np.ndarray:
        """Ensemble: Isolation Forest OR ECOD above its own 99.75th-percentile threshold (~0.5 % false alarms).

        ECOD is kept in the flag because a feature that is constant in normal data (mains power,
        wipe commands) cannot be split by the forest, while its empirical tail probability is extreme."""
        return (self.score(X) > self.threshold) | (self.ecod.score(X) > self.ecod_threshold)

    def explain(self, x: np.ndarray, k: int = 3) -> list[dict]:
        """Top features by distance from normal (z-score), in plain words."""
        z = (np.asarray(x) - self.mu) / self.sd
        idx = np.argsort(-np.abs(z))[:k]
        return [{"feature": FEATURES[i], "plain": PLAIN.get(FEATURES[i], FEATURES[i]),
                 "value": round(float(x[i]), 3), "z": round(float(z[i]), 1)} for i in idx]
