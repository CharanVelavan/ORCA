# GAP-IN-02: No Binding Duty for a Satellite Operator to Warn Downstream Dependent Services

- **Gap ID:** `GAP-IN-02-NO-DOWNSTREAM-WARNING`
- **Topic:** `downstream_warning`
- **Kind:** `coverage`
- **Current Register Status:** `confirmed`

## 1. Domain Gap & Severity
When a cyber incident or outage compromises an emulated or live non-terrestrial network (NTN) gateway or feeder link, incident reporting rules typically route notifications upward to national cyber agencies and telecom regulators, without imposing a binding, time-bounded duty on the satellite operator to warn downstream dependent services (mobile operators using satellite backhaul, power utilities, emergency call centres, hospitals, or payment networks). Compounded by strict confidentiality rules against sharing network topology or status without prior government consent, dependent critical infrastructure operators learn of upstream NTN compromise only after their own services fail or after attacker traffic traverses the link.

- **Severity Score:** **4 / 5**
- **Reason:** Delayed warning to downstream mobile operators, power-grid telemetry nodes, and emergency services prevents timely local failover or defensive isolation while an upstream emulated or live NTN incident unfolds.

## 2. India Evidence

### Verified Records (`kb/india/records.yaml`)
- **`IN-SPACEFW-2026-ANXB-IV`** (CERT-In / SIA-India Cyber Security Framework and Guidelines for Space including Satellite Communication, Annexure B, IV Respond, PDF p. 48; `non_binding`):
  > "Stakeholders: Establish procedures for notifying critical infrastructure partners, regulatory bodies, and customers, especially when service disruption occurs."
- **`IN-PIB-2026-SPACEFW-ADVISORY`** (PIB release 2233122, MeitY, 26 Feb 2026; `non_binding`):
  > "These guidelines are advisory in nature and are intended to advance cyber security preparedness across the space sector."
- **`IN-AUTHZ-2026-R37-5`** (Telecommunications (Authorisation for Provision of Principal Telecommunication Services) Rules, 2026, Rule 37(5), PDF p. 101; `binding`):
  > "Every new authorised entity shall not share any information relating to its telecommunication network with any other person except with the prior approval of the Central Government in writing"
- **`IN-TCSR-2024-R7-2`** (Telecommunications (Telecom Cyber Security) Rules, 2024, G.S.R. 720(E), Rule 7(2), PDF p. 5; `binding`):
  > "The Central Government may, where it determines that disclosure of the security incident is in the public interest, inform the public of such security incident, or require the affected telecommunication entity to do so."
- **`IN-AUTHZ-2026-R38-2-a`** (Authz Rules, 2026, Rule 38(2)(a), PDF p. 101; `binding`):
  > "facilitate dissemination of alert messages through short message service, cell broadcast or any other means as may be directed by Central Government, State Government or any officer authorised in this behalf"
- **`IN-ITACT-2000-70B-4`** (Information Technology Act, 2000, Section 70B(4), PDF p. 30; `binding`):
  > "(d) coordination of cyber incidents response activities;"

### Staged Quotes (auto-checked, not yet human-verified)
- **`in-space-cyber-framework-2026` (page 32)** — CERT-In / SIA-India Space Framework, Clause 6.5 (auto-checked, not yet human-verified):
  > "Unified Incident Response: Ensure coordinated procedures among operators, ground stations, and service providers."
- **`in-tcsr-2024` (page 5)** — Telecommunications (Telecom Cyber Security) Rules, 2024, Rule 7(2) (auto-checked, not yet human-verified):
  > "The Central Government may, where it determines that disclosure of the security incident is in the public interest, inform the public of such security incident, or require the affected telecommunication entity to do so."
- **`in-nciipc-cii-rules-2013` (page 3)** — Information Technology (NCIIPC and Manner of Performing Functions and Duties) Rules, 2013, Rule 4(5) (auto-checked, not yet human-verified):
  > "Coordinating, sharing, monitoring, collecting, analysing and forecasting, national-level threats to critical information infrastructure for policy guidance, expertise-sharing and situational awareness for early warning or alerts."
- **`in-dot-cell-broadcast-rules-2023` (page 3)** — Indian Wireless Telegraphy (Cell Broadcasting Service for Disaster Alerts) Rules, 2023, Rule 2(c) (auto-checked, not yet human-verified):
  > "\"cell broadcast\" means a method of sending messages to multiple mobile telephone users in a defined area at the same time in a broadcast manner."
