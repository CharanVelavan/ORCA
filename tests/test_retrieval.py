"""Retrieval tests for orca.kbvec.

Unit tests (chunking, filters, cache keys, question file) always run. The retrieval-quality test needs a
built index and a reachable embedder, so it skips otherwise. Build with `python -m orca.kbvec ingest`.
"""
from __future__ import annotations

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


def test_chunker_splits_on_headings_and_windows_long_text():
    text = "Rule 7. Reporting\n" + "alpha " * 100 + "\nRule 8. Logs\n" + "beta " * 100
    chunks, last = chunk.chunk_page(text)
    assert [c["clause"] for c in chunks] == ["Rule 7", "Rule 8"] and last == "Rule 8"
    long, _ = chunk.chunk_page("word " * 1000)
    assert len(long) > 1 and all(len(c["text"].split()) <= chunk.MAX_WORDS for c in long)


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
    assert hits and set(hits[0]) == {"chunk_id", "text", "source_id", "title", "jurisdiction",
                                     "binding_status", "page", "clause", "url", "tier", "score"}
    assert get_chunk("IN-CERTIN-DIR-2022-ii")["tier"] == "verified"
    assert get_chunk("no-such-chunk") is None
    res = evaluate.run()
    print("\n" + evaluate.table(res))
    assert res["recall@5"] >= 0.6 and res["mrr"] >= 0.4      # floor, not the target; see docs/KBVEC.md
