"""
Fallback render resolver.

When a renderer does not recognize a primitive's render type, this module
provides a safe degradation path using the fallback_registry.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "data" / "fallback_registry.json"


def load_fallback_registry() -> dict[str, Any]:
    """Load the fallback renderer registry from disk."""
    with open(_REGISTRY_PATH) as f:
        return json.load(f)["fallback_renderers"]


def resolve_fallback(primitive: dict[str, Any]) -> dict[str, Any]:
    """Resolve fallback render parameters for a primitive.

    Returns a dict with all parameters needed to render the primitive using
    its designated fallback renderer.  If the fallback type is unknown, a
    minimal emissive-strip representation is returned as the ultimate safe
    default.
    """
    registry = load_fallback_registry()
    render_cfg = primitive.get("render", {})
    fallback_name = render_cfg.get("fallback", "emissive_strip")
    metadata = render_cfg.get("metadata", {})

    base = registry.get(fallback_name)
    if base is None:
        # Unknown fallback type → degrade to emissive_strip
        base = registry.get("emissive_strip", {
            "geometry": "strip",
            "material": "emissive_unlit",
            "emissive": True,
            "default_color": "#FFFFFF",
            "default_glow_intensity": 0.5,
            "default_strip_width_m": 0.05,
        })

    result: dict[str, Any] = {**base}

    # Override defaults with primitive-specific metadata
    if "color_palette" in metadata:
        result["color"] = metadata["color_palette"][0]
        result["color_palette"] = metadata["color_palette"]
    elif "default_color" in result:
        result["color"] = result.pop("default_color")

    if "glow_intensity" in metadata:
        result["glow_intensity"] = metadata["glow_intensity"]
    elif "default_glow_intensity" in result:
        result["glow_intensity"] = result.pop("default_glow_intensity")

    if "strip_width_m" in metadata:
        result["strip_width_m"] = metadata["strip_width_m"]
    elif "default_strip_width_m" in result:
        result["strip_width_m"] = result.pop("default_strip_width_m")

    return result
