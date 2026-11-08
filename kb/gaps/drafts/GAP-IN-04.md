# GAP-IN-04: Telecom Sites Must Have Power Redundancy, But No Minimum Hours Are Set

> **Review 8 Nov:** the reviewer saw only staged quotes; the Indian evidence is the verified records (CEA 8(11) 10 h for grid equipment; DoT SOP 3.1.3 no hours; TRAI QoS 3.2 excludes power failures). Kept.


- **Gap ID:** `GAP-IN-04-NO-BATTERY-FLOOR`
- **Topic:** `backup_power`
- **Kind:** `ambiguity`
- **Current Register Status:** `confirmed`

## 1. Domain Gap & Severity
When a cyber-physical incident or natural disaster causes a regional electric-grid outage, emulated or live non-terrestrial network (NTN) earth station gateways, satellite user terminals, and connected cellular base stations rely on local battery and generator backup to keep emergency traffic alive. Where telecom regulations require only qualitative "sufficient" or "required" power redundancy and measure availability only via monthly averaged cell-downtime percentages, an operator can satisfy monthly quality-of-service benchmarks while individual disaster-zone sites drain their batteries in a few hours, severing satellite backhaul and 112 emergency access during a prolonged grid outage.

- **Severity Score:** **3 / 5**
- **Reason:** Qualitative power-redundancy rules without a numeric autonomy floor allow critical telecom and satellite-backhaul sites to go dark during multi-hour grid outages while still meeting monthly average uptime targets.

## 2. India Evidence

### Verified Records (`kb/india/records.yaml`)
- **`IN-TRAI-QOS-2024-3-2`** (TRAI Standards of Quality of Service of Access and Broadband Service Regulations, 2024, Regulation 3(2), PDF p. 101; `binding`):
  > "The quality management plan shall provide for required redundancies including power, transmission links, equipment, geo-redundancies in the core network and access network as per relevant standards to achieve end-to-end QoS as per the benchmarks specified in these regulations."
- **`IN-DOT-SOP-2017-3-1-3`** (DoT Standard Operating Procedure (SOP-2017) for Telecommunication Services for Responding to Disasters, §3.1.3, PDF p. 9; `not_stated`):
  > "All the vulnerable critical network components should have sufficient redundancy including transmission links and power backups in terms of battery storage capacity and diesel / fuel availability."
- **`IN-CEA-2020-8-11`** (CEA (Technical Standards for Communication System in Power System Operations) Regulations, 2020, Regulation 8(11), Gazette p. 304 / PDF p. 7; `binding`):
  > "Communication equipment for all the nodes shall be provided with at least ten hours battery backup and extended backup shall be provided depending upon the requirement."

### Staged Quotes (auto-checked, not yet human-verified)
- **`in-trai-qos-2024` (page 113)** — TRAI Standards of Quality of Service of Access and Broadband Service Regulations, 2024, Schedule, para 4.1.3(ii) (`IN-TRAI-QOS-2024-4-1-3` verified):
  > "All such SNOs shall be reported to the Authority within 24 Hrs. from the start of any such outage."
- **`in-cea-cyber-power-guidelines-2021` (page 3)** — CEA Guidelines on Cyber Security in Power Sector 2021, Section 2.0 (auto-checked, not yet human-verified):
  > "**[DROPPED 8 Nov: irrelevant, review row 50]** The requester and the user shall comply with cyber security guidelines issued by the Central Government, from time to time, and the technical standards for communication system in Power Sector laid down by the Authority."

### What Is Missing
India's binding telecom QoS regulation (`IN-TRAI-QOS-2024-3-2`) requires an access provider's quality management plan to provide *"required redundancies including power,"* and DoT's disaster SOP (`IN-DOT-SOP-2017-3-1-3`) asks for *"sufficient"* battery storage capacity and diesel/fuel availability at vulnerable critical network components. Neither sets a minimum numeric duration (in hours) of backup power autonomy for cellular base stations, core nodes, or satellite earth station gateways. By contrast, India's power-sector regulator already mandates a binding **10-hour battery floor** for power-system communication nodes (`IN-CEA-2020-8-11`).

## 3. Global Examples

