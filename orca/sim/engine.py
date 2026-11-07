"""Minute-step simulator of the emulated Chennai NTN network. Deterministic for a given seed.

Everything is emulated: attacks are *conditions* with observable effects on telemetry, never
exploit code. One record per site per minute (see ``RECORD_KEYS``), plus a ground-truth label.

Conditions (kind -> ground-truth class):
  rain               fault-weather            rain cell over the site (ITU-R P.838 fade)
  scintillation      fault-weather            ionospheric GNSS scintillation (natural)
  power_cut          fault-power/equipment    mains off, battery discharges
  equipment_fault    fault-power/equipment    radio/modem failure: received level falls, noise flat
  gateway_power      fault-power/equipment    gateway outage: all satellite paths via it drop
  jamming            attack-jamming           noise floor rises (J/N), received level steady
  mgmt_intrusion     attack-management-plane  KA-SAT chain: VPN login -> config changes -> wipe
  telemetry_edit     attack-management-plane  management system reports false KPIs
  gnss_spoof         attack-gnss              uniform high C/N0, AGC drop, clock and position jumps
  ss7_abuse          attack-signalling        location queries from unknown/foreign sources
  surge              normal                   benign traffic peak (festival, cricket)
  roaming_surge      normal                   benign signalling peak (inbound roamers)

Scenario "pins" (``pin``) override an observed signal from a minute onward, so scenario files
(scenarios/SCHEMA.md signal names) reproduce exactly; link pins clear when the site fails over.
"""
from __future__ import annotations

import datetime as dt
import math
import random
from dataclasses import dataclass, field

from orca.sim import physics
from orca.sim.topology import (DEMAND_SHARE, GATEWAYS, INDIAN_GATEWAYS, LINK_CLASSES, SITES,
                               TERMINALS_PER_SITE)

CLASS_OF = {
    "rain": "fault-weather", "scintillation": "fault-weather",
    "power_cut": "fault-power/equipment", "equipment_fault": "fault-power/equipment",
    "gateway_power": "fault-power/equipment",
    "jamming": "attack-jamming",
    "mgmt_intrusion": "attack-management-plane", "telemetry_edit": "attack-management-plane",
    "gnss_spoof": "attack-gnss", "ss7_abuse": "attack-signalling",
    "surge": "normal", "roaming_surge": "normal",
}
# When several conditions overlap, the label is the most security-relevant one.
LABEL_ORDER = ["attack-management-plane", "attack-jamming", "attack-gnss", "attack-signalling",
               "fault-power/equipment", "fault-weather", "normal"]
CLASSES = ["normal", "fault-weather", "fault-power/equipment", "attack-jamming",
           "attack-management-plane", "attack-gnss", "attack-signalling"]
LINK_SIGNALS = {"snr_db", "link_margin_db", "packet_loss", "txn_success"}

RECORD_KEYS = [
    "t", "ts", "site", "label", "active_path", "path_kind", "gateway",
    "rain_mm_h", "expected_fade_db", "snr_db", "rx_dbm", "noise_dbm", "noise_rise_db", "fade_residual_db",
    "link_margin_db", "capacity_mbps", "demand_mbps", "traffic_load", "packet_loss", "txn_success",
    "mains_power", "battery_pct", "battery_saving", "terminals_up",
    "mgmt_logins", "mgmt_login_anomalous", "mgmt_failed_logins", "mgmt_cmds", "mgmt_wipe", "mgmt_cfg_change",
    "mgmt_telemetry_edit", "reported_loss", "telemetry_mismatch",
    "gnss_cn0_mean", "gnss_cn0_std", "gnss_agc_db", "gnss_clock_offset_ns", "gnss_pos_jump_m",
    "ss7_msg_rate", "ss7_loc_query_rate", "ss7_foreign_share", "ss7_error_rate",
]


@dataclass
class Condition:
    kind: str
    site: str | None          # None = network-wide (e.g. gateway_power uses params.gateway)
    start: int
    end: int | None = None
    params: dict = field(default_factory=dict)

    @property
    def label(self) -> str:
        return CLASS_OF[self.kind]

    def active(self, t: int) -> bool:
        return self.start <= t and (self.end is None or t < self.end)

    def ramp(self, t: int, minutes: float = 5.0) -> float:
        """0 -> 1 over the first ``minutes`` of the condition."""
        return max(0.0, min(1.0, (t - self.start + 1) / minutes))


