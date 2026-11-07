"""Load and validate the policy knowledge base (kb/*.yaml).

The rule engine and the agents read records only through this module, so an id
that is not in the knowledge base can never be cited.
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
KB_DIR = ROOT / "kb"

BINDING = {"binding", "binding_not_in_force", "not_stated", "non_binding", "proposal"}
TRIGGERS = {"occurrence", "noticing", "awareness", "none"}
TOPICS = {
    "incident_reporting", "point_of_contact", "log_retention", "cert_powers",
    "emergency_powers", "telecom_cyber_security", "critical_infrastructure", "standards",
    "personal_data_breach", "cross_border_transfer", "space_cyber", "emergency_priority",
    # added 7 Nov 2026 for topic-coverage gap detection
    "ntn_coverage", "downstream_warning", "capacity_priority", "failover_path_security",
    "backup_power", "joint_command",
    # added 7 Nov 2026 night (policy sweep)
    "data_location", "terminal_control", "interference_reporting", "public_alerts",
    "outage_reporting", "disaster_coordination", "grid_comms_backup",
    "network_info_sharing", "network_redundancy", "standards_power",
}
GAP_KINDS = {"coverage", "ambiguity", "standards"}
GAP_STATUS = {"candidate", "confirmed", "rejected"}   # confirmed / rejected only by a human
JURISDICTIONS = {"IN", "EU", "US", "AE", "INTL"}
DURATION = re.compile(r"^P(\d+D)?(T(\d+H)?(\d+M)?)?$")
RECORD_FIELDS = {
    "id", "jurisdiction", "instrument", "clause", "authority", "binding_status", "issued",
    "in_force_from", "topic", "topics", "obligation", "quote", "pinpoint", "summary", "source",
    "verified", "verified_by", "notes",
}
REQUIRED = {"id", "jurisdiction", "instrument", "clause", "authority", "binding_status",
            "topic", "topics", "summary", "source", "verified"}
GAP_REQUIRED = {"id", "jurisdiction", "kind", "topic", "status", "title", "finding", "evidence",
                "affects", "search", "verified"}
GAP_FIELDS = GAP_REQUIRED | {"analysis", "interim_action", "recommendation", "verified_by", "notes"}
SEARCH_REQUIRED = {"date", "sources_checked", "terms", "nearest_provision", "why_not_covered"}


@dataclass
class KB:
    records: dict[str, dict] = field(default_factory=dict)
    gaps: dict[str, dict] = field(default_factory=dict)
    sources: dict[str, dict] = field(default_factory=dict)
    as_of: dt.date | None = None          # date the KB content was last checked (kb/meta.yaml)

    def get(self, rid: str) -> dict:
        return self.records.get(rid) or self.gaps[rid]

    def by_jurisdiction(self, *codes: str) -> list[dict]:
        return [r for r in self.records.values() if r["jurisdiction"] in codes]

    def in_force_status(self, rid: str, on: dt.date) -> str:
        """in_force | not_yet | status_not_stated | not_binding (see docs/plan/build-contract.md).

        A binding record with in_force_from null counts as in force; validate() flags those
        so the date gets filled in.
        """
        r = self.records[rid]
        b = r["binding_status"]
        if b == "not_stated":
            return "status_not_stated"
        if b in {"non_binding", "proposal"}:
            return "not_binding"
        start = r.get("in_force_from")
        if b == "binding_not_in_force":
            return "in_force" if start is not None and on >= start else "not_yet"
        return "in_force" if start is None or on >= start else "not_yet"

    def in_force(self, rid: str, on: dt.date) -> bool:
        return self.in_force_status(rid, on) == "in_force"

    def covering(self, topic: str, jurisdiction: str, on: dt.date) -> list[dict]:
        """Records of one jurisdiction whose `topics` include `topic`, each copied with `_status`."""
        out = []
        for rid, r in self.records.items():
            if r["jurisdiction"] == jurisdiction and topic in r.get("topics", []):
                out.append({**r, "_status": self.in_force_status(rid, on)})
        return out

    def gaps_for(self, topic: str, jurisdiction: str) -> list[dict]:
        return [g for g in self.gaps.values()
                if g.get("topic") == topic and g["jurisdiction"] in (jurisdiction, "INTL")
                and g.get("status") != "rejected"]          # a human rejected it: never cite it


def _load_list(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text()) or []
    if not isinstance(data, list):
        raise ValueError(f"{path}: top level must be a list")
    return data


def load(kb_dir: Path = KB_DIR) -> KB:
    kb = KB()
    meta = kb_dir / "meta.yaml"
    if meta.exists():
        kb.as_of = (yaml.safe_load(meta.read_text()) or {}).get("as_of")
    for s in _load_list(kb_dir / "sources.yaml"):
        kb.sources[s["id"]] = s
    for p in sorted(kb_dir.glob("gaps/*.yaml")):
        for g in _load_list(p):
            g["_file"] = str(p.relative_to(kb_dir.parent))
            kb.gaps[g["id"]] = g
    for p in sorted(kb_dir.glob("*/*.yaml")):
        if p.parent.name == "gaps":
            continue
        for r in _load_list(p):
            r["_file"] = str(p.relative_to(kb_dir.parent))
            if r["id"] in kb.records:
                raise ValueError(f"duplicate id {r['id']}")
            kb.records[r["id"]] = r
    return kb


def validate(kb: KB) -> list[str]:
    """Return a list of problems; empty means the knowledge base is valid."""
    errs: list[str] = []
    for rid, r in kb.records.items():
        where = f"{r['_file']}:{rid}"
        missing = REQUIRED - r.keys()
        if missing:
            errs.append(f"{where}: missing {sorted(missing)}")
        extra = set(r) - RECORD_FIELDS - {"_file"}
        if extra:
            errs.append(f"{where}: unknown fields {sorted(extra)}")
        if r.get("jurisdiction") not in JURISDICTIONS:
            errs.append(f"{where}: bad jurisdiction {r.get('jurisdiction')}")
        if r.get("binding_status") not in BINDING:
            errs.append(f"{where}: bad binding_status {r.get('binding_status')}")
        if r.get("topic") not in TOPICS:
            errs.append(f"{where}: bad topic {r.get('topic')}")
        tops = r.get("topics") or []
        if not tops or r.get("topic") not in tops:
            errs.append(f"{where}: topics must be a non-empty list that includes topic")
        for t in tops:
            if t not in TOPICS:
                errs.append(f"{where}: bad topics entry {t}")
        if r.get("source") not in kb.sources:
            errs.append(f"{where}: source {r.get('source')} not in sources.yaml")
        for k in ("issued", "in_force_from"):
            v = r.get(k)
            if v is not None and not isinstance(v, dt.date):
                errs.append(f"{where}: {k} must be a YYYY-MM-DD date")
        if r.get("verified"):
            for k in ("quote", "pinpoint", "verified_by"):
                if not r.get(k):
                    errs.append(f"{where}: verified record needs {k}")
        ob = r.get("obligation")
        if ob:
            if ob.get("trigger") not in TRIGGERS:
                errs.append(f"{where}: bad trigger {ob.get('trigger')}")
            d = ob.get("deadline")
            if d is not None and not DURATION.match(str(d)):
                errs.append(f"{where}: deadline {d} is not an ISO 8601 duration")
        if r.get("binding_status") == "binding_not_in_force" and not r.get("notes"):
            errs.append(f"{where}: not-in-force record should say when it commences")
    for gid, g in kb.gaps.items():
        where = f"{g['_file']}:{gid}"
        missing = GAP_REQUIRED - g.keys()
        if missing:
            errs.append(f"{where}: missing {sorted(missing)}")
        extra = set(g) - GAP_FIELDS - {"_file"}
        if extra:
            errs.append(f"{where}: unknown fields {sorted(extra)}")
        if g.get("kind") not in GAP_KINDS:
            errs.append(f"{where}: bad kind {g.get('kind')}")
        if g.get("topic") not in TOPICS:
            errs.append(f"{where}: bad topic {g.get('topic')}")
        if g.get("status") not in GAP_STATUS:
            errs.append(f"{where}: bad status {g.get('status')}")
        if g.get("verified") and (g.get("status") not in ("confirmed", "rejected") or not g.get("verified_by")):
            errs.append(f"{where}: verified gap needs status confirmed/rejected and verified_by (a human)")
        if g.get("status") in ("confirmed", "rejected") and not (g.get("verified") and g.get("verified_by")):
            errs.append(f"{where}: confirmed or rejected gap must be verified by a human (verified_by)")
        srch = g.get("search") or {}
        miss = SEARCH_REQUIRED - srch.keys()
        if miss:
            errs.append(f"{where}: search record missing {sorted(miss)}")
        for sid in srch.get("sources_checked", []):
            if sid not in kb.sources:
                errs.append(f"{where}: sources_checked {sid} not in sources.yaml")
        for ev in g.get("evidence", []):
            if ev not in kb.records:
                errs.append(f"{where}: evidence {ev} is not a record id")
    clash = kb.records.keys() & kb.gaps.keys()
    if clash:
        errs.append(f"ids used for both records and gaps: {sorted(clash)}")
    return errs
