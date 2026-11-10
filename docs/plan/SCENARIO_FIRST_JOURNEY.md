# Scenario-first dashboard journey

## Session checklist

- [x] Inspect user screenshots and current application.
- [x] Verify combined KB and jurisdiction semantics.
- [x] Remove the Active KB switch and retain India defaults with comparative sources.
- [x] Give reporting clocks one keyboard-accessible scroll owner.
- [x] Simplify the Console and add direct-launch icon rail.
- [x] Integrate separate scenario selection and detailed briefing.
- [x] Update navigation, tour and model-mode handoff.
- [x] Write repository guide.md and final suggestions.
- [x] Run focused regressions and production build.
- [x] Test one full scenario and responsive layouts with Chrome DevTools MCP.

## Design decisions

Scenario cards preview a briefing without changing the current run. An explicit Start exercise action creates the exercise and, after confirmed success, opens Console. No 3D scene is mounted on setup. Console keeps observed network, evidence and the original fitted flow; hidden simulator truth has a separate labelled tab. Conditions launch from the left icon rail using the displayed target and duration. Recorded replay remains read-only.

The structured KB already contains 42 India records and nine global records (eight EU, one UAE). The removed toggle changed rule jurisdiction, not loaded records. New UI runs explicitly use Indian rules; comparative source metadata is preserved. Historical EU recordings keep their recorded rule context. Backend switching remains for historical compatibility and tests.

## Planned verification

Use the official Chrome DevTools MCP server for final browser testing. Start from a legacy EU-configured test session, preview S1 without mutation, start it with India rules, exercise the icon rail, inspect models and approvals, inspect Policy and scroll clocks, inspect Recovery, load the same recording in Audit, verify its chain and inspect cross-route read-only behavior. Check light/dark desktop and narrow layouts, keyboard controls, tour targets, empty/error states and repository link. Report actual results without treating scripted expectations as evidence.

## Completed verification

- Production TypeScript check and Vite build passed. The existing lazy 3D bundle still produces a size advisory.
- All 46 focused frontend tests passed, including approval identity, current-plan evidence boundaries and re-attack branch regressions. Nine focused backend projection/live tests and four KB/HTTP checks passed.
- The full Python run finished with 397 passed, three skipped and two obsolete PIN expectations failing (402 collected, 683.72 seconds). Those two tests had already been updated while that run retained their collected old definitions. A separate rerun of both corrected tests passed (2/2, 10.49 seconds). This verifies all 399 runnable cases across the full run and targeted rerun; a second complete run was not performed. The model test emitted one existing physical-core detection warning. `git diff --check` passed.
- Official Chrome DevTools MCP exercised S1 in mock mode: briefing preview made no session mutation; Start sent Indian-rule context and opened Console; the icon rail submitted an accepted CHN-02 jamming condition with a five-minute duration; a PB-01 approval produced reported rollout and re-attack evidence.
- Policy displayed the combined source collection and Indian duties. Keyboard End scrolled the reporting list to its maximum (224 px) while the panel heading stayed fixed and the desktop document stayed within the viewport.
- Recovery displayed all three reported PB-01 rollout stages. A subsequent PB-11 request correctly remained unobserved in the current-response flow, independently of historical PB-01 execution.
- Audit loaded the same S1 recording (232 public replay events, 48 public audit entries), scrubbed to the end and verified the original recording chain. Replay controls remained read-only across Console and Scenarios, with no mutation requests.
- Offline Start failure stayed on the briefing and offered retry. Bundled-fixture navigation changed the fixture without a backend POST. The next-run Live/Qwen preference did not mislabel an existing mock session.
- All 50 responsive cases passed across five screens, five widths (1920, 1366, 1024, 768, 390) and both themes. Desktop pages fit the viewport; Scenarios mounted no 3D canvas; Console contained no setup-guide column; the repository link remained accessible.
- The complete 14-step tour traversed Learn → Scenarios → Console → Policy → Recovery → Audit using native MCP clicks. All newly measured steps had visible targets and cards within the viewport; Finish closed the dialog. The tour generated only GET requests and no console errors or warnings.

Browser snapshots, screenshots, layout metrics and request evidence are local under `.shots/journey-final/`. Tests used an isolated server on port 8068; the user preview on port 8067 remains available. External Qwen availability and inference quality were not tested by this mock walkthrough.

## Bugs corrected during the walkthrough

Approval events now expose a consistent plan identity without rewriting the audit chain. Rollout projection supports the playbook that actually executed and emits only explicitly reported stage health and re-attack outcomes. The UI scopes flow completion to the latest requested plan and its evidence window, preventing earlier approvals, executions or re-attacks from completing a new request.

## Suggested next improvements

1. Show active injected conditions with remaining duration and an explicit stop action backed by the engine.
2. Offer a short judge walkthrough with curated observation checkpoints and a visible exercise-completion summary.
3. Add a per-incident evidence package containing cited verdicts, reporting duties, approvals and execution outcomes, with clear export/redaction limits.
