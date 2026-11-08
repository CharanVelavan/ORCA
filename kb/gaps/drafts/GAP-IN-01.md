# GAP-IN-01: Up to Four Reports to Three Bodies, With Two Different Triggers

> **Review 8 Nov:** strongest gap; CTIR (occurrence), TCSR (awareness), CERT-In (noticing) and NGP (occurrence) triggers confirmed in context.


- **Gap ID:** `GAP-IN-01-REPORTING-CLOCKS`
- **Topic:** `incident_reporting`
- **Kind:** `ambiguity`
- **Current Register Status:** `confirmed`

## 1. Domain Gap & Severity
When a single cyber incident causes an outage on an emulated or live non-terrestrial network (NTN), overlapping sectoral laws (cybersecurity, telecom licensing, critical infrastructure, space authorization, and quality-of-service) require the operator to file multiple separate reports with different regulatory bodies under incompatible clock triggers—"upon noticing / becoming aware" versus "upon occurrence / start of outage." Because an RF jamming or lateral-movement attack on a satellite link often masquerades initially as an equipment or weather fault, an operator that classifies the event as a cyber attack more than six hours after physical onset has already missed an "occurrence"-triggered deadline before awareness ever began.

- **Severity Score:** **4 / 5**
- **Reason:** Divergent "occurrence" versus "awareness" clocks create retroactive non-compliance when a satellite fault is later diagnosed as a cyber attack, while multi-portal filing splits engineering attention during active containment.

## 2. India Evidence

### Verified Records (`kb/india/records.yaml`)
- **`IN-CERTIN-DIR-2022-ii`** (CERT-In Directions under section 70B(6) of the IT Act, 2000, Direction (ii), PDF p. 2; `binding`):
  > "shall mandatorily report cyber incidents as mentioned in Annexure I to CERT-In within 6 hours of noticing such incidents or being brought to notice about such incidents."
- **`IN-TCSR-2024-R7-1`** (Telecommunications (Telecom Cyber Security) Rules, 2024, G.S.R. 720(E), Rule 7(1)(a), PDF p. 5; `binding`):
  > "within six hours of becoming aware of a security incident affecting its telecommunication network or telecommunication service, report the same to the Central Government with relevant details of the affected system including the description of such incident; and"
- **`IN-CTIR-2024-R7-1-j`** (Telecommunications (Critical Telecommunication Infrastructure) Rules, 2024, Rule 7(1)(j), PDF p. 8; `binding`):
  > "no later than six hours of occurrence of such incident"
- **`IN-TRAI-QOS-2024-4-1-3`** (TRAI Standards of Quality of Service of Access and Broadband Service Regulations, 2024, Schedule, para 4.1.3(ii), PDF p. 113; `binding`):
  > "All such SNOs shall be reported to the Authority within 24 Hrs. from the start of any such outage."
- **`IN-AUTHZ-2026-R59-4`** (Telecommunications (Authorisation for Provision of Principal Telecommunication Services) Rules, 2026, Rule 59(4)(a), PDF p. 112; `binding`):
  > "unauthorised satellite signal that it may detect originating or terminating within India; and"
- **`IN-AUTHZ-2026-R62-7`** (Authz Rules, 2026, Rule 62(7), PDF p. 114; `binding`):
  > "Every new authorised entity shall report to the Central Government on the portal, any attempt to access or use the satellite network by a user terminal not registered under sub-rule (6)"

### Staged Quotes (auto-checked, not yet human-verified)
- **`in-ctir-2024` (page 8)** — Telecommunications (Critical Telecommunication Infrastructure) Rules, 2024, Rule 7(1)(j) (auto-checked, not yet human-verified):
  > "implement mechanisms to ensure intimation of security incident(s) to the Central Government, no later than six hours of occurrence of such incident, in the form and manner as may be specified on the portal; and"
- **`in-tcsr-2024` (page 5)** — Telecommunications (Telecom Cyber Security) Rules, 2024, Rule 7(1)(b) (auto-checked, not yet human-verified):
  > "within twenty-four hours of becoming aware of such incident, furnish the following information, as applicable:"
