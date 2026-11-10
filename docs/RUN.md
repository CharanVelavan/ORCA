# ORCA-NTN local judge run guide

Every NTN link and network action is emulated. The recommended dashboard route is local Python.
The repository includes the built frontend, so Node.js is optional unless editing the website.

## Clean installation

Use Python 3.12 and Git. On macOS, LightGBM requires the OpenMP runtime (`brew install libomp`)
if it is not installed. On Debian/Ubuntu install `libgomp1` with the system package manager.

```bash
git clone https://github.com/CharanVelavan/ORCA.git
cd ORCA
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements-judge.lock
python -m orca.live --scenario S1 --llm mock --port 8060
```

Open http://127.0.0.1:8060/. First startup trains M1–M3 on synthetic emulator data when the
`models/orca_models.pkl` cache is absent; allow several minutes. Subsequent starts reuse it. The
training can update `orca/models/metrics.json` and reports a non-fatal core-detection warning on some
Macs. It does not require a Qwen endpoint or the full vector corpus.

The server binds to loopback. Choose another free `--port` for concurrent tests. The simulation starts
paused. In **Scenarios**, preview an exercise and press **Start exercise** to start its clock and open
**Console**. Follow [DEMO.md](DEMO.md) for Console → Policy → Recovery → Audit.

For the maintained `.venv-judge` launcher, optional model/embedding downloads and Windows setup, use
[JUDGE_REPRODUCIBILITY.md](JUDGE_REPRODUCIBILITY.md) and [JUDGE_WINDOWS.md](JUDGE_WINDOWS.md).
The [verification record](JUDGE_VERIFICATION.md) separates the commands actually run from platform
and benchmark checks that remain unverified.

## Scenarios and planned dimensions

| ID | Exercise | Planned dimensions out of the selected nine |
|---|---|---:|
| S0 | Normal baseline and covered duties | 5 |
| S1 | Ground-management intrusion and terminal loss | 9 |
| S2 | Storm, battery risk and scarce service capacity | 9 |
| S3 | Jamming and unsafe backup routes | 9 |
| N1 | Hospital-corridor power and battery failure | 9 |
| N2 | Payment-routing fault | 8 |
| N3 | Unprotected feeder-link audit | 8 |
| N4 | False management telemetry versus independent evidence | 9 |
| N5 | Telecom/grid incident and separate reporting clocks | 9 |
| CAP | Compound weather, intrusion, battery and capacity constraints | 9 |

These are project mappings, not official readiness scores or observed outcomes. Reasons and evidence
gates appear in the scenario briefing and [mapping](plan/SCENARIO_DIMENSION_COVERAGE.md).
India is the default rule context; EU/global sources remain comparisons. No Active KB toggle exists.

## Model modes and connection

- **Mock simulation:** fresh simulator, models and rules; deterministic agent stand-ins; no Qwen call.
- **Live endpoint / Qwen:** fresh simulator with actual OpenAI-compatible model calls.
- **Recorded replay:** previously recorded evidence; no new inference or exercise changes.

For Qwen, start the model server first. Open **Model connection**, configure the base URL and exact
served model ID, discover/test tools, then **Use for next run**. Select the Live mode and start a new
exercise. Settings apply to the next run and are held in memory. Existing runs retain their source.
For the project’s tuned deployment, see [the Qwen evaluation](research/atlas-runs/QWEN_FT_REPORT.md).
Other tool-compatible local servers are options, not an automatic fallback.

CLI users can export environment variables before starting; the Python entry point does not load
`.env` automatically. Docker Compose handles `.env` interpolation separately.

```bash
export LLM_BASE_URL="http://localhost:8000/v1"
# Replace this with the exact identifier returned by your server's /v1/models.
export LLM_MODEL="orca-ntn-qwen-ft"
export LLM_MODE=live
python -m orca.live --scenario S1 --llm local --port 8060
```

If authentication is required, set `LLM_API_KEY` privately or enter it in Model connection. Never
commit it. The dashboard hosts neither Qwen nor the embedding model. A fresh clone does not contain
the full vector index or response cache; [KBVEC.md](KBVEC.md) explains retrieval setup. Structured
records and deterministic rules remain available offline.

## Headless recording and checks

```bash
python tools/validate_kb.py
python scenarios/check_scen.py
python -m orca.live.headless --scenario S1 --llm mock --runs-dir runs
python -m pytest -q
```

The headless commander is a scripted stand-in; the recording labels that fact. Recordings remain in
`runs` when explicitly requested. Audit can load them after a dashboard restart. Verify the
original chain in Audit. Public exports withhold control entries and cannot verify the full chain.
Optional model/index tests may skip when their external artifacts are unavailable. Report the actual
pytest result rather than assuming a historical count.

## Evaluation and performance inspection

Run from the repository root with the prepared environment's interpreter. The commands below use
`python` after activating that environment: `.venv` for the manual installation above, or
`source .venv-judge/bin/activate` for the launcher environment. On Windows, use
`.\.venv-judge\Scripts\python.exe` in place of `python`; activation is optional.

First check the evaluation interfaces without a model request:

```bash
python -m pytest -q tests/test_eval_cases.py tests/test_kbvec_cli.py
python finetune/eval_cases.py --help
python -m orca.kbvec eval --help
```

### Fresh retrieval evaluation

