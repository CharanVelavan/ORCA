"""Write a portable judge-release manifest with exact artifact revisions and local checksums."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('judge_setup', ROOT / 'scripts/judge_setup.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def manifest(tag):
    files = ['submission/ORCA-NTN-SolarSailors-Report.pdf', 'requirements-judge.lock', '.gitattributes', '.env.example', 'quickstart.sh', 'quickstart.bat',
             'orca/agents.py', 'orca/live/session.py', 'orca/kbvec/retrieve.py',
             'scripts/judge_setup.py', 'scripts/verify_live_rag.py',
             'finetune/benchmark300/run.py', 'finetune/benchmark300/verify.py',
             'finetune/benchmark300/sha256.json',
             'dashboard/live/web/public/media/orca-method-4k.mp4',
             'dashboard/live/web/public/media/orca-final-clean-4k.mp4']
    files += [str(p.relative_to(ROOT)) for p in (ROOT / 'docs/research/judge-verification').rglob('*') if p.is_file()]
    return {
        'release_tag': tag, 'code_repository': 'https://github.com/CharanVelavan/ORCA',
        'code_snapshot': 'Resolve release_tag to its exact Git commit; the manifest avoids a self-referential commit hash.',
        'submitted_implementation_commit': 'cec8197', 'submitted_showcase_commit': '287c696',
        'scope': 'Post-submission judge verification; all satellite/network activity is emulated. Linux runtime was excluded.',
        'model': {'repo': setup.MODEL_REPO, 'revision': setup.MODEL_REV, 'files_sha256': setup.MODEL},
        'embedding': {'repo': setup.EMBED_REPO, 'revision': setup.EMBED_REV, 'files_sha256': setup.EMBED},
        'knowledge_base': {'repo': setup.RAG_REPO, 'revision': setup.RAG_REV, 'files_sha256': setup.RAG},
        'reranker': json.loads((ROOT/'docs/research/judge-verification/reranker-checksum.json').read_text()),
        'showcase_url': 'https://orca-ntn.vercel.app',
        'video_urls': ['https://orca-ntn.vercel.app/media/orca-method-4k.mp4',
                       'https://orca-ntn.vercel.app/media/orca-final-clean-4k.mp4'],
        'sha256': {name: digest(ROOT/name) for name in sorted(set(files))},
    }

if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--tag')
    ap.add_argument('--output', type=Path)
    ap.add_argument('--verify', type=Path, help='Verify every local file checksum in an existing release manifest')
    args=ap.parse_args()
    if args.verify:
        if args.tag or args.output:
            ap.error('--verify cannot be combined with --tag or --output')
        data=json.loads(args.verify.read_text())
        failures=[]
        for name, expected in data['sha256'].items():
            target=(ROOT/name).resolve()
            if ROOT not in target.parents or not target.is_file() or digest(target) != expected:
                failures.append(name)
        if failures:
            print('Release verification failed: '+', '.join(failures))
            raise SystemExit(1)
        print(f"Verified {len(data['sha256'])} release file checksums for {data['release_tag']}.")
    else:
        if not args.tag or not args.output:
            ap.error('provide both --tag and --output, or use --verify')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(manifest(args.tag), indent=2)+'\n')
