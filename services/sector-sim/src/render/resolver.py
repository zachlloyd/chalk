"""Render resolver for sector primitives.

Selects the appropriate render path for a primitive.  When no specialised
renderer is registered for a primitive, the fallback configuration from the
catalog is used to produce a safe, emissive-strip (or other shape) render.
"""

from __future__ import annotations

from typing import Any

# Registry of specialised renderers keyed by primitive id.
# Primitives not in this registry will use their catalog fallback.
_RENDERER_REGISTRY: dict[str, Any] = {}


def register_renderer(primitive_id: str, renderer: Any) -> None:
    """Register a specialised renderer for *primitive_id*."""
    _RENDERER_REGISTRY[primitive_id] = renderer


def unregister_renderer(primitive_id: str) -> None:
    """Remove specialised renderer for *primitive_id*, if any."""
    _RENDERER_REGISTRY.pop(primitive_id, None)


class FallbackRenderResult:
    """Describes the visual output when the fallback path is used."""

    def __init__(
        self,
        primitive_id: str,
        shape: str,
        emissive: bool,
        color: str,
        opacity: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.primitive_id = primitive_id
        self.shape = shape
        self.emissive = emissive
        self.color = color
        self.opacity = opacity
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "primitive_id": self.primitive_id,
            "shape": self.shape,
            "emissive": self.emissive,
            "color": self.color,
            "opacity": self.opacity,
            "metadata": self.metadata,
        }


def resolve_render(primitive_def: dict[str, Any]) -> FallbackRenderResult | Any:
    """Resolve the render output for a primitive definition.

    If a specialised renderer is registered for the primitive, delegate to it.
    Otherwise, build a :class:`FallbackRenderResult` from the primitive's
    ``render.fallback`` catalog entry—guaranteeing that even unknown renderers
    produce a visible, emissive (when configured) output.
    """
    prim_id = primitive_def["id"]

    if prim_id in _RENDERER_REGISTRY:
        return _RENDERER_REGISTRY[prim_id](primitive_def)

    fb = primitive_def["render"]["fallback"]
    return FallbackRenderResult(
        primitive_id=prim_id,
        shape=fb["type"],
        emissive=fb.get("emissive", False),
        color=fb.get("color", "#FFFFFF"),
        opacity=fb.get("opacity", 1.0),
        metadata=primitive_def["render"].get("metadata"),
    )
