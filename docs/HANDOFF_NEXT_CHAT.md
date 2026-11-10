> **Historical planning record.** Original status and assumptions may be superseded. For current setup, use the [documentation index](README.md) and [judge reproducibility guide](JUDGE_REPRODUCIBILITY.md).

> **8 Nov update: read `docs/plan/MASTER_PLAN_v3.md` first.** It is the agreed plan (goal, missions,
> agent split, waves, rules, state). It overrides this file where they conflict.

# Handoff for the next chat (written 7 Nov 2026)

Read this first, then `docs/BUILD_PLAN.md` (v1, written before the jury rules below; sections 2–4
on architecture, models and data still apply unless changed here). Submission: **10 Nov 2026**.

## 1. New jury rules (override everything older, including CLAUDE.md)
1. Judging priority: **report > GitHub code > video**.
2. Report: **strictly 5 pages including images**, ITU template.
3. Structure: **a short idea overview first, then detail**: the role of the AI and the role of
   **each** AI agent and ML model, in detail.
4. The idea must be **useful as a pillar of everyday work**, not only a crisis tool.
5. **Policy explainability is critical:** state explicitly **what an AI agent can explain** and
   **what humans must explain**.
6. Any country may be chosen, as long as its policy is clear.
7. Datasets: from the ITU **CG Datasets** catalogue (Feb 2025, 121 datasets):
   `~/Downloads/2.CG Datasets Feb 13 2025 4.docx`.
8. **Code delivery (judges' answer to the user, 7 Nov):** any repo format is fine and a dashboard
   (or anything of our choice) is allowed, but **clear instructions on how to run the entire code are
   mandatory**. We may **host it on Google Cloud or AWS** and link it from the repo so the jury needn't
   set anything up, and/or send the whole code base with clear setup instructions for their laptops.
   **Raspberry Pi 5 and STM32MP135F-DK** may be used if needed.
9. **User priority (7 Nov): the biggest win is finding policy gaps, analysing them and taking the
   required actions.** The gap pipeline (detect → prove with evidence and search record → analyse →
   interim playbook + recommendation to the named regulator) is the headline of the report and demo.

## 2. Scope (decided by the user, 7 Nov)
- Theme: **cyber security in everyday life on NTN (satellite-backed networks) + self-healing from
  the effects of a cyber attack.**
- Why NTN: NTN has little cyber-security policy (a gap), so the project fills it.
- Must state that the system **can be integrated into everyday uses** (payments, hospitals,
  112, utilities, homes that rely on satellite-backed links).

## 3. Decisions still in force (from BUILD_PLAN.md)
- Main city **Chennai**; KB currently India + EU/UAE comparisons (country may change after agent B).
- LLM **Qwen3.8-27B** on our Google Cloud; local qwen2.5:14b fallback; no core fine-tuning
  (QLoRA on Colab A100 = stretch).
- M1 Isolation Forest (+ECOD comparison); M2 minute tier (synthetic) + daily tier (Turkcell),
  framed as an exposure window; M3 LightGBM, 8 classes incl. attack-GNSS, attack-signalling,
  abstain; M4 MILP.
- Agents **monitor, propose, ask a human, then execute** via `execute_playbook` (approval hash,
  ownership, clone test, rule verdict checks). Playbooks PB-01..PB-09.
- KB = structured records (rule engine) + RAG (ChromaDB) over the same official sources.

## 4. Planning agents (all four DONE 7 Nov; merged draft: `docs/BUILD_PLAN_v2.md`, awaiting user approval)
Order: **run agent B first** (it decides the country), then A, C and D in parallel with B's result.
All four plan only and must not edit files. Give each: the jury rules above, this file,
`docs/BUILD_PLAN.md`, `kb/` and the CG dataset list.

| Agent | Model | Job |
|---|---|---|
| **B** (first) | Sonnet 5.5 | **Policy explainability + country.** Split what the AI can explain (which clause applies, deadline arithmetic, why a verdict, SHAP reasons, confidence, which evidence) from what humans must explain (legal interpretation of ambiguity, accountability, proportionality, final decisions, policy recommendations, ethics). Recommend the country with the clearest policy for NTN cyber security (keep India, or another), with official sources. |
| **A** | Sonnet 5.5 | **Role of each AI agent and model in detail.** For each: everyday job (not only in a crisis), inputs, outputs, tools, decisions it may and may not take, the human it reports to, its part in self-healing after an attack. |
| **C** | **Codex `gpt-6.1-sol`, medium effort** | **Datasets + build feasibility.** Pick the best datasets from the CG catalogue for this theme (candidates: #13 SDN intrusion and vulnerability, #49 network log anomaly, #33/#50 5G core failure/RCA, #18 KDDI failure classification, #52/#62 Turkcell RLF, #8 site power, #11 RAN KPIs, #75 DFS secure authentication, #74 RAG for public services, #6 TeleQnA), check accessibility, map each to an agent/model, re-plan a 3-day GitHub build under the new priorities. |
| **D** | Opus 5.5 | **5-page report + integration.** Page and figure budget per section; how to show "pillar of everyday work"; review A–C for conflicts and propose scope cuts. |

Codex command shape (read-only, saves the final answer to a file):
```
cd orca-ntn && codex --search exec -m gpt-6.1-sol -c model_reasoning_effort="medium" \
  -s read-only -C . -o docs/plan/C-datasets-build.md - < docs/plan/prompts/C.txt
```

After the agents: merge into `docs/BUILD_PLAN_v2.md`, give the user a short decision list, and
**build nothing until the user approves v2**. Ask before editing any .docx/.pdf.

## 5. State of the work
- Repo `orca-ntn/` (one commit 9e1ac47; `docs/plan/` and `docs/BUILD_PLAN_v2.md` untracked): KB v1 (23 records, 17 verified quotes,
  7 gaps), validator and tests pass, `docs/BUILD_PLAN.md`, `data/DATA_CARD.md` (v0),
  `data/research/01–03` + `VERIFIED.md`, `data/itu_p838_3_coefficients.csv`, Turkcell data in
  `data/raw/` (gitignored).
- Report `submission/ORCA-NTN-initial-report.docx` is currently **9 pages** and still tells the
  Rajasthan story: it must be cut to 5 and rewritten. Backups in `submission/.work/`.
- README and orca-ntn.html carry the technical figures, Qwen3.8 and LightGBM, but not Chennai,
  GNSS/SS7, minute-level M2 or the jury structure.

## 6. Still needed from the user
4 PDFs blocked for scripts (IT Act, Telecom Cyber Security Rules, DPDP Act, DPDP Rules) into
`orca-ntn/kb/sources/`; Google Cloud endpoint; GitHub account; team split; rural part yes/no;
cross-border partner (Sri Lanka?).
