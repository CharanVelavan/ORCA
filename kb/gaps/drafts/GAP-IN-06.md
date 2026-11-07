# GAP-IN-06: Feeder-Link and Inter-Satellite-Link Security Is Left Unspecified in 3GPP, and India Has Not Used Its Section 19 Standards Power for Satellite Links

- **Gap ID:** `GAP-IN-06-STANDARDS`
- **Topic:** `standards`
- **Kind:** `standards`
- **Current Register Status:** `confirmed`

## 1. Domain Gap & Severity
In 5G non-terrestrial networks (NTN), international mobile standards (3GPP) define user-equipment-to-network security over the service link, but explicitly treat the **feeder link** (ground earth station gateway to satellite) and the **inter-satellite link (ISL)** as out-of-scope transport links, noting only that generic IP layer security *can* be used. Where national telecom regulators possess statutory authority to notify mandatory telecom cybersecurity and encryption standards (and prohibit uncertified equipment), but have not yet notified a link-encryption and authentication standard for emulated or live satellite feeder links and ISLs, operators may carry aggregated backhaul traffic or control flows over unstandardized or unencrypted space data links without violating any notified technical standard.

- **Severity Score:** **4 / 5**
- **Reason:** An emulated or live satellite feeder link or inter-satellite link aggregates traffic from thousands of subscribers and critical infrastructure endpoints, yet neither 3GPP nor national notified telecom standards mandate link-layer cryptographic protection (such as CCSDS SDLS or mandatory IPsec profiles).

## 2. India Evidence

### Verified Records (`kb/india/records.yaml`)
- **`IN-TELACT-2023-19`** (Telecommunications Act, 2023, Section 19(d)–(f), PDF p. 9; `binding`):
  > "(e) cyber security for telecommunication services and telecommunication networks; and (f) encryption and data processing in telecommunication."
- **`IN-SPACEFW-2026-SDLS`** (CERT-In / SIA-India Cyber Security Framework and Guidelines for Space including Satellite Communication, PDF p. 17; `non_binding`):
  > "Adopt standardized and validated cryptographic protocols (e.g., FIPS 140-3, Consultative Committee for Space Data Systems Space Data Link Security (CCSDS SDLS), Advanced Encryption Standard (AES)-256)."
- **`IN-PIB-2026-SPACEFW-ADVISORY`** (PIB release 2233122, MeitY, 26 Feb 2026; `non_binding`):
  > "These guidelines are advisory in nature and are intended to advance cyber security preparedness across the space sector."

### Direct International Standards Evidence (`kb/sources/.text/intl-3gpp-tr-33700-29.txt`)
- **`intl-3gpp-tr-33700-29`** (3GPP TR 33.700-29 V19.1.0, Study on security aspects of 5G satellite access in the 5G architecture phase 3, Clause 4, lines 314 & 317; `non_binding` technical report):
  > "The feeder link and the inter-satellite link (ISL) are assumed to act only as transport layer links and are not specified in 3GPP."
  > "Native IP-based communication protocol (as defined in TS 33.210 [6]) security at the network layer can be used to secure the IP transport connectivity available over the feeder link and the inter-satellite link (ISL) satellite transport links."

### Staged Quotes (auto-checked, not yet human-verified)
- **`in-dot-telecom-standards-rules-2025` (page 8)** — Telecommunications (Framework to Notify Standards, Conformity Assessment and Certification) Rules, 2025, Rule 8(2) (auto-checked, not yet human-verified):
  > "No telecommunication equipment to which a standard applies, shall be sold or deployed in any telecommunication network, or otherwise be used in India, unless it has a valid Certificate of Conformity Assessment."
- **`in-ctir-2024` (page 7)** — Telecommunications (Critical Telecommunication Infrastructure) Rules, 2024, Rule 6(1) (auto-checked, not yet human-verified):
  > "Every telecommunication entity shall ensure that Critical Telecommunication Infrastructure, including any spares, hardware and software used in such Critical Telecommunication Infrastructure, are in compliance with the following standards, namely:–"
- **`inspace-ngp-2024` (page 20)** — IN-SPACe Norms, Guidelines and Procedures for Implementation of Indian Space Policy 2023, Chapter II, Clause 9 (auto-checked, not yet human-verified):
  > "Where specific standards for Space Activities are not explicitly mentioned in this document or any other applicable law of India, the Applicant shall adhere to globally recognized best practices prevailing in the industry."
- **`in-space-cyber-framework-2026` (page 12)** — CERT-In / SIA-India Space Framework, Clause 3.2.2 (auto-checked, not yet human-verified):
  > "All mission systems, ground infrastructure, and communication networks must comply with Catalogue of Indian Standards for Space Industry, Norms, Guidelines and Procedures (NGP) released by the Department of Space."

