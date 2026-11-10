# Legacy lightweight replay viewer

For the current exercise dashboard, use the [project quick start](../README.md) and
[website guide](../guide.md). This directory also retains the original standard-library replay viewer described below.

Reads run files and replays them in a browser. Offline: no LLM, no network, no build step, standard library only.
Every satellite or NTN link shown is emulated.

```bash
python -m dashboard --run runs/mock-s1.jsonl      # http://localhost:8050
python -m dashboard                               # lists every runs/*.jsonl and the bundled samples
python -m dashboard.make_sample                   # rewrite the two bundled sample traces
```

Options: `--runs-dir`, `--host`, `--port`, `--open`. Deep links: `/?run=NAME&compare=NAME&at=N|end`.

## What it reads

Each line is an audit entry (`orca/audit.py`): `{seq, ts, kind, actor, payload, prev_hash, hash}`.
Everything else is derived in `dashboard/adapter.py`. Unknown kinds and missing fields never break the page.

| Kind | Used for |
|---|---|
| `event_released` (`alert_id`, `visible_to`, `t`) | scenario events, site state |
| `agent_task`, `agent_step` (`tool`, `args`, `result`, `rationale`, `citations_*`, `final`) | agents panel, verdicts (from `run_rule_engine`), alert details (from `read_alerts`), gap drafts (`record_gap`) |
| `msg_sent`, `msg_rejected` | messages panel (sender, recipients, type, `data_class`, refs) |
| `approval_requested`, `approved`, `rejected`, `executed`, `rolled_back`, `execute_refused` | approvals with clocks (`expires_at`, `token_expires_at`), map effects of PB-01/06/10-15 |
| `autonomy_set`, `autonomy_downgraded`, `kill_switch`, `kill_switch_released` | autonomy mode and kill switch state |
| `gap_human_decision` | gap draft status |

Run file names: `<scenario>-<rules|norules>-<llm>.jsonl`. A rules/norules pair with the same scenario and llm gets a "Compare" button.

## Optional entries the runner can add (all optional)

- `run_meta` `{scenario, title, rules: bool, llm, start, seed, kb_as_of}`: first entry; replaces guessing from the file name.
- `verdict` `{verdict, rule_id, topic, record_ids, gap_id, explanation}` or `{verdicts: [...]}`: if verdicts are logged outside agent tool calls.
- `gap_raised` `{gap_id, title, topic}`.
- `net_state` `{sites: {CHN-02: {state, path, gateway, note}}, gateways: {GW-IN-1: {state}}, mgmt: {state}}`: exact network state from the simulator. States: normal, at_risk, suspect, fault, attack, down, contained, healed, protected. Without it, the map is inferred from alerts and executed playbooks.

## Live mode hook

`make_server(..., live=obj)` where `obj` has `status()`, `kill(reason)` and `release_kill()`. The kill switch button then POSTs to
`/api/kill` and `/api/kill/release`. With no `live` object (replay) the server answers 409 and changes nothing.
"Follow file" re-reads the run files every 2 seconds, so a run in progress can be watched.
