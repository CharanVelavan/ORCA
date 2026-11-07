"""Shared state of one run: facts, clock, alerts, message bus, routes, assets, approvals, audit.

The simulator and the scenario runner write into it; agents read it only through their tools.
The clock is ``facts["now"]`` and nothing else (no wall clock), so a run replays exactly.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path

from orca import kb as kbmod
from orca.audit import AuditLog

# Who owns what (emulated). execute_playbook refuses targets outside the caller's list.
DEFAULT_ASSETS = {
    "satellite_operator": {"mgmt_account": ["*"], "mgmt_system": ["SAT-MGMT"], "terminal": ["*"]},
    "mobile_operator": {"site": ["CHN-01", "CHN-02", "CHN-03", "CHN-04", "CHN-05", "CHN-06"]},
    "power_utility": {"grid": ["GRID-CHN"]},
}
INDIAN_GATEWAYS = {"GW-IN-1", "GW-IN-2"}

# Dependants that PB-10 warns, per site (emulated dependency graph).
DEPENDANTS = {
    "CHN-01": ["hospital", "112"], "CHN-02": ["payments", "112"], "CHN-03": ["112"],
    "CHN-04": ["grid", "112"], "CHN-05": ["112", "public_alerts"], "CHN-06": ["traffic_signals", "112"],
}


@dataclass
class World:
    facts: dict
    audit: AuditLog
    kb: object = None
    alerts: list = field(default_factory=list)          # {id, at, source(M1..M4|agent), site, label, detail, explain}
    bus: list = field(default_factory=list)             # {at, sender, to, kind, payload}
    routes: dict = field(default_factory=dict)          # site -> {path: {gateway, integrity}}
    active_path: dict = field(default_factory=dict)     # site -> path id
    assets: dict = field(default_factory=lambda: copy.deepcopy(DEFAULT_ASSETS))
    disabled_accounts: set = field(default_factory=set)
    drafts: list = field(default_factory=list)          # notices drafted by agents (a human sends)
    gap_drafts: list = field(default_factory=list)      # record_gap output (a human reviews; never kb/)
    health: object = None                               # callable(targets, playbook, params, stage_pct) -> bool; simulator hook

    def __post_init__(self):
        if self.kb is None:
            self.kb = kbmod.load()

    @classmethod
    def new(cls, facts: dict, audit_path: Path, **kw) -> "World":
        return cls(facts=facts, audit=AuditLog(audit_path), **kw)

    @property
    def now(self) -> str:
        if not self.facts.get("now"):
            raise ValueError("facts.now is not set; every action needs a time from the facts")
        return self.facts["now"]

    def log(self, kind: str, actor: str, payload: dict) -> dict:
        return self.audit.append(kind, actor, payload, ts=self.now)

    def owns(self, role: str, kind: str, target: str) -> bool:
        allowed = self.assets.get(role, {}).get(kind, [])
        return "*" in allowed or target in allowed
