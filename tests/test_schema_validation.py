"""Schema validation tests for the primitive catalog."""

import copy

import jsonschema
from jsonschema import RefResolver
import pytest


class TestCatalogSchemaValidation:
    """Validate the catalog against the JSON schema."""

    def test_catalog_validates_against_schema(self, catalog, catalog_schema):
        """Full catalog passes schema validation."""
        jsonschema.validate(instance=catalog, schema=catalog_schema)

    def test_each_primitive_has_required_fields(self, catalog, catalog_schema):
        """Every primitive in the catalog has all required fields."""
        resolver = RefResolver.from_schema(catalog_schema)
        for prim_id, prim in catalog["primitives"].items():
            # Validate individual primitive against the primitive definition
            jsonschema.validate(
                instance=prim,
                schema=catalog_schema["definitions"]["primitive"],
                resolver=resolver,
            )

    def test_neon_light_strip_v2_present(self, catalog):
        """neon_light_strip_v2 exists in catalog."""
        assert "neon_light_strip_v2" in catalog["primitives"]

    def test_neon_light_strip_v2_category(self, catalog):
        """neon_light_strip_v2 is an ENTITY."""
        prim = catalog["primitives"]["neon_light_strip_v2"]
        assert prim["category"] == "ENTITY"

    def test_neon_light_strip_v2_capabilities(self, catalog):
        """neon_light_strip_v2 has AESTHETIC, LIGHTING, WAYFINDING."""
        prim = catalog["primitives"]["neon_light_strip_v2"]
        assert set(prim["capabilities"]) == {"AESTHETIC", "LIGHTING", "WAYFINDING"}

    def test_neon_light_strip_v2_rollout(self, catalog):
        """neon_light_strip_v2 is EXPERIMENTAL."""
        prim = catalog["primitives"]["neon_light_strip_v2"]
        assert prim["rollout"] == "EXPERIMENTAL"

    def test_neon_light_strip_v2_constraints(self, catalog):
        """neon_light_strip_v2 attaches to block/module face, max 32 segments."""
        prim = catalog["primitives"]["neon_light_strip_v2"]
        assert prim["constraints"]["attach_to"] == "BLOCK_OR_MODULE_FACE"
        assert prim["constraints"]["max_contiguous_segments"] == 32

    def test_neon_light_strip_v2_zero_power_generation(self, catalog):
        """neon_light_strip_v2 generates zero power."""
        prim = catalog["primitives"]["neon_light_strip_v2"]
        assert prim["sim"]["power"]["generation_per_tick"] == 0.0

    def test_neon_light_strip_v2_low_power_consumption(self, catalog):
        """neon_light_strip_v2 has low power consumption (<=1.0)."""
        prim = catalog["primitives"]["neon_light_strip_v2"]
        assert 0 < prim["sim"]["power"]["consumption_per_tick"] <= 1.0

    def test_neon_light_strip_v2_render_metadata(self, catalog):
        """neon_light_strip_v2 has emissive_strip render with color_palette and glow_intensity."""
        prim = catalog["primitives"]["neon_light_strip_v2"]
        render = prim["render"]
        assert render["type"] == "emissive_strip"
        assert render["fallback"] == "emissive_strip"
        assert "color_palette" in render["metadata"]
        assert "glow_intensity" in render["metadata"]
        assert len(render["metadata"]["color_palette"]) >= 1
        assert 0 < render["metadata"]["glow_intensity"] <= 1.0

    def test_schema_rejects_invalid_category(self, catalog, catalog_schema):
        """Schema rejects primitives with invalid category."""
        bad = copy.deepcopy(catalog)
        bad["primitives"]["neon_light_strip_v2"]["category"] = "INVALID"
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=bad, schema=catalog_schema)

    def test_schema_rejects_missing_capabilities(self, catalog, catalog_schema):
        """Schema rejects primitives with empty capabilities."""
        bad = copy.deepcopy(catalog)
        bad["primitives"]["neon_light_strip_v2"]["capabilities"] = []
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=bad, schema=catalog_schema)
