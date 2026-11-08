"""Stateful live-session engine for the emulated NTN control console."""
from __future__ import annotations

import datetime as dt
import json
import threading
import time
from pathlib import Path

from orca import rules
from orca.agents import Agent, EventFeed, PolicyMockLLM, load_agent_roles
from orca.audit import AuditLog
from orca.remediation import Refused, Remediation
from orca.sim import attacks
from orca.sim.engine import Simulator
from orca.sim.netops import attach, check_path_clean
from orca.sim.netstate import NetState
from orca.sim.scenario import load_scenario
from orca.sim.topology import GATEWAYS, SITES
from orca.world import World

from .bus import EventBus
from .impact import Impact
from .inject import INJECTORS, apply as apply_injector, catalogue as injector_catalogue


class LiveSession:
    """One recorded, fully emulated control-room session.

    This class owns the mutable simulation and is intentionally the only object exposed to
    the HTTP handlers.  Every mutating public method takes the same guarded remediation
    path used by batch runs; it never operates a real network.
    """
    tick_seconds = 2.0

    def __init__(self, scenario: str = "s1", llm: str = "mock", rules_enabled: bool = True,
                 kb: str = "india", autoplay: bool = False, sync: bool = True, speed: float = 1.0,
                 runs_dir: str | Path = "runs", pin_sha256: str | None = None):
        self.lock = threading.RLock()
        self.bus = EventBus()
        self.running = False
        self.closed = False
        self._thread: threading.Thread | None = None
        self._last_audit_seq = 0
        self._detected: dict[tuple[str, str], tuple[int, float]] = {}
        self.scheduled: list[dict] = []
        self._schedule_seq = 0
        self.injections: list[dict] = []
        self.detection_times: dict[str, int] = {}
        self.contained_at: dict[str, int | None] = {}
        self.healed_at: dict[str, int | None] = {}
        self.phases: dict[str, int] = {}
        self.speed = self._valid_speed(speed)
        self.sync = bool(sync)
        self.autoplay = bool(autoplay)
        self.llm_mode = llm
        self.rules_enabled = bool(rules_enabled)
        self.kb_name = "eu" if kb == "eu" else "india"
        self._new(scenario, pin_sha256, runs_dir)

    # ---------------------------------------------------------------- session lifecycle
    def _new(self, scenario: str, pin_sha256: str | None, runs_dir: str | Path) -> None:
        self.scenario = load_scenario(scenario)
        self.scenario_name = str(self.scenario["id"]).lower()
        # Live control covers the whole emulated Chennai topology, not just the sites named by
        # a scripted scenario fixture.
        self.sim = Simulator(seed=self.scenario.get("seed", 0), start=str(self.scenario["start"]))
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        mode = "rules" if self.rules_enabled else "norules"
        path = Path(runs_dir) / f"live-{stamp}-{self.scenario_name}-{mode}-{self.llm_mode}.jsonl"
        facts = {"now": self.sim.ts(0), "jurisdiction": "EU" if self.kb_name == "eu" else "IN",
                 "entity": self.scenario.get("entity", {}), "classifications": [], "triggers": {}}
        self.world = World(facts=facts, audit=AuditLog(path))
        self.world.routes = {site: {path: {"gateway": route["gateway"],
                                            "integrity": route.get("integrity", "verified")}
                                    for path, route in paths.items()}
                             for site, paths in self.sim.routes.items()}
        self.world.active_path = {site: state.active_path for site, state in self.sim.state.items()}
        self.net = NetState.load()
        attach(self.world, self.net, self.sim)
        self.rem = Remediation(self.world, pin_sha256=pin_sha256)
        self.roles = load_agent_roles()
        if not self.rules_enabled:
            for role in self.roles.values():
                role.tools = [tool for tool in role.tools if tool != "run_rule_engine"]
        self.feed = EventFeed(self.scenario, self.roles)
        self.agents = {name: Agent(role, self.world, PolicyMockLLM(), self.rem) for name, role in self.roles.items()}
        self.impact, self.shadow = Impact(), Impact()
        self.recording = path
        self.world.log("run_meta", "system", {"scenario": self.scenario_name, "rules": self.rules_enabled,
                                                 "kb": self.kb_name, "llm": self.llm_mode, "emulated": True})
        self._flush_audit()
        self.emit("session", scenario=self.scenario_name, title=self.scenario.get("title", ""),
                  story=self.scenario.get("story", ""), start=str(self.scenario["start"]), llm=self.llm_mode,
                  rules=self.rules_enabled, kb=self.kb_name, autoplay=self.autoplay, sync=self.sync,
                  speed=self.speed, emulated=True)

    def restart(self, **opts) -> dict:
        with self.lock:
            old = self.recording
            # Stop the old clock before replacing its state.  The clock reads attributes
            # from this object, so merely flipping ``closed`` and immediately reinitialising
            # would let it resume against the new session and create duplicate ticks.
            self.close()
            self.__init__(scenario=opts.get("scenario", self.scenario_name), llm=opts.get("llm", self.llm_mode),
                          rules_enabled=opts.get("rules", self.rules_enabled), kb=opts.get("kb", self.kb_name),
                          autoplay=opts.get("autoplay", self.autoplay), sync=opts.get("sync", self.sync),
                          speed=opts.get("speed", self.speed), runs_dir=old.parent)
            return {"ok": True, "recording": str(self.recording), "previous_recording": str(old)}

    def close(self) -> None:
        self.running = False
        self.closed = True
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)

    # ---------------------------------------------------------------- events and state
    def emit(self, event_kind: str, audience: str | None = None, **payload) -> dict:
        # ``kind`` is reserved for the stream discriminator.  Injection metadata is retained
        # as ``injector`` so clients can distinguish ``kind: inject`` from its catalogue id.
        if "kind" in payload:
            payload["injector"] = payload.pop("kind")
        e = {"t": max(self.sim.t, 0), "ts": self.sim.ts(max(self.sim.t, 0)), "kind": event_kind, **payload}
        if audience:
            e["audience"] = audience
        return self.bus.emit(e)

    def _flush_audit(self) -> None:
        for entry in self.world.audit.entries()[self._last_audit_seq:]:
            self._last_audit_seq = entry["seq"]
            p, kind = dict(entry["payload"]), entry["kind"]
            mapped = {"msg_sent": "msg", "msg_rejected": "msg", "approval_requested": "approval",
                      "approved": "approval", "rejected": "approval", "executed": "execute",
                      "execute_refused": "execute", "rolled_back": "rollback", "autonomy_set": "autonomy",
                      "autonomy_downgraded": "autonomy", "kill_switch": "kill",
                      "kill_switch_released": "kill"}.get(kind, kind)
            # Audit payloads for injection scheduling use ``kind`` for the catalogue
            # id.  Preserve the stream discriminator and expose that id as ``injector``.
            if mapped in ("inject", "scheduled") and "kind" in p:
                p["injector"] = p.pop("kind")
            event = {"t": max(self.sim.t, 0), "ts": entry["ts"], "kind": mapped, "audit_kind": kind,
                     "actor": entry["actor"], **p}
            if mapped in ("inject", "scheduled"):
                event["audience"] = "control"
            if kind == "approval_requested":
                event["status"] = "requested"
            elif kind == "approved":
                event["status"] = "approved"
            elif kind == "rejected":
                event["status"] = "rejected"
            elif kind == "execute_refused":
                event.update(result="refused", why=p.get("reason"))
            elif kind == "executed":
                event.update(result="ok" if p.get("ok", True) else "refused", why=p.get("detail"))
            elif kind == "kill_switch":
                event["engaged"] = True
            elif kind == "kill_switch_released":
                event["engaged"] = False
            self.bus.emit(event)

    def state(self) -> dict:
        with self.lock:
            return {"ok": True, "session": self._session_meta(), "t": self.sim.t, "running": self.running,
                    "sites": self._site_state(self.sim.history[-len(self.sim.sites):]), "scheduled": list(self.scheduled),
                    "phases": self._phase_state(),
                    "impact": {"real": self.impact.snapshot(max(self.sim.t, 0)), "shadow": self.shadow.snapshot(max(self.sim.t, 0))},
                    "autonomy": self._autonomy_state(), "recording": str(self.recording), "last_seq": len(self.bus.all())}

    def _session_meta(self) -> dict:
        return {"scenario": self.scenario_name, "llm": self.llm_mode, "rules": self.rules_enabled,
                "kb": self.kb_name, "autoplay": self.autoplay, "sync": self.sync, "speed": self.speed,
                "emulated": True}

    @staticmethod
    def _valid_speed(speed) -> float:
        value = float(speed)
        if value not in (0.5, 1, 2, 5, 10):
            raise ValueError("speed must be one of 0.5, 1, 2, 5, 10")
        return value

    # ---------------------------------------------------------------- clock and injection
    def clock(self, action: str, speed: float | None = None) -> dict:
        with self.lock:
            if speed is not None:
                self.speed = self._valid_speed(speed)
            if action == "play":
                self.running = True
                if self._thread is None or not self._thread.is_alive():
                    self._thread = threading.Thread(target=self._clock_loop, daemon=True, name="orca-live-clock")
                    self._thread.start()
            elif action == "pause":
                self.running = False
            elif action == "step":
                self.tick()
            else:
                raise ValueError("action must be play, pause, or step")
            return {"ok": True, "running": self.running, "speed": self.speed, "t": self.sim.t}

    def _clock_loop(self) -> None:
        while not self.closed:
            if not self.running:
                time.sleep(0.05)
                continue
            time.sleep(self.tick_seconds / self.speed)
            if self.running:
                self.tick()

    def inject(self, kind: str, target: str | None = None, duration_min: int = 10, params: dict | None = None,
               by: str = "human:commander", start: int | None = None) -> dict:
        with self.lock:
            at = self.sim.t + 1 if start is None else int(start)
            applied = apply_injector(self.sim, kind, target, at, duration_min, params)
            iid = f"INJ-{len(self.injections) + 1:03d}"
            item = {"id": iid, "by": by, "params": dict(params or {}), **applied}
            self.injections.append(item)
            self.contained_at[iid], self.healed_at[iid] = None, None
            # Ground truth belongs in the tamper-evident exercise record, but never in an
            # agent feed.  ``_flush_audit`` marks its derived stream event control-only.
            self.world.log("inject", by, self._public_injection(item))
            self._flush_audit()
            return {"ok": True, "injection": self._public_injection(item)}

    def schedule(self, kind: str, target: str | None, at_t: int, duration_min: int, params: dict | None = None) -> dict:
        with self.lock:
            if kind not in INJECTORS or int(at_t) <= self.sim.t:
                raise ValueError("schedule needs a known kind and a future sim minute")
            self._schedule_seq += 1
            item = {"id": f"SCH-{self._schedule_seq:03d}", "kind": kind, "target": target,
                    "at_t": int(at_t), "duration_min": int(duration_min), "params": dict(params or {})}
            self.scheduled.append(item)
            self.world.log("scheduled", "human:commander", item)
            self._flush_audit()
            return {"ok": True, "scheduled": item}

    def delete_schedule(self, schedule_id: str) -> dict:
        with self.lock:
            before = len(self.scheduled)
            self.scheduled = [s for s in self.scheduled if s["id"] != schedule_id]
            if len(self.scheduled) == before:
                raise ValueError("unknown schedule")
            return {"ok": True, "id": schedule_id}

    def tick(self) -> dict:
        with self.lock:
            due = [s for s in self.scheduled if s["at_t"] == self.sim.t + 1]
            self.scheduled = [s for s in self.scheduled if s not in due]
            for s in due:
                self.inject(s["kind"], s["target"], s["duration_min"], s["params"], by="schedule", start=s["at_t"])
            recs = self.sim.step()
            self.world.facts["now"] = self.sim.ts(self.sim.t)
            sites = self._site_state(recs)
            self.emit("tick", sites=sites, gateways=self._gateways(), paths=self._paths())
            self._detect(recs)
            self._run_due_scenario_events()
            self._update_impact(recs)
            if self.sim.t % 5 == 0:
                self.world.log("net_state", "system", {"sites": sites, "gateways": self._gateways()})
            self._flush_audit()
            self.emit("phase", **self._phase_state())
            return {"ok": True, "t": self.sim.t}

    # ---------------------------------------------------------------- detection, routing and actions
    def _detect(self, recs: list[dict]) -> None:
        for r in recs:
            label = r["label"]
            if label == "normal":
                continue
            confidence = 0.95 if label.startswith("attack") else 0.9
            active = [c for c in self.sim.conditions if c.active(self.sim.t) and c.site in (r["site"], None)]
            confidence = min([confidence, *[float(c.params.get("confidence", confidence)) for c in active]])
            key, old = (r["site"], label), self._detected.get((r["site"], label))
            if old and self.sim.t - old[0] < 5 and confidence - old[1] <= .2:
                continue
            self._detected[key] = (self.sim.t, confidence)
            source = "M3" if label != "normal" else "M1"
            signals = self._signals_for(label, r)
            visible = self.feed.route({"actor": source, "signals": signals})
            alert = {"id": f"LIVE-{source}-{r['site']}-{self.sim.t:04d}", "source": source, "site": r["site"],
                     "sites": [r["site"]], "label": label, "confidence": confidence, "signals": signals,
                     "detail": f"{source} classifies an emulated {label} condition at {r['site']}",
                     "visible_to": visible, "explain": {"top_features": self._top_features(r)}}
            self.world.alerts.append(alert)
            self.emit("model", model=source, site=r["site"], **{"class": label, "confidence": confidence,
                      "top_features": self._top_features(r), "text": alert["detail"]})
            self.emit("alert", id=alert["id"], source=source, site=r["site"], label=label,
                      visible_to=visible, text=alert["detail"])
            for inj in self.injections:
                if inj["truth_class"] == label and inj["id"] not in self.detection_times:
                    self.detection_times[inj["id"]] = self.sim.t
            self.world.facts["classifications"] = [{"at": self.world.now,
                                                       "label": "attack" if label.startswith("attack") else "fault"}]
            self.world.facts["triggers"] = {"noticing": self.world.now, "awareness": self.world.now,
                                              "occurrence": self.world.now}
            self.world.facts["applies"] = [r["record"] for r in rules.load_rules(self.world.facts["jurisdiction"])
                                            .get("deadline_rules", [])]
            self._agent_turns(visible, alert)
            self._run_rules()
            if label == "attack-management-plane":
                self._request_plan("satellite_operator", "PB-01", ["noc-vendor-7"], {}, "Contain the emulated management intrusion")
            elif label == "attack-jamming":
                lure = any(c.kind == "jamming" and c.params.get("lure") for c in active)
                path = "C" if lure else "B"
                self._request_plan("mobile_operator", "PB-06", [r["site"]], {"path": path},
                                   "Assess the offered backup path before any emulated failover")
            if label.startswith("attack"):
                self.phases["contain"] = self.sim.t
            elif label.startswith("fault"):
                self.phases["predict"] = self.sim.t

    def _agent_turns(self, roles: list[str], alert: dict) -> None:
        for role in roles:
            self.emit("agent_busy", role=role, busy=True, queue=1)
            try:
                result = self.agents[role].run(f"Assess alert {alert['id']} at {alert['site']}.")
                self.emit("agent_final", role=role, text=result.get("text", "")[:2048], citations=result.get("citations", {}).get("accepted", []))
            except Exception as exc:  # a UI stream must survive one model/role failure
                self.emit("error", where=f"agent:{role}", message=str(exc)[:240])
            finally:
                self.emit("agent_busy", role=role, busy=False, queue=0)

    def _request_plan(self, owner: str, playbook: str, targets: list[str], params: dict, reason: str) -> None:
        try:
            if any(p["playbook"] == playbook and p["owner"] == owner and p["targets"] == targets
                   and p["params"] == params and not p.get("executed") for p in self.rem.plans.values()):
                return
            plan = self.rem.request_approval(owner, playbook, targets, params, reason)
            if plan.get("auto_token"):
                self._execute(owner, plan, plan["auto_token"])
        except Refused as exc:
            self.emit("error", where="request_approval", message=str(exc))
        self._flush_audit()

    def _execute(self, owner: str, plan: dict, token: str) -> dict:
        try:
            result = self.rem.execute(owner, plan["playbook"], plan["targets"], plan["params"], token)
            if result.get("ok"):
                if plan["playbook"] == "PB-06":
                    for site in plan["targets"]:
                        check = check_path_clean(site, plan["params"]["path"], self.net, self.sim)
                        self.emit("heal", site=site, from_path="A", to_path=plan["params"]["path"], check=check)
                        self.phases["heal"] = self.sim.t
                        for inj in self.injections:
                            if site in inj.get("sites", []) and self.healed_at.get(inj["id"]) is None:
                                self.healed_at[inj["id"]] = self.sim.t
                if plan["playbook"] == "PB-01":
                    # Account containment buys time; the fuller management hardening remains a
                    # separately approved, staged patch rather than an implicit escalation.
                    self._request_plan("satellite_operator", "PB-11", ["SAT-MGMT"], {"ticket": "live-containment"},
                                       "Stage credential rotation and MFA after account containment")
                if plan["playbook"] in ("PB-11", "PB-12", "PB-13", "PB-14"):
                    self.phases["fix"] = self.sim.t
                    for stage in result.get("stages", []):
                        self.emit("patch_stage", playbook=plan["playbook"], pct=stage["pct"],
                                  health="ok" if stage["healthy"] else "fail")
                    for attack in attacks.reattacks_for(self.net, plan["playbook"], plan["targets"]):
                        self.emit("reattack", playbook=plan["playbook"], attack=attack["attack"], blocked=not attack["succeeded"])
                for inj in self.injections:
                    if inj["truth_class"].startswith("attack") and self.contained_at.get(inj["id"]) is None:
                        self.contained_at[inj["id"]] = self.sim.t
            return result
        except Refused as exc:
            self.emit("execute", hash=plan["hash"], playbook=plan["playbook"], targets=plan["targets"], result="refused", why=str(exc))
            return {"ok": False, "error": str(exc)}
        finally:
            self._flush_audit()

    def _run_rules(self) -> None:
        if not self.rules_enabled:
            return
        try:
            for verdict in rules.evaluate(self.world.facts, self.world.kb):
                v = verdict.to_dict()
                self.world.log("verdict", "rules", v)
                self.emit("verdict", verdict=v["verdict"], rule=v["rule_id"], topic=v["topic"],
                          records=v["record_ids"], gap_id=v.get("gap_id"), explanation=v["explanation"])
                if v.get("deadline"):
                    self.emit("clock_obligation", regime=v["rule_id"], started_at=self.world.now,
                              due_at=v["deadline"], status="open", trigger="awareness")
                    self.phases["report"] = self.sim.t
        except Exception as exc:
            self.emit("error", where="rules", message=str(exc)[:240])

    def _run_due_scenario_events(self) -> None:
        if not self.autoplay:
            return
        for e in self.scenario.get("events", []):
            if e.get("t") != self.sim.t:
                continue
            for signal in e.get("signals", []):
                site, sig, value = signal.get("site"), signal.get("signal"), signal.get("value")
                if sig == "vpn_login":
                    self.sim.add("mgmt_intrusion", site, start=self.sim.t)
                elif sig == "rain_mm_h" and value:
                    self.sim.add("rain", site, start=self.sim.t, peak=float(value))

    # ---------------------------------------------------------------- commands
    def autonomy(self, mode: str, sites, playbooks, minutes: int, pin: str, by: str = "commander") -> dict:
        with self.lock:
            grant = self.rem.set_mode(mode, by, pin, int(minutes), sites or "*", playbooks or "*")
            self._flush_audit()
            return {"ok": True, "grant": grant}

    def approve(self, plan_hash: str, pin: str, by: str = "commander") -> dict:
        with self.lock:
            token = self.rem.approve(plan_hash, by, pin)
            plan = self.rem.plans[plan_hash]
            result = self._execute(plan["owner"], plan, token)
            self._flush_audit()
            return {"ok": bool(result.get("ok")), "result": result}

    def reject(self, plan_hash: str, reason: str, by: str = "commander") -> dict:
        with self.lock:
            self.rem.reject(plan_hash, by, reason)
            self._flush_audit()
            return {"ok": True}

    def kill(self, pin: str, reason: str, by: str = "commander") -> dict:
        with self.lock:
            self.rem.kill(by, pin, reason)
            self._flush_audit()
            return {"ok": True}

    def release_kill(self, pin: str, by: str = "commander") -> dict:
        with self.lock:
            self.rem.release_kill(by, pin)
            self._flush_audit()
            return {"ok": True}

    def order(self, to: str, text: str) -> dict:
        if to not in self.agents:
            raise ValueError("unknown role")
        with self.lock:
            self.emit("agent_task", role=to, task=text)
            self._agent_turns([to], {"id": "ORDER", "site": None})
            return {"ok": True}

    def ask(self, to: str, question: str) -> dict:
        return self.order(to, question)

    def set_rules(self, on: bool) -> dict:
        self.rules_enabled = bool(on)
        return {"ok": True, "rules": self.rules_enabled}

    def set_kb(self, kb: str) -> dict:
        if kb not in ("india", "eu"):
            raise ValueError("kb must be india or eu")
        self.kb_name, self.world.facts["jurisdiction"] = kb, "EU" if kb == "eu" else "IN"
        if kb == "eu":
            self.world.facts["obligation_questions"] = [{"id": "LIVE-EU-REPORT", "topic": "incident_reporting",
                                                           "text": "Which incident-reporting obligation applies?"}]
        return {"ok": True, "kb": kb}

    def decide_gap(self, gap_id: str, decision: str, pin: str, by: str = "commander") -> dict:
        # PIN validation through the guarded human-side API, without altering the KB.
        self.rem._check_pin(by, pin)
        if decision not in ("confirm", "reject"):
            raise ValueError("decision must be confirm or reject")
        self.world.log("gap_human_decision", f"human:{by}", {"draft_id": gap_id, "decision": decision})
        self._flush_audit()
        return {"ok": True}

    # ---------------------------------------------------------------- views
    def catalogue(self) -> dict:
        return {"ok": True, "scenarios": [{"id": self.scenario_name, "title": self.scenario.get("title", "")}],
                "sites": SITES, "gateways": GATEWAYS, "accounts": ["noc-vendor-7"],
                "playbooks": list(self.rem.cat.values()), "injectors": injector_catalogue()}

    def truth(self) -> dict:
        rows = []
        for i in self.injections:
            rows.append({"id": i["id"], "kind": i["kind"], "target": i["target"], "truth_class": i["truth_class"],
                         "start": i["start"], "end": i["end"], "detected_at": self.detection_times.get(i["id"]),
                         "time_to_detect": self._elapsed(i["id"], self.detection_times.get(i["id"])),
                         "contained_at": self.contained_at.get(i["id"]), "time_to_contain": self._elapsed(i["id"], self.contained_at.get(i["id"])),
                         "healed_at": self.healed_at.get(i["id"]), "time_to_heal": self._elapsed(i["id"], self.healed_at.get(i["id"]))})
        return {"ok": True, "injections": rows}

    def _elapsed(self, iid: str, end: int | None) -> int | None:
        if end is None:
            return None
        return max(0, end - next(i["start"] for i in self.injections if i["id"] == iid))

    def _public_injection(self, item: dict) -> dict:
        return {k: item[k] for k in ("id", "kind", "label", "target", "start", "end", "by", "truth_class")
                if k in item}

    def _site_state(self, records: list[dict]) -> dict:
        out = {}
        for r in records:
            state = "down" if r["packet_loss"] > .8 else "degraded" if r["packet_loss"] > .15 else "ok"
            if self.sim.state[r["site"]].active_path != "A":
                state = "healing" if state != "down" else state
            out[r["site"]] = {k: r[k] for k in ("active_path", "gateway", "snr_db", "link_margin_db", "packet_loss",
                                                   "battery_pct", "mains_power", "terminals_up", "traffic_load", "txn_success")}
            out[r["site"]]["state"] = state
        return out

    def _gateways(self) -> dict:
        return {g: "down" if not self.sim.gateway_up.get(g, True) else "up" for g in GATEWAYS}

    def _paths(self) -> list[dict]:
        return [{"site": s, "path": p, "gateway": r["gateway"], "integrity": r.get("integrity", "unverified"),
                 "active": self.sim.state[s].active_path == p} for s, paths in self.sim.routes.items() for p, r in paths.items()]

    @staticmethod
    def _signals_for(label: str, r: dict) -> list[dict]:
        if label == "attack-management-plane":
            return [{"site": r["site"], "signal": "mgmt_command", "value": r["mgmt_cmds"]}]
        if label == "attack-jamming":
            return [{"site": r["site"], "signal": "snr_db", "value": r["snr_db"]}]
        if label == "fault-weather":
            return [{"site": r["site"], "signal": "rain_mm_h", "value": r["rain_mm_h"]}]
        if label == "fault-power/equipment":
            return [{"site": r["site"], "signal": "mains_power", "value": r["mains_power"]}]
        return []

    @staticmethod
    def _top_features(r: dict) -> list[dict]:
        return [{"name": "packet_loss", "value": r["packet_loss"]}, {"name": "snr_db", "value": r["snr_db"]},
                {"name": "mgmt_cmds", "value": r["mgmt_cmds"]}]

    def _update_impact(self, recs: list[dict]) -> None:
        real = self.impact.update(recs, self.sim.t)
        # The shadow deliberately cannot receive a remediation outcome.  It uses the same telemetry
        # until a heal/contain changes the real sim, then keeps the worse loss for conservative comparison.
        shadow_records = [dict(r, packet_loss=max(r["packet_loss"], .85 if any(i["truth_class"].startswith("attack") for i in self.injections) else r["packet_loss"]),
                               txn_success=min(r["txn_success"], .15 if any(i["truth_class"].startswith("attack") for i in self.injections) else r["txn_success"])) for r in recs]
        shadow = self.shadow.update(shadow_records, self.sim.t)
        self.emit("impact", real=real, shadow=shadow)

    def _phase_state(self) -> dict:
        active = [p for p, t in self.phases.items() if self.sim.t - t <= 5]
        return {"active": active, "latest": max(active, key=lambda p: self.phases[p]) if active else None}

    def _autonomy_state(self) -> dict:
        mode, grant = self.rem.mode_for("PB-06", ["CHN-02"])
        return {"mode": mode, "killed": bool(self.rem.killed), "expires_at": grant.get("expires") if grant else None}
