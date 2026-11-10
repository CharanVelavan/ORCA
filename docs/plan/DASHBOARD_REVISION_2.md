# Cyber-vigilance dashboard revision

Authorized by Charan on 10 November 2026. Work is local until a commit or push is requested.

## Acceptance checklist

- [x] One primary navigation. Remove the duplicate numbered navigation strip.
- [x] Compact session controls. Remove the scenario picker from the global context strip; scenario selection belongs in the simulator.
- [x] Dialogs, dropdowns and tour controls have visible labels, bounded placement and keyboard dismissal.
- [x] Responsive tiles use available space. Desktop Simulator and Operator fit the viewport; small displays retain readable controls.
- [x] A shared-session split workspace shows simulator controls alongside public Operator evidence. Director truth stays visibly separate.
- [x] Operator shows the complete execution flow without chart scrolling. Evidence details and the expanded diagram remain available separately.
- [x] Learn leads with cyber vigilance and secure self-healing for emulated NTN. Scroll points explain ORCA and each component.
- [x] Learn includes the report-aligned architecture and a focused, explorable source-to-evidence graph. KB construction and current hybrid RAG method are explicit.
- [x] HyperFrames film reuses Blender assets for satellite-to-ground-to-services connectivity, ground-management compromise and guarded recovery. Google Cloud TTS narration, captions and a transcript accompany it. A reusable short visual demo appears on Learn.
- [x] Build, relevant regression tests and browser checks cover desktop, small displays, dialogs, tour, split view and media. No claim of real Qwen inference without a running endpoint.

## Film outline

Target 75–90 seconds. The sequence is NTN connectivity; ground-management compromise; model assessment; knowledge and coordination; guarded recovery; recovered services and evidence. All links are emulated. The satellite is never labelled compromised. Agents explain and propose; deterministic rules produce verdicts; humans authorize guarded execution. The architecture uses the same component names in the film and Learn page.

## Delivery ownership

Three agents: workspace layout and interaction; Learn narrative, architecture and knowledge graph; Blender and narrated HyperFrames media. The primary agent integrates, checks regressions and verifies the browser. Source documents and report binaries are read-only.

## Findings from the first verification pass

The official Chrome DevTools MCP confirmed two navigation rows on the prior build. The model settings primary action inherited white text and a transparent background from an overbroad top-navigation button selector. The fixes must be checked through computed styles and screenshots, not only through the presence of button text in the DOM.

The initial 36 focused frontend regressions pass. They cover evidence-derived task state, replay boundaries and reporting-clock identity; this does not establish that the revised layout has passed visual verification.

Google Cloud TTS succeeded using an existing authorized project after the initial project rejected quota use. Direct Blender MCP access was rejected by automatic approval review (`approval policy is never`); local Blender CLI also fails at startup. The media implementation therefore reuses the exported Blender GLB through a browser renderer, preserving the original scene.


## Final verification

- TypeScript project check and production Vite build pass. The existing optional 3D chunk still produces a size advisory; it remains lazy loaded.
- 37 focused frontend tests pass, including a new check that forecast and allocation need their own public model evidence.
- Browser pass: 49 route/viewport combinations across seven routes and widths 1920, 1440, 1366, 1024, 768, 390 and 320 pixels. No horizontal document overflow or JavaScript page errors. All 14 tour steps complete with zero POST requests.
- Follow-up layout checks cover Simulator, Operator and Shared view at 1920/1440/1366/1280/1024 by 768. At 1366 and 1024, shared attack controls are visible and Operator map/evidence occupy reserved space. The final 320-pixel architecture detail was inspected after correcting inherited button height.
- Official Chrome DevTools MCP confirms a 1366 × 768 Operator document, six site cards fully inside the map, visible evidence, no duplicate journey, no global scenario selector and no console errors/warnings. The response overview has equal client and scroll heights (125 pixels), so its flow does not scroll.
- The shared-session browser test creates S1 in mock mode, pauses it, injects two minutes of emulated CHN-02 jamming and steps twice. The director guide records the condition; public M2 evidence appears in the Operator flow drawer. It does not establish completed incident recovery or live Qwen inference.
- Recorded playback continues after Audit → Shared view navigation (cursor 5/256 → 9/256). Run, clock and injection controls remain disabled; the replay check sends no POST requests.
- Learn architecture selection, eight-node graph/list view and six-paragraph transcript work. Both videos play: 89-second narrated film and six-second silent demo, 1280 × 720. The film loads 21 English caption cues. ffprobe confirms H.264 at 24 fps plus AAC audio for the film; a full ffmpeg decode reports no errors. Caption sentence boundaries are estimated.

Scratch browser evidence is under ignored `.shots/revision2/`; reproducible film sources are under `dashboard/live/web/src/home/motion/`. The final preview runs on `http://localhost:8064`. All changes remain local; no commit, push or report edit was performed.
