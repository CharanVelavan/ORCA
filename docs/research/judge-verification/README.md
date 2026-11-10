# Judge verification evidence

This folder preserves measured results and recordings. All links, attacks, notifications and
remediation are emulated. Mock agents, fresh model calls, recorded playback, planned dimension
coverage and observed execution remain separate claims.

- `session-summary.json` and `rag-v2-evaluation.json`: earlier component checks.
- `benchmark300-rescored.json`: independent offline rescoring of the recovered 8 November
  frozen model comparison. Full inputs and raw responses are under `finetune/benchmark300/`.
- `rag-restoration-checksums.json`: all four restored-index source files match the pinned HF revision.
- `macos-20261110/`: current macOS launcher check and fresh S1 mock recording with original chain.
- `windows-20261110/`: native batch launcher, route checks, mock S1 and original-chain evidence.
- `qwen-rag-20261110/`: final combined live integration evidence; a `summary.json` is required to
  establish completion. A progress file or partial recording alone is not a passing result.

The integration driver uses a scripted headless commander and separately labels explicit adviser/
operator questions. Citation rejection and adviser fallback remain visible in the saved evidence.
Audit chain verification establishes consistency with the saved terminal hash; it is not an external
signature or a claim that no one could rewrite a complete chain.
