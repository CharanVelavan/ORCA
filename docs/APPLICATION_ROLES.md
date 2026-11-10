# ORCA-NTN application roles

The live setup uses the project fine-tuned Qwen3.6-35B-A3B model. See
[Judge reproducibility](JUDGE_REPRODUCIBILITY.md) for the pinned artifact and endpoint setup, and
[Post-submission verification](POST_SUBMISSION_VERIFICATION.md) for the combined Qwen/RAG run.
The Gemma experiments below are historical development evidence.

Code: `orca/agents.py`, `orca/protocol.py`, role files `agents/roles/*.yaml`. Tests: `tests/test_agents.py`,
`tests/test_protocol.py` (mock LLM, no network). Every NTN link is **emulated**.

## Parties
| Role | Kind | Sees (scenario routing) | Tools (A-level cap) | Owns | Sharing limits |
|---|---|---|---|---|---|
| satellite_operator | agent | `vpn_login`, `mgmt_command`, `telemetry_reported`; M1/M3 | all 11 (A2) | PB-01..05, PB-11..14 | no customer/personal data to other operators; personal data only to CERT-In |
| mobile_operator | agent | link, traffic, route offers, battery; M2/M4 | all 11 (A2) | PB-06, 07, 09, 10, PB-15..17 | same |
| power_utility | agent | `mains_power`, `battery_pct`; M2 | no playbook tools (A1) | none | operational, indicators |
| cert_in | agent | only events addressed to it | no playbook tools (A1) | none | the only role that may send a (draft) `legal_direction` |
| regulator (DoT) | agent | only events addressed to it | no playbook tools (A1) | none | inform/request/object only; cannot propose or execute |
| gap_analyst | agent | audit questions addressed to it | no playbook tools (A1) | none | may propose PB-10 to its owner |
| policy_adviser | adviser | the KB only | none; called via `ask_adviser` or `PolicyAdviser.ask` | none | answers only with KB citations |
| commander | human | everything | console: approve/reject, decide gaps | all A3 | - |

A role file holds: mandate, reports_to, max_level, tools, owns, `sees`, `sharing`, notice kinds, prompt, a
worked example. `Role.load` refuses unknown tools, a tool above `max_level`, or a name mismatch.

## What is enforced in code
- **Different information.** `EventFeed` releases scenario events progressively; each event reaches only
  the roles it is routed to (explicit `to:`, else the actor role, else the roles whose `sees` match its
  signals/sources). Attacker/environment events show only the observed signals, never the ground truth.
  Alerts carry `visible_to`; `read_alerts`, `explain_model` and message refs respect it. Inbox = messages
  addressed to the role.
- **Different tools.** Only the role's tools are sent to the LLM; enums are narrowed per role (own
  playbooks, allowed message types, data classes, recipients). Any other call is refused and logged.
- **Protocol** (`orca/protocol.py`): `inform | request | propose | object | approve_request`, sender,
  recipients, refs, data class, playbook, in_reply_to. Checks: known parties, allowed type and data class
  per role, no customer/personal data between operators, personal data only to CERT-In, directions only from
  CERT-In and only as a draft `request`, proposals must reach the playbook owner, approve_request only to
  the commander with a plan hash the sender owns, objections need a message the sender was party to, every
  ref must resolve to evidence the sender may see, no unknown ids in the text. Violations: `msg_rejected`.
- **Trace.** Each tool call and each final answer is an `agent_step` audit entry: model reasoning (when the
  endpoint returns `reasoning_content`), the REQUIRED `rationale` argument (a call without it is refused),
  accepted and rejected citations, and the tool result (with a `next:` hint).
- **Citation check.** Accepted: KB record id, non-rejected gap id, or a chunk id for which
  `orca.kbvec.get_chunk` returns a chunk (no `orca.kbvec` package = chunk ids are rejected). A final answer
  with rejected ids gets one rewrite request; what survives is logged as rejected. Verdict words in the
  final text that the rule engine did not return in that turn are flagged (`verdicts_not_from_engine`).
- **Verdicts and gaps.** Only `run_rule_engine` gives verdicts. `record_gap` makes a *pre-confirmed* draft
  in run state (evidence must pass the citation check; topics of human-rejected gaps are refused);
  `Commander.decide_gap` confirms or rejects. Nothing writes to `kb/`.
- **Execution.** Only `execute_playbook` -> `orca.remediation.Remediation.execute` (owner, assets, one-time
  token, expiry, clone test, fresh verdict, PB-06 India gateway + clean path). The token comes only from
  `Commander.approve`, delivered as a protocol message to the plan owner.
