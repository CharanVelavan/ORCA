# ORCA Live UI redesign - plan v3 (8 Nov 2026, ~23:30 IST)

Status: **PLAN ONLY. Nothing is built.** Build starts only when Charan says "go".
Supersedes the screen and layout parts of `LIVE_UI.md` (kept as history). Engine API stays as in
`LIVE_CONSOLE.md` sections 4-5, plus the three small engine additions in section 7 of this file.
Deadline: submission 10 Nov 19:30 IST. Video recorded on 9 Nov evening.

## 0. Decisions (agreed with Charan, 8 Nov)

| # | Decision |
|---|---|
| D1 | Look: **dark mission control** by default (graphite, one ink-blue accent, no neon), light theme as a toggle |
| D2 | 3D on every screen, with a **Blender asset pack** (satellite, gateway dish, cell tower, user terminal) |
| D3 | Video uses a new **`/stage`** route that shows the Simulator and the Console together |
| D4 | **3D network sits in the middle.** The **Pipeline Flow sits on the right side at 26%** |
| D5 | The Pipeline Flow appears **when a simulation starts**. At that moment the Simulator panel collapses into a slim rail |
| D6 | The Pipeline is **visible by default** while running; it can be collapsed into a side rail, and `F` shows it full screen |
| D7 | **Full 7-band detailed diagram** (about 45 nodes), not a light version |
| D8 | ML models are visible tiles that turn **green to red** when they flag. Reports **travel** to the human commander node; the approval **travels back** and the agents execute |
| D9 | Full scope kept (no cuts). Fallback if late: record the video from Replay of a saved run |
| D10 | Work split across 3 models: **Opus 5.5 (lead) / Sonnet 5.5 / Haiku** (section 11) to save usage and go faster |

Problems with the current UI that this fixes (Charan, 8 Nov): looks plain, flow is confusing, 3D is weak,
wrong amount of information.

## 1. Who it is for and what they must understand

Jury watching a 5-7 min video or a live demo in Dubai. In one viewing they must see:
**Models detect, agents coordinate, code decides, humans approve**, on an **emulated** NTN in Chennai,
and the policy gaps that the run exposes. Report > code > video, so every screen must also give good
stills for the 5-page report.

Design read: live incident console plus exercise simulator, mission-control calm, Linear/Vercel restraint with
Palantir-style ops density. Dials (taste skill): Landing 7/6/3, Simulator 4/5/6, Console + Pipeline 3/4/8.

## 2. Screens and routes

| Route | Screen | Sees ground truth? |
|---|---|---|
| `/` | Landing: Blender scene, camera flight Earth -> satellite -> gateway -> Chennai, 3 actions: Run exercise, Simulator, Console | no |
| `/stage` | Video view. State A (setup) and State B (running), section 3 | yes, but only in the Simulator rail and band 2 (labelled "Ground truth, director only") |
| `/control` | Simulator alone (Pi 5 screen) | yes |
| `/console` | Operator console alone (projector) | **never** |
| `/review?file=` | After-action review with the Pipeline in Replay mode | yes (after the fact) |

## 3. Layouts (design size 1920x1080, must also work at 1440x900)

### State A - setup (before Start)
```
+ top bar: ORCA-NTN | Chennai | EMULATED | sim clock | theme | --------------------------------+
| SIMULATOR 34%                     | 3D NETWORK 66%                                              |
| 10 scenario cards (S0..CAP)       | Blender scene, all sites green, EMULATED label              |
|  title, kind, sites, 1-line story | slow idle orbit of the satellite                            |
| Attack palette preview (12)       |                                                             |
| Rules ON/OFF  KB India/EU  speed  |                                                             |
| [ Start exercise ]                |                                                             |
+-----------------------------------+-------------------------------------------------------------+
```

