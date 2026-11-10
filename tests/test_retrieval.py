"""Retrieval tests for orca.kbvec.

Unit tests (chunking, filters, cache keys, question file) always run. The retrieval-quality test needs a
built index and a reachable embedder, so it skips otherwise. Build with `python -m orca.kbvec ingest`.
"""
from __future__ import annotations

import json

import pytest
import yaml

from orca.kbvec import chunk, config, evaluate, replay
from orca.kbvec.retrieve import _allowed


def test_question_file_is_well_formed():
    qs = yaml.safe_load(config.eval_file().read_text())
    assert len(qs) == 30 and len({q["id"] for q in qs}) == 30
    recs = evaluate._records()
    for q in qs:
        g = q["gold"]
        assert ("record" in g and g["record"] in recs) or ("source" in g and "page" in g), q["id"]


def test_v2_question_file_has_fixed_dev_test_split_and_required_categories():
    qs = yaml.safe_load(config.eval_v2_file().read_text())
    assert len(qs) >= 100 and {q["split"] for q in qs} == {"dev", "test"}
    assert sum(q["split"] == "dev" for q in qs) == sum(q["split"] == "test" for q in qs)
    kinds = {q["kind"] for q in qs}
    assert {"positive", "negative", "amendment", "exact_citation"} <= kinds
    assert all(q["kind"] == "negative" or q.get("gold") for q in qs)


def test_chunker_splits_on_headings_and_windows_long_text():
    text = "Rule 7. Reporting\n" + "alpha " * 100 + "\nRule 8. Logs\n" + "beta " * 100
    chunks, last = chunk.chunk_page(text)
    assert [c["clause"] for c in chunks] == ["Rule 7", "Rule 8"] and last == "Rule 8"
    long, _ = chunk.chunk_page("word " * 1000)
    assert len(long) > 1 and all(len(c["text"].split()) <= chunk.MAX_WORDS for c in long)


def test_roman_subclauses_stay_with_their_text_and_heading():
    page = ("Direction 2 point of contact\n"
            "(iii)When required by order of CERT-In, the provider shall act. " + "alpha " * 40 + "\n"
            "(iv) All service providers shall keep logs for 180 days within India. " + "beta " * 40 + "\n"
            "XI B(v) Assure cyber security including encryptions at design level. " + "gamma " * 40)
    chunks, last = chunk.chunk_page(page)
    labels = [c["clause"] for c in chunks]
    assert labels == ["Direction 2", "Direction 2 (iii)", "Direction 2 (iv)", "XI B(v)"], labels
    assert last == "XI B(v)"
    iv = next(c for c in chunks if c["clause"] == "Direction 2 (iv)")
    assert iv["text"].startswith("Direction 2. (iv) All service providers") and "logs for 180 days" in iv["text"]
    assert chunk.sub_clause("iv. Design should minimise debris") == "(iv)"
    assert chunk.sub_clause("I. PRINT MEDIA") is None and chunk.sub_clause("civil text") is None


def test_long_sub_clause_repeats_its_label_on_each_window():
    page = "(iv) Keep logs for 180 days in India. " + "word " * 1000
    chunks, _ = chunk.chunk_page(page)
    assert len(chunks) > 1 and all(c["clause"] == "(iv)" for c in chunks)
    assert all(c["text"].startswith("(iv)") or c["text"].startswith("(iv). ") for c in chunks[1:])
    assert all(len(c["text"].split()) <= chunk.MAX_WORDS for c in chunks)
    plain, _ = chunk.chunk_page("Rule 7. Reporting\n" + "word " * 1000)
    assert [c["text"].split()[0] for c in plain[1:]] == ["word"] * (len(plain) - 1)   # unchanged for non-sub


def test_filters_including_in_force_date():
    meta = {"jurisdiction": "IN", "binding_status": "binding_not_in_force", "in_force_from": "2027-05-13"}
    assert _allowed(meta, {"jurisdiction": "IN"})
    assert not _allowed(meta, {"jurisdiction": "EU"})
    assert not _allowed(meta, {"in_force_on": "2026-11-10"})
    assert _allowed(meta, {"in_force_on": "2027-06-01", "jurisdiction": ["IN", "EU"]})


