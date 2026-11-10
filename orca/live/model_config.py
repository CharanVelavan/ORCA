"""In-memory configuration and bounded probes for an OpenAI-compatible endpoint."""
from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from urllib.parse import urlsplit


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _url(value: object) -> str:
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError('A valid HTTP(S) base URL is required.')
    value = value.strip().rstrip('/')
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError:
        raise ValueError('A valid HTTP(S) base URL is required.') from None
    if (parts.scheme not in ('http', 'https') or not parts.hostname or parts.username is not None
            or parts.password is not None or parts.query or parts.fragment or any(c.isspace() for c in value)):
        raise ValueError('Use an HTTP(S) base URL without credentials, query, or fragment.')
    return value


class ModelConfig:
    """Staged settings; secrets never leave this process through public methods."""
    def __init__(self):
        self._lock = threading.RLock()
        self._values = {'base_url': _url(os.environ.get('LLM_BASE_URL') or 'http://localhost:8000/v1'),
                        'model': os.environ.get('LLM_MODEL') or 'Qwen/Qwen3.6-35B-A3B',
                        'api_key': os.environ.get('LLM_API_KEY', ''),
                        'mode': os.environ.get('LLM_MODE', 'live')}

    def _draft(self, changes: dict) -> dict:
        if not isinstance(changes, dict) or set(changes) - {'base_url', 'model', 'api_key', 'clear_key'}:
            raise ValueError('Invalid model configuration fields.')
        with self._lock:
            cfg = dict(self._values)
        if 'base_url' in changes:
            cfg['base_url'] = _url(changes['base_url'])
        if 'model' in changes:
            model = changes['model']
            if not isinstance(model, str) or not model.strip() or len(model) > 512:
                raise ValueError('A model name is required.')
            cfg['model'] = model.strip()
        if 'clear_key' in changes and not isinstance(changes['clear_key'], bool):
            raise ValueError('clear_key must be a boolean.')
        if changes.get('clear_key'):
            cfg['api_key'] = ''
        key = changes.get('api_key')
        if key is not None:
            if (not isinstance(key, str) or len(key) > 8192 or not key.isascii()
                    or any(ord(ch) < 32 or ord(ch) == 127 for ch in key)):
                raise ValueError('Invalid API key.')
            if key:
                cfg['api_key'] = key
        if cfg['api_key'] and (cfg['api_key'] in cfg['base_url'] or cfg['api_key'] in cfg['model']):
            raise ValueError('Keep the API key out of the URL and model name.')
        return cfg

    def public(self) -> dict:
        with self._lock:
            cfg = dict(self._values)
        return {'ok': True, 'base_url': cfg['base_url'], 'model': cfg['model'],
                'key_set': bool(cfg['api_key']), 'mode': cfg['mode']}

    def update(self, changes: dict) -> dict:
        with self._lock:
            self._values = self._draft(changes)
            return self.public()

    def client_args(self) -> dict:
        with self._lock:
            return dict(self._values)

    @staticmethod
    def _request(cfg: dict, path: str, body: dict | None = None) -> dict:
        headers = {'Content-Type': 'application/json'}
        if cfg['api_key']:
            headers['Authorization'] = 'Bearer ' + cfg['api_key']
        request = urllib.request.Request(cfg['base_url'] + path, headers=headers,
                                         data=json.dumps(body).encode() if body is not None else None)
        try:
            with urllib.request.build_opener(_NoRedirect).open(request, timeout=8) as response:
                raw = response.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024:
                raise ValueError('Endpoint response is too large.')
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise ValueError('Endpoint returned an invalid response.')
            return result
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            raise ValueError('Model endpoint request failed. Check the URL, credentials, and server.') from None

    def discover(self, changes: dict) -> dict:
        cfg = self._draft(changes)
        result = self._request(cfg, '/models')
        data = result.get('data')
        if not isinstance(data, list):
            raise ValueError('Model endpoint returned an invalid model list.')
        return {'ok': True, 'models': [item['id'] for item in data
                                        if isinstance(item, dict) and isinstance(item.get('id'), str)
                                        and (not cfg['api_key'] or cfg['api_key'] not in item['id'])][:500]}

    def test(self, changes: dict) -> dict:
        cfg = self._draft(changes)
        body = {'model': cfg['model'], 'messages': [{'role': 'user', 'content': 'Call the orca_probe tool with value ok.'}],
                'temperature': 0, 'max_tokens': 128, 'chat_template_kwargs': {'enable_thinking': False},
                'tools': [{'type': 'function', 'function': {'name': 'orca_probe', 'description': 'A harmless compatibility test.',
                           'parameters': {'type': 'object', 'properties': {'value': {'type': 'string'}}, 'required': ['value']}}}],
                'tool_choice': 'auto'}
        result = self._request(cfg, '/chat/completions', body)
        try:
            message = result['choices'][0]['message']
            calls = message.get('tool_calls') or []
        except (KeyError, IndexError, TypeError, AttributeError):
            calls = []
        compatible = False
        for call in calls if isinstance(calls, list) else []:
            try:
                function = call['function']
                arguments = json.loads(function['arguments'])
                if (call.get('type') == 'function' and function.get('name') == 'orca_probe'
                        and isinstance(arguments, dict) and isinstance(arguments.get('value'), str)):
                    compatible = True
                    break
            except (KeyError, TypeError, ValueError, AttributeError):
                continue
        return {'ok': True, 'reachable': True, 'tool_call_compatible': compatible}
