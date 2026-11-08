# GAP-IN-09: No Binding Satellite-Specific Cyber-Resilience Baseline (Space Framework Is Advisory)

> **Review 8 Nov (second model + human decision):** narrowed to *no detailed, auditable satellite cyber baseline*. IN-SPACe NGP 2024 Ch. XI B(v), PDF p. 71, asks for "encryptions at design level" (record IN-NGP-2024-XI-B-v, unverified). Register text in `kb/gaps/india.yaml` wins over this draft.


- **Gap ID:** `GAP-IN-09-SPACE-CYBER-ADVISORY`
- **Topic:** `space_cyber`
- **Kind:** `coverage`
- **Current Register Status:** `confirmed`

## 1. Domain Gap & Severity
In any jurisdiction operating an emulated or live non-terrestrial network (NTN), general telecommunications security rules govern enterprise networks and physical sovereignty, but do not mandate satellite-specific cyber controls across the space segment, ground gateway segment, emulated or live radio/feeder/TT&C links, and user terminals (such as telecommand authentication, link-layer encryption, ground-control network segmentation, and isolated management interfaces). Without a binding, auditable satellite cyber baseline, an attacker who compromises a ground management network or VPN can issue unauthorized commands to disable user terminals en masse without the operator having violated any specific technical control prior to the breach.

- **Severity Score:** **5 / 5**
- **Reason:** Ground-segment management and telecommand/control interfaces are single points of failure capable of disabling tens of thousands of satellite user terminals simultaneously, yet satellite-specific technical controls remain non-binding advice.

## 2. India Evidence

### Verified Records (`kb/india/records.yaml`)
- **`IN-PIB-2026-SPACEFW-ADVISORY`** (PIB release 2233122, MeitY, 26 Feb 2026; `non_binding`):
  > "These guidelines are advisory in nature and are intended to advance cyber security preparedness across the space sector."
- **`IN-SPACEFW-2026-SDLS`** (CERT-In / SIA-India Cyber Security Framework and Guidelines for Space including Satellite Communication, PDF p. 17; `non_binding`):
  > "Adopt standardized and validated cryptographic protocols (e.g., FIPS 140-3, Consultative Committee for Space Data Systems Space Data Link Security (CCSDS SDLS), Advanced Encryption Standard (AES)-256)."
- **`IN-SPACEFW-2026-3-2-1`** (CERT-In / SIA-India Space Framework, §3.2.1, PDF p. 12; `non_binding`):
  > "All SatCom operators and service providers must report cybersecurity incidents, breaches, or anomalies within 6 hours of noticing the incident to CERT-In."
- **`IN-AUTHZ-2026-R54-1`** (Telecommunications (Authorisation for Provision of Principal Telecommunication Services) Rules, 2026, Rule 54(1)(a), PDF p. 109; `binding`):
  > "be responsible for security of its telecommunications network and undertake measures"
- **`IN-AUTHZ-2026-R60-1`** (Authz Rules, 2026, Rule 60(1)(f), PDF p. 113; `binding`):
  > "provide any information of and conduct tests, for interference monitoring, and to take necessary steps, as directed by the Central Government, for its mitigation; and"
- **`IN-AUTHZ-2026-R60-1-b`** (Authz Rules, 2026, Rule 60(1)(b), PDF p. 112; `binding`):
  > "ensure that no traffic originating from or terminating at a user terminal located in India is routed via satellite earth station gateways located outside India, directly or through inter-satellite communication links, including during failure of satellite earth station gateway located in India or as part of telecommunication network optimisation;"
- **`IN-AUTHZ-2026-R62-2`** (Authz Rules, 2026, Rule 62(2), PDF p. 114; `binding`):
  > "The operation, maintenance and control facility for the satellite earth station gateway and user terminals connected with the satellite network of a new authorised entity shall be located in India."
- **`IN-AUTHZ-2026-R62-7`** (Authz Rules, 2026, Rule 62(7), PDF p. 114; `binding`):
  > "Every new authorised entity shall report to the Central Government on the portal, any attempt to access or use the satellite network by a user terminal not registered under sub-rule (6)"
