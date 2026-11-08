"""Page text -> clause-level chunks (~512 tokens, 50 overlap, split on legal headings and sub-clauses).

Headings (Article, Section, Rule, Direction, numbered sections, paragraph numbers) open a new clause.
Roman sub-clauses ("(iv) ...", "iv. ...", "(iii)When ...") and chapter sub-clauses ("XI B(v) ...") also open
a new section, so each stays with its own text. A sub-clause label is "<heading> (iv)", and its chunk text
starts with the parent heading (for example "Direction 2. (iv) ..."). A sub-clause that runs on for more
than one window repeats its label on every window. Sections without sub-clauses are chunked exactly as
before, so chunks on other pages keep their text (and their stored embeddings). Tiny sections merge into the
previous one, except sub-clauses, which keep their own chunk.
"""
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
# lowercase roman numerals 1-39 only (no c, d, l, m: those collide with list letters)
_ROMAN = r"x{0,3}(?:ix|iv|v?i{0,3})"
_SUB_PAREN = re.compile(rf"^\(({_ROMAN})\)\s*(?=\S)")          # "(iv) text", "(iii)When"
_SUB_DOT = re.compile(rf"^({_ROMAN})\.\s+(?=\S)")              # "v. Assure ..." (list style)
_SUB_CHAPTER = re.compile(r"^((?:[IVXL]{1,6}\s+)?[A-Z]{1,2}\s*\(([ivx]{1,7})\))(?=\s|[A-Za-z])")  # "XI B(v)"
_TRAILING_SUB = re.compile(r"\s*\([ivxlcdm]+\)$")


def _valid_roman(s: str) -> bool:
    return bool(s) and bool(re.fullmatch(_ROMAN, s))


def sub_clause(line: str, base: str = "") -> str | None:
    """Return the clause label if the line opens a Roman sub-clause, else None."""
    s = line.strip()
    if not s:
        return None
    m = _SUB_CHAPTER.match(s)
    if m and _valid_roman(m.group(2)):
        return re.sub(r"\s+", " ", m.group(1)).replace(" (", "(")
    for rx in (_SUB_PAREN, _SUB_DOT):
        m = rx.match(s)
        if m and _valid_roman(m.group(1)):
            marker = f"({m.group(1)})"
            return f"{base} {marker}".strip() if base else marker
    return None


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


def base_of(clause: str) -> str:
    """The heading a sub-clause label hangs from: 'Direction (iv)' -> 'Direction'."""
    return _TRAILING_SUB.sub("", clause or "").strip()


def _windows(words: list[str], limit: int) -> list[list[str]]:
    if len(words) <= limit:
        return [words]
    step = max(1, limit - OVERLAP_WORDS)
    out, i = [], 0
    while i < len(words):
        out.append(words[i:i + limit])
        if i + limit >= len(words):
            break
        i += step
    return out


def chunk_page(text: str, carry_clause: str = "") -> tuple[list[dict], str]:
    """Split one page. Returns ([{text, clause}], clause in force at the end of the page)."""
    # section = [clause label, lines, is_sub_clause, parent heading, label line is in this page's text]
    sections: list[list] = [[carry_clause, [], False, base_of(carry_clause), False]]
    base = base_of(carry_clause)
    for line in text.splitlines():
        sub = sub_clause(line, base)
        h = None if sub else heading(line)
        if sub or h:
            if sub:
                label, is_sub = sub, True
                parent = "" if _SUB_CHAPTER.match(line.strip()) else base   # "XI B(v)" carries its own label
            else:
                label, is_sub, parent = h, False, ""
                base = h
            if sections[-1][1]:
                sections.append([label, [], is_sub, parent, True])
            else:
                sections[-1][0], sections[-1][2], sections[-1][3], sections[-1][4] = label, is_sub, parent, True
        if line.strip():
            sections[-1][1].append(re.sub(r"\s+", " ", line.strip()))
    merged: list[list] = []                   # [clause, body, is_sub, parent, labelled]
    for clause, lines, is_sub, parent, labelled in sections:
        body = " ".join(lines).strip()
        if not body:
            continue
        n = len(body.split())
        if merged and n < MIN_WORDS and not is_sub and len(merged[-1][1].split()) + n <= MAX_WORDS:
            merged[-1][1] = merged[-1][1] + " " + body
        else:
            merged.append([clause, body, is_sub, parent, labelled])
    out = []
    for clause, body, is_sub, parent, labelled in merged:
        # sub-clause windows reserve room for their prefix so the chunk stays within MAX_WORDS
        room = MAX_WORDS - (len(clause.split()) + 1 if is_sub and clause else 0)
        for idx, w in enumerate(_windows(body.split(), room)):
            prefix = ""
            if is_sub and idx == 0 and labelled and parent:
                prefix = f"{parent}. "                    # the marker is already in the text
            elif is_sub and clause and not (idx == 0 and labelled):
                prefix = f"{clause}. "                    # continuation window, or carried over from last page
            if len(w) >= 5:
                out.append({"text": (prefix + " ".join(w)).strip(), "clause": clause})
    return out, sections[-1][0]
