"""P1 acceptance coverage for the live emulated control engine (mock LLM only)."""
from __future__ import annotations

import hashlib
import json
import threading
from urllib.request import Request, urlopen

import pytest

from orca.live.server import make_server
from orca.live.session import LiveSession


PIN = "2468"


def live(tmp_path, **kw):
    return LiveSession(runs_dir=tmp_path, pin_sha256=hashlib.sha256(PIN.encode()).hexdigest(), **kw)


def events(s, kind):
    return [e for e in s.bus.all() if e["kind"] == kind]


def test_01_headless_ticks_include_every_site(tmp_path):
    s = live(tmp_path)
    for _ in range(30):
        s.tick()
    assert len(events(s, "tick")[-1]["sites"]) == 6
    s.close()


def test_02_intrusion_routes_to_satellite_operator_and_requests_containment(tmp_path):
    s = live(tmp_path)
    s.inject("mgmt_intrusion")
    s.tick()
    assert events(s, "alert")[0]["visible_to"] == ["satellite_operator"]
    assert any(p["playbook"] == "PB-01" for p in s.rem.plans.values())
    s.close()


def test_03_approval_enforces_pin_and_expiry(tmp_path):
    s = live(tmp_path)
    s.inject("mgmt_intrusion"); s.tick()
    plan = next(iter(s.rem.plans.values()))
    with pytest.raises(Exception):
        s.approve(plan["hash"], "bad")
    assert s.approve(plan["hash"], PIN)["ok"]
    s.close()


def test_04_auto_heal_checks_clean_domestic_path_and_refuses_foreign_lure(tmp_path):
    s = live(tmp_path)
    s.autonomy("AUTO", ["CHN-02"], ["PB-06"], 20, PIN)
    s.inject("jamming", "CHN-02"); s.tick()
    assert s.sim.state["CHN-02"].active_path == "B"
    assert events(s, "heal")[0]["check"]["clean"]
    s.close()
    s = live(tmp_path)
    s.autonomy("AUTO", ["CHN-02"], ["PB-06"], 20, PIN)
    s.inject("failover_lure", "CHN-02"); s.tick()
    assert s.sim.state["CHN-02"].active_path == "A"
    assert not next(iter(s.rem.plans.values()))["clone_test"]["passed"]
    s.close()


def test_05_low_confidence_downgrades_auto(tmp_path):
    s = live(tmp_path)
    s.autonomy("AUTO", ["CHN-02"], ["PB-06"], 20, PIN)
    s.inject("jamming", "CHN-02", params={"confidence": .4}); s.tick()
    assert any(e.get("audit_kind") == "autonomy_downgraded" for e in events(s, "autonomy"))
    s.close()


def test_06_kill_revokes_execution_until_release(tmp_path):
    s = live(tmp_path)
    s.inject("mgmt_intrusion"); s.tick(); plan = next(iter(s.rem.plans.values()))
    s.kill(PIN, "exercise")
    with pytest.raises(Exception):
        s.approve(plan["hash"], PIN)
    s.release_kill(PIN)
    assert not s.rem.killed
    s.close()


def test_07_rules_off_suppresses_verdicts_and_eu_cites_eu(tmp_path):
    s = live(tmp_path, rules_enabled=False)
    s.inject("rain"); s.tick()
    assert not events(s, "verdict")
    s.close()
    s = live(tmp_path)
    s.set_kb("eu"); s.inject("rain"); s.tick()
    assert any(any(r.startswith("EU-") for r in e.get("records") or []) for e in events(s, "verdict"))
    s.close()


def test_08_rain_is_fault_not_containment(tmp_path):
    s = live(tmp_path)
    s.inject("rain"); s.tick()
    assert events(s, "alert")[0]["label"] == "fault-weather"
    assert not s.rem.plans
    s.close()


def test_09_patch_stages_and_reattack(tmp_path):
    s = live(tmp_path)
    s.inject("mgmt_intrusion"); s.tick()
    first = next(iter(s.rem.plans.values())); s.approve(first["hash"], PIN)
    patch = next(p for p in s.rem.plans.values() if p["playbook"] == "PB-11")
    assert s.approve(patch["hash"], PIN)["ok"]
    assert [e["pct"] for e in events(s, "patch_stage")] == [5, 25, 100]
    assert all(e["blocked"] for e in events(s, "reattack"))
    s.close()


