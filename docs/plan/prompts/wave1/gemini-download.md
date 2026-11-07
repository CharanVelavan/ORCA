# Task: download, extract metadata and candidate quotes ({{JUR_NAME}}) — ORCA-NTN KB, agent {{AGENT}}

{{RULES}}

## Inputs
Target lists (YAML, written by another agent, may not exist yet):
  {{LISTS}}
Poll: if a list file does not exist yet, run `sleep 120` and check again (up to 3 hours). Process
items in rank order as soon as a list exists; pick up the next list when it appears. Skip ids that
already have a staging file (so a rerun resumes where it stopped). While waiting for the first list,
start on the {{JUR_NAME}} items in ../charan/country-documents.md that are not in kb/sources.yaml.

## Per document
1. Download with curl first:
   `curl -L --fail -A "Mozilla/5.0" --max-time 120 -o corpus/raw/{{AGENT}}/<id>.<ext> "<url>"`
   Check it is the real document (`file`, `pdfinfo`); an HTML error page is a failure. If curl fails,
   try the landing page for the real link, then the browser (one tab, close it after). Give up after
   3 attempts and record status: failed with the reason. Paid standards: status: paid, no download.
2. Extract text: `pdftotext -layout <pdf> corpus/raw/{{AGENT}}/<id>.txt` (HTML: save a plain-text
   copy). If the text has < 200 characters per page it is scanned: set scanned: true and do not
   invent quotes (OCR is done later).
3. Write kb/staging/{{AGENT}}/<id>.yaml:
```
id: <id from the list>
title: ...
authority: ...
jurisdiction: ...
doc_type: ...
url: <the URL actually downloaded>
landing_page: ...
local_path: corpus/raw/{{AGENT}}/<file>
sha256: <shasum -a 256>
bytes: <size>
pages: <pdfinfo pages or null>
retrieved_at: 2026-11-08
status: ok | failed | paid | scanned
official_domain: true|false   # domain belongs to the issuing authority / official gazette
binding_status: binding | advisory | draft | not stated   # as the document itself states; quote the words in binding_basis
binding_basis: "<verbatim words from the doc, or 'not stated in the document'>"
issued: ...
in_force_from: ... | unknown
amends: [...] ; amended_by: [...]
licence: ...
language: en | hi | bilingual | ...
gaps: [GAP-IN-0x ...]
role: india_evidence | global_example | context
candidate_quotes:          # 2-6 per document, the clauses most relevant to the gaps
  - quote: "<copied EXACTLY, character for character, from the .txt; one sentence or clause; no paraphrase, no ellipsis inside>"
    page: <PDF page number where it appears>
    clause: "<section/rule/article number>"
    topic: <one of: incident_reporting, downstream_warning, capacity_priority, backup_power, standards, failover_path_security, space_cyber, personal_data_breach, joint_command, gnss_interference, signalling_security, log_retention, critical_infrastructure, disaster_coordination, data_location, interference_reporting, emergency_powers, telecom_cyber_security, other>
    gap: GAP-IN-0x | null
    supports: proves_gap | answers_gap | global_example | context
    why: "<one sentence>"
verified: false
notes: "<anything uncertain>"
```
   Quotes must be findable with an exact text search in the .txt after collapsing whitespace. A
   quote checker will reject anything that is not. If no relevant clause exists, say so in notes and
   leave candidate_quotes empty. Never put a quote you did not see in the file.
4. Append one line to kb/staging/{{AGENT}}/_progress.md: `<rank> <id> <status> <n quotes>`.

## Finish
When every listed item is processed, write kb/staging/{{AGENT}}/_summary.md: counts by status,
by gap, failures with reasons, and any items where the list's claims (binding, in force, URL)
turned out wrong. Then stop.
