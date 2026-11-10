# ORCA Live Console - build spec (v1, 8 Nov 2026)

Owner of the spec: the lead. Builders: Codex A (engine + API), Codex B (UI). The lead reviews every
phase against the acceptance tests in section 9 before the next phase starts.

## 1. What it is
A live control console for the emulated Chennai NTN. The simulation runs; the human (incident
commander) injects attacks and faults with a click; models detect; agents coordinate, request
playbooks, heal and patch; the human sets autonomy, approves with the PIN, gives orders, or pulls the
kill switch. Every session is recorded to the hash-chained audit JSONL, so any live session replays
offline in the same UI.

Non-negotiables:
- **Safety lives in the engine, never in the UI.** Buttons only call existing code paths:
  `orca.remediation.Remediation` (owner-only playbooks, PIN-hashed approvals, autonomy grants,
  auto-downgrade, kill switch), `orca.protocol` (sharing limits), `orca.rules` (verdicts). The UI can
  never execute anything the engine would refuse. No new bypass, no "demo mode" that skips checks.
- **Everything is emulated.** Every satellite link, attack and service is a simulator condition. The UI
  shows an "Emulated network" badge; links are labelled "(emulated)". No exploit code anywhere.
- **Offline.** No CDN, no internet. Vendored JS only. Works with `--llm mock` with no model running.
- **Recorded.** Each session writes `runs/live-<YYYYmmdd-HHMMSS>-<scenario>-<rules|norules>-<llm>.jsonl`
  via `World.log`, readable by the existing `dashboard/adapter.py`.
- No AI attribution anywhere. Never log or print the PIN or tokens (log only hashes, as now).

## 2. Existing code to reuse (read before building)
| Need | Use |
|---|---|
| Minute simulator, conditions, telemetry | `orca/sim/engine.py` `Simulator` (`add(kind, site, start, end, **params)`, `pin`, `offer_route`, `failover`, `step`, `site_history`, `path_report`); condition kinds and classes in its docstring |
| Network configs, patches, clean-path check, clone test, rollback | `orca/sim/netstate.py`, `orca/sim/netops.py` (`check_path_clean`, `apply_playbook`, `clone_test`, `verify`, `rollback`, `attach`) |
| Attack chains | `orca/sim/attacks.py` (`ka_sat_chain`, `default_cred_login`, `feeder_intercept`, `firmware_exploit`, `foreign_failover`, `reattacks_for`) |
| Scenario loading, signal application, model alerts, release | `orca/sim/scenario.py` `ScenarioRun` (`_apply`, `step_to`, `_model_alerts`, `telemetry`) |
| Models M1-M4 | `orca/models/detector.py` `Detector.load()`, `assess`, `observe`; `orca/models/m2.py`, `m4.py` |
| Agents, routing, tools, mock LLM | `orca/agents.py` (`Agent.run`, `EventFeed`, `Coordinator`, `PolicyMockLLM`, `load_agent_roles`) |
| LLM client | `orca/llm.py` `LLMClient` (env `LLM_BASE_URL`, `LLM_MODEL`) |
| Remediation, autonomy, kill | `orca/remediation.py` |
| Scanner | `orca/scanner.py` |
| World, audit | `orca/world.py`, `orca/audit.py` |
| Batch runner (do not break) | `orca/runner.py`, `run_demo.py` |
| Replay UI + trace adapter | `dashboard/` (keep working; the live UI replaces its front end later) |

If a needed hook is missing in these modules, add the smallest public method; do not fork logic.

## 3. Architecture
```
orca/live/
  __init__.py
  session.py     LiveSession: owns Simulator, NetState/NetOps, World, Remediation, Detector, agents,
                 clock thread, agent worker, impact model, shadow ("without ORCA") sim, event bus
  inject.py      INJECTORS catalogue (section 5) -> Simulator conditions / attack chains
  impact.py      everyday-impact counters from sim records (section 6)
  bus.py         thread-safe event bus: append-only list + condition variable; seq numbers
  server.py      stdlib ThreadingHTTPServer: static files, JSON commands, SSE stream
  __main__.py    python -m orca.live --scenario S1 --llm mock|local --port 8060 [--rules off] [--kb eu]
dashboard/live/static/   (Codex B) index.html, app.js, style.css, vendor/
dashboard/live/fake.py   (Codex B) serves recorded/fake events for UI dev without the engine
```

