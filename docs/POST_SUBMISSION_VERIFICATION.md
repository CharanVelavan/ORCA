# Post-submission judge verification — 10 November 2026

These checks extend the submitted implementation snapshot `cec8197`; they do not replace the
submitted PDF or retroactively change that snapshot. All network links, attacks, notifications and
remediation are emulated. The approved report and completed videos were preserved.

## Results

| Check | Observed result |
|---|---|
| Final Python suite | 441 passed, 3 skipped, one non-fatal physical-core detection warning; 501.89 seconds |
| Frozen historical model comparison | Exact recovered 8 November request archive and four raw-response files published; tuned Qwen first-tool score rescored as 279/300 (93%) |
| Explicit first-tool subset | 243/264 (92.05%); 36 cases have no required first tool |
| Restored broad index | All four pinned source checksums match; 82,191 vectors, 4,096 dimensions |
| Combined live S1 | Minute 88; 319 fresh Qwen calls, three embedding HTTP calls, three BGE reranker calls, three fresh retrievals |
| Combined-run wall time | 952.353 seconds, including index warmup and explicit post-scenario questions |
| Guarded execution | PB-01, PB-11 and PB-06 completed; approvals came from the scripted headless commander |
| Original live audit | 435 entries; chain intact, terminal anchor retained |
| Citation quality | 15 rejected citation occurrences; 583 accepted occurrences are repeated references, not independent correctness judgments |
| Final echo-fallback probe | Four fresh model calls and three embedding/reranking/retrieval calls; echoed answer discarded, cited quote fallback returned; seven-entry audit chain intact |
| macOS launcher | Fresh hash-locked environment installed, website/API/captions served, `--check` passed; mock S1 reached minute 88 with a valid 325-entry chain |
| Windows launcher | Fresh `.bat` installation, dependency imports, full first-run training, 11 HTTP checks, `--check`, complete mock S1 and valid 325-entry chain |

The final frontend build/check results are recorded in `research/judge-verification/frontend-tests.json`.
The unit-test store/cache were isolated from the live restored index. Skips cover the explicitly
opt-in slow fine-tune rebuild and two retrieval checks without their optional index/embedder. The
separate combined run supplies live-pipeline evidence; it is not inferred from unit-test success.

## Bugs corrected

- Live sessions now give the shared policy adviser the real model client in live mode. Mock mode
  keeps its deterministic quote behavior.
- Operator Ask forwards the actual question to the requested agent instead of substituting an
  `Assess alert ORDER` task.
- BM25 consumes tokenized documents as a generator, avoiding the extra whole-corpus token list.
  A regression test confirms identical scores on the test corpus.
- Empty answers and answers that only repeat the question are discarded before a source quote
  fallback. This narrow guard does not validate arbitrary answer semantics or fix model training.
- The endpoint example and obsolete planning notices were already corrected. Docker's host-model
  comment now uses the current example alias. Native Python remains the documented website launcher.

## What the combined run proves

Fine-tuned Qwen ran on a temporary Atlas Daily L4 Spot VM. The restored Chroma index, the official
Qwen3-Embedding-8B Q4 CPU service and BAAI/bge-reranker-base ONNX reranker ran on the Mac. Retrieval
caching was disabled in the observer; the chat client used live calls. Every source revision and
artifact checksum is pinned in the release manifest.

The baseline S1 assessment largely used structured rules and records. Explicit adviser and operator
questions in the **same session** exercised hybrid retrieval and passed retrieved context into Qwen.
The recorded `query_kb` returned three corpus chunks, all present in the pinned ID file. This is a
plumbing/integration check, not an evaluation proving all agent turns use broad RAG.

The first adviser response contained valid source IDs but only repeated its question. That full
recording remains unchanged. After the guard fix, a separate fresh adviser-only probe returned the
source quote fallback, with a valid chain. The 15 rejected citations in the full run remain a material
model limitation. Scenario completion, accepted citation IDs and correct JSON do not establish
substantive legal or model-answer accuracy.

## Windows and macOS scope

Windows: Windows 11 build 26200, ARM64 guest, Python 3.12.10 `win-amd64` under Windows x64 emulation,
8 virtual CPUs and 18 GB RAM. Parallels Desktop/Tools remained version 26.4.0; neither was updated.
The test started from public `cec8197`, then overlaid the session/retrieval fixes and regression source
for the final native S1. This is not a clean-clone claim about a release tag that did not yet exist.
First-run full network-model training took **625 seconds** in that guest, plus installation/startup.
This is an observation, not a promised startup time. Website routes were HTTP-tested; this follow-up
did not perform a new interactive Windows-browser usability test. Fully local chat/embedding model
serving and GPU compatibility on Windows remain untested. The test VM was suspended afterward.

macOS: arm64 Python 3.12, a fresh `.venv-judge`, the current hash-locked requirements and bundled
frontend. The fresh mock S1 and Windows mock S1 produced the same logical terminal chain anchor.
Their JSONL byte checksums differ because file line endings differ. Linux native execution was
explicitly excluded from this follow-up. Earlier dependency resolution does not establish it.

## Benchmark provenance and limits

[The frozen archive](../finetune/benchmark300/README.md) supplies all 300 case IDs, prompts, schemas,
labels, settings and archived responses. Offline rescoring reproduces all four historical first-tool
scores. This is the 8 November rebuilt comparison; exact row identity with an earlier Colab draw is
not proved. The historical llama.cpp build and inference RNG seed were not retained. An exact-input
rerun is supported, but bitwise identical output across machines is not promised. No tools execute
inside the model benchmark; historical `unsafe_exec` means forbidden predicted calls, not execution.

## Evidence and reproduction

- [Evidence index](research/judge-verification/README.md)
- [Full live inspection](research/judge-verification/qwen-rag-20261110/inspection.json)
- [Fresh fallback probe](research/judge-verification/qwen-rag-20261110/adviser-fallback-check/summary.json)
- [Windows record](research/judge-verification/windows-20261110/windows-verification.json)
- [macOS record](research/judge-verification/macos-20261110/verification.json)
- [Pinned artifact restoration](research/judge-verification/rag-restoration-checksums.json)
- [Verified reranker bytes](research/judge-verification/reranker-checksum.json)

With the services and restored index configured as in the judge guide:

```sh
python scripts/verify_live_rag.py --output output/qwen-rag-new
python scripts/verify_live_rag.py --adviser-only --output output/adviser-new
python finetune/benchmark300/verify.py
```

The driver uses a scripted commander, makes fresh model requests and records both public and
control-audience exercise events. These are clearly labeled research recordings, not bundled live
judge results. Original-chain verification is consistency with its retained anchor, not an external
signature or tamper-proof storage.

The temporary cloud VM was deleted after the checks, and Windows was suspended. The standalone
embedding service on this development Mac remains idle on loopback pending desktop-user cleanup:
the agent CLI identity could not signal the desktop-owned process. This is a developer-machine
cleanup note, not a judge setup step; judges do not need that service or access to the team's cloud.
