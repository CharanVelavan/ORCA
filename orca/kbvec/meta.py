"""Canonical jurisdiction and document-type labels for filters. Pure Python, no heavy imports.

Stored metadata is messy (staged YAML is free text: "IN-TN", "International", "rules (gazette notification)",
"master direction"). Filters use the canonical labels below; the retriever expands each one to every stored
value that maps to it, so no re-index is needed.

Jurisdictions: IN, EU, US, AE, INTL. Any other state (UK, CA, AU, JP, SG, ...) is grouped under INTL.
Document types: verified_record, faq, consultation, act, rules, direction, directive, guideline, standard,
recommendation, licence, treaty, regulation, order, policy, report, other.
"""
from __future__ import annotations

import re

JURISDICTIONS = ("IN", "EU", "US", "AE", "INTL")
DOC_TYPES = ("verified_record", "faq", "consultation", "act", "rules", "direction", "directive", "guideline",
             "standard", "recommendation", "licence", "treaty", "regulation", "order", "policy", "report", "other")

# ordered: the first rule that matches a lower-cased stored value wins
_DOC_TYPE_RULES = [
    ("verified_record", r"^verified_record$"),
    ("faq", r"\bfaq"),
    ("consultation", r"consultation|proposal|proposed|discussion paper|\bdraft|explanatory"),
    ("act", r"^act$|\bacts?\b"),
    ("rules", r"\brules?\b"),
    ("direction", r"\bdirections?\b"),
    ("directive", r"directive"),
    ("guideline", r"guideline|\bsops?\b|procedure|technical_guidance|instruction|advisory|framework"),
    ("standard", r"standard|grid code|specification"),
    ("recommendation", r"recommendation"),
    ("licence", r"licen[cs]e|authori[sz]ation"),
    ("treaty", r"treaty|convention|constitution|radio regulations"),
    ("regulation", r"regulation"),
    ("order", r"\border\b|circular|determination|regulatory_(order|decision)|notice|notification"),
    ("policy", r"policy|strategy|\bplan\b|approach|white paper"),
    ("report", r"report|study|statement of reasons|response|answer|web page|compendium|press"),
]
_DOC_TYPE_RX = [(name, re.compile(p)) for name, p in _DOC_TYPE_RULES]


def canon_jurisdiction(value) -> str:
    head = re.split(r"[-_ /]", str(value or "").strip().upper())[0]
    return head if head in ("IN", "EU", "US", "AE") else "INTL"


def canon_doc_type(value) -> str:
    s = re.sub(r"\s+", " ", str(value or "").strip().lower())
    if not s:
        return "other"
    for name, rx in _DOC_TYPE_RX:
        if rx.search(s):
            return name
    return "other"


def norm_text(value) -> str:
    """Case, space, hyphen and underscore insensitive form, for values such as 'not stated' vs 'not_stated'."""
    return re.sub(r"[\s_\-]+", " ", str(value or "").strip().lower())


def guess_doc_type(title: str) -> str:
    """Document type from a source title (used when no metadata exists), e.g. for the grep tool."""
    return canon_doc_type(title)
