# Prompt for ChatGPT: plan ORCA-NTN demo scenarios (8 Nov 2026)

Paste everything below the line into ChatGPT.

---

You are helping me plan demo scenarios for a hackathon prototype. Read all the context first, then do
the task at the end. Do not invent laws, rule numbers or facts. Use only the gaps, rules and parts listed
here. If you need something that isn't listed, say "NEEDS CHECK" instead of making it up.

## 1. The project

- **Name:** ORCA-NTN (Orchestrated Response and Coordination Agents for Non-Terrestrial Networks).
- **Event:** ITU AI for Good Sandbox Hackathon, UAE. Submission on 10 Nov 2026. Jury priority: report >
  code > video. The report is 5 pages.
- **Theme:** cyber security in everyday life on satellite-backed (NTN) networks, plus self-healing.
- **Headline:** find real **policy gaps** in India's law, prove them with quotes, analyse their impact,
  take an interim action, and recommend a fix to a named regulator.
  Pipeline: **Detect → Prove → Analyse → Act → Recommend.**
- **Country:** India only. The EU and UAE are used only as comparisons.
- **City:** **Chennai, an urban setting.** Festivals (Deepavali), the NE monsoon and cyclones (Oct–Dec)
  are realistic triggers.
- **Everything is simulated.** It runs in an ITU-T Y.3172 ML sandbox. Every satellite link is
  **emulated**: never claim real satellite or 3GPP connectivity.

### Setting (emulated)
- Mobile towers in Chennai use **satellite backhaul** for some sites, with microwave or fibre on others.
- Services share the same satellite **operator's ground network**: a regional gateway plus a management
  system. Never say "everything goes through one gateway".
- Dependent everyday services:
  - 112 emergency calls;
  - hospitals;
  - UPI / card payment terminals;
  - the power utility's grid communications;
  - ATMs;
  - traffic signals and public alerts (Cell Broadcast).

### Parts of the system you can use
- **Agents** (LLM-based; they only assess, draft and explain; a human commander approves every action):
  - Mobile operator
  - Satellite operator
  - Power utility
  - National CERT (CERT-In)
  - Telecom regulator (DoT/TRAI, thin)
  - **Gap Analyst** (the lead agent)
  - Human incident commander
- **Rule engine:** deterministic YAML. Every verdict cites a knowledge-base record id. The six verdicts:
  - COMPLIANT
  - VIOLATION
  - AMBIGUITY
  - CONFLICT
  - POTENTIAL_GAP
  - INSUFFICIENT_EVIDENCE
- **ML models:**
  - **M1** anomaly detector (Isolation Forest).
  - **M2** backhaul and battery forecaster: rain fade vs link margin, minutes to outage.
  - **M3** fault-or-attack classifier. It returns 5 causes or abstains: normal, fault-weather,
    fault-power/equipment, attack-jamming, attack-management-plane. It explains itself with SHAP.
  - **M4** capacity allocator (greedy). It needs a priority order as input, but there is no legal one,
    so it always raises GAP-IN-03.
- **Playbooks.** Each is executed only by its owner, after a hashed, time-limited human approval and a
  test on a cloned sandbox. Rollout is staged 5→25→100% with auto-rollback.
  - PB-01 Disable exposed VPN account, rotate credentials (satellite operator)
  - PB-02 Enforce MFA on management access (satellite operator)
  - PB-03 Block attacker sources at the management firewall (satellite operator)
  - PB-04 Roll terminals back to last signed firmware (satellite operator)
  - PB-05 Isolate the management segment, keep logs (satellite operator)
  - PB-06 Fail over to a backup path verified clean first (mobile operator)
  - PB-07 Re-authenticate terminals and towers (mobile operator)
  - PB-08 Apply the vendor patch (asset owner)
  - PB-09 Shed non-critical load to protect the battery (mobile operator)
  - PB-10 Warn dependent services (hospitals, payments, 112) through the agent bus
  - **Built and executable:** PB-01, PB-06, PB-10. The others are specifications only, so prefer these
    three.
- **Hard legal constraint:** Authorisation Rules 2026, Rule 60(1)(b). Failover must not route Indian
  traffic through a foreign gateway.
- **Rules-off comparison:** every scenario is also run with the rule engine switched off, to show what
  goes wrong without it.
- **Judge inject:** judges can type their own event during the demo.

## 2. The confirmed policy gaps (human-reviewed; use only these)

"Not found" always means: not found in the sources we checked, as of 7–8 Nov 2026.

| Id | Gap | One-line evidence |
|---|---|---|
| GAP-IN-01 | Reporting clocks | One incident can need up to 4 reports to 3 bodies, with clocks that start at different moments: "becoming aware" (Telecom Cyber Security Rules 2024 r.7(1)(a), 6 h), "noticing" (CERT-In Directions 2022, 6 h) and "occurrence" (Critical Telecom Infrastructure Rules 2024 r.7(1)(j), 6 h). There is no single portal or clock. |
| GAP-IN-02 | No downstream warning | There is no binding duty to warn the services that depend on a network (hospitals, payments, 112). Authorisation Rule 37(5) even restricts sharing network information. |
| GAP-IN-03 | No priority order for scarce capacity | Telecom Act 2023 s.20(1)(b) allows priority routing by notification in a public emergency. There is no standing ranking of 112, hospitals, grid and payments when backhaul is scarce. |
| GAP-IN-04 | No battery floor | The DoT disaster SOP asks for "sufficient" power backup with no hours. India sets a numeric floor only for power-grid communications (CEA 2020 reg. 8(11)). |
| GAP-IN-06 | Link-security standards | 3GPP TR 33.700-29 says feeder links and inter-satellite links "are not specified in 3GPP". India's power to notify security standards (Telecom Act s.19) has not been used for satellite links. |
| GAP-IN-08 | Partial: clean failover | No explicit rule requires checking that the backup path is clean before failing over during an attack. Jamming can force traffic onto a trap path. |
| **GAP-IN-09** | **Headline: no binding satellite-specific cyber baseline** | The CERT-In / SIA-India space cyber framework (Feb 2026) is "advisory in nature" (PIB 2233122). India's equipment security standard requires a dedicated management interface and secure VPN (ITSAR Group IV 2.12.10, 2.12.12) only for office phone exchanges (PABX), not for satellite equipment. Those two controls are the KA-SAT 2022 entry points. |

