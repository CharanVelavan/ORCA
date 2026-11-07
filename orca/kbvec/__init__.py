"""Vector KB (ChromaDB + nomic + BM25 + reranker). Public interface: search, get_chunk, coverage."""
from .retrieve import coverage, get_chunk, search

__all__ = ["search", "get_chunk", "coverage"]
