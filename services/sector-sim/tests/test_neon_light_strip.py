"""
Tests for the neon_light_strip_v2 primitive.

Covers:
  1. Schema validation — catalog entry satisfies primitive.schema.json
  2. Deterministic sim contract — identical output across different seeds
  3. Render fallback smoke — unknown renderer gracefully displays emissive strip
  4. Perf smoke benchmark — no meaningful per-tick regression
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

import jsonschema
import pytest

# Paths ------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parents[1]  # services/sector-sim
_CATALOG_PATH = _ROOT / "data" / "catalog.json"
_SCHEMA_PATH = _ROOT.parent.parent / "schemas" / "primitive.schema.json"

# Helpers ----------------------------------------------------------------

def _load_json(path: Path) -> Any:
    with open(path) as f:
        return json.load(f)


def _get_primitive(catalog: dict, primitive_id: str) -> dict:
    for p in catalog["primitives"]:
        if p["id"] == primitive_id:
            return p
    raise KeyError(f"Primitive {primitive_id!r} not found in catalog")


# Stub SectorState for sim tests -----------------------------------------

class StubSectorState:
    """In-memory sector state that satisfies the SectorState protocol."""

    def __init__(self, visibility: float = 0.0, power_kw: float = 100.0):
        self._visibility = visibility
        self._power_kw = power_kw

    def get_local_visibility(self) -> float:
        return self._visibility

    def set_local_visibility(self, value: float) -> None:
        self._visibility = value

    def get_power_budget_kw(self) -> float:
        return self._power_kw

    def consume_power_kw(self, amount: float) -> bool:
        if amount > self._power_kw:
            return False
        self._power_kw -= amount
        return True


# ========================================================================
# 1. Schema validation
# ========================================================================

class TestSchemaValidation:
    """Validate that neon_light_strip_v2 conforms to primitive.schema.json."""

    @pytest.fixture()
    def schema(self) -> dict:
        return _load_json(_SCHEMA_PATH)

    @pytest.fixture()
    def primitive(self) -> dict:
        catalog = _load_json(_CATALOG_PATH)
        return _get_primitive(catalog, "neon_light_strip_v2")

    def test_validates_against_schema(self, schema: dict, primitive: dict) -> None:
        """Full schema validation passes with no errors."""
        jsonschema.validate(instance=primitive, schema=schema)

    def test_id_format(self, primitive: dict) -> None:
        assert primitive["id"] == "neon_light_strip_v2"

    def test_category_is_entity(self, primitive: dict) -> None:
        assert primitive["category"] == "ENTITY"

    def test_capabilities(self, primitive: dict) -> None:
        assert set(primitive["capabilities"]) == {"AESTHETIC", "LIGHTING", "WAYFINDING"}

    def test_rollout_experimental(self, primitive: dict) -> None:
        assert primitive["rollout"] == "EXPERIMENTAL"

    def test_zero_power_generation(self, primitive: dict) -> None:
        assert primitive["sim"]["power_generation_kw"] == 0.0

    def test_low_power_consumption(self, primitive: dict) -> None:
        assert 0 < primitive["sim"]["power_consumption_kw"] <= 2.0

    def test_visibility_score_effect_present(self, primitive: dict) -> None:
        effects = primitive["sim"]["tick_effects"]
        vis_effects = [e for e in effects if e["effect"] == "visibility_score"]
        assert len(vis_effects) == 1
        assert vis_effects[0]["scope"] == "LOCAL"
        assert vis_effects[0]["magnitude"] > 0

    def test_constraints_attachment(self, primitive: dict) -> None:
        assert primitive["constraints"]["attachment"] == "block_or_module_face"

    def test_constraints_max_segments(self, primitive: dict) -> None:
        assert primitive["constraints"]["max_contiguous_segments"] == 32

    def test_all_catalog_entries_valid(self, schema: dict) -> None:
        """Every primitive in catalog.json must pass schema validation."""
        catalog = _load_json(_CATALOG_PATH)
        for entry in catalog["primitives"]:
            jsonschema.validate(instance=entry, schema=schema)


# ========================================================================
# 2. Deterministic sim contract test
# ========================================================================

class TestDeterministicSimContract:
    """Verify that sim output is identical across different seeds."""

    @pytest.fixture()
    def sim_config(self) -> dict:
        catalog = _load_json(_CATALOG_PATH)
        return _get_primitive(catalog, "neon_light_strip_v2")["sim"]

    def _run_tick(self, sim_config: dict, seed: int, initial_vis: float = 0.0) -> float:
        """Run one sim tick and return the resulting visibility score."""
        # Import here so module-level import errors are caught as test failures
        import sys, importlib
        sim_dir = str(_ROOT / "sim")
        if sim_dir not in sys.path:
            sys.path.insert(0, sim_dir)

        from effects import apply_tick_effects

        state = StubSectorState(visibility=initial_vis, power_kw=100.0)
        apply_tick_effects(sim_config, state, seed=seed)
        return state.get_local_visibility()

    def test_same_output_across_seeds(self, sim_config: dict) -> None:
        """Different seeds must produce identical visibility contributions."""
        results = [self._run_tick(sim_config, seed=s) for s in [0, 42, 9999, 2**31 - 1]]
        assert len(set(results)) == 1, f"Non-deterministic output: {results}"

    def test_visibility_increases(self, sim_config: dict) -> None:
        """Visibility score must increase from zero after one tick."""
        result = self._run_tick(sim_config, seed=1, initial_vis=0.0)
        assert result > 0.0

    def test_visibility_clamped_at_one(self, sim_config: dict) -> None:
        """Visibility must never exceed 1.0."""
        result = self._run_tick(sim_config, seed=1, initial_vis=0.99)
        assert result <= 1.0

    def test_underpowered_skips_effects(self, sim_config: dict) -> None:
        """When power budget is insufficient, effects should not apply."""
        import sys
        sim_dir = str(_ROOT / "sim")
        if sim_dir not in sys.path:
            sys.path.insert(0, sim_dir)

        from effects import apply_tick_effects

        state = StubSectorState(visibility=0.0, power_kw=0.0)
        apply_tick_effects(sim_config, state, seed=1)
        assert state.get_local_visibility() == 0.0


# ========================================================================
# 3. Render fallback smoke test
# ========================================================================

class TestRenderFallbackSmoke:
    """Confirm that unknown renderers gracefully display as emissive strip."""

    @pytest.fixture()
    def render_config(self) -> dict:
        catalog = _load_json(_CATALOG_PATH)
        return _get_primitive(catalog, "neon_light_strip_v2")["render"]

    def _import_fallback(self):
        import sys, importlib
        render_dir = str(_ROOT / "render")
        if render_dir not in sys.path:
            sys.path.insert(0, render_dir)
        from fallback import resolve_fallback, resolve_emissive_strip_metadata, FallbackRender
        return resolve_fallback, resolve_emissive_strip_metadata, FallbackRender

    def test_known_type_resolves_correctly(self, render_config: dict) -> None:
        resolve_fallback, _, FallbackRender = self._import_fallback()
        fb = resolve_fallback(render_config)
        assert fb.render_type == "emissive_strip"
        assert fb.emissive is True
        assert fb.color == "#00FFFF"

    def test_unknown_type_degrades_to_safe_default(self) -> None:
        """When fallback type is unrecognized, a safe magenta box is returned."""
        resolve_fallback, _, FallbackRender = self._import_fallback()
        weird_config = {
            "fallback": {"type": "holographic_projection", "emissive": True, "color": "#AABBCC"},
            "metadata": {},
        }
        fb = resolve_fallback(weird_config)
        assert fb.render_type == "box"
        assert fb.emissive is False
        assert fb.color == "#FF00FF"

    def test_missing_fallback_block(self) -> None:
        """Completely missing fallback block still returns a safe render."""
        resolve_fallback, _, _ = self._import_fallback()
        fb = resolve_fallback({})
        assert fb.render_type == "box"

    def test_emissive_strip_metadata_defaults(self) -> None:
        """Metadata resolver provides safe defaults when fields are missing."""
        _, resolve_meta, _ = self._import_fallback()
        meta = resolve_meta({"metadata": {}})
        assert meta["color_palette"] == ["#00FFFF"]
        assert 0.0 <= meta["glow_intensity"] <= 1.0

    def test_emissive_strip_metadata_from_catalog(self, render_config: dict) -> None:
        _, resolve_meta, _ = self._import_fallback()
        meta = resolve_meta(render_config)
        assert len(meta["color_palette"]) == 5
        assert meta["glow_intensity"] == 0.85


# ========================================================================
# 4. Perf smoke benchmark
# ========================================================================

class TestPerfSmokeBenchmark:
    """Sanity-check that a single tick does not regress beyond a generous budget."""

    # Budget: 1 ms per tick is extremely generous for a single-primitive tick.
    TICK_BUDGET_SECONDS = 0.001

    @pytest.fixture()
    def sim_config(self) -> dict:
        catalog = _load_json(_CATALOG_PATH)
        return _get_primitive(catalog, "neon_light_strip_v2")["sim"]

    def test_single_tick_within_budget(self, sim_config: dict) -> None:
        import sys
        sim_dir = str(_ROOT / "sim")
        if sim_dir not in sys.path:
            sys.path.insert(0, sim_dir)
        from effects import apply_tick_effects

        state = StubSectorState(visibility=0.0, power_kw=1000.0)

        # Warm up
        apply_tick_effects(sim_config, state, seed=0)

        # Timed run (average of 100 ticks)
        start = time.perf_counter()
        iterations = 100
        for i in range(iterations):
            state._visibility = 0.0
            state._power_kw = 1000.0
            apply_tick_effects(sim_config, state, seed=i)
        elapsed = (time.perf_counter() - start) / iterations

        assert elapsed < self.TICK_BUDGET_SECONDS, (
            f"Per-tick time {elapsed*1000:.3f}ms exceeds budget "
            f"{self.TICK_BUDGET_SECONDS*1000:.3f}ms"
        )
