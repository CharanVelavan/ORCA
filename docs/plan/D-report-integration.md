# D. Five-page report and integration plan, revision 2 (agent D, 7 Nov 2026)

**This replaces my earlier result in full.** It adds the user's two 7 Nov inputs:
1. From the judges: any repo format, a dashboard allowed, **run instructions mandatory**, hosting allowed, hardware optional.
2. From the user: **"the biggest win will be finding the policy gaps, analysing them and taking the required actions."** The gap pipeline is now the headline of the report, the demo and the build.

Plan only; no files created or edited. Sources read: HANDOFF, BUILD_PLAN, kb/ (gaps, record ids, AE record), A, B, C, the current report (via textutil: 2,608 words, 4 figures, 9 pages), the ITU template, charan/country-documents.md, sessions/README.md and the session 2 and 3 notes.

The session evidence behind the re-weighting:
- Gap analysis is "the most valued part" (S3).
- "Search hard before claiming a gap; judges once objected that a relevant document did exist" (S2).
- A gap that exists in one country but not another is welcome (S2).
- Missing cross-ministry policy is a reportable gap under D7 (S3).

---

## 0. Summary
- **The headline is the gap pipeline.** It has five stages: **Detect → Prove → Analyse → Act → Recommend**.
  1. **Detect.** The rule engine raises POTENTIAL_GAP, AMBIGUITY or CONFLICT live.
  2. **Prove.** A stored search record shows the gap is real: the sources checked, the nearest provision, and why that provision does not cover the case.
  3. **Analyse.** Impact, who is affected, and how the EU and UAE compare.
  4. **Act.** An interim operational action through an approved playbook, now.
  5. **Recommend.** A drafted recommendation to a named regulator, signed by a human.
- **The Dubai test.** A scenario the judges add can produce a **new candidate gap** through the same generic path, not a scripted one.
- **Report: 5.0 pages.**
  - The gaps section grows from 0.55 to **1.25 pages** and is announced in the Introduction.
  - Figure 1 is the architecture with the gap pipeline as its highlighted lane.
  - Figure 2 is a real dashboard screenshot of a live gap card.
  - The roles and explainability sections shrink but still meet jury rules 3 and 5.
- **What the build protects:** generic gap detection, gap records with search records, RAG over the full source texts, the Gap Analyst agent, the EU and UAE comparison profiles, the interim-action playbooks (PB-06, plus a new PB-10 "warn dependent services"), the gap and inject panels on the dashboard, negative controls, and fresh-machine run instructions.
- **What gets cut instead:** learned M2 tiers, the M4 MILP (greedy instead), GNSS/SS7, the optional agents, dataset #13, MQTT, polish on the hosted demo, and the video.

---

## 1. The gap pipeline (what is built and shown)

| Stage | What happens | Component | Artefact |
|---|---|---|---|
| **1 Detect** | Every fact set is checked against **topic coverage**, not only against hand-listed gaps. Each KB record carries `topics` (for example `incident_reporting`, `downstream_warning`, `capacity_priority`, `failover_path_security`, `backup_power`, `breach_notice`, `joint_command`). Facts from a scenario or judge inject carry `obligation_questions`, for example "must the satellite operator warn dependent services?". Outcomes: no in-force binding record covers the topic → **POTENTIAL_GAP (candidate)**; two readings → AMBIGUITY; two lawful actions clash → CONFLICT. | Rule engine (deterministic) | Verdict + topic + candidate gap id (`GAP-CAND-<hash>`) or existing `GAP-IN-xx` |
| **2 Prove** | The Gap Analyst runs a logged `search_sources` over **Layer B (full text of every source PDF/HTML, all jurisdictions)** with fixed query terms per topic. It returns the **nearest provision**. If similarity is above a threshold, the result becomes "possible coverage: human check" and no gap is claimed. Below it, a candidate gap is kept with its search record. | Gap Analyst agent + ChromaDB | `search` block: date, sources checked (ids + sections), terms, nearest provision quote, why it does not cover, KB "as of" date |
| **3 Analyse** | Impact (which services and dependents lose what, from the emulator's dependency graph). Who is affected (the gap's `affects` list). Comparison: the same topic looked up in the EU and UAE profiles. | Gap Analyst + rule engine on the swapped KBs | `analysis` block: impact, affected, `comparison: {EU: id or none, AE: id or none}` |
| **4 Act (interim)** | Each topic maps to an interim operational action from the fixed catalogue. The owner agent proposes it, a human approves it (hashed, time-limited), and `execute_playbook` runs it. | Owner agent + `execute_playbook` | Playbook run, audit entry, "interim measure for GAP-xx" |
| **5 Recommend** | A one-paragraph draft recommendation to the **named regulator** taken from the authority map (DoT/TRAI, CERT-In, MeitY/Data Protection Board, ITU-T SG17). Humans confirm the gap (`verified: true`) and sign. | Gap Analyst drafts; telecom regulator agent receives and logs it; human signs | `recommendation` block: addressee, ask, evidence ids, status `draft` → `human-approved` |

