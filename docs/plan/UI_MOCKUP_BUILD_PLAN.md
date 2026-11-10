# UI mockup build plan (9 Nov 2026)

This plan **supersedes** `UI_REDESIGN_PLAN.md` and `FLOWCHART_V2_PLAN.md` wherever they disagree.
Give this file plus `docs/plan/mockups/` to the build agents.

- Deadline: **10 Nov 19:30 IST**. Report > code > video.
- Goal: every screen looks like its mockup and runs on **real engine data**. No hard-coded demo numbers.
- Logos don't matter. Use one logo everywhere; any of the mockups' logos is fine.

## 0. Read first

| File | Why |
|---|---|
| `docs/plan/mockups/01-home.png` … `06-policy-recovery.png` | The target look (light theme, cards, 3D centre, flow panel on the right) |
| `docs/plan/LIVE_CONSOLE.md` §4–5 | Event kinds, API commands. The UI reads only these |
| `docs/plan/LIVE_API_EXAMPLES.md` | Real payloads |
| `docs/plan/UI_REDESIGN_HANDOFF.md` | Hard rules, build command, demo flow |
| `dashboard/live/web/src/` | Existing React app. **Keep** `api.ts`, `stream.ts`, `store.ts`, `types.ts`, `scenes/NetworkScene.tsx`, `pipeline/*`, `inbox/*` logic; restyle and recompose |
| `dashboard/topology.py`, `scenarios/*.yaml`, `playbooks/catalogue.yaml`, `kb/gaps/india.yaml`, `kb/india/records.yaml` | The only allowed source of names, ids and citations |

Build: `cd dashboard/live/web && PATH=/opt/homebrew/opt/node@24/bin:$PATH npm run build` (output `dashboard/live/dist/`, committed).
Run: `python -m orca.live --scenario S1 --llm mock --port 8060`. Dev mode without the engine: `?fake=1`.

## 1. Navigation (decided)

Use the **top bar from 01-home.png**, on every page. **No left sidebar.** That leaves the full width for the three-column layouts.

```
[logo] ORCA-NTN | Home  Simulator  Operations  Investigation  Policy & Gaps  Recovery  Audit & Replay | [Scenario ▾] [● Emulated] [Chennai] [19:04 IST sim] [🔔] [Autonomy ▾] [CV]
```

- The labels are exactly those 7, in that order. The Home cards use the same 7 names and link to the same routes.
- Routes: `/`, `/simulator`, `/operations`, `/investigation`, `/policy`, `/recovery`, `/audit`.
- Right-hand context strip, global (one component):
  - scenario picker → `POST /api/session`;
  - "Emulated" badge, always shown;
  - **sim** clock in IST, from the `tick` `ts`, never the wall clock;
  - bell = count of open approvals plus new gaps;
  - autonomy pill: MANUAL / ASSISTED / AUTO → `POST /api/autonomy` with PIN.
- **One bottom stepper on every page except Home.** It shows the engine's `phase` event:
  **Predict → Heal → Coordinate → Contain → Fix → Report gaps**.
  - Each step is done ✓, current, or pending, with the time it was reached.
  - Clicking a step on Audit & Replay seeks there.
  - Don't invent other step names (the mockups use four different sets; ignore them).
- **One right-hand flow panel** (`pipeline/FlowGraph.tsx`), shown on Operations, Investigation, Policy & Gaps and Recovery.
  - It is resizable 60/40 with a drag handle, as in 03 and 05.
  - Each page shows its own flow (§3). Live per-agent highlight: the node lights up while its agent or model is working (`agent_busy`, `model`).
  - Clicking a node opens "Flow details", as in 05 (bottom right), with the evidence, the model explanation and the related records.

### Status vocabulary, used everywhere
- Site states: `ok / degraded / down / healing`. Colour plus icon plus word, never colour alone.
- "Compromised" applies **only** to `SAT-MGMT` or a gateway. **Never to the satellite.** The KA-SAT story is a ground management-network intrusion.

## 2. Single source of truth for numbers

Make one selector module, `src/derive.ts`. Every card reads it, so no screen has its own numbers.

| UI field | Source |
|---|---|
| Sites affected `n / 6` | `tick.sites[*].state != ok` |
| Capacity / delivered Mbps per service | **new** `tick.services` (work item A) |
| Network health %, availability % | `impact.real` (recompute from the ticks if missing). It must drop during the incident |
| Detection time, time to notify, time to restore | **new** `summary.timings` (work item D) and `clock_obligation` |
| Model cards | `model` events. **M1** shows its score. **M3** shows its class and confidence, or "abstain". **M2** shows minutes to failure plus a sparkline (no "confidence"). **M4** shows its allocation table and "optimal / feasible" (no "confidence") |
| Agents | the 6 roles in `agents/roles/` (mobile operator, satellite operator, power utility, CERT-In, regulator, policy adviser), plus the gap analyst and the human commander. **Models are not agents**: show them in a separate "AI models" card |
| Policy sources count | number of records in the KB manifest, not "1,248" |
| Citations | `verdict.records[]`, `gap.india.records`, `gap.global_examples`. Display the record id and its short title from the KB. **Never free text** |

