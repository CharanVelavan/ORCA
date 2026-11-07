# ORCA-NTN build plan v2 (APPROVED by the user, 7 Nov 2026)

Written 7 Nov 2026 by merging planning agents A–D (`docs/plan/A-agent-roles.md`,
`B-policy-country.md`, `C-datasets-build.md`, `D-report-integration.md`; prompts in `docs/plan/prompts/`).
Supersedes `docs/BUILD_PLAN.md` (v1) where they differ; v1 §2–4 remain the design reference for
anything not changed here. **Nothing is built until the user approves this file.** Submission 10 Nov.

## 0. Inputs that drive v2
- Jury rules 1–7 (HANDOFF §1): report > code > video; **5 pages incl. images**; overview first, then each
  agent/model in detail; everyday use; **AI-vs-human explainability**; any clear-policy country; CG datasets.
- Rule 8 (judges, 7 Nov): any repo format, dashboard OK, **run instructions mandatory**, hosting on
  GCP/AWS OK, Pi 5 + STM32 OK.
- Rule 9 (user, 7 Nov): **the biggest win is finding policy gaps, analysing them and taking the required
  actions.** This is the headline.

## 1. Headline: the gap pipeline (D §1)
**Detect → Prove → Analyse → Act → Recommend.**

| Stage | Built as |
|---|---|
| Detect | Rule engine checks each fact set against **topic coverage** (`topics` on every KB record, `obligation_questions` on facts). No in-force binding record → POTENTIAL_GAP (existing `GAP-IN-xx` or new `GAP-CAND-<hash>`); two readings → AMBIGUITY; clashing lawful actions → CONFLICT. |
| Prove | Gap Analyst's logged `search_sources` over full texts of all sources (embedded ChromaDB). Stores date, sources checked, terms, **nearest provision + quote**, why it does not cover. Above a similarity threshold → "possible coverage: human check", no gap claimed. |
| Analyse | Impact and affected parties from the emulator's dependency graph; same topic looked up in **EU and UAE** profiles. |
| Act | Interim action through a fixed playbook, human-approved, run by `execute_playbook`. |
| Recommend | Drafted recommendation to the named regulator (DoT/TRAI, CERT-In, MeitY/DPB, ITU-T SG17); a human confirms `verified: true` and signs. |

Gap schema adds: `topic, status (candidate|confirmed), search{…}, analysis{impact, affected, comparison{EU, AE}},
interim_action{playbook, owner}, recommendation{regulator, ask}, verified_by`.

False-gap guards: nothing "confirmed" without a human-checked search record; **5 negative controls** that
must NOT become gaps (CERT-In (ii), (iii), (iv); Telecom Act s.2(s) "terrestrial or satellite networks";
UAE TDRA 112 priority); gaps resting on unopened sources stay `candidate`; wording "not found in the
sources we checked, as of <date>".

