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
    global _idx, _reranker
    _idx = None
    _reranker = None


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
            vals = {"jurisdiction": set(), "doc_type": set(), "binding_status": set(), "tier": set()}
            for m in rows["metadatas"]:
                for key in vals:
                    vals[key].add(m.get(key) or "")
            _idx = {"ids": rows["ids"], "docs": rows["documents"], "metas": rows["metadatas"],
                    "pos": {i: n for n, i in enumerate(rows["ids"])}, "vals": vals,
                    "bm25": BM25Okapi((_tok(d) for d in rows["documents"])) if rows["ids"] else None}
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
    clauses = []
    for k, v in simple.items():
        v_set = set(v) if isinstance(v, (list, tuple, set)) else {v}
        if k in idx.get("vals", {}) and idx["vals"][k] and idx["vals"][k] <= v_set:
            continue
        clauses.append({k: ({"$in": list(v)} if isinstance(v, (list, tuple, set)) else v)})
    where = None
    if len(clauses) == 1:
        where = clauses[0]
    elif clauses:
        where = {"$and": clauses}
    res = col.query(query_embeddings=[qv], n_results=min(max(n, 1), len(idx["ids"]) or 1), where=where,
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
    model_name = config.reranker_model()
    if _reranker is None or getattr(_reranker, "_orca_model_name", None) != model_name:
        if "qwen" in model_name.lower():
            import torch
            from sentence_transformers import CrossEncoder
            torch.set_num_threads(config.rerank_threads())
            device = config.rerank_device()
            kwargs = {"torch_dtype": torch.float32} if device == "cpu" else {}
            _reranker = CrossEncoder(model_name, device=device, model_kwargs=kwargs, trust_remote_code=True)
        else:
            from fastembed.rerank.cross_encoder import TextCrossEncoder
            _reranker = TextCrossEncoder(model_name=model_name, threads=config.rerank_threads())
        _reranker._orca_model_name = model_name
    cap = config.rerank_chars()
    pairs = [[query, c["text"][:cap]] for c in cands]
    scores = list(_reranker.predict(pairs) if hasattr(_reranker, "predict")
                  else _reranker.rerank(query, [c["text"][:cap] for c in cands]))
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


_INSTRUMENT_ALIASES: list[tuple[str, str]] | None = None


def _get_instrument_aliases() -> list[tuple[str, str]]:
    global _INSTRUMENT_ALIASES
    if _INSTRUMENT_ALIASES is None:
        aliases = [
            ("cert-in directions", "in-certin-dir-2022"),
            ("cert in directions", "in-certin-dir-2022"),
            ("certin directions", "in-certin-dir-2022"),
            ("telecom cyber security rules", "in-tcsr-2024"),
            ("telecommunications (telecom cyber security) rules", "in-tcsr-2024"),
            ("critical telecommunication infrastructure rules", "in-ctir-2024"),
            ("telecommunications (critical telecommunication infrastructure) rules", "in-ctir-2024"),
            ("space cyber security framework", "in-space-fw-2026"),
            ("space including satellite communication", "in-space-fw-2026"),
            ("digital personal data protection act", "in-dpdp-act-2023"),
            ("dpdp act", "in-dpdp-act-2023"),
            ("digital personal data protection rules", "in-dpdp-rules-2025"),
            ("dpdp rules", "in-dpdp-rules-2025"),
            ("telecommunications act", "in-telact-2023"),
            ("telecom act", "in-telact-2023"),
            ("information technology act", "in-itact-2000"),
            ("it act", "in-itact-2000"),
            ("g.s.r. 720(e)", "in-tcsr-2024"),
            ("g.s.r. 771(e)", "in-tcsr-2025-amendment"),
            ("g.s.r. 892(e)", "in-dpdp-rules-2025-corrigendum"),
            ("g.s.r. 513(e)", "in-authz-rules-2026"),
            ("authorisation rules", "in-authz-rules-2026"),
            ("interconnection instructions", "ae-tdra-interconnection-2006"),
            ("information assurance regulation", "ae-tdra-iar-v1-1"),
            ("disaster sop", "in-dot-disaster-sop-2017"),
            ("sop-2017", "in-dot-disaster-sop-2017"),
            ("trai qos", "in-trai-qos-2024"),
            ("cea regulations", "in-cea-comm-2020"),
            ("47 cfr", "us-fcc-part4"),
            ("nis2", "eu-nis2-2022"),
            ("gdpr", "eu-gdpr-2016"),
        ]
        try:
            import yaml
            sy = config.sources_yaml()
            if sy.exists():
                data = yaml.safe_load(sy.read_text())
                for s in data:
                    sid = s.get("id")
                    title = s.get("title") or ""
                    clean_t = re.sub(r"\(notified.*?\)", "", title, flags=re.I).strip().lower()
                    if clean_t and (clean_t, sid) not in aliases:
                        aliases.append((clean_t, sid))
        except Exception:
            pass
        _INSTRUMENT_ALIASES = sorted(aliases, key=lambda x: -len(x[0]))
    return _INSTRUMENT_ALIASES


def route_citation(query: str, idx: dict, filters: dict | None = None) -> int | None:
    """Find matching chunk index in idx for queries citing specific legal instruments/clauses."""
    ql = query.lower()
    target_src = None
    for alias, sid in _get_instrument_aliases():
        if alias in ql:
            target_src = sid
            break

    m_dir = re.search(r'\bdirection\s*\(([ivx]+)\)', ql)
    m_annx = re.search(r'(?:item\s*\(([ivx0-9a-z]+)\)\s*of\s*annexure\s*([0-9ivx]+)|annexure\s*([0-9ivx]+)[,\s]+item\s*\(([ivx0-9a-z]+)\))', ql)
    m_sec_dot = re.search(r'(?:section|para|§)\s*([0-9]+\.[0-9]+(?:\.[0-9]+)*)', ql)
    m_rule = re.search(r'\b(rule|section|article|regulation|para)\s+([0-9]+[a-z]*)((?:\s*\([0-9a-z]+\))+)?', ql)
    m_gsr = re.search(r'\b(g\.s\.r\.\s*\d+\([a-z]\))', ql)
    m_so = re.search(r'\b(s\.o\.\s*\d+\([a-z]\))', ql)
    m_cfr = re.search(r'\b(\d+\s*cfr\s*§?\s*[\d\.]+)', ql)

    if not (m_dir or m_annx or m_sec_dot or m_rule or m_gsr or m_so or m_cfr):
        return None
    if not target_src and not (m_gsr or m_cfr or m_so):
        return None

    best_idx = None
    best_score = -1.0

    for i, (doc, meta) in enumerate(zip(idx["docs"], idx["metas"])):
        if meta.get("level") == "parent":
            continue
        if target_src and meta.get("source_id") != target_src:
            continue
        if filters and not _allowed(meta, filters):
            continue

        c = (meta.get("clause") or "").strip().lower()
        score = 0.0

        body = doc.split(" | p.")[-1] if " | p." in doc else doc
        if not re.search(r"[\u0900-\u097f]", body):
            score += 15.0

        if m_dir:
            num = m_dir.group(1).lower()
            if c == f"({num})" or c == f"direction ({num})" or f"({num})" in c:
                score += 100.0
        elif m_annx:
            item = (m_annx.group(1) or m_annx.group(4)).lower()
            if f"({item})" in c and ("annexure" in c or "anx" in c):
                score += 100.0
            elif f"({item})" in doc.lower() and "annexure" in doc.lower():
                score += 50.0
        elif m_sec_dot:
            snum = m_sec_dot.group(1).lower()
            if snum in c:
                score += 100.0
            elif snum in doc.lower():
                score += 50.0
        elif m_rule:
            kind, num, sub = m_rule.group(1).lower(), m_rule.group(2).lower(), m_rule.group(3)
            clause_num_match = bool(re.search(r'(?:^|[^\d])' + re.escape(num) + r'(?:[^\d]|$)', c))
            if clause_num_match:
                score += 40.0
            if sub:
                sub_parts = re.findall(r'\([0-9a-z]+\)', sub.lower())
                if all(sp in c for sp in sub_parts):
                    score += 60.0
                elif any(sp in c for sp in sub_parts):
                    score += 30.0
                if all(sp in doc.lower() for sp in sub_parts):
                    score += 50.0
                elif sub_parts and sub_parts[-1] in doc.lower():
                    score += 40.0
            else:
                if clause_num_match:
                    score += 30.0
        elif m_gsr:
            gsr_str = re.sub(r'\s+', '', m_gsr.group(1).lower())
            if gsr_str in re.sub(r'\s+', '', doc.lower()):
                score += 80.0
        elif m_cfr:
            cfr_str = m_cfr.group(1).lower()
            if cfr_str in doc.lower():
                score += 80.0

        if score > 20.0 and score > best_score:
            best_score = score
            best_idx = i

    return best_idx


def _asks_binding_indian_rule(q: str) -> bool:
    ql = q.lower()
    if "binding or advisory" in ql:
        return False
    if re.search(r'\b(binding|mandatory|compulsory)\b', ql):
        return True
    has_in = bool(re.search(r'\b(india|indian)\b', ql))
    has_rule = bool(re.search(r'\b(statute|statutory|duty|obligation|law|rule|regulation|provision|requirement|mandate)\b', ql))
    return has_in and has_rule


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
    target = config.rerank_pool() if rerank else k
    chosen = _dedupe(order, idx, target) if dedupe else order[:target]
    pool = [_row(idx, i, fused[i], cosine=cos.get(i)) for i in chosen]
    if rerank and pool:
        pool = _rerank(query, pool)

    # Citation router promotion
    route_idx = route_citation(query, idx, xf)
    if route_idx is not None:
        route_cid = idx["ids"][route_idx]
        existing = next((h for h in pool if h["chunk_id"] == route_cid), None)
        top_score = (pool[0]["score"] + 10.0) if pool else 100.0
        if existing:
            pool.remove(existing)
            existing["score"] = top_score
            pool.insert(0, existing)
        else:
            new_hit = _row(idx, route_idx, top_score, cosine=cos.get(route_idx))
            pool.insert(0, new_hit)

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
    if not r["ids"] and col.name != "orca_kb":
        try:
            r = store.collection(create=False, name="orca_kb").get(ids=[chunk_id], include=["documents", "metadatas"])
        except Exception:
            pass
    if not r["ids"]:
        return None
    m = r["metadatas"][0]
    return {"chunk_id": chunk_id, "text": r["documents"][0], "source_id": m.get("source_id", ""),
            "title": m.get("title", ""), "jurisdiction": m.get("jurisdiction", ""),
            "binding_status": m.get("binding_status", ""), "page": m.get("page", 0),
            "clause": m.get("clause", "") or None, "url": m.get("url", ""), "tier": m.get("tier", ""),
            "score": 1.0, "parent_id": m.get("parent_id") or None,
            "parent_text": "", "amendment_links": _links(m.get("amendment_links"))}


_VERIFIED_QUOTES: list[tuple[str, str]] | None = None


def _verified_quotes() -> list[tuple[str, str]]:
    """(source_id, normalised first 80 chars of the quote) for every verified KB record."""
    global _VERIFIED_QUOTES
    if _VERIFIED_QUOTES is None:
        from . import ingest
        n = lambda t: re.sub(r"[^a-z0-9]+", " ", str(t).lower()).strip()  # noqa: E731
        _VERIFIED_QUOTES = [(r["source"], n(r["quote"])[:80]) for r in ingest._records()
                            if r.get("verified") and r.get("quote") and n(r["quote"])]
    return _VERIFIED_QUOTES


def _top_has_verified_quote(hits: list[dict]) -> bool:
    """True when a hit is the very text a verified record quotes (the system knows that record)."""
    n = lambda t: re.sub(r"[^a-z0-9]+", " ", str(t).lower()).strip()  # noqa: E731
    quotes = _verified_quotes()
    return any(src == h.get("source_id") and q in n(h.get("text", "")) for h in hits for src, q in quotes)



def search_with_abstention(query: str, k: int = 5, filters: dict | None = None, rerank: bool = True,
                           threshold: float | None = None,
                           temperature: float | None = None,
                           prob_threshold: float | None = None,
                           margin_threshold: float | None = None,
                           z_threshold: float | None = None,
                           **kwargs) -> dict:
    """Retrieve or explicitly abstain using calibrated probability, margin, z-score and jurisdiction gate."""
    import math
    import statistics

    results = search(query, k=k, filters=filters, rerank=rerank, **kwargs)
    if not results:
        return {"results": [], "abstained": True, "best_score": float("-inf"),
                "prob": 0.0, "margin": 0.0, "list_z": 0.0, "reason": "NO_RESULTS"}

    scores = [h["score"] for h in results]
    z1 = scores[0]
    z2 = scores[1] if len(scores) > 1 else z1 - 10.0
    margin = z1 - z2

    T = config.abstain_temperature() if temperature is None else temperature
    prob = 1.0 / (1.0 + math.exp(-z1 / T)) if T > 0 else (1.0 if z1 > 0 else 0.0)

    if len(scores) > 1:
        mean_s = statistics.mean(scores)
        std_s = statistics.pstdev(scores)
        list_z = (z1 - mean_s) / std_s if std_s > 1e-6 else 0.0
    else:
        list_z = 3.0

    prob_cut = config.abstain_prob_threshold() if prob_threshold is None else prob_threshold
    margin_cut = config.abstain_margin_threshold() if margin_threshold is None else margin_threshold
    z_cut = config.abstain_z_threshold() if z_threshold is None else z_threshold
    legacy_cut = config.abstain_threshold() if threshold is None else threshold
    if not rerank and threshold is None:
        legacy_cut = None   # without a reranker the score is an RRF value, not a logit

    # 1. Jurisdiction / binding gate
    if _asks_binding_indian_rule(query):
        top_slice = results[:min(3, len(results))]
        has_binding_in = any(
            canon_jurisdiction(h.get("jurisdiction")) == "IN" and
            norm_text(h.get("binding_status")) in ("binding", "binding not in force")
            for h in top_slice
        )
        if not has_binding_in:
            return {"results": [], "abstained": True, "best_score": z1,
                    "prob": prob, "margin": margin, "list_z": list_z,
                    "reason": "NO_BINDING_IN_JURISDICTION"}

    # 2. Score thresholding
    abstained = False
    reason = None

    if legacy_cut is not None and z1 < legacy_cut:
        abstained = True
        reason = "SCORE_BELOW_THRESHOLD"
    elif prob_cut is not None and prob < prob_cut:
        abstained = True
        reason = "LOW_PROBABILITY"
    elif margin_cut is not None and z_cut is not None:
        if margin < margin_cut and list_z < z_cut:
            abstained = True
            reason = "AMBIGUOUS_CANDIDATES"

    # 3. Safety net: never abstain when the answer is a verified KB record's own text (the gap evidence).
    if abstained and _top_has_verified_quote(results[:3]):
        abstained, reason = False, None

    return {"results": [] if abstained else results, "abstained": abstained,
            "best_score": z1, "prob": prob, "margin": margin, "list_z": list_z,
            "reason": reason, "verified_record_in_top3": _top_has_verified_quote(results[:3])}


def coverage(topic_query: str, jurisdiction: str) -> dict:
    """For gap analysis: how many documents were searched and the nearest clauses (cosine similarity)."""
    idx = _index()
    j = canon_jurisdiction(jurisdiction)
    docs = {m["source_id"] for m in idx["metas"] if canon_jurisdiction(m.get("jurisdiction")) == j}
    hits = _search_full(topic_query, 5, {"jurisdiction": j}, rerank=False)
    nearest = [{**{kk: h[kk] for kk in PUBLIC_KEYS if kk != "score"}, "score": h.get("cosine"),
                "excerpt": h["text"][:240]} for h in hits]
    return {"searched_docs": len(docs), "jurisdiction": j, "query": topic_query, "nearest": nearest}
