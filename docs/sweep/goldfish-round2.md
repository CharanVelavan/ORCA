# Goldfish review, round 2 (7 Nov 2026, night)

Target: Gap Register v3.1 → resolved into **v3.2**. Fresh reviewers again, with no memory of round 1.

| Reviewer | Model | Persona | Status | Blocker / Major / Nit |
|---|---|---|---|---|
| G1 | Claude Sonnet 5.5 | design_critic | completed | 2 / 11 / 8 |
| G3 | Gemini 3.8 Flash | zoom_out | completed | 1 / 8 / 1 |

Round 2 was **not clean**: G1 raised two new Blockers. Every accepted finding was checked in the PDF first.
G1 also confirmed that all Indian rule PDFs on disk are now notified texts, and that every quote is on its cited page.

## Resolution

| Finding | Reviewer | Decision | Change |
|---|---|---|---|
| GAP-07: CERT-In can direct operators (IT Act s.70B(6)), so "does not command" is wrong (B1) | G1 | **FIX** | GAP-07 reframed as **ambiguity**: two binding chains (CERT-In, DoT STDCC) and no tie-break |
| GAP-07: the SOP covers "natural and manmade" disasters; TSPs "shall comply" with STDCC (B2) | G1 | **FIX** | "for natural disasters" removed; DM Act and CCMP flagged as unchecked |
| Annexure B quote is on p. 47, not 48 (Blocker) | G3 | **CONTEST** | Checked pp. 46–49 with `pdftotext -raw`; the text is on p. 48 |
| GAP-06 duplicates GAP-09 (C1) | G1, G3 | **FIX** | GAP-06 narrowed to international feeder-link standards and the unused Telecom Act s.19 standards power |
| Record IN-TELACT-2023-24 mislabelled (s.24 is the Digital Bharat Nidhi) | G1 | **FIX** | Replaced by IN-TELACT-2023-19 (standards power, verified quote) |
| GAP-08 ignores Authz Rule 60(1)(b) (no foreign-gateway failover) and §7.3 integrity check | G1 | **FIX** | Added; PB-06 must respect 60(1)(b) |
| GAP-08 is a playbook feature, so park it | G3 | **CONTEST** | Kept as a technical-baseline gap; the attack path (jamming to force failover) is documented |
| GAP-09 misses Rule 60(1)(f) (interference mitigation) and GMPCS 41.7 / 41.9; scope in notes only | G1 | **FIX** | Added; scope (new authorised entities vs GMPCS licensees) moved into the finding |
| GAP-09 NIS2 comparison shows parity, not a gap | G1, G3 | **FIX** | Comparison set to null, explained in notes (EU Space Act is only a proposal) |
| PIB statement has no record id | G1 | **FIX** | New record IN-PIB-2026-SPACEFW-ADVISORY, cited in GAP-02 and GAP-09 |
| GAP-02 cites TCSR 7(2) without a record; NIS2 23(1) is the better comparator; 37(5) wording inconsistent | G1 | **FIX** | Records IN-TCSR-2024-R7-2, EU-NIS2-2022-ART23-1; one consistent 37(5) position |
| GAP-01 "three moments" vs notes; Authz 59(4)/62(7) reports | G1 | **FIX** | Title "two different triggers"; reports noted; EU comparison caveat |
| GAP-03 misses Authz 67(1), 71(1)(h) emergency duties; s.20 commencement | G1 | **FIX** | Added; why_not_covered says access is not ranking |
| GAP-04 impact contradicted by TRAI downtime benchmark; quote truncated | G1 | **FIX** | Impact rewritten around the monthly benchmark; full quote |
| GAP-04 is engineering, not policy | G3 | **CONTEST** | India already sets a numeric floor for grid comms (CEA 8(11)); settled in round 1 |
| GAP-05 should compare GDPR Art. 34(1), not 33 | G1 | **FIX** | Record EU-GDPR-2016-ART34-1 |
| GAP-05 kind / not NTN-specific | G1, G3 | **SETTLED** | Contested in round 1; not reopened (no new evidence) |
| A6: four gaps have no comparison | G1, G3 | **RECORD** | No comparator found in our KB for 04 (domestic CEA only), 06, 07, 08; stated in notes rather than invented |
| Register-wide unsearched instruments (UASL licences, CCMP, NCIIPC, DM Act, IN-SPACe, TEC) | G1 | **FIX** | Listed in the register header |
| TRAI records `in_force_from` null | G1 | **FIX** | 2024-10-01 (Reg. 1(2)) |
| Agent C's NCSC quote not in its PDF | G1 | **RECORD** | Already treated as unreliable (round 1) |

## State after round 2
- KB: 48 records (39 IN, 8 EU, 1 AE), 47 with verified quotes; all 56 record and nearest-provision quotes
  re-checked against source text (`pdftotext` layout and raw, OCR for CEA): 0 problems.
- Tests: 43 pass. Gaps: 9, all `candidate`.
- A round 3 would test whether v3.2 is clean.
