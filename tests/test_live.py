"""P1 acceptance coverage for the live emulated control engine (mock LLM only)."""
from __future__ import annotations

import hashlib
import json
import threading
from urllib.request import Request, urlopen

import pytest

from orca import rules
from orca.live.server import make_server
from orca.live.session import LiveSession


PIN = "2468"


def live(tmp_path, **kw):
    return LiveSession(runs_dir=tmp_path, pin_sha256=hashlib.sha256(PIN.encode()).hexdigest(), **kw)


def warm(s, n=3):
    """M1-M3 need three observed samples per site before they assess anything."""
    for _ in range(n):
        s.tick()


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
    warm(s); s.inject("mgmt_intrusion")
    s.tick()
    assert events(s, "alert")[0]["visible_to"] == ["satellite_operator"]
    assert any(p["playbook"] == "PB-01" for p in s.rem.plans.values())
    s.close()


def test_03_explicit_approval_executes_without_pin(tmp_path):
    s = live(tmp_path)
    warm(s); s.inject("mgmt_intrusion"); s.tick()
    plan = next(iter(s.rem.plans.values()))
    assert s.approve(plan["hash"])["ok"]
    assert not events(s, "pin_refused")
    s.close()


def test_04_auto_heal_checks_clean_domestic_path_and_refuses_foreign_lure(tmp_path):
    s = live(tmp_path)
    s.autonomy("AUTO", ["CHN-02"], ["PB-06"], 20, PIN)
    warm(s); s.inject("jamming", "CHN-02"); s.tick()
    assert s.sim.state["CHN-02"].active_path == "B"
    assert events(s, "heal")[0]["check"]["clean"]
    s.close()
    s = live(tmp_path)
    s.autonomy("AUTO", ["CHN-02"], ["PB-06"], 20, PIN)
    warm(s); s.inject("failover_lure", "CHN-02")
    for _ in range(5):                          # PB-06 is requested once the lure actually hurts the site
        s.tick()
        if s.rem.plans:
            break
    assert s.sim.state["CHN-02"].active_path == "A"
    assert not next(iter(s.rem.plans.values()))["clone_test"]["passed"]
    s.close()


def test_05_m3_abstention_downgrades_auto(tmp_path):
    # N3's unprotected feeder-link audit is outside M3's observed features, so M3 abstains there.
    s = live(tmp_path, scenario="n3", autoplay=True)
    s.autonomy("AUTO", ["CHN-05"], ["PB-06"], 20, PIN)
    warm(s, 2)                                  # still warming: nothing assessed, nothing downgraded
    assert not events(s, "alert")
    assert not any(e.get("audit_kind") == "autonomy_downgraded" for e in events(s, "autonomy"))
    s.tick()
    assert any(e["source"] == "M3" and e["label"] == "abstain" and e["site"] == "CHN-05" for e in events(s, "alert"))
    assert any(e.get("audit_kind") == "autonomy_downgraded" for e in events(s, "autonomy"))
    assert s.rem.mode_for("PB-06", ["CHN-05"])[0] == "ASSISTED"
    s.close()


def test_05b_m3_warm_up_assesses_nothing_before_three_samples(tmp_path):
    s = live(tmp_path)
    s.inject("mgmt_intrusion"); s.tick()       # attack starts at minute 1; only two samples at minute 1
    s.tick()
    assert not events(s, "alert") and not s.rem.plans
    assert all(e["state"] == "warming" and e["required_samples"] == 3 for e in models(s, "M3"))
    s.tick()
    assert events(s, "alert")[0]["source"] == "M3"
    m3 = [e for e in models(s, "M3") if e["state"] != "warming"]
    assert m3 and all(e["score_kind"] == "uncalibrated_model_probability" for e in m3)
    s.close()


def test_06_kill_revokes_execution_until_release(tmp_path):
    s = live(tmp_path)
    warm(s); s.inject("mgmt_intrusion"); s.tick(); plan = next(iter(s.rem.plans.values()))
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
    warm(s); s.inject("rain"); s.tick()
    assert events(s, "alert")[0]["label"] == "fault-weather"
    assert not s.rem.plans
    s.close()


def test_09_patch_stages_and_reattack(tmp_path):
    s = live(tmp_path)
    warm(s); s.inject("mgmt_intrusion"); s.tick()
    first = next(iter(s.rem.plans.values())); s.approve(first["hash"], PIN)
    patch = next(p for p in s.rem.plans.values() if p["playbook"] == "PB-11")
    assert s.approve(patch["hash"], PIN)["ok"]
    assert [e["pct"] for e in events(s, "patch_stage") if e["playbook"] == "PB-11"] == [5, 25, 100]
    attacks = [e for e in events(s, "reattack") if e["playbook"] == "PB-11"]
    assert attacks and all(e["blocked"] for e in attacks)
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
        assert all(a.adviser is s.adviser and a.adviser.llm is a.llm for a in s.agents.values())
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
    m1 = [e for e in models(s, "M1") if e["site"] == "CHN-03" and e["state"] != "warming"]
    assert {"score", "threshold", "state"} <= set(m1[0]) and 0 <= m1[0]["score"] <= 1
    assert any(e["state"] == "flagged" for e in m1)
    assert any(e["state"] == "ok" for e in models(s, "M1") if e["site"] == "CHN-01")
    assert any(e["state"] == "flagged" and e["horizon_min"] is not None and e["metric"] in ("link_margin", "battery")
               for e in models(s, "M2") if e["site"] == "CHN-03")
    m4 = models(s, "M4")
    assert any(e["state"] == "replan" for e in m4)
    assert all(e["allocation_priority"][0] == "112" and sorted(e["allocation_priority"]) == ["112", "grid", "hospital", "payments"] for e in m4)
    m3 = [e for e in models(s, "M3") if e["state"] not in ("ok", "warming")]
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
    # two warm-up samples, the first assessment, then heartbeat only every 5 sim minutes
    assert [e["t"] for e in m2] == [0, 1, 2, 5, 10]
    assert [e["state"] for e in m2][:2] == ["warming", "warming"]
    s.close()


