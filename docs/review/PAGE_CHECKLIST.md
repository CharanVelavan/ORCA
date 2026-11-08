# Page check list (8 Nov)

Every staged quote the gap drafts (`kb/gaps/drafts/`) rely on. All 78 already match the text word for word
(`kb/staging/_quotecheck.yaml`), so you are NOT checking spelling. For each row, open the file at the page and tick three things:

1. **Page:** the quote is on that PDF page (PDF viewer page, not the printed number). `html` = no pages; use Cmd-F.
2. **Relevance:** the quote says what the gap needs (the "Check" line for that gap).
3. **Binding:** the binding status is right for the *document* (binding law / advisory / draft / not stated).

Mark each row `ok`, `wrong page N`, `irrelevant`, or `binding wrong: X`. I then promote the ok ones to `kb/*/records.yaml`
with `verified: false` for you to flip, or you flip them yourself.

Known problems already found (no need to recheck, I will fix): 3GPP TR 22.822 / 38.821 are not "approved";
TRAI PPDR 15/2017; Space Policy "approved by Cabinet"; MDRI date 27 June; ITU Res 644/646 mismatch; CTIR duplicate.

## GAP-IN-09 (10 quotes)

**Check:** India has no BINDING satellite-specific cyber baseline. Check: the quote is advisory or general (not a binding satellite cyber control). If a quote is a binding, satellite-specific technical control, flag it: it weakens the gap.

| # | Document | File | Page | Binding | Quote (start) | Result |
|---|---|---|---|---|---|---|
| 1 | `in-space-cyber-framework-2026` | `corpus/raw/india/in-space-cyber-framework-2026.pdf` | 12 | not stated | All SatCom operators and service providers must report cybersecurity incidents, breaches, or anomalies within … | |
| 2 | `in-space-cyber-framework-2026` | `corpus/raw/india/in-space-cyber-framework-2026.pdf` | 33 | not stated | All confirmed or suspected cybersecurity incidents affecting satellite networks, ground control systems, or us… | |
| 3 | `in-space-policy-2023` | `corpus/raw/india/in-space-policy-2023.pdf` | 8 | advisory | for telecommunication services shall be governed by the rules, regulations and policies of Department of Telec… | |
| 4 | `in-space-policy-2023` | `corpus/raw/india/in-space-policy-2023.pdf` | 8 | advisory | issue guidelines for meeting safety and security requirements for space objects. | |
| 5 | `inspace-ngp-2024` | `corpus/raw/india/inspace-ngp-2024.pdf` | 22 | binding | IN-SPACe may impose control on operations of the Authorized Space Objects & Space Activities or terminate/susp… | |
| 6 | `inspace-ngp-2024` | `corpus/raw/india/inspace-ngp-2024.pdf` | 71 | binding | Assure cyber security including encryptions at design level and prevent unauthorized commandeering of satellit… | |
| 7 | `eu-space-act-proposal-2025` | `corpus/raw/global/eu-space-act-proposal-2025.html` | html | draft | Union space operators shall take all the necessary measures to manage the risks posed to the security of netwo… | |
| 8 | `eu-space-act-proposal-2025` | `corpus/raw/global/eu-space-act-proposal-2025.html` | html | draft | To date, the cybersecurity of the space sector has been only partly addressed at Union level through a general… | |
| 9 | `eu-space-programme-2021-696` | `corpus/raw/global/eu-space-programme-2021-696.pdf` | 42 | binding | the protection of infrastructure, both ground and space, and of the provision of services, particularly agains… | |
| 10 | `us-fcc-part-4-outage` | `corpus/raw/global/us-fcc-part-4-outage.xml` | html | binding | In addition, all Mobile-Satellite Service (“MSS”) satellite operators shall submit electronically a Notificati… | |

## GAP-IN-02 (7 quotes)

**Check:** No duty to warn downstream dependants (hospitals, 112, banks) of a satellite outage. Check: the quote only covers reporting to the Government/CERT, or (global) shows a duty to notify customers/PSAPs.