Sites (from `dashboard/topology.py`, these match the mockups):
- CHN-01 Park Town (hospital corridor)
- CHN-02 T. Nagar (UPI, ATMs)
- CHN-03 Adyar (homes, 112)
- CHN-04 Guindy (grid communications)
- CHN-05 Ennore (coastal)
- CHN-06 OMR (offices, signals)

Gateways: GW-IN-1 (primary), GW-IN-2 (backup), GW-XX (foreign, forbidden). Management network: SAT-MGMT.

## 3. Screens

### 3.1 Home — `01-home.png`
Copy the layout as drawn: hero on the left, 3D Chennai scene (`landing/Scene3D.tsx`) on the right, "Emulated Network" card, KPI strip, 7 cards.

- **KPI strip:**
  - scenario picker;
  - network health (live, from §2);
  - service availability;
  - active incidents (open alerts);
  - agents online (n/6);
  - KB records;
  - region "Chennai, IN (emulated)".
- **"Run Exercise"** → `POST /api/session` then go to `/operations`. **"Explore Simulator"** → `/simulator`.
- Use a text badge "ITU AI for Good Sandbox", not ITU's logo.

### 3.2 Simulator — `02-simulator.png`
The director's view (the old `Control.tsx`).

- **Left:** scenario list from `GET /api/catalogue`: S0, S1, S2, S3, N1–N5, CAP, each with its title and kind badge (attack / fault / audit / mixed / normal). "New scenario" can be a disabled stub.
- **Centre:**
  - 3D network (`NetworkScene`): satellite, GW-IN-1, GW-IN-2, SAT-MGMT, 6 towers; satellite links and terrestrial links in different line styles; "3D Network / Topology" toggle.
  - Inject toolbar from the `inject` list in LIVE_CONSOLE §5.1: KA-SAT intrusion, jamming, failover lure, GNSS spoof, SS7 abuse, fake telemetry, firmware exploit.
- **Right:**
  - scenario details (title, kind, region, affected sites, objective) from the scenario YAML;
  - "AI Models (live)" M1–M4 with their status.
- **Bottom:**
  - play/pause, sim time, scrubber, speed 0.5/1/2/5/10 → `/api/clock`;
  - "Live" pill;
  - toggles: rules on/off → `/api/rules`, KB India/EU → `/api/kb`, LLM mock/local, sync.
- **Ground truth (`audience:"control"`) may render here, and only here.**

### 3.3 Operations — base `04-operations-b.png`, plus parts of `03-operations-a.png`
The commander's main screen and the main video screen.

- **Header row (from 04):** threat card, affected sites n/6, impact (capacity drop), recovery ETA, network status.
- **Left column:**
  - **Approval request** (from 04): playbook id + title from the catalogue, owner role, targets, reason, chips (Security / rule verdict / service risk), clone-test result, expiry countdown. Buttons: **Approve (PIN) / Modify / Reject / Request analysis** (from 03). Approve → `/api/approve`, Reject → `/api/reject`, Request analysis → `/api/ask`.
    The recommendation is "Requested by satellite operator agent". **The commander approves; they never recommend.**
  - **Agent activity:** the 6 roles only. Each row shows status (running / idle / waiting), current tool and a one-line rationale. Clicking a row opens the agent's full trace (`agent_step`), messages (`msg`) and citations. That covers the jury's per-agent detail and AI-vs-human rule.
- **Centre:** 3D network with the legend (Operational / Degraded / Down / Recovering) and site labels "T. Nagar (Degraded)". Below it:
  - **Remediation progress:** steps from `approval`, `execute`, `patch_stage`, `heal`, `reattack`, with real times.
  - **Policy evidence:** latest `verdict` events as `VERDICT · rule id · record id` with the gap link. "View evidence" goes to `/policy`.
    **Never show "Regulatory gap: None".** If there's no gap, say "No gap raised yet".
- **Right:** "AI models" card from 03 (M1–M4, values as in §2) and "Evidence (top)" from 03, both above the flow panel.
- **Flow panel:** Start → Detect (M1) → Classify (M3 diamond: attack / fault / abstain) → Coordinate agents → Rule engine verdict → Commander decision (Approve / Reject or modify branches, from 03) → Heal over a clean path (clean-path check node) → Validate → Report gaps.
- **Extra panels:**
  - **Kill switch** (`inbox/KillPanel.tsx`) in the header, with a PIN.
  - **Config diff panel** (work item C) opens when a playbook executes.

