"""Deterministic, explicitly emulated everyday-impact estimates."""
from __future__ import annotations

from orca.sim.topology import DEPENDANT_METRICS


class Impact:
    def __init__(self):
        self.calls_112_failed = 0.0
        self.hospital_offline_min = 0.0
        self.payments_failed = 0.0
        self.grid_scada_lost_min = 0.0
        self.people_affected = 0.0
        self.warned_at: dict[str, int | None] = {}

    def update(self, records: list[dict], t: int, warnings: set[str] = frozenset()) -> dict:
        for r in records:
            site, m = r["site"], DEPENDANT_METRICS.get(r["site"], {})
            outage = max(float(r.get("packet_loss", 0)), 1 - float(r.get("txn_success", 1)))
            self.calls_112_failed += m.get("calls_112_per_min", 0) * outage
            self.payments_failed += m.get("payments_per_min", 0) * (1 - float(r.get("txn_success", 1)))
            if m.get("hospital"):
                self.hospital_offline_min += outage
            if m.get("grid_scada"):
                self.grid_scada_lost_min += outage
            self.people_affected += m.get("population", 0) * outage
            for dependant in ("112", "hospital", "payments", "grid"):
                key = f"{site}:{dependant}"
                if key not in self.warned_at:
                    self.warned_at[key] = t if dependant in warnings else None
        return self.snapshot(t)

    def snapshot(self, t: int) -> dict:
        warned = {k: {"warned_at": at, "minutes_to_warn": None if at is None else max(0, at)}
                  for k, at in self.warned_at.items()}
        return {"emulated_estimate": True, "calls_112_failed": round(self.calls_112_failed, 2),
                "hospital_offline_min": round(self.hospital_offline_min, 2),
                "payments_failed": round(self.payments_failed, 2),
                "grid_scada_lost_min": round(self.grid_scada_lost_min, 2),
                "people_affected": round(self.people_affected, 2), "warned_at": warned, "reports": []}
