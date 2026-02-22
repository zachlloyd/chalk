"""
Visibility score computation for sector sim.

Primitives with WAYFINDING or LIGHTING capabilities contribute to local
visibility scores consumed by drone traffic heuristics.
"""

from __future__ import annotations

from typing import Any


def compute_visibility_contribution(primitive: dict[str, Any]) -> float:
    """Return the visibility score contribution for a single primitive.

    Rules:
      - Only primitives with WAYFINDING or LIGHTING contribute.
      - The base contribution is read from sim.visibility_score_contribution.
      - Defaults to 0.0 if the field is absent or the primitive lacks the
        required capabilities.
    """
    capabilities: list[str] = primitive.get("capabilities", [])
    contributing_caps = {"WAYFINDING", "LIGHTING"}
    if not contributing_caps.intersection(capabilities):
        return 0.0
    return float(primitive.get("sim", {}).get("visibility_score_contribution", 0.0))


def aggregate_visibility(primitives: list[dict[str, Any]]) -> float:
    """Sum visibility contributions across all primitives in a sector."""
    return sum(compute_visibility_contribution(p) for p in primitives)


def tick_visibility(sector_state: dict[str, Any]) -> dict[str, Any]:
    """Deterministic per-tick visibility update.

    Reads primitives from *sector_state["primitives"]*, computes the
    aggregate visibility score, and writes it back to
    *sector_state["visibility_score"]*.

    This function is **deterministic**: identical input always produces
    identical output regardless of the random seed.
    """
    primitives: list[dict[str, Any]] = sector_state.get("primitives", [])
    sector_state["visibility_score"] = aggregate_visibility(primitives)
    return sector_state
