# Run ORCA-NTN on a laptop

This guide runs the whole emulated sandbox on one laptop. Every network link in the sandbox is **emulated**.
No real satellite, mobile network or power grid is touched.

Each command below was run on macOS (Apple Silicon) on 8 Nov 2026. Sections marked **coming (Mission 8)** are not built yet.

## 1. What you need

| Part | Needed for | Notes |
|---|---|---|
| Python 3.11 or newer | tests, scenario replay, mock agent run | Checked with Python 3.14.7 (no vector KB packages) |
| Python 3.12 (in `.venv`) | vector KB (`orca.kbvec`) | Checked with 3.12.14, installed by `uv` |
| `uv` (optional) | fetches Python 3.12 and installs the pinned packages | `brew install uv` |
| LM Studio with `text-embedding-nomic-embed-text-v1.5` loaded | vector KB ingest and query | Server on `http://localhost:1234/v1` |
| poppler (`brew install poppler`) | only the corpus tools in `tools/search_sources.py` and `scripts/quote_check.py` | Not needed to run the demo |
| Docker | not used here | `Dockerfile` and `docker-compose.yml` are not tested yet |
| A cloud or local LLM endpoint | live agent runs | **coming (Mission 8)**. The LLM client exists but no runner uses it yet |

You do not need an LLM for sections 2 to 5.

## 2. Install

Clone the repo and enter it:

```
cd orca-ntn
```

**Quick path (tests, scenarios, mock run).** Python 3.11 or newer (`pyproject.toml`) with `pyyaml` and `pytest` is enough.
Tested on Python 3.14.7. That Python had no `chromadb`, so the vector KB was off and the tests still ran.

**Full path (adds the vector KB).** Use Python 3.12 in a local `.venv`:

```
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

`uv` used CPython 3.12.14 and installed every pinned package. Without `uv`, install Python 3.12 yourself and run
`python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt` (not tested here).

## 3. Run the tests

From the repo root:

```
python3 -m pytest -q
```

Result on Python 3.14.7 (no vector KB): **164 passed, 4 skipped, 1 xfailed**.

Run the safety tests on their own, with the skip and xfail reasons shown:

```
python3 -m pytest -q tests/test_safety.py -rxs
```

Result: **65 passed, 3 skipped, 1 xfailed**. The 3 skips are Mission 6 features (autonomy modes, kill switch,
blast-radius cap). The xfail is a known bug in single-use approval tokens (`orca/remediation.py:108-109`).

With the full `.venv` (vector KB installed):

```
.venv/bin/python -m pytest -q
```

Result: **167 passed, 3 skipped, 1 xfailed, 1 failed**. The failure is an existing test,
`tests/test_agents.py::test_adviser_answers_from_kb_with_citations`. With the vector KB on, the policy adviser can cite
a corpus chunk id (for example `in-certin-faq-2022:p15:c0`), and that test only accepts record or gap ids. The
citation is allowed by design. The test is out of date. It was not changed in this step.

## 4. Replay all scenarios

```
python3 scenarios/check_scen.py
```

Each scenario replays its events, runs the rule engine after every event, and checks the expected verdicts.
Last run: 10 scenarios (CAP, N1 to N5, S0 to S3), **0 problems** in every line. The script exits with code 0.

## 5. Check the knowledge base

```
python3 tools/validate_kb.py
```

Expected output: `records: 50 (...)`, `verified quotes: 49`, `gaps: 9`, `sources: 24`, then `OK`.

Only some source files are on disk. Check which ones are present:

```
python3 tools/fetch_sources.py --check
```

Last run: two files were MISSING (`intl-3gpp-tr-33700-29`, `intl-itut-x1144-2024`). The rest were OK. To download
the missing files (uses the network and writes hashes into `kb/sources.yaml`), run `python3 tools/fetch_sources.py`.
That command was **not run** here.

## 6. Mock-LLM agent run

This runs the role agents on scenario S1 with a deterministic mock model. No network and no LLM server.

```
mkdir -p runs && rm -f runs/mock-s1.jsonl && python3 -c "
import yaml, pathlib
from orca.agents import Coordinator, PolicyMockLLM
from orca.world import World
s = yaml.safe_load(open('scenarios/s1.yaml'))
w = World.new({'jurisdiction': 'IN', 'now': s['start']}, pathlib.Path('runs/mock-s1.jsonl'))
res = Coordinator(w, PolicyMockLLM()).run(s)
print(len(res), 'agent turns;', len(w.audit.entries()), 'audit entries; chain intact:', w.audit.verify() is None)
"
```

Last run: **11 agent turns, 56 audit entries, chain intact: True**. The audit file is `runs/mock-s1.jsonl`
(the `runs/` folder is git-ignored).

Run `python3 run_demo.py --kb india` for a quick check. It validates the KB and prints the record count. The full
pipeline is **coming (Mission 8)**.

## 7. Build and query the vector KB

Needs the `.venv` from section 2 and LM Studio on port 1234 with the nomic embedding model loaded. Check the server first:

```
curl -s http://localhost:1234/v1/models
```

Build the index from `kb/sources` and the verified records (about 2 minutes on a laptop):

```
.venv/bin/python -m orca.kbvec ingest
```

Last run: 24 sources, **3,055 chunks embedded**, 50 verified records, no errors. The index is in `chroma/` (git-ignored).

Query it:

```
.venv/bin/python -m orca.kbvec query "6 hour incident report" --filter jurisdiction=IN
```

Last run: the top hit was `IN-CERTIN-DIR-2022-ii` (verified, binding, CERT-In Direction (ii)), then `IN-TCSR-2024-R7-1`.

Find the nearest clauses for a gap check:

```
.venv/bin/python -m orca.kbvec coverage "backup power hours" IN
```

Last run: searched 18 documents, nearest clause `IN-CEA-2020-8-11`.

Save a snapshot of the index (writes `kb/vec_snapshots/`):

```
.venv/bin/python -m orca.kbvec snapshot
```

Last run: 3,055 chunks, embed model `text-embedding-nomic-embed-text-v1.5`.

Score retrieval (30 questions, no reranker):

```
.venv/bin/python -m orca.kbvec evaluate --no-rerank
```

Last run: **recall@5 = 1.000, MRR = 0.933**. This matches the table in `docs/KBVEC.md`.

Note: `query` and `coverage` write the cache in `kb/vec_cache/`. That is intended, and the tests ignore it.

## 8. Coming (Mission 8)

These parts are not built yet. Do not expect them to run:

- autonomy modes MANUAL, ASSISTED and AUTO, with a PIN and expiry per site or playbook;
- kill switch;
- blast-radius cap (sites per action, actions per 10 minutes);
- live LLM agent runs through a runner (LM Studio or a cloud endpoint);
- the full demo pipeline in `run_demo.py` (today it only validates the KB);
- Docker run (`docker-compose.yml`);
- the commander console and dashboard.

## 9. Known issues

- One existing test fails with the vector KB installed (section 3).
- The single-use approval token can be re-minted at the same clock instant (xfail in `tests/test_safety.py`).
  Fix: `orca/remediation.py`, token derivation and `approve()`. This is not fixed in this step.
- Two source files are missing from `kb/sources` (section 5).
- `query`, `coverage` and `snapshot` write into `kb/` (`kb/vec_cache/`, `kb/vec_snapshots/`). Scenario runs do not.
  The safety test ignores `vec_cache` and fails on any other change under `kb/`.
- The approval PIN is checked only for being non-empty (`orca/remediation.py`, `approve()`).