### Threads
- **Clock thread**: every `tick_seconds / speed` advances the sim one minute (`sim.step()`), applies
  due scripted events (autoplay), runs the detector, raises alerts, updates impact (real + shadow),
  emits events. 1x = 1 sim-minute per 2 s. Speeds 0.5, 1, 2, 5, 10.
- **Agent worker** (one thread, priority queue): LLM calls are effectively serial on a local model.
  Each queued item = (priority, role, task text, alert refs). Priority: commander orders > approvals
  follow-ups > new attack alerts > fault alerts > routine.
- **Back-pressure ("sync")**: default ON. While the agent queue is non-empty or a call is in
  flight, the clock waits (max 90 s real time per minute, then continues and emits `clock_waiting`
  -> `clock_resumed`). UI shows "Agents deciding...". OFF = the city keeps moving (realistic).

### Alert -> agent routing in live mode
No scripted events are required. For each new model alert (or injected signal visible to a role):
build a synthetic event `{t, actor: M1|M3|..., what, signals, refs}` and route it with the existing
`EventFeed.route` rules (`sees.signals` / `sees.sources`). Debounce: one alert per (site, class) per
5 sim-minutes; escalate if the class changes or confidence rises by > 0.2. Commander orders go to the
named role only.

## 4. Event stream and state
`GET /api/stream` = Server-Sent Events, one JSON object per `data:` line, field `seq` increasing.
`?since=<seq>` replays missed events. `GET /api/state` = full snapshot (for reload).
`GET /api/replay?file=<recording.jsonl>` returns replay events plus an `audit` view:
the full original chain's tri-state verification result, original non-control entries
with their hashes, and the number of control entries omitted. A public-row export
is redacted and is not independently verifiable as the full chain.

Every event: `{seq, t (sim minute), ts (sim ISO time), kind, ...}`. Kinds and payload fields:
| kind | fields |
|---|---|
| `session` | scenario, title, story, start, llm, rules, kb, autoplay, sync, speed, emulated: true |
| `tick` | sites: {site: {state, active_path, gateway, demand_mbps, capacity_mbps, delivered_mbps, telemetry}}, services: {service: {demand_mbps, delivered_mbps, pct}}, gateways and paths; instantaneous: true |
| `inject` | id, kind, label, target, start, end, by: "human:commander" (ground truth hidden from agents) |
| `model` | model (M1..M4), site, score/class/confidence, top_features, horizon (M2), text |
| `alert` | id, source, site, label, visible_to [roles], text |
| `agent_task` / `agent_step` / `agent_final` | role, task, tool, args, result (truncated 2 KB), rationale, citations, latency_ms, final text |
| `agent_busy` | role, busy: bool, queue: n |
| `msg` | from, to[], type, data_class, text, refs, accepted: bool, reason |
| `verdict` | verdict, rule, question/topic, records[], gap_id, explanation |
| `clock_obligation` | regime (CERT-In 6 h, DoT 6 h, CTI 6 h, TRAI 24 h ...), started_at, due_at, status open\|met\|missed, trigger (noticing\|awareness\|occurrence) |
| `approval` | hash, playbook, owner, targets, params, reason, expires_at, clone_test, status requested\|approved\|rejected\|expired\|auto, mode |
| `execute` | hash, playbook, targets, stage_pct, result ok\|refused, why |
| `heal` | site, from_path, to_path, check {clean: bool, checks[]} |
| `patch_stage` | playbook, pct 5\|25\|100, health ok\|fail |
| `rollback` | hash, why |
| `reattack` | playbook, attack, blocked: bool |
| `autonomy` | mode MANUAL\|ASSISTED\|AUTO, scope {sites, playbooks}, expires_at, by, downgraded_from, cause |
| `kill` | engaged: bool, by, reason, tokens_revoked |
| `gap` | gap_id, title, status, india (one line + records), global_examples [{jurisdiction, clause, shows, tier}], recommendation |
| `phase` | active: [predict\|heal\|coordinate\|contain\|fix\|report], latest (derived: see 7) |
| `impact` | real {..., delivery}, shadow {..., delivery}, instantaneous network totals (section 6) |
| `summary` | final, timings, services, sites, network, units and impact_cumulative |
| `clock_waiting` / `clock_resumed` | reason |
| `error` | where, message (never secrets) |

