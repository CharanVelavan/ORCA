"""Typed coordination protocol between role agents and the human commander.

Every message goes through ``Protocol.send``. It is checked in code, and a message that breaks a rule
is rejected and written to the hash-chained audit log (``msg_rejected``); an accepted one is put on
``world.bus`` and logged (``msg_sent``). Prompts may describe these rules, but only this module
enforces them.

Message types
    inform           share a fact or an assessment
    request          ask a recipient for information or for an action within ITS mandate
    propose          propose a playbook (from the fixed catalogue) or a plan
    object           object to an earlier message or plan (needs ``in_reply_to`` or a plan ref)
    approve_request  ask the human commander to approve a plan (needs the plan hash; commander only)

Checks (all code)
    - sender is a known role or the human commander; type is one of the five; recipients are known,
      non-empty, and do not include the sender;
    - the sender's role file allows this type and this data class (``sharing`` block);
    - sharing limits by mandate: an operator never sends ``customer_data`` or ``personal_data`` to
      another operator; ``personal_data`` goes only to CERT-In; a ``legal_direction`` comes only from
      a role with ``may_direct`` (CERT-In) and is always a draft that a human officer issues;
    - a ``propose`` naming a playbook needs ``may_propose_playbooks`` (the regulator has not), a
      catalogue playbook, and the owner among the recipients unless the sender is the owner;
    - ``approve_request`` goes to the commander only and must reference a plan hash the sender owns;
    - every ref must resolve: a KB record id, a non-rejected gap id, a vector-KB chunk id, an alert
      the SENDER may see, a message the sender was party to, a plan hash, a draft id or a rule id;
    - every KB-looking id in the text must exist (no invented citations).
"""
from __future__ import annotations

import itertools
import re
from dataclasses import asdict, dataclass, field

from orca import rules

TYPES = ("inform", "request", "propose", "object", "approve_request")
DATA_CLASSES = ("operational", "technical_indicator", "customer_data", "personal_data", "legal_direction")
OPERATORS = {"satellite_operator", "mobile_operator", "power_utility"}
COMMANDER = "commander"
MAX_TEXT = 1500
MAX_RECIPIENTS = 7

# KB-looking ids (records, gaps) in free text. Rule ids (IN-R-...) also match and are known.
# Lowercase is allowed after the first segment: record ids end in clause letters (-ii, -iv, -b, -j).
ID_RE = re.compile(r"(?<![\w-])((?:IN|EU|AE|US|INTL)-[A-Z0-9][A-Za-z0-9-]*[A-Za-z0-9]"
                   r"|GAP-(?:IN|EU|AE|US|INTL|CAND)-[A-Za-z0-9-]*[A-Za-z0-9]"
                   r"|[a-z]{2,4}-[a-z0-9][a-z0-9.-]*:p\d+:c\d+)")      # vector-KB chunk id (orca.kbvec)


# ----------------------------------------------------------------------------- citations
def _kbvec():
    """The vector KB (built in parallel). None if the package is absent or broken."""
    try:
        from orca import kbvec  # noqa: PLC0415
        return kbvec
    except Exception:  # noqa: BLE001 - any import failure means "no vector KB"
        return None


def rule_ids() -> set[str]:
    ids: set[str] = set()
    for jur in rules.RULE_FILES:
        r = rules.load_rules(jur)
        ids |= {x["id"] for k in ("clock_groups", "deadline_rules", "conflicts") for x in r[k]}
    return ids


def classify_citation(cid: str, kb) -> str | None:
    """'record' | 'gap' | 'chunk' if ``cid`` is an acceptable citation, else None.

    Accepted: a KB record id, a gap id that a human has not rejected, or a real vector-KB chunk id
    (checked with ``orca.kbvec.get_chunk``). Rejected gaps, rule ids and anything else are refused.
    """
    if not isinstance(cid, str) or not cid:
        return None
    if cid in kb.records:
        return "record"
    g = kb.gaps.get(cid)
    if g is not None:
        return "gap" if g.get("status") != "rejected" else None
    vec = _kbvec()
    if vec is not None:
        try:
            if vec.get_chunk(cid):
                return "chunk"
        except Exception:  # noqa: BLE001
            return None
    return None


