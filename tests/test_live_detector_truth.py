"""Live detector provenance and allocation-status regressions."""
from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

import pytest

from orca.live.session import LiveSession
from orca.sim import service
from orca.sim.engine import CLASSES
from orca.sim.topology import SITES


def _events(session, kind, model=None):
    return [event for event in session.bus.all()
            if event["kind"] == kind and (model is None or event.get("model") == model)]


def _initial_autonomy(session):
    events = session.bus.all()
    session_index = next(i for i, event in enumerate(events) if event["kind"] == "session")
    event = events[session_index + 1]
    assert event["kind"] == "autonomy"
    assert event.get("audience") != "control"
    assert "audit_kind" not in event
    assert {key: event[key] for key in session.state()["autonomy"]} == session.state()["autonomy"]
    return event


def test_initial_and_restarted_session_publish_actual_autonomy(tmp_path, monkeypatch):
    monkeypatch.delenv("ORCA_COMMANDER_PIN_SHA256", raising=False)
    session = LiveSession(runs_dir=tmp_path)
    try:
        initial = _initial_autonomy(session)
        assert initial["mode"] == "MANUAL"
        session.autonomy("AUTO", "*", "*", 20, "demo")
        assert session.state()["autonomy"]["mode"] == "AUTO"
        old_recording, old_stream = session.recording, session.stream_path
        old_stream_content = old_stream.read_text()
        session.restart()
        assert session.recording != old_recording and session.stream_path != old_stream
        assert old_stream.read_text() == old_stream_content
        restarted = _initial_autonomy(session)
        assert restarted["mode"] == "MANUAL"
        assert restarted["seq"] > 0
    finally:
        session.close()


def test_restart_requires_no_commander_pin_with_legacy_configuration(tmp_path, monkeypatch):
    monkeypatch.setenv("ORCA_COMMANDER_PIN_SHA256", "obsolete-configuration")
    session = LiveSession(runs_dir=tmp_path, pin_sha256="obsolete-constructor-value")
    try:
        session.restart()
        result = session.autonomy("AUTO", "*", "*", 20)
        assert result["ok"]
        assert result["grant"]["mode"] == "AUTO"
    finally:
        session.close()


def test_repeated_plan_hash_keeps_each_approval_latency(tmp_path):
    session = LiveSession(runs_dir=tmp_path)
    try:
        def at(minute):
            session.sim.t = minute
            session.world.facts["now"] = session.sim.ts(minute)

        def request():
            plan = session.rem.request_approval(
                "satellite_operator", "PB-01", ["noc-vendor-7"], {}, "containment")
            session._flush_audit()
            return plan

        at(1)
        first = request()
        at(4)
        token = session.rem.approve(first["hash"], "commander", "demo")
        session._flush_audit()
        session.rem.execute("satellite_operator", "PB-01", ["noc-vendor-7"], {}, token)
        session._flush_audit()
        at(5)
        second = request()
        assert second["hash"] == first["hash"]
        at(8)
        session.rem.approve(second["hash"], "commander", "demo")
        session._flush_audit()

        timings = session.timings()
        assert [approval["latency_s"] for approval in timings["approvals"]] == [180, 180]
        assert all(approval["latency_wall_s"] >= 0 for approval in timings["approvals"])
        assert timings["approval_latency_s"] == 180
    finally:
        session.close()


def test_detection_timing_requires_active_matching_site_and_class(tmp_path):
    session = LiveSession(runs_dir=tmp_path)
    try:
        session._agent_turns = lambda *args, **kwargs: None
        session._run_rules = lambda: None
        session._request_plan = lambda *args, **kwargs: None
        session.inject("jamming", "CHN-02", duration_min=10, start=10)
        session.sim.t = 0
        observed = {"site": "CHN-01", "snr_db": 0.0, "mgmt_cmds": 0, "rain_mm_h": 0.0, "mains_power": True}
        session._publish_detection(observed, "M1", "anomaly", {})
        assert session.timings()["incident_start_t"] is None
        assert session.timings()["time_to_detect_min"] is None

        session.sim.t = 10
        session._publish_detection(observed, "M3", "attack-jamming", {})
        observed["site"] = "CHN-02"
        session._publish_detection(observed, "M3", "fault-weather", {})
        assert session.timings()["incident_start_t"] == 10
        assert session.timings()["time_to_detect_min"] is None

        session.sim.t = 12
        session._publish_detection(observed, "M3", "attack-jamming", {})
        assert session.timings()["time_to_detect_min"] == 2
        assert session.timings()["detected_at"] == session.sim.ts(12)
    finally:
        session.close()