| # | Document | File | Page | Binding | Quote (start) | Result |
|---|---|---|---|---|---|---|
| 11 | `in-dot-telecom-standards-rules-2025` | `corpus/raw/india/in-dot-telecom-standards-rules-2025.pdf` | 9 | binding | An authorised entity or a licensee shall, upon becoming aware that a user of its telecommunication services is… | |
| 12 | `in-nciipc-cii-rules-2013` | `corpus/raw/india/in-nciipc-cii-rules-2013.pdf` | 3 | binding | Coordinating, sharing, monitoring, collecting, analysing and forecasting, national-level threats to critical i… | |
| 13 | `in-space-cyber-framework-2026` | `corpus/raw/india/in-space-cyber-framework-2026.pdf` | 32 | not stated | Unified Incident Response: Ensure coordinated procedures among operators, ground stations, and service provide… | |
| 14 | `in-tcsr-2024` | `corpus/raw/india/in-tcsr-2024.pdf` | 5 | binding | The Central Government may, where it determines that disclosure of the security incident is in the public inte… | |
| 15 | `eu-eecc-2018-1972` | `corpus/raw/global/eu-eecc-2018-1972.pdf` | 148 | binding | Member States shall ensure that, when public warning systems regarding imminent or developing major emergencie… | |
| 16 | `eu-nis2-2022` | `corpus/raw/global/eu-nis2-2022.html` | html | binding | Where appropriate, entities concerned shall notify, without undue delay, the recipients of their services of s… | |
| 17 | `us-fcc-911-reliability-2013` | `corpus/raw/global/us-fcc-911-reliability-2013.pdf` | 64 | binding | In addition to any other obligations imposed in this section, within thirty minutes of discovering an outage t… | |

## GAP-IN-08 (8 quotes)

**Check:** Law requires redundancy and an Indian gateway but no clean-path / integrity check before failover. Check: the quote is about redundancy or gateway location, not about verifying a backup path is secure.

| # | Document | File | Page | Binding | Quote (start) | Result |
|---|---|---|---|---|---|---|
| 18 | `in-ctir-2024` | `corpus/raw/india/in-ctir-2024.pdf` | 8 | binding | implement standard operating procedures for security incident response systems, including disaster recovery an… | |
| 19 | `in-dot-unified-licence` | `corpus/raw/india/in-dot-unified-licence.pdf` | 107 | binding | The operation and maintenance centre of the GMPCS Gateway shall also be located in India. | |
| 20 | `in-dot-unified-licence` | `corpus/raw/india/in-dot-unified-licence.pdf` | 110 | binding | All calls originating or terminating from Mobile Terminals in India shall pass through the GMPCS Gateway Switc… | |
| 21 | `in-dot-unified-licence` | `corpus/raw/india/in-dot-unified-licence.pdf` | 110 | binding | Domestic traffic should not be hauled/ routed to any place outside India. | |
| 22 | `in-rbi-psos-cyber-resilience-2024` | `corpus/raw/india/in-rbi-psos-cyber-resilience-2024.html` | html | binding | The PSO shall develop a BCP based on different cyber threat scenarios, including extreme but plausible events … | |
| 23 | `enisa-eecc-security-measures-guideline` | `corpus/raw/global/enisa-eecc-security-measures-guideline.pdf` | 36 | advisory | Establish and maintain an appropriate disaster recovery capability for restoring network and communication ser… | |
| 24 | `us-fcc-911-reliability-2013` | `corpus/raw/global/us-fcc-911-reliability-2013.pdf` | 67 | binding | Eliminated all single points of failure in Critical 911 Circuits or equivalent data paths serving each PSAP. | |
| 25 | `us-fcc-mdri-order-2022` | `corpus/raw/global/us-fcc-mdri-order-2022.pdf` | 23 | binding | Provide for reasonable roaming under disaster arrangements (RuDs) when technically feasible, where: (A) A requ… | |

## GAP-IN-01 (12 quotes)

**Check:** Different clocks start at different triggers (noticing / awareness / occurrence). Check: the exact trigger word and hour count in the quote.

