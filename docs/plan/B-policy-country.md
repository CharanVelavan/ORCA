# Agent B: policy explainability and country (plan only, nothing written)

## 1. Summary

- **Decision: keep India as the primary knowledge base. Keep the EU (NIS2) as the single comparison KB for demo scenario 3.** Optionally add 3 Australian records (about 3 h, stretch only). Switching country would cost about 28-36 h of the roughly 72 h left and gains nothing the jury scores.
- India scores 27/30 on my rubric, Australia 22 (Australia scores 20 vs India 17 on policy clarity alone), then the EU 22, USA 20, Singapore 17, UK 16 and UAE 10. Australia has the cleanest satellite-aware statute, but India has the cheapest switch and the best fit with Chennai. India's three overlapping 6-hour clocks (CERT-In, Telecom Cyber Security Rules, Critical Telecom Infrastructure Rules) are also what makes the AMBIGUITY and CONFLICT hand-offs visible.
- UAE: I found no public binding incident-reporting clock or satellite cyber rule. Keep it as the one verified emergency-priority example (`AE-TDRA-IC-2006-EMERGENCY`) and as evidence of the NTN policy gap.
- Explainability rule for the report: the AI explains **which clause, what it says, how many hours, why this verdict, which features and evidence**. Humans explain **what vague law means, who is accountable, whether an action is proportionate, who gets scarce capacity, what the public is told, and what to recommend to regulators**. Every verdict hands off to a named role.
- Three cheap fixes to the KB were found (section 2e and the switch-cost section). One is a verified quote that strengthens the NTN coverage claim for India: Telecommunications Act 2023 s.2(s) defines a "telecommunication network" as including "terrestrial or satellite networks".

---

## 2. Part 1: policy explainability split

### 2a. What each AI component can explain, and how

| Component | Can explain | Artefact shown |
|---|---|---|
| **Rule engine (P node)**, deterministic | Which record applies; what it says; binding status and in-force date; which clock starts and when it expires; why the verdict is what it is | KB record id plus verbatim quote and pinpoint; deadline arithmetic (`trigger_time + ISO duration`, shown in hours and minutes); verdict trace (facts → rule → record → verdict); `verified` flag; gap id for POTENTIAL_GAP |
| **M1** Isolation Forest | That something is unusual and which window features drove it (login rate, new source, off-hours, commands per session) | Anomaly score; top deviating features against the normal baseline; raw log lines in the window. It does not say what the anomaly is. |
| **M2** forecaster | Minutes to failure and who goes blind | P10/P50/P90 minutes (conformal-calibrated); physics fade margin versus expected rain fade; exposure set; pending patches |
| **M3** 8-class LightGBM | Fault versus attack, which kind, and how sure | Class plus calibrated confidence; SHAP top-3 with sign; fade residual; abstain reason (confidence below threshold, or a missing feed such as GNSS or signalling); evidence list |
| **M4** MILP | Why capacity went to whom | Allocation table; binding constraints; the priority order that was *input* (112 → hospital → water → payments → rest). It cannot say the order is right. |
| **LLM agents** (Qwen3.8) | Plain-language summary of the above; which playbook and why; draft notices; what the clone test showed | Narrative that may cite only record ids returned by `query_kb` or the rule engine; playbook id, clone-test result, rollout stage; the `execute_playbook` audit entry (approval hash, owner, expiry); a hash-chained audit-log entry for every tool call |

The LLM adds no legal facts. Deadlines and verdicts come from code, and the LLM only rephrases them.

### 2b. What humans must explain, and who owns it

