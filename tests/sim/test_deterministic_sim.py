"""Deterministic sim contract tests.

Verifies that sim tick functions produce identical output across multiple
invocations and random seeds, as required by the spec.
"""

from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
CATALOG_PATH = ROOT / "services" / "sector-sim" / "data" / "catalog.json"

# Import sim modules
import sys
sys.path.insert(0, str(ROOT / "services" / "sector-sim" / "src"))
from sim.visibility import tick_visibility  # noqa: E402
from sim.power import tick_power  # noqa: E402


@pytest.fixture
def catalog() -> dict:
    with open(CATALOG_PATH) as f:
        return json.load(f)


def _build_sector_state(catalog: dict) -> dict:
    """Create a sector state containing one of each primitive from the catalog."""
    primitives = []
    for name, defn in catalog["primitives"].items():
        primitives.append({**defn, "id": name})
    return {"primitives": primitives, "visibility_score": 0.0, "power": {}}


SEEDS = [0, 1, 42, 99999, 2**31 - 1]


@pytest.mark.parametrize("seed", SEEDS)
def test_visibility_deterministic_across_seeds(catalog: dict, seed: int) -> None:
    """tick_visibility must return the same result regardless of random seed."""
    random.seed(seed)
    state_a = _build_sector_state(catalog)
    result_a = tick_visibility(copy.deepcopy(state_a))

    random.seed(seed + 1)  # different seed
    state_b = _build_sector_state(catalog)
    result_b = tick_visibility(copy.deepcopy(state_b))

    assert result_a["visibility_score"] == result_b["visibility_score"]


@pytest.mark.parametrize("seed", SEEDS)
def test_power_deterministic_across_seeds(catalog: dict, seed: int) -> None:
    """tick_power must return the same result regardless of random seed."""
    random.seed(seed)
    state_a = _build_sector_state(catalog)
    result_a = tick_power(copy.deepcopy(state_a))

    random.seed(seed + 1)
    state_b = _build_sector_state(catalog)
    result_b = tick_power(copy.deepcopy(state_b))

    assert result_a["power"] == result_b["power"]


def test_neon_strip_zero_generation(catalog: dict) -> None:
    """neon_light_strip_v2 must produce zero power."""
    neon = catalog["primitives"]["neon_light_strip_v2"]
    state = {"primitives": [{**neon, "id": "neon_light_strip_v2"}], "power": {}}
    result = tick_power(state)
    assert result["power"]["generation_kw"] == 0.0


def test_neon_strip_positive_consumption(catalog: dict) -> None:
    """neon_light_strip_v2 must consume a small amount of power."""
    neon = catalog["primitives"]["neon_light_strip_v2"]
    state = {"primitives": [{**neon, "id": "neon_light_strip_v2"}], "power": {}}
    result = tick_power(state)
    assert result["power"]["consumption_kw"] > 0.0


def test_neon_strip_contributes_visibility(catalog: dict) -> None:
    """neon_light_strip_v2 must contribute to visibility score."""
    neon = catalog["primitives"]["neon_light_strip_v2"]
    state = {
        "primitives": [{**neon, "id": "neon_light_strip_v2"}],
        "visibility_score": 0.0,
    }
    result = tick_visibility(state)
    assert result["visibility_score"] > 0.0


def test_repeated_ticks_stable(catalog: dict) -> None:
    """Running multiple ticks on the same state must be idempotent."""
    state = _build_sector_state(catalog)
    for _ in range(10):
        state = tick_visibility(copy.deepcopy(state))
        state = tick_power(copy.deepcopy(state))
    first_vis = state["visibility_score"]
    first_power = state["power"]

    state2 = _build_sector_state(catalog)
    state2 = tick_visibility(state2)
    state2 = tick_power(state2)
    assert state2["visibility_score"] == first_vis
    assert state2["power"] == first_power
