"""Stateful live-session engine for the emulated NTN control console."""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import threading
import time
import uuid
from collections import deque
from functools import lru_cache
from pathlib import Path

from orca import rules
from orca.agents import Agent, EventFeed, PolicyMockLLM, Role, _merge_facts, all_roles, load_agent_roles
from orca.llm import LLMClient
from orca.audit import AuditLog
from orca.models.detector import Detector
from orca.protocol import COMMANDER, Message, Protocol
from orca.remediation import Refused, Remediation
from orca.sim import attacks
from orca.sim.engine import Simulator
from orca.sim.netops import _devices as netops_devices, attach, check_path_clean
from orca.sim.netstate import NetState, unified
from orca.sim.engine import CLASS_OF
from orca.sim.service import PUBLIC_SERVICE_KEY, allocation_error, totals as svc_totals
from orca.sim.scenario import SCEN_DIR, ScenarioRun, load_scenario
from orca.sim.topology import GATEWAYS, INDIAN_GATEWAYS, PRIORITY, SITES
from orca.world import World

from .bus import EventBus
from .impact import Impact
from .inject import INJECTORS, apply as apply_injector, catalogue as injector_catalogue
from .model_config import ModelConfig


@lru_cache(maxsize=1)
def _trained_models() -> dict:
    from orca.models.train import CACHE, load_or_train

    if not CACHE.is_file():
        print("M1-M3 model cache is missing; training the full synthetic models before starting the live engine.",
              file=sys.stderr, flush=True)
    return load_or_train()


