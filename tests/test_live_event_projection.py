"""Public stream must faithfully project guarded execution and approval evidence."""
from orca.live.session import LiveSession


def _events(session, kind):
    return [event for event in session.bus.all() if event['kind'] == kind]


def test_pb01_approval_and_rollout_share_plan_hash(tmp_path):
    session = LiveSession(runs_dir=tmp_path)
    try:
        plan = session.rem.request_approval('satellite_operator', 'PB-01', ['admin'], {}, 'contain account')
        session._flush_audit()
        result = session.approve(plan['hash'])
        assert result['ok']
        stages = [e for e in _events(session, 'patch_stage') if e['playbook'] == 'PB-01']
        assert [(e['pct'], e['health']) for e in stages] == [(5, 'ok'), (25, 'ok'), (100, 'ok')]
        assert all(e['plan_hash'] == plan['hash'] for e in stages)
        approvals = [e for e in _events(session, 'approval') if e.get('playbook') == 'PB-01']
        assert [(e['status'], e['hash']) for e in approvals] == [('requested', plan['hash']), ('approved', plan['hash'])]
        attacks = [e for e in _events(session, 'reattack') if e['playbook'] == 'PB-01']
        verified = next(r for r in result['result']['network'] if r['event'] == 'verified')
        assert verified['reattack'] and len(attacks) == len(verified['reattack'])
        assert all(e['plan_hash'] == plan['hash'] for e in attacks)
        assert [e['blocked'] for e in attacks] == [not r['succeeded'] for r in verified['reattack']]
        assert session.world.audit.verify() is None
    finally:
        session.close()


def test_rejection_uses_same_public_hash_and_audit_is_unchanged(tmp_path):
    session = LiveSession(runs_dir=tmp_path)
    try:
        plan = session.rem.request_approval('satellite_operator', 'PB-01', ['admin'], {}, 'review')
        session._flush_audit()
        session.reject(plan['hash'], 'not now')
        rejected = [e for e in _events(session, 'approval') if e['status'] == 'rejected'][-1]
        assert rejected['hash'] == rejected['plan_hash'] == plan['hash']
        audit = [e for e in session.world.audit.entries() if e['kind'] == 'rejected'][-1]
        assert audit['payload'] == {'plan_hash': plan['hash'], 'reason': 'not now'}
        assert session.world.audit.verify() is None
    finally:
        session.close()


def test_refused_failover_has_no_fabricated_rollout(tmp_path):
    session = LiveSession(runs_dir=tmp_path)
    try:
        plan = session.rem.request_approval('mobile_operator', 'PB-06', ['CHN-01'], {'path': 'not-offered'}, 'unsafe path')
        assert not plan['clone_test']['passed']
        session._flush_audit()
        result = session.approve(plan['hash'])
        assert not result['ok']
        assert not [e for e in _events(session, 'patch_stage') if e['playbook'] == 'PB-06']
        assert not [e for e in _events(session, 'reattack') if e['playbook'] == 'PB-06']
        assert any(e.get('audit_kind') == 'execute_refused' for e in _events(session, 'execute'))
    finally:
        session.close()


def test_no_reattack_is_inferred_when_result_omits_outcome(tmp_path):
    session = LiveSession(runs_dir=tmp_path)
    try:
        session._emit_rollout('PB-01', {'stages': [{'pct': 5, 'healthy': True}], 'network': [
            {'event': 'verified', 'reattack': [{'attack': 'probe', 'target': 'SAT-MGMT'}]}]})
        assert [e['pct'] for e in _events(session, 'patch_stage')] == [5]
        assert not _events(session, 'reattack')
    finally:
        session.close()


def test_recorded_successful_reattack_is_not_reported_as_blocked(tmp_path):
    session = LiveSession(runs_dir=tmp_path)
    try:
        session._emit_rollout('PB-01', {'ok': False, 'stages': [{'pct': 100, 'healthy': False}],
            'network': [{'event': 'verified', 'reattack': [
                {'attack': 'probe', 'target': 'SAT-MGMT', 'succeeded': True}]}]}, plan_hash='plan-1')
        stage = _events(session, 'patch_stage')[-1]
        attack = _events(session, 'reattack')[-1]
        assert stage['health'] == 'fail' and stage['plan_hash'] == 'plan-1'
        assert attack['blocked'] is False and attack['plan_hash'] == 'plan-1'
    finally:
        session.close()