def _index_ready() -> bool:
    try:
        from orca.kbvec import store
        import httpx
        httpx.get(config.embed_url().rstrip("/") + "/models", timeout=3)
        return store.collection().count() > 0
    except Exception:
        return False


@pytest.mark.skipif(not _index_ready(), reason="index not built or embedder not reachable")
def test_retrieval_quality_and_interface():
    from orca.kbvec import get_chunk, search
    hits = search("deadline to report incidents to CERT-In", k=5, cache=False)
    assert hits and {"chunk_id", "text", "source_id", "title", "jurisdiction", "binding_status", "page",
                     "clause", "url", "tier", "score", "parent_id", "parent_text", "amendment_links"} <= set(hits[0])
    assert get_chunk("IN-CERTIN-DIR-2022-ii")["tier"] == "verified"
    assert get_chunk("no-such-chunk") is None
    res = evaluate.run()
    print("\n" + evaluate.table(res))
    assert res["recall@5"] >= 0.6 and res["mrr"] >= 0.4      # floor, not the target; see docs/KBVEC.md


def test_filter_canonicalisation_and_expansion():
    from orca.kbvec import retrieve
    from orca.kbvec.meta import canon_doc_type, canon_jurisdiction
    assert canon_jurisdiction("IN-TN") == "IN" and canon_jurisdiction("UK") == "INTL"
    assert canon_jurisdiction("International") == "INTL" and canon_jurisdiction("us-ca") == "US"
    assert canon_doc_type("master direction") == "direction" and canon_doc_type("guidelines") == "guideline"
    assert canon_doc_type("rules (gazette notification)") == "rules" and canon_doc_type("technical_standard") == "standard"
    f = retrieve.normalize_filters({"jurisdiction": "in", "doc_type": ["direction", "act"],
                                    "binding_status": "not_stated", "tier": None})
    assert f == {"jurisdiction": "IN", "doc_type": ["act", "direction"], "binding_status": "not stated"}
    idx = {"vals": {"jurisdiction": {"IN", "IN-TN", "EU", "UK"},
                    "doc_type": {"directions", "master direction", "act", "standard"},
                    "binding_status": {"not_stated", "binding"}}}
    x = retrieve.expand_filters(f, idx)
    assert x["jurisdiction"] == ["IN", "IN-TN"]
    assert x["doc_type"] == ["act", "directions", "master direction"]
    assert x["binding_status"] == ["not_stated"]
    assert retrieve.expand_filters({"jurisdiction": "US"}, idx) is None      # no stored value: no hits
    with pytest.raises(ValueError):
        retrieve.normalize_filters({"jurisdicton": "IN"})


def test_dedupe_keeps_best_copy_of_identical_and_near_identical_text():
    from orca.kbvec import retrieve
    base = " ".join(f"word{i}" for i in range(120))
    near = base + " extra"
    other = " ".join(f"other{i}" for i in range(120))
    idx = {"docs": [base, base, near, other, base + " x y z"]}
    assert retrieve._dedupe([0, 1, 2, 3, 4], idx, target=5) == [0, 3]
    assert retrieve._dedupe([0, 1, 3], idx, target=2) == [0, 3]


def test_cache_key_depends_on_dedupe_and_version(monkeypatch):
    from orca.kbvec import replay
    monkeypatch.setattr(replay, "_current_sid", lambda: "snap")
    a = replay.cache_key("q", 5, {"jurisdiction": ["IN"]}, True, True)
    assert a != replay.cache_key("q", 5, {"jurisdiction": ["IN"]}, True, False)
    assert a == replay.cache_key("q", 5, {"jurisdiction": ["IN"]}, True, True)