### State B - running (after Start)
```
+ top bar: scenario title | sim clock | x1 x4 x10 | autonomy | kill switch | End exercise ---------+
|RAIL| 3D NETWORK (middle, ~48%)                       | PIPELINE FLOW 26% (default open)           |
|64px|                                                 | narration bar: step n/N, title, sentence   |
| 12 | live sites, links by health, attacker shown     | 1 NETWORK                                  |
| at-| (Stage/Control only), camera eases to the site  | 2 THREAT                                   |
| tack| that changes                                    | 3 DETECT (M1-M4)                           |
| but-+-------------------------------------------------+ 4 COORDINATE (6 agents)                    |
| tons| COMMANDER INBOX + WAR-ROOM LOG (~38% of height) | 5 COMMANDER (rules, clocks, approve)       |
| ||  | approval cards, alerts, agent messages          | 6 EXECUTE & HEAL                           |
| >>  |                                                 | 7 POLICY GAPS                              |
+----+-------------------------------------------------+---------------------------------------------+
```
- Start: the Simulator slides left into the 64 px rail (320 ms, ease-in-out-cubic, transform only), then the
  Pipeline slides in from the right and its bands appear top to bottom, 40 ms apart. The 3D canvas resizes once
  at the end of the transition (no per-frame resize).
- Rail: 12 attack icons grouped attack / fault / benign; hover shows the label, click fires it; fired icons keep
  a check and the IST time. `>>` or key `S` opens the full Simulator as a drawer over the 3D view; the run keeps going.
- Pipeline collapse: button or key `P` folds it into a 56 px right rail with 7 band markers (icon + word on hover);
  the 3D view grows. `F` = Pipeline full screen (for video close-ups); Esc returns.
- End exercise: back to State A; Review opens on the recording.

### Console alone (`/console`)
Same as State B without the attack rail (a 64 px status rail instead: autonomy, kill switch, clocks).
Before the first `alert`, the Pipeline is shown with only band 1 active; it is always visible by default (D6).

### Review (`/review?file=`)
Pipeline full width in Replay mode on top; scrubber (play/pause, x1/x4/x10, step); below it: truth vs detection
timeline, time to detect/contain/heal, decisions (AI vs human), gaps, with vs without ORCA, PNG/JSON export.

## 4. Pipeline Flow (the centrepiece)

### 4.1 Bands and nodes (top to bottom, about 45 nodes)

**Band 1 - NETWORK (normal operation, all EMULATED)**
- Space/ground: GEO satellite (Ku-band, emulated), SAT-MGMT (operator management system), GW-IN-1 (Chennai,
  primary), GW-IN-2 (Bengaluru, backup), GW-XX (foreign, never allowed; shown greyed with a lock).
- Sites (verified in `orca/sim/topology.py`, **6 sites**): CHN-01 Park Town (hospital, 112), CHN-02 T. Nagar
  (payments, 112), CHN-03 Adyar (112), CHN-04 Guindy (grid, 112), CHN-05 Ennore (coastal, alerts), CHN-06 OMR
  (traffic signals, 112).
- Each site chip: state icon + word (`OK` / `DEGRADED` / `DOWN` / `HEALING`), active path (A/B) and gateway,
  one mono telemetry line (SNR or loss or battery, whichever is most relevant). Source: `tick`.

**Band 2 - THREAT**
- 12 chips in 3 groups. Attacks: KA-SAT intrusion, jamming, failover lure, GNSS spoof, SS7, fake telemetry,
  firmware, feeder intercept. Faults: rain, power cut, gateway outage. Benign: festival surge.
- Scenario-scripted threats (from the YAML `actor: attacker|environment|judge` events) show here too.
- When active: the chip lights and a red dashed line runs to the band-1 node it hits.
- **Console variant:** chips are hidden. The band reads "Anomaly observed at CHN-03, cause not yet known".
  The cause appears only in band 3 when M3 names it. A test asserts no `inject` label reaches `/console`.

