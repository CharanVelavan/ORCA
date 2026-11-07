# GAP-IN-03: Priority Callers Exist for Disaster Restoration, But No Binding Ranking for Sharing Scarce Backup Capacity

- **Gap ID:** `GAP-IN-03-NO-PRIORITY-ORDER`
- **Topic:** `capacity_priority`
- **Kind:** `ambiguity`
- **Current Register Status:** `confirmed`

## 1. Domain Gap & Severity
When a primary terrestrial or satellite link fails or is jammed and traffic fails over onto a bandwidth-constrained emulated or live non-terrestrial network (NTN) backup link, total demand from emergency callers, hospitals, power-grid control centres, payment systems, and general subscribers exceeds available link capacity. While telecommunications laws empower governments to order priority routing for authorized responders during declared emergencies and disaster SOPs list categories of "priority callers" for service restoration, no binding, pre-established multi-tier traffic-priority ladder ranks live traffic classes (e.g., Tier 1: emergency 112/PSAP and grid/telecommand control; Tier 2: hospitals and public safety; Tier 3: financial/payments; Tier 4: general consumer data) so an operator or automated controller can lawfully throttle lower tiers during sudden congestion.

- **Severity Score:** **4 / 5**
- **Reason:** Without a binding pre-authorized priority order across critical service classes, an operator throttling traffic on a congested emulated or live NTN backup link must improvise life-safety versus critical-infrastructure trade-offs without regulatory cover.

## 2. India Evidence

### Verified Records (`kb/india/records.yaml`)
- **`IN-DOT-SOP-2017-3-2-5`** (DoT Standard Operating Procedure (SOP-2017) for Telecommunication Services for Responding to Disasters, §3.2.5, PDF p. 12; `not_stated`):
  > "Priority is to be given to these groups for provisioning of additional communication facilities and restoration of telecom services, if required, for quick and efficient rescue and relief operations."
- **`IN-TELACT-2023-20`** (Telecommunications Act, 2023, Section 20(1)(b), PDF p. 9; `binding`):
  > "provide for appropriate mechanism to ensure that messages of a user or group of users authorised for response and recovery during public emergency are routed on priority."
- **`IN-AUTHZ-2026-R38-2-a`** (Telecommunications (Authorisation for Provision of Principal Telecommunication Services) Rules, 2026, Rule 38(2)(a), PDF p. 101; `binding`):
  > "facilitate dissemination of alert messages through short message service, cell broadcast or any other means as may be directed by Central Government, State Government or any officer authorised in this behalf"

### Staged Quotes (auto-checked, not yet human-verified)
- **`in-dot-unified-licence` (page 29)** — Unified Licence Agreement, Part I, Condition 28 (auto-checked, not yet human-verified):
  > "The Licensee shall also facilitate the priority routing of emergency/public utility or any other type of user calls as per guidelines /directions as may be prescribed by Licensor."
- **`in-ndma-communication-guidelines` (page 187)** — National Disaster Management Guidelines: National Disaster Management Information and Communication System (NDMICS), Appendix 20 (auto-checked, not yet human-verified):
  > "voice packets are given higher priority than the data packets at each node of the network to ensure minimum/ constant delay and sent to destination."
- **`in-ndma-communication-guidelines` (page 193)** — NDMA Communication Guidelines (NDMICS), Appendix 24 (auto-checked, not yet human-verified):
  > "During network busy periods, priority call service allows access to network resources in order of user terminals call priority status."
- **`in-ndma-communication-guidelines` (page 193)** — NDMA Communication Guidelines (NDMICS), Appendix 24 (auto-checked, not yet human-verified):
  > "This call service, of which the highest priority is the emergency call, provides the highest uplink priority and highest priority access to network resources."
- **`in-ndma-communication-guidelines` (page 193)** — NDMA Communication Guidelines (NDMICS), Appendix 24 (auto-checked, not yet human-verified):
  > "If a network is busy, the lowest priority communication is dropped to handle the emergency call."
- **`in-mha-erss` (page null - HTML)** — Ministry of Home Affairs, Emergency Response Support System (ERSS-112) (auto-checked, not yet human-verified):
  > "Genuine, actionable calls from citizen on the ‘Call-Taking System’ are forwarded with complete incident data to a ‘Dispatcher’ of Police / Health / Fire / Disaster / Women / Children / Railways helpline system for further actions."

