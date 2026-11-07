"""Automatic exact-match quote check for staged candidate quotes (KB tier 2: auto-checked).

Reads kb/staging/<jur>/<id>.yaml, finds each candidate quote in the document's extracted text
(corpus/raw/<jur>/<id>.txt, or the local_path with .txt), and writes kb/staging/_quotecheck.yaml.

A quote passes only if it appears in the text after normalising whitespace, typographic quotes,
dashes and soft hyphens, and line-break hyphenation. Page numbers are checked when the text has
form feeds (pdftotext keeps one per page). This never sets verified: true; that stays human.

    python3 -I scripts/quote_check.py [--repo PATH]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

TRANS = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-",
                       "—": "-", " ": " ", "­": "", "ﬁ": "fi", "ﬂ": "fl"})


def norm(s: str) -> str:
    s = s.translate(TRANS)
    s = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", s)      # join words hyphenated across lines
    return re.sub(r"\s+", " ", s).strip().lower()


def find_text(repo: Path, jur: str, meta: dict) -> Path | None:
    cands = [repo / "corpus" / "raw" / jur / f"{meta.get('id')}.txt"]
    if meta.get("local_path"):
        lp = repo / meta["local_path"]
        cands += [lp.with_suffix(".txt"), lp]
    return next((p for p in cands if p.is_file() and p.suffix == ".txt"), None)


def check(repo: Path) -> dict:
    out: dict = {"summary": {}, "quotes": []}
    stats = {"pass": 0, "fail": 0, "page_mismatch": 0, "no_text": 0, "docs": 0}
    for f in sorted((repo / "kb" / "staging").glob("*/*.yaml")):
        jur = f.parent.name
        try:
            meta = yaml.safe_load(f.read_text()) or {}
        except yaml.YAMLError as e:
            out["quotes"].append({"doc": f"{jur}/{f.stem}", "result": "bad_yaml", "detail": str(e)[:200]})
            continue
        if not isinstance(meta, dict) or not meta.get("candidate_quotes"):
            continue
        stats["docs"] += 1
        txt = find_text(repo, jur, meta)
        raw = txt.read_text(errors="replace") if txt else ""
        pages = [norm(p) for p in raw.split("\f")] if "\f" in raw else None
        full = norm(raw)
        bb = norm(str(meta.get("binding_basis") or ""))
        if bb and "not stated" not in bb and txt:
            ok = len(bb) >= 15 and bb in full
            out.setdefault("binding_basis", []).append({"doc": f"{jur}/{meta.get('id', f.stem)}",
                "binding_status": meta.get("binding_status"), "result": "pass" if ok else "fail",
                "binding_basis": meta.get("binding_basis")})
            stats["binding_pass" if ok else "binding_fail"] = stats.get("binding_pass" if ok else "binding_fail", 0) + 1
        for i, q in enumerate(meta["candidate_quotes"]):
            quote = norm(str(q.get("quote", "")))
            row = {"doc": f"{jur}/{meta.get('id', f.stem)}", "n": i, "page": q.get("page"),
                   "gap": q.get("gap"), "topic": q.get("topic"), "quote": q.get("quote")}
            if not txt:
                row["result"] = "no_text"; stats["no_text"] += 1
            elif len(quote) < 20 or quote not in full:
                row["result"] = "fail"; stats["fail"] += 1
            else:
                row["result"] = "pass"; stats["pass"] += 1
                if pages:
                    found = [n for n, p in enumerate(pages, 1) if quote in p]
                    row["found_on_pages"] = found
                    if q.get("page") and found and int(q["page"]) not in found:
                        row["note"] = "page_mismatch"; stats["page_mismatch"] += 1
            out["quotes"].append(row)
    out["summary"] = stats
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    repo = Path(ap.parse_args().repo)
    res = check(repo)
    (repo / "kb" / "staging").mkdir(parents=True, exist_ok=True)
    (repo / "kb" / "staging" / "_quotecheck.yaml").write_text(
        yaml.safe_dump(res, sort_keys=False, allow_unicode=True, width=120))
    print(res["summary"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
