# Live console API examples

The live console controls only the **emulated** Chennai network.  All command
examples omit the commander PIN deliberately: callers supply it over HTTP, but
it is neither recorded nor returned.  Error responses have the shape
`{"ok": false, "error": "safe explanation"}`.

## HTTP endpoints

`GET /api/state`

```json
{"ok":true,"t":12,"running":true,"sites":{"CHN-01":{"state":"ok"}},"scheduled":[],"last_seq":42}
```

`GET /api/catalogue`

```json
{"ok":true,"scenarios":[{"id":"s1","title":"..."}],"sites":{"CHN-01":{}},"gateways":{"GW-IN-1":{}},"accounts":["noc-vendor-7"],"playbooks":[{"id":"PB-01"}],"injectors":[{"id":"rain","category":"fault"}]}
```

`GET /api/stream?since=41` (SSE)

```text
data: {"seq":42,"t":12,"ts":"2026-11-10T19:12:00+05:30","kind":"tick","sites":{}}
```

`GET /api/truth` (Exercise Control only; ground truth is not released to agents)

```json
{"ok":true,"injections":[{"id":"INJ-001","kind":"jamming","truth_class":"attack-jamming","start":12,"detected_at":12,"time_to_detect":0,"contained_at":null,"time_to_contain":null,"healed_at":12,"time_to_heal":0}]}
```

`GET /api/replay?file=runs/live-20261108-190000-s1-rules-mock.jsonl`

```json
{"ok":true,"events":[{"seq":1,"t":0,"ts":"2026-11-10T19:00:00+05:30","kind":"run_meta","scenario":"s1","emulated":true}]}
```

`POST /api/session`

```json
{"scenario":"s1","llm":"mock","rules":true,"kb":"india","autoplay":false,"sync":true}
```

`POST /api/clock`

```json
{"action":"play","speed":2}
```

`POST /api/inject`

```json
{"kind":"rain","target":"CHN-01","duration_min":10,"params":{"peak":35}}
```

`POST /api/schedule`

```json
{"kind":"jamming","target":"CHN-02","at_t":25,"duration_min":8,"params":{"j_over_n_db":10}}
```

`DELETE /api/schedule/SCH-001`

```json
{"ok":true,"id":"SCH-001"}
```

`POST /api/autonomy`

```json
{"mode":"AUTO","sites":["CHN-02"],"playbooks":["PB-06"],"minutes":20,"pin":"<redacted>"}
```

`POST /api/approve`

```json
{"hash":"plan-hash","pin":"<redacted>"}
```

`POST /api/reject`

```json
{"hash":"plan-hash","reason":"Exercise controller declined the emulated change"}
```

`POST /api/kill`

```json
{"pin":"<redacted>","reason":"Exercise pause"}
```

`POST /api/kill/release`

```json
{"pin":"<redacted>"}
```

`POST /api/order`

```json
{"to":"satellite_operator","text":"Assess the emulated alert and explain the safest next action."}
```

`POST /api/ask`

```json
{"to":"policy_adviser","question":"Which reporting clock should the commander review?"}
```

`POST /api/rules`

```json
{"on":false}
```

`POST /api/kb`

```json
{"kb":"eu"}
```

`POST /api/gap`

```json
{"gap_id":"GAP-IN-001","decision":"confirm","pin":"<redacted>"}
```

## Event kinds

Every SSE object has `seq`, simulation minute `t`, ISO simulation timestamp
`ts`, and `kind`.  Events that include exercise ground truth carry
`"audience":"control"`; console clients must not pass those to agents.

| Kind | Example JSON |
| --- | --- |
| `session` | `{"kind":"session","scenario":"s1","llm":"mock","rules":true,"emulated":true}` |
| `tick` | `{"kind":"tick","sites":{"CHN-01":{"state":"degraded","active_path":"A"}},"gateways":{"GW-IN-1":"up"},"paths":[]}` |
| `inject` | `{"kind":"inject","audience":"control","id":"INJ-001","injector":"rain","truth_class":"fault-weather","target":"CHN-01","start":4,"end":14,"by":"human:commander"}` |
| `scheduled` | `{"kind":"scheduled","audience":"control","id":"SCH-001","injector":"rain","target":"CHN-01","at_t":20,"duration_min":10}` |
| `model` | `{"kind":"model","model":"M3","site":"CHN-01","class":"fault-weather","confidence":0.9,"top_features":[]}` |
| `alert` | `{"kind":"alert","id":"LIVE-M3-CHN-01-0004","source":"M3","site":"CHN-01","label":"fault-weather","visible_to":["satellite_operator"]}` |
| `agent_task` | `{"kind":"agent_task","role":"satellite_operator","task":"Assess alert LIVE-M3-CHN-01-0004."}` |
| `agent_step` | `{"kind":"agent_step","role":"satellite_operator","tool":"read_alerts","args":{},"result":{},"rationale":"Review the emulated alert."}` |
| `agent_final` | `{"kind":"agent_final","role":"satellite_operator","text":"Assessment complete.","citations":[]}` |
| `agent_busy` | `{"kind":"agent_busy","role":"satellite_operator","busy":true,"queue":1}` |
| `msg` | `{"kind":"msg","from":"mobile_operator","to":["commander"],"type":"inform","data_class":"operational","text":"Emulated site degraded.","accepted":true}` |
| `verdict` | `{"kind":"verdict","verdict":"COMPLIANT","rule":"RULE-01","topic":"incident_reporting","records":["IN-CERT-001"]}` |
| `clock_obligation` | `{"kind":"clock_obligation","regime":"CERT-In 6 h","started_at":"2026-11-10T19:00:00+05:30","due_at":"2026-11-11T01:00:00+05:30","status":"open","trigger":"awareness"}` |
| `approval` | `{"kind":"approval","status":"requested","playbook":"PB-01","owner":"satellite_operator","targets":["noc-vendor-7"]}` |
| `execute` | `{"kind":"execute","playbook":"PB-01","targets":["noc-vendor-7"],"result":"ok"}` |
| `heal` | `{"kind":"heal","site":"CHN-02","from_path":"A","to_path":"B","check":{"clean":true,"checks":[]}}` |
| `patch_stage` | `{"kind":"patch_stage","playbook":"PB-11","pct":25,"health":"ok"}` |
| `rollback` | `{"kind":"rollback","hash":"plan-hash","why":"health check failed"}` |
| `reattack` | `{"kind":"reattack","playbook":"PB-11","attack":"management login","blocked":true}` |
| `autonomy` | `{"kind":"autonomy","mode":"AUTO","scope":{"sites":["CHN-02"],"playbooks":["PB-06"]},"expires_at":"2026-11-10T19:20:00+05:30","by":"commander"}` |
| `kill` | `{"kind":"kill","engaged":true,"by":"commander","reason":"Exercise pause","tokens_revoked":1}` |
| `gap` | `{"kind":"gap","gap_id":"GAP-IN-001","title":"Example gap","status":"candidate","india":"Record summary","global_examples":[],"recommendation":"Human review."}` |
| `phase` | `{"kind":"phase","active":["predict","report"],"latest":"report"}` |
| `impact` | `{"kind":"impact","real":{"emulated_estimate":true,"payments_failed":0},"shadow":{"emulated_estimate":true,"payments_failed":20}}` |
| `clock_waiting` | `{"kind":"clock_waiting","reason":"Agents deciding"}` |
| `clock_resumed` | `{"kind":"clock_resumed","reason":"Agent queue drained"}` |
| `error` | `{"kind":"error","where":"agent:satellite_operator","message":"safe failure detail"}` |