- **`IN-AUTHZ-2026-R59-4`** (Authz Rules, 2026, Rule 59(4)(a), PDF p. 112; `binding`):
  > "unauthorised satellite signal that it may detect originating or terminating within India; and"
- **`IN-NCCS-ITSAR-G4-2-12-10`** (NCCS ITSAR702042604, Common Security Requirements, Group-IV Devices, V2.0.0, Req. 2.12.10, PDF p. 105; `not_stated`):
  > "PABX shall support management software usage/critical command execution only through a dedicated management interface."

### Staged Quotes (auto-checked, not yet human-verified)
- **`inspace-ngp-2024` (page 71)** — IN-SPACe Norms, Guidelines and Procedures for Implementation of Indian Space Policy 2023, Chapter XI, Clause B(v) (auto-checked, not yet human-verified):
  > "Assure cyber security including encryptions at design level and prevent unauthorized commandeering of satellite through adequate data security."
- **`inspace-ngp-2024` (page 22)** — IN-SPACe NGP 2024, Chapter II, Clause 21 (auto-checked, not yet human-verified):
  > "IN-SPACe may impose control on operations of the Authorized Space Objects & Space Activities or terminate/suspend the Authorization, during national emergencies or in the interest of national security, such as situation arising out of or due to conflicts or natural disasters or times of emergency as declared or specified by Government of India or other such contingencies as may be specified by IN-SPACe or the Government of India."
- **`in-space-policy-2023` (page 8)** — Indian Space Policy 2023, Section 5, Clause 13.2 (auto-checked, not yet human-verified):
  > "for telecommunication services shall be governed by the rules, regulations and policies of Department of Telecommunications (DoT), Ministry of Communications."
- **`in-space-policy-2023` (page 8)** — Indian Space Policy 2023, Section 5, Clause 17 (auto-checked, not yet human-verified):
  > "issue guidelines for meeting safety and security requirements for space objects."
- **`in-space-cyber-framework-2026` (page 33)** — CERT-In / SIA-India Space Framework, Clause 7.1 (auto-checked, not yet human-verified):
  > "All confirmed or suspected cybersecurity incidents affecting satellite networks, ground control systems, or user data shall be reported to CERT-In within 6 hours of noticing such incidents or being brought to notice about such incidents as per the cybersecurity directions of CERT-In."

### What Is Missing
India's binding telecom rules (`Authz Rules 2026` Rules 50, 53, 54, 59–62; `TCSR 2024` Rule 4) mandate general network security, domestic gateway location, lawful interception, and rogue-terminal reporting. IN-SPACe's NGP 2024 (`inspace-ngp-2024`, p. 71) includes a one-line design-level objective for space-object applicants to prevent unauthorized satellite commandeering, while deferring telecommunication service rules to DoT (`in-space-policy-2023`, p. 8). Concrete satellite and ground-segment controls—such as dedicated management-interface isolation, VPN cryptographic controls for satellite gateways, micro-segmentation between enterprise IT and ground control, TT&C/feeder-link encryption, and user-terminal firmware signing—exist either only in the non-binding CERT-In/SIA-India Space Framework (`IN-PIB-2026-SPACEFW-ADVISORY`) or in NCCS ITSARs restricted to office PABX systems (`IN-NCCS-ITSAR-G4-2-12-10`), leaving satellite ground and terminal equipment without a binding technical baseline.

## 3. Global Examples

1. **EU NIS2 Directive (`EU-NIS2-2022-ANNEX-I-SPACE` & `EU-NIS2-2022-ART21-2-c`, verified records)**
   - **Instrument:** Directive (EU) 2022/2555 (NIS2)
   - **Clause:** Annex I, Sector 11 (Space) and Article 21(2)(c)
   - **Issuing Authority:** European Parliament and Council
   - **Binding Status:** `binding` (via Member State transposition)
   - **Exact Quote (`EU-NIS2-2022-ANNEX-I-SPACE`, Annex I, Space, page n/a - HTML):**
     > "Operators of ground-based infrastructure, owned, managed and operated by Member States or by private parties, that support the provision of space-based services, excluding providers of public electronic communications networks"
   - **Exact Quote (`EU-NIS2-2022-ART21-2-c`, Article 21(2)(c), page n/a - HTML):**
     > "business continuity, such as backup management and disaster recovery, and crisis management;"
   - **How it closes the gap:** Explicitly designates operators of space ground-based infrastructure as an essential sector subject to mandatory cybersecurity risk-management measures under Article 21 (including supply-chain security, cryptography, access control, and business continuity).