- **`in-dot-telecom-standards-rules-2025` (page 9)** — Telecommunications (Framework to Notify Standards, Conformity Assessment and Certification) Rules, 2025, Rule 10(1) (auto-checked, not yet human-verified):
  > "An authorised entity or a licensee shall, upon becoming aware that a user of its telecommunication services is using telecommunication equipment that does not have a valid Certificate of Conformity Assessment, issue a notice in writing to such user seeking discontinuance by the user of such telecommunication equipment within a period of seven days from the date of issuance of the notice."

### What Is Missing
India's binding laws create upward reporting duties to CERT-In, DoT, and TRAI, give the Central Government discretion to disclose security incidents to the public (`IN-TCSR-2024-R7-2`), and assign early-warning dissemination functions to CERT-In (`IN-ITACT-2000-70B-4`) and NCIIPC (`in-nciipc-cii-rules-2013`, p. 3). However, no binding rule requires a satellite or telecom operator to directly warn downstream critical-infrastructure dependants (mobile operators, power utilities, PSAPs, hospitals, or banks) within a set timeframe when an incident threatens service continuity or integrity. Worse, **Authz Rule 37(5)** (`IN-AUTHZ-2026-R37-5`) prohibits a new authorised entity from sharing any information relating to its telecommunication network with any other person (except equipment suppliers/manufacturers) without prior written Central Government approval, creating a legal barrier to rapid peer-to-dependent technical warnings.

## 3. Global Examples

1. **EU NIS2 Directive — Direct Notification of Affected Service Recipients (`EU-NIS2-2022-ART23-1` & `EU-NIS2-2022-ART23-2`, verified records)**
   - **Instrument:** Directive (EU) 2022/2555 (NIS2)
   - **Clause:** Article 23(1), second sentence, and Article 23(2)
   - **Issuing Authority:** European Parliament and Council
   - **Binding Status:** `binding` (via Member State transposition)
   - **Exact Quote (`EU-NIS2-2022-ART23-1`, Article 23(1), page n/a - HTML; also in staged `eu-nis2-2022`):**
     > "Where appropriate, entities concerned shall notify, without undue delay, the recipients of their services of significant incidents that are likely to adversely affect the provision of those services."
   - **Exact Quote (`EU-NIS2-2022-ART23-2`, Article 23(2), page n/a - HTML):**
     > "essential and important entities communicate, without undue delay, to the recipients of their services that are potentially affected by a significant cyber threat any measures or remedies that those recipients are able to take in response to that threat"
   - **How it closes the gap:** Imposes a direct, binding obligation on covered operators (including telecom and space ground-infrastructure operators) to warn downstream service recipients without undue delay about both active significant incidents and significant cyber threats, including actionable remedies recipients can take.

2. **US FCC 911 Reliability Order — 30-Minute Downstream Outage Notification to Emergency Facilities (`us-fcc-911-reliability-2013`, staged auto-checked)**
   - **Instrument:** FCC Report and Order 13-158 / 47 CFR Part 4 & Part 12 (Improving 911 Reliability)
   - **Clause:** Appendix B, 47 CFR § 4.9(h)
   - **Issuing Authority:** Federal Communications Commission (US)
   - **Binding Status:** `binding`
   - **Exact Quote (`us-fcc-911-reliability-2013`, Appendix B, 47 CFR § 4.9(h), page 64, auto-checked):**
     > "In addition to any other obligations imposed in this section, within thirty minutes of discovering an outage that potentially affects a 911 special facility (as defined in § 4.5), all Covered 911 Service Providers (as defined in § 12.4(a)(4)) shall notify as soon as possible but no later than thirty minutes after discovering the outage any official who has been designated by the affected 911 special facility as the provider’s contact person(s) for communications outages at that facility and convey all available information that may be useful in mitigating the effects of the outage, as well as a name, telephone number, and e-mail address at which the service provider can be reached for follow-up."
   - **How it closes the gap:** Establishes a strict 30-minute clock from discovery for upstream communication providers to directly notify designated downstream emergency facility contacts and share all available information useful for mitigating the outage.