- **Ask the adviser.** Retrieval over records, non-rejected gaps and the vector corpus (if present), with a
  word-overlap relevance gate. No relevant source: "Not found in the sources we checked, as of <kb_as_of>."
  With an LLM, the answer must cite only retrieved ids and contain no verdict word, else it is replaced by a
  direct quote of the sources. Empty responses and exact echoes of the question also trigger this
  source-quote fallback; retrieved citations alone do not make an echoed question an answer.

## Small-model fixes (Gemma 4 12B)
Role-filtered tools; enums on `source`, `site`, `topic`, `type`, `data_class`, `playbook`; `select_playbook`
is described as list-only and its result says "next: request_approval"; `execute_playbook` refusals for a
missing token point to `request_approval`; an empty `read_alerts` filter returns a hint to use `source=any`;
string-for-list arguments are coerced; a short worked example in every role prompt.

## Modes
- `PolicyMockLLM`: deterministic agent (read_alerts -> run_rule_engine -> summary citing engine ids). No network.
- `orca.llm.ScriptedLLM`: fixed replies for tests. `orca.llm.LLMClient` with `LLM_MODE=record|replay` for exact replays.
- `Coordinator(world, llm, commander_policy=...)`: runs a scenario event by event, one agent turn per
  released event, then one round of message delivery. `commander_policy` is the human stand-in for replays.

## Live smoke run (S1, Gemma 4 12B QAT, LM Studio, temperature 0)
Run 8 Nov: `google/gemma-4-12b-qat`, `http://localhost:1234/v1`, max_tokens 1200. A scripted commander
approved executable plans that passed the clone test, and only at the T+43 commander event. Wall time:
1183 s for 16 agent turns (68 steps). Audit chain intact.
- **Information isolation held.** The satellite operator got T+0/4/8/18, the mobile operator T+24/55/78,
  the gap analyst T+12/36 and CERT-In T+30. CERT-In also got turns from messages sent to it. The regulator
  and power utility received nothing, which is correct for S1.
- **Tool choice:** 0 refusals for tools outside the allow-list, 0 missing rationales, 0 bad arguments and 0
  protocol rejections across 15 messages. Each `select_playbook` was followed by `request_approval` (the
  weak spot from the Codex smoke test did not recur). CERT-In sent its directions as draft
  `request`/`legal_direction`, as the role file says.
- **Citations:** 0 rejected. Every final answer cited real record or gap ids. CERT-In quoted the engine's
  AMBIGUITY with GAP-IN-01. No verdict words were found that did not come from the engine.
- **Gaps:** the gap analyst pre-confirmed space_cyber (GAP-IN-09 evidence records) and downstream_warning.
  Weak spot: its downstream_warning evidence was one space-framework record, not GAP-IN-02.
- **Execution:** PB-10 ran after approval (warning on the bus to 112, hospital and payments). PB-01 was
  **refused, "approval expired"**: the plan was requested at T+8, its 30-minute expiry counts from the request
  time, and the commander approved at T+43. The guard worked. Afterwards the mobile operator reused its
  spent PB-10 token, and the one-time check refused it.
- **Misses:** the mobile operator did not request PB-06 at T+55 (verified path B offered), so no failover
  happened. The satellite operator asked for PB-01 three times (same plan hash). The gap analyst wrote
  "Propose PB-10" without the `playbook` field; the agent now fills that field from the text, so the owner
  check applies. One final answer was empty (after a refusal). 17 of 68 steps came back with
  `reasoning_content` (Gemma returns it only on some turns).

## Patches for the lead
1. **`orca/llm.py` keeps model reasoning** (needed for the trace; agents already read it):
   ```diff
   -        return {"role": "assistant", "content": m.get("content"), "tool_calls": m.get("tool_calls") or []}
   +        return {"role": "assistant", "content": m.get("content"), "tool_calls": m.get("tool_calls") or [],
   +                "reasoning_content": m.get("reasoning_content") or m.get("reasoning")}
   ```
   `Agent.run` never sends `reasoning_content` back to the model.
2. **`scenarios/SCHEMA.md`**: document the optional event key `to: [roles]` (explicit release list for
   `EventFeed`), and that attacker/environment events reach agents only as observed signals.
3. **`orca/world.py`**: document the alert keys `t`, `actor`, `sites`, `signals`, `visible_to`
   (`visible_to: None` = everyone, for simulator alerts that predate routing).