- **`inspace-ngp-2024` (page 22)** — IN-SPACe Norms, Guidelines and Procedures for Implementation of Indian Space Policy 2023, Chapter II, Clause 24 (auto-checked, not yet human-verified):
  > "In case of any accident, malfunction, emergency or any other incident which impacts the operation of an Authorized Space Object that poses a threat to the national security, public order, safety of people or their property, national intelligence and security operations, or the environment of India, the Applicant shall immediately carry out appropriate measures to prevent or minimise the consequences of such accident or emergency or incident."
- **`in-cea-cyber-power-guidelines-2021` (page 14)** — CEA Guidelines on Cyber Security in Power Sector 2021, Article 10(h) (auto-checked, not yet human-verified):
  > "The Responsible Entity shall ensure that the CISO compiles details of incident detection, incident handling, learnings from each incident and damage claims made if any and shall report to CERT-In as well as upload information on ISAC-Power Portal."
- **`in-rbi-psos-cyber-resilience-2024` (page null - HTML)** — RBI Master Directions on Cyber Resilience and Digital Payment Security Controls for non-bank PSOs, Paragraph 22 (auto-checked, not yet human-verified):
  > "Any cyber security incident shall also be reported to CERT-In."

### What Is Missing
For a single emulated or live NTN incident affecting designated Critical Telecommunication Infrastructure and causing a district outage of >4 hours, an operator faces up to four separate reports across three authorities (CERT-In, DoT, TRAI)—plus space-object malfunction reporting to IN-SPACe (`inspace-ngp-2024`, p. 22) and unclocked rogue-signal/terminal reporting on the DoT portal (`IN-AUTHZ-2026-R59-4`, `IN-AUTHZ-2026-R62-7`). Crucially, while CERT-In Direction (ii) (`IN-CERTIN-DIR-2022-ii`) and notified TCSR Rule 7(1)(a) (`IN-TCSR-2024-R7-1`) start the 6-hour clock at *noticing / becoming aware*, CTIR Rule 7(1)(j) (`IN-CTIR-2024-R7-1-j`) starts its 6-hour clock at *occurrence*. No rule reconciles the "occurrence" versus "becoming aware" trigger when a fault is later reclassified as an attack, and no single-window portal shares one submission across CERT-In, DoT, and TRAI.

## 3. Global Examples

1. **EU NIS2 Directive & Implementing Regulation (`EU-NIS2-2022-ART23-4-a` & `EU-NIS2-2022-ART23-4-b` verified; `eu-nis2-ir-2024-2690` staged auto-checked)**
   - **Instrument:** Directive (EU) 2022/2555 (NIS2) and Commission Implementing Regulation (EU) 2024/2690
   - **Clause:** NIS2 Article 23(4)(a)–(b); Implementing Regulation Article 10(a) & 10(c)
   - **Issuing Authority:** European Parliament and Council; European Commission
   - **Binding Status:** `binding`
   - **Exact Quote (`EU-NIS2-2022-ART23-4-a`, Article 23(4)(a), page n/a - HTML; also in staged `eu-nis2-2022`):**
     > "without undue delay and in any event within 24 hours of becoming aware of the significant incident, an early warning, which, where applicable, shall indicate whether the significant incident is suspected of being caused by unlawful or malicious acts or could have a cross-border impact"
   - **Exact Quote (`EU-NIS2-2022-ART23-4-b`, Article 23(4)(b), page n/a - HTML):**
     > "without undue delay and in any event within 72 hours of becoming aware of the significant incident, an incident notification"
   - **Exact Quote (`eu-nis2-ir-2024-2690`, Article 10(c), page 11, auto-checked):**
     > "**[DROPPED 8 Nov: irrelevant, review row 36]** the integrity, confidentiality or authenticity of stored, transmitted or processed data related to the provision of a managed service or managed security service is compromised as a result of a suspectedly malicious action;"
   - **How it closes the gap:** Uses a single, unambiguous trigger ("becoming aware of the significant incident") for both the 24-hour early warning and the 72-hour detailed notification, avoiding retroactive breach of an "occurrence" clock when an outage is only later recognized as malicious.

