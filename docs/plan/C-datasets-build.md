| CG catalogue dataset | Decision and ORCA-NTN use | Size and format | Licence / reuse status | Accessibility checked 7 Nov 2026 |
|---|---|---|---|---|
| **#52 — Radio Link Failure Prediction, Turkcell**. [Official repository](https://github.com/Turkcell/ITU-AIMLin5GChallenge-2021) | **Core choice.** Real-data anchor for **M1** daily anomaly experiments, **M2** daily risk if retained, and calibration of synthetic fault behaviour used by **M3**. Feeds mobile/satellite operator assessments. These are terrestrial microwave backhaul measurements, not satellite cyberattack observations. | Local training archive approximately **22 MiB**; test archive approximately **19 MiB**. Nested archives contain six TSV tables and an XLSX example. Locally recounted `rl-kpis.tsv`: **1,992,986 daily rows**, **3,465 links**, **1,674 sites**, **1,219 RLF positives**, 2018-12-31–2020-12-25. KPI TSV is **234,734,782 bytes**. | No explicit dataset licence established from the inspected repository; its README invites research use and requests citation. **Do not label the data MIT merely because ORCA’s code is MIT.** Publish acquisition instructions and derived results; clarify redistribution rights before including raw records. | **VERIFIED locally:** archive and extracted TSV files present and readable; full KPI row count reproduced. Official repository also reachable. |
| **#13 — Intrusion and Vulnerability Detection in Software-Defined Networks (SDN)**. [Public Zenodo deposit](https://zenodo.org/records/15303565), linked by the [ITU challenge solution repository](https://github.com/ITU-AI-ML-in-5G-Challenge/sotirischatzimiltis_sdn_ids) | **Best additional cyber dataset; conditional choice.** **M1** benign-flow anomaly benchmark; separate **M3** intrusion benchmark and attack-feature research. Supports monitoring agents’ evidence. Its attack taxonomy does **not** establish GNSS spoofing, RF jamming, SS7 attacks or satellite management-plane compromise. | Deposit lists approximately **2.3 million records**, **78 features**, benign plus 14 attack types. Four CSVs total **983.7 MB**: `train_data.csv` 155.5 MB; `test_data.csv` 44.6 MB; `Train_ULAK.csv` 608.8 MB; `Test_ULAK.csv` 174.8 MB. | **UNVERIFIED licence.** The rendered Rights section did not expose a licence identifier; metadata API/export attempts failed. Do not infer CC BY from Zenodo defaults. | **VERIFIED deposit and file listing; UNVERIFIED completed download.** Direct CSV download timed out. Important update: the February catalogue’s “not available” note is stale; this public deposit was published in April 2025. |
| **#50 — Network failure detection and root cause analysis in 5GC by NFV-based test environment**. [ITU solution and preprocessed-data description](https://github.com/ITU-AI-ML-in-5G-Challenge/ITU-ML5G-PS-015-Network-failure-detection-in-5GC-team-YOTA-YOTA) | **Reserve fault benchmark.** Separate **M1/M3 evaluation** of lab-injected faults; useful to challenge “every anomaly is an attack.” Prefer its preprocessed files over rebuilding the original 5GC pipeline. Do not equate a lab network fault with a cyberattack. | Original dataset **73 GB**, according to the solution README. Preprocessed `ap_data` contains numeric `.txt` feature/label pairs for three tasks. One fetched training-label file has approximately **93,505 lines**; corresponding feature response exceeded the browser tool’s **4 MiB** limit. Full processed size not established. | Explicit data licence **UNVERIFIED**. A public solution repository does not establish permission to redistribute the original challenge data. | **VERIFIED partial data access:** a [raw label file](https://raw.githubusercontent.com/ITU-AI-ML-in-5G-Challenge/ITU-ML5G-PS-015-Network-failure-detection-in-5GC-team-YOTA-YOTA/main/ap_data/01_a_train_label.txt) was readable. Feature endpoint responded but was too large for the tool. Original challenge download **UNVERIFIED**, returning 502. |
| **#8 — Smart Energy Supply Scheduling for Green Telecom**. [Challenge data page](https://zindi.africa/competitions/smart-energy-supply-scheduling-for-green-telecom/data) | **Optional power calibration.** **M2** battery/exposure estimates; **M3** power-fault evidence; **M4** energy constraints and PB-09 inputs. Useful for routine operations, but not required for the core management-plane scenario. | Page lists `trainData.zip` **321.5 KB**, `SampleSubmission.csv` **170.2 KB**, and Python metric script **7.9 KB**. Site/grid configuration, hourly solar and hourly consumption data. Internal training-file formats not inspected. | Zindi/challenge terms apply; an open dataset licence was **not verified**. Capture the actual terms before use or redistribution. | **VERIFIED page and file listing; UNVERIFIED data download.** Page exposes sign-in/accept-terms flow. |
| **#11 — RAN KPI data / Fault Impact Analysis**. [Challenge data page](https://zindi.africa/competitions/fault-impact-analysis-towards-service-oriented-network-operation-maintenance/data) | **Defer.** Potential **M1/M3 fault-impact evaluation** and service-impact inputs for **M4**. Less useful than local Turkcell data within three days because access may require team approval. | More than **100 network elements**, hourly KPIs, fault duration and adjacency. Page lists `validation_clean.rar` **10.4 MB** and sample CSV **25.4 KB**. Full training size/internal format unknown. | Challenge-specific terms; explicit open licence **UNVERIFIED**. | **VERIFIED page; UNVERIFIED dataset access.** Instructions require ITU registration, team creation and approval before download activation—not merely a Zindi login. |
| **#6 — Specializing Large Language Models for Telecom Networks / TeleQnA**. [Challenge data page](https://zindi.africa/competitions/specializing-large-language-models-for-telecom-networks/data) | **Optional agent evaluation only.** Small telecom-knowledge check for the shared LLM used by agents. Do not use it to validate legal reasoning, execute permissions or country policy. No fine-tuning before submission. | Challenge subset: **1,827 MCQs**, split **1,461 training / 366 test1**. JSON-style records in TXT: training **1 MB**, testing1 **177.5 KB**; additional questions **867.7 KB**; answer mapping CSV **19.8 KB**. Optional `rel18.rar` technical corpus **824.4 MB**. | Challenge subset terms apply; explicit open licence **UNVERIFIED**. Do not silently substitute a differently licensed/full TeleQnA release and describe it as the exact challenge subset. | **VERIFIED page and file listing; UNVERIFIED download.** Sign-in/terms gate. Test1 lacks answers/explanations, so locally scored evaluation requires a labelled holdout. |
| **#74 — ‘AIntuition’: RAG for Public Services and Administration**. [Challenge data page](https://zindi.africa/competitions/retrieval-augmented-generation-rag-for-public-services-and-administration-tasks/data) | **Method/evaluation reference; optional benchmark.** Feeds **RAG/evaluation**, not the deterministic rule engine. **[COUNTRY]** Runtime policy retrieval must use the selected country’s official KB sources, not unrelated administrative documents. | Page lists `Test Documents.zip` **3.5 MB**, reference XLSX **22.7 KB**, `Test.csv` **1.5 KB**, and webinar PDF **2.1 MB**. Internal document mix not inspected. | Page permits appropriate open datasets or custom curation, but this does not grant a blanket licence over linked legal libraries. Benchmark-file licence **UNVERIFIED**; source-specific rights remain relevant. | **VERIFIED page and file listing; UNVERIFIED archive download.** The catalogue entry is partly a RAG task/resource collection, not a ready-made NTN policy corpus. |
| **#49 — Network anomaly detection based on logs**. [Original challenge](https://challenge.aiforgood.itu.int/match/matchitem/33), [ITU solution repository](https://github.com/ITU-AI-ML-in-5G-Challenge/cdacHyd) | **Reject as a delivery dependency.** Excellent conceptual match for management-log **M1**, but no usable challenge corpus was confirmed. Use synthetic management logs instead. | Catalogue describes timestamped text logs, labelled training data and unlabelled test data. Exact challenge corpus size unknown. | Licence **UNVERIFIED**. | **UNVERIFIED dataset access.** Original page could not be fetched; solution code reachable, dataset not confirmed. An [ITU research paper](https://www.itu.int/dms_pub/itu-s/opb/jnl/S-JNL-VOL3.ISSUE2-2022-A20-PDF-E.pdf) also notes confidentiality restrictions for its studied corpora; do not assume those are downloadable challenge files. |
| **#33 — Network failure prediction on CNFs 5GC with Linux eBPF**. [ITU solution repository](https://github.com/ITU-AI-ML-in-5G-Challenge/ML5G-PS-005_MLAB-NFP) | **Defer.** Potential **M2/M3 evaluation** of precursor faults. More instrumentation and feature work than the deadline allows. | Multivariate cAdvisor/eBPF/5GC metrics; solution describes **3,326 metrics** and prediction of registration failures at a ten-minute horizon. Dataset byte size and downloadable archive format unknown. | Licence **UNVERIFIED**. | **VERIFIED solution code; UNVERIFIED dataset access.** Original challenge URL returned 502; no working data archive established. |
| **#18 — KDDI network failure classification using a network digital twin**. [Original challenge](https://challenge.aiforgood.itu.int/match/matchitem/84) | **Defer.** Good **M3 fault-classification** concept; unsuitable as a critical-path dependency without files. | Catalogue reports two lab mobile-core domains, five injected failure types across three VNF types, **16 labels including normal**; CPU, memory and traffic metrics. Size/format unknown. | Licence **UNVERIFIED**. | **UNVERIFIED dataset access.** Catalogue supplies a contact rather than a download; live challenge fetch timed out. |
| **#62 — Using Weather Info for Radio Link Failure Prediction**. [Catalogue download URL](https://mylifebox.com/sharedFiles?publicToken=5f19ec92-da0e-4ab3-bf80-b40817d276a0&language=en) | **Do not count as a second acquired dataset.** Related Turkcell challenge lineage for **M2/fault calibration**. Use #52’s confirmed local archive; establish identity before claiming #62 coverage. | Catalogue describes anonymised RL KPIs and hourly weather. Exact archive size/version unknown. | Licence **UNVERIFIED**. | **UNVERIFIED original download:** Lifebox URL was inaccessible through the browser tool. Local #52 availability does not prove this link or version works. |
| **#75 — ITU Digital Financial Services Blockchain Secure Authentication Application**. [Challenge resource page](https://zindi.africa/competitions/itu-digital-financial-services-blockchain-secure-authentication-application-challenge/data) | **Exclude as a training dataset.** Useful context for everyday payment continuity and authentication, but no established **M1–M4** training role. Do not add a wallet/blockchain integration. | SDK guides, server-provisioning documentation, APK/manual and presentation resources. No labelled authentication telemetry corpus established; dataset size not applicable. | SDK/service terms would need separate inspection; no dataset licence established. | **VERIFIED resource page; UNVERIFIED usable training dataset.** Documentation availability is not evidence of an authentication dataset. |
| **#15 — Network Traffic Scenario Prediction** — additional candidate. [Challenge data page](https://zindi.world/competitions/network-traffic-scenario-prediction-challenge/data) | **Optional benign-load benchmark.** **M1 evaluation** against ordinary changing traffic; possible **M4** demand-pattern research. Lower priority than #13 and #52. Traffic scenarios are not attack ground truth. | **78 training / 19 test scenarios**. `Train_data.zip` **83 MB**, `Test_data.zip` **19.9 MB**, variable-definition TXT **572 B**. Inner data format not verified. | Challenge terms; open licence **UNVERIFIED**. | **VERIFIED page and file listing; UNVERIFIED archive download.** Sign-in/terms flow. |
| **#51 — Network resource allocation for emergency management based on closed-loop analysis** — additional candidate. [Challenge resources](https://github.com/ITU-build-a-thon/challenge-resources) | **Architecture reference only.** Supports **M4** and closed-loop evaluation design. It is not a substitute for a measured demand/capacity dataset. | Public repository lists three PDF resources; no training corpus established. Dataset size not applicable. | Resource/document reuse terms **UNVERIFIED**. | **VERIFIED resource repository; UNVERIFIED numerical dataset.** |

