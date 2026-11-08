"""Dashboard: the server starts and the API returns parsed events. Offline, stdlib only."""
import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from dashboard import adapter
from dashboard.server import SAMPLES, make_server

REPO = Path(__file__).resolve().parents[1]
MOCK = REPO / "runs" / "mock-s1.jsonl"      # runs/ is gitignored: that test skips when it is absent
MOCK_ENV = __import__("os").environ.get("ORCA_MOCK_S1")   # optional path to a copy of mock-s1.jsonl
if MOCK_ENV:
    MOCK = Path(MOCK_ENV)


def _serve(runs_dir, run_files=()):
    srv, _ = make_server(runs_dir, run_files, host="127.0.0.1", port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def _get(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return r.status, r.read()


def _json(url):
    return json.loads(_get(url)[1])


@pytest.fixture
def server(tmp_path):
    from orca.audit import AuditLog
    log = AuditLog(tmp_path / "t1-rules-fake.jsonl")
    log.append("event_released", "scenario", {"alert_id": "EV-1", "visible_to": ["satellite_operator"], "t": 0}, "2026-11-10T19:00:00+05:30")
    log.append("agent_step", "satellite_operator", {"turn": 1, "tool": "read_alerts", "args": {}, "rationale": "look",
               "citations_accepted": [], "citations_rejected": [],
               "result": {"alerts": [{"id": "EV-1", "detail": "M1 flags a login", "label": "anomaly", "sites": ["CHN-02"], "source": "M1"}]}},
               "2026-11-10T19:00:00+05:30")
    log.append("something_new", "runner", {"x": 1}, "2026-11-10T19:05:00+05:30")      # unknown kind must not break anything
    with log.path.open("a") as fh:
        fh.write("{not json\n")                                                          # half-written line is skipped
    srv, base = _serve(tmp_path, [])
    yield base, tmp_path
    srv.shutdown()
    srv.server_close()


def test_server_serves_page_and_lists_runs(server):
    base, _ = server
    code, body = _get(base + "/")
    assert code == 200 and b"ORCA-NTN" in body and b"Emulated network" in body
    names = {r["name"] for r in _json(base + "/api/runs")["runs"]}
    assert "t1-rules-fake" in names and "s1-rules-sample" in names     # run files + bundled samples


def test_api_returns_parsed_events_and_tolerates_unknown_kinds(server):
    base, _ = server
    run = _json(base + "/api/run?name=t1-rules-fake")
    assert [e["type"] for e in run["events"]] == ["scenario_event", "tool_call", "other"]
    assert run["events"][0]["summary"].startswith("M1 flags a login")      # detail taken from the read_alerts result
    assert run["stats"]["bad_lines"] == 1
    assert run["meta"]["rules"] is True and run["meta"]["llm"] == "fake"   # from the file name
    assert run["net"][-1]["sites"]["CHN-02"]["state"] == "suspect"
    assert run["chain"]["ok"] is True                                       # the junk line is skipped; the real entries still verify
    assert json.dumps(run)


def test_unknown_run_and_path_traversal_are_refused(server):
    base, _ = server
    for name in ("nope", "../../etc/passwd", "..%2f..%2fetc%2fpasswd"):
        with pytest.raises(urllib.error.HTTPError) as e:
            _get(base + "/api/run?name=" + name)
        assert e.value.code == 404
    with pytest.raises(urllib.error.HTTPError) as e:
        _get(base + "/..%2f..%2fREADME.md")
    assert e.value.code == 404


def test_kill_switch_is_state_only_in_replay(server):
    base, _ = server
    assert _json(base + "/api/status")["mode"] == "replay"
    req = urllib.request.Request(base + "/api/kill", data=b"{}", method="POST")
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req, timeout=10)
    assert e.value.code == 409
    assert "Replay only" in json.loads(e.value.read())["message"]


@pytest.mark.skipif(not MOCK.exists(), reason="runs/mock-s1.jsonl not present (runs/ is gitignored)")
def test_mock_s1_run_is_parsed():
    srv, base = _serve(MOCK.parent, [MOCK])
    try:
        assert _json(base + "/api/runs")["default"] == "mock-s1"
        run = _json(base + "/api/run?name=mock-s1")
        assert run["stats"]["entries"] == 56 and run["chain"]["ok"] is True
        assert {e["type"] for e in run["events"]} >= {"scenario_event", "task", "tool_call", "final"}
        assert {v["verdict"] for v in run["verdicts"]} >= {"AMBIGUITY", "CONFLICT", "POTENTIAL_GAP"}
        assert "GAP-IN-01-REPORTING-CLOCKS" in {g["id"] for g in run["gaps"]}
        assert {a["name"] for a in run["agents"]} >= {"satellite_operator", "mobile_operator"}
    finally:
        srv.shutdown()
        srv.server_close()


def test_bundled_samples_show_every_panel_and_pair_up():
    on = adapter.build_run(SAMPLES / "s1-rules-sample.jsonl")
    off = adapter.build_run(SAMPLES / "s1-norules-sample.jsonl")
    assert on["chain"]["ok"] is True and off["chain"]["ok"] is True
    assert {v["verdict"] for v in on["verdicts"]} >= {"COMPLIANT", "AMBIGUITY", "CONFLICT", "POTENTIAL_GAP"}
    assert all(v["record_ids"] for v in on["verdicts"])
    statuses = {h["status"] for a in on["approvals"] for h in a["history"]}
    assert statuses >= {"requested", "approved", "rejected", "executed"}
    assert {g["id"] for g in on["gaps"]} >= {"GAP-IN-01-REPORTING-CLOCKS", "GAP-IN-02-NO-DOWNSTREAM-WARNING", "GAP-IN-09-SPACE-CYBER-ADVISORY"}
    assert any(a["killed"] for a in on["autonomy"]) and any(a["mode"] == "ASSISTED" for a in on["autonomy"])
    assert on["net"][-1]["sites"]["CHN-02"]["state"] == "healed" and on["net"][-1]["sites"]["CHN-02"]["gateway"] == "GW-IN-2"
    assert off["verdicts"] == [] and off["meta"]["has_rule_engine"] is False
    assert any(m["rejected"] for m in on["messages"])


def test_adapter_survives_garbage(tmp_path):
    p = tmp_path / "x.jsonl"
    p.write_text('[1,2]\n{"kind": 5, "payload": "str", "ts": "never"}\n{"seq": 1}\n\n{"kind":"approved","payload":{"plan_hash":"zz"}}\n')
    run = adapter.build_run(p)
    assert run["stats"]["entries"] == 3 and run["stats"]["bad_lines"] == 1
    assert run["chain"]["ok"] is None
