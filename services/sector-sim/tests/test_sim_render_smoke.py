"""Sim determinism contract tests and render fallback smoke tests."""

import json
import os
import time

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
CATALOG_PATH = os.path.join(BASE_DIR, "data", "catalog.json")
FALLBACKS_PATH = os.path.join(BASE_DIR, "render", "fallbacks.json")
SEMANTICS_PATH = os.path.join(BASE_DIR, "sim", "semantics.json")


def _load_json(path):
    with open(path) as f:
        return json.load(f)


def _compute_tick(prim_def, seed):
    """Minimal deterministic tick simulation.

    Given a primitive definition and a seed, compute the tick output.
    The contract is that the same inputs always produce the same outputs,
    with no randomness or seed-dependent branching.
    """
    power_delta = prim_def["sim"]["power_generation_kw"] - prim_def["sim"]["power_consumption_kw"]
    visibility = 0.0
    for effect in prim_def["sim"]["tick_effects"]:
        if effect["type"] == "visibility_contribution":
            visibility += effect["score"]
    return {
        "power_delta": power_delta,
        "visibility_score": visibility,
        "seed_echo": seed,  # echo back to prove it doesn't affect output logic
    }


class TestSimDeterminism:
    """Verify that sim tick output is deterministic across seeds."""

    def test_neon_light_strip_deterministic_across_seeds(self):
        catalog = _load_json(CATALOG_PATH)
        prim = catalog["primitives"]["neon_light_strip_v2"]

        results = [_compute_tick(prim, seed) for seed in range(100)]

        # All results (ignoring seed_echo) must be identical
        for r in results:
            assert r["power_delta"] == results[0]["power_delta"]
            assert r["visibility_score"] == results[0]["visibility_score"]

    def test_neon_light_strip_sim_values(self):
        catalog = _load_json(CATALOG_PATH)
        prim = catalog["primitives"]["neon_light_strip_v2"]
        result = _compute_tick(prim, seed=42)

        # zero generation - low consumption = negative delta
        assert result["power_delta"] < 0, "Should consume power, not generate"
        assert result["power_delta"] == -0.2
        assert result["visibility_score"] == 5.0

    def test_all_primitives_deterministic(self):
        """Every primitive in the catalog must produce deterministic tick output."""
        catalog = _load_json(CATALOG_PATH)
        for name, prim in catalog["primitives"].items():
            r1 = _compute_tick(prim, seed=0)
            r2 = _compute_tick(prim, seed=999)
            assert r1["power_delta"] == r2["power_delta"], f"{name} non-deterministic power_delta"
            assert r1["visibility_score"] == r2["visibility_score"], f"{name} non-deterministic visibility"


class TestRenderFallbackSmoke:
    """Verify render fallback behavior for primitives."""

    def test_known_fallbacks_exist(self):
        catalog = _load_json(CATALOG_PATH)
        fallbacks = _load_json(FALLBACKS_PATH)
        known = set(fallbacks["fallback_renderers"].keys())
        for name, prim in catalog["primitives"].items():
            assert prim["render"]["fallback"] in known, (
                f"{name} uses fallback '{prim['render']['fallback']}' not in fallbacks registry"
            )

    def test_emissive_strip_is_emissive(self):
        fallbacks = _load_json(FALLBACKS_PATH)
        strip = fallbacks["fallback_renderers"]["emissive_strip"]
        assert strip["emissive"] is True, "emissive_strip must be emissive"

    def test_neon_light_strip_has_color_palette(self):
        catalog = _load_json(CATALOG_PATH)
        meta = catalog["primitives"]["neon_light_strip_v2"]["render"]["metadata"]
        assert "color_palette" in meta
        assert isinstance(meta["color_palette"], list)
        assert len(meta["color_palette"]) > 0

    def test_neon_light_strip_has_glow_intensity(self):
        catalog = _load_json(CATALOG_PATH)
        meta = catalog["primitives"]["neon_light_strip_v2"]["render"]["metadata"]
        assert "glow_intensity" in meta
        assert 0.0 < meta["glow_intensity"] <= 1.0

    def test_unknown_renderer_graceful_fallback(self):
        """Simulate what happens when a renderer doesn't know the fallback type.

        The contract is: if the fallback type is not recognized by a specific
        renderer, it should still render as an emissive strip (the catalog
        defines emissive=true for the fallback type).
        """
        fallbacks = _load_json(FALLBACKS_PATH)
        catalog = _load_json(CATALOG_PATH)
        prim = catalog["primitives"]["neon_light_strip_v2"]
        fb_name = prim["render"]["fallback"]

        # The fallback registry is the source of truth for unknown renderers
        fb_def = fallbacks["fallback_renderers"].get(fb_name)
        assert fb_def is not None, f"Fallback '{fb_name}' must be registered"
        assert fb_def["emissive"] is True, "Fallback must render as emissive"


class TestPerfSmoke:
    """Basic performance smoke test to detect obvious regressions."""

    def test_tick_computation_perf(self):
        """10k ticks should complete well under 1 second."""
        catalog = _load_json(CATALOG_PATH)
        prim = catalog["primitives"]["neon_light_strip_v2"]

        start = time.monotonic()
        for seed in range(10_000):
            _compute_tick(prim, seed)
        elapsed = time.monotonic() - start

        assert elapsed < 1.0, f"10k ticks took {elapsed:.3f}s, expected < 1s"
