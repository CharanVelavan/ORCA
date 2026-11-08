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

Autonomy (Mission 6). The human sets MANUAL / ASSISTED / AUTO with ``set_mode``, scoped to sites and
playbooks, with a PIN and an expiry (facts clock). MANUAL: every action needs the commander. ASSISTED:
low-risk playbooks (catalogue ``risk: low``) are approved automatically, the rest need the commander.
AUTO: every executable playbook in scope is approved automatically. The automatic approver is logged as
``autonomy:<MODE> (granted by <name>)``. Hard limits hold in every mode: own assets only, no foreign
gateway, clone test, staged rollout with rollback, at most MAX_ACTIONS_PER_WINDOW executions per
WINDOW, and at most MAX_AUTO_TARGETS targets per automatically approved action. AUTO drops to ASSISTED
by itself on M3 doubt, a rollback, a CONFLICT verdict or an audit-chain integrity failure. The kill
switch revokes every token and refuses all execution until a human releases it.

Two clocks: a request goes stale REQUEST_TTL after it was made (an old plan must not be approved against
a changed network); a token is valid TOKEN_TTL from the moment of approval. Tokens are single use and
a plan that has run cannot be approved again; the agent must request again.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import os
from pathlib import Path

import yaml

from orca import rules
from orca.audit import canonical
from orca.world import DEPENDANTS, INDIAN_GATEWAYS, World

CATALOGUE_PATH = Path(__file__).resolve().parent.parent / "playbooks" / "catalogue.yaml"
STAGES = (5, 25, 100)
REQUEST_TTL = dt.timedelta(minutes=30)       # a request goes stale this long after it was made
TOKEN_TTL = dt.timedelta(minutes=15)         # a token is valid this long after approval
DEFAULT_TTL = REQUEST_TTL                    # kept for callers that pass ttl=
MODES = ("MANUAL", "ASSISTED", "AUTO")
WINDOW = dt.timedelta(minutes=10)
MAX_ACTIONS_PER_WINDOW = 6
MAX_AUTO_TARGETS = 2                         # blast-radius cap for automatically approved actions
M3_DOUBT_CONFIDENCE = 0.6


def catalogue() -> dict[str, dict]:
    return {p["id"]: p for p in yaml.safe_load(CATALOGUE_PATH.read_text())}


def plan_hash(playbook: str, targets: list[str], params: dict, owner: str) -> str:
    body = {"playbook": playbook, "targets": sorted(targets), "params": params or {}, "owner": owner}
    return hashlib.sha256(canonical(body).encode()).hexdigest()


class Refused(Exception):
    """execute_playbook / request_approval refused; the message says which check failed."""