**Band 3 - DETECT (ML models watching the network)**
| Tile | Live content | Green -> red rule |
|---|---|---|
| M1 Isolation Forest | sparkline of anomaly score + threshold line | score above threshold |
| M2 forecaster | "time to failure 38 min" or "battery 20 min" countdown | horizon below the alert limit |
| M3 fault-or-attack (8 classes) | class + confidence, e.g. `attack-jamming 0.95` | attack class = red; fault class = amber; `abstain` = amber `UNSURE -> human` |
| M4 MILP allocator | current order 112 > hospital > grid > payments | re-plan = amber (an action, not an alarm) |
- Thin monitoring lines run from band 1 up to each tile with a slow data tick (live state, so allowed to loop).
- Colour change 300 ms plus icon/word swap (`NORMAL` -> `FLAGGED`). A single ring pulse repeats **only until the
  commander acknowledges** the alert.
- **Needs engine addition E1** (section 7): today the live engine only emits `model` events for M3 non-normal labels.

**Band 4 - COORDINATE (6 agents)**
- Mobile operator, satellite operator, power utility, CERT-In, regulator, policy adviser (gap analyst).
- State per agent: idle / thinking (3-dot opacity pulse) / sending. LLM name from the engine (E2).
- `msg` events become small labelled packets between agent nodes; a rejected message bounces back with a cross
  and its reason. Source: `agent_busy`, `agent_task`, `agent_step`, `agent_final`, `msg`.

**Band 5 - COMMANDER (code decides, human approves)**
- Rule engine node: verdict word + rule + KB record (`VIOLATION`, `CONFLICT`, `AMBIGUITY`, `POTENTIAL_GAP`,
  `COMPLIANT`, `INSUFFICIENT_EVIDENCE`). Source: `verdict`.
- Reporting clocks node: one countdown per open obligation. Source: `clock_obligation`.
- **Human commander node** (largest node): receives the report packet (`PB-01 - revoke noc-vendor-7 - asked by
  satellite operator`), shows `AWAITING APPROVAL - expires 4:59`, autonomy badge (MANUAL/ASSISTED/AUTO) and kill
  switch state. **Click the node -> PIN pad opens in place** (same API as the inbox card). In AUTO the packet passes
  the node marked `AUTO - inside scope`. Source: `approval`, `autonomy`, `kill`.

**Band 6 - EXECUTE & HEAL (agents do the job)**
- After approval, a packet `APPROVED #a3f9` travels back to the owner agent in band 4, then this chain lights:
  clone test -> rollout 5% -> 25% -> 100% (linear fill) -> clean-path check (foreign/unverified path rejected) ->
  failover -> re-attack check `BLOCKED`. Failure branch: `AUTO-ROLLBACK`.
- Then a **green return line** runs back up to band 1 and affected sites go DOWN -> HEALING -> OK.
- Source: `execute`, `patch_stage`, `heal`, `reattack`, `rollback`, then `tick`.

**Band 7 - POLICY GAPS**
- India gap -> global example -> recommendation, one card per `gap_id`; commander confirms/rejects (inbox).
- Source: `verdict` events that carry a `gap_id` (there is no separate `gap` event; see E3) and the
  `gap_human_decision` audit entry.

### 4.2 Node states
| State | Look |
|---|---|
| idle | 30% opacity |
| on this scenario's path | faint outline (viewer sees where the story goes) |
| active | full opacity, ink-blue ring, packet travelling on the incoming edge |
| done | full opacity, check + IST time |
| flagged | critical colour, icon + `FLAGGED` |
| skipped | dashed outline (e.g. the attack branch in a fault scenario) |
Status is always icon + word + colour, never colour alone.

### 4.3 Narration bar (Floorplan "Flows" pattern)
`S1 - The night Chennai's satellite terminals disappear - step 5 of 11` / bold title / one plain sentence /
segmented progress / prev, next, pause. Modes: **Live** (follows SSE), **Replay** (recorded JSONL, scrubber),
**Explain** (paused; arrow keys step along the path, Esc returns to live).

