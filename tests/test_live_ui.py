"""Offline build guarantees for the ORCA Live UI."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dashboard" / "live" / "dist"
ALLOWED_URL_PREFIXES = ("http://localhost", "https://localhost", "http://www.w3.org", "https://www.w3.org")


def test_live_ui_dist_exists_and_index_uses_local_assets() -> None:
    index = DIST / "index.html"
    assert index.is_file(), "Build the dashboard/live/web project before running this test."
    html = index.read_text(encoding="utf-8")
    asset_refs = re.findall(r'(?:src|href)=["\']([^"\']+)["\']', html)
    assert asset_refs, "The built index should reference local application assets."
    for ref in asset_refs:
        assert not re.match(r"[a-z]+://", ref), f"External index asset: {ref}"
        if ref.startswith("assets/"):
            assert (DIST / ref).is_file(), f"Missing built asset: {ref}"


def test_live_ui_dist_has_no_external_runtime_urls() -> None:
    assert DIST.is_dir(), "Build the dashboard/live/web project before running this test."
    forbidden: list[str] = []
    for path in DIST.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".html", ".js", ".css", ".svg", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for url in re.findall(r"https?://[^\s\"'<>`\\)]+", text):
            if not url.startswith(ALLOWED_URL_PREFIXES):
                forbidden.append(f"{path.relative_to(DIST)}: {url}")
    assert not forbidden, "External runtime URL(s) found:\n" + "\n".join(forbidden)
