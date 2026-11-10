"""Run all frozen requests against a fresh endpoint, preserving IDs, settings and raw assistant responses."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1]))
from orca.llm import LLMClient
from verify import score, verify


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', required=True, help='Exact served model ID; credentials belong in LLM_API_KEY')
    p.add_argument('--base-url', default=os.environ.get('LLM_BASE_URL', 'http://127.0.0.1:8000/v1'))
    p.add_argument('--output', type=Path, required=True, help='New results directory; existing results are never overwritten')
    args = p.parse_args()
    verify()
    args.output.mkdir(parents=True, exist_ok=False)
    cases = [json.loads(line) for line in (ROOT / 'cases_subset300_tools.jsonl').read_text().splitlines()]
    client = LLMClient(model=args.model, base_url=args.base_url, mode='live', temperature=0, thinking=False, max_tokens=1024)
    responses = []
    started = time.perf_counter()
    with (args.output / 'responses.jsonl').open('x') as log:
        for case in cases:
            begin = time.perf_counter()
            row = {'id': case['id'], 'msg': client.chat(case['messages'], case['tools']), 'elapsed_seconds': time.perf_counter() - begin}
            responses.append(row)
            log.write(json.dumps(row, ensure_ascii=False) + '\n')
            log.flush()
    result = {'scope': 'Fresh inference on frozen 8 Nov comparison cases; not a replacement for historical results',
              'model': args.model, 'elapsed_seconds': time.perf_counter() - started,
              'settings': json.loads((ROOT / 'settings.json').read_text()), 'scores': score(cases, responses)}
    (args.output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['scores'], indent=2))

if __name__ == '__main__':
    main()