class Remediation:
    def __init__(self, world: World, pin_sha256: str | None = None):
        self.w = world
        self.cat = catalogue()
        self.plans: dict[str, dict] = {}      # hash -> plan
        self.tokens: dict[str, dict] = {}     # token -> {hash, approver, expires, used, revoked}
        self.pin_sha256 = pin_sha256 or os.environ.get("ORCA_COMMANDER_PIN_SHA256") or None
        self.grants: list[dict] = []          # autonomy grants: {mode, sites, playbooks, expires, granted_by}
        self.downgraded: str | None = None    # cause, once AUTO has dropped to ASSISTED
        self.killed: dict | None = None       # kill-switch record while engaged
        self.executions: list[str] = []       # times of executions (rate limit)
        self._seq = 0                         # token counter: every approval mints a new token

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
        mode, grant = self.mode_for(playbook, targets)
        plan["mode"] = mode
        if self._auto_ok(mode, pb, targets, plan):
            plan["auto_token"] = self._mint(h, f"autonomy:{mode} (granted by {grant['granted_by']})")
        return plan

    def execute(self, caller: str, playbook: str, targets: list[str], params: dict | None, token: str) -> dict:
        params = params or {}
        try:
            pb = self._pb(playbook)
            if not pb.get("executable"):
                raise Refused(f"{playbook} is specified only, not executable")
            if self.killed:
                raise Refused(f"kill switch engaged by {self.killed['by']}: all execution stopped")
            self._check_owner(caller, pb, targets)
            t = self.tokens.get(token)
            if not t or t["used"] or t.get("revoked"):
                raise Refused("no valid one-time approval token")
            h = plan_hash(playbook, targets, params, caller)
            if t["hash"] != h:
                raise Refused("plan hash does not match the approved plan (targets or parameters changed)")
            if rules.parse_ts(self.w.now) > rules.parse_ts(t["expires"]):
                raise Refused("approval expired (token is valid 15 min from approval)")
            recent = [x for x in self.executions if rules.parse_ts(self.w.now) - rules.parse_ts(x) < WINDOW]
            if len(recent) >= MAX_ACTIONS_PER_WINDOW:
                raise Refused(f"rate limit: {MAX_ACTIONS_PER_WINDOW} executions in {WINDOW} already")
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
        self.plans[h]["executed"] = True
        self.executions.append(self.w.now)
        result = self._rollout(caller, pb, targets, params)
        if not result["ok"]:
            self._downgrade("rollback")
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
        if self.killed:
            raise Refused("kill switch engaged: release it before approving")
        self._check_pin(approver, pin)
        if plan.get("executed"):
            raise Refused("this plan has already run; the agent must request again")
        if rules.parse_ts(self.w.now) > rules.parse_ts(plan["expires_at"]):
            raise Refused("request is stale (older than 30 min); the agent must request again on the current state")
        return self._mint(plan_hash_, approver, human=True)

    def reject(self, plan_hash_: str, approver: str, reason: str) -> None:
        self.w.log("rejected", f"human:{approver}", {"plan_hash": plan_hash_, "reason": reason})

    # ------------------------------------------------------------ autonomy (human side)
    def set_mode(self, mode: str, approver: str, pin: str, minutes: int, sites: list[str] | str = "*",
                 playbooks: list[str] | str = "*") -> dict:
        """Grant an autonomy mode for a scope until now + minutes. MANUAL clears matching grants."""
        if mode not in MODES:
            raise Refused(f"unknown mode {mode}; use one of {', '.join(MODES)}")
        if self.killed:
            raise Refused("kill switch engaged: release it before changing modes")
        self._check_pin(approver, pin)
        if not 0 < minutes <= 24 * 60:
            raise Refused("a mode grant needs an expiry between 1 minute and 24 hours")
        grant = {"mode": mode, "sites": sites, "playbooks": playbooks, "granted_by": approver,
                 "granted_at": self.w.now,
                 "expires": (rules.parse_ts(self.w.now) + dt.timedelta(minutes=minutes)).isoformat()}
        if mode == "MANUAL":
            self.grants = [g for g in self.grants if not (g["sites"] == sites and g["playbooks"] == playbooks)]
        else:
            self.grants.append(grant)
            if mode == "AUTO":
                self.downgraded = None             # a fresh human grant clears an earlier downgrade
        self.w.log("autonomy_set", f"human:{approver}", grant)
        return grant

    def kill(self, approver: str, pin: str, reason: str) -> None:
        """Kill switch: revoke every token, drop all grants, refuse all execution until released."""
        self._check_pin(approver, pin)
        revoked = [k for k, t in self.tokens.items() if not t["used"] and not t.get("revoked")]
        for k in revoked:
            self.tokens[k]["revoked"] = True
        self.grants, self.killed = [], {"by": approver, "at": self.w.now, "reason": reason}
        self.w.log("kill_switch", f"human:{approver}", {"reason": reason, "tokens_revoked": len(revoked)})

    def release_kill(self, approver: str, pin: str) -> None:
        self._check_pin(approver, pin)
        self.w.log("kill_switch_released", f"human:{approver}", {"was": self.killed})
        self.killed = None                         # back to MANUAL everywhere; grants must be set again

    def mode_for(self, playbook: str, targets: list[str]) -> tuple[str, dict | None]:
        """Effective mode for this action: the most autonomous live grant covering it, after downgrades."""
        if self.killed:
            return "MANUAL", None
        self._check_downgrade()
        now = rules.parse_ts(self.w.now)
        best, best_g = "MANUAL", None
        for g in self.grants:
            if now > rules.parse_ts(g["expires"]):
                continue
            if g["playbooks"] != "*" and playbook not in g["playbooks"]:
                continue
            if g["sites"] != "*" and not all(t in g["sites"] for t in targets):
                continue
            m = "ASSISTED" if (g["mode"] == "AUTO" and self.downgraded) else g["mode"]
            if MODES.index(m) > MODES.index(best):
                best, best_g = m, g
        return best, best_g

    # ------------------------------------------------------------ autonomy (internals)
    def _auto_ok(self, mode: str, pb: dict, targets: list[str], plan: dict) -> bool:
        if mode == "MANUAL" or not pb.get("executable"):
            return False
        if mode == "ASSISTED" and pb.get("risk") != "low":
            return False
        if len(targets) > MAX_AUTO_TARGETS:
            self.w.log("autonomy_blocked", "system", {"plan_hash": plan["hash"], "reason":
                       f"{len(targets)} targets > cap {MAX_AUTO_TARGETS}; needs the commander"})
            return False
        if not plan["clone_test"]["passed"] or "VIOLATION" in plan["verdicts"]:
            return False
        return True

    def _mint(self, plan_hash_: str, approver: str, human: bool = False) -> str:
        self._seq += 1
        token = hashlib.sha256(f"{plan_hash_}|{approver}|{self.w.now}|{self._seq}".encode()).hexdigest()[:24]
        expires = (rules.parse_ts(self.w.now) + TOKEN_TTL).isoformat()
        self.tokens[token] = {"hash": plan_hash_, "approver": approver, "expires": expires, "used": False}
        self.plans[plan_hash_]["token_expires_at"] = expires
        self.w.log("approved", f"human:{approver}" if human else approver,
                   {"plan_hash": plan_hash_, "playbook": self.plans[plan_hash_]["playbook"],
                    "token_expires_at": expires, "request_expires_at": self.plans[plan_hash_]["expires_at"]})
        return token

    def _check_pin(self, approver: str, pin: str) -> None:
        if not approver or not pin:
            raise Refused("this needs a name and a PIN")
        if self.pin_sha256 is None:
            return                                 # demo mode: no PIN hash configured (logged in set_mode/approve)
        if not hmac.compare_digest(hashlib.sha256(pin.encode()).hexdigest(), self.pin_sha256):
            self.w.log("pin_refused", f"human:{approver}", {})
            raise Refused("wrong PIN")

    def _check_downgrade(self) -> None:
        if self.downgraded or not any(g["mode"] == "AUTO" for g in self.grants):
            return
        if self.w.audit.verify() is not None:
            return self._downgrade("audit chain integrity failure")
        for a in self.w.alerts:
            if a.get("source") == "M3" and (a.get("label") == "abstain" or a.get("abstained")
                                            or (a.get("confidence") is not None
                                                and a["confidence"] < M3_DOUBT_CONFIDENCE)):
                return self._downgrade(f"M3 doubt on {a.get('site')}")
        if any(v.verdict == "CONFLICT" for v in rules.evaluate(self.w.facts, self.w.kb)):
            return self._downgrade("CONFLICT verdict")

    def _downgrade(self, cause: str) -> None:
        if self.downgraded:
            return
        self.downgraded = cause
        if any(g["mode"] == "AUTO" for g in self.grants):
            self.w.log("autonomy_downgraded", "system", {"from": "AUTO", "to": "ASSISTED", "cause": cause})

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
        from orca.sim import netops as _net
        if pb["id"] in _net.NET_PLAYBOOKS and pb["id"] not in ("PB-06", "PB-01"):
            if self.w.netops is None:
                return {"passed": False, "detail": "no emulated network attached (orca.sim.netops.attach)"}
            return _net.clone_test(self.w.netops.net, pb["id"], targets, params, self.w.netops.sim)
        if pb["id"] == "PB-06" and self.w.netops is not None:
            for site in targets:      # measured clean-path checks (jamming, compromised mgmt, feeder, ...)
                r = _net.check_path_clean(site, params.get("path"), self.w.netops.net, self.w.netops.sim,
                                          route=self.w.routes.get(site, {}).get(params.get("path")))
                if not r["clean"]:
                    bad = [x["check"] for x in r["checks"] if not x["ok"]]
                    return {"passed": False, "detail": f"{site}: path {params.get('path')} not clean: {bad}"}
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
        ops = self.w.netops
        seen = len(ops.records) if ops is not None else 0
        for pct in STAGES:
            ok = self.w.health(targets, pb["id"], params, pct) if self.w.health else True
            stages.append({"pct": pct, "healthy": bool(ok)})
            if not ok:
                net = ops.records[seen:] if ops is not None else []
                return {"ok": False, "stages": stages, "network": net,
                        "detail": f"health check failed at {pct} %, rolled back"}
        if ops is not None:
            network = ops.records[seen:]      # diffs per stage + verify (re-scan, re-attack) -> audit
        if pb["id"] == "PB-01":
            self.w.disabled_accounts.update(targets)
        elif pb["id"] == "PB-06":
            for site in targets:
                self.w.active_path[site] = params["path"]
        elif pb["id"] == "PB-10":
            to = sorted({d for s in targets for d in DEPENDANTS.get(s, [])})
            self.w.bus.append({"at": self.w.now, "sender": caller, "to": to, "kind": "warning",
                               "payload": {"sites": targets, "message": params["message"]}})
        out = {"ok": True, "stages": stages, "detail": "rolled out 5/25/100 %"}
        if ops is not None:
            out["network"] = network
        return out
