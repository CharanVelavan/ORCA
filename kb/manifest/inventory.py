#!/usr/bin/env python3
"""Inventory of the ORCA-NTN document corpus.

Scans kb/sources/ (including kb/sources/incoming/, not the hidden kb/sources/.text/
extraction folder, which is read only as companion text) and corpus/raw/*/.
Each file is joined with its metadata (kb/staging/<folder>/<id>.yaml first, then
kb/sources.yaml) and the result is written to kb/manifest/manifest.yaml.

Re-run any time:   python3 -I kb/manifest/inventory.py
  (run from anywhere; paths are resolved from this file's location)

Guarantees:
- Deterministic: entries sorted by id, no timestamps, so unchanged inputs give an
  identical file.
- Nothing skipped silently: every file that is not treated as a document is listed
  under `skipped` with a reason.
- Read-only for the corpus: files are only hashed, counted and read as text
  (pdfinfo/pdftotext for PDFs, zipfile/regex for DOCX). Nothing is executed or
  opened with any other program. Instructions found inside documents are ignored.
- Writes only kb/manifest/manifest.yaml (via a temporary file in kb/manifest/).

Metadata fields binding_status and in_force_from are copied from staging metadata
(or kb/sources.yaml if it carries them) and never inferred. `verified` is never set.
"""

import datetime
import difflib
import html as htmlmod
import hashlib
import os
import re
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[2]
KB = ROOT / "kb"
SOURCES_DIR = KB / "sources"
SOURCES_YAML = KB / "sources.yaml"
STAGING_DIR = KB / "staging"
CORPUS_RAW = ROOT / "corpus" / "raw"
MANIFEST_DIR = KB / "manifest"
OUT = MANIFEST_DIR / "manifest.yaml"

# Host must equal one of these or be a subdomain of one (dot-bounded match).
OFFICIAL_DOMAINS = (
    "gov.in", "nic.in", "egazette.gov.in", "trai.gov.in", "cert-in.org.in", "dot.gov.in",
    "europa.eu", "eur-lex.europa.eu", "enisa.europa.eu", "nist.gov", "fcc.gov", "cisa.gov",
    "whitehouse.gov", "itu.int", "3gpp.org", "etsi.org", "tdra.gov.ae", "u.ae", "gov.au",
    "cyber.gov.au", "gov.uk", "legislation.gov.uk", "gov.sg", "csa.gov.sg", "imda.gov.sg",
    "ccsds.org", "esa.int", "unoosa.org", "un.org",
)

ID_PREFIX_JURISDICTION = {"in": "IN", "eu": "EU", "us": "US", "ae": "AE", "intl": "INTL"}
SCANNED_CHARS_PER_PAGE = 200      # PDF with fewer non-space text chars per page = scanned
EMPTY_TEXT_CHARS = 200            # HTML with fewer chars is treated as an error page
NEAR_DUPLICATE_RATIO = 0.92
MIN_TITLE_CHARS = 15
DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")
HTML_LIKE_RE = re.compile(rb"<\s*(!doctype\s+html|html|head|body)", re.I)
ERROR_TITLE_RE = re.compile(r"404|not found|access denied|forbidden|error", re.I)

# Files that are never documents, with the reason shown in `skipped`.
SKIP_EXTENSIONS = {
    ".yaml": "metadata file (read as metadata, not a document)",
    ".yml": "metadata file (read as metadata, not a document)",
    ".png": "image asset (page render or figure)",
    ".jpg": "image asset", ".jpeg": "image asset", ".gif": "image asset", ".svg": "image asset",
    ".swift": "OCR helper script (not a document)",
    ".log": "log file (not a document)",
    ".py": "script (not a document)",
}


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def load_yaml(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def normalise(value):
    """Make YAML-safe plain values: dates become ISO strings, keys become strings."""
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): normalise(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalise(v) for v in value]
    return value


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nonspace(text):
    return len(re.sub(r"\s", "", text))


def run_tool(cmd):
    """Run a poppler tool with an argument list (no shell). Returns stdout bytes or None."""
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=300, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def pdf_pages(path):
    out = run_tool(["pdfinfo", str(path)])
    if out is None:
        return None
    match = re.search(rb"^Pages:\s+(\d+)", out, re.M)
    return int(match.group(1)) if match else None


def pdf_text(path):
    out = run_tool(["pdftotext", "-enc", "UTF-8", "-q", str(path), "-"])
    return None if out is None else out.decode("utf-8", "replace")


