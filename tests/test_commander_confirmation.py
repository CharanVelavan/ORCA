"""Commander HTTP actions use explicit confirmation without a PIN."""
import json
import threading
from urllib.request import Request, urlopen

from orca.live.server import make_server
from orca.live.session import LiveSession


def test_commander_http_actions_accept_no_pin(tmp_path, monkeypatch):
    monkeypatch.setenv('ORCA_COMMANDER_PIN_SHA256', 'obsolete-value')
    session = LiveSession(runs_dir=tmp_path, pin_sha256='obsolete-value')
    server = make_server(session, port=0)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    base = f'http://127.0.0.1:{server.server_port}'

    def post(path, body):
        request = Request(base + path, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
        return json.load(urlopen(request, timeout=5))

    try:
        grant = post('/api/autonomy', {'mode': 'AUTO', 'sites': ['CHN-01'], 'playbooks': ['PB-10'], 'minutes': 5})
        assert grant['ok'] and grant['grant']['sites'] == ['CHN-01']
        assert post('/api/autonomy', {'mode': 'MANUAL', 'minutes': 5})['ok']
        assert post('/api/kill', {'reason': 'Commander HTTP test'})['ok']
        assert session.rem.killed
        assert post('/api/kill/release', {})['ok']
        assert session.rem.killed is None
        gap_id = next(iter(session.world.kb.gaps))
        assert post('/api/gap', {'gap_id': gap_id, 'decision': 'confirm'})['ok']
        assert session._gap_decisions[gap_id]['decision'] == 'confirm'
        plan = session.rem.request_approval('satellite_operator', 'PB-01', ['noc-vendor-7'], {}, 'Review exact plan')
        assert post('/api/approve', {'hash': plan['hash']})['ok']
        assert session.rem.plans[plan['hash']]['executed']
        assert not any(e.get('kind') == 'pin_refused' for e in session.bus.all())
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
        session.close()