| Human duty | Why AI cannot | Owner |
|---|---|---|
| Legal interpretation behind AMBIGUITY (for example, "occurrence" versus "noticing"; whether the 2026 space framework binds) | Only the issuing authority or a court can interpret a clause. The AI can list readings. | Operator legal counsel or CISO; authoritative reading from CERT-In or DoT |
| Resolving a CONFLICT between two lawful actions | It is a value judgement, not a lookup | Incident commander (live); regulator (standing rule) |
| Accountability for an approved action | A hash-bound approval makes a person answerable; software cannot be | Approver (named human) and the organisation's CISO |
| Proportionality (isolating a gateway that carries 112; shedding load) | Trade-off between harms | Incident commander; asset owner |
| Is it "significant" or reportable; is the asset designated critical telecom infrastructure | Depends on designation and facts the system may not hold (`IN-CTIR-2024-R7-1-j` applies only if designated) | CISO and counsel |
| Attribution to a state actor | Intelligence and diplomatic judgement | National CERT or government. Never the AI. |
| Who gets scarce capacity (a gap, not a rule) | Needs a published policy choice | Regulator (DoT/TRAI) sets it; incident commander applies an interim, documented choice |
| What customers and the public are told | No Indian duty exists (`GAP-IN-02`); wording affects panic and liability | Operator communications lead; regulator |
| Policy recommendations from the gap register | The AI drafts; people sponsor and sign | Gap Analyst/policy adviser (human), then the organisation |
| Privacy and rights trade-offs (SS7 location data, cross-border CERT sharing) | Rights balancing | Data-protection officer. DPDP is not in force until about May 2027 (`GAP-IN-05`). |
| Whether the KB is complete and current | The AI cannot audit its own sources | KB curator (a human; you or Yogender) |

### 2c. Hand-off per verdict, with a worked example

All record ids are from `kb/india/records.yaml` or `kb/gaps/india.yaml`. Times are invented demo facts.

| Verdict | System shows | Human adds | Worked example |
|---|---|---|---|
| **COMPLIANT** | Record, quote, clock, time used, time left. It means no applicable record is breached on the stated facts, not legal clearance. | Check the facts (who "noticed") and sign the report | Satellite operator notices a management-plane wipe at 19:02. `IN-CERTIN-DIR-2022-ii` (PT6H, noticing; Annexure I item ii, `IN-CERTIN-DIR-2022-ANX1-ii`) is due 01:02. The CERT-In report goes at 22:40, which is 3 h 38 m used and 2 h 22 m left. COMPLIANT. The CISO signs. |
| **VIOLATION** | The breached record, the overrun, and the evidence for the trigger time (audit-log hash) | Explain the delay, own the consequence, fix the process. The KB holds no penalty text, so none is quoted. | The first malicious command is logged at 18:41. The DoT report is sent at 01:15, which is 6 h 34 m. `IN-CTIR-2024-R7-1-j` ("no later than six hours of occurrence", CTI owners) gives VIOLATION by 34 minutes. (Corrected 7 Nov: the notified TCSR counts from becoming aware, so use the CTIR clock for this example.) The operator CISO and counsel write the late-filing statement. |
| **AMBIGUITY** | Each reading, the deadline each gives, and the earliest as the safe working deadline; cites `GAP-IN-01-REPORTING-CLOCKS` | Choose the reading; decide on a protective early filing; ask the authority if needed | M3 first says fault-power at 02:10, then attack-management-plane at 06:40. CERT-In clock (noticing 06:40) is due 12:40. DoT clock is due 07:55 if "occurrence" is the first malicious login (01:55) or 08:10 if it is the outage start (02:10). At 06:40 only 1 h 15 m remains on the stricter reading. Counsel and CISO decide. |
| **CONFLICT** | Both actions, the records behind each side, the overlap in targets, and the playbook preconditions that clash | Pick one; log the reason; escalate the standing question | Satellite agent proposes PB-05 (isolate management segment; supported by `IN-CERTIN-DIR-2022-ANX1-ii` and `IN-CERTIN-DIR-2022-iv`, which preserves logs). The mobile agent proposes PB-06 (fail over through the same gateway to keep 112 up; public-safety context `IN-TELACT-2023-20`). The engine detects the clash from shared targets and preconditions. No record settles it, so it adds the POTENTIAL_GAP below. The incident commander decides. |
| **POTENTIAL_GAP** | The gap id and its evidence records; a statement that the KB is silent, not that nothing exists | Interim decision now; sponsor a recommendation for the regulator | M4 must rank 112, hospital, water and payments for scarce backup capacity. `GAP-IN-03-NO-PRIORITY-ORDER` (evidence `IN-TELACT-2023-20`, `-22`, `-24`, `IN-TCSR-2024-R7-1`). In the UAE swap, `AE-TDRA-IC-2006-EMERGENCY` covers 112 only. The commander records the interim order; the Gap Analyst drafts the recommendation. |
| **INSUFFICIENT_EVIDENCE** | The missing facts, which feed or log is absent, and the clock that would start if the fact is confirmed | Gather evidence or choose a protective report | M3 abstains on a clear-sky outage because the gateway management log is missing. The engine cannot say whether Annexure I item ix (`IN-CERTIN-DIR-2022-ANX1-ix`) applies. It lists "management log for gateway X" as missing. The CISO decides on a precautionary CERT-In report. |