2. **EU Space Act Proposal (`eu-space-act-proposal-2025`, staged auto-checked)**
   - **Instrument:** Proposal for a Regulation on the safety, resilience and sustainability of space activities in the Union (EU Space Act, COM(2025) 335 final)
   - **Clause:** Article 76(1) and Recital (68)
   - **Issuing Authority:** European Commission
   - **Binding Status:** `draft` (legislative proposal for a directly applicable EU Regulation)
   - **Exact Quote (`eu-space-act-proposal-2025`, Article 76(1), page null - HTML, auto-checked):**
     > "Union space operators shall take all the necessary measures to manage the risks posed to the security of network and information systems and the security of the physical infrastructure and environment, in accordance with the principle of proportionality, taking into account their risk profile and size, as well as the nature, scale and complexity of their space activities."
   - **Exact Quote (`eu-space-act-proposal-2025`, Recital (68), page null - HTML, auto-checked):**
     > "To date, the cybersecurity of the space sector has been only partly addressed at Union level through a general applicable framework as laid down by Directive (EU) 2022/2555. The current cybersecurity regime does not comprehensively cover all types of actors and services which are relevant for the space sector."
   - **How it closes the gap:** Recognizes that general cybersecurity rules (like NIS2) do not cover all space segments and establishes a dedicated, binding cybersecurity risk-management regime tailored to space and ground assets across their lifecycle.

3. **EU Space Programme Regulation (`eu-space-programme-2021-696`, staged auto-checked)**
   - **Instrument:** Regulation (EU) 2021/696 establishing the Union Space Programme and EUSPA
   - **Clause:** Article 34(1)(a) and Article 34(2)
   - **Issuing Authority:** European Parliament and Council
   - **Binding Status:** `binding`
   - **Exact Quote (`eu-space-programme-2021-696`, Article 34(1)(a), page 42, auto-checked):**
     > "the protection of infrastructure, both ground and space, and of the provision of services, particularly against physical or cyber-attacks, including interference with data streams;"
   - **How it closes the gap:** Imposes a statutory mandate across both ground and space infrastructure to protect against cyber-attacks and data-stream interference, backed by mandatory component-level risk and threat analyses (Article 34(2)) and formal security accreditation.

4. **US FCC Part 4 Satellite & Gateway Outage Rules (`us-fcc-part-4-outage`, staged auto-checked)**
   - **Instrument:** 47 CFR Part 4 — Disruptions to Communications
   - **Clause:** 47 CFR § 4.9(c)(1)
   - **Issuing Authority:** Federal Communications Commission (US)
   - **Binding Status:** `binding`
   - **Exact Quote (`us-fcc-part-4-outage`, 47 CFR § 4.9(c)(1), page null - XML, auto-checked):**
     > "**[DROPPED 8 Nov: irrelevant, review row 10]** In addition, all Mobile-Satellite Service (“MSS”) satellite operators shall submit electronically a Notification to the Commission within 120 minutes of discovering that they have experienced on any facilities that they own, operate, lease, or otherwise utilize, of an outage of at least 30 minutes duration that manifests itself as a failure of any gateway earth station, except in the case where other earth stations at the gateway location are used to continue gateway operations within 30 minutes of the onset of the failure."
   - **How it closes the gap:** Binds satellite operators to specific operational resilience thresholds for gateway earth stations, satellite transponders, and inter-satellite links, creating direct regulatory accountability if a gateway failure is not absorbed by redundant earth stations within 30 minutes.

## 4. Recommendation

