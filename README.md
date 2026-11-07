# ORCA-NTN

**Orchestrated Response and Coordination Agents: secure self-healing and cyber incident
coordination for satellite-backed networks.** Entry by team Solar Sailors to the ITU AI for Good
Sandbox Hackathon (UAE), problem statement C1.

Everything runs in an ITU-T Y.3172 ML sandbox on an **emulated** network; no real satellite link
is used. Lifecycle: Predict → Heal → Coordinate → Contain → Fix → Report gaps.

## Status

| Part | State |
|---|---|
| Knowledge base (India + EU/UAE comparisons + gap register) | first version, validated |
| Rule engine (P node, six verdicts) | next |
| Scenario timelines, audit log | next |
| Simulator, M1–M4, agents, remediation, console | planned |

## Quick start

```bash
pip install -r requirements.txt
python tools/validate_kb.py      # check the knowledge base
python tools/fetch_sources.py    # download the official PDFs and record their sha256
pytest
python run_demo.py --scenario C0
```

## Layout

```
kb/          policy knowledge base: india/, global/, gaps/, sources.yaml, SCHEMA.md
rules/       YAML policy rules for the P node (cite kb ids)
scenarios/   reproducible scenario timelines (H1–H4, C0–C3)
map/         Y.3172 and Readiness 2.0 mapping
orca/        kb, rules, audit, llm, agents, models (M1–M4), sim, remediation
tools/       validate_kb.py, fetch_sources.py
submission/  technical report, judge Q&A, video script, slides
```

## Models and LLM

- M1 Isolation Forest; M2 LightGBM quantile forecaster + battery model; M3 LightGBM
  fault-or-attack classifier (5 classes incl. abstain) with ITU-R P.838/P.530 fade residual;
  M4 simple capacity optimiser.
- Agents: Qwen3.8-27B on Google Cloud (OpenAI-compatible endpoint, `LLM_BASE_URL`), with local
  qwen2.5:14b via Ollama as the default and offline fallback. Copy `.env.example` to `.env`.

## Licence

MIT. See `LICENSE`.