### 2d. Report-ready table (11 rows, about one third of a page at 8-9 pt) and overview text

**Overview statement (3 sentences):** "ORCA-NTN's AI can show which clause applies, quote it, count the hours and trace why a verdict was reached, but it cannot decide what a vague clause means, who is accountable, or whether a trade-off between lives and security is acceptable. Every verdict names the knowledge-base record it relies on, and every point where the law is ambiguous, conflicting or silent is routed to a named human who approves before any agent acts. Gaps we find are drafts for regulators, not decisions."

| # | Question | AI explains (artefact) | Human explains (owner) |
|---|---|---|---|
| 1 | Which rule applies? | Record id, verbatim quote, binding status, in-force date | Is the KB complete and current (KB curator, counsel) |
| 2 | When is the report due? | Trigger time plus ISO duration, shown in hours | What counts as "occurrence" or "noticing" (counsel; CERT-In/DoT) |
| 3 | Why this verdict? | Trace: facts → rule → record → verdict | Meaning of AMBIGUITY or CONFLICT (counsel) |
| 4 | Fault or attack? | M3 class, calibrated confidence, SHAP top-3, abstain reason | Is it enough to declare, report or attribute (CISO; national CERT) |
| 5 | When will it fail? | M2 P10/P50/P90 minutes, fade margin | Accept the risk of pre-emptive action (incident commander) |
| 6 | Who gets scarce capacity? | M4 allocation and binding constraints | The priority order and its fairness (regulator; commander, interim) |
| 7 | What fix, and what effect? | Playbook, clone-test result, rollout, rollback | Proportionality and approval (named approver, asset owner) |
| 8 | Who is told? | Draft notices with citations; dependents list | Whether and how to warn the public (comms lead, regulator) |
| 9 | Where is the law silent? | Gap-register entry with evidence ids | Policy recommendation to regulators (Gap Analyst, organisation) |
| 10 | Rights and personal data | Flags data categories involved | Privacy and cross-border decision (DPO) |
| 11 | Was the AI right? | Hash-chained audit log, tool-call log, eval scores | Accountability for using AI (CISO, board) |

If the template's 12 pt Times New Roman table style does not fit, drop rows 5 and 11 into prose. Check with Agent D.

### 2e. Failure modes of explanation and guards

