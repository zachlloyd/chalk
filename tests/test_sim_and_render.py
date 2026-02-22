"""Simulation contract tests and render fallback smoke tests."""

import importlib.util
import os
import sys
import time

import pytest

# Import from hyphenated directory using importlib
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SIM_DIR = os.path.join(_ROOT, "services", "sector-sim", "sim")
_RENDER_DIR = os.path.join(_ROOT, "services", "sector-sim", "render")


def _import_from(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_engine = _import_from("engine", os.path.join(_SIM_DIR, "engine.py"))
_resolver = _import_from("resolver", os.path.join(_RENDER_DIR, "resolver.py"))

compute_local_visibility = _engine.compute_local_visibility
compute_power_budget = _engine.compute_power_budget
sim_tick = _engine.sim_tick
KNOWN_RENDERERS = _resolver.KNOWN_RENDERERS
resolve_render_config = _resolver.resolve_render_config


# ---------------------------------------------------------------------------
# Deterministic sim contract tests
# ---------------------------------------------------------------------------

class TestSimDeterminism:
    """Verify that simulation output is deterministic across seeds."""

    PLACED = ["solar_panel_v1", "cargo_beacon_v1", "neon_light_strip_v2"]
    SEEDS = [0, 1, 42, 999, 2**16]

    def test_sim_tick_identical_across_seeds(self, catalog):
        """sim_tick must produce identical power and visibility regardless of seed."""
        results = [sim_tick(self.PLACED, catalog, seed=s) for s in self.SEEDS]
        # All results must match (excluding the tick_seed marker itself)
        baseline_power = results[0]["power"]
        baseline_vis = results[0]["local_visibility"]
        for r in results[1:]:
            assert r["power"] == baseline_power
            assert r["local_visibility"] == baseline_vis

    def test_power_budget_deterministic(self, catalog):
        """compute_power_budget is deterministic."""
        results = [compute_power_budget(self.PLACED, catalog) for _ in range(10)]
        for r in results[1:]:
            assert r == results[0]

    def test_visibility_deterministic(self, catalog):
        """compute_local_visibility is deterministic."""
        results = [compute_local_visibility(self.PLACED, catalog) for _ in range(10)]
        for r in results[1:]:
            assert r == results[0]


# ---------------------------------------------------------------------------
# Neon light strip sim behavior
# ---------------------------------------------------------------------------

class TestNeonLightStripSim:
    """Test neon_light_strip_v2 simulation semantics."""

    def test_zero_power_generation(self, catalog):
        """neon_light_strip_v2 alone generates no power."""
        power = compute_power_budget(["neon_light_strip_v2"], catalog)
        assert power["total_generation"] == 0.0

    def test_positive_power_consumption(self, catalog):
        """neon_light_strip_v2 consumes some power."""
        power = compute_power_budget(["neon_light_strip_v2"], catalog)
        assert power["total_consumption"] > 0.0

    def test_contributes_to_visibility(self, catalog):
        """neon_light_strip_v2 contributes to local visibility score."""
        vis = compute_local_visibility(["neon_light_strip_v2"], catalog)
        assert vis > 0.0

    def test_visibility_contribution_value(self, catalog):
        """neon_light_strip_v2 visibility matches catalog value."""
        expected = catalog["primitives"]["neon_light_strip_v2"]["sim"][
            "visibility_contribution"
        ]
        vis = compute_local_visibility(["neon_light_strip_v2"], catalog)
        assert vis == expected

    def test_combined_visibility_with_beacon(self, catalog):
        """neon_light_strip_v2 + cargo_beacon_v1 visibility is additive."""
        neon_vis = compute_local_visibility(["neon_light_strip_v2"], catalog)
        beacon_vis = compute_local_visibility(["cargo_beacon_v1"], catalog)
        combined = compute_local_visibility(
            ["neon_light_strip_v2", "cargo_beacon_v1"], catalog
        )
        assert combined == neon_vis + beacon_vis


# ---------------------------------------------------------------------------
# Render fallback smoke tests
# ---------------------------------------------------------------------------

class TestRenderFallback:
    """Verify render resolver fallback behavior."""

    def test_neon_strip_primary_render(self, catalog):
        """neon_light_strip_v2 resolves to emissive_strip via primary path."""
        config = resolve_render_config("neon_light_strip_v2", catalog)
        assert config["type"] == "emissive_strip"
        assert config["resolved_from"] == "primary"
        assert "color_palette" in config
        assert "glow_intensity" in config

    def test_neon_strip_unknown_renderer_falls_back(self, catalog):
        """Unknown renderer gracefully falls back to emissive_strip."""
        config = resolve_render_config(
            "neon_light_strip_v2", catalog, renderer_name="unknown_future_renderer"
        )
        assert config["type"] == "emissive_strip"
        assert config["resolved_from"] == "fallback"

    def test_neon_strip_fallback_preserves_metadata(self, catalog):
        """Fallback render still includes the primitive's color palette."""
        config = resolve_render_config(
            "neon_light_strip_v2", catalog, renderer_name="unknown_future_renderer"
        )
        assert len(config["color_palette"]) >= 1

    def test_unknown_primitive_ultimate_fallback(self, catalog):
        """Completely unknown primitive gets ultimate fallback."""
        config = resolve_render_config("nonexistent_prim_xyz", catalog)
        assert config["type"] == "emissive_strip"
        assert config["resolved_from"] == "ultimate_fallback"

    def test_all_catalog_primitives_render_resolvable(self, catalog):
        """Every primitive in the catalog resolves to a known render type."""
        for prim_id in catalog["primitives"]:
            config = resolve_render_config(prim_id, catalog)
            assert config["type"] in KNOWN_RENDERERS, (
                f"{prim_id} resolved to unknown render type: {config['type']}"
            )


# ---------------------------------------------------------------------------
# Performance smoke benchmark
# ---------------------------------------------------------------------------

class TestPerfSmoke:
    """Basic perf smoke test — no meaningful regression per tick."""

    PLACED = ["solar_panel_v1", "cargo_beacon_v1", "neon_light_strip_v2"]
    TICK_COUNT = 1000
    MAX_TOTAL_SECONDS = 2.0  # generous budget for CI

    def test_sim_tick_perf(self, catalog):
        """1000 sim ticks complete within time budget."""
        start = time.perf_counter()
        for i in range(self.TICK_COUNT):
            sim_tick(self.PLACED, catalog, seed=i)
        elapsed = time.perf_counter() - start
        assert elapsed < self.MAX_TOTAL_SECONDS, (
            f"{self.TICK_COUNT} ticks took {elapsed:.3f}s "
            f"(budget: {self.MAX_TOTAL_SECONDS}s)"
        )
