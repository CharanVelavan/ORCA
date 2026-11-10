"""Role agents, the policy/legal adviser, the human commander and the per-agent event feed.

One ``Agent`` class plus one YAML file per role in ``agents/roles/`` (mandate, what it sees, tools,
owned playbooks, sharing limits, prompt, worked example). What an agent may do is decided here, in
code, not in its prompt (docs/plan/A-agent-roles.md section 1, docs/AGENTS.md):

  - different information: an agent sees only scenario events released to it (``EventFeed``), only
    alerts whose ``visible_to`` names it, and only messages addressed to it;
  - different tools: the LLM is sent only the role's allow-listed tools, and a call to any other
    tool is refused; each tool has an autonomy level (A0 read/draft, A1 engine/message/ask/approval
    request, A2 execute with a token); A3 acts (approve, confirm a gap, edit the KB, change a
    verdict, send a legal notice) have no tool at all;
  - coordination only through ``orca.protocol`` (typed, validated, rejected + logged on violation);
  - execute_playbook only through ``orca.remediation`` (owner, assets, one-time token, expiry,
    clone test, fresh verdict, preconditions); never bypassed;
  - every step is written to the hash-chained audit as ``agent_step``: model reasoning (if the
    model returned any), a REQUIRED rationale, and citations split into accepted / rejected;
  - a citation is accepted only if it is a KB record id, a non-rejected gap id, or a real
    vector-KB chunk id (``orca.kbvec.get_chunk``); everything else is rejected and logged;
  - verdicts come only from the rule engine; gap drafts are only "pre-confirmed" by an agent and
    confirmed or rejected by a human (``Commander.decide_gap``), never written to kb/.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from orca import kb as kbmod
from orca import rules
from orca.protocol import (COMMANDER, DATA_CLASSES, ID_RE, TYPES, Message, Protocol, _kbvec,
                           check_citations as split_citations, classify_citation, unknown_ids_in_text)
from orca.remediation import Refused, Remediation
from orca.world import DEPENDANTS, World

ROLES_DIR = Path(__file__).resolve().parent.parent / "agents" / "roles"
MAX_TURNS = 8
SITES = sorted(DEPENDANTS)
MODEL_SOURCES = ("M1", "M2", "M3", "M4")
VERDICT_WORDS = sorted(rules.VERDICTS)
NOTICE_KINDS = ("certin_report", "dot_report", "downstream_warning", "policy_brief", "information_request",
                "advisory")

LEVEL = {  # autonomy ladder (A3 has no tool)
    "read_alerts": 0, "explain_model": 0, "query_kb": 0, "ask_adviser": 0, "draft_notice": 0, "record_gap": 0,
    "run_rule_engine": 1, "select_playbook": 1, "send_message": 1, "request_approval": 1,
    "execute_playbook": 2,
}

COMMON_RULES = """Rules you must follow:
- You assess, draft, explain and propose. Humans decide. You cannot approve a plan, confirm a gap, change a verdict, edit the knowledge base or send a legal notice.
- Policy verdicts come only from run_rule_engine. Never state a verdict, a deadline or a time yourself; quote the tool output.
- Cite only record ids, gap ids or chunk ids that a tool returned to you. Never invent an id, a clause or a quote.
- Every tool call needs a one-line "rationale" argument: why you make this call.
- To run a playbook: request_approval first; execute_playbook only after the commander sends you a token.
- Coordinate only with send_message. Share only what your mandate allows.
- Every satellite link is emulated. For a missing rule say "not found in the sources we checked", never "no law exists".
- Final answer: short plain sentences, then one line "Citations: <ids>" and one line "Human decision needed: <...>"."""

# ------------------------------------------------------------------------------------------- tools
_RAT = {"rationale": {"type": "string", "description": "One short sentence: why you make this call."}}


def _S(props: dict, req: list[str]) -> dict:  # noqa: N802
    return {"type": "object", "properties": {**props, **_RAT}, "required": [*req, "rationale"]}


_TOPICS = sorted(kbmod.TOPICS)
TOOLS = {
    "read_alerts": (
        "Read the events, model alerts and messages released to YOU. source=M3 gives the fault-or-attack "
        "classification, source=M1 anomalies, M2 forecasts, M4 capacity; source=any gives everything. "
        "Use site only to narrow to one tower.",
        _S({"source": {"type": "string", "enum": ["any", *MODEL_SOURCES, "scenario"]},
            "site": {"type": "string", "enum": ["any", *SITES]}}, [])),
    "explain_model": (
        "Get the model's own explanation for one alert id that read_alerts returned to you.",
        _S({"alert_id": {"type": "string"}}, ["alert_id"])),
    "query_kb": (
        "Search the legal knowledge base (verified records and the document corpus). Returns ids you may cite.",
        _S({"question": {"type": "string"}, "topic": {"type": "string", "enum": _TOPICS}}, ["question"])),
    "ask_adviser": (
        "Ask the policy/legal adviser a question. It answers only from the knowledge base, with citations, "
        "or says the answer was not found in the sources checked.",
        _S({"question": {"type": "string"}}, ["question"])),
    "draft_notice": (
        "Draft a notice. It stays a draft until a human sends it. Put the ids you rely on in citations.",
        _S({"kind": {"type": "string", "enum": list(NOTICE_KINDS)}, "recipient": {"type": "string"},
            "body": {"type": "string"}, "citations": {"type": "array", "items": {"type": "string"}}},
           ["kind", "recipient", "body"])),
    "record_gap": (
        "Pre-confirm a policy gap for HUMAN review (only a human confirms). Evidence must be record, gap or "
        "chunk ids that a tool returned.",
        _S({"topic": {"type": "string", "enum": _TOPICS}, "finding": {"type": "string"},
            "evidence": {"type": "array", "items": {"type": "string"}}}, ["topic", "finding", "evidence"])),
    "run_rule_engine": (
        "Run the deterministic rule engine on the current facts (the only source of verdicts and deadlines). "
        "Optionally add coverage questions as {topic, text}.",
        _S({"questions": {"type": "array", "items": {
            "type": "object", "properties": {"topic": {"type": "string", "enum": _TOPICS}, "text": {"type": "string"}},
            "required": ["topic", "text"]}}}, [])),
    "select_playbook": (
        "LIST the fixed playbook catalogue (read only; it does not run or request anything). To act, call "
        "request_approval next.",
        _S({"goal": {"type": "string"}}, [])),
    "send_message": (
        "Send a typed protocol message to other agents or the commander. Types: inform, request, propose "
        "(name a playbook), object (reply to a message id). refs = evidence ids (alerts, records, gaps, plans).",
        _S({"to": {"type": "array", "items": {"type": "string"}},
            "type": {"type": "string", "enum": [t for t in TYPES if t != "approve_request"]},
            "text": {"type": "string"},
            "refs": {"type": "array", "items": {"type": "string"}},
            "data_class": {"type": "string", "enum": ["operational", "technical_indicator", "legal_direction"]},
            "playbook": {"type": "string"}, "in_reply_to": {"type": "string"}}, ["to", "type", "text"])),
    "request_approval": (
        "Ask the human commander to approve a playbook you own, on your own targets. Returns the plan hash, "
        "expiry and clone-test result. This is the step BEFORE execute_playbook.",
        _S({"playbook": {"type": "string"}, "targets": {"type": "array", "items": {"type": "string"}},
            "params": {"type": "object"}, "reason": {"type": "string"}}, ["playbook", "targets", "reason"])),
    "execute_playbook": (
        "Execute an APPROVED playbook you own, with the one-time token the commander sent you. Without a "
        "token it is refused: call request_approval instead.",
        _S({"playbook": {"type": "string"}, "targets": {"type": "array", "items": {"type": "string"}},
            "params": {"type": "object"}, "token": {"type": "string"}}, ["playbook", "targets", "token"])),
}

# Next-step hints added to tool results (helps small models choose the next tool).
NEXT = {
    "read_alerts": "next: explain_model(alert_id) for why a model fired; run_rule_engine for policy; "
                   "send_message to tell a party that needs to know.",
    "explain_model": "next: quote these features as the model's reasons; do not add causes of your own.",
    "query_kb": "next: cite only the ids above. If nothing fits, say 'not found in the sources we checked'.",
    "ask_adviser": "next: quote the adviser's citations; do not add law of your own.",
    "run_rule_engine": "next: quote each verdict with its record ids. For POTENTIAL_GAP you may call record_gap "
                       "with evidence = the record ids and gap id shown. Do not change a verdict.",
    "select_playbook": "next: to act, call request_approval(playbook, targets, params, reason) for a playbook "
                       "with you_own=true. Never call execute_playbook without a token from the commander.",
    "request_approval": "next: wait for the commander. Do NOT call execute_playbook until a message gives you "
                        "a token. You may inform other parties with send_message.",
    "execute_playbook": "next: report the outcome with send_message to the parties affected.",
    "send_message": "next: continue your assessment or give your final answer.",
    "draft_notice": "next: a human reviews and sends the draft; you cannot send it.",
    "record_gap": "next: the gap is pre-confirmed only; a human confirms or rejects it.",
}


# ------------------------------------------------------------------------------------------- roles
@dataclass
class Role:
    name: str
    kind: str                     # agent | adviser | human
    organisation: str
    mandate: str
    reports_to: str
    max_level: int
    tools: list[str]
    owns: list[str]
    prompt: str
    sees: dict = field(default_factory=dict)        # {signals: [...], sources: [...]}
    sharing: dict = field(default_factory=dict)     # protocol limits (see orca/protocol.py)
    notice_kinds: list[str] = field(default_factory=list)
    example: str = ""
    everyday: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, name: str, roles_dir: Path = ROLES_DIR) -> "Role":
        d = yaml.safe_load((roles_dir / f"{name}.yaml").read_text())
        unknown = set(d.get("tools", [])) - set(TOOLS)
        if unknown:
            raise ValueError(f"role {name}: unknown tools {sorted(unknown)}")
        over = [t for t in d.get("tools", []) if LEVEL[t] > d.get("max_level", 0)]
        if over:
            raise ValueError(f"role {name}: tools {over} exceed max_level A{d.get('max_level', 0)}")
        if d["name"] != name:
            raise ValueError(f"role file {name}.yaml has name {d['name']}")
        role_tools = list(d.get("tools", []))
        if not (d.get("sees", {}).get("signals") or d.get("sees", {}).get("sources")):
            role_tools = [t for t in role_tools if t != "read_alerts"]
        return cls(name=d["name"], kind=d.get("kind", "agent"), organisation=d["organisation"],
                   mandate=d.get("mandate", ""), reports_to=d["reports_to"], max_level=d.get("max_level", 0),
                   tools=role_tools, owns=d.get("owns", []), prompt=d.get("prompt", ""),
                   sees=d.get("sees") or {}, sharing=d.get("sharing") or {},
                   notice_kinds=d.get("notice_kinds") or list(NOTICE_KINDS), example=d.get("example", ""),
                   everyday=d.get("everyday", []))

    def tool_schemas(self) -> list[dict]:
        out = []
        for n in self.tools:
            # Empty-feed roles have nothing useful to read; keep legacy direct dispatch safe while
            # withholding the empty tool from the model's advertised schema.
            desc, params = TOOLS[n]
            params = json.loads(json.dumps(params))
            props = params["properties"]
            if n in ("request_approval", "execute_playbook") and self.owns:
                props["playbook"]["enum"] = list(self.owns)
            if n == "draft_notice":
                props["kind"]["enum"] = list(self.notice_kinds)
            if n == "send_message":
                props["to"]["items"]["enum"] = [r for r in agent_roles() if r != self.name] + [COMMANDER]
                props["type"]["enum"] = [t for t in self.sharing.get("may_send", ["inform"]) if t != "approve_request"]
                props["data_class"]["enum"] = list(self.sharing.get("may_share", ["operational"]))
            out.append({"type": "function", "function": {"name": n, "description": desc, "parameters": params}})
        return out

    def system_prompt(self) -> str:
        org = self.organisation
        parts = [f"You are the {self.name.replace('_', ' ')} agent for {org} in an EMULATED satellite-backed "
                 f"network in Chennai.", f"Mandate: {self.mandate.strip()}", self.prompt.strip(),
                 f"You report to: {self.reporting()}."]
        if self.owns:
            parts.append(f"Playbooks you own: {', '.join(self.owns)}. You may run only these, on your own assets.")
        else:
            parts.append("You own no playbooks and can never execute one.")
        if self.example:
            parts.append("Example:\n" + self.example.strip())
        parts.append(COMMON_RULES)
        return "\n\n".join(p for p in parts if p)

    def reporting(self) -> str:
        return self.reports_to


def all_roles() -> list[str]:
    return sorted(p.stem for p in ROLES_DIR.glob("*.yaml"))


def agent_roles() -> list[str]:
    return [n for n in all_roles() if (yaml.safe_load((ROLES_DIR / f"{n}.yaml").read_text()) or {})
            .get("kind", "agent") == "agent"]


def load_agent_roles() -> dict[str, Role]:
    return {n: Role.load(n) for n in agent_roles()}


# ------------------------------------------------------------------------------- citation helpers
def known_ids(world: World) -> set[str]:
    """Record ids, non-rejected gap ids and rule ids (for free-text checks)."""
    from orca.protocol import rule_ids  # noqa: PLC0415
    return (set(world.kb.records) | {g for g, v in world.kb.gaps.items() if v.get("status") != "rejected"}
            | rule_ids())


def check_citations(text: str, world: World) -> list[str]:
    """KB-looking ids in ``text`` that are not in the KB, the gap register or the rule files."""
    return unknown_ids_in_text(text, world.kb)


def citations_in_text(text: str, kb, chunk_ids: set[str] = frozenset()) -> tuple[list[str], list[str]]:
    """(accepted, rejected) citations found in free text. Rule ids are neither."""
    from orca.protocol import rule_ids  # noqa: PLC0415
    rids = rule_ids()
    found = [m for m in ID_RE.findall(text or "") if m not in rids]
    found += [c for c in chunk_ids if c and c in (text or "")]
    acc, rej = split_citations(list(dict.fromkeys(found)), kb)
    return acc, rej


# ------------------------------------------------------------------------------------ event feed
def _merge_facts(facts: dict, add: dict | None) -> None:
    for k, v in (add or {}).items():
        if isinstance(v, list):
            facts.setdefault(k, []).extend(v)
        elif isinstance(v, dict):
            facts.setdefault(k, {}).update(v)
        else:
            facts[k] = v


class EventFeed:
    """Releases scenario events progressively and unevenly: each event reaches only some agents.

    Routing (first match wins): an explicit ``to: [roles]`` on the event; the event's actor if it is a
    role; else, for model, attacker and environment events, the roles whose ``sees.signals`` include one
    of the event's signals, or whose ``sees.sources`` include the actor. Attacker and environment
    events never reveal their ground-truth text, only the signals observed. Commander decisions go to
    every agent; judge events go to nobody.
    """

    def __init__(self, scenario: dict, roles: dict[str, Role]):
        self.sc = scenario
        self.roles = roles
        self.start = rules.parse_ts(scenario["start"])
        self.released: set[int] = set()

    def route(self, e: dict) -> list[str]:
        if e.get("to"):
            return [r for r in e["to"] if r in self.roles]
        actor = e.get("actor")
        if actor in self.roles:
            return [actor]
        if actor == "commander":
            return list(self.roles)
        if actor == "judge":
            return []
        sigs = {s.get("signal") for s in e.get("signals") or []}
        out = [n for n, r in self.roles.items()
               if sigs & set(r.sees.get("signals", [])) or (not sigs and actor in r.sees.get("sources", []))]
        return out

    def alert_for(self, i: int, e: dict, visible_to: list[str]) -> dict:
        actor = e.get("actor")
        sigs = e.get("signals") or []
        sites = sorted({s.get("site") for s in sigs if s.get("site")})
        if actor in ("attacker", "environment"):
            detail = "Signals observed: " + "; ".join(f"{s['site']} {s['signal']}={s.get('value')}" for s in sigs)
            source, label = "scenario", "observation"
        else:
            detail = e.get("what", "")
            source = actor if actor in MODEL_SOURCES else "scenario"
            label = {"M1": "anomaly", "M2": "forecast", "M4": "capacity"}.get(actor, actor)
            if actor == "M3":
                label = self.sc.get("m3_expected", "abstain")
        at = (self.start + dt.timedelta(minutes=e["t"])).isoformat()
        explain = {"note": "scenario stand-in until the M1-M4 models are wired", "signals": sigs}
        return {"id": f"EV-{self.sc['id']}-T{e['t']:03d}-{i}", "at": at, "t": e["t"], "source": source,
                "actor": actor, "site": sites[0] if sites else None, "sites": sites, "label": label,
                "detail": detail, "signals": sigs, "explain": explain, "visible_to": visible_to}

    def release(self, world: World, upto_t: float) -> dict[str, list[dict]]:
        """Release every event with t <= upto_t; merge its facts; return {role: [new alerts]}."""
        out: dict[str, list[dict]] = {}
        for i, e in enumerate(self.sc["events"]):
            if i in self.released or e["t"] > upto_t:
                continue
            self.released.add(i)
            _merge_facts(world.facts, e.get("facts"))
            world.facts["now"] = (self.start + dt.timedelta(minutes=e["t"])).isoformat()
            vis = self.route(e)
            a = self.alert_for(i, e, vis)
            world.alerts.append(a)
            world.log("event_released", "scenario", {"alert_id": a["id"], "visible_to": vis, "t": e["t"]})
            for r in vis:
                out.setdefault(r, []).append(a)
        return out


# ---------------------------------------------------------------------------------- the adviser
_STOP = set("""a an the of to in on for and or is are be been was were it its this that these those what which who
whom how when where why does do did can could should would may might must shall will with without by from as at
any all there their our we you i me my under per than then into about against between during before after over
not no yes if so such same other more most some each only own also law laws rule rules india indian""".split())


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", (text or "").lower().replace("_", " ")) if len(w) > 2 and w not in _STOP}


class PolicyAdviser:
    """"Ask the adviser": answers only from the KB (verified records, gap register, vector corpus).

    Any agent or the human can call ``ask``. It never gives a verdict (the rule engine does) and never
    answers beyond the KB: with no relevant source it returns
    "Not found in the sources we checked, as of <kb_as_of>." With an LLM it phrases the answer from the
    retrieved passages only; every citation is checked and, if any is outside the retrieved set or the
    text states a verdict, the LLM answer is discarded for a deterministic quote of the sources.
    """

    MIN_MATCH = 2
    MIN_RATIO = 0.4

    def __init__(self, world: World, llm=None, jurisdictions: tuple[str, ...] = ("IN", "INTL", "EU", "AE", "US")):
        self.w = world
        self.llm = llm
        self.jur = jurisdictions

    @property
    def kb_as_of(self) -> str:
        return str(self.w.kb.as_of)

    def refusal(self) -> str:
        return f"Not found in the sources we checked, as of {self.kb_as_of}."

    def retrieve(self, question: str, k: int = 5) -> list[dict]:
        q = _words(question)
        if not q:
            return []
        hits = []
        for rid, r in self.w.kb.records.items():
            if r["jurisdiction"] not in self.jur:
                continue
            hay = _words(" ".join(str(r.get(x, "")) for x in ("instrument", "clause", "authority", "summary",
                                                               "quote", "topics")))
            m = len(q & hay)
            hits.append((m, rid, {"id": rid, "kind": "record", "title": f"{r['instrument']}, {r['clause']}",
                                  "jurisdiction": r["jurisdiction"], "binding_status": r["binding_status"],
                                  "verified": bool(r.get("verified")),
                                  "text": r.get("quote") or r.get("summary", ""), "summary": r.get("summary", "")}))
        for gid, g in self.w.kb.gaps.items():
            if g.get("status") == "rejected":
                continue
            hay = _words(" ".join(str(g.get(x, "")) for x in ("title", "finding", "topic")))
            m = len(q & hay)
            hits.append((m, gid, {"id": gid, "kind": "gap", "title": g["title"], "jurisdiction": g["jurisdiction"],
                                  "status": g["status"], "verified": bool(g.get("verified")),
                                  "text": g.get("finding", "")}))
        vec = _kbvec()
        if vec is not None:
            try:
                for c in vec.search_with_abstention(question, k=k, filters=None, rerank=True)["results"]:
                    m = len(q & _words(c.get("text", "")))
                    hits.append((m, c["chunk_id"], {"id": c["chunk_id"], "kind": "chunk", "title": c.get("title"),
                                                    "jurisdiction": c.get("jurisdiction"),
                                                    "binding_status": c.get("binding_status"),
                                                    "verified": False, "tier": c.get("tier"),
                                                    "page": c.get("page"), "clause": c.get("clause"),
                                                    "text": c.get("text", "")[:900]}))
            except Exception as e:  # noqa: BLE001
                self.w.log("adviser_vector_error", "policy_adviser", {"error": str(e)[:300]})
        need = max(1, min(self.MIN_MATCH, len(q)))
        good = [h for h in hits if h[0] >= need and h[0] / len(q) >= self.MIN_RATIO]
        good.sort(key=lambda h: (h[2]["kind"] == "chunk", -h[0], h[2]["kind"] != "record", h[1]))  # verified records and gaps before corpus chunks
        return [h[2] for h in good[:k]]

    def ask(self, question: str, asker: str = "human") -> dict:
        srcs = self.retrieve(question)
        if not srcs:
            out = {"found": False, "answer": self.refusal(), "citations": [], "sources": [],
                   "kb_as_of": self.kb_as_of, "mode": "refusal"}
        else:
            out = self._answer_llm(question, srcs) if self.llm else None
            out = out or self._answer_quote(srcs)
            out |= {"found": True, "sources": [{k: s.get(k) for k in ("id", "kind", "title", "verified",
                                                                        "binding_status", "status", "tier")}
                                               for s in srcs], "kb_as_of": self.kb_as_of}
        self.w.log("adviser_answer", "policy_adviser", {"asker": asker, "question": question, **out})
        return out

    def _answer_quote(self, srcs: list[dict]) -> dict:
        lines = [f"From the sources we checked (KB as of {self.kb_as_of}):"]
        for s in srcs[:3]:
            tag = "verified record" if s["kind"] == "record" and s["verified"] else \
                  "gap register, human-" + str(s.get("status")) if s["kind"] == "gap" else "unverified corpus"
            lines.append(f"- {s['title']} [{s['id']}] ({tag}): {s.get('summary') or s['text'][:300]}")
        lines.append("This is a reading of the sources, not a verdict or legal advice.")
        return {"answer": "\n".join(lines), "citations": [s["id"] for s in srcs[:3]], "mode": "quote"}

    def _answer_llm(self, question: str, srcs: list[dict]) -> dict | None:
        ids = [s["id"] for s in srcs]
        ctx = "\n".join(f"[{s['id']}] {s['title']} ({s['kind']}, verified={s['verified']}): {s['text'][:700]}"
                        for s in srcs)
        sysmsg = ("You are the policy and legal adviser. Answer ONLY from the sources below. Cite source ids in "
                  "square brackets. Never give a compliance verdict. If the sources do not answer the question, "
                  'reply exactly NOT_FOUND. Reply as JSON: {"answer": "...", "citations": ["id", ...]}.')
        try:
            msg = self.llm.chat([{"role": "system", "content": sysmsg},
                                 {"role": "user", "content": f"Sources:\n{ctx}\n\nQuestion: {question}"}], None)
        except Exception as e:  # noqa: BLE001
            self.w.log("adviser_llm_error", "policy_adviser", {"error": str(e)[:300]})
            return None
        raw = (msg.get("content") or "").strip()
        if "NOT_FOUND" in raw:
            return {"answer": self.refusal(), "citations": [], "mode": "llm_not_found"}
        try:
            d = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
            ans, cits = str(d["answer"]), [str(c) for c in d.get("citations", [])]
        except (ValueError, KeyError, TypeError):
            return None
        if not ans.strip() or re.sub(r"[^a-z0-9]+", "", ans.lower()) == re.sub(r"[^a-z0-9]+", "", question.lower()):
            self.w.log("adviser_llm_discarded", "policy_adviser", {"reason": "empty_or_echoed_question", "answer": ans, "citations": cits})
            return None
        cits = list(dict.fromkeys(cits + [c for c in ids if f"[{c}]" in ans]))
        stray = [c for c in ID_RE.findall(ans) if c not in ids]
        if not cits or any(c not in ids for c in cits) or stray or any(v in ans for v in VERDICT_WORDS):
            self.w.log("adviser_llm_discarded", "policy_adviser", {"answer": ans, "citations": cits, "stray": stray})
            return None
        return {"answer": ans, "citations": cits, "mode": "llm", "reasoning": _reasoning(msg)}


# ------------------------------------------------------------------------------------- the agent
def _reasoning(msg: dict) -> str | None:
    r = msg.get("reasoning_content") or msg.get("reasoning")
    return str(r)[:4000] if r else None


def _as_list(v) -> list:
    if v is None:
        return []
    if isinstance(v, str):
        return [x.strip() for x in v.split(",") if x.strip()]
    return list(v)


class Agent:
    def __init__(self, role: Role | str, world: World, llm, remediation: Remediation | None = None,
                 protocol: Protocol | None = None, adviser: PolicyAdviser | None = None):
        self.role = Role.load(role) if isinstance(role, str) else role
        self.w = world
        self.llm = llm
        self.rem = remediation or Remediation(world)
        self.proto = protocol or Protocol(world, load_agent_roles() | {self.role.name: self.role}, self.rem)
        self.adviser = adviser or PolicyAdviser(world)
        self.seen_chunks: set[str] = set()
        self.engine_verdicts: set[str] = set()

    # ---------------------------------------------------------------- loop
    def run(self, task: str) -> dict:
        r = self.role
        messages = [{"role": "system", "content": r.system_prompt()},
                    {"role": "user", "content": f"Scenario clock: {self.w.now}. Task: {task}"}]
        tools = r.tool_schemas()
        calls, errors, retried = [], 0, False
        self.w.log("agent_task", r.name, {"task": task, "tools": [t["function"]["name"] for t in tools]})
        text, final_msg = "", {}
        for turn in range(1, MAX_TURNS + 1):
            msg = self.llm.chat(messages, tools)
            messages.append({k: v for k, v in msg.items() if v and k in ("role", "content", "tool_calls")})
            if not msg.get("tool_calls"):
                text, final_msg = msg.get("content") or "", msg
                acc, rej = citations_in_text(text, self.w.kb, self.seen_chunks)
                if rej and not retried and turn < MAX_TURNS:
                    retried = True
                    self._step(turn, msg, None, {}, text, acc, rej, {"retry": "rejected citations"})
                    messages.append({"role": "user", "content": f"These ids are not in the knowledge base: {rej}. "
                                     "Rewrite your answer citing only ids that a tool returned."})
                    continue
                break
            for tc in msg["tool_calls"]:
                name = tc["function"]["name"]
                try:
                    args = json.loads(tc["function"].get("arguments") or "{}")
                    if not isinstance(args, dict):
                        raise ValueError
                except (json.JSONDecodeError, ValueError):
                    args = {"_unparsed": tc["function"].get("arguments")}
                out = self.call(name, args, turn=turn, msg=msg)
                ok = "refused" not in out and "rejected" not in out
                errors += 0 if ok else 1
                calls.append({"tool": name, "args": {k: v for k, v in args.items() if k != "rationale"}, "ok": ok,
                              **({"refused": out.get("refused") or out.get("rejected")} if not ok else {})})
                messages.append({"role": "tool", "tool_call_id": tc.get("id") or name,
                                 "content": json.dumps(out, default=str)})
        acc, rej = citations_in_text(text, self.w.kb, self.seen_chunks)
        stray_verdicts = [v for v in VERDICT_WORDS if re.search(rf"\b{v}\b", text) and v not in self.engine_verdicts]
        self._step(None, final_msg, None, {}, text, acc, rej, {"final": True, "verdicts_not_from_engine": stray_verdicts})
        return {"role": r.name, "text": text, "tool_calls": calls, "tool_errors": errors,
                "citations": {"accepted": acc, "rejected": rej}, "unknown_ids": rej,
                "verdicts_not_from_engine": stray_verdicts, "messages": messages}

    def _step(self, turn, msg, tool, args, rationale, acc, rej, extra) -> None:
        self.w.log("agent_step", self.role.name, {
            "turn": turn, "tool": tool, "args": args, "reasoning": _reasoning(msg or {}),
            "rationale": rationale, "citations_accepted": acc, "citations_rejected": rej, **extra})

    # ---------------------------------------------------------------- dispatch
    def call(self, name: str, args: dict, turn: int | None = None, msg: dict | None = None) -> dict:
        r = self.role
        args = dict(args)
        rationale = str(args.pop("rationale", "") or "").strip()
        cits = [str(c) for c in _as_list(args.get("citations")) + _as_list(args.get("evidence"))]
        acc, rej = split_citations(cits, self.w.kb)
        if name not in TOOLS:
            out = {"refused": f"unknown tool {name}; your tools: {r.tools}"}
        elif name not in r.tools and not (name == "read_alerts" and not (r.sees.get("signals") or r.sees.get("sources"))):
            out = {"refused": f"{name} is not in the {r.name} allow-list; your tools: {r.tools}"}
        elif LEVEL[name] > r.max_level:
            out = {"refused": f"{name} needs autonomy A{LEVEL[name]}; {r.name} is limited to A{r.max_level}"}
        elif "_unparsed" in args:
            out = {"refused": f"arguments for {name} are not valid JSON"}
        elif not rationale:
            out = {"refused": f"rationale is required: call {name} again with a one-line 'rationale' argument"}
        else:
            try:
                out = getattr(self, f"t_{name}")(**args)
            except Refused as e:
                out = {"refused": str(e)}
            except TypeError as e:
                out = {"refused": f"bad arguments for {name}: {e}"}
            if "refused" not in out and name in NEXT:
                out["next"] = NEXT[name]
        if "refused" in out and name in ("execute_playbook",) and "token" in out["refused"]:
            out["next"] = NEXT["select_playbook"]
        self._step(turn, msg, name, args, rationale, acc, rej, {"result": out})
        return out

    # ---------------------------------------------------------------- A0 tools
    def _visible(self, a: dict) -> bool:
        vis = a.get("visible_to")
        return vis is None or self.role.name in vis

    def t_read_alerts(self, source: str | None = "any", site: str | None = "any") -> dict:
        mine = [a for a in self.w.alerts if self._visible(a)]
        sel = [a for a in mine if (source in (None, "", "any") or a.get("source") == source)
               and (site in (None, "", "any") or site in (a.get("sites") or [a.get("site")]))]
        out = {"alerts": [{k: v for k, v in a.items() if k not in ("explain", "visible_to")} for a in sel[-20:]],
               "messages_to_me": [{k: m.get(k) for k in ("id", "at", "sender", "kind", "payload", "refs",
                                                          "playbook", "data_class")}
                                  for m in self.proto.inbox(self.role.name)][-10:]}
        if not sel and mine:
            out["hint"] = (f"no alert matches source={source}, site={site}; {len(mine)} other alerts are visible to "
                           "you: call read_alerts with source=any")
        return out

    def t_explain_model(self, alert_id: str) -> dict:
        for a in self.w.alerts:
            if a.get("id") == alert_id:
                if not self._visible(a):
                    break   # same answer as a missing id: no leak that it exists
                return {"alert_id": alert_id, "source": a.get("source"), "label": a.get("label"),
                        "explain": a.get("explain", {})}
        return {"refused": f"no alert {alert_id} visible to you"}

    def t_query_kb(self, question: str, topic: str | None = None) -> dict:
        hits = []
        q = _words(question)
        for rid, rec in self.w.kb.records.items():
            if topic and topic not in rec.get("topics", [rec.get("topic")]):
                continue
            hay = _words(" ".join(str(rec.get(k, "")) for k in ("instrument", "clause", "summary", "quote", "topics")))
            score = len(q & hay) / max(1, len(q))
            if score >= 0.25 or topic:
                hits.append((score, rid, rec))
        hits.sort(key=lambda h: (-h[0], h[1]))
        res = [{"id": rid, "clause": rec["clause"], "instrument": rec["instrument"],
                "jurisdiction": rec["jurisdiction"], "binding_status": rec["binding_status"],
                "verified": rec.get("verified", False), "summary": rec.get("summary", "")} for _, rid, rec in hits[:5]]
        chunks = []
        vec = _kbvec()
        if vec is not None:
            try:
                for c in vec.search_with_abstention(question, k=3, filters=None, rerank=True)["results"]:
                    self.seen_chunks.add(c["chunk_id"])
                    chunks.append({k: c.get(k) for k in ("chunk_id", "title", "jurisdiction", "binding_status",
                                                          "page", "clause", "tier")} | {"text": c.get("text", "")[:400],
                                                                                         "verified": False})
            except Exception as e:  # noqa: BLE001
                chunks = [{"error": f"vector KB unavailable: {str(e)[:120]}"}]
        if not res and not chunks:
            return {"results": [], "note": "no record matched; say 'not found in the sources we checked'",
                    "kb_as_of": str(self.w.kb.as_of)}
        return {"results": res, "corpus_chunks": chunks, "kb_as_of": str(self.w.kb.as_of)}

    def t_ask_adviser(self, question: str) -> dict:
        a = self.adviser.ask(question, asker=self.role.name)
        self.seen_chunks |= {c for c in a["citations"] if classify_citation(c, self.w.kb) == "chunk"}
        return {k: a[k] for k in ("found", "answer", "citations", "kb_as_of")}

    def t_draft_notice(self, kind: str, recipient: str, body: str, citations: list | None = None) -> dict:
        if kind not in self.role.notice_kinds:
            raise Refused(f"{self.role.name} may draft only {self.role.notice_kinds}")
        acc, rej = split_citations(_as_list(citations), self.w.kb)
        bad = sorted(set(rej) | set(unknown_ids_in_text(body, self.w.kb)))
        d = {"id": f"DRAFT-{len(self.w.drafts) + 1:03d}", "at": self.w.now, "by": self.role.name, "kind": kind,
             "recipient": recipient, "body": body, "citations": acc, "status": "draft - a human sends it",
             "unknown_ids": bad}
        self.w.drafts.append(d)
        return {"draft_id": d["id"], "status": d["status"], "citations": acc, "rejected_citations": bad}

    def t_record_gap(self, topic: str, finding: str, evidence: list | None = None) -> dict:
        evidence = [str(e) for e in _as_list(evidence)]
        acc, rej = split_citations(evidence, self.w.kb)
        if not evidence or rej:
            raise Refused(f"evidence must be record, gap or chunk ids a tool returned; rejected: {rej or 'none given'}")
        if topic not in kbmod.TOPICS:
            raise Refused(f"unknown topic {topic}")
        rejected = [g["id"] for g in self.w.kb.gaps.values() if g.get("topic") == topic and g.get("status") == "rejected"]
        if rejected:
            raise Refused(f"a human rejected the gap for topic {topic} ({rejected[0]}); it is not raised again")
        registered = [g["id"] for g in self.w.kb.gaps.values() if g.get("topic") == topic]
        d = {"id": f"GAPDRAFT-{len(self.w.gap_drafts) + 1:03d}", "at": self.w.now, "by": self.role.name,
             "topic": topic, "finding": finding, "evidence": acc, "matches_registered": registered,
             "status": "pre-confirmed", "note": f"pre-confirmed by {self.role.name}; only a human confirms or rejects"}
        self.w.gap_drafts.append(d)
        return {"draft_id": d["id"], "matches_registered": registered, "status": d["status"], "note": d["note"]}

    # ---------------------------------------------------------------- A1 tools
    def t_run_rule_engine(self, questions: list | None = None) -> dict:
        facts = dict(self.w.facts)
        if questions:
            extra = []
            for i, q in enumerate(questions, 1):
                if not isinstance(q, dict) or "topic" not in q:
                    raise Refused("each question needs {topic, text}")
                extra.append({"id": f"Q-{self.role.name}-{i}", "topic": q["topic"], "text": q.get("text", "")})
            facts["obligation_questions"] = list(facts.get("obligation_questions") or []) + extra
        out = []
        for v in rules.evaluate(facts, self.w.kb):
            self.engine_verdicts.add(v.verdict)
            out.append({k: getattr(v, k) for k in ("verdict", "rule_id", "topic", "gap_id", "record_ids",
                                                    "explanation", "deadline", "time_left", "notes")})
        return {"kb_as_of": str(self.w.kb.as_of), "verdicts": out, "footer": rules.FOOTER}

    def t_select_playbook(self, goal: str | None = None) -> dict:
        pbs = sorted(self.rem.cat.values(), key=lambda p: (p["owner"] != self.role.name, p["id"]))
        return {"playbooks": [{"id": p["id"], "title": p["title"], "owner": p["owner"],
                               "executable": p.get("executable", False), "you_own": p["owner"] == self.role.name,
                               "params": p.get("params", []), "preconditions": p.get("preconditions", [])}
                              for p in pbs]}

    def t_send_message(self, to, type: str, text: str, refs: list | None = None,  # noqa: A002
                       data_class: str = "operational", playbook: str | None = None,
                       in_reply_to: str | None = None) -> dict:
        if type == "propose" and not playbook:   # small models name the playbook only in the text
            named = sorted(set(re.findall(r"\bPB-\d{2}\b", text or "")))
            playbook = named[0] if len(named) == 1 else None
        m = Message(type=type, sender=self.role.name, recipients=_as_list(to), text=text,
                    refs=[str(x) for x in _as_list(refs)], data_class=data_class or "operational",
                    playbook=playbook or None, in_reply_to=in_reply_to or None)
        res = self.proto.send(m)
        if "rejected" in res:
            return {"refused": f"protocol: {res['rejected']}"}
        return res

    def t_request_approval(self, playbook: str, targets, reason: str, params: dict | None = None) -> dict:
        p = self.rem.request_approval(self.role.name, playbook, _as_list(targets), params, reason)
        res = self.proto.send(Message(type="approve_request", sender=self.role.name, recipients=[COMMANDER],
                                      text=f"Approve {playbook} on {', '.join(_as_list(targets))}: {reason}",
                                      refs=[p["hash"]], playbook=playbook))
        out = {k: p[k] for k in ("hash", "playbook", "targets", "expires_at", "executable", "clone_test", "mode")}
        if p.get("auto_token"):                 # the human granted ASSISTED/AUTO for this scope
            return out | {"status": f"approved automatically under {p['mode']} (hard limits still apply)",
                          "token": p["auto_token"], "token_expires_at": p["token_expires_at"],
                          "next": "call execute_playbook with exactly these targets, params and this token"}
        return out | {"status": "waiting for the human commander", "message": res}

    # ---------------------------------------------------------------- A2 tools
    def t_execute_playbook(self, playbook: str, targets, token: str, params: dict | None = None) -> dict:
        return self.rem.execute(self.role.name, playbook, _as_list(targets), params, token)


# ----------------------------------------------------------------------------------- the human
class Commander:
    """The human incident commander. Approves plans and decides gaps; agents cannot call any of this."""

    def __init__(self, world: World, remediation: Remediation, protocol: Protocol, name: str = "commander"):
        self.w, self.rem, self.proto, self.name = world, remediation, protocol, name
        self.rejected: set[str] = set()

    def pending(self) -> list[dict]:
        used = {t["hash"] for t in self.rem.tokens.values()}
        return [p for h, p in self.rem.plans.items()
                if h not in used and h not in self.rejected and not p.get("executed") and not p.get("auto_token")]

    def approve(self, plan_hash: str, pin: str) -> str:
        token = self.rem.approve(plan_hash, self.name, pin)
        p = self.rem.plans[plan_hash]
        self.proto.send(Message(type="inform", sender=COMMANDER, recipients=[p["owner"]], refs=[plan_hash],
                                text=f"Approved {p['playbook']} on {', '.join(p['targets'])} with params "
                                     f"{json.dumps(p['params'])}. One-time token: {token}. Expires {p['token_expires_at']}. "
                                     "Call execute_playbook with exactly these targets and params."))
        return token

    def reject(self, plan_hash: str, reason: str) -> None:
        self.rem.reject(plan_hash, self.name, reason)

    # autonomy controls (Mission 6): human only, PIN-checked, logged
    def set_mode(self, mode: str, pin: str, minutes: int, sites="*", playbooks="*") -> dict:
        return self.rem.set_mode(mode, self.name, pin, minutes, sites, playbooks)

    def kill(self, pin: str, reason: str) -> None:
        self.rem.kill(self.name, pin, reason)

    def release_kill(self, pin: str) -> None:
        self.rem.release_kill(self.name, pin)
        self.rejected.add(plan_hash)
        p = self.rem.plans.get(plan_hash)
        if p:
            self.proto.send(Message(type="inform", sender=COMMANDER, recipients=[p["owner"]], refs=[plan_hash],
                                    text=f"Rejected {p['playbook']}: {reason}"))

    def decide_gap(self, draft_id: str, decision: str, note: str = "") -> dict:
        """Confirm or reject a pre-confirmed gap draft (run state only; kb/ is edited by people, not code)."""
        if decision not in ("confirmed", "rejected"):
            raise ValueError("decision must be confirmed or rejected")
        for d in self.w.gap_drafts:
            if d["id"] == draft_id:
                d["status"] = decision
                d["decided_by"] = f"human:{self.name}"
                self.w.log("gap_human_decision", f"human:{self.name}", {"draft_id": draft_id, "decision": decision,
                                                                        "note": note})
                return d
        raise KeyError(draft_id)


# ----------------------------------------------------------------------------- deterministic mock
class PolicyMockLLM:
    """Deterministic stand-in for the LLM (no network): read_alerts -> run_rule_engine -> summary.

    Used by tests and by ``LLM_MODE``-free demo runs. It only calls tools the role was sent, cites only
    ids the rule engine returned, and always gives a rationale. Replays are exact.
    """

    def chat(self, messages, tools=None) -> dict:
        names = [t["function"]["name"] for t in tools or []]
        last_user = max(i for i, m in enumerate(messages) if m["role"] == "user")
        done = [m for m in messages[last_user:] if m["role"] == "tool"]
        task = messages[last_user].get("content", "")
        prelude = [n for n in ("read_alerts", "run_rule_engine") if n in names]
        if "fails over towers CHN-01 and CHN-02" in task and "request_approval" in names and len(done) == len(prelude):
            args = {"playbook": "PB-06", "targets": ["CHN-01", "CHN-02"],
                    "params": {"path": "B"}, "reason": "Use verified domestic backup path B",
                    "rationale": "request approval for the clean domestic failover"}
            return {"role": "assistant", "content": None, "tool_calls": [
                {"id": "mock-pb06", "type": "function", "function": {"name": "request_approval", "arguments": json.dumps(args)}}]}
        plan = [n for n in ("read_alerts", "run_rule_engine") if n in names]
        if len(done) < len(plan):
            n = plan[len(done)]
            args = {"source": "any", "rationale": "see what was released to me"} if n == "read_alerts" else \
                   {"rationale": "get verdicts from the rule engine, the only source of verdicts"}
            return {"role": "assistant", "content": None, "tool_calls": [
                {"id": f"mock-{len(done)}", "type": "function", "function": {"name": n, "arguments": json.dumps(args)}}]}
        ids, lines = [], []
        for m in done:
            try:
                d = json.loads(m["content"])
            except (ValueError, TypeError):
                continue
            for v in d.get("verdicts", []):
                ids += v.get("record_ids") or []
                if v.get("gap_id"):
                    ids.append(v["gap_id"])
                lines.append(f"Rule engine: {v['verdict']} on {v.get('topic') or v['rule_id']}.")
            if "alerts" in d:
                lines.insert(0, f"I see {len(d['alerts'])} items released to me.")
        ids = list(dict.fromkeys(ids))
        return {"role": "assistant", "tool_calls": [], "content": "\n".join(
            lines[:6] + [f"Citations: {', '.join(ids) or 'none'}", "Human decision needed: review the verdicts."])}


# ------------------------------------------------------------------------------- the coordinator
class Coordinator:
    """Runs a scenario: releases events per agent, gives each informed agent one turn, delivers messages.

    The commander is a callable ``commander_policy(commander, pending_plans, event)`` invoked at
    commander events (a scripted stand-in for the human in replays; the dashboard replaces it).
    """

    def __init__(self, world: World, llm, roles: list[str] | None = None, commander_policy=None,
                 adviser_llm=None, message_rounds: int = 1, rules_enabled: bool = True):
        self.w = world
        self.roles = load_agent_roles()
        if not rules_enabled:
            for role in self.roles.values():
                role.tools = [tool for tool in role.tools if tool != "run_rule_engine"]
        if roles:
            self.roles = {n: r for n, r in self.roles.items() if n in roles}
        self.rem = Remediation(world)
        self.proto = Protocol(world, load_agent_roles(), self.rem)
        self.adviser = PolicyAdviser(world, adviser_llm)
        self.agents = {n: Agent(r, world, llm, self.rem, self.proto, self.adviser) for n, r in self.roles.items()}
        self.commander = Commander(world, self.rem, self.proto)
        self.commander_policy = commander_policy
        self.message_rounds = message_rounds
        self.results: list[dict] = []

    def run(self, scenario: dict, upto_t: float | None = None) -> list[dict]:
        self.w.facts.setdefault("jurisdiction", scenario.get("jurisdiction", "IN"))
        self.w.facts.setdefault("entity", scenario.get("entity", {}))
        feed = EventFeed(scenario, load_agent_roles())
        for e in scenario["events"]:
            if upto_t is not None and e["t"] > upto_t:
                break
            seen = len(self.w.bus)
            released = feed.release(self.w, e["t"])
            if e.get("actor") == "commander" and self.commander_policy:
                self.commander_policy(self.commander, self.commander.pending(), e)
            for name, alerts in released.items():
                if name in self.agents and e.get("actor") != "commander":
                    task = "New information released to you: " + " | ".join(
                        f"[{a['id']}] T+{a['t']} min: {a['detail']}" for a in alerts) + \
                        ". Assess it within your mandate, use your tools, coordinate if another party must know."
                    self.results.append({"t": e["t"], **self._turn(name, task)})
            for _ in range(self.message_rounds):
                new = self.w.bus[seen:]
                seen = len(self.w.bus)
                to_run = sorted({r for m in new for r in (m["to"] if isinstance(m["to"], list) else [m["to"]])
                                 if r in self.agents})
                for name in to_run:
                    msgs = [m for m in new if name in (m["to"] if isinstance(m["to"], list) else [m["to"]])]
                    task = "New messages for you: " + " | ".join(
                        f"[{m.get('id')}] {m.get('sender')} ({m.get('kind')}): {m['payload'].get('text', '')}"
                        for m in msgs) + ". Act on them within your mandate."
                    self.results.append({"t": e["t"], **self._turn(name, task)})
        return self.results

    def _turn(self, name: str, task: str) -> dict:
        try:
            r = self.agents[name].run(task)
        except Exception as ex:  # noqa: BLE001 - an LLM failure must not stop the run; it is logged
            self.w.log("agent_error", name, {"error": str(ex)[:500]})
            return {"role": name, "error": str(ex)[:500]}
        return {k: v for k, v in r.items() if k != "messages"}
