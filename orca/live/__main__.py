"""Run the live emulated control-console API."""
from __future__ import annotations

import argparse

from .server import make_server
from .session import LiveSession


def main() -> None:
    p = argparse.ArgumentParser(description="ORCA-NTN live console (emulated network)")
    p.add_argument("--scenario", default="s1")
    p.add_argument("--llm", choices=("mock", "local"), default="mock")
    p.add_argument("--port", type=int, default=8060)
    p.add_argument("--rules", choices=("on", "off"), default="on")
    p.add_argument("--kb", choices=("india", "eu"), default="india")
    args = p.parse_args()
    session = LiveSession(args.scenario, args.llm, args.rules == "on", args.kb)
    server = make_server(session, port=args.port)
    try:
        server.serve_forever()
    finally:
        session.close()
        server.server_close()


if __name__ == "__main__":
    main()
