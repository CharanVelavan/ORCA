# Scenario Readiness coverage

Status: approved mappings applied to the dashboard scenario briefings and v7 report, 10 November 2026.
These are **planned coverage counts out of the nine settled project dimensions**, not ITU scores,
observed-run completion counts or a claim of national AI readiness. The allowed set is **D3, D4, D6, D7,
D8, D9, D10, D11, D13**. Do not add D1, D2, D5 or D12.

## Mapping basis and counting rule

The current contract is [CODEX_HANDOFF.md](../../../CODEX_HANDOFF.md), §2.3, and
[REPORT_V4_PLAN.md](REPORT_V4_PLAN.md), Table 3 plan. The existing v4 builder's Table 3 is read-only
source material: `../submission/v4/build_v4.py` from the repo root. It maps C to D7/D4, PP/M to D3/D13,
P to D10/D6, D to D8/D9, and SINK to D11. Older `docs/BUILD_PLAN_v2.md` proposes a smaller claim and is
superseded. Older parent-folder pitch pages also contain obsolete hardware and country claims; their
component descriptions must not be copied into the report.

Count a dimension only when the scenario has an explicit planned activity that exercises the mapped
capability. A component existing elsewhere in the project is insufficient. Count each ID once per scenario.
D4 here means **scenario/context adaptation**, as in the v4 C-node mapping: site, weather, integrity and
jurisdiction affect decisions. It does not mean every scenario performs an India/EU comparison. Current
fresh-run UI uses India; EU replay/comparison evidence is a separate evaluation.

| Scenario | Proposed planned count | Dimension IDs | Scenario-specific reason and source |
|---|---:|---|---|
| **S0 — normal baseline** | **5/9** | D3, D4, D7, D10, D13 | [s0.yaml](../../scenarios/s0.yaml): traffic/weather/link observations, domestic-gateway context and routine cited compliance establish the cross-domain baseline. `playbooks: []`; human decision is explicitly “without manual intervention”. Do not count human intervention/collaboration/impact or an inclusion recovery from merely naming 112. |
| **S1 — management intrusion** | **9/9** | D3, D4, D6, D7, D8, D9, D10, D11, D13 | [s1.yaml](../../scenarios/s1.yaml): management breach affects hospital, 112 and payments; owner conflict and human sequencing, notices and verified domestic failover exercise the full planned chain. |
| **S2 — rain, battery and priority** | **9/9** | D3, D4, D6, D7, D8, D9, D10, D11, D13 | [s2.yaml](../../scenarios/s2.yaml): weather/power/service evidence, temporary human priority order for 112/hospital/grid, warning and constrained-capacity recovery. Priority is operational, not an invented statutory order. |
| **S3 — jamming and unsafe routes** | **9/9** | D3, D4, D6, D7, D8, D9, D10, D11, D13 | [s3.yaml](../../scenarios/s3.yaml): Adyar/112 continuity, fault-versus-jamming evidence, rejection of trap/foreign paths and human-approved domestic path B. This is a jamming scenario, not the older KB-swap description. |
| **N1 — hospital power failure** | **9/9** | D3, D4, D6, D7, D8, D9, D10, D11, D13 | [n1.yaml](../../scenarios/n1.yaml): power-to-telecom dependency, battery forecasts, hospital/112 priority, warning and human-authorised backup recovery. |
| **N2 — payment routing error** | **8/9** | D3, D4, D6, D7, D8, D9, D10, D13 | [n2.yaml](../../scenarios/n2.yaml): maintenance/routing/transaction evidence, merchant advisory and approved domestic failover. Exclude D11: general payment availability alone does not establish inclusion or protection of a prioritised vulnerable service. |
| **N3 — unprotected feeder-link audit** | **8/9** | D3, D4, D6, D7, D8, D9, D10, D13 | [n3.yaml](../../scenarios/n3.yaml): configuration audit, operational telemetry, M3 abstention, standards-gap analysis and proactive human-approved protected-path migration. Exclude D11: no scripted everyday-impact or inclusion-priority outcome. |
| **N4 — false management telemetry** | **9/9** | D3, D4, D6, D7, D8, D9, D10, D11, D13 | [n4.yaml](../../scenarios/n4.yaml): independent 112/user-plane evidence, human resolution of contradictory reports, ordered containment/failover and emergency warning. |
| **N5 — reporting clocks and grid** | **9/9** | D3, D4, D6, D7, D8, D9, D10, D11, D13 | [n5.yaml](../../scenarios/n5.yaml): telecom/grid incident, explicitly degraded 112 routing, independent reporting triggers, human clock alignment, grid warning and authorised domestic failover. |
| **CAP — compound incident** | **9/9** | D3, D4, D6, D7, D8, D9, D10, D11, D13 | [cap.yaml](../../scenarios/cap.yaml): concurrent weather/intrusion/battery/capacity constraints, human triage of 112/hospital/grid, unsafe-route rejection, containment and warnings. |

