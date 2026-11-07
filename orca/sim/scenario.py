"""Drive the simulator from a scenario file and release events progressively, per role.

Routing is NOT re-implemented here: events go through ``orca.agents.EventFeed`` (explicit ``to:``,
else the actor role, else roles whose ``sees`` matches the signals / source). Model alerts produced
from the simulated telemetry are routed with the same ``EventFeed.route`` on a pseudo-event
``{actor: M1..M4, signals: []}``, i.e. to roles whose ``sees.sources`` include that model.

    run = ScenarioRun("s1", world=world)       # world optional
    run.step_to(30)                            # simulate minutes 0..30, release events with t <= 30
    run.run()                                  # to the last event + 10 minutes

Scenario signals (scenarios/SCHEMA.md) become simulator conditions and pins:
  vpn_login{anomalous}      -> mgmt_intrusion condition (KA-SAT stage 1) + pinned login
  mgmt_command{type,count}  -> config_change/reboot: intrusion active; wipe: wipe the site's terminals;
                               telemetry_edit: telemetry_edit condition
  rain_mm_h > 0             -> rain condition (P.838 fade) + pin
  snr_db (scenario attack-jamming, no rain) -> jamming condition + pin; otherwise pin only
  mains_power 0/1           -> power_cut condition starts/ends
  route_candidate           -> route offered to the site (sim.routes and world.routes)
  link_protection           -> observation (feeder audit), kept in ``observations``
  other signals             -> pins (observed value from that minute)
"""
from __future__ import annotations

from pathlib import Path

import yaml

from orca.sim.engine import Simulator
from orca.sim.netstate import NetState
from orca.sim.topology import SITES

SCEN_DIR = Path(__file__).resolve().parents[2] / "scenarios"


def load_scenario(name_or_path) -> dict:
    p = Path(name_or_path)
    if not p.exists():
        p = SCEN_DIR / f"{str(name_or_path).lower()}.yaml"
    return yaml.safe_load(p.read_text())


