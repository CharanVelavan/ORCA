"""OpenAI-compatible embeddings client (LM Studio in dev, the GCP L4 later). No laptop-specific code."""
from __future__ import annotations

import time

import httpx

from . import config


def _post(texts: list[str]) -> list[list[float]]:
    last = None
    for attempt in range(4):
        try:
            r = httpx.post(config.embed_url().rstrip("/") + "/embeddings",
                           headers={"Authorization": f"Bearer {config.embed_key()}"},
                           json={"model": config.embed_model(), "input": texts}, timeout=600)
            r.raise_for_status()
            data = sorted(r.json()["data"], key=lambda d: d["index"])
            return [d["embedding"] for d in data]
        except Exception as e:                # network / 5xx: retry
            last = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"embedding endpoint failed: {last}")


def embed(texts: list[str], kind: str = "document", progress=None) -> list[list[float]]:
    prefix = config.doc_prefix() if kind == "document" else config.query_prefix()
    out: list[list[float]] = []
    b = config.embed_batch()
    for i in range(0, len(texts), b):
        out += _post([prefix + t for t in texts[i:i + b]])
        if progress:
            progress(min(i + b, len(texts)), len(texts))
    return out