Register: GAP-IN-01..07 plus **GAP-IN-08** (no rule requires a clean backup path before failover during an
attack) and **GAP-IN-09** (2026 space framework's legal status not stated). Interim actions and
recommendation addressees per gap: D §1 table.

Judge-added scenario: dashboard inject panel (structured, or free text → LLM → facts shown for human
confirmation) runs the same generic path. Tested with **3 blind injects** written by a non-author.

## 2. Settled scope (changes from v1)
| Area | v2 |
|---|---|
| Country | **India primary + EU comparison + thin UAE profile** (2 new verified records: TDRA IAR v1.1 incident control, Decree-Law 46/2023 Art. 9). Cut Australia, rural part, Sri Lanka. (B, D §6) |
| Agents | One `Agent` class + 6 role YAML files + human commander. **Gap Analyst is the lead agent.** Regulator agent thin (receives recommendations); power agent template-driven; optional agents cut. Tools as A §1.1 + `search_sources`. Autonomy ladder A0–A3 (A §1.2). |
| Playbooks | 10 specs (PB-01..09 + **PB-10 warn dependent services**). **Executable: PB-01, PB-06, PB-10.** PB-05 defined for the S2 conflict (PB-05 vs PB-06). PB-09 only if time. |
| `execute_playbook` | Plan hash, expiry, owner, clone test, fresh verdict (never on VIOLATION, not even with human approval), one-time token. Audit is "tamper-evident". |
| M1 | Isolation Forest + window features. ECOD cut. |
| M2 | Physics minute estimate (P.838 fade vs margin from the extracted CSV). Learned tiers/conformal cut. |
| M3 | LightGBM + SHAP + calibrated abstain, **"5 causes + abstain"** (normal, fault-weather, fault-power/equipment, attack-jamming, attack-management-plane). GNSS/SS7 cut unless the generator already has them. |
| M4 | Greedy allocation; priority order is an input and always returns GAP-IN-03. MILP only if spare time. |
| Data | CG **#52 Turkcell** for M3 fault calibration (download script + checksums; no raw commit, no licence). #13 dropped. Synthetic generator: 6 sites, ~120 episodes, seeded, episode-level splits. |
| KB/RAG | Embedded ChromaDB with bundled embedder, 0.25 refusal, cite Layer-A ids only, `check_citations`. KB fixes from B: CERT-In `in_force_from` 2022-06-27; add `IN-TELACT-2023-2-s`; `verified:false` cannot give COMPLIANT/VIOLATION; `not_stated` → AMBIGUITY; "not legal advice" footer. |
| Transport | In-process event bus. MQTT only for Dubai. |
| LLM | **Qwen3.6-35B-A3B, GGUF IQ4_XS, llama.cpp on GCP Mumbai via Atlas tunnel `localhost:8000/v1`** (user, 7 Nov; replaces Qwen3.8-27B). Thinking **off** by default (`enable_thinking: false`); timestamps always from event facts. Smoke test 10/10 tool calls; full acceptance test on 9 Nov. Labelled `replay` mode for machines without the model. Report the exact model + quant used. |
| Dashboard | Streamlit, no logic in UI. Panels: everyday readiness, alerts + SHAP, verdicts + clocks, **gap card**, approval (name + PIN, hash, expiry), execution/rollback, audit replay, **inject + Reset**, KB swap. |
| Delivery | **Hosted dashboard on GCP (primary judge path)** + mandatory local `docker compose up` that works without our keys. CI on GitHub Actions; `README` "Run it" + `docs/RUN.md` (13 items, D §9); dry run 1 (9 Nov 20:00, non-author, fresh VM), dry run 2 (10 Nov, tagged release). Hosted demo dropped to local-only if GCP is not live by 9 Nov 18:00. |
| Hardware | Not in round 1. Dubai: Pi 5 edge/attacker with tc/netem, STM32MP135F-DK approval console, MQTT. |
| Readiness | Claim **6**: D3, D6, D7, D8, D10, D13 (+D4 if S3 runs). One gap in the Readiness 2.0 report itself. |

## 3. Scenarios (each ends in a gap; each also run with rules off)
S0 normal day (negative controls COMPLIANT, weekly gap review) · S1 Deepavali management-plane wipe +
jamming-forced failover (GAP-IN-01, -02 via PB-10, -08 via PB-06) · S2 PB-05 vs PB-06 conflict
(GAP-IN-03, -07) · S3 same incident under India / EU / UAE · Inject (judges' own). One canonical
timeline in `scenarios/s1.yaml`.

## 4. Report (5 pages; new file `submission/ORCA-NTN-report-v4.docx`, needs user OK)
Header 0.15 · Intro 0.40 (gap headline line with measured counts) · Use case 0.20 · Normal/bad day 0.25 ·
Roles of AI/agents/models 0.80 (Fig 1 with the gap lane + Table 2) · Explainability 0.30 · Requirements
0.20 · Y.3172/Readiness/policies 0.40 · Scenarios 0.70 (Fig 2 live gap card + results table) ·
**Gaps 1.25** · References 0.20. Details and honest-claims list: D §2, §10.

## 5. Protect / cut
**Never cut:** rule engine with topic-coverage gaps + tests; gap schema, search records, negative controls;
full-text RAG + `search_sources`; Gap Analyst; EU/UAE profiles + swap; guarded `execute_playbook` with
PB-01/06/10; audit chain; M1 + M3 with held-out results; dashboard gap card + inject; S0–S3 + rules-off +
blind injects; tested run instructions + CI; the 5-page report.
**Cut first:** QLoRA/TabPFN/ECOD → optional agents/extra countries → #13 → MQTT → GNSS/SS7 → learned M2 →
MILP → video polish → PB-09 → Turkcell daily experiment → hosted-demo polish → hosted demo.

## 6. Day plan: solo (Charan + Claude), revised 7 Nov
Charan works alone (no team members). Claude writes the code, tests and drafts; Charan does what only a
human can: decisions, approvals, legal/gap verification, blocked downloads, GCP, review, video, submission.
"Non-author" checks use a fresh Claude subagent that sees only the README (dry run) or only the scenario
format (blind injects), never the engine code. The LLM endpoint already exists (Charan provides the URL),
via **Atlas**: `localhost:8000/v1` is an IAP+SSH tunnel to a private Spot L4 VM in GCP asia-south1 (llama.cpp, `--200k` profile, 2 slots). No public IP, Spot, 6 h max runtime, so the **hosted judge demo uses labelled `replay` of runs recorded with this model**; live runs via Atlas for video/Dubai. Thinking off for routine agents (max_tokens ~1k); thinking on only for Gap Analyst prove/analyse/recommend and CONFLICT/AMBIGUITY drafts (max_tokens ~6k, ~45 s/call). Per-request context ~7–22k, well within 200k. Fallback: `atlas senior` (Qwen3.8-27B, vLLM). Never the uncensored mode.

| Block | Claude builds | Charan does | Gate (must pass) |
|---|---|---|---|
| **8 Nov AM** | KB fixes (B), gap schema v2, `topics` on records, 5 negative controls; rule engine (6 verdicts + topic coverage) + tests; audit chain | Approve v2; download 4 PDFs; give endpoint URL + key into `.env`; GitHub account | `pytest` green; all 6 verdicts + controls tested |
| **8 Nov PM** | UAE records (after Charan supplies/opens PDFs); full-text ChromaDB index + `search_sources`; search records for GAP-IN-01..09 (drafts); generator (6 sites, ~120 episodes, 5 causes); M1 + M3 baseline | **Verify each gap's search record** (human `verified: true`); check UAE quotes | Gap register v2 with human-checked records; M1/M3 train |
| **9 Nov AM** | `execute_playbook` + approval controls + PB-01/06/10 (+PB-05 spec); LLM client on the endpoint; 6 role agents; Gap Analyst prove/analyse/recommend | Spot-check agent outputs and citations | S1 runs end to end in CLI with real LLM |
| **9 Nov PM** | SHAP + abstain + held-out eval; M2 physics, M4 greedy; S0/S2/S3 + rules-off runs; Streamlit dashboard (gap card, inject, approval, audit); Dockerfile + compose + CI; `docs/RUN.md`; Cloud Run deploy | Try the dashboard; approve plans as the human commander; write 3 inject ideas | **Feature freeze 22:00.** Dry run 1 (fresh-subagent README test) |
| **10 Nov AM** | Final seeded runs → results table, Fig 1/Fig 2 assets; blind-inject test; citation eval; fix README from dry run | **Report v4 review** (Claude drafts the .docx after your OK); record 5-min screen video | Report exactly 5 pages; dry run 2 on tagged release |
| **10 Nov PM** | Final link checks, tag `v1.0-round1` | Push public, email submission **≥6 h before deadline** | Receipt saved |

Extra cuts because solo (before anything in §5's "cut first" list is touched): regulator and power
agents become thin template roles; Streamlit only (no FastAPI); video = one take of the dashboard with
subtitles, or screenshots (session 5 allows this).

## 7. Blockers (owner: user)
1. **4 blocked PDFs** (IT Act, Telecom Cyber Security Rules 2024 + 2025 amendment, DPDP Act, DPDP Rules)
   into `kb/sources/` by 8 Nov noon. Until then GAP-IN-01/-03/-05 stay candidate.
2. **LLM endpoint URL + key** (Charan has it; key goes only in `.env`) and a GCP project for Cloud Run.
3. GitHub account/org; repo must be public for judges.
4. Report header: solo entry (session 3: solo participants are fine). Confirm how to present Solar Sailors / Kaythry P.
5. Exact submission deadline and timezone.