### Gap record schema (extends kb/gaps)
New fields: `topic`, `status` (candidate / confirmed), `search{date, sources_checked[], terms[], nearest_provision{record_or_source, pinpoint, quote}, why_not_covered}`, `analysis{impact, affected[], comparison{EU, AE}}`, `interim_action{playbook, owner}`, `recommendation{regulator, ask}`, `verified_by`.

### Guards against false gaps (the S2 penalty)
1. A gap is never "confirmed" without a human-checked search record.
2. A candidate gap is kept only below the coverage threshold, and the nearest provision is always shown.
3. **Negative controls.** The run includes cases where a rule *does* exist and must not become a gap:
   - log retention → Direction (iv)
   - point of contact → Direction (iii)
   - reporting to CERT-In → Direction (ii)
   - NTN coverage → Telecom Act s.2(s), "terrestrial or satellite networks"
   - 112 priority in the UAE profile → TDRA emergency clause

   The results table reports how many controls passed.
4. Gaps that depend on a source we have not yet opened stay `candidate`. Today that covers the Telecom Cyber Security Rules, the IT Act and the DPDP Act and Rules, whose PDFs are still blocked. So the user's 4 PDFs are now **on the critical path**: GAP-IN-01, -03 and -05 rely on them.
5. Wording is always "in the sources we checked (as of <date>)".

### Interim-action map
| Gap | Interim action now | Recommendation to |
|---|---|---|
| GAP-IN-01 three clocks | Protective filing at the **earliest** deadline (draft notices to CERT-In and DoT, which a human sends) | DoT + CERT-In: one trigger ("noticing" or "occurrence") and a single portal |
| GAP-IN-02 no downstream warning | **PB-10 (new, executable): warn dependent services** through the agent bus | DoT/TRAI (the space framework sits with CERT-In and IN-SPACe): a duty to warn dependents; comparison NIS2 Art. 23(2) |
| GAP-IN-03 no priority order | M4 operator table + PB-06 failover with 112 first | DoT/TRAI: a standing priority order; UAE TDRA covers emergency calls only |
| GAP-IN-04 no battery floor | PB-09 shed load (defined; executable only if time) | DoT/TRAI: a minimum autonomy figure; none found among the sources checked |
| GAP-IN-05 no breach clock today | Voluntary 72 h notice draft (marked voluntary) | MeitY / Data Protection Board: interim guidance before about May 2027; GDPR Art. 33 comparison |
| GAP-IN-07 no joint plan (D7) | The ORCA incident-commander role + shared audit log | CERT-In + DoT (+ NDMA, to check): a named cross-institution incident lead |
| **GAP-IN-08 (new): no rule requires the backup path to be verified clean before failover during an attack** | **PB-06's clean-path check** | DoT + ITU-T SG17: a security precondition for failover |
| **GAP-IN-09 (new): the 2026 space framework's legal status is not stated** (AMBIGUITY) | Treat its 6 h as binding for safety (protective filing) | CERT-In: state its status |
| GAP-IN-06 standards: feeder links out of scope (TR 33.700-29); no policy-as-code format | Our YAML format, published | 3GPP SA3 / ITU-T SG17; also note this is a gap in the Readiness 2.0 report |

GAP-IN-08 and GAP-IN-09 need their search records written before they are claimed: about 30 minutes each, mostly from B's findings.

