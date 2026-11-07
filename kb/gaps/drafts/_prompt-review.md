# Outside-Reader Review of Agent Role Prompts (`agents/roles/*.yaml`)

**Scope:** Review of all 8 role definitions in `agents/roles/*.yaml` (`satellite_operator.yaml`, `mobile_operator.yaml`, `power_utility.yaml`, `cert_in.yaml`, `regulator.yaml`, `gap_analyst.yaml`, `policy_adviser.yaml`, `commander.yaml`), cross-checked against:
- Verified Indian and global records in `kb/india/records.yaml`, `kb/global/records.yaml`, and `kb/gaps/india.yaml`
- Staged Indian and global instruments in `kb/staging/{india,global}/*.yaml`
- Deterministic runtime guards in `orca/agents.py`, `orca/protocol.py`, `orca/remediation.py`, `orca/rules.py`, `orca/world.py`, and `playbooks/catalogue.yaml`
- Empirical tool-calling failures observed on local `google/gemma-4-12b-qat` in `docs/research/gemma4-smoke/gemma_smoke_report.md`

> **Note:** Per Mission 9 rules, no files in `agents/roles/*.yaml` or `orca/` were modified. All suggested edits below are provided as drop-in replacements for human review.

---

## Executive Summary of Findings

1. **Direct Contradictions / Omissions Against Indian Law in the KB (3 High-Severity Issues):**
   - **Missing Authz Rule 37(5) (`IN-AUTHZ-2026-R37-5`) check before inter-operator or downstream network sharing:** Both `satellite_operator.yaml` and `mobile_operator.yaml` instruct the agent to share operational/technical network information with other operators and dependent services (`PB-10`), calling the warning *"voluntary (no binding duty found)"*, without mentioning that **Rule 37(5) of the Telecommunications (Authorisation) Rules, 2026 (`IN-AUTHZ-2026-R37-5`)** prohibits sharing *"any information relating to its telecommunication network with any other person except with the prior approval of the Central Government in writing"* (proviso only for equipment suppliers/manufacturers). In contrast, `kb/gaps/india.yaml` (`GAP-IN-02` `interim_action`) explicitly requires *"checking whether Rule 37(5) approval is needed"*.
   - **Incomplete statutory clocks and rogue-terminal duties in `regulator.yaml` and `satellite_operator.yaml`:** `regulator.yaml` mentions only TCSR Rule 7(1)(a) (`IN-TCSR-2024-7-1-a`) and the CTI clock (`IN-CTIR-2024-9-1-e`), omitting: (a) the **24-hour TRAI SNO major outage clock** (`IN-TRAI-QOS-2024-4-1-3`, plus 72-hour RCA), and (b) the **unclocked DoT portal reporting duties** for rogue radio signals (`IN-AUTHZ-2026-R59-4`) and terminal/telemetry security breaches (`IN-AUTHZ-2026-R62-7`).
   - **Log-retention split (`IN-CERTIN-DIR-2022-iv` 180-day vs. staged `in-ctir-2024` Rule 5(1)(d) 2-year) absent from `cert_in.yaml` and `satellite_operator.yaml`:** Neither prompt warns that high-impact actions (`PB-04` beam/link isolation, `PB-05` management-plane containment) must preserve ICT logs in India for 180 days (`IN-CERTIN-DIR-2022-iv`) and Critical Telecommunication Infrastructure (CTI) logs/prompts for 2 years (`in-ctir-2024` Rule 5(1)(d)).

2. **Schema-vs-Prompt Contradictions that Trap `Gemma 4 12B` (3 High-Severity Issues):**
   - **`sharing.may_share` exposes `customer_data` and `personal_data` in the JSON tool schema for operators:** In `orca/agents.py` (line 200), `tool_schemas()` populates `send_message.parameters.properties.data_class.enum` directly from `role.sharing["may_share"]`. Because `satellite_operator.yaml` and `mobile_operator.yaml` both list `may_share: [operational, technical_indicator, customer_data, personal_data]`, `Gemma 4 12B` sees `customer_data` and `personal_data` as valid enum choices whenever it calls `send_message`. If it sends `customer_data` to another operator or `personal_data` to anyone other than `cert_in`, `Protocol.validate()` (`orca/protocol.py` lines 200–205) rejects the message (`msg_rejected`). Worse, `mobile_operator.yaml`'s text prompt says *"Customer data never goes to another operator"* but **forgets to mention `personal_data`**.
   - **`read_alerts` worked examples in `mobile_operator.yaml` and `power_utility.yaml` teach the exact filter failure observed in the `Gemma 4 12B` smoke test:** In `docs/research/gemma4-smoke/gemma_smoke_report.md` (lines 37–45, 93–106), `Gemma 4 12B` failed 3/3 runs on the multi-turn fault-vs-attack case because it called `read_alerts(site="CHN-03")` without `source="M3"`. Both `mobile_operator.yaml` (line 35: `read_alerts(source="any", site="CHN-02")`) and `power_utility.yaml` (line 29: `read_alerts(source="any", site="CHN-05")`) reinforce this exact mistake in their worked examples.
   - **`select_playbook` vs. `request_approval` confusion (0/3 pass rate on `no_token` in smoke test):** In `gemma_smoke_report.md` (lines 46–48, 108–121), when asked to act on a playbook without an approval token, `Gemma 4 12B` called `select_playbook(goal="PB-06")` 3/3 times instead of calling `request_approval` or explicitly refusing `execute_playbook`. Both `satellite_operator.yaml` and `mobile_operator.yaml` include `select_playbook` in `tools:` without telling the model: *"When asked to run or prepare a specific playbook (e.g. PB-01, PB-06, PB-10) and you have no approval token, call `request_approval` directly—do NOT call `select_playbook` first."*

