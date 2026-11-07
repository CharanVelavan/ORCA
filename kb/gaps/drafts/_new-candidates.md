# New Candidate Policy Gaps Found in the Staged Corpus

- **Status of all entries below:** `candidate` (`verified: false` — drafted for human review only; only the human confirms gaps).
- **Topic exclusions respected:** None of these candidates involves `joint_command` (rejected `GAP-IN-07`) or `personal_data_breach` (rejected `GAP-IN-05`).
- **Scope note:** All non-terrestrial network (NTN) links in the ORCA-NTN Chennai deployment are **emulated**.

---

## Candidate 1: `GAP-CAND-IN-10-LOG-RETENTION-SPLIT`
- **Topic:** `log_retention`
- **Kind:** `ambiguity`
- **Title:** Three different log/update retention rules (180 days, 2 years, 15-day reporting) and an orbital data-localization conflict for store-and-forward satellites
- **Severity Score:** **3 / 5** — Overlapping retention windows and a strict ban on routing or holding copies of network logs outside India create legal ambiguity for non-geostationary (NGSO) satellites that buffer telemetry or store-and-forward logs in orbit before passing over an Indian gateway.
- **Domain Gap:** In an emulated or live NTN architecture, operators generate standard ICT security logs, critical infrastructure network-architecture change logs, software-update audit trails, and onboard spacecraft/payload telemetry logs. When cyber agencies, critical-infrastructure rules, and network authorisation rules set different retention durations and strictly prohibit any network logs or copies from leaving national territory, operators face conflicting retention lifecycles and a physical impossibility for regenerative or store-and-forward satellites whose onboard logs traverse foreign orbital paths before downlink.
- **India Evidence:**
  - **`IN-CERTIN-DIR-2022-iv`** (verified record, `in-certin-dir-2022` Direction (iv), PDF p. 3; `binding`):
    > "maintain them securely for a rolling period of 180 days and the same shall be maintained within the Indian jurisdiction."
  - **`in-ctir-2024` (page 8)** — Telecommunications (Critical Telecommunication Infrastructure) Rules, 2024, Rule 7(1)(c) (auto-checked, not yet human-verified; `binding`):
    > "preserve in a secure manner, for a minimum period of two years or such other period as may be determined by the Central Government, logs and documentation of the telecommunication network architecture of Critical Telecommunication Infrastructure, including changes in such telecommunication network architecture;"
  - **`in-telecom-network-rules-2026` (page 40)** — Telecommunications (Authorisation for Telecommunication Network) Rules, 2026, Rule 25(3) (staged, not yet human-verified; `binding`):
    > "Every new authorised entity shall ensure that all systems of its telecommunication network and the data, logs and information associated with its telecommunication network shall be stored within India and no copies of such data, logs and information shall be routed, shared or made available outside India."
  - **`in-dot-principal-telecom-authorisation-rules-2026` (page 106)** — Telecommunications (Authorisation for Provision of Principal Telecommunication Services) Rules, 2026, Rule 42(1)(b) (staged, not yet human-verified; `binding`):
    > "maintain a record of all software updates and changes, and provide to the Central Government details of such category of software updates and changes within fifteen days of completion of such updates and changes as decided by the Central Government from time to time:"
- **Global / Standards Evidence:**
  - **`intl-3gpp-tr-33700-29`** (3GPP TR 33.700-29 V19.1.0, Clause 5.1.1 & 5.1.2, lines 329 & 338, read in `kb/sources/.text/intl-3gpp-tr-33700-29.txt`): Notes that in Store-and-Forward (S&F) satellite operation, 3GPP network functions onboard a LEO/MEO satellite store uplink data and control messages while the feeder link to the ground gateway is intermittently unavailable, and onboard storage is hardware-constrained.
- **Recommendation:** DoT and CERT-In should issue a harmonized log-retention schedule clarifying (1) which NTN gateway and configuration logs fall under the 2-year CTIR rule versus the 180-day CERT-In ICT log rule, and (2) that transient encrypted buffering of telemetry and audit logs in onboard satellite memory during orbital transit does not violate `Telecom Network Rules 2026 Rule 25(3)` provided logs are downlinked exclusively to gateways located in India (`Authz Rule 60(1)(b)`).