Restore the pinned vector files and start a compatible embedding service using
[the reproducibility guide](JUDGE_REPRODUCIBILITY.md#6-restore-and-use-rag).
The following example uses the helper's local embedding service on port 1235; use the actual URL
and exact advertised embedding ID for an external service. The embedding service must remain running.
This is separate from the chat endpoint.

```bash
export ORCA_EMBED_URL="http://127.0.0.1:1235/v1"
export ORCA_EMBED_MODEL="text-embedding-qwen3-embedding-8b"
mkdir -p runs/evaluation
python -m orca.kbvec eval --v2 --tier corpus > runs/evaluation/rag-v2.json
```

PowerShell equivalent, using the launcher environment:

```powershell
$env:ORCA_EMBED_URL = "http://127.0.0.1:1235/v1"
$env:ORCA_EMBED_MODEL = "text-embedding-qwen3-embedding-8b"
New-Item -ItemType Directory -Force runs\evaluation | Out-Null
.\.venv-judge\Scripts\python.exe -m orca.kbvec eval --v2 --tier corpus | Set-Content -Encoding utf8 runs\evaluation\rag-v2.json
```

`--v2` runs the fixed dev/test questions through `search_with_abstention`, with retrieval caching
disabled. The JSON includes per-question rows, the threshold, `test_n`, `recall@5`, `mrr@10`,
`ndcg@10`, `negative_accuracy`, `negative_abstention_accuracy`, `amendment_hit_rate`,
`exact_citation_hit@1` and test-query p50/p95 latency in milliseconds. Recall/MRR/nDCG use positive
test questions; negative accuracy follows the documented negative-evidence criterion and is distinct
from refusal rate. `--no-rerank` changes the pipeline and should be labelled as a separate diagnostic.

Keep the vector revision, embedding GGUF/hash and quantization, served ID, reranker, Python lock,
code revision, hardware and cache state alongside the output. The first run can include reranker
download/loading overhead; report that state instead of treating latency as a hardware-independent
promise. The [fresh verification record](JUDGE_VERIFICATION.md) and [historical retrieval results](KBVEC.md)
describe separate configurations. A quantized query embedder can change rankings.

### Current model smoke evaluation

Start a tool-compatible chat server and replace the model ID below with the exact ID returned by
its `/v1/models`. This example uses the managed helper alias. Set `LLM_API_KEY` privately if needed.

```bash
python finetune/eval_cases.py --model orca-ntn-qwen-ft \
  --base-url http://127.0.0.1:8000/v1 \
  --cases finetune/data/cases.jsonl --limit 10
```

The scorer selects the first ten held-out rows in file order and writes
`finetune/eval/orca-ntn-qwen-ft-smoke-first10.json`. It makes real model requests but executes no
tools. Omit `--limit` to score all available held-out rows, with the corresponding additional time
and model cost. Output records case IDs, the input hash, per-case tool-schema hashes and their source,
endpoint origin, elapsed seconds, metric denominators and per-case scores. Model IDs are sanitized
for output filenames; copy results before repeating the same command to retain earlier runs.

`valid_json` measures JSON-object tool arguments among predicted calls and is null when no calls
were predicted. `unsafe_exec` is a legacy alias for cases that **attempted** forbidden tool calls;
it does not measure tool execution. `scenario_verdicts_ok` is unmeasured by this scorer. Token speed
and hardware are not inferred from its elapsed time.

This ordered smoke run does not reproduce the historical stratified 300-case / 93% tool-selection
result. The public case pack omits tool schemas; the current CLI supplies current role schemas.
The exact frozen historical requests, supplied schemas and subset provenance remain missing. See
the [benchmark boundary and publication follow-up](JUDGE_REPRODUCIBILITY.md#model-benchmark-reproducibility-boundary).

### End-to-end exercise timing

Use a dedicated output directory to retain a fresh headless recording. On macOS/Linux:

```bash
time python -m orca.live.headless --scenario S1 --llm mock --runs-dir runs/performance-mock
```

For live calls, configure `LLM_BASE_URL`, `LLM_MODEL` and `LLM_MODE=live` as above, then:

```bash
time python -m orca.live.headless --scenario S1 --llm local --runs-dir runs/performance-live
```

Audit lists recordings directly under `runs/`. To inspect these nested performance outputs in the
website, copy the chosen `.jsonl` and matching `.stream.jsonl` pair into `runs/`, or use
`--runs-dir runs` from the start. Keep the pair's filenames unchanged.

In PowerShell, wrap the corresponding interpreter command in `Measure-Command { ... }` to measure
wall time. The headless commander uses scripted approval/notification delays. Inspect its summary
and recording for actual guarded execution, refusals, notification status and recovery; elapsed time
alone does not establish a successful outcome. Simulation minutes and wall seconds are different
clocks. Preserve cold/warm cache state, endpoint configuration and raw evidence with every result.

## Frontend source build

With Node.js and npm:

```bash
cd dashboard/live/web
npm ci
npm run build
cd ../../..
```

Reload the dashboard after rebuilding. The Python server serves `dashboard/live/dist`.

## Docker batch runner

The current Docker Compose command runs `run_demo.py` and a Chroma service. It is a batch runner,
not the local browser dashboard command above. Docker execution was not part of the clean Python
verification. Do not expect `docker compose up` to expose a dashboard port.

```bash
docker compose up --build
docker compose run --rm orca python run_demo.py --scenario s1
docker compose run --rm orca python run_demo.py --scenario s1 --no-rules
docker compose down
```

## Review boundaries

No commander PIN is required. Manual approvals, scoped autonomy, one-time plan tokens, expiry,
ownership, clone tests, path checks and the kill switch remain enforced. Policy findings are bounded
to checked sources. Treat missing evidence, refusal, rollback and reporting status as separate facts.
See [guide.md](../guide.md) for controls and [API examples](plan/LIVE_API_EXAMPLES.md) for automation.
