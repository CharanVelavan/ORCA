# RAG v3 - unified plan (8 Nov 2026, 23:20 IST)

Source: a two-round debate between two Gemini 3.8 Flash agents (accuracy-first vs pragmatic):
`docs/research/rag-v3/flashA_round{1,2}.md`, `flashB_round{1,2}.md`. Their claims were checked against the code and
the index before being adopted. **Projected numbers in the debate files (e.g. "Hit@1 0.98", "~110 ms") are not
measurements and are not used here.** Every v3 change is accepted only if the eval shows it.

## Baseline (measured 8 Nov, 50 held-out test questions, corpus tier)
| | v1 | v2 | v2 + 0.6B reranker (10 cand.) |
|---|---|---|---|
| recall@5 | 0.35 | 0.475 | 0.55 |
| exact-citation hit@1 | 0 | 0 | 0.20 |
| negative abstention | 0.60 | 0 | 0 |
Latency numbers from that run are invalid (Mac swapping).

## Verified findings (checked by the lead)
1. **Sub-clause parser bug - CONFIRMED.** `orca/kbvec/chunk.py` only recognises Roman sub-clauses `(i)`..`(x)`.
   In the index, the Telecom Cyber Security Rules 2024 have clause paths `s.7`, `s.7 (i)`..`s.7 (vi)`: there is no
   `Rule 7(1)(a)`, and Rules are labelled `s.` (section). Arabic `(1)` and letter `(a)` levels are lost, so exact
   citations cannot be matched. This is the main cause of exact-citation hit@1 <= 0.2.
2. **Abstention uses a meaningless score - CONFIRMED.** `evaluate.run_v2` thresholds `hits[0]["score"]`, which is
   an RRF fusion score without the reranker and an uncalibrated logit with it.
3. **Reranker on MPS competes with the embedder for unified memory - CONFIRMED** (25 GB wired, 5.7 GB swap
   during the run). The CPU-latency claims in the debate are unverified; measure before adopting.
4. **Formula-heavy documents are few.** The corpus has 18 ITU sources, mostly X/Y/E-series security and numbering
   texts; ITU-R P.838 (the rain formula) is used by the M2 code, not stored in the KB. Docling's formula benefit is
   therefore small for our questions. The manifest lists 0 skipped files; scanned pages with empty text have not
   been counted yet.

## Plan
### Phase 1 - no re-embedding (about 2 h, all on the Mac)
1. **Calibrated abstention** (both agents agree). Abstain when the top reranker probability `sigmoid(z1/T)` is
   below a threshold OR the margin `z1 - z2` and the list z-score are both small; plus a jurisdiction/binding
   gate: when the question asks for a binding Indian rule and the top hits are non-binding or non-IN, report
   `NO_BINDING_IN_JURISDICTION`. Tune T and the thresholds on the dev split only. Make `evaluate.run_v2` use
   `search_with_abstention` so the harness measures the real path. Safety check: the 9 verified gap-evidence
   records must never be abstained on.
2. **Citation router.** Parse citations in the query (`Rule/Section/Article/Direction/Regulation N(1)(a)`,
   `G.S.R. 720(E)`, `S.O. ...`, `47 CFR § ...`) plus an instrument alias table (e.g. "Telecom Cyber Security Rules"
   -> `in-tcsr-2024`), and boost matching chunks to rank 1 by clause path, falling back to clause-text matching
   for the `(1)(a)` level until Phase 2 fixes the paths.
3. **Reranker on CPU** (`ORCA_RERANK_DEVICE=cpu`, 4 threads) with a smaller pool and text cap; measure p50/p95 with
   nothing else loaded. Keep Qwen3-Reranker-0.6B; it gave the recall gain. bge-reranker-large via FastEmbed ONNX is
   the fallback if CPU latency is over 3 s.
4. Keep **RRF** (Flash A's argument wins: rank fusion is robust to BM25 outliers; RSF was not adopted).
5. **Eval fixes:** score negatives per the RAG_V2 spec (abstain, or no binding IN provision in the top 3), keep the
   reworded exact-citation questions, and report the 4B-reranker column from the Colab scores.

### Phase 2 - re-chunk and re-embed (about 3 h; GPU on GCP RTX PRO 6000 Spot, about $4)
6. **Fix the legal hierarchy parser:** levels `Rule/Section N` > `(1)` > `(a)` > `(i)`, the correct kind label
   (Rule vs Section vs Direction), and canonical paths like `Rule 7(1)(a)`.
7. **Breadcrumb header** stays (v2 already prefixes title | authority | jurisdiction | binding | clause path |
   page); update it with the fixed path.
8. **Docling sidecars** (MIT) only where they help: pages with tables (annexures, schedules) and pages with an empty
   or near-empty text layer (OCR). Count those pages first; skip Docling if the count is small.
9. Re-chunk, re-embed **only the chunks whose text changed** (reuse vectors by text hash), on the GCP GPU with the same
   Qwen3-Embedding-8B bf16, then `load-vectors`, snapshot, and evaluate.

### Not adopted
- ColPali/ColQwen page-image retrieval: no text quotes for the rule engine, multi-vector storage not supported by
  Chroma, and it competes for Mac memory (both agents agree in round 2).
- Full-corpus Docling re-parse: hours of GPU time and it invalidates every vector (Flash B's argument wins).
- Relative score fusion; switching away from the Qwen3 reranker as the default.

## Ship rule (unchanged from RAG_V2)
v3 becomes the default only if, on the test split, recall@5 and negative accuracy both beat v1 and p95 latency on
the Mac is under 3 s. Otherwise keep v1 and report v3 as measured.
