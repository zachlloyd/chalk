"""Schema validation tests for the primitive catalog."""

import jsonschema
import pytest


class TestCatalogSchemaValidation:
    """Validate catalog.json against the JSON schema."""

    def test_catalog_validates_against_schema(self, catalog, schema):
        jsonschema.validate(instance=catalog, schema=schema)

    def test_has_valid_semver_version(self, catalog):
        import re

        assert re.match(r"^\d+\.\d+\.\d+$", catalog["version"])

    def test_primitive_ids_are_unique(self, catalog):
        ids = list(catalog["primitives"].keys())
        assert len(ids) == len(set(ids))

    def test_rejects_invalid_primitive_missing_required_fields(self, schema):
        invalid = {
            "version": "0.1.0",
            "primitives": {"bad_v1": {"category": "ENTITY"}},
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid, schema=schema)

    def test_rejects_unknown_capability(self, schema):
        invalid = {
            "version": "0.1.0",
            "primitives": {
                "test_v1": {
                    "category": "ENTITY",
                    "capabilities": ["UNKNOWN_CAP"],
                    "rollout": "STABLE",
                    "sim": {
                        "power_generation_kw": 0,
                        "power_consumption_kw": 0,
                        "tick_effects": [],
                    },
                    "render": {"fallback": "box", "metadata": {}},
                    "constraints": {
                        "attach_to": ["block_face"],
                        "max_contiguous_segments": None,
                    },
                }
            },
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid, schema=schema)


class TestNeonLightStripV2Schema:
    """Validate neon_light_strip_v2 specific fields against the schema."""

    def test_exists_in_catalog(self, catalog):
        assert "neon_light_strip_v2" in catalog["primitives"]

    def test_category_is_entity(self, neon_def):
        assert neon_def["category"] == "ENTITY"

    def test_has_required_capabilities(self, neon_def):
        caps = neon_def["capabilities"]
        assert "AESTHETIC" in caps
        assert "LIGHTING" in caps
        assert "WAYFINDING" in caps

    def test_rollout_is_experimental(self, neon_def):
        assert neon_def["rollout"] == "EXPERIMENTAL"

    def test_zero_power_generation(self, neon_def):
        assert neon_def["sim"]["power_generation_kw"] == 0.0

    def test_low_power_consumption(self, neon_def):
        assert 0 < neon_def["sim"]["power_consumption_kw"] < 1.0

    def test_has_visibility_tick_effect(self, neon_def):
        effects = neon_def["sim"]["tick_effects"]
        vis_effects = [e for e in effects if e["type"] == "visibility_contribution"]
        assert len(vis_effects) == 1
        assert vis_effects[0]["score"] > 0

    def test_fallback_is_emissive_strip(self, neon_def):
        assert neon_def["render"]["fallback"] == "emissive_strip"

    def test_has_color_palette_metadata(self, neon_def):
        meta = neon_def["render"]["metadata"]
        assert "color_palette" in meta
        assert isinstance(meta["color_palette"], list)
        assert len(meta["color_palette"]) > 0

    def test_has_glow_intensity_metadata(self, neon_def):
        meta = neon_def["render"]["metadata"]
        assert "glow_intensity" in meta
        assert 0 <= meta["glow_intensity"] <= 1.0

    def test_attaches_to_block_and_module_face(self, neon_def):
        attach = neon_def["constraints"]["attach_to"]
        assert "block_face" in attach
        assert "module_face" in attach

    def test_max_contiguous_segments_is_32(self, neon_def):
        assert neon_def["constraints"]["max_contiguous_segments"] == 32
