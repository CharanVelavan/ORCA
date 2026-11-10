# Judge reproducibility guide

This guide separates the minimal local exercise from optional live inference and vector retrieval.
Everything in the network is **emulated**. Follow [DEMO.md](DEMO.md) for the judge presentation,
[RUN.md](RUN.md) for maintained test commands, and [the website guide](../guide.md) for controls.

## 1. Choose a reproduction level

| Goal | Required | Not required |
|---|---|---|
| Run the complete mock-agent sandbox and dashboard | Git, Python 3.12, installed requirements, bundled frontend | GPU, Qwen weights, vector index, model API key, Node.js |
| Inspect a recorded run | Installed dashboard and an existing recording | New model inference or a vector service |
| Run fresh agents against Qwen or another compatible model | The mock setup plus a reachable tool-capable chat endpoint | Hosting weights on the dashboard machine if using a remote endpoint |
| Restore the published vector index | Four verified RAG files and local Chroma | GPU or embedding service during restoration |
| Execute fresh hybrid vector queries | Restored index, matching embedding endpoint (managed or external), reranker cache/network | Re-embedding the entire corpus |
| Edit/rebuild the website | Node.js/npm and frontend lockfile dependencies | Frontend tools for the bundled judge website |

The structured `kb/` records and deterministic YAML rules are separate from the broad vector corpus.
Mock mode can exercise policy verdicts and guards without restoring the full corpus. An absent vector
service does not establish the quality of broad RAG. Audit playback replays recorded evidence and
makes no fresh retrieval call. `LLM_MODE=replay`, by contrast, requires matching model-call cache files;
those ignored caches are not included in a fresh clone.

## 2. Prerequisites and hardware planning

Use **64-bit Python 3.12**. The judge dependency lock targets that minor version;
use a fresh virtual environment rather than an unrelated Python installation. Git is needed to clone.
The launchers do not install Python or system packages and do not request administrator access.

| Component | Practical planning guidance |
|---|---|
| Mock sandbox | A modern CPU and 8 GB RAM are a reasonable starting budget; 16 GB gives more room for model training and browser use. These are planning estimates, not tested minimums. |
| Python environment | Reserve several GB for native wheels and their installed environment. First installation needs internet. |
| Tuned chat model | The weight file alone is 19.18 GB decimal / about 17.86 GiB. Runtime memory also includes context, compute buffers and the OS. A 32 GB host/unified-memory machine is a planning starting point, not a guarantee; CPU inference may be slow. |
| GPU example | The published evaluation used one NVIDIA L4 with 24 GB VRAM, 16,384-token context and one parallel slot. The report records approximately 18.2 GB GPU use for that configuration. This is a measured example, not a universal minimum. |
| Vector restoration/search | The four portable files total about 0.933 GB. Chroma storage, temporary import state, reranker caches and retrieval structures require additional space and RAM. Reserve at least 10 GB extra disk as a planning allowance; check actual free space before importing. |
| Full local chat + embedding + RAG | Raw published files total about 24.79 GB. Plan for at least roughly 35 GB free disk, with more space for caches/index/builds. 32 GB combined host RAM can be tight; 48 GB is a more comfortable planning budget for CPU chat, embedding, Chroma and browser together. These are estimates, not tested minimums or guarantees. |
| Separate embedding weights | The optional official Q4_K_M GGUF adds 4.68 GB before runtime/context overhead. Running the embedder on another machine changes the local memory budget. |
| Browser | A current desktop browser; WebGL is optional. Learn has a lighter static view and topology description. Console also provides observed telemetry and evidence panels. |

The model hardware figures above are from [the recorded Qwen evaluation](research/atlas-runs/QWEN_FT_REPORT.md).
No setup duration or inference speed is promised for a judge's machine.

Platform runtimes:

- **macOS:** install `libomp` for LightGBM (`brew install libomp`). For llama.cpp source builds, install
  Apple's command-line developer tools and CMake; Metal support depends on the chosen build.
- **Debian/Ubuntu:** install `libgomp1`; a distro Python install may also need `python3.12-venv`.
  A source-built model server additionally needs CMake and a C/C++ toolchain; CUDA builds need a
  compatible NVIDIA driver and CUDA toolkit.
