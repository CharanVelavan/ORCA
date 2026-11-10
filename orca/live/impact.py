"""Deterministic, explicitly emulated everyday-impact estimates."""
from __future__ import annotations

from orca.sim.service import PUBLIC_SERVICE_KEY, totals as service_totals
from orca.sim.topology import DEPENDANT_METRICS


def _rate(demand: float, delivered: float) -> dict:
    demand, delivered = round(demand, 2), round(delivered, 2)
    return {"demand_mbps": demand, "delivered_mbps": delivered,
            "pct": round(100 * delivered / demand, 1) if demand else 100.0}


class _DeliveryTotal:
    def __init__(self):
        self.demand = 0.0
        self.delivered = 0.0
        self.now: dict | None = None
        self.minimum: dict | None = None

    def update(self, row: dict, t: int) -> None:
        self.demand += row["demand_mbps"]
        self.delivered += row["delivered_mbps"]
        self.now = dict(row)
        if self.minimum is None or row["pct"] < self.minimum["pct"]:
            self.minimum = {"pct": row["pct"], "t": t}

    def cumulative(self) -> dict:
        return {"demand_mbit": round(self.demand * 60, 2), "delivered_mbit": round(self.delivered * 60, 2),
                "pct": round(100 * self.delivered / self.demand, 1) if self.demand else 100.0,
                "min_pct": self.minimum["pct"], "min_t": self.minimum["t"]}

    def summary(self) -> dict:
        cumulative = self.cumulative()
        return {
            # Kept for existing clients: these legacy fields are sums of Mbps for one-minute samples.
            "cumulative_demand_mbit_min": round(self.demand, 2),
            "cumulative_delivered_mbit_min": round(self.delivered, 2),
            "cumulative_demand_mbit": cumulative["demand_mbit"],
            "cumulative_delivered_mbit": cumulative["delivered_mbit"],
            "cumulative_pct": cumulative["pct"],
            "instant_demand_mbps": self.now["demand_mbps"],
            "instant_delivered_mbps": self.now["delivered_mbps"],
            "instant_pct_now": self.now["pct"],
            "instant_pct_min": cumulative["min_pct"],
            "instant_pct_min_t": cumulative["min_t"],
        }


class Delivery:
    """Aggregate the simulator's per-minute service allocation, not an independent shadow run."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.network = _DeliveryTotal()
        self.sites: dict[str, _DeliveryTotal] = {}
        self.services: dict[str, _DeliveryTotal] = {}
        self.site_services: dict[str, dict[str, _DeliveryTotal]] = {}
        self.now: dict | None = None

    def update(self, records: list[dict], t: int) -> None:
        if not self.enabled:
            return
        if not records:
            raise ValueError("delivery requires site records")
        services = {PUBLIC_SERVICE_KEY.get(name, name): row for name, row in service_totals(records).items()}
        sites = {}
        for record in records:
            site = record["site"]
            rows = {PUBLIC_SERVICE_KEY.get(name, name): dict(row) for name, row in record["services"].items()}
            site_rate = _rate(sum(row["demand_mbps"] for row in rows.values()),
                              sum(row["delivered_mbps"] for row in rows.values()))
            sites[site] = {**site_rate, "services": rows}
            self.sites.setdefault(site, _DeliveryTotal()).update(site_rate, t)
            for name, row in rows.items():
                self.site_services.setdefault(site, {}).setdefault(name, _DeliveryTotal()).update(row, t)
        for name, row in services.items():
            self.services.setdefault(name, _DeliveryTotal()).update(row, t)
        network = _rate(sum(row["demand_mbps"] for row in services.values()),
                        sum(row["delivered_mbps"] for row in services.values()))
        self.network.update(network, t)
        self.now = {"t": t, "network": network, "sites": sites, "services": services}

    def snapshot(self) -> dict:
        if not self.enabled:
            return {"available": False, "reason": "not_simulated", "provenance": "packet_loss_floor_estimate"}
        if self.now is None:
            return {"available": False, "reason": "awaiting_telemetry", "provenance": "emulated_simulator_allocation"}
        sites = {site: {**total.cumulative(),
                        "services": {name: row.cumulative() for name, row in self.site_services[site].items()}}
                 for site, total in self.sites.items()}
        return {"available": True, "provenance": "emulated_simulator_allocation", "now": self.now,
                "cumulative": {"network": self.network.cumulative(), "sites": sites,
                               "services": {name: total.cumulative() for name, total in self.services.items()}},
                "units": {"rate": "Mbps", "volume": "Mbit", "sample_duration_s": 60}}

    def summary(self) -> dict:
        if self.now is None:
            return {"network": {"instant_pct_now": None, "instant_pct_min": None, "cumulative_pct": None},
                    "sites": {}, "services": {}}
        sites = {site: {**total.summary(),
                        "services": {name: row.summary() for name, row in self.site_services[site].items()}}
                 for site, total in self.sites.items()}
        return {"network": self.network.summary(), "sites": sites,
                "services": {name: total.summary() for name, total in self.services.items()}}


class Impact:
    def __init__(self, delivery: bool = True):
        self.calls_112_failed = 0.0
        self.hospital_offline_min = 0.0
        self.payments_failed = 0.0
        self.grid_scada_lost_min = 0.0
        self.people_affected = 0.0
        self.warned_at: dict[str, int | None] = {}
        self.delivery = Delivery(enabled=delivery)

    def update(self, records: list[dict], t: int, warnings: set[str] = frozenset()) -> dict:
        self.delivery.update(records, t)
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
                "people_affected": round(self.people_affected, 2), "warned_at": warned, "reports": [],
                "delivery": self.delivery.snapshot()}
