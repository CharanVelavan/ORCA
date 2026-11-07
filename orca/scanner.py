"""Posture scanner: checks emulated device configs (netconfig/) against netconfig/baseline.yaml.

Each finding names the asset, its owner role, the severity, the evidence (config path and value)
and the playbook that fixes it. A re-scan after a patch proves the fix. Read only: the scanner never
changes a config and never touches a real system.

    python -m orca.scanner              # scan the default (committed) posture
    python -m orca.scanner --json
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from orca.sim.netstate import NetState, version_tuple
from orca.sim.topology import SITES

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# check id -> (title, severity, playbook)
CHECKS = {
    "SCN-VPN-EXPOSED": ("Remote-access VPN reachable from the whole internet", "critical", "PB-12"),
    "SCN-MGMT-EXPOSED": ("Management interface reachable outside the management VLAN", "critical", "PB-12"),
    "SCN-DEFAULT-CRED": ("Account still uses factory-default credentials", "critical", "PB-11"),
    "SCN-NO-MFA": ("MFA not enforced for management access", "high", "PB-11"),
    "SCN-STALE-CRED": ("Credential older than the rotation limit", "medium", "PB-11"),
    "SCN-FEEDER-CLEAR": ("Feeder link not encrypted or not authenticated", "high", "PB-13"),
    "SCN-FW-OUTDATED": ("Firmware below the minimum baseline version", "high", "PB-14"),
    "SCN-FW-UNSIGNED": ("Device accepts unsigned firmware or commands", "high", "PB-14"),
    "SCN-FOREIGN-PATH": ("Failover path through a gateway outside India (Authz Rule 60(1)(b))", "high", "PB-06"),
    "SCN-NO-BATTERY-SAVING": ("Critical site has no battery-saving profile", "low", "PB-15"),
}


@dataclass
class Finding:
    id: str
    check: str
    title: str
    severity: str
    asset: str
    owner: str
    evidence: str
    playbook: str

    def to_dict(self) -> dict:
        return asdict(self)


def _f(check: str, cfg: dict, evidence: str, suffix: str = "") -> Finding:
    title, sev, pb = CHECKS[check]
    asset = cfg["id"]
    return Finding(f"{check}:{asset}{(':' + suffix) if suffix else ''}", check, title, sev, asset,
                   cfg.get("owner", "unknown"), evidence, pb)


def scan(net: NetState | None = None, devices: list[str] | None = None) -> list[Finding]:
    net = net or NetState.load()
    b = net.baseline
    out: list[Finding] = []
    gw_country = {c["id"]: c.get("country") for c in net.by_kind("gateway")}
    for cfg in net.configs.values():
        if devices is not None and cfg["id"] not in devices:
            continue
        if cfg.get("forbidden"):
            continue            # GW-XX is not ours to scan; its use is flagged on the sites that reference it
        kind = cfg.get("kind")
        vpn = cfg.get("vpn") or {}
        if vpn.get("enabled") and vpn.get("exposure") not in b["allowed_vpn_exposure"]:
            out.append(_f("SCN-VPN-EXPOSED", cfg, f"vpn.exposure={vpn.get('exposure')}, "
                                                  f"allowed_sources={vpn.get('allowed_sources')}"))
        mi = cfg.get("mgmt_interface") or {}
        if mi and mi.get("exposure") not in b["allowed_mgmt_exposure"]:
            out.append(_f("SCN-MGMT-EXPOSED", cfg, f"mgmt_interface.exposure={mi.get('exposure')}"))
        auth = cfg.get("auth") or {}
        accounts = [a for a in cfg.get("accounts") or [] if a.get("enabled", True)]
        for a in accounts:
            if a.get("default_password"):
                out.append(_f("SCN-DEFAULT-CRED", cfg, f"accounts[{a['user']}].default_password=true", a["user"]))
        if b.get("require_mfa") and accounts:
            no_mfa = [a["user"] for a in accounts if not a.get("mfa")]
            if not auth.get("mfa_required") or no_mfa:
                out.append(_f("SCN-NO-MFA", cfg, f"auth.mfa_required={auth.get('mfa_required')}, "
                                                 f"accounts without MFA={no_mfa}"))
        stale = [a["user"] for a in accounts if a.get("credential_age_days", 0) > b["max_credential_age_days"]]
        if stale:
            out.append(_f("SCN-STALE-CRED", cfg, f"credential_age_days > {b['max_credential_age_days']} for {stale}"))
        fl = cfg.get("feeder_link")
        if fl is not None and (fl.get("encryption") not in b["feeder_link_encryption"] or not fl.get("authentication")):
            out.append(_f("SCN-FEEDER-CLEAR", cfg, f"feeder_link.encryption={fl.get('encryption')}, "
                                                   f"authentication={fl.get('authentication')}"))
        fw = cfg.get("firmware") or {}
        minimum = b["min_firmware"].get(kind)
        if fw and minimum and version_tuple(fw.get("version", "0")) < version_tuple(minimum):
            out.append(_f("SCN-FW-OUTDATED", cfg, f"firmware.version={fw.get('version')} < {minimum}"))
        if fw and b.get("require_signed_firmware") and (not fw.get("signed") or fw.get("accept_unsigned_commands")):
            out.append(_f("SCN-FW-UNSIGNED", cfg, f"firmware.signed={fw.get('signed')}, "
                                                  f"accept_unsigned_commands={fw.get('accept_unsigned_commands')}"))
        if kind == "site":
            for p in (cfg.get("backhaul") or {}).get("paths", []):
                c = gw_country.get(p.get("gateway"))
                if p.get("failover_allowed") and c not in b["allowed_gateway_countries"]:
                    out.append(_f("SCN-FOREIGN-PATH", cfg, f"backhaul.paths[{p['id']}].gateway={p['gateway']} "
                                                           f"(country {c}), failover_allowed=true", p["id"]))
            deps = set(SITES.get(cfg["id"], {}).get("dependants", []))
            bs = ((cfg.get("power") or {}).get("battery_saving") or {})
            if deps & set(b["battery_saving_required_for"]) and not bs.get("configured"):
                out.append(_f("SCN-NO-BATTERY-SAVING", cfg, f"power.battery_saving.configured=false; dependants={sorted(deps)}"))
    out.sort(key=lambda f: (SEVERITY_ORDER[f.severity], f.asset, f.check))
    return out


def summary(findings: list[Finding]) -> dict:
    s = {k: 0 for k in SEVERITY_ORDER}
    for f in findings:
        s[f.severity] += 1
    return {"total": len(findings), **s}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="ORCA-NTN posture scanner (emulated configs only)")
    ap.add_argument("--dir", default=None, help="netconfig directory (default: committed netconfig/)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    net = NetState.load(a.dir) if a.dir else NetState.load()
    fs = scan(net)
    if a.json:
        print(json.dumps({"summary": summary(fs), "findings": [f.to_dict() for f in fs]}, indent=2))
        return
    for f in fs:
        print(f"{f.severity:8} {f.asset:12} {f.owner:18} {f.playbook}  {f.title}  [{f.evidence}]")
    print(summary(fs))


if __name__ == "__main__":
    main()
