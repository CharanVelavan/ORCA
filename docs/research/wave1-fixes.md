# Wave 1 Staging Fixes Report

Date: 2026-11-08  
Branch: `Pred`  
Agent: Gemini #1 (KB Data Fixer)  

---

## 1. Checker Results: Before vs After

### `scripts/quote_check.py`
| Metric | Before Fixes | After Fixes | Change |
|---|---|---|---|
| `pass` (passing candidate quotes) | 544 | 530 | -14 (18 UAE quotes removed from scope; +1 CPUC quote fixed) |
| `fail` (failing candidate quotes) | 4 | **0** | **-4 (All 4 failing quotes resolved)** |
| `page_mismatch` | 7 | **0** | **-7 (All 7 page mismatches resolved)** |
| `no_text` | 0 | 0 | 0 |
| `docs` (staged documents with quotes) | 250 | 244 | -6 (6 UAE docs with quotes marked skipped) |
| `binding_pass` | 99 | **124** | **+25** |
| `binding_fail` | 38 | **0** | **-38 (All 38 binding_basis fails resolved)** |

### `tools/validate_kb.py`
```
records: 51 ({'EU': 8, 'AE': 1, 'IN': 42}), verified quotes: 49, gaps: 9, sources: 25
OK
```
Status: **PASSED (0 problems)**.

---

## 2. Task 1: Staging Validation Errors Fixed
Six primary discrepancies identified across staging metadata in `kb/staging/` were corrected:
1. `intl-3gpp-tr-22822`: Contradictory binding basis ("approved by 3GPP Technical Specification Groups") corrected to verbatim text from page 1: *"The present document has not been subject to any approval process by the 3GPP Organizational Partners and shall not be implemented. This Report is provided for future development work within 3GPP only."*
2. `intl-3gpp-tr-38821`: Contradictory binding basis corrected to verbatim text from page 5: *"The present document has not been subject to any approval process by the 3GPP Organizational Partners and shall not be implemented. This Specification is provided for future development work within 3GPP only."*
3. `in-space-policy-2023`: Basis error corrected from unstated "approved by the Cabinet Committee on Security" to verbatim text from page 5: *"the reform vision approved by Cabinet"*.
4. `in-trai-ppdr-consultation-2017`: Title and basis number error corrected from "No. 12/2017" to official document title on page 1: *"Consultation Paper No. 15/2017"* and statutory parent provision on page 9: *"for public consultation as per Section 11(a) of TRAI Act, 1997."*
5. `us-fcc-mdri-order-2022`: Adoption date error corrected from "June 28, 2022" to official order date on page 1: *"Adopted: June 27, 2022 Released: July 6, 2022"*.
6. `inspace-ngp-2024`: Fabricated text phrase dropped and replaced with verbatim binding provision from page 152: *"the decisions of IN-SPACe shall be binding on the operators of such facilities"*.

In addition, byte-identical duplicate `in-dot-ctir-2024` was annotated with cross-reference to `in-ctir-2024`.

---

## 3. Task 2: Re-check of 4 Failing Quotes & 7 Page Mismatches

