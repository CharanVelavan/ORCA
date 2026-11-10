# ORCA live dashboard frontend

For a complete local installation, start with the [project README](../../../README.md) and
[judge reproducibility guide](../../../docs/JUDGE_REPRODUCIBILITY.md). The prebuilt frontend is
included; judges do not need Node.js to use it with the Python engine.

For frontend development, run `npm ci` and `npm run dev` in this directory. Vite serves port 5173
and proxies `/api` to an engine running separately on `http://localhost:8060`.
`npm run build` type-checks and writes the application into `../dist`. Geist Sans and Geist Mono
font files are bundled locally.

The application covers Learn, scenario briefings, the exercise Console, Policy & Gaps, Recovery,
Audit & Replay, and the [website guide](../../../guide.md). Satellite and NTN links are emulated.
The optional `?fake=1` development fixture plays bundled S1 events without an engine; it does not
measure live model performance.

The separate [hosted showcase](https://orca-ntn.vercel.app) is maintained in
[ORCA_DEMO](https://github.com/CharanVelavan/ORCA_DEMO). It connects no live model or RAG service.