| Failure | Guard that exists | Cheap guard to add |
|---|---|---|
| **Hallucinated citation** | `orca/kb.py` loads Layer A only, so agents can cite only existing ids. Verdicts come from the deterministic engine. Retrieval refuses below similarity 0.25. | `check_citations`: every id in an LLM answer must exist, and any quoted text must be a substring of the KB `quote`; otherwise reject and log. The planned 20-30 question citation eval reports the rate (about 2 h). |
| **Stale or wrong law** | `in_force_from`, `binding_status`, `verified`, and source sha256 in `sources.yaml`. `KB.in_force()` blocks `binding_not_in_force` (DPDP) and returns False for `not_stated` (space framework). | (1) `in_force()` returns True when `in_force_from` is null and the record is binding. Fill the dates, for example CERT-In Directions: the PDF says "effective after 60 days" from 28 Apr 2022, so 2022-06-27. (2) Print "KB as of <date>" on every verdict. (3) Route `not_stated` to AMBIGUITY, never "not applicable". (4) The TCSR 2025 amendment is still unchecked, so flag `IN-TCSR-2024-R7-1`. |
| **Unverified record presented as fact** (for example `IN-DPDP-RULES-2025-R7`, `verified: false`) | The `verified` flag is carried in the record. | Rule: a `verified: false` record cannot produce VIOLATION or COMPLIANT. It produces INSUFFICIENT_EVIDENCE with a "record unverified" note (about 1 h in the engine). |
| **Over-confident SHAP** | M3 outputs calibrated confidence plus abstain. M2 uses conformal intervals. | Label every SHAP view "model explanation, not proof". Cross-check against the physics fade residual. Show correlated features together. Report calibration on held-out ranges. If SHAP and physics disagree, force abstain. |
| **LLM arithmetic or paraphrase drift** | Deadlines are computed in code. | LLM sees only the result string; unit test that the summary contains the engine's numbers. |
| **"COMPLIANT" read as legal advice** | None yet. | Fixed footer on every verdict: "rule-engine result on stated facts; not legal advice". |
| **Human rubber-stamping** | Hashed, time-limited approval; clone-test result shown. | Console shows counter-evidence and the three alternative readings. Log approver dwell time. |

---

## 3. Part 2: country recommendation

### 3a. Rubric (0-5; for effort, 5 means no work; fit and effort favour India by construction)

| Country | Clarity of obligation | NTN / ground-segment coverage | Binding clock | Open English text | Fit with Chennai / current KB | Effort to switch in 3 days | Total /30 | Policy only /20 |
|---|---|---|---|---|---|---|---|---|
| **India** | 4 | 4 | 5 | 4 | 5 | 5 | **27** | 17 |
| Australia | 5 | 5 | 5 | 5 | 1 | 1 | 22 | 20 |
| EU (NIS2) | 3 | 3 | 5 | 5 | 3 | 3 | 22 | 16 |
| USA | 3 | 5 | 4 | 5 | 1 | 2 | 20 | 17 |
| Singapore | 4 | 2 | 5 | 3 | 1 | 2 | 17 | 14 |
| UK | 3 | 3 | 3 | 4 | 1 | 2 | 16 | 13 |
| UAE | 1 | 1 | 0 | 3 | 2 | 3 | 10 | 5 |

Scores are my judgement from the evidence below. Australia is the clearest on policy alone. USA satellite coverage is outage reporting, not a cyber rule. Singapore NTN coverage is unverified.

### 3b. Evidence per country

**India (current KB).** All verified against PDFs already in `kb/sources/`.
- CERT-In Directions, 28 Apr 2022, binding, issued under IT Act s.70B(6). Direction (ii): "within 6 hours of noticing". Effective "after 60 days from the date" of issue (PDF text), so 27 Jun 2022. The KB leaves this null.
- Telecom Cyber Security Rules 2024 R7(1), 21 Nov 2024, 6 h from occurrence, to DoT. Critical Telecom Infrastructure Rules 2024 R7(1)(j), 22 Nov 2024, 6 h from occurrence, designated assets only.
- NEW, verified: Telecommunications Act 2023 s.2(s), Gazette of India Extraordinary Part II Sec. 1, p.3: "telecommunication network means a system or series of systems of telecommunication equipment or infrastructure, including terrestrial or satellite networks or submarine networks". Binding; commencement in phases, so confirm the date for s.2.
- CERT-In/SIA-India space framework, 26 Feb 2026: SatCom operators report in 6 h (§3.2.1). PIB release 2233122 says it is advisory (corrected 7 Nov).
- Weakness: no downstream-warning duty (`GAP-IN-02`), no priority order, and the space framework's binding status is unclear. That is what ORCA-NTN exposes.

