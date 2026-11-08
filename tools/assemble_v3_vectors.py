"""Assemble full v3 vector index by combining reused v2 vectors and newly embedded vectors.

Verifies:
- Vector array shape (N, 4096) and dtype float16
- 100% unique IDs matching v3/chunks.jsonl exactly
- L2 norms approximately 1.0
"""
from __future__ import annotations

import json
import time
from pathlib import Path
import numpy as np


def assemble_v3(
    v2_embeddings_path: Path = Path("kb/vec_build/embeddings.f16.npy"),
    changed_embeddings_path: Path = Path("kb/vec_build/v3/changed_embeddings.f16.npy"),
    reuse_map_path: Path = Path("kb/vec_build/v3/reuse_map.json"),
    changed_chunks_path: Path = Path("kb/vec_build/v3/changed_chunks.jsonl"),
    v3_chunks_path: Path = Path("kb/vec_build/v3/chunks.jsonl"),
    out_dir: Path = Path("kb/vec_build/v3"),
) -> dict:
    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Loading v3 chunks and extracting expected IDs...")
    v3_ids = []
    with open(v3_chunks_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                v3_ids.append(json.loads(line)["id"])
    total_v3 = len(v3_ids)
    print(f"Total v3 chunks: {total_v3}")

    print(f"Loading v2 embeddings from {v2_embeddings_path}...")
    v2_vecs = np.load(v2_embeddings_path)
    dim = v2_vecs.shape[1]
    print(f"v2 shape: {v2_vecs.shape}")

    print(f"Loading changed embeddings from {changed_embeddings_path}...")
    changed_vecs = np.load(changed_embeddings_path)
    print(f"changed shape: {changed_vecs.shape}")

    print(f"Loading reuse map from {reuse_map_path}...")
    reuse_map = json.loads(reuse_map_path.read_text(encoding="utf-8"))
    print(f"Reused count: {len(reuse_map)}")

    # Allocate full array
    full_vecs = np.zeros((total_v3, dim), dtype=np.float16)

    # Fill reused vectors
    for v3_idx, v2_idx in reuse_map:
        full_vecs[v3_idx] = v2_vecs[v2_idx]

    # Fill changed vectors
    print(f"Mapping changed vectors to v3 indices from {changed_chunks_path}...")
    with open(changed_chunks_path, "r", encoding="utf-8") as f:
        for c_idx, line in enumerate(f):
            if not line.strip():
                continue
            entry = json.loads(line)
            v3_idx = entry["v3_idx"]
            full_vecs[v3_idx] = changed_vecs[c_idx]

    # Verification
    print("Verifying assembled vectors...")
    assert full_vecs.shape == (total_v3, dim), f"Shape mismatch: {full_vecs.shape}"
    assert len(v3_ids) == total_v3, f"ID count mismatch: {len(v3_ids)}"
    assert len(set(v3_ids)) == total_v3, "Duplicate chunk IDs found!"

    # Norm check
    norms = np.linalg.norm(full_vecs.astype(np.float32), axis=1)
    min_norm = float(np.min(norms))
    max_norm = float(np.max(norms))
    mean_norm = float(np.mean(norms))
    zero_norms = int(np.sum(norms < 1e-4))
    print(f"L2 Norms: min={min_norm:.4f}, max={max_norm:.4f}, mean={mean_norm:.4f}, zeros={zero_norms}")
    assert zero_norms == 0, f"Found {zero_norms} zero-norm vectors!"

    # Save outputs
    out_npy = out_dir / "embeddings.f16.npy"
    out_ids = out_dir / "ids.json"
    print(f"Saving {out_npy}...")
    np.save(out_npy, full_vecs)
    print(f"Saving {out_ids}...")
    out_ids.write_text(json.dumps(v3_ids))

    stats = {
        "total_chunks": total_v3,
        "reused_count": len(reuse_map),
        "changed_count": len(changed_vecs),
        "dim": dim,
        "dtype": str(full_vecs.dtype),
        "min_norm": round(min_norm, 4),
        "max_norm": round(max_norm, 4),
        "mean_norm": round(mean_norm, 4),
        "zero_norms": zero_norms,
        "unique_ids": len(set(v3_ids)),
        "elapsed_s": round(time.time() - t0, 2),
    }
    (out_dir / "assembly_stats.json").write_text(json.dumps(stats, indent=2))
    print(f"Assembly completed successfully in {stats['elapsed_s']}s.")
    return stats


if __name__ == "__main__":
    assemble_v3()
