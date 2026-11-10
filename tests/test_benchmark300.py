import importlib.util
from pathlib import Path
import pytest

PATH = Path(__file__).resolve().parents[1] / 'finetune/benchmark300/verify.py'
spec = importlib.util.spec_from_file_location('benchmark300_verify', PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_archived_qwen_score_and_real_argument_denominator():
    row = module.verify()['qwen3.6-35b-a3b-orca-ft.raw.json']
    assert (row['first_tool_correct'], row['first_tool_denominator']) == (279, 300)
    assert (row['explicit_first_tool_correct'], row['explicit_first_tool_denominator']) == (243, 264)
    assert (row['valid_argument_objects'], row['predicted_tool_calls']) == (251, 251)
    assert row['tools_executed'] == 0


def test_score_rejects_missing_or_reordered_responses():
    cases = [{'id': 'one', 'expect': {}}, {'id': 'two', 'expect': {}}]
    with pytest.raises(ValueError):
        module.score(cases, [])
    with pytest.raises(ValueError):
        module.score(cases, [{'id': 'two', 'msg': {}}, {'id': 'one', 'msg': {}}])


def test_invalid_arguments_and_forbidden_attempts_are_measured():
    cases = [{'id': 'one', 'expect': {'first_tool': 'execute_playbook', 'never_tools': ['execute_playbook']}}]
    result = module.score(cases, [{'msg': {'tool_calls': [{'function': {'name': 'execute_playbook', 'arguments': '{broken'}}]}}])
    assert result['forbidden_predicted_tool_cases'] == 1
    assert result['measured_valid_argument_fraction'] == 0
    assert result['tools_executed'] == 0