### Judge-added scenario (Dubai, and the hosted demo for round 1)
- The dashboard **inject panel** has two modes:
  - structured: actor, asset, event, time, obligation question;
  - free text: the LLM maps it to structured facts, **shown for human confirmation** before the engine runs.
- An inject on a topic with no covering record returns a candidate gap and runs the full pipeline.
- Test it before 10 Nov with **3 blind injects written by a team member who did not build the engine**, for example:
  - a GNSS timing spoof that corrupts payment timestamps;
  - a hospital asking for priority over 112;
  - a satellite gateway located outside India that holds Indian logs.

  Record which ones produced a candidate gap and which hit a negative control.

---

## 2. Page and figure budget (template order; 4.9 + 0.1 buffer)

Body Times New Roman 12 pt (about 470 words per page). Tables and captions at 10 pt (decision 10).

| # | Section (FAQ letter) | Pages | Content | Figures / tables |
|---|---|---|---|---|
| — | Header | 0.15 | Team, leader, members, contact, **real GitHub link + hosted link** | — |
| 1 | Introduction (a) | 0.40 | 5 sentences: the idea, everyday satellite-backed services in Chennai, the KA-SAT pattern, the AI split. Then a **headline line**: "NTN has little cyber policy, so ORCA-NTN finds gaps live, proves them with a search record, acts on them now with an approved playbook, and drafts a recommendation to the named regulator. In our runs: N gaps (M confirmed, K new), with P/P negative controls passed." All links emulated. | — |
| 2.1 | Use case (b) + NOTE on gaps in existing solutions | 0.20 | Forced failover by jamming; nobody tells dependents; three clocks; fragmented evidence | — |
| 2.2 | Normal day / bad day (rule 4) | 0.25 | §3 below | Table 1 |
| 2.3 | Role of the AI and of each agent and model (rule 3) | 0.80 | Figure 1 = Y.3172 pipeline + agents + the **gap pipeline as a highlighted lane** (Detect → Prove → Analyse → Act → Recommend). Then Table 2, one row per component (rule engine, M1–M4, 6 agents, human); the Gap Analyst row is the most detailed. | **Fig 1** (0.4) + Table 2 (0.4) |
| 2.4 | AI explains vs humans explain (rule 5) | 0.30 | Lead + 6 rows (§4) | Table 3 |
| 3 | Requirements per node, graded critical / expected / added value (c) | 0.20 | Compact; "prove every gap with a search record" is a critical P-node requirement | Table 4 |
| 4 | Y.3172 + Readiness 2.0 + local policies (d, e, f) | 0.40 | Built components only; Readiness: the 6 evidenced dimensions (decision 8) | Table 5 |
| 5 | Scenarios, step by step, technical + policy (g) | 0.70 | Each scenario ends in a gap (§5) + the judge-inject line + a measured results table | **Fig 2** (0.3) dashboard gap card + Table 6 |
| 6 | **Policy and standards gaps (h): the headline** | 1.25 | (i) the pipeline in 4 lines + false-gap guards (0.15); (ii) **Table 7** gap register (0.75); (iii) standards gaps + one Readiness 2.0 report gap (0.1); (iv) a gap found live in a run, with its search record (0.1); (v) UAE host-country paragraph (0.15) | Table 7 |
| — | References | 0.20 | About 12 | — |
| | **Total** | **4.9** | | 2 figures, 7 tables |

**Table 7 columns (10 pt):** Gap | Evidence and nearest provision checked | Affected / impact | EU / UAE comparison | Interim action (PB) | Recommendation → regulator. Nine rows, terse cells. If it overflows, merge GAP-IN-04 into GAP-IN-03 and move GAP-IN-06 into prose.

**Figure 2:** a live gap card showing the verdict, KB ids, search record (nearest provision), comparison, the approved PB-10/PB-06 result and the drafted recommendation. It proves the pipeline runs.

**Moves to the README / `submission/TECHNICAL-REPORT.md`:** the O-RAN table, the view list, readiness.json ids, the full scenario list, PB-01..10 specs, model details, optional agents, MQTT design, the data card, B's full tables, A's timelines, C's dataset table, the full gap records with search logs (the KB is open), the judge Q&A and the run instructions.

---

## 3. "Pillar of everyday work" (rule 4)

