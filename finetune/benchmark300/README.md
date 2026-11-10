# Frozen 300-case model comparison

This archive closes the missing-input gap for the **8 November 2026 rebuilt comparison**, whose
fine-tuned Qwen first-tool result is 279/300 (93%). It does not prove row identity with the earlier
Colab sample. The recovered files were already stored under ignored `models/llm/qwen-ft/evals/`;
they have been copied without changing the case file or historical raw responses.

## Verify and rescore without inference

From the repository root:

```sh
python finetune/benchmark300/verify.py
```

The verifier checks SHA-256 hashes, 300 unique IDs, embedded prompts/tools/labels, response counts,
and the first-tool accuracy of all four historical models. No predicted tool executes. Historical raw
responses have no IDs; their index is matched to the archived case order used by `historical-eval_wrap.py`.
That association is provenance from the archived runner, not an independent attestation.

## Run fresh inference on exactly these requests

Set `LLM_API_KEY` in the environment only if required. Use the exact endpoint model ID:

```sh
python finetune/benchmark300/run.py --model YOUR_SERVED_MODEL \
  --base-url http://127.0.0.1:8000/v1 --output output/benchmark300-fresh
```

The output directory must not already exist. Each response is flushed to `responses.jsonl` with its
case ID; the final result includes settings, wall time and independently computed scores. Failed or
interrupted runs retain partial responses and do not receive a completed result. This is fresh
inference, not a claim of identical floating-point output across hardware or server versions.

## Files and limits

- `cases_subset300_tools.jsonl`: all IDs, system/user/tool messages, exact tool schemas and labels.
- `case_ids.json`: IDs in request order. These are not the separate 100 training-validation IDs.
- Four `*.raw.json` files: archived assistant responses and per-request durations.
- Four matching result files: untouched historical metrics.
- `settings.json`: documented inference settings, model revision, weight hash and hardware context.
- `historical-*`: original evaluation wrapper, serving scripts, client and scorer for inspection.
  Their machine-specific paths are historical; use `run.py` for a portable rerun.
- `sha256.json`: integrity manifest for frozen historical inputs.

The historical metric counts cases without an expected first tool as correct: 36/300 cases.
Restricting the tuned Qwen score to explicit first-tool labels yields **243/264 (92.05%)**.
The old scorer hard-coded `valid_json`; the new verifier actually parses every predicted argument
object (251/251 for tuned Qwen). `unsafe_exec=0` in the old result means zero forbidden predicted
calls on these cases; **no execution was tested by this benchmark**. Historical `bad_citations`
counts missing expected citations in the first response, not verified hallucinations. Refusal and
final-text measures contain vacuous cases. Scenario verdict placeholders were never evaluated.
The exact historical llama.cpp build and inference RNG seed were not retained. The archive supports
exact request reconstruction and score reproduction from raw responses, not bit-for-bit inference.