3. **EU Electronic Communications Code — Mandatory Transmission of Emergency Warnings (`eu-eecc-2018-1972`, staged auto-checked)**
   - **Instrument:** Directive (EU) 2018/1972 establishing the European Electronic Communications Code
   - **Clause:** Article 110(1)
   - **Issuing Authority:** European Parliament and Council
   - **Binding Status:** `binding`
   - **Exact Quote (`eu-eecc-2018-1972`, Article 110(1), page 148, auto-checked):**
     > "Member States shall ensure that, when public warning systems regarding imminent or developing major emergencies and disasters are in place, public warnings are transmitted by providers of mobile number-based interpersonal communications services to the end-users concerned."
   - **How it closes the gap:** Supplements B2B service-recipient warnings under NIS2 with mandatory downstream warning transmission to end-users during developing emergencies.

## 4. Recommendation

- **Domain-Level Recommendation:** Telecom and space regulators should require NTN and backhaul operators to notify downstream dependent critical-infrastructure operators (mobile networks, power utilities, emergency call centres, hospitals, payment providers) without undue delay—and within a defined short window (e.g., 30 to 60 minutes of awareness)—whenever a security incident or outage on an emulated or live NTN link is likely to adversely affect downstream service availability or integrity, accompanied by a safe-harbour carve-out from network non-disclosure rules for operational threat and outage warnings.
- **Application to India:**
  1. **Department of Telecommunications (DoT):** Amend **Rule 7 of the Telecommunications (Telecom Cyber Security) Rules, 2024** (`in-tcsr-2024`) to add a binding operator-to-dependent-service notification duty (modelled on NIS2 Art. 23(1)–(2) and Advisory Space Framework Annexure B item 4.2, `IN-SPACEFW-2026-ANXB-IV`) when a security incident affects wholesale backhaul or critical infrastructure customers.
  2. **DoT:** Issue a standing written carve-out or proviso under **Rule 37(5) of the 2026 Authorisation Rules** (`IN-AUTHZ-2026-R37-5`) permitting new authorised entities to share operational incident indicators, link degradation notices, and recommended defensive remedies with downstream dependent telecom and critical-infrastructure entities without awaiting case-by-case prior written Central Government approval.

## 5. Search Record

- **Vector KB Queries Run (`orca.kbvec coverage` against `IN`):**
  1. Query: `"satellite operator duty to notify warn downstream customers dependent critical infrastructure services disruption"`
     - **Documents searched:** 18
     - **Nearest clauses returned:**
       - `IN-SPACEFW-2026-ANXB-IV` / `in-space-fw-2026:p48:c0` (score `0.7259` / `0.6942`, `non_binding`, Annexure B, IV Respond, item 4.2, p. 48): *"Stakeholders: Establish procedures for notifying critical infrastructure partners, regulatory bodies, and customers, especially when service disruption occurs."*
       - `in-ctir-2024:p8:c0` (score `0.6811`, `binding`, Rule 7, p. 8): Requires reporting of security incidents affecting Critical Telecommunication Infrastructure to the Central Government.
  2. Query: `"share information telecommunication network prior approval Central Government public disclosure security incident"`
     - **Documents searched:** 18
     - **Nearest clauses returned:**
       - `IN-TCSR-2024-R7-2` / `in-tcsr-2024:p5:c2` (score `0.7253`, `binding`, Rule 7(2), p. 5): Empowers the Central Government to inform the public of a security incident or require the affected entity to do so.
       - `IN-AUTHZ-2026-R37-5` / `in-authz-rules-2026:p101:c2` (score `0.7176` / `0.7175`, `binding`, Rule 37(5), p. 101): Prohibits sharing any information relating to a telecommunication network with any other person except with prior written Central Government approval (with a proviso only for equipment suppliers or manufacturers).
- **Why Nearest Clauses Do Not Close the Gap:** The only clause addressing operator notification to critical-infrastructure partners and customers (`in-space-fw-2026`, p. 48) is a non-binding self-assessment checklist item with no deadline. Meanwhile, `TCSR Rule 7(2)` is a discretionary government power to order public disclosure, and `Authz Rule 37(5)` actively restricts operators from sharing network-related information with third parties without prior written approval.

## 6. What a Human Must Decide
- **Scope of the Rule 37(5) safe harbour:** Whether the recommended standing approval under `Authz Rule 37(5)` should cover only service-degradation and indicators-of-compromise warnings to registered critical-infrastructure dependants, or all enterprise B2B customers.
- **Downstream warning clock:** Whether to align the downstream warning deadline for critical-infrastructure dependants with the US FCC 30-minute PSAP standard (`us-fcc-911-reliability-2013`, p. 64) or with India's 6-hour CERT-In/DoT awareness clock.
