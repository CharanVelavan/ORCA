# Judge setup verification — 10 November 2026

This is an execution record for the judge reproducibility package. Every network link, attack,
notification and remediation described here is emulated. It is not a production NTN deployment or
an independent human evaluation. Start with [JUDGE_REPRODUCIBILITY.md](JUDGE_REPRODUCIBILITY.md)
for setup and [RUN.md](RUN.md) for maintained commands.

> **Follow-up completed:** see [post-submission verification](POST_SUBMISSION_VERIFICATION.md) for
> the combined live Qwen/RAG run, native Windows/macOS checks, recovered frozen benchmark and
> release evidence. The initial component checks below retain their original scope.

## Clean checkout and launcher

The baseline was public `main` at `d73ace6a682483c670c1a570404930691eac75e8`, cloned into an
isolated directory without the project's model or vector caches. The final setup helper and lockfile
were then overlaid for verification. This is not a claim that the old commit contained the new helper.

- A fresh Python 3.12 environment installed the public dependencies on macOS arm64.
- Starting the baseline mock dashboard with no trained model cache completed M1–M3 training and
  served the scenario API, website, captions and 4K film. First startup took several minutes.
- The new `quickstart.sh` installed the hash-locked dependencies into a second, fresh `.venv-judge`.
  A repeat launch reused that environment and served a paused S1 mock session on loopback.
- `--check` passed. Ctrl+C stopped the helper's dashboard child and released its port.
- An occupied dashboard port now produces a short error before installation or downloads; it does
  not terminate the process already using that port.
- Windows and Linux dependency resolution dry runs passed against the universal lock. **Native
  Windows and Linux execution was not performed.** The `.bat` launcher was reviewed statically.

Git, 64-bit Python 3.12 and the platform's native runtime are prerequisites. The optional fully local
model path also requires a compatible installed `llama-server`; the launcher does not install that
binary or provision cloud infrastructure. See the setup guide for memory/disk planning.

## Actual fine-tuned Qwen run

The project fine-tuned IQ4_XS GGUF was downloaded to the test VM and its SHA-256 matched the public
Hugging Face artifact:

`011d7797836571495e8faf545101bee1e71d75a39292e06f946e8a3646b54e16`

Model discovery and the backend's parsed tool-call test passed. A full **S1 with rules enabled** then
ran against that model on an NVIDIA L4, using fresh calls rather than a response-cache replay.
The run took **886.3 seconds wall time** and reached simulation minute 88.

| Observation | Result |
|---|---:|
| Audit entries | 427 |
| Projected stream events | 1,428 |
| Agent tool steps / final responses | 312 / 70 |
| Original deterministic verdict entries | 11 |
| Projected verdict events | 22 |
| Approved playbooks executed successfully | PB-01, PB-11, PB-06 |
| Original audit chain | Verified intact |
| Rejected citation occurrences | 14 |

The 22 projected verdict events include repeated observations; they are not 22 independent rule
evaluations. Citation rejection is a material model-quality limitation: the evidence guard rejected
14 citation occurrences. Successful guarded execution does not establish perfect model output.

The commander in this run was the **scripted headless commander**, with approvals and emulated
notifications scheduled by the driver. The live run used structured policy records; the subsequently
restored broad vector index was tested separately below. This does not establish an end-to-end
Qwen-plus-broad-RAG benchmark. No inference-quality score is inferred from the scenario completing.

The test Atlas GPU VM and its temporary boot disk were deleted after verification. The dashboard's
mock mode and saved recordings remain usable without that cloud endpoint. The launchers do not
start Atlas or require access to the team's private project.

## Browser exercise and replay

A separate S1 mock run exercised the native dashboard **Approve → Confirm** controls for PB-01,
PB-11 and PB-06. Simulation stepping and emulated notifications were automated through the local
API. Console, Policy & Gaps, Recovery and Audit were inspected using the official Chrome DevTools
MCP. The recording reached minute 88, all three executions succeeded, and Audit verified its
original chain. This is an automated UI test, not an independent operator study.