3. **Workflow, Ownership, and Asset-ID Mismatches (4 Medium-Severity Issues):**
   - **Undocumented asset ID `SAT-MGMT` for `PB-02` and `PB-05` in `satellite_operator.yaml`:** `orca/world.py` (line 20) hardcodes `DEFAULT_ASSETS["satellite_operator"] = {"mgmt_account": ["*"], "mgmt_system": ["SAT-MGMT"], "terminal": ["*"]}`. `satellite_operator.yaml` tells the model to use `sat-ops-17` for `PB-01`, but never tells it that `PB-02` and `PB-05` (`target_kind: mgmt_system`) require `targets=["SAT-MGMT"]` and will be refused by `Remediation._check_owner()` (`orca/remediation.py` line 280) if any other target string is passed.
   - **Non-executable playbooks (`PB-02`, `PB-03`, `PB-04`, `PB-05`, `PB-07`, `PB-09`) listed in `owns` without execution guidance:** In `playbooks/catalogue.yaml`, only `PB-01`, `PB-06`, and `PB-10` have `executable: true`. The other playbooks have `executable: false` ("specified only, not executable"). `request_approval` works on them (logging a plan and checking conflicts), but `execute_playbook` always raises `Refused`. The prompts do not explain this distinction.
   - **`PB-10` workflow mismatch between `gap_analyst.yaml`, `mobile_operator.yaml`, and `kb/gaps/india.yaml`:** `kb/gaps/india.yaml` (`GAP-IN-02` line 104) says `owner: satellite_operator` for `PB-10`, whereas `playbooks/catalogue.yaml` (line 66) and `mobile_operator.yaml` assign `PB-10` to `mobile_operator`. Furthermore, `gap_analyst.yaml` has `downstream_warning` in `notice_kinds` and its mandate says *"Draft the PB-10 downstream warning for the mobile operator"*, but its worked example skips `draft_notice(kind="downstream_warning")` and only calls `send_message(type="propose", playbook="PB-10")`.
   - **Worked example errors in `gap_analyst.yaml` and `power_utility.yaml`:**
     - `gap_analyst.yaml` line 33 shows `record_gap(..., evidence=["GAP-IN-02-NO-DOWNSTREAM-WARNING"])`, omitting the verified `IN-*` record IDs (`IN-CERTIN-DIR-2022-v`, `IN-TCSR-2024-7-1-a`, `IN-AUTHZ-2026-R37-5`) that its own prompt (line 25) and `orca/agents.py` (`NEXT["run_rule_engine"]`) require.
     - `power_utility.yaml` line 32 ends with `Final: "Grid fault at CHN-05. Citations: none"`, violating `COMMON_RULES` (`Citations: <ids>`) and failing to cite `IN-CEA-2020-8-11` or `GAP-IN-04-NO-BATTERY-FLOOR`.
     - `cert_in.yaml` and `regulator.yaml` include `read_alerts` in `tools:` even though `sees: signals: [], sources: []` means `read_alerts` always returns `[]` (`orca/agents.py` lines 215–216).

---

## Ranked Concrete Issues & Suggested Edits

### Rank 1 (Critical — Legal Accuracy & KB Alignment): Missing Authz Rule 37(5) (`IN-AUTHZ-2026-R37-5`) Refusal / Approval Gate on Network Information Sharing

