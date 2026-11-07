"""Network config as code: one YAML per emulated device in netconfig/, held in memory as a NetState.

A change is a reviewable unified diff between the YAML text before and after. Rollback = revert to
the snapshot taken before the change. The committed files are the default ("before") posture; a run
never edits them unless ``write`` is called with an explicit directory.
"""
from __future__ import annotations

import copy
import difflib
from pathlib import Path

import yaml

NETCONFIG_DIR = Path(__file__).resolve().parents[2] / "netconfig"
SPECIAL = {"baseline"}


def _dump(cfg: dict) -> str:
    return yaml.safe_dump(cfg, sort_keys=False, width=110)


class NetState:
    def __init__(self, configs: dict[str, dict], baseline: dict):
        self.configs = copy.deepcopy(configs)
        self.baseline = copy.deepcopy(baseline)
        self.log: list[dict] = []          # every change: {change_id, device, diff, reason}

    @classmethod
    def load(cls, directory: Path | str = NETCONFIG_DIR) -> "NetState":
        d = Path(directory)
        configs = {}
        for p in sorted(d.glob("*.yaml")):
            if p.stem in SPECIAL:
                continue
            cfg = yaml.safe_load(p.read_text())
            configs[cfg["id"]] = cfg
        return cls(configs, yaml.safe_load((d / "baseline.yaml").read_text()))

    def clone(self) -> "NetState":
        c = NetState(self.configs, self.baseline)
        c.log = list(self.log)
        return c

    def get(self, device: str) -> dict:
        if device not in self.configs:
            raise KeyError(f"no emulated device {device}")
        return self.configs[device]

    def by_kind(self, kind: str) -> list[dict]:
        return [c for c in self.configs.values() if c.get("kind") == kind]

    def text(self, device: str) -> str:
        return _dump(self.configs[device])

    def snapshot(self, devices: list[str] | None = None) -> dict[str, dict]:
        ids = devices if devices is not None else list(self.configs)
        return {d: copy.deepcopy(self.configs[d]) for d in ids}

    def restore(self, snap: dict[str, dict]) -> str:
        """Revert devices to a snapshot; returns the unified diff of the revert."""
        diffs = []
        for d, cfg in snap.items():
            before = self.text(d)
            self.configs[d] = copy.deepcopy(cfg)
            diffs.append(unified(d, before, self.text(d)))
        return "".join(diffs)

    def write(self, directory: Path | str) -> None:
        out = Path(directory)
        out.mkdir(parents=True, exist_ok=True)
        for d, cfg in self.configs.items():
            (out / f"{d}.yaml").write_text(_dump(cfg))
        (out / "baseline.yaml").write_text(_dump(self.baseline))


def unified(device: str, before: str, after: str) -> str:
    return "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                        fromfile=f"a/netconfig/{device}.yaml", tofile=f"b/netconfig/{device}.yaml"))


def version_tuple(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in str(v).split(".") if x.isdigit())