@dataclass
class SiteState:
    battery_pct: float = 100.0
    terminals_up: int = TERMINALS_PER_SITE
    active_path: str = "A"
    battery_saving: bool = False
    prestaged: str | None = None
    reattack_watch_until: int | None = None
    clock_offset_ns: float = 0.0


class Simulator:
    """``Simulator(seed).run(60)`` -> list of records. ``conditions`` and ``pins`` drive events."""

    def __init__(self, seed: int = 0, start: str = "2026-11-10T19:00:00+05:30", sites: list[str] | None = None,
                 hour_of_day: int | None = None):
        self.seed = seed
        self.rng = random.Random(seed)
        self.start = dt.datetime.fromisoformat(start)
        self.sites = list(sites or sorted(SITES))
        self.t = -1
        self.state = {s: SiteState() for s in self.sites}
        self.conditions: list[Condition] = []
        self.pins: dict[tuple[str, str], tuple[int, object]] = {}
        self.routes: dict[str, dict[str, dict]] = {s: {p: {"gateway": g, "kind": k, "integrity": "verified"}
                                                       for p, (k, g) in SITES[s]["paths"].items()}
                                                   for s in self.sites}
        self.history: list[dict] = []
        self.hour0 = self.start.hour if hour_of_day is None else hour_of_day
        self.gateway_up = {g: True for g in GATEWAYS}
        self.mgmt_contained = False     # set by netops after PB-01/PB-11/PB-12 close the intrusion path

    # ------------------------------------------------------------ inputs
    def add(self, kind: str, site: str | None, start: int | None = None, end: int | None = None, **params) -> Condition:
        if kind not in CLASS_OF:
            raise ValueError(f"unknown condition {kind}")
        c = Condition(kind, site, self.t + 1 if start is None else start, end, params)
        self.conditions.append(c)
        return c

    def pin(self, site: str, signal: str, value, t: int | None = None) -> None:
        self.pins[(site, signal)] = (self.t + 1 if t is None else t, value)

    def offer_route(self, site: str, path: str, gateway: str, integrity: str = "unverified", kind: str = "satellite"):
        self.routes.setdefault(site, {})[path] = {"gateway": gateway, "kind": kind, "integrity": integrity}

    def failover(self, site: str, path: str) -> None:
        """Switch the active path (the effect of PB-06). Clears link pins of the old path."""
        st = self.state[site]
        if st.active_path != path:
            st.active_path = path
            for sig in LINK_SIGNALS:
                self.pins.pop((site, sig), None)

    # ------------------------------------------------------------ helpers
    def _active(self, site: str, t: int, kinds: set[str] | None = None) -> list[Condition]:
        return [c for c in self.conditions if c.active(t) and (c.site in (site, None)) and
                (kinds is None or c.kind in kinds)]

    def _pinned(self, site: str, signal: str, t: int):
        p = self.pins.get((site, signal))
        if p and p[0] <= t:
            return p[1]
        return None

    def ts(self, t: int) -> str:
        return (self.start + dt.timedelta(minutes=t)).isoformat()

    def label(self, site: str, t: int) -> str:
        labels = {c.label for c in self._active(site, t)}
        for lab in LABEL_ORDER:
            if lab in labels:
                return lab
        return "normal"

    # ------------------------------------------------------------ one minute
    def step(self) -> list[dict]:
        self.t += 1
        if self.mgmt_contained:      # attacker locked out: management-plane conditions end
            for c in self.conditions:
                if c.kind in ("mgmt_intrusion", "telemetry_edit") and c.active(self.t):
                    c.end = self.t
        recs =[self._site_minute(s, self.t) for s in self.sites]
        self.history.extend(recs)
        return recs

    def run(self, minutes: int) -> list[dict]:
        out = []
        for _ in range(minutes):
            out.extend(self.step())
        return out

    def _site_minute(self, site: str, t: int) -> dict:
        r, g = self.rng, self.rng.gauss
        st = self.state[site]
        conds = self._active(site, t)
        kinds = {c.kind for c in conds}
        hour = (self.hour0 + t // 60) % 24
        diurnal = 0.75 + 0.35 * math.sin((hour - 9) / 24 * 2 * math.pi)

        # weather
        rain = 0.0
        for c in conds:
            if c.kind == "rain":
                rain = max(rain, c.params.get("peak", 30.0) * c.ramp(t, c.params.get("ramp", 10)))
        rain = max(0.0, rain * (1 + 0.08 * g(0, 1))) if rain else max(0.0, g(0, 0.05))
        pr = self._pinned(site, "rain_mm_h", t)
        if pr is not None:
            rain = float(pr) + (abs(g(0, 0.3)) if pr else 0.0)

        # link on the active path
        path = st.active_path
        route = self.routes[site].get(path) or {"gateway": "GW-IN-1", "kind": "satellite"}
        kind = route.get("kind") or SITES[site]["paths"].get(path, ("satellite", None))[0]
        link = LINK_CLASSES[kind]
        exp_fade = physics.rain_fade_db(link, rain)
        fade = exp_fade * (1 + 0.1 * g(0, 1)) if exp_fade else 0.0
        jn = max([c.params.get("j_over_n_db", 10.0) * c.ramp(t, 3) for c in conds if c.kind == "jamming"
                  and c.params.get("path", "A") == path] or [-99.0])
        rx = link["rx_dbm"] - fade + g(0, 0.3)
        noise = link["noise_dbm"] + g(0, 0.2)
        if jn > -50:
            noise = link["noise_dbm"] + 10 * math.log10(1 + 10 ** (jn / 10)) + g(0, 0.3)
        eq = [c for c in conds if c.kind == "equipment_fault" and c.params.get("path", "A") == path]
        if eq:
            rx -= eq[0].params.get("drop_db", 15.0) * eq[0].ramp(t, 2)
        gw = route.get("gateway")
        gw_down = (not self.gateway_up.get(gw, True)) or any(
            c.kind == "gateway_power" and c.params.get("gateway") == gw for c in self.conditions if c.active(t))
        snr = rx - noise
        if gw_down and kind == "satellite":
            snr = -10.0 + g(0, 0.5)
        noise_rise = noise - link["noise_dbm"]

        # terminals (wipe hits satellite modems)
        for c in conds:
            if c.kind == "mgmt_intrusion" and c.params.get("wipe_at") is not None and t >= c.start + c.params["wipe_at"]:
                st.terminals_up = max(0, st.terminals_up - c.params.get("wipe_rate", 2))
        pt = self._pinned(site, "terminals_up", t)
        if pt is not None:
            st.terminals_up = int(pt)
        if kind == "satellite" and path == "A" and st.terminals_up == 0:
            snr = -15.0 + g(0, 0.5)

        ps = self._pinned(site, "snr_db", t)
        if ps is not None:
            snr = float(ps) + g(0, 0.2)
        fade_residual = (link["clear_snr_db"] - snr) - exp_fade     # SNR loss that the weather does not explain
        margin = snr - link["req_snr_db"]
        pm =self._pinned(site, "link_margin_db", t)
        if pm is not None:
            margin = float(pm) + g(0, 0.15)
        cap_frac = physics.capacity_fraction(snr, link["req_snr_db"])
        if kind == "satellite" and path == "A":
            cap_frac *= st.terminals_up / TERMINALS_PER_SITE

        # power
        mains = 0 if any(c.kind == "power_cut" for c in conds) else 1
        pmains = self._pinned(site, "mains_power", t)
        if pmains is not None:
            mains = int(pmains)
        load_kw = SITES[site]["load_kw"] * (0.6 if st.battery_saving else 1.0) * (0.9 + 0.1 * diurnal)
        if mains:
            st.battery_pct = min(100.0, st.battery_pct + 0.5)
        else:
            st.battery_pct = max(0.0, st.battery_pct - load_kw / SITES[site]["battery_kwh"] * 100 / 60
                                 * (1 + 0.03 * g(0, 1)))
        pb = self._pinned(site, "battery_pct", t)
        if pb is not None and self.pins[(site, "battery_pct")][0] == t:
            st.battery_pct = float(pb)
        if st.battery_pct <= 5.0:
            cap_frac = 0.0          # site shuts down at the cut-off

        # traffic
        surge = max([c.params.get("load", 1.5) for c in conds if c.kind == "surge"] or [0.0])
        demand_load = max(0.3, diurnal * (1 + 0.04 * g(0, 1)))
        if surge:
            demand_load = surge * (1 + 0.03 * g(0, 1))
        ptl = self._pinned(site, "traffic_load", t)
        if isinstance(ptl, dict):
            demand_load = float(ptl.get("load", demand_load))
        capacity = link["capacity_mbps"] * cap_frac
        nominal = LINK_CLASSES[SITES[site]["paths"]["A"][0]]["capacity_mbps"]
        demand = 0.35 * nominal * demand_load       # ASSUMED: 35 % of the primary's capacity at nominal load
        loss = max(0.0, 1 - capacity / demand) if demand > 0 else 0.0
        loss = min(1.0, max(0.0, loss + abs(g(0, 0.005))))
        pl = self._pinned(site, "packet_loss", t)
        if pl is not None:
            loss = min(1.0, max(0.0, float(pl) + g(0, 0.01)))
        txn = max(0.0, min(1.0, 1 - 1.1 * loss + g(0, 0.005)))
        ptx = self._pinned(site, "txn_success", t)
        if isinstance(ptx, dict):
            txn = float(ptx.get("rate", txn))

        # management plane (KA-SAT chain stages)
        logins = 1 if r.random() < 0.04 * diurnal else 0
        anomalous = failed = cmds = wipe = cfg = tedit = 0
        for c in conds:
            if c.kind == "mgmt_intrusion":
                k = t - c.start
                if k == 0 or (k < 3 and r.random() < 0.5):
                    logins += 1
                    anomalous = 1
                failed += r.random() < 0.6 and k < 5
                if k >= c.params.get("cfg_at", 3):
                    cfg += 1 + int(r.random() < 0.5)
                    cmds += cfg
                if c.params.get("wipe_at") is not None and 0 <= k - c.params["wipe_at"] < c.params.get("wipe_minutes", 3):
                    wipe += c.params.get("wipe_cmds", 3)
                    cmds += wipe
            if c.kind == "telemetry_edit":
                tedit += 1 + int(r.random() < 0.5)
                cmds += tedit
        vl = self._pinned(site, "vpn_login", t)
        if isinstance(vl, dict) and self.pins[(site, "vpn_login")][0] == t:
            logins += 1
            anomalous = int(bool(vl.get("anomalous")))
        mc = self._pinned(site, "mgmt_command", t)
        if isinstance(mc, dict) and self.pins[(site, "mgmt_command")][0] == t:
            n = int(mc.get("count", 1))
            cmds += n
            typ = mc.get("type")
            wipe += n if typ == "wipe" else 0
            cfg += n if typ in ("config_change", "reboot") else 0
            tedit += n if typ == "telemetry_edit" else 0
        if r.random() < 0.02:
            cmds += 1                      # routine "show" commands
        reported = loss
        if any(c.kind == "telemetry_edit" for c in conds):
            reported = 0.0
        tr = self._pinned(site, "telemetry_reported", t)
        if isinstance(tr, dict):
            reported = float(tr.get("value", reported))

        # GNSS receiver (timing for the site)
        cn0_mean, cn0_std, agc, pos_jump = 44 + g(0, 0.8), 3.0 + abs(g(0, 0.4)), 0.0 + g(0, 0.3), abs(g(0, 1.5))
        st.clock_offset_ns = 0.9 * st.clock_offset_ns + g(0, 3)
        for c in conds:
            if c.kind == "gnss_spoof":
                a = c.ramp(t, 4) * c.params.get("strength", 1.0)
                cn0_mean += 5 * a
                cn0_std = max(0.3, cn0_std * (1 - 0.8 * a))
                agc -= 6 * a
                st.clock_offset_ns += 40 * a + g(0, 5)
                pos_jump += 300 * a * (1 + 0.2 * g(0, 1))
            elif c.kind == "scintillation":
                a = c.ramp(t, 3) * c.params.get("s4", 0.6)
                cn0_mean -= 6 * a + abs(g(0, 2 * a))
                cn0_std += 5 * a
                pos_jump += 15 * a * abs(g(0, 1))

        # signalling (SS7/Diameter batches seen at the site's core interface)
        msg = max(0.0, 200 * diurnal * (1 + 0.08 * g(0, 1)))
        locq = msg * (0.02 + 0.004 * abs(g(0, 1)))
        foreign = max(0.0, 0.05 + 0.02 * g(0, 1))
        err = max(0.0, 0.01 + 0.004 * g(0, 1))
        for c in conds:
            if c.kind == "ss7_abuse":
                a = c.ramp(t, 3) * c.params.get("intensity", 1.0)
                q = 60 * a * (1 + 0.2 * g(0, 1))
                locq += q
                msg += q
                foreign = min(1.0, foreign + 0.35 * a)
                err += 0.05 * a
            elif c.kind == "roaming_surge":
                a = c.ramp(t, 10) * c.params.get("intensity", 1.0)
                msg *= 1 + 1.2 * a
                locq *= 1 + 1.0 * a
                foreign = min(1.0, foreign + 0.25 * a)

        return {
            "t": t, "ts": self.ts(t), "site": site, "label": self.label(site, t),
            "active_path": path, "path_kind": kind, "gateway": gw,
            "rain_mm_h": round(rain, 3), "expected_fade_db": round(exp_fade, 3), "snr_db": round(snr, 3),
            "rx_dbm": round(rx, 3), "noise_dbm": round(noise, 3), "noise_rise_db": round(noise_rise, 3),
            "fade_residual_db": round(fade_residual, 3), "link_margin_db": round(margin, 3),
            "capacity_mbps": round(capacity, 2), "demand_mbps": round(demand, 2), "traffic_load": round(demand_load, 3),
            "packet_loss": round(loss, 4), "txn_success": round(txn, 4),
            "mains_power": mains, "battery_pct": round(st.battery_pct, 2), "battery_saving": int(st.battery_saving),
            "terminals_up": st.terminals_up,
            "mgmt_logins": logins, "mgmt_login_anomalous": anomalous, "mgmt_failed_logins": int(failed),
            "mgmt_cmds": cmds, "mgmt_wipe": wipe, "mgmt_cfg_change": cfg, "mgmt_telemetry_edit": tedit,
            "reported_loss": round(reported, 4), "telemetry_mismatch": round(abs(loss - reported), 4),
            "gnss_cn0_mean": round(cn0_mean, 3), "gnss_cn0_std": round(cn0_std, 3), "gnss_agc_db": round(agc, 3),
            "gnss_clock_offset_ns": round(st.clock_offset_ns, 2), "gnss_pos_jump_m": round(pos_jump, 2),
            "ss7_msg_rate": round(msg, 2), "ss7_loc_query_rate": round(locq, 2),
            "ss7_foreign_share": round(foreign, 4), "ss7_error_rate": round(err, 4),
        }

    # ------------------------------------------------------------ observations for the rest of ORCA
    def series(self, site: str, key: str) -> list:
        return [h[key] for h in self.history if h["site"] == site]

    def site_history(self, site: str) -> list[dict]:
        return [h for h in self.history if h["site"] == site]

    def path_report(self, site: str, path: str) -> dict:
        """Measured state of a candidate path (used by the PB-06 clean-path check)."""
        route = self.routes.get(site, {}).get(path)
        if not route:
            return {"exists": False}
        t = max(self.t, 0)
        kind = route.get("kind", "satellite")
        jam = [c for c in self._active(site, t, {"jamming"}) if c.params.get("path", "A") == path]
        eq = [c for c in self._active(site, t, {"equipment_fault"}) if c.params.get("path", "A") == path]
        gw = route.get("gateway")
        gw_down = any(c.kind == "gateway_power" and c.params.get("gateway") == gw for c in self.conditions
                      if c.active(t))
        # KA-SAT lesson: while the operator's management network is compromised and not contained,
        # every satellite path it manages is suspect, including the backup gateway.
        mgmt_hot = (kind == "satellite" and not self.mgmt_contained
                    and bool(self._active(site, t, {"mgmt_intrusion", "telemetry_edit"})))
        return {"exists": True, "gateway": gw, "kind": kind, "integrity_flag": route.get("integrity"),
                "gateway_in_india": gw in INDIAN_GATEWAYS, "jammed": bool(jam), "equipment_fault": bool(eq),
                "gateway_down": gw_down, "shares_compromised_mgmt": mgmt_hot}