- **Files affected:** `agents/roles/mobile_operator.yaml`, `agents/roles/satellite_operator.yaml`, `agents/roles/gap_analyst.yaml`, `agents/roles/regulator.yaml`
- **Problem:**
  - `IN-AUTHZ-2026-R37-5` (Telecommunications (Authorisation) Rules, 2026, Rule 37(5), in force, verified) states:
    > *"Every new authorised entity shall not share any information relating to its telecommunication network with any other person except with the prior approval of the Central Government in writing: Provided that nothing in this sub-rule shall apply to the sharing of information by an authorised entity with the telecommunications equipment suppliers or manufacturers for the purpose of resolving network security-related issues."*
  - Neither `mobile_operator.yaml` nor `satellite_operator.yaml` mentions `IN-AUTHZ-2026-R37-5`. Instead, `mobile_operator.yaml` states: *"When a site has hospital, 112, payment or grid dependants and the Gap Analyst proposes PB-10, request approval to warn them; the warning is voluntary (no binding duty found)."*
  - While `GAP-IN-02-NO-DOWNSTREAM-WARNING` confirms there is no mandatory downstream warning duty, `kb/gaps/india.yaml` (lines 105–107) explicitly requires the `PB-10` interim action to proceed *"after checking whether Rule 37(5) approval is needed"*.
- **Suggested Edit (`agents/roles/mobile_operator.yaml` prompt lines 26–28):**
  ```yaml
    When a site has hospital, 112, payment or grid dependants and the Gap Analyst proposes PB-10,
    request approval to warn them; the warning is voluntary (GAP-IN-02-NO-DOWNSTREAM-WARNING),
    and you must note in your reason and message that sharing network information outside equipment
    suppliers requires checking whether Central Government written approval is needed under
    IN-AUTHZ-2026-R37-5.
    Customer or personal data never goes to another operator; personal_data goes only to cert_in.
  ```
- **Suggested Edit (`agents/roles/satellite_operator.yaml` prompt lines 27–28):**
  ```yaml
    Check the KB before citing any rule. Customer or personal data never goes to another operator;
    personal_data may go only to cert_in in an incident report. When sharing network information with
    another operator or dependant, state only high-level impact or indicators and note that detailed
    network-information sharing requires prior written Central Government approval under IN-AUTHZ-2026-R37-5.
  ```

---

### Rank 2 (Critical — `Gemma 4 12B` Tool Accuracy): Fix `select_playbook` vs. `request_approval` Trap in Operator Prompts

- **Files affected:** `agents/roles/satellite_operator.yaml`, `agents/roles/mobile_operator.yaml`
- **Problem:**
  - In `docs/research/gemma4-smoke/gemma_smoke_report.md` (lines 46–48, 108–121), `Gemma 4 12B` failed 3/3 runs on `no_token` because when told to act on a playbook (`PB-06`) without an approval token, it called `select_playbook(goal="PB-06")` instead of `request_approval(...)` or an explicit refusal.
  - Why? Because `satellite_operator.yaml` and `mobile_operator.yaml` expose `select_playbook` alongside `request_approval` and `execute_playbook`, and say *"Never call execute_playbook without a one-time approval token from the human commander; ask with request_approval first."* When a prompt names a playbook ID (`PB-01`, `PB-06`, `PB-10`) and says "no approval token has been issued", `Gemma 4 12B` treats `select_playbook` as a "safe lookup" step instead of directly calling `request_approval`.
- **Suggested Edit (`agents/roles/satellite_operator.yaml` & `agents/roles/mobile_operator.yaml`):**
  Add an explicit disambiguation rule to both prompts:
  ```yaml
    If a playbook id (such as PB-01, PB-06, or PB-10) and its target are already known and you have
    no valid commander approval token, call request_approval directly (or refuse execute_playbook);
    do NOT call select_playbook when the playbook id is already known. Use select_playbook only when
    you do not know which playbook id matches a general goal.
    Never call execute_playbook with an unverified, expired, or guessed token.
  ```

---

### Rank 3 (Critical — `Gemma 4 12B` Tool Accuracy): Fix `read_alerts` Filter Examples (`source="M3"` vs. `source="any"`)

- **Files affected:** `agents/roles/mobile_operator.yaml`, `agents/roles/power_utility.yaml`, `agents/roles/satellite_operator.yaml`
- **Problem:**
  - In `docs/research/gemma4-smoke/gemma_smoke_report.md` (lines 37–45, 93–106), `Gemma 4 12B` failed 3/3 runs on `multi` Turn 1 (`source: expected 'M3', got None`) because it called `read_alerts(site="CHN-03")` without setting `source="M3"`.
  - Look at the worked examples in `mobile_operator.yaml` (line 35) and `power_utility.yaml` (line 29):
    - `mobile_operator.yaml`: `1. Call read_alerts(source="any", site="CHN-02").`
    - `power_utility.yaml`: `1. Call read_alerts(source="any", site="CHN-05").`
  - Teaching `source="any"` whenever a site is mentioned causes `Gemma 4 12B` to omit `source="M3"` when asked to check the fault-vs-attack classifier (`M3`), or to miss `M3` alerts when filtering narrowly.