def test_e1_alert_source_is_real_detector(tmp_path):
    s = live(tmp_path, scenario="n4", autoplay=True)
    for _ in range(20):
        s.tick()
    assert any(e["source"] == "M1" for e in events(s, "alert"))   # telemetry mismatch
    s.close()
    s = live(tmp_path)
    warm(s); s.inject("mgmt_intrusion"); s.tick()
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
    warm(s); s.inject("jamming", "CHN-02"); s.tick()
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
    bad = [e for e in models(s) if e["state"] not in ("ok", "warming")]
    if name == "s0":
        # A normal baseline must not produce any detector alert or flagged model state.
        assert not bad and not events(s, "inject") and not events(s, "alert")
        assert all(e.get("class") in (None, "normal") for e in models(s, "M3"))
        assert not s.rem.plans and not events(s, "execute")
    else:
        assert bad, f"{name}: no model left the ok state"
    verdicts = events(s, "verdict")
    assert all(v["verdict"] in rules.VERDICTS and v.get("rule") and v.get("records") for v in verdicts)
    for t, x in expects:
        assert any(v["verdict"] == x["verdict"] and (not x.get("gap") or v["gap_id"] == x["gap"]) for v in verdicts), (name, t, x)
    # ground truth stays on the control channel only
    for e in s.bus.all():
        if "truth_class" in e or e.get("by") == "scenario":
            assert e["kind"] == "inject" and e["audience"] == "control"
    if name == "n3":
        assert any(e.get("class") == "abstain" and e["state"] == "unsure" for e in models(s, "M3"))
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


def test_audit_only_replay_marks_injection_stop_as_control_truth(tmp_path):
    from orca.live.server import _replay_events

    s = live(tmp_path)
    injected = s.inject("rain")["injection"]
    s.stop_injection(injection_id=injected["id"])
    events = _replay_events(s.recording)
    stopped = [e for e in events if e["kind"] == "inject_stop"]
    assert len(stopped) == 1
    assert stopped[0]["audience"] == "control"
    assert stopped[0]["injector"] == "rain"
    s.close()


def test_replay_exposes_verified_audit_rows_without_control_truth(tmp_path):
    s = live(tmp_path)
    injected = s.inject("rain")["injection"]
    s.stop_injection(injection_id=injected["id"])
    s.tick()
    server, base = serve(s)
    try:
        got = json.load(urlopen(base + "/api/replay?file=" + s.recording.name))
        original = [json.loads(line) for line in s.recording.read_text().splitlines()]
        assert got["source"] == "stream"
        assert got["audit"]["chain"]["ok"] is True
        assert got["audit"]["omitted_control"] == 2
        assert all(row["kind"] not in {"inject", "scheduled", "inject_stopped"} for row in got["audit"]["entries"])
        assert got["audit"]["entries"][0] == original[0]
        assert all(row.get("hash") for row in got["audit"]["entries"])
        s.recording.unlink()
        got = json.load(urlopen(base + "/api/replay?file=" + s.recording.name))
        assert got["source"] == "stream" and got["audit"]["chain"]["ok"] is None
        assert got["audit"]["entries"] == []
    finally:
        server.shutdown(); server.server_close(); s.close()


def test_replay_reports_tampered_and_malformed_audit_chains(tmp_path):
    s = live(tmp_path)
    s.tick()
    server, base = serve(s)
    try:
        original = [json.loads(line) for line in s.recording.read_text().splitlines()]
        lines = json.loads(json.dumps(original))
        lines[0]["payload"]["scenario"] = "tampered"
        s.recording.write_text("\n".join(json.dumps(line) for line in lines) + "\n")
        got = json.load(urlopen(base + "/api/replay?file=" + s.recording.name))
        assert got["source"] == "stream"
        assert got["audit"]["chain"]["ok"] is False
        assert got["audit"]["chain"]["bad_seq"] == 1

        lines = json.loads(json.dumps(original))
        del lines[0]["hash"]
        s.recording.write_text("\n".join(json.dumps(line) for line in lines) + "\n")
        got = json.load(urlopen(base + "/api/replay?file=" + s.recording.name))
        assert got["audit"]["chain"]["ok"] is False
        assert got["audit"]["chain"]["bad_seq"] == 1
        assert "missing hash" in got["audit"]["chain"]["note"]

        with s.recording.open("a") as out:
            out.write("{malformed\n")
        got = json.load(urlopen(base + "/api/replay?file=" + s.recording.name))
        assert got["audit"]["chain"]["ok"] is False
        assert "malformed" in got["audit"]["chain"]["note"]
    finally:
        server.shutdown(); server.server_close(); s.close()