class ScenarioRun:
    def __init__(self, scenario, world=None, roles=None, net: NetState | None = None, detector=None):
        from orca.agents import EventFeed, load_agent_roles   # lazy: agents imports remediation/world
        self.sc = scenario if isinstance(scenario, dict) else load_scenario(scenario)
        self.sim = Simulator(seed=self.sc.get("seed", 0), start=self.sc["start"])
        self.net = net or NetState.load()
        self.world = world
        self.feed = EventFeed(self.sc, roles if roles is not None else load_agent_roles())
        self.detector = detector
        self.applied: set[int] = set()
        self.released: dict[str, list[dict]] = {}
        self.model_alerts: list[dict] = []
        self.observations: list[dict] = []
        if world is not None:
            world.facts.setdefault("jurisdiction", self.sc.get("jurisdiction", "IN"))
            world.facts.setdefault("entity", self.sc.get("entity", {}))

    # ------------------------------------------------------------ scenario signals -> sim
    def _apply(self, e: dict) -> None:
        sim, t = self.sim, e["t"]
        for s in e.get("signals") or []:
            site, sig, val = s.get("site"), s.get("signal"), s.get("value")
            active = lambda kind: [c for c in sim.conditions if c.kind == kind and c.site == site and c.active(t)]  # noqa: E731
            if sig == "vpn_login":
                sim.pin(site, sig, val, t)
                if isinstance(val, dict) and val.get("anomalous") and not active("mgmt_intrusion"):
                    sim.add("mgmt_intrusion", site, start=t)
            elif sig == "mgmt_command":
                sim.pin(site, sig, val, t)
                typ = (val or {}).get("type")
                if typ == "telemetry_edit":
                    if not active("telemetry_edit"):
                        sim.add("telemetry_edit", site, start=t)
                elif typ == "wipe":
                    cur = active("mgmt_intrusion")
                    if cur:
                        cur[0].params["wipe_at"] = t - cur[0].start
                    else:
                        sim.add("mgmt_intrusion", site, start=t, wipe_at=0)
                elif str(self.sc.get("m3_expected", "")).startswith("attack-management"):
                    if not active("mgmt_intrusion"):
                        sim.add("mgmt_intrusion", site, start=t)
                elif str(self.sc.get("m3_expected", "")).startswith("fault-power"):
                    # a legitimate change that breaks the link (N2): equipment/config fault, not an attack
                    if not active("equipment_fault"):
                        sim.add("equipment_fault", site, start=t, path="A", drop_db=20.0)
            elif sig == "rain_mm_h":
                sim.pin(site, sig, val, t)
                for c in active("rain"):
                    c.end = t
                if val and float(val) > 0:
                    sim.add("rain", site, start=t, peak=float(val), ramp=1)
            elif sig == "snr_db":
                sim.pin(site, sig, val, t)
                if self.sc.get("m3_expected") == "attack-jamming" and not active("rain") and not active("jamming"):
                    sim.add("jamming", site, start=t, j_over_n_db=max(3.0, 12.0 - float(val)), path="A")
            elif sig == "mains_power":
                if int(val) == 0 and not active("power_cut"):
                    sim.add("power_cut", site, start=t)
                elif int(val) == 1:
                    for c in active("power_cut"):
                        c.end = t
                sim.pin(site, sig, val, t)
            elif sig == "route_candidate":
                path, gw = val["path"], val["gateway"]
                kind = SITES[site]["paths"].get(path, ("satellite", gw))[0]
                sim.offer_route(site, path, gw, val.get("integrity", "unverified"), kind)
                if self.world is not None:
                    self.world.routes.setdefault(site, {})[path] = {"gateway": gw, "integrity": val.get("integrity", "unverified")}
            elif sig == "link_protection":
                self.observations.append({"t": t, "site": site, "link_protection": val})
            else:
                sim.pin(site, sig, val, t)

    # ------------------------------------------------------------ time
    def step_to(self, t_end: int) -> dict[str, list[dict]]:
        """Simulate up to minute t_end; release due events; return {role: [new alerts]} for this call."""
        out: dict[str, list[dict]] = {}
        while self.sim.t < t_end:
            minute = self.sim.t + 1
            due = [(i, e) for i, e in enumerate(self.sc["events"]) if e["t"] == minute and i not in self.applied]
            for i, e in due:
                self._apply(e)
                self.applied.add(i)
            self.sim.step()
            if due:
                rel = self._release(minute, [e for _, e in due])
                for r, al in rel.items():
                    out.setdefault(r, []).extend(al)
            for a in self._model_alerts(minute):
                for r in a["visible_to"]:
                    out.setdefault(r, []).append(a)
        for r, al in out.items():
            self.released.setdefault(r, []).extend(al)
        return out

    def run(self, extra: int = 10) -> dict[str, list[dict]]:
        return self.step_to(max(e["t"] for e in self.sc["events"]) + extra)

    def _release(self, minute: int, events: list[dict]) -> dict[str, list[dict]]:
        if self.world is not None:
            return self.feed.release(self.world, minute)
        out: dict[str, list[dict]] = {}
        for i, e in enumerate(self.sc["events"]):
            if e in events:
                vis = self.feed.route(e)
                a = self.feed.alert_for(i, e, vis)
                for r in vis:
                    out.setdefault(r, []).append(a)
        return out

    def _model_alerts(self, minute: int) -> list[dict]:
        if self.detector is None:
            return []
        out = []
        for site in self.sc.get("sites") or []:
            for a in self.detector.observe(self.sim.site_history(site), site):
                vis = self.feed.route({"actor": a["source"], "signals": []})
                a = {"id": f"ML-{self.sc['id']}-{a['source']}-T{minute:03d}-{site}", "at": self.sim.ts(minute),
                     "t": minute, "actor": a["source"], "site": site, "sites": [site], "signals": [],
                     "visible_to": vis, **a}
                self.model_alerts.append(a)
                if self.world is not None:
                    self.world.alerts.append(a)
                out.append(a)
        return out

    # ------------------------------------------------------------ views
    def telemetry(self, site: str | None = None) -> list[dict]:
        return [h for h in self.sim.history if site is None or h["site"] == site]

    def measured(self, site: str, key: str, t: int) -> float | None:
        for h in self.sim.history:
            if h["site"] == site and h["t"] == t:
                return h[key]
        return None
