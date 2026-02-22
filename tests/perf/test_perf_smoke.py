"""Performance smoke benchmark.

Ensures that adding neon_light_strip_v2 does not introduce meaningful
per-tick performance regression.  The threshold is generous — this is a
smoke test, not a micro-benchmark.
"""

from __future__ import annotations

import copy
import json
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
CATALOG_PATH = ROOT / "services" / "sector-sim" / "data" / "catalog.json"

sys.path.insert(0, str(ROOT / "services" / "sector-sim" / "src"))
from sim.visibility import tick_visibility  # noqa: E402
from sim.power import tick_power  # noqa: E402

# Budget: 50 ms per tick on a sector with 500 primitives
TICK_BUDGET_SECONDS = 0.05
NUM_PRIMITIVES = 500
NUM_TICKS = 20


@pytest.fixture
def catalog() -> dict:
    with open(CATALOG_PATH) as f:
        return json.load(f)


def _build_large_sector(catalog: dict, count: int) -> dict:
    """Build a sector state with *count* primitives (round-robin from catalog)."""
    prim_defs = list(catalog["primitives"].values())
    primitives = []
    for i in range(count):
        defn = prim_defs[i % len(prim_defs)]
        primitives.append({**defn, "id": f"prim_{i}"})
    return {"primitives": primitives, "visibility_score": 0.0, "power": {}}


def test_tick_performance(catalog: dict) -> None:
    """Average tick time must stay within budget."""
    state = _build_large_sector(catalog, NUM_PRIMITIVES)

    # Warm-up
    for _ in range(3):
        s = copy.deepcopy(state)
        tick_visibility(s)
        tick_power(s)

    elapsed_times: list[float] = []
    for _ in range(NUM_TICKS):
        s = copy.deepcopy(state)
        t0 = time.perf_counter()
        tick_visibility(s)
        tick_power(s)
        elapsed_times.append(time.perf_counter() - t0)

    avg_tick = sum(elapsed_times) / len(elapsed_times)
    assert avg_tick < TICK_BUDGET_SECONDS, (
        f"Average tick {avg_tick:.4f}s exceeds budget {TICK_BUDGET_SECONDS}s"
    )
