# RAG v3 Phase 2 - Re-chunk & Re-embed Implementation Report

**Timestamp:** 9 Nov 2026, 00:30 IST  
**Phase:** Phase 2 (Items 6–9 of `docs/plan/RAG_V3.md`)  
**Status:** In Progress (GPU embedding active on GCP Spot VM)  
**Author:** Antigravity Pair Programmer (Phase 2 Lead)

---

## 1. Executive Summary

Phase 2 replaces the flawed statutory/regulatory chunk parsing of v2 with a canonical legal hierarchy parser, preserves exact hierarchy breadcrumbs, audits and skips redundant Docling table/OCR sidecars, and computes updated 8B dense vectors for all changed chunks using an RTX PRO 6000 96 GB Spot VM on GCP while reusing 23.23% of identical v2 vectors by text hash.

### Key Measured Results So Far:
- **Corpus Size:** 381 source documents (25 registered official + 356 staged corpus), 30,078 total PDF pages.
- **Docling Audit:** 0 relevant pages with missing text layers in verified/eval sources; Docling skipped per plan criteria.
- **Total v3 Chunks:** 137,434 chunks across 370 sources (11 unparsable legacy `.doc`/`.xml` files skipped gracefully).
- **Vector Reuse Rate:** **31,932 / 137,434 chunks (23.23%)** byte-identical to v2; preserved directly from `kb/vec_build/embeddings.f16.npy`.
- **Changed Chunks to Embed:** **105,502 chunks (76.77%)**.
- **Unit Tests:** 5 / 5 passed in `tests/test_chunk_hierarchy.py`.

---

## 2. Changes Implemented

### Item 6: Legal Hierarchy Parser (`orca/kbvec/chunk.py`)
- **4-Level Hierarchy Support:**
  - Level 0: Primary statutory units (`Rule`, `Section`, `Article`, `Direction`, `Regulation` N, `Annexure I`, `Schedule`, `para 3.2.1`).
  - Level 1: Sub-sections / sub-rules `(1)`..`(99)`.
  - Level 2: Clauses `(a)`..`(z)`.
  - Level 3: Sub-clauses `(i)`..`(xx)`.
- **Kind Label Corrections:**
  - Indian Rules documents (e.g. `in-tcsr-2024`, `in-ctir-2024`) now canonicalise as `"Rule"`, not `"s."` (section).
  - Directions (e.g. CERT-In Directions 2022) canonicalise as `"Direction"`.
  - Acts canonicalise as `"Section"`.
  - EU regulations canonicalise as `"Article"`.
- **Inline Headings Parsing:**
  - Handles legal gazette format where headings inline clause numbers (e.g. `7. Reporting of security incidents. — (1) ...`).
- **Unit Test Suite:**
  - Added `tests/test_chunk_hierarchy.py` covering:
    1. `test_in_tcsr_2024_rule_7_1_a`: Verifies `Rule 7(1)(a)` exists with exact parent `Rule 7`.
    2. `test_in_ctir_2024_rule_7_1_j`: Verifies `Rule 7(1)(j)` exists.
    3. `test_in_dpdp_act_2023_section_8_6`: Verifies `Section 8(6)` exists under `Section 8`.
    4. `test_cert_in_directions_hierarchy`: Verifies `Direction (ii)`, `(iii)`, `(iv)`, and `Annexure I, item (ix)`.
    5. `test_deep_hierarchy_progression`: Verifies `Rule 1` > `(1)` > `(a)` > `(i)` canonical paths.

### Item 7: Breadcrumb Header (`orca/kbvec/ingest.py`)
- Preserved the v2 breadcrumb header format:
  `{title} | {authority} | {jurisdiction} | {binding_status}, in force {in_force_from} | {clause_path} | p.{page}`
- Updated `clause_path` to reflect the fixed legal hierarchy paths (e.g. `Rule 7(1)(a)`).

### Item 8: Docling Audit & Decision
- Audited all 381 sources across `kb/sources` and `corpus/raw`:
  - Blank or near-empty pages: 28 total across the entire corpus (all are blank cover/back pages of official PDFs).
  - Relevant evaluation/verified sources (`in-tcsr-2024`, `in-cert-in-directions-2022`, `in-dpdp-act-2023`, `in-telecom-act-2023`): 0 missing text pages. All annexures/schedules have 100% extractable text layers via PyMuPDF.
  - Per RAG v3 plan item 8 ("If fewer than ~30 such pages, skip Docling and say so"), full Docling re-parsing was skipped to avoid invalidating byte-identical embeddings.

### Item 9: Re-chunking & GPU Embedding
- Chunk file: `kb/vec_build/v3/chunks.jsonl` (137,434 rows, sha256: `da1bbcb6321c8511a0dee48cbefc57a65e2eed3ecba5af8aca23f4f34e8a0950`).
- Diff tool: `tools/diff_chunks.py` computed text SHA256 matches:
  - Reused: 31,932 entries mapped in `kb/vec_build/v3/reuse_map.json`.
  - Changed: 105,502 entries staged in `kb/vec_build/v3/changed_chunks.jsonl`.
- Spot VM Infrastructure on GCP:
  - VM Name: `orca-rag-v3`
  - Machine Type: `g4-standard-48` (1x NVIDIA RTX PRO 6000 Blackwell 96 GB)
  - Zone: `asia-south1-c`
  - Subnet: `qwen-ai-subnet`, Network Tag: `qwen-gpu`
  - Image: `qwen38-senior-v1`
  - Boot Disk: 200 GB hyperdisk-balanced (Spot provisioning, STOP on preemption, max run 6h).
- Embedding Script (`finetune/colab/embed_changed.py`):
  - Model: `Qwen/Qwen3-Embedding-8B` in bf16 with SDPA attention.
  - Length-bucketed dynamic batching (batch sizes 2 to 32 depending on token length).
  - Shard checkpoints every 2,000 chunks to disk (`out/shards/shard_*.npy`) for crash/preemption resilience.
  - Memory bounds: VRAM usage bounded within ~33 GB / 97.8 GB; compute utilization 100% at ~500W power draw.

---

## 3. Files Touched

- `orca/kbvec/chunk.py`: Legal hierarchy parser, regexes, kinds, and parent mapping.
- `orca/kbvec/ingest.py`: Chunking paths, document type priorities, and added `load_vectors_v3`.
- `tests/test_chunk_hierarchy.py`: New unit tests for RAG v3 hierarchy.
- `tools/diff_chunks.py`: Script to diff v2 and v3 chunks by SHA256.
- `tools/assemble_v3_vectors.py`: Script to assemble reused and newly embedded vectors.
- `finetune/colab/embed_changed.py`: Production GPU embedding runner with shard checkpoints.
- `docs/research/rag-v3/p2/REPORT.md`: This report.

---

## 4. Next Steps (upon GPU embedding completion)

1. Download vector outputs (`changed_embeddings.f16.npy`, `changed_ids.json`, `changed_meta.json`).
2. **Immediately delete VM `orca-rag-v3` and its boot disk**; verify with `gcloud compute instances/disks list`.
3. Run `tools/assemble_v3_vectors.py` to create `kb/vec_build/v3/embeddings.f16.npy` (137,434 x 4096) and `ids.json`.
4. Call `load_vectors_v3()` to populate collection `orca_v3`.
5. Run evaluation: `ORCA_KBVEC_COLLECTION=orca_v3 .venv/bin/python -m orca.kbvec eval --v2 --tier corpus`.
6. Update this report with final measured eval metrics, norms, and VM billing hours.