**Verification scope.** “VERIFIED” above states exactly what was observed: local records, a readable file, or a reachable page/listing. It does not imply a completed download, an approved account or redistribution permission. No dataset was downloaded or saved during this planning task. Several Zindi URLs redirect to `zindi.world`.

**Recommended submission data stack:** #52 as the guaranteed real-data anchor; #13 as the first conditional addition; a clearly documented synthetic NTN dataset for the missing attack, approval and healing evidence. Time-box all new acquisition/licence work to **two person-hours on 8 November**. Do not make submission depend on provider replies.

## Build plan: 8–10 November

### Feasibility and inspected starting point

A defensible prototype is feasible for three people if the team builds **one complete, guarded response loop** and protects report time. The full `BUILD_PLAN.md` architecture is too large for the available three days.

The inspected repository contains:

| Area | Actual state on 7 November | Planning implication |
|---|---|---|
| `orca/kb.py`, `tools/validate_kb.py`, `tests/test_kb.py` | Functional loader/validator; **23 records, 17 verified quotes, seven gaps, 12 sources**. Validator passes; **three tests passed** when rerun without bytecode/cache writes. | Preserve this foundation. Existing tests validate KB structure and selected dates/triggers, not the complete operational policy engine. |
| `orca/rules.py`, `audit.py`, `remediation.py`, `agents.py`, `llm.py` | Docstring placeholders. | These are implementation tasks, not integration-only tasks. |
| `orca/models/`, `orca/sim/` | Package placeholders. | No trained M1–M4 or generator exists yet. |
| `run_demo.py` | Loads/validates KB and explicitly prints “pipeline not built yet.” | CLI is the fastest route to the first working demo. |
| `rules/`, `scenarios/` | No substantive implementation found. No implemented playbook catalogue found. | Create only the rules/scenario/playbooks necessary for the core path first. |
| `kb/sources/` | **Eight downloaded official sources** present, including PDFs and EU HTML. Four sources remain unhashed/missing according to the manifest. | **[COUNTRY]** Build retrieval from existing verified records/source excerpts; recover additional documents only where needed for chosen claims. |
| `data/` | Turkcell extracted locally; P.838 coefficients and research notes present; data card remains v0. | Real data is available, but synthetic data generation and provenance remain to be built. |
| Git/deployment | Initial commit exists. Compose references the unfinished demo and unpinned/latest components. | Establish a reproducible Python path first; container polish is secondary. |

