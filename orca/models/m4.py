"""M4: who gets scarce backup capacity? Mixed-integer linear program (SciPy HiGHS), greedy fallback.

Decision: integer capacity units u[s, c] (1 unit = ``unit_mbps``) given to service c at site s,
plus a binary "admitted" z[s, c] that is 1 only if the service's minimum (``min_share`` of its demand)
is met. Objective: lexicographic priority by weights 112 > hospital > grid > payments > general
(each weight exceeds the total of all lower ones), then volume. Constraints: per-site and shared-path
capacity. No training. Explanations list what was shed and why.
"""
from __future__ import annotations

import math

import numpy as np

from orca.sim.topology import PRIORITY

MIN_SHARE = {"112": 1.0, "hospital": 0.8, "grid": 0.8, "payments": 0.5, "general": 0.0}


def _weights(services: list[str], n_sites: int, max_units: int) -> dict[str, float]:
    order = sorted(services, key=lambda c: PRIORITY[c], reverse=True)   # lowest priority first
    w, total = {}, 0.0
    for c in order:
        w[c] = total + 1.0
        total += w[c] * n_sites * (max_units + 1)
    return w


def allocate(demand: dict[str, dict[str, float]], capacity: dict[str, float], shared: dict | None = None,
             unit_mbps: float = 1.0) -> dict:
    """demand: {site: {service: Mbps}}; capacity: {site: Mbps on its backup path};
    shared: {"name": {"sites": [...], "mbps": X}} for paths several sites share (e.g. one gateway)."""
    sites = sorted(demand)
    keys = [(s, c) for s in sites for c in sorted(demand[s], key=lambda c: PRIORITY[c]) if demand[s][c] > 0]
    try:
        from scipy.optimize import Bounds, LinearConstraint, milp
    except ImportError:          # pragma: no cover
        return greedy(demand, capacity, shared)
    n = len(keys)
    if n == 0:
        return {"method": "milp", "allocation": {}, "shed": [], "status": "nothing to allocate"}
    dem_u = [math.floor(demand[s][c] / unit_mbps) for s, c in keys]
    w = _weights(sorted({c for _, c in keys}), len(sites), 0)
    # variables: u (n, integer), z (n, binary). Admissions z carry lexicographic priority weights (one
    # higher-priority admission outweighs all lower ones); volume u adds a small priority-ordered bonus.
    eps = 1.0 / (10.0 * (sum(dem_u) + 1))
    cost = np.concatenate([[-eps * (6 - PRIORITY[c]) for _, c in keys], [-w[c] for _, c in keys]])
    rows, lb, ub = [], [], []
    for s in sites:                                       # site capacity
        r = np.zeros(2 * n)
        for i, (si, _) in enumerate(keys):
            if si == s:
                r[i] = 1
        rows.append(r); lb.append(0); ub.append(math.floor(capacity.get(s, 0) / unit_mbps))
    for sh in (shared or {}).values():                    # shared path capacity
        r = np.zeros(2 * n)
        for i, (si, _) in enumerate(keys):
            if si in sh["sites"]:
                r[i] = 1
        rows.append(r); lb.append(0); ub.append(math.floor(sh["mbps"] / unit_mbps))
    for i, (s, c) in enumerate(keys):                     # z=1 only if u >= min share of demand
        r = np.zeros(2 * n)
        r[i] = 1
        r[n + i] = -math.ceil(MIN_SHARE[c] * dem_u[i])
        rows.append(r); lb.append(0); ub.append(np.inf)
    for i, (s, c) in enumerate(keys):                     # strict priority: a lower service gets capacity
        for h, (s2, c2) in enumerate(keys):               # only if every higher one at the site is admitted
            if s2 == s and PRIORITY[c2] < PRIORITY[c]:
                r = np.zeros(2 * n)
                r[i] = 1
                r[n + h] = -dem_u[i]
                rows.append(r); lb.append(-np.inf); ub.append(0)
    res = milp(cost, constraints=LinearConstraint(np.array(rows), lb, ub),
               integrality=np.ones(2 * n), bounds=Bounds(np.zeros(2 * n), np.array(dem_u + [1] * n, dtype=float)))
    if not res.success:
        out = greedy(demand, capacity, shared)
        out["note"] = f"MILP failed ({res.message}); greedy fallback"
        return out
    u = np.round(res.x[:n]).astype(int)
    return _report("milp", keys, demand, [x * unit_mbps for x in u], capacity)


def greedy(demand, capacity, shared=None) -> dict:
    """Fallback: serve services in priority order until capacity runs out."""
    keys = sorted(((s, c) for s in demand for c in demand[s] if demand[s][c] > 0), key=lambda k: (PRIORITY[k[1]], k[0]))
    left = dict(capacity)
    sh_left = {k: v["mbps"] for k, v in (shared or {}).items()}
    got = []
    for s, c in keys:
        room = left.get(s, 0)
        for k, v in (shared or {}).items():
            if s in v["sites"]:
                room = min(room, sh_left[k])
        g = max(0.0, min(demand[s][c], room))
        left[s] = left.get(s, 0) - g
        for k, v in (shared or {}).items():
            if s in v["sites"]:
                sh_left[k] -= g
        got.append(g)
    return _report("greedy", keys, demand, got, capacity)


def _report(method, keys, demand, got, capacity) -> dict:
    alloc: dict = {}
    shed = []
    for (s, c), g in zip(keys, got):
        d = demand[s][c]
        alloc.setdefault(s, {})[c] = {"demand_mbps": round(d, 2), "granted_mbps": round(float(g), 2),
                                      "served": round(float(g) / d, 3) if d else 1.0}
        if g + 1e-9 < d:
            shed.append({"site": s, "service": c, "shed_mbps": round(d - float(g), 2),
                         "why": f"priority {PRIORITY[c]} ({c}) after higher-priority services; capacity "
                                f"{capacity.get(s, 0)} Mbps"})
    return {"method": method, "allocation": alloc, "shed": shed,
            "priority": "112 > hospital > grid > payments > general", "status": "ok"}