---

## Candidate 2: `GAP-CAND-IN-11-GNSS-PNT-SPOOFING`
- **Topic:** `gnss_interference`
- **Kind:** `coverage`
- **Title:** No binding GNSS/NavIC timing-authentication or holdover standard for NTN gateways and 5G base stations, and no deadline for reporting RF/GNSS interference
- **Severity Score:** **4 / 5** — GNSS spoofing or jamming can desynchronize 5G TDD cellular base stations and satellite gateway Doppler/beam-tracking clocks simultaneously, yet no Indian telecom rule mandates authenticated PNT (NavIC/GNSS) or sets a deadline for reporting detected unauthorized satellite signals.
- **Domain Gap:** Emulated and live 5G NTN gateways, phased-array user terminals, and terrestrial 5G TDD base stations depend on Global Navigation Satellite System (GNSS) positioning, navigation, and timing (PNT) signals for ephemeris tracking, Doppler pre-compensation, and microsecond phase synchronization. Adversaries increasingly use RF jamming and GNSS spoofing to disrupt both satellite links and cellular timing. Without binding requirements for multi-constellation/authenticated PNT (e.g., NavIC + GPS with spoofing detection and local oscillator holdover) and a time-bounded clock for reporting RF interference, spoofing attacks degrade network synchronization without triggering mandatory defenses.
- **India Evidence:**
  - **`IN-AUTHZ-2026-R59-4`** (verified record, `in-authz-rules-2026` Rule 59(4)(a), PDF p. 112; `binding`):
    > "unauthorised satellite signal that it may detect originating or terminating within India; and"
    *(Note: Sets no deadline for the report, and covers unauthorized satellite signals rather than GNSS/PNT spoofing of ground timing receivers.)*
  - **`IN-AUTHZ-2026-R60-1`** (verified record, `in-authz-rules-2026` Rule 60(1)(f), PDF p. 113; `binding`):
    > "provide any information of and conduct tests, for interference monitoring, and to take necessary steps, as directed by the Central Government, for its mitigation; and"
    *(Note: Reactive duty triggered "as directed by the Central Government.")*
  - **`IN-AUTHZ-2026-R62-7`** (verified record, `in-authz-rules-2026` Rule 62(11)(a), PDF p. 114; `binding`): Bans location-spoofing tools in user terminals (targeting user evasion of geofencing, not resilience of network infrastructure against external GNSS spoofing).
  - **`in-space-fw-2026:p20:c0`** (corpus chunk, PDF p. 20; `non_binding` per `IN-PIB-2026-SPACEFW-ADVISORY`):
    > "Employ anti-jamming and anti-spoofing techniques for radio frequency (RF) communication"
- **Global Examples:**
  - **`us-whitehouse-spd5-2020`** (Space Policy Directive-5, Section 4(b)(iii), PDF p. 3, verified in PDF on disk; `binding` on US agencies):
    > "Protection against communications jamming and spoofing, such as signal strength monitoring programs, secured transmitters and receivers, authentication, or effective, validated, and tested encryption measures designed to provide security against existing and anticipated threats during the entire mission lifetime;"
  - **`eu-iris2-regulation-2023-588`** (Regulation (EU) 2023/588, Article 3(2)(e), page 15, auto-checked; `binding`):
    > "increase the robustness of the Union’s and the Member States’ communication services and the cyber resilience of the Union, by developing redundancy, passive, proactive and reactive cyber protection and operational cybersecurity and protective measures against cyber threats and other measures against electromagnetic threats;"
  - **`eu-easa-sib-2022-02r4-gnss`** (EASA Safety Information Bulletin SIB 2022-02R4 announcement, page 1, staged; `advisory`):
    > "Stakeholders are encouraged to implement the recommended measures as soon as possible so as to mitigate the impact of GNSS jamming and spoofing on aviation safety."