The same information must also be written to the audit JSONL through `World.log` (existing kinds
where they exist: `agent_task`, `agent_step`, `msg_sent`, `msg_rejected`, `approval_requested`,
`approved`, `executed`, `rolled_back`, `autonomy_set`, `kill_switch`...), plus a first `run_meta`
entry and `net_state` entries every 5 sim-minutes, and alert details inside `event_released`
(dashboard/README.md lists what the replay adapter reads).

## 5. Commands (POST JSON, all return `{ok, ...}` or `{ok:false, error}`)
| Endpoint | Body | Effect |
|---|---|---|
| `/api/session` | scenario, llm mock\|local, rules bool, kb india\|eu, autoplay bool, sync bool | (re)start a session; previous recording closed |
| `/api/clock` | action play\|pause\|step, speed | |
| `/api/inject` | kind, target, duration_min, params{} | add a condition / chain now (section 5.1) |
| `/api/autonomy` | mode, sites, playbooks, minutes, pin | `Remediation.set_mode` |
| `/api/approve` | hash, pin | `Remediation.approve` then the owner agent is queued to execute |
| `/api/reject` | hash, reason | |
| `/api/kill` | pin, reason | `Remediation.kill` |
| `/api/kill/release` | pin | |
| `/api/order` | to (role), text | queued as a commander task to that role (top priority) |
| `/api/ask` | to (role), question | the role answers in plain text (no tools that change state) |
| `/api/rules` | on bool | toggles the rule engine for subsequent agent turns |
| `/api/kb` | india\|eu | swaps the KB jurisdiction for subsequent turns (scenario 3) |
| `/api/gap` | gap_id, decision confirm\|reject, pin | human decision on a gap candidate (logged) |

`GET /api/catalogue` returns scenarios, sites, gateways, accounts, playbooks, injectors (for the UI).

Global `MANUAL` (both site and playbook scopes empty or wildcard) revokes every autonomy grant
and unused automatic approval token. Scoped `MANUAL` removes matching grants and revokes the
unused automatic tokens they cover; it does not revoke human approvals. Automatic approvals
expire no later than their originating grant.

### 5.1 Injectors (`orca/live/inject.py`)
| id | label (UI) | sim | default target | truth class |
|---|---|---|---|---|
| `mgmt_intrusion` | KA-SAT style management intrusion | `ka_sat_chain` + `mgmt_intrusion` | account `noc-vendor-7`, sites CHN-01,CHN-02 | attack-management-plane |
| `jamming` | Jam the satellite uplink | `jamming` (J/N param) | CHN-02 | attack-jamming |
| `failover_lure` | Lure failover to a foreign gateway | `foreign_failover` (offers GW-XX path) | CHN-02 | attack |
| `gnss_spoof` | GNSS spoofing (timing) | `gnss_spoof` | CHN-03 | attack-gnss |
| `ss7_abuse` | SS7 location tracking | `ss7_abuse` | CHN-04 | attack-signalling |
| `telemetry_edit` | Fake "all green" telemetry | `telemetry_edit` | SAT-MGMT | attack-management-plane |
| `firmware_exploit` | Exploit old terminal firmware | `firmware_exploit` | a terminal | attack |
| `feeder_intercept` | Intercept unencrypted feeder link | `feeder_intercept` | GW-IN-1 | attack |
| `rain` | Monsoon rain cell (fault) | `rain` (mm/h) | CHN-01 | fault-weather |
| `power_cut` | Grid power cut (fault) | `power_cut` | CHN-05 | fault-power/equipment |
| `gateway_power` | Gateway outage (fault) | `gateway_power` | GW-IN-1 | fault-power/equipment |
| `surge` | Festival traffic surge (benign) | `surge` | CHN-01 | normal |
Agents never see `inject` ground truth; only signals and model outputs. The UI shows the truth to
the human in a separate "Ground truth" lane so judges can compare detection with reality.

