# UI redesign - handoff for a new chat (8 Nov 2026, 22:00 IST)

The user (Charan) checked the live UI and said it is not good enough. The components and the engine work; the
**visual design and flow** need a full redesign. Read this file first, then the files listed under "Read".

Deadline: submission **10 Nov 19:30 IST**. The UI is needed for the demo video (9 Nov). Report > code > video.

## What ORCA-NTN is (one paragraph)
AI agents that heal satellite-backed networks and coordinate the cyber-incident response, on an **emulated**
network in Chennai. Models detect (M1 anomaly, M2 time-to-failure, M3 fault-or-attack with abstain, M4 MILP
capacity), 6 LLM agents coordinate (mobile operator, satellite operator, power utility, CERT-In, regulator,
policy adviser), a deterministic rule engine gives the legal verdicts (6 verdicts, each citing a KB record),
guards lock execution (owner-only playbooks, PIN approval, autonomy MANUAL/ASSISTED/AUTO, kill switch, hash-chained
audit), the human commander approves, the network heals over clean paths, and India's policy gaps are reported
with global examples. Pitch line: "Models detect, agents coordinate, code decides, humans approve."

## What exists (reuse, do not rebuild the engine)
- Engine: `orca/live/` (`python -m orca.live --scenario S1 --llm mock|local --port 8060`), stdlib HTTP + SSE.
  API and event shapes: `docs/plan/LIVE_CONSOLE.md` sections 4-5 and `docs/plan/LIVE_API_EXAMPLES.md`.
  `audience:"control"` events carry ground truth and must never render on the Console.
- UI: `dashboard/live/web/` - React 18 + TypeScript + Vite + framer-motion + @react-three/fiber/drei + zustand.
  `src/`: `App.tsx`, `Landing.tsx`, `Control.tsx`, `Console.tsx`, `Review.tsx`, `api.ts`, `stream.ts`, `store.ts`,
  `types.ts`, `components/` (`Shell`, `ui`), `scenes/NetworkScene.tsx`, `theme/` (`tokens.css`, `motion.ts`),
  `fake/events.ts` (dev mode `?fake=1`).
  The data layer (`api.ts`, `stream.ts`, `store.ts`, `types.ts`) is fine; the screens and styling are what to redesign.
- Build: `cd dashboard/live/web && PATH=/opt/homebrew/opt/node@24/bin:$PATH npm run build` (the default node is
  broken). Output `dashboard/live/dist/` is committed. Tests: `tests/test_live_ui.py`, `tests/test_live.py`.
- Previous spec (design tokens, motion rules, 3D, screen contents): `docs/plan/LIVE_UI.md`. Treat it as the
  starting point, not a constraint - the user wants a better result.

## Hard rules
- Every NTN link is labelled **"emulated"**; never claim real satellite connectivity.
- Console never shows ground truth. Status = icon + word + colour, never colour alone.
- No external URLs at runtime (fonts, textures, CDNs vendored); judges run it offline.
- No AI-attribution lines in commits or files. Only the lead (main Claude session) commits/pushes.
- Times to the user in IST only.

## Ask the user first (they have not answered yet)
1. What exactly bothered them in the current UI (2-3 things).
2. 2-3 reference sites/products for the look (e.g. Linear, Vercel, Stripe, Palantir-style ops consoles).
3. Which screen matters most for the video (suggested: Console, then Control).
4. 3D: full scene / clean 2D map + small 3D / 3D only on Landing.
5. Light, dark, or both (projector + video often favour dark).
User preferences from earlier: professional, Emil Kowalski motion style (every animation has a job, ease-out,
<300 ms for UI), **no neon**, fully animated and very smooth, light theme available, 3D wanted in Console too,
two operating views (simulator/attacks = Control; operator console = Console).

## Demo flow the UI must carry (video)
Landing -> Start exercise (Control) + Open console (Console) -> director launches KA-SAT intrusion -> Console:
alert, M3 attack class, satellite operator requests PB-01 -> commander approves with PIN -> director launches
jamming -> AUTO heals inside its scope (clean-path check before failover) -> gap card slides in (India vs global
example vs recommendation) -> kill switch -> End exercise -> Review opens on the recording.

## Model / data facts the UI may show (current, 8 Nov)
- Agent LLM: tuned Gemma 4 12B passed the full system test (rules on 40/40, rules off 0/40, 0 unsafe executions).
  Tuned Qwen3.6-35B-A3B scored best on the held-out eval (tool choice 0.93, refusal without token 0.98, 0 unsafe)
  and its system test is running; the final model is decided after it. Show the model name from the engine,
  do not hard-code it.
- M3: 97.1% accuracy on the harder held-out set, abstains 1.7%.
- KB: 7 confirmed India gaps, 19 global examples; RAG v2 index of 82,191 legal clause chunks.