### What Is Missing
India has four pieces of the puzzle, but none forms a binding, ordered live-traffic priority ladder:
1. **Telecom Act s. 20(1)(b)** (`IN-TELACT-2023-20`) and **Unified Licence Condition 28** (`in-dot-unified-licence`, p. 29) authorize priority routing of responder/emergency/public-utility calls *on notification or direction*, rather than establishing a standing multi-class order that applies immediately when an attack degrades a link.
2. **DoT SOP-2017 §3.2.5** (`IN-DOT-SOP-2017-3-2-5`) lists priority user groups (government agencies, police, fire, medical, civil defence, Red Cross, Army, financial institutions, NGOs, telecom restoration staff), but presents them as an unranked open list (*"might include"*) for *provisioning and restoration*, not live packet scheduling.
3. **NDMA NDMICS Guidelines** (`in-ndma-communication-guidelines`, pp. 187, 193) describe terminal call-priority status, voice-over-data queueing, and dropping lowest-priority traffic for emergency calls, but are advisory 2012 disaster guidelines and do not rank critical non-voice data classes (such as hospital telemetry, power-grid SCADA, or payment clearing) against one another on shared satellite backhaul.

## 3. Global Examples

1. **EU Open Internet Access (Net Neutrality) Regulation (`eu-net-neutrality-2015-2120`, staged auto-checked)**
   - **Instrument:** Regulation (EU) 2015/2120 on open internet access
   - **Clause:** Article 3(3)(b) and Article 3(3)(c)
   - **Issuing Authority:** European Parliament and Council
   - **Binding Status:** `binding` (directly applicable EU Regulation)
   - **Exact Quote (`eu-net-neutrality-2015-2120`, Article 3(3)(b), page 9, auto-checked):**
     > "preserve the integrity and security of the network, of services provided via that network, and of the terminal equipment of end-users;"
   - **Exact Quote (`eu-net-neutrality-2015-2120`, Article 3(3)(c), page 9, auto-checked):**
     > "prevent impending network congestion and mitigate the effects of exceptional or temporary network congestion, provided that equivalent categories of traffic are treated equally."
   - **How it closes the gap:** Gives operators a standing, directly applicable statutory exception from equal-traffic-treatment rules to prioritize traffic categories in order to preserve network security/integrity and mitigate exceptional congestion without awaiting a government emergency notification.

2. **EU Critical Entities Resilience (CER) Article 13 Guidelines (`eu-cer-article-13-guidelines-2026`, staged auto-checked)**
   - **Instrument:** European Commission Guidelines on the application of Article 13(5) of Directive (EU) 2022/2557 (C/2026/3712)
   - **Clause:** Paragraph 66
   - **Issuing Authority:** European Commission
   - **Binding Status:** `advisory` (official Commission guidance under binding CER Directive Art. 13)
   - **Exact Quote (`eu-cer-article-13-guidelines-2026`, Paragraph 66, page 10, auto-checked):**
     > "Such measures may include identifying which specific sub-services are most critical so that they are the first to be restored (service prioritisation), maintaining the ability to operate hardware manually if the automated or AI-driven systems fail or are tampered with, and workforce recovery in case of a disruptive incident."
   - **How it closes the gap:** Explicitly directs critical entities to pre-define sub-service prioritization ladders before an incident occurs and pairs automated/AI-driven prioritization with mandatory manual override capabilities.

3. **EU Electronic Communications Code & UAE TDRA Interconnection Instructions (`eu-eecc-2018-1972` staged auto-checked; `AE-TDRA-IC-2006-EMERGENCY` verified)**
   - **Instrument:** Directive (EU) 2018/1972 (EECC) and UAE TDRA Interconnection Instructions v1.2
   - **Clause:** EECC Article 108; TDRA Interconnection Instructions, Emergency calls
   - **Issuing Authority:** European Parliament and Council; TDRA (UAE)
   - **Binding Status:** `binding`
   - **Exact Quote (`eu-eecc-2018-1972`, Article 108, page 146, auto-checked):**
     > "Member States shall ensure that providers of voice communications services take all necessary measures to ensure uninterrupted access to emergency services and uninterrupted transmission of public warnings."
   - **Exact Quote (`AE-TDRA-IC-2006-EMERGENCY`, PDF p. 21, verified):**
     > "All emergency calls must be treated with the highest priority within the Points of Interconnection."
   - **How it closes the gap:** Establishes an absolute, binding top tier for emergency calls and public warnings at interconnection and network bottlenecks, though (like India) neither text establishes a full multi-tier ranking for non-voice critical infrastructure classes below Tier 1.

4. **EU IRIS² Secure Connectivity Regulation (`eu-iris2-regulation-2023-588`, staged auto-checked)**
   - **Instrument:** Regulation (EU) 2023/588 establishing the Union Secure Connectivity Programme (IRIS²)
   - **Clause:** Article 3(1)(a)
   - **Issuing Authority:** European Parliament and Council
   - **Binding Status:** `binding`
   - **Exact Quote (`eu-iris2-regulation-2023-588`, Article 3(1)(a), page 15, auto-checked):**
     > "ensure the provision and long-term availability within the Union’s territory and worldwide uninterrupted access to secure, autonomous, high-quality, reliable and cost-effective satellite governmental communication services to government-authorised users, by establishing a multi-orbital, secure connectivity system under civil control and by supporting the protection of critical infrastructures"
   - **How it closes the gap:** Dedicates sovereign satellite capacity by statute to government-authorized users and critical infrastructure protection during crises.

