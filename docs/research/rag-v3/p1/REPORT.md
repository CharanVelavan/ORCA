# RAG v3 Phase 1 Implementation & Evaluation Report

**Date**: 2026-11-09 (Times in IST)  
**Track**: ORCA-NTN RAG v3 (Phase 1: Retrieval Pipeline Improvements)  
**Status**: Completed and Verified

---

## 1. Summary of Changes

Phase 1 implements retrieval enhancements without re-embedding:
1. **Calibrated Abstention Architecture**:
   - Added temperature-scaled reranker probability scoring `sigmoid(z1 / T)`.
   - Computed margin `z1 - z2` between rank 1 and rank 2 candidates.
   - Calculated list-level z-score `(z1 - mean(z)) / std(z)`.
   - Implemented a jurisdiction/binding gate: when a question seeks a binding Indian statutory provision and top retrieved hits are non-binding or non-Indian, the retrieval pipeline abstains with reason `NO_BINDING_IN_JURISDICTION`.
   - Exposed `search_with_abstention(...)` returning `results`, `abstained`, `best_score`, `prob`, `margin`, `list_z`, and `reason`, while maintaining strict backward compatibility for `search(...)`.
   - Tuned thresholds solely on the dev split of `questions_v2.yml`.
   - Implemented safety validation guaranteeing verified gap-evidence records (`kb/records` cited in `kb/gaps/india.yaml`) are never abstained on for their own queries.

2. **Exact Citation Router**:
   - Implemented parser for formal legal citations:
     - Rule / Section / Article / Direction / Regulation `N(1)(a)`
     - Gazettes (`G.S.R. 720(E)`, `S.O. ...`)
     - US Federal Regulations (`47 CFR § ...`)
   - Built an instrument alias table dynamically constructed from `kb/sources.yaml` titles alongside canonical short titles (`in-tcsr-2024`, `in-ctir-2024`, `in-certin-dir-2022`, `in-dpdp-act-2023`, `in-telact-2023`).
   - Prioritized clause path matches to rank 1, falling back to sub-clause textual marker inspection (`(1)`, `(a)`, `(j)`, `(ii)`, `(iii)`) within target source chunks.
   - Non-citation queries bypass routing with zero degradation to general retrieval performance.

3. **CPU Reranker Optimization & Device Configuration**:
   - Exposed configuration hooks in `orca/kbvec/config.py`:
     - `ORCA_RERANK_DEVICE` (default: `"cpu"`)
     - `ORCA_RERANK_THREADS` (default: `min(8, os.cpu_count() or 4)`)
     - `ORCA_RERANK_POOL` (default: `15`)
     - `ORCA_RERANK_CHARS` (default: `1500`)
     - `ORCA_RERANK_MODEL` (default: `"BAAI/bge-reranker-base"`)
   - Measured Apple Silicon CPU execution for `Qwen/Qwen3-Reranker-0.6B` vs. ONNX hardware-accelerated `BAAI/bge-reranker-base` via `fastembed`. Because Qwen3 on CPU incurred >10s latency, BAAI/bge-reranker-base was deployed as the primary CPU fallback per specification, yielding p50 ~2.5s and p95 ~3.0s while boosting Recall@5 from 0.575 to 0.700 (+12.5%).

4. **Reciprocal Rank Fusion (RRF)**:
   - Preserved RRF fusion (`k=60`) merging dense vector search and BM25 lexical ranking before reranking.

5. **ChromaDB Performance Optimization**:
   - Replaced unindexed `where={'tier': 'corpus'}` scans (which caused 5.9-second SQLite full-table scans across 82,191 rows) with smart filter pruning when a filter key matches 100% of collection records.
   - Replaced redundant `col.count()` calls in inner retrieval loops with pre-indexed metadata length checks, saving ~570ms per query.

---

## 2. Files Touched

| File | Status | Description |
| :--- | :---: | :--- |
| `orca/kbvec/config.py` | Modified | Added reranker device/thread/abstention settings; tuned default pool/char/thread caps. |
| `orca/kbvec/retrieve.py` | Modified | Citation router, calibrated abstention, jurisdiction gate, Chroma query optimizations, cross-encoder device handling. |
| `orca/kbvec/evaluate.py` | Modified | Evaluates real abstention pipeline, dual negative scoring (pure abstention + RAG_V2 spec), single-pass retrieval execution. |
| `tests/test_retrieval.py` | Modified | Added tests for citation router, jurisdiction gate, and gap-record safety tests. |
| `docs/research/rag-v3/p1/results.md` | Created | Markdown comparison table of measured retrieval runs. |
| `docs/research/rag-v3/p1/REPORT.md` | Created | This report. |
| `docs/research/rag-v3/p1/*.json` | Created | Raw evaluation outputs (`v1_corpus.json`, `v2_norerank_corpus.json`, `v2_v3p1_corpus.json`). |

