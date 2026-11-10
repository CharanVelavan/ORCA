"""Delivered Mbps per site and per service for one simulated minute.

Demand comes from the site record (demand_mbps) split by topology.DEMAND_SHARE. Capacity is the
record's measured capacity_mbps. When every service fits, each is delivered in full. Otherwise the
M4 capacity planner (orca.models.m4, a MILP with a greedy fallback) decides who is served first,
so 112 and the hospital keep their full demand while lower priorities are shed.
"""
from __future__ import annotations

import math

from orca.models import m4
from orca.sim.topology import DEMAND_SHARE, PRIORITY, SERVICES

UNIT_MBPS = 0.1
PUBLIC_SERVICE_KEY = {"payments": "upi_atm"}


def service_demand(rec: dict) -> dict[str, float]:
    return {svc: round(rec["demand_mbps"] * DEMAND_SHARE[svc], 2) for svc in SERVICES}


def allocate_minute(records: list[dict]) -> dict:
    """Fill ``delivered_mbps`` and ``services`` on every record; return the planner summary."""
    demand = {r["site"]: service_demand(r) for r in records}
    short = {r["site"]: r["capacity_mbps"] for r in records if r["capacity_mbps"] < r["demand_mbps"] - 1e-9}
    plan = {"method": "none", "solution": None, "status": "not_needed",
            "allocation": {}, "shed": [], "sites": sorted(short)}
    if short:
        res = m4.allocate({s: demand[s] for s in short}, short, unit_mbps=UNIT_MBPS)
        plan.update(method=res["method"], solution=res.get("solution"), status=res.get("status"),
                    allocation=res["allocation"], shed=res["shed"])
        _close_quantisation(plan, demand, short)
    for r in records:
        got = plan["allocation"].get(r["site"], {})
        services = {}
        for svc in SERVICES:
            d = demand[r["site"]][svc]
            g = d if r["site"] not in short else got.get(svc, {}).get("granted_mbps", 0.0)
            services[svc] = {"demand_mbps": d, "delivered_mbps": round(min(g, d), 2),
                             "pct": round(100 * min(g, d) / d, 1) if d else 100.0}
        r["services"] = services
        r["delivered_mbps"] = round(sum(s["delivered_mbps"] for s in services.values()), 2)
    return plan


def allocation_error(plan: dict, records: list[dict]) -> str | None:
    """Validate the displayed post-quantisation allocation, not the solver's raw optimum."""
    allocation = plan.get("allocation")
    short = {r["site"]: r for r in records if r["capacity_mbps"] < r["demand_mbps"] - 1e-9}
    if not isinstance(allocation, dict) or not short or set(allocation) != set(short):
        return "allocation does not cover the capacity-constrained sites"
    plan_sites = plan.get("sites")
    if not isinstance(plan_sites, list) or not all(isinstance(site, str) for site in plan_sites) or set(plan_sites) != set(short):
        return "allocation site list does not match the constrained sites"
    for site, record in short.items():
        rows = allocation[site]
        demand = service_demand(record)
        expected = {svc for svc, value in demand.items() if value > 0}
        if not isinstance(rows, dict) or set(rows) != expected:
            return f"allocation has incomplete service rows for {site}"
        granted = {}
        for svc in expected:
            row = rows[svc]
            if not isinstance(row, dict):
                return f"allocation row for {site}/{svc} is invalid"
            want, give, served = row.get("demand_mbps"), row.get("granted_mbps"), row.get("served")
            if (isinstance(want, bool) or not isinstance(want, (int, float)) or not math.isfinite(want)
                    or isinstance(give, bool) or not isinstance(give, (int, float)) or not math.isfinite(give)
                    or isinstance(served, bool) or not isinstance(served, (int, float)) or not math.isfinite(served)
                    or abs(want - demand[svc]) > 1e-6 or give < 0 or give > want + 1e-6
                    or abs(served - round(give / want if want else 1.0, 3)) > 1e-6):
                return f"allocation has inconsistent demand, grant or served fraction for {site}/{svc}"
            granted[svc] = give
        if sum(granted.values()) > record["capacity_mbps"] + 1e-6:
            return f"allocation exceeds measured capacity for {site}"
        ordered = sorted(expected, key=PRIORITY.get)
        for i, svc in enumerate(ordered):
            if granted[svc] <= 0:
                continue
            for higher in ordered[:i]:
                units = math.floor(demand[higher] / UNIT_MBPS)
                required = math.ceil(m4.MIN_SHARE[higher] * units) * UNIT_MBPS
                if granted[higher] + 1e-6 < required:
                    return f"allocation violates service priority for {site}/{higher}"
    return None


def totals(records: list[dict]) -> dict:
    out = {}
    for svc in sorted(SERVICES, key=PRIORITY.get):
        d = round(sum(r["services"][svc]["demand_mbps"] for r in records), 2)
        g = round(sum(r["services"][svc]["delivered_mbps"] for r in records), 2)
        out[svc] = {"demand_mbps": d, "delivered_mbps": g, "pct": round(100 * min(g, d) / d, 1) if d else 100.0}
    return out


def _close_quantisation(plan: dict, demand: dict, capacity: dict) -> None:
    """The MILP works in UNIT_MBPS steps; a service within one step of its demand is served in full."""
    for site, alloc in plan["allocation"].items():
        room = capacity[site]
        for svc in sorted(alloc, key=PRIORITY.get):
            row, want = alloc[svc], demand[site][svc]
            granted = row["granted_mbps"]
            if granted > 0 and granted >= want - UNIT_MBPS:
                granted = want
            granted = round(max(0.0, min(granted, want, room)), 2)
            row["granted_mbps"] = granted
            room = max(0.0, room - granted)
            row["served"] = round(granted / want, 3) if want else 1.0
    old = {(x["site"], x["service"]): x for x in plan["shed"]}
    shed = []
    for site, alloc in plan["allocation"].items():
        for svc in sorted(alloc, key=PRIORITY.get):
            short = round(demand[site][svc] - alloc[svc]["granted_mbps"], 2)
            if short > 0:
                x = dict(old.get((site, svc)) or {"site": site, "service": svc,
                         "why": f"priority {PRIORITY[svc]} ({svc}) after higher-priority services; "
                                f"capacity {capacity[site]} Mbps"})
                x["shed_mbps"] = short
                shed.append(x)
    plan["shed"] = shed
