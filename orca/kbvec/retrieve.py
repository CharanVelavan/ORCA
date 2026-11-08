"""Hybrid retrieval: Chroma cosine vectors + BM25, fused with RRF, metadata filters, optional cross-encoder rerank."""
from __future__ import annotations

import datetime as dt
import re
import threading

from . import config, replay, store
from .meta import canon_doc_type, canon_jurisdiction, norm_text

PUBLIC_KEYS = ("chunk_id", "text", "source_id", "title", "jurisdiction", "binding_status", "page",
               "clause", "url", "tier", "score", "parent_id", "parent_text", "amendment_links")
FILTER_KEYS = ("jurisdiction", "doc_type", "binding_status", "tier", "source_id", "in_force_on")
RRF_K = 60
CANDIDATES = 40          # per ranker, and the pool handed to the reranker
RERANK_POOL = 30
DUP_SHINGLE = 8          # words per shingle when comparing chunk texts
DUP_THRESHOLD = 0.8      # share of the shorter chunk's shingles that must appear in a kept chunk

_lock = threading.Lock()
_idx: dict | None = None
_reranker = None


def invalidate() -> None:
    global _idx
    _idx = None


_LEGAL_TOKEN = re.compile(r"(?:\d+(?:\.\d+)*(?:\([0-9A-Za-z]+\))+|"
                          r"(?:article|rule|section|regulation|direction)\s+\d+(?:\.\d+)*(?:\([0-9A-Za-z]+\))*|"
                          r"g\.s\.r\.\s*\d+\([A-Za-z]\)|s\.o\.\s*\d+\([A-Za-z]\)|"
                          r"\d+\s*cfr\s*§?\s*\d+(?:\.\d+)*|[a-z0-9]+)", re.I)
_SYNONYMS = {"notify": ("report", "inform"), "report": ("notify", "inform"), "inform": ("notify", "report"),
             "operator": ("licensee", "authorised"), "licensee": ("operator", "authorised"),
             "incident": ("breach", "cyberincident"), "breach": ("incident",),
             "satellite": ("space", "ntn"), "space": ("satellite", "ntn"), "ntn": ("satellite", "space")}


def _tok(s: str) -> list[str]:
    """Legal-aware BM25 tokens, retaining citations such as Rule 7(1)(a)."""
    tokens = [re.sub(r"\s+", "", x.lower()) for x in _LEGAL_TOKEN.findall(s)]
    return tokens + [alt for token in tokens for alt in _SYNONYMS.get(token, ())]


def _index() -> dict:
    global _idx
    with _lock:
        if _idx is None:
            from rank_bm25 import BM25Okapi
            rows = store.all_rows()
            vals = {"jurisdiction": set(), "doc_type": set(), "binding_status": set()}
            for m in rows["metadatas"]:
                for key in vals:
                    vals[key].add(m.get(key) or "")
            _idx = {"ids": rows["ids"], "docs": rows["documents"], "metas": rows["metadatas"],
                    "pos": {i: n for n, i in enumerate(rows["ids"])}, "vals": vals,
                    "bm25": BM25Okapi([_tok(d) for d in rows["documents"]]) if rows["ids"] else None}
        return _idx


def normalize_filters(filters: dict | None) -> dict:
    """Canonical filter values: jurisdiction IN/EU/US/AE/INTL, doc_type from meta.DOC_TYPES, status without
    case or underscore differences. Drops None values; rejects unknown keys so a typo cannot silently match
    nothing."""
    out: dict = {}
    for key, v in (filters or {}).items():
        if v is None:
            continue
        if key not in FILTER_KEYS:
            raise ValueError(f"unknown filter {key!r}; use one of {', '.join(FILTER_KEYS)}")
        vals = list(v) if isinstance(v, (list, tuple, set)) else [v]
        if key == "jurisdiction":
            vals = [canon_jurisdiction(x) for x in vals]
        elif key == "doc_type":
            vals = [canon_doc_type(x) for x in vals]
        elif key == "binding_status":
            vals = [norm_text(x) for x in vals]
        elif key == "in_force_on":
            out[key] = v.isoformat() if isinstance(v, (dt.date, dt.datetime)) else str(v)
            continue
        out[key] = sorted(set(vals)) if isinstance(v, (list, tuple, set)) else vals[0]
    return out