The four missing source entries are the IT Act, Telecom Cyber Security Rules, DPDP Act and DPDP Rules. **[COUNTRY]** Their absence should restrict which claims receive source-backed retrieval; a stored hash or `verified: true` flag alone is not a substitute for an inspectable source.

### Synthetic data still required

No verified candidate above supplies the complete joint observation needed for NTN attack diagnosis and safe healing. The data card must distinguish **observed**, **physics-derived**, **calibrated**, and **assumed** values.

| Synthetic component | Why it remains necessary | Minimum implementation |
|---|---|---|
| Satellite-backed topology and service dependencies | Turkcell does not identify satellite gateways, management ownership or dependent payment/hospital services. | Six sites, one satellite gateway, one primary and one clean backup path; explicit owner/dependency graph. **[COUNTRY]** Geographic labels and service examples follow B’s country choice. |
| Management-plane compromise | Flow intrusion labels do not supply authenticated sessions, change tickets, configuration changes and their effects on terminals. | Normal maintenance versus unauthorised login/configuration change, followed by service loss. Include MFA result, source category, ticket match, command outcome and configuration drift. |
| RF/weather and power counterexamples | Daily Turkish microwave data cannot provide ten-second NTN fault/attack ground truth. | Rain-fade, equipment/power-fault and jamming episodes with explicitly assumed parameters. Do not present Turkish rainfall distributions as local climate calibration. |
| GNSS and signalling | None of the confirmed files establishes these proposed classes. | Minimal receiver/signalling feature generators plus hard ambiguous cases; label these classes as synthetic research coverage. |
| Human approval and remediation | Training datasets do not contain ORCA ownership, approval, rollback or verification events. | Expired, altered, replayed and wrong-owner approvals; clone failures; successful repair; failed verification and rollback. |
| Capacity/service impact | M4 is an optimiser, not a trained predictor; measured service demand and satellite capacity are absent. | Small assumed demand/capacity table. **[COUNTRY]** Service priorities are an explicitly approved operating policy unless B establishes applicable legal requirements. |