**UAE (host).**
- UAE Information Assurance Regulation v1.1, March 2020 (not 2019, as `country-documents.md` says), TDRA. Verified from the PDF: incident management controls speak of "reported within specified timeframes" and "required timeframe", with no number.
- TDRA Interconnection Instructions v1.2: emergency calls get the highest priority at points of interconnection (already `AE-TDRA-IC-2006-EMERGENCY`).
- TDRA press release, 12 Aug 2026: e& and du licences renewed 9 Aug 2026 to 8 Aug 2046 with "a comprehensive framework covering network resilience, backup capacity and international connectivity". The licence text is not public, and the release does not mention cyber security.
- u.ae cyber-safety page: no organisational incident duty or deadline.
- Cyber Security Council Cyber Incident Response Framework page: could not open (connection closed). **UNVERIFIED.** Consultancy blogs give conflicting hours (24 h, "2-4 h"); I do not use them.
- Verdict: no binding public clock or satellite cyber rule found. Not a basis for a rule engine.

**Australia.** Verified from the compiled Act, 4 Jun 2026 compilation (`legislation.gov.au/C2018A00029`).
- Security of Critical Infrastructure Act 2018 s.30BC(1)(d): report "as soon as practicable, and in any event within 12 hours" after the entity becomes aware of a cyber security incident that "has had, or is having, a significant impact (whether direct or indirect) on the availability of the asset". Recipient is the relevant Commonwealth body (s.30BF), which is ASD if no rules specify otherwise. Civil penalty 50 penalty units. Oral reports need a written record within 84 hours (s.30BC(3)).
- s.30BD(1)(d): other incidents with a "relevant impact", 72 hours; written record 48 hours.
- s.5: "critical telecommunications asset" is a carrier- or CSP-owned network or asset used to supply or in connection with a carriage service. "Satellite-based facility" is defined by reference to the Telecommunications Act 1997. s.9(2C) keeps satellites in scope even when located outside Australia if they are on the Register of Space Objects or Australia is the Article VI State.
- s.12M defines "cyber security incident" (unauthorised access, modification or impairment).
- Part 2B applies to telecoms only through the Application Rules: LIN 22/026 s.5(1)(u), added by LIN 25/011. The compilation dated 04/04/2025 shows it. That date matches the Schedule 5 commencement reported by search results (4 Apr 2025); I could not open the Home Affairs or CISC pages (403), so treat the commencement date as UNVERIFIED.
- Binding, English, openly available. The best NTN-explicit statute I found.

**EU (NIS2) / member state.** Verified from `kb/sources/eu-nis2-2022.html`.
- Art. 23(4)(a)-(d): early warning 24 h, notification 72 h, final report within one month, from becoming aware. Art. 23(2): inform potentially affected service recipients.
- Annex I point 8 lists providers of public electronic communications networks. Annex I point 11 (Space) covers ground-based infrastructure but "excluding providers of public electronic communications networks". So satellite network providers fall under point 8, not point 11. This refines the CLAUDE.md line "NIS2 space covers ground infrastructure only".
- A directive applies only through national law. Germany's transposition (`NIS2UmsuCG`, §32 BSIG) is reported in force from 6 Dec 2025, but only consultancy pages said so: **UNVERIFIED**, and German-language. So the EU is a good comparison and a poor primary KB.

**UK.**
- Communications Act 2003 s.105K (inserted by the Telecommunications (Security) Act 2021): per Ofcom, providers must inform Ofcom "as soon as reasonably practicable" of a security compromise with a significant effect on the network or service. s.105J duty to inform users of significant risk.
- Ofcom's statement under s.105Y (PDF, February 2023) expects an initial notice "usually within 3 hours" for urgent compromises and the full report within 72 hours; this is guidance, not statute.
- I could not open the statute on legislation.gov.uk (the page returned an empty response and I did not work around it), so the s.105K wording is from Ofcom's paraphrase. **UNVERIFIED primary.** A May 2026 Ofcom consultation on updating the statement is mentioned in search results only: UNVERIFIED.
- No satellite-specific text found.

