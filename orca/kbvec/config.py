"""Paths and endpoints for the vector KB. Everything is overridable by environment variable."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN_REPO = Path(os.environ.get("ORCA_MAIN_REPO", str(ROOT)))


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
def eval_v2_file() -> Path: return _p("ORCA_KBVEC_EVAL_V2", ROOT / "kb" / "vec_eval" / "questions_v2.yml")
def vec_build_dir() -> Path: return _p("ORCA_KBVEC_BUILD", ROOT / "kb" / "vec_build")


def embed_url() -> str: return os.environ.get("ORCA_EMBED_URL", "http://localhost:1234/v1")
V1_EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5"
V2_EMBED_MODEL = "text-embedding-qwen3-embedding-8b"   # LM Studio GGUF of Qwen/Qwen3-Embedding-8B (index built in bf16)
V2_QUERY_INSTRUCTION = ("Instruct: Given a question about telecom, cyber security or space law, "
                        "retrieve the legal provision that answers it\nQuery: ")


def embed_model() -> str:
    default = V2_EMBED_MODEL if collection_name() == "orca_v2" else V1_EMBED_MODEL
    return os.environ.get("ORCA_EMBED_MODEL", default)


def _is_qwen3_embed() -> bool: return "qwen3-embedding" in embed_model().lower()
def doc_prefix() -> str: return "" if _is_qwen3_embed() else DOC_PREFIX
def query_prefix() -> str: return V2_QUERY_INSTRUCTION if _is_qwen3_embed() else QUERY_PREFIX
def rerank_pool() -> int: return int(os.environ.get("ORCA_RERANK_POOL", "15"))
def rerank_chars() -> int: return int(os.environ.get("ORCA_RERANK_CHARS", "1500"))
def rerank_device() -> str: return os.environ.get("ORCA_RERANK_DEVICE", "cpu")
def rerank_threads() -> int: return int(os.environ.get("ORCA_RERANK_THREADS", str(min(8, os.cpu_count() or 4))))
def embed_key() -> str: return os.environ.get("ORCA_EMBED_KEY", "lm-studio")
def embed_batch() -> int: return int(os.environ.get("ORCA_EMBED_BATCH", "16"))
def reranker_model() -> str: return os.environ.get("ORCA_RERANK_MODEL", "BAAI/bge-reranker-base")
def collection_name() -> str: return os.environ.get("ORCA_KBVEC_COLLECTION", "orca_v2")
# Cut on the cross-encoder (bge-reranker-base) top-1 logit. Chosen on the dev split only (dev plateau -3.9 .. -2.1,
# midpoint rounded); see docs/research/rag-v3/ABSTENTION.md. Meaningless for other rerankers or without one.
DEFAULT_ABSTAIN_THRESHOLD = -3.0


def abstain_threshold() -> float | None:
    value = os.environ.get("ORCA_ABSTAIN_THRESHOLD")
    if value is not None:
        return float(value) if value != "" else None   # empty string turns abstention off
    return DEFAULT_ABSTAIN_THRESHOLD if reranker_model() == "BAAI/bge-reranker-base" else None
def abstain_temperature() -> float:
    return float(os.environ.get("ORCA_ABSTAIN_TEMPERATURE", "2.0"))
def abstain_prob_threshold() -> float | None:
    v = os.environ.get("ORCA_ABSTAIN_PROB_THRESHOLD")
    return float(v) if v not in (None, "") else None
def abstain_margin_threshold() -> float | None:
    v = os.environ.get("ORCA_ABSTAIN_MARGIN_THRESHOLD")
    return float(v) if v not in (None, "") else None
def abstain_z_threshold() -> float | None:
    v = os.environ.get("ORCA_ABSTAIN_Z_THRESHOLD")
    return float(v) if v not in (None, "") else None


# ``orca_kb`` is the legacy v1 collection.  v2 never replaces it.
COLLECTION = "orca_v2"
CHUNK_TOKENS = 512
CHUNK_OVERLAP = 50
DOC_PREFIX = "search_document: "
QUERY_PREFIX = "search_query: "
QWEN_QUERY_INSTRUCTION = ("Instruct: Given a question about telecom, cyber security or space law, "
                          "retrieve the legal provision that answers it\nQuery: ")
