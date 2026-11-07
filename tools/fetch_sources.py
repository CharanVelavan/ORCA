"""Download each official source in kb/sources.yaml into kb/sources/ and record its sha256.

    python tools/fetch_sources.py            # fetch missing files, fill in hashes
    python tools/fetch_sources.py --check    # re-hash local files, report changes

The downloaded files are what ChromaDB indexes for retrieval. They are not committed;
the hashes are, so anyone can check they have the same documents.
"""
import argparse
import hashlib
import re
import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "kb" / "sources.yaml"
OUT = ROOT / "kb" / "sources"
UA = "ORCA-NTN-kb-fetch/0.1"


def local_path(src: dict) -> Path:
    url = src["url"].lower().split("?")[0]
    # India Code serves PDFs from .../bitstreams/<uuid>/content (no .pdf suffix).
    is_pdf = url.endswith((".pdf", ".ashx")) or "/server/api/core/bitstreams/" in url
    ext = ".pdf" if is_pdf else ".html"
    return OUT / (src["id"] + ext)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    text = SOURCES.read_text()
    sources = yaml.safe_load(text)
    failed = 0
    for s in sources:
        p = local_path(s)
        if not p.exists() and not args.check:
            try:
                req = urllib.request.Request(s["url"], headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=60) as r:
                    p.write_bytes(r.read())
            except Exception as e:  # report and continue with the others
                print(f"FAIL {s['id']}: {e}")
                failed += 1
                continue
        if not p.exists():
            print(f"MISSING {s['id']}")
            continue
        h = sha256(p)
        if s.get("sha256") and s["sha256"] != h:
            print(f"CHANGED {s['id']}: {s['sha256'][:12]} -> {h[:12]}")
        elif not s.get("sha256"):
            # Fill in the hash in place, keeping the file's comments and layout.
            text = re.sub(rf"(- id: {re.escape(s['id'])}\n(?:  .*\n)*?  sha256: )null",
                          rf"\g<1>{h}", text, count=1)
            print(f"OK {s['id']} {h[:12]} ({p.stat().st_size // 1024} KB)")
        else:
            print(f"OK {s['id']} unchanged")
    if not args.check:
        SOURCES.write_text(text)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
