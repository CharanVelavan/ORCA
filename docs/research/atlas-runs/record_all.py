"""Record every scenario with real Qwen agents on Atlas, rules on and off. Sequential (one LLM).
Run: LLM_BASE_URL=http://localhost:8000/v1 LLM_MODEL=<atlas model id> [RUN_TAG=gemma-ft] python3 docs/research/atlas-runs/record_all.py
RUN_TAG (default 'qwen') names the traces <SC>-<rules|norules>-<tag>.jsonl; summary is summary.json for qwen, summary-<tag>.json otherwise."""
import json, os, sys, time, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from orca.runner import run_scenario  # noqa: E402
from orca.audit import AuditLog  # noqa: E402

SCEN = ["S0", "S1", "S2", "S3", "N1", "N2", "N3", "N4", "N5", "CAP"]
OUT = ROOT / "runs" / "atlas"
TAG = os.environ.get("RUN_TAG", "qwen")
SUMMARY = ROOT / "docs" / "research" / "atlas-runs" / ("summary.json" if TAG == "qwen" else f"summary-{TAG}.json")
results = json.loads(SUMMARY.read_text()) if SUMMARY.exists() else {}

def atlas_up():
    try:
        urllib.request.urlopen("http://localhost:8000/v1/models", timeout=10); return True
    except Exception:
        return False

for sc in SCEN:
    for rules in (True, False):
        key = f"{sc}-{'rules' if rules else 'norules'}"
        if results.get(key, {}).get("ok"):
            continue
        waited = 0
        while not atlas_up() and waited < 900:
            print(f"{key}: Atlas down, waiting", flush=True); time.sleep(30); waited += 30
        t0 = time.time()
        path = OUT / f"{key}-{TAG}.jsonl"
        try:
            r = run_scenario(sc, llm_mode="local", rules_enabled=rules, audit_path=path)
            entries = list(AuditLog(path).entries())
            kinds = [e["kind"] for e in entries]
            rej = sum(len((e.get("payload") or {}).get("citations_rejected") or []) for e in entries)
            refused = sum(1 for e in entries if e["kind"] == "agent_step" and isinstance((e.get("payload") or {}).get("result"), dict)
                          and "refused" in e["payload"]["result"])
            results[key] = {"ok": True, "found": sum(x["found"] for x in r["expected"]), "expected": len(r["expected"]),
                            "missing": [x["expect"] for x in r["expected"] if not x["found"]],
                            "verdicts": len(r["verdicts"]), "entries": len(entries), "agent_steps": kinds.count("agent_step"),
                            "citations_rejected": rej, "tool_refusals": refused,
                            "executed": kinds.count("executed"), "approvals_requested": kinds.count("approval_requested"),
                            "minutes": round((time.time() - t0) / 60, 1), "trace": str(path.relative_to(ROOT))}
        except Exception as e:
            results[key] = {"ok": False, "error": f"{type(e).__name__}: {e}"[:400], "minutes": round((time.time() - t0) / 60, 1)}
        SUMMARY.write_text(json.dumps(results, indent=1))
        print(key, json.dumps({k: results[key].get(k) for k in ("ok", "found", "expected", "minutes", "error")}), flush=True)
print("ALL DONE", flush=True)