### 4.4 Director queue (so packets never overlap)
Events can arrive in bursts within one second. A small queue turns events into animation steps: each packet holds
the stage for at least 600 ms at x1 (x4: 150 ms, x10: 60 ms, reduced motion: instant). State (colours, numbers)
updates immediately; only the travelling packet waits its turn. Queue depth > 8 -> skip packets, keep state.

### 4.5 Geometry (stack-diagram rules)
Hand-placed coordinate canvas, one SVG overlay for edges. Node box with icon tile + name + mono role line; edges
never cross a node box or label text; edge labels 1-2 words with a background halo; primary flow = accent solid,
monitoring = neutral thin, threat = critical dashed, heal return = ok solid. The 26% column (~500 px) holds a
vertical layout; band 1 and band 2 use chips, the rest use small tiles. Minimum text 12 px.

### 4.6 Credits
Patterns borrowed (no code copied): Floorplan (MIT, github.com/haydenschmitty/floorplan) for the dimmed-map +
narration-bar flow walkthrough; stack-diagram (MIT, github.com/caru-ini/stack-diagram) for node/edge geometry.
Credit both in the README.

## 5. Event -> node mapping (checked against `orca/live/session.py` and `server.py`, 8 Nov)

| Node | Event kind (as the stream sends it) | Verified |
|---|---|---|
| Band 1 sites, gateways, paths | `tick` | yes |
| Band 2 threat | `inject` (`audience:"control"`), `scheduled` | yes, relayed from audit `inject` |
| M3 | `model` (model=`M3`) + `alert` | yes |
| M1, M2, M4 | `model` | **no - engine only emits M3 today (E1)**. Note: `session.py:277` sets `source = "M3"` after skipping `normal`, so the M1 branch never fires |
| Agents | `agent_busy`, `agent_task`, `agent_final` (direct); `agent_step` (relayed from audit) | yes |
| Agent messages | `msg` (from audit `msg_sent` / `msg_rejected`) | yes |
| Rule engine | `verdict` (with `gap_id`) | yes |
| Clocks | `clock_obligation` | yes |
| Commander | `approval` (status requested/approved/rejected), `autonomy`, `kill` | yes, relayed from audit; an `auto` status is not set by the relay - check AUTO path (E3) |
| Execute & heal | `execute`, `patch_stage`, `heal`, `reattack`, `rollback` | yes |
| Gaps | `verdict.gap_id` + audit `gap_human_decision` | yes (no `gap` kind is emitted) |
| Phase strip | `phase` | yes |
| Impact | `impact` (real + shadow) | yes |

## 6. Scenario paths (checked against `scenarios/*.yaml`, 8 Nov)

Every scenario plays **its own scripted events** on Start (no button needed). The 12 attack buttons are extra
free play on top. This answers the earlier open question about N2, N3 and N5: they need no button.

