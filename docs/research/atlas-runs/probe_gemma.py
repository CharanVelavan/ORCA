import json, time, urllib.request, sys
B="http://localhost:8000/v1"
def post(p):
    r=urllib.request.Request(B+"/chat/completions",json.dumps(p).encode(),{"Content-Type":"application/json"})
    t=time.time(); d=json.load(urllib.request.urlopen(r,timeout=300)); return d,time.time()-t
M=json.load(urllib.request.urlopen(B+"/models"))["data"][0]["id"]; print("model",M)
tools=[{"type":"function","function":{"name":"read_alerts","description":"Read current alerts for a site","parameters":{"type":"object","properties":{"site":{"type":"string"},"source":{"type":"string","enum":["M1","M2","M3"]}},"required":["site","source"]}}}]
d,t=post({"model":M,"temperature":0,"max_tokens":300,"messages":[{"role":"system","content":"You are the Mobile Operator agent. Use tools."},{"role":"user","content":"Read current alerts for site CHN-03 from source M3."}],"tools":tools,"tool_choice":"auto"})
m=d["choices"][0]["message"]; print("finish",d["choices"][0]["finish_reason"],"tool_calls",json.dumps(m.get("tool_calls")),"content",repr(m.get("content")),"usage",d["usage"],round(t,2),"s")
for i in range(3):
    d,t=post({"model":M,"temperature":0,"max_tokens":300,"messages":[{"role":"user","content":"Write a detailed explanation of how satellite backhaul failover works for mobile towers, at least 300 words."}]})
    u=d["usage"]; tm=d.get("timings",{}); print("completion_tokens",u["completion_tokens"],"wall",round(t,2),"tok/s wall",round(u["completion_tokens"]/t,1),"server predicted_per_second",tm.get("predicted_per_second"),"prompt_per_second",tm.get("prompt_per_second"))
