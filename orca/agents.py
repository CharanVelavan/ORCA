"""Role agents: one Agent class plus one YAML role file per organisation (agents/roles/*.yaml).

What an agent may do is decided here, in code, not in its prompt (docs/plan/A-agent-roles.md section 1):
  - a tool not in the role's allow-list is refused;
  - each tool has an autonomy level (A0 read/draft, A1 engine/message/ask, A2 execute with a token);
    a role cannot use a tool above its ``max_level``; A3 acts (approve, edit KB, change a verdict,
    send a legal notice) have no tool at all;
  - execute_playbook goes through orca.remediation (owner, assets, one-time token, expiry, clone test,
    fresh verdict, preconditions);
  - record_gap writes a *draft* to the run state, never to kb/;
  - every record or gap id in the agent's final text is checked against the KB (check_citations).
Every tool call and every refusal is written to the hash-chained audit log.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from orca import rules
from orca.remediation import Refused, Remediation
from orca.world import World

ROLES_DIR = Path(__file__).resolve().parent.parent / "agents" / "roles"
MAX_TURNS = 8

LEVEL = {  # autonomy ladder
    "query_kb": 0, "read_alerts": 0, "explain_model": 0, "draft_notice": 0, "record_gap": 0,
    "run_rule_engine": 1, "select_playbook": 1, "send_message": 1, "request_approval": 1,
    "execute_playbook": 2,
}

COMMON_RULES = """Rules you must follow:
- You assess, draft and explain. Humans decide. You cannot approve plans, change a verdict, edit the knowledge base or send a legal notice.
- Policy verdicts come only from run_rule_engine. Never state a verdict, a deadline or a time yourself; quote the tool output.
- Cite only record ids and gap ids that a tool returned to you. Never invent an id, a clause or a quote.
- Times come only from tool outputs (the scenario clock). Never write a date or time of your own.
- Every satellite link is emulated. Say "not found in the sources we checked" for gaps, never "no law exists".
- Write short, plain sentences. End with one line: what you did, and what a human must decide."""

# OpenAI tool schemas
_S = lambda props, req: {"type": "object", "properties": props, "required": req}  # noqa: E731
TOOLS = {
    "query_kb": ("Search the knowledge base of verified legal records. Returns record ids, clauses and summaries.",
                 _S({"question": {"type": "string"}, "topic": {"type": "string"}}, ["question"])),
    "read_alerts": ("Read model alerts (M1-M4) and events, optionally for one site or source.",
                    _S({"site": {"type": "string"}, "source": {"type": "string"}}, [])),
    "explain_model": ("Get the model's own explanation (e.g. SHAP features) for one alert id.",
                      _S({"alert_id": {"type": "string"}}, ["alert_id"])),
    "draft_notice": ("Draft a notice. It stays a draft until a human sends it.",
                     _S({"kind": {"type": "string", "enum": ["certin_report", "dot_report", "downstream_warning",
                                                             "policy_brief", "information_request"]},
                         "recipient": {"type": "string"}, "body": {"type": "string"}}, ["kind", "recipient", "body"])),
    "record_gap": ("Record a DRAFT policy-gap finding for human review. Evidence must be existing record or gap ids.",
                   _S({"topic": {"type": "string"}, "finding": {"type": "string"},
                       "evidence": {"type": "array", "items": {"type": "string"}}}, ["topic", "finding", "evidence"])),
    "run_rule_engine": ("Run the deterministic rule engine on the current facts. Optionally add coverage questions "
                        "as {topic, text}. Returns verdicts with record ids, gap ids and deadlines.",
                        _S({"questions": {"type": "array", "items": _S({"topic": {"type": "string"},
                                                                         "text": {"type": "string"}},
                                                                        ["topic", "text"])}}, [])),
    "select_playbook": ("List playbooks from the fixed catalogue, with owner, preconditions and whether you own them.",
                        _S({"goal": {"type": "string"}}, [])),
    "send_message": ("Send a typed message to another role agent or to the human commander.",
                     _S({"to": {"type": "string"}, "kind": {"type": "string"}, "text": {"type": "string"}},
                        ["to", "kind", "text"])),
    "request_approval": ("Ask the human commander to approve a playbook plan. Returns the plan hash, expiry and "
                         "clone-test result.",
                         _S({"playbook": {"type": "string"}, "targets": {"type": "array", "items": {"type": "string"}},
                             "params": {"type": "object"}, "reason": {"type": "string"}},
                            ["playbook", "targets", "reason"])),
    "execute_playbook": ("Execute an approved playbook you own, with the one-time approval token from the commander.",
                         _S({"playbook": {"type": "string"}, "targets": {"type": "array", "items": {"type": "string"}},
                             "params": {"type": "object"}, "token": {"type": "string"}},
                            ["playbook", "targets", "token"])),
}

_ID = re.compile(r"(?<![\w-])((?:IN|EU|AE|INTL)-[A-Z0-9][A-Z0-9-]*[A-Z0-9]|GAP-(?:IN|EU|AE|INTL|CAND)-[A-Za-z0-9-]+)")


def known_ids(world: World) -> set[str]:
    ids = set(world.kb.records) | set(world.kb.gaps)
    for jur in ("IN", "EU", "AE"):
        r = rules.load_rules(jur)
        ids |= {x["id"] for k in ("clock_groups", "deadline_rules", "conflicts") for x in r[k]}
    return ids


def check_citations(text: str, world: World) -> list[str]:
    """Ids in ``text`` that are not in the KB, the gap register or the rule files."""
    known = known_ids(world)
    return sorted({m for m in _ID.findall(text or "") if m not in known and not m.startswith("GAP-CAND-")})


@dataclass
class Role:
    name: str
    organisation: str
    reports_to: str
    max_level: int
    tools: list[str]
    owns: list[str]
    prompt: str
    everyday: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, name: str, roles_dir: Path = ROLES_DIR) -> "Role":
        d = yaml.safe_load((roles_dir / f"{name}.yaml").read_text())
        unknown = set(d["tools"]) - set(TOOLS)
        if unknown:
            raise ValueError(f"role {name}: unknown tools {sorted(unknown)}")
        return cls(name=d["name"], organisation=d["organisation"], reports_to=d["reports_to"],
                   max_level=d["max_level"], tools=d["tools"], owns=d.get("owns", []), prompt=d["prompt"],
                   everyday=d.get("everyday", []))


def all_roles() -> list[str]:
    return sorted(p.stem for p in ROLES_DIR.glob("*.yaml"))


class Agent:
    def __init__(self, role: Role | str, world: World, llm, remediation: Remediation | None = None):
        self.role = Role.load(role) if isinstance(role, str) else role
        self.w = world
        self.llm = llm
        self.rem = remediation or Remediation(world)

    # ---------------------------------------------------------------- loop
    def run(self, task: str) -> dict:
        r = self.role
        system = f"You are the {r.name.replace('_', ' ')} agent for {r.organisation}.\n{r.prompt}\n\n{COMMON_RULES}"
        user = f"Scenario clock: {self.w.now}. Task: {task}"
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        tools = [{"type": "function", "function": {"name": n, "description": TOOLS[n][0], "parameters": TOOLS[n][1]}}
                 for n in r.tools if LEVEL[n] <= r.max_level]
        calls = []
        self.w.log("agent_task", r.name, {"task": task})
        for _ in range(MAX_TURNS):
            msg = self.llm.chat(messages, tools)
            messages.append({k: v for k, v in msg.items() if v})
            if not msg.get("tool_calls"):
                break
            for tc in msg["tool_calls"]:
                name = tc["function"]["name"]
                try:
                    args = json.loads(tc["function"].get("arguments") or "{}")
                except json.JSONDecodeError:
                    args = {}
                out = self.call(name, args)
                calls.append({"tool": name, "args": args, "ok": "refused" not in out})
                messages.append({"role": "tool", "tool_call_id": tc.get("id", name), "content": json.dumps(out)})
        text = (messages[-1].get("content") if messages[-1]["role"] == "assistant" else None) or ""
        bad = check_citations(text, self.w)
        self.w.log("agent_say", r.name, {"text": text, "unknown_ids": bad})
        return {"role": r.name, "text": text, "tool_calls": calls, "unknown_ids": bad, "messages": messages}

    # ---------------------------------------------------------------- dispatch
    def call(self, name: str, args: dict) -> dict:
        r = self.role
        if name not in TOOLS:
            out = {"refused": f"unknown tool {name}"}
        elif name not in r.tools:
            out = {"refused": f"{name} is not in the {r.name} allow-list"}
        elif LEVEL[name] > r.max_level:
            out = {"refused": f"{name} needs autonomy A{LEVEL[name]}; {r.name} is limited to A{r.max_level}"}
        else:
            try:
                out = getattr(self, f"t_{name}")(**args)
            except Refused as e:
                out = {"refused": str(e)}
            except TypeError as e:
                out = {"refused": f"bad arguments for {name}: {e}"}
        self.w.log("agent_tool", r.name, {"tool": name, "args": args, "result": out})
        return out

    # ---------------------------------------------------------------- tools (A0)
    def t_query_kb(self, question: str, topic: str | None = None) -> dict:
        """Keyword retrieval over verified records (ChromaDB replaces this later; same output)."""
        words = {w for w in re.findall(r"[a-z0-9]+", question.lower()) if len(w) > 2}
        hits = []
        for rid, rec in self.w.kb.records.items():
            if topic and topic not in rec.get("topics", [rec.get("topic")]):
                continue
            hay = " ".join(str(rec.get(k, "")) for k in ("instrument", "clause", "summary", "quote", "topics")).lower()
            score = sum(1 for w in words if w in hay) / max(1, len(words))
            if score >= 0.25 or topic:
                hits.append((score, rid, rec))
        hits.sort(key=lambda h: (-h[0], h[1]))
        if not hits:
            return {"results": [], "note": "no record matched; do not answer from memory"}
        return {"results": [{"id": rid, "clause": rec["clause"], "instrument": rec["instrument"],
                             "binding_status": rec["binding_status"], "verified": rec.get("verified", False),
                             "summary": rec.get("summary", "")} for _, rid, rec in hits[:5]]}

    def t_read_alerts(self, site: str | None = None, source: str | None = None) -> dict:
        a = [x for x in self.w.alerts if (not site or x.get("site") == site) and (not source or x.get("source") == source)]
        return {"alerts": [{k: v for k, v in x.items() if k != "explain"} for x in a[-20:]],
                "messages_to_me": [m for m in self.w.bus if self.role.name in (m["to"] if isinstance(m["to"], list)
                                                                               else [m["to"]])][-10:]}

    def t_explain_model(self, alert_id: str) -> dict:
        for x in self.w.alerts:
            if x.get("id") == alert_id:
                return {"alert_id": alert_id, "source": x.get("source"), "explain": x.get("explain", {})}
        return {"refused": f"no alert {alert_id}"}

    def t_draft_notice(self, kind: str, recipient: str, body: str) -> dict:
        bad = check_citations(body, self.w)
        d = {"id": f"DRAFT-{len(self.w.drafts) + 1:03d}", "at": self.w.now, "by": self.role.name, "kind": kind,
             "recipient": recipient, "body": body, "status": "draft - a human sends it", "unknown_ids": bad}
        self.w.drafts.append(d)
        return {"draft_id": d["id"], "status": d["status"], "unknown_ids": bad}

    def t_record_gap(self, topic: str, finding: str, evidence: list[str]) -> dict:
        known = known_ids(self.w)
        missing = [e for e in evidence if e not in known]
        if not evidence or missing:
            raise Refused(f"evidence must be existing record or gap ids; unknown: {missing or 'none given'}")
        registered = [g["id"] for g in self.w.kb.gaps.values() if g.get("topic") == topic]
        d = {"id": f"GAPDRAFT-{len(self.w.gap_drafts) + 1:03d}", "at": self.w.now, "by": self.role.name,
             "topic": topic, "finding": finding, "evidence": evidence, "matches_registered": registered,
             "status": "draft - human review; not written to kb/"}
        self.w.gap_drafts.append(d)
        return {"draft_id": d["id"], "matches_registered": registered, "status": d["status"]}

    # ---------------------------------------------------------------- tools (A1)
    def t_run_rule_engine(self, questions: list[dict] | None = None) -> dict:
        facts = dict(self.w.facts)
        if questions:
            extra = [{"id": f"Q-{self.role.name}-{i}", "topic": q["topic"], "text": q["text"]}
                     for i, q in enumerate(questions, 1)]
            facts["obligation_questions"] = list(facts.get("obligation_questions") or []) + extra
        out = []
        for v in rules.evaluate(facts, self.w.kb):
            out.append({k: getattr(v, k) for k in ("verdict", "rule_id", "topic", "gap_id", "record_ids",
                                                    "explanation", "deadline", "time_left")})
        return {"kb_as_of": str(self.w.kb.as_of), "verdicts": out, "footer": rules.FOOTER}

    def t_select_playbook(self, goal: str | None = None) -> dict:
        return {"playbooks": [{"id": p["id"], "title": p["title"], "owner": p["owner"],
                               "executable": p.get("executable", False), "you_own": p["owner"] == self.role.name,
                               "preconditions": p.get("preconditions", [])} for p in self.rem.cat.values()]}

    def t_send_message(self, to: str, kind: str, text: str) -> dict:
        m = {"at": self.w.now, "sender": self.role.name, "to": to, "kind": kind, "payload": {"text": text},
             "unknown_ids": check_citations(text, self.w)}
        self.w.bus.append(m)
        return {"sent": True, "unknown_ids": m["unknown_ids"]}

    def t_request_approval(self, playbook: str, targets: list[str], reason: str, params: dict | None = None) -> dict:
        p = self.rem.request_approval(self.role.name, playbook, targets, params, reason)
        return {k: p[k] for k in ("hash", "playbook", "targets", "expires_at", "executable", "clone_test")} | {
            "status": "waiting for the human commander"}

    # ---------------------------------------------------------------- tools (A2)
    def t_execute_playbook(self, playbook: str, targets: list[str], token: str, params: dict | None = None) -> dict:
        return self.rem.execute(self.role.name, playbook, targets, params, token)