**USA.** Verified through the eCFR renderer; wording was relayed by the fetch tool, so recheck verbatim before quoting.
- 47 CFR 4.9(c): satellite operators and providers notify the FCC "within 120 minutes of discovering" qualifying outages of at least 30 minutes (for example loss of a satellite or transponder, or 900,000 user-minutes). Initial report within 72 hours, final within 30 days. §4.5(a) defines an outage as a significant degradation in an end user's ability to communicate.
- This is outage reporting, not a cyber-incident rule. The CIRCIA cyber-incident rule (72 h/24 h) was, according to search results, sent to OMB on 1 Oct 2026 and not yet published. **UNVERIFIED and not in force.**

**Singapore.**
- Cybersecurity Act 2018 s.14(1) and the CII Regulations. CSA page (opened): provider-owned CII owners notify "within 2 hours from awareness", supplementary details within 72 hours, a final report within 30 days.
- Gazette S 678/2025 (opened), in operation 31 Oct 2025, amends regulation 5 (72 h supplementary, 30-day final).
- Satellite coverage not found. Singapore Statutes Online returned 403, so the exact 2-hour text of regulation 5(1)(a) is **UNVERIFIED**.

### 3c. Recommendation

**India primary + EU comparison for scenario 3 (already built).** Reasons:
1. Binding clocks, named authorities, English official text and an explicit satellite-network definition already exist (rubric 27/30).
2. Messy overlap (three 6 h clocks, unclear space-framework status, no downstream warning, no priority order) gives six honest verdicts and real hand-offs. A single clean regime like Australia's would show fewer AMBIGUITY and CONFLICT cases.
3. The EU contrast (Art. 23(2)) is already coded as `EU-NIS2-2022-ART23-2`.
4. Australia is the better statute, but its cost is the whole story and KB, with no scoring benefit under rule 6.

**Optional stretch (after the rule engine passes tests, about 3 h):** add three verified Australian records to `kb/global/`: s.30BC(1) (12 h), s.5 "critical telecommunications asset", s.9(2C) (satellite). Add `AU` to `JURISDICTIONS` in `orca/kb.py`. This gives one report sentence: "Among the countries we checked, only Australia's critical-infrastructure statute names satellite facilities with extraterritorial reach." Say "among those we checked", not "only". Skip if time is short.

### 3d. If we switch anyway: what changes and the cost

| Change | Hours |
|---|---|
| New KB `kb/au/` of about 14-18 records with quote verification, new `sources.yaml` entries and hashes | 6-8 |
| New gap register (Australian gaps), rewritten rules YAML and unit tests | 5-6 |
| Agent roles and playbook owners renamed (CERT-In/DoT → ASD/CISC/ACMA and home affairs) | 2 |
| Move story and scenarios U1-U6 from Chennai to an Australian city; regenerate synthetic data with local rain-fade parameters | 8-10 |
| Report, README, HTML and figures rewritten | 4-6 |
| Re-verify everything and handle the hand-off | 3-4 |
| **Total** | **28-36** |

If we stay with India: add `IN-TELACT-2023-2-s` (verified quote above, about 20 min), set `in_force_from: 2022-06-27` on the three CERT-In Direction records, and apply the stale-law guards in 2e (about 2-3 h in total).

---

## 4. Open questions for the user

