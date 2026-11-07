"""Synthetic training episodes from the simulator (fixed seeds, exact labels).

Two splits with different seeds and parameter ranges: ``train`` and a HARDER ``heldout`` range
(weaker jammers, low-and-slow intrusions, weak spoofers, confounders), per docs/BUILD_PLAN.md §4.1.
Each episode: one site, 50 minutes, the condition starts at minute 15-25.
"""
from __future__ import annotations

import random

from orca.sim.engine import CLASSES, Simulator
from orca.sim.topology import SITES

RADIO_SITES = [s for s, v in SITES.items() if v["paths"]["A"][0] in ("satellite", "microwave")]
SAT_SITES = [s for s, v in SITES.items() if v["paths"]["A"][0] == "satellite"]
EPISODE_MIN = 50

# split -> parameter ranges
RANGES = {
    "train": {"rain": (15, 120), "jn": (5, 25), "spoof": (0.5, 1.0), "ss7": (0.5, 1.2), "scint": (0.4, 0.8),
              "battery": (40, 100), "surge": (1.2, 1.7), "roam": (0.5, 1.0), "eq_drop": (8, 25),
              "cfg_at": (2, 6), "wipe_p": 0.5, "confound_p": 0.15},
    "heldout": {"rain": (8, 180), "jn": (2.5, 7), "spoof": (0.35, 0.7), "ss7": (0.35, 0.7), "scint": (0.7, 1.0),
                "battery": (15, 40), "surge": (1.6, 2.0), "roam": (0.9, 1.4), "eq_drop": (5, 12),
                "cfg_at": (5, 12), "wipe_p": 0.2, "confound_p": 0.35},
}
SPLIT_SEED = {"train": 10_000, "heldout": 90_000}


def episode(i: int, split: str = "train", cls: str | None = None) -> tuple[Simulator, str, int]:
    rr = RANGES[split]
    rng = random.Random(SPLIT_SEED[split] + i)
    cls = cls or CLASSES[i % len(CLASSES)]
    pool = {"attack-management-plane": SAT_SITES, "fault-weather": RADIO_SITES, "attack-jamming": RADIO_SITES}
    site = rng.choice(pool.get(cls, sorted(SITES)))
    sim = Simulator(seed=SPLIT_SEED[split] + i, sites=[site], hour_of_day=rng.randrange(24))
    s = rng.randint(15, 25)
    u = lambda key: rng.uniform(*rr[key])  # noqa: E731
    if cls == "normal":
        k = rng.random()
        if k < 0.3:
            sim.add("surge", site, start=s, load=u("surge"))
        elif k < 0.55:
            sim.add("roaming_surge", site, start=s, intensity=u("roam"))
        elif k < 0.7:
            sim.add("rain", site, start=s, peak=rng.uniform(0.5, 3.0))      # drizzle, no outage
    elif cls == "fault-weather":
        if rng.random() < 0.8:
            sim.add("rain", site, start=s, peak=u("rain"), ramp=rng.randint(3, 20))
        else:
            sim.add("scintillation", site, start=s, s4=u("scint"))
    elif cls == "fault-power/equipment":
        k = rng.random()
        if k < 0.45:
            sim.state[site].battery_pct = u("battery")
            sim.add("power_cut", site, start=s)
        elif k < 0.85 or SITES[site]["paths"]["A"][0] != "satellite":
            sim.add("equipment_fault", site, start=s, drop_db=u("eq_drop"), path="A")
        else:
            gw = SITES[site]["paths"]["A"][1]
            sim.add("gateway_power", None, start=s, gateway=gw)
    elif cls == "attack-jamming":
        sim.add("jamming", site, start=s, j_over_n_db=u("jn"), path="A")
    elif cls == "attack-management-plane":
        if rng.random() < 0.8:
            sim.add("mgmt_intrusion", site, start=s, cfg_at=rng.randint(*rr["cfg_at"]),
                    wipe_at=(rng.randint(8, 20) if rng.random() < rr["wipe_p"] else None))
        else:
            sim.add("telemetry_edit", site, start=s)
    elif cls == "attack-gnss":
        sim.add("gnss_spoof", site, start=s, strength=u("spoof"))
    elif cls == "attack-signalling":
        sim.add("ss7_abuse", site, start=s, intensity=u("ss7"))
    # confounders: weather or benign load on top of the condition
    if cls != "normal" and rng.random() < rr["confound_p"]:
        k = rng.random()
        if k < 0.5 and cls != "fault-weather":
            sim.add("rain", site, start=rng.randint(5, 30), peak=rng.uniform(5, 40))
        elif k < 0.75:
            sim.add("surge", site, start=rng.randint(5, 30), load=rng.uniform(1.1, 1.5))
        else:
            sim.add("roaming_surge", site, start=rng.randint(5, 30), intensity=rng.uniform(0.3, 0.8))
    sim.run(EPISODE_MIN)
    return sim, site, s


def windows(n: int, split: str = "train", start_after: int = 2, normal_from: int = 10):
    """Yield (history, index, label) for every labelled minute of n episodes."""
    for i in range(n):
        sim, site, s = episode(i, split)
        hist = sim.site_history(site)
        for j, h in enumerate(hist):
            if j < normal_from:
                continue
            if j < s or j >= s + start_after:
                yield hist, j, h["label"], i


# ---------------------------------------------------------------------- M2 minute tier
def m2_episode(i: int, split: str = "train") -> tuple[list[dict], list[int]]:
    """Rain approaching a radio link, a power cut, or a quiet day; returns (history, minutes_to_failure).

    Minutes before the onset are excluded (None): an onset nobody can see coming is not forecastable,
    and keeping them would teach the model to predict failures on healthy links."""
    rng = random.Random(SPLIT_SEED[split] + 500_000 + i)
    k = rng.random()
    site = rng.choice(sorted(SITES) if k >= 0.8 else RADIO_SITES)
    sim = Simulator(seed=SPLIT_SEED[split] + 500_000 + i, sites=[site], hour_of_day=rng.randrange(24))
    horizon = 120
    onset = rng.randint(5, 20)
    if k < 0.4:
        peak = rng.uniform(20, 160) if split == "train" else rng.uniform(15, 200)
        sim.add("rain", site, start=onset, peak=peak, ramp=rng.randint(15, 60))
    elif k < 0.8:
        sim.state[site].battery_pct = rng.uniform(15, 100) if split == "train" else rng.uniform(10, 40)
        sim.state[site].battery_saving = rng.random() < 0.3
        sim.add("power_cut", site, start=onset)
    else:
        onset = 0                         # quiet: no condition, the right answer is "no failure"
        if rng.random() < 0.5:
            sim.add("rain", site, start=rng.randint(5, 20), peak=rng.uniform(0.5, 4))
    hist = sim.run(200)
    fail = [h["link_margin_db"] < 0 or h["battery_pct"] <= 5.0 for h in hist]
    ttf = []
    for j in range(len(hist)):
        nxt = next((m for m in range(j, len(hist)) if fail[m]), None)
        if j < onset:
            ttf.append(None)
        elif nxt is not None:
            ttf.append(min(horizon, nxt - j))
        elif len(hist) - j > horizon:
            ttf.append(horizon)          # observed: no failure within the horizon
        else:
            ttf.append(None)             # censored by the episode end: unknown, excluded
    return hist, ttf
