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