def expand_filters(filters: dict, idx: dict) -> dict | None:
    """Map canonical filter values to every stored value that means the same thing.

    Returns None when a filter matches no stored value (the search then returns nothing)."""
    out: dict = {}
    for key, want in filters.items():
        if key not in ("jurisdiction", "doc_type", "binding_status"):
            out[key] = want
            continue
        wanted = set(want) if isinstance(want, (list, tuple, set)) else {want}
        if key == "jurisdiction":
            raw = [x for x in idx["vals"][key] if canon_jurisdiction(x) in wanted]
        elif key == "doc_type":
            raw = [x for x in idx["vals"][key] if canon_doc_type(x) in wanted]
        else:
            raw = [x for x in idx["vals"][key] if norm_text(x) in wanted]
        if not raw:
            return None
        out[key] = sorted(raw)
    return out


def _allowed(meta: dict, filters: dict) -> bool:
    # Parent sections are expansion payloads, never independent search results.
    if meta.get("level") == "parent":
        return False
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
         "score": float(score), "parent_id": m.get("parent_id") or None,
         "parent_text": "", "amendment_links": _links(m.get("amendment_links"))}
    d.update(extra)
    return d


def _links(value) -> list:
    if isinstance(value, list):
        return value
    if not value:
        return []
    try:
        import json
        return json.loads(value)
    except (TypeError, ValueError):
        return [str(value)]


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
        # fastembed is retained as a lightweight compatibility path.  Qwen
        # rerankers require transformers and can be selected through the env.
        if "qwen" in config.reranker_model().lower():
            from sentence_transformers import CrossEncoder
            _reranker = CrossEncoder(config.reranker_model(), trust_remote_code=True)
        else:
            from fastembed.rerank.cross_encoder import TextCrossEncoder
            _reranker = TextCrossEncoder(model_name=config.reranker_model())
    pairs = [[query, c["text"][:8000]] for c in cands]
    scores = list(_reranker.predict(pairs) if hasattr(_reranker, "predict")
                  else _reranker.rerank(query, [c["text"][:8000] for c in cands]))
    for c, s in zip(cands, scores):
        c["score"] = float(s)
    return sorted(cands, key=lambda c: -c["score"])


def _shingles(text: str) -> set:
    w = _tok(text)
    if len(w) <= DUP_SHINGLE:
        return {tuple(w)} if w else set()
    return {hash(tuple(w[i:i + DUP_SHINGLE])) for i in range(len(w) - DUP_SHINGLE + 1)}


def _near_duplicate(a: set, b: set) -> bool:
    small = a if len(a) <= len(b) else b
    if not small:
        return False
    return len(a & b) / len(small) >= DUP_THRESHOLD


def _dedupe(order: list[int], idx: dict, target: int) -> list[int]:
    """Keep the best-ranked chunk of each group of identical or near-identical texts.

    Covers the same page chunk returned twice, duplicate PDFs (same sha256, so identical chunks under two
    source ids) and boilerplate repeated across documents. Dropped copies are not reported."""
    kept: list[int] = []
    sigs: list[set] = []
    for i in order:
        text = idx["docs"][i]
        sig = _shingles(text)
        if any(text == idx["docs"][j] or _near_duplicate(sig, s) for j, s in zip(kept, sigs)):
            continue
        kept.append(i)
        sigs.append(sig)
        if len(kept) >= target:
            break
    return kept


