"use strict";

const { tick } = require("../services/sector-sim/sim/engine");
const catalog = require("../services/sector-sim/data/catalog.json");

const neon = catalog.primitives.neon_light_strip_v2;
const sectorState = { power: 100, visibility: 0 };

describe("deterministic sim contract — neon_light_strip_v2", () => {
  test("same seed produces identical output on repeated runs", () => {
    const seed = 42;
    const result1 = tick([neon], sectorState, seed);
    const result2 = tick([neon], sectorState, seed);
    expect(result1).toEqual(result2);
  });

  test("output is identical across 100 repeated invocations with same seed", () => {
    const seed = 12345;
    const baseline = tick([neon], sectorState, seed);
    for (let i = 0; i < 100; i++) {
      expect(tick([neon], sectorState, seed)).toEqual(baseline);
    }
  });

  test("different seeds still produce deterministic (not random) per-seed output", () => {
    const seeds = [1, 2, 3, 999, 65535];
    for (const seed of seeds) {
      const a = tick([neon], sectorState, seed);
      const b = tick([neon], sectorState, seed);
      expect(a).toEqual(b);
    }
  });

  test("neon_light_strip_v2 contributes visibility_score_delta", () => {
    const result = tick([neon], sectorState, 42);
    expect(result.visibility_score_delta).toBe(neon.sim.visibility_score);
  });

  test("neon_light_strip_v2 has zero power_delta (no generation)", () => {
    const result = tick([neon], sectorState, 42);
    expect(result.power_delta).toBe(0);
  });

  test("neon_light_strip_v2 consumes power", () => {
    const result = tick([neon], sectorState, 42);
    expect(result.power_consumed).toBe(neon.sim.power_consumption);
  });

  test("neon_light_strip_v2 contributes light_level_delta", () => {
    const result = tick([neon], sectorState, 42);
    expect(result.light_level_delta).toBe(1.0);
  });

  test("neon_light_strip_v2 contributes morale_delta via AESTHETIC", () => {
    const result = tick([neon], sectorState, 42);
    expect(result.morale_delta).toBeCloseTo(0.1, 5);
  });

  test("multiple neon strips produce linearly scaled output", () => {
    const singles = tick([neon], sectorState, 42);
    const triples = tick([neon, neon, neon], sectorState, 42);
    expect(triples.visibility_score_delta).toBeCloseTo(
      singles.visibility_score_delta * 3,
      5
    );
    expect(triples.power_consumed).toBeCloseTo(singles.power_consumed * 3, 5);
  });
});
