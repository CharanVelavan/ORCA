"""Page text -> clause-level chunks (~512 tokens, 50 overlap, split on legal headings)."""
from __future__ import annotations

import re

from .config import CHUNK_OVERLAP, CHUNK_TOKENS

WORDS_PER_TOKEN = 1 / 1.35            # rough: 1 word ~ 1.35 tokens for English legal text
MAX_WORDS = int(CHUNK_TOKENS * WORDS_PER_TOKEN)
OVERLAP_WORDS = int(CHUNK_OVERLAP * WORDS_PER_TOKEN)
MIN_WORDS = 60                         # tiny sections are merged into the previous chunk

_KEYWORD = re.compile(
    r"^(Article|Section|Rule|Regulation|Direction|Clause|Annexure|Annex|Chapter|Part|Schedule)"
    r"\s+([0-9]+[A-Z]?|[IVXL]+)(\s*\([0-9a-zA-Z]+\))*", re.I)
_NUMBERED = re.compile(r"^(\d{1,3}[A-Z]?)\.\s+\S")
_PARA = re.compile(r"^(\d+(?:\.\d+){1,4})\s+[A-Z]")


def heading(line: str) -> str | None:
    """Return a clause label if the line opens a rule/section/article, else None."""
    s = line.strip()
    if not s or len(s) > 200:
        return None
    m = _KEYWORD.match(s)
    if m:
        return m.group(0).strip()
    m = _NUMBERED.match(s)
    if m:
        return f"s.{m.group(1)}"
    m = _PARA.match(s)
    if m:
        return f"para {m.group(1)}"
    return None


def _windows(words: list[str]) -> list[list[str]]:
    if len(words) <= MAX_WORDS:
        return [words]
    out, i = [], 0
    while i < len(words):
        out.append(words[i:i + MAX_WORDS])
        if i + MAX_WORDS >= len(words):
            break
        i += MAX_WORDS - OVERLAP_WORDS
    return out


def chunk_page(text: str, carry_clause: str = "") -> tuple[list[dict], str]:
    """Split one page. Returns ([{text, clause}], clause in force at the end of the page)."""
    sections: list[tuple[str, list[str]]] = [(carry_clause, [])]
    for line in text.splitlines():
        h = heading(line)
        if h and sections[-1][1]:
            sections.append((h, []))
        elif h:
            sections[-1] = (h, sections[-1][1])
        if line.strip():
            sections[-1][1].append(re.sub(r"\s+", " ", line.strip()))
    merged: list[tuple[str, str]] = []
    for clause, lines in sections:
        body = " ".join(lines).strip()
        if not body:
            continue
        n = len(body.split())
        if merged and n < MIN_WORDS and len(merged[-1][1].split()) + n <= MAX_WORDS:
            merged[-1] = (merged[-1][0], merged[-1][1] + " " + body)
        else:
            merged.append((clause, body))
    out = []
    for clause, body in merged:
        for w in _windows(body.split()):
            if len(w) >= 5:
                out.append({"text": " ".join(w), "clause": clause})
    return out, sections[-1][0]