- **Windows:** follow [JUDGE_WINDOWS.md](JUDGE_WINDOWS.md). Use a Python 3.12 installer with its launcher.
  The mock launcher was exercised on macOS and Windows 11 ARM with x64 Python under Parallels.
  See the Windows guide for the exact scope. Linux native execution was excluded from this follow-up.

## 3. Recommended launchers

From a checkout of `https://github.com/CharanVelavan/ORCA`:

```bash
./quickstart.sh
```

Or in Windows PowerShell/Command Prompt:

```powershell
.\quickstart.bat
```

The default creates or reuses `.venv-judge`, installs `requirements-judge.lock` with `--require-hashes`, verifies key imports and
starts `python -m orca.live --scenario S1 --llm mock --port 8060`. It serves the committed
`dashboard/live/dist`; it does not build the frontend, download model weights or restore RAG.
Open http://127.0.0.1:8060/. First startup trains M1–M3 if `models/orca_models.pkl` is absent.
The server begins paused; use **Scenarios → Start exercise** to start its clock.

```bash
./quickstart.sh --dry-run
./quickstart.sh --check
./quickstart.sh --scenario N5 --port 8061
```

`--dry-run` validates and describes actions without installing, downloading or starting. `--check`
checks a previously prepared environment; it does not create one. `--venv PATH` selects another
virtual environment. Stop the server with Ctrl+C. Use a different port for a separate verification
process rather than restarting someone else's active session.

### Optional single-command live preparation

After installing a compatible `llama-server` executable and meeting the model memory/disk
requirements, this command downloads and verifies the published chat, embedding and RAG files,
restores Chroma, creates its manifest, starts local chat/embedding servers, waits for their advertised
models, then launches the live dashboard:

```bash
./quickstart.sh --download-model --serve-model --download-rag --prepare-rag \
  --download-embedding --serve-embedding
```

Windows PowerShell/Command Prompt equivalent:

```powershell
.\quickstart.bat --download-model --serve-model --download-rag --prepare-rag --download-embedding --serve-embedding
```

The model binary is **not** automatically
downloaded or installed. The helper finds `llama-server` on PATH or accepts `--llama-server PATH`.
CPU inference is the default (`--gpu-layers 0`); add `--gpu-layers 99` only for an appropriate build and
available accelerator memory. The helper uses 16,384 context, the alias `orca-ntn-qwen-ft` and the
local chat endpoint `http://127.0.0.1:8000/v1`. Port 8000 must be free; the dashboard uses its separate
`--port` (8060 by default). The managed embedding service uses CPU, alias
`text-embedding-qwen3-embedding-8b` and `http://127.0.0.1:1235/v1`. It refuses to take over occupied
service ports and stops its own server subprocesses when the helper exits. The helper does not stop
an externally supplied endpoint.

`--serve-model` implies live mode; omit external `--endpoint` and `--model-id` arguments for this
path. It cannot be combined with `--download-only`. It verifies discovery before launching, but
still use the UI tool-compatibility test. This path has not been executed on native Windows.

**Fresh vector search uses its own embedding service.** The complete command above explicitly
requests `--download-embedding --serve-embedding`; this is separate from serving the chat model.
Alternatively omit those flags and provide `--embedding-endpoint URL --embedding-model ID` for a
running compatible service (§6). Use `ORCA_EMBED_KEY` privately if it requires authentication.
Omitting all embedding options leaves the separate service as a manual prerequisite. The helper
does not install llama.cpp or infer that the chat model can produce compatible vectors.

For preparation without serving:

```bash
./quickstart.sh --download-rag --prepare-rag --download-only
```

`--check --prepare-rag` verifies downloaded source-file checksums only; it does not establish that
Chroma has been populated or that embedding/search works. Use the actual load and query steps in §6.

### Manual alternative

macOS/Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements-judge.lock
python -m orca.live --scenario S1 --llm mock --port 8060
```

Windows PowerShell, without changing PowerShell's script execution policy:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-judge.lock
.\.venv\Scripts\python.exe -m orca.live --scenario S1 --llm mock --port 8060
```

