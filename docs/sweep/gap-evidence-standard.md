# Gap Evidence Standard (ORCA-NTN, v1, 7 Nov 2026)

The yardstick Goldfish reviewers use to audit the India gap register (`kb/gaps/india.yaml`)
and the sweep results (`docs/sweep/sweep-india*.yaml`). A gap is a claim about the law. It must
survive a sceptical regulator reading it cold.

## A. Every gap must answer these core questions

| # | Question | Fails when |
|---|---|---|
| A1 | **What exactly is missing?** One sentence, narrow and testable. | Broad claims ("India has no satellite cyber law"). |
| A2 | **Where did we look?** `search.sources_checked` lists each source; `terms` lists what was searched. | Sources missing that an Indian regulator would name first (DoT licence conditions, TRAI regulations, CERT-In directions, sector rules). |
| A3 | **What is the nearest provision?** Source, pinpoint, page, exact quote. | No nearest provision, or a quote not in the cited PDF page. |
| A4 | **Why does it not cover the topic?** Binding status, in-force date, scope (who, what), or power-vs-duty. | Reason is opinion, or ignores a provision that does cover it. |
| A5 | **Is it a legal gap, a clarity gap, or a technical-baseline gap?** `kind` is right. | A missing technical control (e.g. anti-replay) presented as a missing law; guidance treated as law. |
| A6 | **Comparison.** At least one EU or UAE (or international standard) provision that does what India lacks, with pinpoint. A proposal is labelled a proposal. | Comparison invented, or a proposal (EU Space Act) presented as law. |
| A7 | **Impact.** Who is harmed, in our NTN scenario terms. | No concrete affected party. |
| A8 | **Action.** Interim action (playbook) and a recommendation naming the regulator and the ask. | No owner, or the ask drafts legislation (we don't draft laws). |
| A9 | **Status honesty.** `status: candidate` until a human confirms. | `confirmed` without `verified_by`. |

## B. Wording rules

- Say "not found in the sources we checked, as of <date>". Never "no law exists" / "India has no …".
- A power ("the Government may …") is not a duty. Say which it is.
- Guidance of unstated or advisory status can make a topic UNCLEAR, never COVERED.
- Do not call a source "binding" or "non-binding" unless the source or an official statement says so; cite it.
- Plain English, short sentences. Quotes exact.

## C. Register-level checks

- C1 No duplicates: two gaps must not claim the same missing thing.
- C2 Coverage: every sweep item with result NOT_FOUND or UNCLEAR either maps to a gap, is merged into one, or
  is explicitly parked with a reason (e.g. "technical control, out of policy scope").
- C3 Proportion: the register should not look like a list of everything India lacks. Prioritise by impact on
  everyday services over NTN (hospitals, payments, 112, power).
- C4 Contradictions: no gap may contradict a KB record that is `verified: true`.
- C5 Leads: claims from `docs/sweep/external-review-7nov.md` are leads. Any gap that relies on one must cite
  the primary document, not the review.

## D. Severity for findings

- **Blocker**: factual error (wrong clause, wrong date, quote not in source), or a gap that a cited provision already covers.
- **Major**: missing core question (A1–A9), overbroad claim, missing obvious source, wrong `kind`.
- **Nit**: wording, style, clarity.
