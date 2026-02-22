"""
Render fallback resolver for sector-sim primitives.

When a client renderer does not recognize a primitive's native render type,
the fallback configuration is used to guarantee *something* sensible is drawn.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Fallback render types
# ---------------------------------------------------------------------------

_KNOWN_FALLBACK_TYPES = {
    "box",
    "flat_panel",
    "emissive_strip",
}


@dataclass(frozen=True)
class FallbackRender:
    """Resolved fallback render descriptor."""

    render_type: str
    emissive: bool
    color: str  # hex, e.g. "#00FFFF"

    # Additional metadata forwarded to the renderer.
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_DEFAULT_FALLBACK = FallbackRender(
    render_type="box",
    emissive=False,
    color="#FF00FF",  # magenta — unmistakable "missing" color
)


def resolve_fallback(render_config: dict) -> FallbackRender:
    """Return a ``FallbackRender`` for the given primitive render block.

    If the declared fallback type is unknown, returns a safe magenta box so
    that the renderer never crashes or shows nothing.

    Parameters
    ----------
    render_config : dict
        The ``render`` block from a catalog entry.
    """
    fb = render_config.get("fallback")
    if fb is None:
        return _DEFAULT_FALLBACK

    fb_type = fb.get("type", "box")
    if fb_type not in _KNOWN_FALLBACK_TYPES:
        # Unknown type — degrade gracefully to safe default.
        return _DEFAULT_FALLBACK

    return FallbackRender(
        render_type=fb_type,
        emissive=fb.get("emissive", False),
        color=fb.get("color", _DEFAULT_FALLBACK.color),
        metadata=render_config.get("metadata", {}),
    )


def resolve_emissive_strip_metadata(render_config: dict) -> Dict[str, Any]:
    """Extract emissive-strip-specific metadata with safe defaults.

    Returns a dict with:
      - color_palette: list of hex strings (default: single-entry cyan)
      - glow_intensity: float in [0.0, 1.0] (default: 0.8)
    """
    meta = render_config.get("metadata", {})

    palette = meta.get("color_palette", ["#00FFFF"])
    if not isinstance(palette, list) or len(palette) == 0:
        palette = ["#00FFFF"]

    intensity = meta.get("glow_intensity", 0.8)
    glow_range = meta.get("glow_intensity_range", [0.0, 1.0])
    lo, hi = glow_range[0], glow_range[1]
    intensity = max(lo, min(hi, intensity))

    return {
        "color_palette": palette,
        "glow_intensity": intensity,
    }
