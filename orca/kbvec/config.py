"""Paths and endpoints for the vector KB. Everything is overridable by environment variable."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN_REPO = Path(os.environ.get("ORCA_MAIN_REPO", "/Users/CharanVelavan/Charan/SSN/UAE/orca-ntn"))


def _p(env: str, default: Path) -> Path:
    return Path(os.environ.get(env, str(default)))


def sources_dir() -> Path: return _p("ORCA_KB_SOURCES", MAIN_REPO / "kb" / "sources")
def sources_yaml() -> Path: return _p("ORCA_KB_SOURCES_YAML", MAIN_REPO / "kb" / "sources.yaml")
def staging_dir() -> Path: return _p("ORCA_KB_STAGING", MAIN_REPO / "kb" / "staging")
def corpus_dir() -> Path: return _p("ORCA_CORPUS_DIR", MAIN_REPO / "corpus")


def records_files() -> list[Path]:
    base = _p("ORCA_KB_DIR", ROOT / "kb")
    return [base / "india" / "records.yaml", base / "global" / "records.yaml"]


def chroma_dir() -> Path: return _p("ORCA_CHROMA_DIR", ROOT / "chroma")
def cache_dir() -> Path: return _p("ORCA_KBVEC_CACHE", ROOT / "kb" / "vec_cache")
def snapshot_dir() -> Path: return _p("ORCA_KBVEC_SNAPSHOTS", ROOT / "kb" / "vec_snapshots")
def eval_file() -> Path: return _p("ORCA_KBVEC_EVAL", ROOT / "kb" / "vec_eval" / "questions.yml")


def embed_url() -> str: return os.environ.get("ORCA_EMBED_URL", "http://localhost:1234/v1")
def embed_model() -> str: return os.environ.get("ORCA_EMBED_MODEL", "text-embedding-nomic-embed-text-v1.5")
def embed_key() -> str: return os.environ.get("ORCA_EMBED_KEY", "lm-studio")
def embed_batch() -> int: return int(os.environ.get("ORCA_EMBED_BATCH", "16"))
def reranker_model() -> str: return os.environ.get("ORCA_RERANK_MODEL", "Xenova/ms-marco-MiniLM-L-6-v2")


COLLECTION = "orca_kb"
CHUNK_TOKENS = 512
CHUNK_OVERLAP = 50
DOC_PREFIX = "search_document: "
QUERY_PREFIX = "search_query: "
