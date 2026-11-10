# Dashboard journey and guided tour

Implemented on 10 November 2026. The current source is the authority. This document supersedes the older light-theme-only layout specification for the redesigned pages.

## Visitor journey

1. **Learn** explains the Chennai story, emulated underlay, methodology, M1–M4, agent responsibilities, deterministic rules, human authority, policy gaps, evaluation and limits.
2. **Simulator** is the director workspace. Select a scenario to preview its guide and planned schedule. Starting the selected exercise is a separate action. Launch emulated conditions, inspect director truth, and pause or advance the clock.
3. **Operator** receives public observations. Review the network, agent activity, citations, models and proposed actions. Existing commander authorization guards remain in place.
4. **Policy & Gaps** separates reporting duties, evaluated verdicts, candidate gaps and human review.
5. **Recovery** shows actual rollout, service delivery, re-attack and rollback evidence.
6. **Audit & Replay** provides recording selection and a read-only cursor through public evidence.

The primary navigation connects these views without a duplicate journey strip. **Shared view** opens Simulator and Operator side by side in one session. **Guided tour** starts fourteen explanatory steps. It navigates and highlights real controls, but never starts a session, injects a condition, approves a plan, changes a KB or runs a tool. It can be skipped or restarted. Native modal semantics provide keyboard focus containment and Escape dismissal.

## Model connection

From a workspace, open **Model connection**. Enter the API base URL including `/v1`, discover or enter the model identifier, and provide an optional API key. **Test tool compatibility** performs a harmless parsed tool-call probe without executing a tool. **Use for next run** stages the settings in backend memory. Select **Live endpoint / Qwen** and start a new run to apply them.

The browser communicates with the ORCA backend. Localhost refers to that backend's host; a model on the host of a Docker container may require `host.docker.internal`. Existing environment defaults still work. Keys are not returned, stored in the browser or included in audit metadata. Connection failure is explicit and never silently switches to mock.

Modes are labelled separately: mock simulation, live endpoint with actual model/source metadata, cached model replay where configured, and recorded dashboard replay. Choosing recorded replay opens Audit to select a recording. Replay playback belongs to the shared application shell and continues across routes, with pause/resume and cursor controls in the session strip. A new session clears previous run state.

Endpoints: GET/POST `/api/model-config`; POST `/api/model-config/discover`; POST `/api/model-config/test`; GET `/api/scenario-detail?id=S3` (director-only response).

## Workflow and clock semantics

Footer lifecycle names remain Predict → Heal → Coordinate → Contain → Fix → Report gaps. They represent parallel workstreams. **Seen** means activity was observed; it is not an incident-completion claim. **Active** requires actual pending agent or human work. Five-second legacy phase recency cannot establish task completion.

Compact and expanded execution graphs use a shared evidence projection. A model output completes a classification task even if the classified condition remains flagged. A clean check alone cannot prove failover. A restoration timing alone cannot prove re-attack validation. New approvals cannot borrow older execution results. Missing evidence remains unobserved.

Reporting obligations carry stable identities, event sequences and policy epochs. Current summaries cannot borrow notices from an older policy epoch. Legacy recordings join only on an exact regime/trigger-time/deadline tuple. Verdict explanations retain their evaluation date and time, separate from the current simulation countdown. Times are displayed in IST.

## Diagram and motion

**Expand detailed flow** opens the recovered seven-band diagram with zoom, keyboard-focusable evidence and scrolling when zoomed. The separate Architecture view explains methodology and refusal/rollback branches without pretending it is a completed run.

The Learn film is a real HyperFrames render: 98.5 seconds, with a native 3840 × 2160 master at 24 fps and a 1280 × 720 web copy. Google Cloud Enceladus narrates in American English at its natural speaking rate, with original sound effects ducked below speech. It reuses the existing Blender-exported models for an emulated connectivity, compromise and recovery storyboard. A separate six-second silent network clip is also available on Learn. Source, local assets and pinned commands are in `dashboard/live/web/src/home/motion/`. The MP4, poster and captions are in `dashboard/live/web/public/media/`. It is an explicitly labelled illustration, with native controls, transcript and no autoplay. Judges need no HyperFrames installation.

