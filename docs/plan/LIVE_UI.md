# ORCA Live UI - build spec (v1, 8 Nov 2026)

Replaces section 8 of `docs/plan/LIVE_CONSOLE.md`. The engine and API (sections 1-7 there) are built
separately; the UI talks to them only through `/api/*` and the SSE stream (section 4 there).

## 1. Four screens, one app
| Route | Screen | Who uses it | Sees ground truth? |
|---|---|---|---|
| `/` | **Landing**: 3D Earth -> satellite -> gateway -> Chennai, two big actions | everyone | no |
| `/control` | **Exercise Control** (red cell): scenario, clock, inject and schedule attacks, 3D network with the truth, shadow city, scoreboard | exercise director (Pi 5 screen) | **yes** |
| `/console` | **ORCA Operator Console** (blue): alerts, models, 3D live network, war room, approvals, autonomy, kill switch, orders, rulebook, gaps, impact | incident commander (projector) | **never** (drop events with `audience: "control"`) |
| `/review?file=` | **After-action review**: truth vs detection on one timeline, time to detect/contain/heal, decisions (AI vs human), gaps, with vs without ORCA, export PNG/JSON for the report | judges, report | yes (it is after the fact) |
Both live screens can be open at once (two windows or two devices) on the same session.

**Demo flow**: Landing -> "Start exercise" opens Control and "Open console" opens Console ->
director launches KA-SAT intrusion -> console reacts (alert, M3 attack, satellite operator requests
PB-01) -> commander approves with PIN -> director launches jamming -> AUTO heals inside its scope ->
gap card slides in -> kill switch demo -> "End exercise" -> Review opens on the recording.

## 2. Stack (decided)
- React 18 + TypeScript + Vite; **Motion** (framer-motion) for UI motion; **@react-three/fiber +
  @react-three/drei** for 3D; **zustand** for state; no UI kit (own components), CSS variables +
  CSS modules. Icons: lucide-react. Fonts vendored: Inter (UI), JetBrains Mono (ids, times) - OFL.
- Source in `dashboard/live/web/`; `npm run build` writes `dashboard/live/dist/`, which **is
  committed** (judges need no Node and no internet). `node_modules/` is gitignored.
- The engine serves `dist/` (SPA fallback). Dev: Vite on :5173 proxying `/api` to :8060.
- **No external URLs at runtime** (no CDN, fonts or textures from the web). A test greps `dist/`.

## 3. Design system (professional, calm, no neon, light default)
Principles: information first; one accent; status always = icon + word + colour (never colour
alone); generous whitespace; hairline borders instead of heavy shadows; numbers in tabular figures.
No glow, no gradients on text, no neon, no glassmorphism except one subtle blur (<= 12 px) on the
3D overlay labels.

Tokens (`web/src/theme/tokens.css`), light default, dark via `[data-theme="dark"]` toggle in the top
bar (remember choice in localStorage, wrapped in try/catch):
| token | light | dark |
|---|---|---|
| `--bg` | #F6F5F2 | #121417 |
| `--surface` | #FFFFFF | #1A1D21 |
| `--surface-2` | #F0EEEA | #22262B |
| `--ink` | #1B1F24 | #E7E9EC |
| `--ink-muted` | #5B6470 | #9AA3AE |
| `--border` | #E3E1DC | #2A2E34 |
| `--accent` (ink blue) | #2F5D8A | #7FA7CF |
| `--ok` | #3F7D58 | #74B08C |
| `--warn` | #A86F12 | #D6A24E |
| `--critical` | #B5473A | #E07F72 |
| `--healing` | #5E57A0 | #A39BDA |
| `--info` | #3F6E9E | #86ADD6 |
| `--unknown` | #8A8F98 | #8A8F98 |
Type scale: 12 / 14 (body) / 16 / 20 / 28 / 40 (clock). Radius 8 (cards), 6 (controls). Spacing 4-pt grid.
3D scene uses the same tokens (read CSS variables into three.js materials; matte, low-roughness
materials, soft ambient + one directional light; no bloom, no emissive glow).

