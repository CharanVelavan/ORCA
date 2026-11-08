# Flowchart v2: the live centrepiece (plan, 9 Nov 00:37 IST)

The user's brief, 9 Nov 00:37 IST:
- The flowchart is the core of the system. It is what the jury watches to see how our models execute. Don't go easy on it.
- Make it as visual as possible, with different shapes.
- Make it extremely detailed. Every agent moves in real time and is highlighted. No one-line summary per block.
- Show real-time messages on the flowchart. Examples: "M1 detects VPN misconfiguration", "asks the human commander", "agents apply the patch".
- Layout: flowchart about 60% of the screen and the 3D scene about 40%, with a draggable divider.

Start after 02:32 IST, 9 Nov. Finish the small pending checks first. The v2 build replaces the 7-step `FlowChart.tsx` summary view.

## 1. Layout
- `/stage` running layout: `[64px sim rail] | [flowchart ~60%] ⇔ [3D over inbox ~40%]`.
  - A vertical drag handle sits between the two panes (pointer and keyboard ←/→, 8% steps).
  - Clamp the flowchart to 40–75%.
  - Store the ratio in localStorage `orca-split`, wrapped in try/catch.
  - Double-click the handle to reset it to 60%.
- The 3D view and the inbox stack in the right pane (3D 60 / inbox 40). The approval also appears inside the flowchart.
- Full-screen (F) still opens the flowchart alone.

## 2. Diagram: a swimlane graph in SVG with real shapes
The diagram reads left to right, with one lane per band and a scrub bar like a video progress bar along the top.

| Lane | Nodes | Shape |
|---|---|---|
| Network | satellite, management network, GW-IN-1, 6 Chennai sites | satellite glyph, rounded rectangle, gateway tower |
| Threat | each injector fired (VPN misconfiguration, jamming, GNSS, SS7…) | red hexagon or octagon, pulsing |
| AI models | M1 anomaly, M2 forecast, M3 fault-or-attack, M4 allocator | rounded card with a live sparkline or score bar and an 8-class bar for M3 |
| Agents | the 6 core agents plus the extras, each its own node | circle avatar with a role icon and colour; glowing ring while busy |
| Rule engine | P node | diamond (decision) showing the verdict word + KB id |
| Clocks | CERT-In 6 h, NIS2 24 h/72 h… | clock dial counting down |
| Commander | human with the PIN | shield / pill; the PinPad opens inline when an approval is pending |
| Fix & heal | clone → 5% → 25% → 100% → re-attack → rollback/return | chevron arrows in sequence that fill as each stage runs |
| Policy gaps | GAP-IN-01..09 | document / flag shape that drops in as found |

- Edges are curved SVG paths (cubic béziers).
  - An idle edge is thin and muted.
  - An active edge is thicker, in the accent colour, and animated with `stroke-dashoffset`.
- Packets are small dots carrying a label chip that travel along the edges of each `msg`, `alert` and `task` event.
  - They move between agents too, for example satellite operator ⇄ CERT.
  - They are driven by the existing director queue (one at a time, hold by speed).
- Highlighting:
  - The active node gets a glow and a slight scale.
  - Nodes the flow has passed through stay solid.
  - Nodes not reached yet are dimmed to 40%.
- Use the existing `pipeline/model.ts` NodeDef ids and `usePipeline` nodes, phases and tones. Do not add a new store.

## 3. Real-time messages on the chart
- Every event becomes a short sentence in plain English. It shows as a speech bubble next to the node that acted, and fades after about 2 holds.
  - "M1 flags anomaly at CHN-03 (score 0.91)"
  - "M3: attack, not fault (VPN misconfiguration)"
  - "Rule engine: VIOLATION · CERT-In Dir. (ii) 6 h"
  - "Satellite operator → CERT-In: incident report"
  - "Asking the commander to approve plan #a1b2"
  - "Patch tested in a clone → rolling out 5%"
  - "Re-attack blocked ✓"
  - "Gap found: GAP-IN-04"
- A running ticker strip under the chart holds the last 4 messages, each with an IST time and the actor's icon, so nothing is missed.
- Write the sentences in a single `pipeline/sentences.ts`, as `(event) => {actor, target?, text}`. Lead (Opus) owns this file.

