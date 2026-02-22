"use strict";

const { CAPABILITIES } = require("./capabilities");

/**
 * Simple seeded PRNG (mulberry32) for deterministic simulation.
 */
function createRng(seed) {
  let s = seed | 0;
  return function () {
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Run a single sim tick for a list of placed primitives.
 *
 * @param {Object[]} placedPrimitives - Array of primitive catalog entries that
 *   are placed in the sector.
 * @param {Object} sectorState - Current sector state (power, visibility, etc.).
 * @param {number} seed - RNG seed for this tick.
 * @returns {Object} Aggregated tick output deltas.
 */
function tick(placedPrimitives, sectorState, seed) {
  const rng = createRng(seed);

  const output = {
    power_delta: 0,
    power_consumed: 0,
    light_level_delta: 0,
    morale_delta: 0,
    visibility_score_delta: 0,
  };

  for (const primitive of placedPrimitives) {
    // Power consumption is always deducted
    output.power_consumed += primitive.sim.power_consumption;

    // Run each capability hook
    for (const capName of primitive.capabilities) {
      const cap = CAPABILITIES[capName];
      if (!cap) {
        throw new Error(`Unknown capability: ${capName}`);
      }
      const result = cap.tick(primitive, sectorState, rng);
      for (const [key, value] of Object.entries(result)) {
        if (key in output) {
          output[key] += value;
        }
      }
    }
  }

  return output;
}

module.exports = { tick, createRng };
