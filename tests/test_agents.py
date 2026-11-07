"""Role agents with a mock LLM: isolation, tools, citations, approval, adviser, trace."""
import json
from pathlib import Path

import pytest
import yaml

from orca import agents as A
from orca.agents import (Agent, Commander, Coordinator, EventFeed, PolicyAdviser, PolicyMockLLM, Role,
                         load_agent_roles)
from orca.llm import ScriptedLLM, tool_call
from orca.protocol import Message, Protocol
from orca.remediation import Remediation, catalogue
from orca.world import World

ROOT = Path(__file__).resolve().parent.parent
NOW = "2026-11-10T19:30:00+05:30"
R = "because"   # rationale


def scen(name):
    return yaml.safe_load((ROOT / "scenarios" / f"{name}.yaml").read_text())


@pytest.fixture
def w(tmp_path):
    return World.new({"jurisdiction": "IN", "now": NOW}, tmp_path / "audit.jsonl")


def team(w, llm=None):
    rem = Remediation(w)
    proto = Protocol(w, load_agent_roles(), rem)
    adv = PolicyAdviser(w)
    mk = lambda role, l=llm: Agent(role, w, l or ScriptedLLM([]), rem, proto, adv)  # noqa: E731
    return rem, proto, mk


def steps(w, kind="agent_step"):
    return [e for e in w.audit.entries() if e["kind"] == kind]


# ------------------------------------------------------------------ role files
def test_role_files_load_and_are_consistent():
    roles = load_agent_roles()
    assert set(roles) == {"satellite_operator", "mobile_operator", "power_utility", "cert_in", "regulator",
                          "gap_analyst"}
    assert Role.load("policy_adviser").kind == "adviser" and Role.load("commander").kind == "human"
    cat = catalogue()
    for r in roles.values():
        assert r.mandate and r.reports_to and r.example, r.name
        assert all(A.LEVEL[t] <= r.max_level for t in r.tools)
        for pb in r.owns:
            assert cat[pb]["owner"] == r.name
        assert ("execute_playbook" in r.tools) == bool(r.owns)
    assert not {"execute_playbook", "select_playbook", "request_approval"} & set(roles["regulator"].tools)
    assert roles["cert_in"].sharing["may_direct"] and not roles["regulator"].sharing["may_propose_playbooks"]


def test_role_over_its_level_is_refused(tmp_path):
    (tmp_path / "bad.yaml").write_text(yaml.safe_dump({"name": "bad", "organisation": "x", "reports_to": "y",
                                                       "max_level": 1, "tools": ["execute_playbook"]}))
    with pytest.raises(ValueError, match="exceed max_level"):
        Role.load("bad", tmp_path)


# ------------------------------------------------------------------ tool isolation
@pytest.mark.parametrize("role", sorted(A.agent_roles()))
def test_llm_is_sent_only_the_roles_tools(w, role):
    llm = ScriptedLLM([{"content": "Nothing to do. Citations: none"}])
    _, _, mk = team(w, llm)
    mk(role).run("check in")
    sent = [t["function"]["name"] for t in llm.requests[0]["tools"]]
    assert sent == Role.load(role).tools
    for t in llm.requests[0]["tools"]:
        assert "rationale" in t["function"]["parameters"]["required"]


def test_tool_outside_allow_list_refused_and_logged(w):
    llm = ScriptedLLM([{"tool_calls": [tool_call("execute_playbook", {"playbook": "PB-06", "targets": ["CHN-02"],
                                                                       "token": "x", "rationale": R})]},
                       {"content": "Done."}])
    _, _, mk = team(w, llm)
    out = mk("regulator").run("fail over CHN-02")
    assert not out["tool_calls"][0]["ok"] and "allow-list" in out["tool_calls"][0]["refused"]
    assert steps(w)[0]["payload"]["result"]["refused"]


def test_missing_rationale_refused(w):
    _, _, mk = team(w)
    out = mk("cert_in").call("run_rule_engine", {})
    assert "rationale is required" in out["refused"]
    assert "verdicts" in mk("cert_in").call("run_rule_engine", {"rationale": R})


def test_proposal_naming_a_playbook_in_text_is_checked_against_its_owner(w):
    _, _, mk = team(w)
    ga = mk("gap_analyst")
    out = ga.call("send_message", {"to": ["cert_in"], "type": "propose", "text": "Propose PB-10 for CHN-02.",
                                   "rationale": R})
    assert "owned by mobile_operator" in out["refused"]
    assert ga.call("send_message", {"to": ["mobile_operator"], "type": "propose", "text": "Propose PB-10.",
                                    "rationale": R})["sent"]
    assert w.bus[-1]["playbook"] == "PB-10"


