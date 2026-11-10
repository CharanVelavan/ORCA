# Report v4 plan (9 Nov 2026, IST)

Supersedes the page budget in `D-report-integration.md` §2 (rev 2, 7 Nov), which predates the build.
Status: **plan only.** No `.docx` is created or edited until Charan says so.

## 1. Hard rules (from the jury and the user)

- **Strictly 5 pages, images included.** Judged first: report > code > video.
- ITU template formatting: Times New Roman 12 pt, justified, template table style. Tables and captions 10 pt.
- **Six mandatory sections, used verbatim as the headings, in this order** (user, 9 Nov):
  1. Introduction (problem to be solved)
  2. Explain your solution
  3. Why is it novel, innovative
  4. Standards mapping e.g. ITU-T Y.3172
  5. Scenarios for demo
  6. Standards and policy gaps
  The template's other asks still appear, inside these sections: the "gaps in existing solutions" NOTE
  (§2), the per-node requirements (folded into the §4 table), the mapping table column order (§4).
  Every section must be present and visible. A missing one is a fail, so none is ever cut to save space.
- Plain words. Sentences of about 5–7 words.
- No overview of "AI agents". Explain each agent's role and each model's role.
- Say what the AI explains and what humans must explain.
- Headline = **policy gaps**: detect → prove → analyse → act → recommend.
- All links emulated. No real satellite or 3GPP connectivity claimed.
- Header: Solar Sailors; Charan Velavan (leader), Yogender Raju, Kaythry P; SSN College of Engineering;
  GitHub `github.com/CharanVelavan/ORCA`; KB `huggingface.co/datasets/CharanVelavan/orca-ntn-kb-v2`.

## 2. Structure and page budget (target 4.80; hard limit 5.00)

**5 pages total, everything inside it:** header, figures, tables, references. No appendix, no cover page,
no annex. The 0.20 buffer absorbs Word vs Chrome reflow. Page count is checked after every edit, on the
Word-exported PDF as the final judge.

About 470 words per full text page at 12 pt. Short sentences make it fewer words per line, so
budget about 400.

| # | Heading (verbatim) | Pages | Content | Figures / tables |
|---|---|---:|---|---|
| — | Header | 0.15 | Team, college, contact, GitHub, KB link, model link | — |
| 1 | **Introduction (problem to be solved)** | 0.40 | Chennai services ride satellite backhaul (112, UPI, hospital). KA-SAT pattern: VPN → management network → wipe, plus jamming forcing failover. "Nobody was told." Three reporting clocks. Then the headline line with measured numbers (§4). | — |
| 2 | **Explain your solution** | 1.35 | 2.1 What ORCA does, one paragraph, plus the NOTE: which gaps of existing tools it closes. 2.2 Normal day vs bad day (pillar of everyday work). 2.3 Role of every component. 2.4 AI explains vs human explains. | **Fig 1** architecture (0.40), **Table 1** components (0.45), **Table 2** explainability (0.25) |
| 3 | **Why is it novel, innovative** | 0.30 | Five novelty claims (§3 below), one short paragraph each, each pointing to repo evidence. | — |
| 4 | **Standards mapping e.g. ITU-T Y.3172** | 0.60 | Template table, column order: node \| use case (actual component and data) \| key requirement \| Readiness 2.0 \| documents. SRC, C, PP, M, P, D, SINK. Claim only D3, D4, D6, D7, D8, D9, D10, D11, D13. | **Table 3** |
| 5 | **Scenarios for demo** | 0.70 | Three scenarios, step by step, each ending in a gap. One line on the judge-inject path. Measured results table. | **Fig 2** dashboard screenshot (0.30), **Table 4** results |
| 6 | **Standards and policy gaps** (headline) | 1.15 | Pipeline in 4 lines + false-gap guards. Gap register. Two rejected gaps as proof of rigour. Standards gaps. UAE host paragraph. | **Table 5** gap register (0.70) |
| — | References | 0.15 | About 14, numbered, 10 pt, one line each | — |
| | **Total** | **4.80** (+0.20 buffer = 5.00) | | 2 figures, 5 tables |

If it overflows: (1) shrink Fig 2 to a crop of the gap card; (2) merge Table 2 into Table 1 as a column;
(3) cut 2.2 to three rows. Never cut §6.

## 3. Content decisions

### 2.3 Table 1: one row per component (role, input, output, what it may not do)
Rule engine (P node, deterministic, six verdicts with KB ids) · M1 anomaly · M2 minute forecast ·
M3 fault-or-attack (8 classes, abstains) · M4 MILP capacity allocator · RAG (cites chunk ids) ·
8 roles: mobile operator, satellite operator, power utility, CERT-In, regulator, policy adviser,
Gap Analyst (most detailed row), commander (human). Last column: "can execute?" Only owners, only
approved playbooks, only with a hashed, time-limited human token.

### §3 Novelty (five claims, each backed by something in the repo)
1. Fault-or-attack decides the legal regime, so M3 feeds the rule engine directly.
2. Gaps are found live and proven with a search record (sources checked, nearest clause, why it fails).
3. Fixes are config-as-code: diff, clone test, 5→25→100% rollout, auto-rollback, re-attack check.
4. Failover checks that the backup path is clean first (failover is an attack path).
5. A deterministic rule engine with an LLM on top. Measured: rules on vs off (§4 numbers).

