# RAG v2 - build spec (8 Nov 2026)

Goal: the best retrieval we can ship by 10 Nov for legal/regulatory evidence, measured honestly, and
replayable offline. Keep the public interface (`orca.kbvec.search`, `get_chunk`, `coverage`, the
replay cache, chunk ids cited by agents) so agents, protocol and the dashboard keep working.

## Stack
| Layer | v1 | v2 |
|---|---|---|
| Parsing | PyMuPDF pages | PyMuPDF + **legal-structure parser** (Act/Chapter/Part > Section/Rule/Article/Regulation/Direction > (1) > (a) > (i); Annexure/Schedule; numbered headings "3.2.1") |
| Chunks | ~512 tok, page-bound, heading starts | **clause chunks** (one clause or sub-clause, max ~400 tok, split long ones by sentence with 1-sentence overlap) + **parent sections** (the full Section/Rule/Article, max ~2,000 tok) stored separately |
| Chunk header | none | deterministic prefix in the embedded and BM25 text: `<title> | <authority> | <jurisdiction> | <binding_status>, in force <date> | <clause path e.g. Rule 7 > (1) > (a)> | p.<page>` |
| Dense | nomic-embed-text v1.5 (LM Studio) | **Qwen3-Embedding-8B** (index built on Colab A100 in bf16; queries via LM Studio GGUF Q8_0 of the same model, fallback Qwen3-Embedding-4B). Query instruction: `Instruct: Given a question about telecom, cyber security or space law, retrieve the legal provision that answers it\nQuery: <q>`; documents have no instruction |
| Sparse | BM25 | BM25 with a **legal tokenizer** (keeps `7(1)(a)`, `G.S.R. 720(E)`, `Article 23(4)`, `S.O. 1234(E)`, `47 CFR § 4.9` as tokens) + small synonym map (notify/report/inform; operator/licensee/authorised entity; incident/breach/cyber incident; satellite/space/NTN) |
| Fusion | RRF | RRF (dense, BM25) over clause chunks, k=60, top 50 candidates |
| Rerank | MiniLM web cross-encoder (hurt recall) | **Qwen3-Reranker** (0.6B default on the Mac via transformers on MPS/CPU; 4B when `ORCA_RERANK_MODEL` says so, e.g. on Atlas/Colab), top 50 -> top k |
| Return | chunk | clause chunk + its **parent section text** (small-to-big) + **amendment links** (records/sources with `amends`/`amended_by` pointing to it) |
| Abstain | none | calibrated score threshold -> `{"results": [], "abstained": true, "best_score": x}`; agents then return INSUFFICIENT_EVIDENCE. Threshold chosen on the dev half of the eval set |
| Store | Chroma | Chroma (unchanged), new collection `orca_v2`; v1 collection kept until v2 wins |

Chunk ids stay `<source_id>:p<page>:c<n>`; parent ids `<source_id>:s:<clause-path-slug>`; verified records
keep `chunk_id == record id`. Metadata adds `clause_path`, `parent_id`, `level`, `lang`.

## Build pipeline (Colab does only the GPU part)
1. Mac: `python -m orca.kbvec chunk --corpus` -> `kb/vec_build/chunks.jsonl` (id, text_with_header,
   metadata) + `kb/vec_build/manifest.json` (counts, sha256 of each source, parser version). CPU only.
2. User uploads `chunks.jsonl` to Google Drive `MyDrive/orca-ft/rag/` (one drag and drop).
3. Colab: `finetune/colab/embed_corpus.py` (pasted into a cell by the Colab agent): loads
   Qwen3-Embedding-8B with sentence-transformers (bf16, flash/sdpa attention, batch by length), embeds every
   chunk (no instruction), L2-normalises, writes `embeddings.f16.npy` + `ids.json` + `model.json`
   (model id, revision, dim, dtype, time) to Drive. Also embeds the eval questions (with instruction) for
   a drift check.
4. User downloads the three files into `kb/vec_build/`.
5. Mac: `python -m orca.kbvec load-vectors` builds collection `orca_v2` from the precomputed vectors (no
   re-embedding) + the BM25 index; `python -m orca.kbvec snapshot`.
6. Drift check: embed 50 chunks and 20 questions locally through LM Studio's Q8_0 GGUF; mean cosine to the
   Colab vectors must be >= 0.99, else fall back to embedding queries with the 4B model on both sides (or
   flag it in the report).

## Evaluation (`kb/vec_eval/questions_v2.yml`, ~100 questions)
- 60 positive: gold = verified record id, or (source, page) of a staged quote that passed the exact-text
  check. Spread over IN / EU / US / INTL / AE and all gap topics. Write questions in plain words a
  regulator or operator would use, not copied from the quote.
- 20 **negative** (absence): questions whose answer is "not in our corpus", built from the gap register's
  search records (e.g. "binding duty for an Indian satellite operator to warn hospitals and banks").
  Correct = abstain, or return only non-binding / other-jurisdiction material (scored by metadata).
- 10 multi-hop / amendment (rule + amending instrument, or rule + in-force date).
- 10 exact-citation lookups ("What does Rule 7(1)(a) of the Telecom Cyber Security Rules say?").
- Split 50/50 dev/test (fixed seed); tune the abstention threshold and fusion weights on dev only.
- Report for v1 and v2 on test: recall@5, MRR@10, nDCG@10 (positives); abstention accuracy (negatives);
  amendment hit rate; exact-citation hit@1; p50/p95 query latency on the Mac. Corpus-only tier is the
  headline. Write the table into docs/KBVEC.md.
- **Ship rule:** v2 becomes default only if corpus-only recall@5 and negative accuracy both beat v1 and p95
  latency on the Mac is under 3 s with the 0.6B reranker. Otherwise keep v1 and report v2 as measured.

## Safety and replay
- Cache key adds the collection name and embedding model id; old cache entries stay valid for v1.
- Abstention must never turn a found binding record into "no evidence": test with the 9 verified gap
  evidence records.
- Agents and protocol: chunk-id citation check unchanged; parent ids are citable too (add to
  `get_chunk`).
- No corpus text is committed to git (corpus/ stays ignored); `kb/vec_build/` is gitignored except
  `manifest.json`.
