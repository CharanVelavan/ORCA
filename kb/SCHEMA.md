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
  topic: incident_reporting        # see TOPICS below
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

Gap records (`kb/gaps/*.yaml`) use `id`, `jurisdiction`, `title`, `finding`, `evidence` (a list of
record ids that show the gap), `affects` (actors), and `verified`.

TOPICS: `incident_reporting`, `point_of_contact`, `log_retention`, `cert_powers`, `emergency_powers`,
`telecom_cyber_security`, `critical_infrastructure`, `standards`, `personal_data_breach`,
`cross_border_transfer`, `space_cyber`, `emergency_priority`.

`python tools/validate_kb.py` checks every file against these rules.