**Rejected by the human reviewer.** Do NOT use these as gaps:
- GAP-IN-05: the data-breach clock exists, but its start date is deferred to May 2027.
- GAP-IN-07: "who leads" is general cyber coordination, not satellite-specific.

If a scenario touches one of them, the engine shows "rejected by a human reviewer". That is fine, and it
even helps to show the AI respecting a human decision.

**Negative controls.** These must come out COMPLIANT, never a gap:
- CERT-In Directions (ii) 6-hour report, (iii) point of contact, (iv) 180-day logs;
- Telecom Act s.2 covers "terrestrial or satellite networks".

## 3. Real attacks you may base scenarios on (facts already checked)

- **KA-SAT, 24 Feb 2022.** A misconfigured VPN gave access to the operator's management network.
  Commands sent from it wiped tens of thousands of user modems. About 5,800 Enercon wind turbines lost
  remote monitoring. The EU, UK and US attributed it to Russia.
- **"Don't Look Up", ACM CCS 2025.** 39 GEO satellites were observed with about $800 of equipment, and
  about 50% of the traffic was unencrypted.
- **Jamming to force failover.** This is a known pattern. Jamming a primary link pushes traffic to a
  backup path the attacker controls.

## 4. Scenarios already drafted (refine these; don't duplicate them)

- **S0 Normal day:** the control run; everything COMPLIANT.
- **S1 KA-SAT replay:** VPN → management network → wipe commands brick Chennai terminals; 112 and
  payments fail. Gaps 09, 01, 02.
- **S2 Traffic overload:** a festival or cyclone surge saturates backhaul. M3 must say "load, not
  attack", because that decides which legal rules apply. Agents disagree on who gets capacity
  (PB-05 vs PB-06 conflict). Gaps 03, 04.
- **S3 Self-healing:** a hacker compromises the link serving one cell. ORCA checks the backup path is
  clean, then other emulated satellites or beams take over the cell, staying on Indian gateways
  (Rule 60(1)(b)). Gaps 08, 06.

## 5. The task

Plan scenarios for an **urban Chennai** setting. Give me:

**A. Refined versions of S1, S2 and S3** (the three most crucial ones), in the format below.

**B. Five NEW candidate scenarios**, also urban Chennai and different from S1–S3. I will pick the best
ones. Good candidates:
- hit services people use every day;
- have a believable cause, either a real attack pattern or a real Chennai event;
- make the rule engine produce at least one gap;
- show self-healing or a human decision.

**C. One "capstone" scenario that covers ALL 7 confirmed gaps** (01, 02, 03, 04, 06, 08, 09) in one
believable timeline of at most about 3 hours of event time. It must stay realistic; don't force every
gap in. Mark which minute each gap fires.

### Format for every scenario
1. **Title and one-line story**, in plain words.
2. **Trigger and cause**: attack or fault, and which M3 class should come out.
3. **Timeline**: 6–12 timestamped events (T+0 min …), each naming the agent or model that acts.
4. **Everyday impact**: who in Chennai notices, and when.
5. **Rule-engine verdicts expected**: verdict, topic and gap id, with the event that triggers each.
6. **Models used**: M1/M2/M3/M4, with the input signal each one sees.
7. **Playbooks**: which ones, who owns each, who approves, and the clean-path check if failover happens.
8. **Self-healing step**: what heals, and how we prove it healed (metric before and after).
9. **Human decision point(s)**: what the commander must decide and why the AI can't.
10. **Rules-off contrast**: what goes wrong without the rule engine (one or two lines).
11. **Data needed**: synthetic signals to generate (link SNR, packet loss, battery %, login events,
    traffic load, etc.).
12. **Demo length**: target 60–120 seconds of screen time.
13. **Risks**: anything that might be unrealistic, or that needs a fact check (mark it NEEDS CHECK).

### Then give
- A **coverage matrix**: scenarios × gaps 01/02/03/04/06/08/09, plus which M1–M4 and PB-xx each uses.
- Your **ranking** of the 5 new candidates, with one line of reasoning each.

### Rules for your answer
- Use short, simple sentences (5–7 words where possible).
- Describe all satellite links as emulated.
- Do not invent laws, clause numbers, incidents or statistics. Use only what is above, or mark NEEDS
  CHECK.
- Do not use GAP-IN-05 or GAP-IN-07 as gaps.
- Keep failover on Indian gateways (Rule 60(1)(b)).
- Prefer PB-01, PB-06 and PB-10. Others may appear as "specified, not executed".