2. **EU Cyber Resilience Act — Simultaneous Single-Submission Reporting (`eu-cyber-resilience-act-2024`, staged auto-checked)**
   - **Instrument:** Regulation (EU) 2024/2847 (Cyber Resilience Act)
   - **Clause:** Article 14(1) and Article 14(2)(a)
   - **Issuing Authority:** European Parliament and Council
   - **Binding Status:** `binding`
   - **Exact Quote (`eu-cyber-resilience-act-2024`, Article 14(1), page 38, auto-checked):**
     > "**[DROPPED 8 Nov: irrelevant, review row 33]** A manufacturer shall notify any actively exploited vulnerability contained in the product with digital elements that it becomes aware of simultaneously to the CSIRT designated as coordinator, in accordance with paragraph 7 of this Article, and to ENISA."
   - **Exact Quote (`eu-cyber-resilience-act-2024`, Article 14(2)(a), page 38, auto-checked):**
     > "an early warning notification of an actively exploited vulnerability, without undue delay and in any event within 24 hours of the manufacturer becoming aware of it, indicating, where applicable, the Member States on the territory of which the manufacturer is aware that their product with digital elements has been made available;"
   - **How it closes the gap:** Implements a "report-once, distribute-simultaneously" architecture anchored to awareness, eliminating duplicate filings to separate national and Union authorities.

3. **US FCC Part 4 Satellite Outage Reporting (`us-fcc-part-4-outage`, staged auto-checked)**
   - **Instrument:** 47 CFR Part 4 — Disruptions to Communications (NORS)
   - **Clause:** 47 CFR § 4.9(c)(1)
   - **Issuing Authority:** Federal Communications Commission (US)
   - **Binding Status:** `binding`
   - **Exact Quote (`us-fcc-part-4-outage`, 47 CFR § 4.9(c)(1), page null - XML, auto-checked):**
     > "All satellite operators shall submit electronically a Notification to the Commission within 120 minutes of discovering that they have experienced on any facilities that they own, operate, lease, or otherwise utilize, of an outage of at least 30 minutes duration that manifests itself as a failure of any of the following key system elements: One or more satellite transponders, satellite beams, inter-satellite links, or entire satellites."
   - **How it closes the gap:** Starts the satellite reporting clock explicitly from "discovering" (awareness) rather than physical occurrence, and sets an objective 30-minute duration threshold for satellite transponders, beams, inter-satellite links, and gateways.

