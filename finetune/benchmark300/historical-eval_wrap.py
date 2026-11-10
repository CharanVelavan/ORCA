"""Run the stock finetune/eval_cases.py evaluate() and also log raw responses."""
import sys, json, time, importlib
sys.path.insert(0, '/home/charanaklavya12_gmail_com/orca-ntn')
sys.path.insert(0, '/home/charanaklavya12_gmail_com/orca-ntn/finetune')
import eval_cases
from orca.llm import LLMClient
model, base, cases, rawout, outjson = sys.argv[1:6]
raw = []
orig = LLMClient.chat
def chat(self, messages, tools=None):
    t = time.time(); m = orig(self, messages, tools); raw.append({'dt': round(time.time() - t, 2), 'msg': m}); return m
LLMClient.chat = chat
t0 = time.time()
out, path = eval_cases.evaluate(model, base, cases)
out['wall_s'] = round(time.time() - t0); out['s_per_case'] = round(out['wall_s'] / max(1, out['n_cases']), 2)
json.dump(out, open(outjson, 'w'), indent=2)
json.dump(raw, open(rawout, 'w'))
print(json.dumps(out, indent=2))