| # | Document | File | Page | Binding | Quote (start) | Result |
|---|---|---|---|---|---|---|
| 26 | `in-cea-cyber-power-guidelines-2021` | `corpus/raw/india/in-cea-cyber-power-guidelines-2021.pdf` | 14 | binding | The Responsible Entity shall ensure that the CISO compiles details of incident detection, incident handling, l… | |
| 27 | `in-ctir-2024` | `corpus/raw/india/in-ctir-2024.pdf` | 8 | binding | implement mechanisms to ensure intimation of security incident(s) to the Central Government, no later than six… | |
| 28 | `in-rbi-psos-cyber-resilience-2024` | `corpus/raw/india/in-rbi-psos-cyber-resilience-2024.html` | html | binding | Any cyber security incident shall also be reported to CERT-In. | |
| 29 | `in-tcsr-2024` | `corpus/raw/india/in-tcsr-2024.pdf` | 5 | binding | within six hours of becoming aware of a security incident affecting its telecommunication network or telecommu… | |
| 30 | `in-tcsr-2024` | `corpus/raw/india/in-tcsr-2024.pdf` | 5 | binding | within twenty-four hours of becoming aware of such incident, furnish the following information, as applicable: | |
| 31 | `inspace-ngp-2024` | `corpus/raw/india/inspace-ngp-2024.pdf` | 22 | binding | In case of any accident, malfunction, emergency or any other incident which impacts the operation of an Author… | |
| 32 | `eu-cer-2022-2557` | `corpus/raw/global/eu-cer-2022-2557.pdf` | 22 | binding | Member States shall ensure that, unless operationally unable to do so, critical entities submit an initial not… | |
| 33 | `eu-cyber-resilience-act-2024` | `corpus/raw/global/eu-cyber-resilience-act-2024.pdf` | 38 | binding | A manufacturer shall notify any actively exploited vulnerability contained in the product with digital element… | |
| 34 | `eu-cyber-resilience-act-2024` | `corpus/raw/global/eu-cyber-resilience-act-2024.pdf` | 38 | binding | an early warning notification of an actively exploited vulnerability, without undue delay and in any event wit… | |
| 35 | `eu-nis2-2022` | `corpus/raw/global/eu-nis2-2022.html` | html | binding | without undue delay and in any event within 24 hours of becoming aware of the significant incident, an early w… | |
| 36 | `eu-nis2-ir-2024-2690` | `corpus/raw/global/eu-nis2-ir-2024-2690.pdf` | 11 | binding | the integrity, confidentiality or authenticity of stored, transmitted or processed data related to the provisi… | |
| 37 | `us-fcc-part-4-outage` | `corpus/raw/global/us-fcc-part-4-outage.xml` | html | binding | All satellite operators shall submit electronically a Notification to the Commission within 120 minutes of dis… | |

## GAP-IN-03 (12 quotes)

**Check:** No rule says which wins: containment (cut the link) or continuity (keep 112 up). Check: the quote gives priority to emergency traffic or a containment power, without settling the order between them.

| # | Document | File | Page | Binding | Quote (start) | Result |
|---|---|---|---|---|---|---|
| 38 | `in-dot-unified-licence` | `corpus/raw/india/in-dot-unified-licence.pdf` | 29 | binding | The Licensee shall also facilitate the priority routing of emergency/public utility or any other type of user … | |
| 39 | `in-mha-erss` | `corpus/raw/india/in-mha-erss.html` | html | not stated | Genuine, actionable calls from citizen on the ‘Call-Taking System’ are forwarded with complete incident data t… | |
| 40 | `in-ndma-communication-guidelines` | `corpus/raw/india/in-ndma-communication-guidelines.pdf` | 187 | advisory | voice packets are given higher priority than the data packets at each node of the network to ensure minimum/ c… | |
| 41 | `in-ndma-communication-guidelines` | `corpus/raw/india/in-ndma-communication-guidelines.pdf` | 193 | advisory | During network busy periods, priority call service allows access to network resources in order of user termina… | |
| 42 | `in-ndma-communication-guidelines` | `corpus/raw/india/in-ndma-communication-guidelines.pdf` | 193 | advisory | This call service, of which the highest priority is the emergency call, provides the highest uplink priority a… | |
| 43 | `in-ndma-communication-guidelines` | `corpus/raw/india/in-ndma-communication-guidelines.pdf` | 193 | advisory | If a network is busy, the lowest priority communication is dropped to handle the emergency call. | |
| 44 | `in-telact-2023` | `corpus/raw/india/in-telact-2023.pdf` | 9 | binding | provide for appropriate mechanism to ensure that messages of a user or group of users authorised for response … | |
| 45 | `eu-cer-article-13-guidelines-2026` | `corpus/raw/global/eu-cer-article-13-guidelines-2026.pdf` | 10 | advisory | Such measures may include identifying which specific sub-services are most critical so that they are the first… | |
| 46 | `eu-eecc-2018-1972` | `corpus/raw/global/eu-eecc-2018-1972.pdf` | 146 | binding | Member States shall ensure that providers of voice communications services take all necessary measures to ensu… | |
| 47 | `eu-iris2-regulation-2023-588` | `corpus/raw/global/eu-iris2-regulation-2023-588.pdf` | 15 | binding | ensure the provision and long-term availability within the Union’s territory and worldwide uninterrupted acces… | |
| 48 | `eu-net-neutrality-2015-2120` | `corpus/raw/global/eu-net-neutrality-2015-2120.pdf` | 9 | binding | preserve the integrity and security of the network, of services provided via that network, and of the terminal… | |
| 49 | `eu-net-neutrality-2015-2120` | `corpus/raw/global/eu-net-neutrality-2015-2120.pdf` | 9 | binding | prevent impending network congestion and mitigate the effects of exceptional or temporary network congestion, … | |

