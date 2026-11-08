"""Compute diff between v2 and v3 chunks by SHA256 of text.

Emits:
- kb/vec_build/v3/changed_chunks.jsonl: only chunks that need embedding
- kb/vec_build/v3/reuse_map.json: mapping of v3 indices to v2 indices
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

def diff_and_prepare(
    v2_chunks_path: Path = Path("kb/vec_build/chunks.jsonl"),
    v3_chunks_path: Path = Path("kb/vec_build/v3/chunks.jsonl"),
    out_dir: Path = Path("kb/vec_build/v3"),
) -> dict:
    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading v2 chunks from {v2_chunks_path}...")
    v2_sha_to_idx: dict[str, int] = {}
    with open(v2_chunks_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if not line.strip():
                continue
            row = json.loads(line)
            sha = hashlib.sha256(row["text"].encode("utf-8")).hexdigest()
            # If multiple have the exact same text, any of their indices points to identical vector
            if sha not in v2_sha_to_idx:
                v2_sha_to_idx[sha] = idx
    print(f"Loaded {len(v2_sha_to_idx)} unique text hashes from v2.")

    print(f"Scanning v3 chunks from {v3_chunks_path}...")
    changed_rows: list[dict] = []
    # reuse_map: list of (v3_idx, v2_idx)
    reuse_map: list[list[int]] = []
    total_v3 = 0

    changed_file = out_dir / "changed_chunks.jsonl"
    with open(v3_chunks_path, "r", encoding="utf-8") as fin, \
         open(changed_file, "w", encoding="utf-8") as fout:
        for idx, line in enumerate(fin):
            if not line.strip():
                continue
            total_v3 += 1
            row = json.loads(line)
            sha = hashlib.sha256(row["text"].encode("utf-8")).hexdigest()
            if sha in v2_sha_to_idx:
                reuse_map.append([idx, v2_sha_to_idx[sha]])
            else:
                entry = {"v3_idx": idx, "id": row["id"], "text": row["text"]}
                fout.write(json.dumps(entry, ensure_ascii=False) + "\n")
                changed_rows.append(entry)

    (out_dir / "reuse_map.json").write_text(json.dumps(reuse_map))
    
    stats = {
        "v2_unique_texts": len(v2_sha_to_idx),
        "v3_total_chunks": total_v3,
        "reused_count": len(reuse_map),
        "changed_count": len(changed_rows),
        "reused_pct": round(len(reuse_map) / max(total_v3, 1) * 100, 2),
        "changed_pct": round(len(changed_rows) / max(total_v3, 1) * 100, 2),
        "elapsed_s": round(time.time() - t0, 2),
        "changed_chunks_path": str(changed_file),
        "reuse_map_path": str(out_dir / "reuse_map.json"),
    }
    (out_dir / "diff_stats.json").write_text(json.dumps(stats, indent=2))
    print(json.dumps(stats, indent=2))
    return stats

if __name__ == "__main__":
    diff_and_prepare()
