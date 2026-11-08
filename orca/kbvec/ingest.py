"""Parse sources and verified records into chunks, embed, store. Incremental by sha256."""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

import yaml

from . import config, store
from .chunk import base_of, chunk_page, parent_of
from .meta import canon_doc_type, canon_jurisdiction

DOC_TYPES = [("directions", r"\bdirections?\b"), ("act", r"\bact\b"), ("rules", r"\brules?\b"),
             ("directive", r"directive"), ("regulation", r"regulation"), ("licence", r"licen[cs]e|authori[sz]ation"),
             ("guidelines", r"guideline|framework|sop|procedure"), ("standard", r"standard|itsar|recommendation|3gpp|itu-t"),
             ("faq", r"\bfaq"), ("press_release", r"\bpib\b|press"), ("report", r"report|study")]
PREFIX_JURIS = {"in": "IN", "inspace": "IN", "eu": "EU", "us": "US", "ae": "AE", "intl": "INTL"}


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


def corpus_sources(corpus_root: Path | None = None, staging: Path | None = None) -> list[dict]:
    """Staged downloads: kb/staging/<india|global>/<id>.yaml with files under corpus/raw."""
    out = []
    reg = _load_yaml(config.sources_yaml()) or []
    registered = {s["id"] for s in reg} | {s["sha256"] for s in reg if s.get("sha256")}
    explicit_root = corpus_root is not None
    corpus_root = corpus_root or config.corpus_dir()
    staging = staging or config.staging_dir()
    for y in sorted(staging.glob("*/*.yaml")):
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
        # The Colab archive is rooted at the repository's corpus/ directory;
        # staged metadata deliberately remains in git and retains repo-relative
        # paths such as corpus/raw/india/doc.pdf.
        cands = [lp] if lp.is_absolute() else ([corpus_root.parent / lp, corpus_root / lp, corpus_root / lp.name]
                                                if explicit_root else [config.MAIN_REPO / lp, corpus_root.parent / lp,
                                                                         corpus_root / lp, corpus_root / lp.name])
        f = next((c for c in cands if c.is_file()), None)
        if f is None:
            continue
        out.append({
            "source_id": str(m["id"]), "title": m.get("title", m["id"]), "authority": m.get("authority", ""),
            "jurisdiction": canon_jurisdiction(m.get("jurisdiction") or ("IN" if y.parent.name == "india" else "INTL")),
            "doc_type": canon_doc_type(m.get("doc_type", guess_doc_type(str(m.get("title", ""))))),
            "binding_status": m.get("binding_status", "not_stated"),
            "in_force_from": str(m.get("in_force_from") or ""), "licence": str(m.get("licence") or "not_stated"),
            "url": m.get("url", ""), "path": f, "sidecar": None, "tier": "corpus",
            "lang": m.get("language", "en"), "amends": m.get("amends") or [],
            "amended_by": m.get("amended_by") or []})
    return out


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "preamble"


def _header(meta: dict) -> str:
    clause = meta.get("clause_path") or meta.get("clause") or "preamble"
    force = meta.get("in_force_from") or "not stated"
    return (f"{meta.get('title', '')} | {meta.get('authority', '')} | {meta.get('jurisdiction', '')} | "
            f"{meta.get('binding_status', 'not_stated')}, in force {force} | {clause} | p.{meta.get('page', 0)}")


