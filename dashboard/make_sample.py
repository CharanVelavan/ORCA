"""Write two SAMPLE traces (rules on, rules off) so the dashboard has something to show with no other run.

    python -m dashboard.make_sample            # rewrites dashboard/samples/*.jsonl

These are hand-built from the S1 scenario script (scenarios/s1.yaml) in the real audit format with a
valid hash chain. They are NOT model runs. Every satellite link in them is emulated. The first entry,
``run_meta``, says so. Real runs from orca/runner.py go in runs/ and replace them in the picker.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "samples"
START = dt.datetime.fromisoformat("2026-11-10T19:00:00+05:30")
GENESIS = "0" * 64


def canon(o) -> str:
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class Trace:
    """Collects (minute, kind, actor, payload) in any order; ``write`` sorts by time and chains the hashes."""

    def __init__(self):
        self.pending: list[tuple] = []

    def add(self, t: float, kind: str, actor: str, payload: dict) -> None:
        self.pending.append((t, len(self.pending), kind, actor, payload))

    def rows(self) -> list[dict]:
        out: list[dict] = []
        for t, _, kind, actor, payload in sorted(self.pending, key=lambda r: (r[0], r[1])):
            prev = out[-1]["hash"] if out else GENESIS
            e = {"seq": len(out) + 1, "ts": (START + dt.timedelta(minutes=t)).isoformat(), "kind": kind,
                 "actor": actor, "payload": payload, "prev_hash": prev}
            e["hash"] = hashlib.sha256(canon(e).encode()).hexdigest()
            out.append(e)
        return out

    def write(self, path: Path) -> None:
        path.write_text("".join(canon(r) + "\n" for r in self.rows()), encoding="utf-8")


def plan_hash(pb: str, targets: list[str], owner: str) -> str:
    return hashlib.sha256(canon({"playbook": pb, "targets": sorted(targets), "owner": owner}).encode()).hexdigest()


def iso(t: float) -> str:
    return (START + dt.timedelta(minutes=t)).isoformat()


ALERTS = [
    (0, "M1", "anomaly", ["CHN-02"], "M1 flags an anomalous VPN login on the management plane.", ["satellite_operator"],
     [{"signal": "vpn_login", "site": "CHN-02", "value": {"anomalous": True, "user": "noc-vendor-7"}}]),
    (8, "M3", "attack-management-plane", ["CHN-02"], "M3 classifies management-plane attack pattern.", ["satellite_operator"],
     [{"signal": "mgmt_command", "site": "CHN-02", "value": {"type": "config_change", "count": 4}}]),
    (18, "attacker", "attack-management-plane", ["CHN-01", "CHN-02"], "Wipe commands reach the emulated satellite modems.",
     ["satellite_operator"], [{"signal": "mgmt_command", "site": "CHN-02", "value": {"type": "wipe", "count": 12}}]),
    (24, "mobile_operator", "down", ["CHN-01", "CHN-02"], "Backhaul modems lost at CHN-01 and CHN-02. 112 and UPI calls fail.",
     ["mobile_operator"], [{"signal": "terminals_up", "site": "CHN-02", "value": 0}]),
    (55, "mobile_operator", "route_offer", ["CHN-01", "CHN-02"], "Microwave backup path B via GW-IN-2 offered. Integrity verified.",
     ["mobile_operator"], [{"signal": "route_candidate", "site": "CHN-02", "value": {"path": "B", "gateway": "GW-IN-2", "integrity": "verified"}}]),
    (78, "M1", "normal", ["CHN-01", "CHN-02"], "M1 confirms critical traffic is back over microwave backup.", ["mobile_operator"], []),
]

V_GAP09 = {"verdict": "POTENTIAL_GAP", "rule_id": "IN-R-COVERAGE", "topic": "space_cyber", "gap_id": "GAP-IN-09-SPACE-CYBER-ADVISORY",
           "record_ids": ["IN-SPACEFW-2026-3-2-1", "IN-PIB-2026-SPACEFW-ADVISORY"],
           "explanation": "No in-force verified record sets a binding satellite cyber baseline. The space framework is advisory.",
           "deadline": None, "time_left": None, "notes": []}
V_CLOCKS = {"verdict": "AMBIGUITY", "rule_id": "IN-R-CLOCKS", "topic": "incident_reporting", "gap_id": "GAP-IN-01-REPORTING-CLOCKS",
            "record_ids": ["IN-CERTIN-DIR-2022-ii", "IN-TCSR-2024-R7-1", "IN-CTIR-2024-R7-1-j"],
            "explanation": "Three clocks apply to one incident and start at different times: noticing 19:04, awareness 19:18, occurrence 19:00.",
            "deadline": iso(360), "time_left": "5 h 30 m left", "notes": ["Safe working deadline is the earliest one."]}
V_WARN = {"verdict": "POTENTIAL_GAP", "rule_id": "IN-R-COVERAGE", "topic": "downstream_warning", "gap_id": "GAP-IN-02-NO-DOWNSTREAM-WARNING",
          "record_ids": ["IN-TELACT-2023-20"],
          "explanation": "No in-force verified record requires a satellite operator to warn the services that depend on it.",
          "deadline": None, "time_left": None, "notes": []}
V_CONFLICT = {"verdict": "CONFLICT", "rule_id": "IN-R-CONFLICT-PB05-PB06", "topic": "joint_command", "gap_id": None,
              "record_ids": ["IN-CERTIN-DIR-2022-ANX1-ii", "IN-TELACT-2023-20"],
              "explanation": "PB-05 (isolate management segment) and PB-06 (fail over) target the same towers CHN-01 and CHN-02.",
              "deadline": None, "time_left": None, "notes": ["Rejected gap GAP-IN-07 is not raised again."]}
V_LOC = {"verdict": "COMPLIANT", "rule_id": "IN-R-COVERAGE", "topic": "data_location", "gap_id": None,
         "record_ids": ["IN-AUTHZ-2026-R60-1-b"], "explanation": "Failover gateway GW-IN-2 is in India (Authz Rule 60(1)(b)).",
         "deadline": None, "time_left": None, "notes": []}


def build(rules: bool) -> Trace:
    tr = Trace()
    tr.add(0, "run_meta", "system", {
        "scenario": "S1", "title": "SAMPLE trace, not a model run: " + ("rule engine on" if rules else "rule engine off"),
        "rules": rules, "llm": "sample", "start": START.isoformat(), "kb_as_of": "2026-11-07",
        "note": "Hand-built from scenarios/s1.yaml for the dashboard. All satellite links are emulated."})
    def step(t, actor, tool, args, result, rationale, cited=None, final=False, turn=1):
        tr.add(t, "agent_step", actor, {"turn": turn, "tool": tool, "args": args, "reasoning": None, "rationale": rationale,
                                       "citations_accepted": cited or [], "citations_rejected": [],
                                       **({"result": result} if not final else {"final": True, "verdicts_not_from_engine": []})})

    def release(i, a):
        t, src, label, sites, detail, vis, sigs = a
        al = {"actor": src, "at": iso(t), "detail": detail, "id": f"EV-S1-T{t:03d}-{i}", "label": label, "signals": sigs,
              "site": sites[0], "sites": sites, "source": src if src.startswith("M") else "scenario", "t": t}
        tr.add(t, "event_released", "scenario", {"alert_id": al["id"], "visible_to": vis, "t": t})
        for r in vis:
            tr.add(t, "agent_task", r, {"task": f"New information released to you: [{al['id']}] T+{t} min: {detail}. Assess it within your mandate.",
                                        "tools": ["read_alerts", "run_rule_engine", "send_message", "request_approval", "execute_playbook"]})
            step(t, r, "read_alerts", {"source": "any"}, {"alerts": [al], "messages_to_me": []}, "see what was released to me")
        return al

    al = [release(i, a) for i, a in enumerate(ALERTS)]
    sat, mob = "satellite_operator", "mobile_operator"
    h_pb01 = plan_hash("PB-01", ["noc-vendor-7"], sat)
    h_pb05 = plan_hash("PB-05", ["SAT-MGMT"], sat)
    h_pb06 = plan_hash("PB-06", ["CHN-01", "CHN-02"], mob)
    h_pb10 = plan_hash("PB-10", ["CHN-01", "CHN-02"], mob)

    def plan(t, pb, title, owner, targets, h, params, reason, ttl=30):
        tr.add(t, "approval_requested", owner, {
            "hash": h, "playbook": pb, "title": title, "owner": owner, "targets": targets, "params": params,
            "reason": reason, "requested_at": iso(t), "expires_at": iso(t + ttl), "executable": pb != "PB-05",
            "clone_test": {"passed": True, "detail": "preconditions hold on a copy of the emulated state"},
            "verdicts": [v["verdict"] for v in ([V_GAP09, V_CLOCKS] if rules else [])]})

    def approve(t, h, pb, ttl=15, req_exp=None):
        tr.add(t, "approved", "human:commander", {"plan_hash": h, "playbook": pb, "token_expires_at": iso(t + ttl), "request_expires_at": req_exp})

    # T+8: management plane attack. Satellite operator asks to disable the exposed account.
    if rules:
        step(8, sat, "run_rule_engine", {}, {"kb_as_of": "2026-11-07", "verdicts": [V_GAP09], "footer": "Rule-engine result on stated facts. Not legal advice."},
             "get verdicts from the rule engine, the only source of verdicts", ["IN-SPACEFW-2026-3-2-1", "GAP-IN-09-SPACE-CYBER-ADVISORY"], turn=2)
    step(8, sat, "request_approval", {"playbook": "PB-01", "targets": ["noc-vendor-7"], "reason": "M3 says management-plane attack. Disable the exposed VPN account."},
         {"hash": h_pb01, "playbook": "PB-01", "status": "waiting for the human commander"}, "contain first")
    plan(8, "PB-01", "Disable exposed VPN account, rotate credentials", sat, ["noc-vendor-7"], h_pb01, {}, "M3 says management-plane attack. Disable the exposed VPN account.")
    tr.add(8, "msg_sent", sat, {"id": "MSG-0001", "type": "approve_request", "sender": sat, "recipients": ["commander"], "refs": [h_pb01],
                                 "text": "Approve PB-01 on noc-vendor-7: disable exposed VPN account.", "data_class": "operational", "playbook": "PB-01", "at": iso(8)})
    if rules:
        tr.add(12, "agent_task", "gap_analyst", {"task": "Audit binding satellite cyber baselines.", "tools": ["query_kb", "run_rule_engine", "record_gap"]})
        step(12, "gap_analyst", "run_rule_engine", {"questions": [{"topic": "space_cyber"}]}, {"verdicts": [V_GAP09]}, "check coverage of space cyber", ["GAP-IN-09-SPACE-CYBER-ADVISORY"])
        step(12, "gap_analyst", "record_gap", {"topic": "space_cyber", "finding": "No binding satellite cyber baseline found.", "evidence": ["IN-SPACEFW-2026-3-2-1"]},
             {"draft_id": "GAPDRAFT-001", "matches_registered": ["GAP-IN-09-SPACE-CYBER-ADVISORY"], "status": "pre-confirmed"}, "record the gap with evidence", ["IN-SPACEFW-2026-3-2-1"], turn=2)
        tr.add(12, "msg_sent", "gap_analyst", {"id": "MSG-0002", "type": "inform", "sender": "gap_analyst", "recipients": [sat], "refs": ["GAP-IN-09-SPACE-CYBER-ADVISORY"],
                                                "text": "Space cyber baseline is advisory only. See GAP-IN-09.", "data_class": "operational", "at": iso(12)})
    tr.add(14, "approved", "human:commander", {"plan_hash": h_pb01, "playbook": "PB-01", "token_expires_at": iso(29), "request_expires_at": iso(38)})
    tr.add(15, "executed", sat, {"playbook": "PB-01", "targets": ["noc-vendor-7"], "params": {}, "plan_hash": h_pb01, "approver": "commander", "ok": True,
                                  "stages": [{"pct": 5, "healthy": True}, {"pct": 25, "healthy": True}, {"pct": 100, "healthy": True}], "detail": "rolled out 5/25/100 %"})
    # T+24: the outage is visible. Mobile operator talks to the satellite operator and a data-sharing rule bites.
    tr.add(26, "msg_rejected", mob, {"message": {"type": "inform", "sender": mob, "recipients": [sat], "text": "Customer list for CHN-02 attached.", "data_class": "customer",
                                                  "refs": [], "playbook": None}, "reason": "customer data may not go to another operator"})
    tr.add(27, "msg_sent", mob, {"id": "MSG-0003", "type": "inform", "sender": mob, "recipients": [sat, "cert_in"], "refs": [],
                                  "text": "Modem loss at CHN-01 and CHN-02. 112 and UPI affected from T+24.", "data_class": "operational", "at": iso(27)})
    # T+30: reporting clocks.
    if rules:
        tr.add(30, "agent_task", "cert_in", {"task": "Map the statutory reporting clocks.", "tools": ["run_rule_engine", "send_message"]})
        step(30, "cert_in", "run_rule_engine", {}, {"verdicts": [V_GAP09, V_CLOCKS]}, "get clock verdicts",
             ["IN-CERTIN-DIR-2022-ii", "IN-TCSR-2024-R7-1", "IN-CTIR-2024-R7-1-j", "GAP-IN-01-REPORTING-CLOCKS"])
        tr.add(31, "msg_sent", "cert_in", {"id": "MSG-0004", "type": "request", "sender": "cert_in", "recipients": [sat],
                                            "refs": ["GAP-IN-01-REPORTING-CLOCKS"], "text": "Draft a CERT-In report by 01:00. Earliest clock is the safe one.",
                                            "data_class": "operational", "at": iso(31)})
        step(36, "gap_analyst", "run_rule_engine", {"questions": [{"topic": "downstream_warning"}]}, {"verdicts": [V_GAP09, V_CLOCKS, V_WARN]},
             "check who must warn 112 and the hospital", ["GAP-IN-02-NO-DOWNSTREAM-WARNING"], turn=3)
    # T+40: conflicting proposals.
    tr.add(40, "msg_sent", sat, {"id": "MSG-0005", "type": "propose", "sender": sat, "recipients": [sat, "commander"], "refs": [],
                                  "text": "Propose PB-05: isolate management segment.", "data_class": "operational", "playbook": "PB-05", "at": iso(40)})
    plan(40, "PB-05", "Isolate the management segment (keep logs)", sat, ["SAT-MGMT"], h_pb05, {}, "Contain the management plane fully.")
    plan(40, "PB-06", "Fail over to a backup path verified clean first", mob, ["CHN-01", "CHN-02"], h_pb06, {"path": "B"}, "Move 112 and UPI to microwave backup.")
    if rules:
        step(40, mob, "run_rule_engine", {}, {"verdicts": [V_GAP09, V_CLOCKS, V_WARN, V_CONFLICT]}, "check my plan against the other proposal", ["IN-R-CONFLICT-PB05-PB06"], turn=2)
    if rules:
        plan(41, "PB-10", "Warn downstream services", mob, ["CHN-01", "CHN-02"], h_pb10, {"message": "Satellite backhaul lost at CHN-01 and CHN-02. Use alternatives."}, "112, hospital and payments need to know.")
    # T+43: the commander decides.
    if rules:
        tr.add(43, "rejected", "human:commander", {"plan_hash": h_pb05, "reason": "Conflict with PB-06 on the same towers. Run PB-01 first, then PB-06."})
        approve(43, h_pb10, "PB-10", req_exp=iso(71))
        tr.add(44, "executed", mob, {"playbook": "PB-10", "targets": ["CHN-01", "CHN-02"], "params": {}, "plan_hash": h_pb10, "approver": "commander", "ok": True,
                                      "stages": [{"pct": 5, "healthy": True}, {"pct": 25, "healthy": True}, {"pct": 100, "healthy": True}], "detail": "rolled out 5/25/100 %"})
        tr.add(44, "msg_sent", mob, {"id": "MSG-0006", "type": "inform", "sender": mob, "recipients": ["hospital", "emergency_112", "payments"], "refs": [h_pb10],
                                      "text": "Warning: satellite backhaul lost at CHN-01 and CHN-02.", "data_class": "operational", "at": iso(44)})
    else:
        approve(43, h_pb05, "PB-05", req_exp=iso(70))
        approve(43, h_pb06, "PB-06", req_exp=iso(70))
        tr.add(45, "execute_refused", sat, {"playbook": "PB-05", "targets": ["SAT-MGMT"],
                                             "reason": "PB-05 cuts the management path PB-06 needs. Both approved on the same towers: deadlock"})
        tr.add(46, "execute_refused", mob, {"playbook": "PB-06", "targets": ["CHN-01", "CHN-02"], "reason": "management plane still isolated by PB-05: path not clean"})
    # T+50: autonomy and a kill switch drill (shows the controls in the replay).
    tr.add(50, "autonomy_set", "human:commander", {"mode": "ASSISTED", "sites": ["CHN-01", "CHN-02"], "playbooks": ["PB-10"], "granted_by": "commander",
                                                    "granted_at": iso(50), "expires": iso(110)})
    tr.add(53, "kill_switch", "human:commander", {"reason": "drill: confirm the kill switch stops everything", "tokens_revoked": 0})
    tr.add(54, "kill_switch_released", "human:commander", {"was": {"by": "commander", "at": iso(53), "reason": "drill"}})
    if rules:
        # T+55: clean failover.
        step(55, mob, "run_rule_engine", {"questions": [{"topic": "data_location"}]}, {"verdicts": [V_GAP09, V_CLOCKS, V_WARN, V_CONFLICT, V_LOC]},
             "check the failover gateway is in India", ["IN-AUTHZ-2026-R60-1-b"], turn=2)
        plan(55, "PB-06", "Fail over to a backup path verified clean first", mob, ["CHN-01", "CHN-02"], h_pb06, {"path": "B"}, "Path B via GW-IN-2 is verified clean and in India.")
        approve(57, h_pb06, "PB-06", req_exp=iso(85))
        tr.add(58, "executed", mob, {"playbook": "PB-06", "targets": ["CHN-01", "CHN-02"], "params": {"path": "B"}, "plan_hash": h_pb06, "approver": "commander", "ok": True,
                                      "stages": [{"pct": 5, "healthy": True}, {"pct": 25, "healthy": True}, {"pct": 100, "healthy": True}], "detail": "rolled out 5/25/100 %"})
        step(58, mob, None, {}, None, "Failed over CHN-01 and CHN-02 to path B via GW-IN-2. Verdicts cited: IN-AUTHZ-2026-R60-1-b.", ["IN-AUTHZ-2026-R60-1-b"], final=True)
        tr.add(60, "gap_human_decision", "human:commander", {"draft_id": "GAPDRAFT-001", "decision": "confirmed", "note": "evidence read, matches GAP-IN-09"})
    else:
        tr.add(60, "execute_refused", mob, {"playbook": "PB-06", "targets": ["CHN-01", "CHN-02"], "reason": "approval expired (token is valid 15 min from approval)"})
    return tr


def main() -> None:
    OUT.mkdir(exist_ok=True)
    build(True).write(OUT / "s1-rules-sample.jsonl")
    build(False).write(OUT / "s1-norules-sample.jsonl")
    print("wrote", *sorted(p.name for p in OUT.glob("*.jsonl")))


if __name__ == "__main__":
    main()
