# ORCA-NTN judge demonstration

All links, conditions and recovery actions are emulated. This walkthrough uses one shared session.

## Start locally

Follow [RUN.md](RUN.md) to create a Python 3.12 environment and install requirements, then run:

```bash
python -m orca.live --scenario S1 --llm mock --port 8060
```

Open http://127.0.0.1:8060/. First startup trains the full synthetic model bundle if the ignored
`models/orca_models.pkl` cache is missing. Allow several minutes before expecting the server to answer.
Later startups reuse the cache. The committed dashboard and media require no frontend build.

## Main judge path

1. **Learn:** inspect the architecture and KB/RAG explanation. Play the narrated film if useful.
2. **Scenarios:** select S1 and read its objective, signals, planned response, schedule and planned
   Readiness dimensions. Selection is a preview; press **Start exercise** to create a fresh run and
   enter **Console** automatically.
3. **Console:** pause or use **Step 1 min** to inspect released observations. Read Models, Alerts and
   Agents. The director rail launches additional emulated conditions; its countdown and Stop affect
   future simulated ticks. Stop does not undo earlier changes. Director truth is separately labelled.
4. **Approvals:** inspect the exact owner, targets, evidence, clone test and expiry. Approve or reject
   manually. Approval does not guarantee execution: every backend guard still applies. No PIN is used.
5. **Policy & Gaps:** inspect cited duties, separate reporting triggers and candidate gaps. Scroll the
   clock list. New runs use Indian rules with EU/global comparison sources in the same collection.
6. **Recovery:** inspect execution results, rollout health, clean-path and re-attack evidence. Preserve
   refusals and missing evidence; throughput alone does not prove secure recovery.
7. **Audit & Replay:** select the recording created by this run, scrub its events and **Verify chain**.
   **Recording evidence JSON** exports public evidence for that entire recording, independently of
   search filters. It may include several incidents and cannot independently verify the original chain.
8. Use **Judge walkthrough** to review the six available evidence checkpoints. Completion measures
   your review, not whether recovery succeeded. The separate **Guided tour** explains the interface.

Use **Change scenario** to return to the briefing. Visiting Scenarios does not reset the active run.
Replay stays read-only across views. Choose **Return to live** in Audit before changing an exercise.

## Other exercises

- **S2:** inspect rain/battery forecasts and constrained service capacity. Check actual 112/hospital
  demand and delivery rather than assuming the scripted priority outcome happened.
- **S3:** inspect jamming and unsafe or foreign backup offers; require a verified domestic path.
- **N5:** inspect separate reporting clocks, telecom/grid evidence and candidate findings.

There is no Active KB toggle. Historical EU recordings retain their own rule context; paired country
comparisons can use the headless `--kb` option. The website starts new runs with India.

## Real Qwen inference

A model server must already be running. Open **Model connection**, enter the OpenAI-compatible
base URL and exact model ID returned by `/v1/models`, test tool compatibility, then choose **Use for
next run**. Select **Live endpoint / Qwen** and start the scenario. Configuration is in memory and
resets when this dashboard server restarts. Keep API keys out of chat and source control.

Alternatively export `LLM_BASE_URL`, `LLM_MODEL` and, if required, `LLM_API_KEY` in the shell before
launching with `--llm local`. The Python CLI does not automatically load `.env`.

Mock simulation makes no Qwen calls. Recorded replay makes no new inference calls. Live endpoint
mode uses the configured server and reports errors; it does not silently fall back to mock replies.

## Save a deterministic fallback recording

```bash
python -m orca.live.headless --scenario S1 --llm mock --runs-dir runs
```

The headless driver uses a labelled scripted commander with a fixed approval delay. It exercises the
same owner, token, expiry and execution guards. It is not a recording of a person approving in the UI.
It writes audit and stream files. Restart the dashboard after generating recordings if the Audit list
was already open; choose the stream recording in Audit and verify the chain.

For further details, see [the website guide](../guide.md), [KB setup](KBVEC.md) and
[the dimension mapping](plan/SCENARIO_DIMENSION_COVERAGE.md).
