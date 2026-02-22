"""Sector simulation engine.

Processes primitives each tick, computing power budgets and local effects
such as visibility scores used by drone traffic heuristics.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CATALOG_PATH = Path(__file__).resolve().parents[2] / "data" / "catalog.json"


def load_catalog(path: Path | None = None) -> dict[str, Any]:
    """Load and return the primitive catalog."""
    with open(path or CATALOG_PATH) as f:
        return json.load(f)


def get_primitive(catalog: dict[str, Any], primitive_id: str) -> dict[str, Any]:
    """Retrieve a single primitive definition from the catalog."""
    prims = catalog.get("primitives", {})
    if primitive_id not in prims:
        raise KeyError(f"Unknown primitive: {primitive_id}")
    return prims[primitive_id]


class SectorState:
    """Mutable state for a single sector during simulation."""

    def __init__(self) -> None:
        self.total_power_generation: float = 0.0
        self.total_power_consumption: float = 0.0
        self.local_visibility_score: float = 0.0
        self.tick_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_power_generation": self.total_power_generation,
            "total_power_consumption": self.total_power_consumption,
            "local_visibility_score": self.local_visibility_score,
            "tick_count": self.tick_count,
        }


def sim_tick(
    state: SectorState,
    placed_primitives: list[dict[str, Any]],
    catalog: dict[str, Any],
) -> SectorState:
    """Run one simulation tick.

    For each placed primitive, accumulate power budget and apply any sim
    effects.  The tick is fully deterministic—identical inputs always produce
    identical outputs regardless of iteration order because we sort placed
    primitives by id before processing.

    Parameters
    ----------
    state:
        Current sector state (mutated in place and returned).
    placed_primitives:
        List of dicts with at least ``{"primitive_id": "<id>", "count": <n>}``.
    catalog:
        The full primitive catalog dict.
    """
    # Sort for determinism
    sorted_primitives = sorted(placed_primitives, key=lambda p: p["primitive_id"])

    for entry in sorted_primitives:
        prim_id = entry["primitive_id"]
        count = entry.get("count", 1)
        prim = get_primitive(catalog, prim_id)
        sim_cfg = prim["sim"]

        state.total_power_generation += sim_cfg["power_generation"] * count
        state.total_power_consumption += sim_cfg["power_consumption"] * count

        for effect in sim_cfg.get("effects", []):
            if effect["type"] == "VISIBILITY_SCORE" and effect["scope"] == "LOCAL":
                state.local_visibility_score += effect["value"] * count

    state.tick_count += 1
    return state
