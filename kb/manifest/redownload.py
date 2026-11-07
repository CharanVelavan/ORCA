#!/usr/bin/env python3
"""Rebuild the ORCA-NTN corpus from kb/manifest/manifest.yaml.

PDFs and other source files are not committed to git. This script downloads each
document in the manifest with curl into a target directory, then checks its sha256
against the manifest. Downloads that do not match are kept aside as *.mismatch and
reported, never silently accepted.

Usage:
  python3 -I kb/manifest/redownload.py --out <target-dir>              # download all
  python3 -I kb/manifest/redownload.py --out <dir> --only id1,id2     # selected ids
  python3 -I kb/manifest/redownload.py --out <dir> --dry-run          # print plan only
  python3 -I kb/manifest/redownload.py --out <dir> --force            # re-fetch existing files

Files are saved as <target-dir>/<id><extension>. Downloaded content is untrusted: it is
only hashed, and written to disk. Nothing is executed or opened with another program.
Only the `url` values from the manifest are fetched.
"""

import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import yaml

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "manifest.yaml"
CURL_TIMEOUT_S = 600


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(url, dest):
    """Download url to dest with curl (argument list, no shell). Returns (ok, message)."""
    cmd = [
        "curl", "--fail", "--location", "--silent", "--show-error",
        "--retry", "2", "--max-time", str(CURL_TIMEOUT_S),
        "--output", str(dest), url,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=CURL_TIMEOUT_S + 60, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"curl failed: {exc}"
    if proc.returncode != 0:
        return False, f"curl exit {proc.returncode}: {proc.stderr.decode('utf-8', 'replace').strip()[:200]}"
    return True, "ok"


def extract_member(archive_path, member_name, dest):
    """Copy one member out of a zip by its base name. Returns (ok, message)."""
    try:
        with zipfile.ZipFile(archive_path) as archive:
            matches = [i for i in archive.infolist()
                       if not i.is_dir() and Path(i.filename).name == member_name]
            if len(matches) != 1:
                return False, f"zip member {member_name} found {len(matches)} times"
            with archive.open(matches[0]) as src, open(dest, "wb") as out:
                out.write(src.read())
    except (zipfile.BadZipFile, OSError, RuntimeError) as exc:
        return False, f"zip extract failed: {exc}"
    return True, "ok"


def target_name(doc):
    local = doc.get("local_path")
    suffix = Path(local).suffix if local else Path(urlparse(doc["url"]).path).suffix
    return f"{doc['id']}{suffix}"


def process(doc, out_dir, force, dry_run):
    """Returns (status, detail). status is OK, PRESENT, DRY, NO_HASH, NO_URL, FAIL or MISMATCH."""
    if not doc.get("url"):
        return "NO_URL", "manifest entry has no url"
    expected = doc.get("sha256")
    name = target_name(doc)
    dest = out_dir / name
    if dry_run:
        return "DRY", f"{doc['url']} -> {dest}"
    if dest.exists() and not force and expected and sha256_file(dest) == expected:
        return "PRESENT", str(dest)

    url_path = urlparse(doc["url"]).path.lower()
    is_zip_member = url_path.endswith(".zip") and not name.lower().endswith(".zip")
    with tempfile.TemporaryDirectory(dir=out_dir) as tmp:
        tmp_dl = Path(tmp) / "download"
        ok, msg = fetch(doc["url"], tmp_dl)
        if not ok:
            return "FAIL", msg
        if is_zip_member:
            tmp_file = Path(tmp) / name
            ok, msg = extract_member(tmp_dl, Path(doc.get("local_path") or name).name, tmp_file)
            if not ok:
                return "FAIL", msg
        else:
            tmp_file = tmp_dl
        actual = sha256_file(tmp_file)
        if expected and actual != expected:
            mismatch = out_dir / (name + ".mismatch")
            os.replace(tmp_file, mismatch)
            return "MISMATCH", f"sha256 {actual} != manifest {expected}; kept as {mismatch.name}"
        os.replace(tmp_file, dest)
    if not expected:
        return "NO_HASH", f"saved {dest.name}; manifest has no sha256 to check"
    return "OK", str(dest)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", required=True, help="target directory (created if missing)")
    parser.add_argument("--only", default="", help="comma-separated manifest ids to fetch")
    parser.add_argument("--force", action="store_true", help="re-download files already present")
    parser.add_argument("--dry-run", action="store_true", help="print the plan, download nothing")
    args = parser.parse_args()

    with open(MANIFEST, encoding="utf-8") as fh:
        manifest = yaml.safe_load(fh)
    docs = manifest.get("documents", [])
    wanted = {s.strip() for s in args.only.split(",") if s.strip()}
    if wanted:
        docs = [d for d in docs if d.get("id") in wanted]
        missing = wanted - {d.get("id") for d in docs}
        if missing:
            print(f"ids not in manifest: {', '.join(sorted(missing))}", file=sys.stderr)
            return 2

    out_dir = Path(args.out).resolve()
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    counts = {}
    failures = 0
    for doc in sorted(docs, key=lambda d: d["id"]):
        status, detail = process(doc, out_dir, args.force, args.dry_run)
        counts[status] = counts.get(status, 0) + 1
        if status in ("FAIL", "MISMATCH"):
            failures += 1
        print(f"{status:<9} {doc['id']}  {detail}")

    print("summary: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
