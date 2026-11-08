"""Catalogue and safe application of live simulator conditions.

The catalogue names incident *conditions* in the emulated network.  It intentionally
contains no exploit implementation or real network operation.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Injector:
    id: str
    label: str
    default_target: str
    truth_class: str
    category: str


INJECTORS = {
    "mgmt_intrusion": Injector("mgmt_intrusion", "KA-SAT style management intrusion", "noc-vendor-7", "attack-management-plane", "attack"),
    "jamming": Injector("jamming", "Jam the satellite uplink", "CHN-02", "attack-jamming", "attack"),
    "failover_lure": Injector("failover_lure", "Lure failover to a foreign gateway", "CHN-02", "attack", "attack"),
    "gnss_spoof": Injector("gnss_spoof", "GNSS spoofing (timing)", "CHN-03", "attack-gnss", "attack"),
    "ss7_abuse": Injector("ss7_abuse", "SS7 location tracking", "CHN-04", "attack-signalling", "attack"),
    "telemetry_edit": Injector("telemetry_edit", "Fake all-green telemetry", "SAT-MGMT", "attack-management-plane", "attack"),
    "firmware_exploit": Injector("firmware_exploit", "Exploit old terminal firmware", "CHN-01", "attack", "attack"),
    "feeder_intercept": Injector("feeder_intercept", "Intercept unencrypted feeder link", "GW-IN-1", "attack", "attack"),
    "rain": Injector("rain", "Monsoon rain cell", "CHN-01", "fault-weather", "fault"),
    "power_cut": Injector("power_cut", "Grid power cut", "CHN-05", "fault-power/equipment", "fault"),
    "gateway_power": Injector("gateway_power", "Gateway outage", "GW-IN-1", "fault-power/equipment", "fault"),
    "surge": Injector("surge", "Festival traffic surge", "CHN-01", "normal", "benign"),
}


def catalogue() -> list[dict]:
    return [{"id": i.id, "label": i.label, "default_target": i.default_target,
             "category": i.category} for i in INJECTORS.values()]


def apply(sim, kind: str, target: str | None, start: int, duration_min: int, params: dict | None = None) -> dict:
    """Apply one catalogue item to a simulator and return non-secret public metadata."""
    if kind not in INJECTORS:
        raise ValueError(f"unknown injector {kind}")
    spec, p = INJECTORS[kind], dict(params or {})
    target = target or spec.default_target
    end = start + max(1, int(duration_min))
    sites = [target] if target.startswith("CHN-") else []
    if kind == "mgmt_intrusion":
        sites = p.pop("sites", ["CHN-01", "CHN-02"])
        wipe_at = p.pop("wipe_at", 3)
        for site in sites:
            sim.add("mgmt_intrusion", site, start=start, end=end, wipe_at=wipe_at, **p)
    elif kind == "failover_lure":
        sim.offer_route(target, "C", "GW-XX", integrity="unverified", kind="satellite")
        # A short degradation makes the offered route meaningful without changing its unsafe status.
        sim.add("jamming", target, start=start, end=end, j_over_n_db=p.get("j_over_n_db", 10), path="A", lure=True)
    elif kind in ("firmware_exploit", "feeder_intercept"):
        # The existing attack-graph models the weakness; a management-plane signal is all agents observe.
        for site in sites or ["CHN-01"]:
            sim.add("mgmt_intrusion", site, start=start, end=end, wipe_at=10_000, **p)
    elif kind == "gateway_power":
        sim.add("gateway_power", None, start=start, end=end, gateway=target, **p)
    elif kind == "telemetry_edit":
        for site in p.pop("sites", ["CHN-01", "CHN-02"]):
            sim.add("telemetry_edit", site, start=start, end=end, **p)
    else:
        sim.add(kind, target, start=start, end=end, **p)
    return {"kind": kind, "label": spec.label, "target": target, "start": start, "end": end,
            "truth_class": spec.truth_class, "sites": sites}
