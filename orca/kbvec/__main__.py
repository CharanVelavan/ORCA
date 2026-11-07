"""python -m orca.kbvec ingest [--corpus] | query "<q>" | eval | snapshot | coverage "<q>" <J>"""
from __future__ import annotations

import argparse
import json


def main() -> None:
    ap = argparse.ArgumentParser(prog="orca.kbvec")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("ingest", help="parse + embed kb/sources and verified records (incremental)")
    p.add_argument("--corpus", action="store_true", help="also ingest the staged corpus (corpus/raw + kb/staging)")
    p = sub.add_parser("query")
    p.add_argument("q")
    p.add_argument("-k", type=int, default=5)
    p.add_argument("--no-rerank", action="store_true")
    p.add_argument("--filter", action="append", default=[], metavar="key=value")
    p = sub.add_parser("eval", aliases=["evaluate"], help="retrieval test (recall@5, MRR)")
    p.add_argument("--no-rerank", action="store_true")
    p.add_argument("--tier", choices=["corpus", "verified"], help="restrict retrieval to one tier")
    sub.add_parser("snapshot", help="write an index manifest; cached retrievals are keyed to it")
    p = sub.add_parser("coverage")
    p.add_argument("q")
    p.add_argument("jurisdiction")
    a = ap.parse_args()

    if a.cmd == "ingest":
        from .ingest import ingest
        print(json.dumps(ingest(corpus=a.corpus), indent=1))
    elif a.cmd == "query":
        from .retrieve import search
        f = dict(x.split("=", 1) for x in a.filter) or None
        for h in search(a.q, k=a.k, filters=f, rerank=not a.no_rerank, cache=False):
            print(f"{h['score']:8.3f}  {h['chunk_id']}  [{h['tier']}/{h['jurisdiction']}/{h['binding_status']}] "
                  f"p{h['page']} {h['clause'] or ''}\n          {h['text'][:200]!r}")
    elif a.cmd in ("eval", "evaluate"):
        from . import evaluate
        print(evaluate.table(evaluate.run(rerank=not a.no_rerank, tier=a.tier)))
    elif a.cmd == "snapshot":
        from .replay import snapshot
        print(json.dumps(snapshot(), indent=1))
    elif a.cmd == "coverage":
        from .retrieve import coverage
        print(json.dumps(coverage(a.q, a.jurisdiction), indent=1))


if __name__ == "__main__":
    main()
