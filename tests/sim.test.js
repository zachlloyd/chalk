"use strict";

const fs = require("fs");
const path = require("path");
const {
  PlannerController,
  StructureController,
  StructureState,
  SwarmController,
} = require("../controllers");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const blueprintPath = path.resolve(__dirname, "..", "blueprint.json");
const blueprint = JSON.parse(fs.readFileSync(blueprintPath, "utf-8"));

let passed = 0;
let failed = 0;
const failures = [];

function assert(condition, label) {
  if (condition) {
    passed++;
  } else {
    failed++;
    failures.push(label);
    console.error(`  FAIL: ${label}`);
  }
}

function assertEqual(actual, expected, label) {
  if (actual === expected) {
    passed++;
  } else {
    failed++;
    failures.push(`${label} (expected ${expected}, got ${actual})`);
    console.error(`  FAIL: ${label} — expected ${expected}, got ${actual}`);
  }
}

function assertDeepEqual(actual, expected, label) {
  const a = JSON.stringify(actual);
  const b = JSON.stringify(expected);
  if (a === b) {
    passed++;
  } else {
    failed++;
    failures.push(`${label}`);
    console.error(`  FAIL: ${label}\n    expected: ${b}\n    actual:   ${a}`);
  }
}

function assertThrows(fn, label) {
  try {
    fn();
    failed++;
    failures.push(`${label} (expected error, none thrown)`);
    console.error(`  FAIL: ${label} — expected error, none thrown`);
  } catch (_) {
    passed++;
  }
}

// ===================================================================
// SECTION 1: Blueprint Integrity
// ===================================================================
console.log("\n=== Blueprint Integrity ===");

assert(blueprint.id === "refinery-hub-alpha", "blueprint id");
assert(blueprint.anchor === "sector-1-anchor-1", "blueprint anchor matches sector-1-anchor-1");
assert(blueprint.version === "1.0.0", "blueprint version");
assert(blueprint.metadata.anchorRef === "sector-1-anchor-1", "metadata anchorRef");
assert(blueprint.metadata.sector === "sector-1", "metadata sector");

// Layout zones
assertEqual(blueprint.layout.zones.length, 4, "four layout zones");
const zoneIds = blueprint.layout.zones.map((z) => z.id);
assert(zoneIds.includes("intake-zone"), "has intake-zone");
assert(zoneIds.includes("processing-zone"), "has processing-zone");
assert(zoneIds.includes("storage-zone"), "has storage-zone");
assert(zoneIds.includes("distribution-zone"), "has distribution-zone");

// All structure IDs are unique
const allStructIds = blueprint.layout.zones.flatMap((z) =>
  z.structures.map((s) => s.id)
);
assertEqual(
  new Set(allStructIds).size,
  allStructIds.length,
  "all structure IDs unique"
);

// Connections form a valid pipeline chain
const connFrom = blueprint.layout.connections.map((c) => c.from);
const connTo = blueprint.layout.connections.map((c) => c.to);
assert(connFrom.includes("intake-zone"), "connection from intake-zone");
assert(connTo.includes("distribution-zone"), "connection to distribution-zone");

// Bounds encapsulate all zone positions
const bounds = blueprint.layout.bounds;
for (const zone of blueprint.layout.zones) {
  assert(
    zone.position.x + zone.size.width <= bounds.width,
    `zone ${zone.id} fits within bounds width`
  );
  assert(
    zone.position.y + zone.size.height <= bounds.height,
    `zone ${zone.id} fits within bounds height`
  );
}

// Swarm config
assertEqual(blueprint.swarm.maxDrones, 12, "swarm maxDrones");
assertEqual(blueprint.swarm.droneSpec.cargoCapacity, 50, "drone cargoCapacity");
assertEqual(blueprint.swarm.patrolRoutes.length, 2, "two patrol routes");

// ===================================================================
// SECTION 2: Planner Controller
// ===================================================================
console.log("\n=== Planner Controller ===");

