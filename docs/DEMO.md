# ORCA-NTN demo

The demo runs entirely on the emulated Chennai network. It uses the mock LLM and makes no external model calls.

## Start the console

From the repository root, start the live server:

```bash
python -m orca.live --scenario S1 --llm mock --port 8060
```

Open [http://127.0.0.1:8060/](http://127.0.0.1:8060/) in a browser. On Simulator, select a scenario and click **Start selected scenario**; this starts the emulated session and its clock. Use the clock controls to pause or resume it. All displayed times are simulation time in IST.

For a source build, with Node.js 24 and npm installed:

```bash
cd dashboard/live/web
npm ci
npm run build
cd ../../..
```

The build is served by the live server. If Python dependencies are not installed, install the repository requirements in the active Python environment before starting the server.

## Path 1: S1 - SAT-MGMT intrusion and recovery

1. Select **S1** in Simulator and click **Start selected scenario**.
2. Open **Operations**. Follow the M1/M3 evidence and the alert as the emulated incident develops. The intrusion targets SAT-MGMT, the operator's ground management network; the satellite itself is not compromised.
3. Review the PB-01 request, its owner, targets, clone-test result and evidence. The incident commander approves or rejects it. Use the explicit confirmation action; no commander PIN is required. Execution still checks the exact plan, owner, expiry and safety guards.
4. Open **Recovery** to inspect the execute diff, staged rollout, rollback and re-attack check, together with the event-derived delivery and timing results.
5. Open **Investigation** to review the model and telemetry evidence. Ground truth is available only on Simulator.

## Path 2: S2 - storm and capacity allocation

1. In Simulator, select **S2** and click **Start selected scenario**.
2. Review **Operations** for the storm, the clean-path check and the recovery action.
3. Open **Recovery** and inspect the M4 allocation and delivered Mbps by service. During scarcity, verify from the displayed event data that 112 and hospital demand are prioritized while lower-priority service may be shed.

## Path 3: N5 - reporting clocks and knowledge-base comparison

1. In Simulator, select **N5** and click **Start selected scenario**.
2. Let the simulation reach minute 64 (about 20:04 IST from its 19:00 start). This is when N5 evaluates the data-location question and the related candidate finding can appear.
3. Open **Policy & Gaps** and review the reporting obligations, their trigger basis and due times, and the gap records.
4. Switch the knowledge base from **India** to **EU** using the page control. Compare the updated clocks and gaps, then switch back to India. The records shown are those supplied by the selected knowledge base.

## Headless smoke checks

These commands run a scenario without the browser and print its final summary:

```bash
python -m orca.live.headless --scenario S1 --llm mock
python -m orca.live.headless --scenario S2 --llm mock
python -m orca.live.headless --scenario N5 --llm mock
```

Use the browser for the commander approval flow and the India/EU knowledge-base comparison. Do not treat simulator ground truth as operator evidence.


## Redesigned dashboard and tour

Open the landing page to learn the method. Use **Guided tour** in the navigation for a fourteen-step walkthrough. Follow **Learn → Simulator → Operator → Policy & Gaps → Recovery → Audit & Replay**.

The Simulator previews each scenario before starting it and explains its planned events. Attack launch controls operate only inside the emulated network. The Operator receives observed public evidence.

For live inference, open **Model connection**, enter an OpenAI-compatible base URL and exact served model identifier, test tool compatibility, and select **Use for next run**. Choose **Live endpoint / Qwen**, then start a new run. Mock simulation and recorded replay remain explicit alternatives. A model server must already be running; the dashboard does not download or host the model.

Use **Shared view** to run the Simulator beside the Operator in one session. The Simulator sees director truth; the Operator receives released observations. Open **Mode help** for the difference between mock, live and recorded replay.

Use **Detailed graph** on Operator to open the full execution diagram or system architecture. Lifecycle **Seen** means observed work, not verified incident completion. Historical verdicts show their evaluation time separately from current clocks. See [the journey implementation notes](plan/DASHBOARD_JOURNEY_IMPLEMENTATION.md) for contracts and validation.
