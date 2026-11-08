"""python -m dashboard --run runs/mock-s1.jsonl  ->  http://localhost:8050"""
from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

from .server import make_server


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m dashboard",
                                 description="ORCA-NTN dashboard. Reads run files, works offline. All NTN links are emulated.")
    ap.add_argument("--run", action="append", default=[], metavar="FILE",
                    help="run file (JSON Lines audit trace) to open first; may repeat")
    ap.add_argument("--runs-dir", default="runs", help="folder scanned for *.jsonl runs (default: runs)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8050)
    ap.add_argument("--open", action="store_true", help="open the page in the default browser")
    a = ap.parse_args(argv)
    for f in a.run:
        if not Path(f).is_file():
            print(f"warning: run file not found: {f}", file=sys.stderr)
    srv, store = make_server(a.runs_dir, a.run, a.host, a.port)
    url = f"http://{'localhost' if a.host in ('127.0.0.1', 'localhost') else a.host}:{a.port}"
    print(f"ORCA-NTN dashboard on {url}  (replay mode, {len(store.files())} runs found). Ctrl+C to stop.")
    if a.open:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
