"""Hybrid retrieval: Chroma cosine vectors + BM25, fused with RRF, metadata filters, optional cross-encoder rerank."""
from __future__ import annotations

import datetime as dt
import re
import threading

from . import config, replay, store

PUBLIC_KEYS = ("chunk_id", "text", "source_id", "title", "jurisdiction", "binding_status", "page",
               "clause", "url", "tier", "score")
RRF_K = 60
CANDIDATES = 40          # per ranker, and the pool handed to the reranker
RERANK_POOL = 30

_lock = threading.Lock()
_idx: dict | None = None
_reranker = None


def invalidate() -> None:
    global _idx
    _idx = None


def _tok(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", s.lower())


def _index() -> dict:
    global _idx
    with _lock:
        if _idx is None:
            from rank_bm25 import BM25Okapi
            rows = store.all_rows()
            _idx = {"ids": rows["ids"], "docs": rows["documents"], "metas": rows["metadatas"],
                    "pos": {i: n for n, i in enumerate(rows["ids"])},
                    "bm25": BM25Okapi([_tok(d) for d in rows["documents"]]) if rows["ids"] else None}
        return _idx


def _allowed(meta: dict, filters: dict) -> bool:
    for key, want in filters.items():
        if key == "in_force_on":
            continue
        have = meta.get(key)
        if isinstance(want, (list, tuple, set)):
            if have not in want:
                return False
        elif have != want:
            return False
    on = filters.get("in_force_on")
    if on:
        on = on.isoformat() if isinstance(on, (dt.date, dt.datetime)) else str(on)
        start = meta.get("in_force_from") or ""
        if meta.get("binding_status") in ("binding_not_in_force", "binding") and start and start > on:
            return False
    return True


def _row(idx: dict, i: int, score: float, **extra) -> dict:
    m = idx["metas"][i]
    d = {"chunk_id": idx["ids"][i], "text": idx["docs"][i], "source_id": m.get("source_id", ""),
         "title": m.get("title", ""), "jurisdiction": m.get("jurisdiction", ""),
         "binding_status": m.get("binding_status", ""), "page": m.get("page", 0),
         "clause": m.get("clause", "") or None, "url": m.get("url", ""), "tier": m.get("tier", ""),
         "score": float(score)}
    d.update(extra)
    return d


def _vector_rank(query: str, filters: dict, n: int) -> list[tuple[int, float]]:
    from . import embed
    idx = _index()
    col = store.collection()
    qv = embed.embed([query], kind="query")[0]
    simple = {k: v for k, v in filters.items() if k != "in_force_on"}
    where = None
    clauses = [{k: ({"$in": list(v)} if isinstance(v, (list, tuple, set)) else v)} for k, v in simple.items()]
    if len(clauses) == 1:
        where = clauses[0]
    elif clauses:
        where = {"$and": clauses}
    res = col.query(query_embeddings=[qv], n_results=min(max(n, 1), max(col.count(), 1)), where=where,
                    include=["distances", "metadatas"])
    out = []
    for cid, dist, meta in zip(res["ids"][0], res["distances"][0], res["metadatas"][0]):
        if _allowed(meta, filters):
            out.append((idx["pos"][cid], 1.0 - dist))      # cosine similarity
    return out


def _bm25_rank(query: str, filters: dict, n: int) -> list[tuple[int, float]]:
    idx = _index()
    if not idx["bm25"]:
        return []
    scores = idx["bm25"].get_scores(_tok(query))
    order = sorted(range(len(scores)), key=lambda i: -scores[i])
    out = []
    for i in order:
        if scores[i] <= 0:
            break
        if _allowed(idx["metas"][i], filters):
            out.append((i, scores[i]))
            if len(out) >= n:
                break
    return out


def _rerank(query: str, cands: list[dict]) -> list[dict]:
    global _reranker
    if _reranker is None:
        from fastembed.rerank.cross_encoder import TextCrossEncoder
        _reranker = TextCrossEncoder(model_name=config.reranker_model())
    scores = list(_reranker.rerank(query, [c["text"][:2000] for c in cands]))
    for c, s in zip(cands, scores):
        c["score"] = float(s)
    return sorted(cands, key=lambda c: -c["score"])


def _search_full(query: str, k: int, filters: dict, rerank: bool) -> list[dict]:
    idx = _index()
    if not idx["ids"]:
        return []
    vec = _vector_rank(query, filters, CANDIDATES)
    bm = _bm25_rank(query, filters, CANDIDATES)
    cos = dict(vec)
    fused: dict[int, float] = {}
    for ranking in (vec, bm):
        for r, (i, _) in enumerate(ranking):
            fused[i] = fused.get(i, 0.0) + 1.0 / (RRF_K + r + 1)
    order = sorted(fused, key=lambda i: -fused[i])
    pool = [_row(idx, i, fused[i], cosine=cos.get(i)) for i in order[:RERANK_POOL if rerank else k]]
    if rerank and pool:
        pool = _rerank(query, pool)
    return pool[:k]


def search(query: str, k: int = 5, filters: dict | None = None, rerank: bool = True,
           cache: bool = True) -> list[dict]:
    """Hybrid search. Each hit has exactly PUBLIC_KEYS. Replays from the retrieval cache when present."""
    filters = {kk: v for kk, v in (filters or {}).items() if v is not None}
    key = None
    if cache:
        key = replay.cache_key(query, k, filters, rerank)
        hit = replay.cache_get(key)
        if hit is not None:
            return hit
    out = [{kk: h[kk] for kk in PUBLIC_KEYS} for h in _search_full(query, k, filters, rerank)]
    if cache:
        replay.cache_put(key, query, k, filters, rerank, out)
    return out


def get_chunk(chunk_id: str) -> dict | None:
    col = store.collection()
    r = col.get(ids=[chunk_id], include=["documents", "metadatas"])
    if not r["ids"]:
        return None
    m = r["metadatas"][0]
    return {"chunk_id": chunk_id, "text": r["documents"][0], "source_id": m.get("source_id", ""),
            "title": m.get("title", ""), "jurisdiction": m.get("jurisdiction", ""),
            "binding_status": m.get("binding_status", ""), "page": m.get("page", 0),
            "clause": m.get("clause", "") or None, "url": m.get("url", ""), "tier": m.get("tier", ""),
            "score": 1.0}


def coverage(topic_query: str, jurisdiction: str) -> dict:
    """For gap analysis: how many documents were searched and the nearest clauses (cosine similarity)."""
    idx = _index()
    docs = {m["source_id"] for m in idx["metas"] if m.get("jurisdiction") == jurisdiction and m.get("tier") == "corpus"}
    docs |= {m["source_id"] for m in idx["metas"] if m.get("jurisdiction") == jurisdiction}
    hits = _search_full(topic_query, 5, {"jurisdiction": jurisdiction}, rerank=False)
    nearest = [{**{kk: h[kk] for kk in PUBLIC_KEYS if kk != "score"}, "score": h.get("cosine"),
                "excerpt": h["text"][:240]} for h in hits]
    return {"searched_docs": len(docs), "jurisdiction": jurisdiction, "query": topic_query, "nearest": nearest}
