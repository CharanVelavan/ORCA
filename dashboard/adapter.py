"""Adapter: run file (JSON Lines audit trace) -> one normalised model for the browser.

Design rules
- Standard library only. No orca imports, so the dashboard runs anywhere.
- Tolerant. A missing field, a wrong type, an unknown ``kind`` or a half-written last line never
  raises. Unknown entries become generic ``other`` events and still show up in the timeline.
- The trace format will grow. Everything the page needs is derived here, in one place.

Entry format (orca/audit.py): {seq, ts, kind, actor, payload, prev_hash, hash}.

Kinds understood today
  event_released, agent_task, agent_step, msg_sent, msg_rejected, approval_requested, approved,
  rejected, executed, rolled_back, execute_refused, autonomy_set, autonomy_blocked,
  autonomy_downgraded, kill_switch, kill_switch_released, pin_refused, gap_human_decision,
  adviser_answer, adviser_*_error, adviser_llm_discarded, agent_error
Optional kinds the runner may add (all optional; see dashboard/README.md)
  run_meta   {scenario, title, rules: bool, llm, start, seed}
  verdict    {verdict, rule_id, topic, record_ids, gap_id, explanation, ...} or {verdicts: [..]}
  gap_raised {gap_id | id, title, topic, status, evidence}
  net_state  {sites: {id: {state, path, gateway, note}}, gateways: {id: {state}}, mgmt: {state}}
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path

from . import topology

GENESIS = "0" * 64
VERDICTS = ("COMPLIANT", "VIOLATION", "AMBIGUITY", "CONFLICT", "POTENTIAL_GAP", "INSUFFICIENT_EVIDENCE")
GAP_ID = re.compile(r"\bGAP-[A-Z]{2,}-\d+[A-Z0-9-]*\b")
SITE_ID = re.compile(r"\b(?:TERM-)?(CHN-\d{2})\b")

# Playbook -> (what happens on the map when it runs, note). Mirrors playbooks/catalogue.yaml ids.
PB_EFFECT = {
    "PB-01": ("mgmt", "contained", "account disabled, sessions revoked"),
    "PB-11": ("mgmt", "contained", "credentials rotated, MFA on"),
    "PB-12": ("mgmt", "contained", "VPN and management interface closed"),
    "PB-13": ("gateway", "protected", "feeder link encrypted"),
    "PB-14": ("site", "protected", "firmware updated in waves"),
    "PB-15": ("site", "protected", "battery-saving mode on"),
    "PB-10": ("site", None, "downstream warning sent"),
    "PB-06": ("failover", "healed", "failed over to a verified clean backup path"),
}


# ----------------------------------------------------------------------------- small helpers
def _d(x) -> dict:
    return x if isinstance(x, dict) else {}


def _l(x) -> list:
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def _s(x, n: int = 0) -> str:
    s = "" if x is None else (x if isinstance(x, str) else json.dumps(x, default=str, ensure_ascii=False))
    s = " ".join(s.split())
    return s if not n or len(s) <= n else s[: n - 1] + "…"


def _epoch(ts) -> float | None:
    try:
        t = dt.datetime.fromisoformat(str(ts))
        if t.tzinfo is None:
            t = t.replace(tzinfo=dt.timezone.utc)
        return t.timestamp()
    except (ValueError, TypeError):
        return None


def _actor(a) -> str:
    a = _s(a) or "unknown"
    return "commander" if a.startswith("human:") else a


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def verify_chain(entries: list[dict]) -> dict:
    """Same rule as orca.audit.AuditLog.verify. ``ok`` is None when entries carry no hashes."""
    if not entries or not all(isinstance(e.get("hash"), str) for e in entries):
        return {"ok": None, "bad_seq": None, "note": "no hash chain in this file"}
    prev, n = GENESIS, 1
    for e in entries:
        body = {k: v for k, v in e.items() if k != "hash"}
        good = (e.get("seq") == n and e.get("prev_hash") == prev
                and hashlib.sha256(canonical(body).encode("utf-8")).hexdigest() == e["hash"])
        if not good:
            return {"ok": False, "bad_seq": n, "note": f"chain breaks at entry {n}"}
        prev, n = e["hash"], n + 1
    return {"ok": True, "bad_seq": None, "note": "audit chain intact"}


def read_entries(path: Path) -> tuple[list[dict], int]:
    """All JSON objects in the file, in order. Bad lines are counted and skipped."""
    out, bad = [], 0
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [], 0
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except ValueError:
            bad += 1
            continue
        if isinstance(e, dict):
            out.append(e)
        else:
            bad += 1
    return out, bad


def parse_run_name(name: str) -> dict:
    """runs/<scenario>-<rules|norules>-<llm>.jsonl, else best effort (mock-s1 -> scenario s1, llm mock)."""
    m = re.match(r"^(?P<scen>[A-Za-z0-9]+)-(?P<rules>rules|norules)-(?P<llm>.+)$", name)
    if m:
        return {"scenario": m["scen"].upper(), "rules": m["rules"] == "rules", "llm": m["llm"]}
    m = re.match(r"^(?P<llm>[A-Za-z0-9]+)-(?P<scen>[A-Za-z]\d?[A-Za-z]*\d*)$", name)
    if m:
        return {"scenario": m["scen"].upper(), "rules": None, "llm": m["llm"]}
    return {"scenario": None, "rules": None, "llm": None}


# ----------------------------------------------------------------------------- summaries
def _tool_brief(tool: str, args: dict, res: dict) -> str:
    if "refused" in res:
        return "refused: " + _s(res["refused"], 160)
    if tool == "read_alerts":
        return f"read {len(_l(res.get('alerts')))} alerts, {len(_l(res.get('messages_to_me')))} messages"
    if tool == "run_rule_engine":
        vs = _l(res.get("verdicts"))
        names = ", ".join(dict.fromkeys(_s(_d(v).get("verdict")) for v in vs)) or "no verdicts"
        return f"{len(vs)} verdicts: {names}"
    if tool == "explain_model":
        return "explained " + _s(args.get("alert_id"))
    if tool in ("query_kb", "ask_adviser"):
        return "asked: " + _s(args.get("question"), 120)
    if tool == "select_playbook":
        return f"listed {len(_l(res.get('playbooks')))} playbooks"
    if tool == "send_message":
        return f"to {_s(args.get('to'))} ({_s(args.get('type'))}): {_s(args.get('text'), 140)}"
    if tool == "request_approval":
        return f"asked approval for {_s(args.get('playbook'))} on {_s(args.get('targets'))}: {_s(res.get('status'), 80)}"
    if tool == "execute_playbook":
        return f"{_s(args.get('playbook'))}: {'ok' if res.get('ok') else _s(res.get('detail') or 'not ok', 120)}"
    if tool == "draft_notice":
        return f"drafted {_s(args.get('kind'))} for {_s(args.get('recipient'))}"
    if tool == "record_gap":
        return f"gap draft on {_s(args.get('topic'))}: {_s(res.get('status'))}"
    return _s(res, 140) if res else "(no result)"


def _summary(kind: str, actor: str, p: dict, alerts: dict) -> tuple[str, str]:
    """(type, one-line summary) for an audit entry. Unknown kinds fall through to ('other', ...)."""
    if kind == "event_released":
        a = alerts.get(_s(p.get("alert_id")), {})
        who = ", ".join(_l(p.get("visible_to"))) or "everyone"
        return "scenario_event", f"{_s(a.get('detail')) or 'Event ' + _s(p.get('alert_id'))} (seen by {who})"
    if kind == "agent_task":
        return "task", "Task: " + _s(p.get("task"), 200)
    if kind == "agent_step":
        if p.get("final") or not p.get("tool"):
            return "final", "Final answer: " + _s(p.get("rationale"), 200)
        return "tool_call", f"{p['tool']}: " + _tool_brief(_s(p["tool"]), _d(p.get("args")), _d(p.get("result")))
    if kind == "msg_sent":
        return "message", f"{_s(p.get('sender'))} to {_s(p.get('recipients'))} ({_s(p.get('type'))}): {_s(p.get('text'), 160)}"
    if kind == "msg_rejected":
        m = _d(p.get("message"))
        return "message_rejected", f"Message {_s(m.get('sender'))} to {_s(m.get('recipients'))} refused: {_s(p.get('reason'), 140)}"
    if kind == "approval_requested":
        return "approval", f"Approval requested: {_s(p.get('playbook'))} on {_s(p.get('targets'))}"
    if kind == "approved":
        by = "commander" if actor == "commander" else actor
        return "approval", f"Approved {_s(p.get('playbook'))} by {by}"
    if kind == "rejected":
        return "approval", "Commander rejected a plan: " + _s(p.get("reason"), 140)
    if kind in ("executed", "rolled_back"):
        return "execution", f"{'Executed' if kind == 'executed' else 'Rolled back'} {_s(p.get('playbook'))} on {_s(p.get('targets'))}"
    if kind == "execute_refused":
        return "execution", f"Execution refused for {_s(p.get('playbook'))}: {_s(p.get('reason'), 140)}"
    if kind.startswith("autonomy"):
        return "autonomy", f"{kind.replace('_', ' ').capitalize()}: " + _s(p.get("mode") or p.get("to") or p.get("reason"), 120)
    if kind.startswith("kill_switch"):
        return "kill", ("Kill switch released" if kind.endswith("released") else "Kill switch engaged: " + _s(p.get("reason"), 120))
    if kind == "pin_refused":
        return "approval", "Wrong PIN refused"
    if kind == "gap_human_decision":
        return "gap", f"Human {_s(p.get('decision'))} gap draft {_s(p.get('draft_id'))}"
    if kind == "gap_raised":
        return "gap", f"Gap {_s(p.get('gap_id') or p.get('id'))}: {_s(p.get('title'), 120)}"
    if kind.startswith("adviser"):
        return "adviser", f"{kind.replace('_', ' ').capitalize()}: " + _s(p.get("question") or p.get("error"), 140)
    if kind == "agent_error":
        return "error", "Agent error: " + _s(p.get("error"), 160)
    if kind == "verdict":
        v = _d(p)
        return "verdict", f"{_s(v.get('verdict'))} {_s(v.get('topic') or v.get('rule_id'))}"
    if kind == "net_state":
        return "net", "Network state updated"
    if kind == "run_meta":
        return "meta", "Run started: " + _s(p.get("title") or p.get("scenario"))
    return "other", f"{kind}: " + _s(p, 140)


# ----------------------------------------------------------------------------- site state rules
def _alert_state(a: dict) -> str | None:
    label = _s(a.get("label")).lower()
    src = _s(a.get("source"))
    if label.startswith("attack"):
        return "attack"
    if label.startswith("fault"):
        return "fault"
    if label == "abstain" or a.get("abstained"):
        return "suspect"
    if label == "anomaly":
        return "suspect"
    if src == "M2" and label not in ("normal", ""):
        return "at_risk"
    for sig in _l(a.get("signals")):
        s = _d(sig)
        name, val = _s(s.get("signal")), s.get("value")
        if name == "vpn_login" and _d(val).get("anomalous"):
            return "suspect"
        if name == "mgmt_command" and _s(_d(val).get("type")) in ("wipe", "config_change", "telemetry_edit"):
            return "attack"
        if name == "terminals_up" and val == 0:
            return "down"
        if name == "mains_power" and val == 0:
            return "fault"
        if name == "packet_loss" and isinstance(val, (int, float)) and val >= 0.5:
            return "down"
    return None


_RANK = {"normal": 0, "protected": 1, "healed": 1, "contained": 1, "at_risk": 2, "suspect": 3,
         "fault": 4, "attack": 5, "down": 6}


def _sites_in(targets) -> list[str]:
    out = []
    for t in _l(targets):
        m = SITE_ID.search(_s(t))
        if m and m[1] in topology.SITES and m[1] not in out:
            out.append(m[1])
    return out


class _Net:
    def __init__(self):
        self.sites = {k: {"state": "normal", "path": "A", "gateway": v["paths"]["A"][1], "note": ""}
                      for k, v in topology.SITES.items()}
        self.gateways = {k: {"state": "normal", "note": ""} for k in topology.GATEWAYS}
        self.mgmt = {"state": "normal", "note": ""}
        self.timeline: list[dict] = []

    def snap(self, idx: int, epoch, t, why: str) -> None:
        self.timeline.append({"idx": idx, "epoch": epoch, "t": t, "why": why,
                              "sites": json.loads(json.dumps(self.sites)),
                              "gateways": json.loads(json.dumps(self.gateways)),
                              "mgmt": dict(self.mgmt)})

    def raise_state(self, site: str, state: str, note: str = "") -> bool:
        """Raise a site to a worse state. Never lowers it (healing sets the state directly)."""
        cur = self.sites[site]
        if _RANK.get(state, 0) <= _RANK.get(cur["state"], 0):
            return False
        cur["state"], cur["note"] = state, note or cur["note"]
        return True

    def override(self, p: dict) -> None:
        for sid, v in _d(p.get("sites")).items():
            if sid in self.sites and isinstance(v, dict):
                self.sites[sid].update({k: v[k] for k in ("state", "path", "gateway", "note") if k in v})
        for gid, v in _d(p.get("gateways")).items():
            if gid in self.gateways and isinstance(v, dict):
                self.gateways[gid].update({k: v[k] for k in ("state", "note") if k in v})
        if isinstance(p.get("mgmt"), dict):
            self.mgmt.update({k: p["mgmt"][k] for k in ("state", "note") if k in p["mgmt"]})


# ----------------------------------------------------------------------------- main entry
def build_run(path, name: str | None = None, gap_register: dict | None = None) -> dict:
    """Parse one run file into the model the page renders. Never raises on bad content."""
    path = Path(path)
    name = name or path.stem
    entries, bad_lines = read_entries(path)
    meta = parse_run_name(name)
    gap_register = gap_register or {}

    # pass 1: alert registry (details come from read_alerts results) and run_meta
    alerts: dict[str, dict] = {}
    for e in entries:
        p = _d(e.get("payload"))
        if e.get("kind") == "run_meta":
            for k in ("scenario", "title", "llm", "start", "seed", "kb_as_of"):
                if p.get(k) is not None:
                    meta[k] = p[k]
            if isinstance(p.get("rules"), bool):
                meta["rules"] = p["rules"]
        if e.get("kind") == "agent_step" and p.get("tool") == "read_alerts":
            for a in _l(_d(p.get("result")).get("alerts")):
                if isinstance(a, dict) and a.get("id"):
                    alerts.setdefault(_s(a["id"]), a)

    first = next((x for x in (_epoch(e.get("ts")) for e in entries) if x is not None), None)
    start = _epoch(meta.get("start")) or first or 0.0

    events: list[dict] = []
    verdicts: dict[tuple, dict] = {}
    messages: list[dict] = []
    approvals: dict[str, dict] = {}
    approval_order: list[str] = []
    latest: dict[str, str] = {}          # plan hash -> key of its newest card
    autonomy = [{"idx": -1, "epoch": start, "t": 0, "mode": "MANUAL", "killed": False, "note": "default"}]
    gaps: dict[str, dict] = {}
    gap_drafts: dict[str, dict] = {}
    agents: dict[str, dict] = {}
    net = _Net()
    net.snap(-1, start, 0, "start")
    state = {"mode": "MANUAL", "killed": False, "expires": None}
    seen_alert_state: set[str] = set()

    def agent(name_: str) -> dict:
        return agents.setdefault(name_, {"name": name_, "tasks": 0, "calls": 0, "refused": 0, "messages_sent": 0,
                                         "steps": []})

    def gap(gid: str, idx: int, epoch, t, via: str, **kw) -> None:
        g = gaps.setdefault(gid, {"id": gid, "first_idx": idx, "first_epoch": epoch, "first_t": t, "via": [],
                                  **{k: v for k, v in _d(gap_register.get(gid)).items()}})
        if via not in g["via"]:
            g["via"].append(via)
        for k, v in kw.items():
            if v and not g.get(k):
                g[k] = v

    def push_auto(idx, epoch, t, note, expires=None) -> None:
        autonomy.append({"idx": idx, "epoch": epoch, "t": t, "mode": state["mode"], "killed": state["killed"],
                         "expires_epoch": expires, "note": note})

    def find_plan(pb, targets):
        for h in reversed(approval_order):
            a = approvals[h]
            if a["playbook"] == pb and (not targets or sorted(map(str, a["targets"])) == sorted(map(str, targets))):
                return a
        for h in reversed(approval_order):
            if approvals[h]["playbook"] == pb:
                return approvals[h]
        return None

    for idx, e in enumerate(entries):
        e = _d(e)
        kind, actor, p = _s(e.get("kind")) or "unknown", _actor(e.get("actor")), _d(e.get("payload"))
        epoch = _epoch(e.get("ts"))
        t = round((epoch - start) / 60, 2) if epoch is not None else (events[-1]["t"] if events else 0)
        if epoch is None:
            epoch = events[-1]["epoch"] if events else start
        typ, summ = _summary(kind, actor, p, alerts)
        ev = {"idx": idx, "seq": e.get("seq", idx + 1), "ts": e.get("ts"), "epoch": epoch, "t": t, "kind": kind,
              "actor": actor, "type": typ, "summary": summ, "payload": p}

        # ---- per-kind derivation
        if kind == "event_released":
            a = alerts.get(_s(p.get("alert_id")), {})
            ev["visible_to"] = _l(p.get("visible_to"))
            if p.get("t") is not None:
                ev["scenario_t"] = p.get("t")
            st = _alert_state(a) if a else None
            if st:
                for site in _sites_in(a.get("sites") or [a.get("site")]):
                    if net.raise_state(site, st, _s(a.get("detail"), 90)):
                        net.snap(idx, epoch, t, f"{site} {st}")
                if st in ("attack", "suspect") and any(
                        _s(_d(s).get("signal")) in ("vpn_login", "mgmt_command") for s in _l(a.get("signals"))):
                    if net.mgmt["state"] in ("normal",) or (st == "attack" and net.mgmt["state"] == "suspect"):
                        net.mgmt = {"state": st, "note": _s(a.get("detail"), 90)}
                        net.snap(idx, epoch, t, "SAT-MGMT " + st)
        elif kind == "agent_task":
            agent(actor)["tasks"] += 1
            agent(actor)["steps"].append({"idx": idx, "t": t, "type": "task", "text": _s(p.get("task"))})
        elif kind == "agent_step":
            a_ = agent(actor)
            res = _d(p.get("result"))
            step = {"idx": idx, "t": t, "turn": p.get("turn"), "tool": p.get("tool"), "args": _d(p.get("args")),
                    "rationale": _s(p.get("rationale")), "reasoning": _s(p.get("reasoning")),
                    "cited": [_s(c) for c in _l(p.get("citations_accepted"))],
                    "cited_rejected": [_s(c) for c in _l(p.get("citations_rejected"))],
                    "final": bool(p.get("final") or not p.get("tool")), "refused": res.get("refused"),
                    "brief": _tool_brief(_s(p.get("tool")), _d(p.get("args")), res) if p.get("tool") else "",
                    "stray_verdicts": _l(p.get("verdicts_not_from_engine"))}
            step["type"] = "final" if step["final"] else "tool_call"
            a_["steps"].append(step)
            if not step["final"]:
                a_["calls"] += 1
                if res.get("refused"):
                    a_["refused"] += 1
            for c in step["cited"]:
                if GAP_ID.fullmatch(c):
                    gap(c, idx, epoch, t, "cited by " + actor)
            tool = p.get("tool")
            if tool == "run_rule_engine":
                for v in _l(res.get("verdicts")):
                    _add_verdict(verdicts, _d(v), idx, epoch, t, actor, gap, kb_as_of=res.get("kb_as_of"))
            elif tool == "record_gap" and "refused" not in res:
                did = _s(res.get("draft_id"))
                gap_drafts[did] = {"id": did, "topic": _s(_d(p.get("args")).get("topic")), "by": actor,
                                   "finding": _s(_d(p.get("args")).get("finding")),
                                   "evidence": [_s(x) for x in _l(_d(p.get("args")).get("evidence"))],
                                   "status": _s(res.get("status")) or "pre-confirmed", "idx": idx, "t": t,
                                   "epoch": epoch, "history": [{"idx": idx, "status": _s(res.get("status")) or "pre-confirmed"}]}
                for gid in _l(res.get("matches_registered")):
                    gap(_s(gid), idx, epoch, t, f"draft {did} by {actor}")
            elif tool == "draft_notice" and "refused" not in res:
                pass
        elif kind == "msg_sent":
            m = {"idx": idx, "t": t, "epoch": epoch, "id": _s(p.get("id")), "sender": _s(p.get("sender")) or actor,
                 "recipients": [_s(r) for r in _l(p.get("recipients"))], "type": _s(p.get("type")),
                 "text": _s(p.get("text")), "data_class": _s(p.get("data_class")) or "operational",
                 "refs": [_s(r) for r in _l(p.get("refs"))], "playbook": p.get("playbook"),
                 "in_reply_to": p.get("in_reply_to"), "rejected": False}
            messages.append(m)
            agent(m["sender"])["messages_sent"] += 1
        elif kind == "msg_rejected":
            mm = _d(p.get("message"))
            messages.append({"idx": idx, "t": t, "epoch": epoch, "id": "", "sender": _s(mm.get("sender")) or actor,
                             "recipients": [_s(r) for r in _l(mm.get("recipients"))], "type": _s(mm.get("type")),
                             "text": _s(mm.get("text")), "data_class": _s(mm.get("data_class")) or "operational",
                             "refs": [], "playbook": mm.get("playbook"), "in_reply_to": None, "rejected": True,
                             "reason": _s(p.get("reason"))})
        elif kind == "approval_requested":
            ph = _s(p.get("hash")) or f"plan-{idx}"
            h = ph if ph not in approvals else f"{ph}#{idx}"      # same plan asked again: a new card
            latest[ph] = h
            ct = _d(p.get("clone_test"))
            approvals[h] = {"hash": ph, "key": h, "playbook": _s(p.get("playbook")), "title": _s(p.get("title")),
                            "owner": _s(p.get("owner")) or actor, "targets": _l(p.get("targets")),
                            "params": _d(p.get("params")), "reason": _s(p.get("reason")),
                            "requested_idx": idx, "requested_epoch": epoch, "requested_t": t,
                            "expires_epoch": _epoch(p.get("expires_at")), "token_expires_epoch": None,
                            "executable": p.get("executable"), "clone_test": {"passed": ct.get("passed"), "detail": _s(ct.get("detail"))},
                            "verdicts": [_s(v) for v in _l(p.get("verdicts"))],
                            "history": [{"idx": idx, "epoch": epoch, "t": t, "status": "requested", "by": actor, "detail": ""}]}
            approval_order.append(h)
        elif kind == "approved":
            a = approvals.get(latest.get(_s(p.get("plan_hash")), ""))
            if a:
                human = e.get("actor", "").startswith("human:") if isinstance(e.get("actor"), str) else False
                a["token_expires_epoch"] = _epoch(p.get("token_expires_at"))
                a["history"].append({"idx": idx, "epoch": epoch, "t": t, "status": "approved", "by": actor,
                                     "auto": not human, "detail": ""})
        elif kind == "rejected":
            a = approvals.get(latest.get(_s(p.get("plan_hash")), ""))
            if a:
                a["history"].append({"idx": idx, "epoch": epoch, "t": t, "status": "rejected", "by": actor,
                                     "detail": _s(p.get("reason"))})
        elif kind in ("executed", "rolled_back", "execute_refused"):
            pb, targets = _s(p.get("playbook")), _l(p.get("targets"))
            a = approvals.get(latest.get(_s(p.get("plan_hash")), "")) or find_plan(pb, targets)
            status = {"executed": "executed", "rolled_back": "rolled_back", "execute_refused": "refused"}[kind]
            detail = _s(p.get("detail") or p.get("reason"))
            if a:
                a["history"].append({"idx": idx, "epoch": epoch, "t": t, "status": status, "by": actor, "detail": detail,
                                     "stages": _l(p.get("stages"))})
            else:   # refused or executed without a visible request: keep it visible as its own card
                h = f"orphan-{idx}"
                approvals[h] = {"hash": h, "key": h, "playbook": pb, "title": "", "owner": actor, "targets": targets, "params": _d(p.get("params")),
                                "reason": "", "requested_idx": idx, "requested_epoch": epoch, "requested_t": t,
                                "expires_epoch": None, "token_expires_epoch": None, "executable": None,
                                "clone_test": {}, "verdicts": [],
                                "history": [{"idx": idx, "epoch": epoch, "t": t, "status": status, "by": actor, "detail": detail}]}
                approval_order.append(h)
            if kind == "executed":
                _apply_playbook(net, pb, targets, _d(p.get("params")), idx, epoch, t)
            elif kind == "rolled_back":
                _rollback(net, targets, idx, epoch, t)
        elif kind == "autonomy_set":
            mode = _s(p.get("mode")) or "MANUAL"
            state.update(mode=mode, expires=_epoch(p.get("expires")))
            push_auto(idx, epoch, t, f"{mode} for {_s(p.get('sites'))} / {_s(p.get('playbooks'))} by {_s(p.get('granted_by'))}",
                      state["expires"])
        elif kind == "autonomy_downgraded":
            state["mode"] = _s(p.get("to")) or "ASSISTED"
            push_auto(idx, epoch, t, "AUTO dropped to ASSISTED: " + _s(p.get("cause"), 120), state["expires"])
        elif kind == "kill_switch":
            state.update(killed=True, mode="MANUAL")
            push_auto(idx, epoch, t, "kill switch: " + _s(p.get("reason"), 120))
        elif kind == "kill_switch_released":
            state.update(killed=False, mode="MANUAL")
            push_auto(idx, epoch, t, "kill switch released")
        elif kind == "gap_human_decision":
            d = gap_drafts.get(_s(p.get("draft_id")))
            if d:
                d["status"] = _s(p.get("decision"))
                d["history"].append({"idx": idx, "status": d["status"]})
        elif kind == "gap_raised":
            gid = _s(p.get("gap_id") or p.get("id"))
            if gid:
                gap(gid, idx, epoch, t, "gap_raised by " + actor, title=_s(p.get("title")), topic=_s(p.get("topic")))
        elif kind == "verdict":
            for v in (_l(p.get("verdicts")) if "verdicts" in p else [p]):
                if isinstance(v, dict) and v.get("verdict"):
                    _add_verdict(verdicts, v, idx, epoch, t, actor, gap, kb_as_of=p.get("kb_as_of"))
        elif kind == "net_state":
            net.override(p)
            net.snap(idx, epoch, t, "net_state")

        # any other free-text mention of a gap id is shown as surfaced too
        events.append(ev)

    chain = verify_chain(entries)
    vlist = sorted(verdicts.values(), key=lambda v: v["first_idx"])
    for g in gaps.values():
        g.setdefault("title", "")
        g.setdefault("register_status", g.pop("status", None))
    stats = {"entries": len(entries), "bad_lines": bad_lines, "agents": len(agents), "verdicts": len(vlist),
             "messages": len(messages), "approvals": len(approvals),
             "duration_min": events[-1]["t"] if events else 0}
    meta.setdefault("start", dt.datetime.fromtimestamp(start, dt.timezone.utc).isoformat() if first else None)
    meta["start_epoch"] = start
    meta["name"] = name
    meta["has_rule_engine"] = bool(vlist) or meta.get("rules") is True
    return {"name": name, "meta": meta, "chain": chain, "stats": stats, "events": events,
            "verdicts": vlist, "messages": messages,
            "approvals": [approvals[h] for h in approval_order], "autonomy": autonomy,
            "gaps": sorted(gaps.values(), key=lambda g: (g["first_idx"], g["id"])),
            "gap_drafts": sorted(gap_drafts.values(), key=lambda g: g["idx"]),
            "agents": sorted(agents.values(), key=lambda a: a["name"]),
            "net": net.timeline, "alerts": list(alerts.values())}


def _add_verdict(store: dict, v: dict, idx: int, epoch, t, actor: str, gap_fn, kb_as_of=None) -> None:
    verdict = _s(v.get("verdict")).upper()
    key = (verdict, _s(v.get("rule_id")), _s(v.get("topic")), _s(v.get("gap_id")),
           tuple(sorted(_s(r) for r in _l(v.get("record_ids")))))
    cur = store.get(key)
    if cur:
        cur["repeats"] += 1
        if actor not in cur["seen_by"]:
            cur["seen_by"].append(actor)
        cur["last_idx"] = idx
        return
    gid = _s(v.get("gap_id")) or None
    store[key] = {"verdict": verdict, "known": verdict in VERDICTS, "rule_id": _s(v.get("rule_id")), "topic": _s(v.get("topic")),
                  "gap_id": gid, "record_ids": [_s(r) for r in _l(v.get("record_ids"))],
                  "explanation": _s(v.get("explanation")), "deadline": v.get("deadline"),
                  "time_left": v.get("time_left"), "notes": [_s(n) for n in _l(v.get("notes"))],
                  "kb_as_of": kb_as_of, "first_idx": idx, "last_idx": idx, "first_t": t, "first_epoch": epoch,
                  "seen_by": [actor], "repeats": 1}
    if gid:
        gap_fn(gid, idx, epoch, t, f"{verdict} verdict")


def _apply_playbook(net: _Net, pb: str, targets: list, params: dict, idx: int, epoch, t) -> None:
    scope, state, note = PB_EFFECT.get(pb, (None, None, ""))
    changed = False
    if scope == "failover":
        for site in _sites_in(targets):
            path = _s(params.get("path")) or "B"
            spec = topology.SITES[site]["paths"].get(path)
            if spec:
                net.sites[site].update({"state": "healed", "path": path, "gateway": spec[1],
                                        "note": f"PB-06 moved to path {path} ({spec[0]}, emulated if satellite)"})
                changed = True
    elif scope == "mgmt":
        net.mgmt = {"state": state, "note": f"{pb}: {note}"}
        changed = True
    elif scope == "gateway":
        for gw in [x for x in map(_s, targets) if x in net.gateways] or ["GW-IN-1"]:
            net.gateways[gw] = {"state": state, "note": f"{pb}: {note}"}
            changed = True
    elif scope == "site":
        for site in _sites_in(targets):
            cur = net.sites[site]
            if state and _RANK.get(cur["state"], 0) <= 1:
                cur["state"] = state
            cur["note"] = f"{pb}: {note}"
            changed = True
    if changed:
        net.snap(idx, epoch, t, f"{pb} executed")


def _rollback(net: _Net, targets: list, idx: int, epoch, t) -> None:
    for site in _sites_in(targets):
        net.sites[site]["note"] = "rolled back"
    net.snap(idx, epoch, t, "rolled back")
