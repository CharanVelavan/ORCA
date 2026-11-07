"""M2 daily tier: which radio links are at risk of a radio-link failure in the next days? (REAL data)

Data: ITU AI/ML Challenge Turkcell radio-link-failure set, ``rl-kpis.tsv`` (daily KPIs per link,
label ``rlf``). Not in the repo (data/raw/ is gitignored); point ORCA_TURKCELL_DIR at the folder that
holds rl-kpis.tsv, or place it under data/raw/turkcell/.

Task: from one link-day's KPIs (and the change from the previous day), predict whether the link has
an RLF within the next ``H`` days. Time split (no leakage): train before 2020-06-01, test from it.
LightGBM classifier; we report ROC-AUC, PR-AUC and the base rate. Turkey microwave links, so this
calibrates fault behaviour only; it is not Chennai data and not satellite data.

    ORCA_TURKCELL_DIR=/path/to/regionA .venv/bin/python -m orca.models.m2_daily
"""
from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "metrics_daily.json"
NUM = ["severaly_error_second", "error_second", "unavail_second", "avail_time", "bbe", "rxlevmax", "capacity"]
H = 3
SPLIT = "2020-06-01"


def find_file() -> Path | None:
    cands = []
    if os.environ.get("ORCA_TURKCELL_DIR"):
        cands.append(Path(os.environ["ORCA_TURKCELL_DIR"]) / "rl-kpis.tsv")
    cands += list((ROOT / "data" / "raw" / "turkcell").rglob("rl-kpis.tsv")) if (ROOT / "data" / "raw" / "turkcell").exists() else []
    return next((p for p in cands if p.exists()), None)


def load(path: Path):
    links = defaultdict(list)
    with path.open() as f:
        r = csv.reader(f, delimiter="\t")
        head = next(r)
        ix = {k: head.index(k) for k in NUM + ["datetime", "mlid", "site_id", "rlf", "freq_band", "modulation"]}
        for row in r:
            try:
                vals = [float(row[ix[k]]) if row[ix[k]] not in ("", "nan") else np.nan for k in NUM]
            except ValueError:
                continue
            links[(row[ix["site_id"]], row[ix["mlid"]])].append(
                (row[ix["datetime"]], vals, row[ix["rlf"]] == "True", row[ix["freq_band"]]))
    return links


def build(links):
    X, y, day = [], [], []
    bands = ["f1", "f2", "f3", "f4", "f5"]
    for rows in links.values():
        rows.sort()
        rlf = [r[2] for r in rows]
        for i, (d, v, _, band) in enumerate(rows):
            if i + H >= len(rows):
                break
            prev = rows[i - 1][1] if i else v
            X.append(v + [a - b for a, b in zip(v, prev)] + [float(band == b) for b in bands])
            y.append(any(rlf[i + 1: i + 1 + H]))
            day.append(d)
    return np.asarray(X, dtype=float), np.asarray(y), np.asarray(day)


def run() -> dict:
    p = find_file()
    if p is None:
        return {"status": "skipped", "reason": "rl-kpis.tsv not found (set ORCA_TURKCELL_DIR)"}
    import lightgbm as lgb
    from sklearn.metrics import average_precision_score, roc_auc_score
    X, y, day = build(load(p))
    tr, te = day < SPLIT, day >= SPLIT
    clf = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50,
                             scale_pos_weight=float((~y[tr]).sum() / max(1, y[tr].sum())) ** 0.5,
                             random_state=7, deterministic=True, force_row_wise=True, verbose=-1)
    clf.fit(X[tr], y[tr])
    s = clf.predict_proba(X[te])[:, 1]
    top = np.argsort(-s)[: max(1, int(0.01 * len(s)))]
    out = {"status": "ok", "data": "Turkcell rl-kpis.tsv (real, daily, Turkey microwave links)",
           "task": f"RLF within the next {H} days from one link-day", "split": f"time: train < {SPLIT} <= test",
           "n_train": int(tr.sum()), "n_test": int(te.sum()), "base_rate_test": round(float(y[te].mean()), 5),
           "roc_auc": round(float(roc_auc_score(y[te], s)), 3), "pr_auc": round(float(average_precision_score(y[te], s)), 4),
           "precision_top_1pct": round(float(y[te][top].mean()), 4)}
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
