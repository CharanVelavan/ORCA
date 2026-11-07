# Scenario file format (v1, 8 Nov 2026)

One YAML file per scenario in `scenarios/`. A file is **data, not code**. The simulator turns `signals` into
time series (seeded). The runner merges each event's `facts` into the rule-engine facts (format: docstring
of `orca/rules.py`), runs the engine after every event, and checks the `expect` list. A scenario whose
expected verdicts do not appear fails its test.

All satellite links, towers, attacks and services are **emulated**. Never claim real connectivity.

## Top level

```yaml
id: S1                       # S0..S3, N1..N5, CAP
title: The night Chennai's satellite terminals disappear
story: One plain sentence.
kind: attack                 # normal | attack | fault | mixed | audit
start: "2026-11-10T19:00:00+05:30"   # T+0. Every time in the file is minutes after this.
seed: 101                    # simulator seed (S0=100, S1=101, ... CAP=110)
jurisdiction: IN
entity: {designated_cti: true}       # true only if the scenario says the operator is critical telecom infrastructure
m3_expected: attack-management-plane # normal | fault-weather | fault-power/equipment | attack-jamming
                                     # | attack-management-plane | abstain (benign overload = normal)
sites: [CHN-01, CHN-02]      # from the site list below
everyday_impact:             # who in Chennai notices, and from which minute
  - {who: "112 callers", from: 24, what: "calls fail"}
events: [...]                # see below
playbooks: [...]             # see below
heal: {...}                  # see below
human_decisions: ["..."]
rules_off: "What goes wrong without the rule engine (one or two lines)."
demo_seconds: 110
risks: ["...", "NEEDS CHECK: ..."]
```

## Events

```yaml
events:
  - t: 0                     # minutes after start
    actor: M1                # M1 | M2 | M3 | M4 | attacker | environment | judge | satellite_operator |
                             # mobile_operator | power_utility | cert_in | regulator | gap_analyst | commander
    what: M1 flags an unusual VPN login.
    signals:                 # optional; inputs for the simulator (names and units below)
      - {site: CHN-02, signal: vpn_login, value: {user: noc-vendor-7, anomalous: true}}
    facts:                   # optional; merged into the rule-engine facts (lists are appended)
      obligation_questions:
        - {id: Q-S1-SPACE, topic: space_cyber, text: Is there a binding satellite-specific cyber baseline?}
    expect:                  # optional; verdicts that must exist after this event
      - {verdict: POTENTIAL_GAP, gap: GAP-IN-09-SPACE-CYBER-ADVISORY}
```

### Signal names (the simulator knows only these)
| signal | value | unit / notes |
|---|---|---|
| `snr_db` | number | link SNR |
| `rain_mm_h` | number | rain rate (drives fade in M2) |
| `link_margin_db` | number | margin left on the link |
| `packet_loss` | 0..1 | fraction |
| `traffic_load` | `{service: 112\|hospital\|payments\|grid\|general, load: 0..2}` | 1.0 = capacity |
| `mains_power` | 0 or 1 | site mains supply |
| `battery_pct` | 0..100 | site battery |
| `vpn_login` | `{user, anomalous: bool}` | management VPN session |
| `mgmt_command` | `{type: wipe\|reboot\|config_change\|telemetry_edit, count}` | management-plane commands |
| `terminals_up` | integer | backhaul modems online at the site |
| `telemetry_reported` | `{metric, value}` | what the management system says |
| `route_candidate` | `{path: A\|B\|..., gateway: GW-IN-1\|GW-IN-2\|GW-XX, integrity: verified\|unverified\|failed}` | backup path offered |
| `link_protection` | `protected\|unprotected` | audit result for a link |
| `txn_success` | `{service, rate: 0..1}` | measured service success |