| ID | Kind / M3 expected | Threat (band 2) | Models (band 3) | Commander moment | Heal | Gaps lit (band 7) |
|---|---|---|---|---|---|---|
| S0 | normal / normal | none | all green | none | none | none (6 COMPLIANT) |
| S1 | attack / attack-mgmt | VPN login + wipe commands, CHN-01/02 | M1 red, M3 red | **CONFLICT** PB-05 vs PB-06 -> commander sequences PB-01 first | microwave backup (PB-06) | 09, 01 (AMBIGUITY clocks), 02 |
| S2 | fault / fault-weather | monsoon rain, CHN-05 (+ mains loss) | M1, M2 amber/red, M3 amber (fault), **M4 re-plans** | commander sets temporary priority order | CHN-05 to domestic backup, PB-10 warning | 04, 03 |
| S3 | attack / attack-jamming | RF jamming, CHN-03 | M1, M2, M3 red | path A fails integrity, **GW-XX blocked**, commander approves PB-06 on path B via GW-IN-2 | clean path B | 08, 06 |
| N1 | fault / fault-power | grid failure, CHN-01 Park Town | M1, **M2 battery 20 min**, M3 amber | commander approves PB-10 hospital warning, then PB-06 | microwave backup | 04, 02 |
| N2 | fault / fault-power-equipment | maintenance routing error, CHN-02 | M1 (payments drop), M3 amber | commander approves PB-10 merchant advisory | microwave backup | 02 |
| N3 | audit / **abstain** | judge audit: feeder link unprotected, CHN-05 | M1 green, **M3 amber UNSURE** | commander orders avoidance, approves PB-06 | protected domestic path | 06, 09 |
| N4 | attack / attack-mgmt | fake telemetry, CHN-03 | **M1 red on telemetry mismatch**, M3 red | CONFLICT PB-05 vs PB-06 -> PB-01 first | domestic path B | 09, 08, 02 |
| N5 | attack / attack-mgmt | mgmt intrusion, CHN-04 Guindy (CTI designated) | M1, M3 red | **several reporting clocks**; approves PB-01 + PB-10 (grid) | domestic backup | 01, 09, 02 |
| CAP | mixed / attack-mgmt | rain CHN-05 + intrusion CHN-02 + battery CHN-01 | all four models active; M3 separates attack from rain | approves PB-01, sets priority order, GW-XX blocked | path B via GW-IN-2 | 09, 06, 04, 08, 03, 02, 01 |

Corrections to the earlier chat plan: there are 6 sites (not 5); S1 heals over microwave and features a CONFLICT
verdict; S3 is commander-approved (not AUTO) in the YAML; N1 is CHN-01 (not CHN-05); N3 is an audit where M3
abstains (not the feeder-intercept button). Video scenarios (Charan, 8 Nov: any 2 is fine): **S1** (attack response, PIN approval) and **S3** (safe self-healing). S2 is the swap-in if we want fault vs attack. Other 8 run but get no extra polish.

## 7. Engine additions needed (small, Python, owner Sonnet)

| ID | Change | Why |
|---|---|---|
| E1 | Emit `model` status for **M1, M2, M4** on change (and every 5 sim-min): `{model, site, score/threshold or horizon_min or allocation, state: ok|flagged}`; fix `session.py:277` so M1 can be the source | band 3 green -> red needs all four models live |
| E2 | Add the LLM **model name** to the `session` event (today only `llm: mock|local`) | show the real model, never hard-code |
| E3 | Check the AUTO path emits an `approval` with `status: auto`; if not, add it in `_flush_audit` | commander node shows `AUTO - inside scope` |
Tests: extend `tests/test_live.py` for E1-E3. No other engine changes.

## 8. Visual system

- Tokens (`theme/tokens.css`), dark default, light via `[data-theme="light"]`:

| token | dark | light |
|---|---|---|
| `--bg` | #111316 | #F4F5F7 |
| `--surface` | #1A1D21 | #FFFFFF |
| `--surface-2` | #22262B | #ECEEF1 |
| `--ink` | #E7E9EC | #16181C |
| `--ink-muted` | #9AA3AE | #5B6470 |
| `--border` | #2A2E34 | #DDE0E4 |
| `--accent` (ink blue) | #7FA7CF | #2F5D8A |
| `--ok` | #74B08C | #3F7D58 |
| `--warn` | #D6A24E | #A86F12 |
| `--critical` | #E07F72 | #B5473A |
| `--healing` | #A39BDA | #5E57A0 |
| `--unknown` | #8A8F98 | #8A8F98 |
- Fonts: **Geist** (UI) + **Geist Mono** (ids, times, numbers), OFL, vendored as woff2. Tabular figures.
- Icons: keep `lucide-react` (already a dependency), one stroke width (1.5).
- Radius: 8 cards, 6 controls, full pill only for status chips. Hairline borders; no glow, no gradient text.
- Copy: plain words; no em-dashes in visible UI text; every link and figure labelled EMULATED where relevant.

## 9. Motion (Emil Kowalski rules: every animation has a job)

