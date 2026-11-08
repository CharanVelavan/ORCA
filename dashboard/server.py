"""Small stdlib HTTP server: one static page plus a read-only JSON API over run files.

API
  GET  /api/runs                list runs (runs dir, bundled samples, --run file) with pairing info
  GET  /api/run?name=<name>     the normalised model for one run (see adapter.build_run)
  GET  /api/topology            emulated Chennai sites, gateways, backup paths
  GET  /api/status              {"mode": "replay"|"live", "kill": {...}}
  POST /api/kill                kill switch hook. Replay: refused with a message. Live: calls LIVE.kill()
  POST /api/kill/release        same for release

Live mode hook: pass an object with ``kill(reason) -> dict``, ``release_kill() -> dict`` and
``status() -> dict`` as ``live=`` to ``make_server``. Replay mode never changes anything.
"""
from __future__ import annotations

import json
import mimetypes
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import adapter, topology

HERE = Path(__file__).resolve().parent
STATIC = HERE / "static"
SAMPLES = HERE / "samples"
REPO = HERE.parent


def _gap_register() -> dict:
    """Titles and human status of registered gaps (kb/gaps/*.yaml). Optional: {} if PyYAML or files are missing."""
    out: dict = {}
    try:
        import yaml  # type: ignore
    except ImportError:
        return out
    for f in sorted((REPO / "kb" / "gaps").glob("*.yaml")):
        try:
            for g in yaml.safe_load(f.read_text(encoding="utf-8")) or []:
                if isinstance(g, dict) and g.get("id"):
                    out[str(g["id"])] = {"title": g.get("title", ""), "status": g.get("status"), "topic": g.get("topic")}
        except Exception:  # noqa: BLE001 - a broken register must not stop the dashboard
            continue
    return out


class RunStore:
    """Finds run files and caches parsed runs by (path, mtime, size)."""

    def __init__(self, runs_dir, extra_files=(), samples_dir=SAMPLES):
        self.runs_dir = Path(runs_dir)
        self.extra = [Path(f) for f in extra_files]
        self.samples_dir = Path(samples_dir) if samples_dir else None
        self._cache: dict = {}
        self._lock = threading.Lock()
        self._register = None

    def files(self) -> dict[str, tuple[Path, str]]:
        found: dict[str, tuple[Path, str]] = {}
        if self.samples_dir and self.samples_dir.is_dir():
            for f in sorted(self.samples_dir.glob("*.jsonl")):
                found[f.stem] = (f, "sample")
        if self.runs_dir.is_dir():
            for f in sorted(self.runs_dir.glob("*.jsonl")):
                found[f.stem] = (f, "runs")
        for f in self.extra:
            if f.is_file():
                found[f.stem] = (f, "arg")
        return found

    def listing(self) -> list[dict]:
        rows = []
        for name, (path, source) in self.files().items():
            info = adapter.parse_run_name(name)
            try:
                st = path.stat()
                size, mtime = st.st_size, st.st_mtime
            except OSError:
                size, mtime = 0, 0
            rows.append({"name": name, "source": source, "bytes": size, "mtime": mtime, **info})
        names = {r["name"]: r for r in rows}
        for r in rows:   # pair <scenario>-rules-<llm> with <scenario>-norules-<llm>
            m = adapter.re.match(r"^(.+)-(rules|norules)-(.+)$", r["name"])
            if m:
                other = f"{m[1]}-{'norules' if m[2] == 'rules' else 'rules'}-{m[3]}"
                r["pair"] = other if other in names else None
            else:
                r["pair"] = None
        return rows

    def get(self, name: str) -> dict | None:
        item = self.files().get(name)
        if item is None:        # only names from the listing are served: no path from the URL is ever opened
            return None
        path, source = item
        try:
            st = path.stat()
        except OSError:
            return None
        key = (str(path), st.st_mtime_ns, st.st_size)
        with self._lock:
            hit = self._cache.get(name)
            if hit and hit[0] == key:
                return hit[1]
            if self._register is None:
                self._register = _gap_register()
            run = adapter.build_run(path, name, self._register)
            run["meta"]["source"] = source
            self._cache[name] = (key, run)
            return run


def make_handler(store: RunStore, live=None, default_run: str | None = None):
    class Handler(BaseHTTPRequestHandler):
        server_version = "orca-dashboard/1"

        def log_message(self, fmt, *args):  # quiet by default
            pass

        # ---- helpers
        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj, code: int = 200) -> None:
            self._send(code, json.dumps(obj, default=str).encode("utf-8"), "application/json; charset=utf-8")

        def _status(self) -> dict:
            if live is not None:
                try:
                    return {"mode": "live", **live.status()}
                except Exception as e:  # noqa: BLE001
                    return {"mode": "live", "error": str(e)}
            return {"mode": "replay", "kill": {"engaged": None, "note": "Replay mode. The kill switch shows state only."}}

        # ---- routes
        def do_GET(self):  # noqa: N802
            u = urlparse(self.path)
            q = parse_qs(u.query)
            if u.path == "/api/runs":
                return self._json({"runs": store.listing(), "default": default_run})
            if u.path == "/api/run":
                run = store.get((q.get("name") or [""])[0])
                if run is None:
                    return self._json({"error": "unknown run"}, 404)
                return self._json(run)
            if u.path == "/api/topology":
                return self._json(topology.as_dict())
            if u.path == "/api/status":
                return self._json(self._status())
            return self._static(u.path)

        def do_POST(self):  # noqa: N802
            u = urlparse(self.path)
            if u.path not in ("/api/kill", "/api/kill/release"):
                return self._json({"error": "not found"}, 404)
            n = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(n) or b"{}") if n else {}
            except ValueError:
                body = {}
            if live is None:
                return self._json({"ok": False, "mode": "replay",
                                   "message": "Replay only. Nothing was changed. In live mode this button calls the commander kill switch."},
                                  409)
            try:
                res = live.release_kill() if u.path.endswith("release") else live.kill(str(body.get("reason") or "dashboard"))
                return self._json({"ok": True, "mode": "live", **(res or {})})
            except Exception as e:  # noqa: BLE001
                return self._json({"ok": False, "mode": "live", "message": str(e)}, 400)

        def _static(self, path: str) -> None:
            rel = "index.html" if path in ("", "/") else path.lstrip("/")
            f = (STATIC / rel).resolve()
            if STATIC not in f.parents or not f.is_file():
                return self._json({"error": "not found"}, 404)
            ctype = mimetypes.guess_type(str(f))[0] or "application/octet-stream"
            if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
                ctype += "; charset=utf-8"
            self._send(200, f.read_bytes(), ctype)

    return Handler


def make_server(runs_dir="runs", run_files=(), host="127.0.0.1", port=8050, live=None, samples_dir=SAMPLES):
    store = RunStore(runs_dir, run_files, samples_dir)
    default = Path(run_files[0]).stem if run_files else None
    return ThreadingHTTPServer((host, port), make_handler(store, live, default)), store