A manageable initial dataset is **140 episodes: 20 per substantive class**, each 20 minutes at ten-second intervals across six sites—approximately **100,800 site-time rows**, before separate event logs. This is a proposed engineering budget, not an existing dataset.

Resolve the current “eight-class” terminology precisely: **M3 has seven substantive classes plus an abstention outcome**. Train seven classes; use confidence/evidence rules to produce `abstain`. Abstention is not an eighth physical cause.

For evaluation:

- Split by **whole episode**, holding out generator settings and event families; never randomly split adjacent telemetry rows.
- Keep a small additional suite with unseen site identities.
- Exclude labels, root-cause fields, scenario IDs and future measurements from features.
- For Turkcell future-risk experiments, use only measurements available before the prediction horizon. Do not use same-day failure-derived counters as if they predicted that same day’s failure in advance.
- Report real-data and synthetic-data results separately. Different feature spaces require separate adapters/experiments; do not concatenate SDN flows, daily microwave rows and ten-second satellite features into a supposedly homogeneous dataset.
- Turkcell supplies **RLF versus non-RLF**, not verified weather-versus-power-versus-attack causes. Do not relabel every RLF as `fault-weather`.

### Minimum viable demonstration

**[COUNTRY]** Use the current Chennai payment-connectivity story provisionally; swap geographic labels and the jurisdiction profile after B reports.