- **Recommendation:** DoT and TEC should notify a PNT resilience standard under **Telecom Act s. 19** requiring satellite earth station gateways and 5G base stations to support authenticated multi-constellation timing (NavIC + GNSS spoofing detection) and oscillator holdover, and amend **Authz Rule 59(4)** to set a 6-hour reporting deadline for detected RF/GNSS jamming or spoofing events.

---

## Candidate 3: `GAP-CAND-IN-12-SIGNALLING-AND-STORE-FORWARD-AUTH`
- **Topic:** `signalling_security`
- **Kind:** `standards`
- **Title:** Unspecified 5G NTN Store-and-Forward NAS/AKA authentication and emergency-roaming signalling security
- **Severity Score:** **4 / 5** — Intermittent feeder-link availability in LEO/MEO store-and-forward satellite operations leaves 5G NAS/AKA authentication incomplete and exposes user terminals and onboard satellite storage to unauthenticated control-plane denial-of-service and fake-satellite-ID spoofing.
- **Domain Gap:** When 5G or IoT user equipment connects via an emulated or live non-geostationary (LEO/MEO) satellite operating in Store-and-Forward (S&F) mode—or roams onto an alternate operator's network during a disaster—the satellite may not have a live feeder link to the ground core network (AMF/UDM/HSS) at the moment of registration. As documented by 3GPP SA3, incomplete mutual authentication (EPS/5G AKA) and unprotected NAS reject/interim messages allow an attacker over the air to exhaust onboard satellite storage with spoofed uplink requests or disconnect legitimate user terminals via forged `Attach Reject` messages with fake wait timers.
- **India & International Standards Evidence:**
  - **`intl-3gpp-tr-33700-29`** (3GPP TR 33.700-29 V19.1.0, Clause 4 line 318 & Clause 5.1.1–5.1.2 lines 331–339, read directly in `kb/sources/.text/intl-3gpp-tr-33700-29.txt`):
    > "Security for Store and Forward Satellite operation is only support for IoT NTN (EPS) in this release."
    > "1. The EPS/5G AKA procedure may not get fully completed or is partially completed. It results into incomplete procedure for mutual authentication between the network and the UE."
    > "For the downlink data (e.g., NAS message before authentication), similarly, the UE is not able to verify its integrity. It is hard to detect whether the data is sent from a legitimate network or an external attacker. As an example, the external attacker can send fake information (e.g., satellite ID(s), wait timer) in Attach Reject message thus resulting in DoS attack on the UE."
  - **`in-trai-satellite-low-bit-rate-recommendations` (page 2)** — TRAI Recommendations on Licensing Framework for Satellite Based Connectivity for Low Bit Rate Applications, Paragraph 7(b) & 7(d) (staged, not yet human-verified; `advisory`):
    > "All types of satellite viz. Geo Stationary Orbit (GSO) and Non-GSO (NGSO) satellites and any of the permitted satellite frequency bands may be used for providing satellite-based low-bit-rate connectivity."
  - **`in-authz-rules-2026:p101:c3`** (corpus chunk, Rule 38(2)(b), PDF p. 101; `binding`): Requires access-service licensees to *"implement roaming in accordance with the guidelines or directions issued by the Central Government or the designated agency"*, without specifying signalling-plane security controls for NTN or disaster roaming.
- **Global Examples:**
  - **`us-nist-ir-8401-2022`** (NIST IR 8401, Section 1.1, PDF p. 12, staged; `advisory`):
    > "respond to confidentiality breaches of Telemetry, Tracking, and Command (TT&C) and a manipulation or loss of satellite commands or telemetry in a timely, effective, and resilient manner; and"
  - **`us-cisa-satcom-advisory-2022`** (CISA-FBI Alert AA22-076A, Mitigations for SATCOM Network Providers, HTML, staged; `advisory`):
    > "The presence of insecure remote access tools—such as Teletype Network Protocol (Telnet), File Transfer Protocol (FTP), Secure Shell Protocol (SSH), Secure Copy Protocol (SCP), and Virtual Network Computing (VNC)—facilitating communications to and from SATCOM terminals."
