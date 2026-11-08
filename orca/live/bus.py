"""Thread-safe append-only event stream used by the live console."""
from __future__ import annotations

import threading
from datetime import datetime, timezone


class EventBus:
    def __init__(self):
        self._events: list[dict] = []
        self._condition = threading.Condition()

    def emit(self, event: dict) -> dict:
        """Append an event, assigning its monotonically increasing sequence number."""
        with self._condition:
            item = dict(event)
            item.setdefault("ts", datetime.now(timezone.utc).isoformat())
            item["seq"] = len(self._events) + 1
            self._events.append(item)
            self._condition.notify_all()
            return dict(item)

    def since(self, seq: int = 0) -> list[dict]:
        with self._condition:
            return [dict(e) for e in self._events if e["seq"] > seq]

    def wait_since(self, seq: int, timeout: float = 15.0) -> list[dict]:
        with self._condition:
            events = self.since(seq)
            if not events:
                self._condition.wait(timeout)
                events = self.since(seq)
            return events

    def all(self) -> list[dict]:
        return self.since(0)
