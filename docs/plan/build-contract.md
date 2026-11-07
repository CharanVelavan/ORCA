# Build contract: KB ↔ rule engine ↔ audit (7 Nov 2026)

Shared interface for tonight's build (BUILD_PLAN_v2 §6, block "8 Nov AM").
File owners: **Claude (orchestrator)** owns `kb/**`, `orca/kb.py`, `tools/validate_kb.py`, `kb/SCHEMA.md`.
**Sonnet helper** owns `orca/rules.py`, `rules/*.yaml`, `orca/audit.py`, `tests/test_rules.py`,
`tests/test_audit.py`. Nobody commits; the user reviews first.

## 1. KB changes (landing tonight; read through `orca.kb.load()` only)

### Records (`kb/<jurisdiction>/records.yaml`)
- New required field **`topics: [str, ...]`**, non-empty, always includes the primary `topic`.
  Topic coverage = "an in-force, binding, verified record whose `topics` contains the topic".
- New topics added to `TOPICS`: `ntn_coverage`, `downstream_warning`, `capacity_priority`,
  `failover_path_security`, `backup_power`, `joint_command`.
- New record `IN-TELACT-2023-2-s` (topics `[ntn_coverage]`, verified quote "including terrestrial
  or satellite networks").
- CERT-In Direction records get `in_force_from: 2022-06-27`.
- `binding_status` values unchanged: `binding | binding_not_in_force | not_stated | non_binding | proposal`.

### KB helpers in `orca/kb.py`
- `kb.as_of -> datetime.date` (from `kb/meta.yaml`), printed on every verdict.
- `kb.in_force_status(rid, on: date) -> str`, one of:
  - `in_force`: binding, and `in_force_from` is null or ≤ `on`;
  - `not_yet`: `binding_not_in_force`, or `in_force_from` > `on`;
  - `status_not_stated`: `binding_status == not_stated` (route to AMBIGUITY, never "not applicable");
  - `not_binding`: `non_binding` or `proposal`.
- `kb.covering(topic, jurisdiction, on) -> list[dict]`: records with that topic and jurisdiction,
  each annotated with `_status` (the value above). The engine decides what counts.
- `kb.gaps_for(topic, jurisdiction) -> list[dict]`: registered gap records for that topic.
- The existing `kb.in_force(rid, on)` stays and is `in_force_status(...) == "in_force"`.

### Gap records (`kb/gaps/*.yaml`)
New fields: `kind` (`coverage | ambiguity | standards`), `topic`, `status` (`candidate | confirmed`),
`search{date, sources_checked[], terms[], nearest_provision{source, pinpoint, quote}, why_not_covered}`,
`analysis{impact, affected[], comparison{EU, AE}}`, `interim_action{playbook, owner}`,
`recommendation{regulator, ask}`, `verified_by`. `verified: true` only when `status: confirmed`
(a human did it). Tonight **all gaps are `candidate`**.

| id | kind | topic |
|---|---|---|
| GAP-IN-01-THREE-CLOCKS | ambiguity | incident_reporting |
| GAP-IN-02-NO-DOWNSTREAM-WARNING | coverage | downstream_warning |
| GAP-IN-03-NO-PRIORITY-ORDER | coverage | capacity_priority |
| GAP-IN-04-NO-BATTERY-FLOOR | coverage | backup_power |
| GAP-IN-05-NO-BREACH-CLOCK-TODAY | coverage | personal_data_breach |
| GAP-IN-06-STANDARDS | standards | standards |
| GAP-IN-07-NO-JOINT-PLAN | coverage | joint_command |
| GAP-IN-08-NO-CLEAN-PATH-CHECK | coverage | failover_path_security |
| GAP-IN-09-SPACE-FW-STATUS | ambiguity | space_cyber |

Topic coverage today (what the engine must find):
- IN covered: `incident_reporting` (CERT-In ii, TCSR R7(1)), `point_of_contact` (iii),
  `log_retention` (iv), `ntn_coverage` (Telecom Act s.2(s)), `cert_powers`, `telecom_cyber_security`.
- IN not covered → gap: `downstream_warning`, `capacity_priority`, `backup_power`, `joint_command`,
  `failover_path_security`, `personal_data_breach` (records exist but `not_yet` until 2027-05-13).
- AE covered: `emergency_priority` (AE-TDRA-IC-2006-EMERGENCY). EU covered: `downstream_warning`
  (NIS2 Art. 23(2)), `personal_data_breach` (GDPR Art. 33(1)).
- Unverified records (`verified: false`) **cannot produce COMPLIANT or VIOLATION**; they produce
  INSUFFICIENT_EVIDENCE with note "record unverified". Some IN records are still unverified tonight;
  the engine must handle that, not assume.

## 2. Rule engine (`orca/rules.py`, `rules/<jur>.yaml`)
- Deterministic. No LLM. Facts in (a dict loaded from a scenario/inject YAML), verdicts out.
- Six verdicts: `COMPLIANT, VIOLATION, AMBIGUITY, CONFLICT, POTENTIAL_GAP, INSUFFICIENT_EVIDENCE`.
- Every verdict cites at least one KB record id or gap id that exists in the KB.
- Verdict object (dataclass, JSON-serialisable via `to_dict()`), at least:
  `verdict, rule_id, topic, record_ids[], gap_id|None, explanation (template text, built in code,
  with the numbers), deadline (ISO datetime)|None, time_left|None, readings[] (AMBIGUITY),
  actions[] (CONFLICT), notes[], kb_as_of, footer`.
- Footer on every verdict: **"Rule-engine result on stated facts. Not legal advice."**
- Timestamps only from facts (never "now" from the clock unless the facts give `now`).
- Uncovered topic → POTENTIAL_GAP with the registered gap id for (jurisdiction, topic), else
  `GAP-CAND-<first 8 hex of sha1("<jur>:<topic>")>`, status candidate.
- Wording in explanations: "not found in the sources we checked, as of <kb_as_of>". Never "no rule exists".

## 3. Audit log (`orca/audit.py`)
Append-only JSONL, each entry `{seq, ts (from caller), kind, actor, payload, prev_hash, hash}`;
`hash = sha256(canonical JSON of the entry without hash)`. `verify()` returns the first broken seq
or None. Call it **tamper-evident**, never tamper-proof.