## 4. Visual quality
- Minimum text sizes: 14 px for node titles and 15 px for bubbles. The title word must not be truncated, and labels must not overlap; reserve lane heights so they can't.
- Colour tokens come from the theme, and both themes must work.
  - Threat is red, models are blue, agents use per-role hues at low saturation, rules are amber, human is the accent, heal is green, gaps are violet.
- Motion:
  - Node highlight: 180 ms ease-out.
  - Packets travel for the hold time.
  - Edge dash animation runs only while the edge is active.
  - Respect `prefers-reduced-motion` by jumping straight to the end state.
- An explain/replay scrub bar sits on top. Dragging it replays the beats (reuse `explainIdx`).

## 5. Work split
- Opus (lead):
  - `sentences.ts`
  - the graph layout (fixed lane coordinates, computed with no runtime layout lib)
  - packet routing
  - the review pass
- Sonnet 5.5:
  - the SVG shape components (Hexagon, Diamond, Chevron, Avatar, Dial, DocFlag, ModelCard)
  - the split pane with the drag handle
  - the ticker
- Haiku: CSS tokens and colour per role, plus screenshot runs.

## 6. Verify
- Run the S1 and S3 fixtures at 1920×1080 and 1440×900 in both themes and take screenshots.
  - Check there is no overlap, the packets visibly travel between agents, and the bubbles are readable.
- Then rehearse live against the engine on :8061 with PIN 2468, run pytest, and commit the UI files only.

## 7. 3D scene in sync with the flowchart (added 9 Nov, 00:45 IST)

User brief: make the 3D scene more active and illustrative, in step with the flowchart, in the style of animated 3D explainer diagrams made in Blender.

**One shared beat drives both views.** The 3D scene reads the same `usePipeline` current packet and beat that the flowchart reads. When the flowchart highlights a step, the 3D scene shows the same moment.

What each beat looks like in 3D:

| Beat | 3D action |
|---|---|
| Threat | A red attacker node rises in, and a glowing red beam crawls from the attacker along the VPN to the management network. The target site pulses red, with a shockwave ring on the ground. |
| M1–M4 detect | A scan sweep (a translucent cone or ring) passes over the affected site. A floating holo-card shows the score (for example "M1 0.91"). M3 shows "ATTACK" vs "FAULT". |
| Agents coordinate | Floating agent badges (the same icons and colours as the flowchart) orbit above the gateway. Message dots arc between them, and the arcs match the flowchart packets. |
| Rule engine / clocks | An amber diamond hologram over the management network flashes the verdict, and a clock ring around it counts down. |
| Commander | The camera pulls back to a wide view, and a shield icon hovers waiting. On approval it pulses green. |
| Fix and heal | A blue wireframe clone of the site appears beside it and turns green. The rollout fills the links in 5% → 25% → 100% stages. A green energy pulse travels backup path B. A re-attack beam hits a shield bubble and shatters. |
| Gaps | Violet flag pins drop onto the map at the place where each gap applies. |

Camera:
- Each step has a scripted shot: threat, then a close-up of the site, then the agent cluster, then a wide shot for the commander, then a follow along the heal path.
- The camera eases with `damp3` (moving about 1.2 s per shot).
- If the user drags the view, auto-follow pauses for 8 s.

Style:
- Clean, stylised "explainer" look: soft studio light, light bloom (drei `Bloom` via postprocessing only if it's under 60 KB gzipped; otherwise use emissive materials alone).
- Animated dashed lines (shader `uv` offset).
- Extra assets: holo-card, shield bubble and flag pin. These are built in Blender via `assets-src/build_assets.py` and exported into `orca-assets.glb`; simple primitives are fine where there's no model.
- This is an original style; don't copy any game's assets or look.

Performance:
- Hold 60 fps on the laptop. At most about 40 animated objects, instanced dots, and no shadows from the effects.
- Respect `prefers-reduced-motion`: show static highlights with no beams.

Split of work:
- Opus: the beat → 3D action map (`scenes/beats3d.ts`) and the camera script.
- Sonnet 5.5: the effect components (Beam, Shockwave, ScanSweep, HoloCard, OrbitBadges, ShieldBubble, FlagPin).
- Haiku: the Blender asset additions and the screenshot runs.

Verify: on S1 and S3, a side-by-side screenshot at each step shows the flowchart highlight and the 3D action on the same beat.
