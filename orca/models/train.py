"""Train M1-M3 from the simulator (fixed seeds), evaluate M1-M4, save metrics.

    .venv/bin/python -m orca.models.train            # ~1-2 min on a laptop CPU
    .venv/bin/python -m orca.models.train --quick    # small sizes, for tests

Outputs: orca/models/metrics.json (committed, the numbers the report quotes) and a model cache
models/orca_models.pkl (gitignored). Splits: train / validation (same ranges, other seeds) /
held-out (HARDER ranges and other seeds, orca/sim/dataset.py RANGES).
"""
from __future__ import annotations

import argparse
import json
import pickle
import time
from pathlib import Path

import numpy as np

from orca.models.features import FEATURES, M2_FEATURES, m2_features, physics_ttf, window_features
from orca.models.m1 import M1
from orca.models.m2 import HORIZON, M2
from orca.models.m3 import ABSTAIN, LABELS, M3
from orca.models import m4
from orca.sim import dataset
from orca.sim.engine import CLASSES

ROOT = Path(__file__).resolve().parents[2]
METRICS = Path(__file__).resolve().parent / "metrics.json"
CACHE = ROOT / "models" / "orca_models.pkl"
SEED = 7
SIZES = {"full": {"train": 1400, "val": 350, "heldout": 700, "m2": 500, "m2_cal": 120, "m2_test": 200},
         "quick": {"train": 210, "val": 70, "heldout": 140, "m2": 80, "m2_cal": 30, "m2_test": 40}}


def build(n: int, split: str, offset: int = 0, stride: int = 1):
    X, y, ep = [], [], []
    for i in range(n):
        sim, site, s = dataset.episode(offset + i, split)
        hist = sim.site_history(site)
        for j in range(10, len(hist), stride):
            if s <= j < s + 2:
                continue        # first two minutes of onset are ambiguous by design
            X.append(window_features(hist, j))
            y.append(CLASSES.index(hist[j]["label"]))
            ep.append(offset + i)
    return np.asarray(X, dtype=float), np.asarray(y), np.asarray(ep)


def build_m2(n: int, split: str, offset: int = 0):
    X, y, base = [], [], []
    for i in range(n):
        hist, ttf = dataset.m2_episode(offset + i, split)
        for j in range(10, len(hist) - 1, 2):
            if ttf[j] is None:
                continue
            X.append(m2_features(hist, j))
            y.append(ttf[j])
            base.append(physics_ttf(hist, j))
    return np.asarray(X, dtype=float), np.asarray(y, dtype=float), np.asarray(base, dtype=float)


def per_class(y_true, y_pred, labels) -> dict:
    out = {}
    for k, name in enumerate(labels):
        tp = int(((y_pred == k) & (y_true == k)).sum())
        fp = int(((y_pred == k) & (y_true != k)).sum())
        fn = int(((y_pred != k) & (y_true == k)).sum())
        out[name] = {"precision": round(tp / (tp + fp), 3) if tp + fp else None,
                     "recall": round(tp / (tp + fn), 3) if tp + fn else None, "support": int((y_true == k).sum())}
    return out


def confusion(y_true, y_pred, n_true, n_pred) -> list[list[int]]:
    m = np.zeros((n_true, n_pred), dtype=int)
    for a, b in zip(y_true, y_pred):
        m[a, b] += 1
    return m.tolist()


def auc(scores, positive) -> float:
    order = np.argsort(scores)
    ranks = np.empty(len(scores))
    ranks[order] = np.arange(1, len(scores) + 1)
    p = positive.sum()
    nn = len(positive) - p
    return float((ranks[positive].sum() - p * (p + 1) / 2) / (p * nn)) if p and nn else float("nan")


