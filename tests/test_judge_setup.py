"""Bootstrap validation without downloads or changes to the user's environment."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

import pytest


def test_pinned_lock_install_requires_hashes(monkeypatch, tmp_path):
    monkeypatch.setattr(setup, 'REQUIREMENTS', tmp_path / 'requirements-judge.lock')
    command = setup.install_command(Path('/python path/python'))
    assert '--require-hashes' in command
    assert command[-1] == str(tmp_path / 'requirements-judge.lock')

SPEC = importlib.util.spec_from_file_location('judge_setup', Path(__file__).resolve().parents[1] / 'scripts/judge_setup.py')
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)
REAL_DASHBOARD_PORT_CHECK = setup.require_dashboard_port

@pytest.fixture(autouse=True)
def isolate_dashboard_port(monkeypatch):
    # Other tests exercise arguments and lifecycle, not ambient port availability.
    monkeypatch.setattr(setup, 'require_dashboard_port', lambda _port: None)


def test_dry_run_does_not_create_environment_or_make_network_calls(tmp_path, capsys):
    env = tmp_path / 'missing-env'
    with patch.object(setup, 'endpoint_ready', side_effect=AssertionError('network called')), \
         patch.object(setup.venv.EnvBuilder, 'create', side_effect=AssertionError('environment created')):
        assert setup.main(['--mode','live','--endpoint','http://localhost:9000/v1','--model-id','served-id',
                           '--venv',str(env),'--download-model','--dry-run']) == 0
    assert not env.exists()
    assert 'Dry run' in capsys.readouterr().out


def test_invalid_live_options_are_rejected_without_echoing_credentials(capsys):
    with pytest.raises(SystemExit):
        setup.main(['--mode','live','--endpoint','https://user:secret@example.test/v1','--model-id','id','--dry-run'])
    assert 'secret' not in capsys.readouterr().err
    with pytest.raises(SystemExit): setup.main(['--mode','live','--dry-run'])


def test_check_missing_environment_is_read_only(tmp_path):
    env = tmp_path / 'absent'
    assert setup.main(['--check','--venv',str(env)]) == 1
    assert not env.exists()


def test_existing_mismatched_download_is_never_overwritten(tmp_path):
    path = tmp_path / 'file.gguf'; path.write_bytes(b'personal data')
    with patch.object(setup.subprocess, 'run', side_effect=AssertionError('download called')):
        with pytest.raises(RuntimeError, match='does not match'):
            setup.download_files(Path('/unused'), tmp_path, 'repo', 'rev', {'file.gguf':hashlib.sha256(b'other').hexdigest()}, 'model')
    assert path.read_bytes() == b'personal data'


def test_live_discovery_checks_exact_identifier_without_printing_key(monkeypatch):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            assert self.path == '/v1/models'
            assert self.headers.get('Authorization') == 'Bearer private-test-value'
            data = json.dumps({'data':[{'id':'served-model'}]}).encode()
            self.send_response(200); self.end_headers(); self.wfile.write(data)
        def log_message(self, *args): pass
    server = HTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv('LLM_API_KEY','private-test-value')
    try:
        endpoint = f'http://127.0.0.1:{server.server_port}/v1'
        assert setup.endpoint_ready(endpoint, 'served-model')
        assert not setup.endpoint_ready(endpoint, 'different-model')
    finally:
        server.shutdown(); server.server_close()


def test_ready_mock_environment_is_reused_without_install_or_download(tmp_path):
    env = tmp_path / 'existing'
    with patch.object(setup, 'environment_ready', return_value=True), \
         patch.object(setup.venv.EnvBuilder, 'create', side_effect=AssertionError('created again')), \
         patch.object(setup, 'download_files', side_effect=AssertionError('unexpected download')), \
         patch.object(setup, 'run_dashboard', return_value=0) as launch:
        assert setup.main(['--venv',str(env)]) == 0
    args, _ = launch.call_args
    assert args[0][-2:] == ['--port', '8060']
    assert args[0][args[0].index('--llm') + 1] == 'mock'


def test_live_launch_uses_exact_model_without_printing_secret(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv('LLM_API_KEY','private-test-value')
    with patch.object(setup, 'environment_ready', return_value=True), \
         patch.object(setup, 'endpoint_ready', return_value=True), \
         patch.object(setup, 'run_dashboard', return_value=0) as launch:
        assert setup.main(['--venv',str(tmp_path/'env'),'--mode','live',
                           '--endpoint','http://127.0.0.1:9000/v1','--model-id','served-model']) == 0
    env = launch.call_args.args[1]
    assert env['LLM_MODEL'] == 'served-model'
    assert env['LLM_API_KEY'] == 'private-test-value'
    out = capsys.readouterr()
    assert 'private-test-value' not in out.out + out.err


def test_llama_command_preserves_paths_and_cpu_default():
    model = Path('/a directory/model name.gguf')
    command = setup.llama_command('/another directory/llama-server', model)
    assert command[0] == '/another directory/llama-server'
    assert command[command.index('--model') + 1] == str(model)
    assert command[command.index('--alias') + 1] == setup.LOCAL_MODEL
    assert command[command.index('--ctx-size') + 1] == '16384'
    assert command[command.index('--n-gpu-layers') + 1] == '0'
    assert command[command.index('--device') + 1] == 'none'
    assert '--no-kv-offload' in command and '--no-op-offload' in command
    gpu_command = setup.llama_command('llama-server', model, 7)
    assert gpu_command[-1] == '7' and '--device' not in gpu_command


def test_rag_prepare_requires_all_verified_files_before_mutation():
    with patch.object(setup, 'checked_files', return_value=False), \
         patch.object(setup.subprocess, 'run', side_effect=AssertionError('index mutation')):
        with pytest.raises(RuntimeError, match='missing or fail checksum'):
            setup.prepare_rag(Path('/unused'))


def test_rag_prepare_loads_before_snapshot():
    with patch.object(setup, 'checked_files', return_value=True), \
         patch.object(setup.subprocess, 'run') as run:
        run.return_value.returncode = 0
        setup.prepare_rag(Path('/python'))
    assert [call.args[0][-1] for call in run.call_args_list] == ['load-vectors', 'snapshot']
    assert all(call.kwargs['env']['ORCA_KBVEC_COLLECTION'] == 'orca_v2' for call in run.call_args_list)
    assert all(call.kwargs['env']['ORCA_KBVEC_BUILD'] == str(setup.ROOT / 'kb/vec_build') for call in run.call_args_list)


def fake_root(tmp_path):
    (tmp_path / 'scenarios').mkdir()
    (tmp_path / 'scenarios/s1.yaml').write_text('')
    (tmp_path / 'dashboard/live/dist').mkdir(parents=True)
    (tmp_path / 'dashboard/live/dist/index.html').write_text('')
    model = tmp_path / 'models/llm/qwen-ft' / next(iter(setup.MODEL))
    model.parent.mkdir(parents=True)
    model.write_bytes(b'test')
    return tmp_path


def test_local_model_cleanup_on_dashboard_exit(tmp_path, monkeypatch):
    monkeypatch.setattr(setup, 'ROOT', fake_root(tmp_path))
    monkeypatch.setenv('LLM_API_KEY', 'private-test-value')
    process = object()
    with patch.object(setup, 'environment_ready', return_value=True), \
         patch.object(setup, 'find_llama_server', return_value='/program files/llama-server'), \
         patch.object(setup, 'checked_files', return_value=True), \
         patch.object(setup, 'require_local_port'), \
         patch.object(setup, 'wait_for_local_model') as wait, \
         patch.object(setup, 'stop_local_model') as stop, \
         patch.object(setup.subprocess, 'Popen', return_value=process) as popen, \
         patch.object(setup, 'run_dashboard', return_value=0) as dashboard:
        assert setup.main(['--venv',str(tmp_path/'env'),'--serve-model']) == 0
    wait.assert_called_once_with(process)
    stop.assert_called_once_with(process)
    assert popen.call_args.args[0][0] == '/program files/llama-server'
    assert dashboard.call_args.args[1]['LLM_MODEL'] == setup.LOCAL_MODEL
    assert dashboard.call_args.args[1]['LLM_BASE_URL'] == setup.LOCAL_ENDPOINT
    assert dashboard.call_args.args[1]['LLM_API_KEY'] == ''
    assert 'LLM_API_KEY' not in popen.call_args.kwargs['env']


def test_local_model_cleanup_when_readiness_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(setup, 'ROOT', fake_root(tmp_path))
    process = object()
    with patch.object(setup, 'environment_ready', return_value=True), \
         patch.object(setup, 'find_llama_server', return_value='llama-server'), \
         patch.object(setup, 'checked_files', return_value=True), \
         patch.object(setup, 'require_local_port'), \
         patch.object(setup, 'wait_for_local_model', side_effect=RuntimeError('not ready')), \
         patch.object(setup, 'stop_local_model') as stop, \
         patch.object(setup.subprocess, 'Popen', return_value=process), \
         patch.object(setup, 'run_dashboard', side_effect=AssertionError('must not start dashboard')):
        assert setup.main(['--venv',str(tmp_path/'env'),'--serve-model']) == 1
    stop.assert_called_once_with(process)


def test_prepare_only_does_not_start_dashboard(tmp_path):
    with patch.object(setup, 'environment_ready', return_value=True), \
         patch.object(setup, 'checked_files', return_value=True), \
         patch.object(setup, 'check_disk_space'), \
         patch.object(setup, 'prepare_rag') as prepare, \
         patch.object(setup, 'run_dashboard', side_effect=AssertionError('dashboard started')):
        assert setup.main(['--venv',str(tmp_path/'env'),'--prepare-rag','--download-only']) == 0
    prepare.assert_called_once()


def test_low_disk_space_blocks_optional_download(monkeypatch):
    from types import SimpleNamespace
    args = setup.parser().parse_args(['--download-model','--dry-run'])
    monkeypatch.setattr(setup.shutil, 'disk_usage', lambda _path: SimpleNamespace(free=1))
    with pytest.raises(RuntimeError, match='Insufficient free disk'):
        setup.check_disk_space(args)


def test_serve_check_does_not_start_or_probe_endpoint(tmp_path):
    with patch.object(setup, 'environment_ready', return_value=True), \
         patch.object(setup, 'checked_files', return_value=True), \
         patch.object(setup, 'find_llama_server', return_value='llama-server'), \
         patch.object(setup, 'endpoint_ready', side_effect=AssertionError('endpoint probed')), \
         patch.object(setup.subprocess, 'Popen', side_effect=AssertionError('model started')):
        assert setup.main(['--venv',str(tmp_path/'env'),'--serve-model','--check']) == 0


def test_dashboard_child_cleaned_up_on_interrupt():
    from unittest.mock import Mock
    process = Mock()
    process.wait.side_effect = KeyboardInterrupt
    with patch.object(setup.subprocess, 'Popen', return_value=process), \
         patch.object(setup, 'stop_local_model') as stop:
        with pytest.raises(KeyboardInterrupt):
            setup.run_dashboard(['python','-m','orca.live'], {})
    stop.assert_called_once_with(process)


def test_embedding_command_is_cpu_only_and_preserves_path():
    model = Path('/model directory/embedding model.gguf')
    command = setup.embedding_command('/program directory/llama-server', model)
    assert command[command.index('--model') + 1] == str(model)
    assert command[command.index('--alias') + 1] == setup.EMBED_MODEL
    assert command[command.index('--port') + 1] == '1235'
    assert command[command.index('--pooling') + 1] == 'last'
    assert command[command.index('--ctx-size') + 1] == '8192'
    assert command[command.index('--n-gpu-layers') + 1] == '0'
    assert command[command.index('--device') + 1] == 'none'
    assert all(flag in command for flag in ('--embedding','--no-kv-offload','--no-op-offload'))


def test_embedding_arguments_require_complete_safe_pair(capsys):
    for argv in (['--embedding-endpoint','http://localhost:1235/v1'],
                 ['--serve-embedding','--embedding-model','id'],
                 ['--serve-embedding','--port','1235']):
        with pytest.raises(SystemExit): setup.main([*argv,'--dry-run'])
    with pytest.raises(SystemExit):
        setup.main(['--embedding-endpoint','https://user:private@example.test/v1','--embedding-model','id','--dry-run'])
    assert 'private' not in capsys.readouterr().err


def test_external_embedding_check_probes_exact_id_without_key_output(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv('ORCA_EMBED_KEY','private-embedding-key')
    with patch.object(setup, 'environment_ready', return_value=True), \
         patch.object(setup, 'endpoint_ready', return_value=True) as probe:
        assert setup.main(['--venv',str(tmp_path/'env'),'--check','--embedding-endpoint','http://localhost:1235/v1','--embedding-model','embed-id']) == 0
    probe.assert_called_once_with('http://localhost:1235/v1','embed-id',use_env_key=True,key_env='ORCA_EMBED_KEY')
    out = capsys.readouterr()
    assert 'private-embedding-key' not in out.out + out.err


def test_both_local_servers_cleaned_and_embedding_configured(tmp_path, monkeypatch):
    monkeypatch.setattr(setup, 'ROOT', fake_root(tmp_path))
    embedding = tmp_path / 'models/llm/qwen-embedding' / next(iter(setup.EMBED))
    embedding.parent.mkdir(parents=True); embedding.write_bytes(b'test')
    monkeypatch.setenv('ORCA_EMBED_KEY','private-embedding-key')
    generation, vector = object(), object()
    with patch.object(setup, 'environment_ready', return_value=True), \
         patch.object(setup, 'find_llama_server', return_value='llama-server'), \
         patch.object(setup, 'checked_files', return_value=True), \
         patch.object(setup, 'require_local_port'), patch.object(setup, 'require_embedding_port'), \
         patch.object(setup, 'wait_for_local_model'), patch.object(setup, 'wait_for_local_embedding'), \
         patch.object(setup, 'stop_local_model') as stop, \
         patch.object(setup.subprocess, 'Popen', side_effect=[generation,vector]) as starts, \
         patch.object(setup, 'run_dashboard', return_value=0) as dashboard:
        assert setup.main(['--venv',str(tmp_path/'env'),'--serve-model','--serve-embedding']) == 0
    assert [call.args[0] for call in stop.call_args_list] == [vector,generation]
    assert dashboard.call_args.args[1]['ORCA_EMBED_URL'] == setup.EMBED_ENDPOINT
    assert dashboard.call_args.args[1]['ORCA_EMBED_MODEL'] == setup.EMBED_MODEL
    assert dashboard.call_args.args[1]['ORCA_EMBED_KEY'] == ''
    assert all('ORCA_EMBED_KEY' not in call.kwargs['env'] for call in starts.call_args_list)


def test_embedding_failure_still_stops_generation(tmp_path, monkeypatch):
    monkeypatch.setattr(setup, 'ROOT', fake_root(tmp_path))
    embedding = tmp_path / 'models/llm/qwen-embedding' / next(iter(setup.EMBED))
    embedding.parent.mkdir(parents=True); embedding.write_bytes(b'test')
    generation, vector = object(), object()
    with patch.object(setup, 'environment_ready', return_value=True), \
         patch.object(setup, 'find_llama_server', return_value='llama-server'), \
         patch.object(setup, 'checked_files', return_value=True), \
         patch.object(setup, 'require_local_port'), patch.object(setup, 'require_embedding_port'), \
         patch.object(setup, 'wait_for_local_model'), \
         patch.object(setup, 'wait_for_local_embedding', side_effect=RuntimeError('embedding failed')), \
         patch.object(setup, 'stop_local_model') as stop, \
         patch.object(setup.subprocess, 'Popen', side_effect=[generation,vector]), \
         patch.object(setup, 'run_dashboard', side_effect=AssertionError('dashboard started')):
        assert setup.main(['--venv',str(tmp_path/'env'),'--serve-model','--serve-embedding']) == 1
    assert [call.args[0] for call in stop.call_args_list] == [vector,generation]


def test_local_embedding_check_probes_without_starting_or_exposing_key(tmp_path, monkeypatch):
    monkeypatch.setenv('ORCA_EMBED_KEY','private-embedding-key')
    with patch.object(setup, 'environment_ready', return_value=True), \
         patch.object(setup, 'checked_files', return_value=True), \
         patch.object(setup, 'find_llama_server', return_value='llama-server'), \
         patch.object(setup, 'endpoint_ready', return_value=True) as probe, \
         patch.object(setup.subprocess, 'Popen', side_effect=AssertionError('must not start')):
        assert setup.main(['--venv',str(tmp_path/'env'),'--serve-embedding','--check']) == 0
    probe.assert_called_once_with(setup.EMBED_ENDPOINT, setup.EMBED_MODEL, use_env_key=False, key_env='ORCA_EMBED_KEY')


def test_occupied_dashboard_port_fails_before_setup_or_launch(tmp_path, monkeypatch, capsys):
    import socket
    monkeypatch.setattr(setup, 'require_dashboard_port', REAL_DASHBOARD_PORT_CHECK)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(('127.0.0.1', 0)); occupied.listen()
        port = occupied.getsockname()[1]
        with patch.object(setup, 'environment_ready', side_effect=AssertionError('setup attempted')), \
             patch.object(setup, 'run_dashboard', side_effect=AssertionError('dashboard launched')):
            assert setup.main(['--port',str(port),'--venv',str(tmp_path/'env')]) == 1
    assert f'Dashboard port {port} is unavailable' in capsys.readouterr().err
    assert not (tmp_path/'env').exists()
