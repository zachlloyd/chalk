"use strict";

const Ajv = require("ajv");
const catalog = require("../services/sector-sim/data/catalog.json");
const schema = require("../services/sector-sim/data/schema.json");

const ajv = new Ajv({ allErrors: true });
const validate = ajv.compile(schema);

describe("catalog schema validation", () => {
  test("entire catalog validates against schema", () => {
    const valid = validate(catalog);
    if (!valid) {
      // Pretty-print errors for debugging
      const msgs = validate.errors.map(
        (e) => `${e.instancePath} ${e.message}`
      );
      throw new Error(`Schema validation failed:\n${msgs.join("\n")}`);
    }
    expect(valid).toBe(true);
  });

  test("every primitive key matches its id field", () => {
    for (const [key, prim] of Object.entries(catalog.primitives)) {
      expect(prim.id).toBe(key);
    }
  });

  test("neon_light_strip_v2 has required capabilities", () => {
    const neon = catalog.primitives.neon_light_strip_v2;
    expect(neon).toBeDefined();
    expect(neon.capabilities).toContain("AESTHETIC");
    expect(neon.capabilities).toContain("LIGHTING");
    expect(neon.capabilities).toContain("WAYFINDING");
  });

  test("neon_light_strip_v2 is category ENTITY", () => {
    expect(catalog.primitives.neon_light_strip_v2.category).toBe("ENTITY");
  });

  test("neon_light_strip_v2 rollout is EXPERIMENTAL", () => {
    expect(catalog.primitives.neon_light_strip_v2.rollout).toBe("EXPERIMENTAL");
  });

  test("neon_light_strip_v2 constraints are correct", () => {
    const c = catalog.primitives.neon_light_strip_v2.constraints;
    expect(c.attach_to).toBe("BLOCK_OR_MODULE_FACE");
    expect(c.max_contiguous).toBe(32);
  });

  test("neon_light_strip_v2 has zero power generation", () => {
    expect(catalog.primitives.neon_light_strip_v2.sim.power_generation).toBe(0);
  });

  test("neon_light_strip_v2 has low power consumption", () => {
    const consumption = catalog.primitives.neon_light_strip_v2.sim.power_consumption;
    expect(consumption).toBeGreaterThan(0);
    expect(consumption).toBeLessThan(5); // "low" threshold
  });

  test("rejects catalog entry with invalid category", () => {
    const badCatalog = JSON.parse(JSON.stringify(catalog));
    badCatalog.primitives.neon_light_strip_v2.category = "INVALID";
    expect(validate(badCatalog)).toBe(false);
  });

  test("rejects catalog entry with missing required field", () => {
    const badCatalog = JSON.parse(JSON.stringify(catalog));
    delete badCatalog.primitives.neon_light_strip_v2.sim;
    expect(validate(badCatalog)).toBe(false);
  });
});
