"""Schema validation tests for the primitive catalog."""

import json
import os
import pytest
from jsonschema import validate, ValidationError

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
CATALOG_PATH = os.path.join(BASE_DIR, "data", "catalog.json")
SCHEMA_PATH = os.path.join(BASE_DIR, "schemas", "catalog.schema.json")
SEMANTICS_PATH = os.path.join(BASE_DIR, "sim", "semantics.json")


@pytest.fixture(scope="module")
def schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def catalog():
    with open(CATALOG_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def semantics():
    with open(SEMANTICS_PATH) as f:
        return json.load(f)


class TestCatalogSchemaValidation:
    """Validate catalog.json against its JSON schema."""

    def test_catalog_validates_against_schema(self, catalog, schema):
        validate(instance=catalog, schema=schema)

    def test_all_primitives_have_required_fields(self, catalog):
        required = {"category", "capabilities", "rollout", "sim", "render", "constraints"}
        for name, prim in catalog["primitives"].items():
            assert required.issubset(prim.keys()), f"{name} missing fields: {required - prim.keys()}"

    def test_capabilities_are_known(self, catalog, semantics):
        known = set(semantics["capabilities"].keys())
        for name, prim in catalog["primitives"].items():
            for cap in prim["capabilities"]:
                assert cap in known, f"{name} has unknown capability '{cap}'"

    def test_tick_effect_types_are_known(self, catalog, semantics):
        known = set(semantics["tick_effects"].keys())
        for name, prim in catalog["primitives"].items():
            for eff in prim["sim"]["tick_effects"]:
                assert eff["type"] in known, f"{name} has unknown tick_effect type '{eff['type']}'"


class TestNeonLightStripV2Schema:
    """Specific schema checks for the neon_light_strip_v2 primitive."""

    def test_neon_light_strip_exists(self, catalog):
        assert "neon_light_strip_v2" in catalog["primitives"]

    def test_category_is_entity(self, catalog):
        prim = catalog["primitives"]["neon_light_strip_v2"]
        assert prim["category"] == "ENTITY"

    def test_capabilities(self, catalog):
        prim = catalog["primitives"]["neon_light_strip_v2"]
        assert set(prim["capabilities"]) == {"AESTHETIC", "LIGHTING", "WAYFINDING"}

    def test_rollout_is_experimental(self, catalog):
        prim = catalog["primitives"]["neon_light_strip_v2"]
        assert prim["rollout"] == "EXPERIMENTAL"

    def test_constraints_attach_to(self, catalog):
        prim = catalog["primitives"]["neon_light_strip_v2"]
        assert set(prim["constraints"]["attach_to"]) == {"block_face", "module_face"}

    def test_max_contiguous_segments(self, catalog):
        prim = catalog["primitives"]["neon_light_strip_v2"]
        assert prim["constraints"]["max_contiguous_segments"] == 32

    def test_schema_rejects_invalid_primitive(self, schema):
        """Ensure the schema correctly rejects a malformed primitive."""
        bad_catalog = {
            "version": "1.0.0",
            "primitives": {
                "bad_prim": {
                    "category": "INVALID_CAT",
                    "capabilities": [],
                    "rollout": "STABLE",
                    "sim": {
                        "power_generation_kw": 0,
                        "power_consumption_kw": 0,
                        "tick_effects": []
                    },
                    "render": {"fallback": "x", "metadata": {}},
                    "constraints": {"attach_to": ["block_face"]}
                }
            }
        }
        with pytest.raises(ValidationError):
            validate(instance=bad_catalog, schema=schema)