def html_to_text(raw):
    raw = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", raw)
    text = re.sub(r"(?s)<[^>]+>", " ", raw)
    return htmlmod.unescape(text)


def language_guess(text):
    """Return (language, devanagari_share). Share = Devanagari / letters."""
    if not text:
        return None, None
    letters = sum(1 for ch in text if ch.isalpha())
    if letters < 50:
        return None, None
    devanagari = len(DEVANAGARI_RE.findall(text))
    share = devanagari / letters
    if share >= 0.5:
        lang = "hi"
    elif share >= 0.02:
        lang = "bilingual"
    else:
        lang = "en"
    return lang, round(share, 4)


def classify(path):
    ext = path.suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in (".html", ".htm"):
        return "html"
    if ext == ".docx":
        return "docx"
    if ext in (".txt", ".md", ".json", ".xml", ".csv"):
        return "text"
    return "other"


def read_head(path, size=2048):
    with open(path, "rb") as fh:
        return fh.read(size)


def inspect_document(path, ftype):
    """Hash and measure one file. Returns a dict; never raises for bad files."""
    res = {
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "file_type": ftype,
        "pages": None,
        "text_chars": None,
        "text_chars_per_page": None,
        "scanned": None,
        "live_text": None,
        "problems": [],
    }
    if ftype == "pdf":
        head = read_head(path)
        if not head.startswith(b"%PDF"):
            res["problems"].append(
                "html_saved_as_pdf" if HTML_LIKE_RE.search(head) else "invalid_pdf_magic")
            return res
        pages = pdf_pages(path)
        text = pdf_text(path) if pages else None
        if not pages or text is None:
            res["problems"].append("pdf_unreadable")
            return res
        chars = nonspace(text)
        res.update(pages=pages, text_chars=chars,
                   text_chars_per_page=round(chars / pages), live_text=text)
        res["scanned"] = chars / pages < SCANNED_CHARS_PER_PAGE
        if res["scanned"]:
            res["problems"].append("scanned_or_no_text_layer")
    elif ftype == "html":
        raw = path.read_bytes().decode("utf-8", "replace")
        title = re.search(r"(?is)<title[^>]*>(.*?)</title>", raw)
        text = html_to_text(raw)
        chars = nonspace(text)
        res.update(text_chars=chars, live_text=text)
        if (title and ERROR_TITLE_RE.search(title.group(1))) or chars < EMPTY_TEXT_CHARS:
            res["problems"].append("html_error_page")
    elif ftype == "docx":
        try:
            with zipfile.ZipFile(path) as archive:
                xml = archive.read("word/document.xml").decode("utf-8", "replace")
        except (zipfile.BadZipFile, KeyError, OSError):
            res["problems"].append("invalid_docx")
            return res
        text = htmlmod.unescape(" ".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml)))
        res.update(text_chars=nonspace(text), live_text=text)
    elif ftype == "text":
        text = path.read_bytes().decode("utf-8", "replace")
        res.update(text_chars=nonspace(text), live_text=text)
    else:
        res["problems"].append("unsupported_file_type")
    return res


def title_key(title):
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()


def host_is_official(host):
    if not host:
        return False
    return any(host == d or host.endswith("." + d) for d in OFFICIAL_DOMAINS)


def first_match(mapping, *keys):
    for key in keys:
        if key and key in mapping:
            return mapping[key]
    return None


