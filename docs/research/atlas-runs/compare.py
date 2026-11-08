import json
q=json.load(open('summary.json')); g=json.load(open('summary-gemma-ft.json'))
def f(d,k):
    v=d.get(k)
    if not v: return "not run"
    if not v.get("ok"): return "ERR"
    return f"{v['found']}/{v['expected']}"
def m(d,k,key):
    v=d.get(k) or {}; return v.get(key,"-")
print("| Scenario | Rules | Qwen found | Gemma-ft found | Gemma min (Qwen min) | Gemma tool refusals | Gemma cit. rejected | Gemma approvals req. | Gemma executed |")
print("|---|---|---|---|---|---|---|---|---|")
tq=tg=0;ft=0;fe=0
for sc in ["S0","S1","S2","S3","N1","N2","N3","N4","N5","CAP"]:
    for r in ("rules","norules"):
        k=f"{sc}-{r}"
        print(f"| {sc} | {'on' if r=='rules' else 'off'} | {f(q,k)} | {f(g,k)} | {m(g,k,'minutes')} ({m(q,k,'minutes')}) | {m(g,k,'tool_refusals')} | {m(g,k,'citations_rejected')} | {m(g,k,'approvals_requested')} | {m(g,k,'executed')} |")
        if r=="rules" and g.get(k,{}).get("ok") and sc in("S0","S1","S2","S3","N1","N2","N3"):
            ft+=g[k]["found"]; fe+=g[k]["expected"]
print("\nGemma rules-on S0-S3,N1-N3:",ft,"/",fe)
for r in ("rules","norules"):
    print(r,"total found (all run):",sum(v.get('found',0) for k,v in g.items() if k.endswith("-"+r) and v.get('ok')),"/",sum(v.get('expected',0) for k,v in g.items() if k.endswith("-"+r) and v.get('ok')))