## 6. Impact model (`orca/live/impact.py`)
Per sim-minute, from site records and the dependants of each site (add a small table in
`orca/sim/topology.py` if missing: which sites carry 112, hospital, payments, grid SCADA):
- `calls_112_failed` (expected calls/min x failure fraction from capacity shortfall and packet loss)
- `hospital_offline_min`, `payments_failed` (txn volume x (1 - txn_success)), `grid_scada_lost_min`
- `people_affected` (site population share x outage), `warned_at` per dependant (minute PB-10 or
  a downstream warning message reached it; null if never), `minutes_to_warn`
- `reports`: list of obligation clocks and whether met.
`impact.real.delivery` contains the simulator allocation for the current minute and cumulative
network, site and service totals, including each site's service breakdown. Rates are Mbps; cumulative
volumes are Mbit, calculated from one-minute samples (Mbps × 60 seconds). Site demand is the sum
of independently rounded service demands and can differ slightly from the raw site demand in `tick`.
The summary retains the older `cumulative_*_mbit_min` fields for compatibility: they are sums of the
one-minute Mbps samples, not Mbit; use the new `cumulative_*_mbit` fields for actual volume.

**Shadow estimate ("without ORCA")**: the current implementation applies a conservative packet-loss
floor to the real telemetry for the impact counters. It is not a second simulator or an independent
capacity allocation. Its `delivery` is explicitly unavailable with `reason: "not_simulated"`; do not
present the real run's delivered Mbps as shadow throughput. All figures are emulated estimates.

## 7. Phase derivation
predict: M2 forecast or M1 early score with no outage yet; heal: a `heal`/PB-06/battery-saving action
in progress; coordinate: messages between >= 2 organisations in the last 5 min; contain: PB-01..05
requested/executing; fix: patch stages (PB-11..15) or re-attack checks; report: obligation clocks open
or gap events. Several may be active; the bar highlights all active, the latest strongest.

## 8. UI (Codex B) - `dashboard/live/static/`
Stack: vendored **Preact + htm** (no build step) and plain SVG; optional vendored **uPlot** for
sparklines. Files under `vendor/` with licence headers. Dark ops theme readable on a projector
(min 14 px body, high contrast), colour-blind-safe status colours plus icons/text (never colour only).

Layout (desktop 1440x900 first; usable at 1280):
- **Top bar**: ORCA-NTN, sim clock (big), play/pause/step/speed, scenario picker, Rules ON/OFF,
  KB India/EU, autonomy mode chip (with expiry countdown), "Emulated network" badge, REC dot,
  **KILL SWITCH** (red, asks PIN + reason).
- **Lifecycle bar**: Predict - Heal - Coordinate - Contain - Fix - Report gaps, lit from `phase`.
- **Left: Attack lab**: injector buttons grouped Attacks / Faults / Benign, target picker, duration,
  "Launch". Below: Ground-truth lane (what the human injected, when).
- **Centre: Live map**: stylised Chennai (SVG): sites with dependant icons (hospital, 112, payments,
  grid), towers, emulated satellite links (dotted, animated flow), gateways GW-IN-1/GW-IN-2/GW-XX
  (foreign, marked), backup paths. Colours from `tick`. Click a dependant -> highlight its chain down to
  the gateway. Healing animation: path check (clean/dirty) then traffic moves. Under the map: model
  strip (M1 anomaly sparkline per site, M3 class + confidence, M2 battery/link forecast).