def check_citations(cits, kb) -> tuple[list[str], list[str]]:
    """Split a citation list into (accepted, rejected)."""
    ok, bad = [], []
    for c in cits or []:
        (ok if classify_citation(c, kb) else bad).append(c)
    return ok, bad


def unknown_ids_in_text(text: str, kb, extra_known: set[str] | None = None) -> list[str]:
    """KB-looking ids in ``text`` that are neither a record, a non-rejected gap nor a rule id."""
    known = set(kb.records) | {g for g, v in kb.gaps.items() if v.get("status") != "rejected"} | rule_ids()
    known |= extra_known or set()
    vec = _kbvec()
    return sorted({m for m in ID_RE.findall(text or "") if m not in known
                   and not (":p" in m and vec is not None and vec.get_chunk(m) is not None)})


# ----------------------------------------------------------------------------- message
@dataclass
class Message:
    type: str
    sender: str
    recipients: list[str]
    text: str
    refs: list[str] = field(default_factory=list)
    data_class: str = "operational"
    playbook: str | None = None
    in_reply_to: str | None = None
    id: str = ""
    at: str = ""

    def to_bus(self) -> dict:
        """Shape stored on world.bus (keeps the older keys ``to``, ``kind``, ``payload``)."""
        d = asdict(self)
        d["to"] = list(self.recipients)
        d["kind"] = self.type
        d["payload"] = {"text": self.text}
        return d


class ProtocolViolation(Exception):
    pass