### Failing Quotes (4 items -> 0 fails)
- `global/us-cpuc-d21-02-029-2021` (quote #2):
  - **Issue**: Extracted quote failed due to newline hyphenation artifact in pdftotext joining "address-" and "serviceresiliency@cpuc.ca.gov".
  - **Fix**: Shortened quote to verbatim clause preceding hyphenation on PDF page 107 (Ordering Paragraph 5): `"Facilities-based wireline providers shall file information only emergency operations plans pursuant to Section 5.9.2 of this decision, on an annual basis, with the first due within 60 days of the effective date of this decision to the Director of the Communications Division"`.
  - **Result**: `pass` on page 107.
- `global/ae-pdpl-decree-law-45-2021` (quotes #0, #1, #2):
  - **Issue**: Quotes were empty strings or garbled Arabic fragments (`'يف حال ع'`).
  - **Fix**: Document is a UAE instrument outside the single verified UAE global example (`ae-tdra-interconnection-2006`). Out-of-scope UAE documents marked `status: skipped`, `skipped: "out of scope (UAE host only, decided 8 Nov)"`, and candidate quotes cleared.
  - **Result**: Resolved cleanly without inventing Arabic text.

### Page Mismatches (7 items -> 0 mismatches)
- `global/intl-3gpp-tr-22822` (quote #2): Staged page 6 corrected to PDF page 5 (Clause 6.2 `[PR 6.2.006]`).
- `global/intl-3gpp-tr-38821` (quotes #0, #1, #2): Staged page 5 corrected to PDF page 10 for all three quotes (Clauses 5.1.1 and 5.2.1.1).
- `global/intl-unoosa-debris-guidelines-2007` (quote #0): Staged page 1 corrected to PDF page 5 (Preface section page iii).
- `india/in-trai-direction-cellular-outages-2024` (quote #0): Staged page 17 corrected to PDF page 3 (Paragraph 7(i) Annexure-II outage reporting deadline).
- `global/ae-tdra-space-services-policy` (quote #2): Staged page 3 verified on PDF page 4 (Article 4.1 harmful interference remedy); document also marked skipped as out-of-scope UAE.

---

## 4. Task 3: Re-check of 38 Failing Binding Bases (38 fails -> 0 fails)

Each failing basis was verified against extracted text in `corpus/raw/` or marked `unclear` / `not stated` with a documented reason:

### Global (26 items)
1. `ae-pdpl-decree-law-45-2021`: Marked skipped (`out of scope (UAE host only, decided 8 Nov)`), `binding_status: not stated`.
2. `enisa-eecc-incident-reporting-guideline`: `binding_status: advisory`, basis updated to verbatim p. 2 text: `"This publication should not be construed to be a legal action of ENISA"`.
3. `enisa-eecc-security-measures-guideline`: `binding_status: advisory`, basis updated to verbatim p. 6 text: `"Neither the high-level security objectives nor the detailed security measures should be seen as binding recommendations about which are appropriate security measures for providers to take."`.
4. `enisa-space-threat-landscape-2025`: `binding_status: advisory`, basis updated to verbatim p. 3 text: `"It does not endorse a regulatory obligation of ENISA or of ENISA bodies pursuant to the Regulation (EU) No 2019/881."`.
5. `eu-5g-cybersecurity-toolbox-2020`: `binding_status: unclear`, basis marked: `"not stated in the document (document does not state its legal status; sets out a non-binding coordinated European approach based on Commission Recommendation 2019/534)"`.
6. `eu-cer-2022-2557`: `binding_status: binding`, basis updated to verbatim entry-into-force article on p. 29: `"This Directive shall enter into force on the twentieth day following that of its publication in the Official Journal of the European Union."`.
7. `eu-cer-article-13-guidelines-2026`: `binding_status: advisory`, basis updated to verbatim p. 1 text: `"This Communication is not legally binding and does not affect the interpretation of EU law by the Court of Justice of the European Union."`.
8. `eu-eecc-2018-1972`: `binding_status: binding`, basis updated to verbatim entry-into-force text on p. 154: `"This Directive shall enter into force on the third day following that of its publication in the Official Journal of the European Union."`.
9. `eu-nis2-2022`: `binding_status: binding`, basis updated to verbatim entry-into-force text: `"This Directive shall enter into force on the twentieth day following that of its publication in the Official Journal of the European Union."`.
10. `eu-space-act-proposal-2025`: `binding_status: draft`, basis updated to verbatim proposal header: `"Proposal for a REGULATION OF THE EUROPEAN PARLIAMENT AND OF THE COUNCIL"`.
11–17. `intl-3gpp-ts-22153`, `intl-3gpp-ts-23501`, `intl-3gpp-ts-23502`, `intl-3gpp-ts-32541`, `intl-3gpp-ts-33501`, `intl-3gpp-ts-38300`, `intl-3gpp-ts-38401`: `binding_status: unclear`, basis marked: `"not stated in the document (3GPP technical specification; legal status as voluntary consensus standard not stated in the text)"`.
18. `itu-d-netp-guidelines-2020`: `binding_status: not stated`, basis updated to verbatim p. 9 scope sentence: `"This guide is intended primarily for national authorities responsible for the development and implementation of the NETP"`.
19, 22, 23, 24. `itu-e108-2016`, `itu-x1056-2020`, `itu-x1060-2021`, `itu-x1812-2023`: `binding_status: advisory`, basis updated to verbatim Recommendation status on p. 4: `"Compliance with this Recommendation is voluntary. However, the Recommendation may contain certain mandatory provisions"`.
20. `itu-r-res644-2019`: `binding_status: binding`, basis updated to verbatim Secretariat note: `"This revision of the Radio Regulations, complementing the Constitution and the Convention of the International Telecommunication Union"`.
21. `itu-radio-regulations-app10`: `binding_status: binding`, basis updated to verbatim Secretariat note: `"This revision of the Radio Regulations, complementing the Constitution and the Convention of the International Telecommunication Union"`.
25. `us-fcc-mdri-order-2022`: `binding_status: binding`, basis updated to verbatim adoption/release line on p. 1: `"Adopted: June 27, 2022 Released: July 6, 2022"`.
26. `us-fcc-part-4-outage`: `binding_status: binding`, basis updated to verbatim §4.1(a) text: `"the Federal Communications Commission is setting forth requirements pertinent to the reporting of disruptions"`.

### India (12 items)
27. `in-ctir-2024`: `binding_status: binding`, basis updated to verbatim gazette notification preamble on p. 6: `"Now, therefore, in exercise of the powers conferred by sub-section (4) of section 22 read with clause (w) of sub-section (2) of section 56 of the Telecommunications Act, 2023 (44 of 2023), the Central Government hereby makes the following rules, namely:-"`.
28. `in-dot-ctir-2024`: `binding_status: binding`, same preamble; cross-referenced as duplicate of `in-ctir-2024`.
29. `in-dot-telecom-standards-rules-2025`: `binding_status: binding`, title updated to official gazette title and basis to verbatim enacting clause: `"the Central Government hereby makes the following rules, namely:– 1. Short title and commencement.– (1) These rules may be called the Telecommunications (Framework to Notify Standards, Conformity Assessment and Certification) Rules, 2025."`.
30. `in-dot-unified-licence`: `binding_status: binding`, basis updated to verbatim condition on p. 17: `"Any order passed under these statutes shall be binding on the licensee."`.
31. `in-mha-ners-guidelines-2015`: `binding_status: advisory`, basis updated to verbatim implementation statement on p. 3: `"These guidelines would provide clarity to the State Governments/UT Administrations on the implementation aspect of the entire project."`.
32. `in-national-cyber-security-policy-2013`: `binding_status: unclear`, basis marked: `"not stated in the document (non-statutory national policy without parent Act citation)"`.
33. `in-ndma-communication-guidelines`: `binding_status: unclear`, basis marked: `"not stated in the document (national guidelines issued by NDMA; Disaster Management Act 2005 cited as context, not statutory rule-making power)"`.
34. `in-rbi-it-outsourcing-directions-2023`: `binding_status: binding`, basis updated to verbatim circular text on p. 1: `"the finalised Reserve Bank of India (Outsourcing of Information Technology Services) Directions, 2023 are enclosed herewith"`.
35. `in-space-policy-2023`: `binding_status: advisory`, basis updated to verbatim p. 5 text: `"the reform vision approved by Cabinet"`.
36. `in-tcsr-2024`: `binding_status: binding`, basis updated to verbatim gazette rule 1 text: `"the Central Government hereby makes the following rules, namely:- 1. Short title and commencement. — (1) These rules may be called the Telecommunications (Telecom Cyber Security) Rules, 2024."`.
37. `in-trai-ppdr-consultation-2017`: `binding_status: advisory`, title corrected to Consultation Paper No. 15/2017 and basis to verbatim statutory power on p. 9: `"for public consultation as per Section 11(a) of TRAI Act, 1997."`.
38. `inspace-ngp-2024`: `binding_status: binding`, basis updated to verbatim binding clause on p. 152: `"the decisions of IN-SPACe shall be binding on the operators of such facilities"`.

---

## 5. Task 4: UAE Documents Out-of-Scope Marking

Per project design decisions (CLAUDE.md & jury guidelines 8 Nov 2026), the knowledge base is India-focused with EU/US comparative instruments. The UAE hosts the event; only one verified UAE document is retained in the active knowledge base:
- **Retained**: `ae-tdra-interconnection-2006` (TDRA Interconnection Instructions v1.2, §4.5 priority for emergency calls at Points of Interconnection; mapped to record `AE-TDRA-IC-2006-EMERGENCY`).

All other 9 remaining UAE documents across staging and corpus raw were marked as `skipped: out of scope (UAE host only, decided 8 Nov)`:
1. `ae-ai-charter-2024`
2. `ae-ai-charter-2026`
3. `ae-pdpl-decree-law-45-2021`
4. `ae-tdra-iar-v1-1`
5. `ae-tdra-resilience`
6. `ae-tdra-space-services-policy`
7. `ae-cybercrime-law-2021`
8. `ae-csc-ciip-policy` (and companion files in `corpus/raw/claude-uae/`)
9. `ae-tdra-ntemp` (in `corpus/raw/claude-uae/`)

In `kb/staging/global/`, candidate quotes for these instruments were cleared, and their status updated to `skipped`. In `kb/manifest/manifest.yaml`, entries were marked with `skipped: "out of scope (UAE host only, decided 8 Nov)"` and paths indexed in the manifest's `skipped:` list.