1. **US FCC 911 Reliability Order — 24-Hour and 72-Hour Numeric Backup Power Floor (`us-fcc-911-reliability-2013`, staged auto-checked)**
   - **Instrument:** FCC Report and Order 13-158 / 47 CFR Part 12 (Improving 911 Reliability)
   - **Clause:** Appendix B, 47 CFR § 12.4(c)(2)(i)(C)
   - **Issuing Authority:** Federal Communications Commission (US)
   - **Binding Status:** `binding`
   - **Exact Quote (`us-fcc-911-reliability-2013`, Appendix B, 47 CFR § 12.4(c)(2)(i)(C), page 68, auto-checked):**
     > "Provisions backup power through fixed generators, portable generators, batteries, fuel cells, or a combination of these or other such sources to maintain full-service functionality, including network monitoring capabilities, for at least 24 hours at full office load or, if the central office hosts a Selective Router, at least 72 hours at full office load; provided, however, that any such portable generators shall be readily available within the time it takes the batteries to drain, notwithstanding potential demand for such generators elsewhere in the service provider’s network."
   - **How it closes the gap:** Replaces qualitative "sufficient power" language with a binding, auditable numeric standard: **at least 24 hours** at full load for central offices and **at least 72 hours** at full load for selective router hubs, including network monitoring capabilities and guaranteed generator dispatch before batteries drain.

2. **California Public Utilities Commission (CPUC) Wireless & Wireline 72-Hour Resiliency Decisions (`us-cpuc-d20-07-011-2020` & `us-cpuc-d21-02-029-2021`, staged auto-checked)**
   - **Instrument:** CPUC Decision D.20-07-011 (Wireless Provider Resiliency Strategies) and Decision D.21-02-029 (Wireline Provider Resiliency Strategies)
   - **Clause:** D.20-07-011 Ordering Paragraph 1 & 2 (pp. 146, 148); D.21-02-029 Ordering Paragraph 4 (p. 106)
   - **Issuing Authority:** California Public Utilities Commission (US-CA)
   - **Binding Status:** `binding`
   - **Exact Quote (`us-cpuc-d20-07-011-2020`, Ordering Paragraph 2, page 148, auto-checked):**
     > "Facilities-based wireless providers shall, in their Communications Resiliency Plan pursuant to Section 6.5.2 of this decision, demonstrate their ability to meet the 72-hour backup power requirement, in Tier 2 and Tier 3 High Fire Threat Districts"
   - **Exact Quote (`us-cpuc-d21-02-029-2021`, Ordering Paragraph 4, page 106, auto-checked):**
     > "Facilities-based wireline providers shall, in their Communications Resiliency Plan pursuant to Section 5.6.2 of this decision, demonstrate their ability to: (a) meet the 72-hour backup power requirement, in Tier 2 and Tier 3 High Fire Threat Districts"
   - **How it closes the gap:** Imposes a mandatory **72-hour backup power requirement** on both wireless and wireline facilities in high-hazard zones specifically to preserve emergency calling (9-1-1), emergency notifications, and basic internet access for emergency notices during grid shutoffs.

3. **ENISA EECC Security Measures Guideline & EU CER Directive (`enisa-eecc-security-measures-guideline` & `eu-cer-2022-2557`, staged auto-checked)**
   - **Instrument:** ENISA Guideline on Security Measures under the EECC (4th ed.) and Directive (EU) 2022/2557 (CER)
   - **Clause:** ENISA Security Objective SO10 (p. 26); CER Directive Article 13(1)(d) (p. 20)
   - **Issuing Authority:** ENISA; European Parliament and Council
   - **Binding Status:** ENISA Guideline is `advisory`; CER Directive is `binding`
   - **Exact Quote (`enisa-eecc-security-measures-guideline`, SO10, page 26, auto-checked):**
     > "Establish and maintain appropriate security of critical supplies (for example electric power, fuel, cooling etc.24)."
   - **How it closes the gap:** Requires telecom operators to maintain audited security and continuity of electric power, fuel, and cooling supplies, though—unlike the US FCC/CPUC and India's CEA—the EU texts leave exact hourly autonomy floors to national implementation.

## 4. Recommendation