def eval_m3(m3: M3, X, y) -> dict:
    idx, conf = m3.predict(X)
    raw = m3.model.predict_proba(X).argmax(1)
    acc_mask = idx != len(CLASSES)
    return {
        "n": int(len(y)),
        "accuracy_no_abstain": round(float((raw == y).mean()), 3),
        "coverage": round(float(acc_mask.mean()), 3),
        "selective_accuracy": round(float((idx[acc_mask] == y[acc_mask]).mean()), 3) if acc_mask.any() else None,
        "abstain_rate": round(float((~acc_mask).mean()), 3),
        "per_class": per_class(y, idx, LABELS[:-1]),
        "confusion_rows_true_cols_pred": {"rows": CLASSES, "cols": LABELS,
                                          "matrix": confusion(y, idx, len(CLASSES), len(LABELS))},
    }


def train(quick: bool = False, save: bool = True) -> tuple[dict, dict]:
    t0 = time.time()
    sz = SIZES["quick" if quick else "full"]
    Xtr, ytr, _ = build(sz["train"], "train", 0)
    Xva, yva, _ = build(sz["val"], "train", 50_000)
    Xho, yho, _ = build(sz["heldout"], "heldout", 0)
    Xin, yin, _ = build(sz["val"], "train", 60_000)           # in-distribution test (same ranges, unseen seeds)
    # abstain calibration: deployment-like (held-out ranges) but disjoint seeds from the held-out test
    Xcal, ycal, _ = build(sz["val"], "heldout", 50_000)

    m1 = M1(SEED).fit(Xtr[ytr == 0], Xva[yva == 0])
    m3 = M3(SEED).fit(Xtr, ytr, Xcal, ycal)

    def m1_eval(X, y):
        s = m1.score(X)
        e = m1.ecod.score(X)
        flag = m1.flag(X)
        f_if = s > m1.threshold
        return {"auc_iforest": round(auc(s, y != 0), 3), "auc_ecod": round(auc(e, y != 0), 3),
                "ensemble_false_alarm_rate_normal": round(float(flag[y == 0].mean()), 4),
                "ensemble_detection_rate_by_class": {c: round(float(flag[y == k].mean()), 3)
                                                     for k, c in enumerate(CLASSES) if k},
                "iforest_only_false_alarm_rate": round(float(f_if[y == 0].mean()), 4),
                "iforest_only_detection_rate": round(float(f_if[y != 0].mean()), 3),
                "ecod_only_false_alarm_rate": round(float((e > m1.ecod_threshold)[y == 0].mean()), 4),
                "ecod_only_detection_rate": round(float((e > m1.ecod_threshold)[y != 0].mean()), 3)}

    X2, y2, _ = build_m2(sz["m2"], "train", 0)
    X2c, y2c, _ = build_m2(sz["m2_cal"], "train", 20_000)
    X2t, y2t, b2t = build_m2(sz["m2_test"], "heldout", 0)
    m2 = M2(SEED).fit(X2, y2, X2c, y2c)
    lo, mid, hi = m2.predict(X2t)
    fail = y2t < HORIZON
    m2m = {"n_test": int(len(y2t)), "n_failing": int(fail.sum()),
           "mae_p50_failing_min": round(float(np.abs(mid[fail] - y2t[fail]).mean()), 2),
           "mae_physics_baseline_failing_min": round(float(np.abs(np.clip(b2t[fail], 0, HORIZON) - y2t[fail]).mean()), 2),
           "interval_p10_p90_coverage": round(float(((y2t >= lo) & (y2t <= hi)).mean()), 3),
           "mean_interval_width_min": round(float((hi - lo).mean()), 1),
           "conformal_widening_min": round(m2.conformal, 2),
           "false_forecast_rate_no_failure": round(float((mid[~fail] < 60).mean()), 4) if (~fail).any() else None,
           "within_30min_recall":round(float(((mid <= 30) & (y2t <= 30)).sum() / max(1, (y2t <= 30).sum())), 3),
           "features": M2_FEATURES, "horizon_min": HORIZON, "test_split": "heldout (harder ranges)"}

    m4m = m4_selftest()
    metrics = {
        "generated_by": "python -m orca.models.train" + (" --quick" if quick else ""),
        "seed": SEED, "data": "synthetic, emulated Chennai network (orca/sim); no real operator data",
        "sizes": {"m3_train_windows": int(len(ytr)), "val": int(len(yva)), "abstain_calibration": int(len(ycal)),
                  "test_in_distribution": int(len(yin)), "heldout_harder": int(len(yho))},
        "M1": {"model": "IsolationForest(200 trees) on normal windows; ECOD (numpy) comparison",
               "threshold": round(m1.threshold, 4), "in_distribution": m1_eval(Xin, yin), "heldout_harder": m1_eval(Xho, yho)},
        "M2_minute": {"model": "LightGBM quantile P10/P50/P90 + split-conformal", **m2m},
        "M3": {"model": "LightGBM multiclass + calibrated abstain + TreeSHAP", "classes": LABELS,
               "abstain_tau": m3.tau, "abstain_margin": m3.margin,
               "in_distribution": eval_m3(m3, Xin, yin), "heldout_harder": eval_m3(m3, Xho, yho)},
        "M4": m4m,
        "features": FEATURES,
        "train_seconds": round(time.time() - t0, 1),
    }
    models = {"m1": m1, "m2": m2, "m3": m3, "features": FEATURES, "quick": quick}
    if save:
        if not quick:
            METRICS.write_text(json.dumps(metrics, indent=2) + "\n")
        CACHE.parent.mkdir(exist_ok=True)
        with (CACHE.with_name("orca_models_quick.pkl") if quick else CACHE).open("wb") as f:
            pickle.dump(models, f)
    return models, metrics


