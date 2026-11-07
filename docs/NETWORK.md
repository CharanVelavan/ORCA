# ORCA-NTN network side: simulator, posture scanner, config as code, models, playbooks

Missions 5 and 6 (Opus B, 8 Nov 2026). **Everything is emulated.** No real network, device, vendor
code or exploit is used. Attacks are simulated conditions with observable effects only. Re-attack tests
are logical attack-graph checks on the emulated configs.

## 1. How to run

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt
python3 -m orca.scanner                    # posture of the committed netconfig/ (stdlib + pyyaml only)
python3 -m orca.sim.demo [--diffs]         # scan -> PB-12/11/13/14/15/06 -> re-scan -> re-attack -> rollback
.venv/bin/python -m orca.models.train      # trains M1-M3, evaluates M1-M4, writes orca/models/metrics.json (~20 s)
ORCA_TURKCELL_DIR=<folder with rl-kpis.tsv> .venv/bin/python -m orca.models.m2_daily   # M2 daily tier (real data)
.venv/bin/python -m pytest -q              # all tests; test_models.py is skipped without lightgbm/sklearn/scipy
```

From code (what the runner and dashboard call):
```python
from orca.sim.scenario import ScenarioRun
from orca.models.detector import Detector
from orca.sim import netops
run = ScenarioRun("s1", world=world, detector=Detector.load())   # world and detector are optional
run.step_to(30)                          # simulate minutes 0..30; returns {role: [alerts released this call]}
ops = netops.attach(world, sim=run.sim)  # world.health = ops.health; world.netops = ops
```

## 2. Simulator (`orca/sim/`)

| File | What |
|---|---|
| `topology.py` | 6 Chennai sites (SCHEMA table), gateways `GW-IN-1` (primary), `GW-IN-2` (backup), `GW-XX` (outside India, `allowed: False`), link budgets (ASSUMED), services and M4 priority |
| `physics.py` | ITU-R P.838-3 from `data/itu_p838_3_coefficients.csv` (exact rows, log-log interpolation, polarisation and elevation per eqs. 4-5); **simplified** P.618 slant path (horizontal reduction factor only); **simplified** older P.530 hop factor; jamming SINR = S/(N+J) |
| `engine.py` | `Simulator(seed)`: deterministic, one record per site per minute (`RECORD_KEYS`), ground-truth label. Conditions: rain, scintillation, power_cut, equipment_fault, gateway_power, jamming, mgmt_intrusion (KA-SAT chain: anomalous VPN login, config changes, wipe, terminals down), telemetry_edit, gnss_spoof, ss7_abuse, surge, roaming_surge. Scenario pins override observed signals. `path_report()` feeds the clean-path check |
| `scenario.py` | `ScenarioRun`: maps scenario signals (SCHEMA names only) to conditions and pins; releases events **through `agents.EventFeed`** (explicit `to:`, else actor, else `sees`). Model alerts are routed with `EventFeed.route({"actor": "M1".., "signals": []})`, i.e. to roles whose `sees.sources` list the model. With a `World`, facts merge, `world.routes` gets the route candidates, and alerts land in `world.alerts` |
| `netstate.py` | `NetState`: `netconfig/*.yaml` in memory; `unified()` diffs; snapshot and restore |
| `netops.py` | `apply_playbook`, `verify`, `rollback`, `clone_test`, `check_path_clean`, `verify_routes`, `NetOps.health` (the `World.health` hook), `attach` |
| `attacks.py` | Re-attack tests: `ka_sat_chain`, `default_cred_login`, `feeder_intercept`, `firmware_exploit`, `foreign_failover` |
| `dataset.py` | Training episodes; `train` and **harder** `heldout` ranges (weaker jammers, low-and-slow intrusions, weak spoofers, more confounders) |
| `demo.py` | Patch demo CLI |

Scenario mapping notes: `snr_db` becomes jamming only when the scenario is `attack-jamming` and there is no rain. A routine `config_change` in a `fault-power/equipment` scenario (N2) becomes an equipment fault, not an intrusion. All 10 scenarios simulate; M3 (via the detector) gives the scenario's story label at each affected site.

## 3. Posture scanner and config as code

`netconfig/`: one YAML per emulated device (SAT-MGMT, GW-IN-1, GW-IN-2, GW-XX, TERM-CHN-01..05,
CHN-01..06) plus `baseline.yaml` (ASSUMED hardening baseline). Credentials are vault references, never
values. `orca/scanner.py` is read only. Each finding has id, check, severity, asset, owner role,
evidence (config path and value) and the fixing playbook.

**Default posture (before): 13 findings: 3 critical, 7 high, 1 medium, 2 low**

| Severity | Asset | Finding | Playbook |
|---|---|---|---|
| critical | SAT-MGMT | VPN reachable from the whole internet (0.0.0.0/0) | PB-12 |
| critical | SAT-MGMT | Management interface exposed to the internet | PB-12 |
| critical | SAT-MGMT | `admin` still on factory-default credentials | PB-11 |
| high | SAT-MGMT | MFA not enforced (noc-vendor-7, admin, telemetry-srv) | PB-11 |
| high | GW-IN-1 | Feeder link unencrypted and unauthenticated | PB-13 |
| high | TERM-CHN-01, -02, -05 | Firmware below 3.2.0 | PB-14 |
| high | TERM-CHN-02 | Accepts unsigned firmware/commands | PB-14 |
| high | CHN-03 | Failover path C via GW-XX allowed (Authz Rule 60(1)(b)) | PB-06 |
| medium | SAT-MGMT | Credentials older than 90 days | PB-11 |
| low | CHN-01, CHN-05 | No battery-saving profile at a hospital/112 site | PB-15 |

The KA-SAT chain re-attack **succeeds** on the default posture.

**After PB-12, PB-11, PB-13, PB-14, PB-15, PB-06: 0 findings**; every re-attack fails and names the
blocking step (KA-SAT chain blocked at "reach VPN from the internet"; with PB-11 alone, at "log in
with a weak or stolen credential"). Rollback restores the exact text (13 findings again).

## 4. Playbooks (`playbooks/catalogue.yaml`)

New: PB-11 rotate credentials + MFA, PB-12 close VPN/management interface, PB-13 feeder-link
encryption, PB-14 firmware in waves, PB-15 battery-saving mode, PB-16 pre-stage clean backup path from
M2, PB-17 re-attack watch. Extended: PB-01, PB-06 (network fields). Each has owner, target_kind,
preconditions, `netconfig` (what the diff changes), `sim_action`, `verification` (re-scan checks and
re-attack), `rollback`, `closes`. The fields remediation reads (id, title, owner, executable,
target_kind, params) are unchanged in form.

**PB-06 clean-path check** (`netops.check_path_clean`), all must pass: path exists; gateway in India
(Authz Rule 60(1)(b)); gateway not `forbidden`; not jammed (noise floor); no equipment fault; gateway
up; management plane not compromised (KA-SAT lesson: while the operator's management network is under
an uncontained intrusion, every satellite path it manages is suspect, including the backup gateway);
feeder link encrypted (satellite paths); integrity probe not `failed`. A `failed` integrity is never
upgraded.

**Staging:** at `pct` %, a playbook applies to ceil(n x pct / 100) of the sorted targets (PB-14 waves).
`NetOps.health` applies each stage's new targets, runs `verify` at 100 % (re-scan + re-attack) and on
any failure rolls back everything it applied and returns False (`params.simulate_failure_at: 25`
demonstrates a rollback). It contains the management intrusion in the simulator after PB-01/11/12.

## 5. Models (`orca/models/`, metrics in `orca/models/metrics.json`)

Synthetic data from the simulator, seed 7; 53,200 training windows. Test sets: in-distribution
(unseen seeds) and **held-out harder** (other seeds and harder ranges). The in-distribution scores are
near 1.0 because the data are physics-generated; **quote the held-out numbers**.

**M3 fault-vs-attack** (LightGBM, 8 outputs = 7 classes + abstain; abstain thresholds calibrated
on a held-out-range split disjoint from the test: tau 0.90, target precision 0.99). Held-out harder,
n = 26,600: accuracy 0.971 without abstain; **coverage 0.983, accuracy on answered 0.987, abstain 1.7 %**.

| Class | Precision | Recall |
|---|---|---|
| normal | 0.996 | 1.000 |
| fault-weather | 0.922 | 1.000 |
| fault-power/equipment | 1.000 | 0.841 |
| attack-jamming | 1.000 | 0.897 |
| attack-management-plane | 1.000 | 0.984 |
| attack-gnss | 1.000 | 1.000 |
| attack-signalling | 1.000 | 0.994 |

Main error: weak jamming (J/N 2.5-7 dB) under rain read as fault-weather (253 of 2,838 windows), i.e.
weather as the attacker's alibi; equipment faults abstained or read as weather. Explanations are
LightGBM TreeSHAP (`pred_contrib`), as plain-word features ("noise floor rise=14.98").

**M1 anomaly** (Isolation Forest + ECOD, flag = either above its 99.75th-percentile threshold).
In-distribution: false alarms 0.53 % of normal site-minutes, AUC IF 0.90 / ECOD 0.996. Held-out
harder: false alarms 2.3 %, detection 60-100 % by class (GNSS 99.8 %, jamming 60 %, management plane
61 %). Isolation Forest alone detects only ~22 %: it cannot split on features that are constant in
normal data (mains power, wipe commands); ECOD catches those. That is why both are in the flag.

**M2 minute tier** (hybrid: physics time-to-failure + LightGBM quantile residual P10/P50/P90 +
split-conformal). Held-out harder, n = 15,595: MAE of P50 4.31 min vs physics baseline 4.29 min (equal:
the ML adds a calibrated interval, not point accuracy, on physics-generated data); P10-P90 coverage
0.925, mean width 8.7 min; recall of "fails within 30 min" 0.959; false forecast (<60 min) on links
that do not fail 3.4 %. Output names the exposure (dependants) and the pre-emptive playbooks
(PB-16/PB-06 for links, PB-15/PB-10 for power).

**M2 daily tier** (real Turkcell `rl-kpis.tsv`, time split at 2020-06-01, RLF within 3 days, no
weather features): ROC-AUC 0.57, PR-AUC 0.0053 vs base rate 0.00245, precision in the top 1 % 0.015
(about 6x lift). Weak; it calibrates fault behaviour only (Turkey microwave links, not Chennai, not
satellite). `orca/models/metrics_daily.json`.

**M4 capacity** (SciPy `milp`/HiGHS; admission binaries with lexicographic priority weights; strict
priority constraint: a lower service at a site gets capacity only if every higher one there is
admitted; greedy fallback). Storm case (two sites share a 60 Mbps gateway, 100 Mbps demand): 112 and
hospital fully served; general load shed. A randomised test checks that 112 is never shed while
payments or general traffic get capacity.

**Detector** (`detector.py`): alerts on change only (M1 rising edge, new M3 label, M2 countdown under
60 min with physical evidence), 10-minute hysteresis. M1 anomaly + M3 "normal" below 0.99 = abstain.

## 6. What is stubbed or simplified
- Physics: simplified P.618 and P.530 (stated above); rain height 5 km and link budgets are ASSUMED.
- GNSS and SS7 are summary statistics per minute (C/N0 mean/spread, AGC, clock offset, position jump;
  message rate, location-query rate, foreign share), not protocol traces.
- Re-attack tests are attack-graph checks on config, not traffic replay.
- Neighbour-cell compensation: not built (first in the cut order).
- No MQTT; the simulator is called in-process.
- M2 daily tier has no weather join (met-real.tsv not used).
- Scenarios N2/N3 run in the simulator; N3 (audit) has no incident, so M3 says normal, not abstain.

## 7. Patches for the lead

I did not edit `orca/world.py`, `orca/remediation.py`, `orca/rules.py`, `agents/roles/` or `scenarios/`.
Checked: this diff applies with `patch -p1` and the whole suite passes on a patched copy (153 passed);
PB-13 then executes end to end (clone test passes, re-scan clean, feeder re-attack blocked).

1. **`orca/world.py` + `orca/remediation.py`** (diff below): gateway assets for `satellite_operator`
   (PB-13; never GW-XX); a `netops` field on World; `clone_test` runs `netops.clone_test` (apply +
   verify on a clone of configs and simulator) for network playbooks and the measured clean-path check
   for PB-06, and refuses a network playbook when no emulated network is attached (today it would
   "succeed" with no effect); `_rollout` returns the per-stage diffs and the verify result as
   `network`, so they reach the audit.
2. **`agents/roles/*.yaml`** (Opus A): add PB-11, PB-12, PB-13, PB-14 to `satellite_operator.owns` and
   PB-15, PB-16, PB-17 to `mobile_operator.owns` (test_agents checks the owner match).
3. **`scenarios/check_scen.py` / `SCHEMA.md`**: `EXEC_OK` allows only PB-01/06/10; add PB-11..17 if a
   scenario should show a patch as executed. Optional signal names for GNSS/SS7 scenarios
   (`gnss_spoof`, `ss7_abuse`) if wanted; the simulator already models them as conditions.
4. **Hard limits**: PB-14 on three terminals at three sites exceeds a blast-radius cap of 2 sites per
   action; count per wave, or have agents split it into two approvals.
5. **Auto-downgrade**: an M3 alert with `explain.abstained: true` (or label `abstain`) is the M3-doubt
   signal for AUTO → ASSISTED.
6. **EventFeed stand-in**: `alert_for` marks model events "scenario stand-in"; with
   `ScenarioRun(..., detector=Detector.load())` real M1/M2/M3 alerts (with explanations) are appended
   to `world.alerts`, routed by the same `EventFeed.route`.

```diff
--- a/orca/world.py
+++ b/orca/world.py
@@ -17,7 +17,8 @@
 
 # Who owns what (emulated). execute_playbook refuses targets outside the caller's list.
 DEFAULT_ASSETS = {
-    "satellite_operator": {"mgmt_account": ["*"], "mgmt_system": ["SAT-MGMT"], "terminal": ["*"]},
+    "satellite_operator": {"mgmt_account": ["*"], "mgmt_system": ["SAT-MGMT"], "terminal": ["*"],
+                           "gateway": ["GW-IN-1", "GW-IN-2"]},     # never GW-XX (Authz Rule 60(1)(b))
     "mobile_operator": {"site": ["CHN-01", "CHN-02", "CHN-03", "CHN-04", "CHN-05", "CHN-06"]},
     "power_utility": {"grid": ["GRID-CHN"]},
 }
@@ -44,6 +45,7 @@
     drafts: list = field(default_factory=list)          # notices drafted by agents (a human sends)
     gap_drafts: list = field(default_factory=list)      # record_gap output (a human reviews; never kb/)
     health: object = None                               # callable(targets, playbook, params, stage_pct) -> bool; simulator hook
+    netops: object = None                               # orca.sim.netops.NetOps (set by orca.sim.netops.attach)
 
     def __post_init__(self):
         if self.kb is None:
--- a/orca/remediation.py
+++ b/orca/remediation.py
@@ -129,6 +129,18 @@
 
     def clone_test(self, pb: dict, targets: list[str], params: dict) -> dict:
         """Run the plan's preconditions on a copy of the state. Nothing real changes."""
+        from orca.sim import netops as _net
+        if pb["id"] in _net.NET_PLAYBOOKS and pb["id"] not in ("PB-06", "PB-01"):
+            if self.w.netops is None:
+                return {"passed": False, "detail": "no emulated network attached (orca.sim.netops.attach)"}
+            return _net.clone_test(self.w.netops.net, pb["id"], targets, params, self.w.netops.sim)
+        if pb["id"] == "PB-06" and self.w.netops is not None:
+            for site in targets:      # measured clean-path checks (jamming, compromised mgmt, feeder, ...)
+                r = _net.check_path_clean(site, params.get("path"), self.w.netops.net, self.w.netops.sim,
+                                          route=self.w.routes.get(site, {}).get(params.get("path")))
+                if not r["clean"]:
+                    bad = [x["check"] for x in r["checks"] if not x["ok"]]
+                    return {"passed": False, "detail": f"{site}: path {params.get('path')} not clean: {bad}"}
         if pb["id"] == "PB-06":
             path = params.get("path")
             for site in targets:
@@ -148,11 +160,17 @@
     # ------------------------------------------------------------ effects
     def _rollout(self, caller: str, pb: dict, targets: list[str], params: dict) -> dict:
         stages = []
+        ops = self.w.netops
+        seen = len(ops.records) if ops is not None else 0
         for pct in STAGES:
             ok = self.w.health(targets, pb["id"], params, pct) if self.w.health else True
             stages.append({"pct": pct, "healthy": bool(ok)})
             if not ok:
-                return {"ok": False, "stages": stages, "detail": f"health check failed at {pct} %, rolled back"}
+                net = ops.records[seen:] if ops is not None else []
+                return {"ok": False, "stages": stages, "network": net,
+                        "detail": f"health check failed at {pct} %, rolled back"}
+        if ops is not None:
+            network = ops.records[seen:]      # diffs per stage + verify (re-scan, re-attack) -> audit
         if pb["id"] == "PB-01":
             self.w.disabled_accounts.update(targets)
         elif pb["id"] == "PB-06":
@@ -162,4 +180,7 @@
             to = sorted({d for s in targets for d in DEPENDANTS.get(s, [])})
             self.w.bus.append({"at": self.w.now, "sender": caller, "to": to, "kind": "warning",
                                "payload": {"sites": targets, "message": params["message"]}})
-        return {"ok": True, "stages": stages, "detail": "rolled out 5/25/100 %"}
+        out = {"ok": True, "stages": stages, "detail": "rolled out 5/25/100 %"}
+        if ops is not None:
+            out["network"] = network
+        return out
```

## 8. Open issues
- Weak jamming under rain is the main M3 error (the "weather alibi"); more training on mixed
  jamming + rain, or a physics rule (noise rise > 2 dB with rain present → abstain), would help.
- The M1 held-out false-alarm rate (2.3 %) is high for 24/7 use; tune per site or add a persistence rule.
- The demand model (35 % of primary capacity at nominal load) is ASSUMED; S2's 112 overload comes from
  scenario pins, not physics.
- Lightgbm on macOS needs libomp (it worked here with the wheel); Docker needs `libgomp1`.
- `models/orca_models.pkl` is a gitignored cache; `load_or_train()` retrains if it is missing (~20 s).
