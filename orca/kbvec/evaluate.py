"""Retrieval test: recall@5 and MRR over kb/vec_eval/questions.yaml.

Gold is one of
  {record: <verified record id>}      hit = that record, or a corpus chunk of the same source whose text holds the record's quote
  {source: <source_id>, page: <n>}    hit = any chunk (either tier) of that source on that page
"""
from __future__ import annotations

import re

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


def run(rerank: bool = True, filters_on: bool = True, tier: str | None = None) -> dict:
    qs = yaml.safe_load(config.eval_file().read_text())
    recs = _records()
    rows = []
    for q in qs:
        f = dict(q.get("filters") or {}) if filters_on else {}
        if tier:
            f["tier"] = tier            # tier=corpus: raw document chunks only, the hard test
        hits = search(q["question"], k=K, filters=f or None,
                      rerank=rerank, cache=False)
        rank = next((n + 1 for n, h in enumerate(hits) if _is_hit(h, q["gold"], recs)), None)
        rows.append({"id": q["id"], "question": q["question"], "gold": q["gold"], "rank": rank,
                     "top1": hits[0]["chunk_id"] if hits else None})
    n = len(rows)
    return {"rows": rows, "n": n, "recall@5": sum(1 for r in rows if r["rank"]) / n,
            "mrr": sum(1 / r["rank"] for r in rows if r["rank"]) / n}


def table(res: dict) -> str:
    out = [f"{'id':<5} {'rank':<5} {'gold':<34} question"]
    for r in res["rows"]:
        g = r["gold"].get("record") or f"{r['gold']['source']} p{r['gold']['page']}"
        out.append(f"{r['id']:<5} {str(r['rank'] or '-'):<5} {g:<34} {r['question'][:70]}")
    out.append(f"\nquestions={res['n']}  recall@5={res['recall@5']:.3f}  MRR={res['mrr']:.3f}")
    return "\n".join(out)