- **Suggested Edit (`agents/roles/mobile_operator.yaml` lines 22, 34–36 & `agents/roles/power_utility.yaml` lines 19, 28–30):**
  - In `mobile_operator.yaml`:
    ```yaml
    prompt: |
      You are the Mobile Operator NOC agent for the Chennai 5G network (sites CHN-01..CHN-06) with
      emulated NTN backhaul. Start with read_alerts: pass source="M3" (and site="CHN-0x") whenever
      checking fault-vs-attack classification, or source="M2" for transport/KPI anomalies. If M3
       shows an attack or low confidence, call explain_model on that alert.
    ```
    And update `example` in `mobile_operator.yaml`:
    ```yaml
    example: |
      Task: "Check fault-vs-attack classification on CHN-02 and prepare a reroute to path B."
      1. Call read_alerts(source="M3", site="CHN-02").
      2. Call explain_model(alert_id="<M3 alert id>").
      3. Call query_kb(query="gateway in India traffic routing", jurisdiction="IN").
      4. Call request_approval(playbook="PB-06", targets=["CHN-02"], params={"path": "B"}, reason="Reroute CHN-02 to verified Indian gateway path B per IN-AUTHZ-2026-R60-1-b").
      5. Final: state the M3 verdict, the request hash, and "Citations: IN-AUTHZ-2026-R60-1-b".
    ```
  - In `power_utility.yaml`:
    ```yaml
    prompt: |
      You are the Power Utility agent for the Chennai grid serving sites CHN-01..CHN-06. Start with
      read_alerts: pass source="M3" when checking whether an outage is a grid fault or a cyber attack,
      and call explain_model on the M3 alert so you can tell the other roles which features drove the
      fault-vs-attack call.
    ```

---

### Rank 4 (High — Schema & Protocol Safety): Restrict `sharing.may_share` or Add Strict Recipient-by-Class Rules in Operator Prompts

- **Files affected:** `agents/roles/satellite_operator.yaml`, `agents/roles/mobile_operator.yaml`
- **Problem:**
  - Both files declare:
    ```yaml
    sharing:
      may_send: [inform, request, propose, object, approve_request]
      may_share: [operational, technical_indicator, customer_data, personal_data]
      may_propose_playbooks: true
    ```
  - In `orca/protocol.py` (lines 200–205):
    - An operator may **never** send `customer_data` or `personal_data` to another operator (`satellite_operator`, `mobile_operator`, `power_utility`).
    - Any role may send `personal_data` **only** to `cert_in` (`if m.data_class == "personal_data" and any(r != "cert_in" for r in m.recipients): no(...)`).
  - However, in `mobile_operator.yaml`, the prompt only says *"Customer data never goes to another operator"*—it omits that `personal_data` can **only** go to `cert_in` (not even to `regulator`, `gap_analyst`, or `policy_adviser`)! And in both operator roles, `send_message` defaults to `operational`, while incidents go to CERT-In via `draft_notice(kind="cert_in_6h")`, not `send_message(data_class="personal_data")`.
- **Suggested Edit:**
  1. Either remove `customer_data, personal_data` from `sharing.may_share` in `satellite_operator.yaml` and `mobile_operator.yaml` (unless a scenario specifically tests `send_message` with `personal_data` to `cert_in`), **or**
  2. Explicitly state the exact `Protocol.validate` matrix in both prompts:
     ```yaml
     In send_message, always use data_class="operational" or "technical_indicator" when messaging
     operators, regulator, gap_analyst, policy_adviser, or commander. Never send customer_data to
     another operator (satellite_operator, mobile_operator, power_utility), and never send
     personal_data to any recipient except cert_in.
     ```

---

### Rank 5 (High — Runtime Asset Refusal Bug): Specify `SAT-MGMT` Target ID and Executable vs. Specified-Only Playbooks in `satellite_operator.yaml`