def _search_full(query: str, k: int, filters: dict, rerank: bool, dedupe: bool = True) -> list[dict]:
    idx = _index()
    if not idx["ids"]:
        return []
    xf = expand_filters(normalize_filters(filters), idx)
    if xf is None:
        return []
    vec = _vector_rank(query, xf, CANDIDATES)
    bm = _bm25_rank(query, xf, CANDIDATES)
    cos = dict(vec)
    fused: dict[int, float] = {}
    for ranking in (vec, bm):
        for r, (i, _) in enumerate(ranking):
            fused[i] = fused.get(i, 0.0) + 1.0 / (RRF_K + r + 1)
    order = sorted(fused, key=lambda i: -fused[i])
    target = RERANK_POOL if rerank else k
    chosen = _dedupe(order, idx, target) if dedupe else order[:target]
    pool = [_row(idx, i, fused[i], cosine=cos.get(i)) for i in chosen]
    if rerank and pool:
        pool = _rerank(query, pool)
    # Small-to-big expansion stays outside ranking: parents never displace a
    # precise clause, but are returned with it when present in this collection.
    parents = {m.get("parent_id"): d for m, d in zip(idx["metas"], idx["docs"]) if m.get("level") == "parent"}
    for hit in pool:
        if hit.get("parent_id"):
            hit["parent_text"] = parents.get(hit["parent_id"], "")
    return pool[:k]


def search(query: str, k: int = 5, filters: dict | None = None, rerank: bool = True,
           cache: bool = True, dedupe: bool = True) -> list[dict]:
    """Hybrid search. Each hit has exactly PUBLIC_KEYS. Replays from the retrieval cache when present.

    filters (all optional, combined with AND; a list means "any of"):
      jurisdiction  IN, EU, US, AE, INTL (other states are INTL)
      doc_type      act, rules, direction, directive, guideline, standard, recommendation, licence, treaty,
                    regulation, order, policy, report, consultation, faq, verified_record, other
      binding_status, tier (corpus | verified), source_id, in_force_on (ISO date)
    dedupe=False keeps identical or near-identical chunks in the results (for debugging).
    """
    filters = normalize_filters(filters)
    key = None
    if cache:
        key = replay.cache_key(query, k, filters, rerank, dedupe)
        hit = replay.cache_get(key)
        if hit is not None:
            return hit
    out = [{kk: h[kk] for kk in PUBLIC_KEYS} for h in _search_full(query, k, filters, rerank, dedupe)
           if h.get("tier") != "parent"]
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
            "score": 1.0, "parent_id": m.get("parent_id") or None,
            "parent_text": "", "amendment_links": _links(m.get("amendment_links"))}


def search_with_abstention(query: str, k: int = 5, filters: dict | None = None, rerank: bool = True,
                           threshold: float | None = None, **kwargs) -> dict:
    """Retrieve or explicitly abstain.  A configured threshold is calibration data, never a default claim."""
    results = search(query, k=k, filters=filters, rerank=rerank, **kwargs)
    best = results[0]["score"] if results else float("-inf")
    threshold = config.abstain_threshold() if threshold is None else threshold
    abstained = not results or (threshold is not None and best < threshold)
    return {"results": [] if abstained else results, "abstained": abstained, "best_score": best}


def coverage(topic_query: str, jurisdiction: str) -> dict:
    """For gap analysis: how many documents were searched and the nearest clauses (cosine similarity)."""
    idx = _index()
    j = canon_jurisdiction(jurisdiction)
    docs = {m["source_id"] for m in idx["metas"] if canon_jurisdiction(m.get("jurisdiction")) == j}
    hits = _search_full(topic_query, 5, {"jurisdiction": j}, rerank=False)
    nearest = [{**{kk: h[kk] for kk in PUBLIC_KEYS if kk != "score"}, "score": h.get("cosine"),
                "excerpt": h["text"][:240]} for h in hits]
    return {"searched_docs": len(docs), "jurisdiction": j, "query": topic_query, "nearest": nearest}
