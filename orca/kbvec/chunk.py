"""Page text -> clause-level chunks (~512 tokens, 50 overlap, split on legal headings and sub-clauses).

Supports legal hierarchy:
Rule / Section / Article / Regulation / Direction N > (1) > (a) > (i)
Canonical paths: "Rule 7(1)(a)", "Section 8(6)", "Direction (ii)", "Annexure I, item (ix)".
Headings open a new clause. Sub-clauses stay with their own text and inherit parent context.
"""
from __future__ import annotations

import re

from .config import CHUNK_OVERLAP, CHUNK_TOKENS

WORDS_PER_TOKEN = 1 / 1.35            # rough: 1 word ~ 1.35 tokens for English legal text
MAX_WORDS = int(CHUNK_TOKENS * WORDS_PER_TOKEN)
OVERLAP_WORDS = int(CHUNK_OVERLAP * WORDS_PER_TOKEN)
MIN_WORDS = 60                         # tiny sections are merged into the previous chunk (within same section)

_ROMAN_SET = {"i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x",
              "xi", "xii", "xiii", "xiv", "xv", "xvi", "xvii", "xviii", "xix", "xx"}

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
_SUB_ARABIC = re.compile(r"^\((\d{1,3}[A-Z]?)\)\s*(?=\S)")
_SUB_LETTER = re.compile(r"^\(([a-z]{1,2})\)\s*(?=\S)")
_SUB_ROMAN_PAREN = re.compile(r"^\(([ivx]{1,7})\)\s*(?=\S)", re.I)
_SUB_ROMAN_DOT = re.compile(r"^([ivx]{1,7})\.\s+(?=\S)", re.I)
_INLINE_SUB = re.compile(r"[.—–-]+\s*\((\d{1,3}[A-Z]?)\)\s+")
_TRAILING_SUB = re.compile(r"\s*\([ivxlcdm0-9a-z]+\)$", re.I)


def _valid_roman(s: str) -> bool:
    return bool(s) and (s.lower() in _ROMAN_SET or bool(re.fullmatch(_ROMAN, s.lower())))


def parse_clause_path(clause: str) -> tuple[str, str | None, str | None, str | None]:
    """Parse a canonical clause path into (h0, h1, h2, h3)."""
    if not clause:
        return ("", None, None, None)
    m = re.match(r"^(Annexure\s+[IVXL]+|\bSchedule\s+[IVXL\d]+),\s*item\s*(\([a-z0-9]+\))$", clause, re.I)
    if m:
        return (m.group(1), None, None, m.group(2))
    m = re.match(r"^(Direction)\s+(\([ivx]+\))$", clause, re.I)
    if m:
        return (m.group(1), None, None, m.group(2))
    m = re.match(r"^(Direction\s+\d+[A-Z]?)\s+(\([ivx]+\))$", clause, re.I)
    if m:
        return (m.group(1), None, None, m.group(2))
    m = re.match(r"^\(([ivx]+)\)$", clause, re.I)
    if m:
        return ("", None, None, f"({m.group(1).lower()})")
    m = re.match(r"^([^(]+?)(?:\((\d+[A-Z]?)\))?(?:\(([a-z]{1,2})\))?(?:\(([ivx]+)\))?$", clause)
    if m and any(m.groups()[1:]):
        h0, h1, h2, h3 = m.groups()
        return (h0.strip(), f"({h1})" if h1 else None, f"({h2})" if h2 else None, f"({h3})" if h3 else None)
    return (clause.strip(), None, None, None)


def base_of(clause: str) -> str:
    """The heading a sub-clause label hangs from: 'Direction (iv)' -> 'Direction', 'Rule 7(1)(a)' -> 'Rule 7'."""
    h0, _, _, _ = parse_clause_path(clause)
    return h0 or _TRAILING_SUB.sub("", clause or "").strip()


def parent_of(clause: str) -> str:
    """Return the top-level section/heading for parent chunk grouping: 'Rule 7(1)(a)' -> 'Rule 7'."""
    h0, _, _, _ = parse_clause_path(clause)
    return h0 or base_of(clause)