### 3.4 Investigation — `05-investigation.png`
Copy it as drawn. This is the fault-vs-attack screen.

- **Header:** incident, M3 class with confidence, severity, status. A step picker that seeks within the phase.
- **Affected assets:** SAT-MGMT "Compromised", GW-IN-1 "Suspicious", CHN-xx "Unusual traffic". **Not the satellite.** In the 3D scene, red marks go on the management network and gateway, not on the satellite links.
- **Telemetry for the selected site:** line chart of `snr_db`, `packet_loss`, `traffic_load`, **delivered Mbps** (from A), with a marker at the attack time. For S1, traffic **drops**; it doesn't rise.
- **Anomaly and model predictions:** M1 score gauge plus the model table per §2. M3 `top_features` show as "why".
- **Attack vs network fault, evidence:** two columns.
  - Attack: management login from an unknown account, command burst, no preceding RF or weather drop.
  - Fault: rain fade, power, hardware, link margin.
  Each line is ticked or empty from real signals in `model.top_features` and `tick`.
- **Root-cause hypotheses:** M3 class probabilities (top 3), as bars.
- **Evidence timeline:** `alert`, `model`, `inject` (Simulator only), `approval`, `execute`, at sim times.
- **Network impact:** affected sites, delivered-Mbps change, QoS state.
- **Flow panel:** Incident detected → Collect evidence → diamond "Attack or network fault?". The attack branch goes to Root cause → Impact → Recommend response. The fault branch goes to Validate fault → Restore capacity. The unused branch is greyed out, as in 05.

### 3.5 Policy & Gaps — top half of `06-policy-recovery.png`
**The headline screen.** Protect it first in any scope cut.

- **Left tabs:**
  - Indian regulations (n);
  - Global references (n);
  - Country comparison;
  - Policy gaps (n);
  - Recommendation.
- **Regulations table:** columns are instrument | applicability | binding status | citation (record id) | relevance. **Rows only from `kb/india/records.yaml`**, for example:
  - IN-CERTIN-DIR-2022-ii (6 h to CERT-In);
  - IN-TCSR-2024-R7-1 (6 h to DoT);
  - IN-CTIR-2024-R7-1-j;
  - IN-TELACT-2023-20;
  - IN-DPDP-RULES-2025-R7, with the badge "not in force until May 2027";
  - IN-SPACEFW-2026-3-2-1, with the badge "advisory".
- **Reporting clocks card:** live `clock_obligation` countdowns (regime, trigger noticing / awareness / occurrence, due time, met / missed).
- **Country comparison:** India vs a global example per gap, from `gap.global_examples` (jurisdiction, clause, tier).
  - **Don't hard-code Yes/No.**
  - EU NIS2 space covers ground infrastructure only. The EU Space Act is a draft. Label each one by its tier.
- **Candidate policy gaps:** cards for GAP-IN-01 … GAP-IN-09 as they fire (`gap` events). Each card shows title, status, India records, global example and recommendation. Confirm / Reject with PIN → `/api/gap`.
- **Rule engine verdicts:** list with the six verdict chips (`COMPLIANT`, `VIOLATION`, `AMBIGUITY`, `CONFLICT`, `POTENTIAL_GAP`, `INSUFFICIENT_EVIDENCE`), each with its rule id and record ids. **No "Verified 0.92" badge on LLM text.** LLM recommendation text is labelled "Draft by policy adviser agent".
- **KB swap:** an India ⇄ EU toggle (`/api/kb`) on this page too, for demo path 3.
- **Flow panel (from 06):** S1 → Detect → Analyse & retrieve → diamond "Policy adequate?". The No branch goes to Gap & recommendation → Approval → Recover & validate; the Yes branch goes to Execute recovery.

### 3.6 Recovery — bottom half of `06-policy-recovery.png`, plus work items B, C, D

- **Availability chart:** before / during / after bands from `impact.real`. The dip **starts at the attack time**.
- **KPI tiles (from D):**
  - outage duration;
  - availability after;
  - time to detect;
  - time to notify vs the 6 h clock;
  - time to restore;
  - approval latency;
  - failed remediation attempts;
  - rollback success.
- **Delivered Mbps per service (B):** stacked or multi-line chart for 112, hospital, UPI/ATM, grid and general, with markers for attack, fix and rollback. Footer line, for example "112 kept at 100% of demand; UPI shed to X%" (computed, not typed).
- **Config diff and rollout (C):**
  - before/after diff of the changed config (red/green lines);
  - rollout stepper 5% → 25% → 100% with health per stage (`patch_stage`);
  - auto-rollback events (`rollback`);
  - re-attack check result (`reattack`).