class LiveSession:
    """One recorded, fully emulated control-room session.

    This class owns the mutable simulation and is intentionally the only object exposed to
    the HTTP handlers.  Every mutating public method takes the same guarded remediation
    path used by batch runs; it never operates a real network.
    """
    tick_seconds = 2.0

    def __init__(self, scenario: str = "s1", llm: str = "mock", rules_enabled: bool = True,
                 kb: str = "india", autoplay: bool = False, sync: bool = True, speed: float = 1.0,
                 runs_dir: str | Path = "runs", pin_sha256: str | None = None,
                 model_config: ModelConfig | None = None):
        self.lock = threading.RLock()
        self.bus = EventBus()
        self.running = False
        self.closed = False
        self._thread: threading.Thread | None = None
        self._last_audit_seq = 0
        self._detected: dict[tuple[str, str, str], int] = {}
        self.detector = Detector(_trained_models())
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
        self.model_config = model_config if model_config is not None else ModelConfig()
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
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        mode = "rules" if self.rules_enabled else "norules"
        path = Path(runs_dir) / f"live-{stamp}-{self.scenario_name}-{mode}-{self.llm_mode}.jsonl"
        facts = {"now": self.sim.ts(0), "jurisdiction": "EU" if self.kb_name == "eu" else "IN",
                 "entity": self.scenario.get("entity", {}), "classifications": []}
        self.world = World(facts=facts, audit=AuditLog(path))
        self.world.routes = {site: {path: {"gateway": route["gateway"],
                                            "integrity": route.get("integrity", "verified")}
                                    for path, route in paths.items()}
                             for site, paths in self.sim.routes.items()}
        self.world.active_path = {site: state.active_path for site, state in self.sim.state.items()}
        self.net = NetState.load()
        attach(self.world, self.net, self.sim)
        self.rem = Remediation(self.world, pin_sha256=pin_sha256)
        self.proto = Protocol(self.world, load_agent_roles(), self.rem)
        self._diffs, self._appr, self._svc_hist = {}, {}, []
        self._approval_history: list[tuple[str, dict]] = []
        self._stage_fault = getattr(self, "_stage_fault", None)
        self._failures: list[dict] = []
        self._clock_ids: dict[tuple, str] = {}
        self._summary_sig, self._summary_final = None, False
        self._raw_execute = self.rem.execute
        self.rem.execute = self._observed_execute
        self.roles = load_agent_roles()
        if not self.rules_enabled:
            for role in self.roles.values():
                role.tools = [tool for tool in role.tools if tool != "run_rule_engine"]
        self.feed = EventFeed(self.scenario, self.roles)
        llm_client = PolicyMockLLM() if self.llm_mode == "mock" else LLMClient(**self.model_config.client_args())
        self.llm_source = "mock" if self.llm_mode == "mock" else llm_client.mode
        self.llm_model = "mock" if self.llm_mode == "mock" else (getattr(llm_client, "model", None)
                                                                  or os.environ.get("LLM_MODEL", "local"))
        self.agents = {name: Agent(role, self.world, llm_client, self.rem) for name, role in self.roles.items()}
        # Scripted-scenario playback reuses the batch runner's signal -> simulator mapping on this sim.
        self._scen = ScenarioRun(self.scenario, world=self.world, roles=self.roles, net=self.net)
        self._scen.sim = self.sim
        self._facts_done: set[int] = set()
        self._model_last: dict[tuple, tuple] = {}
        self._hist: dict[str, deque] = {}
        self._assessments: dict[str, dict] = {}
        self._audit_sites: dict[str, int] = {}
        self._verdict_keys: set[tuple] = set()
        self._gap_keys: set[tuple] = set()
        self._gap_ctx: dict[str, dict] = {}
        self._gap_decisions: dict[str, dict] = {}
        self._scen_applies: list[str] = []
        self._scen_questions: list[dict] = []
        self._route_offers: list[dict] = []
        self._live_offer_sites: set[str] = set()
        self._offer_sites = {sg["site"] for ev in self.scenario.get("events", []) for sg in ev.get("signals") or []
                             if sg.get("signal") == "route_candidate"}
        self.impact, self.shadow = Impact(), Impact(delivery=False)
        self.recording = path
        # Every event that goes through the bus is also appended to a sidecar, so a replay can
        # play back exactly what the live SSE client saw (the audit log lacks ticks, models, ...).
        self.stream_path = path.with_name(path.stem + ".stream.jsonl")
        self.stream_path.parent.mkdir(parents=True, exist_ok=True)
        self.stream_path.write_text("")
        self._wrap_bus_emit()
        self.world.log("run_meta", "system", {"scenario": self.scenario_name, "rules": self.rules_enabled,
                                                 "kb": self.kb_name, "llm": self.llm_mode, "emulated": True})
        self._flush_audit()
        self.emit("session", scenario=self.scenario_name, title=self.scenario.get("title", ""),
                  story=self.scenario.get("story", ""), start=str(self.scenario["start"]), llm=self.llm_mode, llm_model=self.llm_model, llm_source=self.llm_source,
                  rules=self.rules_enabled, kb=self.kb_name, autoplay=self.autoplay, sync=self.sync,
                  speed=self.speed, emulated=True)
        self.emit("autonomy", **self._autonomy_state(), initial=True)

    def _wrap_bus_emit(self) -> None:
        bus, sink, lock = self.bus, self.stream_path, threading.Lock()
        original = bus.emit

        def emit(event: dict) -> dict:
            item = original(event)
            with lock, sink.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(item, default=str, separators=(",", ":")) + "\n")
                fh.flush()
            return item

        bus.emit = emit

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
                          speed=opts.get("speed", self.speed), runs_dir=old.parent,
                          pin_sha256=opts.get("pin_sha256", self.rem.pin_sha256), model_config=self.model_config)
            return {"ok": True, "recording": str(self.recording), "stream": str(self.stream_path), "previous_recording": str(old)}

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
                      "kill_switch_released": "kill", "inject_stopped": "inject_stop"}.get(kind, kind)
            # Audit payloads for injection scheduling use ``kind`` for the catalogue
            # id.  Preserve the stream discriminator and expose that id as ``injector``.
            if mapped in ("inject", "scheduled", "inject_stop") and "kind" in p:
                p["injector"] = p.pop("kind")
            event = {"t": max(self.sim.t, 0), "ts": entry["ts"], "kind": mapped, "audit_kind": kind,
                     "actor": entry["actor"], **p}
            if kind == "verdict":
                event["rule"] = event.pop("rule_id", event.get("rule"))
                event["records"] = event.pop("record_ids", event.get("records", []))
            if mapped == "approval" and not event.get("hash") and p.get("plan_hash"):
                # Stream consumers key request and decision by the same plan hash.
                # The original hash-chained audit payload is left untouched.
                event["hash"] = p["plan_hash"]
            if mapped in ("inject", "scheduled", "inject_stop"):
                event["audience"] = "control"
            if kind in ("executed", "rolled_back", "execute_refused"):
                self._attach_diffs(event, p)
            if kind in ("approval_requested", "approved") and p.get("plan_hash", p.get("hash")):
                h = p.get("plan_hash") or p.get("hash")
                rec = self._appr.setdefault(h, {})
                if kind == "approval_requested" and "approved" in rec:
                    self._approval_history.append((h, rec))
                    rec = self._appr[h] = {}
                rec["requested" if kind == "approval_requested" else "approved"] = {
                    "t": self.sim.t, "ts": entry["ts"], "wall": time.monotonic(),
                    "auto": str(entry["actor"]).startswith("autonomy:")}
            if kind == "approval_requested":
                event["status"] = "requested"
            elif kind == "approved":
                event["status"] = "auto" if str(entry["actor"]).startswith("autonomy:") else "approved"
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
            if kind == "rolled_back":
                event["result"] = "rolled_back"
                self.bus.emit(dict(event, kind="execute"))
            self.bus.emit(event)

    def _config_texts(self, playbook: str, targets: list[str]) -> dict[str, str | None]:
        """Config text per device; None marks a device without an emulated configuration (reported, not hidden)."""
        out: dict[str, str | None] = {}
        for device in sorted(set(netops_devices(self.net, playbook, list(targets)))):
            try:
                out[device] = self.net.text(device)
            except KeyError:
                out[device] = None
        return out

    def _diff_set(self, playbook: str, targets: list[str], before: dict[str, str]) -> list[dict]:
        rows = []
        for device, old in before.items():
            if old is None:
                rows.append({"target": device, "device": device, "before": "", "after": "", "unified": "",
                             "changed": False, "missing_config": True,
                             "warning": f"no emulated configuration for {device}; diff unavailable"})
                continue
            new = self.net.text(device)
            rows.append({"target": device, "device": device, "before": old, "after": new,
                         "unified": unified(device, old, new), "changed": old != new})
        if not rows:    # playbooks with no configuration action (e.g. a warning) change nothing
            rows = [{"target": t, "device": None, "before": "", "after": "", "unified": "", "changed": False}
                    for t in targets]
        return rows

    def _attach_diffs(self, event: dict, p: dict) -> None:
        key = (p.get("playbook"), tuple(p.get("targets") or []))
        rows = self._diffs.pop(key, None)
        if rows is None:
            rows = self._diff_set(key[0], list(key[1]), self._config_texts(key[0], list(key[1])))
        event["diffs"] = rows
        event["diff"] = next((r for r in rows if r["changed"]), rows[0] if rows else None)
        event["changed"] = any(r["changed"] for r in rows)
        rec = [n for n in p.get("network") or [] if n.get("event") == "rolled_back"]
        if rec:
            event["revert_diff"] = rec[-1].get("revert_diff", "")
            event["reason"] = rec[-1].get("reason")
            event["stage_pct"] = rec[-1].get("stage_pct")

    def _observed_execute(self, caller, playbook, targets, params, token):
        targets = list(targets)
        before = self._config_texts(playbook, targets)
        key = (playbook, tuple(targets))
        token_info = self.rem.tokens.get(token) or {}
        plan_hash = token_info.get("hash")
        try:
            result = self._raw_execute(caller, playbook, targets, params, token)
        except Refused:
            self._diffs[key] = self._diff_set(playbook, targets, before)
            raise
        self._diffs[key] = self._diff_set(playbook, targets, before)
        self._emit_rollout(playbook, result, plan_hash=plan_hash)
        if not result.get("ok") and (params or {}).get("simulate_failure_at"):
            self._failures.append({"t": self.sim.t, "playbook": playbook, "targets": targets})
            retry = {k: v for k, v in (params or {}).items() if k != "simulate_failure_at"}
            self._request_plan(caller, playbook, targets, retry, "Retry after the emulated health check rolled back")
        return result

    def _emit_rollout(self, playbook: str, result: dict, plan_hash: str | None = None) -> None:
        """Project only stage and re-attack results actually recorded by execution."""
        net = result.get("network") or []
        context = {"playbook": playbook}
        if plan_hash:
            context["plan_hash"] = plan_hash
        for stage in result.get("stages") or []:
            if not isinstance(stage, dict) or not isinstance(stage.get("pct"), (int, float)) or not isinstance(stage.get("healthy"), bool):
                continue
            rec = next((n for n in net if n.get("event") == "stage_applied" and n.get("stage_pct") == stage["pct"]), None)
            payload = {"pct": stage["pct"], "health": "ok" if stage["healthy"] else "fail"}
            if rec is not None:
                payload.update(applied=rec.get("applied", []), devices=rec.get("devices_changed", []), diff=rec.get("diff", ""))
            self.emit("patch_stage", **context, **payload)
        verified = next((n for n in net if n.get("event") == "verified"), None)
        for attack in (verified or {}).get("reattack", []):
            if not isinstance(attack, dict) or not isinstance(attack.get("succeeded"), bool) or not attack.get("attack") or not attack.get("target"):
                continue
            self.emit("reattack", **context, attack=attack["attack"], target=attack["target"],
                      blocked=not attack["succeeded"], blocked_by=attack.get("blocked_by"),
                      blocked_at=attack.get("blocked_at"))

    def arm_stage_fault(self, pct: int | None) -> dict:
        """Make the next staged patch fail its emulated health check at this stage (real rollback demo)."""
        with self.lock:
            if pct is not None and pct not in (5, 25, 100):
                raise ValueError("stage must be 5, 25 or 100")
            self._stage_fault = pct
            return {"ok": True, "stage_fault": pct}

    def state(self) -> dict:
        with self.lock:
            return {"ok": True, "session": self._session_meta(), "t": self.sim.t, "running": self.running,
                    "sites": self._site_state(self.sim.history[-len(self.sim.sites):]), "scheduled": list(self.scheduled),
                    "phases": self._phase_state(),
                    "impact": {"real": self.impact.snapshot(max(self.sim.t, 0)), "shadow": self.shadow.snapshot(max(self.sim.t, 0))},
                    "autonomy": self._autonomy_state(), "recording": str(self.recording), "last_seq": len(self.bus.all())}

    def _session_meta(self) -> dict:
        return {"scenario": self.scenario_name, "llm": self.llm_mode, "llm_model": self.llm_model, "llm_source": self.llm_source, "rules": self.rules_enabled,
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
            before = len(self.sim.conditions)
            routes_before = {site: {path: dict(route) for path, route in routes.items()}
                             for site, routes in self.sim.routes.items()}
            applied = apply_injector(self.sim, kind, target, at, duration_min, params)
            for site, routes in self.sim.routes.items():
                for path, route in routes.items():
                    if routes_before.get(site, {}).get(path) != route:
                        self._route_offers.append({"site": site, "path": path})
                        self._live_offer_sites.add(site)
            iid = f"INJ-{len(self.injections) + 1:03d}"
            item = {"id": iid, "by": by, "params": dict(params or {}), **applied,
                    "_conds": self.sim.conditions[before:]}   # kept server-side so the director can stop it
            self.injections.append(item)
            self.contained_at[iid], self.healed_at[iid] = None, None
            # Ground truth belongs in the tamper-evident exercise record, but never in an
            # agent feed.  ``_flush_audit`` marks its derived stream event control-only.
            self.world.log("inject", by, self._public_injection(item))
            self._flush_audit()
            return {"ok": True, "injection": self._public_injection(item)}

    def running_injections(self) -> list[dict]:
        """Director-only conditions still active now or queued for the next step."""
        with self.lock:
            t = self.sim.t
            result = []
            for item in self.injections:
                conditions = item.get("_conds", [])
                if item.get("_stopped") or not any(c.end is None or c.end > t for c in conditions):
                    continue
                # Conditions may have ended early through containment. Report their actual end.
                ends = [c.end for c in conditions]
                end = None if any(value is None for value in ends) else max(ends)
                cancellable = any(c.end is None or c.end > max(c.start, t + 1) for c in conditions)
                result.append({**self._public_injection(item), "end": end,
                               "state": "pending" if t < item["start"] else "active",
                               "cancellable": cancellable})
            return result

    def stop_injection(self, injection_id: str | None = None, kind: str | None = None,
                       by: str = "human:commander") -> dict:
        """Cancel future condition effects. Prior effects and offered routes are not undone."""
        with self.lock:
            t = self.sim.t
            items = [i for i in self.injections if not i.get("_stopped")
                     and any(c.end is None or c.end > max(c.start, t + 1) for c in i.get("_conds", []))
                     and (i["id"] == injection_id if injection_id else bool(kind and i["kind"] == kind))]
            if not items:
                raise ValueError("no cancellable condition found")
            for it in items:
                for c in it["_conds"]:
                    stop_at = max(c.start, t + 1)
                    c.end = stop_at if c.end is None else min(c.end, stop_at)
                it["end"] = max(c.end for c in it["_conds"])
                it["_stopped"] = True
                self.world.log("inject_stopped", by, {"id": it["id"], "kind": it["kind"], "label": it["label"],
                                                       "target": it["target"], "end": it["end"]})
            self._flush_audit()
            return {"ok": True, "stopped": [i["id"] for i in items]}

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
            self._apply_scenario_signals(self.sim.t + 1)
            recs = self.sim.step()
            self.world.facts["now"] = self.sim.ts(self.sim.t)
            sites = self._site_state(recs)
            services = self._service_totals(recs)
            self.emit("tick", sites=sites, gateways=self._gateways(), paths=self._paths(), services=services,
                      instantaneous=True)
            self._detect(recs)
            self._apply_scenario_facts(self.sim.t)
            self._handle_route_offers(recs, sites)
            self._model_status(recs, sites)
            self._update_impact(recs)
            if self.sim.t % 5 == 0:
                self.world.log("net_state", "system", {"sites": sites, "gateways": self._gateways()})
            self._flush_audit()
            self.emit("phase", **self._phase_state())
            self._publish_summary()
            return {"ok": True, "t": self.sim.t}

    # ---------------------------------------------------------------- incident timings and summary
    SUMMARY_TAIL_MIN = 10

    @staticmethod
    def _minutes(a: str | None, b: str | None) -> float | None:
        if not a or not b:
            return None
        return round((rules.parse_ts(b) - rules.parse_ts(a)).total_seconds() / 60, 2)

    def _authority_role(self, record_id: str) -> str:
        authority = str((self.world.kb.records.get(record_id) or {}).get("authority", "")).lower()
        return "cert_in" if "cert" in authority else "regulator"

    def timings(self) -> dict:
        """Incident timings from engine events. A value that has not happened yet is None (unavailable)."""
        events = self.bus.all()
        started = [i for i in self.injections if i["start"] <= self.sim.t]
        inc = min(started, key=lambda i: i["start"]) if started else None
        start = {"t": inc["start"]} if inc else None
        start_ts = self.sim.ts(start["t"]) if start else None
        detected_t = self.detection_times.get(inc["id"]) if inc else None
        detected_at = self.sim.ts(detected_t) if detected_t is not None else None
        deadline_rules = rules.load_rules(self.world.facts["jurisdiction"]).get("deadline_rules", [])
        record_of = {r["id"]: r["record"] for r in deadline_rules}
        clocks = {}
        # Only the current evaluation epoch counts: clocks before the last kb or rules switch are
        # history (kept in the event log and audit), not the current policy view.
        epoch = max((e["seq"] for e in events if e["kind"] in ("kb_changed", "rules_changed")), default=-1)
        notices = [e for e in events if e["kind"] == "msg" and e.get("audit_kind") == "msg_sent"
                   and e["seq"] >= epoch]
        for e in events if self.rules_enabled else ():
            if e["kind"] != "clock_obligation" or e["regime"] not in record_of or e["seq"] < epoch:
                continue
            clocks[e["regime"]] = {"regime": e["regime"], "record_id": record_of[e["regime"]],   # latest wins
                                   "obligation_id": e.get("obligation_id"), "obligation_seq": e["seq"],
                                   "policy_epoch": e.get("policy_epoch", epoch),
                                   "trigger": e.get("trigger"), "started_at": e["started_at"], "due_at": e["due_at"]}
        for c in clocks.values():
            role = self._authority_role(c["record_id"])
            first = next((m for m in notices if role in (m.get("recipients") or m.get("to") or [])
                          ), None)
            c["notify_role"] = role
            c["notified_at"] = first["ts"] if first else None
            lead = self._minutes(c["started_at"], c["notified_at"])
            c["notified_before_start"] = lead is not None and lead < 0     # told before the clock's trigger time
            c["time_to_notify_min"] = None if lead is None else max(0.0, lead)
            c["window_min"] = self._minutes(c["started_at"], c["due_at"])
            c["met"] = None if first is None else rules.parse_ts(first["ts"]) <= rules.parse_ts(c["due_at"])
        approvals = []
        records = [*self._approval_history, *self._appr.items()]
        records.sort(key=lambda item: item[1].get("requested", {}).get("wall", float("inf")))
        for h, rec in records:
            if "requested" in rec and "approved" in rec:
                a, b = rec["requested"], rec["approved"]
                plan = self.rem.plans.get(h, {})
                approvals.append({"hash": h, "playbook": plan.get("playbook"), "auto": b["auto"],
                                  "latency_s": round((rules.parse_ts(b["ts"]) - rules.parse_ts(a["ts"])).total_seconds()),
                                  "latency_wall_s": round(b["wall"] - a["wall"], 2)})
        human = [a for a in approvals if not a["auto"]]
        audit = self.world.audit.entries()
        rolled = [e for e in events if e["kind"] == "rollback"]
        refused = [e for e in audit if e["kind"] == "execute_refused"]
        hist = self._svc_hist
        restore = degraded = None
        if hist and start is not None:
            base = hist[0]["pct"]
            low = [h for h in hist if h["t"] >= start["t"]]
            deg = next((h for h in low if h["pct"] < base - 1), None)
            if deg is not None:
                degraded = {"t": deg["t"], "ts": deg["ts"], "pct": deg["pct"], "baseline_pct": base}
                back = next((h for h in low if h["t"] > deg["t"] and h["pct"] >= base - 1), None)
                restore = back
        return {
            "incident_start_t": start["t"] if start else None, "incident_start_ts": start_ts,
            "time_to_detect_min": self._minutes(start_ts, detected_at),
            "detected_at": detected_at,
            "clocks": list(clocks.values()),
            "time_to_notify_min": {c["regime"]: c["time_to_notify_min"] for c in clocks.values()},
            "time_to_restore_min": self._minutes(start_ts, restore["ts"]) if restore else None,
            "degraded": degraded, "restored_at": restore["ts"] if restore else None,
            "approvals": approvals,
            "approval_latency_s": human[0]["latency_s"] if human else None,
            "approval_latency_wall_s": human[0]["latency_wall_s"] if human else None,
            "failed_attempts": len(rolled) + len(refused) if (rolled or refused or self._appr) else None,
            "failed_breakdown": {"rolled_back": len(rolled), "refused": len(refused)},
            "rollback_ok": (all(not e.get("changed") and bool(e.get("revert_diff") is not None) for e in rolled)
                            if rolled else None),
        }

    def summary(self, final: bool = False) -> dict:
        with self.lock:
            impact = self.impact.snapshot(self.sim.t)
            delivery = self.impact.delivery.summary()
            return {"final": final, "t": self.sim.t, "emulated": True, "scenario": self.scenario_name,
                    "rules": self.rules_enabled, "kb": self.kb_name, "timings": self.timings(),
                    "services": delivery["services"], "sites": delivery["sites"], "network": delivery["network"],
                    "units": {"rate": "Mbps", "volume": "Mbit", "sample_duration_s": 60},
                    "impact_cumulative": impact}

    def _publish_summary(self, force: bool = False) -> None:
        end_t = max((e["t"] for e in self.scenario.get("events", [])), default=0) + self.SUMMARY_TAIL_MIN
        final = self.autoplay and self.sim.t >= end_t and not self._summary_final
        timings = self.timings()
        sig = json.dumps(timings, sort_keys=True, default=str)
        if final or force or sig != self._summary_sig:
            self._summary_sig = sig
            if final:
                self._summary_final = True
            self.emit("summary", **self.summary(final=final))

    def finish(self) -> dict:
        with self.lock:
            self._summary_final = True
            self._summary_sig = None
            return {"ok": True, "summary": self.emit("summary", **self.summary(final=True))}

    # ---------------------------------------------------------------- detection, routing and actions
    def _detect(self, recs: list[dict]) -> None:
        self._assessments = {}
        for r in recs:
            site = r["site"]
            hist = self._hist.setdefault(site, deque(maxlen=11))
            hist.append(r)
            if len(hist) < 3:
                continue
            assessment = self.detector.assess(list(hist), site)
            if site in self._audit_sites and self.sim.t >= self._audit_sites[site]:
                assessment["m3"] = {"label": "abstain", "abstained": True, "why": [],
                                    "note": "The unprotected-link audit is outside M3's observed features; active interception is not assessed.",
                                    "provenance": "coverage_guard"}
            self._assessments[site] = assessment
            m3 = assessment["m3"]
            if m3["label"] != "normal":
                self._publish_detection(r, "M3", m3["label"], m3)
            if assessment["m1"]["anomalous"]:
                self._publish_detection(r, "M1", "anomaly", assessment["m1"])

    def _publish_detection(self, r: dict, source: str, label: str, result: dict) -> None:
        site = r["site"]
        key = (site, source, label)
        if key in self._detected and self.sim.t - self._detected[key] < 5:
            return
        self._detected[key] = self.sim.t
        signals = self._signals_for(label, r) if source == "M3" else [
            {"site": site, "signal": "snr_db", "value": r["snr_db"]},
            {"site": site, "signal": "mgmt_command", "value": r["mgmt_cmds"]},
        ]
        visible = self.feed.route({"actor": source, "signals": signals})
        detail = (f"M3 abstains at {site}; a human must assess the emulated condition" if label == "abstain"
                  else f"{source} reports {label} in observed emulated telemetry at {site}")
        alert = {"id": f"LIVE-{source}-{site}-{self.sim.t:04d}", "source": source, "site": site,
                 "sites": [site], "label": label, "signals": signals, "detail": detail, "visible_to": visible,
                 "explain": {"top_features": result.get("why", []), "note": result.get("note", "")}}
        if source == "M3":
            alert["abstained"] = bool(result.get("abstained"))
            if "confidence" in result:
                alert["confidence"] = result["confidence"]
        self.world.alerts.append(alert)
        self.emit("alert", id=alert["id"], source=source, site=site, label=label,
                  visible_to=visible, text=detail)
        if source == "M3" and label != "abstain":
            for inj in self.injections:
                matches_class = inj["truth_class"] == label or (inj["truth_class"] == "attack" and label.startswith("attack"))
                active = inj["start"] <= self.sim.t and (inj["end"] is None or self.sim.t < inj["end"])
                if matches_class and active and (not inj["sites"] or site in inj["sites"]) and inj["id"] not in self.detection_times:
                    self.detection_times[inj["id"]] = self.sim.t
            category = "attack" if label.startswith("attack") else "fault"
            classifications = self.world.facts.setdefault("classifications", [])
            previous = next((entry for entry in reversed(classifications) if entry.get("site") == site), None)
            if previous is None or previous["label"] != category:
                classifications.append({"at": self.world.now, "site": site, "label": category})
            if category == "attack":
                triggers = self.world.facts.setdefault("triggers", {})
                triggers.setdefault("noticing", self.world.now)
                triggers.setdefault("awareness", self.world.now)
        self._agent_turns(visible, alert)
        self._run_rules()
        if source == "M3" and label == "abstain":
            self.rem.mode_for("PB-06", [site])
        elif source == "M3" and label == "attack-management-plane" and not self.sim.mgmt_contained:
            self._request_plan("satellite_operator", "PB-01", ["noc-vendor-7"], {}, "Contain the emulated management intrusion")
        elif (source == "M3" and label == "attack-jamming"
              and not (self.autoplay and site in self._offer_sites) and site not in self._live_offer_sites):
            self._request_plan("mobile_operator", "PB-06", [site], {"path": "B"},
                               "Assess the backup path before any emulated failover")
        if source == "M3" and label.startswith("attack"):
            self.phases["contain"] = self.sim.t
        elif source == "M1" or label.startswith("fault"):
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
            if self._stage_fault and playbook in ("PB-11", "PB-12", "PB-13", "PB-14"):
                params = {**params, "simulate_failure_at": self._stage_fault}
                self._stage_fault = None
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
                for inj in self.injections:
                    if inj["truth_class"].startswith("attack") and self.contained_at.get(inj["id"]) is None:
                        self.contained_at[inj["id"]] = self.sim.t
            return result
        except Refused as exc:
            return {"ok": False, "error": str(exc)}
        finally:
            self._flush_audit()

    def _run_rules(self) -> None:
        if not self.rules_enabled:
            return
        try:
            for verdict in rules.evaluate(self.world.facts, self.world.kb):
                v = verdict.to_dict()
                vkey = (v["rule_id"], v["verdict"], v.get("gap_id"), v.get("topic"), v.get("deadline"))
                if vkey in self._verdict_keys:
                    continue
                self._verdict_keys.add(vkey)
                self.world.log("verdict", "rules", v)
                self.emit("verdict", verdict=v["verdict"], rule=v["rule_id"], topic=v["topic"],
                          records=v["record_ids"], gap_id=v.get("gap_id"), explanation=v["explanation"])
                if v.get("gap_id"):
                    self._emit_gap(v["gap_id"], v)
                if v.get("deadline") and v.get("trigger") and v.get("starts"):   # a deadline rule, not a clock group
                    epoch = max((e["seq"] for e in self.bus.all()
                                 if e["kind"] in ("kb_changed", "rules_changed")), default=-1)
                    self.emit("clock_obligation", regime=v["rule_id"], started_at=v["starts"],
                              due_at=v["deadline"], status="open", trigger=v["trigger"], records=v["record_ids"],
                              obligation_id=self._clock_ids.setdefault((epoch, v["rule_id"], v["starts"], v["deadline"]), uuid.uuid4().hex), policy_epoch=epoch)
                    self.phases["report"] = self.sim.t
        except Exception as exc:
            self.emit("error", where="rules", message=str(exc)[:240])

    def _emit_gap(self, gap_id: str, verdict: dict | None = None, force: bool = False) -> None:
        """Emit the gap a verdict cites, from the KB gap register; a gap not yet registered is a
        candidate carrying only what the verdict itself says. A human decision overlays the status."""
        if verdict:
            self._gap_ctx[gap_id] = {"verdict": verdict["verdict"], "rule": verdict["rule_id"],
                                     "records": verdict["record_ids"], "topic": verdict.get("topic"),
                                     "explanation": verdict["explanation"]}
        ctx = self._gap_ctx.get(gap_id, {})
        g = self.world.kb.gaps.get(gap_id)
        dec = self._gap_decisions.get(gap_id)
        status = ({"confirm": "confirmed", "reject": "rejected"}[dec["decision"]] if dec
                  else (g.get("status") if g else "candidate"))
        if not force and (gap_id, status) in self._gap_keys:
            return
        self._gap_keys.add((gap_id, status))
        if g:
            body = {"title": g.get("title"), "topic": g.get("topic"), "jurisdiction": g.get("jurisdiction"),
                    "gap_kind": g.get("kind"), "finding": g.get("finding"), "evidence": g.get("evidence", []),
                    "affects": g.get("affects", []), "global_examples": g.get("global_examples", []),
                    "recommendation": g.get("recommendation"), "interim_action": g.get("interim_action"),
                    "verified": bool(g.get("verified")), "verified_by": g.get("verified_by"), "source": "register"}
        else:
            body = {"title": f"Candidate gap: {ctx.get('topic')}", "topic": ctx.get("topic"),
                    "jurisdiction": self.world.facts["jurisdiction"], "gap_kind": None, "finding": ctx.get("explanation"),
                    "evidence": [], "affects": [], "global_examples": [], "recommendation": None,
                    "interim_action": None, "verified": False, "verified_by": None, "source": "candidate"}
        if dec:
            body.update(verified=True, verified_by=dec["by"])
        self.emit("gap", gap_id=gap_id, id=gap_id, status=status, decision=dec, records=ctx.get("records", []),
                  rule=ctx.get("rule"), verdict=ctx.get("verdict"), **body)

    M2_FLAG_MIN = 45
    ALLOCATION = ["112", "hospital", "grid", "payments"]
    SERVICE_SITE = {"hospital": "CHN-01", "payments": "CHN-02", "112": "CHN-03", "grid": "CHN-04"}

    def _apply_scenario_signals(self, minute: int) -> None:
        """Play the scenario's scripted signals at their minute (before that minute is simulated)."""
        if not self.autoplay:
            return
        for e in self.scenario.get("events", []):
            if e.get("t") != minute:
                continue
            before, obs = len(self.sim.conditions), len(self._scen.observations)
            self._scen._apply(e)
            for sig in e.get("signals") or []:
                if sig.get("signal") == "route_candidate":
                    self._route_offers.append({"site": sig["site"], "path": sig["value"]["path"]})
            for cond in self.sim.conditions[before:]:
                self._record_scripted_threat(cond)
            for o in self._scen.observations[obs:]:
                if o["link_protection"] == "unprotected":
                    self._audit_sites[o["site"]] = minute
                else:
                    self._audit_sites.pop(o["site"], None)

    def _handle_route_offers(self, recs: list[dict], sites: dict) -> None:
        """A scenario offered a backup path: ask for PB-06 if the site is hurt (the guards judge the path).

        A verified path through an Indian gateway also covers other hurt scenario sites that have the
        same clean path.  A foreign, unverified or failed offer is requested for its own site only, so
        the clean-path check refuses it where the commander can see it.
        """
        offers, self._route_offers = self._route_offers, []
        by_site = {r["site"]: r for r in recs}

        def hurt(site: str) -> bool:
            return site in sites and (sites[site]["state"] in ("degraded", "down") or not by_site[site]["mains_power"])

        def clean(site: str, path: str) -> bool:
            route = self.sim.routes.get(site, {}).get(path) or {}
            return route.get("integrity") == "verified" and route.get("gateway") in INDIAN_GATEWAYS

        for off in offers:
            site, path = off["site"], off["path"]
            if site not in self.sim.state or self.sim.state[site].active_path == path:
                continue
            if not hurt(site):
                self._route_offers.append(off)
                continue
            targets = [site]
            if clean(site, path):
                targets += [s for s in self.scenario.get("sites", []) if s != site and s in self.sim.state
                            and hurt(s) and self.sim.state[s].active_path != path and clean(s, path)]
            self._request_plan("mobile_operator", "PB-06", sorted(targets[:2]), {"path": path},
                               f"Fail over to offered backup path {path} after the scenario offered it")

    def _record_scripted_threat(self, cond) -> None:
        """Ground truth of a scripted threat: control-audience only, like a free-play injection."""
        iid = f"INJ-{len(self.injections) + 1:03d}"
        inj = INJECTORS.get(cond.kind)
        item = {"id": iid, "by": "scenario", "params": dict(cond.params), "kind": cond.kind,
                "label": inj.label if inj else cond.kind.replace("_", " "), "target": cond.site or "",
                "start": cond.start, "end": cond.end, "truth_class": CLASS_OF[cond.kind],
                "sites": [cond.site] if cond.site else [], "_conds": [cond]}
        self.injections.append(item)
        self.contained_at[iid], self.healed_at[iid] = None, None
        self.world.log("inject", "scenario", self._public_injection(item))

    def _apply_scenario_facts(self, minute: int) -> None:
        """Merge each due scenario ``facts`` block into the world facts and run the rule engine."""
        if not self.autoplay:
            return
        due = [(i, e) for i, e in enumerate(self.scenario.get("events", []))
               if e.get("t") == minute and e.get("facts") and i not in self._facts_done]
        for i, e in due:
            self._facts_done.add(i)
            facts = e["facts"]
            self._scen_applies += [a for a in facts.get("applies", []) if a not in self._scen_applies]
            self._scen_questions += [q for q in facts.get("obligation_questions", []) if q not in self._scen_questions]
            if self.world.facts["jurisdiction"] != "IN":     # the scenario's applies list names India records
                facts = {k: v for k, v in facts.items() if k != "applies"}
            _merge_facts(self.world.facts, facts)
            if "applies" in facts:
                self.world.facts["applies"] = list(dict.fromkeys(self.world.facts["applies"]))
        if due:
            self._run_rules()

    # ---------------------------------------------------------------- model status (M1, M2, M3 state, M4)
    def _emit_model(self, key: tuple, signature: tuple, heartbeat: bool, **payload) -> None:
        if heartbeat or self._model_last.get(key) != signature:
            self._model_last[key] = signature
            self.emit("model", **payload)

    def _model_status(self, recs: list[dict], sites: dict) -> None:
        heartbeat = self.sim.t % 5 == 0
        stressed = []
        for r in recs:
            site = r["site"]
            assessment = self._assessments.get(site)
            if assessment is None:
                count = len(self._hist.get(site, ()))
                for name in ("M1", "M2", "M3"):
                    self._emit_model((name, site), ("warming", count), heartbeat, model=name, site=site,
                                     state="warming", samples=count, required_samples=3,
                                     provenance="collecting_observed_telemetry")
            else:
                m1, m2, m3 = assessment["m1"], assessment["m2"], assessment["m3"]
                state = "flagged" if m1["anomalous"] else "ok"
                self._emit_model(("M1", site), (state, tuple(m1["flag_sources"])), heartbeat, model="M1", site=site,
                                 state=state, score=m1["score"], threshold=m1["threshold"],
                                 ecod_score=m1["ecod_score"], ecod_threshold=m1["ecod_threshold"],
                                 flag_sources=m1["flag_sources"], top_features=m1["why"],
                                 provenance="isolation_forest_and_ecod_synthetic")
                forecast = m2["minutes_to_failure"]
                horizon = forecast["p50"] if forecast["p50"] < m2["horizon_min"] else None
                metric = "battery" if m2["cause"] == "power" else "link_margin"
                state = "flagged" if horizon is not None and horizon <= self.M2_FLAG_MIN else "ok"
                self._emit_model(("M2", site), (state, metric), heartbeat, model="M2", site=site,
                                 horizon_min=horizon, forecast_window_min=m2["horizon_min"],
                                 forecast_p10_min=forecast["p10"], forecast_p90_min=forecast["p90"],
                                 metric=metric, state=state, provenance="lightgbm_quantile_synthetic")
                label = m3["label"]
                state = ("unsure" if label == "abstain" else "flagged" if label.startswith("attack")
                         else "fault" if label.startswith("fault") else "ok")
                extra = {key: m3[key] for key in ("confidence", "probabilities") if key in m3}
                self._emit_model(("M3", site), (state, label, m3.get("provenance")), heartbeat, model="M3", site=site,
                                 state=state, abstain=bool(m3["abstained"]), top_features=m3["why"],
                                 note=m3["note"], provenance=m3.get("provenance", "lightgbm_multiclass_synthetic"),
                                 score_kind="uncalibrated_model_probability" if "confidence" in m3 else None,
                                 **{"class": label}, **extra)
            if sites[site]["state"] in ("degraded", "down") or not r["mains_power"]:
                stressed.append(site)
        affected = [svc for svc, site in self.SERVICE_SITE.items() if site in stressed]
        allocation = (["112"] + [s for s in self.ALLOCATION if s != "112" and s in affected]
                      + [s for s in self.ALLOCATION if s != "112" and s not in affected]) if stressed else list(self.ALLOCATION)
        state = "replan" if stressed else "ok"
        plan = self.sim.m4_plan or {}
        shed = plan.get("shed", [])
        method, upstream = plan.get("method"), plan.get("solution")
        valid_result = (plan.get("status") == "ok" and
                        ((method == "milp" and upstream == "optimal") or
                         (method == "greedy" and upstream == "feasible")))
        validation = (allocation_error(plan, recs) if valid_result else
                      "The planner did not provide a successful, recognised result."
                      if method and method != "none" else None)
        valid_result = valid_result and validation is None
        solution = "feasible" if valid_result else None
        upstream = upstream if valid_result else None
        rows = self._m4_rows(plan) if valid_result else []
        self._emit_model(("M4",), (state, tuple(allocation), method, solution, upstream, plan.get("status"),
                                   validation, json.dumps(shed, sort_keys=True, default=str), json.dumps(rows, sort_keys=True)),
                         heartbeat, model="M4", allocation=rows, allocation_priority=allocation, state=state, sites=stressed,
                         method=method or "none", solution=solution, upstream_solution=upstream,
                         solver_status=plan.get("status"),
                         solution_scope="postprocessed_capacity_and_priority" if valid_result else None,
                         upstream_solution_scope="before_quantisation_closure" if valid_result else None,
                         validation_error=validation, shed=shed if valid_result else [], plan_sites=plan.get("sites", []))

    @staticmethod
    def _m4_rows(plan: dict) -> list[dict]:
        """Per site and service rows of the M4 plan: demand, granted and shed Mbps (from the planner, not recomputed)."""
        rows = []
        for site in sorted(plan.get("allocation") or {}):
            alloc = plan["allocation"][site]
            for svc in sorted(alloc, key=PRIORITY.get):
                row = alloc[svc]
                rows.append({"site": site, "service": LiveSession.SERVICE_KEY.get(svc, svc), "priority": PRIORITY[svc],
                             "demand_mbps": row["demand_mbps"], "granted_mbps": row["granted_mbps"],
                             "mbps": row["granted_mbps"], "pct": round(100 * row["served"], 1),
                             "shed_mbps": round(row["demand_mbps"] - row["granted_mbps"], 2)})
        return rows

    # ---------------------------------------------------------------- commands
    def autonomy(self, mode: str, sites, playbooks, minutes: int, pin: str = "", by: str = "commander") -> dict:
        with self.lock:
            grant = self.rem.set_mode(mode, by, pin, int(minutes), sites or "*", playbooks or "*")
            self._flush_audit()
            return {"ok": True, "grant": grant}

    def approve(self, plan_hash: str, pin: str = "", by: str = "commander") -> dict:
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

    def kill(self, pin: str = "", reason: str = "", by: str = "commander") -> dict:
        with self.lock:
            self.rem.kill(by, pin, reason)
            self._flush_audit()
            return {"ok": True}

    def release_kill(self, pin: str = "", by: str = "commander") -> dict:
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

    def notify(self, to: str, text: str, data_class: str = "operational") -> dict:
        """The human commander informs a party (for example CERT-In). Goes through the typed protocol."""
        with self.lock:
            res = self.proto.send(Message(type="inform", sender=COMMANDER, recipients=[to], text=text,
                                          data_class=data_class))
            self._flush_audit()
            if "rejected" in res:
                raise ValueError(res["rejected"])
            self._publish_summary()
            return {"ok": True, **res}

    def ask(self, to: str, question: str) -> dict:
        return self.order(to, question)

    def set_rules(self, on: bool) -> dict:
        on = bool(on)
        with self.lock:
            if on == self.rules_enabled:
                return {"ok": True, "rules": on, "changed": False}
            self.rules_enabled = on
            self._verdict_keys.clear()
            self._gap_keys.clear()
            self.emit("rules_changed", rules=on, jurisdiction=self.world.facts["jurisdiction"])
            self._run_rules()               # no-op when switched off
            self._flush_audit()
            self._publish_summary(force=True)
        return {"ok": True, "rules": on, "changed": True}

    def set_kb(self, kb: str) -> dict:
        if kb not in ("india", "eu"):
            raise ValueError("kb must be india or eu")
        with self.lock:
            if kb == self.kb_name:
                return {"ok": True, "kb": kb, "changed": False}
            previous, prev_jur = self.kb_name, self.world.facts["jurisdiction"]
            facts = self.world.facts
            self.kb_name, facts["jurisdiction"] = kb, "EU" if kb == "eu" else "IN"
            questions = list(self._scen_questions)
            if kb == "eu":
                questions.append({"id": "LIVE-EU-REPORT", "topic": "incident_reporting",
                                  "text": "Which incident-reporting obligation applies?"})
                facts.pop("applies", None)     # India record ids; the EU rules pick their own defaults
            elif self._scen_applies:
                facts["applies"] = list(self._scen_applies)
            if questions:
                facts["obligation_questions"] = questions
            else:
                facts.pop("obligation_questions", None)
            self._verdict_keys.clear()
            self._gap_keys.clear()
            self.emit("kb_changed", kb=kb, previous=previous, jurisdiction=facts["jurisdiction"],
                      previous_jurisdiction=prev_jur, kb_as_of=str(self.world.kb.as_of))
            self._run_rules()
            self._flush_audit()
            self._publish_summary(force=True)
        return {"ok": True, "kb": kb, "changed": True}

    def decide_gap(self, gap_id: str, decision: str, pin: str = "", by: str = "commander") -> dict:
        # Explicit human decision through the commander API, without altering the KB.
        self.rem._check_commander(by)
        if decision not in ("confirm", "reject"):
            raise ValueError("decision must be confirm or reject")
        if gap_id not in self.world.kb.gaps and gap_id not in self._gap_ctx:
            raise ValueError(f"unknown gap {gap_id}")
        with self.lock:
            self.world.log("gap_human_decision", f"human:{by}", {"draft_id": gap_id, "decision": decision})
            self._gap_decisions[gap_id] = {"decision": decision, "by": by, "at": self.sim.ts(max(self.sim.t, 0))}
            self._emit_gap(gap_id, force=True)
            self._flush_audit()
        return {"ok": True, "gap_id": gap_id, "status": "confirmed" if decision == "confirm" else "rejected"}

    # ---------------------------------------------------------------- views
    def catalogue(self) -> dict:
        return {"ok": True, "scenarios": self._scenario_list(),
                "sites": SITES, "gateways": GATEWAYS, "accounts": ["noc-vendor-7"],
                "playbooks": list(self.rem.cat.values()), "injectors": injector_catalogue(),
                "records": self._record_manifest(), "gaps": self._gap_manifest(),
                "roles": self._role_manifest(), "kb_as_of": str(self.world.kb.as_of),
                "region": GATEWAYS["GW-IN-1"]["city"]}

    def scenario_detail(self, scenario_id: str) -> dict:
        """Director-only planned scenario timeline; it is not operator evidence."""
        allowed = {str(row['id']).lower() for row in self._scenario_list()}
        name = str(scenario_id).lower()
        if name not in allowed:
            raise ValueError('Unknown scenario.')
        scenario = load_scenario(name)
        return {'ok': True, 'audience': 'control', 'id': scenario['id'],
                'title': scenario.get('title', ''), 'story': scenario.get('story', ''),
                'kind': scenario.get('kind', ''), 'start': str(scenario.get('start', '')),
                'sites': scenario.get('sites', []), 'everyday_impact': scenario.get('everyday_impact', []),
                'human_decisions': scenario.get('human_decisions', []), 'objective': scenario.get('heal', {}),
                'schedule': [{'t': event.get('t'), 'actor': event.get('actor'), 'what': event.get('what', '')}
                             for event in scenario.get('events', [])]}

    def _record_manifest(self) -> list[dict]:
        on = dt.date.fromisoformat(str(self.scenario["start"])[:10])
        out = []
        for rec in self.world.kb.records.values():
            source = self.world.kb.sources.get(rec.get("source"), {})
            out.append({"id": rec["id"], "jurisdiction": rec.get("jurisdiction"), "instrument": rec.get("instrument"),
                        "clause": rec.get("clause"), "authority": rec.get("authority"),
                        "binding_status": rec.get("binding_status"), "in_force_from": rec.get("in_force_from"),
                        "in_force_status": self.world.kb.in_force_status(rec["id"], on), "issued": rec.get("issued"),
                        "topic": rec.get("topic"), "pinpoint": rec.get("pinpoint"), "verified": bool(rec.get("verified")),
                        "summary": rec.get("summary"), "quote": rec.get("quote"),
                        "source_url": source.get("url"), "source_sha256": source.get("sha256")})
        return out

    def _gap_manifest(self) -> list[dict]:
        return [{"id": g["id"], "title": g.get("title"), "status": g.get("status"), "topic": g.get("topic"),
                 "jurisdiction": g.get("jurisdiction"), "kind": g.get("kind"), "evidence": g.get("evidence", []),
                 "global_examples": g.get("global_examples", [])} for g in self.world.kb.gaps.values()]

    def _role_manifest(self) -> list[dict]:
        roles = {n: Role.load(n) for n in all_roles()}
        return [{"name": r.name, "kind": r.kind, "organisation": r.organisation, "mandate": r.mandate.strip(),
                 "owns": r.owns} for r in roles.values()]

    @staticmethod
    def _scenario_list() -> list[dict]:
        order = ["s0", "s1", "s2", "s3", "n1", "n2", "n3", "n4", "n5", "cap"]
        out = []
        for name in order:
            path = SCEN_DIR / f"{name}.yaml"
            if not path.is_file():
                continue
            sc = load_scenario(path)
            out.append({"id": str(sc["id"]), "title": sc.get("title", ""), "story": sc.get("story", ""),
                        "kind": sc.get("kind", ""), "sites": sc.get("sites", []),
                        "m3_expected": sc.get("m3_expected", ""), "start": str(sc.get("start", "")),
                        "region": GATEWAYS["GW-IN-1"]["city"], "objective": sc.get("heal") or {},
                        "everyday_impact": sc.get("everyday_impact", []),
                        "human_decisions": sc.get("human_decisions", []),
                        "demo_seconds": sc.get("demo_seconds")})
        return out

    def truth(self) -> dict:
        with self.lock:
            rows = []
            for i in self.injections:
                rows.append({"id": i["id"], "kind": i["kind"], "target": i["target"], "truth_class": i["truth_class"],
                             "start": i["start"], "end": i["end"], "detected_at": self.detection_times.get(i["id"]),
                             "time_to_detect": self._elapsed(i["id"], self.detection_times.get(i["id"])),
                             "contained_at": self.contained_at.get(i["id"]), "time_to_contain": self._elapsed(i["id"], self.contained_at.get(i["id"])),
                             "healed_at": self.healed_at.get(i["id"]), "time_to_heal": self._elapsed(i["id"], self.healed_at.get(i["id"]))})
            return {"ok": True, "t": self.sim.t, "injections": rows, "running_injections": self.running_injections()}

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
            nothing_delivered = r["demand_mbps"] > 0 and r["delivered_mbps"] <= 0
            state = ("down" if r["packet_loss"] > .8 or nothing_delivered
                     else "degraded" if r["packet_loss"] > .15 else "ok")
            if self.sim.state[r["site"]].active_path != "A":
                state = "healing" if state != "down" else state
            out[r["site"]] = {k: r[k] for k in ("active_path", "gateway", "snr_db", "link_margin_db", "packet_loss",
                                                   "battery_pct", "terminals_up", "traffic_load", "txn_success",
                                                   "demand_mbps", "capacity_mbps", "delivered_mbps")}
            out[r["site"]]["mains_power"] = bool(r["mains_power"])    # the simulator stores 0/1
            out[r["site"]]["state"] = state
        return out

    SERVICE_KEY = PUBLIC_SERVICE_KEY

    def _service_totals(self, recs: list[dict]) -> dict:
        """Instantaneous per-service demand/delivered over all sites for this minute (not cumulative)."""
        tot = svc_totals(recs)
        out = {self.SERVICE_KEY.get(k, k): v for k, v in tot.items()}
        demand = sum(v["demand_mbps"] for v in out.values())
        delivered = sum(v["delivered_mbps"] for v in out.values())
        self._svc_hist.append({"t": self.sim.t, "ts": self.sim.ts(self.sim.t), "demand_mbps": round(demand, 2),
                               "delivered_mbps": round(delivered, 2),
                               "pct": round(100 * delivered / demand, 1) if demand else 100.0,
                               "services": out})
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

    def _update_impact(self, recs: list[dict]) -> None:
        real = self.impact.update(recs, self.sim.t)
        # The shadow deliberately cannot receive a remediation outcome.  It uses the same telemetry
        # until a heal/contain changes the real sim, then keeps the worse loss for conservative comparison.
        shadow_records = [dict({k: v for k, v in r.items() if k not in ("services", "delivered_mbps")},
                               packet_loss=max(r["packet_loss"], .85 if any(i["truth_class"].startswith("attack") for i in self.injections) else r["packet_loss"]),
                               txn_success=min(r["txn_success"], .15 if any(i["truth_class"].startswith("attack") for i in self.injections) else r["txn_success"])) for r in recs]
        shadow = self.shadow.update(shadow_records, self.sim.t)
        now = self._svc_hist[-1] if self._svc_hist else {}
        self.emit("impact", real=real, shadow=shadow, cumulative=True,
                  instantaneous={"network_availability_pct": now.get("pct"), "delivered_mbps": now.get("delivered_mbps"),
                                 "demand_mbps": now.get("demand_mbps")})

    def _phase_state(self) -> dict:
        active = [p for p, t in self.phases.items() if self.sim.t - t <= 5]
        return {"active": active, "latest": max(active, key=lambda p: self.phases[p]) if active else None}

    def _autonomy_state(self) -> dict:
        mode, grant = self.rem.mode_for("PB-06", ["CHN-02"])
        return {"mode": mode, "killed": bool(self.rem.killed), "expires_at": grant.get("expires") if grant else None}