def test_send_message_enums_limited_by_role():
    sch = {t["function"]["name"]: t["function"]["parameters"] for t in Role.load("regulator").tool_schemas()}
    props = sch["send_message"]["properties"]
    assert "propose" not in props["type"]["enum"] and props["data_class"]["enum"] == ["operational"]
    assert "regulator" not in props["to"]["items"]["enum"] and "commander" in props["to"]["items"]["enum"]
    sat = {t["function"]["name"]: t["function"]["parameters"] for t in Role.load("satellite_operator").tool_schemas()}
    assert sat["request_approval"]["properties"]["playbook"]["enum"] == ["PB-01", "PB-02", "PB-03", "PB-04", "PB-05"]


# ------------------------------------------------------------------ information isolation
def test_events_released_only_to_their_roles(w):
    feed = EventFeed(scen("s1"), load_agent_roles())
    got = feed.release(w, 30)
    assert [a["t"] for a in got["satellite_operator"]] == [0, 4, 8, 18]
    assert [a["t"] for a in got["mobile_operator"]] == [24]
    assert [a["t"] for a in got["gap_analyst"]] == [12]
    assert [a["t"] for a in got["cert_in"]] == [30]
    assert "regulator" not in got and "power_utility" not in got
    assert w.facts["now"] == "2026-11-10T19:30:00+05:30" and w.facts["triggers"]["noticing"]
    assert not feed.release(w, 30)          # nothing released twice


def test_agent_never_sees_another_roles_events_or_messages(w):
    _, proto, mk = team(w)
    EventFeed(scen("s1"), load_agent_roles()).release(w, 24)
    proto.send(Message(type="inform", sender="satellite_operator", recipients=["cert_in"], text="Intrusion seen."))
    mob = mk("mobile_operator").call("read_alerts", {"source": "any", "rationale": R})
    assert {a["t"] for a in mob["alerts"]} == {24} and mob["messages_to_me"] == []
    sat_alert = next(a["id"] for a in w.alerts if a["t"] == 0)
    assert "refused" in mk("mobile_operator").call("explain_model", {"alert_id": sat_alert, "rationale": R})
    assert "explain" in mk("satellite_operator").call("explain_model", {"alert_id": sat_alert, "rationale": R})
    cert = mk("cert_in").call("read_alerts", {"rationale": R})
    assert cert["alerts"] == [] and [m["sender"] for m in cert["messages_to_me"]] == ["satellite_operator"]


def test_attacker_ground_truth_is_hidden(w):
    got = EventFeed(scen("n4"), load_agent_roles()).release(w, 0)
    a = got["satellite_operator"][0]
    assert "Attacker" not in a["detail"] and a["detail"].startswith("Signals observed")


def test_empty_filter_gives_a_hint(w):
    _, _, mk = team(w)
    EventFeed(scen("s1"), load_agent_roles()).release(w, 8)
    out = mk("satellite_operator").call("read_alerts", {"source": "M2", "rationale": R})
    assert out["alerts"] == [] and "source=any" in out["hint"]
    assert [a["label"] for a in mk("satellite_operator").call("read_alerts", {"source": "M3", "rationale": R})
            ["alerts"]] == ["attack-management-plane"]


# ------------------------------------------------------------------ citations
def test_fake_citation_in_final_answer_rejected_and_retried(w):
    llm = ScriptedLLM([{"content": "Report under IN-FAKE-2099-1. Citations: IN-FAKE-2099-1"},
                       {"content": "Report under IN-CERTIN-DIR-2022-ii. Citations: IN-CERTIN-DIR-2022-ii"}])
    _, _, mk = team(w, llm)
    out = mk("cert_in").run("which rule?")
    assert out["citations"] == {"accepted": ["IN-CERTIN-DIR-2022-ii"], "rejected": []}
    users = [m["content"] for m in out["messages"] if m["role"] == "user"]
    assert len(llm.requests) == 2 and "not in the knowledge base" in users[-1]
    first = steps(w)[0]["payload"]
    assert first["citations_rejected"] == ["IN-FAKE-2099-1"] and first["retry"]


def test_fake_citation_survives_only_as_rejected(w):
    llm = ScriptedLLM([{"content": "See IN-FAKE-2099-1."}, {"content": "Still IN-FAKE-2099-1."}])
    _, _, mk = team(w, llm)
    assert mk("cert_in").run("x")["citations"]["rejected"] == ["IN-FAKE-2099-1"]