- **Files affected:** `agents/roles/satellite_operator.yaml`
- **Problem:**
  - `orca/world.py` (line 20) defines:
    ```python
    DEFAULT_ASSETS = {
        "satellite_operator": {"mgmt_account": ["*"], "mgmt_system": ["SAT-MGMT"], "terminal": ["*"]},
        ...
    }
    ```
  - In `playbooks/catalogue.yaml`:
    - `PB-01` (`target_kind: mgmt_account`, `executable: true`): accepts any account name (`"*"`), e.g. `["sat-ops-17"]`.
    - `PB-02` (`target_kind: mgmt_system`, `executable: false`): accepts **only** `["SAT-MGMT"]`!
    - `PB-03` (`target_kind: terminal`, `executable: false`): accepts any terminal ID (`"*"`), e.g. `["TERM-CHN-01"]`.
    - `PB-04` (`target_kind: terminal`, `executable: false`): accepts any terminal ID (`"*"`).
    - `PB-05` (`target_kind: mgmt_system`, `executable: false`): accepts **only** `["SAT-MGMT"]`!
  - Because `satellite_operator.yaml` says *"Use account names such as sat-ops-17 as targets for PB-01"* and says nothing about targets for `PB-02`..`PB-05`, `Gemma 4 12B` will pass site names (`["CHN-01"]`) or account names (`["sat-ops-17"]`) to `PB-02` or `PB-05`, causing `Remediation._check_owner` to throw `Refused: target ... is not in satellite_operator's assets`!
  - Furthermore, `satellite_operator.yaml` does not mention that `PB-02`, `PB-03`, `PB-04`, and `PB-05` are `executable: false` (specified-only in the catalogue: you may call `request_approval` or propose them to test rule conflicts such as `PB-05` vs `PB-06`, but `execute_playbook` will always refuse them).
- **Suggested Edit (`agents/roles/satellite_operator.yaml` prompt lines 20–28):**
  ```yaml
    Never call execute_playbook without a one-time approval token from the human commander; ask with
    request_approval first. Only PB-01 is executable in the simulator (use account names such as
    ["sat-ops-17"] as targets). PB-02, PB-03, PB-04, and PB-05 are specified-only (never call
    execute_playbook on them, though you may call request_approval or propose them):
    - For PB-02 and PB-05 (target_kind: mgmt_system), always use targets=["SAT-MGMT"].
    - For PB-03 and PB-04 (target_kind: terminal), use terminal ids (or site terminal ids).
    PB-04 and PB-05 are high impact: PB-05 (Isolate management plane) conflicts with PB-06 reroutes
    (rule IN-R-CONFLICT-CONTAIN-VS- CONTINUITY) and must preserve 180-day ICT logs in India
    (IN-CERTIN-DIR-2022-iv). Always explain that trade-off to the commander.
  ```

---

### Rank 6 (High — Worked Example Bug): Fix `gap_analyst.yaml` Example so `record_gap` Includes Verified `IN-*` Record IDs and `PB-10` Uses `draft_notice`

- **Files affected:** `agents/roles/gap_analyst.yaml`
- **Problem:**
  1. In `gap_analyst.yaml`, the prompt (line 25) instructs:
     > *"For each POTENTIAL_GAP or AMBIGUITY verdict, call record_gap with the engine's gap id and record ids as evidence"*
     And `orca/agents.py` (`NEXT["run_rule_engine"]`, line 48) instructs:
     > *"if any verdict is POTENTIAL_GAP or AMBIGUITY, call record_gap (gap_id = the verdict's gap_id, evidence = the record ids and gap id shown)"*
     Yet the worked example in `gap_analyst.yaml` (line 33) shows:
     ```yaml
     3. Call record_gap(gap_id="GAP-IN-02-NO-DOWNSTREAM-WARNING", topic="downstream_dependants_warning", statement="No binding Indian duty to warn dependent services.", evidence=["GAP-IN-02-NO-DOWNSTREAM-WARNING"]).
     ```
     Because `Gemma 4 12B` copies the structure of the few-shot `example:` block verbatim, it will pass only the gap ID in `evidence` and omit the verified `IN-*` record IDs (`IN-CERTIN-DIR-2022-v`, `IN-TCSR-2024-7-1-a`, `IN-AUTHZ-2026-R37-5`)!
  2. Furthermore, `gap_analyst.yaml` declares `notice_kinds: [downstream_warning]` and its mandate says *"Draft the PB-10 downstream warning for the mobile operator"*, but its prompt and example never tell it when to call `draft_notice(kind="downstream_warning", ...)` vs. `send_message(type="propose", playbook="PB-10", ...)`.
  3. Finally, note the cross-file inconsistency between `kb/gaps/india.yaml` line 104 (`GAP-IN-02` `interim_action.owner: satellite_operator`) and `playbooks/catalogue.yaml` line 66 (`PB-10` `owner: mobile_operator`). In `orca/protocol.py` (line 220), `Protocol.validate` checks `self.rem.cat[m.playbook]["owner"]`, which is `mobile_operator`. So `gap_analyst.yaml` addressing `PB-10` to `mobile_operator` matches `catalogue.yaml`, but the prompt should remind the Gap Analyst to include the warning message text and cite `IN-AUTHZ-2026-R37-5`.
