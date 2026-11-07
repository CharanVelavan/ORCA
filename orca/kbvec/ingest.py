"""Parse sources and verified records into chunks, embed, store. Incremental by sha256."""
from __future__ import annotations

import hashlib
import re
import sys
import time
from pathlib import Path

import yaml

from . import config, embed as emb, store
from .chunk import chunk_page

DOC_TYPES = [("act", r"\bact\b"), ("rules", r"\brules?\b"), ("directions", r"direction"),
             ("directive", r"directive"), ("regulation", r"regulation"), ("licence", r"licen[cs]e|authori[sz]ation"),
             ("guidelines", r"guideline|framework|sop|procedure"), ("standard", r"standard|itsar|recommendation|3gpp|itu-t"),
             ("faq", r"\bfaq"), ("press_release", r"\bpib\b|press"), ("report", r"report|study")]
PREFIX_JURIS = {"in": "IN", "eu": "EU", "us": "US", "ae": "AE", "intl": "INTL"}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _text_sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def guess_doc_type(title: str) -> str:
    t = title.lower()
    for name, pat in DOC_TYPES:
        if re.search(pat, t):
            return name
    return "other"


# ---------------------------------------------------------------- parsing (documents are untrusted data)
def _pages_from_pdf(p: Path) -> list[str]:
    import fitz
    with fitz.open(p) as d:
        return [pg.get_text("text") for pg in d]


def _pages_from_html(p: Path) -> list[str]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(p.read_text(errors="replace"), "html.parser")
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    text = soup.get_text("\n")
    return [re.sub(r"\n\s*\n+", "\n", text)]


def parse_pages(path: Path, sidecar: Path | None = None) -> list[str]:
    """Return a list of page texts (index 0 = page 1). Never executes or follows anything in the file."""
    if sidecar and sidecar.exists() and sidecar.stat().st_size > 200:
        return sidecar.read_text(errors="replace").split("\f")
    suf = path.suffix.lower()
    if suf == ".pdf":
        return _pages_from_pdf(path)
    if suf in (".html", ".htm"):
        return _pages_from_html(path)
    if suf in (".txt", ".md"):
        return path.read_text(errors="replace").split("\f")
    raise ValueError(f"unsupported file type {suf}")


# ---------------------------------------------------------------- metadata
def _load_yaml(p: Path):
    return yaml.safe_load(p.read_text()) or [] if p.exists() else []


def _records() -> list[dict]:
    out = []
    for f in config.records_files():
        out += _load_yaml(f)
    return out


def official_sources() -> list[dict]:
    """kb/sources.yaml entries whose file exists, with metadata derived from the verified records."""
    recs = _records()
    by_src: dict[str, list[dict]] = {}
    for r in recs:
        by_src.setdefault(r["source"], []).append(r)
    out = []
    for s in _load_yaml(config.sources_yaml()):
        files = [f for f in config.sources_dir().glob(s["id"] + ".*") if f.is_file()]
        if not files:
            continue
        rs = by_src.get(s["id"], [])
        binding = max({r["binding_status"] for r in rs}, key=[r["binding_status"] for r in rs].count) if rs else "not_stated"
        starts = sorted(str(r["in_force_from"]) for r in rs if r.get("in_force_from"))
        side = config.sources_dir() / ".text" / (s["id"] + ".txt")
        out.append({
            "source_id": s["id"], "title": s["title"], "authority": s.get("authority", ""),
            "jurisdiction": PREFIX_JURIS.get(s["id"].split("-")[0], "INTL"),
            "doc_type": guess_doc_type(s["title"]), "binding_status": binding,
            "in_force_from": starts[0] if starts else "", "licence": "official publication (reuse terms not checked)",
            "url": s.get("url", ""), "path": files[0], "sidecar": side if side.exists() else None,
            "tier": "corpus"})
    return out


def corpus_sources() -> list[dict]:
    """Staged downloads: kb/staging/<india|global>/<id>.yaml with files under corpus/raw."""
    out = []
    reg = _load_yaml(config.sources_yaml()) or []
    registered = {s["id"] for s in reg} | {s["sha256"] for s in reg if s.get("sha256")}
    for y in sorted(config.staging_dir().glob("*/*.yaml")):
        if y.name.startswith("_"):                 # pipeline outputs (_quotecheck etc.), not documents
            continue
        m = _load_yaml(y)
        if isinstance(m, list):
            m = m[0] if m else {}
        if not isinstance(m, dict) or not m.get("id") or not m.get("local_path"):
            continue
        # gates: downloaded OK, official domain, not a re-download of a registered source
        if m.get("status") != "ok" or m.get("official_domain") is False or str(m["id"]) in registered \
                or str(m.get("sha256") or "") in registered:
            continue
        lp = Path(m["local_path"])
        cands = [lp] if lp.is_absolute() else [config.MAIN_REPO / lp, config.corpus_dir().parent / lp, config.corpus_dir() / lp]
        f = next((c for c in cands if c.is_file()), None)
        if f is None:
            continue
        out.append({
            "source_id": str(m["id"]), "title": m.get("title", m["id"]), "authority": m.get("authority", ""),
            "jurisdiction": m.get("jurisdiction") or ("IN" if y.parent.name == "india" else "INTL"),
            "doc_type": m.get("doc_type", guess_doc_type(str(m.get("title", "")))),
            "binding_status": m.get("binding_status", "not_stated"),
            "in_force_from": str(m.get("in_force_from") or ""), "licence": str(m.get("licence") or "not_stated"),
            "url": m.get("url", ""), "path": f, "sidecar": None, "tier": "corpus"})
    return out


