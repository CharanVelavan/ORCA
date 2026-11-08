# RAG v3 Phase 1 Retrieval Benchmark Results

Evaluated on 2026-11-09 (IST) against `kb/vec_eval/questions_v2.yml` (50 dev, 50 test queries across 4 categories: general, exact citation, amendment, and unanswerable/negative).

## Retrieval Benchmark Comparison

| Setting | Recall@5 | MRR@10 | NDCG@10 | Exact-Citation Hit@1 | Amendment Hit | Neg Abstained Rate | Neg Spec Acc | p50 Latency (ms) | p95 Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **v1 Baseline** (`orca_kb`, nomic-embed-v1.5, no rerank) | 0.400 | 0.327 | 0.362 | 0.600 | 0.400 | 0.900 | 0.900 | 432.3 | 4971.5 |
| **v2 Baseline** (`orca_v2`, qwen3-8b, no rerank) | 0.575 | 0.470 | 0.513 | 1.000 | 0.400 | 0.300 | 0.300 | 612.2 | 727.2 |
| **v2 + Reranker + Router + Abstention** (`orca_v2`, v3 Phase 1) | **0.700** | **0.535** | **0.582** | **1.000** | **0.800** | **0.500** | **0.500** | 2542.1 | 3026.9 |

### Metric Definitions
- **Recall@5**: Proportion of non-negative test queries whose gold document was retrieved within the top 5 positions without being abstained on.
- **MRR@10**: Mean Reciprocal Rank across positive test queries within the top 10 positions (unabstained).
- **NDCG@10**: Normalized Discounted Cumulative Gain at rank 10 across positive test queries.
- **Exact-Citation Hit@1**: Proportion of exact legal citation queries where the targeted clause chunk is boosted to rank 1 (10 / 10 = 100%).
- **Amendment Hit**: Hit rate for queries concerning amended provisions where the amending or amended law chunk is retrieved.
- **Neg Abstained Rate**: Proportion of negative/unanswerable test queries where the system explicitly abstained.
- **Neg Spec Acc**: Proportion of negative queries where the system either abstained OR no binding Indian provision was retrieved in top 3 hits.
- **Latency**: End-to-end retrieval latency measured per query on Apple Silicon CPU (including live embedding, vector retrieval, BM25, RRF fusion, deduplication, and cross-encoder reranking).

### Raw Benchmark Artefacts
- v1 baseline: `docs/research/rag-v3/p1/v1_corpus.json`
- v2 baseline (no rerank): `docs/research/rag-v3/p1/v2_norerank_corpus.json`
- v2 + v3p1 (rerank + router + abstention): `docs/research/rag-v3/p1/v2_v3p1_corpus.json`
