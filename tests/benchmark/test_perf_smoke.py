"""Performance smoke benchmark.

Runs a configurable number of sim ticks with neon_light_strip_v2
primitives and asserts that per-tick latency stays within an acceptable
budget.  This is a smoke test, not a micro-benchmark—it catches gross
regressions, not subtle ones.
"""

import time
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "sector-sim" / "src"))

from sim.engine import SectorState, load_catalog, sim_tick

CATALOG_PATH = Path(__file__).resolve().parents[2] / "services" / "sector-sim" / "data" / "catalog.json"

# Budget: each tick must complete in under this many seconds.
# This is intentionally generous for CI environments.
MAX_PER_TICK_SECONDS = 0.01  # 10 ms

TICK_COUNT = 500

PLACED_PRIMITIVES = [
    {"primitive_id": "neon_light_strip_v2", "count": 20},
    {"primitive_id": "solar_panel_v1", "count": 10},
]


@pytest.fixture()
def catalog():
    return load_catalog(CATALOG_PATH)


def test_per_tick_latency_within_budget(catalog):
    """Average per-tick latency must stay under MAX_PER_TICK_SECONDS."""
    state = SectorState()

    start = time.perf_counter()
    for _ in range(TICK_COUNT):
        sim_tick(state, PLACED_PRIMITIVES, catalog)
    elapsed = time.perf_counter() - start

    avg_tick = elapsed / TICK_COUNT
    assert avg_tick < MAX_PER_TICK_SECONDS, (
        f"Average tick latency {avg_tick*1000:.3f}ms exceeds budget "
        f"{MAX_PER_TICK_SECONDS*1000:.1f}ms"
    )


def test_neon_strip_only_perf(catalog):
    """Benchmark with only neon light strips to isolate their cost."""
    state = SectorState()
    placed = [{"primitive_id": "neon_light_strip_v2", "count": 50}]

    start = time.perf_counter()
    for _ in range(TICK_COUNT):
        sim_tick(state, placed, catalog)
    elapsed = time.perf_counter() - start

    avg_tick = elapsed / TICK_COUNT
    assert avg_tick < MAX_PER_TICK_SECONDS, (
        f"Neon-only avg tick latency {avg_tick*1000:.3f}ms exceeds budget "
        f"{MAX_PER_TICK_SECONDS*1000:.1f}ms"
    )
