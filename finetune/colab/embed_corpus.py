"""Colab GPU stage for ORCA RAG v2.  Run from a fresh clone; no corpus is committed.

The Drive zip must be MyDrive/orca-ft/rag/orca-corpus.zip and contain corpus/raw/**
and kb/sources/**.  Staged YAML remains in the clone at kb/staging.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import zipfile
from pathlib import Path

import numpy as np

DRIVE = Path("/content/drive/MyDrive/orca-ft/rag")
REPO = Path(os.environ.get("ORCA_REPO", "/content/orca-ntn"))
WORK = Path("/content/orca-corpus")
OUT = DRIVE / "out"
MODEL = os.environ.get("ORCA_EMBED_MODEL", "Qwen/Qwen3-Embedding-8B")
RERANKER = os.environ.get("ORCA_RERANK_MODEL", "Qwen/Qwen3-Reranker-4B")
QUERY_INSTRUCTION = ("Instruct: Given a question about telecom, cyber security or space law, "
                     "retrieve the legal provision that answers it\nQuery: ")


def unzip_corpus() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(DRIVE / "orca-corpus.zip") as zf:
        # Reject unsafe archive member names even though it is user-supplied data.
        for member in zf.infolist():
            target = (WORK / member.filename).resolve()
            if not target.is_relative_to(WORK.resolve()):
                raise ValueError(f"unsafe zip member: {member.filename}")
        zf.extractall(WORK)


def run_chunker() -> Path:
    out = OUT / "chunks.jsonl"
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run(["python", "-m", "orca.kbvec", "chunk", "--corpus", "--corpus-dir", str(WORK / "corpus"),
                    "--sources-dir", str(WORK / "kb" / "sources"), "--out", str(out)], cwd=REPO, check=True)
    return out


def encode_sorted(model, texts: list[str], batch_size: int, prompt: bool = False) -> np.ndarray:
    """Length sorting reduces padding; restore original order before writing ids."""
    order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
    result = [None] * len(texts)
    for start in range(0, len(order), batch_size):
        ix = order[start:start + batch_size]
        batch = [QUERY_INSTRUCTION + texts[i] if prompt else texts[i] for i in ix]
        vectors = model.encode(batch, batch_size=len(batch), normalize_embeddings=True, show_progress_bar=False,
                               convert_to_numpy=True)
        for i, vector in zip(ix, vectors):
            result[i] = vector
    return np.asarray(result, dtype=np.float32)


def embed() -> None:
    from sentence_transformers import SentenceTransformer
    import torch
    chunks = run_chunker()
    rows = [json.loads(line) for line in chunks.read_text().splitlines() if line.strip()]
    model = SentenceTransformer(MODEL, model_kwargs={"torch_dtype": torch.bfloat16, "attn_implementation": "sdpa"},
                            trust_remote_code=True, device="cuda")
    vectors = encode_sorted(model, [r["text"] for r in rows], batch_size=int(os.environ.get("ORCA_BATCH", "24")))
    vectors /= np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)
    np.save(OUT / "embeddings.f16.npy", vectors.astype(np.float16))
    (OUT / "ids.json").write_text(json.dumps([r["id"] for r in rows]))
    (OUT / "model.json").write_text(json.dumps({"model_id": MODEL, "dim": int(vectors.shape[1]), "dtype": "float16",
        "normalised": True, "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, indent=2))
    # Keep the exact chunk payload alongside embeddings; it is the load-vectors input.
    (OUT / "chunks.jsonl").write_text(chunks.read_text())
    questions = __import__("yaml").safe_load((REPO / "kb/vec_eval/questions_v2.yml").read_text())
    qvec = encode_sorted(model, [q["question"] for q in questions], batch_size=32, prompt=True)
    np.save(OUT / "questions_v2.f16.npy", qvec.astype(np.float16))
    (OUT / "questions_v2_ids.json").write_text(json.dumps([q["id"] for q in questions]))


def rerank_eval() -> None:
    """Optional 4B GPU comparison. It scores every question against its top retrieved candidates."""
    from sentence_transformers import CrossEncoder
    rows = [json.loads(line) for line in (OUT / "chunks.jsonl").read_text().splitlines() if line.strip()]
    questions = __import__("yaml").safe_load((REPO / "kb/vec_eval/questions_v2.yml").read_text())
    # This dense candidate approximation makes the comparison replayable; local evaluation remains authoritative.
    vec = np.load(OUT / "embeddings.f16.npy").astype(np.float32)
    qvec = np.load(OUT / "questions_v2.f16.npy").astype(np.float32)
    model = CrossEncoder(RERANKER, trust_remote_code=True, device="cuda")
    output = []
    for q, query_vec in zip(questions, qvec):
        top = np.argsort(-(vec @ query_vec))[:50]
        scores = model.predict([[q["question"], rows[i]["text"][:8000]] for i in top], batch_size=8)
        output.append({"id": q["id"], "model": RERANKER,
                       "candidates": [{"id": rows[i]["id"], "score": float(s)} for i, s in zip(top, scores)]})
    (OUT / "reranker_4b_scores.json").write_text(json.dumps(output, indent=2))


if __name__ == "__main__":
    unzip_corpus()
    embed()
    rerank_eval()
