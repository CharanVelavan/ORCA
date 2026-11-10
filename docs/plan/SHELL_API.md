# Dashboard shell contract

The top navigation and context strip are owned by `src/shell/Shell.tsx`; the
shell also renders one lifecycle stepper on every route except Home. Pages
provide their content, not their own navigation or footer.

## Page composition

```tsx
import { PageFrame, Panel, Stat, StatusBadge, FLOW_RESPONSE } from '../shell';
import { hasTelemetry, networkHealthPct, pctView, sitesAffected, useDerived } from '../derive';

export default function Example() {
  const data = useDerived();
  const affected = sitesAffected(data);
  return (
    <PageFrame title="Operations" flow={FLOW_RESPONSE}
      kpis={<Stat label="Network health" testid="network-health" {...pctView(networkHealthPct(data))} />}>
      <Panel title="Sites">
        {hasTelemetry(data) ? `${affected.affected} / ${affected.total}` : 'Unavailable'}
        <StatusBadge tone="unknown" word="Awaiting telemetry" />
      </Panel>
    </PageFrame>
  );
}
```

`PageFrame` accepts `title`, `subtitle`, `actions`, `kpis`, `flow` and
`children`. A `flow` adds the resizable right panel; import `FLOW_RESPONSE`,
`FLOW_INVESTIGATION`, `FLOW_POLICY` or `FLOW_RECOVERY` from `src/shell`. It
uses the `pipeline/FlowGraph.tsx` entrypoint and the existing pipeline state.
The resize separator supports the mouse and left/right arrow keys. Page owners
may supply a `FlowConfig`, but must not change another page's files.

`Panel`, `Stat`, `StatusBadge`, `Pill`, `Chip`, `Code`, `Empty`,
`EmulatedBadge` and `Sparkline` are exported from `src/shell`. Status is an icon,
word and colour. Use `data-testid` through the `Stat` `testid` prop for shared
cross-page metrics. Every data-rich chart also needs a labelled table or
equivalent textual values.

## Data and event rules

Import `useDerived()` and selectors from `src/derive.ts`. Important selectors:

- `sitesAffected`, `sites`, `hasTelemetry`, `networkHealthPct` and
  `serviceAvailabilityPct`. Health and availability are current delivered
  demand shares, not cumulative run totals; absent measurements are unavailable.
- `services`, `deliveredMbps`, `serviceSeries`: latest per-service Mbps,
  aggregate delivered Mbps (including a real zero), and tick history.
- `gatewayHealth`: operational allowed ground stations from actual gateway
  states; unavailable until each allowed gateway has reported.
- `models`: M1 score, M2 `horizon_min`, M3 class/confidence or abstain, M4
  allocation rows and `optimal`/`feasible`. Do not show confidence for M2/M4.
- `agents`, `operatorsOnline`, `openApprovals`, `openGaps`, `citationIds`,
  `phaseSteps`, `timings`, `scenarioCtx` and `useCatalogueCounts`.
- `useLiveStore` retains `events`, `tickHistory`, `phaseHistory`, `summary`,
  `verdicts`, `obligations`, approvals and agents. Only the Simulator may read
  the separate `truth` and `schedules` fields. Control-audience events never
  enter the common `events` or `raw` lists.
- `kb_changed` and `rules_changed` clear current verdicts, obligations, gaps
  and summary; the full non-control event history remains available for audit.

`GET /api/catalogue` contains scenarios, site/gateway metadata, playbooks,
injectors, records, gaps and roles. Use its record metadata for citation titles,
binding and in-force status. `summary.timings` values can be null; do not
replace them with zero or a success state. All times are simulated; use
`simClockIST()` from `src/shell` for display.

The shell keeps the flow graph active from live events, not scenario ground
truth. Decision branches remain unresolved until the relevant model, rule,
verification or rollback event is observed. `source` in the live store can be
set to `replay` to stop the live bridge while replay drives the same state.

## Styling and motion

`src/theme/tokens.css` defines light-theme surface, ink, status, spacing,
radius, typography and motion tokens. Use the existing `sh-*` classes and
semantic tokens; no runtime remote fonts or assets. Use tabular figures for
numbers. UI transitions are 120-240 ms with ease-out; avoid bouncy effects and
honour `prefers-reduced-motion`. Use the existing React 18/Fiber 8 scene as the
3D base; no post-processing or network-fetched textures.

## Routes and integration

The lead rewires the lazy imports in `src/App.tsx` after the page owners finish.
Routes are `/`, `/simulator`, `/operations`, `/investigation`, `/policy`,
`/recovery` and `/audit`. Legacy routes redirect while preserving the query.
When linking between pages during fixture playback, preserve the current
`?fake=1&scn=...` query; fixture playback cannot execute backend commands.
Do not edit `App.tsx`, the shell, `derive.ts`, `store.ts`, `stream.ts`, `api.ts`
or another owner's page without coordinating with the lead.

Build from `dashboard/live/web` with Node 24 and `npm run build`. In the
current workstation, Homebrew Node 24 cannot load its linked simdjson library;
the lead has an isolated Node 24 runtime in the session workspace. The
workstation-specific workaround is not required on judges' machines.
