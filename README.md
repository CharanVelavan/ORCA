# ORCA-NTN

**Orchestrated Response and Coordination Agents: secure self-healing and cyber incident
coordination for satellite-backed networks.** Entry by team Solar Sailors to the ITU AI for Good
Sandbox Hackathon (UAE), problem statement C1.

Everything runs in an ITU-T Y.3172 ML sandbox on an **emulated** network; no real satellite link
is used. Lifecycle: Predict → Heal → Coordinate → Contain → Fix → Report gaps.

Read the [website guide](guide.md) for scenario setup, Console controls, policy evidence and recorded replay.

The updated five-page report is available as [PDF](submission/ORCA-NTN-report-v7.pdf) and
[editable DOCX](submission/ORCA-NTN-report-v7.docx). It explains the nine selected Readiness
dimensions and distinguishes planned scenario coverage from observed-run evidence.

## Status

| Part | State |
|---|---|
| Emulated Chennai network, scenarios, M1–M4 and agents | Implemented in the live prototype |
| Guarded remediation, approvals, autonomy and audit | Implemented in the live prototype |
| Policy verdicts, reporting clocks and gap register | Available in the Policy & Gaps console |
| Dashboard | Home, Simulator, Operations, Investigation, Policy & Gaps, Recovery, and Audit & Replay |
| Demo instructions | [`docs/DEMO.md`](docs/DEMO.md) |

## Quick start

Install the repository's Python requirements, then start the live emulated console:

```bash
pip install -r requirements.txt
python -m orca.live --scenario S1 --llm mock --port 8060
```

Open `http://127.0.0.1:8060/`. See [`docs/DEMO.md`](docs/DEMO.md) for the S1, S2, and N5 demo paths and source-build instructions.

## Layout

```
kb/          policy knowledge base: india/, global/, gaps/, sources.yaml, SCHEMA.md
rules/       YAML policy rules for the P node (cite kb ids)
scenarios/   reproducible scenario timelines
map/         Y.3172 and Readiness 2.0 mapping
orca/        kb, rules, audit, llm, agents, models (M1–M4), sim, remediation
tools/       validate_kb.py, fetch_sources.py
submission/  technical report, judge Q&A, video script, slides
dashboard/   live React console and emulated-network scene
docs/        run instructions, demo paths, and build plans
```

## Models and LLM

- M1 Isolation Forest anomaly detector; M2 minute-level link and battery forecaster; M3 LightGBM
  fault-or-attack classifier with 8 classes, including GNSS and signalling attacks; M4 mixed-integer
  capacity allocator.
- Agents: Qwen3.8-27B on Google Cloud (OpenAI-compatible endpoint, `LLM_BASE_URL`), with local
  qwen2.5:14b via Ollama as the default and offline fallback. Copy `.env.example` to `.env`.

## Licence

MIT. See `LICENSE`.
