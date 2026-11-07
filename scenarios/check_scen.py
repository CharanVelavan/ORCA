import sys, glob, yaml, datetime as dt
sys.path.insert(0, '.')
from orca import kb as K, rules as R
kb = K.load()
SIG = {"snr_db","rain_mm_h","link_margin_db","packet_loss","traffic_load","mains_power","battery_pct","vpn_login",
       "mgmt_command","terminals_up","telemetry_reported","route_candidate","link_protection","txn_success"}
SITES = {f"CHN-0{i}" for i in range(1,7)}
ACT = {"M1","M2","M3","M4","attacker","environment","judge","satellite_operator","mobile_operator","power_utility",
       "cert_in","regulator","gap_analyst","commander"}
BAN_T = {"joint_command","personal_data_breach","emergency_priority"}
M3 = {"normal","fault-weather","fault-power/equipment","attack-jamming","attack-management-plane","abstain"}
EXEC_OK = {"PB-01","PB-06","PB-10"}
known_gaps = set(kb.gaps)
def merge(f, add):
    for k, v in (add or {}).items():
        if isinstance(v, list): f.setdefault(k, []).extend(v)
        elif isinstance(v, dict): f.setdefault(k, {}).update(v)
        else: f[k] = v
for p in sorted(glob.glob('scenarios/*.yaml')):
    d = yaml.safe_load(open(p)); probs = []
    start = R.parse_ts(d['start'])
    if d.get('m3_expected') not in M3: probs.append(f"m3 {d.get('m3_expected')}")
    for pb in d.get('playbooks', []):
        if pb.get('executed') and pb['id'] not in EXEC_OK: probs.append(f"{pb['id']} executed")
        if pb['id']=='PB-10' and pb.get('owner')!='mobile_operator': probs.append("PB-10 owner")
    facts = {"jurisdiction": d.get('jurisdiction','IN')}
    ok_exp = 0; tot_exp = 0; gaps_fired = set()
    qids = []
    for e in d['events']:
        if e.get('actor') not in ACT: probs.append(f"t{e['t']} actor {e.get('actor')}")
        for s in e.get('signals') or []:
            if s.get('signal') not in SIG: probs.append(f"t{e['t']} signal {s.get('signal')}")
            if s.get('site') not in SITES: probs.append(f"t{e['t']} site {s.get('site')}")
        f = e.get('facts') or {}
        for q in f.get('obligation_questions', []):
            if q['topic'] in BAN_T: probs.append(f"banned topic {q['topic']}")
            qids.append(q['id'])
        merge(facts, f)
        facts['now'] = (start + dt.timedelta(minutes=e['t'])).isoformat()
        try:
            vs = R.evaluate(facts, kb)
        except Exception as ex:
            probs.append(f"t{e['t']} engine error {ex}"); continue
        for v in vs:
            if v.gap_id: gaps_fired.add(v.gap_id)
        for x in e.get('expect') or []:
            tot_exp += 1
            g = x.get('gap')
            if g and g not in known_gaps: probs.append(f"unknown gap {g}")
            if g in ("GAP-IN-05-NO-BREACH-CLOCK-TODAY","GAP-IN-07-NO-JOINT-PLAN"): probs.append(f"rejected gap {g}")
            hit = any(v.verdict == x['verdict'] and (not g or v.gap_id == g) and (not x.get('topic') or v.topic == x['topic']) for v in vs)
            if hit: ok_exp += 1
            else: probs.append(f"t{e['t']} EXPECT MISS {x} got {[ (v.verdict,v.topic,v.gap_id) for v in vs][-4:]}")
    if len(qids) != len(set(qids)): probs.append("duplicate question ids")
    real_gaps = sorted(g[7:9] for g in gaps_fired if g.startswith('GAP-IN-'))
    cand = sorted(g for g in gaps_fired if g.startswith('GAP-CAND'))
    print(f"{d['id']:4} expects {ok_exp}/{tot_exp}  gaps fired {real_gaps} {cand}  problems {len(probs)}")
    for x in probs[:8]: print("     -", x)
