#!/usr/bin/env python3
"""Observation-only OpenAI chat-completions runner for the ORCA OOD safety probe."""
import argparse, datetime, json, time, urllib.request, urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE='http://localhost:8000/v1'

def now_ist():
 return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).isoformat(timespec='seconds')

def send(case, model, phase):
 payload={'model':model,'messages':[{'role':'system','content':case['system']},{'role':'user','content':case['prompt']}],
          'temperature':0,'max_tokens':800,'tools':case['tools'],'tool_choice':'auto',
          'chat_template_kwargs':{'enable_thinking':False}}
 start=time.perf_counter(); response={}; error=None
 try:
  req=urllib.request.Request(BASE+'/chat/completions',json.dumps(payload).encode(),{'Content-Type':'application/json'})
  with urllib.request.urlopen(req,timeout=300) as res: response=json.load(res)
 except Exception as exc:
  error=exc.read().decode(errors='replace') if hasattr(exc,'read') else str(exc)
 return {'timestamp_ist':now_ist(),'phase':phase,'model':model,'case_id':case['id'],'category':case['category'],'role':case['role'],'prompt':case['prompt'],'request':payload,'response':response,'error':error,'latency_seconds':round(time.perf_counter()-start,3)}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--model',required=True,choices=['qwen-ft','gemma-ft']); ap.add_argument('--phase',required=True,choices=['base','paraphrase']); args=ap.parse_args()
 src=ROOT/('cases.json' if args.phase=='base' else 'cases_paraphrase.json')
 cases=json.loads(src.read_text())['cases']
 dest=ROOT/f'results_{args.model}.jsonl'
 mode='w' if args.phase=='base' else 'a'
 with dest.open(mode) as f:
  for i,c in enumerate(cases,1):
   row=send(c,args.model,args.phase); f.write(json.dumps(row,ensure_ascii=False)+'\n'); f.flush()
   msg=(row['response'].get('choices') or [{}])[0].get('message',{})
   calls=msg.get('tool_calls') or []
   names=[x.get('function',{}).get('name','?') for x in calls]
   print(f"{i}/{len(cases)} {c['id']} {row['latency_seconds']:.1f}s tools={names} error={'yes' if row['error'] else 'no'}",flush=True)
if __name__=='__main__': main()
