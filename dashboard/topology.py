"""Static layout of the emulated Chennai network for the map panel.

Mirrors orca/sim/topology.py on purpose (the dashboard must not import the simulator, so it
runs with only the standard library). If the simulator topology changes, update this file.
Everything here is emulated: no real satellite, gateway or tower is meant.
"""
from __future__ import annotations

GATEWAYS = {
    "GW-IN-1": {"country": "IN", "role": "primary", "label": "Gateway 1 (India, primary)", "allowed": True},
    "GW-IN-2": {"country": "IN", "role": "backup", "label": "Gateway 2 (India, backup)", "allowed": True},
    "GW-XX": {"country": "XX", "role": "foreign", "label": "Gateway outside India (forbidden)", "allowed": False},
}

# paths: A = primary, B = backup. [link kind, gateway]
SITES = {
    "CHN-01": {"area": "Park Town", "role": "hospital corridor",
               "paths": {"A": ["satellite", "GW-IN-1"], "B": ["microwave", "GW-IN-2"]}},
    "CHN-02": {"area": "T. Nagar", "role": "shops, UPI and ATMs",
               "paths": {"A": ["satellite", "GW-IN-1"], "B": ["microwave", "GW-IN-2"]}},
    "CHN-03": {"area": "Adyar", "role": "homes, 112",
               "paths": {"A": ["microwave", "GW-IN-1"], "B": ["satellite", "GW-IN-2"]}},
    "CHN-04": {"area": "Guindy", "role": "grid communications",
               "paths": {"A": ["fibre", "GW-IN-1"], "B": ["satellite", "GW-IN-2"]}},
    "CHN-05": {"area": "Ennore", "role": "coastal, cyclone-exposed",
               "paths": {"A": ["satellite", "GW-IN-1"], "B": ["satellite", "GW-IN-2"]}},
    "CHN-06": {"area": "OMR", "role": "offices, traffic signals",
               "paths": {"A": ["microwave", "GW-IN-1"], "B": ["fibre", "GW-IN-2"]}},
}

MGMT = {"id": "SAT-MGMT", "label": "Satellite operator management network"}


def as_dict() -> dict:
    return {"sites": SITES, "gateways": GATEWAYS, "mgmt": MGMT,
            "note": "All links are emulated. No real satellite connectivity is used or claimed."}