def test_v2_export_has_headers_parents_and_manifest(tmp_path):
    from orca.kbvec import ingest
    src = tmp_path / "rule.txt"
    src.write_text("Rule 7. Reports\n(1) An operator shall report.\n(a) The notice is due in six hours.\n")
    rows = ingest.v2_source_chunks({"source_id": "in-demo", "title": "Demo Rules", "authority": "DoT",
                                    "jurisdiction": "IN", "doc_type": "rules", "binding_status": "binding",
                                    "in_force_from": "2026-01-01", "licence": "official", "url": "", "path": src,
                                    "sidecar": None, "tier": "corpus", "lang": "en", "amends": [], "amended_by": []})
    clauses = [r for r in rows if r["meta"]["level"] == "clause"]
    parents = [r for r in rows if r["meta"]["level"] == "parent"]
    assert clauses and parents
    assert clauses[0]["text"].startswith("Demo Rules | DoT | IN | binding, in force 2026-01-01 | ")
    assert all(r["meta"]["parent_id"] for r in clauses)


def test_get_chunk_fails_closed_without_chromadb(monkeypatch):
    import orca.kbvec as kbvec
    import builtins
    real_import = builtins.__import__
    def blocked(name, *args, **kwargs):
        if name == "chromadb":
            raise ModuleNotFoundError("No module named 'chromadb'", name="chromadb")
        return real_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", blocked)
    assert kbvec.get_chunk("invented:p1:c1") is None


def test_citation_router_parsing_and_aliases():
    from orca.kbvec.retrieve import _get_instrument_aliases, route_citation, _index

    aliases = dict(_get_instrument_aliases())
    assert aliases.get("telecom cyber security rules") == "in-tcsr-2024"
    assert aliases.get("critical telecommunication infrastructure rules") == "in-ctir-2024"
    assert aliases.get("cert-in directions") == "in-certin-dir-2022"
    assert aliases.get("digital personal data protection act") == "in-dpdp-act-2023"
    assert aliases.get("telecommunications act") == "in-telact-2023"

    mock_idx = {
        "ids": ["chunk1", "chunk2", "chunk3"],
        "docs": [
            "Telecommunications (Telecom Cyber Security) Rules, 2024 | DoT | IN | binding | s.7 | p.5\n7. Reporting (1) ... (a) report within six hours",
            "General noise text about cybersecurity in telecom networks without citations.",
            "Directions under section 70B(6) | CERT-In | IN | binding | (ii) | p.2\n(ii) report within six hours",
        ],
        "metas": [
            {"source_id": "in-tcsr-2024", "clause": "s.7", "page": 5, "level": "clause"},
            {"source_id": "other", "clause": "p.1", "page": 1, "level": "clause"},
            {"source_id": "in-certin-dir-2022", "clause": "(ii)", "page": 2, "level": "clause"},
        ],
    }
    # Citation parsing and matching on mock index
    assert route_citation("What does Rule 7(1)(a) of the Telecom Cyber Security Rules 2024 say?", mock_idx) == 0
    assert route_citation("What does Direction (ii) of the CERT-In Directions require?", mock_idx) == 2
    # Non-citation queries must return None
    assert route_citation("How does a satellite authenticate with the ground station?", mock_idx) is None


def test_calibrated_abstention_jurisdiction_gate():
    from orca.kbvec.retrieve import _asks_binding_indian_rule, search_with_abstention
    import orca.kbvec.retrieve as ret_mod

    assert _asks_binding_indian_rule("Is there a binding Indian rule requiring a satellite operator to warn hospitals?")
    assert _asks_binding_indian_rule("What Indian rule imposes a fixed battery-hour minimum?")
    assert _asks_binding_indian_rule("What mandatory provision requires a common ground gateway?")
    assert not _asks_binding_indian_rule("Are India's space cyber guidelines binding or advisory?")
    assert not _asks_binding_indian_rule("When must an EU essential entity issue an early warning?")

    # 1. Test jurisdiction gate triggers when top hits are non-binding or non-IN
    orig_search = ret_mod.search
    ret_mod.search = lambda *a, **k: [
        {"chunk_id": "eu-chunk-1", "jurisdiction": "EU", "binding_status": "binding", "score": 10.0},
        {"chunk_id": "in-advisory-1", "jurisdiction": "IN", "binding_status": "advisory", "score": 9.0},
    ]
    try:
        res = search_with_abstention("What binding Indian rule requires continuous monitoring?", k=2)
        assert res["abstained"] is True
        assert res["reason"] == "NO_BINDING_IN_JURISDICTION"
        assert "prob" in res and "margin" in res and "list_z" in res
    finally:
        ret_mod.search = orig_search

    # 2. Test score thresholding
    ret_mod.search = lambda *a, **k: [
        {"chunk_id": "in-1", "jurisdiction": "IN", "binding_status": "binding", "score": 0.01},
    ]
    try:
        res2 = search_with_abstention("When must a telecom security event be reported?", threshold=0.05)
        assert res2["abstained"] is True
        assert res2["reason"] == "SCORE_BELOW_THRESHOLD"
    finally:
        ret_mod.search = orig_search


