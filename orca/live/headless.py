"""Run one live scenario without a browser: the commander approves after a delay, then print the summary.

    python -m orca.live.headless --scenario S1 --llm mock --approve-after 3 --notify-after 5 --stage-fault 25

The commander here is a scripted stand-in with a fixed delay; every action goes through the same guarded
session methods as the dashboard (approve, notify). Everything is emulated.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from orca.remediation import Refused

from .session import LiveSession


def run(scenario: str, llm: str = "mock", approve_after: int = 3, notify_after: int | None = 5,
        stage_fault: int | None = None, rules_on: bool = True, kb: str = "india", runs_dir: str | Path | None = None,
        max_minutes: int = 400, session_hook=None):
    """Drive one scenario to its final summary and return ``session_hook(session)`` (default: the session itself).

    The session is closed, and a scratch runs directory (system temp, when none is given) removed, before returning.
    """
    scratch = None if runs_dir else tempfile.TemporaryDirectory(prefix="orca-headless-")
    s = LiveSession(scenario, llm, rules_on, kb, autoplay=True, sync=True,
                    runs_dir=Path(runs_dir) if runs_dir else Path(scratch.name))
    try:
        _drive(s, approve_after, notify_after, stage_fault, max_minutes)
        return session_hook(s) if session_hook else s
    finally:
        s.close()
        if scratch:
            scratch.cleanup()


def _drive(s: LiveSession, approve_after: int, notify_after: int | None, stage_fault: int | None,
           max_minutes: int) -> None:
    if stage_fault:
        s.arm_stage_fault(stage_fault)
    notified = False
    for _ in range(max_minutes):
        s.tick()
        for h, plan in list(s.rem.plans.items()):
            appr = s._appr.get(h, {})
            pending = not plan.get("executed") and "approved" not in appr and not plan.get("auto_token")
            if "requested" in appr and pending and s.sim.t - appr["requested"]["t"] >= approve_after:
                try:
                    s.approve(h, "demo")
                except (Refused, ValueError) as exc:     # a refusal is a real outcome, already in the audit log
                    print(f"approve refused: {exc}", file=sys.stderr)
        # Only an alert the model classes as an attack, with a reporting clock running, is a reportable
        # cyber incident; a weather or equipment fault gets no scripted cyber notification.
        events = s.bus.all()
        alerts = [e for e in events if e["kind"] == "alert" and str(e.get("label", "")).startswith("attack")]
        reportable = alerts and any(e["kind"] == "clock_obligation" for e in events)
        if notify_after is not None and not notified and reportable and s.sim.t - alerts[0]["t"] >= notify_after:
            for role in ("cert_in", "regulator"):
                s.notify(role, "Incident notification from the human commander (emulated).")
            notified = True
        if s._summary_final:
            break
    if not s._summary_final:
        s.finish()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scenario", default="S1")
    ap.add_argument("--llm", default="mock", choices=["mock", "local"])
    ap.add_argument("--approve-after", type=int, default=3, help="sim minutes the commander takes to approve")
    ap.add_argument("--notify-after", type=int, default=5,
                    help="sim minutes after the first alert to notify CERT-In and the regulator (-1 = never)")
    ap.add_argument("--stage-fault", type=int, choices=[5, 25, 100], default=None)
    ap.add_argument("--rules", choices=["on", "off"], default="on")
    ap.add_argument("--kb", choices=["india", "eu"], default="india")
    ap.add_argument("--runs-dir", default=None)
    ap.add_argument("--export", default=None, help="write every stream event (including audience:control) as a JSON list, the fixture format")
    ap.add_argument("--export-catalogue", default=None, help="write session.catalogue() as JSON (fake-mode fixture)")
    a = ap.parse_args(argv)
    def collect(s: LiveSession):
        if a.export:
            Path(a.export).write_text(json.dumps(s.bus.all(), default=str, separators=(",", ":")))
        if a.export_catalogue:
            out = Path(a.export_catalogue)
            cat = s.catalogue()
            ids = [x.get("id") for x in cat["scenarios"]]
            cat["fixture_scenarios"] = [i for i in ids if i and (out.parent / f"{i}.json").is_file()]
            out.write_text(json.dumps(cat, default=str, separators=(",", ":")))
        return s.summary(final=True)

    summary = run(a.scenario, a.llm, a.approve_after, None if a.notify_after < 0 else a.notify_after, a.stage_fault,
                  a.rules == "on", a.kb, a.runs_dir, session_hook=collect)
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
