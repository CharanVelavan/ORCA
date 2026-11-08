"""Stdlib HTTP/SSE server for :mod:`orca.live`."""
from __future__ import annotations

import json
import mimetypes
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from dashboard import adapter

from .session import LiveSession

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "dashboard" / "live" / "dist"
STATIC = ROOT / "dashboard" / "live" / "static"


def _replay_events(path: Path) -> list[dict]:
    """Translate audit JSONL to a minimal section-4 event stream for the replay client."""
    # Parse once through the established replay adapter: a malformed/tampered chain is still visible
    # in its normal after-action-review data, while the event list stays lightweight for the live UI.
    adapter.build_run(path, path.stem)
    out = []
    kind_map = {"event_released": "alert", "inject": "inject", "scheduled": "scheduled",
                "approval_requested": "approval", "approved": "approval",
                "rejected": "approval", "executed": "execute", "execute_refused": "execute",
                "autonomy_set": "autonomy", "autonomy_downgraded": "autonomy", "kill_switch": "kill",
                "kill_switch_released": "kill", "msg_sent": "msg", "msg_rejected": "msg"}
    for entry in json.loads("[" + ",".join(line for line in path.read_text().splitlines() if line.strip()) + "]") if path.stat().st_size else []:
        payload = dict(entry.get("payload") or {})
        kind = kind_map.get(entry.get("kind"), entry.get("kind"))
        if kind in ("inject", "scheduled") and "kind" in payload:
            payload["injector"] = payload.pop("kind")
        event = {"seq": entry.get("seq"), "t": payload.get("t", payload.get("start", payload.get("at_t", 0))),
                 "ts": entry.get("ts"), "kind": kind, "actor": entry.get("actor"), **payload}
        if kind in ("inject", "scheduled"):
            event["audience"] = "control"
        out.append(event)
    return out


STREAM_SUFFIX = ".stream.jsonl"


def list_runs(runs: Path) -> dict:
    """Audit recordings under ``runs/`` (newest first); a sidecar only sets ``stream: true``."""
    rows = []
    for path in runs.glob("*.jsonl"):
        if path.name.endswith(STREAM_SUFFIX):
            continue
        scenario = None
        try:
            with path.open(encoding="utf-8") as fh:
                first = json.loads(fh.readline() or "{}")
            scenario = (first.get("payload") or {}).get("scenario")
        except (OSError, ValueError):
            pass
        if not scenario and path.name.split("-")[0].isalnum() and path.name.split("-")[0].isupper():
            scenario = path.name.split("-")[0]
        stat = path.stat()
        rows.append({"file": path.name, "scenario": str(scenario).upper() if scenario else None,
                     "stream": (runs / f"{path.stem}{STREAM_SUFFIX}").is_file(),
                     "size": stat.st_size, "mtime": stat.st_mtime})
    rows.sort(key=lambda r: r["mtime"], reverse=True)
    return {"ok": True, "runs": rows}


def stream_chunks(session: LiveSession, since: int = 0, poll: float = 1.0, heartbeat: float = 15.0):
    """Yield stream events (dicts) and ``None`` heartbeats, following a session restart.

    A restart replaces ``session.bus`` with a fresh bus whose seq restarts at 1, so the cursor
    is reset whenever the bus object changes. A short poll picks the switch up quickly.
    """
    bus, last = session.bus, time.monotonic()
    while True:
        if session.bus is not bus:
            bus, since = session.bus, 0
        events = bus.wait_since(since, poll)
        if session.bus is not bus:
            continue
        if events:
            for event in events:
                since = event["seq"]
                yield event
            last = time.monotonic()
        elif time.monotonic() - last >= heartbeat:
            last = time.monotonic()
            yield None


