# A. Role of each AI agent and ML model in ORCA-NTN

Planning output from agent A, 7 Nov 2026. Plan only; nothing was built or edited. Items that depend on the country are marked **[COUNTRY]** (assumed India primary, EU/UAE comparison). KB record and gap ids are quoted from `kb/india/records.yaml`, `kb/global/records.yaml` and `kb/gaps/india.yaml`. I did not use `india-citation-check.md`.

## 0. Overview in four lines

- **The AI is split by what it is good at.** Models (M1-M4) sense and forecast. The rule engine (P node) is the only thing that gives a policy verdict. LLM agents read, draft, explain and execute approved playbooks. Humans approve and own interpretation.
- **Every agent has an everyday job.** The same agents and models run all week on drift checks, patch exposure, forecasts and compliance self-checks. The incident is the same loop run faster, with a human approval at the end.
- **One agent codebase, six role files.** An agent is a YAML role file (system prompt, tool allow-list, owned playbooks, inbox topics) on one shared `Agent` class. Build cost is about one agent plus config.
- **No agent can change a verdict, an approval or someone else's asset.** These limits are enforced in code (section 1.3), not by prompting.

## 1. Common framework (applies to every LLM agent)

### 1.1 Shared tool set
| Tool | Purpose | Notes |
|---|---|---|
| `query_kb(question, layer)` | RAG over ChromaDB, returns record ids | Refuses below similarity 0.25. Agents may cite only ids that exist in Layer A. |
| `run_rule_engine(facts)` | Deterministic verdict plus clocks | Returns one of the six verdicts, the KB id (or a GAP id) and deadline arithmetic. |
| `select_playbook(incident_ctx)` | Picks from PB-01..09 | Returns candidates, preconditions and risk. It cannot invent steps. |
| `draft_notice(type, recipient)` | Fills a notice template | The result is a **draft**; a human sends it. |
| `execute_playbook(id, target, approval_token)` | Runs one approved playbook | Four checks, below. Owner agents only. |
| `read_alerts(topic, window)` | Read-only view of `alerts/ml`, telemetry and logs | Added: agents need evidence without raw MQTT access. |
| `explain_model(alert_id)` | Returns M1/M3 feature attributions (SHAP), M2 quantiles, M4 constraints | Added: so the agent quotes the model's own reasons and does not invent them. |
| `send_message(role, payload)` | Typed message on the agent bus (`agents/<role>`) | Added: the only coordination channel; it is audited. |
| `record_gap(finding, evidence)` | Writes a draft gap record (`POTENTIAL_GAP` with a GAP id) | Added: a human reviews it before it enters `kb/gaps/`. |
| `request_approval(plan)` | Puts a hashed plan on the commander console | Added: creates the hash, expiry and clone-test result. |

Deliberately not given: a shell, file writes outside the audit log, network access, KB editing.

### 1.2 Autonomy ladder
- **A0, always allowed:** read, analyse, explain, draft, record a gap draft.
- **A1, allowed after A0:** run the rule engine, select a playbook, ask a human, message another agent.
- **A2, only with a valid approval token:** `execute_playbook` on an asset the agent's organisation owns.
- **A3, never by an agent:** change a verdict, edit the KB, send a legal notice, approve a plan, act on another organisation's assets, interpret an ambiguity, accept a risk.

### 1.3 `execute_playbook` checks (code, not prompt)
Refuses unless all hold: (1) the hash matches the exact playbook, targets and parameters; (2) the approval has not expired; (3) the target is in the caller's own asset list; (4) the clone test passed and the rule verdict is not `VIOLATION`. After running it does staged rollout 5/25/100 %, auto-rollback on a failed health check, and a re-attack check.

Everyday approvals use the same mechanism with a longer expiry. A "maintenance window" approval is a normal hashed approval that lasts hours, not minutes. This avoids inventing standing permissions.

