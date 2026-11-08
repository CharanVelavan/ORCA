# GAP-IN-08: Partial Gap — No Explicit Pre-Failover Clean-Path Security Check During an Attack

> **Review 8 Nov:** kept as a *partial* gap - no *explicit* pre-failover clean-path check. Register text wins over this draft.


- **Gap ID:** `GAP-IN-08-NO-CLEAN-PATH-CHECK`
- **Topic:** `failover_path_security`
- **Kind:** `standards`
- **Current Register Status:** `confirmed` (confirmed as partial by human review on 8 Nov 2026)

## 1. Domain Gap & Severity
In an emulated or live non-terrestrial network (NTN), continuity regulations require operators to maintain backup links or alternate gateways and to switch traffic automatically or manually when the primary link degrades. However, RF jamming or denial-of-service against a primary satellite or terrestrial link is a documented adversary technique used to force automated failover onto a secondary path or alternate gateway that the attacker has already compromised or can intercept. Existing rules require general business-continuity plans, prohibit routing via foreign gateways, and advise verifying system integrity *after* an incident before resuming full operations, but no technical standard mandates an automated pre-failover security and integrity check of the backup path *at the moment of failover* during an active attack.

- **Severity Score:** **3 / 5**
- **Reason:** Jamming-induced failover can Herd live emergency and critical-infrastructure traffic onto a compromised secondary link, though general continuity duties and domestic-gateway restrictions partially bound the exposure.

## 2. India Evidence

### Verified Records (`kb/india/records.yaml`)
- **`IN-CTIR-2024-R7-1-i`** (Telecommunications (Critical Telecommunication Infrastructure) Rules, 2024, Rule 7(1)(i), PDF p. 8; `binding`):
  > "implement standard operating procedures for security incident response systems, including disaster recovery and business continuity;"
- **`IN-AUTHZ-2026-R60-1-b`** (Telecommunications (Authorisation for Provision of Principal Telecommunication Services) Rules, 2026, Rule 60(1)(b), PDF p. 112; `binding`):
  > "ensure that no traffic originating from or terminating at a user terminal located in India is routed via satellite earth station gateways located outside India, directly or through inter-satellite communication links, including during failure of satellite earth station gateway located in India or as part of telecommunication network optimisation;"
- **`IN-AUTHZ-2026-R60-1`** (Authz Rules, 2026, Rule 60(1)(f), PDF p. 113; `binding`):
  > "provide any information of and conduct tests, for interference monitoring, and to take necessary steps, as directed by the Central Government, for its mitigation; and"
- **`IN-SPACEFW-2026-7-3`** (CERT-In / SIA-India Cyber Security Framework and Guidelines for Space including Satellite Communication, §7.3 Recovery, PDF p. 34; `non_binding`):
  > "Affected systems shall be restored to a verified secure state through re-imaging, patching, and validation of integrity before resumption of full operations."
- **`IN-PIB-2026-SPACEFW-ADVISORY`** (PIB release 2233122, MeitY, 26 Feb 2026; `non_binding`):
  > "These guidelines are advisory in nature and are intended to advance cyber security preparedness across the space sector."

### Staged Quotes (auto-checked, not yet human-verified)
- **`in-ctir-2024` (page 8)** — Telecommunications (Critical Telecommunication Infrastructure) Rules, 2024, Rule 7(1)(i) (auto-checked, not yet human-verified):
  > "implement standard operating procedures for security incident response systems, including disaster recovery and business continuity;"
- **`in-dot-unified-licence` (page 107)** — Unified Licence Agreement, Chapter XII (GMPCS), Condition 7.1 (auto-checked, not yet human-verified):
  > "The operation and maintenance centre of the GMPCS Gateway shall also be located in India."
- **`in-dot-unified-licence` (page 110)** — Unified Licence Agreement, Chapter XII (GMPCS), Condition 7.15 (auto-checked, not yet human-verified):
  > "All calls originating or terminating from Mobile Terminals in India shall pass through the GMPCS Gateway Switch located in India."
- **`in-dot-unified-licence` (page 110)** — Unified Licence Agreement, Chapter XII (GMPCS), Condition 7.15 (auto-checked, not yet human-verified):
  > "Domestic traffic should not be hauled/ routed to any place outside India."