| Token | Value | Use |
|---|---|---|
| dur1 | 120 ms | press, PIN keys, play/pause |
| dur2 | 180 ms | chips, toasts, narration text cross-fade |
| dur3 | 240 ms | cards, node becomes active, drawers |
| dur4 | 300-320 ms | colour change green->red, Simulator collapse |
| illustrative | 600-1200 ms | packets on edges, Landing camera, camera ease to site |
Easing: enter/exit `cubic-bezier(.165,.84,.44,1)`; on-screen morph `cubic-bezier(.645,.045,.355,1)`; progress and
countdowns linear. Exits about 0.75x of enters. Scale from 0.96-0.98, never 0. Transform and opacity only.
Loops only for live state (data ticks, unacknowledged alarm, thinking dots). `prefers-reduced-motion`: no camera
flights, no packets, no layout animation; instant state changes. 60 fps target on Apple silicon.

## 10. 3D and Blender

- Blender pack -> one `orca-assets.glb` (< 2 MB, meshopt or uncompressed, no Draco decoder; vendored):
  GEO satellite, gateway dish, cell tower, user terminal. Low-poly, matte, colours from tokens at runtime.
  Built with the Blender MCP; source `.blend` committed under `dashboard/live/assets-src/`.
- Procedural in R3F: Chennai coastline tile, 6 site pillars, links (colour by health, flow direction for active
  path), orbit arc, attacker marker (Stage/Control only), heal sweep.
- Camera: Landing flight about 1 s per leg; State B eases to the site that changed (spring, no bounce).
- No bloom, no emissive glow. Lazy-load the 3D bundle.

## 11. Team and delegation (Opus lead, Sonnet, Haiku)

Goal: save usage limits, keep one clear end-to-end design, ship faster. **Opus 5.5 (this session) is the lead**: owns
this spec, architecture, the hardest UI pieces, integration, review and every commit/push. Subagents never commit.

| Model | Load | Gets |
|---|---|---|
| **Haiku** | low | mechanical, well-specified, easy to verify: transcribing tables into data files, vendoring fonts, token CSS, running build/tests/greps, copy audit, screenshots |
| **Sonnet 5.5** | medium | self-contained features with a clear brief: engine E1-E3 + tests, Simulator panel + rail, Commander inbox + PIN, Landing, Review replay, Blender pack |
| **Opus 5.5** | medium-high | Stage state machine + layout, Pipeline Flow core (geometry, event reducer, director queue, packets, commander node, return line, truth guard), 3D integration, final rehearsal |

### Task list
| ID | Task | Owner | Files it owns | Done when |
|---|---|---|---|---|
| H1 | Vendor Geist + Geist Mono (OFL) and write `tokens.css` from section 8 | Haiku | `src/theme/fonts/*`, `src/theme/tokens.css` | build passes, no external URL |
| H2 | `scenarioPaths.ts` from section 6 + the YAML files | Haiku | `src/pipeline/scenarioPaths.ts` | one entry per scenario, ids match YAML |
| H3 | `pipelineNodes.ts`: node ids, labels, band, icon, from section 4.1 | Haiku | `src/pipeline/pipelineNodes.ts` | 45 nodes, typecheck passes |
| H4 | QA sweep after each wave: build, `pytest tests/test_live*.py`, grep `dist/` for external URLs and em-dashes, screenshot list | Haiku | none (read only) | report pasted to lead |
| S1 | Engine E1-E3 + tests | Sonnet | `orca/live/session.py`, `tests/test_live.py` | tests pass, events visible in `?fake=1` fixtures too |
| S2 | Simulator panel (State A) + attack rail (State B) + drawer | Sonnet | `src/sim/*` | fires all 12 injectors via existing `api.ts` |
| S3 | Commander inbox, approval card, PIN pad (reused by commander node), war-room log | Sonnet | `src/inbox/*` | approve/reject round trip on S1 |
| S4 | Blender pack via Blender MCP -> `orca-assets.glb` | Sonnet | `assets-src/*`, `public/models/*` | GLB < 2 MB, loads offline |
| S5 | Landing (camera flight, 3 actions) | Sonnet | `src/Landing.tsx`, `src/landing/*` | 60 fps, reduced-motion fallback |
| S6 | Review: replay scrubber driving the Pipeline + metrics | Sonnet | `src/Review.tsx`, `src/review/*` | plays a `runs/live-*.jsonl` end to end |
| O1 | Stage shell, State A/B machine, collapse rails, keyboard (`S`,`P`,`F`,Esc), top bar | Opus | `src/App.tsx`, `src/stage/*`, `src/components/Shell.tsx` | transitions per section 3 |
| O2 | PipelineFlow core: canvas, edges, event reducer, director queue, narration bar, Console truth variant | Opus | `src/pipeline/*` (except H2/H3 files) | S1 plays correctly in Live and Replay |
| O3 | Packets, commander node with PIN, return heal line, green->red model tiles | Opus | `src/pipeline/*` | S1 and S3 pass rehearsal |
| O4 | 3D scene rewrite with the GLB, camera eases, attacker marker gating | Opus | `src/scenes/*` | Console shows no attacker marker |
| O5 | Integration, review of every Sonnet/Haiku diff, rehearsal S1/S3, rebuild `dist/`, commit + push | Opus | all | video-ready |