## 4. Motion (Emil Kowalski / motion-design rules - every animation has a job)
Tokens (`web/src/theme/motion.ts` and CSS vars):
- Durations: `dur1 120ms` (press, quick fades), `dur2 180ms` (popovers, toasts, chips), `dur3 240ms`
  (dialogs, drawers, cards), `dur4 300ms` (upper bound for UI), `illustrative 700-1200ms` (landing,
  camera moves only).
- Easing: enter/exit `ease-out-quart cubic-bezier(.165,.84,.44,1)`; on-screen morph/layout
  `ease-in-out-cubic cubic-bezier(.645,.045,.355,1)`; hover colour `150ms ease`; progress/countdowns
  `linear`. Exits faster than enters (~0.75x). Springs only for interruptible things (drawers,
  dragged items, camera) with no bounce for click-triggered UI.
Rules:
- Animate only `transform` and `opacity` (and three.js transforms). Never width/height/top/left.
- Enter from where it comes from: approval cards slide up from the inbox edge (translateY 8 px +
  scale .98 -> 1); toasts from the top-right; the "Why?" drawer from the right; gap cards from the
  rulebook side. Scale from 0.96, never from 0. Transform-origin = trigger.
- Lists (messages, verdicts) use layout animation (Motion `layout`) so new items push others smoothly.
- Countdowns and progress bars `linear`; the sim clock digits tick with a 120 ms vertical roll.
- Agent "thinking": a calm 3-dot pulse (opacity only), not a spinner.
- High-frequency controls (play/pause, speed, PIN keypad) respond in <= 120 ms or not at all.
- `prefers-reduced-motion`: disable camera flights, flowing links and layout animation; keep
  instant state changes.
- Target 60 fps on an Apple-silicon laptop; no layout thrash; `will-change` only while animating.

## 5. 3D (in all three live views)
Shared scene component `NetworkScene` (react-three-fiber), stylised, not photoreal:
- A matte ground tile for Chennai (simple coastline shape, no external map tiles), site pillars
  (towers) at fixed positions from `/api/catalogue`, small dependant markers (hospital, 112,
  payments, grid) as HTML labels (drei `Html`, always facing camera, readable 14 px).
- Satellite above on a thin orbit arc; emulated links as thin tubes with a slow dashed flow
  (texture offset, linear), labelled "(emulated)". Gateways GW-IN-1, GW-IN-2 on the ground at the
  edge; GW-XX (foreign) outside the coastline, visibly marked "foreign".
- State from `tick`: site/link colour from status tokens; a link that drops fades and stops flowing;
  failover = the new path draws on (300 ms) after its clean-path check badge (clean/dirty) appears.
- Attack visuals (Control screen, and on Console only after detection): a muted red pulse travelling
  along the attack chain (VPN -> management system -> terminals); jamming = a soft noise ring over
  the site; rain = a translucent cell; power cut = the site's battery ring draining.
- Camera presets: City, Network, Satellite (buttons + keys 1/2/3), tween 700 ms ease-in-out-cubic;
  orbit controls clamped (no flipping under the ground). Click a dependant -> highlight its chain to
  the gateway and dim the rest.
- Performance: instanced meshes, < 150 draw calls, DPR capped at 2, `frameloop="demand"` when nothing
  animates. Fallback: if WebGL fails or reduced motion is set, render the same data as a flat SVG map.
- Console readability: 3D is the centre panel, but every state shown in 3D is also in a side list
  (sites and status), so nothing is only visible in 3D.