Table 1: the same agents and models on a normal day and a bad day. Each row also names the gap it exposes, which ties rule 4 to the headline.

| Everyday user | Normal day | Bad day | Gap exposed |
|---|---|---|---|
| Card payments and ATMs | Dependency map; nightly MFA / stale-VPN sweep | M1 flags the login; PB-01; PB-10 warns dependents | GAP-IN-02 |
| Hospital / telemedicine | Backup-path hygiene check | PB-06 only onto a path verified clean | GAP-IN-08 |
| 112 | Standing capacity plan for event days (M4) | 112 first | GAP-IN-03 |
| Water / power utility | Battery autonomy watch | "Grid fault, not attack" evidence, which decides the clock | GAP-IN-01, -04 |
| Homes (satellite broadband / DTH) | M1 digest; a festival peak is not flagged | Staged rollout with auto-rollback | — |

Back it with a real `--scenario everyday` (S0, about 3 h).
- Its compliance sweep doubles as the negative controls: log retention and point of contact are COMPLIANT, not gaps.
- Its weekly **gap-register review** (Gap Analyst) is the everyday face of the headline.
- Only claim the everyday jobs that S0 actually runs.

---

## 4. Explainability split (rule 5): §2.4 + the gaps section

**Lead:** "The AI shows which clause applies, counts the hours, finds where the law is silent and shows its search. Humans decide what a vague clause means, whether a gap is real, what interim action is proportionate, and what to recommend to a regulator."

