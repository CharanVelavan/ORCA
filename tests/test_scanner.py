"""Posture scanner, netconfig diffs, patch playbooks PB-11..15 with re-scan and re-attack proof."""
import re
from pathlib import Path

import pytest
import yaml

from orca.remediation import catalogue
from orca.scanner import CHECKS, scan, summary
from orca.sim import attacks, netops
from orca.sim.netstate import NETCONFIG_DIR, NetState

PATCHES = [
    ("PB-11", ["SAT-MGMT"], {"SCN-DEFAULT-CRED", "SCN-NO-MFA", "SCN-STALE-CRED"}),
    ("PB-12", ["SAT-MGMT"], {"SCN-VPN-EXPOSED", "SCN-MGMT-EXPOSED"}),
    ("PB-13", ["GW-IN-1"], {"SCN-FEEDER-CLEAR"}),
    ("PB-14", ["TERM-CHN-01", "TERM-CHN-02", "TERM-CHN-05"], {"SCN-FW-OUTDATED", "SCN-FW-UNSIGNED"}),
    ("PB-15", ["CHN-01", "CHN-05"], {"SCN-NO-BATTERY-SAVING"}),
]


def test_default_posture_findings():
    fs = scan()
    assert summary(fs) == {"total": 13, "critical": 3, "high": 7, "medium": 1, "low": 2}
    ids = {f.id for f in fs}
    assert {"SCN-VPN-EXPOSED:SAT-MGMT", "SCN-MGMT-EXPOSED:SAT-MGMT", "SCN-DEFAULT-CRED:SAT-MGMT:admin",
            "SCN-FEEDER-CLEAR:GW-IN-1", "SCN-FOREIGN-PATH:CHN-03:C", "SCN-FW-UNSIGNED:TERM-CHN-02"} <= ids
    for f in fs:
        assert f.owner in ("satellite_operator", "mobile_operator") and f.playbook == CHECKS[f.check][2]
        assert f.evidence
    assert not any(f.asset == "GW-XX" for f in fs)            # not ours; flagged where a site references it


def test_every_finding_playbook_is_in_the_catalogue_with_matching_owner():
    cat = catalogue()
    for f in scan():
        pb = cat[f.playbook]
        assert pb["executable"] and pb["owner"] == f.owner, f.id


def test_scanner_is_read_only():
    before = {p.name: p.read_text() for p in NETCONFIG_DIR.glob("*.yaml")}
    scan()
    assert before == {p.name: p.read_text() for p in NETCONFIG_DIR.glob("*.yaml")}


@pytest.mark.parametrize("pb,targets,checks", PATCHES)
def test_patch_closes_findings_and_reattack_fails(pb, targets, checks):
    net = NetState.load()
    open_before = {f.id for f in scan(net) if f.check in checks}
    assert open_before
    reattack_before = attacks.reattacks_for(net, pb, targets)
    p = netops.apply_playbook(net, pb, targets)
    assert p.diff.startswith("--- a/netconfig/") and "+++ b/netconfig/" in p.diff
    v = netops.verify(net, p)
    assert v["ok"] and set(v["closed"]) == open_before and not v["remaining"]
    if reattack_before:
        assert any(r["succeeded"] for r in reattack_before)
        assert v["reattack"] and not any(r["succeeded"] for r in v["reattack"])
        assert all(r["blocked_at"] for r in v["reattack"])


@pytest.mark.parametrize("pb,targets,checks", PATCHES)
def test_rollback_reverts_exactly(pb, targets, checks):
    net = NetState.load()
    before = {d: net.text(d) for d in net.configs}
    p = netops.apply_playbook(net, pb, targets)
    revert = netops.rollback(net, p)
    assert revert and {d: net.text(d) for d in net.configs} == before
    assert {f.id for f in scan(net) if f.check in checks}


def test_ka_sat_chain_needs_every_step():
    net = NetState.load()
    r = attacks.ka_sat_chain(net)
    assert r["succeeded"] and all(s["holds"] for s in r["chain"])
    netops.apply_playbook(net, "PB-01", ["admin"])              # contain one account: still weak noc-vendor-7
    assert attacks.ka_sat_chain(net)["succeeded"]
    netops.apply_playbook(net, "PB-01", ["noc-vendor-7", "telemetry-srv"])
    r = attacks.ka_sat_chain(net)
    assert not r["succeeded"] and r["blocked_at"] == "log in with a weak or stolen credential"


def test_pb14_rolls_out_in_waves():
    net = NetState.load()
    targets = ["TERM-CHN-01", "TERM-CHN-02", "TERM-CHN-05"]
    seen = []
    for pct in (5, 25, 100):
        p = netops.apply_playbook(net, "PB-14", targets, stage_pct=pct,
                                  only=[t for t in netops._stage_subset(targets, pct) if t not in seen])
        seen += p.applied
        assert len(seen) == {5: 1, 25: 1, 100: 3}[pct]
    assert not [f for f in scan(net) if f.check.startswith("SCN-FW")]


def test_patch_refusals_change_nothing():
    net = NetState.load()
    before = {d: net.text(d) for d in net.configs}
    with pytest.raises(netops.PatchRefused):
        netops.apply_playbook(net, "PB-13", ["GW-XX"])              # never patch (or use) the foreign gateway
    with pytest.raises(KeyError):
        netops.apply_playbook(net, "PB-12", ["NO-SUCH-DEVICE"])
    with pytest.raises(netops.PatchRefused):
        netops.apply_playbook(net, "PB-03", ["SAT-MGMT"])           # no network action defined
    assert {d: net.text(d) for d in net.configs} == before


def test_all_patches_then_full_rescan_is_clean():
    net = NetState.load()
    for pb, targets, _ in PATCHES:
        netops.apply_playbook(net, pb, targets)
    netops.apply_playbook(net, "PB-06", ["CHN-03"], params={"path": "B"})
    assert scan(net) == []
    assert not attacks.ka_sat_chain(net)["succeeded"]


def test_netconfig_files_hold_no_secrets_and_are_marked_emulated():
    for p in NETCONFIG_DIR.glob("*.yaml"):
        text = p.read_text()
        assert "EMULATED" in text or p.stem == "baseline", p.name
        assert not re.search(r"(?i)\b(password|secret|token|private_key)\s*:", text), p.name
        cfg = yaml.safe_load(text)
        if p.stem != "baseline":
            assert cfg["id"] == p.stem


def test_new_playbooks_have_network_fields():
    cat = catalogue()
    for pid in ("PB-06", "PB-11", "PB-12", "PB-13", "PB-14", "PB-15", "PB-16", "PB-17"):
        pb = cat[pid]
        assert pb["executable"] and pb["owner"] and pb["target_kind"]
        assert pb.get("verification") and pb.get("rollback") and pb.get("netconfig"), pid
        assert pid in netops.NET_PLAYBOOKS
