"""Patch and heal playbooks on the emulated network: apply -> diff -> verify (re-scan + re-attack) -> rollback.

Clean functions the lead calls from orca/remediation.py (which keeps every guard: autonomy mode,
approval token, owner, clone test, hard limits, staged rollout, kill switch):

    net = NetState.load(); ops = NetOps(net, sim)
    p = apply_playbook(net, "PB-12", ["SAT-MGMT"], stage_pct=100, sim=sim)   # -> Patch (diff, changes)
    v = verify(net, p, sim)       # {"ok", "closed", "remaining", "reattack": [...]}
    rollback(net, p, sim)         # revert diff
    attach(world, net, sim)       # world.health = ops.health (applies stage by stage, rolls back on failure)

Staging: a stage of ``pct`` % applies the playbook to ceil(n * pct / 100) of the sorted targets
(PB-14 firmware "in waves"); a single target is applied at the first stage and re-checked at each.
Nothing here touches a real device: changes are edits of in-memory YAML plus simulator state.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

from orca.scanner import CHECKS, scan
from orca.sim import attacks
from orca.sim.netstate import NetState, unified
from orca.sim.topology import INDIAN_GATEWAYS

# playbook -> (device kind its targets name, scanner checks it must close)
NET_PLAYBOOKS = {
    "PB-01": ("mgmt_account", []),
    "PB-06": ("site", ["SCN-FOREIGN-PATH"]),
    "PB-11": ("device", ["SCN-DEFAULT-CRED", "SCN-NO-MFA", "SCN-STALE-CRED"]),
    "PB-12": ("device", ["SCN-VPN-EXPOSED", "SCN-MGMT-EXPOSED"]),
    "PB-13": ("gateway", ["SCN-FEEDER-CLEAR"]),
    "PB-14": ("device", ["SCN-FW-OUTDATED", "SCN-FW-UNSIGNED"]),
    "PB-15": ("site", ["SCN-NO-BATTERY-SAVING"]),
    "PB-16": ("site", []),
    "PB-17": ("site", []),
}
CONTAINS_MGMT = {"PB-01", "PB-11", "PB-12"}


class PatchRefused(Exception):
    """A precondition failed; nothing was changed."""


@dataclass
class Patch:
    playbook: str
    targets: list[str]
    stage_pct: int
    applied: list[str]
    changes: list[dict]                       # [{device, diff}]
    params: dict = field(default_factory=dict)
    detail: str = ""
    snapshot: dict = field(default_factory=dict, repr=False)   # device -> config before (for rollback)
    sim_before: dict = field(default_factory=dict, repr=False)

    @property
    def diff(self) -> str:
        return "".join(c["diff"] for c in self.changes)

    def to_dict(self) -> dict:
        return {"playbook": self.playbook, "targets": self.targets, "stage_pct": self.stage_pct,
                "applied": self.applied, "params": self.params, "detail": self.detail,
                "devices_changed": [c["device"] for c in self.changes], "diff": self.diff}


# ---------------------------------------------------------------------------- clean-path check (PB-06)
def check_path_clean(site: str, path: str, net: NetState | None = None, sim=None, route: dict | None = None) -> dict:
    """Is a candidate backup path clean? Every check must pass; a 'failed' integrity is never upgraded.

    Checks: path exists; gateway in India (Authz Rule 60(1)(b)); gateway not marked forbidden in netconfig;
    not jammed; no equipment fault; gateway up; not managed by a compromised, uncontained management
    network; feeder link of a satellite path is encrypted; integrity probe not failed.
    """
    rep = sim.path_report(site, path) if sim is not None else {"exists": route is not None}
    if route is None and sim is not None:
        route = sim.routes.get(site, {}).get(path)
    if route is None and net is not None:
        p = next((p for p in net.get(site).get("backhaul", {}).get("paths", []) if p["id"] == path), None)
        route = {"gateway": p["gateway"], "kind": p["kind"], "integrity": "unverified"} if p else None
    checks = []

    def c(name, ok, why):
        checks.append({"check": name, "ok": bool(ok), "why": why})

    c("path exists", route is not None, f"{site} path {path}")
    if route is None:
        return {"site": site, "path": path, "clean": False, "integrity": "failed", "checks": checks}
    gw = route.get("gateway")
    c("gateway in India (Authz Rule 60(1)(b))", gw in INDIAN_GATEWAYS, f"gateway={gw}")
    if net is not None and gw in net.configs:
        c("gateway not forbidden", not net.get(gw).get("forbidden"), f"{gw}.forbidden={net.get(gw).get('forbidden')}")
    if sim is not None and rep.get("exists"):
        c("not jammed", not rep["jammed"], "noise floor normal" if not rep["jammed"] else "noise floor raised (J/N)")
        c("no equipment fault", not rep["equipment_fault"], "")
        c("gateway up", not rep["gateway_down"], "")
        c("management plane not compromised", not rep["shares_compromised_mgmt"],
          "same operator management network is under an uncontained intrusion" if rep["shares_compromised_mgmt"] else "")
    if net is not None and route.get("kind") == "satellite" and gw in net.configs:
        fl = net.get(gw).get("feeder_link") or {}
        c("feeder link encrypted", fl.get("encryption") in net.baseline["feeder_link_encryption"],
          f"{gw}.feeder_link.encryption={fl.get('encryption')}")
    c("integrity probe not failed", route.get("integrity") != "failed", f"integrity={route.get('integrity')}")
    clean = all(x["ok"] for x in checks)
    integrity = "failed" if route.get("integrity") == "failed" or not clean else "verified"
    return {"site": site, "path": path, "gateway": gw, "clean": clean, "integrity": integrity, "checks": checks}


def verify_routes(world, sim=None, net: NetState | None = None) -> dict:
    """Run the clean-path check on every offered route and write the measured integrity into world.routes."""
    out = {}
    for site, paths in (world.routes or {}).items():
        for path, r in paths.items():
            res = check_path_clean(site, path, net, sim, route=r)
            r["integrity"] = res["integrity"]
            r["checks"] = res["checks"]
            out[f"{site}/{path}"] = res
    return out


# ---------------------------------------------------------------------------- apply / verify / rollback
def _devices(net: NetState, playbook: str, targets: list[str]) -> list[str]:
    if playbook == "PB-01":
        return ["SAT-MGMT"]
    return [t for t in targets]


def _stage_subset(targets: list[str], pct: int) -> list[str]:
    ts = sorted(targets)
    return ts[:max(1, math.ceil(len(ts) * pct / 100))] if ts else []


def _mutate(net: NetState, playbook: str, target: str, params: dict, sim) -> None:
    if playbook == "PB-01":
        m = net.get("SAT-MGMT")
        acc = next((a for a in m.get("accounts", []) if a["user"] == target), None)
        if acc is None:
            raise PatchRefused(f"no management account {target}")
        acc["enabled"] = False
        acc["credential_ref"] = f"revoked:{params.get('ticket', 'PB-01')}"
        return
    cfg = net.get(target)
    if playbook == "PB-11":
        if not cfg.get("accounts"):
            raise PatchRefused(f"{target} has no accounts")
        cfg.setdefault("auth", {})["mfa_required"] = True
        for a in cfg["accounts"]:
            if not a.get("enabled", True):
                continue
            a["mfa"] = True
            a["default_password"] = False
            a["credential_age_days"] = 0
            a["credential_ref"] = f"vault:emulated/{target}/{a['user']}/rotated-{params.get('ticket', 'PB-11')}"
    elif playbook == "PB-12":
        if cfg.get("vpn"):
            cfg["vpn"]["exposure"] = "restricted"
            cfg["vpn"]["allowed_sources"] = ["noc-jump-host (emulated 10.20.0.10/32)"]
        if cfg.get("mgmt_interface"):
            cfg["mgmt_interface"]["exposure"] = "jump_host_only"
    elif playbook == "PB-13":
        if cfg.get("kind") != "gateway" or cfg.get("forbidden"):
            raise PatchRefused(f"{target} is not one of our gateways")
        fl = cfg.setdefault("feeder_link", {})
        fl["encryption"] = net.baseline["feeder_link_encryption"][0]
        fl["authentication"] = True
        fl["key_ref"] = f"hsm:emulated/feeder/{target}/{params.get('ticket', 'PB-13')}"
    elif playbook == "PB-14":
        kind = cfg.get("kind")
        tgt = net.baseline.get("firmware_target", {}).get(kind) or net.baseline["min_firmware"].get(kind)
        if not tgt:
            raise PatchRefused(f"no firmware target for {kind}")
        cfg["firmware"]["version"] = params.get("version", tgt)
        cfg["firmware"]["signed"] = True
        if "accept_unsigned_commands" in cfg["firmware"]:
            cfg["firmware"]["accept_unsigned_commands"] = False
    elif playbook == "PB-15":
        bs = cfg.setdefault("power", {}).setdefault("battery_saving", {})
        bs["configured"] = True
        bs["enabled"] = bool(params.get("enable", True))
        bs["shed"] = params.get("shed", ["general"])
        if sim is not None and target in sim.state:
            sim.state[target].battery_saving = bs["enabled"]
    elif playbook in ("PB-06", "PB-16"):
        path = params.get("path")
        res = check_path_clean(target, path, net, sim, route=(sim.routes.get(target, {}).get(path) if sim else None))
        if not res["clean"]:
            bad = [x["check"] + (f" ({x['why']})" if x["why"] else "") for x in res["checks"] if not x["ok"]]
            raise PatchRefused(f"{target} path {path} is not clean: {', '.join(bad)}")
        bh = cfg.setdefault("backhaul", {})
        paths = bh.setdefault("paths", [])
        if not any(p["id"] == path for p in paths) and sim is not None:
            r = sim.routes[target][path]
            paths.append({"id": path, "kind": r.get("kind", "satellite"), "gateway": r["gateway"], "failover_allowed": True})
        countries = {c["id"]: c.get("country") for c in net.by_kind("gateway")}
        for p in paths:      # prune forbidden failover paths (Authz Rule 60(1)(b))
            if countries.get(p.get("gateway")) != "IN":
                p["failover_allowed"] = False
        if playbook == "PB-06":
            bh["active_path"] = path
            if sim is not None and target in sim.state:
                sim.failover(target, path)
        else:
            bh["prestaged_path"] = path
            if sim is not None and target in sim.state:
                sim.state[target].prestaged = path
    elif playbook == "PB-17":
        mon = cfg.setdefault("monitoring", {})
        mon["reattack_watch"] = True
        mon["watch_minutes"] = int(params.get("minutes", 60))
        if sim is not None and target in sim.state:
            sim.state[target].reattack_watch_until = sim.t + mon["watch_minutes"]
    else:
        raise PatchRefused(f"{playbook} has no network action")


def apply_playbook(net: NetState, playbook: str, targets: list[str], stage_pct: int = 100,
                   params: dict | None = None, sim=None, only: list[str] | None = None) -> Patch:
    """Apply one stage of a playbook. ``only`` limits it to these targets (incremental staging)."""
    if playbook not in NET_PLAYBOOKS:
        raise PatchRefused(f"{playbook} has no network action")
    params = dict(params or {})
    subset = only if only is not None else _stage_subset(targets, stage_pct)
    devices = sorted(set(_devices(net, playbook, subset)))
    for d in devices:
        net.get(d)                                       # KeyError for unknown devices, before any change
    snap = net.snapshot(devices)
    sim_before = {"mgmt_contained": getattr(sim, "mgmt_contained", None),
                  "state": {t: vars(sim.state[t]).copy() for t in subset if sim is not None and t in sim.state}}
    before = {d: net.text(d) for d in devices}
    try:
        for t in subset:
            _mutate(net, playbook, t, params, sim)
    except Exception:
        net.restore(snap)
        _restore_sim(sim, sim_before)
        raise
    changes = [{"device": d, "diff": unified(d, before[d], net.text(d))} for d in devices]
    changes = [c for c in changes if c["diff"]]
    if playbook in CONTAINS_MGMT and sim is not None and stage_pct >= 100:
        sim.mgmt_contained = True
    p = Patch(playbook, list(targets), stage_pct, list(subset), changes, params,
              f"{playbook} applied to {subset} at stage {stage_pct} %", snap, sim_before)
    net.log.append({"playbook": playbook, "stage_pct": stage_pct, "applied": list(subset),
                    "devices": [c["device"] for c in changes], "diff": p.diff})
    return p


def _restore_sim(sim, before: dict) -> None:
    if sim is None or not before:
        return
    if before.get("mgmt_contained") is not None:
        sim.mgmt_contained = before["mgmt_contained"]
    for site, st in before.get("state", {}).items():
        old_path = sim.state[site].active_path
        for k, v in st.items():
            setattr(sim.state[site], k, v)
        if st.get("active_path") != old_path:
            sim.failover(site, st["active_path"])


def rollback(net: NetState, patch: Patch, sim=None) -> str:
    """Revert a patch. Returns the diff of the revert (the patch, reversed)."""
    d = net.restore(patch.snapshot)
    _restore_sim(sim, patch.sim_before)
    net.log.append({"playbook": patch.playbook, "rollback": True, "devices": list(patch.snapshot), "diff": d})
    return d


def verify(net: NetState, patch: Patch, sim=None) -> dict:
    """Re-scan the patched devices and re-run the matching emulated attacks. ok = fixed and attack fails."""
    pb = patch.playbook
    devices = sorted(set(_devices(net, pb, patch.targets)))
    checks = NET_PLAYBOOKS[pb][1]
    before_ns = NetState(patch.snapshot | {d: c for d, c in net.configs.items() if d not in patch.snapshot}, net.baseline)
    before = {f.id for f in scan(before_ns, devices) if f.check in checks}
    after = {f.id for f in scan(net, devices) if f.check in checks}
    re = attacks.reattacks_for(net, pb, patch.targets)
    extra = []
    if pb in ("PB-06", "PB-16"):
        for t in patch.targets:
            path = patch.params.get("path")
            r = check_path_clean(t, path, net, sim)
            extra.append({"check": f"{t} path {path} clean", "ok": r["clean"]})
            if pb == "PB-06" and sim is not None and t in sim.state:
                extra.append({"check": f"{t} active path is {path}", "ok": sim.state[t].active_path == path})
    if pb == "PB-15" and sim is not None:
        extra += [{"check": f"{t} battery-saving active", "ok": sim.state[t].battery_saving}
                  for t in patch.targets if t in sim.state]
    ok = not after and not any(r["succeeded"] for r in re) and all(x["ok"] for x in extra)
    return {"ok": ok, "playbook": pb, "closed": sorted(before - after), "remaining": sorted(after),
            "reattack": [{k: r[k] for k in ("attack", "target", "succeeded", "blocked_at", "blocked_by")} for r in re],
            "checks": extra}


# ---------------------------------------------------------------------------- remediation hook
class NetOps:
    """Simulator hook for ``World.health``: applies each stage, checks health, rolls back on failure.

    ``health(targets, playbook, params, stage_pct)`` is called by Remediation._rollout after every stage
    (5, 25, 100 %). For a network playbook it applies the stage's new targets, checks the emulated
    service, and at 100 % runs ``verify`` (re-scan + re-attack). Any failure rolls back everything this
    run applied and returns False, so the lead's staged rollout reports "rolled back".
    ``params["simulate_failure_at"] = <pct>`` forces a failed stage (rollback demo).
    """

    def __init__(self, net: NetState | None = None, sim=None):
        self.net = net or NetState.load()
        self.sim = sim
        self.runs: dict[str, dict] = {}
        self.records: list[dict] = []        # what happened, for the audit log (lead logs these)

    def _key(self, targets, playbook, params) -> str:
        return json.dumps([playbook, sorted(targets), {k: v for k, v in (params or {}).items()}], sort_keys=True)

    def health(self, targets, playbook, params, stage_pct) -> bool:
        params = params or {}
        if playbook not in NET_PLAYBOOKS:
            return True
        key = self._key(targets, playbook, params)
        run = self.runs.get(key)
        if run is None or stage_pct <= 5 or run.get("done"):
            run = self.runs[key] = {"patches": [], "applied": [], "done": False}
        want = _stage_subset(targets, stage_pct)
        new = [t for t in want if t not in run["applied"]]
        try:
            if new:
                p = apply_playbook(self.net, playbook, targets, stage_pct, params, self.sim, only=new)
                run["patches"].append(p)
                run["applied"] += new
                self.records.append({"event": "stage_applied", **p.to_dict()})
            if params.get("simulate_failure_at") == stage_pct:
                raise PatchRefused(f"emulated health check failed at {stage_pct} %")
            if stage_pct >= 100:
                if playbook in CONTAINS_MGMT and self.sim is not None:
                    self.sim.mgmt_contained = True
                v = verify(self.net, _merge(run["patches"], playbook, targets, params), self.sim)
                self.records.append({"event": "verified", **v})
                run["done"] = True
                if not v["ok"]:
                    raise PatchRefused(f"verification failed: remaining={v['remaining']}, "
                                       f"reattack={[r for r in v['reattack'] if r['succeeded']]}")
            return True
        except (PatchRefused, KeyError) as e:
            reverts = [rollback(self.net, p, self.sim) for p in reversed(run["patches"])]
            self.records.append({"event": "rolled_back", "playbook": playbook, "targets": targets,
                                 "stage_pct": stage_pct, "reason": str(e), "revert_diff": "".join(reverts)})
            run["done"] = True
            return False


def _merge(patches: list[Patch], playbook, targets, params) -> Patch:
    snap: dict = {}
    for p in patches:
        for d, c in p.snapshot.items():
            snap.setdefault(d, c)
    return Patch(playbook, list(targets), 100, [t for p in patches for t in p.applied],
                 [c for p in patches for c in p.changes], params, "", snap)


def clone_test(net: NetState, playbook: str, targets: list[str], params: dict | None = None, sim=None) -> dict:
    """Apply + verify on a clone of the configs and of the simulator. Nothing real (or live) changes."""
    import copy
    if playbook not in NET_PLAYBOOKS:
        return {"passed": True, "detail": "no network action", "diff": ""}
    c_net, c_sim = net.clone(), (copy.deepcopy(sim) if sim is not None else None)
    try:
        p = apply_playbook(c_net, playbook, targets, 100, params, c_sim)
    except (PatchRefused, KeyError) as e:
        return {"passed": False, "detail": f"clone apply refused: {e}", "diff": ""}
    v = verify(c_net, p, c_sim)
    bad = [r for r in v["reattack"] if r["succeeded"]]
    detail = ("re-scan clean and re-attack blocked on the clone" if v["ok"] else
              f"remaining findings {v['remaining']}; re-attack succeeded {[(r['attack'], r['target']) for r in bad]}; "
              f"failed checks {[x['check'] for x in v['checks'] if not x['ok']]}")
    return {"passed": v["ok"], "detail": detail, "diff": p.diff, "verify": v}


def attach(world, net: NetState | None = None, sim=None) -> NetOps:
    """Wire the emulated network into a World: health hook + handle for the dashboard/runner."""
    ops = NetOps(net, sim)
    world.health = ops.health
    world.netops = ops
    return ops


def playbook_checks(playbook: str) -> list[dict]:
    return [{"check": c, "title": CHECKS[c][0]} for c in NET_PLAYBOOKS.get(playbook, ("", []))[1]]