def source_chunks(src: dict) -> list[dict]:
    pages = parse_pages(src["path"], src.get("sidecar"))
    sha = sha256_file(src["path"])
    rows, clause = [], ""
    for pno, text in enumerate(pages, start=1):
        chunks, clause = chunk_page(text, clause)
        for n, c in enumerate(chunks):
            rows.append({"id": f"{src['source_id']}:p{pno}:c{n}", "text": c["text"], "meta": {
                "source_id": src["source_id"], "title": src["title"], "authority": src["authority"],
                "jurisdiction": src["jurisdiction"], "doc_type": src["doc_type"],
                "binding_status": src["binding_status"], "in_force_from": src["in_force_from"],
                "licence": src["licence"], "page": pno, "clause": c["clause"], "sha256": sha,
                "url": src["url"], "tier": src["tier"]}})
    return rows


def record_chunks() -> list[dict]:
    srcs = {s["id"]: s for s in _load_yaml(config.sources_yaml())}
    rows = []
    for r in _records():
        s = srcs.get(r["source"], {})
        m = re.search(r"(?:PDF p\.|Gazette p\.|\bp\.)\s*(\d+)", r.get("pinpoint") or "")
        quote = r.get("quote") or ""
        text = f"{r['instrument']}, {r['clause']}. {quote} Summary: {r['summary']}".strip()
        rows.append({"id": r["id"], "text": text, "meta": {
            "source_id": r["source"], "title": r["instrument"], "authority": r.get("authority", ""),
            "jurisdiction": r["jurisdiction"], "doc_type": "verified_record",
            "binding_status": r["binding_status"], "in_force_from": str(r.get("in_force_from") or ""),
            "licence": "official publication (quote)", "page": int(m.group(1)) if m else 0,
            "clause": r["clause"], "sha256": s.get("sha256", ""), "url": s.get("url", ""),
            "tier": "verified"}})
    return rows


# ---------------------------------------------------------------- incremental write
def _upsert(rows: list[dict], what: str, log) -> int:
    """Embed and write rows whose text changed. Returns number written."""
    col = store.collection()
    have = {}
    for off in range(0, col.count(), 2000):
        g = col.get(limit=2000, offset=off, include=["metadatas"])
        have.update({i: m for i, m in zip(g["ids"], g["metadatas"])})
    model = config.embed_model()
    todo = []
    for r in rows:
        r["meta"]["text_sha"] = _text_sha(r["text"])
        r["meta"]["embed_model"] = model
        old = have.get(r["id"])
        if not old or old.get("text_sha") != r["meta"]["text_sha"] or old.get("embed_model") != model:
            todo.append(r)
    if not todo:
        return 0
    t0 = time.time()
    B = 64
    for i in range(0, len(todo), B):
        part = todo[i:i + B]
        vecs = emb.embed([p["text"] for p in part])
        col.upsert(ids=[p["id"] for p in part], embeddings=vecs, documents=[p["text"] for p in part],
                   metadatas=[p["meta"] for p in part])
        log(f"  {what}: {min(i + B, len(todo))}/{len(todo)} chunks embedded ({time.time() - t0:.0f}s)")
    return len(todo)


def _drop_stale(source_id: str, keep_ids: set[str]) -> None:
    col = store.collection()
    got = col.get(where={"$and": [{"source_id": source_id}, {"tier": "corpus"}]}, include=[])
    stale = [i for i in got["ids"] if i not in keep_ids]
    if stale:
        col.delete(ids=stale)


def ingest(corpus: bool = False, log=print) -> dict:
    t0 = time.time()
    stats = {"sources": 0, "chunks_total": 0, "chunks_embedded": 0, "skipped_sources": 0, "errors": []}
    srcs = official_sources() + (corpus_sources() if corpus else [])
    col = store.collection()
    for s in srcs:
        sha = sha256_file(s["path"])
        got = col.get(where={"$and": [{"source_id": s["source_id"]}, {"tier": "corpus"}]}, limit=1, include=["metadatas"])
        unchanged = (got["ids"] and got["metadatas"][0].get("sha256") == sha
                     and got["metadatas"][0].get("embed_model") == config.embed_model())
        if unchanged:
            stats["skipped_sources"] += 1
            continue
        try:
            rows = source_chunks(s)
        except Exception as e:
            stats["errors"].append(f"{s['source_id']}: {e}")
            log(f"  SKIP {s['source_id']}: {e}")
            continue
        if not rows:
            stats["errors"].append(f"{s['source_id']}: no text (scanned? needs OCR)")
            log(f"  SKIP {s['source_id']}: no extractable text (needs OCR)")
            continue
        log(f"{s['source_id']}: {len(rows)} chunks")
        _drop_stale(s["source_id"], {r["id"] for r in rows})
        stats["chunks_embedded"] += _upsert(rows, s["source_id"], log)
        stats["sources"] += 1
    recs = record_chunks()
    stats["chunks_embedded"] += _upsert(recs, "verified records", log)
    stats["verified_records"] = len(recs)
    stats["chunks_total"] = store.collection().count()
    stats["seconds"] = round(time.time() - t0, 1)
    from . import retrieve
    retrieve.invalidate()
    return stats