def main():
    warnings = []

    # ---- metadata -------------------------------------------------------
    sources = {}
    if SOURCES_YAML.exists():
        for entry in load_yaml(SOURCES_YAML) or []:
            if not isinstance(entry, dict) or not entry.get("id"):
                warnings.append("kb/sources.yaml: entry without id ignored")
                continue
            sid = str(entry["id"])
            if sid in sources:
                warnings.append(f"kb/sources.yaml: duplicate id {sid} (first kept)")
                continue
            sources[sid] = entry
    sources_matched = set()

    staging_items = []   # dicts with metadata + _path, _folder, _matched
    staging_skipped = []
    staging_by_id = {}
    staging_by_file = {}
    if STAGING_DIR.exists():
        for path in sorted(STAGING_DIR.rglob("*")):
            if path.is_dir():
                continue
            if path.suffix.lower() not in (".yaml", ".yml") or path.name.startswith("_"):
                staging_skipped.append({"path": rel(path),
                                        "reason": "staging note (not metadata, not a document)"})
                continue
            try:
                data = load_yaml(path)
            except yaml.YAMLError as exc:
                warnings.append(f"{rel(path)}: unreadable YAML ({type(exc).__name__})")
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    warnings.append(f"{rel(path)}: entry is not a mapping, ignored")
                    continue
                item = dict(item)
                item["_path"] = rel(path)
                item["_folder"] = path.parent.name
                item["_matched"] = False
                sid = str(item.get("id") or path.stem)
                item["_id"] = sid
                if sid in staging_by_id:
                    warnings.append(f"{rel(path)}: duplicate staging id {sid} (first kept)")
                    continue
                staging_items.append(item)
                staging_by_id[sid] = item
                for field in ("local_path", "file", "path"):
                    if item.get(field):
                        staging_by_file.setdefault(Path(str(item[field])).name, item)
                        break

    # ---- discovery ------------------------------------------------------
    # Each file gets (path, source label, corpus folder or None, hidden flag).
    roots = []
    if SOURCES_DIR.exists():
        roots.append((SOURCES_DIR, "kb/sources", None))
    if CORPUS_RAW.exists():
        roots.append((CORPUS_RAW, "corpus", None))

    all_files = []
    for root, label, _ in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames.sort()
            parts = Path(dirpath).relative_to(root).parts
            hidden_dir = next((p for p in parts if p.startswith(".")), None)
            for name in sorted(filenames):
                path = Path(dirpath) / name
                if label == "corpus":
                    folder = parts[0] if parts else "raw"
                    source = f"corpus/{folder}"
                else:
                    folder = None
                    source = "kb/sources"
                all_files.append({"path": path, "source": source, "folder": folder,
                                  "hidden_dir": hidden_dir, "name": name})

    skipped = list(staging_skipped)
    binary_keys = set()
    for item in all_files:
        name = item["name"]
        if item["hidden_dir"] or name.startswith("."):
            continue
        if Path(name).suffix.lower() == ".txt" or Path(name).suffix.lower() in SKIP_EXTENSIONS:
            continue
        binary_keys.add(name)
        binary_keys.add(Path(name).stem)

    # Companion text index: every .txt in scanned trees, including hidden folders.
    txt_index = {}
    for item in all_files:
        if item["name"].endswith(".txt"):
            base = item["name"][:-4]
            is_ocr = base.endswith(".ocr")
            key = base[:-4] if is_ocr else base
            txt_index.setdefault(key, []).append((item["path"], is_ocr))

    documents = []
    for item in all_files:
        path, name = item["path"], item["name"]
        ext = Path(name).suffix.lower()
        if item["hidden_dir"]:
            skipped.append({"path": rel(path), "reason":
                            f"inside dot-folder '{item['hidden_dir']}' (extraction or companion "
                            "text, read only via companion lookup)"})
            continue
        if name.startswith("."):
            skipped.append({"path": rel(path), "reason": "hidden system file"})
            continue
        if ext in SKIP_EXTENSIONS:
            skipped.append({"path": rel(path), "reason": SKIP_EXTENSIONS[ext]})
            continue
        if ext == ".txt":
            base = name[:-4]
            base_no_ocr = base[:-4] if base.endswith(".ocr") else base
            if base in binary_keys or base_no_ocr in binary_keys:
                skipped.append({"path": rel(path), "reason":
                                "extracted text companion of a document in the same set"})
                continue
        documents.append(item)

    # ---- build records --------------------------------------------------
    records = []
    for item in documents:
        path, name, source, folder = item["path"], item["name"], item["source"], item["folder"]
        stem = Path(name).stem
        staging = staging_by_file.get(name) or staging_by_id.get(stem) or staging_by_id.get(name)
        if staging is not None:
            staging["_matched"] = True
        sources_entry = first_match(sources, stem, name)
        if sources_entry is not None:
            sources_matched.add(str(sources_entry.get("id")) if sources_entry.get("id") else stem)

        ftype = classify(path)
        measured = inspect_document(path, ftype)
        problems = list(measured["problems"])

        companion = None
        candidates = txt_index.get(name) or txt_index.get(stem) or []
        if candidates:
            candidates = sorted(
                candidates,
                key=lambda c: (c[0].parent != path.parent, c[1], str(c[0])))
            companion = candidates[0][0]
        companion_text = None
        if companion is not None:
            companion_text = companion.read_bytes().decode("utf-8", "replace")
        lang, share = language_guess(companion_text if companion_text is not None
                                     else measured["live_text"])

        meta = staging if staging is not None else sources_entry
        if meta is None:
            problems.append("no_metadata")
        jurisdiction, jur_source = None, None
        if meta and meta.get("jurisdiction"):
            jurisdiction, jur_source = str(meta["jurisdiction"]), "metadata"
        elif folder == "india":
            jurisdiction, jur_source = "IN", "corpus folder"
        else:
            prefix = stem.split("-")[0].lower()
            if prefix in ID_PREFIX_JURISDICTION:
                jurisdiction, jur_source = ID_PREFIX_JURISDICTION[prefix], "id prefix"
            else:
                jurisdiction, jur_source = "unknown", None

        url = meta.get("url") if meta else None
        host = urlparse(str(url)).hostname.lower() if url and urlparse(str(url)).hostname else None
        official = host_is_official(host)
        if not url:
            problems.append("no_url")
        if not official:
            problems.append("non_official_domain")

        sha = measured["sha256"]
        if staging and staging.get("sha256") and str(staging["sha256"]) != sha:
            problems.append("sha256_mismatch_staging")
        if sources_entry and sources_entry.get("sha256") and str(sources_entry["sha256"]) != sha:
            problems.append("sha256_mismatch_sources_yaml")
        if (staging and sources_entry and staging.get("sha256") and sources_entry.get("sha256")
                and str(staging["sha256"]) != str(sources_entry["sha256"])):
            problems.append("sha256_staging_vs_sources_yaml_differ")

        if staging is not None:
            origin = "staging"
            meta_id = staging["_id"]
        elif sources_entry is not None:
            origin = "kb/sources.yaml"
            meta_id = str(sources_entry.get("id") or stem)
        else:
            origin = None
            meta_id = stem

        def pick(field):
            if staging is not None and field in staging:
                return normalise(staging[field])
            if sources_entry is not None and field in sources_entry:
                return normalise(sources_entry[field])
            return None

        licence = staging.get("licence", staging.get("license")) if staging else None
        if licence is None and sources_entry is not None:
            licence = sources_entry.get("licence", sources_entry.get("license"))

        records.append({
            "id": meta_id,
            "title": pick("title") or stem,
            "authority": pick("authority"),
            "jurisdiction": jurisdiction,
            "jurisdiction_source": jur_source,
            "url": str(url) if url else None,
            "url_host": host,
            "official_domain": official,
            "local_path": rel(path),
            "source": source,
            "metadata_origin": origin,
            "bytes": measured["bytes"],
            "sha256": sha,
            "file_type": ftype,
            "pages": measured["pages"],
            "text_chars": measured["text_chars"],
            "text_chars_per_page": measured["text_chars_per_page"],
            "scanned": measured["scanned"],
            "language": lang,
            "devanagari_share": share,
            "companion_text": rel(companion) if companion is not None else None,
            "licence": normalise(licence),
            "binding_status": pick("binding_status"),
            "in_force_from": pick("in_force_from"),
            "notes": pick("notes"),
            "duplicate_of": [],
            "near_duplicate_of": [],
            "problems": problems,
        })

    # Missing files: metadata with no matching file.
    for item in staging_items:
        if not item["_matched"]:
            records.append({
                "id": item["_id"], "title": normalise(item.get("title")) or item["_id"],
                "authority": normalise(item.get("authority")),
                "jurisdiction": normalise(item.get("jurisdiction")) or "unknown",
                "jurisdiction_source": "metadata" if item.get("jurisdiction") else None,
                "url": normalise(item.get("url")), "url_host": None, "official_domain": False,
                "local_path": None,
                "source": (f"corpus/{item['_folder']}" if item["_folder"] in ("india", "global")
                           else "kb/staging"),
                "metadata_origin": "staging", "bytes": None, "sha256": None,
                "file_type": None, "pages": None, "text_chars": None,
                "text_chars_per_page": None, "scanned": None, "language": None,
                "devanagari_share": None, "companion_text": None,
                "licence": normalise(item.get("licence", item.get("license"))),
                "binding_status": normalise(item.get("binding_status")),
                "in_force_from": normalise(item.get("in_force_from")),
                "notes": normalise(item.get("notes")),
                "duplicate_of": [], "near_duplicate_of": [],
                "problems": ["missing_file"] + ([] if item.get("url") else ["no_url"]),
            })
    for sid, entry in sources.items():
        if sid not in sources_matched:
            records.append({
                "id": sid, "title": normalise(entry.get("title")) or sid,
                "authority": normalise(entry.get("authority")), "jurisdiction": None,
                "jurisdiction_source": None, "url": normalise(entry.get("url")),
                "url_host": None, "official_domain": False, "local_path": None,
                "source": "kb/sources", "metadata_origin": "kb/sources.yaml", "bytes": None,
                "sha256": None, "file_type": None, "pages": None, "text_chars": None,
                "text_chars_per_page": None, "scanned": None, "language": None,
                "devanagari_share": None, "companion_text": None, "licence": None,
                "binding_status": normalise(entry.get("binding_status")),
                "in_force_from": normalise(entry.get("in_force_from")),
                "notes": normalise(entry.get("notes")),
                "duplicate_of": [], "near_duplicate_of": [],
                "problems": ["missing_file"],
            })

    records.sort(key=lambda r: (r["id"], r["source"] != "kb/sources", r["local_path"] or ""))

    # Unique ids: a repeated id gets a #n suffix and a duplicate_id problem.
    seen = Counter()
    for rec in records:
        seen[rec["id"]] += 1
        if seen[rec["id"]] > 1:
            rec["id"] = f"{rec['id']}#{seen[rec['id']]}"
            rec["problems"].append("duplicate_id")

    # Duplicate content (same sha256) and near-duplicate titles.
    by_sha = {}
    for rec in records:
        if rec["sha256"]:
            by_sha.setdefault(rec["sha256"], []).append(rec)
    for group in by_sha.values():
        if len(group) > 1:
            for rec in group:
                rec["duplicate_of"] = sorted(o["id"] for o in group if o is not rec)
                rec["problems"].append("duplicate_content")
    keyed = [(rec, title_key(rec["title"])) for rec in records]
    for i, (a, ka) in enumerate(keyed):
        if len(ka) < MIN_TITLE_CHARS:
            continue
        for b, kb_ in keyed[i + 1:]:
            if len(kb_) < MIN_TITLE_CHARS or (a["sha256"] and a["sha256"] == b["sha256"]):
                continue
            matcher = difflib.SequenceMatcher(None, ka, kb_)
            if matcher.quick_ratio() < NEAR_DUPLICATE_RATIO:
                continue
            if matcher.ratio() >= NEAR_DUPLICATE_RATIO:
                a["near_duplicate_of"].append(b["id"])
                b["near_duplicate_of"].append(a["id"])
    for rec in records:
        if rec["near_duplicate_of"]:
            rec["near_duplicate_of"] = sorted(set(rec["near_duplicate_of"]))
            rec["problems"].append("near_duplicate_title")

    for rec in records:
        rec["problems"] = sorted(set(rec["problems"]))

    documents_out = records
    skipped.sort(key=lambda s: s["path"])

    # ---- summary --------------------------------------------------------
    def count(fn):
        return {str(k): v for k, v in sorted(Counter(fn(r) for r in documents_out).items(),
                                             key=lambda kv: str(kv[0]))}

    problem_counts = Counter(p for r in documents_out for p in r["problems"])
    summary = {
        "documents": len(documents_out),
        "documents_with_problems": sum(1 for r in documents_out if r["problems"]),
        "skipped": len(skipped),
        "warnings": len(warnings),
        "by_jurisdiction": count(lambda r: r["jurisdiction"]),
        "by_source": count(lambda r: r["source"]),
        "scanned": count(lambda r: {True: "true", False: "false", None: "not_applicable"}[r["scanned"]]),
        "language": count(lambda r: r["language"] or "undetermined"),
        "official_domain": count(lambda r: "true" if r["official_domain"] else "false"),
        "duplicates": {
            "entries_with_duplicate_content": sum(1 for r in documents_out if r["duplicate_of"]),
            "entries_with_near_duplicate_title": sum(1 for r in documents_out if r["near_duplicate_of"]),
        },
        "binding_status_stated": sum(1 for r in documents_out if r["binding_status"]),
        "problems": dict(sorted(problem_counts.items())),
    }

    manifest = {
        "summary": summary,
        "official_domains": list(OFFICIAL_DOMAINS),
        "warnings": warnings,
        "documents": [normalise(r) for r in documents_out],
        "skipped": skipped,
    }

    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".yaml.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write("# Corpus manifest written by kb/manifest/inventory.py. Do not edit by hand.\n")
        fh.write("# Re-run: python3 -I kb/manifest/inventory.py\n")
        yaml.safe_dump(manifest, fh, sort_keys=False, allow_unicode=True, width=200)
    os.replace(tmp, OUT)

    print(yaml.safe_dump({"summary": summary}, sort_keys=False, allow_unicode=True))
    print(f"Wrote {rel(OUT)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