def test_audit_only_replay_reports_malformed_chain_without_hiding_valid_events(tmp_path):
    s = live(tmp_path)
    injected = s.inject("rain")["injection"]
    s.stop_injection(injection_id=injected["id"])
    s.tick()
    server, base = serve(s)
    try:
        s.stream_path.unlink()
        with s.recording.open("a") as out:
            out.write("{malformed\n")
        got = json.load(urlopen(base + "/api/replay?file=" + s.recording.name))
        assert got["source"] == "audit"
        assert got["audit"]["chain"]["ok"] is False
        assert "malformed" in got["audit"]["chain"]["note"]
        assert any(event["kind"] == "tick" or event["kind"] == "net_state" for event in got["events"])
        assert all(event.get("audience") == "control"
                   for event in got["events"] if event["kind"] in {"inject", "inject_stop"})
        assert got["audit"]["omitted_control"] == 2
    finally:
        server.shutdown(); server.server_close(); s.close()


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


def test_live_director_can_stop_a_running_attack(tmp_path):
    s = live(tmp_path, scenario="S0")
    s.inject("jamming", "CHN-02", 30)
    for _ in range(3):
        s.tick()
    running = [i["kind"] for i in s.running_injections()]
    assert "jamming" in running
    out = s.stop_injection(kind="jamming")
    assert out["ok"] and out["stopped"]
    for _ in range(2):
        s.tick()
    assert "jamming" not in [i["kind"] for i in s.running_injections()]
    stop = events(s, "inject_stop")
    assert stop and stop[0]["audience"] == "control" and stop[0]["injector"] == "jamming"
    with pytest.raises(ValueError):
        s.stop_injection(kind="jamming")


# ---------------------------------------------------------------- delivered Mbps, diffs, timings, summary
SERVICE_KEYS = {"112", "hospital", "upi_atm", "grid", "general"}


def test_20_tick_has_delivered_mbps_per_site_and_service(tmp_path):
    s = live(tmp_path)
    s.tick()
    tick = events(s, "tick")[-1]
    assert tick["instantaneous"] is True and set(tick["services"]) == SERVICE_KEYS
    for svc in tick["services"].values():
        assert set(svc) == {"demand_mbps", "delivered_mbps", "pct"} and 0 <= svc["pct"] <= 100
    for site in tick["sites"].values():
        assert {"demand_mbps", "capacity_mbps", "delivered_mbps"} <= set(site)
    assert round(sum(v["delivered_mbps"] for v in tick["sites"].values()), 1) == \
        round(sum(v["delivered_mbps"] for v in tick["services"].values()), 1)
    s.close()


def test_impact_delivery_matches_ticks_and_summary_without_fabricating_shadow_throughput(tmp_path):
    s = live(tmp_path)
    for _ in range(2):
        s.tick()
    ticks = events(s, "tick")
    impact = events(s, "impact")[-1]
    delivery = impact["real"]["delivery"]
    assert delivery["available"] is True
    assert delivery["provenance"] == "emulated_simulator_allocation"
    assert delivery["now"]["services"] == ticks[-1]["services"]
    assert set(delivery["now"]["sites"]) == set(ticks[-1]["sites"])
    for site, row in delivery["now"]["sites"].items():
        assert row["delivered_mbps"] == ticks[-1]["sites"][site]["delivered_mbps"]
        assert set(row["services"]) == SERVICE_KEYS
        assert round(sum(x["delivered_mbps"] for x in row["services"].values()), 2) == row["delivered_mbps"]
    for service in SERVICE_KEYS:
        expected = round(sum(tick["services"][service]["delivered_mbps"] for tick in ticks) * 60, 2)
        assert delivery["cumulative"]["services"][service]["delivered_mbit"] == expected

    shadow = impact["shadow"]["delivery"]
    assert shadow == {"available": False, "reason": "not_simulated", "provenance": "packet_loss_floor_estimate"}
    summary = s.summary()
    assert summary["network"]["instant_delivered_mbps"] == delivery["now"]["network"]["delivered_mbps"]
    assert summary["services"]["112"]["cumulative_delivered_mbit"] == delivery["cumulative"]["services"]["112"]["delivered_mbit"]
    for site in ticks[-1]["sites"]:
        assert summary["sites"][site]["instant_delivered_mbps"] == ticks[-1]["sites"][site]["delivered_mbps"]
        assert set(summary["sites"][site]["services"]) == SERVICE_KEYS
    s.close()


def test_impact_delivery_is_unavailable_before_the_first_tick(tmp_path):
    s = live(tmp_path)
    real = s.impact.snapshot(0)["delivery"]
    assert real == {"available": False, "reason": "awaiting_telemetry", "provenance": "emulated_simulator_allocation"}
    assert s.summary()["sites"] == {}
    with pytest.raises(ValueError, match="site records"):
        s.impact.update([], 0)
    s.close()