def test_contained_management_attack_does_not_repeat_containment_request(tmp_path):
    session = LiveSession(runs_dir=tmp_path)
    try:
        requests = []
        session._request_plan = lambda *args, **kwargs: requests.append((args, kwargs))
        session._agent_turns = lambda *args, **kwargs: None
        session._run_rules = lambda: None
        session.sim.mgmt_contained = True
        session._publish_detection({"site": "CHN-02", "mgmt_cmds": 0}, "M3", "attack-management-plane", {})
        assert requests == []
    finally:
        session.close()


@pytest.mark.parametrize("plan", [
    None,
    {},
    {"method": "none", "solution": "optimal"},
    {"method": "milp"},
    {"method": "milp", "solution": "optimal"},
    {"method": "milp", "status": "failed"},
    {"method": "milp", "status": "failed", "solution": "optimal"},
    {"method": "greedy", "solution": "optimal"},
])
def test_missing_or_failed_m4_status_is_not_optimal(tmp_path, plan):
    session = LiveSession(runs_dir=tmp_path)
    try:
        records = session.sim.step()
        session.sim.m4_plan = plan
        session._model_status(records, session._site_state(records))
        event = _events(session, "model", "M4")[-1]
        assert event.get("solution") is None
        assert event.get("upstream_solution") is None
        assert not any("confidence" in key for key in event)
    finally:
        session.close()


def _scarce_allocation(session):
    session.sim.step()
    record = deepcopy(session.sim.step()[0])
    record["capacity_mbps"] = round(record["demand_mbps"] / 2, 2)
    plan = service.allocate_minute([record])
    assert plan["method"] in ("milp", "greedy")
    return record, plan


def test_m4_validates_postprocessed_allocation_and_status_transitions(tmp_path):
    session = LiveSession(runs_dir=tmp_path)
    try:
        record, plan = _scarce_allocation(session)
        sites = session._site_state([record])
        session.sim.m4_plan = plan
        session._model_status([record], sites)
        good = _events(session, "model", "M4")[-1]
        assert good["solution"] == "feasible"
        assert good["solution_scope"] == "postprocessed_capacity_and_priority"
        assert good["upstream_solution"] == plan["solution"]
        assert good["upstream_solution_scope"] == "before_quantisation_closure"

        failed = {**deepcopy(plan), "status": "failed"}
        session.sim.m4_plan = failed
        before = len(_events(session, "model", "M4"))
        session._model_status([record], sites)
        assert len(_events(session, "model", "M4")) == before + 1
        assert _events(session, "model", "M4")[-1]["solution"] is None
        assert _events(session, "model", "M4")[-1]["upstream_solution"] is None

        session.sim.m4_plan = plan
        session._model_status([record], sites)
        assert _events(session, "model", "M4")[-1]["solution"] == "feasible"

        corrupt = deepcopy(plan)
        row = next(iter(corrupt["allocation"][record["site"]].values()))
        row["granted_mbps"] = row["demand_mbps"] + 1
        session.sim.m4_plan = corrupt
        session._model_status([record], sites)
        assert _events(session, "model", "M4")[-1]["solution"] is None
    finally:
        session.close()


def test_failed_solver_greedy_fallback_is_only_feasible(tmp_path, monkeypatch):
    import scipy.optimize

    monkeypatch.setattr(scipy.optimize, "milp",
                        lambda *args, **kwargs: SimpleNamespace(success=False, message="test failure"))
    session = LiveSession(runs_dir=tmp_path)
    try:
        record, plan = _scarce_allocation(session)
        assert plan["method"] == "greedy" and plan["solution"] == "feasible"
        session.sim.m4_plan = plan
        session._model_status([record], session._site_state([record]))
        event = _events(session, "model", "M4")[-1]
        assert event["solution"] == "feasible"
        assert event["upstream_solution"] == "feasible"
    finally:
        session.close()