## 4. Recommendation

- **Domain-Level Recommendation:** Telecom regulators should promulgate a standing, ordered multi-tier traffic priority schedule for bandwidth-constrained backup links (including emulated or live NTN satellite backhaul) that operators are pre-authorized to enforce automatically or via human commander approval whenever primary backhaul is lost or degraded:
  - **Tier 1:** Emergency calls/messages (112 / PSAP), public disaster warnings, and network/satellite TT&C and power-grid teleprotection control signals.
  - **Tier 2:** Government emergency operation centres, police, fire, hospitals/medical services, and telecom restoration teams.
  - **Tier 3:** Regulated financial/payment clearing and essential public utilities.
  - **Tier 4:** General commercial and consumer best-effort traffic (subject to rate-limiting or load-shedding during congestion).
- **Application to India:**
  1. **Department of Telecommunications (DoT):** Issue a standing notification/guideline under **Section 20(1)(b) of the Telecommunications Act, 2023** (`IN-TELACT-2023-20`), **Rule 38(1) of the 2026 Authorisation Rules** (`in-dot-principal-telecom-authorisation-rules-2026`, p. 101), and **Unified Licence Condition 28** (`in-dot-unified-licence`, p. 29) converting the unranked priority user groups in **DoT SOP-2017 §3.2.5** (`IN-DOT-SOP-2017-3-2-5`) and the preemption logic in **NDMA NDMICS Appendix 24** (`in-ndma-communication-guidelines`, p. 193) into a binding four-tier QoS preemption schedule for congested backup links.
  2. **Telecom Regulatory Authority of India (TRAI):** Incorporate standing emergency congestion-management and priority-queueing exemptions into TRAI's Quality of Service Regulations (`in-trai-qos-2024`) so operators are not penalized for throttling Tier 4 traffic while preserving Tier 1–3 services on backup satellite links.

## 5. Search Record

- **Vector KB Queries Run (`orca.kbvec coverage` against `IN`):**
  1. Query: `"priority callers priority user groups emergency communication 112 PSAP scarce backup capacity ranking satellite backhaul"`
     - **Documents searched:** 18
     - **Nearest clauses returned:**
       - `in-dot-disaster-sop-2017:p12:c1` / `IN-DOT-SOP-2017-3-2-5` (score `0.7535` / `0.7452`, `not_stated`, §3.2.5, p. 12): Identifies priority user groups (government agencies, police, fire, medical, civil defence, Red Cross, Army, financial institutions, NGOs, restoration staff) for provisioning of additional facilities and restoration.
       - `IN-TELACT-2023-20` (score `0.7456`, `binding`, Section 20(1)(b), p. 9): Empowers government by notification during a public emergency to ensure messages of authorized response/recovery users are routed on priority.
  2. Query: `"messages authorised for response and recovery during public emergency routed on priority end-to-end priority"`
     - **Documents searched:** 18
     - **Nearest clauses returned:**
       - `IN-TELACT-2023-20` / `in-telact-2023:p9:c3` (score `0.8651` / `0.7582`, `binding`, Section 20(1)(b), p. 9): Case-by-case notification power for priority routing during public emergencies.
       - `in-authz-rules-2026:p101:c3` (score `0.7328`, `binding`, Rule 38(1)–(2), p. 101): Requires adherence to Central Government disaster guidelines, alert dissemination, and intra-circle roaming as directed.
- **Why Nearest Clauses Do Not Close the Gap:** `Telecom Act s. 20(1)(b)` is an enabling power requiring a specific emergency notification rather than a standing rule for sudden link congestion; `DoT SOP-2017 §3.2.5` is an unranked open list for restoration and provisioning; and `NDMA NDMICS` (`in-ndma-communication-guidelines`, p. 193) is advisory guidance from 2012. None provides a binding, ordered ranking across live traffic classes (112, hospitals, grid control, payments, ordinary traffic) when an operator must ration scarce satellite backhaul.

## 6. What a Human Must Decide
- **Whether to add `in-ndma-communication-guidelines` (p. 193) and `in-dot-unified-licence` (p. 29) to `kb/gaps/india.yaml`:** Both passed the automated quote check and materially strengthen the India evidence by showing that Unified Licence Condition 28 anticipates Licensor priority-routing guidelines and NDMA Appendix 24 already describes call-priority preemption in advisory form.
- **Exact relative rank of power-grid telemetry versus hospital/medical traffic below 112:** When DoT converts SOP-2017 §3.2.5 into a ranked schedule, a human policymaker must decide whether machine-to-machine power-grid protection shares Tier 1 with 112 calls (because grid collapse downs the telecom towers themselves) or sits in Tier 2 alongside hospitals.
