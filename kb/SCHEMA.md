# Knowledge-base record format

Every legal or policy statement the system uses is a **record** in a YAML file under `kb/`.
The rule engine cites record ids in its verdicts; the agents may only cite ids that exist here.

```yaml
- id: IN-TCSR-2024-R7-1            # unique, stable: COUNTRY-INSTRUMENT-YEAR-CLAUSE
  jurisdiction: IN                 # IN, EU, US, AE, INTL
  instrument: Telecommunications (Telecom Cyber Security) Rules, 2024
  clause: Rule 7(1)
  authority: Department of Telecommunications (DoT)
  binding_status: binding          # binding | binding_not_in_force | not_stated | non_binding | proposal
  issued: 2024-11-21
  in_force_from: 2024-11-21        # null if unknown; a future date if not yet commenced
  topic: incident_reporting        # see TOPICS below (primary topic)
  topics: [incident_reporting, telecom_cyber_security]  # every topic this clause covers; must include topic
  obligation:                      # optional; only for clauses that create a duty
    actor: telecommunication_entity
    action: report_security_incident
    recipient: Central Government
    deadline: PT6H                 # ISO 8601 duration
    trigger: occurrence            # occurrence | noticing | awareness | none
  quote: "such entity shall report the same to the Central Government within six (6) hours of such occurrence"
  pinpoint: Rule 7(1), PDF p. 11   # where the quote is in the source
  summary: Six-hour report to the Central Government, counted from occurrence.
  source: in-tcsr-2024             # id in kb/sources.yaml (URL + sha256)
  verified: true                   # true only if the quote was checked against the official PDF
  verified_by: charan/india-citation-check.md (5 Nov 2026)
  notes: null
```

Rules for records:

1. `quote` must be **verbatim** from the official text. If nobody has checked it, leave `quote: null`
   and set `verified: false`; the summary can still describe the clause.
2. `verified: true` needs `quote`, `pinpoint` and `verified_by`.
3. Never add a document that a search reported as NOT FOUND. A missing rule becomes a **gap record**
   in `kb/gaps/` instead.
4. Dates are ISO (`YYYY-MM-DD`); deadlines are ISO 8601 durations (`PT6H`, `PT72H`).
5. News articles are never sources.

Gap records (`kb/gaps/*.yaml`, v2 from 7 Nov 2026) use `id`, `jurisdiction`, `kind`
(`coverage | ambiguity | standards`), `topic`, `status` (`candidate | confirmed`), `title`, `finding`,
`evidence` (record ids), `affects` (actors), `search` (`date`, `sources_checked`, `terms`,
`nearest_provision{source, pinpoint, quote}`, `why_not_covered`), optional `analysis`
(`impact`, `affected`, `comparison{EU, AE}`), `interim_action` (`playbook`, `owner`, `action`),
`recommendation` (`regulator`, `ask`), `verified`, `verified_by`, `notes`.
A gap is `confirmed` with `verified: true` only after a **human** checks its search record and
writes their name and date in `verified_by`. The validator enforces this.

Topic coverage: the rule engine treats a topic as covered when an in-force, binding, verified
record lists it in `topics`. See `docs/plan/build-contract.md`.

TOPICS: `incident_reporting`, `point_of_contact`, `log_retention`, `cert_powers`, `emergency_powers`,
`telecom_cyber_security`, `critical_infrastructure`, `standards`, `personal_data_breach`,
`cross_border_transfer`, `space_cyber`, `emergency_priority`, `ntn_coverage`, `downstream_warning`,
`capacity_priority`, `failover_path_security`, `backup_power`, `joint_command`.

`python tools/validate_kb.py` checks every file against these rules.