def test_record_gap_evidence_checked_and_only_pre_confirmed(w):
    _, _, mk = team(w)
    ga = mk("gap_analyst")
    assert "rejected" in ga.call("record_gap", {"topic": "downstream_warning", "finding": "f",
                                                "evidence": ["IN-FAKE-1"], "rationale": R})["refused"]
    assert "a human rejected" in ga.call("record_gap", {"topic": "joint_command", "finding": "f",
                                                        "evidence": ["IN-TELACT-2023-20"], "rationale": R})["refused"]
    out = ga.call("record_gap", {"topic": "downstream_warning", "finding": "No duty to warn found.",
                                 "evidence": ["GAP-IN-02-NO-DOWNSTREAM-WARNING"], "rationale": R})
    assert out["status"] == "pre-confirmed" and "next" in out
    before = dict(w.kb.gaps["GAP-IN-02-NO-DOWNSTREAM-WARNING"])
    rem = Remediation(w)
    d = Commander(w, rem, Protocol(w, load_agent_roles(), rem)).decide_gap(out["draft_id"], "confirmed")
    assert d["status"] == "confirmed" and d["decided_by"] == "human:commander"
    assert w.kb.gaps["GAP-IN-02-NO-DOWNSTREAM-WARNING"] == before        # kb untouched


def test_draft_notice_flags_fake_citations(w):
    _, _, mk = team(w)
    out = mk("satellite_operator").call("draft_notice", {"kind": "certin_report", "recipient": "CERT-In",
                                                         "body": "Incident.", "citations": ["IN-CERTIN-DIR-2022-ii",
                                                                                            "IN-NOPE-1"],
                                                         "rationale": R})
    assert out["citations"] == ["IN-CERTIN-DIR-2022-ii"] and out["rejected_citations"] == ["IN-NOPE-1"]
    assert "refused" in mk("satellite_operator").call("draft_notice", {"kind": "dot_report", "recipient": "DoT",
                                                                       "body": "x", "rationale": R})


def test_verdict_not_from_engine_is_flagged(w):
    llm = ScriptedLLM([{"content": "The operator is COMPLIANT."}])
    _, _, mk = team(w, llm)
    assert mk("regulator").run("x")["verdicts_not_from_engine"] == ["COMPLIANT"]


# ------------------------------------------------------------------ nothing executes without approval
def _routes(w, gw="GW-IN-2"):
    w.routes = {"CHN-02": {"B": {"gateway": gw, "integrity": "verified"}}}


def test_execute_without_token_refused_with_hint(w):
    _routes(w)
    _, _, mk = team(w)
    out = mk("mobile_operator").call("execute_playbook", {"playbook": "PB-06", "targets": ["CHN-02"],
                                                          "params": {"path": "B"}, "token": "fake", "rationale": R})
    assert "token" in out["refused"] and "request_approval" in out["next"]
    assert w.active_path == {}


def test_request_then_execute_needs_the_human(w):
    _routes(w)
    rem, proto, mk = team(w)
    mob = mk("mobile_operator")
    req = mob.call("request_approval", {"playbook": "PB-06", "targets": ["CHN-02"], "params": {"path": "B"},
                                        "reason": "fail over", "rationale": R})
    assert req["clone_test"]["passed"] and "do not call execute_playbook" in req["next"].lower()
    assert w.bus[-1]["kind"] == "approve_request" and w.bus[-1]["to"] == ["commander"]
    args = {"playbook": "PB-06", "targets": ["CHN-02"], "params": {"path": "B"}, "rationale": R}
    assert "refused" in mob.call("execute_playbook", {**args, "token": req["hash"]})   # a hash is not a token
    assert w.active_path == {}
    token = Commander(w, rem, proto).approve(req["hash"], "1234")
    assert token in w.bus[-1]["payload"]["text"] and w.bus[-1]["to"] == ["mobile_operator"]
    assert "refused" in mk("satellite_operator").call("execute_playbook", {**args, "token": token})   # not owner
    out = mob.call("execute_playbook", {**args, "token": token})
    assert out["ok"] and w.active_path == {"CHN-02": "B"}
    assert "refused" in mob.call("execute_playbook", {**args, "token": token})                        # one-time


def test_foreign_gateway_blocked_even_when_approved(w):
    _routes(w, gw="GW-XX")
    rem, proto, mk = team(w)
    mob = mk("mobile_operator")
    req = mob.call("request_approval", {"playbook": "PB-06", "targets": ["CHN-02"], "params": {"path": "B"},
                                        "reason": "fail over", "rationale": R})
    assert not req["clone_test"]["passed"]
    token = Commander(w, rem, proto).approve(req["hash"], "1234")
    out = mob.call("execute_playbook", {"playbook": "PB-06", "targets": ["CHN-02"], "params": {"path": "B"},
                                        "token": token, "rationale": R})
    assert "outside India" in out["refused"] and w.active_path == {}