def sub_clause(line: str, base: str = "") -> str | None:
    """Return the clause label if the line opens a Roman or chapter sub-clause, else None."""
    s = line.strip()
    if not s:
        return None
    m = _SUB_CHAPTER.match(s)
    if m and _valid_roman(m.group(2)):
        return re.sub(r"\s+", " ", m.group(1)).replace(" (", "(")
    for rx in (_SUB_PAREN, _SUB_DOT):
        m = rx.match(s)
        if m and _valid_roman(m.group(1)):
            marker = f"({m.group(1).lower()})"
            return f"{base} {marker}".strip() if base else marker
    return None


def heading(line: str, doc_type: str = "") -> str | None:
    """Return a clause label if the line opens a rule/section/article, else None."""
    s = line.strip()
    if not s or len(s) > 200:
        return None
    m = _KEYWORD.match(s)
    if m:
        return m.group(0).strip()
    m = _NUMBERED.match(s)
    if m:
        dt = (doc_type or "").lower()
        if "rule" in dt:
            kind = "Rule"
        elif "act" in dt:
            kind = "Section"
        elif "regulat" in dt:
            kind = "Regulation"
        elif "direct" in dt:
            kind = "Direction"
        else:
            kind = "Section"
        return f"{kind} {m.group(1)}"
    m = _PARA.match(s)
    if m:
        return f"para {m.group(1)}"
    return None


def build_clause_str(h0: str, h1: str | None, h2: str | None, h3: str | None) -> str:
    if not h0:
        return (h1 or "") + (h2 or "") + (h3 or "")
    if re.match(r"^(Annexure|Schedule)\s+[IVXL\d]+", h0, re.I):
        if h3:
            return f"{h0}, item {h3}"
        return f"{h0}{h1 or ''}"
    if h0 == "Direction":
        if h3:
            return f"Direction {h3}"
        return "Direction"
    if re.match(r"^Direction\s+\d+", h0, re.I):
        if h3 and not h1 and not h2:
            return f"{h0} {h3}"
    return f"{h0}{h1 or ''}{h2 or ''}{h3 or ''}"