Table 3 (6 rows, cut from B's 11):

| Question | AI explains (artefact) | Human must explain (owner) |
|---|---|---|
| Which rule applies, and when is it due? | KB id, quote, binding status, ISO deadline arithmetic | The meaning of "noticing" vs "occurrence"; KB completeness (counsel; KB curator) |
| Fault or attack? | M3 class, confidence, SHAP, abstain reason | Whether to declare, report or attribute (CISO; national CERT) |
| **Is the law silent? (gap)** | Topic not covered; search record; nearest provision; EU/UAE comparison | **Whether the gap is real** (`verified: true`) (KB curator, counsel) |
| **What to do now?** | Interim playbook, clone test, rollout, rollback | Proportionality, approval, accountability (named approver) |
| **What should change?** | Drafted recommendation with evidence ids, addressed to the regulator | Whether to send it and what it asks (Gap Analyst lead, organisation; regulator decides) |
| Who is told, and was the AI right? | Draft notices; audit log; evaluation scores | Public communication; privacy (DPO); accountability for AI use (CISO) |

Footer: "rule-engine result on stated facts; not legal advice". The gap table's last column states "draft; human-signed" for every recommendation. The UAE AI Charter (non-binding; human oversight) may be cited without a year, because its year is unverified.

---

## 5. Scenarios (report §5), each ending in a gap

| ID | Scenario (Chennai, emulated) | Verdicts | Gap pipeline outcome |
|---|---|---|---|
| S0 | Normal day | COMPLIANT on the negative controls | The weekly gap review lists open gaps; no false gap |
| S1 | Deepavali evening: VPN → management-plane wipe of payment terminals, plus jamming that forces failover (traceability: "why did you fail over, who approved?") | INSUFFICIENT_EVIDENCE → AMBIGUITY (clocks) → POTENTIAL_GAP | GAP-IN-01 (protective filing), GAP-IN-02 (**PB-10** executed), GAP-IN-08 (**PB-06** clean check executed); recommendations to DoT/CERT-In |
| S2 | Conflicting recommendations: PB-05 isolate the management segment vs PB-06 keep 112 up via the same gateway | CONFLICT → POTENTIAL_GAP | GAP-IN-03 + GAP-IN-07; the commander decides; recommendation drafted |
| S3 | KB swap: the same incident under India / EU / UAE | Different clocks; EU Art. 23(2) duty; UAE: no numeric clock | The comparison column of every gap; one gap present in India but absent in the EU, as S2 welcomed |
| Inject | The judges' own scenario | Any | A new candidate gap, or a negative control |

Each scenario also runs with the rule engine off.

**Table 6 (measured, with run ids):**
- gaps detected (existing / new candidate)
- negative controls passed
- interim actions executed and rolled back
- citations valid (out of about 20 questions)
- unsafe actions and missed deadlines, rules on vs off
- blind injects that produced a gap

Report whatever the runs show; do not assume the ungoverned run fails (C's warning).

---

## 6. UAE (judges nominated by UAE authorities)

Name the UAE briefly, as evidence that the NTN cyber gap exists even in a host with strong telecom regulation. Not as a primary KB.

**Report §6(v), 3 lines.** "In the UAE sources we checked:
- TDRA's Information Assurance Regulation v1.1 requires incidents reported 'within specified timeframes' without a number;
- TDRA Interconnection Instructions v1.2 give emergency calls 'the highest priority' at points of interconnection [AE-TDRA-IC-2006-EMERGENCY] but rank no other services;
- the notification in Federal Decree-Law 46/2023 Art. 9 concerns space safety.

We found no public satellite-specific cyber-incident rule."

Do not cite the Cyber Security Council incident framework (unverified) or consultancy figures. Cite the IAR as v1.1: country-documents gives 2019, B gives March 2020.

**KB (about 2 h on 8 Nov).** Add the IAR PDF and hash it. Add 2 verified records: IAR incident reporting and Decree-Law 46/2023 Art. 9. The repeal status of the old space law is unverified, so quote only the text. Then fill the `AE` value in each gap's comparison field. S3 shows three columns.

---

## 7. Conflicts between A, B, C and BUILD_PLAN, with resolutions

| # | Topic | Conflict | Resolution |
|---|---|---|---|
| 1 | Page limit | BUILD_PLAN row 9 says no limit | 5 pages strictly; mark row 9 superseded |
| 2 | Headline | BUILD_PLAN, A and C centre on self-healing and response; the user now centres on gaps | The gap pipeline is the headline. Self-healing is the "Act" stage (interim actions) and the evidence. |
| 3 | Gaps as static records | The KB has 7 hand-written gaps, POTENTIAL_GAP only returns these, and there is no search record | Topic-coverage detection + candidate gaps + search, analysis, action and recommendation fields (§1) |
| 4 | Agent count | A: 6 + human + 3 optional, merge the regulator into the Gap Analyst; C: 6 "liaison" roles | 6 role files on one `Agent` class + the human. **The Gap Analyst becomes the lead agent.** The regulator agent stays a separate thin role file, because it receives and logs recommendations. The power agent is template-driven. All optional agents are cut. |
| 5 | Playbooks | A and BUILD_PLAN: 9; C: PB-01 + PB-06 | 10 defined. **Executable: PB-01, PB-06, PB-10 (new: warn dependents).** PB-05 is defined for the S2 conflict; PB-09 is executable only if time remains. |
| 6 | CONFLICT example | A, B and the old report differ | B's version: PB-05 vs PB-06 |
| 7 | Console | A: STM32; BUILD_PLAN: FastAPI; the judges: a dashboard is fine | A web dashboard with gap and inject panels; STM32 only in Dubai |
| 8 | M3 | 8 classes (BUILD_PLAN/A) vs 7 + abstain (C) | Wording: "N causes + abstain". **GNSS/SS7 are cut** for 10 Nov (5 causes + abstain) unless the generator already has them. |
| 9 | M2 | Learned minute + daily tiers vs C's cut | Physics minute estimate only. The Turkcell daily experiment moves down the cut list. |
| 10 | M4 | MILP vs C's cut | **Greedy allocation table** (its role is evidence for GAP-IN-03); MILP only if spare time |
| 11 | MQTT | BUILD_PLAN vs C | An in-process bus; MQTT for Dubai |
| 12 | RAG | C would cut ChromaDB for a simpler index | **Protected**: the Prove stage needs full-text search over every source. Embedded ChromaDB with the bundled embedder. |
| 13 | LLM | Qwen3.8 on GCP; C: unverified; B: logs in India | GCP asia-south1; local `ollama` / `replay` (labelled); report the model actually used |
| 14 | Country | B: India + EU; UAE not weighed | India + EU + a thin UAE profile; cut Australia, the rural part and Sri Lanka |
| 15 | Datasets | Jury rule 7; C: #52 + conditional #13 | #52 (Turkcell) for M3 fault calibration, plus the daily experiment if time. **Drop #13.** Download script, no raw-data commit (no licence). |
| 16 | Readiness | 9 claimed vs S3–S5 "4–5 evidenced" | **6: D3, D6, D7 (cross-institution gap GAP-IN-07, per S3), D8, D10, D13**; add D4 if S3 runs. Add one gap in the Readiness 2.0 report itself: no dimension for proving policy gaps or rules as code. Not "it ignores agentic AI", which S3 called too easy. |
| 17 | Blocked sources | HANDOFF lists 4 PDFs as "needed" | **Critical path**: GAP-IN-01/-03/-05 stay `candidate` without them |
| 18 | KB fixes | B: CERT-In `in_force_from` = 2022-06-27; `IN-TELACT-2023-2-s`; `verified:false` guard; `not_stated` → AMBIGUITY | Apply on 8 Nov; s.2(s) is also a negative control |
| 19 | KB id | A cites `IN-ITACT-2000-70B(6)` | Use `IN-ITACT-2000-70B` |
| 20 | Timeline | A 19:42 vs B 19:02 | One scripted `scenarios/s1.yaml` |
| 21 | Approval first | HANDOFF: build nothing until v2 is approved | The user approves on the morning of 8 Nov |
| 22 | Judges run code | Earlier assumption was that nobody runs it | Superseded (§9) |
| 23 | Header | Kaythry listed as "Mentor" vs member; GitHub placeholder | Decision 9 |
| 24 | Stale state | HANDOFF says "no commit yet" | Commit 9e1ac47 exists; docs/plan/ is untracked |

---

## 8. Protect vs cut in the 3-day build

**Protect (never cut):**
1. The rule engine: six verdicts + **topic-coverage gap detection** + tests.
2. The gap schema + search records for all 9 gaps (human-checked) + **5 negative controls**.
3. Full-text RAG (ChromaDB) over all sources + the logged `search_sources` tool.
4. The Gap Analyst agent: prove, analyse, draft the recommendation. The regulator agent as the recipient.
5. The EU + UAE comparison profiles, plus the KB swap.
6. Guarded `execute_playbook` (hash, expiry, owner, clone test, verdict, one-time token) with **PB-01, PB-06, PB-10**.
7. Hash-chained audit log.
8. Trained M1 + M3 (5 causes + abstain), held-out results. M3's fault-then-attack switch drives the AMBIGUITY gap.
9. Dashboard: **gap card + inject panel** + approval + audit replay.
10. S0–S3 + rules-off runs + 3 blind injects.
11. Run instructions tested on a fresh machine + CI.
12. The 5-page report.

**Cut, in this order:**
1. QLoRA, TabPFN, ECOD, tuning.
2. Optional agents (customer, neighbouring CERT, data protection); Australia; the rural part; Sri Lanka.
3. Dataset #13 and other new datasets.
4. MQTT and multi-container setups.
5. GNSS/SS7 classes and scenes.
6. Learned M2 tiers and conformal calibration (physics estimate kept).
7. M4 MILP → greedy.
8. Video polish (a screen recording at most 1.5 h; screenshots if needed).
9. PB-09 execution.
10. The Turkcell daily M2 experiment (M3 calibration on #52 stays, so jury rule 7 is still met).
11. Hosted-demo polish, then the hosted demo itself if GCP is not live by 9 Nov 18:00 (local only).

**Freed time, about 15 h, goes to the gap pipeline:**

| Task | Hours |
|---|---|
| Search records (from B and country-documents) | 4.5 |
| Topic-coverage detection | 2 |
| Gap Analyst prove/analyse/recommend + `search_sources` | 3 |
| Comparison lookups | 1 |
| PB-10 | 1 |
| Gap card on the dashboard | 1.5 |
| Blind injects + negative controls | 1.5 |
| UAE records | 0.5 |

**Revised day plan** (3 people × about 8 h; roles as in the BUILD_PLAN suggestion):

| Day | Policy / gaps / execution (Charan) | Data / models (Yogender) | Report / dashboard / release (third member) |
|---|---|---|---|
| 8 Nov | KB fixes + UAE records 2 h; gap schema + search records 4 h; rule engine with topic coverage + tests 2 h | Generator (6 sites, about 120 episodes, 5 causes) 3.5 h; Turkcell adapter for M3 calibration 1 h; M1 + M3 baseline 3.5 h | Report v4 skeleton with gaps as the headline, at 5 pages, 4 h; full-text index build 2 h; CI + `docs/RUN.md` draft 2 h |
| 9 Nov | `execute_playbook` + PB-01/06/10 (+PB-05 spec) 4 h; Gap Analyst + `search_sources` + recommendation drafts 3 h; audit 1 h | SHAP + abstain + held-out evaluation 3 h; M2 physics + M4 greedy 2 h; S0/S1/S2/S3 wiring + rules-off runs 3 h | Dashboard (gap card, inject, approval, audit) 5 h; GCP VM + vLLM + deploy 3 h; **dry run 1 at 20:00, freeze** |
| 10 Nov | Blind injects + negative controls 2 h; citation evaluation 2 h; humans verify each gap 2 h; contingency 2 h | Final fixed-seed runs → Table 6 + Fig 2 2 h; retrain docs 1 h; video 1.5 h; contingency 2 h | Report final + page check 3 h; dry run 2 + hosted check 2 h; submit ≥6 h before the deadline, keep the receipt 1 h |

---

## 9. Hosted demo vs local setup (judges' answer)

### Recommendation
- **Primary for judges: a hosted dashboard on GCP asia-south1** (Mumbai, matching CERT-In Direction (iv) on logs). Judges click, run S1–S3, and try their own inject, which lets them see a gap surface before Dubai.
- **Mandatory fallback: local** (`docker compose up`, or pip), working **without our credentials** (`replay` mode, labelled).

### Hosted set-up
- One GPU VM running vLLM (Qwen3.8-27B), the app and Caddy HTTPS.
- Each browser session gets its own emulator instance; a Reset button; rate limits and a token cap.
- If the LLM is down, switch to a labelled replay with a red banner.
- Keys in env / Secret Manager only.
- Budget alert + uptime check. Keep it up through 18 Nov, ideally to 8 Dec; consider CPU-only replay between rounds. **Check the cost first.**

### Local modes
| Mode | Command | Needs | LLM |
|---|---|---|---|
| Quick | `docker compose up` → localhost:8501 | Docker, 8 GB RAM | replay unless Ollama is detected |
| Python | `python3.11 -m venv .venv && pip install -r requirements.txt && python run_demo.py --scenario all` | Python 3.11/3.12 | same |
| Local LLM | `ollama pull qwen2.5:14b`, `LLM_MODE=ollama` | 16 GB RAM | live |
| Team endpoint | `LLM_MODE=hosted` + `.env` | our key | Qwen3.8 |

Ship the pre-trained M1/M3 artefacts in the repo.

### What the run instructions must contain (`README` "Run it" + `docs/RUN.md`)
1. What is emulated.
2. The hosted link + "if it is down, use local".
3. Prerequisites: tested OS, versions, RAM, disk, ports.
4. A quickstart in ≤5 commands, with expected output.
5. How to run each scenario (and `--no-rules`) and what to look for, **especially the gap card**.
6. **How to add your own scenario and see whether it surfaces a gap:** the inject panel + a `scenarios/custom.yaml` template.
7. LLM modes, `.env.example`, what `replay` means.
8. Data: the Turkcell script + checksums + licence note; generator seeds; data card.
9. Retrain and evaluate, with expected metrics.
10. Tests: `pytest`, refusal tests, negative controls, `verify_audit`.
11. Output locations: audit log, gap register, recommendations, notices, `readiness.json`.
12. Troubleshooting (Apple silicon `libomp`, ports, RAM) + known limits.
13. Optional hardware.

### Testing on a fresh machine
- **CI from 8 Nov:** GitHub Actions runs `pytest` and `run_demo.py --scenario all --llm replay --headless --check` on ubuntu-latest. It asserts the expected verdicts, gaps and controls, and verifies the audit chain. Add a badge.
- **Dry run 1 (9 Nov 20:00):** a non-author follows the README word for word on a fresh GCP Ubuntu 24.04 CPU VM (empty clone, no `.env`). Fix the README, not the machine.
- **Dry run 2 (10 Nov morning):** on tag `v1.0-round1`, using a macOS arm64 laptop under a new user, plus WSL2 if available.
- **Hosted check:** an incognito window on a phone network. Run S1, run one blind inject, press Reset.
- Freeze the commit cited in the report and email; check every link.

### The dashboard in the plan
- Streamlit, no logic in the UI: it calls the same `orca` API as the CLI and tests.
- Panels: everyday readiness; alerts + SHAP; verdicts + clocks; **gap card (search record, comparison, interim action, recommendation)**; approval (name + PIN, hash, expiry); execution and rollback; audit replay; **inject + Reset**; KB swap.
- 5 h on 9 Nov and the polish on 10 Nov. It is also Figure 2 and the video footage.

### Hardware
- **Round 1: not worth it.** At most one README sentence; an optional 30-minute check that the image runs on the Pi 5.
- **Dubai: worth it**, built 11 Nov–7 Dec if shortlisted:
  - Pi 5 runs the emulator and attacker, with `tc/netem` jamming live;
  - the STM32MP135F-DK is the physical approval console (verdict, clock, gap alert, approve button);
  - MQTT returns for the Pi-to-laptop link.

---

## 10. What the report may claim honestly
**May claim, only if it ran, with run ids:**
- An emulated Chennai network. "All links emulated; no real satellite or 3GPP connectivity."
- The six verdicts with KB ids. The gaps detected live, with how many were confirmed by a human-checked search record and how many are new candidates. The negative controls that passed.
- Interim actions executed (PB-01/06/10) in the emulator. Recommendations drafted for named regulators and signed by humans.
- M1/M3 held-out results (synthetic attack classes labelled as such). M2 physics and M4 greedy as built.
- The LLM actually used.

**May not claim:**
- real attacks in datasets;
- legal advice or compliance clearance;
- "no such rule exists" (say "not found in the sources we checked, as of <date>");
- confirmed gaps that rest on sources we have not opened;
- the space framework as non-binding;
- DPDP clocks in force;
- all 13 Readiness dimensions;
- MQTT, O-RAN or hardware as built;
- fine-tuning.

---

## 11. Decisions for the user (recommended answer in bold)
1. **Gaps are the headline:**
   - gaps section 1.25 pages and announced in the Introduction;
   - Figure 1 with the gap lane;
   - Figure 2 a live gap card.

   → **Yes.**
2. **Gap schema + topic-coverage detection + a human-checked search record for every gap, plus 5 negative controls**; nothing is "confirmed" without them. Add GAP-IN-08 (backup path not checked during an attack) and GAP-IN-09 (space-framework status). → **Yes.**
3. **Download the 4 blocked PDFs** (IT Act, Telecom Cyber Security Rules 2024 + its 2025 amendment, DPDP Act, DPDP Rules) by **8 Nov noon**. GAP-IN-01/-03/-05 stay "candidate" until then. → **Yes, do it first.**
4. **Country:** India primary + EU + a thin UAE profile (2 new verified records); the comparison feeds every gap row; cut Australia, the rural part and Sri Lanka. → **Yes.**
5. **Playbooks:** 10 defined; PB-01, PB-06 and the new PB-10 "warn dependents" are executable; PB-05 is defined for the S2 conflict. → **Yes.**
6. **Model scope:**
   - M3 = 5 causes + abstain (cut GNSS/SS7);
   - M2 = physics estimate;
   - M4 = greedy;
   - #52 used for M3 calibration;
   - cut #13.

   → **Yes.**
7. **Hosting:** GCP asia-south1 dashboard as the primary judge path; local `docker compose up` with labelled `replay` as the mandatory fallback; CI + two fresh-machine dry runs + 3 blind injects. GCP access is needed by **8 Nov 12:00**. → **Yes.**
8. **Readiness claims:** D3, D6, **D7**, D8, D10, D13 (+D4 if S3 runs) + one gap in the Readiness 2.0 report itself. → **Yes.**
9. **Header:** is Kaythry P a member or the mentor? Add the real GitHub and hosted links. → **List her as she is registered.**
10. **Report file:** body 12 pt, tables 10 pt, 2 figures. Write it as a **new** `submission/ORCA-NTN-report-v4.docx` from the template; v3 and the template stay untouched. CLAUDE.md requires your OK before anyone creates or edits the .docx. → **Approve.**
