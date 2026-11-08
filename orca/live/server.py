"""Stdlib HTTP/SSE server for :mod:`orca.live`."""
from __future__ import annotations

import json
import mimetypes
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
                # Keep the connection open and re-check after every standard SSE heartbeat window.
                while True:
                    events = session.bus.wait_since(since, 15)
                    if not events:
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
                        continue
                    for event in events:
                        self.wfile.write(b"data: " + json.dumps(event, default=str).encode() + b"\n\n")
                        since = event["seq"]
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
            path = session.recording.parent / candidate.name
            if not path.is_file():
                return self._json({"ok": False, "error": "recording not found"}, 404)
            try:
                return self._json({"ok": True, "events": _replay_events(path)})
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
