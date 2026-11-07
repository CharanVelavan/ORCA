"""Run a demo scenario end to end.

    python run_demo.py --scenario C0            # rule engine on
    python run_demo.py --scenario C0 --no-rules # baseline: agents only
    python run_demo.py --kb eu                  # scenario 3: swap the knowledge base

Status: skeleton. Only the knowledge-base check runs today; the pipeline stages are
added in order (rule engine, scenario timeline, audit log, models, agents, remediation).
"""
import argparse
import sys

from orca import kb as kbmod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="C0")
    ap.add_argument("--kb", default="india", choices=["india", "eu"])
    ap.add_argument("--no-rules", action="store_true")
    args = ap.parse_args()

    kb = kbmod.load()
    errs = kbmod.validate(kb)
    if errs:
        print("\n".join(errs))
        return 1
    codes = ("IN",) if args.kb == "india" else ("EU",)
    recs = kb.by_jurisdiction(*codes)
    print(f"Knowledge base '{args.kb}': {len(recs)} records, {len(kb.gaps)} gaps")
    print(f"Scenario {args.scenario}: pipeline not built yet (rules={'off' if args.no_rules else 'on'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