- **Domain-Level Recommendation:** National telecom and space regulators should convert advisory satellite cybersecurity guidelines into a binding, auditable baseline covering all segments of an emulated or live NTN: (1) strict isolation of ground-station management interfaces and multi-factor VPN access, (2) micro-segmentation between corporate IT and satellite TT&C/gateway networks, (3) authenticated and encrypted telecommand, telemetry, and feeder links, and (4) cryptographic firmware validation and secure boot on satellite user terminals and gateway routers.
- **Application to India:**
  1. **Department of Telecommunications (DoT) & National Centre for Communication Security (NCCS):** Exercise the standards notification power under **Section 19(d)–(f) of the Telecommunications Act, 2023** (`IN-TELACT-2023-19`) and the **Telecommunications (Framework to Notify Standards, Conformity Assessment and Certification) Rules, 2025** (`in-dot-telecom-standards-rules-2025`, p. 8) to issue a mandatory NCCS Indian Telecom Security Assurance Requirements (ITSAR) standard for satellite earth station gateways and user terminals, extending the management-interface isolation and VPN controls currently limited to Group-IV PABX devices (`IN-NCCS-ITSAR-G4-2-12-10`).
  2. **DoT & CERT-In:** Incorporate a core subset of the **2026 CERT-In / SIA-India Space Cyber Security Framework** (`in-space-fw-2026`) as binding technical conditions under **Rule 60 / Rule 62 of the 2026 Authorisation Rules**, aligned with IN-SPACe's design-level security requirement (`inspace-ngp-2024`, p. 71).

## 5. Search Record

- **Vector KB Queries Run (`orca.kbvec coverage` against `IN`):**
  1. Query: `"satellite cyber security baseline telecommand telemetry encryption management interface segmentation"`
     - **Documents searched:** 18
     - **Nearest clauses returned:**
       - `in-space-fw-2026:p17:c0` (score `0.7312`, `non_binding`, s.5, p. 17): Requires micro-segmentation, end-to-end encryption for TT&C and payload links (CCSDS SDLS, FIPS 140-3, AES-256), isolated key management, and secure boot.
       - `in-space-fw-2026:p45:c0` (score `0.7360`, `non_binding`, s.12, p. 45): Lists mitigations for flight software tampering and bus snooping (cryptographically signed firmware updates, HSMs).
       - `in-space-fw-2026:p38:c1` (score `0.7108`, `non_binding`, s.10, p. 38): Security testing and certification across SATCOM lifecycle phases.
  2. Query: `"binding security requirements satellite earth station gateway user terminal authorisation rules"`
     - **Documents searched:** 18
     - **Nearest clauses returned:**
       - `in-authz-rules-2026:p112:c3` / `IN-AUTHZ-2026-R60-1-b` (score `0.7754` / `0.7604`, `binding`, Rule 60, p. 112): Requires Indian user traffic to pass through a gateway in India and bans routing or mirroring via foreign gateways.
       - `IN-AUTHZ-2026-R62-2` (score `0.7630`, `binding`, Rule 62(2), p. 114): Requires the operation, maintenance, and control facility for satellite gateways and user terminals to be located in India.
- **Why Nearest Clauses Do Not Close the Gap:** The nearest technical clauses in `in-space-fw-2026` (pages 17, 38, 45) contain the exact controls needed to prevent a KA-SAT-style ground/terminal compromise, but PIB release 2233122 (`IN-PIB-2026-SPACEFW-ADVISORY`) confirms those guidelines are advisory. Conversely, the binding clauses in `in-authz-rules-2026` (Rules 60 and 62) govern territorial routing, gateway location, and terminal registration, without setting cyber-resilience controls for gateways, links, or terminals.

## 6. What a Human Must Decide
- **Whether IN-SPACe NGP 2024 (`inspace-ngp-2024`, p. 71) narrows the gap wording:** NGP 2024 states that space-object applicants must *"Assure cyber security including encryptions at design level and prevent unauthorized commandeering of satellite through adequate data security."* A human reviewer must decide whether to cite this in `kb/gaps/india.yaml` as a binding high-level space-segment duty while keeping GAP-IN-09 confirmed for the missing operational, ground-gateway, and terminal baseline under DoT/NCCS.
- **Which regulatory hook to prioritize for India's recommendation:** Whether DoT should mandate satellite gateway/terminal controls primarily via a new **NCCS ITSAR equipment standard** under Telecom Act s.19 (`in-dot-telecom-standards-rules-2025`), or via **Authorisation Rules Chapter VII** operational conditions.
