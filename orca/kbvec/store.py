"""ChromaDB persistent store (cosine), imported lazily for dependency-free tests."""
from __future__ import annotations

from . import config

_client = None


def collection(create: bool = True, name: str | None = None):
    global _client
    import chromadb
    path = str(config.chroma_dir())
    if _client is None or getattr(_client, "_orca_path", None) != path:
        config.chroma_dir().mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=path)
        _client._orca_path = path
    name = name or config.collection_name()
    if create:
        return _client.get_or_create_collection(name, metadata={"hnsw:space": "cosine"})
    return _client.get_collection(name)


def reset_client() -> None:
    global _client
    _client = None


def all_rows(name: str | None = None) -> dict:
    """ids, documents, metadatas of every chunk (used for BM25, snapshots and filters)."""
    col = collection(name=name)
    n = col.count()
    out = {"ids": [], "documents": [], "metadatas": []}
    for off in range(0, n, 2000):
        r = col.get(limit=2000, offset=off, include=["documents", "metadatas"])
        for k in out:
            out[k] += r[k]
    return out