### 1.4 Two honest limits to state in the report
- Qwen3.8 is non-deterministic in wording even at temperature 0, so only the rule engine output, the model outputs and the audit chain are reproducible. The agent's prose is explanation, never evidence.
- Agents explain the *mechanism* of their output (inputs, clause, model features). Why a rule is the right rule, and who is accountable, is for humans. Agent B owns the full split.

## 2. Non-LLM components

### 2.1 Rule engine (P node, `orca/rules.py`, `rules/<country>.yaml`)
- **Everyday job.**
  - Nightly compliance self-check of each organisation's configuration against the loaded KB. Example: is the audit-log retention setting at least 180 days? [COUNTRY]
  - Re-evaluate all open obligations when the KB file hash changes (this is the KB update review).
  - Run as a pre-check on any proposed playbook.
- **Inputs.** Structured facts (event type, timestamps for occurrence and noticing, actor, asset class, proposed action) plus KB Layer A. No RAG, no LLM.
- **Outputs.** `{verdict, kb_ids[], clocks[{id, trigger, deadline, due_at}], gap_id?}`. The verdict is one of the six: COMPLIANT, VIOLATION, AMBIGUITY, CONFLICT, POTENTIAL_GAP, INSUFFICIENT_EVIDENCE.
- **Verdict triggers.**
  - **COMPLIANT / VIOLATION:** a rule matches and the facts satisfy or break it.
  - **AMBIGUITY:** two readings of the same clause give different clocks. Example [COUNTRY]: `IN-CERTIN-DIR-2022-ii` counts from *noticing*, `IN-TCSR-2024-R7-1` counts from *occurrence*.
  - **CONFLICT:** two rules or two agents' recommendations cannot both hold.
  - **POTENTIAL_GAP:** no rule covers the case. It returns a GAP id, such as `GAP-IN-03-NO-PRIORITY-ORDER`.
  - **INSUFFICIENT_EVIDENCE:** a required fact is missing. Example: time of occurrence unknown.
- **Tools.** None. It is a function that the agents' `run_rule_engine` and `execute_playbook` call.
- **May decide alone.** Everything about verdict and clock arithmetic. **May not:** interpret, recommend a policy, or run anything. It reports to no human; the report states its rules are authored by humans (the team, with legal review).
- **Self-healing part.** Heal: gates every playbook (blocks on VIOLATION). Coordinate: computes and shows the live clocks. Report gaps: the source of every gap record.
- **Explains.** Exactly which clause fired, with the verbatim quote and pinpoint, how each deadline was computed, and why a case was a gap, because its rule trace is the whole logic.

### 2.2 M1 Isolation Forest anomaly (+ ECOD comparison)
- **Everyday job.** Continuous drift detector: new management-plane source, off-hours login, command-rate change, SNR slope change. Daily "top 5 oddities" digest for the operators. This is the baseline alert stream; false-positive rate on Diwali/festival surges (U3) is the headline everyday metric.
- **Inputs.** `telemetry/link/*`, `logs/mgmt/*`, `logs/signalling/*` window features. **Outputs.** `alerts/ml` anomaly score, top contributing features, entity.
- **Tools / playbooks.** None; it is a model. **May decide:** raise an alert, trigger M3 and the agents. **May not:** act, classify cause, or declare an attack. Reports to the NOC and security analyst of the owning organisation.
- **Self-healing part.** Predict/Detect: earliest signal (the management-plane login alarm precedes the wipe). It is the only component that sees attacks M3 was never trained on.
- **Explains.** Which features pushed the score up and how rare the value is; not what the cause is.

### 2.3 M2 forecaster (minute tier and daily tier)
- **Everyday job.**
  - **Daily tier:** weekly link-risk and exposure forecast ("which links are at risk 1-5 days out, and which pending patches would fall inside the exposure window"). Used for maintenance scheduling.
  - **Minute tier:** rolling minutes-to-failure P10/P50/P90 during weather and battery run-out, so planned work is not scheduled into a predicted outage.