- **Suggested Edit (`agents/roles/gap_analyst.yaml` lines 25–37):**
  ```yaml
    For each POTENTIAL_GAP or AMBIGUITY verdict, call record_gap with the engine's gap id and both
    the gap id and the checked IN-* record ids as evidence, then query_kb for EU or AE records on
    the same topic if comparative context is requested. When downstream services (hospital, 112,
    payments, grid) depend on an affected site, call draft_notice(kind="downstream_warning", ...)
    and propose PB-10 to mobile_operator with the warning text and a note to check IN-AUTHZ-2026-R37-5.
    Never revive a gap marked rejected by a human (GAP-IN-05-PERSONAL-DATA-BREACH, GAP-IN-07-JOINT-COMMAND).
  example: |
    Task: "Check whether Indian law requires warning downstream dependants and record any gap."
    1. Call run_rule_engine(jurisdiction="IN", obligation_questions=[{"id": "Q1", "topic": "downstream_dependants_warning"}]).
    2. Call query_kb(query="downstream dependants warning notification", jurisdiction="IN").
    3. Call record_gap(gap_id="GAP-IN-02-NO-DOWNSTREAM-WARNING", topic="downstream_dependants_warning", statement="No binding Indian duty to warn dependent services found in checked sources; check IN-AUTHZ-2026-R37-5 before sharing network details.", evidence=["GAP-IN-02-NO-DOWNSTREAM-WARNING", "IN-CERTIN-DIR-2022-v", "IN-TCSR-2024-7-1-a", "IN-AUTHZ-2026-R37-5"]).
    4. Call send_message(to=["mobile_operator"], type="propose", playbook="PB-10", refs=["GAP-IN-02-NO-DOWNSTREAM-WARNING", "IN-AUTHZ-2026-R37-5"], text="Propose PB-10: warn hospital and 112 dependants of degraded backhaul (voluntary under GAP-IN-02-NO-DOWNSTREAM-WARNING; check IN-AUTHZ-2026-R37-5 approval).").
    5. Final: state the gap finding and "Citations: GAP-IN-02-NO-DOWNSTREAM-WARNING, IN-CERTIN-DIR-2022-v, IN-TCSR-2024-7-1-a, IN-AUTHZ-2026-R37-5".
  ```

---

### Rank 7 (Medium — Legal Completeness): Expand `regulator.yaml` to Cover All DoT / TRAI / IN-SPACe Instruments in the KB

- **Files affected:** `agents/roles/regulator.yaml`, `agents/roles/cert_in.yaml`
- **Problem:**
  - `regulator.yaml` currently says:
    > *"Look up IN-TCSR-2024-7-1-a (6-hour notice after becoming aware, 24-hour details) and the CTI clock with query_kb and run_rule_engine; draft the DoT notice with draft_notice (kind dot_6h) and inform the commander."*
  - It completely misses:
    1. **TRAI QoS Regulation 2024 (`IN-TRAI-QOS-2024-4-1-3`):** 24-hour major SNO outage reporting clock to TRAI (plus 72-hour root cause analysis) when an outage affects all services in a district/sub-division for >4 hours.
    2. **Authz Rules 2026 Rule 60(1)(b) (`IN-AUTHZ-2026-R60-1-b`):** Prohibition on routing domestic Indian traffic through a gateway outside India (needed so the Regulator can object if an operator proposes a foreign gateway route!).
    3. **Authz Rules 2026 Rule 59(4) (`IN-AUTHZ-2026-R59-4`) and Rule 62(7) (`IN-AUTHZ-2026-R62-7`):** Duty to report rogue signals, rogue terminals, and telemetry/navigation breaches to the Central Government on the portal (unclocked — `GAP-IN-09-SAT-OPERATOR-DUTIES`).
    4. **IN-SPACe May 2026 Cybersecurity Framework (`IN-PIB-2026-SPACEFW-ADVISORY`, `IN-SPACEFW-2026-SDLS`):** Advisory status not stated on its face (`AMBIGUITY` verdict in rule engine).
  - Additionally, both `regulator.yaml` and `cert_in.yaml` list `read_alerts` in `tools:` even though both have `sees: signals: [], sources: []`, so `read_alerts` always returns `[]` (`orca/agents.py` lines 215–216) and wastes a tool turn if `Gemma 4 12B` calls it!
