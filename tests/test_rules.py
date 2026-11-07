import datetime as dt

import pytest

from orca import kb as kbmod
from orca import rules

KB = kbmod.load()
FOOTER = "Rule-engine result on stated facts. Not legal advice."
IST = "+05:30"


def ev(facts):
    return rules.evaluate(facts, KB)


def one(vs, verdict=None, rule_id=None):
    hits = [v for v in vs if (verdict is None or v.verdict == verdict)
            and (rule_id is None or v.rule_id == rule_id)]
    assert len(hits) == 1, [(v.verdict, v.rule_id) for v in vs]
    return hits[0]


def q(topic, text="", jur="IN", **kw):
    return {"id": f"Q-{topic}", "topic": topic, "text": text or topic, "jurisdiction": jur, **kw}


def question(topic, jur="IN", on="2026-11-10", **kw):
    return ev({"jurisdiction": jur, "on": on, "obligation_questions": [q(topic, jur=jur, **kw)]})[0]


# ---------------------------------------------------------------- deadlines
CLOCKS = {"jurisdiction": "IN", "now": f"2026-11-10T20:00:00{IST}",
          "triggers": {"noticing": f"2026-11-10T19:02:00{IST}", "occurrence": f"2026-11-10T18:40:00{IST}"}}


def test_certin_deadline_arithmetic():
    f = {**CLOCKS, "applies": ["IN-CERTIN-DIR-2022-ii"]}
    v = one(ev(f))
    assert v.verdict == "COMPLIANT" and v.record_ids == ["IN-CERTIN-DIR-2022-ii"]
    assert dt.datetime.fromisoformat(v.deadline) == dt.datetime.fromisoformat(f"2026-11-11T01:02:00{IST}")
    assert v.time_left == "5 h 02 m left"          # 20:00 -> 01:02
    assert "pending" in " ".join(v.notes)


def test_tcsr_deadline_arithmetic():
    v = one(ev({**CLOCKS, "applies": ["IN-TCSR-2024-R7-1"]}))
    assert dt.datetime.fromisoformat(v.deadline) == dt.datetime.fromisoformat(f"2026-11-11T00:40:00{IST}")
    assert v.deadline.endswith("+05:30")


def test_sent_in_time_is_compliant_and_late_is_violation():
    f = {**CLOCKS, "applies": ["IN-CERTIN-DIR-2022-ii"],
         "reports": [{"record": "IN-CERTIN-DIR-2022-ii", "sent_at": f"2026-11-10T22:40:00{IST}"}]}
    v = one(ev(f))
    assert v.verdict == "COMPLIANT" and v.time_left == "2 h 22 m left"
    f["reports"][0]["sent_at"] = f"2026-11-11T01:36:00{IST}"
    v = one(ev(f))
    assert v.verdict == "VIOLATION" and v.time_left == "0 h 34 m overdue"


def test_not_sent_after_deadline_is_violation():
    f = {**CLOCKS, "applies": ["IN-TCSR-2024-R7-1"], "now": f"2026-11-11T01:00:00{IST}"}
    assert one(ev(f)).verdict == "VIOLATION"


def test_missing_trigger_or_now_is_insufficient_evidence():
    f = {"jurisdiction": "IN", "now": f"2026-11-10T20:00:00{IST}", "applies": ["IN-TCSR-2024-R7-1"],
         "triggers": {"noticing": f"2026-11-10T19:02:00{IST}"}}
    v = one(ev(f))
    assert v.verdict == "INSUFFICIENT_EVIDENCE" and "triggers.occurrence" in v.explanation
    f = {**CLOCKS, "applies": ["IN-TCSR-2024-R7-1"]}
    del f["now"]
    assert one(ev(f)).verdict == "INSUFFICIENT_EVIDENCE"


def test_ambiguity_gives_earliest_deadline():
    vs = ev(CLOCKS)
    amb = one(vs, "AMBIGUITY", "IN-R-CLOCKS")
    assert amb.gap_id == "GAP-IN-01-THREE-CLOCKS"
    assert dt.datetime.fromisoformat(amb.deadline) == dt.datetime.fromisoformat(f"2026-11-11T00:40:00{IST}")
    assert len(amb.readings) == 2
    assert {r["record"] for r in amb.readings} == {"IN-CERTIN-DIR-2022-ii", "IN-TCSR-2024-R7-1"}
    assert amb.time_left == "4 h 40 m left"