- **`in-rbi-psos-cyber-resilience-2024` (page null - HTML)** — RBI Master Directions on Cyber Resilience and Digital Payment Security Controls for non-bank PSOs, Paragraph 23 (auto-checked, not yet human-verified):
  > "The PSO shall develop a BCP based on different cyber threat scenarios, including extreme but plausible events to which it may be exposed."

### What Is Missing
This gap is confirmed as **partial**. India's binding rules establish two essential guardrails: (1) Critical Telecommunication Infrastructure owners must maintain standard operating procedures for disaster recovery and business continuity (`IN-CTIR-2024-R7-1-i`), and (2) satellite licensees are strictly prohibited from routing or failing over Indian user traffic to any satellite earth station gateway outside India, even during a domestic gateway failure (`IN-AUTHZ-2026-R60-1-b`, `in-dot-unified-licence` p. 110). Furthermore, the advisory Space Framework (`IN-SPACEFW-2026-7-3`) requires verifying system integrity *after* an incident before resuming full operations. What is missing is a specific technical baseline requiring an operator (or its automated failover controller) to verify that the domestic standby satellite/backhaul path is uncompromised (clean configuration, valid cryptographic session, no active intrusion alerts) *before* switching live traffic onto it during a suspected attack.

## 3. Global Examples

1. **US FCC Mandatory Disaster Response Initiative (`us-fcc-mdri-order-2022`, staged auto-checked)**
   - **Instrument:** FCC Report and Order 22-50 / 47 CFR § 4.17 (Resilient Networks; Mandatory Disaster Response Initiative)
   - **Clause:** 47 CFR § 4.17(a)(3)(i)
   - **Issuing Authority:** Federal Communications Commission (US)
   - **Binding Status:** `binding`
   - **Exact Quote (`us-fcc-mdri-order-2022`, 47 CFR § 4.17(a)(3)(i), page 23, auto-checked):**
     > "Provide for reasonable roaming under disaster arrangements (RuDs) when technically feasible, where: (A) A requesting provider’s network has become inoperable and the requesting provider has taken all appropriate steps to attempt to restore its own network; and (B) The provider receiving the request (home provider) has determined that roaming is technically feasible and will not adversely affect service to the home provider’s own subscribers"
   - **How it closes the gap:** Requires an explicit pre-switch determination by the receiving network operator that failing traffic over onto the alternate network is technically feasible and will not adversely affect existing service before disaster roaming traffic is admitted.

2. **US FCC 911 Reliability Order — Elimination of Single Points of Failure on Failover Paths (`us-fcc-911-reliability-2013`, staged auto-checked)**
   - **Instrument:** FCC Report and Order 13-158 / 47 CFR Part 12 (Improving 911 Reliability)
   - **Clause:** Appendix B, 47 CFR § 12.4(c)(1)(i)(C)
   - **Issuing Authority:** Federal Communications Commission (US)
   - **Binding Status:** `binding`
   - **Exact Quote (`us-fcc-911-reliability-2013`, Appendix B, 47 CFR § 12.4(c)(1)(i)(C), page 67, auto-checked):**
     > "Eliminated all single points of failure in Critical 911 Circuits or equivalent data paths serving each PSAP."
   - **How it closes the gap:** Mandates annual certification and auditing of diverse primary and backup paths serving emergency centres to ensure that a failure or compromise of one element cannot compromise the backup path.

3. **EU NIS2 Directive & ENISA EECC Security Measures Guideline (`EU-NIS2-2022-ART21-2-c` verified; `enisa-eecc-security-measures-guideline` & `eu-cer-article-13-guidelines-2026` staged auto-checked)**
   - **Instrument:** Directive (EU) 2022/2555 (NIS2) and ENISA Guideline on Security Measures under the EECC (4th ed.)
   - **Clause:** NIS2 Article 21(2)(c); ENISA Security Objective SO22
   - **Issuing Authority:** European Parliament and Council; ENISA
   - **Binding Status:** NIS2 is `binding`; ENISA EECC Guideline is `advisory`
   - **Exact Quote (`EU-NIS2-2022-ART21-2-c`, Article 21(2)(c), page n/a - HTML):**
     > "business continuity, such as backup management and disaster recovery, and crisis management;"
   - **Exact Quote (`enisa-eecc-security-measures-guideline`, SO22, page 36, auto-checked):**
     > "Establish and maintain an appropriate disaster recovery capability for restoring network and communication services in case of natural and/or major disasters."
   - **How it closes the gap:** Binds space ground operators and telecom providers to maintain audited backup management and disaster recovery capabilities, though—like India—neither text explicitly specifies a real-time cryptographic/posture clean-path check prior to automated attack-triggered failover.