def m4_selftest() -> dict:
    """Storm case: CHN-01 and CHN-05 share a 60 Mbps backup gateway; demand 100 Mbps."""
    demand = {"CHN-01": {"112": 6, "hospital": 14, "payments": 10, "general": 20},
              "CHN-05": {"112": 5, "grid": 8, "payments": 12, "general": 25}}
    cap = {"CHN-01": 45, "CHN-05": 40}
    shared = {"GW-IN-2": {"sites": ["CHN-01", "CHN-05"], "mbps": 60}}
    r = m4.allocate(demand, cap, shared)
    g = m4.greedy(demand, cap, shared)
    served = lambda res, c: all(res["allocation"][s][c]["served"] >= 0.999 for s in res["allocation"] if c in res["allocation"][s])  # noqa: E731
    return {"model": "MILP (SciPy HiGHS) with lexicographic priority; greedy fallback",
            "case": "two sites share a 60 Mbps backup gateway, 100 Mbps demand", "method": r["method"],
            "112_fully_served": served(r, "112"), "hospital_fully_served": served(r, "hospital"),
            "shed": r["shed"], "greedy_shed": g["shed"]}


def load_or_train(quick: bool = False) -> dict:
    path = CACHE.with_name("orca_models_quick.pkl") if quick else CACHE
    if path.exists():
        with path.open("rb") as f:
            return pickle.load(f)
    return train(quick=quick)[0]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args(argv)
    _, m = train(quick=a.quick)
    print(json.dumps({k: m[k] for k in ("sizes", "train_seconds")}, indent=1))
    print("M1 heldout", m["M1"]["heldout_harder"])
    print("M2", {k: v for k, v in m["M2_minute"].items() if k != "features"})
    for split in ("in_distribution", "heldout_harder"):
        e = m["M3"][split]
        print("M3", split, {k: e[k] for k in ("accuracy_no_abstain", "coverage", "selective_accuracy", "abstain_rate")})
        for c, v in e["per_class"].items():
            print(f"   {c:26} P={v['precision']} R={v['recall']} n={v['support']}")
    print("M4", m["M4"])


if __name__ == "__main__":
    main()
