"use strict";

const { tick } = require("../services/sector-sim/sim/engine");
const catalog = require("../services/sector-sim/data/catalog.json");

const sectorState = { power: 100, visibility: 0 };
const TICK_COUNT = 10000;

// Budget: each tick must average under this many milliseconds.
// This is a smoke test, not a micro-benchmark — we just want to catch
// catastrophic regressions (e.g. accidental O(n^2) loops).
const MAX_AVG_TICK_MS = 1.0;

function benchmarkPrimitive(primitiveId) {
  const prim = catalog.primitives[primitiveId];
  const placed = [prim];
  const start = performance.now();
  for (let i = 0; i < TICK_COUNT; i++) {
    tick(placed, sectorState, i);
  }
  const elapsed = performance.now() - start;
  return elapsed / TICK_COUNT;
}

describe("per-tick perf smoke", () => {
  test(`neon_light_strip_v2: avg tick < ${MAX_AVG_TICK_MS}ms over ${TICK_COUNT} ticks`, () => {
    const avgMs = benchmarkPrimitive("neon_light_strip_v2");
    expect(avgMs).toBeLessThan(MAX_AVG_TICK_MS);
  });

  test("neon_light_strip_v2 is not meaningfully slower than solar_panel_v1", () => {
    const neonAvg = benchmarkPrimitive("neon_light_strip_v2");
    const solarAvg = benchmarkPrimitive("solar_panel_v1");
    // Allow up to 5x overhead (neon has 3 capabilities vs 1), but should
    // realistically be under 3x.
    expect(neonAvg).toBeLessThan(solarAvg * 5);
  });

  test(`32 contiguous neon strips tick within budget`, () => {
    const prim = catalog.primitives.neon_light_strip_v2;
    const placed = Array(32).fill(prim);
    const start = performance.now();
    for (let i = 0; i < TICK_COUNT; i++) {
      tick(placed, sectorState, i);
    }
    const elapsed = performance.now() - start;
    const avgMs = elapsed / TICK_COUNT;
    // 32 strips should still be well under 10ms per tick.
    expect(avgMs).toBeLessThan(10.0);
  });
});
