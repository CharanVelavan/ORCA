import json
from pathlib import Path

import pytest

from finetune import eval_cases as ev


def case(ident, scenario='N4', **extra):
    return {'id': ident, 'scenario': scenario, 'role': 'satellite_operator', 'messages': [{'role': 'user', 'content': 'test'}],
            'expect': {'first_tool': 'read_alerts', 'never_tools': ['execute_playbook']}, **extra}


def call(name, args):
    return {'function': {'name': name, 'arguments': args}}


def setup_eval(monkeypatch, tmp_path, rows, replies):
    path = tmp_path / 'cases.jsonl'
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    monkeypatch.setattr(ev, 'OUT', tmp_path / 'out')
    instances = []
    class Fake:
        def __init__(self, **kwargs):
            self.base_url = 'http://localhost:8000/v1'; self.replies = list(replies); self.requests = []; instances.append(self)
        def chat(self, messages, tools=None):
            self.requests.append((messages, tools)); return self.replies.pop(0)
    monkeypatch.setattr(ev, 'LLMClient', Fake)
    return path, instances


def test_real_json_object_scoring_and_unsafe_attempts(monkeypatch, tmp_path):
    rows = [case('a'), case('b', 'N5'), case('c', 'CAP'), case('d')]
    replies = [
        {'tool_calls': [call('read_alerts', '{bad')]},
        {'tool_calls': [call('execute_playbook', '[]'), call('execute_playbook', '{}')]},
        {'tool_calls': [call('read_alerts', '{"source":"M3"}')]},
        {'content': 'No tool needed', 'tool_calls': []},
    ]
    path, clients = setup_eval(monkeypatch, tmp_path, rows, replies)
    result, output = ev.evaluate('test-model', cases_path=path)
    assert result['n_cases'] == 4 and result['case_ids'] == ['a', 'b', 'c', 'd']
    assert result['valid_json'] == .5
    assert result['valid_json_numerator'] == 2 and result['valid_json_denominator'] == 4
    assert result['unsafe_exec'] == result['unsafe_tool_attempts'] == 1
    assert result['unsafe_tool_call_count'] == 2
    assert result['scenario_verdicts_ok'] == {'N4': None, 'N5': None, 'CAP': None}
    assert result['tools_source_counts'] == {'case': 0, 'current_role': 4}
    assert clients[0].requests[0][1] and output.exists()
    assert 'no tool was executed' in result['metric_notes']['unsafe_exec'].lower()


def test_no_tool_calls_have_no_json_denominator(monkeypatch, tmp_path):
    path, _ = setup_eval(monkeypatch, tmp_path, [case('a')], [{'content':'done', 'tool_calls':[]}])
    result, _ = ev.evaluate('model', cases_path=path)
    assert result['valid_json'] is None and result['valid_json_denominator'] == 0


def test_missing_empty_and_nonheld_cases_fail_before_client(monkeypatch, tmp_path):
    def forbidden_client(**kwargs): raise AssertionError('must not create client')
    monkeypatch.setattr(ev, 'LLMClient', forbidden_client)
    with pytest.raises(FileNotFoundError): ev.evaluate('model', cases_path=tmp_path/'absent')
    path = tmp_path/'empty.jsonl'; path.write_text(' \n')
    with pytest.raises(ValueError, match='held-out'): ev.evaluate('model', cases_path=path)
    path.write_text(json.dumps(case('a','S1'))+'\n')
    with pytest.raises(ValueError, match='held-out'): ev.evaluate('model', cases_path=path)


def test_limit_is_ordered_and_preserves_explicit_schema(monkeypatch, tmp_path):
    rows = [case('skip','S1'),case('first',tools=[]),case('second','N5'),case('third','CAP')]
    path, clients = setup_eval(monkeypatch, tmp_path, rows, [{'tool_calls':[]},{'tool_calls':[]}])
    result, _ = ev.evaluate('model', cases_path=path, limit=2)
    assert result['case_ids'] == ['first', 'second'] and result['n_cases'] == 2
    assert result['heldout_cases_available'] == 3 and result['limit'] == 2
    assert clients[0].requests[0][1] == [] and clients[0].requests[1][1]
    assert result['tools_source_counts'] == {'case': 1, 'current_role': 1}
    with pytest.raises(ValueError, match='positive'): ev.evaluate('model', cases_path=path, limit=0)


def test_unknown_role_fails_before_any_request(monkeypatch, tmp_path):
    path, clients = setup_eval(monkeypatch, tmp_path, [case('a',role='unknown')], [])
    with pytest.raises(ValueError, match='role'): ev.evaluate('model', cases_path=path)
    assert not clients


def test_strict_json_and_endpoint_redaction(monkeypatch):
    assert ev._parse_arguments(call('tool', '{"value": NaN}')) is None
    assert ev._parse_arguments(call('tool', 'null')) is None
    assert ev._parse_arguments(call('tool', '{}')) == {}
    assert ev._parse_arguments({'function': {'name': 'tool'}}) is None
    assert ev._endpoint_origin('https://user:password@example.test:8443/v1/private?key=secret') == 'https://example.test:8443'
    monkeypatch.setenv('LLM_API_KEY', 'secret')
    assert ev._endpoint_origin('https://secret.example.test/v1') is None
