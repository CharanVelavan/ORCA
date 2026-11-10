# Judge readiness verification

## Completed session checklist

- [x] Inspect published instructions, model/RAG contracts and stale routes.
- [x] Clone public main into an isolated directory without project caches or credentials.
- [x] Install dependencies in fresh Python 3.12 environments and create a universal hash lock.
- [x] Start the mock dashboard cold, then verify repeat quick-start launch and cleanup.
- [x] Verify scenario APIs, bundled UI/media, and website guide on desktop/mobile.
- [x] Correct README/RUN/DEMO and deliver complete HF/local endpoint/RAG/Windows guides.
- [x] Download and checksum the tuned Qwen weight on the test VM; verify discovery/tools.
- [x] Complete a real Qwen S1 run and a separate browser-approval mock S1 run.
- [x] Restore the public vector index, run fresh retrieval evaluation and managed embedding cleanup.
- [x] Verify recording chains and source/download links; document actual results and remaining limits.

## Final checks

- Python targeted setup, scorer, KB CLI, safety and live projection suite: **117 passed in 84.46 s**.
- Frontend state, evidence, clocks, flow, policy and dimensions suite: **55 passed**.
- Offline guide synchronization tests: **2 passed** (byte-identical copy and missing-source failure).
- TypeScript and production Vite build: **passed**. Existing optional 3D chunk is about 977 kB and
  still produces the build size advisory; no build failure.
- All seven maintained Markdown entry points: no missing repository-relative file targets.
- All three served guide downloads: HTTP 200, exact bytes match repository sources.
- Chrome DevTools MCP: guide 1440×900 and 320×900, no document horizontal overflow or console
  errors/warnings; native recording selection and Verify chain passed for the fresh Qwen run.
- Public KB validation: 51 records, 49 quote checks; all ten scenario files and 40 expected verdicts passed.
- Fresh RAG v2 evaluation: 50 test questions, Recall@5 0.70; raw rows retained in the repository.
- Native Windows/Linux runtime: **not run**. Dependency resolution dry runs passed; batch launcher
  static checks only. Historical 300-case Qwen request bundle: **still missing**, no new 93% claim.
- Atlas test VM and temporary boot disk: deleted and absence verified. No cloud endpoint is required
  for the default launcher.

See [JUDGE_VERIFICATION.md](../JUDGE_VERIFICATION.md) for modes, commander provenance, 14 rejected
citation occurrences, actual recording counts, hardware and benchmark limits. The initial baseline
was commit `d73ace6a682483c670c1a570404930691eac75e8`; new setup files were overlaid in the isolated
checkout for testing. The user's existing dashboard on port 8067 was preserved.