def test_10_shadow_impact_is_conservative(tmp_path):
    s = live(tmp_path)
    s.inject("mgmt_intrusion")
    for _ in range(4): s.tick()
    impact = events(s, "impact")[-1]
    assert impact["shadow"]["payments_failed"] >= impact["real"]["payments_failed"]
    assert all(v >= 0 for k, v in impact["real"].items() if isinstance(v, (int, float)))
    s.close()


def test_11_recording_is_chained_and_replayable(tmp_path):
    s = live(tmp_path); s.tick()
    assert s.world.audit.verify() is None
    from dashboard.adapter import build_run
    assert build_run(s.recording, s.recording.stem)["chain"]["ok"]
    s.close()


def test_12_server_catalogue_session_inject_and_sse_replay(tmp_path):
    s = live(tmp_path)
    server = make_server(s, port=0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    assert json.load(urlopen(base + "/api/catalogue"))["ok"]
    req = Request(base + "/api/inject", data=json.dumps({"kind": "rain"}).encode(), headers={"Content-Type": "application/json"})
    assert json.load(urlopen(req))["ok"]
    s.tick()
    stream = urlopen(base + "/api/stream?since=0", timeout=2)
    assert stream.readline().startswith(b"data: ")
    stream.close(); server.shutdown(); server.server_close(); s.close()


def test_13_schedule_truth_and_control_audience(tmp_path):
    s = live(tmp_path)
    scheduled = s.schedule("rain", "CHN-01", 2, 3)
    assert scheduled["scheduled"]["id"].startswith("SCH-")
    # Simulator minute zero is the first tick, so a schedule at minute 2 is
    # applied immediately before the third tick.
    s.tick(); s.tick(); s.tick()
    assert s.truth()["injections"]
    assert all(e.get("audience") == "control" for e in events(s, "inject"))
    s.close()


def test_live_session_uses_real_client_when_llm_is_local():
    # Atlas test 8 Nov: --llm local was silently running the mock policy.
    from orca.live.session import LiveSession
    from orca.llm import LLMClient
    s = LiveSession(scenario="S1", llm="local")
    try:
        assert all(isinstance(a.llm, LLMClient) for a in s.agents.values())
    finally:
        getattr(s, "close", lambda: None)()


# ---------------------------------------------------------------- UI redesign engine additions (E1-E6)
SCENARIOS = ["s0", "s1", "s2", "s3", "n1", "n2", "n3", "n4", "n5", "cap"]


def models(s, name=None):
    return [e for e in events(s, "model") if name in (None, e["model"])]


def test_e1_m1_m2_m4_events_flip_state_in_s3_and_s2(tmp_path):
    s = live(tmp_path, scenario="s3", autoplay=True)
    for _ in range(40):
        s.tick()
    m1 = [e for e in models(s, "M1") if e["site"] == "CHN-03"]
    assert {"score", "threshold", "state"} <= set(m1[0]) and 0 <= m1[0]["score"] <= 1
    assert any(e["state"] == "flagged" for e in m1)
    assert any(e["state"] == "ok" for e in models(s, "M1") if e["site"] == "CHN-01")
    assert any(e["state"] == "flagged" and e["horizon_min"] is not None and e["metric"] in ("link_margin", "battery")
               for e in models(s, "M2") if e["site"] == "CHN-03")
    m4 = models(s, "M4")
    assert any(e["state"] == "replan" for e in m4)
    assert all(e["allocation"][0] == "112" and sorted(e["allocation"]) == ["112", "grid", "hospital", "payments"] for e in m4)
    m3 = [e for e in models(s, "M3") if e["state"] != "ok"]
    assert m3 and all(e["state"] == "flagged" for e in m3 if e["class"].startswith("attack"))
    s.close()
    s = live(tmp_path, scenario="s2", autoplay=True)
    for _ in range(40):
        s.tick()
    assert any(e["state"] == "fault" for e in models(s, "M3"))
    assert any(e["state"] == "flagged" for e in models(s, "M2")) and any(e["state"] == "replan" for e in models(s, "M4"))
    s.close()


def test_e1_m4_flips_from_ok_to_replan_on_power_cut(tmp_path):
    s = live(tmp_path)
    s.tick()
    s.inject("power_cut", "CHN-05"); s.tick(); s.tick()
    m4 = models(s, "M4")
    assert [m4[0]["state"], m4[-1]["state"]] == ["ok", "replan"] and "CHN-05" in m4[-1]["sites"]
    s.close()


def test_e1_changes_only_plus_heartbeat(tmp_path):
    s = live(tmp_path)
    for _ in range(12):
        s.tick()
    m2 = [e for e in models(s, "M2") if e["site"] == "CHN-01"]
    assert [e["t"] for e in m2] == [0, 5, 10]   # steady state: heartbeat only, every 5 sim minutes
    s.close()


def test_e1_alert_source_is_real_detector(tmp_path):
    s = live(tmp_path, scenario="n4", autoplay=True)
    for _ in range(20):
        s.tick()
    assert any(e["source"] == "M1" for e in events(s, "alert"))   # telemetry mismatch
    s.close()
    s = live(tmp_path)
    s.inject("mgmt_intrusion"); s.tick()
    assert events(s, "alert")[0]["source"] == "M3"
    s.close()


def test_e2_llm_model_in_session_event_and_meta(tmp_path, monkeypatch):
    s = live(tmp_path)
    assert events(s, "session")[0]["llm_model"] == "mock" == s.state()["session"]["llm_model"]
    s.close()
    monkeypatch.setenv("LLM_MODEL", "test-model-x")
    s = live(tmp_path, llm="local")
    assert events(s, "session")[0]["llm_model"] == "test-model-x"
    s.close()


def test_e3_auto_execution_emits_auto_approval(tmp_path):
    s = live(tmp_path)
    s.autonomy("AUTO", ["CHN-02"], ["PB-06"], 20, PIN)
    s.inject("jamming", "CHN-02"); s.tick()
    statuses = [e["status"] for e in events(s, "approval")]
    assert "requested" in statuses and "auto" in statuses and "approved" not in statuses
    s.close()


@pytest.mark.parametrize("name", SCENARIOS)
def test_e4_every_scenario_plays_live(tmp_path, name):
    import yaml
    from orca.sim.scenario import SCEN_DIR
    spec = yaml.safe_load((SCEN_DIR / f"{name}.yaml").read_text())
    expects = [(e["t"], x) for e in spec["events"] for x in e.get("expect") or []]
    s = live(tmp_path, scenario=name, autoplay=True)
    for _ in range(max([60] + [t + 1 for t, _ in expects])):
        s.tick()
    bad = [e for e in models(s) if e["state"] not in ("ok",)]
    if name == "s0":
        assert not bad and not events(s, "inject")
    else:
        assert bad, f"{name}: no model left the ok state"
    verdicts = events(s, "verdict")
    for t, x in expects:
        assert any(v["verdict"] == x["verdict"] and (not x.get("gap") or v["gap_id"] == x["gap"]) for v in verdicts), (name, t, x)
    # ground truth stays on the control channel only
    for e in s.bus.all():
        if "truth_class" in e or e.get("by") == "scenario":
            assert e["kind"] == "inject" and e["audience"] == "control"
    if name == "n3":
        assert any(e["class"] == "abstain" and e["state"] == "unsure" for e in models(s, "M3"))
    s.close()


def test_e4_scripted_threats_are_recorded_as_ground_truth(tmp_path):
    s = live(tmp_path, scenario="s1", autoplay=True)
    for _ in range(3):
        s.tick()
    inj = events(s, "inject")
    assert inj and inj[0]["by"] == "scenario" and inj[0]["audience"] == "control"
    assert s.truth()["injections"]
    s.close()


def test_e4_s3_offers_route_candidates_live(tmp_path):
    s = live(tmp_path, scenario="s3", autoplay=True)
    for _ in range(40):
        s.tick()
    assert s.sim.routes["CHN-03"]["C"]["gateway"] == "GW-XX"
    assert s.sim.routes["CHN-03"]["A"]["integrity"] == "failed"
    s.close()


def test_e5_catalogue_lists_all_scenarios(tmp_path):
    s = live(tmp_path)
    cat = s.catalogue()
    assert [x["id"] for x in cat["scenarios"]] == ["S0", "S1", "S2", "S3", "N1", "N2", "N3", "N4", "N5", "CAP"]
    assert {"id", "title", "story", "kind", "sites", "m3_expected", "start"} <= set(cat["scenarios"][0])
    assert {"sites", "gateways", "accounts", "playbooks", "injectors"} <= set(cat)
    s.close()


def test_e6_stream_follows_session_restart(tmp_path):
    from orca.live.server import stream_chunks
    s = live(tmp_path)
    for _ in range(3):
        s.tick()
    gen = stream_chunks(s, since=0, poll=0.05, heartbeat=0.2)
    first = next(gen)
    assert first["seq"] == 1
    old_bus = s.bus
    for _ in range(len(old_bus.all()) - 1):
        next(gen)                       # drain the old bus; cursor is now high
    s.restart(scenario="s2")
    assert s.bus is not old_bus
    got = [next(gen) for _ in range(3)]
    ev = next(e for e in got if e)
    assert ev["seq"] == 1 and s.bus.all()[0] == ev
    s.close()


# ---------------------------------------------------------------- E7 stream sidecar, E8 runs list, E9 scripted heals
def serve(s):
    server = make_server(s, port=0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}"


def test_e7_sidecar_holds_every_bus_event_and_replay_prefers_it(tmp_path):
    s = live(tmp_path, scenario="s1", autoplay=True)
    for _ in range(8):
        s.tick()
    sidecar = s.recording.with_name(s.recording.stem + ".stream.jsonl")
    assert sidecar.is_file()
    lines = [json.loads(x) for x in sidecar.read_text().splitlines()]
    assert lines == json.loads(json.dumps(s.bus.all(), default=str))
    assert {"tick", "model", "phase", "impact", "inject"} <= {e["kind"] for e in lines}
    assert any(e.get("audience") == "control" for e in lines)
    server, base = serve(s)
    for name in (s.recording.name, sidecar.name):
        got = json.load(urlopen(base + "/api/replay?file=" + name))
        assert got["ok"] and got["source"] == "stream" and got["events"] == lines
    # without a sidecar the audit translation is used
    sidecar.unlink()
    got = json.load(urlopen(base + "/api/replay?file=" + s.recording.name))
    assert got["ok"] and got["source"] == "audit" and got["events"]
    server.shutdown(); server.server_close(); s.close()


def test_e7_restart_starts_a_new_sidecar(tmp_path):
    s = live(tmp_path)
    s.tick()
    first = s.stream_path
    s.restart(scenario="s2")
    assert s.stream_path != first and first.is_file()
    assert json.loads(s.stream_path.read_text().splitlines()[0])["seq"] == 1
    s.close()


def test_e8_runs_list_newest_first_with_stream_flag(tmp_path):
    import os
    s = live(tmp_path, scenario="s3")
    s.tick()
    old = tmp_path / "S9-rules-mock.jsonl"
    old.write_text("")
    os.utime(old, (1, 1))
    server, base = serve(s)
    runs = json.load(urlopen(base + "/api/runs"))
    assert runs["ok"] and [r["file"] for r in runs["runs"]] == [s.recording.name, "S9-rules-mock.jsonl"]
    assert runs["runs"][0]["stream"] is True and runs["runs"][0]["scenario"] == "S3"
    assert runs["runs"][1]["stream"] is False and runs["runs"][1]["scenario"] == "S9"
    assert {"file", "scenario", "stream", "size", "mtime"} <= set(runs["runs"][0])
    assert not any(r["file"].endswith(".stream.jsonl") for r in runs["runs"])
    server.shutdown(); server.server_close(); s.close()


def play_and_approve(s, minutes):
    seen = set()
    for _ in range(minutes):
        s.tick()
        for e in events(s, "approval"):
            if e["status"] == "requested" and e["hash"] not in seen:
                seen.add(e["hash"])
                try:
                    s.approve(e["hash"], PIN)
                except Exception:
                    pass


def test_e9_s1_conflict_then_pb06_heal_on_microwave(tmp_path):
    s = live(tmp_path, scenario="s1", autoplay=True)
    play_and_approve(s, 60)
    assert any(v["verdict"] == "CONFLICT" for v in events(s, "verdict"))
    heals = events(s, "heal")
    assert {h["site"] for h in heals} == {"CHN-01", "CHN-02"} and all(h["to_path"] == "B" and h["check"]["clean"] for h in heals)
    assert min(h["t"] for h in heals) >= 55
    s.close()


def test_e9_s3_refuses_foreign_path_then_heals_on_b(tmp_path):
    s = live(tmp_path, scenario="s3", autoplay=True)
    play_and_approve(s, 50)
    assert any(e["result"] == "refused" for e in events(s, "execute"))
    heals = events(s, "heal")
    assert len(heals) == 1 and heals[0]["to_path"] == "B" and heals[0]["t"] >= 42
    assert s.sim.routes["CHN-03"]["B"]["gateway"] == "GW-IN-2"
    s.close()


def test_e9_n1_heals_after_clean_backup_is_offered(tmp_path):
    s = live(tmp_path, scenario="n1", autoplay=True)
    play_and_approve(s, 55)
    heals = events(s, "heal")
    assert [(h["site"], h["to_path"]) for h in heals] == [("CHN-01", "B")] and heals[0]["t"] >= 48
    s.close()