- **Inputs.** Weather, link, power telemetry; patch state; Turkcell daily features for the daily tier. **Outputs.** `minutes_to_failure` quantiles, exposure set (who goes blind), pending patches, recommended pre-emptive playbook (suggestion only).
- **Tools / playbooks.** None. **May decide:** publish forecasts and warn. **May not:** schedule maintenance or execute. Reports to the mobile operator NOC (link) and the power utility (battery).
- **Self-healing part.** Predict: a predicted outage is a predicted exposure window, so it triggers PB-08 (patch before the window), PB-09 (shed load) or PB-06 readiness (verify the backup path) *before* the failure. It also supplies the "expected failure?" input that M3 uses to separate weather from attack.
- **Explains.** The margin calculation (expected fade vs fade margin), the quantile band and the calibration used. It cannot say it is certain; it gives intervals and states the daily tier is real-data, the minute tier is synthetic.

### 2.4 M3 fault-vs-attack classifier (LightGBM, SHAP, calibrated abstain)
- **Everyday job.** Weekly review of classified events (fault-weather, fault-power, etc.) so the false-alarm rate is visible. Every fault ticket gets a class, which also feeds the evidence for regulatory "was it an attack?" questions.
- **Inputs.** M1 alert, M2 expected-failure signal, link residuals, power, GNSS, signalling and management-plane features. **Outputs.** One of 8 classes (normal, fault-weather, fault-equipment/power, attack-jamming, attack-management-plane, attack-GNSS, attack-signalling, abstain), confidence, SHAP reasons.
- **Tools / playbooks.** None. **May decide:** a class with confidence, or abstain. **May not:** declare an incident, start a legal clock or choose a response. Below the confidence threshold it must return `abstain`. Reports to the security analyst in each organisation.
- **Self-healing part.** Coordinate/Contain: its class decides whether the incident is treated as a fault or an attack and which agent plans first. A wrong call changes which clock starts, hence the abstain path.
- **Explains.** The top SHAP features, a calibrated confidence and why it abstained. It cannot explain the true cause beyond its training data.

### 2.5 M4 MILP capacity allocator
- **Everyday job.** Daily/weekly "if the main path drops, who keeps capacity" plan, checked against the current priority table, plus event-day dry runs (cricket match, festival). Gives the critical-service customer a standing answer, not only a crisis one.
- **Inputs.** Available backup capacity, demand per service class, priority table (an organisation-set input, because no national order exists in the KB [COUNTRY]). **Outputs.** Allocation (112, hospital, water, payments, rest), binding constraints, objective value.
- **Tools / playbooks.** None. **May decide:** the optimal allocation for the given table. **May not:** set the priority order. Reports to the mobile operator's NOC lead and incident commander.
- **Self-healing part.** Heal: tells PB-06 and PB-09 how much capacity goes to whom during failover.
- **Explains.** Which constraints are tight and what changes if one service is moved. It cannot say the priority order is fair. That is the human/regulator question (`GAP-IN-03-NO-PRIORITY-ORDER`).

## 3. LLM agents (Qwen3.8-27B)

Playbook ownership: PB-01..05 satellite operator, PB-06/07/09 mobile operator. PB-08 is "asset owner": each owner agent runs it only on its own assets (check 3 enforces this). Agents with no playbook can never reach A2.

### 3.1 Mobile operator agent
- **Everyday job.**
  - Daily tower/backhaul config-drift check against baseline.
  - Patch-exposure tracking for gNB/transport firmware, against M2's exposure windows.
  - Weekly M2 risk review and failover-path hygiene (is the backup path itself clean and patched?).
  - Event-day capacity dry runs with M4.
- **Inputs.** `alerts/ml`, `telemetry/link|power`, M2 exposure set, M4 allocation, inbox from satellite operator agent. **Outputs.** Failover proposals, patch plans, drafted regulator/CERT notices, "backup path clean" attestations.
- **Tools.** All shared tools. **Owns:** PB-06 (failover to a path verified clean first), PB-07 (re-authenticate terminals and towers), PB-09 (shed non-critical load), PB-08 on its own assets.
- **May alone (A0/A1).** Draft, propose, run the rule engine, message other agents. **May not:** execute without an approval token, fail over onto a path that has not passed the clean check, act on the satellite operator's management network, send a notice. Reports to the mobile operator's NOC lead.
- **Self-healing.** Predict: pre-empt with PB-08/09. Heal: PB-06 failover, PB-09 shedding. Contain: refuses a trap path (U5). Fix: PB-07 after management-plane recovery. Report: drafts its [COUNTRY] DoT report (`IN-TCSR-2024-R7-1`) and flags `GAP-IN-03`.
- **Explains.** Why this failover path and not another, which clause its draft rests on, and which model output triggered the proposal.