### Facts → verdicts (checked on the engine, 8 Nov; use exactly these)
| Gap | How to trigger it | Verdict the engine returns |
|---|---|---|
| GAP-IN-01-REPORTING-CLOCKS | `triggers` with **different** times for `noticing`, `awareness` and `occurrence`, plus `applies: [IN-CERTIN-DIR-2022-ii, IN-TCSR-2024-R7-1, IN-CTIR-2024-R7-1-j]` (CTIR only when `entity.designated_cti: true`) | `AMBIGUITY` (rule IN-R-CLOCKS) |
| GAP-IN-02-NO-DOWNSTREAM-WARNING | obligation question, topic `downstream_warning` | `POTENTIAL_GAP` |
| GAP-IN-03-NO-PRIORITY-ORDER | obligation question, topic `capacity_priority` | `AMBIGUITY` |
| GAP-IN-04-NO-BATTERY-FLOOR | obligation question, topic `backup_power` | `AMBIGUITY` |
| GAP-IN-06-STANDARDS | obligation question, topic `standards` | `POTENTIAL_GAP` |
| GAP-IN-08-NO-CLEAN-PATH-CHECK | obligation question, topic `failover_path_security` | `POTENTIAL_GAP` |
| GAP-IN-09-SPACE-CYBER-ADVISORY | obligation question, topic `space_cyber` | `POTENTIAL_GAP` |

Other results you may use:
- Indian gateway check: question topic `data_location` gives `COMPLIANT` (Authz Rule 60(1)(b)). A route through
  `GW-XX` (foreign) is **blocked by PB-06's precondition**, not by an engine verdict; write it as an event by
  `mobile_operator`, with no `expect`.
- Report sent in time: `reports: [{record: IN-CERTIN-DIR-2022-ii, sent_at: ...}]` gives `COMPLIANT` for that deadline rule.
- Fault then attack: `classifications: [{at, label: fault}, {at, label: attack}]` gives an AMBIGUITY note.
- PB-05 vs PB-06 on the same target: `proposed_actions` with both gives `CONFLICT` (rule IN-R-CONFLICT-PB05-PB06).
  Its linked topic `joint_command` is GAP-IN-07, **rejected by a human**, so the CONFLICT line carries
  `gap_id: null` and a note "rejected gap GAP-IN-07 … not raised as a gap". No extra verdict line is added
  and no `GAP-CAND-*` id is created. That is good evidence of the AI respecting a human decision.
- Never use topics `joint_command` or `personal_data_breach` to claim a gap (GAP-IN-07 and -05 are rejected).
  Never use `emergency_priority` (no record; it would invent a candidate gap).
- Negative controls (S0): topics `incident_reporting`, `telecom_cyber_security`, `data_location` give `COMPLIANT`.

## Playbooks

```yaml
playbooks:
  - {id: PB-01, owner: satellite_operator, approver: commander, executed: true}
  - {id: PB-06, owner: mobile_operator, approver: commander, executed: true,
     precondition: "path integrity verified and gateway in India (Authz Rule 60(1)(b))"}
  - {id: PB-10, owner: mobile_operator, approver: commander, executed: true}   # Gap Analyst drafts the warning
  - {id: PB-05, owner: satellite_operator, approver: commander, executed: false, note: "specified, not executed"}
```
Only PB-01, PB-06 and PB-10 may have `executed: true`. Every executed playbook implies: hashed, time-limited
human approval; cloned-sandbox test; staged rollout 5→25→100%; auto-rollback.

## Heal

```yaml
heal:
  what: Tower CHN-02 moves from its wiped satellite modem to microwave backhaul.
  metric: txn_success            # or packet_loss
  service: 112
  site: CHN-02
  target_before: 0.42            # TARGETS for the simulator. The report quotes measured values only.
  target_after: 0.95
  proof: [route trace shows GW-IN-2, path B integrity verified, txn_success measured after]
```

## Fixed sites and gateways (emulated)
| id | area | role | backhaul |
|---|---|---|---|
| CHN-01 | Park Town | hospital corridor | satellite (GW-IN-1), microwave backup |
| CHN-02 | T. Nagar | shops, UPI and ATMs | satellite (GW-IN-1), microwave backup |
| CHN-03 | Adyar | homes, 112 | microwave, satellite backup |
| CHN-04 | Guindy | grid communications (power utility) | fibre, satellite backup |
| CHN-05 | Ennore | coastal, cyclone-exposed | satellite (GW-IN-1), satellite backup via GW-IN-2 |
| CHN-06 | OMR | offices, traffic signals | microwave, fibre backup |

Gateways: `GW-IN-1` (India, primary), `GW-IN-2` (India, backup), `GW-XX` (outside India; forbidden by
Authz Rule 60(1)(b), "including during failure of satellite earth station gateway located in India").

## Event routing (agents, 8 Nov)
- Optional event key `to: [roles]` is the explicit release list: only those roles see the event. Without it,
  the event goes to its actor role, else to roles whose `sees` (agents/roles/*.yaml) matches its signals.
- Attacker and environment events never reach agents as text: agents see only the observed signals.