def test_s2_milp_optimum_does_not_certify_adjusted_rows(tmp_path):
    from orca.models import m4

    session = LiveSession(scenario="S2", autoplay=True, runs_dir=tmp_path)
    try:
        for _ in range(max(event["t"] for event in session.scenario["events"]) + 1):
            session.tick()
            plan = session.sim.m4_plan
            if plan["method"] == "milp" and plan["allocation"]:
                break
        else:
            pytest.fail("S2 did not produce a MILP allocation")

        records = session.sim.history[-len(session.sim.sites):]
        capacity = {r["site"]: r["capacity_mbps"] for r in records
                    if r["capacity_mbps"] < r["demand_mbps"] - 1e-9}
        demand = {r["site"]: service.service_demand(r) for r in records if r["site"] in capacity}
        raw = m4.allocate(demand, capacity, unit_mbps=service.UNIT_MBPS)
        assert raw["solution"] == "optimal"
        assert any(row["granted_mbps"] != raw["allocation"][site][name]["granted_mbps"]
                   for site, allocation in plan["allocation"].items()
                   for name, row in allocation.items())
        event = _events(session, "model", "M4")[-1]
        assert event["solution"] == "feasible"
        assert event["upstream_solution"] == "optimal"
    finally:
        session.close()


def _isolated_detector(session, record):
    session._agent_turns = lambda *args, **kwargs: None
    session._run_rules = lambda: None
    session._request_plan = lambda *args, **kwargs: None
    session._detect([record])
    session._model_status([record], session._site_state([record]))
    return [{key: value for key, value in event.items() if key != "seq"}
            for event in session.bus.all()
            if event["kind"] in ("model", "alert") and event.get("site") == record["site"]]


def test_changing_only_hidden_truth_cannot_change_public_detector_output(tmp_path):
    outputs, observations = [], []
    for label in ("normal", next(value for value in CLASSES if value == "attack-management-plane")):
        session = LiveSession(runs_dir=tmp_path / label)
        try:
            for _ in range(3):
                record = session.sim.step()[0]
                record["label"] = label
                output = _isolated_detector(session, record)
            observations.append({key: value for key, value in record.items() if key != "label"})
            outputs.append(output)
        finally:
            session.close()
    assert observations[0] == observations[1]
    assert outputs[0] == outputs[1]
    assert any(event.get("model") == "M3" and event.get("class") is not None for event in outputs[0])


def test_hidden_injector_confidence_cannot_change_public_prediction(tmp_path):
    observations, outputs = [], []
    site = next(site for site in SITES if site == "CHN-02")
    for i, params in enumerate(({}, {"confidence": 0.4})):
        session = LiveSession(runs_dir=tmp_path / str(i))
        try:
            session.inject("jamming", site, params=params)
            for _ in range(3):
                record = next(record for record in session.sim.step() if record["site"] == site)
                output = _isolated_detector(session, record)
            observations.append(record)
            outputs.append(output)
        finally:
            session.close()
    assert observations[0] == observations[1]
    assert outputs[0] == outputs[1]
    assert any(event.get("model") == "M3" and "confidence" in event for event in outputs[0])


def test_live_m3_provides_honest_provenance_without_invented_confidence(tmp_path):
    session = LiveSession(runs_dir=tmp_path)
    try:
        session.inject("mgmt_intrusion")
        record = session.sim.step()[0]
        _isolated_detector(session, record)
        event = next(event for event in _events(session, "model", "M3") if event["site"] == record["site"])
        assert event["provenance"] == "collecting_observed_telemetry"
        assert "confidence" not in event
        for _ in range(2):
            record = session.sim.step()[0]
            _isolated_detector(session, record)
        event = [e for e in _events(session, "model", "M3") if e["site"] == record["site"]][-1]
        prediction = session.detector.assess(list(session._hist[record["site"]]), record["site"])["m3"]
        assert event["provenance"] == "lightgbm_multiclass_synthetic"
        assert event["class"] == prediction["label"]
        assert event["confidence"] == prediction["confidence"]
        assert event["probabilities"] == prediction["probabilities"]
        assert event["score_kind"] == "uncalibrated_model_probability"
    finally:
        session.close()