## GAP-IN-04 (5 quotes)

**Check:** No numeric battery-hour floor for towers in India. Check: Indian quotes have no hour number; global quotes do (24 h / 72 h).

| # | Document | File | Page | Binding | Quote (start) | Result |
|---|---|---|---|---|---|---|
| 50 | `in-cea-cyber-power-guidelines-2021` | `corpus/raw/india/in-cea-cyber-power-guidelines-2021.pdf` | 3 | binding | The requester and the user shall comply with cyber security guidelines issued by the Central Government, from … | |
| 51 | `enisa-eecc-security-measures-guideline` | `corpus/raw/global/enisa-eecc-security-measures-guideline.pdf` | 26 | advisory | Establish and maintain appropriate security of critical supplies (for example electric power, fuel, cooling et… | |
| 52 | `us-cpuc-d20-07-011-2020` | `corpus/raw/global/us-cpuc-d20-07-011-2020.pdf` | 148 | binding | Facilities-based wireless providers shall, in their Communications Resiliency Plan pursuant to Section 6.5.2 o… | |
| 53 | `us-cpuc-d21-02-029-2021` | `corpus/raw/global/us-cpuc-d21-02-029-2021.pdf` | 106 | binding | Facilities-based wireline providers shall, in their Communications Resiliency Plan pursuant to Section 5.6.2 o… | |
| 54 | `us-fcc-911-reliability-2013` | `corpus/raw/global/us-fcc-911-reliability-2013.pdf` | 68 | binding | Provisions backup power through fixed generators, portable generators, batteries, fuel cells, or a combination… | |

## GAP-IN-06 (9 quotes)

**Check:** Space-link encryption (e.g. CCSDS SDLS) is not mandatory in India. Check: Indian quotes make standards mandatory only once notified, or are advisory; nothing mandates satellite-link crypto.

| # | Document | File | Page | Binding | Quote (start) | Result |
|---|---|---|---|---|---|---|
| 55 | `in-ctir-2024` | `corpus/raw/india/in-ctir-2024.pdf` | 7 | binding | Every telecommunication entity shall ensure that Critical Telecommunication Infrastructure, including any spar… | |
| 56 | `in-dot-telecom-standards-rules-2025` | `corpus/raw/india/in-dot-telecom-standards-rules-2025.pdf` | 8 | binding | No telecommunication equipment to which a standard applies, shall be sold or deployed in any telecommunication… | |
| 57 | `in-space-cyber-framework-2026` | `corpus/raw/india/in-space-cyber-framework-2026.pdf` | 12 | not stated | All mission systems, ground infrastructure, and communication networks must comply with Catalogue of Indian St… | |
| 58 | `inspace-ngp-2024` | `corpus/raw/india/inspace-ngp-2024.pdf` | 20 | binding | Where specific standards for Space Activities are not explicitly mentioned in this document or any other appli… | |
| 59 | `enisa-space-threat-landscape-2025` | `corpus/raw/global/enisa-space-threat-landscape-2025.pdf` | 7 | advisory | Deployment of validated and tested cryptographic technologies measures into space systems; | |
| 60 | `eu-cybersecurity-act-2019` | `corpus/raw/global/eu-cybersecurity-act-2019.pdf` | 42 | binding | A European cybersecurity certification scheme may specify one or more of the following assurance levels for IC… | |
| 61 | `eu-space-programme-2021-696` | `corpus/raw/global/eu-space-programme-2021-696.pdf` | 41 | binding | to use the security rules of the Council and of the Commission, which provide, inter alia, for a separation be… | |
| 62 | `eu-space-programme-2021-696` | `corpus/raw/global/eu-space-programme-2021-696.pdf` | 42 | binding | the protection of infrastructure, both ground and space, and of the provision of services, particularly agains… | |
| 63 | `us-nist-ir-8270-2023` | `corpus/raw/global/us-nist-ir-8270-2023.pdf` | 12 | advisory | Communications between operational satellites for mission functions – such as command and control, networking … | |

## _new-candidates (15 quotes)

**Check:** Candidate gaps GAP-CAND-IN-10..14 (log retention, GNSS/PNT, store-and-forward, AI-agent autonomy, multi-orbit trust). Check: the quote supports the candidate topic; then tell me confirm or reject per candidate.

| # | Document | File | Page | Binding | Quote (start) | Result |
|---|---|---|---|---|---|---|
| 64 | `in-ctir-2024` | `corpus/raw/india/in-ctir-2024.pdf` | 8 | binding | preserve in a secure manner, for a minimum period of two years or such other period as may be determined by th… | |
| 65 | `in-dot-principal-telecom-authorisation-rules-2026` | `corpus/raw/india/in-dot-principal-telecom-authorisation-rules-2026.pdf` | 106 | binding | maintain a record of all software updates and changes, and provide to the Central Government details of such c… | |
| 66 | `in-telecom-network-rules-2026` | `corpus/raw/india/in-telecom-network-rules-2026.pdf` | 40 | binding | Every new authorised entity shall ensure that all systems of its telecommunication network and the data, logs … | |
| 67 | `in-trai-satellite-low-bit-rate-recommendations` | `corpus/raw/india/in-trai-satellite-low-bit-rate-recommendations.pdf` | 2 | advisory | All types of satellite viz. Geo Stationary Orbit (GSO) and Non-GSO (NGSO) satellites and any of the permitted … | |
| 68 | `in-trai-space-spectrum-consultation-2023` | `corpus/raw/india/in-trai-space-spectrum-consultation-2023.pdf` | 32 | advisory | According to 3GPP15, for the service continuity between NTN and Terrestrial Networks (TN), 5G system shall sup… | |
| 69 | `ae-ai-charter-2026` | `corpus/raw/global/ae-ai-charter-2026.html` | html | advisory | The Charter emphasizes the irreplaceable value of human judgment and human oversight over AI, aligning with et… | |
| 70 | `eu-cer-article-13-guidelines-2026` | `corpus/raw/global/eu-cer-article-13-guidelines-2026.pdf` | 10 | advisory | Such measures may include identifying which specific sub-services are most critical so that they are the first… | |
| 71 | `eu-easa-sib-2022-02r4-gnss` | `corpus/raw/global/eu-easa-sib-2022-02r4-gnss.html` | 1 | advisory | Stakeholders are encouraged to implement the recommended measures as soon as possible so as to mitigate the im… | |
| 72 | `eu-iris2-regulation-2023-588` | `corpus/raw/global/eu-iris2-regulation-2023-588.pdf` | 15 | binding | increase the robustness of the Union’s and the Member States’ communication services and the cyber resilience … | |
| 73 | `us-cisa-satcom-advisory-2022` | `corpus/raw/global/us-cisa-satcom-advisory-2022.html` | html | advisory | The presence of insecure remote access tools—such as Teletype Network Protocol (Telnet), File Transfer Protoco… | |
| 74 | `us-cisa-satcom-advisory-2022` | `corpus/raw/global/us-cisa-satcom-advisory-2022.html` | html | advisory | Review existing trust relationships with IT service providers. Threat actors are known to exploit trust relati… | |
| 75 | `us-cisa-space-zero-trust-2024` | `corpus/raw/global/us-cisa-space-zero-trust-2024.pdf` | 6 | advisory | Once an entity is authorized (and that entity can be a person, or a non-person such as an artificial intellige… | |
| 76 | `us-nist-ir-8401-2022` | `corpus/raw/global/us-nist-ir-8401-2022.pdf` | 12 | advisory | respond to confidentiality breaches of Telemetry, Tracking, and Command (TT&C) and a manipulation or loss of s… | |
| 77 | `us-nist-ir-8441-2023` | `corpus/raw/global/us-nist-ir-8441-2023.pdf` | 4 | advisory | The space sector is transitioning towards Hybrid Satellite Networks (HSN) which is an aggregation of independe… | |
| 78 | `us-nist-ir-8441-2023` | `corpus/raw/global/us-nist-ir-8441-2023.pdf` | 9 | advisory | The components within an HSN are likely to have varying levels of trust among different components, requiring … | |