Use the interpreter from the environment you actually prepared. `.venv` in the manual path and
`.venv-judge` in the launcher path are different directories. The CLI does not load `.env` automatically.
Cold training may update `orca/models/metrics.json`; the trained `.pkl` cache is ignored by Git.

### Dependency lock and maintenance

`requirements-judge.lock` freezes transitive Python versions and permitted artifact hashes with
Python 3.12 / macOS / Linux / Windows markers. Pip selects the applicable platform entries and
verifies the downloaded files. Native OS libraries, the model-server executable and GPU drivers
remain separate prerequisites; a universal Python lock is not proof of native execution on every OS.
The helper prefers the lock and detects changes to both dependency input and lock in its setup signature.

`requirements.txt` remains the direct-dependency source. Maintainers can regenerate the universal
lock with `uv pip compile --universal --python-version 3.12 --generate-hashes requirements.txt -o requirements-judge.lock`,
then review/test the result. **uv is not a judge prerequisite.** Do not regenerate or casually upgrade
packages when reproducing the supplied environment. Use its pip hash-check command above.

## 4. Minimal judge exercise

1. Open Learn, then Scenarios. Select S1 and inspect the briefing and planned schedule.
2. Keep Mock simulation for the offline-agent exercise. Selecting a card changes no active run.
3. Press Start exercise. The page enters Console only after backend confirmation.
4. Inspect released telemetry, actual model output, agents and approval requests. The director action
   rail injects emulated conditions; operator evidence does not disclose hidden director truth.
5. Inspect cited findings and independent reporting triggers in Policy & Gaps. Review actual guard,
   rollout, path, re-attack and service outcomes in Recovery.
6. Open Audit & Replay and select the newly created recording. Verify its original chain, inspect raw
   public events and export the evidence package. Replay remains read-only across routes.
7. Use Judge walkthrough for six manual evidence-review checkpoints. Its summary is not a score of
   incident resolution. The longer Guided tour explains the interface without executing actions.

A fresh clone need not contain historical `runs/` files. Generate a local recording through the UI or
use the headless commands in [DEMO.md](DEMO.md). Headless approvals are a labelled scripted commander,
not a person interacting with the UI. One recording can contain multiple injected incidents.

## 5. Verified public artifacts

Metadata below was checked against the public Hugging Face API on **10 November 2026**. Revisions
are pinned so a later `main` update cannot silently change the download. Public access was available
without authentication at verification time. Recheck source terms before redistribution.

### Tuned chat model

