"""Reusable scenario execution and result extraction for demos and evaluation."""
from __future__ import annotations
import json
from pathlib import Path
import yaml
from orca.agents import Coordinator, PolicyMockLLM
from orca.audit import AuditLog
from orca.llm import LLMClient
from orca.world import World
from orca.sim.scenario import load_scenario

ROOT = Path(__file__).resolve().parents[1]

def run_scenario(scenario_id: str, *, llm_mode="mock", rules_enabled=True, audit_path=None, model=None):
    sc = load_scenario(scenario_id)
    ident = str(sc.get("id", scenario_id)).upper()
    if audit_path is None:
        audit_path = ROOT / "runs" / f"{ident}-{'rules' if rules_enabled else 'norules'}-{llm_mode}.jsonl"
    audit_path = Path(audit_path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text("")
    world = World.new({"now": str(sc["start"]), "jurisdiction": sc.get("jurisdiction", "IN"), "entity": sc.get("entity", {})}, audit_path)
    llm = PolicyMockLLM() if llm_mode == "mock" else LLMClient(model=model)
    coordinator = Coordinator(world, llm, rules_enabled=rules_enabled)
    results = coordinator.run(sc)
    verdicts = []
    for entry in AuditLog(audit_path).entries():
        if entry["kind"] == "tool_result":
            continue
        payload = entry.get("payload", {})
        if entry["kind"] == "agent_step" and isinstance(payload.get("result"), dict):
            verdicts.extend(payload["result"].get("verdicts", []))
    expected = [v for e in sc.get("events", []) for v in (e.get("expect") or [])]
    matched = []
    for ex in expected:
        matched.append({"expect": ex, "found": any(v.get("verdict")==ex.get("verdict") and (not ex.get("gap") or v.get("gap_id")==ex.get("gap")) for v in verdicts)})
    return {"scenario": ident, "results": results, "verdicts": verdicts, "expected": matched, "audit": str(audit_path)}


def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--no-rules", action="store_true")
    ap.add_argument("--llm", choices=["mock","local"], default="mock")
    a=ap.parse_args(argv)
    out=run_scenario(a.scenario, llm_mode=a.llm, rules_enabled=not a.no_rules)
    print(f"Scenario {out['scenario']} ({'no rules' if a.no_rules else 'rules'}, {a.llm})")
    for v in out["expected"]: print(f"{'FOUND' if v['found'] else 'MISSING'} {v['expect']}")
    print(f"Audit trace: {out['audit']}")
    return 0
if __name__ == '__main__': raise SystemExit(main())