The demonstration should begin with routine work: a readiness summary identifies overdue maintenance, configuration drift, current anomalies and which services depend on the satellite path. A legitimate maintenance burst should be shown as a counterexample.

The incident then follows one complete path:

1. Replay a seeded management-plane compromise affecting the satellite-backed service.
2. **M1** detects unusual behaviour using observed window features.
3. **M3 LightGBM** assesses the cause, supplies confidence and SHAP feature contributions, or abstains.
4. Operator agents retrieve evidence and propose fixed playbooks. The deterministic **P node** returns scoped verdicts with KB IDs.
5. **[COUNTRY]** Show applicable reporting triggers and deadline arithmetic separately from ML confidence. A model score must not silently establish legal applicability or reset a clock.
6. Run the proposed action in a cloned simulator state.
7. Show the exact plan, targets, owner, evidence and expiry to a human.
8. The authorised owner agent calls `execute_playbook` using the issued approval token.
9. Verify restored service and replay the attack against the repaired clone. If verification fails, roll back.
10. Verify the audit chain and produce a readiness/result summary plus draft notices.

Implement **PB-01 and PB-06 first**: disable the compromised management identity, then restore service through a backup path verified clean. Each owner approves/executes its own action. Remaining playbooks can remain documented future work.

Required execution controls:

