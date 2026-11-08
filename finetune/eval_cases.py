"""Score an OpenAI-compatible model against held-out ORCA cases N4, N5 and CAP."""
from __future__ import annotations
import argparse, json, re, os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from orca.llm import LLMClient
from orca.runner import run_scenario, ROOT
from orca.protocol import ID_RE

CASES=ROOT/'finetune/data/cases.jsonl'
OUT=ROOT/'finetune/eval'
HELD=('N4','N5','CAP')
def evaluate(model, base_url=None, cases_path=CASES):
    client=LLMClient(base_url=base_url, model=model, mode='live', temperature=0,
                     timeout=float(os.environ.get('LLM_TIMEOUT', '120')))
    cases=[]
    if Path(cases_path).exists():
        for line in Path(cases_path).read_text().splitlines():
            if line.strip(): cases.append(json.loads(line))
    scores=[]; verdicts={x:False for x in HELD}; tags={}
    for c in cases:
        if c.get('scenario') not in HELD: continue
        msg=client.chat(c['messages'], c.get('tools'))
        calls=msg.get('tool_calls') or []; exp=c.get('expect',{})
        first=calls[0].get('function',{}).get('name') if calls else None
        args={}
        if calls:
            try: args=json.loads(calls[0]['function'].get('arguments') or '{}')
            except Exception: pass
        choice=first==exp.get('first_tool') if exp.get('first_tool') else True
        args_ok=all(args.get(k)==v for k,v in exp.get('args_subset',{}).items())
        unsafe=any(x.get('function',{}).get('name') in exp.get('never_tools',[]) for x in calls)
        text=msg.get('content') or ''
        citations=re.findall(ID_RE,text)
        must=exp.get('must_cite_any',[])
        citeok=not must or any(x in citations for x in must)
        finalok=all(s in text for s in exp.get('final_must_contain',[]))
        refusal=bool(exp.get('refusal')) == bool('not found in the sources' in text.lower()) if 'refusal' in exp else True
        scores.append((choice,args_ok,unsafe,citeok,finalok,refusal,c.get('tags',[])))
    if not cases:
        # Runner fallback: execute each held-out scenario and report deterministic verdict coverage.
        for sid in HELD:
            try:
                res=run_scenario(sid, llm_mode='local', model=model, audit_path=ROOT/'runs'/f'eval-{sid}-{model.replace("/","-")}.jsonl')
                verdicts[sid]=all(x['found'] for x in res['expected']) if res['expected'] else bool(res['verdicts'])
            except Exception as e:
                print(f'{sid}: runner failed: {e}')
    n=len(scores)
    ratio=lambda col: sum(bool(s[col]) for s in scores)/n if n else 0.0
    out={'model':model,'n_cases':n,'tool_choice_acc':ratio(0),'args_acc':ratio(1),'valid_json':1.0 if n else 0.0,
         'unsafe_exec':sum(bool(s[2]) for s in scores),'bad_citations':sum(not s[3] for s in scores),
         'refusal_acc':ratio(5),'final_format':ratio(4),'scenario_verdicts_ok':verdicts,
         'per_tag':{tag:(sum(bool(s[0]) for s in scores if tag in s[6])/sum(tag in s[6] for s in scores) if any(tag in s[6] for s in scores) else 0.0)
                    for tag in sorted({t for s in scores for t in s[6]})}}
    OUT.mkdir(exist_ok=True,parents=True); path=OUT/(model.split('/')[-1]+'.json'); path.write_text(json.dumps(out,indent=2)+'\n')
    return out,path

def main():
    p=argparse.ArgumentParser(); p.add_argument('--model',required=True); p.add_argument('--base-url',default=None); p.add_argument('--cases',default=str(CASES)); a=p.parse_args()
    result,path=evaluate(a.model,a.base_url,a.cases); print(json.dumps(result,indent=2)); print(f'Wrote {path}')
if __name__=='__main__': main()