### Waves (9 Nov, IST)
| Time | Opus | Sonnet (parallel agents) | Haiku |
|---|---|---|---|
| 08:00-10:00 | O1 | S1 engine, S4 Blender | H1, H2, H3 |
| 10:00-14:00 | O2 | S2 Simulator, S3 Inbox | H4 after S1 |
| 14:00-17:00 | O3, O4 | S5 Landing, S6 Review | H4 |
| 17:00-19:30 | O5 rehearsal + fixes | fixes on request | H4 final + screenshots |
| 19:30-late | record video (Charan), Replay fallback | - | - |

### Rules for delegation (usage savings)
- Each subagent gets a **short brief**: task id, the section numbers of this file to read, files it owns, files it
  must not touch, done-when check. It does not get the chat history.
- File ownership above prevents edit conflicts; shared files (`store.ts`, `types.ts`, `api.ts`) are changed only by Opus.
- Subagents report a summary + changed file list; Opus reviews the diff, not whole files.
- Haiku runs the checks so Opus does not spend tokens on build logs.
- Node: `PATH=/opt/homebrew/opt/node@24/bin:$PATH` (default node is broken). Only Opus commits/pushes; no AI-attribution lines.

## 12. Acceptance checks
- `/console` never renders `inject`/`scheduled` labels or the attacker marker (unit test on the reducer + grep test).
- Every NTN link and the 3D scene show EMULATED. Status = icon + word + colour everywhere.
- `dist/` has no external URLs (existing test) and no em-dashes in UI strings.
- S1 live: band order threat -> M1/M3 red -> agents -> verdict -> packet to commander -> PIN -> packet back -> rollout ->
  re-attack blocked -> return line -> sites OK -> gap cards. Same path in Replay from the recording.
- 1920x1080 and 1440x900 without overlap; Pipeline text >= 12 px; 60 fps with Pipeline + 3D on Apple silicon.
- Reduced motion works. Light and dark both checked.

## 13. Risks and fallbacks
| Risk | Fallback |
|---|---|
| Behind schedule on 9 Nov | Record from Replay of a saved S1 run; polish S1 first, then S3 |
| 45 nodes too dense at 26% | `F` full screen for close-ups; band 1 telemetry only on affected sites |
| Packet bursts | director queue (4.4) |
| Blender pack late | procedural shapes already in the scene; swap GLB in when ready |
| E1 slips | M1/M2/M4 tiles show "monitoring" state from `tick` data until E1 lands |

## 14. Open items for Charan
- Approve this plan, then say "go".
- Video scenarios: S1 + S3 (decided 8 Nov); S2 optional swap.
