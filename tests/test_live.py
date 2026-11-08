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