def test_fault_then_attack_lists_each_reading():
    f = {**CLOCKS, "triggers": {"noticing": f"2026-11-11T06:40:00{IST}",
                                "occurrence": [{"label": "outage start", "at": f"2026-11-11T02:10:00{IST}"},
                                               {"label": "first malicious login", "at": f"2026-11-11T01:55:00{IST}"}]},
         "now": f"2026-11-11T06:40:00{IST}",
         "classifications": [{"at": f"2026-11-11T02:10:00{IST}", "label": "fault"},
                             {"at": f"2026-11-11T06:40:00{IST}", "label": "attack"}]}
    amb = one(ev(f), "AMBIGUITY", "IN-R-CLOCKS")
    assert len(amb.readings) == 3
    assert amb.deadline.startswith("2026-11-11T07:55")
    assert amb.time_left == "1 h 15 m left"
    assert any("fault" in n for n in amb.notes)


def test_space_framework_status_not_stated_is_ambiguity():
    f = {**CLOCKS, "applies": ["IN-SPACEFW-2026-3-2-1"]}
    v = one(ev(f))
    assert v.verdict == "AMBIGUITY" and v.gap_id == "GAP-IN-09-SPACE-FW-STATUS"
    assert "not applicable" not in v.explanation.replace("'not applicable'", "")


# ---------------------------------------------------------------- conflict
def test_conflict_pb05_pb06():
    f = {"jurisdiction": "IN", "proposed_actions": [
        {"playbook": "PB-05", "agent": "satellite_operator", "targets": ["gw-chennai-1"],
         "supporting_records": ["IN-CERTIN-DIR-2022-ANX1-ii", "IN-CERTIN-DIR-2022-iv"]},
        {"playbook": "PB-06", "agent": "mobile_operator", "targets": ["gw-chennai-1", "gw-2"],
         "supporting_records": ["IN-TELACT-2023-20"]}]}
    v = one(ev(f))
    assert v.verdict == "CONFLICT" and len(v.actions) == 2
    assert {"IN-CERTIN-DIR-2022-iv", "IN-TELACT-2023-20"} <= set(v.record_ids)
    assert "gw-chennai-1" in v.explanation
    f["proposed_actions"][1]["targets"] = ["gw-2"]
    assert ev(f) == []                      # no shared target, no clash


# ---------------------------------------------------------------- coverage and guards
def test_each_of_six_verdicts_occurs():
    seen = {v.verdict for v in ev(CLOCKS)}                                   # AMBIGUITY, COMPLIANT
    seen |= {question("capacity_priority").verdict}                          # POTENTIAL_GAP
    seen |= {one(ev({**CLOCKS, "now": f"2026-11-11T02:00:00{IST}", "applies": ["IN-TCSR-2024-R7-1"]})).verdict}
    seen |= {one(ev({"jurisdiction": "IN", "applies": ["IN-TCSR-2024-R7-1"], "triggers": {}})).verdict}
    seen |= {ev({"proposed_actions": [{"playbook": "PB-05", "targets": ["g"]},
                                      {"playbook": "PB-06", "targets": ["g"]}]})[0].verdict}
    assert seen == rules.VERDICTS


def test_unverified_record_never_compliant_or_violation():
    unv = [r for r in KB.records.values() if not r.get("verified") and r["jurisdiction"] == "IN"]
    assert unv, "no unverified IN record left in the KB to test with"
    for r in unv:
        for on in ("2026-11-10", "2030-01-01"):
            for topic in r["topics"]:
                v = question(topic, on=on)
                if v.verdict in ("COMPLIANT", "VIOLATION"):
                    assert r["id"] not in v.record_ids, (r["id"], v.verdict)
    # the engine guard itself, forced through a verified-false record
    eng = rules._Engine({"jurisdiction": "IN"}, KB)
    v = eng.add("COMPLIANT", "X", unv[0]["topic"], [unv[0]["id"]], "covered")
    assert v.verdict == "INSUFFICIENT_EVIDENCE" and "unverified" in v.explanation


