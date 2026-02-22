"use strict";

const { resolve } = require("../services/sector-sim/render/fallback");

describe("render fallback smoke — neon_light_strip_v2", () => {
  test("unknown renderer returns emissive_strip fallback", () => {
    const result = resolve("neon_light_strip_v2", "unknown");
    expect(result.mode).toBe("fallback");
    expect(result.type).toBe("emissive_strip");
    expect(result.emissive).toBe(true);
  });

  test("null renderer returns emissive_strip fallback", () => {
    const result = resolve("neon_light_strip_v2", null);
    expect(result.mode).toBe("fallback");
    expect(result.type).toBe("emissive_strip");
    expect(result.emissive).toBe(true);
  });

  test("fallback includes glow_intensity from configurable defaults", () => {
    const result = resolve("neon_light_strip_v2", "unknown");
    expect(result.glow_intensity).toBe(2.5);
  });

  test("fallback includes default color", () => {
    const result = resolve("neon_light_strip_v2", "unknown");
    expect(result.color).toEqual([0.0, 1.0, 0.8, 1.0]);
  });

  test("fallback respects glow_intensity override", () => {
    const result = resolve("neon_light_strip_v2", "unknown", {
      glow_intensity: 7.0,
    });
    expect(result.glow_intensity).toBe(7.0);
  });

  test("fallback respects color override", () => {
    const customColor = [1.0, 0.0, 0.0, 1.0];
    const result = resolve("neon_light_strip_v2", "unknown", {
      color: customColor,
    });
    expect(result.color).toEqual(customColor);
  });

  test("known renderer returns model mode for neon_light_strip_v2", () => {
    const result = resolve("neon_light_strip_v2", "webgl2");
    expect(result.mode).toBe("model");
    expect(result.model).toBe("neon_light_strip_v2.glb");
  });

  test("completely unknown primitive returns safe magenta box fallback", () => {
    const result = resolve("nonexistent_widget_v99", "unknown");
    expect(result.mode).toBe("fallback");
    expect(result.type).toBe("box");
    expect(result.color).toEqual([1.0, 0.0, 1.0, 1.0]);
    expect(result.emissive).toBe(false);
  });

  test("existing non-emissive primitive falls back correctly", () => {
    const result = resolve("solar_panel_v1", "unknown");
    expect(result.mode).toBe("fallback");
    expect(result.type).toBe("flat_quad");
    expect(result.emissive).toBe(false);
  });
});