def make_handler(session: LiveSession):
    class Handler(BaseHTTPRequestHandler):
        server_version = "orca-live/1"

        def log_message(self, fmt, *args):
            pass

        def _send(self, code: int, raw: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "http://localhost:5173")
            self.end_headers()
            self.wfile.write(raw)

        def _json(self, value, code: int = 200):
            self._send(code, json.dumps(value, default=str).encode(), "application/json; charset=utf-8")

        def do_OPTIONS(self):  # noqa: N802
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "http://localhost:5173")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def do_GET(self):  # noqa: N802
            u, q = urlparse(self.path), parse_qs(urlparse(self.path).query)
            if u.path == "/api/stream":
                return self._stream(int((q.get("since") or ["0"])[0]))
            if u.path == "/api/state":
                return self._json(session.state())
            if u.path == "/api/catalogue":
                return self._json(session.catalogue())
            if u.path == "/api/truth":
                return self._json(session.truth())
            if u.path == "/api/runs":
                return self._json(list_runs(session.recording.parent))
            if u.path == "/api/replay":
                return self._replay((q.get("file") or [""])[0])
            return self._static(u.path)

        def do_POST(self):  # noqa: N802
            u = urlparse(self.path)
            try:
                n = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(n) or b"{}") if n else {}
                if not isinstance(body, dict):
                    raise ValueError("body must be an object")
                result = self._command(u.path, body)
                self._json(result, 200 if result.get("ok") else 400)
            except (ValueError, KeyError) as exc:
                self._json({"ok": False, "error": str(exc)}, 400)
            except Exception as exc:  # Remediation refuses safely; the server only returns its safe text.
                self._json({"ok": False, "error": str(exc)}, 400)

        def do_DELETE(self):  # noqa: N802
            u = urlparse(self.path)
            if u.path.startswith("/api/schedule/"):
                try:
                    return self._json(session.delete_schedule(u.path.rsplit("/", 1)[1]))
                except ValueError as exc:
                    return self._json({"ok": False, "error": str(exc)}, 404)
            return self._json({"ok": False, "error": "not found"}, 404)

        def _command(self, path: str, b: dict) -> dict:
            if path == "/api/session":
                return session.restart(**b)
            if path == "/api/clock":
                return session.clock(b.get("action", ""), b.get("speed"))
            if path == "/api/inject":
                return session.inject(b["kind"], b.get("target"), b.get("duration_min", 10), b.get("params") or {})
            if path == "/api/inject/stop":
                return session.stop_injection(b.get("id"), b.get("kind"))
            if path == "/api/schedule":
                return session.schedule(b["kind"], b.get("target"), b["at_t"], b["duration_min"], b.get("params") or {})
            if path == "/api/autonomy":
                return session.autonomy(b["mode"], b.get("sites", "*"), b.get("playbooks", "*"), b["minutes"], b.get("pin", ""))
            if path == "/api/approve":
                return session.approve(b["hash"], b.get("pin", ""))
            if path == "/api/reject":
                return session.reject(b["hash"], b.get("reason", ""))
            if path == "/api/kill":
                return session.kill(b.get("pin", ""), b.get("reason", ""))
            if path == "/api/kill/release":
                return session.release_kill(b.get("pin", ""))
            if path == "/api/order":
                return session.order(b["to"], b["text"])
            if path == "/api/ask":
                return session.ask(b["to"], b["question"])
            if path == "/api/rules":
                return session.set_rules(b["on"])
            if path == "/api/kb":
                return session.set_kb(b["kb"])
            if path == "/api/gap":
                return session.decide_gap(b["gap_id"], b["decision"], b.get("pin", ""))
            raise ValueError("not found")

        def _stream(self, since: int) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "http://localhost:5173")
            self.end_headers()
            try:
                for event in stream_chunks(session, since):
                    if event is None:
                        self.wfile.write(b": heartbeat\n\n")
                    else:
                        self.wfile.write(b"data: " + json.dumps(event, default=str).encode() + b"\n\n")
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                return

        def _replay(self, name: str) -> None:
            # Only files directly under runs/ are accepted; URL input never becomes an arbitrary path.
            candidate = Path(name)
            if candidate.parts[:1] == ("runs",):
                candidate = Path(*candidate.parts[1:])
            if len(candidate.parts) != 1 or candidate.suffix != ".jsonl":
                return self._json({"ok": False, "error": "file must name a runs/*.jsonl recording"}, 400)
            runs = session.recording.parent
            base = candidate.name[:-len(STREAM_SUFFIX)] if candidate.name.endswith(STREAM_SUFFIX) else candidate.stem
            audit, sidecar = runs / f"{base}.jsonl", runs / f"{base}{STREAM_SUFFIX}"
            try:
                if sidecar.is_file():
                    lines = [json.loads(line) for line in sidecar.read_text(encoding="utf-8").splitlines() if line.strip()]
                    return self._json({"ok": True, "events": lines, "source": "stream"})
                if not audit.is_file():
                    return self._json({"ok": False, "error": "recording not found"}, 404)
                return self._json({"ok": True, "events": _replay_events(audit), "source": "audit"})
            except Exception as exc:
                return self._json({"ok": False, "error": f"cannot parse recording: {exc}"}, 400)

        def _static(self, path: str) -> None:
            root = DIST if DIST.is_dir() else STATIC
            rel = "index.html" if path in ("", "/") else path.lstrip("/")
            file = (root / rel).resolve()
            if root not in file.parents or not file.is_file():
                file = root / "index.html"  # SPA fallback
            if not file.is_file():
                return self._json({"ok": False, "error": "live UI has not been built"}, 404)
            ctype = mimetypes.guess_type(str(file))[0] or "application/octet-stream"
            if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
                ctype += "; charset=utf-8"
            self._send(200, file.read_bytes(), ctype)

    return Handler


def make_server(session: LiveSession, host: str = "127.0.0.1", port: int = 8060) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(session))
