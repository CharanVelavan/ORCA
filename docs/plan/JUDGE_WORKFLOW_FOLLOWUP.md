# Judge workflow follow-up

## Session checklist

- [x] Confirm requested scope and preserve the report unchanged.
- [x] Split implementation across three sub-agents and the integrating parent.
- [x] Plan scenario dimension counts and supporting report wording.
- [x] Update the NTN tagline.
- [x] Implement active-condition duration and engine-backed stop controls.
- [x] Implement evidence-based judge checkpoints and completion summary.
- [x] Implement a public recording evidence export with explicit incident-scope limits.
- [x] Review integration and update guide.md.
- [x] Run focused frontend/backend checks and production build.
- [x] Verify changed flows in Chrome DevTools MCP and report limits.

## Scope

Dimension coverage is a planning deliverable in this turn. Do not alter the report or add dimension counts to the product yet. Use the settled maximum of nine Readiness 2.0 dimensions; distinguish scenario objectives from evidence observed in a particular run. Implement the three previously proposed improvements now. Keep all NTN links emulated, operator truth boundaries intact and replay read-only.

## Results

- Proposed dimension mapping: S0 5/9; N2 and N3 8/9; S1, S2, S3, N1, N4, N5 and CAP 9/9. Reasons, evidence gates and report wording are in [SCENARIO_DIMENSION_COVERAGE.md](SCENARIO_DIMENSION_COVERAGE.md). No report or dimension badge was changed.
- Condition Stop uses the engine's exact injection ID, cancels future condition ticks and logs control-only evidence. It does not reverse earlier effects. Director snapshots stay in the rail's local state.
- Six judge checkpoints require actual public evidence and manual review. Completion means review completion, including inspection of pending or failed outcomes. Older supported proof survives later events; rewind/new run/source changes invalidate unsupported marks.
- Recording evidence JSON fetches fresh public recording data, including facts, models, verdicts/gaps, duties, approvals, execution and outcomes. One recording may contain multiple incidents; no boundaries are inferred. Original-chain status and package integrity limitations are separate.
- TypeScript and Vite build passed. The existing lazy 3D chunk size advisory remains. All 53 focused frontend tests and all 75 live-engine/new-stop tests passed; an additional five focused stop/control-isolation checks passed. `git diff --check` passed.
- Official Chrome DevTools MCP verified pending → active countdown, Stop removal, the JSON download (37 facts, 94 model outputs, nine verdict/gap entries, two duties, three approvals, five execution entries, two summaries in the selected S1 recording), and export scope independent of a zero-match Audit filter.
- MCP checked six manual acknowledgements at the S1 recording end, then rewind to event zero: the summary changed from six reviewed to zero reviewed with six awaiting evidence. The dialog fit desktop and 320-pixel mobile viewports and remained internally scrollable.
- All 40 responsive checks passed across Scenarios, Console, Policy, Recovery and Audit; light/dark themes; widths 1440, 1024, 768 and 320. Desktop pages fit; fitted flows and repository access remained intact. No browser errors or warnings were reported.

Artifacts: `.shots/judge-followup/`. The refreshed preview is on port 8067. Testing used mock inference and existing public S1 recordings; no external Qwen inference or real network action was tested. No commit or push was made.