### What Is Missing
1. **International 3GPP gap:** 3GPP TR 33.700-29 Clause 4 explicitly places feeder links and inter-satellite links outside 3GPP specification scope, stating only that network-layer IP security (TS 33.210) *can* be used.
2. **Unused Indian standards power:** India has enacted a complete legal enforcement mechanism—**Section 19 of the Telecommunications Act, 2023** (`IN-TELACT-2023-19`), the **2025 Standards, Conformity Assessment and Certification Rules** (`in-dot-telecom-standards-rules-2025`, p. 8), and **CTIR Rule 6(1)** (`in-ctir-2024`, p. 7)—under which no equipment subject to a notified standard may be deployed without a Certificate of Conformity Assessment. Yet no satellite link-security or encryption standard has been notified under Section 19. Even **IN-SPACe NGP 2024** (`inspace-ngp-2024`, p. 20) acknowledges that specific Indian standards for space activities may be absent and defaults to *"globally recognized best practices prevailing in the industry,"* while the **2026 Space Framework** (`IN-SPACEFW-2026-SDLS`) names **CCSDS SDLS (CCSDS 355.0-B-2), FIPS 140-3, and AES-256** only as non-binding advice.

## 3. Global Examples

1. **ENISA Space Threat Landscape 2025 (`enisa-space-threat-landscape-2025`, staged auto-checked)**
   - **Instrument:** ENISA Report — Space Threat Landscape 2025
   - **Clause:** Executive Summary (page 7)
   - **Issuing Authority:** European Union Agency for Cybersecurity (ENISA)
   - **Binding Status:** `advisory`
   - **Exact Quote (`enisa-space-threat-landscape-2025`, Executive Summary, page 7, auto-checked):**
     > "Deployment of validated and tested cryptographic technologies measures into space systems;"
   - **How it closes the gap:** Recommends mandatory deployment of validated, tested cryptographic protocols across space and link segments (including CCSDS Space Data Link Security and authenticated telecommand/feeder links) as part of the European Space Cybersecurity Controls Framework referenced on p. 40 of `in-space-fw-2026`.

2. **EU Space Programme Regulation & IRIS² Secure Connectivity Regulation (`eu-space-programme-2021-696` & `eu-iris2-regulation-2023-588`, staged auto-checked)**
   - **Instrument:** Regulation (EU) 2021/696 (Union Space Programme) and Regulation (EU) 2023/588 (IRIS²)
   - **Clause:** Regulation (EU) 2021/696 Article 34(1)(a) (p. 42) and Article 33(b) (p. 41); Regulation (EU) 2023/588 Article 3(2)(b) & (e) (p. 15)
   - **Issuing Authority:** European Parliament and Council
   - **Binding Status:** `binding`
   - **Exact Quote (`eu-space-programme-2021-696`, Article 34(1)(a), page 42, auto-checked):**
     > "the protection of infrastructure, both ground and space, and of the provision of services, particularly against physical or cyber-attacks, including interference with data streams;"
   - **Exact Quote (`eu-space-programme-2021-696`, Article 33(b), page 41, auto-checked):**
     > "to use the security rules of the Council and of the Commission, which provide, inter alia, for a separation between operational functions and those associated with accreditation."
   - **How it closes the gap:** Subjects Union space-programme and sovereign connectivity systems (including ground-to-space and inter-satellite data streams) to mandatory security accreditation and data-stream protection rules.

3. **US Space Policy Directive-5 & NIST IR 8270 (`us-whitehouse-spd5-2020` & `us-nist-ir-8270-2023`, staged — text verified directly in PDF on disk)**
   - **Instrument:** US Presidential Memorandum — Space Policy Directive-5 (85 FR 56155) and NIST IR 8270 (Introduction to Cybersecurity for Commercial Satellite Operations)
   - **Clause:** SPD-5 Section 4(b)(i) & (iii) (PDF p. 3); NIST IR 8270 Section 2.1.2 (PDF p. 12)
   - **Issuing Authority:** Executive Office of the President of the United States; NIST
   - **Binding Status:** SPD-5 is `binding` on US federal agencies (norm-setting for commercial systems); NIST IR 8270 is `advisory`
   - **Exact Quote (`us-whitehouse-spd5-2020`, Section 4(b)(i), PDF page 3, verified in PDF):**
     > "Protection against unauthorized access to critical space vehicle functions. This should include safeguarding command, control, and telemetry links using effective and validated authentication or encryption measures designed to remain secure against existing and anticipated threats during the entire mission lifetime;"
   - **Exact Quote (`us-nist-ir-8270-2023`, Section 2.1.2, PDF page 12, verified in PDF):**
     > "Communications between operational satellites for mission functions – such as command and control, networking of compute capabilities, redundancy of operations and mission functions, tracking, and communications – are known as inter-vehicle communications. Therefore, the integrity, availability, and confidentiality of these communications are critical."
   - **How it closes the gap:** Explicitly targets both ground-to-satellite RF/optical links and satellite-to-satellite (inter-vehicle / ISL) links, requiring validated authentication and encryption engineered to last the full mission lifetime.

