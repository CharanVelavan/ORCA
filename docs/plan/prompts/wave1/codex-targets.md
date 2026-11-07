# Task: document target list for the ORCA-NTN knowledge base (Codex, web search)

{{RULES}}

## Context
The KB must hold the laws, rules, directions, strategies, data-protection rules, institutional
mandates, emergency powers, treaty obligations and energy/infrastructure constraints that bear on
cyber security and self-healing of satellite-backed (NTN) networks and the everyday services that
depend on them (112, hospitals, payments, power grid, telecom). Scoring: KB completeness, accuracy,
structure; policy-gap identification; and "accuracy of the global policy examples is critical".

Our confirmed gaps (rank documents by how much they help prove, disprove or compare these):
- GAP-IN-01 incident_reporting: up to four reports to three bodies, with two different triggers
- GAP-IN-02 downstream_warning: no binding duty for a satellite operator to warn dependent services
- GAP-IN-03 capacity_priority: priority callers exist for disaster restoration, but no ranking for scarce backup capacity
- GAP-IN-04 backup_power: telecom sites must have power redundancy, but no minimum hours
- GAP-IN-06 standards: feeder-link / inter-satellite-link security unspecified; standards power unused
- GAP-IN-08 failover_path_security: no explicit check that the backup path is clean before failover during an attack
- GAP-IN-09 space_cyber: no binding satellite-specific cyber-resilience baseline; the space framework is advisory
Rejected by the human (still useful as context, low rank): GAP-IN-05 personal_data_breach, GAP-IN-07 joint_command.
Also relevant topics: GNSS jamming/spoofing, SS7/signalling security, log retention, critical
information infrastructure, disaster management, satellite authorisation/landing rights, gateway
location, interference reporting, data localisation, AI governance in telecom.

Already in the KB (do not list again; skip duplicates): read kb/sources.yaml and
../charan/country-documents.md (relative to the repo) for the existing and already-verified sources.

## Your job: {{SCOPE}}

For each document give a YAML list item (no prose outside the YAML, no code fences):
- rank: integer (1 = most gap-relevant)
  id: short slug, e.g. in-dot-satcom-policy-2023 / eu-cer-2022 (jurisdiction prefix: in-, eu-, us-, ae-, au-, uk-, sg-, jp-, ca-, intl-)
  title: official title
  authority: issuing body
  jurisdiction: IN | EU | US | AE | AU | UK | SG | JP | CA | INTL | other ISO code
  doc_type: act | rules | regulation | direction | order | licence | standard | guideline | strategy | sop | report | treaty | consultation
  url: DIRECT link to the official PDF/HTML on an official domain (prefer the PDF). Must be a URL you saw in search results; never guess a URL.
  landing_page: official page that links to it (if different)
  binding_status: binding | advisory | draft | not stated  (as the source itself or its issuer says)
  issued: YYYY-MM-DD or YYYY
  in_force: yes | no (with date) | partly | unknown
  amendments: known amendments/corrigenda with years, or "none found"
  licence: e.g. "Government of India open (GODL)", "EUR-Lex reuse policy", "public domain (US Gov)", "paid", "unknown"
  gaps: [GAP-IN-0x, ...] it bears on, or [] for context
  role: india_evidence | global_example | context
  relevance: 1-5 (5 = directly proves or answers a gap)
  why: one sentence on what clause/theme makes it relevant (only what you actually saw)

Prefer primary instruments over summaries. Include amendments as their own items. Mark
uncertainty honestly (binding_status "not stated", in_force "unknown"). Quality over padding:
an item without a real official URL must be dropped, not invented.
