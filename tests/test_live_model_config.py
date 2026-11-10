import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from orca.live.model_config import ModelConfig
from orca.live.server import make_server
from orca.live.session import LiveSession


class Endpoint(BaseHTTPRequestHandler):
    requests = []
    tool_response = True

    def log_message(self, *args):
        pass

    def respond(self, value):
        raw = json.dumps(value).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        self.requests.append((self.path, self.headers.get('Authorization')))
        self.respond({'data': [{'id': 'qwen-test'}]})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.requests.append((self.path, self.headers.get('Authorization'), body))
        calls = [{'type': 'function', 'function': {'name': 'orca_probe', 'arguments': '{"value":"ok"}'}}] if self.tool_response else []
        self.respond({'choices': [{'message': {'tool_calls': calls}}]})


@pytest.fixture
def endpoint():
    Endpoint.requests = []
    Endpoint.tool_response = True
    server = ThreadingHTTPServer(('127.0.0.1', 0), Endpoint)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}/v1'
    server.shutdown()
    server.server_close()
    thread.join()


def post(url, value):
    request = Request(url, data=json.dumps(value).encode(), headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def test_config_probes_redacts_and_restarts(tmp_path, endpoint, monkeypatch):
    monkeypatch.delenv('LLM_API_KEY', raising=False)
    session = LiveSession(runs_dir=tmp_path)
    server = make_server(session, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    secret = 'private-test-key'
    try:
        configured = post(base + '/api/model-config', {'base_url': endpoint, 'model': 'qwen-test', 'api_key': secret})
        assert configured['key_set'] and secret not in json.dumps(configured)
        assert secret not in json.dumps(json.load(urlopen(base + '/api/model-config')))
        assert post(base + '/api/model-config/discover', {})['models'] == ['qwen-test']
        probe = post(base + '/api/model-config/test', {})
        assert probe['reachable'] and probe['tool_call_compatible']
        assert Endpoint.requests[-1][1] == 'Bearer ' + secret
        assert Endpoint.requests[-1][2]['tools'][0]['function']['name'] == 'orca_probe'
        assert session.llm_mode == 'mock'  # staged, existing session unchanged
        post(base + '/api/session', {'llm': 'local'})
        client = next(iter(session.agents.values())).llm
        assert client.base_url == endpoint and client.model == 'qwen-test' and client.api_key == secret
        assert session.state()['session']['llm_source'] == 'live'
        assert secret not in json.dumps(session.state())
        assert secret not in json.dumps(session.bus.all())
        post(base + '/api/model-config', {'api_key': ''})
        assert session.model_config.public()['key_set']
        post(base + '/api/model-config', {'clear_key': True})
        assert not session.model_config.public()['key_set']
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
        session.close()


def test_invalid_urls_and_probe_failures_are_safe(endpoint):
    config = ModelConfig()
    for value in ('file:///etc/passwd', 'http://user:pass@host/v1', 'https://example.com/v1?key=secret'):
        with pytest.raises(ValueError):
            config.update({'base_url': value})
    config.update({'base_url': endpoint, 'model': 'qwen-test', 'api_key': 'secret'})
    Endpoint.tool_response = False
    assert config.test({})['tool_call_compatible'] is False
    with pytest.raises(ValueError) as error:
        config.test({'base_url': 'http://127.0.0.1:1/v1'})
    assert 'secret' not in str(error.value)


def test_scenario_detail_is_director_only_and_rejects_paths(tmp_path):
    session = LiveSession(runs_dir=tmp_path)
    try:
        detail = session.scenario_detail('S1')
        assert detail['audience'] == 'control' and detail['schedule'][0]['t'] == 0
        assert detail['story'] and detail['schedule'][0]['what']
        with pytest.raises(ValueError):
            session.scenario_detail('../../etc/passwd')
    finally:
        session.close()


def test_reporting_clock_identity_excludes_notice_from_previous_policy_epoch(tmp_path):
    session = LiveSession(runs_dir=tmp_path)
    try:
        from orca import rules
        deadline = rules.load_rules('IN')['deadline_rules'][0]
        regime = deadline['id']
        start = session.sim.ts(0)
        due = session.sim.ts(360)
        session.emit('clock_obligation', regime=regime, started_at=start, due_at=due,
                     obligation_id='old', policy_epoch=-1)
        session.emit('msg', audit_kind='msg_sent', recipients=['cert_in', 'regulator'])
        old = session.timings()['clocks'][0]
        assert old['obligation_id'] == 'old' and old['notified_at'] is not None
        change = session.emit('rules_changed', rules=True)
        new = session.emit('clock_obligation', regime=regime, started_at=start, due_at=due,
                           obligation_id='new', policy_epoch=change['seq'])
        clock = session.timings()['clocks'][0]
        assert clock['obligation_id'] == 'new'
        assert clock['obligation_seq'] == new['seq']
        assert clock['policy_epoch'] == change['seq']
        assert clock['notified_at'] is None and clock['met'] is None
        session.emit('msg', audit_kind='msg_sent', recipients=['cert_in', 'regulator'])
        assert session.timings()['clocks'][0]['notified_at'] is not None
    finally:
        session.close()


def test_same_reporting_obligation_keeps_identity_on_reevaluation(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from orca import rules
    session = LiveSession(runs_dir=tmp_path)
    try:
        value = {'rule_id': 'R-TEST', 'verdict': 'COMPLIANT', 'topic': 'reporting',
                 'record_ids': [], 'explanation': 'test evaluation', 'trigger': 'awareness',
                 'starts': session.sim.ts(0), 'deadline': session.sim.ts(360)}
        monkeypatch.setattr(rules, 'evaluate', lambda *_: [SimpleNamespace(to_dict=lambda: dict(value))])
        session._run_rules()
        value['verdict'] = 'VIOLATION'
        session._run_rules()
        obligations = [e for e in session.bus.all() if e['kind'] == 'clock_obligation' and e['regime'] == 'R-TEST']
        assert len(obligations) == 2
        assert obligations[0]['obligation_id'] == obligations[1]['obligation_id']
    finally:
        session.close()
