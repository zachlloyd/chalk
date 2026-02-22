"use strict";

/**
 * Capability definitions for sector-sim primitives.
 *
 * Each capability maps to a set of sim-tick hooks that the engine invokes
 * when processing primitives that declare that capability.
 */

const CAPABILITIES = {
  POWER_GENERATION: {
    description: "Generates power for the sector grid.",
    tick(primitive, _sectorState, _rng) {
      return { power_delta: primitive.sim.power_generation };
    },
  },

  HABITATION: {
    description: "Provides habitable space for crew.",
    tick(_primitive, _sectorState, _rng) {
      // Habitation has no per-tick numeric output; it gates crew placement.
      return {};
    },
  },

  LIGHTING: {
    description: "Emits light within the local area.",
    tick(primitive, _sectorState, _rng) {
      // Lighting contributes to ambient light level; no separate output key.
      return { light_level_delta: primitive.sim.power_consumption > 0 ? 1.0 : 0.0 };
    },
  },

  AESTHETIC: {
    description: "Provides a decorative or morale benefit.",
    tick(_primitive, _sectorState, _rng) {
      return { morale_delta: 0.1 };
    },
  },

  WAYFINDING: {
    description:
      "Contributes to local visibility score used by drone traffic heuristics.",
    tick(primitive, _sectorState, _rng) {
      return { visibility_score_delta: primitive.sim.visibility_score };
    },
  },

  STORAGE: {
    description: "Provides inventory storage capacity.",
    tick(_primitive, _sectorState, _rng) {
      return {};
    },
  },

  TRANSPORT: {
    description: "Enables movement of entities between sectors.",
    tick(_primitive, _sectorState, _rng) {
      return {};
    },
  },
};

module.exports = { CAPABILITIES };
