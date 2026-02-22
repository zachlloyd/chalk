"""
Render resolver for sector-sim primitives.

Resolves the render type for a primitive, falling back to the declared
fallback type when the requested renderer is unknown.
"""

from typing import Any


# Registry of known renderer types.
# Each entry maps a render type name to a callable that returns render config.
KNOWN_RENDERERS: set[str] = {
    "flat_panel",
    "beacon_pulse",
    "emissive_strip",
}

# Default fallback used when both the primary type and declared fallback
# are unknown. This should never happen with a valid catalog, but provides
# a safe last-resort.
ULTIMATE_FALLBACK_TYPE = "emissive_strip"
ULTIMATE_FALLBACK_CONFIG = {
    "type": "emissive_strip",
    "color_palette": ["#ffffff"],
    "glow_intensity": 0.5,
}


def resolve_render_config(
    primitive_id: str,
    catalog: dict[str, Any],
    renderer_name: str | None = None,
) -> dict[str, Any]:
    """Resolve the render configuration for a primitive.

    If renderer_name is provided and matches the primitive's render type,
    returns the full metadata. Otherwise falls back to the declared fallback
    type. If even the fallback is unknown, returns the ultimate fallback.

    Args:
        primitive_id: ID of the primitive in the catalog.
        catalog: The loaded primitive catalog.
        renderer_name: Optional specific renderer to request. If None,
            uses the primitive's declared type.

    Returns:
        Dict with resolved render configuration including type and metadata.
    """
    primitives = catalog.get("primitives", {})
    if primitive_id not in primitives:
        return {**ULTIMATE_FALLBACK_CONFIG, "resolved_from": "ultimate_fallback"}

    render = primitives[primitive_id]["render"]
    requested = renderer_name or render["type"]

    # Happy path: requested renderer is known
    if requested in KNOWN_RENDERERS and requested == render["type"]:
        return {
            "type": render["type"],
            "resolved_from": "primary",
            **render["metadata"],
        }

    # Fallback path: use declared fallback
    fallback_type = render.get("fallback", ULTIMATE_FALLBACK_TYPE)
    if fallback_type in KNOWN_RENDERERS:
        return {
            "type": fallback_type,
            "resolved_from": "fallback",
            **render["metadata"],
        }

    # Ultimate fallback: should not reach here with valid catalog
    return {**ULTIMATE_FALLBACK_CONFIG, "resolved_from": "ultimate_fallback"}
