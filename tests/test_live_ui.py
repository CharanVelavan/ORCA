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


def test_live_ui_bundle_has_all_routes_and_split_views() -> None:
    """The offline bundle keeps the seven shell routes as lazy route chunks."""
    assets = DIST / "assets"
    names = {path.name for path in assets.glob("*.js")}
    for route in ("Home-", "Simulator-", "Operations-", "Investigation-", "Policy-", "Recovery-", "Audit-"):
        assert any(name.startswith(route) for name in names), f"Missing built {route[:-1]} route chunk"


def test_live_ui_bundle_keeps_control_events_out_of_console_store() -> None:
    """Control-only ground truth is deliberately filtered before console rendering."""
    store = ROOT / "dashboard" / "live" / "web" / "src" / "store.ts"
    source = store.read_text(encoding="utf-8")
    assert "if (event.audience === 'control') return state" in source
    assert "addControl" in source


def test_live_ui_console_never_receives_ground_truth() -> None:
    """Plan 12: /console must never see inject/scheduled ground truth, in the store, the Pipeline or the 3D view."""
    web = ROOT / "dashboard" / "live" / "web" / "src"
    bridge = (web / "stage" / "DataBridge.tsx").read_text(encoding="utf-8")
    expr = bridge.split("truthRoute = ")[1].split("\n")[0]
    assert "path === '/simulator'" in expr      # ground truth reaches the Simulator route only (plus legacy /control)
    for route in ("/console", "/operations", "/investigation", "/policy", "/recovery", "/audit", "/review", "/stage", "path === '/'"):
        assert route not in expr, f"{route} must never receive ground truth"
    pipeline = (web / "pipeline" / "pipelineStore.ts").read_text(encoding="utf-8")
    assert "if (!truth && event.audience === 'control') return;" in pipeline
    console = (web / "Console.tsx").read_text(encoding="utf-8")
    assert "truth={false}" in console
    scene = (web / "scenes" / "NetworkScene.tsx").read_text(encoding="utf-8")
    assert "truth && isAttack && <Attacker" in scene


def test_live_ui_routes_are_lazy_in_source_and_glb_ships() -> None:
    app = (ROOT / "dashboard" / "live" / "web" / "src" / "App.tsx").read_text(encoding="utf-8")
    for route in ("Home", "Simulator", "Operations", "Investigation", "Policy", "Recovery", "Audit"):
        assert f"const {route} = lazy(" in app, f"{route} must be a lazy route"
    glb = DIST / "models" / "orca-assets.glb"
    assert glb.is_file() and glb.stat().st_size < 2_000_000
