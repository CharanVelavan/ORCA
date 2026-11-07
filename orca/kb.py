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
}
JURISDICTIONS = {"IN", "EU", "US", "AE", "INTL"}
DURATION = re.compile(r"^P(\d+D)?(T(\d+H)?(\d+M)?)?$")
RECORD_FIELDS = {
    "id", "jurisdiction", "instrument", "clause", "authority", "binding_status", "issued",
    "in_force_from", "topic", "obligation", "quote", "pinpoint", "summary", "source",
    "verified", "verified_by", "notes",
}
REQUIRED = {"id", "jurisdiction", "instrument", "clause", "authority", "binding_status",
            "topic", "summary", "source", "verified"}
GAP_REQUIRED = {"id", "jurisdiction", "title", "finding", "evidence", "affects", "verified"}


@dataclass
class KB:
    records: dict[str, dict] = field(default_factory=dict)
    gaps: dict[str, dict] = field(default_factory=dict)
    sources: dict[str, dict] = field(default_factory=dict)

    def get(self, rid: str) -> dict:
        return self.records.get(rid) or self.gaps[rid]

    def by_jurisdiction(self, *codes: str) -> list[dict]:
        return [r for r in self.records.values() if r["jurisdiction"] in codes]

    def in_force(self, rid: str, on: dt.date) -> bool:
        r = self.records[rid]
        if r["binding_status"] not in {"binding", "binding_not_in_force"}:
            return False
        start = r.get("in_force_from")
        if start is None:
            return r["binding_status"] == "binding"
        return on >= start


def _load_list(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text()) or []
    if not isinstance(data, list):
        raise ValueError(f"{path}: top level must be a list")
    return data


def load(kb_dir: Path = KB_DIR) -> KB:
    kb = KB()
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
        for ev in g.get("evidence", []):
            if ev not in kb.records:
                errs.append(f"{where}: evidence {ev} is not a record id")
    clash = kb.records.keys() & kb.gaps.keys()
    if clash:
        errs.append(f"ids used for both records and gaps: {sorted(clash)}")
    return errs
