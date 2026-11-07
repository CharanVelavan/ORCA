"""Typed coordination protocol: every rule is enforced in code; violations are rejected and logged."""
import types

import pytest

from orca import protocol as P
from orca.agents import load_agent_roles
from orca.protocol import Message, Protocol
from orca.remediation import Remediation
from orca.world import World

NOW = "2026-11-10T19:30:00+05:30"


@pytest.fixture
def env(tmp_path):
    w = World.new({"jurisdiction": "IN", "now": NOW}, tmp_path / "audit.jsonl")
    rem = Remediation(w)
    return w, rem, Protocol(w, load_agent_roles(), rem)


def send(proto, **kw):
    kw.setdefault("text", "Status update.")
    return proto.send(Message(**kw))


def kinds(w):
    return [e["kind"] for e in w.audit.entries()]


def test_valid_inform_is_delivered_and_logged(env):
    w, _, proto = env
    r = send(proto, type="inform", sender="satellite_operator", recipients=["cert_in"],
             refs=["IN-CERTIN-DIR-2022-ii"])
    assert r == {"sent": True, "id": "MSG-0001"}
    assert w.bus[-1]["to"] == ["cert_in"] and w.bus[-1]["kind"] == "inform"
    assert kinds(w) == ["msg_sent"] and w.audit.verify() is None
    assert [m["id"] for m in proto.inbox("cert_in")] == ["MSG-0001"]
    assert proto.inbox("mobile_operator") == []


@pytest.mark.parametrize("kw, why", [
    (dict(type="shout", sender="cert_in", recipients=["regulator"]), "type must be"),
    (dict(type="inform", sender="hacker", recipients=["regulator"]), "unknown sender"),
    (dict(type="inform", sender="cert_in", recipients=["nobody"]), "unknown recipient"),
    (dict(type="inform", sender="cert_in", recipients=["cert_in"]), "own sender"),
    (dict(type="inform", sender="cert_in", recipients=[]), "at least one recipient"),
    (dict(type="inform", sender="cert_in", recipients=["regulator"], text="  "), "text is required"),
    (dict(type="propose", sender="regulator", recipients=["mobile_operator"], playbook="PB-06"), "may not send propose"),
    (dict(type="request", sender="power_utility", recipients=["mobile_operator"], data_class="customer_data"),
     "may not share customer_data"),
])
def test_malformed_or_unauthorised_messages_rejected(env, kw, why):
    w, _, proto = env
    r = send(proto, **kw)
    assert why in r["rejected"]
    assert w.bus == [] and kinds(w) == ["msg_rejected"]


def test_operator_cannot_push_customer_data_to_another_operator(env):
    w, _, proto = env
    r = send(proto, type="inform", sender="mobile_operator", recipients=["satellite_operator"],
             data_class="customer_data", text="Subscriber list for CHN-02.")
    assert "another operator" in r["rejected"]
    ok = send(proto, type="inform", sender="mobile_operator", recipients=["cert_in"], data_class="customer_data",
              text="Affected subscriber count for the incident report.")
    assert ok["sent"]


def test_personal_data_only_to_cert_in(env):
    _, _, proto = env
    r = send(proto, type="inform", sender="satellite_operator", recipients=["regulator"], data_class="personal_data")
    assert "only to cert_in" in r["rejected"]


def test_only_cert_in_can_direct_and_only_as_request(env):
    _, _, proto = env
    r = send(proto, type="request", sender="regulator", recipients=["mobile_operator"], data_class="legal_direction")
    assert "legal_direction" in r["rejected"]
    r = send(proto, type="inform", sender="cert_in", recipients=["mobile_operator"], data_class="legal_direction")
    assert "must be a request" in r["rejected"]
    r = send(proto, type="request", sender="cert_in", recipients=["mobile_operator", "satellite_operator"],
             data_class="legal_direction", text="Draft direction: preserve logs.", refs=["IN-CERTIN-DIR-2022-iv"])
    assert r["sent"]


def test_proposal_must_reach_the_playbook_owner(env):
    _, _, proto = env
    r = send(proto, type="propose", sender="gap_analyst", recipients=["cert_in"], playbook="PB-10")
    assert "owned by mobile_operator" in r["rejected"]
    r = send(proto, type="propose", sender="gap_analyst", recipients=["mobile_operator"], playbook="PB-99")
    assert "not in the playbook catalogue" in r["rejected"]
    assert send(proto, type="propose", sender="gap_analyst", recipients=["mobile_operator"], playbook="PB-10",
                text="Propose PB-10 for CHN-02 dependants.")["sent"]


