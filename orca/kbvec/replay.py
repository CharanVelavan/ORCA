"""Index snapshot (manifest) and the retrieval cache that lets a recorded demo replay without the embedder."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from . import config, store


def _manifest_body() -> dict:
    rows = store.all_rows()
    chunks = sorted(
        ({"chunk_id": i, "sha256": m.get("sha256", ""), "text_sha": m.get("text_sha", ""), "tier": m.get("tier", "")}
         for i, m in zip(rows["ids"], rows["metadatas"])), key=lambda c: c["chunk_id"])
    models = sorted({m.get("embed_model", "") for m in rows["metadatas"]})
    return {"embed_model": ", ".join(models), "chunk_count": len(chunks), "chunks": chunks}


def snapshot_id(body: dict | None = None) -> str:
    """Content hash of the index (chunk ids, hashes, embed model). Same index -> same id."""
    body = body or _manifest_body()
    blob = json.dumps({k: body[k] for k in ("embed_model", "chunks")}, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def snapshot() -> dict:
    """Write kb/vec_snapshots/<id>.json and return a summary."""
    body = _manifest_body()
    sid = snapshot_id(body)
    body = {"snapshot_id": sid, "created": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), **body}
    config.snapshot_dir().mkdir(parents=True, exist_ok=True)
    path = config.snapshot_dir() / f"{sid}.json"
    path.write_text(json.dumps(body, indent=1))
    return {"snapshot_id": sid, "path": str(path), "chunk_count": body["chunk_count"], "embed_model": body["embed_model"]}


_sid_cache: tuple[int, str] | None = None


def _current_sid() -> str:
    global _sid_cache
    n = store.collection().count()
    if _sid_cache is None or _sid_cache[0] != n:
        _sid_cache = (n, snapshot_id())
    return _sid_cache[1]


def cache_key(query: str, k: int, filters: dict, rerank: bool) -> str:
    blob = json.dumps({"q": query, "k": k, "f": filters, "r": rerank, "snap": _current_sid()},
                      sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()[:24]


def _path(key: str) -> Path:
    return config.cache_dir() / f"{key}.json"


def cache_get(key: str):
    p = _path(key)
    if p.exists():
        return json.loads(p.read_text())["results"]
    return None


def cache_put(key: str, query: str, k: int, filters: dict, rerank: bool, results: list[dict]) -> None:
    config.cache_dir().mkdir(parents=True, exist_ok=True)
    _path(key).write_text(json.dumps(
        {"snapshot_id": _current_sid(), "query": query, "k": k, "filters": filters, "rerank": rerank,
         "results": results}, indent=1, default=str))
