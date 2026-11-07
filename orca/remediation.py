"""Guarded remediation: approval requests, human approval, and execute_playbook.

These checks are code, not prompt text (docs/plan/A-agent-roles.md section 1.3). execute_playbook
refuses unless ALL hold:
  1. the playbook is in the catalogue and executable;
  2. the caller is the playbook's owner and every target is in the caller's own asset list;
  3. a one-time approval token exists for exactly this plan (hash of playbook, targets, params, owner);
  4. the approval has not expired (times from the facts, never the wall clock);
  5. the clone test passed;
  6. a fresh rule-engine run on the current facts has no VIOLATION;
  7. playbook preconditions hold (PB-06: path integrity verified and gateway in India, Authz Rule 60(1)(b)).
Then: staged rollout 5 -> 25 -> 100 %, with a health check after each stage and rollback on failure.

Approval is a human act. ``approve`` is called by the commander console, never exposed as an agent tool.
"""
from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path

import yaml

from orca import rules
from orca.audit import canonical
from orca.world import DEPENDANTS, INDIAN_GATEWAYS, World

CATALOGUE_PATH = Path(__file__).resolve().parent.parent / "playbooks" / "catalogue.yaml"
STAGES = (5, 25, 100)
DEFAULT_TTL = dt.timedelta(minutes=30)


def catalogue() -> dict[str, dict]:
    return {p["id"]: p for p in yaml.safe_load(CATALOGUE_PATH.read_text())}


def plan_hash(playbook: str, targets: list[str], params: dict, owner: str) -> str:
    body = {"playbook": playbook, "targets": sorted(targets), "params": params or {}, "owner": owner}
    return hashlib.sha256(canonical(body).encode()).hexdigest()


class Refused(Exception):
    """execute_playbook / request_approval refused; the message says which check failed."""


