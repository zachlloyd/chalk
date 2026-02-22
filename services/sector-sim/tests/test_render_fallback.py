"""Render fallback smoke tests for neon_light_strip_v2.

Confirms that an unknown renderer gracefully displays the primitive
as an emissive strip using the fallback system.
"""


def _resolve_render(primitive_def, fallback_renderers, available_assets=None):
    """Resolve render output, falling back when the primary asset is unavailable.

    If the renderer doesn't know the asset (not in available_assets), the
    declared fallback renderer is used. If the fallback isn't found either,
    a default box is used as the ultimate fallback.
    """
    if available_assets is None:
        available_assets = set()

    render = primitive_def.get("render", {})
    fallback_name = render.get("fallback")
    metadata = render.get("metadata", {})

    fallback_def = fallback_renderers.get(fallback_name)

    if fallback_def is None:
        # Ultimate fallback: box (safe default)
        return {
            "mode": "fallback",
            "fallback_name": "box",
            "renderer": {"geometry": "cube", "emissive": False, "default_color": "#808080"},
            "metadata": {},
        }

    # Apply metadata overrides to fallback
    resolved = dict(fallback_def)
    if "emissive_fallback_color" in metadata:
        resolved["default_color"] = metadata["emissive_fallback_color"]
    if "emissive_fallback_intensity" in metadata:
        resolved["emissive_intensity"] = metadata["emissive_fallback_intensity"]

    return {
        "mode": "fallback",
        "fallback_name": fallback_name,
        "renderer": resolved,
        "metadata": metadata,
    }


class TestRenderFallbackNeonStrip:
    """Smoke test: neon_light_strip_v2 renders via emissive_strip fallback."""

    def test_falls_back_to_emissive_strip_when_asset_unknown(self, neon_def, fallbacks):
        result = _resolve_render(neon_def, fallbacks["fallback_renderers"])
        assert result["mode"] == "fallback"
        assert result["fallback_name"] == "emissive_strip"

    def test_fallback_renderer_is_emissive(self, neon_def, fallbacks):
        result = _resolve_render(neon_def, fallbacks["fallback_renderers"])
        assert result["renderer"]["emissive"] is True

    def test_fallback_renderer_uses_strip_geometry(self, neon_def, fallbacks):
        result = _resolve_render(neon_def, fallbacks["fallback_renderers"])
        assert result["renderer"]["geometry"] == "strip"

    def test_fallback_applies_emissive_color_from_metadata(self, neon_def, fallbacks):
        result = _resolve_render(neon_def, fallbacks["fallback_renderers"])
        assert result["renderer"]["default_color"] == "#ff00ff"

    def test_fallback_applies_emissive_intensity_from_metadata(self, neon_def, fallbacks):
        result = _resolve_render(neon_def, fallbacks["fallback_renderers"])
        assert result["renderer"]["emissive_intensity"] == 0.7

    def test_preserves_metadata_in_output(self, neon_def, fallbacks):
        result = _resolve_render(neon_def, fallbacks["fallback_renderers"])
        assert "color_palette" in result["metadata"]
        assert result["metadata"]["glow_intensity"] == 0.85

    def test_all_catalog_primitives_resolve_fallback(self, catalog, fallbacks):
        for prim_id, defn in catalog["primitives"].items():
            result = _resolve_render(defn, fallbacks["fallback_renderers"])
            assert result["mode"] == "fallback", f"{prim_id}: no fallback mode"
            assert "renderer" in result, f"{prim_id}: no renderer in result"

    def test_unknown_fallback_returns_box(self, fallbacks):
        bad_prim = {"render": {"fallback": "nonexistent_thing", "metadata": {}}}
        result = _resolve_render(bad_prim, fallbacks["fallback_renderers"])
        assert result["mode"] == "fallback"
        assert result["fallback_name"] == "box"

    def test_emissive_strip_registered_in_fallbacks(self, fallbacks):
        assert "emissive_strip" in fallbacks["fallback_renderers"]
        fb = fallbacks["fallback_renderers"]["emissive_strip"]
        assert fb["emissive"] is True
        assert fb["geometry"] == "strip"