def _parse_line(line: str, h0: str, h1: str | None, h2: str | None, h3: str | None, doc_type: str = ""):
    s = line.strip()
    if not s:
        return None
    # 1. Sub chapter like "XI B(v)"
    m = _SUB_CHAPTER.match(s)
    if m and _valid_roman(m.group(2)):
        lbl = re.sub(r"\s+", " ", m.group(1)).replace(" (", "(")
        return (lbl, None, None, None, True, "")

    # 2. Check if Annexure / Schedule item
    if h0 and re.match(r"^(Annexure|Schedule)\s+[IVXL\d]+", h0, re.I):
        m = _SUB_ROMAN_DOT.match(s) or _SUB_ROMAN_PAREN.match(s)
        if m and _valid_roman(m.group(1)):
            new_h3 = f"({m.group(1).lower()})"
            return (h0, None, None, new_h3, True, h0)

    # 3. Heading check
    if len(s) <= 200:
        m = _KEYWORD.match(s)
        if m:
            new_h0 = m.group(0).strip()
            m_in = _INLINE_SUB.search(s)
            new_h1 = f"({m_in.group(1)})" if m_in else None
            return (new_h0, new_h1, None, None, False, "")
        m = _NUMBERED.match(s)
        if m:
            dt = doc_type.lower()
            if "rule" in dt:
                kind = "Rule"
            elif "act" in dt:
                kind = "Section"
            elif "regulat" in dt:
                kind = "Regulation"
            elif "direct" in dt:
                kind = "Direction"
            elif h0 and h0.split()[0] in ("Rule", "Section", "Article", "Regulation", "Direction"):
                kind = h0.split()[0]
            else:
                kind = "Section"
            new_h0 = f"{kind} {m.group(1)}"
            m_in = _INLINE_SUB.search(s)
            new_h1 = f"({m_in.group(1)})" if m_in else None
            return (new_h0, new_h1, None, None, False, "")
        m = _PARA.match(s)
        if m:
            return (f"para {m.group(1)}", None, None, None, False, "")

    # 4. Check if document is Directions and line starts with (i)..(xx)
    is_direction_doc = "direction" in doc_type.lower() or (h0 and "direction" in h0.lower())
    if is_direction_doc and not h1 and not h2:
        m = _SUB_ROMAN_PAREN.match(s)
        if m and _valid_roman(m.group(1)):
            new_h3 = f"({m.group(1).lower()})"
            base_dir = h0 if (h0 and "Direction" in h0) else "Direction"
            return (base_dir, None, None, new_h3, True, base_dir)

    # 5. Arabic sub-clause: (1), (2), (12)
    m = _SUB_ARABIC.match(s)
    if m:
        new_h1 = f"({m.group(1)})"
        return (h0, new_h1, None, None, True, h0)

    # 6. Letter or Roman sub-clause
    m_let = _SUB_LETTER.match(s)
    m_rom = _SUB_ROMAN_PAREN.match(s) or _SUB_ROMAN_DOT.match(s)
    if m_let:
        val = m_let.group(1).lower()
        if not _valid_roman(val):
            new_h2 = f"({val})"
            return (h0, h1, new_h2, None, True, h0)
        else:
            if h2 and len(h2.strip("()")) == 1 and len(val) == 1 and ord(val) == ord(h2.strip("()")) + 1:
                new_h2 = f"({val})"
                return (h0, h1, new_h2, None, True, h0)
            elif h2:
                new_h3 = f"({val})"
                return (h0, h1, h2, new_h3, True, h0)
            elif h1:
                new_h3 = f"({val})"
                return (h0, h1, None, new_h3, True, h0)
            else:
                new_h3 = f"({val})"
                return (h0, None, None, new_h3, True, h0)

    if m_rom and _valid_roman(m_rom.group(1)):
        val = m_rom.group(1).lower()
        new_h3 = f"({val})"
        return (h0, h1, h2, new_h3, True, h0)

    return None


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


def chunk_page(text: str, carry_clause: str = "", doc_type: str = "") -> tuple[list[dict], str]:
    """Split one page into clause-level chunks (~512 tokens, 50 overlap, split on legal headings and sub-clauses)."""
    h0, h1, h2, h3 = parse_clause_path(carry_clause)
    base = h0
    sections: list[list] = [[carry_clause, [], False, base, False]]

    for line in text.splitlines():
        parsed = _parse_line(line, h0, h1, h2, h3, doc_type)
        if parsed:
            h0, h1, h2, h3, is_sub, parent = parsed
            label = build_clause_str(h0, h1, h2, h3)
            base = h0
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
        same_section = bool(merged and base_of(clause) == base_of(merged[-1][0]))
        if merged and n < MIN_WORDS and not is_sub and same_section and len(merged[-1][1].split()) + n <= MAX_WORDS:
            merged[-1][1] = merged[-1][1] + " " + body
        else:
            merged.append([clause, body, is_sub, parent, labelled])

    out = []
    for clause, body, is_sub, parent, labelled in merged:
        # sub-clause windows reserve room for their prefix so the chunk stays within MAX_WORDS
        room = MAX_WORDS - (len(clause.split()) + 1 if is_sub and clause else 0)
        for idx, w in enumerate(_windows(body.split(), room)):
            prefix = ""
            if is_sub and idx == 0 and labelled and parent and not body.startswith(parent):
                prefix = f"{parent}. "                    # the marker is already in the text
            elif is_sub and clause and not (idx == 0 and labelled):
                prefix = f"{clause}. "                    # continuation window, or carried over from last page
            min_len = 2 if is_sub else 5
            if len(w) >= min_len:
                out.append({"text": (prefix + " ".join(w)).strip(), "clause": clause})
    return out, sections[-1][0]
