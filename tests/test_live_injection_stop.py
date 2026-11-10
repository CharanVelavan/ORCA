"""Director stop affects future emulated conditions, never prior effects."""
import pytest
from orca.live.session import LiveSession


def test_stop_pending_and_running_are_exact_once_and_preserve_other_conditions(tmp_path):
    s = LiveSession(runs_dir=tmp_path, scenario='S0')
    try:
        first = s.inject('jamming', 'CHN-02', 5)['injection']
        second = s.inject('jamming', 'CHN-03', 5)['injection']
        state = s.truth()
        assert state['t'] == -1
        assert {row['id'] for row in state['running_injections']} == {first['id'], second['id']}
        assert all(row['state'] == 'pending' and row['cancellable'] for row in state['running_injections'])
        assert s.stop_injection(injection_id=first['id'])['stopped'] == [first['id']]
        with pytest.raises(ValueError, match='no cancellable'):
            s.stop_injection(injection_id=first['id'])
        s.tick()
        assert not s.sim.conditions[0].active(s.sim.t)
        assert s.sim.conditions[1].active(s.sim.t)
        assert s.truth()['running_injections'][0]['state'] == 'active'
        s.stop_injection(injection_id=second['id'])
        s.tick()
        assert not s.sim.conditions[1].active(s.sim.t)
        assert not s.truth()['running_injections']
        stopped = [e for e in s.bus.all() if e['kind'] == 'inject_stop']
        assert len(stopped) == 2 and all(e['audience'] == 'control' for e in stopped)
    finally:
        s.close()


def test_stop_does_not_undo_offered_route_and_expired_cannot_stop(tmp_path):
    s = LiveSession(runs_dir=tmp_path, scenario='S0')
    try:
        lure = s.inject('failover_lure', 'CHN-02', 5)['injection']
        assert s.sim.routes['CHN-02']['C']['gateway'] == 'GW-XX'
        s.stop_injection(injection_id=lure['id'])
        assert s.sim.routes['CHN-02']['C']['gateway'] == 'GW-XX'
        one = s.inject('rain', 'CHN-01', 1)['injection']
        s.tick()
        active = next(row for row in s.truth()['running_injections'] if row['id'] == one['id'])
        assert active['state'] == 'active' and not active['cancellable']
        with pytest.raises(ValueError, match='no cancellable'):
            s.stop_injection(injection_id=one['id'])
        s.tick()
        assert not any(row['id'] == one['id'] for row in s.truth()['running_injections'])
    finally:
        s.close()


def test_director_truth_and_stop_api_are_separate_from_operator_state(tmp_path):
    import json
    import threading
    from urllib.request import Request, urlopen
    from orca.live.server import make_server
    s = LiveSession(runs_dir=tmp_path, scenario='S0')
    server = make_server(s, port=0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_address[1]}'
    def post(path, body):
        return json.load(urlopen(Request(base + path, data=json.dumps(body).encode(), headers={'Content-Type':'application/json'}, method='POST')))
    try:
        item = post('/api/inject', {'kind':'rain','target':'CHN-01','duration_min':5})['injection']
        truth = json.load(urlopen(base + '/api/truth'))
        assert [row['id'] for row in truth['running_injections']] == [item['id']]
        public = json.load(urlopen(base + '/api/state'))
        assert 'running_injections' not in public and 'injections' not in public
        assert post('/api/inject/stop', {'id':item['id']})['stopped'] == [item['id']]
        assert not json.load(urlopen(base + '/api/truth'))['running_injections']
    finally:
        server.shutdown(); server.server_close(); s.close()
