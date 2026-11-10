"""Record a fresh Qwen + hybrid RAG integration exercise. Uses scripted commander decisions; all links emulated.

Configure LLM_BASE_URL, LLM_MODEL, ORCA_EMBED_URL, ORCA_CHROMA_DIR and FASTEMBED_CACHE_PATH first.
Run with: python scripts/verify_live_rag.py --output output/qwen-rag-new
"""
from __future__ import annotations
import argparse
import faulthandler
import hashlib
import json
import math
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from orca.audit import AuditLog
from orca.kbvec import embed, retrieve, store
from orca.llm import LLMClient
from orca.live.headless import run


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--scenario', default='S1')
    ap.add_argument('--adviser-only', action='store_true', help='Run grounded adviser/operator probes without driving an incident')
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    if (a.output / 'summary.json').exists() or list(a.output.glob('live-*.jsonl')):
        ap.error('output already contains a run; choose a fresh directory')
    faulthandler.dump_traceback_later(180, repeat=True)
    started = time.perf_counter()
    counters = {'fresh_model_calls': 0, 'embedding_http_calls': 0, 'reranker_calls': 0, 'retrieval_calls': 0}
    observer = (a.output / 'pipeline-observations.jsonl').open('x')
    def observe(kind, values):
        observer.write(json.dumps({'kind': kind, 'elapsed_seconds': round(time.perf_counter()-started, 3), **values})+'\n')
        observer.flush()
        (a.output / 'progress.json').write_text(json.dumps(counters))
    original_post, original_embed, original_rerank = LLMClient._post, embed._post, retrieve._rerank
    import orca.kbvec as kbvec
    original_search = kbvec.search_with_abstention
    def post(self, body):
        result = original_post(self, body)
        counters['fresh_model_calls'] += 1
        observe('fresh_model_response', {'model': self.model, 'tool_calls': len(result.get('tool_calls') or [])})
        return result
    def embeddings(texts):
        result = original_embed(texts)
        counters['embedding_http_calls'] += 1
        observe('embedding_http_response', {'inputs': len(texts), 'dimensions': len(result[0]) if result else 0})
        return result
    def rerank(query, candidates):
        result = original_rerank(query, candidates)
        counters['reranker_calls'] += 1
        observe('rerank_response', {'model': retrieve.config.reranker_model(), 'candidates': len(candidates)})
        return result
    def search(*args, **kwargs):
        kwargs['cache'] = False  # every observed retrieval performs fresh work
        result = original_search(*args, **kwargs)
        counters['retrieval_calls'] += 1
        observe('retrieval_response', {'query': args[0], 'abstained': result['abstained'],
                                      'chunk_ids': [r['chunk_id'] for r in result['results']]})
        return result
    LLMClient._post, embed._post, retrieve._rerank = post, embeddings, rerank
    kbvec.search_with_abstention = search
    try:
        count = store.collection(create=False).count()
        if count != 82191:
            raise RuntimeError(f'Expected restored v2 collection of 82191 vectors; got {count}')
        search('What incident-reporting obligations apply after stolen satellite operator management credentials?', k=5, rerank=True)
        def collect(s):
            # Exercise the live adviser and operator Ask path in this same fresh scenario session.
            answer = s.adviser.ask("CERT-In incident reporting six hours noticing", asker="scripted integration check")
            (a.output / 'grounded-adviser-answer.json').write_text(json.dumps(answer, indent=2, default=str)+'\n')
            s.ask('cert_in', 'First use query_kb to retrieve CERT-In incident reporting obligations. Then explain the trigger using only returned citations. Do not send a notification or execute a playbook.')
            s._flush_audit()
            events = s.bus.all()
            (a.output / 'stream.json').write_text(json.dumps(events, ensure_ascii=False, default=str))
            return s.summary(final=not a.adviser_only)
        if a.adviser_only:
            from orca.live.session import LiveSession
            session = LiveSession(a.scenario, llm='local', runs_dir=a.output)
            try:
                summary = collect(session)
            finally:
                session.close()
        else:
            summary = run(a.scenario, llm='local', runs_dir=a.output, max_minutes=120, session_hook=collect)
        logs = [p for p in a.output.glob('*.jsonl') if p.name != 'pipeline-observations.jsonl' and not p.name.endswith('.stream.jsonl')]
        chains = []
        for path in logs:
            entries = AuditLog(path).entries()
            if entries and 'prev_hash' in entries[0]:
                chains.append({'file': path.name, 'entries': len(entries), 'bad_sequence': AuditLog(path).verify(),
                               'anchor': entries[-1]['hash'], 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        result = {'scenario': a.scenario, 'adviser_only': a.adviser_only, 'all_links_emulated': True, 'commander': 'scripted headless commander',
                  'mode': 'fresh live model requests; fresh hybrid retrieval, no retrieval cache',
                  'collection_vectors': count, 'counters': counters, 'elapsed_seconds': round(time.perf_counter()-started, 3),
                  'audit_chains': chains, 'session_summary': summary}
        (a.output / 'summary.json').write_text(json.dumps(result, indent=2, default=str)+'\n')
        if not chains or any(c['bad_sequence'] is not None for c in chains) or not all(counters.values()) or counters['retrieval_calls'] < 2:
            raise RuntimeError('Integration incomplete or chain invalid; inspect saved evidence')
        print(json.dumps({k:v for k,v in result.items() if k != 'session_summary'}, indent=2))
    finally:
        LLMClient._post, embed._post, retrieve._rerank = original_post, original_embed, original_rerank
        kbvec.search_with_abstention = original_search
        observer.close()

if __name__ == '__main__':
    main()