- **Validation checks:** link stability, service health, no anomaly (M1–M4), resilience target, clean path verified. Each is pass/fail from real events.
- **Flow panel:** Heal → Clean-path check → Stage 5/25/100 → Re-attack check → Validate → Close.

### 3.7 Audit & Replay — no mockup
Same visual language. Reuse `Review.tsx` and `review/*`.

- Pick a recording (run) from `runs/`.
- The timeline scrubber seeks every page's state.
- Hash-chained audit table: seq, time, actor (agent / model / human / rule), kind, summary, hash ✓.
- Filter by actor type, and an "AI vs human" split.
- Export JSONL.

## 4. Demo paths (the video, and docs/DEMO.md)

Three paths, on scenarios that already exist:

1. **S1, KA-SAT-style wipe.**
   - Detect, then isolate with commander approval.
   - Config diff on screen, re-attack check passes, rollback demonstrated.
   - Main thing to add: the diff in the dashboard (C).
2. **S2, storm and the fight for capacity.**
   - Failover only after the clean-path check.
   - Then the M4 MILP keeps 112 and the hospital fully served while lower-priority traffic is shed.
   - Main thing to add: the throughput chart per service (B).
3. **N5, several reporting clocks, plus the knowledge-base swap.**
   - The same incident under India and EU rules shows different deadlines and different gaps.
   - That is the policy-gap headline.

## 5. Backend work (from the 9 Nov proposal, ~5.5 h)

| # | Change | Time |
|---|---|---|
| A | Compute `delivered_mbps` for each site and each service (112, hospital, UPI/ATM, grid, general) in the simulator and `impact.py`. Emit it in `tick.services` and add it to the scenario summaries | ~1 h |
| B | Dashboard panel: delivered Mbps per service over time, with markers for the attack and the fix (Recovery page plus the Investigation telemetry) | ~1.5 h |
| C | Dashboard panel: config diff and rollout stage (5→25→100%) when a playbook runs. Add `diff {target, before, after}` to the `execute` event | ~1.5 h |
| D | Incident timings (time to detect, time to notify against the 6 h clock, time to restore) in the summaries, plus a `summary` event at the end of the run | ~1 h |
| E | `docs/DEMO.md`: a three-path script with exact commands. It is also the video script | ~0.5 h |

Order: after the Hugging Face and Qwen uploads, before the report v4, so the report can cite the new numbers (for example, "112 kept at 100% of demand while UPI was shed to X%").

## 6. Agent split and order

| Agent | Scope | Depends on |
|---|---|---|
| **1 Backend** | A, C (diff field), D; update `fake/` events with the new fields; tests in `tests/test_live.py` | — |
| **2 Shell** | Top nav, context strip, bottom stepper, `derive.ts`, routes, Home, Simulator | — |
| **3 Ops** | Operations and Investigation pages, flow panel variants, agent detail drawer | 2 (shell) |
| **4 Policy/Recovery** | Policy & Gaps, Recovery (B and C panels), Audit & Replay | 1 (fields), 2 |
| **Lead** | E (DEMO.md), integration, build, the `dist/` commit, screenshot pass | all |

- Agents 1 and 2 start in parallel.
- Agents 3 and 4 start once the shell merges. Until agent 1 lands, they use `?fake=1` with the new fields.
- Only the lead commits.

## 7. Hard rules (from the handoff)

- Every NTN link and the network badge say **"Emulated"**. Never claim real satellite connectivity.
- The Console pages never show ground truth (`audience:"control"`). Only the Simulator does.
- Status = icon + word + colour.
- Times in IST, from the sim clock.
- No runtime external URLs (fonts and textures vendored; judges run offline).
- Citations only from the KB (record ids).
- Motion has a job, ease-out, <300 ms for UI. No neon. Light theme.
- No AI-attribution lines in commits or files.

## 8. Acceptance (the lead checks before submitting)

1. All 7 nav items work, and each page matches its mockup's layout.
2. Run S1, S2, N5 end to end with `--llm mock`. Every number on every page comes from events. The S1 numbers agree across Home, Operations, Investigation and Recovery.
3. The S1 traffic dip lines up with the attack time. The satellite is never marked compromised.
4. Policy & Gaps shows ≥1 gap card with record ids. The India⇄EU swap changes the clocks and gaps on N5.
5. Recovery shows the per-service Mbps chart, the config diff, 5/25/100 rollout, rollback and re-attack check.
6. `npm run build` passes; `pytest tests/test_live.py tests/test_live_ui.py` passes; `dist/` is updated.
7. Two clean screenshots for the report: Operations (S1, approval pending) and Policy & Gaps (N5, gaps shown).