const planner = new PlannerController(blueprint);

// Route for raw-ore
const oreRoute = planner.planRoute("raw-ore");
assert(oreRoute.route.length >= 4, "raw-ore route has ≥4 hops");
assert(oreRoute.route[0] === "intake-dock-1", "raw-ore route starts at intake dock");
assert(oreRoute.route.includes("refinery-primary"), "raw-ore route includes refinery-primary");
assert(oreRoute.route.includes("silo-refined"), "raw-ore route includes silo-refined");
assert(oreRoute.throughput > 0, "raw-ore throughput > 0");
assertEqual(oreRoute.throughput, 80, "raw-ore throughput clamped to conveyor rate 80");

// Route for crystal-shard
const crystalRoute = planner.planRoute("crystal-shard");
assert(crystalRoute.route.includes("refinery-primary"), "crystal-shard route uses refinery-primary");
// crystal-dust goes to vault-crystal
assert(crystalRoute.route.includes("vault-crystal"), "crystal-shard route stores in vault-crystal");

// Total storage capacity = 800 + 600 + 400 + 200
assertEqual(planner.totalStorageCapacity(), 2000, "total storage capacity 2000");

// ===================================================================
// SECTION 3: Structure Controller
// ===================================================================
console.log("\n=== Structure Controller ===");

const structs = new StructureController();

// Register & build
structs.register("refinery-primary", 2);
assertEqual(structs.getState("refinery-primary").state, StructureState.PLANNED, "initial state is planned");
assertEqual(structs.getState("refinery-primary").tier, 2, "initial tier is 2");

structs.startBuild("refinery-primary", 3);
assertEqual(structs.getState("refinery-primary").state, StructureState.BUILDING, "state is building");
assertEqual(structs.getState("refinery-primary").ticksRemaining, 3, "3 ticks remaining");

// Tick through build
structs.tick();
assertEqual(structs.getState("refinery-primary").ticksRemaining, 2, "2 ticks remaining");
structs.tick();
structs.tick();
assertEqual(structs.getState("refinery-primary").state, StructureState.OPERATIONAL, "operational after 3 ticks");
assertEqual(structs.getState("refinery-primary").ticksRemaining, 0, "0 ticks remaining");

// Upgrade
structs.startUpgrade("refinery-primary", 2);
assertEqual(structs.getState("refinery-primary").state, StructureState.UPGRADING, "state is upgrading");
structs.tick();
structs.tick();
assertEqual(structs.getState("refinery-primary").state, StructureState.OPERATIONAL, "operational after upgrade");
assertEqual(structs.getState("refinery-primary").tier, 3, "tier bumped to 3 after upgrade");

// Decommission
structs.decommission("refinery-primary");
assertEqual(structs.getState("refinery-primary").state, StructureState.DECOMMISSIONED, "state is decommissioned");

// Error paths
assertThrows(() => structs.register("refinery-primary"), "duplicate register throws");
assertThrows(() => structs.startBuild("refinery-primary", 1), "build on decommissioned throws");
assertThrows(() => structs._get("nonexistent"), "unknown structure throws");

// ===================================================================
// SECTION 4: Swarm Controller
// ===================================================================
console.log("\n=== Swarm Controller ===");

const swarm = new SwarmController(blueprint.swarm);

// Spawn drones
const d1 = swarm.spawnDrone();
const d2 = swarm.spawnDrone();
assertEqual(d1, "drone-0", "first drone id");
assertEqual(d2, "drone-1", "second drone id");
assertEqual(swarm.idleCount(), 2, "2 idle drones");

// Dispatch
swarm.dispatch(d1, "route-intake-sweep");
const status1 = swarm.getDroneStatus(d1);
assertEqual(status1.state, "collecting", "drone-0 collecting");
assertEqual(status1.routeId, "route-intake-sweep", "drone-0 on correct route");
assertDeepEqual(status1.position, { x: -50, y: 0, z: 0 }, "drone-0 at first waypoint");
assertEqual(swarm.idleCount(), 1, "1 idle after dispatch");

