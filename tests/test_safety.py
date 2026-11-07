"""Safety tests: the hard limits that must hold in code, not in prompts.

No LLM, no network. Mock and scripted agents only (``PolicyMockLLM``, ``ScriptedLLM``). The
knowledge base is loaded in memory; nothing here writes to ``kb/`` (a test asserts that).

Covered now:
    - execution needs a valid, unexpired, single-use approval token from the human commander;
    - an agent cannot execute another owner's playbook or act outside its own assets;
    - a foreign gateway (not in India) is refused even after approval (Authz Rule 60(1)(b));
    - an unverified KB record never yields COMPLIANT or VIOLATION;
    - a human-rejected gap (GAP-IN-05, GAP-IN-07) is never raised again, including via PB-05/PB-06;
    - the audit chain detects tampering;
    - made-up record ids and chunk ids are rejected as citations;
    - a mock scenario run does not write to kb/.

Not built yet (skipped with a reason): autonomy modes, kill switch, blast-radius cap.

The re-mintable token bug found here (8 Nov) is fixed in Mission 6; its test now passes.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from orca import kb as kbmod
from orca import rules
from orca.agents import (TOOLS, Agent, Coordinator, PolicyMockLLM, citations_in_text, load_agent_roles)
from orca.audit import GENESIS, AuditLog
from orca.llm import ScriptedLLM
from orca.protocol import Message, Protocol, check_citations, classify_citation
from orca.remediation import Refused, Remediation
from orca.world import INDIAN_GATEWAYS, World

ROOT = Path(__file__).resolve().parent.parent
KB_DIR = ROOT / "kb"
SCEN_DIR = ROOT / "scenarios"
NOW = "2026-11-10T19:30:00+05:30"
REJECTED_GAPS = ("GAP-IN-05-NO-BREACH-CLOCK-TODAY", "GAP-IN-07-NO-JOINT-PLAN")
SCEN_FILES = sorted(p.name for p in SCEN_DIR.glob("*.yaml"))


# ------------------------------------------------------------------ helpers
@pytest.fixture
def w(tmp_path):
    return World.new({"jurisdiction": "IN", "now": NOW}, tmp_path / "audit.jsonl")


def approve_plan(rem, caller, playbook, targets, params=None, pin="4321"):
    """Agent requests, human (commander) approves. Returns (plan, token)."""
    plan = rem.request_approval(caller, playbook, targets, params, "safety test")
    token = rem.approve(plan["hash"], "Charan Velavan", pin)
    return plan, token


def kinds(w):
    return [e["kind"] for e in w.audit.entries()]


def load_scenario(name):
    return yaml.safe_load((SCEN_DIR / name).read_text())


def merged_facts(scenario):
    """Scenario facts after every event, the way scenarios/check_scen.py merges them."""
    facts = {"jurisdiction": scenario.get("jurisdiction", "IN")}
    start = rules.parse_ts(scenario["start"])
    last_t = 0
    for e in scenario["events"]:
        for k, v in (e.get("facts") or {}).items():
            if isinstance(v, list):
                facts.setdefault(k, []).extend(v)
            elif isinstance(v, dict):
                facts.setdefault(k, {}).update(v)
            else:
                facts[k] = v
        last_t = max(last_t, e["t"])
    facts["now"] = (start + dt.timedelta(minutes=last_t)).isoformat()
    return facts


def tree_hashes(root: Path, skip=("vec_cache", "vec_snapshots", "staging", "manifest")) -> dict:
    """sha256 of every file under root, except caches and the pipeline folders (staging, manifest)
    that the download agents write to concurrently. Records, gaps and sources stay guarded."""
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and not any(part in skip for part in p.relative_to(root).parts[:-1]):
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


# ================================================================== approval tokens
def test_no_playbook_runs_without_a_token(w):
    rem = Remediation(w)
    rem.request_approval("satellite_operator", "PB-01", ["noc-vendor-7"], {}, "test")
    for bad in ("", "0" * 24, "not-a-token"):
        with pytest.raises(Refused, match="no valid one-time approval token"):
            rem.execute("satellite_operator", "PB-01", ["noc-vendor-7"], {}, bad)
    assert "executed" not in kinds(w) and "rolled_back" not in kinds(w)


def test_approved_token_is_single_use(w):
    rem = Remediation(w)
    plan, token = approve_plan(rem, "satellite_operator", "PB-01", ["noc-vendor-7"])
    assert rem.execute("satellite_operator", "PB-01", ["noc-vendor-7"], {}, token)["ok"]
    with pytest.raises(Refused, match="no valid one-time approval token"):
        rem.execute("satellite_operator", "PB-01", ["noc-vendor-7"], {}, token)


def test_token_is_bound_to_the_approved_plan(w):
    rem = Remediation(w)
    _, token = approve_plan(rem, "satellite_operator", "PB-01", ["noc-vendor-7"])
    with pytest.raises(Refused, match="plan hash does not match"):
        rem.execute("satellite_operator", "PB-01", ["another-account"], {}, token)
    assert "executed" not in kinds(w)


def test_expired_token_is_refused(w):
    rem = Remediation(w)
    _, token = approve_plan(rem, "satellite_operator", "PB-01", ["noc-vendor-7"])
    w.facts["now"] = "2026-11-10T20:05:00+05:30"       # 35 min later; default TTL is 30 min
    with pytest.raises(Refused, match="approval expired"):
        rem.execute("satellite_operator", "PB-01", ["noc-vendor-7"], {}, token)
    assert "executed" not in kinds(w)


def test_approval_needs_a_known_plan_and_a_pin(w):
    rem = Remediation(w)
    with pytest.raises(Refused, match="unknown plan"):
        rem.approve("f" * 64, "Charan Velavan", "4321")
    plan = rem.request_approval("satellite_operator", "PB-01", ["noc-vendor-7"], {}, "test")
    with pytest.raises(Refused, match="PIN"):
        rem.approve(plan["hash"], "Charan Velavan", "")


def test_agents_have_no_approve_tool(w):
    assert not {"approve", "reject", "decide_gap", "approve_plan"} & set(TOOLS)
    for role in load_agent_roles().values():
        assert "approve" not in role.tools and "reject" not in role.tools
    rem = Remediation(w)
    agent = Agent("satellite_operator", w, ScriptedLLM([]), rem)
    out = agent.call("approve", {"plan_hash": "x" * 64, "pin": "1", "rationale": "try"})
    assert "refused" in out


def test_agent_execute_without_token_is_refused_through_the_tool_path(w):
    rem = Remediation(w)
    agent = Agent("satellite_operator", w, ScriptedLLM([]), rem)
    agent.call("request_approval", {"playbook": "PB-01", "targets": ["noc-vendor-7"], "reason": "test",
                                    "rationale": "test"})
    out = agent.call("execute_playbook", {"playbook": "PB-01", "targets": ["noc-vendor-7"], "token": "",
                                          "rationale": "try without approval"})
    assert "refused" in out and "token" in out["refused"]
    assert "executed" not in kinds(w)


def at(w, minutes):
    """Move the facts clock to NOW + minutes."""
    w.facts["now"] = (dt.datetime.fromisoformat(NOW) + dt.timedelta(minutes=minutes)).isoformat()


def clean_route(w, site="CHN-02", path="B", gateway="GW-IN-2"):
    w.routes = {site: {path: {"gateway": gateway, "integrity": "verified"}}}


WARN = {"message": "Emulated satellite backhaul degraded; expect delays."}


def test_single_use_token_cannot_be_reminted(w):
    rem = Remediation(w)
    plan, token = approve_plan(rem, "satellite_operator", "PB-01", ["noc-vendor-7"])
    assert rem.execute("satellite_operator", "PB-01", ["noc-vendor-7"], {}, token)["ok"]
    with pytest.raises(Refused, match="already run"):             # same clock instant, same PIN
        rem.approve(plan["hash"], "Charan Velavan", "4321")
    with pytest.raises(Refused):
        rem.execute("satellite_operator", "PB-01", ["noc-vendor-7"], {}, token)


def test_each_approval_mints_a_new_token(w):
    rem = Remediation(w)
    plan = rem.request_approval("satellite_operator", "PB-01", ["noc-vendor-7"], {}, "t")
    assert rem.approve(plan["hash"], "Charan Velavan", "4321") != rem.approve(plan["hash"], "Charan Velavan", "4321")


# ------------------------------------------------------------------ Mission 6: two clocks
def test_token_clock_starts_at_approval(w):
    rem = Remediation(w)
    plan = rem.request_approval("satellite_operator", "PB-01", ["noc-vendor-7"], {}, "t")
    at(w, 25)                                       # human takes 25 min: request still fresh (30 min)
    token = rem.approve(plan["hash"], "Charan Velavan", "4321")
    at(w, 38)                                       # 13 min after approval, 38 after request: still valid
    assert rem.execute("satellite_operator", "PB-01", ["noc-vendor-7"], {}, token)["ok"]


def test_token_expires_15_min_after_approval(w):
    rem = Remediation(w)
    _, token = approve_plan(rem, "satellite_operator", "PB-01", ["noc-vendor-7"])
    at(w, 16)
    with pytest.raises(Refused, match="approval expired"):
        rem.execute("satellite_operator", "PB-01", ["noc-vendor-7"], {}, token)


def test_stale_request_cannot_be_approved(w):
    rem = Remediation(w)
    plan = rem.request_approval("satellite_operator", "PB-01", ["noc-vendor-7"], {}, "t")
    at(w, 31)
    with pytest.raises(Refused, match="stale"):
        rem.approve(plan["hash"], "Charan Velavan", "4321")


def test_configured_pin_is_checked(w):
    import hashlib
    rem = Remediation(w, pin_sha256=hashlib.sha256(b"2468").hexdigest())
    plan = rem.request_approval("satellite_operator", "PB-01", ["noc-vendor-7"], {}, "t")
    with pytest.raises(Refused, match="wrong PIN"):
        rem.approve(plan["hash"], "Charan Velavan", "4321")
    assert rem.approve(plan["hash"], "Charan Velavan", "2468")


# ------------------------------------------------------------------ Mission 6: autonomy modes
def test_autonomy_modes_gate_execution(w):
    rem = Remediation(w)
    clean_route(w)
    assert "auto_token" not in rem.request_approval("mobile_operator", "PB-10", ["CHN-01"], WARN, "t")  # MANUAL
    rem.set_mode("ASSISTED", "Charan Velavan", "4321", minutes=60)
    low = rem.request_approval("mobile_operator", "PB-10", ["CHN-01"], WARN, "t")
    assert low["mode"] == "ASSISTED" and low["auto_token"]
    assert rem.execute("mobile_operator", "PB-10", ["CHN-01"], WARN, low["auto_token"])["ok"]
    med = rem.request_approval("mobile_operator", "PB-06", ["CHN-02"], {"path": "B"}, "t")
    assert "auto_token" not in med                  # PB-06 is medium risk: ASSISTED asks the human
    rem.set_mode("AUTO", "Charan Velavan", "4321", minutes=60, sites=["CHN-02"])
    med = rem.request_approval("mobile_operator", "PB-06", ["CHN-02"], {"path": "B"}, "t2")
    assert med["mode"] == "AUTO" and rem.execute("mobile_operator", "PB-06", ["CHN-02"], {"path": "B"},
                                                 med["auto_token"])["ok"]
    assert any(e["kind"] == "approved" and e["actor"].startswith("autonomy:AUTO") for e in w.audit.entries())


def test_autonomy_scope_and_expiry(w):
    rem = Remediation(w)
    rem.set_mode("AUTO", "Charan Velavan", "4321", minutes=10, sites=["CHN-03"])
    assert rem.mode_for("PB-10", ["CHN-01"])[0] == "MANUAL"      # outside the granted sites
    assert rem.mode_for("PB-10", ["CHN-03"])[0] == "AUTO"
    at(w, 11)
    assert rem.mode_for("PB-10", ["CHN-03"])[0] == "MANUAL"      # grant expired


def test_auto_never_uses_a_foreign_gateway(w):
    rem = Remediation(w)
    clean_route(w, gateway="GW-XX")
    rem.set_mode("AUTO", "Charan Velavan", "4321", minutes=60)
    plan = rem.request_approval("mobile_operator", "PB-06", ["CHN-02"], {"path": "B"}, "t")
    assert "auto_token" not in plan and not plan["clone_test"]["passed"]


def test_auto_downgrades_on_m3_doubt(w):
    rem = Remediation(w)
    rem.set_mode("AUTO", "Charan Velavan", "4321", minutes=60)
    w.alerts.append({"source": "M3", "site": "CHN-02", "label": "abstain"})
    assert rem.mode_for("PB-06", ["CHN-02"])[0] == "ASSISTED"
    assert "autonomy_downgraded" in kinds(w)


def test_kill_switch_stops_execution(w):
    rem = Remediation(w)
    rem.set_mode("AUTO", "Charan Velavan", "4321", minutes=60)
    plan = rem.request_approval("mobile_operator", "PB-10", ["CHN-01"], WARN, "t")
    rem.kill("Charan Velavan", "4321", "operator saw something odd")
    with pytest.raises(Refused, match="kill switch"):
        rem.execute("mobile_operator", "PB-10", ["CHN-01"], WARN, plan["auto_token"])
    with pytest.raises(Refused, match="kill switch"):
        rem.approve(plan["hash"], "Charan Velavan", "4321")
    rem.release_kill("Charan Velavan", "4321")
    assert rem.mode_for("PB-10", ["CHN-01"])[0] == "MANUAL"      # grants must be set again
    with pytest.raises(Refused):                                   # the revoked token stays dead
        rem.execute("mobile_operator", "PB-10", ["CHN-01"], WARN, plan["auto_token"])


def test_blast_radius_cap(w):
    rem = Remediation(w)
    rem.set_mode("AUTO", "Charan Velavan", "4321", minutes=60)
    wide = rem.request_approval("mobile_operator", "PB-10", ["CHN-01", "CHN-02", "CHN-03"], WARN, "t")
    assert "auto_token" not in wide and "autonomy_blocked" in kinds(w)
    for i in range(6):                              # rate limit: 6 executions per 10 min, any mode
        p = rem.request_approval("mobile_operator", "PB-10", ["CHN-01"], {"message": f"w{i}"}, "t")
        rem.execute("mobile_operator", "PB-10", ["CHN-01"], {"message": f"w{i}"}, p["auto_token"])
    p = rem.request_approval("mobile_operator", "PB-10", ["CHN-01"], {"message": "w7"}, "t")
    with pytest.raises(Refused, match="rate limit"):
        rem.execute("mobile_operator", "PB-10", ["CHN-01"], {"message": "w7"}, p["auto_token"])


def test_agent_cannot_execute_another_owners_playbook(w):
    rem = Remediation(w)
    _, token = approve_plan(rem, "satellite_operator", "PB-01", ["noc-vendor-7"])
    with pytest.raises(Refused, match="owned by satellite_operator, not mobile_operator"):
        rem.execute("mobile_operator", "PB-01", ["noc-vendor-7"], {}, token)
    agent = Agent("mobile_operator", w, ScriptedLLM([]), rem)
    out = agent.call("execute_playbook", {"playbook": "PB-01", "targets": ["noc-vendor-7"], "token": token,
                                          "rationale": "take over"})
    assert "refused" in out
    assert "executed" not in kinds(w)


def test_agent_cannot_act_outside_its_own_assets(w):
    rem = Remediation(w)
    with pytest.raises(Refused, match="not in mobile_operator's assets"):
        rem.request_approval("mobile_operator", "PB-06", ["CHN-99"], {"path": "P-FO"}, "test")


def _gateway_world(w, gateway, integrity="verified"):
    w.routes = {"CHN-01": {"P-FO": {"gateway": gateway, "integrity": integrity}}}
    return w


def test_foreign_gateway_is_refused_even_after_approval(w):
    _gateway_world(w, "GW-XX")
    rem = Remediation(w)
    plan, token = approve_plan(rem, "mobile_operator", "PB-06", ["CHN-01"], {"path": "P-FO"})
    assert plan["clone_test"]["passed"] is False and "GW-XX" in plan["clone_test"]["detail"]
    with pytest.raises(Refused, match="outside India"):
        rem.execute("mobile_operator", "PB-06", ["CHN-01"], {"path": "P-FO"}, token)
    assert "P-FO" not in w.active_path.values() and "CHN-01" not in w.active_path
    assert "execute_refused" in kinds(w) and "executed" not in kinds(w)


def test_positive_control_indian_gateway_fails_over(w):
    """The same plan with an Indian gateway passes. Shows the refusal above is the gateway check."""
    assert "GW-IN-1" in INDIAN_GATEWAYS
    _gateway_world(w, "GW-IN-1")
    rem = Remediation(w)
    _, token = approve_plan(rem, "mobile_operator", "PB-06", ["CHN-01"], {"path": "P-FO"})
    assert rem.execute("mobile_operator", "PB-06", ["CHN-01"], {"path": "P-FO"}, token)["ok"]
    assert w.active_path["CHN-01"] == "P-FO"


def test_failover_refused_when_backup_path_is_not_verified_clean(w):
    _gateway_world(w, "GW-IN-1", integrity="unknown")
    rem = Remediation(w)
    plan, token = approve_plan(rem, "mobile_operator", "PB-06", ["CHN-01"], {"path": "P-FO"})
    assert plan["clone_test"]["passed"] is False
    with pytest.raises(Refused, match="clone test failed"):
        rem.execute("mobile_operator", "PB-06", ["CHN-01"], {"path": "P-FO"}, token)


# ================================================================== knowledge base guards
def _unverified_kb():
    kb = kbmod.load()
    for r in kb.records.values():
        r["verified"] = False           # in memory only; kb/ on disk is not touched
    return kb


def _all_deadline_facts():
    """Facts that start every deadline clock and report late, so VIOLATION would appear if allowed."""
    rules_ = rules.load_rules("IN")
    applies = [x["record"] for x in rules_["deadline_rules"]]
    t0 = "2026-11-10T10:00:00+05:30"
    return {"jurisdiction": "IN", "now": "2026-11-12T12:00:00+05:30", "on": "2026-11-10",
            "applies": applies,
            "triggers": {"occurrence": t0, "noticing": t0, "awareness": t0},
            "reports": [{"record": rid, "sent_at": "2026-11-12T11:00:00+05:30"} for rid in applies]}


def test_positive_control_verified_kb_does_produce_violations():
    """Without this, the unverified-record test below could pass for the wrong reason."""
    vs = rules.evaluate(_all_deadline_facts(), kbmod.load())
    assert any(v.verdict == "VIOLATION" for v in vs)


def test_unverified_record_never_yields_compliant_or_violation():
    vs = rules.evaluate(_all_deadline_facts(), _unverified_kb())
    assert vs, "expected at least one verdict"
    assert not [v for v in vs if v.verdict in ("COMPLIANT", "VIOLATION")]


@pytest.mark.parametrize("name", SCEN_FILES)
def test_scenario_verdicts_cite_only_verified_records(name):
    """For every scenario, COMPLIANT/VIOLATION only ever cite verified records."""
    kb = kbmod.load()
    facts = merged_facts(load_scenario(name))
    for v in rules.evaluate(facts, kb):
        if v.verdict in ("COMPLIANT", "VIOLATION"):
            assert all(kb.records[r]["verified"] for r in v.record_ids), (name, v.rule_id, v.record_ids)


@pytest.mark.parametrize("name", SCEN_FILES)
def test_unverified_kb_gives_no_compliant_or_violation_in_any_scenario(name):
    facts = merged_facts(load_scenario(name))
    vs = rules.evaluate(facts, _unverified_kb())
    assert not [v for v in vs if v.verdict in ("COMPLIANT", "VIOLATION")], name


def test_rejected_gaps_are_recorded_as_rejected_by_a_human():
    kb = kbmod.load()
    for gid in REJECTED_GAPS:
        g = kb.gaps[gid]
        assert g["status"] == "rejected" and g.get("verified_by"), gid


def test_rejected_gap_citation_is_refused():
    kb = kbmod.load()
    for gid in REJECTED_GAPS:
        assert classify_citation(gid, kb) is None
        assert gid in check_citations([gid], kb)[1]


@pytest.mark.parametrize("topic", ["joint_command", "personal_data_breach"])
def test_rejected_gap_topic_is_never_raised_as_gap(topic):
    kb = kbmod.load()
    gid, _ = rules.find_gap(kb, topic, "IN")
    assert gid not in REJECTED_GAPS
    facts = {"jurisdiction": "IN", "now": NOW, "on": "2026-11-10",
             "obligation_questions": [{"id": f"Q-{topic}", "topic": topic, "text": topic}]}
    for v in rules.evaluate(facts, kb):
        assert v.gap_id not in REJECTED_GAPS, (v.rule_id, v.gap_id)


def _pb05_pb06(targets=("CHN-01",)):
    return {"jurisdiction": "IN", "now": NOW, "on": "2026-11-10", "proposed_actions": [
        {"playbook": "PB-05", "agent": "satellite_operator", "targets": list(targets),
         "supporting_records": ["IN-CERTIN-DIR-2022-ANX1-ii"]},
        {"playbook": "PB-06", "agent": "mobile_operator", "targets": list(targets),
         "supporting_records": ["IN-CERTIN-DIR-2022-ANX1-ii"]}]}


def test_pb05_pb06_conflict_still_shown_but_rejected_gap_not_raised():
    vs = [v for v in rules.evaluate(_pb05_pb06(), kbmod.load()) if v.verdict == "CONFLICT"]
    assert len(vs) == 1
    assert vs[0].gap_id is None
    assert any("GAP-IN-07-NO-JOINT-PLAN" in n for n in vs[0].notes)


def test_pb05_pb06_conflict_raises_gap_when_gap_is_not_rejected():
    """Positive control: with GAP-IN-07 not rejected, the same conflict cites it."""
    kb = kbmod.load()
    kb.gaps["GAP-IN-07-NO-JOINT-PLAN"]["status"] = "candidate"     # in memory only
    vs = [v for v in rules.evaluate(_pb05_pb06(), kb) if v.verdict == "CONFLICT"]
    assert vs and vs[0].gap_id == "GAP-IN-07-NO-JOINT-PLAN"


def test_no_scenario_raises_a_rejected_gap():
    kb = kbmod.load()
    for name in SCEN_FILES:
        for v in rules.evaluate(merged_facts(load_scenario(name)), kb):
            assert v.gap_id not in REJECTED_GAPS, (name, v.rule_id)


def test_rejected_gap_stays_out_of_s1_with_a_pb05_pb06_conflict():
    kb = kbmod.load()
    facts = merged_facts(load_scenario("s1.yaml"))
    facts["proposed_actions"] = _pb05_pb06(("CHN-01", "CHN-02"))["proposed_actions"]
    for v in rules.evaluate(facts, kb):
        assert v.gap_id not in REJECTED_GAPS, v.rule_id


# ================================================================== audit chain
def _audit_with(tmp_path, n=3):
    log = AuditLog(tmp_path / "chain.jsonl")
    for i in range(n):
        log.append("step", f"agent{i}", {"n": i, "text": f"entry {i}"}, ts=NOW)
    return log


def test_intact_audit_chain_verifies(tmp_path):
    log = _audit_with(tmp_path)
    assert log.verify() is None
    assert log.entries()[0]["prev_hash"] == GENESIS


def test_edited_audit_entry_fails_verification(tmp_path):
    log = _audit_with(tmp_path)
    lines = log.path.read_text().splitlines()
    e = json.loads(lines[1])
    e["payload"]["text"] = "entry 1, edited"          # hash left as it was
    lines[1] = json.dumps(e, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    log.path.write_text("\n".join(lines) + "\n")
    assert log.verify() == 2


def test_deleted_audit_entry_fails_verification(tmp_path):
    log = _audit_with(tmp_path)
    lines = log.path.read_text().splitlines()
    del lines[1]
    log.path.write_text("\n".join(lines) + "\n")
    assert log.verify() == 2


def test_reordered_audit_entries_fail_verification(tmp_path):
    log = _audit_with(tmp_path)
    lines = log.path.read_text().splitlines()
    lines[1], lines[2] = lines[2], lines[1]
    log.path.write_text("\n".join(lines) + "\n")
    assert log.verify() == 2


def test_unparseable_audit_line_fails_verification(tmp_path):
    log = _audit_with(tmp_path)
    lines = log.path.read_text().splitlines()
    lines[2] = lines[2][:-5]                          # truncated JSON
    log.path.write_text("\n".join(lines) + "\n")
    assert log.verify() == 3


def test_tampering_with_an_approval_is_detected_in_a_real_run(w):
    rem = Remediation(w)
    approve_plan(rem, "satellite_operator", "PB-01", ["noc-vendor-7"])
    assert w.audit.verify() is None
    lines = w.audit.path.read_text().splitlines()
    idx = next(i for i, l in enumerate(lines) if '"kind":"approved"' in l)
    e = json.loads(lines[idx])
    e["actor"] = "human:someone-else"
    lines[idx] = json.dumps(e, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    w.audit.path.write_text("\n".join(lines) + "\n")
    assert w.audit.verify() == e["seq"]


# ================================================================== citations
def test_made_up_record_id_is_rejected():
    kb = kbmod.load()
    fake = "IN-MADEUP-2026-X-99"
    assert classify_citation(fake, kb) is None
    assert fake in check_citations([fake], kb)[1]


def test_real_record_id_is_accepted():
    kb = kbmod.load()
    assert "IN-CERTIN-DIR-2022-ii" in kb.records
    assert classify_citation("IN-CERTIN-DIR-2022-ii", kb) == "record"


@pytest.mark.parametrize("chunk", ["cert-in-direction-2022:p9:c99", "dot-sop-2017:p1:c1"])
def test_made_up_chunk_id_is_rejected(chunk):
    kb = kbmod.load()
    assert classify_citation(chunk, kb) is None
    acc, rej = citations_in_text(f"As stated in {chunk}, report within six hours.", kb)
    assert chunk in rej and chunk not in acc


def test_agent_text_with_made_up_ids_is_flagged():
    kb = kbmod.load()
    acc, rej = citations_in_text("Cite IN-MADEUP-2026-X-99 and cert-in-direction-2022:p9:c99.", kb)
    assert not acc and set(rej) == {"IN-MADEUP-2026-X-99", "cert-in-direction-2022:p9:c99"}


def test_protocol_rejects_message_that_cites_an_invented_id(w):
    rem = Remediation(w)
    proto = Protocol(w, load_agent_roles(), rem)
    res = proto.send(Message(type="inform", sender="satellite_operator", recipients=["cert_in"],
                             text="Incident per IN-MADEUP-2026-X-99 needs reporting."))
    assert "rejected" in res and "IN-MADEUP-2026-X-99" in res["rejected"]
    assert "msg_rejected" in kinds(w) and "msg_sent" not in kinds(w)


def test_protocol_rejects_message_that_cites_an_invented_chunk(w):
    rem = Remediation(w)
    proto = Protocol(w, load_agent_roles(), rem)
    res = proto.send(Message(type="inform", sender="satellite_operator", recipients=["cert_in"],
                             text="See cert-in-direction-2022:p9:c99 for the deadline."))
    assert "rejected" in res and "cert-in-direction-2022:p9:c99" in res["rejected"]


# ================================================================== kb/ is read-only during a run
@pytest.mark.parametrize("name", SCEN_FILES)
def test_mock_scenario_run_does_not_write_kb(name, tmp_path):
    before = tree_hashes(KB_DIR)
    scenario = load_scenario(name)
    world = World.new({"jurisdiction": scenario.get("jurisdiction", "IN"), "now": scenario["start"]},
                      tmp_path / "audit.jsonl")
    Coordinator(world, PolicyMockLLM()).run(scenario)
    assert world.audit.entries(), "the run wrote no audit entries"
    assert tree_hashes(KB_DIR) == before, f"{name} changed files under kb/"