- Canonical plan hash covering playbook, targets, parameters and relevant configuration version.
- Approval expiry, authenticated approver and one-time token consumption.
- Ownership, clone-test and fresh policy-verdict checks immediately before execution.
- Explicit playbook allowlist; no free-form commands.
- Simulator state changes with visible effects; no production infrastructure.
- Hash-chained audit verification, with a checkpoint digest exported alongside results. Describe this as **tamper-evident**, not tamper-proof.

A hash identifies an approved plan; it does not authenticate the human by itself. The approval tool must issue/store the token through an authenticated local session or equivalent mechanism.

For the six verdicts, test each independently and retain all individual findings. `COMPLIANT` must mean “the checked conditions are satisfied,” not universal legal compliance. `POTENTIAL_GAP` must mean “the reviewed corpus lacks a verified rule,” not permission to act. Unresolved ambiguity, conflict or missing evidence should block execution pending resolution; a human approval must not override a `VIOLATION`.

### Team allocation and hour estimates

Assumption: **three people × eight hours/day × three days = 72 person-hours**, including four contingency hours on 10 November. Person labels describe responsibilities, not confirmed team assignments.

| Date | Person A — policy/rules/execution | Person B — data/models/evaluation | Person C — report/demo/release | Daily gate |
|---|---|---|---|---|
| **8 Nov — 24 person-hours** | **8 h:** **[COUNTRY]** policy/profile and source review **2 h**; six-verdict rule engine and tests **4 h**; audit append/verification **2 h**. | **8 h:** acquisition/provenance checks **1.5 h**; minimal generator and data-card specification **3 h**; M1 baseline **1.5 h**; M3 training baseline **2 h**. | **8 h:** five-page report structure and first draft **5 h**; CLI evidence/approval display **2 h**; shared schemas and integration **1 h**. | Rules and audit work; seeded data exists; M1/M3 train; report fits a planned five-page structure. |
| **9 Nov — 24 person-hours** | **8 h:** `execute_playbook`, approval controls, clone/rollback checks **5 h**; retrieval and shared LLM/role tools **2 h**; **[COUNTRY]** report evidence corrections **1 h**. | **8 h:** M3 SHAP, confidence threshold and abstention **4 h**; held-out evaluation **2 h**; end-to-end model integration **2 h**. | **8 h:** report rewrite using measured results **4 h**; minimal commander display or CLI polish **2 h**; integration/negative-path checks **2 h**. | Complete attack→approval→healing run; one denied-action run; report complete at five pages. **Freeze features that evening.** |
| **10 Nov — 24 person-hours** | **8 h:** **[COUNTRY]** final policy/explainability review **3 h**; execution-negative tests **2 h**; release review **1 h**; contingency **2 h**. | **8 h:** final fixed-seed evaluation **2 h**; results/limitations for report **2 h**; clean-environment reproduction and model artifacts **2 h**; contingency **2 h**. | **8 h:** report render/page/figure verification **3 h**; GitHub/package/link checks **1 h**; simple video **2 h**; submission and receipt checks **2 h**. | Submit report and working GitHub artifact before the actual deadline; video receives only remaining scheduled time. |

Confirm the organiser’s exact deadline and timezone on 8 November. Target submission **at least six hours before that deadline**; do not assume the end of the Indian calendar day.

### Ten delivery milestones

These are proposed checkpoints, not claims of completed work. `update_plan` was unavailable for this planning session.