def test_approve_request_needs_own_plan_and_goes_to_commander_only(env):
    w, rem, proto = env
    r = send(proto, type="approve_request", sender="satellite_operator", recipients=["commander"], refs=[])
    assert "plan hash you own" in r["rejected"]
    plan = rem.request_approval("satellite_operator", "PB-01", ["noc-vendor-7"], {}, "exposed account")
    r = send(proto, type="approve_request", sender="satellite_operator", recipients=["cert_in"], refs=[plan["hash"]])
    assert "commander only" in r["rejected"]
    r = send(proto, type="approve_request", sender="mobile_operator", recipients=["commander"], refs=[plan["hash"]])
    assert "rejected" in r          # not the plan owner
    assert send(proto, type="approve_request", sender="satellite_operator", recipients=["commander"],
                refs=[plan["hash"]])["sent"]


def test_refs_must_resolve_to_evidence_the_sender_may_see(env):
    w, _, proto = env
    w.alerts.append({"id": "EV-X-T000-0", "visible_to": ["satellite_operator"]})
    r = send(proto, type="inform", sender="mobile_operator", recipients=["cert_in"], refs=["EV-X-T000-0"])
    assert "does not resolve" in r["rejected"]
    assert send(proto, type="inform", sender="satellite_operator", recipients=["cert_in"], refs=["EV-X-T000-0"])["sent"]
    r = send(proto, type="inform", sender="cert_in", recipients=["regulator"], refs=["IN-FAKE-2099-1"])
    assert "does not resolve" in r["rejected"]


def test_invented_ids_in_text_rejected(env):
    _, _, proto = env
    r = send(proto, type="inform", sender="cert_in", recipients=["regulator"],
             text="Under IN-CERTIN-DIR-2022-ii and IN-MADEUP-2030-9 the report is due.")
    assert "IN-MADEUP-2030-9" in r["rejected"]
    assert send(proto, type="inform", sender="cert_in", recipients=["regulator"],
                text="Under IN-CERTIN-DIR-2022-ii the report goes to CERT-In.")["sent"]


def test_rejected_gap_is_not_a_citation(env):
    w, _, proto = env
    assert P.classify_citation("GAP-IN-07-NO-JOINT-PLAN", w.kb) is None
    assert P.classify_citation("GAP-IN-02-NO-DOWNSTREAM-WARNING", w.kb) == "gap"
    r = send(proto, type="inform", sender="gap_analyst", recipients=["regulator"], refs=["GAP-IN-07-NO-JOINT-PLAN"])
    assert "rejected" in r


def test_objection_needs_a_message_it_is_party_to(env):
    _, _, proto = env
    assert "in_reply_to" in send(proto, type="object", sender="cert_in", recipients=["regulator"])["rejected"]
    m1 = send(proto, type="inform", sender="satellite_operator", recipients=["mobile_operator"])["id"]
    r = send(proto, type="object", sender="cert_in", recipients=["mobile_operator"], in_reply_to=m1)
    assert "not a message you sent or received" in r["rejected"]
    assert send(proto, type="object", sender="mobile_operator", recipients=["satellite_operator"],
                in_reply_to=m1, text="PB-05 would cut 112 traffic on CHN-02.")["sent"]


def test_chunk_ids_checked_against_vector_kb(env, monkeypatch):
    w, _, proto = env
    monkeypatch.setattr(P, "_kbvec", lambda: None)                       # package absent
    assert P.classify_citation("chunk-abc", w.kb) is None
    fake = types.SimpleNamespace(get_chunk=lambda cid: {"chunk_id": cid} if cid == "chunk-abc" else None,
                                 search=lambda *a, **k: [])
    monkeypatch.setattr(P, "_kbvec", lambda: fake)
    assert P.classify_citation("chunk-abc", w.kb) == "chunk"
    assert P.classify_citation("chunk-zzz", w.kb) is None
    assert send(proto, type="inform", sender="cert_in", recipients=["regulator"], refs=["chunk-abc"])["sent"]
    assert "rejected" in send(proto, type="inform", sender="cert_in", recipients=["regulator"], refs=["chunk-zzz"])


def test_audit_chain_intact_after_mixed_traffic(env):
    w, _, proto = env
    send(proto, type="inform", sender="cert_in", recipients=["regulator"])
    send(proto, type="shout", sender="cert_in", recipients=["regulator"])
    assert kinds(w) == ["msg_sent", "msg_rejected"]
    assert w.audit.verify() is None


def test_chunk_ids_in_free_text_are_seen():
    # a vector-KB chunk id written in prose must be picked up, so a made-up one can be rejected
    from orca.protocol import ID_RE
    assert ID_RE.findall("see in-tcsr-2024:p5:c2 and IN-TCSR-2024-R7-1") == ["in-tcsr-2024:p5:c2", "IN-TCSR-2024-R7-1"]
    assert ID_RE.findall("time 10:30 on p5") == []
