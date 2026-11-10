"""LLM client for the role agents. OpenAI-compatible chat completions, standard library only.

Modes (env ``LLM_MODE``):
    live    call the endpoint (``LLM_BASE_URL``, e.g. http://localhost:8000/v1 through the Atlas tunnel)
    record  call the endpoint and save every response under data/llm_cache/
    replay  never call the network; answer from data/llm_cache/ (judges' machines, CI)

Responses are keyed by sha256 of the canonical request (model, messages, tools), so a replay is exact.
``ScriptedLLM`` is a fake for tests: it returns a fixed list of assistant messages in order.

The LLM never supplies a timestamp, a verdict or a record id that we trust: tools take times from the
scenario facts, the rule engine gives verdicts, and ``orca.agents.check_citations`` checks every id.
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "llm_cache"


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class LLMError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, base_url: str | None = None, model: str | None = None, api_key: str | None = None,
                 mode: str | None = None, temperature: float | None = None, thinking: bool = False,
                 max_tokens: int = 1024, timeout: float = 120, cache_dir: Path = CACHE_DIR):
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL") or "http://localhost:8000/v1").rstrip("/")
        self.model = model or os.environ.get("LLM_MODEL") or "Qwen/Qwen3.6-35B-A3B"
        self.api_key = api_key if api_key is not None else os.environ.get("LLM_API_KEY", "")
        self.mode = mode or os.environ.get("LLM_MODE", "live")
        if self.mode not in {"live", "record", "replay"}:
            raise ValueError(f"LLM_MODE must be live, record or replay, not {self.mode!r}")
        self.temperature = float(temperature if temperature is not None else os.environ.get("LLM_TEMPERATURE", 0))
        self.thinking = thinking
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.cache_dir = Path(cache_dir)

    # ---------------------------------------------------------------- public
    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Return the assistant message dict: {"role": "assistant", "content": str|None, "tool_calls": [...]}."""
        body = {"model": self.model, "messages": messages, "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                # Qwen3 on llama.cpp: thinking off, or it spends the whole budget on reasoning (7 Nov smoke test)
                "chat_template_kwargs": {"enable_thinking": self.thinking}}
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        key = hashlib.sha256(_canonical({k: body[k] for k in ("model", "messages")} | {"tools": tools or []})
                             .encode()).hexdigest()
        path = self.cache_dir / f"{key}.json"
        if self.mode == "replay":
            if not path.exists():
                raise LLMError(f"replay: no recorded response for request {key[:12]} (run once with LLM_MODE=record)")
            return json.loads(path.read_text())["message"]
        msg = self._post(body)
        if self.mode == "record":
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            path.write_text(_canonical({"model": self.model, "message": msg}))
        return msg

    # ---------------------------------------------------------------- transport
    def _post(self, body: dict) -> dict:
        req = urllib.request.Request(f"{self.base_url}/chat/completions", data=_canonical(body).encode(),
                                     headers={"Content-Type": "application/json",
                                              **({"Authorization": f"Bearer {self.api_key}"} if self.api_key else {})})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read())
        except (urllib.error.URLError, TimeoutError) as e:
            raise LLMError(f"LLM endpoint {self.base_url} not reachable: {e}") from e
        try:
            m = data["choices"][0]["message"]
        except (KeyError, IndexError) as e:
            raise LLMError(f"unexpected LLM response: {str(data)[:300]}") from e
        return {"role": "assistant", "content": m.get("content"), "tool_calls": m.get("tool_calls") or [],
                "reasoning_content": m.get("reasoning_content") or m.get("reasoning")}


class ScriptedLLM:
    """Test double: returns the given assistant messages in order; records what it was sent."""

    def __init__(self, replies: list[dict]):
        self.replies = list(replies)
        self.requests: list[dict] = []

    def chat(self, messages, tools=None) -> dict:
        self.requests.append({"messages": messages, "tools": tools})
        if not self.replies:
            return {"role": "assistant", "content": "done", "tool_calls": []}
        r = self.replies.pop(0)
        return {"role": "assistant", "content": r.get("content"), "tool_calls": r.get("tool_calls", [])}


def tool_call(name: str, args: dict, call_id: str = "c1") -> dict:
    """Build an OpenAI-format tool call (for ScriptedLLM replies and tests)."""
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}