Repository: [CharanVelavan/orca-ntn-qwen3.6-35b-a3b-ft-gguf](https://huggingface.co/CharanVelavan/orca-ntn-qwen3.6-35b-a3b-ft-gguf).
Revision: `a0bdc74681870544849cafaf2d5a35a6a5cbd488`. Card licence: **Apache-2.0**.

| File | Bytes | SHA-256 |
|---|---:|---|
| `Qwen3.6-35B-A3B-orca-ft.IQ4_XS.gguf` | 19,179,521,888 | `011d7797836571495e8faf545101bee1e71d75a39292e06f946e8a3646b54e16` |

Optional download with the helper:

```bash
./quickstart.sh --download-model --download-only
```

This download-only command verifies the GGUF under `models/llm/qwen-ft`. It does **not** start a model server;
the explicit `--serve-model` path in §3 can manage one after prerequisites are installed.
Omitting `--download-only` starts the dashboard after the requested download, using the chosen mode.
An existing file with a different checksum is refused rather than overwritten.

Activate the virtual environment you prepared before the following manual commands; launcher users
can run `source .venv-judge/bin/activate` on macOS/Linux.

Manual alternative, using the [official HF CLI](https://huggingface.co/docs/huggingface_hub/guides/cli):

```bash
hf --help
hf download CharanVelavan/orca-ntn-qwen3.6-35b-a3b-ft-gguf \
  Qwen3.6-35B-A3B-orca-ft.IQ4_XS.gguf Qwen3.6-35B-A3B-orca-ft.IQ4_XS.gguf.sha256 \
  --revision a0bdc74681870544849cafaf2d5a35a6a5cbd488 --local-dir models/llm/qwen-ft
```

On macOS, verify the published sidecar **from the directory containing the GGUF**; it uses a relative filename:

```bash
cd models/llm/qwen-ft
shasum -a 256 -c Qwen3.6-35B-A3B-orca-ft.IQ4_XS.gguf.sha256
```

On Linux use `sha256sum -c`; on Windows use `Get-FileHash -Algorithm SHA256 PATH` and compare with
the table. Return to the repository root for subsequent commands.

### Optional matching embedding model

Official repository: [Qwen/Qwen3-Embedding-8B-GGUF](https://huggingface.co/Qwen/Qwen3-Embedding-8B-GGUF).
Revision: `69d0e58a13e463cd99a9b83e3f5fee7c10265fab`. Card licence: **Apache-2.0**.
The public API's file size and LFS SHA-256 were checked for this exact revision.

| File | Bytes | SHA-256 |
|---|---:|---|
| `Qwen3-Embedding-8B-Q4_K_M.gguf` | 4,676,804,928 | `3fcd3febec8b3fd64435204db75bf0dd73b91e8d0661e0331acfe7e7c3120b85` |

```bash
./quickstart.sh --download-embedding --download-only
```

The helper stores it under `models/llm/qwen-embedding`. Add `--serve-embedding` to start the CPU
service with an installed compatible llama.cpp binary, or combine the flags with the full local path
in §3. A download-only operation does not start either server.

The published corpus vectors were built with Qwen3-Embedding-8B and stored as normalised float16.
This Q4_K_M GGUF supplies **quantized query embeddings**. They can change rankings and scores relative
to the original build/evaluation configuration. A healthy 4,096-dimensional endpoint is a functional
compatibility check, not proof of bit-identical retrieval or the published recall/latency results.

### Portable RAG v2 files

Repository: [CharanVelavan/orca-ntn-kb-v2](https://huggingface.co/datasets/CharanVelavan/orca-ntn-kb-v2).
Revision: `769dcc85b6be9e308b038831072a5b848e740a94`. Card licence: **other / mixed-source-documents**.
The code is MIT; the source documents retain their issuing bodies' terms. This dataset is not blanket
MIT-licensed. Its [card](https://huggingface.co/datasets/CharanVelavan/orca-ntn-kb-v2/blob/769dcc85b6be9e308b038831072a5b848e740a94/README.md)
explains known extraction/rebuild differences and source rights.

| Required file | Bytes | SHA-256 |
|---|---:|---|
| `chunks.jsonl` | 256,169,422 | `efe2d3f7b7b03d32e87da9cc38c75771287ade5184de2e6bdec20b800704c9b4` |
| `embeddings.f16.npy` | 673,308,800 | `c3216a1917f3516deca194eac27eb98cb29500c7b87732974c347191fe0be4cf` |
| `ids.json` | 3,464,575 | `b9ee8382010e469ebbc09e47b7579772dbb449433f3a8374014f82c5c4a5b55d` |
| `model.json` | 202 | `470b4f3b2d50ca9a05e157f9880c7f6ea1238e2848c657505b4dc4980de42183` |

The four files total **932,942,999 bytes**. They contain 82,191 ordered chunks/vectors, 4,096 dimensions,
float16 storage and normalised Qwen3-Embedding-8B vectors. They are **loose files, not a ZIP archive**.
The repository additionally publishes `SHA256SUMS`, the source build manifest and its README.

```bash
./quickstart.sh --download-rag --download-only
```

Or manually:

```bash
hf download CharanVelavan/orca-ntn-kb-v2 --repo-type dataset \
  --revision 769dcc85b6be9e308b038831072a5b848e740a94 --local-dir kb/vec_build
cd kb/vec_build
shasum -a 256 -c SHA256SUMS
```

All four entries must report OK. Use `sha256sum` on Linux or PowerShell `Get-FileHash` on Windows.
Return to the repository root before loading the index.

## 6. Restore and use RAG

With the launcher environment, run from the repository root:

```bash
.venv-judge/bin/python -m orca.kbvec load-vectors
.venv-judge/bin/python -m orca.kbvec snapshot
```

Windows equivalents use `.\.venv-judge\Scripts\python.exe`. With the manual environment, use its
`python` instead. The loader expects `kb/vec_build/{chunks.jsonl,embeddings.f16.npy,ids.json}` and
checks row counts and exact ID order before upserting the **`orca_v2`** collection. It restores supplied
vectors without a GPU or embedding request. Expected loaded metadata is 82,191 rows and 4,096 dimensions.
`ORCA_CHROMA_DIR` changes the local persistent-store directory; default is `chroma/`.

**`snapshot` writes a content-hash manifest in `kb/vec_snapshots`; it does not restore vectors.**
The downloader alone does not build Chroma; explicitly include `--prepare-rag` to run both
`load-vectors` and `snapshot` as part of helper preparation.

A fresh query needs a separate OpenAI-compatible **embedding** server providing the matching
Qwen3-Embedding-8B family at 4,096 dimensions. The helper can manage the optional CPU service via
`--serve-embedding`; alternatively use an existing local or remote service. The public RAG payload includes stored document
vectors; the embedding GGUF is a separate optional download. Budget additional disk and runtime
memory for that model if you host it yourself. Do not point this URL at the tuned chat GGUF.
Dimension compatibility alone does not make a different embedding model compatible.

macOS/Linux example, after starting the embedding server separately:

```bash
export ORCA_KBVEC_COLLECTION=orca_v2
export ORCA_EMBED_URL=http://127.0.0.1:1235/v1
export ORCA_EMBED_MODEL=text-embedding-qwen3-embedding-8b
.venv-judge/bin/python -m orca.kbvec query "6 hour incident report" --filter jurisdiction=IN
```

PowerShell uses `$env:ORCA_EMBED_URL = 'http://127.0.0.1:1235/v1'` and the Windows environment's Python
path. Port 1235 is the managed-service example; the code default without overrides remains
`http://localhost:1234/v1`. Set `ORCA_EMBED_MODEL` to the exact ID your compatible embedding server exposes. Query prefixes
are applied by ORCA. `ORCA_EMBED_KEY` is available for an authenticated embedding service.

The default reranker is `BAAI/bge-reranker-base`, supported by the pinned FastEmbed package on CPU.
The first reranked query may download its ONNX artifacts. A later run needs those cache files to work
without internet. `--no-rerank` is a diagnostic setting; its rankings are not the default evaluation.
The optional Qwen reranker path uses additional Torch/Sentence Transformers dependencies, and is
not needed for this default restore path.

The `query` command prints search results; agent retrieval uses `search_with_abstention`. To inspect
that refusal boundary directly after restoring the index and starting the embedder:

```bash
.venv-judge/bin/python -c "from orca.kbvec import search_with_abstention; print(search_with_abstention('6 hour incident report', filters={'jurisdiction':'IN'}))"
```

The default combines Chroma cosine search, BM25, reciprocal-rank fusion, bge reranking, exact-citation
promotion and abstention checks. Legal status, jurisdiction, effective date, page and clause remain
metadata. See [KBVEC.md](KBVEC.md) for measured recall, refusal and latency limits and current evaluation
commands. Rebuilding chunks from source with a later parser does not guarantee identical bytes to
this published snapshot; use the verified payload for exact stored-document/vector reproduction.

## 7. Run the tuned chat model locally

Install a compatible [llama.cpp server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md).
The published model evaluation used llama.cpp commit `998200491327347eed85f007e4de7a1a7c871453`.
A build must support this model architecture and parsed tool calls, not just plain text generation.
Follow the project's [build instructions](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md)
for your platform and GPU backend.

One source-build outline, with Git/CMake/C++ tools already installed:

```bash
git clone https://github.com/ggml-org/llama.cpp.git llama.cpp
git -C llama.cpp checkout 998200491327347eed85f007e4de7a1a7c871453
cmake -S llama.cpp -B llama.cpp/build -DCMAKE_BUILD_TYPE=Release
cmake --build llama.cpp/build --config Release -j
```

Use the published evaluation commit when reproducing that build; current upstream versions can change
flags and model support. Enable the appropriate backend during configuration: for example
`-DGGML_CUDA=ON` for a suitable NVIDIA setup, or the documented Metal build on Apple hardware.
The outline above is not a claim that every native platform/backend combination has been tested here.

From the ORCA repository root, after downloading the GGUF:

```bash
llama-server -m models/llm/qwen-ft/Qwen3.6-35B-A3B-orca-ft.IQ4_XS.gguf \
  -c 16384 -ngl 99 -fa on --cache-type-k q8_0 --cache-type-v q8_0 \
  -np 1 --jinja --alias orca-qwen --host 127.0.0.1 --port 8000
```

If built from source, replace `llama-server` with its built executable path, commonly
`./llama.cpp/build/bin/llama-server` on Unix-like systems. Windows builds use `llama-server.exe`;
the precise output subdirectory depends on the CMake generator. For a CPU-only build use `-ngl 0`;
context length, backend and available memory affect feasibility and latency.

The explicit alias makes the advertised model ID **`orca-qwen`**. Without an alias, a server may
advertise the model's filesystem path. The actual Atlas deployment, for example, reports
`/opt/qwen/models/Qwen3.6-35B-A3B-orca-ft.IQ4_XS.gguf`; use that exact ID when connecting to it.
ORCA turns thinking off in its chat request. Do not assume a server accepts that option correctly
without testing its tool response.

In a second terminal:

```bash
./quickstart.sh --mode live --endpoint http://127.0.0.1:8000/v1 --model-id orca-qwen
```

In the UI, open Model connection, discover/test tools and save. Then select Live endpoint / Qwen
and start the scenario. A loaded model and successful `/v1/models` discovery do not prove a valid
parsed tool call; use the tool-compatibility test before judging agent behaviour.

## 8. Connect a remote endpoint

The chat server can run on another machine. Use its reachable HTTP(S) API base, including `/v1`,
and exact served ID. An SSH tunnel can expose a server you control only on your local loopback:

```bash
ssh -N -L 8000:127.0.0.1:8000 your-user@your-model-host
```

Keep the tunnel terminal open, then use `http://127.0.0.1:8000/v1` in the launcher or Model connection.
Replace the example host/user with your own; this command does not provision a VM or grant access
to the project's private deployment. Remote infrastructure and any paid API usage are separate setup.

For an authenticated service, supply its key through Model connection or the `LLM_API_KEY`
environment variable. Keep credentials out of URLs and `--model-id`. The helper rejects URLs
containing credentials, query strings or fragments. Direct Python launch can use `LLM_BASE_URL`,
`LLM_MODEL` and `LLM_API_KEY`; ensure `LLM_MODE=live` for fresh calls. `record` calls and caches;
`replay` requires existing exact-request cache entries and makes no fresh calls.

The model URL is resolved by the **ORCA backend**, not the browser. In Docker, `localhost` refers to
the container; host services may require `host.docker.internal`. Native Python is the supported
minimal dashboard path. The current Compose file runs the older batch demo and is not the documented
local judge website launcher; do not assume `docker compose up` exposes the dashboard.

## 9. Check results and troubleshoot

### Model benchmark reproducibility boundary

The recovered [frozen 300-case comparison](../finetune/benchmark300/README.md) contains case IDs,
full prompts, exact tool schemas and labels, documented inference settings, archived responses for
four models and SHA-256 checks. `python finetune/benchmark300/verify.py` reproduces the historical
first-tool scores without model calls. `run.py` in that directory records a fresh rerun separately.

This is the 8 November rebuilt stratified comparison. Its row identity with the earlier Colab draw
cannot be proved. Tuned Qwen matches 279/300 first-tool labels (93%), including 36 cases with no
expected first tool; the explicit-label subset is 243/264 (92.05%). No tools execute in this benchmark.
The historical server build and inference RNG seed were not retained, so exact requests and archived
scores are reproducible, while bitwise inference outputs are not promised. The old scorer's
`valid_json` constant is replaced by actual parsing in the new verifier. See the archive README for
citation, refusal, final-format and scenario-placeholder limitations.

The general `finetune/eval_cases.py --limit` command remains an ordered smoke test with a different
scope. It is not the frozen stratified comparison. Use [RUN.md](RUN.md) for both commands.

### Operational troubleshooting

| Symptom | Check or action |
|---|---|
| `python3.12` or `py -3.12` missing | Install 64-bit Python 3.12, reopen the terminal and confirm `--version`. |
| `libomp`/`libgomp` or native DLL import error | Install the platform runtime in §2; use the Windows guide for native DLL issues. |
| First startup appears slow before the site opens | Cold M1–M3 training occurs before the HTTP server binds. Wait for training; preserve the terminal error if it fails. |
| Port already in use | Stop your own previous process or select another `--port`; do not terminate an unrelated session. |
| Website missing or stale | Confirm `dashboard/live/dist/index.html` exists, the intended server/port is open, and refresh. Node is needed only to rebuild source. |
| No telemetry yet | The initial session is paused. Start an exercise or play its clock. |
| No recording in Audit | Produce one through a run or the documented headless driver, then reload the recording list. |
| Model discovery fails | Verify base URL includes `/v1`, endpoint is reachable from the backend, exact ID matches and key/tunnel is valid. |
| Discovery works but tools fail | Run the dashboard tool test; verify the model build, chat template, `--jinja`, context and tool support. No silent mock fallback is supplied. |
| Vector query connects to the chat model | Configure `ORCA_EMBED_URL` and a matching embedding model separately from `LLM_BASE_URL`. |
| Vector dimension/ID-order error | Verify all four files from the same pinned dataset revision; do not mix snapshots. |
| Reranker download fails | Check network/cache availability; `--no-rerank` can isolate the issue but changes the pipeline. |
| Long live response or missing result | Check endpoint logs/context/GPU memory and UI error records. Model latency varies; missing output is not successful completion. |
| 3D fails or is slow | Keep the static view and use telemetry/text evidence; 3D loads only when enabled. |

[RUN.md](RUN.md) maintains tests and performance inspection commands. A limited model smoke run
(for example ten cases) is not comparable to the published 300-case evaluation. Distinguish parsed
JSON/tool-call validity, attempted execution calls and actual backend-authorised execution outcomes. The historical model-card
throughput and [RAG test results](KBVEC.md) belong to their documented configurations; a passing
mock exercise, artifact hash or endpoint probe does not establish a full live recovery outcome.

Fresh-clone verification in this session used code revision `d73ace6` in an isolated checkout:
requirements installation, selected Python tests, cold model training, static media/routes and the ten
scenario verdict checks. Optional launchers/docs were reviewed separately as they were added.
The published dataset was additionally downloaded, all four checksums verified, and its 82,191 rows /
4,096 dimensions restored in the isolated checkout. A subsequent fresh evaluation used the CPU
Qwen3-Embedding-8B Q4 service, default BGE reranker and 50 test questions:

| Metric | Fresh restored-index result |
|---|---:|
| Recall@5 | 0.70 |
| MRR@10 | 0.537083 |
| nDCG@10 | 0.588758 |
| Negative accuracy | 0.70 |
| Amendment hit rate | 0.80 |
| Exact citation hit@1 | 1.00 |
| Test-query p50 / p95 | 7,153 / 13,208 ms |

These measurements belong to this restored-index configuration, not the historical timing setup.
Negative accuracy follows the evaluator's evidence criterion and is distinct from negative
abstention accuracy. Quantized-query rankings may differ from the original evaluation setup.
The [judge verification record](JUDGE_VERIFICATION.md) holds the actual commands, environment,
evidence locations and live-model outcomes. Windows mock-launcher and S1 checks passed in the
recorded VM configuration; fully local Windows model serving remains untested.
Do not infer a live recovery outcome from an artifact download, passing mock run or endpoint probe.

## Post-submission combined verification

The [follow-up verification record](POST_SUBMISSION_VERIFICATION.md) documents the combined
fine-tuned Qwen + restored index + CPU embedding + BGE reranker run, native Windows/macOS
launcher checks, recovered benchmark archive and pinned artifact versions. It also records rejected
citations and the adviser fallback limitation. These are measured checks, not a claim of perfect
model accuracy, native Linux support or live satellite connectivity.
