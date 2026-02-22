"""
Simulation tick-effect handlers for sector-sim primitives.

Each effect function receives the primitive's sim config, the current sector
state, and a deterministic RNG seed. Effects MUST be pure functions of their
inputs so that sim output is reproducible across seeds.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Protocol


class SectorState(Protocol):
    """Minimal interface expected by effect handlers."""

    def get_local_visibility(self) -> float: ...
    def set_local_visibility(self, value: float) -> None: ...
    def get_power_budget_kw(self) -> float: ...
    def consume_power_kw(self, amount: float) -> bool: ...


# ---------------------------------------------------------------------------
# Effect registry
# ---------------------------------------------------------------------------

_EFFECT_REGISTRY: Dict[str, Any] = {}


def register_effect(name: str):
    """Decorator that registers a tick-effect handler by name."""

    def decorator(fn):
        _EFFECT_REGISTRY[name] = fn
        return fn

    return decorator


def get_effect(name: str):
    """Look up a registered effect handler; raises KeyError if unknown."""
    return _EFFECT_REGISTRY[name]


def list_effects() -> list[str]:
    return sorted(_EFFECT_REGISTRY.keys())


# ---------------------------------------------------------------------------
# Built-in effects
# ---------------------------------------------------------------------------


@register_effect("life_support")
def life_support_effect(
    magnitude: float,
    scope: str,
    sector_state: SectorState,
    seed: int,
) -> None:
    """Maintains life-support level in the given scope (deterministic, seed-independent)."""
    # Life-support is a simple additive contribution; no randomness.
    _ = seed  # unused but required by interface
    pass  # actual integration handled by sector aggregator


@register_effect("visibility_score")
def visibility_score_effect(
    magnitude: float,
    scope: str,
    sector_state: SectorState,
    seed: int,
) -> None:
    """Contributes to local visibility score used by drone-traffic heuristics.

    The contribution is purely additive and deterministic — no randomness is
    involved so that the sim contract test can assert identical output across
    different seeds.

    magnitude: visibility contribution *per segment* (segments resolved at
               placement time and encoded in instance state).
    scope:     must be LOCAL for this effect.
    """
    _ = seed  # deterministic — seed is unused
    if scope != "LOCAL":
        raise ValueError(f"visibility_score effect only supports LOCAL scope, got {scope}")

    current = sector_state.get_local_visibility()
    # Clamp final value to [0.0, 1.0]
    new_value = min(1.0, current + magnitude)
    sector_state.set_local_visibility(new_value)


# ---------------------------------------------------------------------------
# Tick driver
# ---------------------------------------------------------------------------


def apply_tick_effects(
    primitive_sim_config: dict,
    sector_state: SectorState,
    seed: int,
) -> None:
    """Apply all tick effects declared by a primitive's sim config.

    Parameters
    ----------
    primitive_sim_config : dict
        The ``sim`` block from a catalog entry, containing
        ``power_consumption_kw``, ``power_generation_kw``, and ``tick_effects``.
    sector_state : SectorState
        Mutable handle to the current sector state.
    seed : int
        Deterministic seed for any effects that require reproducible randomness.
    """
    # Power bookkeeping
    consumption = primitive_sim_config.get("power_consumption_kw", 0.0)
    if consumption > 0.0:
        if not sector_state.consume_power_kw(consumption):
            return  # underpowered — skip effects this tick

    for effect_def in primitive_sim_config.get("tick_effects", []):
        handler = get_effect(effect_def["effect"])
        handler(
            magnitude=effect_def["magnitude"],
            scope=effect_def["scope"],
            sector_state=sector_state,
            seed=seed,
        )