| # | Target | Completion evidence |
|---|---|---|
| 1 | 8 Nov morning: scope and contracts locked | **[COUNTRY]** selected jurisdiction profile; shared fact, model-output, plan and audit schemas; dataset manifest. |
| 2 | 8 Nov: deterministic policy engine | Fixtures exercise all six verdicts, correct record IDs, missing evidence and effective dates. |
| 3 | 8 Nov: audit foundation | Chain verifies; changing an earlier event is detected. |
| 4 | 8 Nov: reproducible data | Turkcell adapter/profile plus seeded synthetic episodes and documented train/test separation. |
| 5 | 8 Nov evening: M1 and M3 baseline | Both train/load/infer with measured outputs; no hard-coded incident label masquerading as inference. |
| 6 | 9 Nov: explanation layer | M3 SHAP and abstention; retrieval returns valid record IDs; LLM outputs pass schema/citation checks. |
| 7 | 9 Nov: guarded execution | Approval expiry, alteration, replay, owner, clone and verdict rejection cases pass. |
| 8 | 9 Nov evening: complete scenario | Routine readiness, attack, approval, repair, verification and rollback branch demonstrated. |
| 9 | 10 Nov: evidence and report frozen | Measured results linked to run IDs; report exactly five pages including images; implemented/planned distinctions consistent. |
| 10 | 10 Nov: reproducible release and submission | Clean run succeeds; GitHub revision fixed; report/video links work; submission receipt recorded. |

### AI-agent roles and policy explainability in the build

Use **one shared LLM client with role-specific prompts, tool permissions and structured outputs**. Six separate deployed models or autonomous processes are unnecessary.

| Agent role | Minimum implemented contribution |
|---|---|
| Satellite operator | Explain gateway/management evidence; propose and execute its approved PB-01 action. |
| Mobile operator | Explain service dependencies; propose and execute approved PB-06 failover. |
| Power utility | Supply power evidence that can support a fault diagnosis or explain uncertainty. |
| **[COUNTRY] National incident-response liaison** | Draft a reporting package from verified facts and relevant KB records; no actual submission. |
| **[COUNTRY] Telecom regulator liaison** | Explain applicable sector-rule checks and unresolved applicability; no impersonation of a regulator. |
| Gap Analyst | Identify missing evidence or a corpus-scoped policy gap; keep recommendations distinct from binding obligations. |

**AI may explain:** observations, anomaly scores, model confidence, SHAP contributions, retrieved clauses, selected rule conditions, deadline arithmetic, playbook preconditions and verification outcomes.

**Humans must explain and own:** disputed legal applicability, interpretation of ambiguity/conflict, proportionality of service disruption, operational priority choices, accountability, approval/rejection and proposed policy changes. SHAP explains model contributions; it does not prove causation or legal liability.

**[COUNTRY]** Preserve the KB corrections: CERT-In point of contact is Direction **(iii)**; log retention is **(iv)**. Use KB/PDF Annexure entries rather than the erroneous citation-check quotations. The 2026 space framework has `binding_status: not_stated`; do not promote it to binding law or label it definitively non-binding. B must resolve applicability/current amendments before these become runtime conclusions.

### Minimum evaluation evidence for the report

Reserve report space for a compact measured-results table, not just architecture diagrams.

| Component | Evidence to collect |
|---|---|
| M1 | Held-out attack detection and false alarms during benign maintenance/load changes; simulated time to first alert. |
| M3 | Per-class precision/recall, macro-F1, confusion matrix, abstention coverage and error among accepted predictions. State which classes are synthetic-only. |
| Rule engine | Six-verdict fixtures, missing-fact cases, effective-date checks and valid citation IDs. |
| Approval/execution | Expired/altered/replayed approval, wrong owner, failed clone and blocked verdict all reject execution. |
| Healing | Service restoration and re-attack outcomes; explicit rollback on failed verification. Timings are simulator timings. |
| Retrieval/LLM | Approximately 20 curated questions checking valid citations, supporting evidence and refusal under missing evidence or misleading log text. |
| Everyday utility | Readiness summary plus benign-maintenance counterexample; demonstrate useful output before an attack. |

If an agents-only or `--no-rules` comparison is retained, run it exclusively in the simulator and report actual outcomes. Do not assume the unguarded baseline will necessarily fail.

### Ordered cut list

Drop these in order as schedule pressure rises:

