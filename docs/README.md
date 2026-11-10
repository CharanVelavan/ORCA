# Documentation index

Start with the [project README](../README.md). All satellite and NTN links in this project are emulated.
The [hosted showcase](https://orca-ntn.vercel.app) provides learning and recorded playback. Use the
[implementation repository](https://github.com/CharanVelavan/ORCA) locally for new exercises and model evaluation.

## Run and reproduce

| Guide | Purpose |
|---|---|
| [Judge reproducibility](JUDGE_REPRODUCIBILITY.md) | Quick start, published model and RAG downloads, endpoints, evaluation and limits |
| [Windows setup](JUDGE_WINDOWS.md) | Windows requirements and launcher instructions |
| [Website guide](../guide.md) | Scenario selection, Console, Policy, Recovery and Audit |
| [Run commands](RUN.md) | Runtime and test commands |
| [Demo walkthrough](DEMO.md) | Demonstration paths and expected evidence |
| [Verification record](JUDGE_VERIFICATION.md) | Tested setup and measured results; platform limitations |

## Understand the implementation

| Reference | Purpose |
|---|---|
| [Vector KB](KBVEC.md) | Corpus, embeddings, hybrid retrieval and evaluation |
| [Network](NETWORK.md) | Emulated topology and network behavior |
| [ORCA role agents](APPLICATION_ROLES.md) | Application agents and their responsibilities |
| [Scenario dimensions](plan/SCENARIO_DIMENSION_COVERAGE.md) | Readiness dimension coverage and evidence boundaries |
| [Submission files](../submission/README.md) | Report and submission artifacts |

The `research/` directory preserves experiment records. Their numbers belong to the stated dataset,
model, endpoint and run; they do not automatically describe a later run.

## Historical planning records

`BUILD_PLAN.md`, `BUILD_PLAN_v2.md`, `HANDOFF_NEXT_CHAT.md`, and most files under `plan/` preserve the
design and implementation history. Old status lists, model choices, PIN requirements and screen layouts
may be superseded. Use the current guides above and the runtime for present behavior. The scenario
coverage and judge readiness records under `plan/` remain useful evidence with their stated scope.

Historical files are retained in place so existing links remain valid. They are not fresh setup instructions.