1. Approve India primary + EU comparison, with Australia as an optional 3-record stretch?
2. Where will Qwen3.8 run? CERT-In Direction (iv) requires logs "within the Indian jurisdiction" (`IN-CERTIN-DIR-2022-iv`). If the Google Cloud endpoint is outside India, the engine's own policy would flag it. A Mumbai or Delhi region fixes that.
3. Which human roles appear on the demo console (incident commander, CISO, counsel, DPO, Gap Analyst)? Part 1 assumes these five.
4. Who downloads the blocked PDFs (Telecom Cyber Security Rules 2024 and its 2025 amendment, DPDP Act and Rules, IT Act)? Until then, `IN-TCSR-2024-R7-1` cannot be checked against its current text.
5. Should the report say "not legal advice" in the explainability section? I recommend yes.
6. How should the report describe the 2026 space framework: "legal status not stated"? I recommend that exact wording.

---

## 5. Sources opened

**VERIFIED (opened official text):**
- Security of Critical Infrastructure Act 2018, 4 Jun 2026 compilation, https://www.legislation.gov.au/C2018A00029/2026-06-04/2026-06-04/text/original/epub/OEBPS/document_1/document_1.html (ss.5, 9(2B)-(2D), 12M, 30BB, 30BC, 30BD, 30BF)
- Security of Critical Infrastructure (Application) Rules (LIN 22/026) 2022, compilation 04/04/2025, https://www.legislation.gov.au/F2022L00562/2025-04-04/2025-04-04/text/original/pdf (s.5(1)(u))
- Security of Critical Infrastructure Amendment (2025 Measures No. 1) Rules 2025 (LIN 25/011), https://www.legislation.gov.au/F2025L00324/asmade/2025-03-13/text/original/pdf (commencement clause only)
- 47 CFR 4.9, 4.5, 4.1, 64.2011 via https://www.ecfr.gov/ (wording relayed by the fetch tool; recheck before quoting)
- Ofcom, General statement of policy under s.105Y (Feb 2023), https://www.ofcom.org.uk/__data/assets/pdf_file/0030/253677/General-statement-of-policy-under-section-105Y-of-the-Communications-Act-2003.pdf
- Singapore Gazette S 678/2025, https://assets.egazette.gov.sg/2025/Legislative%20Supplements/Subsidiary%20Legislation%20Supplement/678.pdf; CSA forms page, https://www.csa.gov.sg/legislation/forms/
- NIS2 (Directive (EU) 2022/2555), local `kb/sources/eu-nis2-2022.html`
- Local India PDFs in `kb/sources/`: Telecommunications Act 2023, CERT-In Directions 2022, CERT-In/SIA-India space framework 2026
- TDRA UAE Information Assurance Regulation v1.1 (March 2020), https://tdra.gov.ae/-/media/About/regulations-and-ruling/EN/UAE-Information-Assurance-Regulation-v1-1-pdf.ashx
- TDRA press release 12 Aug 2026, https://tdra.gov.ae/en/media/press-release/2026/digital-infrastructure-and-the-digital-economy
- u.ae cyber safety page, https://u.ae/en/information-and-services/justice-safety-and-the-law/Safety/cyber-safety-and-digital-security (no duty found)
- Project files: HANDOFF_NEXT_CHAT.md, BUILD_PLAN.md, `kb/` (SCHEMA, sources, India, global, gaps), `orca/kb.py`, `charan/country-documents.md`

**UNVERIFIED (could not open an official text, or only secondary reports):**
- UK Communications Act 2003 s.105J/105K statute text (legislation.gov.uk returned an empty page; I did not work around it)
- Singapore Statutes Online regulation 5(1)(a) 2-hour wording (403)
- UAE Cyber Security Council Cyber Incident Response Framework page (connection closed)
- Home Affairs and CISC telecom pages (403): commencement of SOCI Schedule 5 on 4 Apr 2025 (only inferred from the 04/04/2025 compilation date and search results)
- CIRCIA final-rule status (search results only)
- German NIS2UmsuCG/§32 BSIG in force 6 Dec 2025 (consultancy pages only)
- Ofcom's May 2026 consultation (search results only)
- Items listed as unverified in CLAUDE.md that I did not touch: UAE Decree-Law 46/2023 repeal, UAE AI Charter year, 3GPP TS 32.541