def v2_source_chunks(src: dict) -> list[dict]:
    """Produce embeddable clause rows plus independent parent-section rows.

    This is intentionally file-system only, so the same function runs from a
    clean clone in Colab before Chroma, an embedding endpoint, or a GPU exist.
    """
    pages, sha, clauses, carry = parse_pages(src["path"], src.get("sidecar")), sha256_file(src["path"]), [], ""
    doc_type = src.get("doc_type", "")
    for page, body in enumerate(pages, 1):
        bits, carry = chunk_page(body, carry, doc_type=doc_type)
        for ordinal, bit in enumerate(bits):
            path = bit["clause"] or "Preamble"
            parent_path = parent_of(path)
            parent_id = f"{src['source_id']}:s:{_slug(parent_path)}"
            meta = {"source_id": src["source_id"], "title": src["title"], "authority": src["authority"],
                    "jurisdiction": canon_jurisdiction(src["jurisdiction"]), "doc_type": canon_doc_type(src["doc_type"]),
                    "binding_status": src["binding_status"], "in_force_from": src["in_force_from"],
                    "licence": src["licence"], "page": page, "clause": path, "clause_path": path,
                    "parent_id": parent_id, "level": "clause", "lang": src.get("lang", "en"), "sha256": sha,
                    "url": src["url"], "tier": src["tier"],
                    # Chroma metadata accepts scalar values only; preserve link
                    # lists losslessly for retrieval as compact JSON.
                    "amendment_links": json.dumps(list(src.get("amends") or []) + list(src.get("amended_by") or []))}
            clauses.append({"id": f"{src['source_id']}:p{page}:c{ordinal}",
                            "text": _header(meta) + "\n" + bit["text"], "meta": meta})
    parents: dict[str, list[dict]] = {}
    for row in clauses:
        parents.setdefault(row["meta"]["parent_id"], []).append(row)
    output = clauses[:]
    for parent_id, children in parents.items():
        words = " ".join(r["text"].split("\n", 1)[-1] for r in children).split()
        first = children[0]
        parent_path = parent_of(first["meta"]["clause_path"])
        # Parent chunks are bounded independently; a suffix avoids duplicate ids
        # for unusually long statutory sections.
        for n in range(0, len(words), 2000):
            meta = dict(first["meta"], level="parent", clause=parent_path, clause_path=parent_path,
                        parent_id=parent_id)
            suffix = "" if n == 0 else f":{n // 2000 + 1}"
            output.append({"id": parent_id + suffix, "text": _header(meta) + "\n" + " ".join(words[n:n + 2000]),
                           "meta": meta})
    return output