### 3.2 Satellite operator agent
- **Everyday job.**
  - Management-plane hygiene: VPN accounts without MFA, stale credentials, firmware-signing status, source-IP baseline changes.
  - Firmware-version inventory and weekly vulnerability-advisory match against the terminal fleet.
  - 180-day log retention check [COUNTRY] (`IN-CERTIN-DIR-2022-iv`).
  - Point-of-contact record check (`IN-CERTIN-DIR-2022-iii`).
- **Inputs.** `logs/mgmt/*`, M1/M3 alerts, simulated advisories, ownership map of terminals and gateways. **Outputs.** Hardening proposals, containment plans, drafted CERT report, **downstream warnings to dependent services** (message to mobile, power, customer agents).
- **Tools.** All shared tools. **Owns:** PB-01 (disable exposed VPN account, rotate credentials), PB-02 (enforce MFA), PB-03 (block attacker sources), PB-04 (roll terminals back to last signed firmware), PB-05 (isolate management segment, keeping logs), PB-08 on its own assets.
- **May alone.** Analyse, draft, propose, message downstream agents. **May not:** execute any of PB-01..05 without approval (PB-05 and PB-04 are high-impact and always need the incident commander), touch tower or utility assets, or decide that the warning to downstream parties is legally required (there is none: `GAP-IN-02-NO-DOWNSTREAM-WARNING`). It warns voluntarily and records the gap. Reports to the satellite operator's security lead.
- **Self-healing.** Predict: its everyday hygiene closes the VPN door that KA-SAT used. Contain: PB-03, PB-01, PB-05. Fix: PB-04 rollback, PB-02. Coordinate: first to send the downstream warning. Report: CERT-In draft (`IN-CERTIN-DIR-2022-ii`, 6 h from noticing).
- **Explains.** Which KB clause governs retention or reporting, why a given playbook order was chosen, and what each playbook step does. It cannot say whether voluntary warning is the right norm.

