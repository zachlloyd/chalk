"""Render fallback smoke tests.

Confirms that when no specialised renderer is registered for
neon_light_strip_v2, the render resolver gracefully produces a
FallbackRenderResult with the expected emissive-strip properties.
"""

import json
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "sector-sim" / "src"))

from render.resolver import (
    FallbackRenderResult,
    resolve_render,
    unregister_renderer,
)
from sim.engine import load_catalog

CATALOG_PATH = Path(__file__).resolve().parents[2] / "services" / "sector-sim" / "data" / "catalog.json"


@pytest.fixture()
def catalog():
    return load_catalog(CATALOG_PATH)


@pytest.fixture()
def neon_strip_def(catalog):
    return catalog["primitives"]["neon_light_strip_v2"]


@pytest.fixture(autouse=True)
def _ensure_no_custom_renderer():
    """Ensure no specialised renderer is registered for the neon strip."""
    unregister_renderer("neon_light_strip_v2")
    yield
    unregister_renderer("neon_light_strip_v2")


def test_fallback_returns_fallback_result(neon_strip_def):
    """Without a registered renderer, resolve_render must return a
    FallbackRenderResult."""
    result = resolve_render(neon_strip_def)
    assert isinstance(result, FallbackRenderResult)


def test_fallback_shape_is_strip(neon_strip_def):
    """The fallback shape for neon_light_strip_v2 must be STRIP."""
    result = resolve_render(neon_strip_def)
    assert result.shape == "STRIP"


def test_fallback_is_emissive(neon_strip_def):
    """The fallback render must be emissive for a neon light strip."""
    result = resolve_render(neon_strip_def)
    assert result.emissive is True


def test_fallback_has_valid_color(neon_strip_def):
    """The fallback color must be a valid hex colour."""
    result = resolve_render(neon_strip_def)
    assert result.color.startswith("#")
    assert len(result.color) == 7


def test_fallback_opacity_in_range(neon_strip_def):
    """Opacity must be between 0 and 1 inclusive."""
    result = resolve_render(neon_strip_def)
    assert 0.0 <= result.opacity <= 1.0


def test_fallback_metadata_contains_color_palette(neon_strip_def):
    """Render metadata must include a color_palette list."""
    result = resolve_render(neon_strip_def)
    assert "color_palette" in result.metadata
    assert isinstance(result.metadata["color_palette"], list)
    assert len(result.metadata["color_palette"]) > 0


def test_fallback_metadata_contains_glow_intensity(neon_strip_def):
    """Render metadata must include glow_intensity."""
    result = resolve_render(neon_strip_def)
    assert "glow_intensity" in result.metadata
    assert 0 < result.metadata["glow_intensity"] <= 1.0


def test_fallback_to_dict_roundtrip(neon_strip_def):
    """to_dict must produce a serialisable representation."""
    result = resolve_render(neon_strip_def)
    d = result.to_dict()
    assert d["primitive_id"] == "neon_light_strip_v2"
    assert d["shape"] == "STRIP"
    assert d["emissive"] is True
    # Ensure JSON-serialisable
    json.dumps(d)


def test_all_primitives_have_safe_fallback(catalog):
    """Every primitive in the catalog must produce a non-None fallback render
    when no specialised renderer is registered."""
    for prim_id, prim_def in catalog["primitives"].items():
        unregister_renderer(prim_id)
        result = resolve_render(prim_def)
        assert result is not None, f"{prim_id} produced None fallback"
        assert isinstance(result, FallbackRenderResult)