- **Suggested Edit (`agents/roles/regulator.yaml`):**
  - Remove `read_alerts` from `tools:` (or note in the prompt: *"You have no direct telemetry feed (`sees: []`); rely on facts in the task or messages from operators, not `read_alerts`."*).
  - Expand the prompt:
    ```yaml
    prompt: |
      You are the DoT / TRAI / IN-SPACe Regulator Liaison agent. You track telecom, QoS, and space
      sector obligations:
      - DoT TCSR 2024 Rule 7(1)(a) (IN-TCSR-2024-7-1-a: 6-hour notice from awareness, 24-hour details)
      - DoT CTI Rules 2024 Rule 9(1)(e) (IN-CTIR-2024-9-1-e: 6-hour CTI incident report from occurrence,
        3-hour on Critical National Entity request)
      - TRAI QoS Regulations 2024 (IN-TRAI-QOS-2024-4-1-3: 24-hour SNO major outage notice to TRAI)
      - Authz Rules 2026 (IN-AUTHZ-2026-R60-1-b: no routing Indian traffic via foreign gateways;
        IN-AUTHZ-2026-R59-4 and IN-AUTHZ-2026-R62-7: report rogue signals/terminals on the portal;
        IN-AUTHZ-2026-R37-5: prior written Central Government approval before sharing network info)
      - IN-SPACe 2026 Space Cybersecurity Framework (IN-PIB-2026-SPACEFW-ADVISORY, IN-SPACEFW-2026-SDLS:
        binding status not stated, treated as AMBIGUITY).
      Use run_rule_engine and query_kb, draft the DoT notice with draft_notice (kind dot_6h), and
      object via send_message(type="object") if any proposed plan routes domestic traffic through a
      foreign gateway or violates a statutory clock. Never propose or execute network playbooks.
    ```

---

### Rank 8 (Medium — Citation Rule Violation in Worked Example): Fix `power_utility.yaml` `Citations: none` and `PB-09` Guidance

- **Files affected:** `agents/roles/power_utility.yaml`
- **Problem:**
  1. `orca/agents.py` (`COMMON_RULES`, line 25) mandates:
     > *"End your final answer with `Citations: <ids>` listing only ids that appeared in tool results this turn."*
     Yet `power_utility.yaml` line 32 says:
     ```yaml
     4. Final: "Grid fault at CHN-05. Citations: none".
     ```
     If `power_utility` never queries the KB, it never cites `IN-CEA-2020-8-11` (10-hour battery backup floor for grid communication links), `IN-TRAI-QOS-2024-3-2` (power outages excluded from cell-availability uptime), or `GAP-IN-04-NO-BATTERY-FLOOR` (no mandatory battery reserve floor for mobile towers/NTN terminals) when reporting battery depletion!
  2. `power_utility.yaml` says: *"Load shedding (PB-09) belongs to the mobile operator: send it a request if needed, never try to run a playbook yourself."* However, `PB-09` is `executable: false` in `playbooks/catalogue.yaml`, and `power_utility` has `may_propose_playbooks: false` (so it must use `type="request"` with `playbook=None` or `playbook="PB-09"`, never `type="propose"`).
- **Suggested Edit (`agents/roles/power_utility.yaml`):**
  ```yaml
  prompt: |
    You are the Power Utility agent for the Chennai grid serving sites CHN-01..CHN-06. Start with
    read_alerts(source="M3") and call explain_model on the M3 alert so you can tell the other roles
    which features drove the fault-vs-attack call. Report feeder trips, voltage state and battery
    hours left to the mobile operator and the commander using send_message(type="inform" or "request").
    When battery reserve is relevant, call query_kb(query="battery backup power outage tower",
    jurisdiction="IN") to cite IN-CEA-2020-8-11, IN-TRAI-QOS-2024-3-2, or GAP-IN-04-NO-BATTERY-FLOOR.
    Load shedding (PB-09) belongs to mobile_operator: send a request message (never type="propose")
    if load shedding is needed, and never try to run a playbook yourself.
  example: |
    Task: "Check power alerts at CHN-05 and tell the mobile operator."
    1. Call read_alerts(source="M3", site="CHN-05").
    2. Call explain_model(alert_id="AL-01").
    3. Call query_kb(query="battery backup power outage", jurisdiction="IN").
    4. Call send_message(to=["mobile_operator"], type="inform", refs=["AL-01", "IN-CEA-2020-8-11", "GAP-IN-04-NO-BATTERY-FLOOR"], text="Grid fault at CHN-05; tower on battery (no telecom battery floor under GAP-IN-04-NO-BATTERY-FLOOR; grid comms 10h floor under IN-CEA-2020-8-11).").
    5. Final: "Grid fault at CHN-05 reported to mobile_operator. Citations: IN-CEA-2020-8-11, GAP-IN-04-NO-BATTERY-FLOOR".
  ```

---

### Rank 9 (Low — Defensive Guardrails): Add Rejected-Gap and State-Attribution Refusals to `policy_adviser.yaml` and `commander.yaml`

- **Files affected:** `agents/roles/policy_adviser.yaml`, `agents/roles/commander.yaml`
- **Problem:**
  - `gap_analyst.yaml` says *"Never revive a gap marked rejected by a human"*, and `cert_in.yaml` says *"Never attribute an attack to a state or actor"*.
  - However, `policy_adviser.yaml` and `commander.yaml` do not repeat these two explicit refusals in their role prompts (relying only on `COMMON_RULES` in `orca/agents.py`). Repeating the exact rejected gap IDs (`GAP-IN-05-PERSONAL-DATA-BREACH` and `GAP-IN-07-JOINT-COMMAND`) in `policy_adviser.yaml` and `commander.yaml` prevents `Gemma 4 12B` from proposing policy options on personal data breach or joint command if prompted by an adversarial or ambiguous user query.
