"""Portable RAG v2 build/query commands; GPU embedding happens separately in Colab."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(prog="orca.kbvec")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("ingest", help="parse + embed kb/sources and verified records (incremental)")
    p.add_argument("--corpus", action="store_true", help="also ingest the staged corpus (corpus/raw + kb/staging)")
    p = sub.add_parser("chunk", help="parse legal structure and write v2 chunks.jsonl; no embedder required")
    p.add_argument("--corpus", action="store_true", help="include staged metadata and corpus/raw documents")
    p.add_argument("--corpus-dir", type=Path, help="unzipped corpus directory (normally .../corpus)")
    p.add_argument("--sources-dir", type=Path, help="unzipped kb/sources directory")
    p.add_argument("--out", type=Path, required=True, help="output chunks.jsonl path")
    p = sub.add_parser("load-vectors", help="load Colab embeddings into the orca_v2 collection without embedding")
    p.add_argument("--chunks", type=Path)
    p.add_argument("--embeddings", type=Path)
    p.add_argument("--ids", type=Path)
    p = sub.add_parser("query")
    p.add_argument("q")
    p.add_argument("-k", type=int, default=5)
    p.add_argument("--no-rerank", action="store_true")
    p.add_argument("--filter", action="append", default=[], metavar="key=value",
                   help="jurisdiction=IN|EU|US|AE|INTL, doc_type=act|rules|direction|guideline|standard|licence|...;"
                        " repeat a key or use commas for 'any of'")
    p.add_argument("--no-dedupe", action="store_true", help="keep identical or near-identical chunks")
    p = sub.add_parser("eval", aliases=["evaluate"], help="retrieval test (recall@5, MRR)")
    p.add_argument("--v2", action="store_true", help="run fixed dev/test v2 evaluation and threshold calibration")
    p.add_argument("--no-rerank", action="store_true")
    p.add_argument("--tier", choices=["corpus", "verified"], help="restrict retrieval to one tier")
    p.add_argument("--no-dedupe", action="store_true", help="keep identical or near-identical chunks")
    sub.add_parser("snapshot", help="write an index manifest; cached retrievals are keyed to it")
    p = sub.add_parser("coverage")
    p.add_argument("q")
    p.add_argument("jurisdiction")
    a = ap.parse_args()

    if a.cmd == "ingest":
        from .ingest import ingest
        print(json.dumps(ingest(corpus=a.corpus), indent=1))
    elif a.cmd == "chunk":
        from .ingest import build_chunks
        print(json.dumps(build_chunks(corpus=a.corpus, corpus_root=a.corpus_dir,
                                     sources_root=a.sources_dir, out=a.out), indent=2))
    elif a.cmd == "load-vectors":
        from .ingest import load_vectors
        print(json.dumps(load_vectors(a.chunks, a.embeddings, a.ids), indent=2))
    elif a.cmd == "query":
        from .retrieve import search
        f: dict = {}
        for x in a.filter:
            key, _, val = x.partition("=")
            f.setdefault(key, []).extend(v for v in val.split(",") if v)
        f = {k2: (v[0] if len(v) == 1 else v) for k2, v in f.items()} or None
        for h in search(a.q, k=a.k, filters=f, rerank=not a.no_rerank, cache=False, dedupe=not a.no_dedupe):
            print(f"{h['score']:8.3f}  {h['chunk_id']}  [{h['tier']}/{h['jurisdiction']}/{h['binding_status']}] "
                  f"p{h['page']} {h['clause'] or ''}\n          {h['text'][:200]!r}")
    elif a.cmd in ("eval", "evaluate"):
        from . import evaluate
        if a.v2:
            print(json.dumps(evaluate.run_v2(rerank=not a.no_rerank, tier=a.tier or "corpus"), indent=2))
        else:
            print(evaluate.table(evaluate.run(rerank=not a.no_rerank, tier=a.tier, dedupe=not a.no_dedupe)))
    elif a.cmd == "snapshot":
        from .replay import snapshot
        print(json.dumps(snapshot(), indent=1))
    elif a.cmd == "coverage":
        from .retrieve import coverage
        print(json.dumps(coverage(a.q, a.jurisdiction), indent=1))


if __name__ == "__main__":
    main()
