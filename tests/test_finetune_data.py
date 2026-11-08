"""Checks for the fine-tune data (finetune/data/*.jsonl, stats.json) against finetune/SCHEMA.md.

Run: python -m pytest -q tests/test_finetune_data.py
Set ORCA_FT_REBUILD_CHECK=1 to also rebuild the data into a temporary folder and compare it byte for byte
(slow: about two minutes).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
from collections import Counter
from pathlib import Path

import pytest
import yaml

from orca import agents as A
from orca import kb as kbmod
from orca import protocol as P

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "finetune" / "data"
TRAIN_SCEN = {"S0", "S1", "S2", "S3", "N1", "N2", "N3"}
TEST_SCEN = {"N4", "N5", "CAP"}
TAGS = {"tool_choice", "filter_source", "approval_first", "no_token_refuse", "cite_kb", "insufficient_evidence",
        "refuse_out_of_scope", "ask_owner", "share_limits", "final_format"}
AGENT_ROLES = set(A.agent_roles())
VERDICT_WORDS = sorted(A.VERDICT_WORDS)
MAX_CHARS = 24000   # about 7,000 tokens: inside the 8192-token training length


def _load(name: str) -> list[dict]:
    path = DATA / name
    if not path.exists():
        pytest.skip(f"{path} not built yet: run python finetune/make_data.py")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.fixture(scope="module")
def train():
    return _load("train.jsonl")


@pytest.fixture(scope="module")
def test_rows():
    return _load("test.jsonl")


@pytest.fixture(scope="module")
def cases():
    return _load("cases.jsonl")


@pytest.fixture(scope="module")
def stats():
    path = DATA / "stats.json"
    if not path.exists():
        pytest.skip("stats.json not built yet")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def kb():
    return kbmod.load()


def known_ids(kb) -> set[str]:
    rules = P.rule_ids()
    gaps = {g for g, v in kb.gaps.items() if v.get("status") != "rejected"}
    return set(kb.records) | gaps | rules


def tool_outputs(msgs: list[dict]) -> dict[str, dict]:
    """tool_call_id -> parsed tool output."""
    return {m["tool_call_id"]: json.loads(m["content"]) for m in msgs if m["role"] == "tool"}


# ----------------------------------------------------------------------------- format and roles
def test_every_line_is_a_valid_conversation(train, test_rows):
    for row in train + test_rows:
        assert set(row) >= {"id", "scenario", "role", "split", "tags", "tools", "messages"}, row.get("id")
        assert row["role"] in AGENT_ROLES, row["id"]
        assert row["tags"] and set(row["tags"]) <= TAGS, row["id"]
        assert row["messages"][0]["role"] == "system" and row["messages"][1]["role"] == "user", row["id"]
        assert row["messages"][1]["content"].startswith("Scenario clock: "), row["id"]
        assert "Task: [EV-" in row["messages"][1]["content"], row["id"]
        assert row["messages"][-1]["role"] == "assistant" and not row["messages"][-1].get("tool_calls"), row["id"]


def test_split_labels_match_files(train, test_rows):
    assert all(r["split"] == "train" for r in train)
    assert all(r["split"] == "test" for r in test_rows)


def test_system_and_tools_come_from_the_frozen_role_files(train, test_rows):
    roles = {n: A.Role.load(n) for n in AGENT_ROLES}
    for row in train + test_rows:
        role = roles[row["role"]]
        assert row["messages"][0]["content"] == role.system_prompt(), row["id"]
        assert row["tools"] == role.tool_schemas(), row["id"]


def test_frozen_prompts_are_what_the_data_was_built_from(stats):
    h = hashlib.sha256()
    for p in sorted((ROOT / "agents" / "roles").glob("*.yaml")):
        h.update(p.name.encode() + p.read_bytes())
    assert stats["roles_sha256"] == h.hexdigest(), "role files changed since the data was built: re-run make_data.py"


def test_tool_calls_use_only_the_roles_tools_and_parse(train, test_rows):
    for row in train + test_rows:
        allowed = set(A.Role.load(row["role"]).tools)
        call_ids = set()
        for m in row["messages"]:
            for tc in m.get("tool_calls") or []:
                assert tc["type"] == "function", row["id"]
                name = tc["function"]["name"]
                assert name in allowed, f"{row['id']}: {name} is not in {row['role']}'s allow-list"
                args = json.loads(tc["function"]["arguments"])   # arguments are a JSON string
                assert isinstance(args, dict), row["id"]
                assert str(args.get("rationale", "")).strip(), f"{row['id']}: {name} has no rationale"
                call_ids.add(tc["id"])
        answered = {m["tool_call_id"] for m in row["messages"] if m["role"] == "tool"}
        assert answered == call_ids, row["id"]
        for m in row["messages"]:
            if m["role"] == "tool":
                json.loads(m["content"])   # tool output is a JSON string


def test_no_execute_playbook_without_a_commander_token(train, test_rows):
    for row in train + test_rows:
        msgs = row["messages"]
        for k, m in enumerate(msgs):
            for tc in m.get("tool_calls") or []:
                if tc["function"]["name"] != "execute_playbook":
                    continue
                token = json.loads(tc["function"]["arguments"])["token"]
                earlier = [x["content"] or "" for x in msgs[:k] if x["role"] in ("user", "tool")]
                from_commander = [c for c in earlier if token in c and "commander" in c and "One-time token" in c]
                assert from_commander, f"{row['id']}: execute_playbook with a token the commander never sent"


def test_executions_only_after_a_request_for_the_same_plan(train, test_rows):
    for row in train + test_rows:
        requested = {}
        for m in row["messages"]:
            for tc in m.get("tool_calls") or []:
                a = json.loads(tc["function"]["arguments"])
                if tc["function"]["name"] == "request_approval":
                    requested[a["playbook"]] = sorted(a["targets"])
                if tc["function"]["name"] == "execute_playbook":
                    assert requested.get(a["playbook"]) == sorted(a["targets"]), row["id"]


# ----------------------------------------------------------------------------- citations and verdicts
def test_citations_exist_in_the_knowledge_base(train, test_rows, kb):
    known = known_ids(kb)
    for row in train + test_rows:
        final = row["messages"][-1]["content"]
        assert "Citations:" in final and "Human decision needed:" in final, row["id"]
        line = re.search(r"^Citations: (.*)$", final, re.M).group(1)
        cited = [c.strip() for c in line.split(",") if c.strip() and c.strip() != "none"]
        for cid in cited:
            assert cid in known, f"{row['id']}: citation {cid} is not a KB record, gap or rule"
        for found in P.ID_RE.findall(final):
            assert found in known, f"{row['id']}: {found} in the answer is not in the KB"


def test_citations_were_returned_by_a_tool(train, test_rows, kb):
    known_ids_cache = known_ids(kb)
    for row in train + test_rows:
        outs = tool_outputs(row["messages"])
        blob = json.dumps(list(outs.values()), ensure_ascii=False)
        returned = {x for x in known_ids_cache if x in blob}
        final = row["messages"][-1]["content"]
        line = re.search(r"^Citations: (.*)$", final, re.M).group(1)
        for cid in [c.strip() for c in line.split(",") if c.strip() and c.strip() != "none"]:
            assert cid in returned, f"{row['id']}: {cid} was never returned by a tool"


def test_verdicts_in_answers_come_from_the_rule_engine(train, test_rows):
    for row in train + test_rows:
        final = row["messages"][-1]["content"]
        engine_called = any(tc["function"]["name"] == "run_rule_engine"
                            for m in row["messages"] for tc in (m.get("tool_calls") or []))
        for v in VERDICT_WORDS:
            if re.search(rf"\b{v}\b", final):
                assert engine_called, f"{row['id']}: verdict {v} stated without run_rule_engine"


def test_final_answers_are_short_plain_text(train, test_rows):
    for row in train + test_rows:
        assert len(row["messages"][-1]["content"]) < 1200, row["id"]
        assert "```" not in row["messages"][-1]["content"], row["id"]


def test_rows_fit_the_training_length(train, test_rows):
    for row in train + test_rows:
        assert len(json.dumps(row, ensure_ascii=False)) < MAX_CHARS, row["id"]


# ----------------------------------------------------------------------------- split and leakage
def test_train_has_only_training_scenarios(train):
    assert {r["scenario"] for r in train} <= TRAIN_SCEN


def test_no_test_scenario_ids_in_train(train):
    blob = "\n".join(json.dumps(r, ensure_ascii=False) for r in train)
    assert not re.search(r"EV-(N4|N5|CAP)-", blob)
    assert not re.search(r'"scenario": "(N4|N5|CAP)"', blob)


def test_no_test_scenario_sentence_in_train(train):
    texts = set()
    for sid in TEST_SCEN:
        sc = yaml.safe_load((ROOT / "scenarios" / f"{sid.lower()}.yaml").read_text())
        texts |= {e["what"] for e in sc["events"] if e.get("what")}
    for row in train:
        task = row["messages"][1]["content"]
        for t in texts:
            assert t not in task, f"{row['id']}: a sentence written for a held-out scenario is in the training task"


def test_held_out_scenarios_only_in_test_and_cases(test_rows, cases):
    assert {r["scenario"] for r in test_rows} <= TEST_SCEN
    assert {c["scenario"] for c in cases} <= TEST_SCEN


def test_no_conversation_id_is_shared_between_splits(train, test_rows):
    assert not {r["id"] for r in train} & {r["id"] for r in test_rows}


# ----------------------------------------------------------------------------- mix and coverage
def test_target_mix_in_train(train):
    n = len(train)
    refusal = sum(1 for r in train if {"no_token_refuse", "insufficient_evidence", "refuse_out_of_scope",
                                       "share_limits"} & set(r["tags"]))
    no_token = sum(1 for r in train if "no_token_refuse" in r["tags"])
    assert refusal / n >= 0.15
    assert no_token / n >= 0.10


def test_every_agent_role_is_in_train(train):
    assert {r["role"] for r in train} == AGENT_ROLES


def test_cases_are_well_formed(cases):
    for c in cases:
        exp = c["expect"]
        assert "execute_playbook" in exp["never_tools"], c["id"]
        assert exp["final_must_contain"] == ["Citations:", "Human decision needed:"], c["id"]
        assert c["messages"][0]["role"] == "system" and c["messages"][1]["role"] == "user", c["id"]
        assert c["messages"][-1]["role"] in ("user", "tool"), c["id"]   # the case stops before the next decision
        if exp.get("first_tool") is not None:
            assert exp["first_tool"] in A.Role.load(c["role"]).tools, c["id"]
            assert exp["first_tool"] not in exp["never_tools"], c["id"]


def test_stats_match_the_files(stats, train, test_rows, cases):
    assert stats["counts"] == {"train": len(train), "test": len(test_rows), "cases": len(cases)}
    assert stats["train"]["by_role"] == dict(sorted(Counter(r["role"] for r in train).items()))


def test_stats_splits_listed(stats):
    assert set(stats["split"]["train"]) == TRAIN_SCEN
    assert set(stats["split"]["test_and_cases"]) == TEST_SCEN


# ----------------------------------------------------------------------------- determinism (opt-in)
@pytest.mark.skipif(os.environ.get("ORCA_FT_REBUILD_CHECK") != "1", reason="slow: set ORCA_FT_REBUILD_CHECK=1")
def test_rebuild_is_byte_identical(tmp_path):
    spec = importlib.util.spec_from_file_location("make_data", ROOT / "finetune" / "make_data.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.build(out_dir=tmp_path / "out", tmp_root=tmp_path / "work")
    for name in ("train.jsonl", "test.jsonl", "cases.jsonl", "stats.json"):
        assert (tmp_path / "out" / name).read_bytes() == (DATA / name).read_bytes(), name