def test_cannot_request_approval_for_someone_elses_playbook(w):
    _, _, mk = team(w)
    out = mk("mobile_operator").call("request_approval", {"playbook": "PB-05", "targets": ["SAT-MGMT"],
                                                          "reason": "x", "rationale": R})
    assert "owned by satellite_operator" in out["refused"]


# ------------------------------------------------------------------ adviser
def test_adviser_answers_from_kb_with_citations(w):
    a = PolicyAdviser(w).ask("Within how many hours must a cyber incident be reported to CERT-In?")
    assert a["found"] and "IN-CERTIN-DIR-2022-ii" in a["citations"]
    assert all(w.kb.records.get(c) or w.kb.gaps.get(c) for c in a["citations"])


@pytest.mark.parametrize("q", ["What is the fine for jaywalking in Mumbai?", "What is the capital of France?",
                               "Who won the cricket world cup?"])
def test_adviser_refuses_beyond_the_kb(w, q):
    a = PolicyAdviser(w).ask(q)
    assert not a["found"] and a["citations"] == []
    assert a["answer"] == f"Not found in the sources we checked, as of {w.kb.as_of}."


def test_adviser_discards_llm_answers_with_bad_citations_or_verdicts(w):
    q = "Within how many hours must a cyber incident be reported to CERT-In?"
    for content in ['{"answer": "Six hours [IN-FAKE-1].", "citations": ["IN-FAKE-1"]}',
                    '{"answer": "You are COMPLIANT [IN-CERTIN-DIR-2022-ii].", "citations": ["IN-CERTIN-DIR-2022-ii"]}',
                    "Six hours, trust me."]:
        a = PolicyAdviser(w, ScriptedLLM([{"content": content}])).ask(q)
        assert a["mode"] == "quote" and "IN-FAKE-1" not in a["citations"]
    good = '{"answer": "Within six hours of noticing [IN-CERTIN-DIR-2022-ii].", "citations": ["IN-CERTIN-DIR-2022-ii"]}'
    assert PolicyAdviser(w, ScriptedLLM([{"content": good}])).ask(q)["mode"] == "llm"
    nf = PolicyAdviser(w, ScriptedLLM([{"content": "NOT_FOUND"}])).ask(q)
    assert nf["answer"].startswith("Not found in the sources we checked")


def test_agent_can_ask_the_adviser(w):
    _, _, mk = team(w)
    out = mk("power_utility").call("ask_adviser", {"question": "Is there a minimum battery backup duty for towers?",
                                                   "rationale": R})
    assert "answer" in out and out["kb_as_of"] == str(w.kb.as_of)
    assert any(e["kind"] == "adviser_answer" for e in w.audit.entries())


# ------------------------------------------------------------------ trace
def test_trace_logs_reasoning_rationale_and_citations(w):
    llm = ScriptedLLM([{"tool_calls": [tool_call("run_rule_engine", {"rationale": "need the clocks"})]},
                       {"content": "See GAP-IN-01-REPORTING-CLOCKS. Citations: GAP-IN-01-REPORTING-CLOCKS"}])
    real_chat = llm.chat
    llm.chat = lambda m, t=None: {**real_chat(m, t), "reasoning_content": "thinking about clocks"}
    _, _, mk = team(w, llm)
    mk("cert_in").run("clocks?")
    s = steps(w)
    assert s[0]["payload"]["tool"] == "run_rule_engine" and s[0]["payload"]["rationale"] == "need the clocks"
    assert s[0]["payload"]["reasoning"] == "thinking about clocks"
    assert s[-1]["payload"]["final"] and s[-1]["payload"]["citations_accepted"] == ["GAP-IN-01-REPORTING-CLOCKS"]
    assert w.audit.verify() is None
    assert "reasoning_content" not in json.dumps(llm.requests[1]["messages"])   # not echoed back to the model


def test_coordinator_runs_s1_with_mock_llm(w):
    w.facts = {"jurisdiction": "IN"}
    c = Coordinator(w, PolicyMockLLM())
    res = c.run(scen("s1"))
    assert res and not [r for r in res if r.get("error")]
    assert {r["role"] for r in res} == {"satellite_operator", "mobile_operator", "gap_analyst", "cert_in"}
    assert all(not r["citations"]["rejected"] and not r["tool_errors"] for r in res)
    cert = next(r for r in res if r["role"] == "cert_in")
    assert "GAP-IN-01-REPORTING-CLOCKS" in cert["citations"]["accepted"]
    assert w.audit.verify() is None
