# ORCA Live UI

Install dependencies once with `npm install`. Run `npm run dev` for Vite on port 5173; `/api` requests proxy to `http://localhost:8060`. Use `?fake=1` (for example `/console?fake=1`) to play the bundled emulated S1 event sequence without an engine.

`npm run build` type-checks and builds the offline application into `../dist`. All application assets, including the Inter and JetBrains Mono font files, are bundled locally.
