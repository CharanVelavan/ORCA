# Goldfish review, round 1 (7 Nov 2026, night)

Elephant-Goldfish Model (google/elephant-goldfish-model). **Elephant:** Claude Opus 5.5 (holds context, wrote
Gap Register v3, resolves findings). **Goldfish:** three fresh reviewers with no chat history. They read only
the register, `gap-evidence-standard.md`, the KB and the source files. All three were read-only.

| Reviewer | Model | Persona | Status | Blocker / Major / Nit |
|---|---|---|---|---|
| G1 | Claude Sonnet 5.5 | design_critic (sceptical regulator's lawyer) | completed | 4 / 11 / 3 |
| G2 | Gemini 3.8 Flash | comprehension (naive reader) | completed | 1 / 8 / 2 |
| G3 | Gemini 3.8 Flash | zoom_out (big picture) | completed | 0 / 7 / 2 |

Target: `kb/gaps/india.yaml` v3 → resolved into **v3.1**. Every finding below was checked by Claude in the PDF
before it was accepted.

## The most important finding

**G1-B1: the TCSR file on disk was the draft.** `kb/sources/in-tcsr-2024.pdf` was G.S.R. 520(E) of 28 Aug 2024,
the draft for public comment. It came from a dot.gov.in URL. The notified rules (G.S.R. 720(E), 21 Nov 2024) say
Rule 7(1)(a): "within six hours of **becoming aware**", plus details within 24 hours. The 5 Nov citation check, the KB
record and Claude's rejection of external-review lead R1 all relied on the draft. **R1 was right.**
- Fixed: the notified text has replaced the draft (the draft is kept in `kb/sources/incoming/`). The record and the
  engine trigger now use `awareness`. GAP-IN-01 is rewritten. Tests are reworked: for an ordinary telecom entity, the
  CERT-In and DoT clocks now start together, and the conflict remains for CTI owners (occurrence).
- Lesson: check that a Gazette PDF is the *notified* text ("Whereas a draft … has been considered"), not the draft
  ("The following draft rules … proposes to make").
- Agent C's sources report also gave sha256 values for our TCSR files that match no file on disk. Its hashes are
  treated as unreliable.

## Resolution

| Finding | Reviewer(s) | Decision | What changed |
|---|---|---|---|
| TCSR draft, not final (B1, B2, M11) | G1 | **FIX** | See above |
| GAP-06: "no Indian text names a standard" is false; the framework names CCSDS SDLS (B3) | G1 | **FIX** | Reworded to "no *binding* Indian rule"; new record IN-SPACEFW-2026-SDLS is the nearest provision |
| GAP-06 mixes link security and a policy format; YAML part is self-serving | G1, G2, G3 | **FIX** | Policy-format claim dropped; X.1144/XACML acknowledged in notes |
| GAP-09 "only advisory" ignores binding general duties (Authz 47/50/53/54, TCSR 4) (B4) | G1 | **FIX** | Narrowed to "no binding *satellite-specific* baseline"; new record IN-AUTHZ-2026-R54-1; scope note on new authorised entities and the GMPCS licence |
| GAP-09 nearest provision is a press release (F7) | G3 | **FIX** | Nearest = framework control (p. 17); PIB moved to why_not_covered |
| GAP-09 NIS2 comparison scope (M10) | G1 | **FIX** | Qualifier added (Annex I excludes public e-comms providers) |
| GAP-08 is a technical control, not a law gap (A5) | G1, G2, G3 | **FIX** | kind → standards; EU comparison removed; CTIR 7(1)(i) DR/BCP added |
| GAP-01 nearest provision is a drafting line (M1, F6) | G1, G3 | **FIX** | Nearest = CTIR 7(1)(j) (portal "form and manner" hook) |
| GAP-01 TRAI threshold and actor (M2) | G1 | **FIX** | "access provider … more than four hours in a district" |
| GAP-02 misses CERT-In alert function and Authz 37(5) sharing ban (M3) | G1 | **FIX** | New records IN-ITACT-2000-70B-4, IN-AUTHZ-2026-R37-5; ask now includes a standing 37(5) approval |
| GAP-03 misses Authz 38(1) hook, SOP 6.2 "shall", TRAI 4.2.2 (M4) | G1 | **FIX** | Added to finding; UAE comparison qualified |
| GAP-04 misses binding TRAI Reg. 3(2) redundancy (M5) | G1 | **FIX** | New record IN-TRAI-QOS-2024-3-2 as nearest binding provision |
| GAP-04 kind "ambiguity" fits poorly (M5) | G1 | **CONTEST** | The engine returns AMBIGUITY (the SOP's status is not stated); the kind matches the verdict. Title now says "no minimum hours" |
| GAP-05 commencement source and pages (M6) | G1 | **FIX** | Act footnote (G.S.R. 843(E)) cited; CERT-In Annexure pages p. 4 → p. 5; Directions (iii)/(iv) p. 2 → p. 3 |
| GAP-05 should not be `coverage` / not NTN-specific (M6, F5) | G1, G3 | **CONTEST** | No duty to notify affected people is in force today, which is a coverage gap now. The title and notes say it is a transition period. Subscriber data is part of the demo scenario |
| GAP-07 misses CERT-In s.70B(4)(d) coordination (M8) | G1 | **FIX** | Finding narrowed: coordination exists, joint command does not |
| GAP-07 `affects: [all]` (F9) | G3 | **FIX** | Explicit list |
| GAP-07 DM Act 2005, national CCMP not searched (M8, A2) | G1 | **RECORD** | Noted in the gap; human check before confirming |
| Space ISAC and satellite incident type missing (F4) | G3 | **RECORD** | Parked as GAP-09 sub-points (proportion, C3); not new gaps tonight |
| SUMMARY.md points to the retired GAP-09 id (F2) | G3 | **FIX** | Regenerated; 0 unmapped, 0 stale ids |
| Parking reasons too thin (F8) | G3 | **FIX** | SD-05, CL-12 reasons rewritten |
| Undefined acronyms, internal code names in text (G2 F1–F11) | G2 | **FIX** | Glossary in the file header; interim actions in plain words; dated negatives in every finding |
| Titles are absolute negatives (G2 F4, F9) | G2 | **CONTEST** | Titles are short labels; each finding carries the dated, scoped claim (stated in the file header) |
| Space framework record pages (§3.2.1 p. 11 → 12; §7.1 p. 32 → 33) (M10) | G1 | **FIX** | Corrected |
| Playbook ids PB-xx undefined (N3) | G1, G2 | **FIX** | Glossary points to docs/plan |

## State after round 1
- KB: 42 records (35 IN, 6 EU, 1 AE), 40 verified quotes, all re-checked against source text. 23 sources, 9 gaps,
  all `candidate`.
- Tests: 43 pass.
- **Round 2 (next):** fresh Goldfish on v3.1, to confirm that no Blocker or Major finding remains open (EGM "clean round").