- **Recommendation:** DoT, TEC, and TSDSI should require cryptographic ingress filtering and pre-provisioned authentication vectors (or cryptographic client puzzles per 3GPP TR 33.700-29 Solutions #7/#21) before enabling NGSO Store-and-Forward satellite services in India, and mandate signalling-firewall checks on inter-operator disaster roaming interfaces under **Authz Rule 38(2)(b)**.

---

## Candidate 4: `GAP-CAND-IN-13-AI-AGENT-AUTONOMY-GOVERNANCE`
- **Topic:** `ai_governance_and_manual_override`
- **Kind:** `coverage`
- **Title:** No binding rules for autonomous AI agent authorization, blast-radius limits, or mandatory manual hardware override in telecom/NTN self-healing
- **Severity Score:** **3 / 5** — Advisory space guidelines encourage AI/ML anomaly detection, but no binding Indian telecom or space rule requires Zero-Trust non-person entity (NPE) authorization, blast-radius caps, or manual hardware override if an automated or AI-driven network controller fails or is tampered with.
- **Domain Gap:** As telecom and emulated or live NTN operators adopt AI multi-agent systems for automated anomaly detection, traffic rerouting, and configuration patching, an compromised or hallucinating AI agent with write access to network configurations can trigger cascading outages across multiple sites or violate routing sovereignty rules. While advisory frameworks promote AI/ML analytics for detection, binding regulations lack guardrails for AI-driven *actuation*—specifically non-person entity (NPE) Zero-Trust authorization, staged blast-radius limits, and a mandatory manual hardware override.
- **India Evidence:**
  - **`in-space-fw-2026:p17:c0`** (corpus chunk, §5.7 Continuous Monitoring and Anomaly Detection, PDF p. 17; `non_binding`):
    > "Detect anomalies, unauthorized commands, or unusual data flows through AI/ML- assisted analytics."
  - **`in-dot-principal-telecom-authorisation-rules-2026` (page 106)** — Authz Rules, 2026, Rule 42(1)(b) (staged, not yet human-verified; `binding`):
    > "maintain a record of all software updates and changes, and provide to the Central Government details of such category of software updates and changes within fifteen days of completion of such updates and changes as decided by the Central Government from time to time:"
    *(Note: Requires ex-post record-keeping of software updates, but sets no pre-execution human-oversight or manual-override standard for AI-driven network changes.)*
- **Global Examples:**
  - **`eu-cer-article-13-guidelines-2026` (page 10)** — European Commission Guidelines on Article 13(5) of Directive (EU) 2022/2557 (CER), Paragraph 66 (auto-checked; `advisory` under binding CER Directive):
    > "Such measures may include identifying which specific sub-services are most critical so that they are the first to be restored (service prioritisation), maintaining the ability to operate hardware manually if the automated or AI-driven systems fail or are tampered with, and workforce recovery in case of a disruptive incident."
  - **`us-cisa-space-zero-trust-2024` (page 6)** — CISA Space Systems Security and Resilience Landscape: Zero Trust in the Space Environment, Section IV (staged; `advisory`):
    > "Once an entity is authorized (and that entity can be a person, or a non-person such as an artificial intelligence agent or another software process), the communications are secured. One way to secure communications is via encryption or segmentation."
  - **`ae-ai-charter-2026` (page null)** — UAE Charter for the Development and Use of Artificial Intelligence (auto-checked; `advisory`):
    > "The Charter emphasizes the irreplaceable value of human judgment and human oversight over AI, aligning with ethical values and social standards to correct any errors or biases that may arise."
- **Recommendation:** DoT and CERT-In should supplement **CTIR Rule 7** and the **2026 Space Cyber Security Framework** with binding operational guardrails for automated/AI-driven network remediation: (1) explicit Zero-Trust authorization and scoped credentials for AI agents, (2) staged rollout and blast-radius limits, and (3) a mandatory manual override capability (per `eu-cer-article-13-guidelines-2026`, p. 10) allowing human operators to lock out AI actuation and operate critical gateways manually if the AI system fails or is tampered with.

---

## Candidate 5: `GAP-CAND-IN-14-HYBRID-MULTI-ORBIT-TRUST-BOUNDARY`
- **Topic:** `supply_chain_and_multi_orbit_trust`
- **Kind:** `standards`
- **Title:** Shared satellite gateways are permitted under Authz Rule 61(1), but no Zero-Trust tenant-isolation standard governs multi-operator or hybrid satellite networks
- **Severity Score:** **3 / 5** — Allowing multiple telecom licensees to share a satellite earth station gateway or lease capacity across third-party GSO/NGSO constellations without a binding multi-tenant isolation standard creates a cross-operator lateral-movement risk.
- **Domain Gap:** Modern non-terrestrial networks increasingly operate as **Hybrid Satellite Networks (HSNs)** in which multiple mobile operators, enterprise users, and space-segment providers share physical satellite earth station gateways, ground cloud infrastructure, or hosted payloads. While licensing rules permit gateway sharing and mandate procuring hardware from "trusted sources," they do not define cryptographic tenant isolation, virtual routing separation, or Zero-Trust boundary controls between co-resident operators sharing an earth station gateway.
- **India Evidence:**
  - **`in-authz-rules-2026:p113:c2`** (corpus chunk, Rule 61(1), PDF p. 113; `binding`):
    > "61. Rollout obligations.—(1) Every new authorised entity having permission under rule 59 for provision of principal telecommunication service, may establish its own satellite earth station gateway or use the satellite earth station gateway established by other new authorised entities or licensees that are eligible for sharing or providing such satellite earth station gateways under the terms of their respective authorisation or license."
  - **`in-trai-space-spectrum-consultation-2023` (page 32)** — TRAI Consultation Paper on Assignment of Spectrum for Space-based Communication Services, Paragraph 2.55 (staged, not yet human-verified; `advisory`):
    > "According to 3GPP15, for the service continuity between NTN and Terrestrial Networks (TN), 5G system shall support service continuity between 5G terrestrial access network and 5G satellite access networks owned by the same operator or owned by two different operators having an agreement."
  - **`IN-AUTHZ-2026-R54-1`** (verified record, `in-authz-rules-2026` Rule 54(1)(a), PDF p. 109; `binding`) & **`in-dot-nsdts-amendment-2026`** (staged, PDF p. 2; `binding`): Require general network security and connecting only "Trusted Products" from "Trusted Sources," but set no multi-tenant isolation requirements for shared satellite gateways under Rule 61(1).
- **Global Examples:**
  - **`us-nist-ir-8441-2023` (page 4 & page 9)** — NIST IR 8441, Cybersecurity Framework Profile for Hybrid Satellite Networks (HSN), Abstract & Section 1 (staged; `advisory`):
    > "The space sector is transitioning towards Hybrid Satellite Networks (HSN) which is an aggregation of independently owned and operated terminals, antennas, satellites, payloads, or other components that comprise a satellite system."
    > "The components within an HSN are likely to have varying levels of trust among different components, requiring frameworks for establishing confidentiality and integrity of individual components while still enabling availability of required shared services."
  - **`us-cisa-satcom-advisory-2022` (page null - HTML)** — Joint CISA-FBI Alert AA22-076A, Mitigations for SATCOM Network Providers and Customers (staged; `advisory`):
    > "Review existing trust relationships with IT service providers. Threat actors are known to exploit trust relationships between providers and their customers to gain access to customer networks and data."
- **Recommendation:** DoT and NCCS should issue binding technical security conditions under **Authz Rule 61(1)** and **Telecom Act s. 19** requiring any shared satellite earth station gateway to enforce hardware-backed cryptographic tenant isolation, separate management planes per lessee, and Zero-Trust inter-operator interfaces modeled on **NIST IR 8441**.