def test_21_short_capacity_sheds_low_priority_and_keeps_112_and_hospital(tmp_path):
    s = live(tmp_path)
    s.inject("surge", "CHN-04", 12, {"load": 3.0})
    for _ in range(5):
        s.tick()
    tick = events(s, "tick")[-1]
    assert tick["sites"]["CHN-04"]["capacity_mbps"] < tick["sites"]["CHN-04"]["demand_mbps"]
    m4 = [e for e in events(s, "model") if e["model"] == "M4"][-1]
    assert m4["solution"] in ("optimal", "feasible") and m4["method"] in ("milp", "greedy")
    assert {x["service"] for x in m4["shed"]} and not {"112", "hospital"} & {x["service"] for x in m4["shed"]}
    assert tick["services"]["112"]["pct"] == 100 and tick["services"]["hospital"]["pct"] == 100
    assert tick["services"]["general"]["pct"] < 100
    s.close()


def test_22_every_execute_event_has_real_diffs_including_refusals(tmp_path):
    s = live(tmp_path)
    warm(s); s.inject("mgmt_intrusion"); s.tick()
    first = next(iter(s.rem.plans.values()))
    s.approve(first["hash"], PIN)
    ok = [e for e in events(s, "execute") if e["playbook"] == "PB-01"][-1]
    row = ok["diffs"][0]
    assert ok["changed"] and row["before"] != row["after"] and row["unified"] and row["device"] == "SAT-MGMT"
    plan = s.rem.request_approval("satellite_operator", "PB-12", ["SAT-MGMT"], {}, "refusal check")
    with pytest.raises(Exception):
        s.rem.execute("satellite_operator", "PB-12", ["SAT-MGMT"], {}, "no-token")
    s._flush_audit()
    refused = [e for e in events(s, "execute") if e.get("result") == "refused"][-1]
    assert refused["changed"] is False
    assert all(d["before"] == d["after"] and not d["unified"] for d in refused["diffs"])
    assert plan["hash"]
    s.close()


def test_23_stage_fault_rolls_back_for_real_then_retry_needs_new_approval(tmp_path):
    s = live(tmp_path)
    s.arm_stage_fault(25)
    warm(s); s.inject("mgmt_intrusion"); s.tick()
    s.approve(next(iter(s.rem.plans.values()))["hash"], PIN)
    faulted = next(p for p in s.rem.plans.values() if p["playbook"] == "PB-11")
    before = s.net.text("SAT-MGMT")
    assert not s.approve(faulted["hash"], PIN)["ok"]
    assert s.net.text("SAT-MGMT") == before                     # really reverted
    stages = [e for e in events(s, "patch_stage") if e["playbook"] == "PB-11"]
    assert [(e["pct"], e["health"]) for e in stages] == [(5, "ok"), (25, "fail")]
    rb = events(s, "rollback")[-1]
    assert rb["changed"] is False and rb["stage_pct"] == 25 and rb["revert_diff"]
    retry = [p for p in s.rem.plans.values() if p["playbook"] == "PB-11" and not p.get("executed")]
    assert len(retry) == 1 and "simulate_failure_at" not in retry[0]["params"]
    assert s.approve(retry[0]["hash"], PIN)["ok"]
    assert [e["pct"] for e in events(s, "patch_stage") if e["playbook"] == "PB-11"][-3:] == [5, 25, 100]
    attacks = [e for e in events(s, "reattack") if e["playbook"] == "PB-11"]
    assert attacks and all(e["blocked"] for e in attacks)
    t = s.timings()
    assert t["failed_attempts"] == 1 and t["rollback_ok"] is True
    s.close()


def test_24_timings_are_none_until_known_and_summary_is_non_control(tmp_path):
    s = live(tmp_path)
    t0 = s.timings()
    assert t0["time_to_detect_min"] is None and t0["rollback_ok"] is None and t0["approval_latency_s"] is None
    warm(s); s.inject("mgmt_intrusion"); s.tick()
    s.notify("cert_in", "emulated notification")
    s.tick()
    summary = events(s, "summary")[-1]
    assert "audience" not in summary and summary["final"] is False
    t = summary["timings"]
    assert t["time_to_detect_min"] == 0.0 and t["clocks"]
    obligations = {e["seq"]: e for e in events(s, "clock_obligation")}
    assert all(c["obligation_id"] == obligations[c["obligation_seq"]]["obligation_id"]
               and c["policy_epoch"] == obligations[c["obligation_seq"]]["policy_epoch"] for c in t["clocks"])
    assert set(t["time_to_notify_min"]) == {c["regime"] for c in t["clocks"]}
    assert all(c["time_to_notify_min"] is not None for c in t["clocks"] if c["notify_role"] == "cert_in")
    assert "truth_class" not in json.dumps(summary)
    final = s.finish()["summary"]
    assert final["final"] is True and {"services", "network", "impact_cumulative"} <= set(final)
    s.close()


def test_25_headless_s1_has_final_summary_and_dip(tmp_path):
    from orca.live.headless import run
    s = run("S1", "mock", runs_dir=tmp_path, stage_fault=25)
    final = events(s, "summary")[-1]
    assert final["final"] is True
    net = final["network"]
    assert net["instant_pct_min"] < 100 and net["instant_pct_min"] < net["cumulative_pct"] <= 100
    t = final["timings"]
    assert t["failed_attempts"] == 1 and t["rollback_ok"] is True and t["time_to_restore_min"] is not None
    assert t["approval_latency_s"] == 180
    s.close()


