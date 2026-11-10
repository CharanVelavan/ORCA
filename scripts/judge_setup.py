#!/usr/bin/env python3
"""Create a judge environment and run the emulated ORCA dashboard.

No model, vector corpus, or endpoint is required for the default mock run.
Secrets are read only from the environment or the dashboard, never CLI arguments.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import signal
import shutil
import socket
import time
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit
import venv

ROOT = Path(__file__).resolve().parents[1]
BASE_REQUIREMENTS = ROOT / 'requirements.txt'
LOCK_REQUIREMENTS = ROOT / 'requirements-judge.lock'
REQUIREMENTS = LOCK_REQUIREMENTS if LOCK_REQUIREMENTS.is_file() else BASE_REQUIREMENTS
DEFAULT_ENV = ROOT / '.venv-judge'
MODEL_REPO = 'CharanVelavan/orca-ntn-qwen3.6-35b-a3b-ft-gguf'
MODEL_REV = 'a0bdc74681870544849cafaf2d5a35a6a5cbd488'
RAG_REPO = 'CharanVelavan/orca-ntn-kb-v2'
RAG_REV = '769dcc85b6be9e308b038831072a5b848e740a94'
LOCAL_ENDPOINT = 'http://127.0.0.1:8000/v1'
LOCAL_MODEL = 'orca-ntn-qwen-ft'
EMBED_REPO = 'Qwen/Qwen3-Embedding-8B-GGUF'
EMBED_REV = '69d0e58a13e463cd99a9b83e3f5fee7c10265fab'
EMBED_ENDPOINT = 'http://127.0.0.1:1235/v1'
EMBED_MODEL = 'text-embedding-qwen3-embedding-8b'
EMBED = {'Qwen3-Embedding-8B-Q4_K_M.gguf': '3fcd3febec8b3fd64435204db75bf0dd73b91e8d0661e0331acfe7e7c3120b85'}
MODEL = {'Qwen3.6-35B-A3B-orca-ft.IQ4_XS.gguf': '011d7797836571495e8faf545101bee1e71d75a39292e06f946e8a3646b54e16'}
RAG = {
    'chunks.jsonl': 'efe2d3f7b7b03d32e87da9cc38c75771287ade5184de2e6bdec20b800704c9b4',
    'embeddings.f16.npy': 'c3216a1917f3516deca194eac27eb98cb29500c7b87732974c347191fe0be4cf',
    'ids.json': 'b9ee8382010e469ebbc09e47b7579772dbb449433f3a8374014f82c5c4a5b55d',
    'model.json': '470b4f3b2d50ca9a05e157f9880c7f6ea1238e2848c657505b4dc4980de42183',
}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='Set up and run the ORCA-NTN emulated dashboard.')
    p.add_argument('--mode', choices=('mock', 'live'), default=None)
    p.add_argument('--endpoint', help='OpenAI-compatible API base URL (no credentials or query)')
    p.add_argument('--model-id', help='Exact model ID reported by the endpoint')
    p.add_argument('--scenario', default='S1', help='Initial scenario ID (default S1)')
    p.add_argument('--port', type=int, default=8060, help='Loopback dashboard port (default 8060)')
    p.add_argument('--venv', type=Path, default=DEFAULT_ENV, help='Virtual environment path (default .venv-judge)')
    p.add_argument('--download-model', action='store_true', help='Download the optional ~19.2 GB tuned GGUF')
    p.add_argument('--download-embedding', action='store_true', help='Download the optional ~4.68 GB embedding GGUF')
    p.add_argument('--serve-embedding', action='store_true', help='Start a local CPU embedding server on port 1235')
    p.add_argument('--embedding-endpoint', help='External embedding API base URL (no credentials or query)')
    p.add_argument('--embedding-model', help='Exact embedding model ID reported by the endpoint')
    p.add_argument('--download-rag', action='store_true', help='Download optional ~0.94 GB vector build files')
    p.add_argument('--prepare-rag', action='store_true', help='Load verified vector files into Chroma and create a snapshot')
    p.add_argument('--serve-model', action='store_true', help='Start an installed llama-server for the downloaded model; implies live mode')
    p.add_argument('--llama-server', help='Path to an installed llama-server executable (otherwise search PATH)')
    p.add_argument('--gpu-layers', type=int, help='Explicit llama.cpp GPU layer count (default 0, CPU)')
    p.add_argument('--download-only', action='store_true', help='Prepare requested downloads without starting the dashboard')
    checks = p.add_mutually_exclusive_group()
    checks.add_argument('--check', action='store_true', help='Check an existing setup; do not install or launch')
    checks.add_argument('--dry-run', action='store_true', help='Validate arguments and show actions without making changes')
    return p


def validate(args: argparse.Namespace, p: argparse.ArgumentParser) -> None:
    args.mode = args.mode or ('live' if args.serve_model else 'mock')
    if args.serve_model:
        if args.mode != 'live' or args.endpoint or args.model_id:
            p.error('--serve-model uses its own local live endpoint; omit --mode mock, --endpoint and --model-id')
        if args.port == 8000:
            p.error('dashboard port must differ from the local model server port 8000')
        args.endpoint, args.model_id = LOCAL_ENDPOINT, LOCAL_MODEL
    if args.serve_embedding:
        if args.embedding_endpoint or args.embedding_model:
            p.error('--serve-embedding uses its own local endpoint; omit --embedding-endpoint and --embedding-model')
        if args.port == 1235:
            p.error('dashboard port must differ from the local embedding server port 1235')
        args.embedding_endpoint, args.embedding_model = EMBED_ENDPOINT, EMBED_MODEL
    if bool(args.embedding_endpoint) != bool(args.embedding_model):
        p.error('--embedding-endpoint and --embedding-model must be supplied together')
    if args.llama_server and not (args.serve_model or args.serve_embedding):
        p.error('--llama-server requires --serve-model or --serve-embedding')
    if args.gpu_layers is not None and not args.serve_model:
        p.error('--gpu-layers requires --serve-model')
    if args.gpu_layers is not None and args.gpu_layers < 0:
        p.error('--gpu-layers must be a nonnegative integer')
    if args.download_only and (args.serve_model or args.serve_embedding):
        p.error('--download-only cannot start a model server')
    if not 1 <= args.port <= 65535:
        p.error('port must be between 1 and 65535')
    if not args.scenario or not args.scenario.isalnum() or len(args.scenario) > 32:
        p.error('scenario must be an alphanumeric scenario ID')
    if not (ROOT / 'scenarios' / (args.scenario.lower() + '.yaml')).is_file():
        p.error('scenario ID was not found in the repository')
    if args.mode == 'live' and (not args.endpoint or not args.model_id):
        p.error('live mode requires both --endpoint and --model-id')
    if args.mode == 'mock' and (args.endpoint or args.model_id):
        p.error('--endpoint and --model-id require --mode live')
    if args.download_only and not (args.download_model or args.download_embedding or args.download_rag or args.prepare_rag):
        p.error('--download-only requires a download or --prepare-rag')
    if args.endpoint:
        try:
            parts = urlsplit(args.endpoint)
            _ = parts.port
            if (parts.scheme not in ('http', 'https') or not parts.hostname or parts.username is not None
                    or parts.password is not None or parts.query or parts.fragment or any(c.isspace() for c in args.endpoint)):
                raise ValueError
        except ValueError:
            p.error('endpoint must be an HTTP(S) base URL without credentials, query, or fragment')
        secret = os.environ.get('LLM_API_KEY', '')
        if secret and (secret in args.endpoint or secret in (args.model_id or '')):
            p.error('keep credentials out of endpoint and model ID')
    if args.model_id and (not args.model_id.strip() or len(args.model_id) > 512 or any(ord(c) < 32 for c in args.model_id)):
        p.error('model ID must be a nonempty exact endpoint identifier')
    if args.embedding_endpoint:
        try:
            parts = urlsplit(args.embedding_endpoint)
            _ = parts.port
            if (parts.scheme not in ('http', 'https') or not parts.hostname or parts.username is not None
                    or parts.password is not None or parts.query or parts.fragment or any(c.isspace() for c in args.embedding_endpoint)):
                raise ValueError
        except ValueError:
            p.error('embedding endpoint must be an HTTP(S) base URL without credentials, query, or fragment')
        key = os.environ.get('ORCA_EMBED_KEY', '')
        if key and (key in args.embedding_endpoint or key in args.embedding_model):
            p.error('keep credentials out of embedding endpoint and model ID')
        if not args.embedding_model.strip() or len(args.embedding_model) > 512 or any(ord(c) < 32 for c in args.embedding_model):
            p.error('embedding model must be a nonempty exact endpoint identifier')


def venv_python(directory: Path) -> Path:
    return directory / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def dependency_signature() -> str:
    return hashlib.sha256(BASE_REQUIREMENTS.read_bytes() + b'\n' + REQUIREMENTS.read_bytes() + b'\npython=3.12\n').hexdigest()


def install_command(python: Path) -> list[str]:
    return [str(python), '-m', 'pip', 'install', *(['--require-hashes'] if REQUIREMENTS.name == 'requirements-judge.lock' else []), '-r', str(REQUIREMENTS)]


def environment_ready(directory: Path) -> bool:
    python = venv_python(directory)
    marker = directory / '.orca-requirements.sha256'
    try:
        if not python.is_file() or marker.read_text().strip() != dependency_signature():
            return False
        probe = subprocess.run([str(python), '-c', 'import sys,yaml,numpy,scipy,sklearn,lightgbm; assert sys.version_info[:2] == (3,12)'],
                               cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return probe.returncode == 0
    except (OSError, ValueError):
        return False


def endpoint_ready(endpoint: str, model: str, *, use_env_key: bool = True, key_env: str = 'LLM_API_KEY') -> bool:
    """Discover the exact model, without logging URL, key, response, or exception."""
    headers = {}
    if use_env_key and os.environ.get(key_env):
        headers['Authorization'] = 'Bearer ' + os.environ[key_env]
    request = urllib.request.Request(endpoint.rstrip('/') + '/models', headers=headers)
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=8) as response:
            raw = response.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            return False
        result = json.loads(raw)
        return isinstance(result, dict) and isinstance(result.get('data'), list) and any(
            isinstance(row, dict) and row.get('id') == model for row in result['data'])
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return False


def checked_files(directory: Path, files: dict[str,str]) -> bool:
    return all((directory / name).is_file() and digest(directory / name) == expected for name, expected in files.items())


def download_files(python: Path, directory: Path, repo: str, revision: str, files: dict[str,str], repo_type: str) -> None:
    # Never overwrite existing different data. Resume only absent files through the Hub cache.
    for name, expected in files.items():
        dest = directory / name
        if dest.exists() and (not dest.is_file() or digest(dest) != expected):
            raise RuntimeError(f'Existing {name} does not match the published checksum; move it before downloading.')
    missing = [name for name in files if not (directory / name).exists()]
    if missing:
        directory.mkdir(parents=True, exist_ok=True)
        script = ('from huggingface_hub import hf_hub_download\nimport sys\n'
                  'repo,revision,directory,kind,*names=sys.argv[1:]\n'
                  'for name in names: hf_hub_download(repo_id=repo,filename=name,revision=revision,repo_type=kind,local_dir=directory)\n')
        env = os.environ.copy()
        env['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
        result = subprocess.run([str(python), '-c', script, repo, revision, str(directory), repo_type, *missing],
                                cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if result.returncode:
            raise RuntimeError('Hugging Face download failed. Check connectivity and available disk space.')
    if not checked_files(directory, files):
        raise RuntimeError('Downloaded file checksum mismatch. The file was not used.')



def find_llama_server(explicit: str | None) -> str | None:
    """Accept an exact path (including spaces) or an executable on PATH."""
    if explicit:
        path = Path(explicit).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return str(path.resolve())
        return shutil.which(explicit)
    return shutil.which('llama-server')


def llama_command(binary: str, model_path: Path, gpu_layers: int = 0) -> list[str]:
    command = [binary, '--model', str(model_path), '--jinja', '--alias', LOCAL_MODEL,
               '--ctx-size', '16384', '--host', '127.0.0.1', '--port', '8000',
               '--n-gpu-layers', str(gpu_layers)]
    if gpu_layers == 0:
        command.extend(['--device', 'none', '--no-kv-offload', '--no-op-offload'])
    return command


def embedding_command(binary: str, model_path: Path) -> list[str]:
    return [binary, '--model', str(model_path), '--embedding', '--pooling', 'last', '--alias', EMBED_MODEL,
            '--host', '127.0.0.1', '--port', '1235', '--ctx-size', '8192', '--n-gpu-layers', '0',
            '--device', 'none', '--no-kv-offload', '--no-op-offload', '--threads', '8', '--parallel', '1']


def prepare_rag(python: Path) -> None:
    if not checked_files(ROOT / 'kb/vec_build', RAG):
        raise RuntimeError('RAG files are missing or fail checksum verification. Run with --download-rag --prepare-rag.')
    print('Loading verified vectors into Chroma; this may take several minutes.', flush=True)
    rag_env = os.environ.copy()
    rag_env.update(ORCA_KBVEC_COLLECTION='orca_v2', ORCA_KBVEC_BUILD=str(ROOT / 'kb/vec_build'))
    for command in ('load-vectors', 'snapshot'):
        result = subprocess.run([str(python), '-m', 'orca.kbvec', command], cwd=ROOT, env=rag_env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if result.returncode:
            raise RuntimeError(f'RAG {command} failed. Check disk space and the local Chroma configuration.')
    print('RAG index loaded and snapshot created. Live vector queries also need a compatible embedding endpoint.')



def check_disk_space(args: argparse.Namespace) -> None:
    """Conservative preflight for optional assets in the default repository volume."""
    needed = 0
    if args.download_model and not (ROOT / 'models/llm/qwen-ft' / next(iter(MODEL))).is_file():
        needed += 19_179_521_888
    if args.download_embedding and not (ROOT / 'models/llm/qwen-embedding' / next(iter(EMBED))).is_file():
        needed += 4_676_804_928
    if args.download_rag:
        sizes = {'chunks.jsonl':256_169_422, 'embeddings.f16.npy':673_308_800,
                 'ids.json':3_464_575, 'model.json':202}
        needed += sum(size for name, size in sizes.items() if not (ROOT / 'kb/vec_build' / name).is_file())
    # An existing Chroma may be reused; an alternate ORCA_CHROMA_DIR may be on another volume.
    if args.prepare_rag and not os.environ.get('ORCA_CHROMA_DIR') and not (ROOT / 'chroma/chroma.sqlite3').exists():
        needed += 8 * 1024 ** 3
    if needed and shutil.disk_usage(ROOT).free < needed + 2 * 1024 ** 3:
        raise RuntimeError('Insufficient free disk space for the selected optional files and index, including 2 GiB headroom.')


def require_dashboard_port(port: int) -> None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Match HTTPServer's address reuse on POSIX, but never use Windows' permissive SO_REUSEADDR.
            if os.name != 'nt': sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('127.0.0.1', port))
    except OSError:
        raise RuntimeError(f'Dashboard port {port} is unavailable. Stop the existing service or choose another with --port.') from None


def require_local_port() -> None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('127.0.0.1', 8000))
    except OSError:
        raise RuntimeError('Local model port 8000 is unavailable. Stop the existing service or use --mode live with its endpoint.') from None


def require_embedding_port() -> None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('127.0.0.1', 1235))
    except OSError:
        raise RuntimeError('Local embedding port 1235 is unavailable. Stop the existing service or use --embedding-endpoint and --embedding-model.') from None


def wait_for_local_embedding(process: subprocess.Popen, timeout: float = 300) -> None:
    deadline = time.monotonic() + timeout
    next_update = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError('Embedding server exited before it was ready. See runs/setup/embedding-server.log.')
        if endpoint_ready(EMBED_ENDPOINT, EMBED_MODEL, use_env_key=False):
            return
        if time.monotonic() >= next_update:
            print('Still waiting for the local embedding model to load…', flush=True)
            next_update = time.monotonic() + 30
        time.sleep(1)
    raise RuntimeError('Embedding server did not advertise the model in time. See runs/setup/embedding-server.log.')


def wait_for_local_model(process: subprocess.Popen, timeout: float = 300) -> None:
    deadline = time.monotonic() + timeout
    next_update = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError('llama-server exited before the model was ready. Check compatibility and memory; see runs/setup/llama-server.log.')
        if endpoint_ready(LOCAL_ENDPOINT, LOCAL_MODEL, use_env_key=False):
            return
        if time.monotonic() >= next_update:
            print('Still waiting for the local model to load…', flush=True)
            next_update = time.monotonic() + 30
        time.sleep(1)
    raise RuntimeError('llama-server did not advertise the model in time. See runs/setup/llama-server.log.')


def stop_local_model(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        process.terminate()
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()



def run_dashboard(command: list[str], env: dict[str, str]) -> int:
    """Own the child so an interrupt or termination never leaves its port open."""
    options = {'cwd': ROOT, 'env': env}
    if os.name != 'nt': options['start_new_session'] = True
    process = subprocess.Popen(command, **options)
    try:
        return process.wait()
    finally:
        stop_local_model(process)


def main(argv: list[str] | None = None) -> int:
    p = parser()
    args = p.parse_args(argv)
    validate(args, p)
    if sys.version_info[:2] != (3, 12):
        print('Python 3.12 is required for the pinned dependencies.', file=sys.stderr)
        return 2
    directory = args.venv.expanduser().resolve()
    python = venv_python(directory)
    if not (ROOT / 'dashboard/live/dist/index.html').is_file():
        print('Bundled dashboard is missing: dashboard/live/dist/index.html.', file=sys.stderr)
        return 1
    if args.dry_run:
        print('Dry run: validate/create isolated Python environment and install pinned requirements if needed.' + ('' if args.download_only else ' Then start the dashboard.'))
        if args.mode == 'live': print('Live mode: verify the exact model ID through the configured endpoint.')
        if args.download_model: print('Optional model: download and verify the ~19.2 GB GGUF.')
        if args.download_embedding: print('Optional embedding model: download and verify the ~4.68 GB GGUF.')
        if args.serve_embedding: print('Local embedding: start the CPU server, verify its model ID and stop it on exit.')
        elif args.embedding_endpoint: print('External embedding: verify the exact advertised model ID.')
        if args.download_rag: print('Optional RAG: download and verify ~0.94 GB of vector build files.')
        if args.prepare_rag: print('Prepare RAG: verify the files, load Chroma and write a snapshot.')
        if args.serve_model: print('Local model: start an installed llama-server, wait for the exact model, then run live; stop it on exit.')
        if args.download_only: print('Download-only: do not start the dashboard.')
        return 0
    if args.check:
        if not environment_ready(directory):
            print('Judge environment missing, incomplete, or requirements changed. Run quickstart first.', file=sys.stderr)
            return 1
        if args.download_model and not checked_files(ROOT / 'models/llm/qwen-ft', MODEL):
            print('Optional model missing or checksum mismatch.', file=sys.stderr); return 1
        if (args.download_embedding or args.serve_embedding) and not checked_files(ROOT / 'models/llm/qwen-embedding', EMBED):
            print('Embedding model missing or checksum mismatch.', file=sys.stderr); return 1
        if args.serve_embedding and not find_llama_server(args.llama_server):
            print('llama-server is missing.', file=sys.stderr); return 1
        if args.embedding_endpoint and not endpoint_ready(args.embedding_endpoint, args.embedding_model, use_env_key=not args.serve_embedding, key_env='ORCA_EMBED_KEY'):
            print('Embedding endpoint unavailable or exact model ID not advertised.', file=sys.stderr); return 1
        if args.download_rag and not checked_files(ROOT / 'kb/vec_build', RAG):
            print('Optional vector files missing or checksum mismatch.', file=sys.stderr); return 1
        if args.prepare_rag and not checked_files(ROOT / 'kb/vec_build', RAG):
            print('RAG source files missing or checksum mismatch.', file=sys.stderr); return 1
        if args.serve_model and (not find_llama_server(args.llama_server) or not checked_files(ROOT / 'models/llm/qwen-ft', MODEL)):
            print('llama-server or the verified model file is missing.', file=sys.stderr); return 1
        if args.mode == 'live' and not args.serve_model and not endpoint_ready(args.endpoint, args.model_id):
            print('Endpoint unavailable or exact model ID not advertised.', file=sys.stderr); return 1
        if args.prepare_rag: print('RAG source files verified; this check does not test the index or embedding endpoint.')
        print('Dependency and selected artifact checks passed.'); return 0
    # Refuse an impossible full-path setup before installing packages or downloading large assets.
    if not args.download_only:
        try: require_dashboard_port(args.port)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    if (args.serve_model or args.serve_embedding) and not find_llama_server(args.llama_server):
        print('llama-server was not found. Install a compatible llama.cpp build and add it to PATH or pass --llama-server PATH.', file=sys.stderr)
        return 1
    if args.serve_model and not args.download_model and not (ROOT / 'models/llm/qwen-ft' / next(iter(MODEL))).is_file():
        print('Verified GGUF is missing. Add --download-model or provide the published file in models/llm/qwen-ft.', file=sys.stderr)
        return 1
    if args.serve_embedding and not args.download_embedding and not (ROOT / 'models/llm/qwen-embedding' / next(iter(EMBED))).is_file():
        print('Verified embedding GGUF is missing. Add --download-embedding.', file=sys.stderr)
        return 1
    if args.prepare_rag and not args.download_rag and not checked_files(ROOT / 'kb/vec_build', RAG):
        print('RAG files are missing or fail checksum verification. Add --download-rag.', file=sys.stderr)
        return 1
    if not environment_ready(directory):
        if directory.exists() and not python.is_file():
            print('The environment directory exists but is not a usable Python environment.', file=sys.stderr); return 1
        print('Preparing Python 3.12 environment and installing pinned dependencies. This can take several minutes.', flush=True)
        try:
            if not python.exists(): venv.EnvBuilder(with_pip=True).create(directory)
            result = subprocess.run(install_command(python), cwd=ROOT,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            if result.returncode: raise RuntimeError('Dependency installation failed. Check network access, Python 3.12 and platform libraries (macOS: libomp).')
            (directory / '.orca-requirements.sha256').write_text(dependency_signature() + '\n')
            if not environment_ready(directory): raise RuntimeError('Dependency import check failed. On macOS check libomp; on Linux check libgomp.')
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            print(str(exc) if isinstance(exc, RuntimeError) else 'Could not prepare the Python environment.', file=sys.stderr)
            return 1
    try:
        check_disk_space(args)
        if args.download_model:
            print('Downloading/verifying the optional ~19.2 GB model.', flush=True)
            download_files(python, ROOT / 'models/llm/qwen-ft', MODEL_REPO, MODEL_REV, MODEL, 'model')
            print('Model verified in models/llm/qwen-ft.' + (' The local server will start below.' if args.serve_model else ' Start a compatible model server separately.'))
        if args.download_embedding:
            print('Downloading/verifying the optional ~4.68 GB embedding model.', flush=True)
            download_files(python, ROOT / 'models/llm/qwen-embedding', EMBED_REPO, EMBED_REV, EMBED, 'model')
            print('Embedding model verified in models/llm/qwen-embedding.')
        if args.download_rag:
            print('Downloading/verifying the optional ~0.94 GB RAG files.', flush=True)
            download_files(python, ROOT / 'kb/vec_build', RAG_REPO, RAG_REV, RAG, 'dataset')
            print('Vector files verified in kb/vec_build.')
            if not args.prepare_rag:
                display_python = subprocess.list2cmdline([str(python)]) if os.name == 'nt' else shlex.quote(str(python))
                print(f'To build the index: {display_python} -m orca.kbvec load-vectors')
                print(f'Then run: {display_python} -m orca.kbvec snapshot')
            print('Live retrieval also needs a compatible embedding endpoint; see docs/KBVEC.md.')
        if args.prepare_rag:
            prepare_rag(python)
    except (OSError, RuntimeError) as exc:
        print(str(exc) if isinstance(exc, RuntimeError) else 'Could not verify or write downloaded files.', file=sys.stderr)
        return 1
    if args.download_only: return 0
    local_process = None
    embedding_process = None
    previous_sigterm = None
    try:
        def handle_termination(signum, _frame):
            raise SystemExit(128 + signum)
        previous_sigterm = signal.signal(signal.SIGTERM, handle_termination)
        if args.serve_model: require_local_port()
        if args.serve_embedding:
            if not checked_files(ROOT / 'models/llm/qwen-embedding', EMBED):
                raise RuntimeError('Verified embedding GGUF is missing or fails checksum verification.')
            require_embedding_port()
        if args.serve_model:
            binary = find_llama_server(args.llama_server)
            if not binary:
                raise RuntimeError('llama-server was not found. Install a compatible llama.cpp build and add it to PATH or pass --llama-server PATH.')
            if not checked_files(ROOT / 'models/llm/qwen-ft', MODEL):
                raise RuntimeError('Verified GGUF is missing. Run with --download-model or provide the published file in models/llm/qwen-ft.')
            model_path = ROOT / 'models/llm/qwen-ft' / next(iter(MODEL))
            print('Starting local llama-server on 127.0.0.1:8000. Model loading can take several minutes.', flush=True)
            log_dir = ROOT / 'runs/setup'
            log_dir.mkdir(parents=True, exist_ok=True)
            # The local server needs no credentials. Avoid passing secrets into its loggable environment.
            model_env = {key: value for key, value in os.environ.items()
                         if not key.upper().endswith('_KEY')
                         and not any(part in key.upper() for part in ('TOKEN', 'API_KEY', 'PASSWORD', 'SECRET'))}
            popen_options = {'cwd': ROOT, 'stderr': subprocess.STDOUT, 'env': model_env}
            if os.name != 'nt': popen_options['start_new_session'] = True
            with (log_dir / 'llama-server.log').open('a', encoding='utf-8') as log:
                local_process = subprocess.Popen(llama_command(binary, model_path, args.gpu_layers or 0), stdout=log, **popen_options)
            print('Local server diagnostics: runs/setup/llama-server.log', flush=True)
            wait_for_local_model(local_process)
        elif args.mode == 'live' and not endpoint_ready(args.endpoint, args.model_id):
            raise RuntimeError('Endpoint unavailable or exact model ID not advertised. Start the model server and verify its model ID.')
        if args.serve_embedding:
            binary = find_llama_server(args.llama_server)
            if not binary or not checked_files(ROOT / 'models/llm/qwen-embedding', EMBED):
                raise RuntimeError('llama-server or verified embedding GGUF is missing. Add --download-embedding if needed.')
            model_path = ROOT / 'models/llm/qwen-embedding' / next(iter(EMBED))
            print('Starting local embedding server on 127.0.0.1:1235. Model loading may take several minutes.', flush=True)
            log_dir = ROOT / 'runs/setup'
            log_dir.mkdir(parents=True, exist_ok=True)
            model_env = {key: value for key, value in os.environ.items()
                         if not key.upper().endswith('_KEY')
                         and not any(part in key.upper() for part in ('TOKEN', 'API_KEY', 'PASSWORD', 'SECRET'))}
            options = {'cwd': ROOT, 'stderr': subprocess.STDOUT, 'env': model_env}
            if os.name != 'nt': options['start_new_session'] = True
            with (log_dir / 'embedding-server.log').open('a', encoding='utf-8') as log:
                embedding_process = subprocess.Popen(embedding_command(binary, model_path), stdout=log, **options)
            print('Embedding server diagnostics: runs/setup/embedding-server.log', flush=True)
            wait_for_local_embedding(embedding_process)
        elif args.embedding_endpoint and not endpoint_ready(args.embedding_endpoint, args.embedding_model, key_env='ORCA_EMBED_KEY'):
            raise RuntimeError('Embedding endpoint unavailable or exact model ID not advertised.')
        env = os.environ.copy()
        if args.prepare_rag: env['ORCA_KBVEC_COLLECTION'] = 'orca_v2'
        if args.embedding_endpoint:
            env.update(ORCA_EMBED_URL=args.embedding_endpoint.rstrip('/'), ORCA_EMBED_MODEL=args.embedding_model)
            if args.serve_embedding: env['ORCA_EMBED_KEY'] = ''
        if args.mode == 'live':
            env.update(LLM_BASE_URL=args.endpoint.rstrip('/'), LLM_MODEL=args.model_id, LLM_MODE='live')
            if args.serve_model: env['LLM_API_KEY'] = ''
        print(f'Starting {args.mode} dashboard at http://127.0.0.1:{args.port}/ (Ctrl+C to stop).', flush=True)
        return run_dashboard([str(python), '-m', 'orca.live', '--scenario', args.scenario.upper(), '--llm', 'local' if args.mode == 'live' else 'mock', '--port', str(args.port)], env)
    except KeyboardInterrupt:
        return 130
    except (OSError, RuntimeError) as exc:
        print(str(exc) if isinstance(exc, RuntimeError) else 'Could not start the requested service.', file=sys.stderr)
        return 1
    finally:
        try:
            if embedding_process is not None:
                stop_local_model(embedding_process)
        finally:
            try:
                if local_process is not None:
                    stop_local_model(local_process)
            finally:
                if previous_sigterm is not None:
                    signal.signal(signal.SIGTERM, previous_sigterm)


if __name__ == '__main__':
    raise SystemExit(main())
