# ORCA-NTN method film

The 98.5-second film has a 3840 × 2160, 24 fps master and a 1280 × 720 web version. Six HyperFrames scenes use local GSAP and Google Cloud Text-to-Speech `en-US-Chirp3-HD-Enceladus` narration at the auditioned speaking rate 1.0. A quiet original effects bed is sidechain-ducked beneath speech; the final mix receives 4 dB of gain. The 3D scenes use Three.js and the existing Blender-exported `public/models/orca-assets.glb`; they are captured at native 4K using browser and renderer pixel ratio 3. The separate six-second `orca-network-demo.mp4` is a silent loop. All links are emulated and the scenario is illustrative.

`TRANSCRIPT.md`, `narration.json` and `public/media/orca-method.vtt` contain the words. Caption sentence boundaries are proportional estimates, not forced alignment. The architecture shows detect, decide, act and report: facts go to deterministic rules; agents use RAG. Human approval in the film describes assisted mode.

## Rebuild the master and web version

With Node, ffmpeg, Python 3, Chrome headless shell, HyperFrames 0.9.26 and the included 4K 3D clips:

```sh
npm run check
npm run render
ffprobe -v error -show_entries stream=codec_name,codec_type,width,height,r_frame_rate,duration -of compact ../../../public/media/orca-method-4k.mp4
ffprobe -v error -show_entries stream=codec_name,codec_type,width,height,r_frame_rate,duration -of compact ../../../public/media/orca-method.mp4
```

`node export-brand.mjs` refreshes the 84 × 84 brand-mark raster from the shared SVG for a 28 CSS-pixel mark. `render` captures the vector composition natively at 4K and calls `assemble.py`. That script validates that each speech segment fits its scene, composites the three 4K shots, mixes the ducked sound effects, writes the 4K master, derives the smaller web version and poster, and generates the VTT. Scene timing lives in `index.html`; speech starts 0.3 seconds into each scene. Run `npm run sound-effects` to recreate the original effects bed. Local narration files make rendering independent of cloud access.

To synthesize speech again, set `GOOGLE_CLOUD_QUOTA_PROJECT` to a project authorized for Text-to-Speech and run `python3 synthesize.py` with application-default credentials. Never place credentials in this directory. The caller needs `serviceusage.services.use`; changes in text or speaking rate may require scene retiming. Verify audio and captions after any change.

## Rebuild the 3D shots

`network-3d.html` uses the GLB and adds procedural buildings, gateways and connections without modifying the Blender file. Serve `dashboard/live/web` at port 8789. Make Playwright available to Node (or set `PLAYWRIGHT_MODULE` to its entry point), and set `HYPERFRAMES_BROWSER_PATH` to a Chrome headless shell. From this directory:

```sh
for mode in normal attack recovery; do VIDEO_PIXEL_RATIO=3 node capture-3d.mjs "$mode"; done
for mode in normal attack recovery; do ffmpeg -framerate 24 -i "/private/tmp/orca-3d-frames-$mode-4k/%04d.png" -c:v libx264 -preset veryfast -pix_fmt yuv420p -crf 20 "assets/$mode-4k.mp4"; done
```

The 4K capture uses a 1280 × 720 CSS viewport at device pixel ratio 3; both the canvas renderer and screenshot are 3840 × 2160. HyperFrames is a build-time tool, not a runtime dependency of the application. Inspect the six scenes, speech and poster after rebuilding.

## Original music bed

`background_music.py` generates `assets/background-music.flac`: a deterministic 98.5-second stereo instrumental with a soft pad and arpeggio, derived from the duration in `index.html`. It uses NumPy and ffmpeg and contains no sampled or stock audio. Its measured mean is −24.9 dBFS and peak −15.0 dBFS; mixing at `volume=0.16` places its mean around −40.8 dBFS before final gain. Duck it beneath narration, retain the separately generated effects bed, and verify the completed mix for clipping after any level change.

## Live captions, music and effects

The final film has always-visible, word-highlighted captions in a small lower strip that does not cover diagram labels or the footer. The approved narration is split into 41 phrases (189 words). Local faster-whisper word timestamps supply the alignment; recognized text is never substituted for the approved script. Unmatched ASR tokens are discarded and timing substitutions are bounded to the associated spoken interval. Word timing is model-estimated, not manually forced alignment.

The original 98.5-second instrumental bed uses a soft pad and sparse arpeggio. Its level is `volume=0.16` before the final 4 dB gain. Music and effects have separate speech-controlled sidechain compressors. The final safety limiter caps unexpected peaks; the measured output peak is −3.2 dBFS, with no clipping. The music has a three-second opening fade and five-second closing fade. There are no downloaded stock tracks or additional vocals.

For caption or mix changes without re-rendering the network:

```sh
python3 -m pip install -r caption-requirements.txt
python3 render_captions.py
python3 finish_film.py
```

`finish_film.py` uses `assets/film-clean-4k.mp4` to prevent repeated caption burns and rebuilds the audio from narration, effects and music. `npm run render` refreshes that clean base after a fresh HyperFrames render. The clean base is a build asset; the dashboard serves the captioned exports. The temporary caption PNG strip is generated under `/private/tmp/orca-live-captions`.

If the narration changes, run `python3 caption_timing.py` first. This downloads a build-only `base.en` model into a temporary cache. The included timing JSON makes ordinary builds independent of speech-model downloads. Timing validation retains every approved word, rejects overlapping phrase cues and bounds every cue to the film duration. The optional WebVTT track is not enabled by default, avoiding a second caption layer on top of the visible captions.
