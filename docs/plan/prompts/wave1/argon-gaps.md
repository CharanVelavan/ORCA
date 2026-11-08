# Task: gap analyst drafts (Mission 9) + agent prompt review — Gemini 4 Argon, ORCA-NTN

{{RULES}}

You write ONLY to kb/gaps/drafts/ (and kb/gaps/drafts/_prompt-review.md). Never edit kb/gaps/india.yaml,
records, agents/roles or code. Only the human confirms gaps; you draft.

## Inputs (read them)
- docs/plan/MASTER_PLAN_v3.md §2-§3 (evaluation: "focus on domain-specific policy gaps and finding relevant
  global policy examples"; "accuracy of the global policy examples is critical").
- kb/gaps/india.yaml: the 9 gaps (7 confirmed, 05 and 07 REJECTED by the human: never revive them).
- kb/india/records.yaml, kb/global/records.yaml: verified records (cite by id).
- kb/staging/{india,global}/*.yaml: staged documents with candidate_quotes (unverified; growing while you
  work); kb/staging/_quotecheck.yaml says which quotes exactly match the source text (result: pass).
- The vector KB, for search records: `cd <repo> && .claude/worktrees/agent-a6a6933ad04d0a87e/.venv/bin/python -m orca.kbvec coverage "<query>" IN`
  with env ORCA_CHROMA_DIR=.claude/worktrees/agent-a6a6933ad04d0a87e/chroma (prints how many docs were
  searched and the nearest clauses). Use it to write each gap's search record.

## Output 1: one draft per confirmed gap: kb/gaps/drafts/GAP-IN-0x.md (01, 02, 03, 04, 06, 08, 09)
Four layers, short plain sentences:
1. Domain gap (NTN cyber security, stated for any country) and a severity score 1-5 with a one-line reason.
2. India evidence: verified record ids with the exact quote; plus staged quotes that passed the quote
   check (mark them "auto-checked, not yet human-verified" with doc id + page). Say what is missing.
3. ≥2 global examples (EU NIS2 / EU Space Act draft / ENISA / US FCC / NIST / UAE TDRA / Australia ASD /
   UK TSA / ITU-T / 3GPP ...): for each, instrument, clause, issuing authority, binding status, exact
   quote from a staged/verified source with page, and how it closes the gap. Only examples whose text you
   actually saw in a source file; mark any you could not verify as "unverified lead".
4. Recommendation at domain level (what a regulator should require), then how it applies to India (which
   authority, which existing power). No drafted legislation.
Plus a "Search record" section: queries run, number of docs searched, nearest clauses and why they don't
close the gap (from `coverage`). Plus "What a human must decide" (1-3 bullets).
Also kb/gaps/drafts/_new-candidates.md: up to 5 NEW candidate gaps you found in the staged corpus
(GNSS interference, SS7/signalling, log retention, etc.), each with evidence; never on topics joint_command
or personal_data_breach.

## Output 2: kb/gaps/drafts/_prompt-review.md
Review agents/roles/*.yaml (role prompts, mandates, sharing limits) as an outside reader: unclear
instructions, mandates that contradict Indian law as recorded in the KB, missing refusals, places the
small local model (Gemma 4 12B) will likely misread. Concrete suggested edits, ranked. Do not edit them.

Work in this order: 09, 02, 08, 01, 03, 04, 06, then candidates, then the prompt review. Re-read staging
before each gap (it grows). Finish with kb/gaps/drafts/_summary.md (what is solid, what is thin).