// Collect partial
const collected1 = swarm.collect(d1, 20);
assertEqual(collected1, 20, "collected 20 units");
assertEqual(swarm.getDroneStatus(d1).cargo, 20, "cargo is 20");
assertEqual(swarm.getDroneStatus(d1).state, "collecting", "still collecting (under threshold)");

// Collect to capacity (threshold 0.1 → auto-return at ≥ 45 cargo)
const collected2 = swarm.collect(d1, 30);
assertEqual(collected2, 30, "collected 30 more units");
assertEqual(swarm.getDroneStatus(d1).cargo, 50, "cargo is 50 (full)");
assertEqual(swarm.getDroneStatus(d1).state, "returning", "auto-return triggered at capacity");

// Return to hub
const offloaded = swarm.returnToHub(d1);
assertEqual(offloaded, 50, "offloaded 50 units");
assertEqual(swarm.getDroneStatus(d1).state, "idle", "drone-0 idle after return");
assertDeepEqual(swarm.getDroneStatus(d1).position, { x: 0, y: 0, z: 0 }, "drone-0 back at origin");

// Error paths
assertThrows(() => swarm.dispatch(d1, "nonexistent-route"), "dispatch to unknown route throws");
assertThrows(() => swarm.collect(d1, 10), "collect on idle drone throws");
assertThrows(() => swarm._getDrone("fake"), "unknown drone throws");

// Capacity enforcement
for (let i = swarm.drones.size; i < blueprint.swarm.maxDrones; i++) {
  swarm.spawnDrone();
}
assertThrows(() => swarm.spawnDrone(), "exceeding maxDrones throws");

// ===================================================================
// SECTION 5: Integration — Full Pipeline Sim
// ===================================================================
console.log("\n=== Integration: Full Pipeline Sim ===");

// Build all refineries, run swarm collection, verify end-to-end flow
const integ = new StructureController();
const processingStructures = blueprint.layout.zones
  .find((z) => z.id === "processing-zone")
  .structures;

for (const s of processingStructures) {
  integ.register(s.id, s.tier);
  integ.startBuild(s.id, s.processingTime);
}

// Tick until all operational
let maxTicks = 20;
while (maxTicks-- > 0) {
  const states = processingStructures.map((s) => integ.getState(s.id).state);
  if (states.every((st) => st === StructureState.OPERATIONAL)) break;
  integ.tick();
}

for (const s of processingStructures) {
  assertEqual(
    integ.getState(s.id).state,
    StructureState.OPERATIONAL,
    `${s.id} operational after build`
  );
}

// Swarm run: spawn, dispatch, collect full, return
const intSwarm = new SwarmController(blueprint.swarm);
const drone = intSwarm.spawnDrone();
intSwarm.dispatch(drone, "route-intake-sweep");
intSwarm.collect(drone, 50);
assertEqual(intSwarm.getDroneStatus(drone).state, "returning", "integration drone returning");
const intOffload = intSwarm.returnToHub(drone);
assertEqual(intOffload, 50, "integration offload 50");

// Planner route validates the processing chain exists
const intRoute = planner.planRoute("raw-ore");
assert(intRoute.route.length >= 4, "integration route has ≥4 hops");
assert(intRoute.throughput > 0, "integration throughput positive");

// ===================================================================
// Summary
// ===================================================================
console.log(`\n========================================`);
console.log(`  Results: ${passed} passed, ${failed} failed`);
console.log(`========================================`);
if (failures.length > 0) {
  console.log("\nFailures:");
  for (const f of failures) {
    console.log(`  - ${f}`);
  }
  process.exit(1);
} else {
  console.log("\nAll tests passed.");
  process.exit(0);
}
