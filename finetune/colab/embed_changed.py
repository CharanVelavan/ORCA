"""Embed changed chunks with Qwen/Qwen3-Embedding-8B on GPU.

Features:
- Length-bucketed dynamic batching within each shard: eliminates padding waste and prevents OOM on 2000-word parent chunks
- Shard checkpoints (default 2,000 chunks) so a crash/preemption resumes cleanly
- Preserves exact row ordering in each shard
- L2-normalised float16 output
- No instruction prefix for document chunks (same as v2)
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from pathlib import Path

import numpy as np


def encode_shard_bucketed(model, texts: list[str]) -> np.ndarray:
    """Encode texts by length buckets within a shard to maximize speed and prevent OOM."""
    import torch

    order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
    vectors = [None] * len(texts)

    idx = 0
    while idx < len(order):
        first_word_count = len(texts[order[idx]].split())
        if first_word_count > 1200:
            b_size = 2
        elif first_word_count > 600:
            b_size = 8
        elif first_word_count > 300:
            b_size = 16
        else:
            b_size = 32

        batch_indices = order[idx : idx + b_size]
        batch_texts = [texts[i] for i in batch_indices]

        vecs = model.encode(
            batch_texts,
            batch_size=len(batch_texts),
            normalize_embeddings=False,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        for i, vec in zip(batch_indices, vecs):
            vectors[i] = vec
        idx += len(batch_indices)

    assert all(v is not None for v in vectors), "Missing vector in shard encoding"
    return np.asarray(vectors, dtype=np.float32)


def embed_changed(
    input_file: Path,
    output_dir: Path,
    model_name: str = "Qwen/Qwen3-Embedding-8B",
    shard_size: int = 2000,
) -> dict:
    import torch
    from sentence_transformers import SentenceTransformer

    t0 = time.time()
    output_dir.mkdir(parents=True, exist_ok=True)
    shards_dir = output_dir / "shards"
    shards_dir.mkdir(parents=True, exist_ok=True)

    print(f"Reading {input_file}...")
    rows = [json.loads(line) for line in input_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    total = len(rows)
    print(f"Loaded {total} changed chunks to embed.")

    if total == 0:
        empty = np.zeros((0, 4096), dtype=np.float16)
        np.save(output_dir / "changed_embeddings.f16.npy", empty)
        (output_dir / "changed_ids.json").write_text("[]")
        return {"total": 0, "model": model_name, "elapsed_s": 0}

    # Check existing shard checkpoints
    existing_shards = sorted(shards_dir.glob("shard_*.npy"))
    completed_chunks = 0
    all_vectors = []

    for sf in existing_shards:
        part = np.load(sf)
        completed_chunks += len(part)
        all_vectors.append(part)

    print(f"Found {len(existing_shards)} existing shard checkpoints with {completed_chunks}/{total} chunks.")

    if completed_chunks < total:
        print(f"Loading {model_name} on GPU in bf16 with SDPA...")
        model = SentenceTransformer(
            model_name,
            model_kwargs={"torch_dtype": torch.bfloat16, "attn_implementation": "sdpa"},
            trust_remote_code=True,
            device="cuda",
        )
        print("Model loaded successfully.")

        shard_idx = len(existing_shards)
        while completed_chunks < total:
            next_chunk_end = min(completed_chunks + shard_size, total)
            shard_rows = rows[completed_chunks:next_chunk_end]
            shard_texts = [r["text"] for r in shard_rows]

            t_shard = time.time()
            shard_vecs = encode_shard_bucketed(model, shard_texts)
            shard_path = shards_dir / f"shard_{shard_idx:05d}.npy"
            np.save(shard_path, shard_vecs)
            all_vectors.append(shard_vecs)

            completed_chunks += len(shard_rows)
            shard_idx += 1
            torch.cuda.empty_cache()
            print(
                f"Saved checkpoint {shard_path.name} ({completed_chunks}/{total} chunks, shard {time.time() - t_shard:.1f}s, total {time.time() - t0:.1f}s)",
                flush=True,
            )

    print("Concatenating all shards and normalizing...")
    final_vecs = np.concatenate(all_vectors, axis=0).astype(np.float32)
    assert len(final_vecs) == total, f"Expected {total} vectors, got {len(final_vecs)}"

    # L2-normalise
    norms = np.maximum(np.linalg.norm(final_vecs, axis=1, keepdims=True), 1e-12)
    final_vecs /= norms

    out_npy = output_dir / "changed_embeddings.f16.npy"
    out_ids = output_dir / "changed_ids.json"
    out_meta = output_dir / "changed_meta.json"

    np.save(out_npy, final_vecs.astype(np.float16))
    out_ids.write_text(json.dumps([r["id"] for r in rows]))

    meta = {
        "model_id": model_name,
        "total_chunks": total,
        "dim": int(final_vecs.shape[1]),
        "dtype": "float16",
        "normalised": True,
        "elapsed_s": round(time.time() - t0, 2),
        "mean_norm": float(np.mean(np.linalg.norm(final_vecs, axis=1))),
    }
    out_meta.write_text(json.dumps(meta, indent=2))
    print(f"Saved {out_npy} and {out_ids} successfully in {meta['elapsed_s']}s.", flush=True)
    return meta


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("changed_chunks.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    parser.add_argument("--model", type=str, default="Qwen/Qwen3-Embedding-8B")
    parser.add_argument("--shard-size", type=int, default=2000)
    parser.add_argument("--token-budget", type=int, default=8192)  # kept for CLI compat
    parser.add_argument("--checkpoint-every", type=int, default=2000)  # kept for CLI compat
    args = parser.parse_args()
    embed_changed(args.input, args.output_dir, args.model, args.shard_size)
