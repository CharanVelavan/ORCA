"""Retrieval test: recall@5 and MRR over kb/vec_eval/questions.yaml.

Gold is one of
  {record: <verified record id>}      hit = that record, or a corpus chunk of the same source whose text holds the record's quote
  {source: <source_id>, page: <n>}    hit = any chunk (either tier) of that source on that page
"""
from __future__ import annotations

import re
import statistics
import time

import yaml

from . import config, ingest
from .retrieve import search

K = 5


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _records() -> dict:
    return {r["id"]: r for r in ingest._records()}


def _is_hit(hit: dict, gold: dict, recs: dict) -> bool:
    if "record" in gold:
        if hit["chunk_id"] == gold["record"]:
            return True
        r = recs[gold["record"]]
        q = _norm(r.get("quote") or "")[:80]
        return bool(q) and hit["source_id"] == r["source"] and q in _norm(hit["text"])
    return hit["source_id"] == gold["source"] and int(hit["page"]) == int(gold["page"])


def run(rerank: bool = True, filters_on: bool = True, tier: str | None = None, dedupe: bool = True) -> dict:
    qs = yaml.safe_load(config.eval_file().read_text())
    recs = _records()
    rows = []
    for q in qs:
        f = dict(q.get("filters") or {}) if filters_on else {}
        if tier:
            f["tier"] = tier            # tier=corpus: raw document chunks only, the hard test
        hits = search(q["question"], k=K, filters=f or None, rerank=rerank, cache=False, dedupe=dedupe)
        rank = next((n + 1 for n, h in enumerate(hits) if _is_hit(h, q["gold"], recs)), None)
        rows.append({"id": q["id"], "question": q["question"], "gold": q["gold"], "rank": rank,
                     "top1": hits[0]["chunk_id"] if hits else None})
    n = len(rows)
    return {"rows": rows, "n": n, "recall@5": sum(1 for r in rows if r["rank"]) / n,
            "mrr": sum(1 / r["rank"] for r in rows if r["rank"]) / n,
            "settings": {"rerank": rerank, "tier": tier or "both", "dedupe": dedupe}}


def table(res: dict) -> str:
    out = [f"{'id':<5} {'rank':<5} {'gold':<34} question"]
    for r in res["rows"]:
        g = r["gold"].get("record") or f"{r['gold']['source']} p{r['gold']['page']}"
        out.append(f"{r['id']:<5} {str(r['rank'] or '-'):<5} {g:<34} {r['question'][:70]}")
    out.append(f"\nquestions={res['n']}  recall@5={res['recall@5']:.3f}  MRR={res['mrr']:.3f}")
    return "\n".join(out)


def tune_abstention(dev_rows: list[dict]) -> float:
    """Choose a score cut only on dev examples, maximizing negative/positive accuracy."""
    scores = sorted({float(r["best_score"]) for r in dev_rows if r["best_score"] != float("-inf")})
    if not scores:
        return 0.0
    choices = [scores[0] - 1e-6] + [(a + b) / 2 for a, b in zip(scores, scores[1:])] + [scores[-1] + 1e-6]
    return max(choices, key=lambda t: sum((r["best_score"] < t) == (r["kind"] == "negative") for r in dev_rows))


def run_v2(rerank: bool = True, tier: str = "corpus", threshold: float | None = None) -> dict:
    """Evaluate v2 without leaking test labels into threshold selection."""
    qs, recs = yaml.safe_load(config.eval_v2_file().read_text()), _records()
    rows = []
    for q in qs:
        t0 = time.perf_counter()
        hits = search(q["question"], k=10, filters={"tier": tier}, rerank=rerank, cache=False)
        rank = next((i + 1 for i, h in enumerate(hits) if q.get("gold") and _is_hit(h, q["gold"], recs)), None)
        rows.append({"id": q["id"], "split": q["split"], "kind": q["kind"], "rank": rank,
                     "best_score": hits[0]["score"] if hits else float("-inf"),
                     "latency_ms": (time.perf_counter() - t0) * 1000})
    threshold = tune_abstention([r for r in rows if r["split"] == "dev"]) if threshold is None else threshold
    test, pos = [r for r in rows if r["split"] == "test"], []
    pos = [r for r in test if r["kind"] != "negative"]
    neg = [r for r in test if r["kind"] == "negative"]
    at = lambda kind: [r for r in test if r["kind"] == kind]
    return {"rows": rows, "threshold": threshold, "test_n": len(test),
            "recall@5": sum(bool(r["rank"] and r["rank"] <= 5) for r in pos) / len(pos) if pos else 0,
            "mrr@10": sum(1 / r["rank"] for r in pos if r["rank"] and r["rank"] <= 10) / len(pos) if pos else 0,
            "ndcg@10": sum(1 / __import__("math").log2(r["rank"] + 1) for r in pos if r["rank"] and r["rank"] <= 10) / len(pos) if pos else 0,
            "negative_accuracy": sum(r["best_score"] < threshold for r in neg) / len(neg) if neg else 0,
            "amendment_hit_rate": sum(bool(r["rank"]) for r in at("amendment")) / max(1, len(at("amendment"))),
            "exact_citation_hit@1": sum(r["rank"] == 1 for r in at("exact_citation")) / max(1, len(at("exact_citation"))),
            "p50_latency_ms": statistics.median(r["latency_ms"] for r in test),
            "p95_latency_ms": sorted(r["latency_ms"] for r in test)[max(0, int(.95 * len(test)) - 1)]}
