"""
Sector simulation engine.

Processes primitives each tick to compute power budgets and local visibility
scores used by drone traffic heuristics.
"""

import json
import os
from typing import Any


CATALOG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "catalog.json"
)


def load_catalog(path: str | None = None) -> dict[str, Any]:
    """Load the primitive catalog from disk."""
    with open(path or CATALOG_PATH, "r") as f:
        return json.load(f)


def compute_power_budget(
    placed_primitives: list[str], catalog: dict[str, Any]
) -> dict[str, float]:
    """Compute net power generation and consumption for placed primitives.

    Returns dict with keys: total_generation, total_consumption, net_power.
    """
    total_gen = 0.0
    total_con = 0.0
    primitives = catalog["primitives"]
    for prim_id in placed_primitives:
        if prim_id not in primitives:
            continue
        power = primitives[prim_id]["sim"]["power"]
        total_gen += power["generation_per_tick"]
        total_con += power["consumption_per_tick"]
    return {
        "total_generation": total_gen,
        "total_consumption": total_con,
        "net_power": total_gen - total_con,
    }


def compute_local_visibility(
    placed_primitives: list[str], catalog: dict[str, Any]
) -> float:
    """Compute the local visibility score for a set of placed primitives.

    Primitives with LIGHTING or WAYFINDING capabilities contribute to
    the visibility score, which is used by drone traffic heuristics.
    """
    total_visibility = 0.0
    primitives = catalog["primitives"]
    for prim_id in placed_primitives:
        if prim_id not in primitives:
            continue
        prim = primitives[prim_id]
        caps = set(prim.get("capabilities", []))
        # Only primitives with lighting or wayfinding capabilities contribute
        if caps & {"LIGHTING", "WAYFINDING"}:
            total_visibility += prim["sim"]["visibility_contribution"]
    return total_visibility


def sim_tick(
    placed_primitives: list[str],
    catalog: dict[str, Any],
    seed: int = 0,
) -> dict[str, Any]:
    """Run a single deterministic simulation tick.

    The seed parameter exists for contract-test compatibility but the sim
    is fully deterministic — output must be identical regardless of seed.
    """
    power = compute_power_budget(placed_primitives, catalog)
    visibility = compute_local_visibility(placed_primitives, catalog)
    return {
        "power": power,
        "local_visibility": visibility,
        "tick_seed": seed,
    }