## 6. Screen contents
**Landing**: full-bleed 3D Earth (low-poly, procedural, no texture download), slow auto-rotate, a
single 1.2 s illustrative camera flight on load from orbit to Chennai, then the title "ORCA-NTN",
one sentence ("AI agents that heal satellite-backed networks and coordinate the response - on an
emulated network"), two buttons: Start exercise / Open console, and a small link to Review.

**Control** (red cell), top bar + three columns:
- Left: scenario picker, session settings (LLM mock/local, rules, KB, autoplay, sync), clock and
  speed. Attack catalogue grouped Attacks / Faults / Benign; each card shows the kill-chain steps and
  the truth class; target picker, duration, "Launch now" or "Schedule at T+__".
- Centre: `NetworkScene` with ground truth overlays; below it the schedule timeline (drag to move a
  scheduled inject; delete).
- Right: Scoreboard from `/api/truth` (per injection: detected? time to detect, contain, heal) and
  the shadow city counters (Without ORCA) vs real.

**Console** (blue), top bar (clock, scenario, rules, KB, autonomy chip with expiry, Emulated badge,
REC, theme toggle, KILL), lifecycle bar (Predict, Heal, Coordinate, Contain, Fix, Report gaps), then:
- Left: Alerts and models (alert list; M1 anomaly sparkline per site; M3 class + confidence; M2
  battery/link forecast); each alert has "Why?".
- Centre: `NetworkScene` (no ground truth) + the site status list.
- Right: War room: 6 organisation cards + policy adviser (idle / thinking / waiting approval, last
  action, what it sees, blind spot); message feed (type, data class, rejected in critical colour with
  reason); "Order or ask an agent" box.
- Bottom: Approvals inbox (playbook, owner, targets, reason, clone test result, linear countdown, PIN
  keypad, Approve / Reject, Why?), Autonomy panel (mode, scope sites/playbooks, minutes, PIN; shows
  auto-downgrades), Rulebook (obligation clocks with countdowns; verdicts with record ids; gap cards:
  India vs global example (tier label) vs recommendation), Impact (with ORCA vs without ORCA counters,
  labelled "emulated estimates").
- "Why?" drawer everywhere an AI decision appears: model features, rule id, KB quotes with record
  ids, and who decided (AI agent / human commander / automatic under AUTO grant).
- Scene intro overlay on session start (5 s, skippable).

**Review**: run picker (runs/*.jsonl), swimlane timeline (truth lane, model lane, each agent lane,
human lane) with scrubbing; KPI tiles (time to detect, contain, heal; obligations met; gaps found;
AI vs human decisions); with vs without ORCA chart; replay of the 3D scene at the scrub position;
export PNG (for the report) and JSON.

## 7. Data layer
- `api.ts`: typed fetch wrappers for every endpoint in LIVE_CONSOLE.md section 5 + `/api/schedule`,
  `/api/truth`, `/api/replay`.
- `stream.ts`: EventSource on `/api/stream?since=<seq>` with reconnect and `since` resume; the console
  drops `audience: "control"` events before they reach the store.
- `store.ts` (zustand): reducers per event kind (section 4 of LIVE_CONSOLE.md); unknown kinds kept
  in a raw log, never crash.
- `fake/`: a dev mode (`?fake=1`) that plays a bundled event list so the UI works before the engine is
  ready; replaced by the engine's `docs/plan/LIVE_API_EXAMPLES.md` shapes when they land.

## 8. Acceptance (the lead checks)
1. `npm run build` passes with no type errors; `dist/` committed; size < 6 MB gzipped.
2. Every screen renders from `?fake=1` with no console errors; then against the real engine
   (`python -m orca.live --llm mock`).
3. No external URLs in `dist/` (test); fonts and any textures are local files.
4. Light and dark themes both pass WCAG AA contrast for text; status never colour-only.
5. 60 fps on the Console with the 3D scene idle and during a failover (Chrome performance panel,
   M-series Mac); reduced-motion fallback works; WebGL-off fallback shows the SVG map.
6. Console never displays ground truth (test: feed a `control` event; it must not render).
7. Review loads `runs/*.jsonl` recordings and exports a PNG.
8. `tests/test_live_ui.py`: static files served by the engine, vendor/no-external-URL check.
