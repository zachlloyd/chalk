"""Schema validation tests for catalog.json."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
CATALOG_PATH = ROOT / "services" / "sector-sim" / "data" / "catalog.json"
SCHEMA_PATH = ROOT / "schemas" / "catalog.schema.json"


@pytest.fixture
def catalog() -> dict:
    with open(CATALOG_PATH) as f:
        return json.load(f)


@pytest.fixture
def schema() -> dict:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def test_catalog_validates_against_schema(catalog: dict, schema: dict) -> None:
    """The full catalog must pass JSON-Schema validation."""
    jsonschema.validate(instance=catalog, schema=schema)


def test_neon_light_strip_v2_present(catalog: dict) -> None:
    """neon_light_strip_v2 must exist in the catalog."""
    assert "neon_light_strip_v2" in catalog["primitives"]


def test_neon_light_strip_v2_category(catalog: dict) -> None:
    entry = catalog["primitives"]["neon_light_strip_v2"]
    assert entry["category"] == "ENTITY"


def test_neon_light_strip_v2_capabilities(catalog: dict) -> None:
    entry = catalog["primitives"]["neon_light_strip_v2"]
    assert set(entry["capabilities"]) == {"AESTHETIC", "LIGHTING", "WAYFINDING"}


def test_neon_light_strip_v2_rollout(catalog: dict) -> None:
    entry = catalog["primitives"]["neon_light_strip_v2"]
    assert entry["rollout"] == "EXPERIMENTAL"


def test_neon_light_strip_v2_zero_power_generation(catalog: dict) -> None:
    entry = catalog["primitives"]["neon_light_strip_v2"]
    assert entry["sim"]["power_generation_kw"] == 0.0


def test_neon_light_strip_v2_low_power_consumption(catalog: dict) -> None:
    entry = catalog["primitives"]["neon_light_strip_v2"]
    assert 0 < entry["sim"]["power_consumption_kw"] <= 1.0


def test_neon_light_strip_v2_max_segments(catalog: dict) -> None:
    entry = catalog["primitives"]["neon_light_strip_v2"]
    assert entry["constraints"]["max_contiguous_segments"] == 32


def test_neon_light_strip_v2_attach_constraint(catalog: dict) -> None:
    entry = catalog["primitives"]["neon_light_strip_v2"]
    for face in entry["constraints"]["attach_to"]:
        assert face in ("block_face", "module_face")


def test_neon_light_strip_v2_render_fallback(catalog: dict) -> None:
    entry = catalog["primitives"]["neon_light_strip_v2"]
    assert entry["render"]["fallback"] == "emissive_strip"


def test_neon_light_strip_v2_color_palette(catalog: dict) -> None:
    entry = catalog["primitives"]["neon_light_strip_v2"]
    palette = entry["render"]["metadata"]["color_palette"]
    assert isinstance(palette, list) and len(palette) > 0


def test_neon_light_strip_v2_glow_intensity(catalog: dict) -> None:
    entry = catalog["primitives"]["neon_light_strip_v2"]
    intensity = entry["render"]["metadata"]["glow_intensity"]
    assert 0.0 < intensity <= 1.0


def test_all_primitives_validate(catalog: dict, schema: dict) -> None:
    """Every primitive in the catalog must individually pass schema checks."""
    for name, prim in catalog["primitives"].items():
        jsonschema.validate(
            instance=prim,
            schema=schema["definitions"]["primitive"],
        )
