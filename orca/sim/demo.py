"""Patch demo on the emulated network: scan -> patch (diff) -> re-scan -> re-attack -> rollback.

    python -m orca.sim.demo             # all patch playbooks, summary
    python -m orca.sim.demo --diffs     # also print every unified diff
"""
from __future__ import annotations

import argparse

from orca.scanner import scan, summary
from orca.sim import attacks, netops
from orca.sim.netstate import NetState

STEPS = [("PB-12", ["SAT-MGMT"], {}), ("PB-11", ["SAT-MGMT"], {}), ("PB-13", ["GW-IN-1"], {}),
         ("PB-14", ["TERM-CHN-01", "TERM-CHN-02", "TERM-CHN-05"], {}), ("PB-15", ["CHN-01", "CHN-05"], {}),
         ("PB-06", ["CHN-03"], {"path": "B"})]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--diffs", action="store_true")
    a = ap.parse_args(argv)
    net = NetState.load()
    print("BEFORE", summary(scan(net)), "| KA-SAT chain succeeds:", attacks.ka_sat_chain(net)["succeeded"])
    patches = []
    for pb, targets, params in STEPS:
        p = netops.apply_playbook(net, pb, targets, params=params)
        v = netops.verify(net, p)
        patches.append(p)
        ra = "; ".join(f"{r['attack']}@{r['target']} blocked at '{r['blocked_at']}'" for r in v["reattack"]) or "-"
        print(f"{pb} on {targets}: verified={v['ok']} closed={len(v['closed'])} re-attack: {ra}")
        if a.diffs:
            print(p.diff)
    print("AFTER ", summary(scan(net)), "| KA-SAT chain succeeds:", attacks.ka_sat_chain(net)["succeeded"])
    for p in reversed(patches):
        netops.rollback(net, p)
    print("ROLLED BACK", summary(scan(net)))


if __name__ == "__main__":
    main()