@pytest.mark.skipif(not _index_ready(), reason="index not built or embedder not reachable")
def test_verified_gap_evidence_records_never_abstained():
    from orca.kbvec import search_with_abstention, config
    from pathlib import Path

    gap_yaml = config.MAIN_REPO / "kb" / "gaps" / "india.yaml"
    if not gap_yaml.exists():
        pytest.skip("kb/gaps/india.yaml not found")
    data = yaml.safe_load(gap_yaml.read_text())
    verified_gap_recs = {e for g in data for e in g.get("evidence", [])}

    qs = yaml.safe_load(config.eval_v2_file().read_text())
    target_qs = [q for q in qs if q.get("gold", {}).get("record") in verified_gap_recs and q.get("kind") != "negative"]

    assert len(target_qs) > 0, "no evaluation questions found for verified gap records"
    for q in target_qs[:10]:
        res = search_with_abstention(q["question"], k=5, rerank=False, cache=False)
        assert not res["abstained"], f"abstained on verified gap question {q['id']}: {q['question']}"


# ------------------------------------------------------------------ abstention operating point (9 Nov)
def test_default_abstain_cut_is_tied_to_the_bge_reranker(monkeypatch):
    from orca.kbvec import config
    monkeypatch.delenv("ORCA_ABSTAIN_THRESHOLD", raising=False)
    monkeypatch.setenv("ORCA_RERANK_MODEL", "BAAI/bge-reranker-base")
    assert config.abstain_threshold() == config.DEFAULT_ABSTAIN_THRESHOLD == -3.0
    monkeypatch.setenv("ORCA_RERANK_MODEL", "Qwen/Qwen3-Reranker-0.6B")
    assert config.abstain_threshold() is None          # logits of another model: no cut
    monkeypatch.setenv("ORCA_RERANK_MODEL", "BAAI/bge-reranker-base")
    monkeypatch.setenv("ORCA_ABSTAIN_THRESHOLD", "")
    assert config.abstain_threshold() is None          # empty string switches abstention off


def test_verified_record_text_is_never_treated_as_unanswerable():
    from orca.kbvec import ingest
    from orca.kbvec.retrieve import _top_has_verified_quote
    rec = next(r for r in ingest._records() if r.get("verified") and r.get("quote"))
    hit = {"source_id": rec["source"], "text": "preamble " + rec["quote"] + " trailing text"}
    assert _top_has_verified_quote([hit])
    assert not _top_has_verified_quote([{"source_id": "other-source", "text": rec["quote"]}])
    assert not _top_has_verified_quote([{"source_id": rec["source"], "text": "an unrelated passage"}])


def test_bm25_initialization_streams_tokens_without_changing_scores(monkeypatch):
    import numpy as np
    import rank_bm25
    from orca.kbvec import retrieve
    original = rank_bm25.BM25Okapi
    docs = ['satellite management incident report', 'weather rain backhaul fault', 'battery power outage']
    expected = original([retrieve._tok(d) for d in docs]).get_scores(retrieve._tok('incident report'))
    seen = []
    def streamed(corpus):
        assert not isinstance(corpus, list), 'Do not retain tokens for the full corpus at once'
        seen.append(True)
        return original(corpus)
    monkeypatch.setattr(rank_bm25, 'BM25Okapi', streamed)
    monkeypatch.setattr(retrieve, '_idx', None)
    monkeypatch.setattr(retrieve.store, 'all_rows', lambda: {
        'ids': ['a', 'b', 'c'], 'documents': docs, 'metadatas': [{}, {}, {}]})
    idx = retrieve._index()
    np.testing.assert_array_equal(idx['bm25'].get_scores(retrieve._tok('incident report')), expected)
    assert seen == [True]