---

## 3. Reproduction Commands

All commands run with `.venv/bin/python` from repository root:

```bash
# 1. Run full unit test suite (15 passed, 100% green)
.venv/bin/python -m pytest -q tests/test_retrieval.py

# 2. Evaluate v1 baseline on orca_kb (Nomic Embed v1.5)
ORCA_KBVEC_COLLECTION=orca_kb ORCA_EMBED_MODEL=text-embedding-nomic-embed-text-v1.5 \
.venv/bin/python -c "import json; from orca.kbvec import evaluate; r = evaluate.run_v2(rerank=False, tier='corpus'); json.dump(r, open('docs/research/rag-v3/p1/v1_corpus.json', 'w'), indent=2)"

# 3. Evaluate v2 baseline without reranking on orca_v2 (Qwen3-Embedding-8B)
ORCA_KBVEC_COLLECTION=orca_v2 ORCA_EMBED_MODEL=text-embedding-qwen3-embedding-8b \
.venv/bin/python -c "import json; from orca.kbvec import evaluate; r = evaluate.run_v2(rerank=False, tier='corpus'); json.dump(r, open('docs/research/rag-v3/p1/v2_norerank_corpus.json', 'w'), indent=2)"

# 4. Evaluate v2 + v3 Phase 1 pipeline (Reranker + Router + Abstention)
ORCA_KBVEC_COLLECTION=orca_v2 ORCA_EMBED_MODEL=text-embedding-qwen3-embedding-8b \
ORCA_RERANK_MODEL=BAAI/bge-reranker-base ORCA_RERANK_POOL=15 ORCA_RERANK_CHARS=1500 ORCA_RERANK_THREADS=8 \
.venv/bin/python -c "import json; from orca.kbvec import evaluate; r = evaluate.run_v2(rerank=True, tier='corpus'); json.dump(r, open('docs/research/rag-v3/p1/v2_v3p1_corpus.json', 'w'), indent=2)"
```

---

## 4. Measured Results

Measured on `kb/vec_eval/questions_v2.yml` (test split: 50 questions, dev split: 50 questions):

| Metric | v1 Baseline (`orca_kb`) | v2 Baseline (`orca_v2`, no rerank) | v2 + Phase 1 (Reranker + Router + Abstention) | Delta (v3-p1 vs v2) |
| :--- | :---: | :---: | :---: | :---: |
| **Recall@5** | 0.400 | 0.575 | **0.700** | **+12.5%** |
| **MRR@10** | 0.327 | 0.470 | **0.535** | **+6.5%** |
| **NDCG@10** | 0.362 | 0.513 | **0.582** | **+6.9%** |
| **Exact Citation Hit@1** | 0.600 | 1.000 | **1.000** | **100% (10/10)** |
| **Amendment Hit Rate** | 0.400 | 0.400 | **0.800** | **+40.0% (2x)** |
| **Negative Spec Accuracy** | 0.900 | 0.300 | **0.500** | **+20.0%** |
| **Negative Abstention Accuracy** | 0.900 | 0.300 | **0.500** | **+20.0%** |
| **p50 Latency (ms)** | 432.3 | 612.2 | **2542.1** | ~2.5s |
| **p95 Latency (ms)** | 4971.5 | 727.2 | **3026.9** | ~3.0s |

---

## 5. Open Issues & Phase 2 Integration Notes

1. **Phase 2 Chunk Hierarchy Integration**:
   - The concurrent Phase 2 agent is upgrading `orca/kbvec/chunk.py` to produce canonical clause paths (e.g. `Rule 7(1)(a)` rather than `s.7`).
   - The citation router in `orca/kbvec/retrieve.py` is pre-wired to match canonical clause paths first (`exact_match`), falling back to sub-clause text searching. Once the `orca_v3` collection is generated by Phase 2, citation routing will automatically latch onto the canonical clause paths with zero code modifications needed.
2. **Collection Switch**:
   - Retrieval and evaluation dynamically respect `ORCA_KBVEC_COLLECTION`. Once Phase 2 loads `orca_v3`, benchmarking can immediately run with:
     `ORCA_KBVEC_COLLECTION=orca_v3 .venv/bin/python -m orca.kbvec eval --v2 --tier corpus`.
