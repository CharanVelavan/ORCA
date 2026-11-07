"""Hash-chained, append-only audit log (JSON Lines).

Every step (alert, verdict, approval, rollout, rollback) is one entry:

    {seq, ts, kind, actor, payload, prev_hash, hash}

``hash`` is sha256 of the canonical JSON of the entry *without* the ``hash`` key, and
``prev_hash`` is the previous entry's hash (64 zeros for the first entry). Editing,
deleting or reordering a line therefore breaks the chain, and ``verify()`` reports the
first sequence number where it breaks.

This is **tamper-evident, not tamper-proof**: someone who can rewrite the whole file and
recompute every hash can forge a log. Anchor the latest hash somewhere else (a printed
approval, a second system) if you need more than detection of casual edits.

Timestamps come from the caller (``ts``), never from the clock, so replays are deterministic.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

GENESIS = "0" * 64


def canonical(obj: dict) -> str:
    """Canonical JSON: sorted keys, no spaces, UTF-8 characters kept."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(entry: dict) -> str:
    body = {k: v for k, v in entry.items() if k != "hash"}
    return hashlib.sha256(canonical(body).encode("utf-8")).hexdigest()


class AuditLog:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def entries(self) -> list[dict]:
        """All entries in file order. A line that is not valid JSON raises ValueError."""
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
        return out

    def append(self, kind: str, actor: str, payload: dict, ts: str) -> dict:
        """Add one entry chained to the previous one and return it."""
        existing = self.entries()
        prev = existing[-1]["hash"] if existing else GENESIS
        entry = {
            "seq": len(existing) + 1,
            "ts": ts,
            "kind": kind,
            "actor": actor,
            "payload": payload,
            "prev_hash": prev,
        }
        entry["hash"] = _hash(entry)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(canonical(entry) + "\n")
        return entry

    def verify(self) -> int | None:
        """Return None if the chain is intact, else the first sequence number that is bad.

        Checks, per line: sequence is 1, 2, 3...; prev_hash matches the previous hash;
        the stored hash matches the recomputed one. A line that cannot be parsed counts
        as bad at its expected sequence number.
        """
        prev = GENESIS
        expected = 1
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                e = json.loads(line)
                ok = (e["seq"] == expected and e["prev_hash"] == prev
                      and e["hash"] == _hash(e))
            except (ValueError, KeyError, TypeError):
                return expected
            if not ok:
                return expected
            prev = e["hash"]
            expected += 1
        return None