class Remediation:
    def __init__(self, world: World):
        self.w = world
        self.cat = catalogue()
        self.plans: dict[str, dict] = {}      # hash -> plan
        self.tokens: dict[str, dict] = {}     # token -> {hash, approver, expires, used}

    # ------------------------------------------------------------ agent side
    def request_approval(self, caller: str, playbook: str, targets: list[str], params: dict | None,
                         reason: str, ttl: dt.timedelta = DEFAULT_TTL) -> dict:
        pb = self._pb(playbook)
        self._check_owner(caller, pb, targets)
        h = plan_hash(playbook, targets, params or {}, caller)
        now = rules.parse_ts(self.w.now)
        plan = {"hash": h, "playbook": playbook, "title": pb["title"], "owner": caller, "targets": list(targets),
                "params": params or {}, "reason": reason, "requested_at": self.w.now,
                "expires_at": (now + ttl).isoformat(), "executable": pb.get("executable", False),
                "clone_test": self.clone_test(pb, targets, params or {}),
                "verdicts": [v.verdict for v in rules.evaluate(self.w.facts, self.w.kb)]}
        self.plans[h] = plan
        self.w.log("approval_requested", caller, plan)
        return plan

    def execute(self, caller: str, playbook: str, targets: list[str], params: dict | None, token: str) -> dict:
        params = params or {}
        try:
            pb = self._pb(playbook)
            if not pb.get("executable"):
                raise Refused(f"{playbook} is specified only, not executable")
            self._check_owner(caller, pb, targets)
            t = self.tokens.get(token)
            if not t or t["used"]:
                raise Refused("no valid one-time approval token")
            h = plan_hash(playbook, targets, params, caller)
            if t["hash"] != h:
                raise Refused("plan hash does not match the approved plan (targets or parameters changed)")
            if rules.parse_ts(self.w.now) > rules.parse_ts(t["expires"]):
                raise Refused("approval expired")
            ct = self.clone_test(pb, targets, params)
            if not ct["passed"]:
                raise Refused(f"clone test failed: {ct['detail']}")
            fresh = rules.evaluate(self.w.facts, self.w.kb)
            if any(v.verdict == "VIOLATION" for v in fresh):
                raise Refused("fresh rule-engine verdict contains VIOLATION")
        except Refused as e:
            self.w.log("execute_refused", caller, {"playbook": playbook, "targets": targets, "reason": str(e)})
            raise
        t["used"] = True
        result = self._rollout(caller, pb, targets, params)
        self.w.log("executed" if result["ok"] else "rolled_back", caller,
                   {"playbook": playbook, "targets": targets, "params": params, "plan_hash": h,
                    "approver": t["approver"], **result})
        return result

    # ------------------------------------------------------------ human side
    def approve(self, plan_hash_: str, approver: str, pin: str) -> str:
        """Commander approves a plan. Returns a one-time token. Never called by an agent."""
        plan = self.plans.get(plan_hash_)
        if not plan:
            raise Refused("unknown plan")
        if not approver or not pin:
            raise Refused("approval needs a name and a PIN")
        token = hashlib.sha256(f"{plan_hash_}|{approver}|{pin}|{self.w.now}".encode()).hexdigest()[:24]
        self.tokens[token] = {"hash": plan_hash_, "approver": approver, "expires": plan["expires_at"], "used": False}
        self.w.log("approved", f"human:{approver}", {"plan_hash": plan_hash_, "playbook": plan["playbook"],
                                                    "expires_at": plan["expires_at"]})
        return token

    def reject(self, plan_hash_: str, approver: str, reason: str) -> None:
        self.w.log("rejected", f"human:{approver}", {"plan_hash": plan_hash_, "reason": reason})

    # ------------------------------------------------------------ checks
    def _pb(self, playbook: str) -> dict:
        if playbook not in self.cat:
            raise Refused(f"{playbook} is not in the playbook catalogue")
        return self.cat[playbook]

    def _check_owner(self, caller: str, pb: dict, targets: list[str]) -> None:
        if pb["owner"] != caller:
            raise Refused(f"{pb['id']} is owned by {pb['owner']}, not {caller}")
        for t in targets:
            if not self.w.owns(caller, pb["target_kind"], t):
                raise Refused(f"target {t} is not in {caller}'s assets")

    def clone_test(self, pb: dict, targets: list[str], params: dict) -> dict:
        """Run the plan's preconditions on a copy of the state. Nothing real changes."""
        if pb["id"] == "PB-06":
            path = params.get("path")
            for site in targets:
                cand = self.w.routes.get(site, {}).get(path)
                if not cand:
                    return {"passed": False, "detail": f"{site}: no backup path {path!r} offered"}
                if cand.get("gateway") not in INDIAN_GATEWAYS:
                    return {"passed": False, "detail": f"{site}: path {path} uses gateway {cand.get('gateway')} "
                                                       "outside India (Authz Rule 60(1)(b))"}
                if cand.get("integrity") != "verified":
                    return {"passed": False, "detail": f"{site}: path {path} integrity is {cand.get('integrity')}, "
                                                       "not verified clean"}
        if pb["id"] == "PB-10" and not params.get("message"):
            return {"passed": False, "detail": "warning text is empty"}
        return {"passed": True, "detail": "preconditions hold on the cloned state"}

    # ------------------------------------------------------------ effects
    def _rollout(self, caller: str, pb: dict, targets: list[str], params: dict) -> dict:
        stages = []
        for pct in STAGES:
            ok = self.w.health(targets, pb["id"], params, pct) if self.w.health else True
            stages.append({"pct": pct, "healthy": bool(ok)})
            if not ok:
                return {"ok": False, "stages": stages, "detail": f"health check failed at {pct} %, rolled back"}
        if pb["id"] == "PB-01":
            self.w.disabled_accounts.update(targets)
        elif pb["id"] == "PB-06":
            for site in targets:
                self.w.active_path[site] = params["path"]
        elif pb["id"] == "PB-10":
            to = sorted({d for s in targets for d in DEPENDANTS.get(s, [])})
            self.w.bus.append({"at": self.w.now, "sender": caller, "to": to, "kind": "warning",
                               "payload": {"sites": targets, "message": params["message"]}})
        return {"ok": True, "stages": stages, "detail": "rolled out 5/25/100 %"}
