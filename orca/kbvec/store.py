"""ChromaDB persistent store (cosine), as in the ITU reference stack."""
from __future__ import annotations

import chromadb

from . import config

_client = None


def collection(create: bool = True):
    global _client
    path = str(config.chroma_dir())
    if _client is None or getattr(_client, "_orca_path", None) != path:
        config.chroma_dir().mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=path)
        _client._orca_path = path
    if create:
        return _client.get_or_create_collection(config.COLLECTION, metadata={"hnsw:space": "cosine"})
    return _client.get_collection(config.COLLECTION)


def reset_client() -> None:
    global _client
    _client = None


def all_rows() -> dict:
    """ids, documents, metadatas of every chunk (used for BM25, snapshots and filters)."""
    col = collection()
    n = col.count()
    out = {"ids": [], "documents": [], "metadatas": []}
    for off in range(0, n, 2000):
        r = col.get(limit=2000, offset=off, include=["documents", "metadatas"])
        for k in out:
            out[k] += r[k]
    return out