def test_s1_degradation_is_visible_while_pb01_approval_is_pending(tmp_path):
    from orca.live.headless import run
    s = run("S1", "mock", approve_after=25, notify_after=5, stage_fault=25, runs_dir=tmp_path)
    ev = s.bus.all()
    request = next(e for e in ev if e["kind"] == "approval" and e.get("playbook") == "PB-01"
                   and e.get("status") == "requested")
    approved = next(e for e in ev if e["kind"] == "approval" and e.get("playbook") == "PB-01"
                    and e.get("status") == "approved")
    detection = next(e for e in ev if e["kind"] == "alert" and e["source"] == "M3"
                     and e["label"] == "attack-management-plane")
    drop = next(e for e in ev if e["kind"] == "tick" and
                any(e["sites"][site]["delivered_mbps"] == 0 for site in ("CHN-01", "CHN-02")))
    assert detection["t"] == 2 and s.timings()["time_to_detect_min"] == 2
    assert request["t"] == 2 and drop["t"] == 19 and approved["t"] == 27
    assert request["t"] < drop["t"] < approved["t"]
    assert all(drop["sites"][site]["mains_power"] and drop["sites"][site]["delivered_mbps"] == 0
               for site in ("CHN-01", "CHN-02"))
    s.close()


def test_26_catalogue_exposes_records_gaps_roles_from_files(tmp_path):
    s = live(tmp_path)
    cat = s.catalogue()
    assert {r["id"] for r in cat["records"]} == set(s.world.kb.records)
    assert {"id", "clause", "binding_status", "in_force_status", "instrument"} <= set(cat["records"][0])
    record = next(r for r in cat["records"] if r["id"] == "IN-CERTIN-DIR-2022-ii")
    original = s.world.kb.records[record["id"]]
    source = s.world.kb.sources[original["source"]]
    assert record["quote"] == original["quote"]
    assert record["summary"] == original["summary"]
    assert record["source_url"] == source["url"]
    assert record["source_sha256"] == source["sha256"]
    assert "verified_by" not in record  # public evidence, not local reviewer paths
    assert {g["id"] for g in cat["gaps"]} == set(s.world.kb.gaps)
    assert {"commander", "gap_analyst", "cert_in"} <= {r["name"] for r in cat["roles"]}
    assert all({"region", "objective", "everyday_impact"} <= set(x) for x in cat["scenarios"])
    s.close()


def test_27_allocation_never_exceeds_capacity_over_fractional_inputs():
    import random
    from orca.sim import service
    rnd = random.Random(7)
    checked = shed_cases = 0
    for _ in range(300):
        d = round(rnd.uniform(5, 450), 2)
        c = round(d * rnd.uniform(0.05, 0.99), 2)
        rec = {"site": "CHN-01", "demand_mbps": d, "capacity_mbps": c}
        service.allocate_minute([rec])
        rows = rec["services"]
        assert all(r["delivered_mbps"] >= 0 and r["delivered_mbps"] <= r["demand_mbps"] + 1e-9 for r in rows.values())
        assert sum(r["delivered_mbps"] for r in rows.values()) <= c + 0.005 * len(rows) + 1e-9, (d, c)
        assert rec["delivered_mbps"] <= c + 0.005 * len(rows) + 1e-9
        if any(r["pct"] < 100 for r in rows.values()):
            shed_cases += 1
        checked += 1
    assert checked == 300 and shed_cases > 150


def test_28_s2_storm_sheds_lower_priorities_and_restores(tmp_path):
    from orca.live.headless import run
    s = run("S2", "mock", runs_dir=tmp_path)
    ev = s.bus.all()
    short = [(e, sid) for e in ev if e["kind"] == "tick" for sid, x in e["sites"].items()
             if x["capacity_mbps"] > 0 and x["capacity_mbps"] < x["demand_mbps"] - 0.1]
    assert len(short) > 20                                  # real partial capacity, not an outage
    for e, sid in short:
        x = e["sites"][sid]
        assert x["delivered_mbps"] <= x["capacity_mbps"] + 0.05
        assert e["services"]["112"]["pct"] == 100 and e["services"]["hospital"]["pct"] == 100
        assert all(e["services"][service]["delivered_mbps"] == e["services"][service]["demand_mbps"]
                   for service in ("112", "hospital"))
    assert any(e["services"]["general"]["pct"] < 100 for e, _ in short)
    m4 = [e for e in ev if e["kind"] == "model" and e.get("model") == "M4" and e.get("shed")]
    assert m4 and all(e["solution"] == "feasible" and e["upstream_solution"] == "optimal" for e in m4) and all(x["service"] not in ("112", "hospital") for e in m4 for x in e["shed"])
    ex = events(s, "execute")
    assert ex and all(e["playbook"] == "PB-06" and e["result"] == "ok" and e["changed"] for e in ex)
    final = events(s, "summary")[-1]
    assert final["final"] and final["timings"]["time_to_restore_min"] is not None
    assert final["network"]["instant_pct_now"] == 100 and final["network"]["instant_pct_min"] < 100
    s.close()


