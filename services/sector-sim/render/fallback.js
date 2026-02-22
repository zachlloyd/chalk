"use strict";

const renderMetadata = require("./metadata.json");

/**
 * Resolve render instructions for a primitive.
 *
 * If the requested renderer is unavailable (e.g. the model file is missing or
 * the renderer is unknown), the fallback render config from metadata is used.
 *
 * @param {string} primitiveId - Catalog ID of the primitive.
 * @param {string|null} renderer - Name of the renderer, or null to force fallback.
 * @param {Object} [overrides] - Optional config overrides (color_palette, glow_intensity, etc.).
 * @returns {Object} Render instructions.
 */
function resolve(primitiveId, renderer, overrides = {}) {
  const meta = renderMetadata[primitiveId];
  if (!meta) {
    // Completely unknown primitive — return a minimal safe default.
    return {
      primitive_id: primitiveId,
      mode: "fallback",
      type: "box",
      color: [1.0, 0.0, 1.0, 1.0], // magenta = "missing" sentinel
      emissive: false,
      glow_intensity: 0,
    };
  }

  // If the renderer is known and the model exists, use it directly.
  if (renderer && renderer !== "unknown") {
    return {
      primitive_id: primitiveId,
      mode: "model",
      model: meta.model,
      renderer,
    };
  }

  // Fallback path: use the metadata fallback config with optional overrides.
  const fb = meta.fallback;
  const glowIntensity =
    overrides.glow_intensity ??
    (meta.configurable.glow_intensity
      ? meta.configurable.glow_intensity.default
      : fb.glow_intensity ?? 0);

  return {
    primitive_id: primitiveId,
    mode: "fallback",
    type: fb.type,
    color: overrides.color ?? fb.color,
    emissive: fb.emissive,
    glow_intensity: glowIntensity,
  };
}

module.exports = { resolve };
