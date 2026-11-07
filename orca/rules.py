"""P node: deterministic YAML rule engine. Facts in, verdicts out, each citing a KB id.

Verdicts: COMPLIANT, VIOLATION, AMBIGUITY, CONFLICT, POTENTIAL_GAP, INSUFFICIENT_EVIDENCE.
No LLM, no wall clock: every time comes from the facts. Numbers in explanations are
computed here. Every verdict carries ``kb_as_of`` and the fixed footer.

FACTS FORMAT (a dict, usually loaded from a scenario YAML; timestamps are ISO 8601 with an
offset, for example "2026-11-10T19:02:00+05:30"):

    jurisdiction: IN                    # which rules/<jur>.yaml and which KB records to use
    now: <ts>                           # the only clock; needed for "time left" and "not yet sent"
    on: 2026-11-10                      # date for in-force tests (default: date of now, else KB as-of)
    applies: [record ids]               # which deadline records apply (default: rules marked default)
    triggers:                           # when the clocks start
      noticing: <ts>
      occurrence: <ts> | [{label: .., at: <ts>}]   # a list means several readings
      awareness: <ts>
    classifications: [{at: <ts>, label: fault|attack}]   # fault -> attack is noted as ambiguity
    reports: [{record: <id>, sent_at: <ts>}]             # reports already sent
    proposed_actions:                   # from agents, checked against rules' conflict pairs
      - {playbook: PB-05, agent: .., targets: [..], supporting_records: [..], preconditions: [..]}
    obligation_questions:               # topic coverage checks
      - {id: .., topic: .., text: .., record: <optional id that must be among the covering ones>,
         jurisdiction: <optional override>}

Rule files (rules/india.yaml) hold: clock_groups, deadline_rules, conflicts. The deadline and
trigger of each rule come from the KB obligation, never from the rule file.

Guards: a record with verified: false never yields COMPLIANT or VIOLATION; a record whose
binding status is not stated yields AMBIGUITY, never "not applicable"; a topic is covered only by
an in-force, verified record.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

RULES_DIR = Path(__file__).resolve().parent.parent / "rules"
RULE_FILES = {"IN": "india.yaml", "EU": "eu.yaml", "AE": "ae.yaml"}
FOOTER = "Rule-engine result on stated facts. Not legal advice."
VERDICTS = {"COMPLIANT", "VIOLATION", "AMBIGUITY", "CONFLICT", "POTENTIAL_GAP",
            "INSUFFICIENT_EVIDENCE"}
DURATION = re.compile(r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?)?$")


@dataclass
class Verdict:
    verdict: str
    rule_id: str
    topic: str | None
    record_ids: list[str]
    explanation: str
    gap_id: str | None = None
    deadline: str | None = None           # ISO datetime (earliest = safe working deadline)
    time_left: str | None = None          # text such as "2 h 22 m left" / "34 m overdue"
    readings: list[dict] = field(default_factory=list)   # AMBIGUITY: one per reading
    actions: list[dict] = field(default_factory=list)    # CONFLICT: the clashing actions
    notes: list[str] = field(default_factory=list)
    kb_as_of: str = ""
    footer: str = FOOTER

    def to_dict(self) -> dict:
        return asdict(self)


# ----------------------------------------------------------------- small helpers
def load_rules(jurisdiction: str) -> dict:
    """Rule file for a jurisdiction; an empty rule set if there is none (coverage still works)."""
    name = RULE_FILES.get(jurisdiction)
    path = RULES_DIR / name if name else None
    data = yaml.safe_load(path.read_text()) if path and path.exists() else None
    data = data or {}
    for key in ("clock_groups", "deadline_rules", "conflicts"):
        data.setdefault(key, [])
    return data


def parse_duration(text: str) -> dt.timedelta:
    m = DURATION.match(str(text))
    if not m or not any(m.groups()):
        raise ValueError(f"not an ISO 8601 duration: {text}")
    d, h, mi = (int(x or 0) for x in m.groups())
    return dt.timedelta(days=d, hours=h, minutes=mi)


def parse_ts(value) -> dt.datetime:
    """Timezone-aware datetime from a string or a YAML-parsed datetime; naive is an error."""
    t = value if isinstance(value, dt.datetime) else dt.datetime.fromisoformat(str(value))
    if t.tzinfo is None:
        raise ValueError(f"timestamp has no timezone offset: {value}")
    return t


def fmt_delta(td: dt.timedelta) -> str:
    mins = int(abs(td).total_seconds() // 60)
    return f"{mins // 60} h {mins % 60:02d} m"


def left_text(deadline: dt.datetime, at: dt.datetime) -> str:
    td = deadline - at
    return f"{fmt_delta(td)} left" if td >= dt.timedelta(0) else f"{fmt_delta(td)} overdue"


def candidate_gap_id(jurisdiction: str, topic: str) -> str:
    return "GAP-CAND-" + hashlib.sha1(f"{jurisdiction}:{topic}".encode()).hexdigest()[:8]


def find_gap(kb, topic: str, jurisdiction: str) -> tuple[str, str]:
    """(gap id, status): the registered gap for the topic, else a deterministic candidate id."""
    found = kb.gaps_for(topic, jurisdiction)
    if found:
        return found[0]["id"], found[0].get("status", "candidate")
    return candidate_gap_id(jurisdiction, topic), "candidate (not yet in the gap register)"


def rejected_gap(kb, topic: str, jurisdiction: str) -> dict | None:
    """The gap a human rejected for this topic, if any. Check this before find_gap: a rejected
    gap must never be re-raised under a fresh candidate id."""
    for g in kb.gaps.values():
        if (g.get("topic") == topic and g["jurisdiction"] in (jurisdiction, "INTL")
                and g.get("status") == "rejected"):
            return g
    return None


# ----------------------------------------------------------------- the engine
class _Engine:
    def __init__(self, facts: dict, kb):
        self.facts, self.kb = facts, kb
        self.jur = facts.get("jurisdiction", "IN")
        self.rules = load_rules(self.jur)
        self.as_of = str(kb.as_of)
        self.now = parse_ts(facts["now"]) if facts.get("now") else None
        if facts.get("on"):
            self.on = facts["on"] if isinstance(facts["on"], dt.date) else dt.date.fromisoformat(str(facts["on"]))
        else:
            self.on = self.now.date() if self.now else kb.as_of
        self.out: list[Verdict] = []
        self.clock_readings: dict[str, list[dict]] = {}   # group id -> readings from deadline rules

    # one place builds and checks every verdict
    def add(self, verdict, rule_id, topic, records, explanation, **kw) -> Verdict:
        known = [r for r in dict.fromkeys(records) if r in self.kb.records]
        notes = list(kw.pop("notes", []))
        notes += [f"cited id {r} is not in the KB and was dropped" for r in records if r not in known]
        # Guard: an unverified record can never give COMPLIANT or VIOLATION.
        unverified = [r for r in known if not self.kb.records[r].get("verified")]
        if verdict in ("COMPLIANT", "VIOLATION") and unverified:
            verdict = "INSUFFICIENT_EVIDENCE"
            explanation = (f"Record unverified ({', '.join(unverified)}): the quote has not been checked "
                           f"against the official text, so no compliance finding is made.")
            kw.update(deadline=None, time_left=None)
        gap_id = kw.get("gap_id")
        if not known and not gap_id:
            raise ValueError(f"verdict {rule_id} cites nothing")
        v = Verdict(verdict, rule_id, topic, known, explanation, notes=notes, kb_as_of=self.as_of, **kw)
        self.out.append(v)
        return v

    def timestamp(self, value, what, problems):
        try:
            return parse_ts(value)
        except (ValueError, TypeError):
            problems.append(f"{what} is missing or not a timezone-aware timestamp")
            return None

    def readings_for(self, trigger: str, problems) -> list[tuple[str, dt.datetime]]:
        """[(label, time)] for a trigger kind; several when the facts list alternatives."""
        raw = (self.facts.get("triggers") or {}).get(trigger)
        if raw is None:
            problems.append(f"triggers.{trigger}")
            return []
        items = raw if isinstance(raw, list) else [{"label": f"{trigger} time", "at": raw}]
        out = []
        for it in items:
            t = self.timestamp(it["at"], f"triggers.{trigger}", problems)
            if t:
                out.append((it.get("label", f"{trigger} time"), t))
        return out

    # ---- 1. deadline rules (and the not-stated status guard)
    def deadline_rules(self):
        if not any(k in self.facts for k in ("triggers", "applies", "reports")):
            return                      # no incident described: nothing to count
        applies = self.facts.get("applies")
        for rule in self.rules["deadline_rules"]:
            rid = rule["record"]
            if (rid not in applies) if applies is not None else (not rule.get("default", False)):
                continue
            self.one_deadline(rule, self.kb.records[rid])

    def one_deadline(self, rule, rec):
        rid, topic = rec["id"], rec["topic"]
        ob = rec.get("obligation") or {}
        status = self.kb.in_force_status(rid, self.on)
        problems: list[str] = []
        dur = parse_duration(ob["deadline"]) if ob.get("deadline") else None
        trig = ob.get("trigger")
        readings = self.readings_for(trig, problems) if dur and trig not in (None, "none") else []
        rows = [{"label": lab, "trigger": trig, "starts": t.isoformat(), "deadline": (t + dur).isoformat(),
                 "_dt": t + dur} for lab, t in readings]

        if status == "status_not_stated":   # never "not applicable"
            gap = rule.get("gap")
            self.add("AMBIGUITY", rule["id"], topic, [rid],
                     f"{rec['instrument']} {rec['clause']} says {ob.get('deadline', 'no deadline')} from {trig}, but "
                     f"its binding status is not stated in the document. Read it both ways until the "
                     f"authority says which applies; it is not treated as inapplicable.",
                     gap_id=gap,
                     deadline=min(r["_dt"] for r in rows).isoformat() if rows else None,
                     readings=[{"reading": "binding", "deadlines": [r["deadline"] for r in rows]},
                               {"reading": "not binding", "deadlines": []}],
                     notes=["safe working assumption: binding (earliest deadline above)"] if rows else [])
            return
        if not rec.get("verified"):
            self.add("INSUFFICIENT_EVIDENCE", rule["id"], topic, [rid],
                     f"Record unverified ({rid}): its clock is not applied until the quote is checked.")
            return
        if status != "in_force":
            start = rec.get("in_force_from")
            self.add("INSUFFICIENT_EVIDENCE", rule["id"], topic, [rid],
                     f"{rid} is {status.replace('_', ' ')} on {self.on}"
                     + (f" (commences {start})." if start else "."))
            return
        if not dur:
            self.add("INSUFFICIENT_EVIDENCE", rule["id"], topic, [rid], f"{rid} sets no deadline to compute.")
            return
        sent = next((r for r in self.facts.get("reports") or [] if r.get("record") == rid), None)
        sent_at = self.timestamp(sent["sent_at"], "reports.sent_at", problems) if sent else None
        if sent is None and self.now is None:
            problems.append("now (needed to judge a report that has not been sent)")
        if problems or not rows:
            self.add("INSUFFICIENT_EVIDENCE", rule["id"], topic, [rid],
                     f"Cannot compute the {rid} deadline; missing facts: {', '.join(problems)}. "
                     f"The clock starts when the {trig} time is confirmed.")
            return

        first, last = min(r["_dt"] for r in rows), max(r["_dt"] for r in rows)
        at = sent_at or self.now
        what = f"{rid} ({ob['deadline']} from {trig}): earliest deadline {first.isoformat()}"
        if sent_at:
            state = f"report sent {sent_at.isoformat()}"
        else:
            state = f"not sent, now {self.now.isoformat()}"
        if at <= first:
            verdict = "COMPLIANT"
            body = f"{what}; {state}, {left_text(first, at)} on the stated facts."
            if not sent_at:
                body += " Report still pending; compliant only while time remains."
        elif at <= last:
            verdict = "AMBIGUITY"
            body = (f"{what}, latest {last.isoformat()}; {state}. It is late on the stricter reading and on time "
                    f"on the later one, so the readings differ.")
        else:
            verdict = "VIOLATION"
            body = f"{what}; {state}, {left_text(first, at)} against the earliest deadline."
        self.add(verdict, rule["id"], topic, [rid], body, deadline=first.isoformat(),
                 time_left=left_text(first, at),
                 readings=[{k: v for k, v in r.items() if k != "_dt"} for r in rows] if len(rows) > 1 else [],
                 notes=["report pending"] if (verdict == "COMPLIANT" and not sent_at) else [])
        self.clock_readings.setdefault(rule.get("group", ""), []).extend(
            {"record": rid, **{k: v for k, v in r.items()}} for r in rows)

    # ---- 2. AMBIGUITY across records that give different clocks for one incident
    def clock_groups(self):
        cls = sorted(self.facts.get("classifications") or [], key=lambda c: str(c["at"]))
        labels = [c["label"] for c in cls]
        reclassified = "fault" in labels and "attack" in labels and labels.index("fault") < labels.index("attack")
        for grp in self.rules["clock_groups"]:
            rows = self.clock_readings.get(grp["id"], [])
            distinct = {r["deadline"] for r in rows}
            if len(distinct) < 2 and not (reclassified and rows):
                continue
            first = min(rows, key=lambda r: r["_dt"])
            readings = [{k: v for k, v in r.items() if k != "_dt"} for r in sorted(rows, key=lambda r: r["_dt"])]
            gap, _ = find_gap(self.kb, grp["topic"], self.jur) if not grp.get("gap") else (grp["gap"], "")
            body = (f"{len(rows)} readings give {len(distinct)} different deadlines for the same incident; "
                    f"the earliest, {first['deadline']} ({first['record']}, {first['trigger']} = {first['starts']}), "
                    f"is the safe working deadline.")
            notes = []
            if self.now:
                body += f" {left_text(first['_dt'], self.now)} at {self.now.isoformat()}."
            if reclassified:
                notes.append("incident was first classified as fault, then as attack; clocks may start "
                             f"from different times ({', '.join(c['at'] if isinstance(c['at'], str) else c['at'].isoformat() for c in cls)})")
            self.add("AMBIGUITY", grp["id"], grp["topic"], sorted({r["record"] for r in rows}), body,
                     gap_id=gap, deadline=first["deadline"],
                     time_left=left_text(first["_dt"], self.now) if self.now else None,
                     readings=readings, notes=notes)

    # ---- 3. CONFLICT between proposed actions
    def conflicts(self):
        acts = {a["playbook"]: a for a in self.facts.get("proposed_actions") or []}
        for rule in self.rules["conflicts"]:
            a, b = (acts.get(p) for p in rule["playbooks"])
            if not (a and b):
                continue
            ta, tb = set(a.get("targets") or []), set(b.get("targets") or [])
            recs = list(a.get("supporting_records") or []) + list(b.get("supporting_records") or [])
            if not (ta and tb):
                self.add("INSUFFICIENT_EVIDENCE", rule["id"], rule.get("topic"), recs or [rule["records"][0]],
                         "Two proposed actions may clash, but one has no targets listed; cannot test overlap.")
                continue
            shared = sorted(ta & tb)
            if not shared:
                continue
            body = (f"{a['playbook']} ({a.get('agent', '?')}) and {b['playbook']} ({b.get('agent', '?')}) both act on "
                    f"{', '.join(shared)}. {rule['clash']} The cited records support each side but none settles the "
                    f"choice in the sources we checked, as of {self.as_of}; a human decides.")
            rej = rejected_gap(self.kb, rule["gap_topic"], self.jur)
            if rej:                       # a human ruled this is not a gap: keep the clash, raise no gap
                gap, note = None, (f"rejected gap {rej['id']} ({rej.get('verified_by')}): "
                                   f"topic '{rule['gap_topic']}' not raised as a gap")
            else:
                gap, status = find_gap(self.kb, rule["gap_topic"], self.jur)
                note = f"gap {gap}: {status}"
            self.add("CONFLICT", rule["id"], rule.get("topic"), recs or rule["records"], body, gap_id=gap,
                     actions=[dict(a), dict(b)],
                     notes=[note])

    # ---- 4. topic coverage
    def questions(self):
        for q in self.facts.get("obligation_questions") or []:
            jur, topic = q.get("jurisdiction", self.jur), q["topic"]
            recs = self.kb.covering(topic, jur, self.on)
            if q.get("record"):
                recs = [r for r in recs if r["id"] == q["record"]]
            by = lambda s: [r for r in recs if r["_status"] == s]     # noqa: E731
            ids = lambda rs: [r["id"] for r in rs]                    # noqa: E731
            label = f"{q['id']} ({q.get('text', topic)})"
            rid = f"COVERAGE:{jur}:{topic}"
            ok = [r for r in by("in_force") if r.get("verified")]
            if ok:
                self.add("COMPLIANT", rid, topic, ids(ok),
                         f"{label}: covered by {', '.join(ids(ok))} ({jur}, in force on {self.on}).")
                continue
            if recs and all(r["_status"] == "status_not_stated" for r in recs):
                gap, st = find_gap(self.kb, topic, jur)
                notes = [f"gap {gap}: {st}"]
                self.add("AMBIGUITY", rid, topic, ids(recs),
                         f"{label}: the only matching record(s) {', '.join(ids(recs))} do not state whether they bind, "
                         f"so two readings are given and neither is dropped as 'not applicable'.",
                         gap_id=gap,
                         readings=[{"reading": "record binding", "result": "duty as written in the record (see its quote)"},
                                   {"reading": "record not binding",
                                    "result": f"no duty found in the sources we checked, as of {self.as_of}"}],
                         notes=notes)
                continue
            if by("in_force"):
                self.add("INSUFFICIENT_EVIDENCE", rid, topic, ids(by("in_force")),
                         f"{label}: the matching {jur} record(s) {', '.join(ids(by('in_force')))} are in force but "
                         f"record unverified, so coverage is not asserted.")
                continue
            g = rejected_gap(self.kb, topic, jur)
            if g:                         # a human ruled this is not a gap: state the facts, cite the decision
                cite = ids(recs) or [e for e in g.get("evidence", []) if e in self.kb.records]
                self.add("INSUFFICIENT_EVIDENCE", rid, topic, cite,
                         f"{label}: no in-force duty specific to this topic on {self.on}, but gap {g['id']} was "
                         f"rejected by a human reviewer ({g.get('verified_by')}). Not reported as a gap.",
                         notes=[f"rejected gap {g['id']}"], **({} if cite else {"gap_id": g["id"]}))
                continue
            gap, st = find_gap(self.kb, topic, jur)
            if by("not_yet"):
                starts = sorted({str(r["in_force_from"]) for r in by("not_yet") if r.get("in_force_from")})
                when = f"commence {starts[0]}" if starts else "have not commenced (date not recorded)"
                body = (f"{label}: matching {jur} record(s) {', '.join(ids(by('not_yet')))} are not in force on {self.on}; "
                        f"they {when}. Nothing in force was found in the sources we checked, as of {self.as_of}.")
                cited = ids(by("not_yet"))
            else:
                body = (f"{label}: no in-force, binding {jur} record on '{topic}' was found in the sources we checked, "
                        f"as of {self.as_of}. This is a candidate gap for a human to confirm.")
                cited = []
                if by("not_binding"):
                    body += f" Non-binding material exists: {', '.join(ids(by('not_binding')))}."
                    cited = ids(by("not_binding"))
            self.add("POTENTIAL_GAP", rid, topic, cited, body, gap_id=gap, notes=[f"gap {gap}: {st}"])

    def run(self) -> list[Verdict]:
        self.deadline_rules()
        self.clock_groups()
        self.conflicts()
        self.questions()
        return self.out


def evaluate(facts: dict, kb) -> list[Verdict]:
    """Run every rule against the facts and return the verdicts (possibly none)."""
    return _Engine(facts, kb).run()