class Protocol:
    """Validates and delivers messages for one run. ``roles`` maps role name -> Role (orca.agents)."""

    def __init__(self, world, roles: dict, remediation=None):
        self.w = world
        self.roles = roles
        self.rem = remediation
        self._seq = itertools.count(1)

    # ------------------------------------------------------------------ public
    def send(self, msg: Message) -> dict:
        msg.at = self.w.now
        try:
            self.validate(msg)
        except ProtocolViolation as e:
            self.w.log("msg_rejected", msg.sender, {"message": asdict(msg), "reason": str(e)})
            return {"rejected": str(e)}
        msg.id = f"MSG-{next(self._seq):04d}"
        self.w.bus.append(msg.to_bus())
        self.w.log("msg_sent", msg.sender, asdict(msg))
        return {"sent": True, "id": msg.id}

    def inbox(self, role: str) -> list[dict]:
        out = []
        for m in self.w.bus:
            to = m.get("to")
            to = to if isinstance(to, list) else [to]
            if role in to:
                out.append(m)
        return out

    # ------------------------------------------------------------------ checks
    def validate(self, m: Message) -> None:
        def no(reason):
            raise ProtocolViolation(reason)

        parties = set(self.roles) | {COMMANDER}
        if m.sender not in parties:
            no(f"unknown sender {m.sender!r}")
        if m.type not in TYPES:
            no(f"type must be one of {list(TYPES)}, not {m.type!r}")
        if m.data_class not in DATA_CLASSES:
            no(f"data_class must be one of {list(DATA_CLASSES)}, not {m.data_class!r}")
        if not isinstance(m.recipients, list) or not m.recipients:
            no("at least one recipient is required")
        if len(m.recipients) > MAX_RECIPIENTS:
            no(f"at most {MAX_RECIPIENTS} recipients")
        for r in m.recipients:
            if r not in parties:
                no(f"unknown recipient {r!r}; known: {sorted(parties)}")
        if m.sender in m.recipients:
            no("a message cannot be sent to its own sender")
        if not (m.text or "").strip():
            no("text is required")
        if len(m.text) > MAX_TEXT:
            no(f"text longer than {MAX_TEXT} characters")

        share = self._sharing(m.sender)
        # sharing limits by mandate
        if m.data_class in ("customer_data", "personal_data") and m.sender in OPERATORS:
            other_ops = [r for r in m.recipients if r in OPERATORS and r != m.sender]
            if other_ops:
                no(f"an operator may not share {m.data_class} with another operator ({', '.join(other_ops)})")
        if m.data_class == "personal_data" and any(r != "cert_in" for r in m.recipients):
            no("personal_data may go only to cert_in (incident report), never to other parties")
        if m.data_class == "legal_direction":
            if not share.get("may_direct"):
                no(f"{m.sender} has no power to direct; only cert_in may send a (draft) legal_direction")
            if m.type != "request":
                no("a legal_direction must be a request")

        if m.type not in share["may_send"]:
            no(f"{m.sender} may not send {m.type} messages (role file sharing.may_send)")
        if m.data_class not in {"customer_data", "personal_data"} and m.data_class not in share["may_share"]:
            no(f"{m.sender} may not share {m.data_class} (role file sharing.may_share)")

        # type-specific rules
        if m.playbook is not None:
            cat = self.rem.cat if self.rem else {}
            if m.playbook not in cat:
                no(f"{m.playbook} is not in the playbook catalogue")
        if m.type == "propose" and m.playbook:
            if not share.get("may_propose_playbooks"):
                no(f"{m.sender} may not propose playbooks (no execution mandate)")
            owner = self.rem.cat[m.playbook]["owner"]
            if owner != m.sender and owner not in m.recipients and owner != "asset_owner":
                no(f"{m.playbook} is owned by {owner}; address the proposal to {owner}")
        if m.type == "approve_request":
            if m.recipients != [COMMANDER]:
                no("approve_request goes to the commander only")
            plans = self.rem.plans if self.rem else {}
            mine = [r for r in m.refs if r in plans and plans[r]["owner"] == m.sender]
            if not mine:
                no("approve_request must reference a plan hash you own (use request_approval first)")
        if m.type == "object":
            if not m.in_reply_to and not any(self._is_plan(r) for r in m.refs):
                no("an objection needs in_reply_to (a message id) or a plan hash in refs")
        if m.in_reply_to is not None and not self._party_to(m.in_reply_to, m.sender):
            no(f"in_reply_to {m.in_reply_to!r} is not a message you sent or received")

        # refs and citations
        for r in m.refs or []:
            if not self._ref_ok(r, m.sender):
                no(f"ref {r!r} does not resolve to evidence you may see (record, gap, chunk, your alert, "
                   "message, plan, draft or rule id)")
        bad = unknown_ids_in_text(m.text, self.w.kb)
        if bad:
            no(f"text cites unknown ids {bad}; cite only ids that a tool returned")

    # ------------------------------------------------------------------ helpers
    def _sharing(self, sender: str) -> dict:
        if sender == COMMANDER:
            return {"may_send": list(TYPES), "may_share": list(DATA_CLASSES), "may_direct": False,
                    "may_propose_playbooks": True}
        s = dict(self.roles[sender].sharing or {})
        s.setdefault("may_send", ["inform", "request"])
        s.setdefault("may_share", ["operational"])
        return s

    def _is_plan(self, ref: str) -> bool:
        return bool(self.rem and ref in self.rem.plans)

    def _party_to(self, msg_id: str, who: str) -> bool:
        for m in self.w.bus:
            if m.get("id") == msg_id:
                to = m.get("to") if isinstance(m.get("to"), list) else [m.get("to")]
                return m.get("sender") == who or who in to
        return False

    def _ref_ok(self, ref: str, sender: str) -> bool:
        if not isinstance(ref, str) or not ref:
            return False
        if classify_citation(ref, self.w.kb):
            return True
        if ref in rule_ids() or self._is_plan(ref):
            return True
        if ref.startswith("MSG-"):
            return self._party_to(ref, sender)
        if any(d.get("id") == ref for d in list(self.w.drafts) + list(self.w.gap_drafts)):
            return True
        for a in self.w.alerts:
            if a.get("id") == ref:
                vis = a.get("visible_to")
                return sender == COMMANDER or vis is None or sender in vis
        return False
