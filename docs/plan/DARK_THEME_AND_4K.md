# Brand, theme and narrated 4K film

Requested by Charan after selecting American English Enceladus from the Google Cloud auditions. All work is local; no report documents are edited.

## Delivery checklist

- [x] Use the selected Google Cloud voice: `en-US-Chirp3-HD-Enceladus`.
- [x] Prepare original sound effects for links, intrusion, coordination, rollout and recovery.
- [x] Mix effects below narration and check peaks and timing.
- [x] Render native 3840 × 2160 graphics and 3D network footage.
- [x] Export the 4K master, practical web copy, poster and matching captions.
- [x] Create the original dorsal-fin/orbital ORCA mark, wordmark asset and favicon.
- [x] Compress the Operator heading into a single row with the safety control.
- [x] Add a persistent accessible theme toggle with prepaint application.
- [x] Apply dark presentation to Learn, workspaces, diagrams and dialogs.
- [x] Verify final build, theme persistence, responsive layout and media playback.

## Theme behavior

The saved `orca-theme` value accepts `light` and `dark`, defaulting to light when absent or invalid. The document head applies it before React renders. The toggle immediately updates the document, store and localStorage. Core brand fields retain black, burgundy and white; dark presentation uses neutral charcoal surfaces and readable semantic colors.

## Initial browser results

All seven primary routes preserve the selected dark theme across navigation. Switching to light then reloading preserves light. Model settings and mode help render with dark surfaces and readable labels. At 1366 × 768, Operator's title, description and kill-switch control share a 32-pixel row. No page errors were reported.


## Final verification

- Master: 3840 × 2160, H.264 at 24 fps, AAC audio, 98.500 seconds, 8,652,689 bytes. The text/vector composition and all three network shots were rendered natively at 4K. A 1280 × 720 web copy retains the same narration and duration.
- Google Cloud voice: `en-US-Chirp3-HD-Enceladus`, speaking rate 1.0. The longer 98.5-second timeline preserves natural speech. Every segment fits its scene. Original effects are sidechain-ducked below narration; final audio peak −3.3 dB, mean −22.8 dB. Levels and audio presence were measured; no subjective audio audition is claimed.
- English VTT: 21 ordered sentence cues, 0.300–97.848 seconds. Sentence boundaries are estimated. Transcript text remains available on Learn.
- Browser playback confirms the default source is the 4K master, video metadata is 3840 × 2160, playback advances, captions load, and the quality selector switches to the 720p web copy.
- 98 responsive checks across seven routes, seven widths (1920 through 320) and both themes passed without theme mismatch, horizontal document overflow, clipped fitted chart or JavaScript page errors. Desktop workspace documents fit at 1024 pixels and above in the tested 768-pixel height.
- Dark-mode dialogs and tour controls were checked separately. A low-contrast mode-help selector was corrected and its intro, instructions and footnote verified with the final computed colors.
- Official Chrome DevTools MCP confirmed dark theme persistence, the new SVG brand mark, a 32-pixel Operator header, a 1366 × 768 document and a fully fitted side chart. No console warnings or errors appeared.
- TypeScript and production Vite build pass; 37 focused frontend regressions pass. The existing optional 3D chunk remains lazy-loaded and still produces a bundle-size advisory. A full ffmpeg decode of the 4K master passes.

Preview: `http://localhost:8064`. 4K download: `/media/orca-method-4k.mp4`. Brand source assets: `/brand/orca-mark.svg` and `/brand/orca-wordmark.svg`. Changes remain local; no commit or push was performed.

## Caption and soundtrack follow-up

The final 4K and HD exports now include visible word-highlighted captions, an original instrumental bed and the previously included effects. The approved 189 words form 41 non-overlapping phrase cues. Word timings come from local speech-model timestamps mapped back to the approved script; remaining substitutions are model-estimated. Music and effects are ducked independently beneath Enceladus. The final measured mix is −22.7 dBFS mean and −3.2 dBFS peak. Duration remains 98.5 seconds. The WebVTT remains available as an optional text track, with no default duplicate layer.

Captioned export verification: both production media copies match their source hashes. Browser playback confirms 3840 × 2160 and 98.5 seconds for the master, 1280 × 720 for HD, 41 optional text cues, and no default duplicate text layer. Full ffmpeg decoding and the production build pass. Representative network, incident and recovery frames show readable word highlighting below the existing footer content.
