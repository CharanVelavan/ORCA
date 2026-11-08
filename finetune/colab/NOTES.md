# Colab notes (Sonnet #1, phase 1 smoke test, 8 Nov 2026)

Runtime: A100-SXM4-40GB (was 80GB earlier in the session; the runtime was re-allocated), Python 3.13.16, CUDA toolkit 13.0.
Model: `unsloth/gemma-4-12b-it` (ungated mirror, loads without a token), 4-bit via `FastModel.from_pretrained(load_in_4bit=True)`; 7.2 GiB loaded.
Versions: unsloth 2026.11.3, unsloth_zoo 2026.11.3, torch 2.14.1+cu130, transformers 5.17.0 (unsloth pins it down from 5.22.1), trl 1.15.0, peft 0.21.2, bitsandbytes 0.50.2. xformers is installed but unusable with this torch (PyTorch attention is used; harmless).
LoRA: r=16, alpha=32, dropout 0, language layers only (attention + MLP), 65.6M trainable (0.55%).

## Chat template facts (Gemma 4)
- Tools are supported natively: `tokenizer.apply_chat_template(msgs, tools=tools)`. Use `tok = tokenizer.tokenizer` (Unsloth returns a Processor).
- `tool_calls[].function.arguments` MUST be a dict. A JSON string is rendered raw and not in Gemma's native `{key:<|"|>value<|"|>}` format. The trainer does `json.loads` on the arguments before rendering. Keep arguments as JSON strings in the data files (SCHEMA is unchanged).
- Tool call, tool response and final answer all sit inside ONE `<|turn>model ... <turn|>` span; there is no turn boundary at the tool result. So `train_on_responses_only` (turn markers) would also train on tool outputs. We use a custom char-span mask instead (see below).
- At inference the generation prompt after a user turn adds an empty thought channel `<|channel>thought\n<channel|>` (thinking off); after a tool response it adds nothing. The training renderer inserts that empty channel after the last `<|turn>model\n`, to match inference. It is masked.
- A tool call ends with `<tool_call|><|tool_response>`; `<|tool_response>` is the stop token. We train through that token.

## Masking (verified)
Unmasked spans: the tool call text up to and including `<|tool_response>`; the final answer through `<turn|>`. Masked: system, tools, user, the thought-channel prefix, tool response body. One sample: 266 tokens, 75 unmasked, decoded pieces were exactly the call and the final answer.

## Smoke train
30 synthetic conversations (SCHEMA format), batch 2 x grad-accum 2, 20 steps, lr 2e-4 linear, adamw_8bit, SFTTrainer with pre-tokenized `input_ids`/`labels` and DataCollatorForSeq2Seq.
Loss: 3.58, 3.54, 3.32, 2.18, 1.54, 1.12, 0.84, 0.58, 0.34, 0.18, 0.16, 0.09, 0.08, 0.08, 0.05, 0.09, 0.06, 0.06, 0.04, 0.05. Peak GPU 8.1 GiB at ~290 tokens. 271 s total (includes compile).

## Export
- Adapter: `/content/drive/MyDrive/orca-ft/smoke/lora` (adapter_model.safetensors + tokenizer + chat_template).
- GGUF: `model.save_pretrained_gguf(dir, tokenizer, quantization_method="q4_k_m")` works first try, about 10 min (merge to 16-bit 22 GiB, bf16 GGUF, quantize). Output `gemma-4-12b-it.Q4_K_M.gguf` 6.87 GiB (+ 0.16 GiB mmproj, not needed for text), copied to `/content/drive/MyDrive/orca-ft/smoke/`.
- llama.cpp (prebuilt b12189, CPU) loads it and, given the training-format prefix, emits the trained tool call and stops at `<|tool_response>`.
- Serving note: the llama.cpp/Ollama chat template must be the Gemma 4 one with tools; the Ollama modelfile mapping for this model was not found by Unsloth.
