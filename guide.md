# ORCA-NTN dashboard guide

ORCA-NTN demonstrates cyber vigilance, secure recovery and incident coordination on an **emulated** Chennai network. Every satellite, gateway, link and injected condition belongs to the software sandbox. The website does not control a live satellite network.

Models detect and forecast. Agents explain evidence and coordinate a response. Deterministic code evaluates policy and execution guards. A person reviews plans and confirms policy findings.

## Start the website locally

From the repository root, using Python 3.12:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m orca.live --scenario S1 --llm mock --port 8060
```

Open [http://localhost:8060](http://localhost:8060). If the environment is already installed, run only the final command. Choose another free port if needed.

The server serves the production dashboard in `dashboard/live/dist`. Node.js is needed only when changing or rebuilding the frontend:

```bash
cd dashboard/live/web
npm ci
npm run build
```

Return to the repository root before starting the Python server. See [docs/RUN.md](docs/RUN.md) for environment and model details.

## Follow the main journey

| Screen | Purpose | Next action |
| --- | --- | --- |
| Learn (`/`) | Understand NTN, ORCA, the methodology, architecture and evidence pipeline. Watch the narrated film or enable the interactive 3D illustration. | Choose a scenario. |
| Scenarios (`/scenarios`) | Browse all ten exercises. Read the selected scenario's setup, progression, signals, model roles, planned response and schedule. No 3D view runs here. | Start the selected exercise. |
| Console (`/workspace`) | Observe the network, inspect models and agents, launch emulated conditions and review proposed actions. | Review Policy and Recovery evidence. |
| Policy & Gaps (`/policy`) | Inspect candidate findings, applicable duties, reporting clocks and source records. | Confirm or reject a finding after reviewing evidence. |
| Recovery (`/recovery`) | Inspect clone tests, path checks, rollout, re-attack checks, restoration and rollback evidence. | Inspect the full record in Audit. |
| Audit & Replay (`/audit`) | Select a recording, filter its audit events, inspect an event, verify its original chain and replay its observations. | Seek, export public audit entries or return to live. |

The GitHub button in the header opens [CharanVelavan/ORCA](https://github.com/CharanVelavan/ORCA). Theme selection persists across navigation and reloads.

**Judge walkthrough** opens six evidence checkpoints: observed network, model output, cited policy finding, human decision boundary, recorded outcome and policy gap evidence. Inspect the linked view, then mark an available checkpoint reviewed. Missing evidence remains unavailable. The summary measures your review, not incident resolution or successful recovery. Starting, approving and injecting remain manual actions. The original Guided tour remains available for learning the interface.

## Choose and start a scenario

1. Open **Scenarios** or use **Choose scenario** in the session bar.
2. Select a scenario card. This previews its briefing and does not replace the active run.
3. Read the objective and planned progression. The schedule is director information, not evidence that an action succeeded.
4. Select the desired next-run mode. Configure and test the endpoint first for Live endpoint mode.
5. Press **Start exercise**. The dashboard enters Console automatically after the backend confirms the exercise has started. An error keeps you on the briefing page.
6. Use **Change scenario** to return to setup. Merely visiting setup does not restart the current exercise.

| Scenario | What to investigate |
| --- | --- |
| S0 | Normal operation and baseline telemetry. |
| S1 | Stolen ground-management credentials, terminal wipe commands and guarded recovery. |
| S2 | Rain fade, power risk and competing services under limited capacity. |
| S3 | Jamming, unsafe failover candidates and a verified domestic recovery path. |
| N1 | Park Town mains failure and falling battery reserve. |
| N2 | A routing fault affecting payment delivery. |
| N3 | Unprotected feeder-link traffic despite apparently healthy throughput. |
| N4 | Falsified management telemetry versus independent service evidence. |
| N5 | A management-plane breach affecting grid and emergency communications. |
| CAP | Concurrent weather, intrusion, battery and capacity constraints. |

A planned response is not a guaranteed outcome. The Console and recording show what was actually observed or executed.

## Understand the three run modes

| Mode | What runs | Can change the emulated network? |
| --- | --- | --- |
| Mock simulation | A fresh simulator run, M1–M4 and deterministic rules. Agent replies use offline deterministic stand-ins. No Qwen request is made. | Yes, through the Console. |
| Live endpoint / Qwen | A fresh simulator run with agents calling the configured OpenAI-compatible model endpoint. | Yes, through the same guarded controls. |
| Recorded replay | Previously recorded events. It does not create a fresh incident or call Qwen. | No. Injections, approvals and policy decisions are read-only. |

The mode selector prepares the next run. The source label describes the current run. Selecting a mode alone does not restart it. Cached model responses, if configured, are labelled separately.

### Connect a local or remote Qwen endpoint

1. Start the model server separately.
2. Open **Model connection**.
3. Enter its API base URL, including `/v1`, and the exact served model identifier. Use model discovery when supported.
4. Provide an optional API key if the endpoint requires it.
5. Test the connection and tool-call compatibility, then save.
6. Select **Live endpoint / Qwen**, choose a scenario and start it.

`localhost` in the model URL means the computer running the ORCA backend. Inside Docker on macOS, a host model server commonly uses `host.docker.internal`. Settings are held in backend memory for the next run. Model errors remain visible; a failed live request is not presented as a successful Qwen response.

## Use the Console

The left icon rail launches emulated conditions. Hover or focus an icon to inspect its condition, target and duration **before clicking**. By default, each condition uses its catalogue target for five simulation minutes. Change the target or duration controls to override that choice. Clicking an enabled icon sends the injection request directly; the recorded director event confirms that the engine accepted it.

The rail groups attacks, faults and benign load conditions. Examples include management intrusion, jamming, unsafe-failover lure, GNSS spoofing, SS7 abuse, telemetry falsification, rain, power failure and traffic surge. These controls affect only the emulator.

Use Play, Pause, Step 1 min and Speed to inspect the unfolding run. Operator tabs expose approvals, alerts, agents, models and policy evidence. **Director truth** is a separate tab; the operator agents do not receive that hidden schedule as evidence.

Drag panel dividers to resize the network, evidence and flow regions. Focus a divider and use the arrow keys for keyboard resizing. Sizes persist; **Reset panel sizes** restores the defaults. Smaller displays stack the regions and keep their internal content scrollable.

The original flowchart fits its side panel. Use its zoom slider or buttons, Ctrl/Command plus the mouse wheel, drag-to-pan, arrow keys, Fit and fullscreen when supported. Zoom does not introduce chart scrollbars.

## Review an action

The Console rail also lists **Injected conditions** with engine-reported remaining simulation minutes. Pending conditions begin on the next step. Use **Stop** to cancel future condition ticks; the action is recorded. Stopping does not undo an earlier terminal wipe or remove an already offered route. Replay and fixture views do not expose live condition controls.

Inspect the proposed playbook, owner, exact targets, parameters, evidence and expiry. Choose Approve, then Confirm approval, or reject the plan with a reason. There is **no commander PIN**.

Removing the PIN does not remove execution checks. The backend still checks ownership, the exact plan and one-time token, expiry, clone test, fresh rule verdict, path integrity and rollout health. The kill switch revokes tokens and blocks execution until released. Autonomy grants retain their selected scope and expiry.

## Read Policy & Gaps

The structured knowledge base is one collection: Indian records plus EU/global comparison material. New website exercises use **Indian rules**. Comparative sources retain their jurisdiction, legal status and effective dates; EU text does not automatically become an Indian obligation. Historical EU recordings keep their recorded rule context.

Use the Gaps, Duties and Sources tabs and search field. Select a row to read its full evidence. Source records can show their summary, checked excerpt, verification state, source URL and SHA-256. Missing metadata is labelled unavailable rather than invented.

The reporting-clock heading stays fixed while the clock list scrolls. Hover over the list and scroll, or focus it and use the keyboard. Resize its divider to show more clocks at once.

Keep each clock's trigger distinct: noticing, awareness and occurrence are not interchangeable. The countdown uses the simulation clock. Rule explanations are immutable evaluations and display their own evaluation timestamp, so an earlier explanation can show more time remaining than the current clock.

A gap title is a candidate finding, supported by a bounded search. Read its citations, nearby provisions and global examples before confirming or rejecting it. “Not found in the sources checked” is not proof that no rule exists. Human decisions are recorded without rewriting the source KB.

## Inspect Recovery and Audit

Recovery separates observed checks and execution results. Restored throughput alone does not prove that every guard or re-attack check passed. Missing evidence remains visible.

The flow's **Current response** label identifies the plan it is evaluating. Execution tables also retain earlier results; a completed earlier plan does not complete a newly requested plan. Rollout health and re-attack outcomes appear only when the backend reports them. Stage health alone does not establish a per-device configuration change.

In Audit, choose a recording with a stream when available. Play, pause, step or drag the scrubber. Selecting an audit event seeks playback to its time and opens its inspector. Search and category filters limit the event index and timeline. Raw JSON is read-only.

**Verify chain** asks the server to recheck the original recording. The UI reports the actual result, including broken or unavailable chains. Export downloads filtered public audit JSONL. Exercise-control entries are withheld, so that redacted export cannot independently verify the full original chain.

**Recording evidence JSON** downloads a fresh public evidence package for the entire selected recording. It includes facts, model outputs, cited verdicts and gaps, reporting duties, approvals, execution and outcomes, plus missing-evidence notices. It ignores the current search filters and replay position. One recording can contain several incidents; the export does not infer incident boundaries. Known exercise-control entries are withheld, but this is not comprehensive sensitive-data redaction. Review before sharing. Original-chain status is labelled separately and does not certify the exported package.

Replay applies across screens. Navigate to Console, Policy or Recovery to inspect the same replay cursor. Return to Audit and choose **Return to live** before changing an exercise.

## Troubleshooting

- **No telemetry:** start the selected exercise or press Play. A fresh paused session can have no samples yet.
- **No reporting duties:** wait for applicable evidence. An empty list does not establish compliance.
- **Inactive attack icons:** check the connection, selected duration and whether the page is replaying a recording.
- **No approval request:** inspect alerts and agents; do not treat the scripted schedule as an actual request.
- **Live endpoint error:** check Model connection and the model server. Start a fresh exercise after changing saved endpoint settings.
- **Old UI after a build:** reload the page. Confirm you are using the intended local server port.
- **3D unavailable:** keep the static view and text description. The rest of the dashboard works without WebGL.

## Validation and limits

Use [docs/RUN.md](docs/RUN.md) for the general test commands. The scenario-first revision's browser checks and results are recorded in [docs/plan/SCENARIO_FIRST_JOURNEY.md](docs/plan/SCENARIO_FIRST_JOURNEY.md). The full walkthrough uses the official Chrome DevTools MCP server. Mock-mode checks do not establish availability or quality of an external Qwen server.

Each scenario briefing displays its planned Readiness dimension count, included IDs and rationale. The [dimension coverage mapping](docs/plan/SCENARIO_DIMENSION_COVERAGE.md) explains the evidence gates. The v7 report includes the same counts. These are planned mappings, not automatic scores for the current run.
