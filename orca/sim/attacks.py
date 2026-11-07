"""Re-attack tests: replay an *emulated* attack path against the emulated configs.

No exploit code. Each test is a chain of preconditions read from netconfig (an attack graph); the
attack "succeeds" only if every step's precondition holds. After a patch, the re-attack must fail,
and the result names the step that now blocks it.

Tests:
  ka_sat_chain        misconfigured VPN -> login -> management interface -> wipe terminals (KA-SAT 2022 pattern)
  default_cred_login  log in with factory-default credentials on any device
  feeder_intercept    read or inject on an unencrypted feeder link ("Don't Look Up", CCS 2025 pattern)
  firmware_exploit    known flaw in firmware below baseline, or unsigned commands accepted
  foreign_failover    traffic can fail over through a gateway outside India
"""
from __future__ import annotations

from orca.sim.netstate import NetState, version_tuple


def _result(name: str, target: str, chain: list[dict]) -> dict:
    ok = all(s["holds"] for s in chain)
    blocked = next((s for s in chain if not s["holds"]), None)
    return {"attack": name, "target": target, "succeeded": ok, "chain": chain,
            "blocked_at": blocked["step"] if blocked else None,
            "blocked_by": blocked["why"] if blocked else None}


def ka_sat_chain(net: NetState, account: str | None = None) -> dict:
    m = net.get("SAT-MGMT")
    vpn, auth = m.get("vpn") or {}, m.get("auth") or {}
    acc = [a for a in m.get("accounts", []) if a.get("enabled", True) and (account is None or a["user"] == account)]
    reachable = bool(vpn.get("enabled")) and vpn.get("exposure") == "internet"
    weak = [a["user"] for a in acc if a.get("default_password") or
            (not a.get("mfa") and not auth.get("mfa_required") and
             a.get("credential_age_days", 0) > net.baseline["max_credential_age_days"])]
    mi = (m.get("mgmt_interface") or {}).get("exposure")
    terms = [t for t in net.by_kind("terminal")
             if (t.get("firmware") or {}).get("accept_unsigned_commands")
             or version_tuple(t["firmware"]["version"]) < version_tuple(net.baseline["min_firmware"]["terminal"])]
    chain = [
        {"step": "reach VPN from the internet", "holds": reachable,
         "why": f"vpn.exposure={vpn.get('exposure')}"},
        {"step": "log in with a weak or stolen credential", "holds": bool(weak),
         "why": f"weak accounts={weak}" if weak else "no account without MFA and with a stale or default credential"},
        {"step": "reach the management interface", "holds": mi in ("internet", "vpn"),
         "why": f"mgmt_interface.exposure={mi}"},
        {"step": "send destructive commands that terminals accept", "holds": bool(terms) or
         any(not (t.get("firmware") or {}).get("signed") for t in net.by_kind("terminal")),
         "why": f"vulnerable terminals={[t['id'] for t in terms]}"},
    ]
    return _result("ka_sat_chain", account or "SAT-MGMT", chain)


def default_cred_login(net: NetState, device: str) -> dict:
    cfg = net.get(device)
    users = [a["user"] for a in cfg.get("accounts", []) if a.get("enabled", True) and a.get("default_password")]
    return _result("default_cred_login", device, [
        {"step": "device offers a login", "holds": bool(cfg.get("accounts")), "why": "accounts configured"},
        {"step": "a factory-default credential works", "holds": bool(users), "why": f"default accounts={users}"},
    ])


def feeder_intercept(net: NetState, gateway: str) -> dict:
    fl = net.get(gateway).get("feeder_link") or {}
    return _result("feeder_intercept", gateway, [
        {"step": "receive the feeder downlink with a low-cost dish", "holds": True, "why": "broadcast by physics"},
        {"step": "traffic is readable or injectable", "holds": fl.get("encryption") in (None, "none", "unknown")
         or not fl.get("authentication"), "why": f"encryption={fl.get('encryption')}, auth={fl.get('authentication')}"},
    ])


def firmware_exploit(net: NetState, device: str) -> dict:
    cfg = net.get(device)
    fw = cfg.get("firmware") or {}
    minimum = net.baseline["min_firmware"].get(cfg.get("kind"), "0")
    old = version_tuple(fw.get("version", "0")) < version_tuple(minimum)
    return _result("firmware_exploit", device, [
        {"step": "reach the device management plane", "holds": True, "why": "assume insider or prior foothold"},
        {"step": "firmware has a known flaw or accepts unsigned code", "holds": old or bool(fw.get("accept_unsigned_commands"))
         or not fw.get("signed", True), "why": f"version={fw.get('version')} (min {minimum}), signed={fw.get('signed')}, "
                                               f"accept_unsigned={fw.get('accept_unsigned_commands')}"},
    ])


def foreign_failover(net: NetState, site: str) -> dict:
    cfg = net.get(site)
    countries = {c["id"]: c.get("country") for c in net.by_kind("gateway")}
    bad = [p["id"] for p in cfg.get("backhaul", {}).get("paths", [])
           if p.get("failover_allowed") and countries.get(p.get("gateway")) != "IN"]
    return _result("foreign_failover", site, [
        {"step": "force failover (jam or cut the primary)", "holds": True, "why": "attacker can degrade the primary"},
        {"step": "a path through a gateway outside India is allowed", "holds": bool(bad), "why": f"paths={bad}"},
    ])


# Which re-attack proves which playbook (and for which targets).
def reattacks_for(net: NetState, playbook: str, targets: list[str]) -> list[dict]:
    if playbook in ("PB-11",):
        return [ka_sat_chain(net)] + [default_cred_login(net, t) for t in targets if t in net.configs]
    if playbook == "PB-01":
        return [ka_sat_chain(net, a) for a in targets]
    if playbook == "PB-12":
        return [ka_sat_chain(net)]
    if playbook == "PB-13":
        return [feeder_intercept(net, t) for t in targets]
    if playbook == "PB-14":
        return [firmware_exploit(net, t) for t in targets]
    if playbook in ("PB-06", "PB-16"):
        return [foreign_failover(net, t) for t in targets if t in net.configs]
    return []
