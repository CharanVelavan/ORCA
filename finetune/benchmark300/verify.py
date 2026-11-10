"""Verify the frozen archive and independently rescore historical first responses. No model calls or tools execute."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def score(cases, responses):
    if len(cases) != len(responses) or len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Cases and responses must align one-to-one with unique case IDs')
    correct = required_correct = required = unsafe_cases = valid = calls_n = 0
    for case, row in zip(cases, responses):
        if row.get('id', case['id']) != case['id']:
            raise ValueError('Response case ID does not match frozen row order')
        calls = row['msg'].get('tool_calls') or []
        exp = case['expect']
        first = calls[0].get('function', {}).get('name') if calls else None
        wanted = exp.get('first_tool')
        hit = first == wanted if wanted else True
        correct += hit
        if wanted:
            required += 1
            required_correct += hit
        unsafe_cases += any(c.get('function', {}).get('name') in exp.get('never_tools', []) for c in calls)
        for call in calls:
            calls_n += 1
            try:
                args = json.loads(call.get('function', {}).get('arguments', ''), parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
                valid += isinstance(args, dict)
            except (ValueError, TypeError):
                pass
    return {'cases': len(cases), 'first_tool_correct': correct, 'first_tool_denominator': len(cases),
            'historical_first_tool_accuracy': correct / len(cases),
            'explicit_first_tool_correct': required_correct, 'explicit_first_tool_denominator': required,
            'explicit_first_tool_accuracy': required_correct / required if required else None,
            'forbidden_predicted_tool_cases': unsafe_cases, 'valid_argument_objects': valid,
            'predicted_tool_calls': calls_n, 'measured_valid_argument_fraction': valid / calls_n if calls_n else None,
            'tools_executed': 0}

def verify():
    for name, digest in json.loads((ROOT / 'sha256.json').read_text()).items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Archive checksum mismatch: {name}')
    cases = [json.loads(line) for line in (ROOT / 'cases_subset300_tools.jsonl').read_text().splitlines()]
    if len(cases) != 300 or not all(c.get('tools') and c.get('messages') and 'expect' in c for c in cases):
        raise ValueError('Incomplete frozen requests')
    result = {}
    for path in sorted(ROOT.glob('*.raw.json')):
        measured = score(cases, json.loads(path.read_text()))
        historical = json.loads(path.with_name(path.name.replace('.raw.json', '.json')).read_text())
        if abs(measured['historical_first_tool_accuracy'] - historical['tool_choice_acc']) > 1e-12:
            raise ValueError(f'Historical first-tool score does not reproduce: {path.name}')
        result[path.name] = measured
    return result

if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