### §5 Scenarios (pick three; all exist in `scenarios/`)
| Scenario | Story | Ends in |
|---|---|---|
| **S1** | Management-plane wipe of Chennai terminals | GAP-IN-02 (no downstream warning) + PB-10 warn dependents |
| **S3** | Cell heals itself without trusting the backup | GAP-IN-08 (no clean-path check) + PB-06 |
| **N5** | One incident, several reporting clocks | GAP-IN-01 (three clocks, two triggers); earliest-deadline rule |
Plus one line: judges can inject their own scenario through the live dashboard.
S2 (storm, M4 keeps 112 and the hospital served) goes in as one sentence under S3 if space allows.

### §6 Gap register (Table 5): the 7 confirmed gaps
GAP-IN-01 clocks · 02 no downstream warning · 03 no priority ranking for backup capacity ·
04 no battery floor · 06 feeder-link / ISL standards · 08 no clean-path check · 09 space cyber advisory only.
Columns: Gap | Evidence and nearest provision | Who is hurt | EU / UAE comparison | Interim action (PB) |
Recommendation → regulator (draft, human-signed).
Then one line: **GAP-IN-05 and GAP-IN-07 were rejected** after review. GAP-IN-05: the DPDP breach
clock exists but starts only about May 2027, a transition period, not an absent law. GAP-IN-07: reframed
as an ambiguity, since s.70B(6) gives a direction power and an SOP covers man-made disasters; the
Disaster Management Act 2005, the national CCMP and the NCIIPC rules were not searched. Rejecting our
own candidates shows the guard works. (Source: `kb/gaps/india.yaml`, `notes`.)

## 4. Numbers the report may cite (all measured, source files in the repo)

| Claim | Number | Source |
|---|---|---|
| Gaps found, rules on vs off (tuned Qwen, 10 scenarios) | **40/40 vs 0/40** | `docs/research/atlas-runs/compare-qwen-ft.md` |
| Playbooks executed by an agent without a human token | **0** in all recorded runs | same |
| Fine-tune, 300 held-out cases: tool choice | 0.557 → **0.930**; unsafe executions 3 → **0** | `models/llm/qwen-ft/NOTES.md` |
| Safety probe: fake-token prompts | tuned Qwen tried `execute_playbook` 2/16 times. **The gate is the safety layer, not the model.** Confirm the gate refused both before citing. | `docs/research/atlas-runs/ood-probe/REPORT.md` |
| M1 (held-out harder) | ECOD AUC 0.988; false alarms 2.3% | `orca/models/metrics.json` |
| M3 (held-out harder) | accuracy 0.971; selective 0.987; abstains 1.7% | same |
| M2 minute | MAE 4.31 min (physics 4.29); P10–P90 coverage 0.925 | same. **Say "matches physics, adds calibrated intervals".** |
| M4 | 112 and hospital fully served on 60 Mbps backup for 100 Mbps demand | same |
| RAG v2 default | recall@5 0.700; exact citation 5/5; 0 of 54 gap-evidence questions refused | `docs/KBVEC.md` |
| Incident timings (detect, notify vs 6 h, restore) | **pending**: being added by the other agent | — |

Do **not** cite: M3 in-distribution 1.0 (too clean, synthetic); M2 daily AUC 0.57 except as "real
failure prediction is hard" in one clause; any number not in a file above.

## 5. May claim / may not claim (updated from D §10)
- **Now allowed** (built since 7 Nov): fine-tuning (QLoRA Qwen3.6-35B-A3B, public GGUF); M4 MILP;
  M3 with GNSS and SS7 classes; M2 learned minute model; public KB on Hugging Face.
- **Still not allowed:** real attacks or real operator data; legal advice; "no such rule exists"
  (say "not found in the sources we checked, as of 7 Nov 2026"); DPDP clocks in force; all 13
  Readiness dimensions; hardware or MQTT as built; latency below 3 s for RAG.

## 6. Workflow and timeline

| When (IST) | Step | Who |
|---|---|---|
| 9 Nov, evening | Write `submission/REPORT-v4.md` in this structure, real numbers only | Claude |
| 9 Nov, evening | Render the Markdown to A4 with template-like CSS (TNR 12 pt) in headless Chrome; count pages; trim to 5.0 | Claude |
| 9 Nov, night | Charan reviews the draft and the page check | Charan |
| 10 Nov, morning | After Charan's OK: build `submission/ORCA-NTN-report-v4.docx` from a **copy** of the template; v3 and the template stay untouched | Claude, with approval |
| 10 Nov, ~11:00 | Drop in Fig 2 (final UI screenshot) and the incident timings from the other agent | Claude |
| 10 Nov, 13:00 | Word export to PDF, final page check, freeze | Charan |
| 10 Nov, 15:00 | Submit (deadline 19:30 IST planned; hard 01:30 IST 11 Nov) | Charan |

## 7. Open questions for Charan
1. Kaythry P: member or mentor? List as registered.
2. Fig 1: redraw the architecture for v4 (gap lane highlighted), or reuse `figures/` from v3?
3. Contact email in the header: which address?
4. Approve the workflow in §6, including the new `.docx` built from a template copy?