def test_29_headless_default_leaves_no_scratch_dir():
    import os
    from orca.live.headless import run
    before = set(os.listdir("."))
    assert run("S0", "mock", session_hook=lambda s: s.closed or s.sim.t >= 0) is not None
    assert set(os.listdir(".")) == before


def test_30_api_notify_emits_met_clock_status_with_mock_llm(tmp_path):
    s = live(tmp_path)
    server = make_server(s, port=0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    warm(s); s.inject("mgmt_intrusion"); s.tick()
    before = events(s, "summary")[-1]["timings"]
    assert all(c["notified_at"] is None and c["met"] is None for c in before["clocks"])
    req = Request(base + "/api/notify", data=json.dumps({"to": "cert_in", "text": "Incident notice (emulated)"}).encode(),
                  headers={"Content-Type": "application/json"})
    assert json.load(urlopen(req))["ok"]
    after = events(s, "summary")[-1]["timings"]          # published by the API call itself, no further tick
    mine = [c for c in after["clocks"] if c["notify_role"] == "cert_in"]
    assert mine and all(c["met"] is True and c["time_to_notify_min"] is not None for c in mine)
    server.shutdown(); server.server_close(); s.close()


def test_31_m4_allocation_rows_match_tick_values(tmp_path):
    from orca.live.headless import run
    s = run("S2", "mock", runs_dir=tmp_path)
    ev = s.bus.all()
    ticks = {e["t"]: e for e in ev if e["kind"] == "tick"}
    m4 = [e for e in ev if e["kind"] == "model" and e.get("model") == "M4" and e["allocation"]]
    assert m4 and isinstance(m4[0]["allocation_priority"][0], str)
    for e in m4:
        assert not any("confidence" in k for k in e) and e["solution"] in ("optimal", "feasible")
        tick = ticks[e["t"]]
        by_site: dict = {}
        for row in e["allocation"]:
            assert {"site", "service", "demand_mbps", "granted_mbps", "shed_mbps"} <= set(row)
            svc = tick["sites"][row["site"]]["services"][row["service"]] if "services" in tick["sites"][row["site"]] else None
            by_site[row["site"]] = by_site.get(row["site"], 0) + row["granted_mbps"]
            if svc is not None:
                assert abs(svc["delivered_mbps"] - row["granted_mbps"]) <= 0.01
        for site, granted in by_site.items():
            assert abs(tick["sites"][site]["delivered_mbps"] - granted) <= 0.06
        assert {"112", "hospital"} <= {r["service"] for r in e["allocation"] if r["granted_mbps"] >= r["demand_mbps"]}
        for svc, agg in tick["services"].items():
            shed = sum(r["shed_mbps"] for r in e["allocation"] if r["service"] == svc)
            assert abs((agg["demand_mbps"] - agg["delivered_mbps"]) - shed) <= 0.06 or any(
                x["capacity_mbps"] <= 0 for x in tick["sites"].values()), (e["t"], svc)
    s.close()


def _verdict_ids(s):
    return {(e.get("rule") or e.get("rule_id") or e.get("topic"), e["verdict"], e.get("gap_id")) for e in s.bus.all() if e["kind"] == "verdict"}


def test_32_weather_fault_starts_no_reporting_clock_but_attacks_do(tmp_path):
    from orca.live.headless import run
    fault = run("S2", "mock", runs_dir=tmp_path / "a")
    assert not [e for e in fault.bus.all() if e["kind"] == "clock_obligation"]
    assert not fault.world.facts.get("triggers") and "applies" not in fault.world.facts
    assert not events(fault, "summary")[-1]["timings"]["clocks"]
    assert not [e for e in fault.bus.all() if e["kind"] == "msg" and e.get("audit_kind") == "msg_sent"]   # no cyber report
    assert not any(r.startswith(("IN-R-DEADLINE", "IN-R-CLOCKS")) for r, _, _ in _verdict_ids(fault))
    for name in ("S1", "N5"):
        attack = run(name, "mock", runs_dir=tmp_path / name)
        regimes = {e["regime"] for e in attack.bus.all() if e["kind"] == "clock_obligation"}
        assert {"IN-R-DEADLINE-CERTIN-ii", "IN-R-DEADLINE-TCSR-7-1", "IN-R-DEADLINE-CTIR-7-1-j"} <= regimes


def test_33_live_fault_then_attack_starts_clock_at_the_attack(tmp_path):
    s = live(tmp_path)
    s.inject("rain"); s.tick(); s.tick()
    assert not s.world.facts.get("triggers")
    warm(s); s.inject("mgmt_intrusion"); s.tick()
    assert s.world.facts.get("triggers") and any(e["kind"] == "clock_obligation" for e in s.bus.all())
    s.close()


def test_34_n5_india_to_eu_swap_changes_clocks_and_gaps(tmp_path):
    from orca.live.headless import run
    india = run("N5", "mock", kb="india", runs_dir=tmp_path / "in")
    eu = run("N5", "mock", kb="eu", runs_dir=tmp_path / "eu")
    clocks = lambda s: {c["regime"]: c["window_min"] for c in events(s, "summary")[-1]["timings"]["clocks"]}  # noqa: E731
    assert set(clocks(india)) == {"IN-R-DEADLINE-CERTIN-ii", "IN-R-DEADLINE-TCSR-7-1", "IN-R-DEADLINE-CTIR-7-1-j"}
    assert clocks(eu) == {"EU-R-DEADLINE-NIS2-23-4-a": 1440.0, "EU-R-DEADLINE-NIS2-23-4-b": 4320.0}
    gaps = lambda s: {g for _, _, g in _verdict_ids(s) if g}  # noqa: E731
    assert {"GAP-IN-01-REPORTING-CLOCKS", "GAP-IN-02-NO-DOWNSTREAM-WARNING", "GAP-IN-09-SPACE-CYBER-ADVISORY"} <= gaps(india)
    assert not any(g.startswith("GAP-IN-") for g in gaps(eu)) and gaps(eu) != gaps(india)


def test_35_mid_run_set_kb_eu_recomputes_clocks(tmp_path):
    s = live(tmp_path)
    warm(s); s.inject("mgmt_intrusion"); s.tick()
    assert any(e["kind"] == "clock_obligation" and e["regime"].startswith("IN-") for e in s.bus.all())
    s.set_kb("eu"); s.tick()
    assert any(e["kind"] == "clock_obligation" and e["regime"].startswith("EU-R-DEADLINE-NIS2") for e in s.bus.all())
    s.close()


def _clock_events(s):
    return [e for e in s.bus.all() if e["kind"] == "clock_obligation"]


def test_36_clock_events_carry_each_rules_own_trigger_and_start(tmp_path):
    from orca.live.headless import run
    s = run("N5", "mock", runs_dir=tmp_path)
    last = {e["regime"]: e for e in _clock_events(s)}
    assert {r: (e["trigger"], e["started_at"][:16]) for r, e in last.items()} == {
        "IN-R-DEADLINE-CERTIN-ii": ("noticing", "2026-11-10T19:05"),
        "IN-R-DEADLINE-TCSR-7-1": ("awareness", "2026-11-10T19:18"),
        "IN-R-DEADLINE-CTIR-7-1-j": ("occurrence", "2026-11-10T19:00")}
    assert all(e["due_at"][:13] == "2026-11-11T01" for e in last.values())   # six hours from each start
    assert "IN-R-CLOCKS" not in last                                         # a clock group is not a clock
    first = [e for e in _clock_events(s) if e["regime"] == "IN-R-DEADLINE-CERTIN-ii"]
    assert len(first) >= 2 and first[0]["started_at"] != first[-1]["started_at"]   # corrected when facts arrive


def test_37_missing_occurrence_is_insufficient_evidence_not_detection_time(tmp_path):
    s = live(tmp_path)
    warm(s); s.inject("mgmt_intrusion"); s.tick()
    assert "noticing" in s.world.facts["triggers"] and "occurrence" not in s.world.facts["triggers"]
    assert not [e for e in _clock_events(s) if e["regime"] == "IN-R-DEADLINE-CTIR-7-1-j"]
    assert any(e["kind"] == "verdict" and e.get("rule") == "IN-R-DEADLINE-CTIR-7-1-j"
               and e["verdict"] == "INSUFFICIENT_EVIDENCE" and "triggers.occurrence" in e["explanation"]
               for e in s.bus.all())
    s.close()


def test_38_gap_events_come_from_verdict_gap_ids_and_the_kb(tmp_path):
    from orca.live.headless import run
    s = run("N5", "mock", runs_dir=tmp_path)
    gaps = {e["gap_id"]: e for e in s.bus.all() if e["kind"] == "gap"}
    cited = {e["gap_id"] for e in s.bus.all() if e["kind"] == "verdict" and e.get("gap_id")}
    assert cited and cited == set(gaps)
    for gid, e in gaps.items():
        reg = s.world.kb.gaps[gid]
        assert (e["title"], e["status"], e["recommendation"], e["evidence"], e["global_examples"], e["source"]) == (
            reg["title"], reg["status"], reg.get("recommendation"), reg.get("evidence", []),
            reg.get("global_examples", []), "register")
        assert e["records"] and e["verdict"] in rules.VERDICTS


def test_39_gap_decision_emits_updated_state_and_rejects_bad_input(tmp_path):
    from orca.live.headless import run

    def decide(s):
        gid = next(e["gap_id"] for e in s.bus.all() if e["kind"] == "gap")
        n = len([e for e in s.bus.all() if e["kind"] == "gap"])
        with pytest.raises(ValueError):
            s.decide_gap("GAP-NOPE", "confirm", PIN)
        with pytest.raises(ValueError):
            s.decide_gap(gid, "invalid-decision")
        assert len([e for e in s.bus.all() if e["kind"] == "gap"]) == n
        s.decide_gap(gid, "reject")
        return gid, n, [e for e in s.bus.all() if e["kind"] == "gap"]
    gid, n, ev = run("N5", "mock", runs_dir=tmp_path, session_hook=decide)
    assert len(ev) == n + 1 and ev[-1]["gap_id"] == gid and ev[-1]["status"] == "rejected"
    assert ev[-1]["decision"]["decision"] == "reject" and ev[-1]["verified_by"] == "commander"


def test_40_kb_roundtrip_india_eu_india(tmp_path):
    from orca.live.headless import run

    def roundtrip(s):
        n0 = len(s.bus.all())
        s.set_kb("eu"); s.tick()
        n1 = len(s.bus.all())
        s.set_kb("india"); s.tick()
        assert s.set_kb("india")["changed"] is False
        return n0, n1, s.bus.all(), s.timings()
    n0, n1, ev, tim = run("N5", "mock", runs_dir=tmp_path, session_hook=roundtrip)
    changed = [e for e in ev if e["kind"] == "kb_changed"]
    assert [(e["kb"], e["previous"]) for e in changed] == [("eu", "india"), ("india", "eu")]
    assert ev[n0]["kind"] == "kb_changed" and ev[n1]["kind"] == "kb_changed"
    eu, back = ev[n0:n1], ev[n1:]
    kinds = lambda part, k: [e for e in part if e["kind"] == k]  # noqa: E731
    assert {e["regime"][:2] for e in kinds(eu, "clock_obligation")} == {"EU"}
    assert not [e for e in kinds(eu, "gap") if e["gap_id"].startswith("GAP-IN-")]
    assert {e["regime"][:2] for e in kinds(back, "clock_obligation")} == {"IN"}
    assert {"GAP-IN-01-REPORTING-CLOCKS", "GAP-IN-02-NO-DOWNSTREAM-WARNING",
            "GAP-IN-09-SPACE-CYBER-ADVISORY"} <= {e["gap_id"] for e in kinds(back, "gap")}
    assert kinds(eu, "summary") and kinds(back, "summary")                   # fresh summary after each switch
    assert kinds(ev[:n0], "clock_obligation") and len(ev) > n1 > n0          # history retained
    assert {c["regime"][:2] for c in tim["clocks"]} == {"IN"}


def test_41_rules_off_then_on_emits_rules_changed_and_reevaluates(tmp_path):
    from orca.live.headless import run

    def toggle(s):
        n0 = len(s.bus.all())
        assert s.set_rules(False)["changed"] is True and s.set_rules(False)["changed"] is False
        n1 = len(s.bus.all())
        s.set_rules(True); s.tick()
        return n0, n1, s.bus.all()
    n0, n1, ev = run("N5", "mock", runs_dir=tmp_path, session_hook=toggle)
    off, on = ev[n0:n1], ev[n1:]
    assert off[0]["kind"] == "rules_changed" and off[0]["rules"] is False
    assert not [e for e in off if e["kind"] in ("verdict", "clock_obligation", "gap")]
    assert [e["kind"] for e in off].count("summary") == 1
    assert on[0]["kind"] == "rules_changed" and on[0]["rules"] is True
    assert {e["gap_id"] for e in on if e["kind"] == "gap"} >= {"GAP-IN-01-REPORTING-CLOCKS"}
    assert {e["regime"] for e in on if e["kind"] == "clock_obligation"} >= {"IN-R-DEADLINE-CERTIN-ii"}
    assert [e for e in on if e["kind"] == "verdict"] and [e for e in on if e["kind"] == "summary"]


def test_42_rules_off_summary_has_no_clocks_and_back_on_restores_them(tmp_path):
    from orca.live.headless import run

    def toggle(s):
        before = s.timings()["clocks"]
        s.set_rules(False)
        off = [e for e in s.bus.all() if e["kind"] == "summary"][-1]["timings"]
        s.set_rules(True)
        on = [e for e in s.bus.all() if e["kind"] == "summary"][-1]["timings"]
        return before, off, on
    before, off, on = run("N5", "mock", runs_dir=tmp_path, session_hook=toggle)
    assert before and off["clocks"] == [] and off["time_to_notify_min"] == {}
    assert {c["regime"] for c in on["clocks"]} == {c["regime"] for c in before}


def test_39_s1_terminals_lost_while_mains_power_stays_on(tmp_path):
    from orca.live.headless import run
    s = run("S1", "mock", runs_dir=tmp_path)
    ticks = events(s, "tick")
    assert all(isinstance(x["mains_power"], bool) for e in ticks for x in e["sites"].values())
    lost = [(e["t"], sid, x) for e in ticks for sid, x in e["sites"].items()
            if sid in ("CHN-01", "CHN-02") and x["active_path"] == "A" and x["terminals_up"] == 0]
    assert lost and all(x["mains_power"] is True and x["delivered_mbps"] == 0 and x["state"] == "down" for _, _, x in lost)
    # the drop follows the scripted wipe (t=18) and modem loss (t=24), not the first M3 alert
    assert min(t for t, _, _ in lost) == 24
    s.close()


def test_operator_question_reaches_requested_agent_unchanged(tmp_path, monkeypatch):
    s = live(tmp_path)
    try:
        assert s.adviser.llm is None  # mock mode remains deterministic
        received = []
        monkeypatch.setattr(s.agents["cert_in"], "run", lambda task: received.append(task) or {"text": "Read the cited sources", "citations": {"accepted": []}})
        question = "Explain CERT-In Direction (ii) and retrieve the reporting trigger."
        s.ask("cert_in", question)
        assert received == [question]
    finally:
        s.close()
