"""Schema validation tests for the primitive catalog."""

import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "services" / "sector-sim" / "data" / "catalog.json"
SCHEMA_PATH = REPO_ROOT / "services" / "sector-sim" / "schema" / "primitive_catalog.schema.json"


@pytest.fixture()
def catalog():
    with open(CATALOG_PATH) as f:
        return json.load(f)


@pytest.fixture()
def schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def test_catalog_validates_against_schema(catalog, schema):
    """Full catalog must validate against the JSON schema."""
    jsonschema.validate(instance=catalog, schema=schema)


def test_neon_light_strip_v2_present(catalog):
    """The neon_light_strip_v2 primitive must exist in the catalog."""
    assert "neon_light_strip_v2" in catalog["primitives"]


def test_neon_light_strip_v2_category(catalog):
    prim = catalog["primitives"]["neon_light_strip_v2"]
    assert prim["category"] == "ENTITY"


def test_neon_light_strip_v2_capabilities(catalog):
    prim = catalog["primitives"]["neon_light_strip_v2"]
    assert set(prim["capabilities"]) == {"AESTHETIC", "LIGHTING", "WAYFINDING"}


def test_neon_light_strip_v2_rollout(catalog):
    prim = catalog["primitives"]["neon_light_strip_v2"]
    assert prim["rollout"] == "EXPERIMENTAL"


def test_neon_light_strip_v2_constraints(catalog):
    prim = catalog["primitives"]["neon_light_strip_v2"]
    assert prim["constraints"]["attachment"] == "BLOCK_OR_MODULE_FACE"
    assert prim["constraints"]["max_contiguous_segments"] == 32


def test_neon_light_strip_v2_sim(catalog):
    sim = catalog["primitives"]["neon_light_strip_v2"]["sim"]
    assert sim["power_generation"] == 0.0
    assert sim["power_consumption"] > 0
    assert any(e["type"] == "VISIBILITY_SCORE" for e in sim.get("effects", []))


def test_neon_light_strip_v2_render_fallback(catalog):
    fb = catalog["primitives"]["neon_light_strip_v2"]["render"]["fallback"]
    assert fb["type"] == "STRIP"
    assert fb["emissive"] is True


def test_neon_light_strip_v2_render_metadata(catalog):
    meta = catalog["primitives"]["neon_light_strip_v2"]["render"]["metadata"]
    assert "color_palette" in meta
    assert isinstance(meta["color_palette"], list)
    assert len(meta["color_palette"]) > 0
    assert "glow_intensity" in meta
    assert 0 < meta["glow_intensity"] <= 1.0


def test_all_primitives_validate_individually(catalog, schema):
    """Each primitive must independently satisfy the schema's Primitive def."""
    # Validate each primitive entry through the full catalog schema by
    # constructing a per-primitive wrapper catalog and validating that.
    for name, prim in catalog["primitives"].items():
        single_catalog = {
            "version": catalog["version"],
            "primitives": {name: prim},
        }
        jsonschema.validate(instance=single_catalog, schema=schema)