## Validation

Target workspace viewport: 1366 × 768 CSS pixels, 100% zoom. The Learn page scrolls. The Operator response-flow overview fits without scrolling; each task opens its evidence. Workspace lists, evidence and detail panes may scroll internally. A short-height or narrow display uses a readable scrolling fallback rather than hiding controls. Narrow screens use a readable scroll fallback.

Run frontend checks from `dashboard/live/web`:

```sh
node --test --test-concurrency=1 tests/live-store.test.mjs tests/workflow-clock.test.mjs src/review/audit.test.mjs src/review/normalize.test.mjs
npm run build
```

Run relevant backend checks from the repository root:

```sh
python -m pytest tests/test_live_model_config.py tests/test_live_ui.py -q
```

Browser verification uses an isolated server/profile and the official ChromeDevTools MCP server. Never reconfigure a judge's running session as a side effect of the tour.

### Verification recorded on 10 November

- TypeScript compilation and production Vite build passed. The existing optional 3D bundle still produces a size advisory; it is lazy-loaded.
- 36 focused frontend tests passed.
- 11 focused backend/API/UI-boundary tests passed on the final backend changes.
- The broader live suite passed 76 tests during implementation; final clock edits were separately covered by focused regressions.
- Browser: all six main routes and thirteen tour steps passed with zero page errors. The tour issued zero POST requests.
- Simulator and Operator stayed at 1366 × 768 without document scrolling. At 1440/1024/768/390 px widths, neither workspace produced horizontal document overflow; smaller layouts use readable vertical scrolling.
- Official Chrome DevTools MCP 1.12.0 confirmed six Operator sites visible, a 1366 × 768 document, working API requests, and no console warnings/errors. Recorded playback continued across Audit → Operator with a moving cursor and read-only controls.
- Model configuration, discovery, secret redaction and session application were exercised against a compatible test endpoint. Actual live Qwen inference requires the user's running model server and was not claimed as tested.

## Revision 2

The Learn page now leads with cyber vigilance and secure self-healing, explains ORCA in scroll-revealed points, and includes an interactive report-aligned architecture. The KB graph separates the verified-rule path from the broader retrieval path. The current RAG method, provenance and measured limits are explicit.

The redundant global scenario selector and numbered navigation strip were removed. Current scenario identity appears in the shared Simulator header. Workspace headings are compact. Model, tour and mode-help dialogs use explicit contrast; the tour spotlight preserves the highlighted content and bounds the explanatory card. Run-mode help explains fresh mock simulation, fresh endpoint inference and read-only saved-event playback.

See [the revision acceptance checklist](DASHBOARD_REVISION_2.md) for the current verification outcome.

### Restored side-panel chart

Following Charan’s review, the compact task grid is replaced by the original decision-and-branch flowchart in the right-hand panel, including Shared view. It fits the complete diagram to both available dimensions by default. Zoom controls, background dragging, keyboard arrow panning and Fit allow closer inspection without chart scrollbars. The panel remains resizable. On narrow screens it moves beneath the content. Evidence projection and the expanded seven-band diagram are retained.

Restored-chart validation: TypeScript and production build pass; 37 focused frontend tests pass. Browser checks at 1920/1366/1024/390 pixels cover Operator, Shared view, Policy and Recovery: all sixteen diagrams fit their viewports with hidden overflow and no compact task grid. Zoom increased from 29% to 57%, arrow panning moved the chart, and Fit restored 29%. Official Chrome DevTools MCP independently confirmed the complete original chart fits the 1366 × 768 Operator side panel. The overview necessarily uses small type to show the whole vertical chart; zoom provides readable inspection.

The later brand/theme/film delivery is documented in [Dark theme and 4K verification](DARK_THEME_AND_4K.md). The top navigation now includes a saved light/dark toggle, the new ORCA dorsal-fin/orbit mark and favicon. Workspace headers use compact inline identity and safety controls.