- **Right: War room**: 6 organisation cards (satellite operator, mobile operator, power utility,
  CERT-In, regulator, gap analyst) + policy adviser: status (idle / thinking with spinner / waiting
  approval), last action, what it can see, blind spot. Message feed with arrows/chips (type, data
  class, rejected messages in red with reason). Box: "Order or ask an agent" (role picker).
- **Bottom row**: Approvals inbox (cards: playbook, owner, targets, reason, clone test, countdown,
  PIN field, Approve/Reject, "Why?" drawer = model evidence + verdicts + KB quotes); Rulebook
  (open obligation clocks with countdowns; verdict list with record ids; gap cards sliding in:
  India vs global example vs recommendation); Impact (big counters, With ORCA vs Without ORCA).
- **Scene intro**: first load (and on session start) a 5-second overlay: "Tuesday 19:00, Chennai.
  [N] people, 112, hospitals, UPI payments and the grid depend on towers backed by one satellite
  operator's ground network (emulated). Launch an attack to begin." Skippable.
- **Replay mode**: `?replay=<run file>` drives the same components from a recorded JSONL (reuse
  `dashboard/adapter.py` via the server), with play/pause/scrub.
- "Why?" everywhere an AI decision appears (alert, verdict, approval): model features, rule id,
  record quotes, who decided (AI vs human) - this is the jury's explainability requirement.

## 9. Phases and acceptance tests (the lead checks these)
**P1 engine (Codex A)** - `tests/test_live.py`, mock LLM, test PIN hash, no network:
1. Start S1 headless; 30 ticks run; `tick` events carry every site.
2. Inject `mgmt_intrusion`; within 10 sim-minutes an M1 or M3 `alert` reaches satellite_operator
   only (routing respects `sees`), and an `approval` for PB-01 or PB-05 is requested.
3. Approve with the right PIN -> `execute ok`; wrong PIN -> refused; expired -> `expired`.
4. AUTO granted for CHN-02/PB-06 -> a jamming injection leads to `heal` with a clean-path check and
   `execute` without a human approval, logged `autonomy:AUTO (granted by ...)`; `failover_lure` path
   through GW-XX is refused.
5. M3 low confidence or a CONFLICT verdict -> `autonomy` downgrade event AUTO->ASSISTED.
6. Kill switch -> every pending token revoked; any later execute refused; release -> MANUAL.
7. Rules OFF -> no `verdict` events; KB eu -> verdicts cite EU records.
8. `rain` injection -> M3 says fault-weather, no containment playbook requested (fault vs attack).
9. Patch flow: PB-11/12 staged 5->25->100 with health checks; `reattack` blocked after the fix.
10. Shadow impact >= real impact for the KA-SAT case; counters non-negative.
11. Recording: the JSONL hash chain verifies (`orca.audit`), and `dashboard.adapter` parses it.
12. Server: `/api/catalogue`, `/api/session`, `/api/inject`, SSE `since=` replay work (test with
    urllib, ephemeral port).
13. Whole existing suite still passes (`python -m pytest -q`; check the exit code, not a pipe).

**P2 UI (Codex B)**, built in parallel against section 4 using `dashboard/live/fake.py` (it replays a
P1 recording or a hand-made event list). Acceptance: every panel renders from fake events; no console
errors; works offline; replay mode works on a `runs/*.jsonl`; `tests/test_live_ui.py` checks static
files are served, vendor files exist, and no external URLs appear in static files.

**P3 integration (both, after the lead's P1+P2 review)**: UI on the real engine with `--llm mock`,
then `--llm local` (LM Studio `google/gemma-4-12b-qat`, back-pressure on); `docs/LIVE_DEMO.md`
rehearsal script (S1 live in 5 minutes: intrusion -> detection -> PB-01 approve -> jamming -> AUTO
heal -> gap card -> kill switch demo -> replay).