## 4. Recommendation

- **Domain-Level Recommendation:** Telecom and satellite standards bodies and regulators should require that automated or assisted failover mechanisms for emulated or live NTN backhaul enforce a two-part pre-failover gate whenever link loss coincides with anomaly or jamming indicators: (1) a jurisdictional routing check confirming the alternate gateway is domestic, and (2) an automated posture and telemetry check confirming the standby link and gateway have no active intrusion alerts, unencrypted feeder links, or unauthorized configuration diffs.
- **Application to India:**
  1. **Department of Telecommunications (DoT):** Issue a technical guideline or circular under **Rule 7(1)(i) of the Critical Telecommunication Infrastructure Rules, 2024** (`IN-CTIR-2024-R7-1-i`) and **Rule 60(1)(b) of the 2026 Authorisation Rules** (`IN-AUTHZ-2026-R60-1-b`) specifying that CTI disaster-recovery SOPs for satellite backhaul must verify both domestic gateway location and clean security posture of the standby domestic gateway before switching traffic during a security incident.
  2. **Telecommunication Engineering Centre (TEC) / NCCS & ITU-T SG17:** Include pre-failover path-integrity verification in national telecom security standards notified under **Section 19 of the Telecommunications Act, 2023** (`IN-TELACT-2023-19`) and contribute the requirement to **ITU-T Study Group 17** for AI-assisted network healing (aligned with ITU-T Y.3172).

## 5. Search Record

- **Vector KB Queries Run (`orca.kbvec coverage` against `IN`):**
  1. Query: `"failover backup path clean uncompromised integrity check before switching traffic satellite earth station gateway"`
     - **Documents searched:** 18
     - **Nearest clauses returned:**
       - `in-authz-rules-2026:p113:c0` / `in-authz-rules-2026:p112:c3` / `IN-AUTHZ-2026-R60-1-b` (scores `0.6912`, `0.6838`, `0.6801`, `binding`, Rule 60(1)(a)–(f), pp. 112–113): Requires all Indian user traffic to pass through a gateway in India, prohibits routing via foreign gateways even during domestic gateway failure, and requires real-time traffic and interference monitoring.
  2. Query: `"disaster recovery business continuity alternate ground station redundant link integrity validation"`
     - **Documents searched:** 18
     - **Nearest clauses returned:**
       - `in-space-fw-2026:p49:c0` (score `0.7173`, `non_binding`, Annexure B, para 5.2, p. 49): Advises contingency plans for switching to redundant systems, alternate ground stations, or terrestrial links during a SATCOM disruption.
       - `IN-CTIR-2024-R7-1-i` (score `0.6964`, `binding`, Rule 7(1)(i), p. 8): Requires standard operating procedures for security incident response systems, including disaster recovery and business continuity.
       - `in-space-fw-2026:p39:c0` (score `0.6792`, `non_binding`, s.10, p. 39): Recommends continuous in-orbit and operational vulnerability scanning and anomaly detection.
- **Why Nearest Clauses Do Not Close the Gap:** `Authz Rule 60(1)(b)` restricts *where* failover traffic may go (only gateways inside India), `CTIR Rule 7(1)(i)` requires having a disaster-recovery SOP, and `in-space-fw-2026` (§7.3, p. 34 and para 5.2, p. 49) advises switching to alternate ground stations and validating integrity *before resumption of full operations* post-incident. None of these clauses mandates verifying that the standby path itself is clean and uncompromised *before* failing traffic over during an active jamming or cyber event.

## 6. What a Human Must Decide
- **Whether to frame GAP-IN-08 primarily as an international standards gap alongside GAP-IN-06:** Because neither EU NIS2 nor US FCC rules explicitly require a real-time cyber-posture check of the standby link at the moment of failover (only technical feasibility and physical circuit diversity), a human reviewer should decide whether to highlight GAP-IN-08 in the report as an operational AI self-healing safeguard (`PB-06`) that advances global practice.
