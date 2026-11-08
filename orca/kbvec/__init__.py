"""Vector KB public interface.

Keep this module deliberately light: the agent/protocol citation guard imports it even on
machines that have not installed ChromaDB.  Importing the retrieval implementation only
when one of the public functions is called lets an invented chunk be rejected cleanly
instead of turning a missing optional dependency into a protocol failure.
"""
from __future__ import annotations

__all__ = ["search", "get_chunk", "coverage", "search_with_abstention"]


def search(*args, **kwargs):
    from .retrieve import search as _search
    return _search(*args, **kwargs)


def get_chunk(*args, **kwargs):
    # Citation validation is a safety boundary.  A machine without the optional
    # retrieval stack must reject an unrecognised vector id, not turn that
    # rejection into a protocol exception.
    try:
        from .retrieve import get_chunk as _get_chunk
        return _get_chunk(*args, **kwargs)
    except ModuleNotFoundError as exc:
        if exc.name == "chromadb":
            return None
        raise


def coverage(*args, **kwargs):
    from .retrieve import coverage as _coverage
    return _coverage(*args, **kwargs)


def search_with_abstention(*args, **kwargs):
    from .retrieve import search_with_abstention as _search_with_abstention
    return _search_with_abstention(*args, **kwargs)
