# RAG v3 Phase 2 Final Results

**Evaluation date:** 9 Nov 2026 (IST)  
**Corpus:** `kb/vec_eval/questions_v2.yml`, tier `corpus`, test split (50 questions)  
**Query embedding:** LM Studio `text-embedding-qwen3-embedding-8b` for v2/v3; v1 uses its indexed model, `text-embedding-nomic-embed-text-v1.5`.  
**Reranker pipeline:** `BAAI/bge-reranker-base`, pool 15, text cap 1,500 chars, 8 threads.  
**Harness:** `evaluate.run_v2`, same session and scoring for all six runs. The no-rerank and rerank outputs are in the adjacent JSON files.

## Comparison

Latency is milliseconds. `Negative accuracy` is the RAG v2 spec score; negative abstention accuracy is also shown because that is the metric named in the requested comparison.

| Index / pipeline | Recall@5 | MRR@10 | Exact citation@1 | Amendment hit | Negative abstention accuracy | Negative spec accuracy | p50 latency | p95 latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v1, no reranker | 0.400 | 0.327 | 0.600 (3/5) | 0.400 | 0.900 (9/10) | 0.900 (9/10) | 598 | 11,310 |
| v1 + P1 reranker | 0.475 | 0.408 | 0.800 (4/5) | 0.600 | 0.700 (7/10) | 0.700 (7/10) | 4,582 | 13,176 |
| v2, no reranker | 0.575 | 0.470 | 1.000 (5/5) | 0.400 | 0.300 (3/10) | 0.300 (3/10) | 616 | 727 |
| v2 + P1 reranker | 0.700 | 0.535 | 1.000 (5/5) | 0.800 | 0.500 (5/10) | 0.500 (5/10) | 2,841 | 5,008 |
| v3, no reranker | 0.625 | 0.466 | 1.000 (5/5) | 0.600 | 0.400 (4/10) | 0.400 (4/10) | 901 | 1,625 |
| v3 + P1 reranker | 0.675 | 0.612 | 1.000 (5/5) | 0.800 | 0.300 (3/10) | 0.300 (3/10) | 3,527 | 4,167 |

## Ship rule

**FAIL — do not make v3 the default.** The plan requires test recall@5 and negative accuracy to both beat v1, and Mac p95 latency to be under 3 seconds. Against the corresponding v1 settings, v3 without reranking improves recall (0.625 vs 0.400) but misses negative accuracy (0.400 vs 0.900); its p95 is 1,625 ms. With reranking, v3 improves recall (0.675 vs 0.475) but misses negative accuracy (0.300 vs 0.700) and p95 is 4,167 ms. Since all required conditions are conjunctive, both configurations fail the rule.

## Exact-citation questions

Ranks below are the rank of a matching gold result in the returned list; `—` means no matching result in the top 10. None of these ten rows was abstained on. `v3 no-rerank / v3 + P1 pipeline`:

| Eval ID | Citation question | Rank |
|---|---|---:|
| V2-091 | What does Direction (ii) of the CERT-In Directions under section 70B(6) of the IT Act say? | 1 / 1 |
| V2-092 | What does Direction (iii) of the CERT-In Directions of 28 April 2022 require? | 1 / 1 |
| V2-093 | What does Direction (iv) of the CERT-In Directions under section 70B(6) say about logs? | 1 / 1 |
| V2-094 | What is item (ix) of Annexure I to the CERT-In Directions 2022? | 1 / 1 |
| V2-095 | What does Rule 7(1)(a) of the Telecom Cyber Security Rules 2024 say? | 1 / 1 |
| V2-096 | What does Rule 7(1)(j) of the Critical Telecommunication Infrastructure Rules 2024 say? | 1 / 1 |
| V2-097 | What does section 3.2.1 of the CERT-In / SIA-India space cyber security framework say? | 1 / 1 |
| V2-098 | What does Section 8(6) of the Digital Personal Data Protection Act 2023 say? | 1 / 1 |
| V2-099 | What does Rule 7 of the Digital Personal Data Protection Rules 2025 say? | — / 9 |
| V2-100 | What does Section 2(s) of the Telecommunications Act 2023 define? | 1 / 1 |

The test split contains five exact-citation questions, so both v3 configurations score 5/5 on the test metric. The table values and counts are test-split metrics. The ten exact-citation questions shown here include both dev and test rows; across all ten, v3 without reranking has 9/10 at rank 1 and v3 with reranking has 9/10 at rank 1 (V2-099 moves from no match in the top 10 to rank 9). The YAML currently splits the ten exact-citation questions evenly between dev and test, despite the task description referring to ten test questions.

## Parser audit

- **68 chunks** have a bare clause path exactly `(3)`, `(4)`, or `(5)` with no parent path. Examples include TCSR preamble chunks and additional corpus sources. These are ambiguous or unparented hierarchy labels.
- **1 chunk** has the known colliding path `Rule 2(1)(i)(ii)` (`in-tcsr-2024:p2:c13`), where the same `(i)` is interpreted first as a letter and again as a Roman marker.
- No parser change was made. These cases need corpus-specific interpretation, and correcting path metadata alone would leave the existing embedded header/text inconsistent with the vector. Any future correction that changes chunk text requires re-embedding the affected chunk; this phase did not re-embed.

## Vector/index completion

The merged matrix is `137,434 × 4,096`, float16, in `chunks.jsonl` order. All 137,434 IDs are unique and present once; values are finite; measured L2 norms range from 0.999754 to 1.000244. `manifest.json` now has a `vectors` section containing the matrix and ID SHA-256 hashes. The collection `orca_v3` was populated from this matrix with each chunk's metadata, including `clause_path`. `retrieve.py` builds its BM25 index lazily from the active Chroma collection selected by `ORCA_KBVEC_COLLECTION`; the same setting also selects the vector collection. Snapshot written to `kb/vec_snapshots/5bc27509717361cc.json` (137,434 chunks; snapshot reports no embed model metadata).

## Test suite

`.venv/bin/python -m pytest -q`: **3 failed, 319 passed, 2 skipped** (332.31 s). Failures:

- `tests/test_agents.py::test_adviser_answers_from_kb_with_citations` — returned chunk IDs rather than the fixture's expected record ID.
- `tests/test_agents.py::test_adviser_refuses_beyond_the_kb[What is the capital of France?]` — adviser returned `found=True`.
- `tests/test_agents.py::test_adviser_discards_llm_answers_with_bad_citations_or_verdicts` — expected LLM mode, got quote mode.

These tests are outside the vector assembly and retrieval evaluation path. The workspace already contained unrelated modified files before this work, so I cannot establish from this run whether these failures pre-date the current session.

## Measurement limits

The test split has 50 questions and 10 negatives. It contains five exact-citation questions; the YAML has ten exact-citation questions total across dev and test. Negative accuracy therefore moves in 10 percentage-point increments, while exact-citation accuracy on test moves in 20-point increments. Amendment hit is measured on the amendment subset in the same test harness. No confidence intervals or significance tests were measured. The table reports query latency measured during each sequential run on this Mac; the reranker rows include CPU reranking and the no-reranker rows do not. No cloud throughput, quality outside this fixed test set, or end-to-end application latency was measured.
