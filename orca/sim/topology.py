"""Emulated Chennai topology: 6 sites, 3 gateways, backhaul paths. Nothing here is a real network.

Values marked ASSUMED are our stated parameters (docs/NETWORK.md), not operator data.
Site list and backhaul mix follow scenarios/SCHEMA.md ("Fixed sites and gateways").
"""
from __future__ import annotations

# Gateways. GW-XX is outside India and must never carry traffic (Authz Rules 2026, Rule 60(1)(b):
# "including during failure of satellite earth station gateway located in India").
GATEWAYS = {
    "GW-IN-1": {"country": "IN", "role": "primary", "city": "Chennai (emulated)", "allowed": True},
    "GW-IN-2": {"country": "IN", "role": "backup", "city": "Bengaluru (emulated)", "allowed": True},
    "GW-XX": {"country": "XX", "role": "foreign", "city": "outside India (emulated)", "allowed": False},
}
INDIAN_GATEWAYS = frozenset(g for g, v in GATEWAYS.items() if v["country"] == "IN")

# Link classes (ASSUMED budgets). Satellite = GEO Ku-band user downlink 12 GHz, circular polarisation.
LINK_CLASSES = {
    "satellite": {"freq_GHz": 12.0, "clear_snr_db": 12.0, "req_snr_db": 2.0, "capacity_mbps": 150.0,
                  "elevation_deg": 75.0, "rx_dbm": -60.0, "noise_dbm": -72.0},
    "microwave": {"freq_GHz": 18.0, "clear_snr_db": 30.0, "req_snr_db": 12.0, "capacity_mbps": 400.0,
                  "path_km": 5.0, "rx_dbm": -45.0, "noise_dbm": -75.0},
    "fibre": {"freq_GHz": None, "clear_snr_db": 40.0, "req_snr_db": 10.0, "capacity_mbps": 1000.0,
              "rx_dbm": -10.0, "noise_dbm": -50.0},
}

# Sites. Path A = primary, B = domestic backup. Path C (via GW-XX) is never configured by default;
# a scenario may *offer* it as a route candidate (the trap PB-06 must refuse).
SITES = {
    "CHN-01": {"area": "Park Town", "lat": 13.0810, "lon": 80.2750, "role": "hospital corridor",
               "paths": {"A": ("satellite", "GW-IN-1"), "B": ("microwave", "GW-IN-2")},
               "battery_kwh": 10.0, "load_kw": 2.0, "dependants": ["hospital", "112"]},
    "CHN-02": {"area": "T. Nagar", "lat": 13.0418, "lon": 80.2341, "role": "shops, UPI and ATMs",
               "paths": {"A": ("satellite", "GW-IN-1"), "B": ("microwave", "GW-IN-2")},
               "battery_kwh": 10.0, "load_kw": 2.2, "dependants": ["payments", "112"]},
    "CHN-03": {"area": "Adyar", "lat": 13.0012, "lon": 80.2565, "role": "homes, 112",
               "paths": {"A": ("microwave", "GW-IN-1"), "B": ("satellite", "GW-IN-2")},
               "battery_kwh": 8.0, "load_kw": 1.6, "dependants": ["112"]},
    "CHN-04": {"area": "Guindy", "lat": 13.0067, "lon": 80.2206, "role": "grid communications",
               "paths": {"A": ("fibre", "GW-IN-1"), "B": ("satellite", "GW-IN-2")},
               "battery_kwh": 12.0, "load_kw": 2.0, "dependants": ["grid", "112"]},
    "CHN-05": {"area": "Ennore", "lat": 13.2146, "lon": 80.3203, "role": "coastal, cyclone-exposed",
               "paths": {"A": ("satellite", "GW-IN-1"), "B": ("satellite", "GW-IN-2")},
               "battery_kwh": 8.0, "load_kw": 1.8, "dependants": ["112", "public_alerts"]},
    "CHN-06": {"area": "OMR", "lat": 12.9406, "lon": 80.2365, "role": "offices, traffic signals",
               "paths": {"A": ("microwave", "GW-IN-1"), "B": ("fibre", "GW-IN-2")},
               "battery_kwh": 10.0, "load_kw": 2.0, "dependants": ["traffic_signals", "112"]},
}
SITE_IDS = sorted(SITES)

# Services and priority for M4 (lower = more important). ASSUMED demand shares of a site's traffic.
SERVICES = ("112", "hospital", "payments", "grid", "general")
PRIORITY = {"112": 1, "hospital": 2, "grid": 3, "payments": 4, "general": 5}
DEMAND_SHARE = {"112": 0.05, "hospital": 0.10, "grid": 0.05, "payments": 0.15, "general": 0.65}
TERMINALS_PER_SITE = 4          # ASSUMED satellite modems per site