- **Domain-Level Recommendation:** Telecom regulators should establish a tiered, numeric backup-power autonomy floor (combining on-site batteries, solar/fuel cells, and guaranteed generator fuel) for telecom and NTN ground infrastructure: e.g., **at least 10 to 24 hours** for emergency-corridor cellular base stations and critical-infrastructure sites, and **at least 24 to 72 hours** for satellite earth station gateways, core switches, and emergency call-routing hubs, paired with authorization for automated non-critical load-shedding (`PB-09` / `PB-15`) when grid power fails.
- **Application to India:**
  1. **Department of Telecommunications (DoT) & TRAI:** Amend **TRAI's Quality of Service Regulations, 2024** (`IN-TRAI-QOS-2024-3-2`) and issue a binding direction under **Rule 38(1) of the 2026 Authorisation Rules** / **Rule 7 of the Critical Telecommunication Infrastructure Rules, 2024** (`in-ctir-2024`) to replace the qualitative word *"sufficient"* in **DoT SOP-2017 §3.1.3** (`IN-DOT-SOP-2017-3-1-3`) with a numeric hourly floor—adopting India's own **10-hour battery floor from CEA Regulation 8(11)** (`IN-CEA-2020-8-11`) for priority access sites and the **24-to-72-hour FCC standard** (`us-fcc-911-reliability-2013`, p. 68) for satellite earth station gateways and CTI core hubs.

## 5. Search Record

- **Vector KB Queries Run (`orca.kbvec coverage` against `IN`):**
  1. Query: `"battery backup power redundancy minimum hours diesel UPS satellite earth station gateway telecom site"`
     - **Documents searched:** 18
     - **Nearest clauses returned:**
       - `in-dot-disaster-sop-2017:p9:c2` / `IN-DOT-SOP-2017-3-1-3` (score `0.7666` / `0.7608`, `not_stated`, §3.1.3 & §3.1.4, p. 9): Recommends *"sufficient redundancy including transmission links and power backups in terms of battery storage capacity and diesel / fuel availability"* and UPS with *"sufficient External Battery support."*
       - `IN-CEA-2020-8-11` (score `0.7499`, `binding`, Regulation 8(11), p. 304): Mandates *"at least ten hours battery backup"* for power-system communication nodes.
  2. Query: `"ten hours battery backup quality management plan required redundancies including power"`
     - **Documents searched:** 18
     - **Nearest clauses returned:**
       - `IN-CEA-2020-8-11` (score `0.7429`, `binding`, Regulation 8(11), p. 304): 10-hour battery floor for power-grid communication equipment.
       - `IN-DOT-SOP-2017-3-1-3` (score `0.6956`, `not_stated`, §3.1.3, p. 9): Non-numeric *"sufficient"* backup power in DoT's disaster SOP.
       - `IN-TRAI-QOS-2024-3-2` (score `0.6507`, `binding`, Regulation 3(2), p. 101): Requires quality management plans to provide *"required redundancies including power"* without specifying hours.
- **Why Nearest Clauses Do Not Close the Gap:** `TRAI QoS Regulation 3(2)` is binding on access providers but sets no number of hours; `DoT SOP-2017 §3.1.3` uses the qualitative term *"sufficient"* and has unstated legal force; and `CEA Regulation 8(11)` sets a binding 10-hour floor, but applies only to power-sector communication nodes, not telecom sites or satellite earth station gateways.

## 6. What a Human Must Decide
- **Updating `kb/gaps/india.yaml` with the new US FCC and CPUC global examples:** Previously `india.yaml` noted only the domestic CEA comparison (`IN-CEA-2020-8-11`). A human reviewer should decide whether to promote `us-fcc-911-reliability-2013` (p. 68, 24h/72h) and `us-cpuc-d20-07-011-2020` (p. 148, 72h) into `kb/global/records.yaml` and link them in `india.yaml`.
- **Note on `us-fcc-backup-power-rule-920`:** While 47 CFR § 9.20(b) required 8-hour and 24-hour customer premises backup power offerings, § 9.20(g) states that section ceased to be in effect as of September 1, 2025. The human reviewer should therefore rely on the in-force **47 CFR § 12.4(c)(2)(i)(C)** central-office/hub rule (`us-fcc-911-reliability-2013`, p. 68) and **CPUC D.20-07-011 / D.21-02-029** (`us-cpuc-d20-07-011-2020`, p. 148) rather than § 9.20.
