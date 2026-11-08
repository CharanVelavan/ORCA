"""Table: tuned Qwen vs tuned Gemma vs base Qwen. Run from this folder: python3 compare_qwen_ft.py"""
import json
q=json.load(open('summary.json')); g=json.load(open('summary-gemma-ft.json')); t=json.load(open('summary-qwen-ft.json'))
def f(d,k):
    v=d.get(k)
    if not v: return "not run"
    if not v.get("ok"): return "ERR"
    return f"{v['found']}/{v['expected']}"
def m(d,k,key):
    v=d.get(k) or {}; return v.get(key,"-")
print("| Scenario | Rules | Qwen-ft found | Gemma-ft found | Base Qwen found | Qwen-ft min | Gemma-ft min | Base Qwen min | Qwen-ft tool refusals | Qwen-ft cit. rejected | Qwen-ft approvals | Qwen-ft executed | Qwen-ft agent steps | Gemma-ft agent steps |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for sc in ["S0","S1","S2","S3","N1","N2","N3","N4","N5","CAP"]:
    for r in ("rules","norules"):
        k=f"{sc}-{r}"
        print(f"| {sc} | {'on' if r=='rules' else 'off'} | {f(t,k)} | {f(g,k)} | {f(q,k)} | {m(t,k,'minutes')} | {m(g,k,'minutes')} | {m(q,k,'minutes')} | {m(t,k,'tool_refusals')} | {m(t,k,'citations_rejected')} | {m(t,k,'approvals_requested')} | {m(t,k,'executed')} | {m(t,k,'agent_steps')} | {m(g,k,'agent_steps')} |")
for name,d in (("Qwen-ft",t),("Gemma-ft",g),("Base Qwen",q)):
    for r in ("rules","norules"):
        ks=[v for k,v in d.items() if k.endswith("-"+r) and v.get('ok')]
        print(f"{name} {r}: found {sum(v['found'] for v in ks)}/{sum(v['expected'] for v in ks)} over {len(ks)} runs; minutes {round(sum(v['minutes'] for v in ks),1)}; executed {sum(v['executed'] for v in ks)}; citations rejected {sum(v['citations_rejected'] for v in ks)}; tool refusals {sum(v['tool_refusals'] for v in ks)}")