4. **EU Cybersecurity Act (`eu-cybersecurity-act-2019`, staged auto-checked)**
   - **Instrument:** Regulation (EU) 2019/881 (Cybersecurity Act)
   - **Clause:** Article 51(i) and Article 52(1)
   - **Issuing Authority:** European Parliament and Council
   - **Binding Status:** `binding`
   - **Exact Quote (`eu-cybersecurity-act-2019`, Article 52(1), page 42, auto-checked):**
     > "A European cybersecurity certification scheme may specify one or more of the following assurance levels for ICT products, ICT services and ICT processes: ‘basic’, ‘substantial’ or ‘high’."
   - **How it closes the gap:** Provides the statutory certification-scheme machinery (analogous to India's 2025 Telecom Standards Rules) for translating technical link and equipment standards into tiered conformity certificates.

## 4. Recommendation

- **Domain-Level Recommendation:** International telecom standards bodies (**3GPP SA3** and **ITU-T Study Group 17**) should replace the permissive "can be used" assumption in 3GPP TR 33.700-29 Clause 4 with a normative requirement that NTN feeder links and inter-satellite links implement authenticated, replay-protected link or network-layer encryption (such as **CCSDS 355.0-B-2 Space Data Link Security (SDLS)** or a mandatory **3GPP TS 33.210 IPsec/MACsec profile**). Concurrently, national telecom regulators should exercise their domestic standards-notification powers to mandate conformity with these link-encryption standards for all licensed NTN gateways and satellites.
- **Application to India:**
  1. **Department of Telecommunications (DoT) & Telecommunication Engineering Centre (TEC) / NCCS:** Exercise **Section 19(d)–(f) of the Telecommunications Act, 2023** (`IN-TELACT-2023-19`) and **Rule 8(2) of the Telecommunications (Framework to Notify Standards, Conformity Assessment and Certification) Rules, 2025** (`in-dot-telecom-standards-rules-2025`, p. 8) to notify a binding satellite link-security standard requiring **CCSDS SDLS / AES-256 / FIPS 140-3** (already named in the advisory Space Framework on pp. 17, 19, 20, 40, `IN-SPACEFW-2026-SDLS`) or a mandatory TS 33.210 IPsec profile on all emulated or live feeder links and inter-satellite links serving Indian gateways.
  2. **TSDSI / DoT International Coordination:** Submit a normative contribution from India (TSDSI / TEC) to **3GPP SA3** and **ITU-T SG17** closing the feeder-link and ISL specification deferral in 3GPP Release 19/20.

## 5. Search Record

- **Vector KB Queries Run (`orca.kbvec coverage` against `IN`):**
  1. Query: `"feeder link inter-satellite link encryption security standard CCSDS SDLS conformity assessment Section 19"`
     - **Documents searched:** 18
     - **Nearest clauses returned:**
       - `IN-SPACEFW-2026-SDLS` / `in-space-fw-2026:p17:c0` (score `0.7932`, `non_binding`, s.5.5, p. 17): Recommends end-to-end encryption for TT&C and payload links using FIPS 140-3, CCSDS SDLS, and AES-256.
       - `in-space-fw-2026:p19:c2` / `in-space-fw-2026:p20:c0` (scores `0.7323`, `0.7026`, `non_binding`, s.6.1, pp. 19–20): Maps space-segment command authentication, link encryption, and key rotation to CCSDS SDLS, ECSS-E-ST-70, and NIST SP 800-53/800-57.
  2. Query: `"notify standards conformity assessment telecommunication security cyber security encryption satellite"`
     - **Documents searched:** 18
     - **Nearest clauses returned:**
       - `in-telact-2023:p9:c2` / `IN-TELACT-2023-19` (score `0.7903`, `binding`, Section 19(a)–(f), p. 9): Empowers the Central Government to notify standards and conformity assessment measures for telecom security, cyber security, and encryption.
       - `in-space-fw-2026:p40:c0` (score `0.7595`, `non_binding`, s.10.3, p. 40): Lists recommended international certification frameworks including ENISA Space Cybersecurity Controls Framework (2025), ECSS-E-ST-80C, CCSDS 355.0-B-2 (SDLS), NIST IR 8270, ISO/IEC 15408, and FIPS 140-3.
- **Why Nearest Clauses Do Not Close the Gap:** `Telecom Act s. 19` and `in-dot-telecom-standards-rules-2025` provide the binding legal power and certification enforcement mechanism, while `in-space-fw-2026` (pages 17, 19, 20, 40) identifies the exact international cryptographic standards (CCSDS 355.0-B-2 SDLS, FIPS 140-3, AES-256). However, because `in-space-fw-2026` is advisory (`IN-PIB-2026-SPACEFW-ADVISORY`) and DoT has not yet notified a satellite link standard under Section 19—and 3GPP TR 33.700-29 Clause 4 leaves feeder links and ISLs unspecified—no binding standard currently governs feeder-link or ISL security.

## 6. What a Human Must Decide
- **Whether to add `in-dot-telecom-standards-rules-2025` (p. 8) and `inspace-ngp-2024` (p. 20) to `kb/gaps/india.yaml`:** Both passed the automated quote check. `in-dot-telecom-standards-rules-2025` Rule 8(2) shows that the Section 19 conformity-assessment machinery is now in force (May 2025), making the absence of a notified satellite-link standard even sharper, while `inspace-ngp-2024` Clause 9 explicitly admits that specific Indian standards for space activities are not yet mentioned in law.