def test_footer_asof_and_ids_exist_on_all_verdicts():
    qs = [q(t) for t in ("incident_reporting", "capacity_priority", "personal_data_breach", "space_cyber",
                         "downstream_warning", "no_such_topic_xyz", "cert_powers")]
    f = {**CLOCKS, "on": "2026-11-10", "obligation_questions": qs,
         "proposed_actions": [{"playbook": "PB-05", "targets": ["g"], "supporting_records": ["IN-CERTIN-DIR-2022-iv"]},
                              {"playbook": "PB-06", "targets": ["g"], "supporting_records": ["NOT-A-RECORD"]}]}
    vs = ev(f)
    assert len(vs) >= 8
    for v in vs:
        assert v.footer == FOOTER and v.kb_as_of == str(KB.as_of)
        assert v.verdict in rules.VERDICTS and (v.record_ids or v.gap_id)
        for rid in v.record_ids:
            assert rid in KB.records
        if v.gap_id:
            assert v.gap_id in KB.gaps or v.gap_id.startswith("GAP-CAND-")
        assert "no rule exists" not in v.explanation.lower()
        assert v.to_dict()["footer"] == FOOTER


def test_explanation_wording_for_gaps():
    v = question("capacity_priority")
    assert f"as of {KB.as_of}" in v.explanation
    assert "sources we checked" in v.explanation


# ---------------------------------------------------------------- negative controls
@pytest.mark.parametrize("jur,topic,record", [
    ("IN", "log_retention", "IN-CERTIN-DIR-2022-iv"),
    ("IN", "point_of_contact", "IN-CERTIN-DIR-2022-iii"),
    ("IN", "incident_reporting", "IN-CERTIN-DIR-2022-ii"),
    ("IN", "ntn_coverage", "IN-TELACT-2023-2-s"),
    ("AE", "emergency_priority", "AE-TDRA-IC-2006-EMERGENCY"),
])
def test_negative_control(jur, topic, record):
    v = question(topic, jur=jur, record=record)
    assert v.verdict == "COMPLIANT", v.explanation
    assert record in v.record_ids and f"covered by {record}" in v.explanation
    assert v.gap_id is None
    # and without naming the record the topic is still covered
    assert question(topic, jur=jur).verdict == "COMPLIANT"


# ---------------------------------------------------------------- positive gap checks
def test_downstream_warning_in_is_ambiguity_via_space_framework():
    v = question("downstream_warning")
    assert v.verdict == "AMBIGUITY" and v.gap_id.startswith("GAP-IN-02")
    assert "IN-SPACEFW-2026-ANXB-IV" in v.record_ids
    assert len(v.readings) == 2 and any("GAP-IN-09-SPACE-FW-STATUS" in n for n in v.notes)


@pytest.mark.parametrize("topic,prefix", [
    ("capacity_priority", "GAP-IN-03"),
    ("failover_path_security", "GAP-IN-08"),
    ("backup_power", "GAP-IN-04"),
    ("joint_command", "GAP-IN-07"),
])
def test_potential_gap_registered(topic, prefix):
    v = question(topic)
    assert v.verdict == "POTENTIAL_GAP" and v.gap_id.startswith(prefix)


def test_personal_data_breach_not_yet_in_force():
    v = question("personal_data_breach", on="2026-11-10")
    assert v.verdict == "POTENTIAL_GAP" and v.gap_id.startswith("GAP-IN-05")
    assert "2027-05-13" in v.explanation
    # after commencement (13 May 2027) the verified DPDP records cover the topic
    later = question("personal_data_breach", on="2027-06-01")
    assert later.verdict == "COMPLIANT" and later.gap_id is None
    assert {"IN-DPDP-ACT-2023-8-6", "IN-DPDP-RULES-2025-R7"} & set(later.record_ids)


def test_unknown_topic_gets_candidate_id():
    import hashlib
    v = question("quantum_widgets")
    assert v.verdict == "POTENTIAL_GAP"
    assert v.gap_id == "GAP-CAND-" + hashlib.sha1(b"IN:quantum_widgets").hexdigest()[:8]


def test_eu_downstream_warning_covered():
    v = question("downstream_warning", jur="EU")
    assert v.verdict == "COMPLIANT" and "EU-NIS2-2022-ART23-2" in v.record_ids


def test_rule_files_reference_real_records_and_gaps():
    for jur in rules.RULE_FILES:
        r = rules.load_rules(jur)
        for d in r["deadline_rules"]:
            assert d["record"] in KB.records and ("gap" not in d or d["gap"] in KB.gaps)
        for c in r["conflicts"]:
            assert all(x in KB.records for x in c["records"])
