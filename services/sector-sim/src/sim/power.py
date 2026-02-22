"""
Power budget computation for sector sim.
"""

from __future__ import annotations

from typing import Any


def compute_power_balance(primitives: list[dict[str, Any]]) -> dict[str, float]:
    """Return generation, consumption, and net power across primitives."""
    generation = sum(
        float(p.get("sim", {}).get("power_generation_kw", 0.0)) for p in primitives
    )
    consumption = sum(
        float(p.get("sim", {}).get("power_consumption_kw", 0.0)) for p in primitives
    )
    return {
        "generation_kw": generation,
        "consumption_kw": consumption,
        "net_kw": generation - consumption,
    }


def tick_power(sector_state: dict[str, Any]) -> dict[str, Any]:
    """Deterministic per-tick power update."""
    primitives: list[dict[str, Any]] = sector_state.get("primitives", [])
    sector_state["power"] = compute_power_balance(primitives)
    return sector_state
