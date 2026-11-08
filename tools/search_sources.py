"""Page-aware full-text search over the downloaded official sources.

Usage:
    python tools/search_sources.py "battery|backup power" [--jur IN] [--doc-type act] [--context 1]

Each hit prints: source id, PDF page, and the matching line with neighbours.
Text is extracted with `pdftotext -layout` (pages split on form feeds) and cached
in kb/sources/.text/ (not committed). HTML and .docx sources are one page (page = 1).
Scanned PDFs use an OCR file kb/sources/.text/<id>.ocr.txt if present (pages offset:
the OCR covers only the pages named in sources.yaml `notes`).

Filters use the same canonical labels as the vector KB (orca/kbvec/meta.py): --jur IN|EU|US|AE|INTL
(other states are INTL) and --doc-type act|rules|direction|guideline|standard|licence|... The document type
is guessed from the source title. Sources whose extracted text is identical (duplicate downloads) are
searched once; the duplicates are listed on stderr.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "kb" / "sources"
CACHE = SRC / ".text"


def _load_meta():
    """orca/kbvec/meta.py without importing the package (which needs chromadb)."""
    spec = importlib.util.spec_from_file_location("orca_kbvec_meta", ROOT / "orca" / "kbvec" / "meta.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


meta = _load_meta()


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


def _text_key(pgs: list[str]) -> str:
    return hashlib.sha256("\f".join(pgs).encode()).hexdigest()


def search(pattern: str, jur: str | None = None, context: int = 1, doc_type: str | None = None):
    rx = re.compile(pattern, re.IGNORECASE)
    want_j = meta.canon_jurisdiction(jur) if jur else None
    want_t = meta.canon_doc_type(doc_type) if doc_type else None
    sources = yaml.safe_load((ROOT / "kb" / "sources.yaml").read_text())
    first_of: dict[str, str] = {}           # text hash -> first source id with that text
    duplicates: list[tuple[str, str]] = []
    for s in sources:
        sid = s["id"]
        if want_j and meta.canon_jurisdiction(sid.split("-")[0]) != want_j:
            continue
        if want_t and meta.canon_doc_type(meta.guess_doc_type(s.get("title", ""))) != want_t:
            continue
        pgs = pages(sid)
        if not pgs:
            continue
        key = _text_key(pgs)
        if key in first_of:
            duplicates.append((sid, first_of[key]))
            continue
        first_of[key] = sid
        for pno, page in enumerate(pgs, start=1):
            lines = page.splitlines()
            for i, line in enumerate(lines):
                if rx.search(line):
                    lo, hi = max(0, i - context), min(len(lines), i + context + 1)
                    snippet = " / ".join(l.strip() for l in lines[lo:hi] if l.strip())
                    yield sid, pno, snippet
    search.duplicates = duplicates


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern")
    ap.add_argument("--jur", help="IN, EU, US, AE or INTL (other states are INTL)")
    ap.add_argument("--doc-type", help="act, rules, direction, directive, guideline, standard, licence, ...")
    ap.add_argument("--context", type=int, default=1)
    a = ap.parse_args(argv)
    n = 0
    for sid, pno, snip in search(a.pattern, a.jur, a.context, a.doc_type):
        print(f"{sid} p.{pno}: {snip[:400]}")
        n += 1
    for dup, first in getattr(search, "duplicates", []):
        print(f"(skipped {dup}: identical text to {first})", file=sys.stderr)
    print(f"-- {n} hits", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
