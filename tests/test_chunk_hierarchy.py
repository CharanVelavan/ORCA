"""Unit tests for legal hierarchy parser (RAG v3 Phase 2 item 6).

Verifies levels: Rule/Section/Article/Direction/Regulation N > (1) > (a) > (i),
correct kind labels (Rules are "Rule", not "s."),
canonical clause_paths like "Rule 7(1)(a)",
and verification on in-tcsr-2024, in-ctir-2024, in-dpdp-act-2023, and CERT-In Directions.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from orca.kbvec import chunk, config, ingest


def test_tcsr_2024_rule_7_1_a_exists():
    """Verify Rule 7(1)(a) exists in in-tcsr-2024."""
    src = next(s for s in ingest.official_sources() if s["source_id"] == "in-tcsr-2024")
    chunks = ingest.v2_source_chunks(src)
    r7_chunks = [c for c in chunks if c["meta"].get("clause_path") == "Rule 7(1)(a)"]
    assert len(r7_chunks) >= 1, "Rule 7(1)(a) must exist in in-tcsr-2024"
    c = r7_chunks[0]
    assert c["meta"]["source_id"] == "in-tcsr-2024"
    assert c["meta"]["clause"] == "Rule 7(1)(a)"
    assert c["meta"]["parent_id"] == "in-tcsr-2024:s:rule-7"
    assert re.match(r"^in-tcsr-2024:p\d+:c\d+$", c["id"])
    assert "within six hours" in c["text"]
    assert "Rule 7(1)(a)" in c["text"].split("\n")[0]   # in breadcrumb header


def test_ctir_2024_rule_7_1_j_exists():
    """Verify Rule 7(1)(j) exists in in-ctir-2024."""
    src = next(s for s in ingest.official_sources() if s["source_id"] == "in-ctir-2024")
    chunks = ingest.v2_source_chunks(src)
    r7_chunks = [c for c in chunks if c["meta"].get("clause_path") == "Rule 7(1)(j)"]
    assert len(r7_chunks) >= 1, "Rule 7(1)(j) must exist in in-ctir-2024"
    c = r7_chunks[0]
    assert c["meta"]["source_id"] == "in-ctir-2024"
    assert c["meta"]["clause"] == "Rule 7(1)(j)"
    assert c["meta"]["parent_id"] == "in-ctir-2024:s:rule-7"
    assert re.match(r"^in-ctir-2024:p\d+:c\d+$", c["id"])
    assert "intimation of security incident" in c["text"]
    assert "Rule 7(1)(j)" in c["text"].split("\n")[0]


def test_dpdp_act_section_8_6_exists():
    """Verify Section 8(6) exists in in-dpdp-act-2023."""
    src = next(s for s in ingest.official_sources() if s["source_id"] == "in-dpdp-act-2023")
    chunks = ingest.v2_source_chunks(src)
    s8_chunks = [c for c in chunks if c["meta"].get("clause_path") == "Section 8(6)"]
    assert len(s8_chunks) >= 1, "Section 8(6) must exist in in-dpdp-act-2023"
    c = s8_chunks[0]
    assert c["meta"]["source_id"] == "in-dpdp-act-2023"
    assert c["meta"]["clause"] == "Section 8(6)"
    assert c["meta"]["parent_id"] == "in-dpdp-act-2023:s:section-8"
    assert re.match(r"^in-dpdp-act-2023:p\d+:c\d+$", c["id"])
    assert "personal data breach" in c["text"]
    assert "Section 8(6)" in c["text"].split("\n")[0]


def test_certin_directions_and_annexure_items():
    """Verify Direction (ii)/(iii)/(iv) and Annexure I items exist in CERT-In Directions."""
    src = next(s for s in ingest.official_sources() if s["source_id"] == "in-certin-dir-2022")
    chunks = ingest.v2_source_chunks(src)
    clauses = {c["meta"].get("clause_path") for c in chunks}
    assert "Direction (ii)" in clauses
    assert "Direction (iii)" in clauses
    assert "Direction (iv)" in clauses
    assert "Annexure I, item (ix)" in clauses
    ix_chunk = next(c for c in chunks if c["meta"].get("clause_path") == "Annexure I, item (ix)")
    assert ix_chunk["meta"]["parent_id"] == "in-certin-dir-2022:s:annexure-i"
    assert "Attacks on Critical infrastructure" in ix_chunk["text"]


def test_hierarchy_level_nesting_and_kind_labels():
    """Verify level progression: Rule/Section N > (1) > (a) > (i) and kind labels."""
    sample = (
        "7. Reporting Obligations. — (1) An operator shall comply with: —\n"
        "    (a) notify incidents within six hours with details;\n"
        "    (b) submit detailed report within 24 hours including: —\n"
        "        (i) affected subscribers count;\n"
        "        (ii) duration and scope;\n"
        "(2) The regulator may publish advisory.\n"
    )
    chunks_rule, last = chunk.chunk_page(sample, doc_type="rules")
    rule_labels = [c["clause"] for c in chunks_rule]
    assert "Rule 7(1)" in rule_labels
    assert "Rule 7(1)(a)" in rule_labels
    assert "Rule 7(1)(b)" in rule_labels
    assert "Rule 7(1)(b)(i)" in rule_labels
    assert "Rule 7(1)(b)(ii)" in rule_labels
    assert "Rule 7(2)" in rule_labels
    assert not any(c.startswith("s.") for c in rule_labels)

    # Act document uses Section
    chunks_act, _ = chunk.chunk_page(sample, doc_type="act")
    act_labels = [c["clause"] for c in chunks_act]
    assert "Section 7(1)(a)" in act_labels
    assert not any(c.startswith("s.") for c in act_labels)
