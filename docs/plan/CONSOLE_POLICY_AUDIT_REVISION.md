# Unified console, Learn, Policy and Audit revision

Requested and approved by Charan in the current session. Policy/Audit concept image was reviewed and both layouts explicitly approved before implementation. Image generation was used only for layout exploration; production evidence must come from the existing APIs/helpers.

## Session checklist

- [x] Inspect the current screens and preserve existing work.
- [x] Generate Policy/Audit concepts and obtain approval.
- [x] Consolidate primary navigation around the exercise Console.
- [x] Merge scenario direction, observed network, evidence and attack controls.
- [x] Add persisted pointer/keyboard panel resizing and reset.
- [x] Explain all ten scenarios and enhance original fitted-flow controls.
- [x] Keep one film, simplify download text and restore interactive 3D.
- [x] Add graph hover/focus previews with pinned selection.
- [x] Implement approved Policy and Audit workspaces.
- [x] Complete integrated browser and regression verification.

## Boundaries

All networks and attacks remain emulated. Director ground truth stays separate from operator evidence. Replay cannot send engine commands. Existing PIN, ownership and guarded execution checks remain in place. No documents, commits or remote pushes are authorized by this UI task.

## Verification so far

- 37 focused frontend regressions passed.
- Twelve console viewport/theme cases (1920,1366,1024,768,390,320; light/dark) passed document width checks and fit-to-view checks. Desktop cases fit the viewport height.
- All five panel separators respond to keyboard input. Pointer resizing and reload persistence passed. Reset restores defaults.
- Fixture replay launch is disabled and emitted zero POSTs during tab/layout interaction.
- Learn has exactly one video and the download text requested. Five widths (1366 through320) passed horizontal overflow checks.
- Interactive3D lazy activation produced a nonempty1268x540canvas; static mode unmounted it. Hover/focus graph preview preserves pinned selection.
- Official Chrome DevTools MCP confirmed unified panel labels, separator values, disabled replay launch and fitted-flow zoom slider.

The optional3D module still produces the existing bundle-size advisory and loads only when requested.

## Approved workspaces

Policy now has a searchable Gaps/Duties/Sources list, a selected-item inspector, current reporting clocks and the original fitted policy flow. Gap confirmation retains the existing PIN guard. Sources display only catalogue-supplied summaries, excerpts, verification state, URL and SHA-256; the API now forwards those public fields from the existing KB.

Audit now has recording transport, a filter/index, chronological timeline, selected event inspector, public JSONL export, server chain recheck and scrubber. Record selection seeks playback; verification rechecks the loaded recording version. Original chain status remains separate from redacted public exports. Both workspaces use persisted resizable splits and mobile stacking.

Integrated browser verification loaded an actual mock recording with 1,313 replay events and 321 public audit entries. Seeking, stepping, playing, searching, selection, chain recheck and export passed. Navigating to Policy showed three gaps and five duties; navigating to Console kept all engine commands disabled. The full sequence sent zero POSTs. Twenty-four Policy/Audit viewport/theme checks passed document overflow and fitted-flow checks, with zero JavaScript errors. The mobile Audit header was then adjusted to place its title and actions on separate full-width rows.

Final focused regressions: 41 frontend tests and two backend catalogue/HTTP tests passed. Official Chrome DevTools MCP independently confirmed recording load, 160 paginated visible index entries, a selected inspector, verified-chain labels and a 1366x768 document matching the viewport.

Current preview with the expanded catalogue API: http://localhost:8067/. The previous8064 process is left running; use8067 for the complete current backend/UI combination. No commit or push.

Final production build and TypeScript pass. After the mobile header adjustment, the 24 Policy/Audit checks and 12 Console checks passed again. The populated replay flow still reported three gaps, five duties, 321 exported public audit entries, zero POSTs and zero JavaScript errors. Screenshot artifacts are under `.shots/revision3/`. The 14-step guided tour was also checked and did not issue commands.

## Commander PIN removal (user-requested follow-up)

Charan explicitly requested removing the commander PIN. This supersedes the PIN references in the earlier implementation notes. The dashboard no longer renders PIN fields or sends PIN values for approval, autonomy, kill/release or gap decisions. The HTTP API accepts those commands without a PIN; legacy hash settings/constructor inputs are ignored. Explicit confirmation, named commander attribution, scoped grants, expiry, owner checks, exact-plan one-time tokens, clone tests, fresh verdicts and rollback guards remain. Replay guards remain in place. Active RUN/DEMO instructions and environment/Compose examples were updated.

Validation: 80 backend safety/commander HTTP tests and 41 focused frontend regressions passed; TypeScript and production build passed. Browser exercised kill, release, manual-mode confirmation, exact-plan approval and gap confirmation without password fields or PIN request values, with no JavaScript errors. Preview restarted at the same http://localhost:8067/ address with the updated backend.