The new `/guide` page was checked at 1440×900 and 320×900. Neither viewport had document-level
horizontal overflow. All three Markdown download URLs returned HTTP 200, and no browser console
errors or warnings were present on the guide. The Markdown files are copied from repository sources
at build time. Final source/build checks are listed in the session checklist.

Three complete recording pairs were retained locally in ignored `runs/`, including the real Qwen
recording `live-20261110-081234-618448-s1-rules-local.jsonl`. They can be opened from Audit on this
machine. They are not silently bundled as a new judge's live evidence. Run the documented headless
driver or start an exercise to generate that judge's own recording.

## Public RAG restoration and fresh evaluation

The four required files were downloaded anonymously from the pinned public HF dataset. All four
checksums passed, and `load-vectors` restored **82,191 vectors with 4,096 dimensions** into a fresh
`orca_v2` collection. A fresh CERT-In reporting query returned the Direction (ii) clause first.

The official Qwen3-Embedding-8B Q4_K_M GGUF ran on CPU, with the BAAI/bge-reranker-base ONNX
reranker. The fixed v2 evaluation ran all 100 development/test questions; the following quality
metrics use the **50-question test split**, with the development-selected threshold of −3.0:

| Metric | Fresh result |
|---|---:|
| Recall@5 | 0.7000 |
| MRR@10 | 0.5371 |
| nDCG@10 | 0.5888 |
| Negative abstention accuracy | 0.7000 |
| Amendment hit rate | 0.8000 |
| Exact-citation hit@1 | 1.0000 |
| Median / p95 latency | 7.153 s / 13.208 s |

The evaluation's denominators differ by question category. Exact-citation hit@1 applies to the
explicit-citation subset, not all questions. Latency describes this CPU run, including its runtime
conditions; it is not a promised judge-machine speed. Full rows and evaluator fields are retained in
[rag-v2-evaluation.json](research/judge-verification/rag-v2-evaluation.json).

The helper's `--serve-embedding` path was also exercised against the verified cached GGUF: it started
the real CPU embedding service and mock dashboard, a fresh vector query returned the same CERT-In
clause first, and Ctrl+C released both ports 1235 and 8074. This test reused the cached embedding
weight through a local symlink to avoid a duplicate 4.68 GB download; the public dataset download was
tested separately. Non-fatal macOS cache/telemetry warnings did not prevent the query result.

The previously misplaced CLI `--v2` option was moved onto `eval`/`evaluate`, making the documented
command executable. Tests cover both aliases and legacy evaluation argument handling.

## Benchmark boundary and remaining gaps

The model scorer now supplies current role tool schemas when a case lacks them, records case IDs
and schema/data hashes, and measures JSON validity rather than reporting a constant pass. It never
executes predicted tools. `--limit 10` means the first ten held-out rows in file order, which are not
the historical stratified 300-case sample.

At this initial component-verification stage, the historical **93% tool-selection** result had not
been rerun and its public request archive was missing. The follow-up recovered the 8 November
comparison archive and reproduced 279/300 from its raw responses. See the
[frozen inputs, provenance and limits](../finetune/benchmark300/README.md). A later limited model smoke attempt did not complete after the first VM disappeared;
no passing result or new benchmark score is claimed for it.

At that initial stage, native Windows/Linux runtime testing and simultaneous fully local chat
plus embedding performance were unverified. The follow-up adds Windows mock execution and combined
remote-Qwen/local-RAG verification; Linux and fully local Windows model serving remain untested. The hosted model, fresh local vector search,
managed embedding startup/cleanup and mock launcher are separate checks. The launch scripts make
the supported setup paths concrete without claiming every hardware combination was exercised.

[session-summary.json](research/judge-verification/session-summary.json) records recording counts,
hashes, mode and commander provenance. It cannot independently verify an original chain without the
corresponding local JSONL file. See [the readiness checklist](plan/JUDGE_READINESS_CHECK.md) for final
code/build test counts.
