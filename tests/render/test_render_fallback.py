"""Render fallback smoke tests.

Confirms that unknown renderers gracefully degrade to the emissive strip
representation, and that the neon_light_strip_v2 primitive resolves correctly.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
CATALOG_PATH = ROOT / "services" / "sector-sim" / "data" / "catalog.json"

sys.path.insert(0, str(ROOT / "services" / "render-engine" / "src"))
from fallback import resolve_fallback, load_fallback_registry  # noqa: E402


@pytest.fixture
def catalog() -> dict:
    with open(CATALOG_PATH) as f:
        return json.load(f)


@pytest.fixture
def neon_primitive(catalog: dict) -> dict:
    return catalog["primitives"]["neon_light_strip_v2"]


def test_emissive_strip_in_registry() -> None:
    """The emissive_strip fallback must be registered."""
    registry = load_fallback_registry()
    assert "emissive_strip" in registry
    assert registry["emissive_strip"]["emissive"] is True


def test_neon_strip_resolves_to_emissive(neon_primitive: dict) -> None:
    """neon_light_strip_v2 must resolve to an emissive strip fallback."""
    result = resolve_fallback(neon_primitive)
    assert result["geometry"] == "strip"
    assert result["material"] == "emissive_unlit"
    assert result["emissive"] is True


def test_neon_strip_color_from_palette(neon_primitive: dict) -> None:
    """Resolved color must come from the primitive's palette."""
    result = resolve_fallback(neon_primitive)
    palette = neon_primitive["render"]["metadata"]["color_palette"]
    assert result["color"] == palette[0]
    assert result["color_palette"] == palette


def test_neon_strip_glow_intensity(neon_primitive: dict) -> None:
    """Glow intensity must match the primitive metadata."""
    result = resolve_fallback(neon_primitive)
    expected = neon_primitive["render"]["metadata"]["glow_intensity"]
    assert result["glow_intensity"] == expected


def test_unknown_fallback_degrades_to_emissive_strip() -> None:
    """A primitive with a completely unknown fallback type must degrade safely."""
    fake_primitive = {
        "render": {
            "fallback": "holographic_projector_9000",
            "metadata": {},
        }
    }
    result = resolve_fallback(fake_primitive)
    assert result["geometry"] == "strip"
    assert result["material"] == "emissive_unlit"
    assert result["emissive"] is True
    assert "glow_intensity" in result


def test_missing_render_block_degrades() -> None:
    """A primitive with no render block at all must still resolve safely."""
    result = resolve_fallback({})
    assert result["emissive"] is True
    assert result["geometry"] == "strip"
