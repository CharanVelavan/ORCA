"""Page-aware full-text search over the downloaded official sources.

Usage:
    python tools/search_sources.py "battery|backup power" [--jur IN] [--context 1]

Each hit prints: source id, PDF page, and the matching line with neighbours.
Text is extracted with `pdftotext -layout` (pages split on form feeds) and cached
in kb/sources/.text/ (not committed). HTML and .docx sources are one page (page = 1).
Scanned PDFs use an OCR file kb/sources/.text/<id>.ocr.txt if present (pages offset:
the OCR covers only the pages named in sources.yaml `notes`).
"""
from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "kb" / "sources"
CACHE = SRC / ".text"


def pages(source_id: str) -> list[str]:
    """Return the text of each page of a local source (1-indexed by position)."""
    CACHE.mkdir(exist_ok=True)
    cached = CACHE / f"{source_id}.txt"
    pdf, htm, docx = (SRC / f"{source_id}.{ext}" for ext in ("pdf", "html", "docx"))
    ocr = CACHE / f"{source_id}.ocr.txt"   # scanned PDFs: macOS Vision OCR text, one page per "=== " block
    if not cached.exists():
        if ocr.exists():
            text = "\f".join(re.split(r"^=== .*$", ocr.read_text(), flags=re.M)[1:])
        elif pdf.exists():
            text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                                  capture_output=True, text=True, check=True).stdout
        elif docx.exists():
            text = subprocess.run(["textutil", "-convert", "txt", "-stdout", str(docx)],
                                  capture_output=True, text=True, check=True).stdout
        elif htm.exists():
            raw = htm.read_text(errors="ignore")
            raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
            text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
            text = re.sub(r"[ \t]+", " ", text)
        else:
            return []
        cached.write_text(text)
    return cached.read_text().split("\f")


def search(pattern: str, jur: str | None = None, context: int = 1):
    rx = re.compile(pattern, re.IGNORECASE)
    sources = yaml.safe_load((ROOT / "kb" / "sources.yaml").read_text())
    for s in sources:
        sid = s["id"]
        if jur and not sid.startswith(jur.lower() + "-"):
            continue
        for pno, page in enumerate(pages(sid), start=1):
            lines = page.splitlines()
            for i, line in enumerate(lines):
                if rx.search(line):
                    lo, hi = max(0, i - context), min(len(lines), i + context + 1)
                    snippet = " / ".join(l.strip() for l in lines[lo:hi] if l.strip())
                    yield sid, pno, snippet


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern")
    ap.add_argument("--jur", help="IN, EU or AE (source id prefix)")
    ap.add_argument("--context", type=int, default=1)
    a = ap.parse_args(argv)
    n = 0
    for sid, pno, snip in search(a.pattern, a.jur, a.context):
        print(f"{sid} p.{pno}: {snip[:400]}")
        n += 1
    print(f"-- {n} hits", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