def build_chunks(corpus: bool = False, corpus_root: Path | None = None, sources_root: Path | None = None,
                 out: Path | None = None) -> dict:
    """Write portable v2 JSONL and a content manifest without embeddings."""
    corpus_root = corpus_root or config.corpus_dir()
    old_sources = os.environ.get("ORCA_KB_SOURCES")
    if sources_root is not None:
        os.environ["ORCA_KB_SOURCES"] = str(sources_root)
    try:
        srcs = official_sources() + (corpus_sources(corpus_root) if corpus else [])
    finally:
        if sources_root is not None:
            if old_sources is None:
                os.environ.pop("ORCA_KB_SOURCES", None)
            else:
                os.environ["ORCA_KB_SOURCES"] = old_sources
    rows, skipped, sources = [], [], []
    for src in srcs:
        try:
            got = v2_source_chunks(src)
        except Exception as exc:
            skipped.append({"source_id": src["source_id"], "error": str(exc)})
            continue
        if not got:
            skipped.append({"source_id": src["source_id"], "error": "no extractable text"})
            continue
        rows.extend(got)
        sources.append({"source_id": src["source_id"], "sha256": sha256_file(src["path"]), "chunks": len(got)})
    out = out or config.vec_build_dir() / "chunks.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows))
    manifest = {"parser_version": "rag-v2-legal-structure-1", "chunk_count": len(rows), "source_count": len(sources),
                "sources": sources, "skipped": skipped, "chunks_sha256": sha256_file(out)}
    (out.parent / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return {"out": str(out), **manifest}


def load_vectors(chunks: Path | None = None, embeddings: Path | None = None, ids: Path | None = None) -> dict:
    """Load Colab vectors into orca_v2 exactly as supplied; never call the embedder."""
    import numpy as np
    base = config.vec_build_dir()
    chunks, embeddings, ids = chunks or base / "chunks.jsonl", embeddings or base / "embeddings.f16.npy", ids or base / "ids.json"
    rows = [json.loads(line) for line in chunks.read_text().splitlines() if line.strip()]
    vector_ids, vectors = json.loads(ids.read_text()), np.load(embeddings, mmap_mode="r")
    if len(rows) != len(vector_ids) or len(rows) != len(vectors):
        raise ValueError("chunks.jsonl, ids.json and embeddings.f16.npy have different lengths")
    if [r["id"] for r in rows] != vector_ids:
        raise ValueError("ids.json does not exactly match chunks.jsonl order")
    col = store.collection(name="orca_v2")
    for start in range(0, len(rows), 500):
        part, vec = rows[start:start + 500], vectors[start:start + 500]
        col.upsert(ids=[r["id"] for r in part], documents=[r["text"] for r in part],
                   metadatas=[r["meta"] for r in part], embeddings=[[float(x) for x in v] for v in vec])
    from . import retrieve
    retrieve.invalidate()
    return {"collection": "orca_v2", "loaded": len(rows), "dimensions": int(vectors.shape[1]) if len(vectors.shape) > 1 else 0}


def load_vectors_v3(chunks: Path | None = None, embeddings: Path | None = None, ids: Path | None = None,
                    collection: str = "orca_v3") -> dict:
    """Load precomputed vectors into collection orca_v3 without calling an embedder."""
    import numpy as np
    base = config.vec_build_dir() / "v3"
    chunks = chunks or base / "chunks.jsonl"
    embeddings = embeddings or base / "embeddings.f16.npy"
    ids = ids or base / "ids.json"
    rows = [json.loads(line) for line in chunks.read_text().splitlines() if line.strip()]
    vector_ids, vectors = json.loads(ids.read_text()), np.load(embeddings, mmap_mode="r")
    if len(rows) != len(vector_ids) or len(rows) != len(vectors):
        raise ValueError("chunks.jsonl, ids.json and embeddings.f16.npy have different lengths")
    if [r["id"] for r in rows] != vector_ids:
        raise ValueError("ids.json does not exactly match chunks.jsonl order")
    col = store.collection(name=collection)
    for start in range(0, len(rows), 500):
        part, vec = rows[start:start + 500], vectors[start:start + 500]
        col.upsert(ids=[r["id"] for r in part], documents=[r["text"] for r in part],
                   metadatas=[r["meta"] for r in part], embeddings=[[float(x) for x in v] for v in vec])
    from . import retrieve
    retrieve.invalidate()
    return {"collection": collection, "loaded": len(rows),
            "dimensions": int(vectors.shape[1]) if len(vectors.shape) > 1 else 0}


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
_REUSE: dict | None = None


def _reuse_map() -> dict:
    """text_sha -> embedding from another store (ORCA_REUSE_CHROMA, a read-only copy), same embed model.

    Lets a rebuild into a scratch directory skip re-embedding chunks whose text did not change. Only used
    when the env var is set; the live store is never opened by this path.
    """
    global _REUSE
    if _REUSE is None:
        _REUSE = {}
        src = os.environ.get("ORCA_REUSE_CHROMA")
        if src:
            import chromadb
            col = chromadb.PersistentClient(path=src).get_collection(config.COLLECTION)
            model = config.embed_model()
            for off in range(0, col.count(), 2000):
                g = col.get(limit=2000, offset=off, include=["embeddings", "metadatas"])
                for vec, m in zip(g["embeddings"], g["metadatas"]):
                    if m.get("embed_model") == model and m.get("text_sha"):
                        _REUSE.setdefault(m["text_sha"], [float(x) for x in vec])
    return _REUSE


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
    reuse = _reuse_map()
    reused = [r for r in todo if r["meta"]["text_sha"] in reuse]
    fresh = [r for r in todo if r["meta"]["text_sha"] not in reuse]
    t0 = time.time()
    B = 64
    for i in range(0, len(reused), B):
        part = reused[i:i + B]
        col.upsert(ids=[p["id"] for p in part], embeddings=[reuse[p["meta"]["text_sha"]] for p in part],
                   documents=[p["text"] for p in part], metadatas=[p["meta"] for p in part])
    if reused:
        log(f"  {what}: {len(reused)} chunks reused from ORCA_REUSE_CHROMA")
    for i in range(0, len(fresh), B):
        part = fresh[i:i + B]
        from . import embed as emb
        vecs = emb.embed([p["text"] for p in part])
        col.upsert(ids=[p["id"] for p in part], embeddings=vecs, documents=[p["text"] for p in part],
                   metadatas=[p["meta"] for p in part])
        log(f"  {what}: {min(i + B, len(fresh))}/{len(fresh)} chunks embedded ({time.time() - t0:.0f}s)")
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
