# Vector KB (`orca/kbvec`)

Mirrors the ITU reference stack (CrashingGuru/ITUAIReadiness): ChromaDB (cosine), nomic-embed-text, ~512-token
chunks with 50 overlap, PyMuPDF parsing. Added: BM25 hybrid, RRF fusion, metadata filters, cross-encoder rerank,
index snapshot and retrieval cache for exact replay.

## Run
```
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m orca.kbvec ingest            # kb/sources + verified records (incremental, skips unchanged sha256)
.venv/bin/python -m orca.kbvec ingest --corpus   # also corpus/raw + kb/staging (run on the Atlas L4 for the full set)
.venv/bin/python -m orca.kbvec query "6 hour incident report" --filter jurisdiction=IN
.venv/bin/python -m orca.kbvec evaluate [--tier corpus] [--no-rerank]   # alias: eval
.venv/bin/python -m orca.kbvec snapshot
.venv/bin/python -m orca.kbvec coverage "backup power hours" IN
```
Python API: `from orca.kbvec import search, get_chunk, coverage`.
`search(query, k=5, filters=None, rerank=True)`; filters: `jurisdiction`, `binding_status`, `tier`, `doc_type`,
`source_id` (value or list) and `in_force_on` (ISO date; drops binding rules not yet in force).
`get_chunk(id)` returns None for an unknown id; verified records have `chunk_id == record id`.

## Config (env)
`ORCA_EMBED_URL` (default `http://localhost:1234/v1`), `ORCA_EMBED_MODEL` (`text-embedding-nomic-embed-text-v1.5`),
`ORCA_EMBED_KEY`, `ORCA_EMBED_BATCH`, `ORCA_RERANK_MODEL` (`Xenova/ms-marco-MiniLM-L-6-v2`), `ORCA_MAIN_REPO`
(where gitignored `kb/sources` and `corpus/` live), `ORCA_KB_SOURCES`, `ORCA_KB_STAGING`, `ORCA_CORPUS_DIR`,
`ORCA_CHROMA_DIR` (default `chroma/`), `ORCA_KBVEC_CACHE` (`kb/vec_cache/`), `ORCA_KBVEC_SNAPSHOTS`.
Nomic task prefixes `search_document: ` / `search_query: ` are added by the client.

## Chunks
`chunk_id = <source_id>:p<page>:c<n>`; verified records use their record id. Metadata: source_id, title, authority,
jurisdiction, doc_type, binding_status, in_force_from, licence, page, clause, sha256 (source file), url, tier
(`corpus` | `verified`), plus text_sha and embed_model for incremental ingest. Chunks never cross a page. Headings
(Article, Section, Rule, Regulation, Direction, Annexure, numbered sections) start a new chunk; clause carries across
pages. Source jurisdiction comes from the id prefix; binding status and in-force date from the verified records that
cite the source (else `not_stated`); staged corpus items use their YAML metadata.

## Replay
`snapshot` writes `kb/vec_snapshots/<id>.json` (chunk ids, sha256, embed model, time). The snapshot id is a content
hash of the index. `search()` caches results in `kb/vec_cache/<hash>.json` keyed by query + k + filters + rerank +
snapshot id; a cache hit needs neither the embedder nor the reranker. Pass `cache=False` to bypass.

## Retrieval test
30 questions in `kb/vec_eval/questions.yml` (`.yml`, not `.yaml`, so `orca/kb.py`'s `kb/*/*.yaml` loader skips it).
Gold = a verified record id (hit also if a corpus chunk of the same source contains the record's quote) or a
(source, PDF page) pair. Metric: right clause in top 5 and MRR.

| Setting | recall@5 | MRR |
|---|---|---|
| both tiers, rerank on | 0.933 | 0.911 |
| both tiers, rerank off | 1.000 | 0.933 |
| corpus tier only (raw document chunks), rerank on | 0.767 | 0.513 |
| corpus tier only, rerank off | 0.800 | 0.589 |

The both-tier numbers are flattered: verified-record chunks contain the record's summary, which paraphrases the
question. The corpus-only row is the honest test of chunking plus embedding. The small MiniLM cross-encoder did
not help on this set (it was trained for web passages, not statutes); keep it switchable.

## Limits
Roman-numeral sub-clauses such as "(iii)" are not treated as headings. Scanned PDFs without a text layer are
skipped and logged (OCR is not built here). nomic is English-only. Corpus ingest is untested at scale.