## What would count as observed proof

These are the project's working dimension labels. They are not a replacement for the official framework.
The implementation references describe where to inspect evidence; they do not certify that a particular run passed.

| ID | Why it is mapped | Evidence needed before an observed-run claim |
|---|---|---|
| D3 — cross-domain prevention, detection and response | Telecom, power/weather and service facts enter the response pipeline. | Time-stamped public telemetry/model/incident evidence plus the relevant response record. Baseline evidence alone supports only baseline integration. |
| D4 — contextualisation | Site, hazard, backup-path integrity and domestic-gateway context change a decision. | Explicit contextual facts and the resulting model/rule/route decision; a country-comparison claim additionally needs paired India/EU runs. |
| D6 — human interface | A person can inspect, approve, reject and stop bounded changes. | The actual approval/decision/kill record and scope. A visible button or scripted commander step is insufficient. |
| D7 — strategy alignment | Objectives are decomposed into role-owned tasks and ordered plans. | Role tasks/messages, owner assignment and the recorded sequence; an institutional strategy claim needs external evidence beyond this sandbox. |
| D8 — collaboration with AI | Agent proposals inform a human decision under explicit boundaries. | Linked agent proposal, cited explanation and human decision. Do not claim an AI-only/human-only benefit without a measured comparison. |
| D9 — impact of humans | Human choices can change sequence, scope or priorities. | Recorded decision and its linked downstream change; use actual approval latency where available. Scripted stand-ins must be labelled. |
| D10 — AI and policies | Deterministic rules cite verified records; candidate gaps preserve bounded evidence. | Actual cited verdict, legal status/trigger metadata and a candidate/human gap review where applicable. “Not found” is bounded to the searched sources. |
| D11 — AI for inclusion | Explicit emergency/hospital service protection or priority is planned. | Per-service demand/delivery and a recorded priority/warning/response. Service names or aggregate uptime alone are insufficient; no real-world equity outcome is claimed. |
| D13 — digital infrastructure | Link, battery, gateway and capacity state are modelled. | Emulated telemetry, model/allocation/route records and measured service outcomes; do not imply deployed satellite infrastructure. |

Useful implementation references: [docs/APPLICATION_ROLES.md](../AGENTS.md), [orca/protocol.py](../../orca/protocol.py),
[orca/remediation.py](../../orca/remediation.py), [orca/live/session.py](../../orca/live/session.py), and
[dashboard/live/web/src/workflow.ts](../../dashboard/live/web/src/workflow.ts). Human review confirmation,
execution, clean-path success, staged rollout and re-attack success remain separate facts.

## Report wording basis

> The project maps its implemented capabilities to nine selected AI Readiness 2.0 dimensions: D3, D4,
> D6, D7, D8, D9, D10, D11 and D13. Scenario plans exercise different subsets: five for the normal
> baseline, eight for payment-routing and feeder-link audits, and nine for the seven full incident
> scenarios. These are planned mappings, not official readiness scores. Observed evidence is reported
> separately for each recorded run; scripted decisions and unmet outcomes remain labelled.

The dashboard briefing displays each planned count, included IDs and scenario-specific rationale.
The v7 report includes the counts, exclusions and rationale. No automatic observed-coverage score is
computed. Such a score would need evidence gates bound to one run and replay cursor, with missing or
failed outcomes retained for review.