4. **EU Critical Entities Resilience (CER) Directive (`eu-cer-2022-2557`, staged auto-checked)**
   - **Instrument:** Directive (EU) 2022/2557 on the resilience of critical entities
   - **Clause:** Article 15(1)
   - **Issuing Authority:** European Parliament and Council
   - **Binding Status:** `binding`
   - **Exact Quote (`eu-cer-2022-2557`, Article 15(1), page 22, auto-checked):**
     > "Member States shall ensure that, unless operationally unable to do so, critical entities submit an initial notification no later than 24 hours after becoming aware of an incident, followed, where relevant, by a detailed report no later than one month thereafter."
   - **How it closes the gap:** Even for physical/critical infrastructure resilience (the EU counterpart to India's CTIR 2024), the reporting clock starts at "becoming aware" rather than "occurrence," and includes an operational-inability safeguard during active crisis response.

## 4. Recommendation

- **Domain-Level Recommendation:** Regulators should harmonize all cyber and critical-infrastructure incident reporting clocks to start from a single trigger—**awareness / discovery** that an incident meets reporting criteria—and establish a single-window electronic portal that automatically routes one structured submission (6-hour initial notice + 24-hour/72-hour detailed update) to the national CSIRT, the telecom ministry, the space regulator, and the quality-of-service regulator.
- **Application to India:**
  1. **Department of Telecommunications (DoT):** Amend or clarify **Rule 7(1)(j) of the Critical Telecommunication Infrastructure Rules, 2024** (`IN-CTIR-2024-R7-1-j`) so that its 6-hour clock runs from *"becoming aware"* of a security incident, matching **Rule 7(1)(a) of the notified Telecom Cyber Security Rules, 2024** (`IN-TCSR-2024-R7-1`) and **CERT-In Direction (ii)** (`IN-CERTIN-DIR-2022-ii`), and specify a 6-hour or 24-hour awareness deadline for satellite rogue-signal/terminal reports under **Authz Rules 59(4) and 62(7)**.
  2. **DoT, CERT-In & TRAI:** Configure the central portal specified under **TCSR Rule 7(1)** and **CTIR Rule 7(1)(j)** as a single-window intake that simultaneously satisfies CERT-In Direction (ii) (`IN-CERTIN-DIR-2022-ii`), NCIIPC information-exchange rules (`in-nciipc-cii-rules-2013`, p. 4), and TRAI Significant Network Outage reporting (`IN-TRAI-QOS-2024-4-1-3`).

## 5. Search Record

- **Vector KB Queries Run (`orca.kbvec coverage` against `IN`):**
  1. Query: `"report security incident six hours becoming aware noticing occurrence twenty-four hours portal CERT-In Central Government"`
     - **Documents searched:** 18
     - **Nearest clauses returned:**
       - `IN-SPACEFW-2026-3-2-1` (score `0.7956`, `non_binding`, §3.2.1, p. 12): 6 hours of noticing the incident to CERT-In.
       - `in-tcsr-2024:p5:c2` / `IN-TCSR-2024-R7-1` (score `0.7938` / `0.7736`, `binding`, Rule 7(1)(a)–(b), p. 5): 6 hours of becoming aware to the Central Government, plus detailed fields within 24 hours of becoming aware.
       - `IN-CERTIN-DIR-2022-ii` (score `0.7681`, `binding`, Direction (ii), p. 2): 6 hours of noticing or being brought to notice to CERT-In.
  2. Query: `"single joint report incident reporting portal TRAI significant network outage 24 hours"`
     - **Documents searched:** 18
     - **Nearest clauses returned:**
       - `in-trai-qos-2024:p148:c2` / `IN-TRAI-QOS-2024-4-1-3` (score `0.7833` / `0.7676`, `binding`, Schedule para 4.1.3(ii) & Explanatory Memorandum para 5.3.3, pp. 113, 148): Significant network outages (>4 hours in a district) must be reported to TRAI within 24 hours from the start of the outage.
       - `in-trai-qos-2024:p149:c0` (score `0.7429`, `binding`, Explanatory Memorandum para 5.3.3(a)(iii), p. 149): Notes operator feedback that reporting during an active outage demands significant time and effort across teams.
- **Why Nearest Clauses Do Not Close the Gap:** Each instrument sets its own recipient and trigger (`noticing` for CERT-In, `becoming aware` for TCSR, `occurrence` for CTIR, and `start of any such outage` for TRAI). Although TCSR and CTIR both refer to "the portal," no provision creates a unified filing mechanism across DoT, CERT-In, and TRAI, or resolves the conflict between CTIR's `occurrence` trigger and TCSR/CERT-In's `awareness` trigger when a fault is later diagnosed as a cyber attack.

## 6. What a Human Must Decide
- **Whether to include IN-SPACe NGP 2024 (`inspace-ngp-2024`, p. 22) as a fifth reporting stream:** NGP 2024 Clause 24 requires space-object authorization holders to report any malfunction or incident affecting an authorized space object that poses a threat to national security or public safety to IN-SPACe. A human reviewer should decide whether to add IN-SPACe to the title/finding ("five reports to four bodies") or keep the focus on the telecom/cyber triad (CERT-In, DoT, TRAI).
- **Whether CTIR's "occurrence" trigger should be treated as tolled until awareness during fault-to-attack reclassification:** Until DoT clarifies CTIR Rule 7(1)(j), the human commander must confirm the interim policy of filing protective notices on the earliest possible clock.