- **Suggested Edit (`agents/roles/policy_adviser.yaml` & `agents/roles/commander.yaml`):**
  - Append to `policy_adviser.yaml` prompt:
    ```yaml
    Never recommend options for rejected gaps (GAP-IN-05-PERSONAL-DATA-BREACH, GAP-IN-07-JOINT-COMMAND),
    never attribute an attack to a state or actor, and never draft statutory or legislative text.
    ```
  - Append to `commander.yaml` prompt:
    ```yaml
    Never approve or propose a foreign gateway route (IN-AUTHZ-2026-R60-1-b), never revive rejected
    gaps (GAP-IN-05-PERSONAL-DATA-BREACH, GAP-IN-07-JOINT-COMMAND), and never attribute an attack to
    a state or actor.
    ```

---

## Summary Matrix by Role File

| Role File | Clear Mandate? | Contradicts / Omits Indian Law in KB? | Missing Refusals? | `Gemma 4 12B` Misread Risk | Priority |
|---|---|---|---|---|---|
| `satellite_operator.yaml` | Mostly clear; missing `SAT-MGMT` target ID & executable vs specified-only split | Omits `IN-AUTHZ-2026-R37-5` (network info sharing approval), `IN-AUTHZ-2026-R59-4`/`R62-7` (portal reporting), and `IN-CERTIN-DIR-2022-iv` (180-day logs) | Missing refusal to call `select_playbook` when playbook ID is already given without token; `may_share` exposes `customer_data`/`personal_data` | **High** (`select_playbook` trap on `no_token`; `Refused` on `PB-02`/`PB-05` if target != `SAT-MGMT`) | **P0** |
| `mobile_operator.yaml` | Clear on `PB-06` and `IN-AUTHZ-2026-R60-1-b` | Calls `PB-10` warning "voluntary" without citing `IN-AUTHZ-2026-R37-5` check; prompt omits `personal_data` restriction | Missing refusal on `personal_data` to non-`cert_in`; missing refusal to call `select_playbook` when playbook ID is known | **High** (`example` uses `read_alerts(source="any")`, causing `multi` Turn 1 failure in smoke test) | **P0** |
| `gap_analyst.yaml` | Clear on gap workflow; minor ambiguity on `draft_notice(downstream_warning)` vs `PB-10` | None, though `PB-10` proposal should cite `IN-AUTHZ-2026-R37-5` | Explicitly refuses rejected gaps (`GAP-IN-05`, `GAP-IN-07`) | **High** (`example` passes only `["GAP-IN-02-..."]` to `record_gap.evidence`, omitting `IN-*` records) | **P1** |
| `regulator.yaml` | Too narrow (mentions only TCSR 7(1)(a) & CTI clock) | Omits `IN-TRAI-QOS-2024-4-1-3` (24h TRAI clock), `IN-AUTHZ-2026-R60-1-b`, `R59-4`, `R62-7`, and `IN-PIB-2026-SPACEFW-ADVISORY` | Missing explicit instruction to `object` (`type="object"`) to foreign gateway or clock-violating plans | **Medium** (`read_alerts` is in `tools:` despite `sees: []`, risking wasted empty tool calls) | **P1** |
| `power_utility.yaml` | Clear on grid fault & battery reporting | Omits `IN-CEA-2020-8-11` (10h grid comms battery floor) and `GAP-IN-04-NO-BATTERY-FLOOR` | Clear on not running playbooks | **Medium** (`example` uses `read_alerts(source="any")` and ends with `Citations: none`) | **P1** |
| `cert_in.yaml` | Clear on 6h clock (`IN-CERTIN-DIR-2022-v`) and clock clash (`IN-R-CLOCK-01`) | Omits `IN-CERTIN-DIR-2022-iv` (180-day ICT log retention in India) vs CTI 2-year logs | Strong refusals (never attribute; legal directions are human-issued drafts only) | **Low-Medium** (`read_alerts` in `tools:` despite `sees: []`) | **P2** |
| `policy_adviser.yaml` | Clear on domain-level options and citing verified records | None | Add explicit refusal for rejected gaps `GAP-IN-05` & `GAP-IN-07` and state attribution | **Low** (`example` is clean and matches `NEXT` hints) | **P2** |
| `commander.yaml` | Clear on sitrep synthesis and waiting for human PIN approval | None | Add explicit refusal for foreign gateway `GW-XX` and rejected gaps `GAP-IN-05` & `GAP-IN-07` | **Low** (`example` is clean) | **P2** |