1. QLoRA, TabPFN, ECOD comparisons and hyperparameter searches.
2. Additional newly acquired datasets beyond #52 and a quickly cleared #13 subset.
3. Full-city map, elaborate console, animations and video production polish.
4. MQTT/live streaming and multi-service deployment; use an in-process replay loop.
5. Extra cities, cross-border scenarios and live jurisdiction switching. **[COUNTRY]** Keep a static comparison in the report only if B supports it.
6. PB-02–PB-05 and PB-07–PB-09 execution; retain the two core playbooks.
7. Learned minute/daily M2 tiers and conformal calibration; retain a clearly labelled simple exposure estimate only if useful.
8. M4 MILP; use a transparent small allocation example or defer allocation entirely. **[COUNTRY]** Do not present the priority ladder as law.
9. Dedicated Chroma infrastructure; retain retrieval over verified KB records using a simpler local index.
10. Additional runtime role calls and GNSS/signalling demonstration scenes. Preserve documented roles and mark unexercised capabilities honestly.

**Do not cut:** the five-page report, deterministic six-verdict rule engine, audit log, guarded `execute_playbook`, trained M1 and M3 with held-out evidence, human explanation/approval, and one complete end-to-end scenario.

### Risks and fallbacks

| Risk | Trigger / decision deadline | Fallback |
|---|---|---|
| #13 download or licence unresolved | Two-hour acquisition budget exhausted on 8 Nov | Proceed with local #52 and explicit synthetic attack data. Do not claim a real NTN cyberattack benchmark. |
| New data has incompatible features/labels | Adapter requires more than a small separate experiment | Keep it as a separate benchmark or drop it; do not fabricate cross-domain mappings. |
| Rare Turkcell positives / leakage | Daily experiment looks strong only under random row splitting | Use time-aware evaluation, report precision-recall and prevalence; do not rely on accuracy. Drop the forecast if it cannot be evaluated credibly. |
| Qwen3.8-27B GCP endpoint unavailable | No working endpoint/model identifier by 8 Nov afternoon | Use the specified local `qwen2.5:14b` fallback if installed and responsive. Record actual model/version/latency. Treat Qwen3.8 availability and licence claims as unverified until checked. |
| Local LLM too slow or unavailable | Calls exceed demo latency budget or model cannot load | Run safety/rules/execution deterministically; label any recorded LLM replay explicitly. Report reduced live-agent scope rather than presenting templates as live inference. |
| Compute or dependency friction | Installation/training exceeds the first short baseline session | Use CPU, bounded samples and pinned Python **3.11/3.12** environment; no GPU requirement for M1/M3. Keep a tested model artifact and reproducible training command. |
| Synthetic performance is unrealistically easy | Excellent scores collapse on changed parameters or benign maintenance | Remove identifiers/future leakage, increase overlap and missing evidence, report abstention and limits. |
| **[COUNTRY] Country or policy changes** | B recommends a switch | Swap jurisdiction profile, citations, recipients and location labels; preserve model/control interfaces. Freeze one primary profile on 8 Nov. |
| **[COUNTRY] Unverified or incomplete legal evidence** | Missing source, unknown amendment, designation or commencement | Return scoped uncertainty; exclude unsupported obligations from executable checks. Existing KB tests do not establish current legal completeness. |
| Integration slips on 9 Nov | No complete guarded run by evening | Stop optional features, use CLI and two playbooks, protect report/results work on 10 Nov. |
| Report exceeds five pages | First rendered draft does not fit | Remove secondary scenarios and repeated diagrams; retain short overview, each agent/model’s role, policy explainability, evidence and limitations. |
| Submission/GitHub access fails | Account or upload path untested by 9 Nov | Resolve access early, prepare release archive and verify all submitted links; preserve the submission buffer. |

The submission should describe a **working emulated prototype with measured limits**. Full NTN validation, comprehensive legal coverage, field-proven eight-outcome diagnosis and production deployment remain future work unless the team produces evidence for them before the freeze.