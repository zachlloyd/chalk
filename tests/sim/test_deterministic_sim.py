"""Deterministic simulation contract tests.

Verifies that the sim engine produces identical output across multiple
runs with different seeds / iteration patterns, ensuring no hidden
non-determinism.
"""

import copy
import json
import random
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "sector-sim" / "src"))

from sim.engine import SectorState, load_catalog, sim_tick

CATALOG_PATH = Path(__file__).resolve().parents[2] / "services" / "sector-sim" / "data" / "catalog.json"

PLACED_PRIMITIVES = [
    {"primitive_id": "neon_light_strip_v2", "count": 5},
    {"primitive_id": "solar_panel_v1", "count": 3},
]


@pytest.fixture()
def catalog():
    return load_catalog(CATALOG_PATH)


def _run_n_ticks(catalog, placed, n=10):
    """Run *n* ticks and return the final state dict."""
    state = SectorState()
    for _ in range(n):
        sim_tick(state, placed, catalog)
    return state.to_dict()


def test_deterministic_across_seeds(catalog):
    """Running the same scenario with different random seeds must produce
    identical sim output, proving the engine has no seed-dependent behaviour."""
    results = []
    for seed in [0, 42, 12345, 999999]:
        random.seed(seed)
        result = _run_n_ticks(catalog, PLACED_PRIMITIVES, n=20)
        results.append(result)

    first = results[0]
    for i, r in enumerate(results[1:], start=1):
        assert r == first, f"Seed index {i} diverged from seed index 0: {r} != {first}"


def test_deterministic_across_repeated_runs(catalog):
    """Two identical back-to-back runs must yield the same output."""
    r1 = _run_n_ticks(catalog, PLACED_PRIMITIVES, n=50)
    r2 = _run_n_ticks(catalog, PLACED_PRIMITIVES, n=50)
    assert r1 == r2


def test_deterministic_with_shuffled_input(catalog):
    """Shuffling the placed-primitives list must not change the output,
    since the engine sorts internally for determinism."""
    baseline = _run_n_ticks(catalog, PLACED_PRIMITIVES, n=10)

    for seed in range(10):
        shuffled = copy.deepcopy(PLACED_PRIMITIVES)
        random.seed(seed)
        random.shuffle(shuffled)
        result = _run_n_ticks(catalog, shuffled, n=10)
        assert result == baseline, f"Shuffled with seed {seed} diverged"


def test_neon_strip_visibility_score_accumulated(catalog):
    """Verify that VISIBILITY_SCORE effect accumulates correctly."""
    state = SectorState()
    placed = [{"primitive_id": "neon_light_strip_v2", "count": 4}]
    sim_tick(state, placed, catalog)

    neon = catalog["primitives"]["neon_light_strip_v2"]
    vis_effect = next(e for e in neon["sim"]["effects"] if e["type"] == "VISIBILITY_SCORE")
    expected = vis_effect["value"] * 4
    assert state.local_visibility_score == pytest.approx(expected)


def test_neon_strip_zero_power_generation(catalog):
    """Neon light strip must not generate power."""
    state = SectorState()
    placed = [{"primitive_id": "neon_light_strip_v2", "count": 10}]
    sim_tick(state, placed, catalog)
    assert state.total_power_generation == 0.0


def test_neon_strip_power_consumption(catalog):
    """Neon light strip must consume a small amount of power."""
    state = SectorState()
    placed = [{"primitive_id": "neon_light_strip_v2", "count": 1}]
    sim_tick(state, placed, catalog)
    assert state.total_power_consumption > 0.0
    assert state.total_power_consumption < 5.0  # "low" consumption