### 3.3 Power utility agent
- **Everyday job.** Grid-outage and battery autonomy watch for towers and gateways; weekly battery-health report from M2's power forecast; patch/config check for the utility's RTUs and battery controllers. [COUNTRY] notes that no battery floor exists (`GAP-IN-04-NO-BATTERY-FLOOR`), so it works to an operator-set threshold.
- **Inputs.** `telemetry/power/*`, `telemetry/weather/*`, M2 power quantiles, M3 fault-power class, messages from the mobile operator. **Outputs.** Fault certificate ("grid fault, not attack") for M3, restoration estimate, load-shed requests to the mobile operator, drafted utility incident notice.
- **Tools.** `read_alerts`, `explain_model`, `query_kb`, `run_rule_engine`, `draft_notice`, `send_message`, `record_gap`, `request_approval`, `execute_playbook`. **Owns:** PB-08 on its own assets only. It has no ownership of PB-09 (shedding is the mobile operator's load).
- **May alone.** Declare a power-side fact (grid on/off, restoration ETA) as evidence. **May not:** execute on tower or network assets, classify an incident as an attack. Reports to the utility's control-room duty officer.
- **Self-healing.** Predict/Heal: battery run-out and restoration ETA feed PB-09 timing. Coordinate: lets the commander separate a gateway power failure from an attack (U6). Fix: PB-08 on its controllers.
- **Explains.** The power data behind its fault statement and the battery forecast band. It cannot guarantee restoration times.
- **Build note.** Lowest-value agent; keep it but thin (see section 6).

### 3.4 National CERT agent [COUNTRY: CERT-In]
- **Everyday job.** Receives and triages everyday reports; checks submissions for completeness against the required incident categories (`IN-CERTIN-DIR-2022-ANX1-*` items); keeps a weekly advisory summary for the other agents; point-of-contact register check.
- **Inputs.** Drafted notices from operators, CERT-relevant `alerts/ml`, advisories in the KB. **Outputs.** Completeness check, triage class, advisory draft to sector, request-for-information draft.
- **Tools.** `query_kb`, `run_rule_engine`, `read_alerts`, `explain_model`, `draft_notice`, `send_message`, `record_gap`. **No** `execute_playbook`, no `select_playbook`: it owns **no playbooks** and cannot touch operator assets.
- **May alone.** Triage a report, request missing information, draft an advisory. **May not:** issue a direction (`IN-ITACT-2000-70B(6)`), publish an advisory, or attribute an attack. Reports to the CERT duty analyst.
- **Self-healing.** Coordinate/Report: receives the 6-hour report, checks it against the Annexure categories, relays a draft advisory to other operators (the information flow the KB says has no duty behind it).
- **Explains.** Which Annexure item an incident maps to, and why a report is incomplete. It cannot say whether an event is a cyber "incident" in the legal sense when the categories are unclear. Humans interpret that.

### 3.5 Telecom regulator agent [COUNTRY: DoT]
- **Everyday job.** Compliance self-check roll-up for the sector (which operators have a stale point of contact, retention gaps, unpatched fleets); monitors the KB for newly notified rules and drafts a change summary for human review; keeps the open-obligation list.
- **Inputs.** Rule-engine compliance results, operator notices, gap drafts. **Outputs.** Compliance roll-up, clock status for DoT-bound reports, draft information request.
- **Tools.** Same as the CERT agent. **No playbooks.**
- **May alone.** Roll up, flag, draft. **May not:** find a licensee in violation (the rule engine returns the verdict, a human regulator decides what follows), set penalties, change a priority order, or amend rules. Reports to the regulator's compliance officer.
- **Self-healing.** Coordinate/Report: tracks the second 6-hour clock (`IN-TCSR-2024-R7-1`, from occurrence), and shows the commander when the two clocks differ (`GAP-IN-01-THREE-CLOCKS`).
- **Explains.** How the sector status was computed and the clauses used. It cannot say whether a rule is proportionate.
- **Merge candidate:** see section 6.

### 3.6 Gap Analyst / policy adviser agent
- **Everyday job.** Weekly gap register review: groups `record_gap` drafts, deduplicates, checks each against KB Layer A, and proposes new or updated gap records with evidence ids. Runs the "country swap" diff (India KB vs EU KB) as a standing report.
- **Inputs.** `POTENTIAL_GAP` verdicts, gap drafts from all agents, both KB layers, the loaded standards list. **Outputs.** Gap register proposals (`GAP-*`), readiness.json inputs, policy-question briefs for humans.
- **Tools.** `query_kb`, `run_rule_engine`, `read_alerts`, `explain_model`, `record_gap`, `draft_notice` (policy brief type only), `send_message`. **No playbooks.**
- **May alone.** Draft a gap record and a question. **May not:** write a policy recommendation as a decision, edit the KB, claim a gap is verified (only humans set `verified: true`), draft legislation. Reports to the policy lead.
- **Self-healing.** Report gaps: the final step. Turns what the rule engine could not answer into the list of missing rules (for example no downstream warning duty, no priority order, no joint plan: `GAP-IN-02`, `-03`, `-07`).
- **Explains.** Why something counts as a gap (the evidence ids that show nothing covers it). It cannot say what the rule should be. That is policy and for humans.

### 3.7 Human incident commander (not an AI)
- **Everyday job.** Weekly review of the console: gaps, clocks, M2 risk and open approvals. Runs the monthly drill. Approves maintenance-window plans.
- **Inputs.** Console: plan, evidence, M3 SHAP reasons, rule verdicts, clocks, clone-test result. **Outputs.** Approve or reject (hashed, time-limited), final send of any notice, ruling on AMBIGUITY and CONFLICT.
- **Tools.** The console (STM32MP135F-DK) and the approve button. Nothing else.
- **Decides alone.** All of A3 in section 1.2. **Reports to** the organisations' executives and, for legal matters, counsel.
- **Self-healing.** Approver at "Ask"; owner of every irreversible decision.
- **Explains.** Why this plan, why this reading of an ambiguous clause, who is accountable, whether a trade-off is proportionate. These are exactly the items agents are prohibited from explaining as their own (agent B owns the table).

### 3.8 Optional agents (only after the six work)
**Neighbouring CERT [COUNTRY: another country's CERT, e.g. Sri Lanka CERT].**
- **Everyday job.** Weekly indicator exchange.
- **Inputs/outputs.** Receives a sanitised indicator list from the national CERT agent; returns "seen here too".
- **Tools.** `query_kb`, `send_message`, `draft_notice`. **No playbooks. May not** receive raw logs; reports to its human CERT analyst.
- **Self-healing.** Coordinate across borders.
- **Explains.** Which indicators matched. **Value is low for the 10 Nov scope.** Implement as a message stub.

**Data-protection authority.**
- **Everyday job.** Checks whether telemetry and logs contain personal data.
- **Inputs.** Pseudonymised logs, notices. **Outputs.** Breach-notice completeness check.
- **Tools.** `query_kb`, `run_rule_engine`, `draft_notice`. **No playbooks.**
- **[COUNTRY]** In India the binding breach clock is not yet in force (`IN-DPDP-ACT-2023-8-6`, `IN-DPDP-RULES-2025-R7`, `GAP-IN-05-NO-BREACH-CLOCK-TODAY`), so it mostly returns `INSUFFICIENT_EVIDENCE` or `POTENTIAL_GAP`. If the country changes to the EU, this agent becomes meaningful (GDPR Art. 33, `EU-GDPR-2016-ART33-1`).
- **Explains.** Which clause would apply. It cannot say whether a breach is likely to harm individuals. That is a human assessment.
- **Merge into the Gap Analyst.**

**Critical-service customer (hospital or payments switch).**
- **Everyday job.** Checks the customer's own dependency list against the satellite operator's published status; gets M4's standing allocation; reviews its own fallback (offline payments, 112 priority).
- **Inputs.** Downstream warnings, M4 allocation. **Outputs.** "Impact on us" statement, request for priority.
- **Tools.** `read_alerts` (own scope), `explain_model`, `query_kb`, `draft_notice`, `send_message`, `record_gap`, `request_approval`. **Owns** no network playbooks; PB-08 on its own endpoints is possible.
- **May alone.** Switch its own fallback after approval. **May not:** reroute operator capacity, claim priority it was not assigned. Reports to the hospital IT head or payments risk officer.
- **Self-healing.** Receives `GAP-IN-02`'s missing downstream warning; this agent shows why the warning matters.
- **Explains.** Its own impact numbers. **Best of the three for the "pillar of everyday work" story.** Keep this one if time allows.

## 4. One incident: Chennai, management-plane wipe plus jamming-forced failover (illustrative times)

| Time | Event | Who acts | Output / rule |
|---|---|---|---|
| 19:42 | Unusual VPN login from a new source, off-pattern | **M1** | Anomaly alert with top features |
| 19:42 | Satellite agent reads alert, asks `query_kb` and `run_rule_engine` | Satellite operator agent | `INSUFFICIENT_EVIDENCE` (no wipe yet), watch raised |
| 19:51 | Wipe commands to terminals begin (occurrence) | simulator | Payments terminals start dropping |
| 19:54 | Class: attack-management-plane, 0.91 | **M3** | SHAP: command rate, source, no weather expected from M2 |
| 19:54 | Clock check | **Rule engine** | AMBIGUITY: CERT-In 6 h from noticing (`IN-CERTIN-DIR-2022-ii`) vs DoT 6 h from occurrence (`IN-TCSR-2024-R7-1`) and M1's 19:42 alert may count as "noticing"; `GAP-IN-01` |
| 19:55 | Plan: PB-03 + PB-01 (+ PB-05 option) | Satellite operator agent | Select, clone test, `request_approval` |
| 19:56 | Jamming raises the noise floor on the microwave link | simulator | M3 now sees jamming too |
| 19:57 | Warn downstream | Satellite agent to mobile, power, customer agents | Voluntary; `record_gap` (`GAP-IN-02`) |
| 19:58 | Mobile agent proposes PB-06 failover | Mobile operator agent | Preconditions: backup path clean check; M4 allocates capacity 112 > hospital > water > payments |
| 19:58 | Priority order | **Rule engine** | POTENTIAL_GAP (`GAP-IN-03`); allocation is the operator's table, flagged |
| 19:59 | CONFLICT: PB-05 isolation vs keeping terminals reachable for rollback | **Rule engine** / agents | Two recommendations flagged for human |
| 20:00 | Commander reads evidence, rules on the reading of "noticing", approves PB-03, PB-01, PB-06 (hash, expiry) | **Human commander** | Approval token |
| 20:01 | Satellite agent `execute_playbook` PB-03, PB-01; staged 5/25/100 %; re-attack check | Satellite operator agent | Result on `actions/result/*` |
| 20:03 | Mobile agent `execute_playbook` PB-06 | Mobile operator agent | Backup path verified clean first |
| 20:10 | PB-04 rollback of wiped terminals, PB-07 re-authentication | Both owner agents (second approval) | Auto-rollback if a health check fails |
| 20:15 | Power utility confirms grid fine (rules out fault-power) | Power utility agent | Evidence to M3 context |
| 20:30 | Drafts: CERT-In report, DoT report | Satellite and mobile agents | Humans review and send |
| 20:35 | CERT agent completeness check against Annexure | National CERT agent | Draft advisory for sector |
| 20:40 | Regulator agent shows both clocks and time remaining | Telecom regulator agent | Console |
| 21:00 | Gap register updated: `GAP-IN-01`, `-02`, `-03`, `-07` | Gap Analyst agent | Proposal for humans |
| Next day | Hash-chained audit and report | Audit log | Reproducible |

## 5. An everyday day (no incident), "a normal Tuesday"

| Time | Component | Task |
|---|---|---|
| 00:30 | Rule engine | Nightly compliance sweep of configs against the KB (retention, point of contact, KB hash change) |
| 02:00 | M2 daily tier | Weekly risk forecast for links and exposure windows (Tuesday run) |
| 06:30 | Satellite operator agent | Management-plane hygiene: MFA coverage, stale accounts, source baseline, advisory match |
| 07:00 | Mobile operator agent | Config-drift check, patch-exposure report using M2's windows |
| 08:00 | Power utility agent | Battery autonomy and grid-outage watch; weekly battery-health report |
| 09:00 | M1 | Daily "top oddities" digest to the NOCs (festival traffic correctly not flagged) |
| 10:30 | Commander | Reviews the console; approves a maintenance-window plan (PB-08 on three towers, 8 h approval) |
| 11:00 | Mobile and power agents | `execute_playbook` PB-08 inside the window, avoiding M2 minute-tier risk windows |
| 13:00 | M2 minute tier | During afternoon rain, minutes-to-failure bands; M3 classes any fault as weather (class logged) |
| 14:00 | M4 | Standing allocation refreshed, event-day dry run for a cricket match |
| 15:00 | National CERT agent | Triage of the day's voluntary reports, advisory summary |
| 16:00 | Telecom regulator agent | Sector compliance roll-up, flags a stale point of contact |
| 17:00 | Critical-service customer agent (optional) | Checks fallback against M4 allocation |
| 18:00 | Gap Analyst agent | Weekly gap register review; India-vs-EU KB diff |
| 18:30 | Commander | Rules on two gap proposals; marks verified or not |

## 6. What can be cut or merged (3 days left)

- **Keep, high value:** rule engine, M1, M3, satellite operator agent, mobile operator agent, human commander, Gap Analyst. These carry the whole story and both clocks.
- **Keep, thin:** power utility agent. It needs only three tools and mostly returns power facts; M2 and M3 already carry the weather and power alibi. Build it last of the six and make it template-driven.
- **Merge:** telecom regulator agent into the Gap Analyst codebase as a second role file ("regulator view"), same tools, a different prompt and inbox. The two have the same tool allow-list and no playbooks; two role files cost only config.
- **Cut for 10 Nov:** neighbouring CERT (message stub only, or leave to the Dubai demo) and data-protection authority (no binding clock in force [COUNTRY]; fold it into the Gap Analyst's note on `GAP-IN-05`). Reconsider the data-protection agent if the country moves to the EU.
- **Keep if time:** critical-service customer, because it best shows "pillar of everyday work" (a hospital or payment switch gets a daily answer).
- **Model cuts:** the ECOD comparison and the M2 minute-tier conformal layer are the first to drop if M1/M2 slip. Nothing else is optional.
- **Build order:** one `Agent` class + role YAML + tools first (so agents 1-6 cost config), then `execute_playbook`, then the owner agents.

## 7. Report table (fits about half a page)

| Component | Everyday job | Inputs > Outputs | Playbooks / tools | May not | Human | Can explain |
|---|---|---|---|---|---|---|
| **Rule engine (P)** | Nightly compliance check, KB-change re-eval | Facts + KB > 6 verdicts, ids, clocks | none (function) | interpret, run | Policy lead | Clause, quote, clock arithmetic |
| **M1 Isolation Forest** | Drift and oddity digest | Link, mgmt, signalling > anomaly score | none | classify cause, act | NOC / analyst | Which features were rare |
| **M2 forecaster** | Weekly risk, minute countdown | Weather, power, link > time-to-failure bands | none | schedule, execute | NOC, utility | Margin calc, interval |
| **M3 classifier** | Weekly class review | Alerts, M2 > 8 classes + SHAP + abstain | none | declare incident | Analyst | Top features, confidence |
| **M4 MILP** | Daily allocation, dry runs | Capacity, demand > allocation | none | set priority order | NOC lead | Tight constraints |
| **Mobile operator agent** | Drift, patch exposure, path hygiene | Alerts, M2, M4 > failover plan, notice | PB-06, 07, 09, 08 | fail over to unclean path | NOC lead | Why this path, clause |
| **Satellite operator agent** | MFA, firmware, logs, advisories | Mgmt logs, M1/M3 > contain plan, warning | PB-01-05, 08 | act on others' assets | Security lead | Why this order, clause |
| **Power utility agent** | Battery and grid watch | Power, M2 > fault statement, ETA | PB-08 (own) | call an attack | Duty officer | Power data, forecast band |
| **National CERT agent** | Triage, advisory summary | Notices > completeness, advisory draft | none | issue direction | CERT analyst | Annexure mapping |
| **Telecom regulator agent** | Sector roll-up, KB watch | Verdicts > roll-up, clock status | none | find violation | Compliance officer | How status computed |
| **Gap Analyst agent** | Weekly gap review, KB diff | Gaps > gap proposals | none | write policy, verify | Policy lead | Why it is a gap |
| **Incident commander (human)** | Console review, drills | Evidence, plan > approval | console | n/a | Executives, counsel | Why, who is accountable |
| *Neighbouring CERT (opt.)* | Indicator exchange | Indicators > matches | none | receive raw logs | CERT analyst | Which matched |
| *Data-protection (opt.)* | Personal-data check | Logs > notice check | none | assess harm | DPA officer | Applicable clause |
| *Critical-service customer (opt.)* | Fallback check | Warnings, M4 > impact | PB-08 (own) | claim priority | Hospital / payments head | Own impact |

Country-dependent items: authority names (CERT-In, DoT), all clock values and clause ids, the gap ids, notice templates, the data-protection agent's relevance, and the neighbouring-CERT partner. Everything else is country-neutral.
