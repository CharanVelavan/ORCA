from orca.runner import run_scenario
from orca.audit import AuditLog


def test_s1_mock_requests_clean_path_failover(tmp_path):
    trace = tmp_path / 'trace.jsonl'
    out = run_scenario('S1', llm_mode='mock', audit_path=trace)
    entries = AuditLog(trace).entries()
    plans = [e for e in entries if e['kind'] == 'approval_requested' and e['payload'].get('playbook') == 'PB-06']
    assert plans
    assert plans[0]['payload']['params'] == {'path': 'B'}
    assert plans[0]['payload']['targets'] == ['CHN-01', 'CHN-02']
    assert all(v['found'] for v in out['expected'])


def test_no_rules_removes_rule_tool(tmp_path):
    trace = tmp_path / 'norules.jsonl'
    run_scenario('S1', llm_mode='mock', rules_enabled=False, audit_path=trace)
    entries = AuditLog(trace).entries()
    tasks = [e for e in entries if e['kind'] == 'agent_task']
    assert tasks
    assert all('run_rule_engine' not in e['payload']['tools'] for e in tasks)
