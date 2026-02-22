"use strict";

// ---------------------------------------------------------------------------
// Planner Controller
// Decides how resources flow through the hub: intake → processing → storage → distribution.
// ---------------------------------------------------------------------------

class PlannerController {
  /**
   * @param {object} blueprint - Parsed blueprint.json
   */
  constructor(blueprint) {
    this.blueprint = blueprint;
    this.zones = new Map();
    this.connections = [];
    this._index(blueprint);
  }

  /** Build internal lookup structures from the blueprint. */
  _index(bp) {
    for (const zone of bp.layout.zones) {
      this.zones.set(zone.id, { ...zone, structuresById: new Map() });
      for (const s of zone.structures) {
        this.zones.get(zone.id).structuresById.set(s.id, s);
      }
    }
    this.connections = bp.layout.connections;
  }

  /**
   * Compute the optimal route for a given resource type from intake to distribution.
   * Returns an ordered list of structure IDs the resource should pass through.
   *
   * @param {string} resourceType - e.g. "raw-ore"
   * @returns {{ route: string[], throughput: number }}
   */
  planRoute(resourceType) {
    const route = [];
    let throughput = Infinity;

    // 1. Find an intake dock
    const intakeZone = this.zones.get("intake-zone");
    const dock = intakeZone
      ? [...intakeZone.structuresById.values()].find((s) => s.type === "dock")
      : null;
    if (!dock) return { route: [], throughput: 0 };
    route.push(dock.id);
    throughput = Math.min(throughput, dock.throughput);

    // 2. Find a conveyor from this dock into a refinery that accepts the resource
    const conveyor = intakeZone
      ? [...intakeZone.structuresById.values()].find(
          (s) => s.type === "conveyor" && s.from === dock.id
        )
      : null;
    if (conveyor) {
      route.push(conveyor.id);
      throughput = Math.min(throughput, conveyor.rate);
    }

    // 3. Find a refinery that accepts resourceType
    const processingZone = this.zones.get("processing-zone");
    const refinery = processingZone
      ? [...processingZone.structuresById.values()].find(
          (s) => s.type === "refinery" && s.inputTypes && s.inputTypes.includes(resourceType)
        )
      : null;
    if (refinery) {
      route.push(refinery.id);
    }

    // 4. Find appropriate storage silo
    const storageZone = this.zones.get("storage-zone");
    if (storageZone) {
      // Match the input resource index to the corresponding output type
      let outputType = resourceType;
      if (refinery) {
        const inputIdx = refinery.inputTypes.indexOf(resourceType);
        outputType =
          inputIdx >= 0 && inputIdx < refinery.outputTypes.length
            ? refinery.outputTypes[inputIdx]
            : refinery.outputTypes[0];
      }
      const silo = [...storageZone.structuresById.values()].find(
        (s) => (s.type === "silo" || s.type === "vault") && s.storedType === outputType
      );
      if (silo) route.push(silo.id);
    }

    // 5. Find an outbound dock
    const distZone = this.zones.get("distribution-zone");
    const outDock = distZone
      ? [...distZone.structuresById.values()].find((s) => s.type === "dock")
      : null;
    if (outDock) {
      route.push(outDock.id);
      throughput = Math.min(throughput, outDock.throughput);
    }

    // Clamp throughput by pipeline connections
    for (const conn of this.connections) {
      throughput = Math.min(throughput, conn.bandwidth);
    }

    return { route, throughput };
  }

  /**
   * Return total storage capacity across all silos and vaults.
   * @returns {number}
   */
  totalStorageCapacity() {
    const storageZone = this.zones.get("storage-zone");
    if (!storageZone) return 0;
    let total = 0;
    for (const s of storageZone.structuresById.values()) {
      if (s.maxUnits) total += s.maxUnits;
    }
    return total;
  }
}

// ---------------------------------------------------------------------------
// Structure Controller
// Manages the lifecycle of structures: build, operate, upgrade, decommission.
// ---------------------------------------------------------------------------

const StructureState = Object.freeze({
  PLANNED: "planned",
  BUILDING: "building",
  OPERATIONAL: "operational",
  UPGRADING: "upgrading",
  DECOMMISSIONED: "decommissioned",
});

class StructureController {
  constructor() {
    /** @type {Map<string, { state: string, tier: number, ticksRemaining: number }>} */
    this.structures = new Map();
  }

  /**
   * Register a structure in PLANNED state.
   * @param {string} id
   * @param {number} tier
   */
  register(id, tier = 1) {
    if (this.structures.has(id)) {
      throw new Error(`Structure ${id} already registered`);
    }
    this.structures.set(id, {
      state: StructureState.PLANNED,
      tier,
      ticksRemaining: 0,
    });
  }

  /**
   * Start building a planned structure. Takes `ticks` simulation ticks to complete.
   * @param {string} id
   * @param {number} ticks
   */
  startBuild(id, ticks) {
    const s = this._get(id);
    if (s.state !== StructureState.PLANNED) {
      throw new Error(`Cannot build ${id}: current state is ${s.state}`);
    }
    s.state = StructureState.BUILDING;
    s.ticksRemaining = ticks;
  }

  /**
   * Begin an upgrade cycle. The structure goes offline during upgrade.
   * @param {string} id
   * @param {number} ticks
   */
  startUpgrade(id, ticks) {
    const s = this._get(id);
    if (s.state !== StructureState.OPERATIONAL) {
      throw new Error(`Cannot upgrade ${id}: current state is ${s.state}`);
    }
    s.state = StructureState.UPGRADING;
    s.ticksRemaining = ticks;
  }

  /**
   * Decommission a structure, removing it from active service.
   * @param {string} id
   */
  decommission(id) {
    const s = this._get(id);
    s.state = StructureState.DECOMMISSIONED;
    s.ticksRemaining = 0;
  }

  /**
   * Advance simulation by one tick. Structures in BUILDING or UPGRADING
   * transition to OPERATIONAL when their countdown reaches zero.
   */
  tick() {
    for (const [, s] of this.structures) {
      if (
        s.state === StructureState.BUILDING ||
        s.state === StructureState.UPGRADING
      ) {
        s.ticksRemaining = Math.max(0, s.ticksRemaining - 1);
        if (s.ticksRemaining === 0) {
          if (s.state === StructureState.UPGRADING) s.tier += 1;
          s.state = StructureState.OPERATIONAL;
        }
      }
    }
  }

  /**
   * Return the current state snapshot for a structure.
   * @param {string} id
   */
  getState(id) {
    return { ...this._get(id) };
  }

  /** @private */
  _get(id) {
    const s = this.structures.get(id);
    if (!s) throw new Error(`Unknown structure: ${id}`);
    return s;
  }
}

// ---------------------------------------------------------------------------
// Swarm Controller
// Manages drone dispatch, collection runs, and return-to-hub cycles.
// ---------------------------------------------------------------------------

class SwarmController {
  /**
   * @param {object} swarmConfig - The `swarm` section of the blueprint.
   */
  constructor(swarmConfig) {
    this.config = swarmConfig;
    this.spec = swarmConfig.droneSpec;
    /** @type {Map<string, { cargo: number, position: {x:number,y:number,z:number}, state: string, routeId: string|null }>} */
    this.drones = new Map();
    this._nextDroneId = 0;
  }

  /**
   * Spawn a drone at the hub origin.
   * @returns {string} droneId
   */
  spawnDrone() {
    if (this.drones.size >= this.config.maxDrones) {
      throw new Error("Drone pool at capacity");
    }
    const id = `drone-${this._nextDroneId++}`;
    this.drones.set(id, {
      cargo: 0,
      position: { x: 0, y: 0, z: 0 },
      state: "idle",
      routeId: null,
    });
    return id;
  }

  /**
   * Dispatch a drone along a named patrol route.
   * @param {string} droneId
   * @param {string} routeId
   */
  dispatch(droneId, routeId) {
    const drone = this._getDrone(droneId);
    const route = this.config.patrolRoutes.find((r) => r.id === routeId);
    if (!route) throw new Error(`Unknown route: ${routeId}`);
    if (drone.state !== "idle") {
      throw new Error(`Drone ${droneId} is not idle (state: ${drone.state})`);
    }
    drone.state = "collecting";
    drone.routeId = routeId;
    // Move to first waypoint
    const wp = route.waypoints[0];
    drone.position = { ...wp };
  }

  /**
   * Simulate the drone collecting resources. Adds `amount` cargo (clamped to capacity).
   * @param {string} droneId
   * @param {number} amount
   * @returns {number} actual amount collected
   */
  collect(droneId, amount) {
    const drone = this._getDrone(droneId);
    if (drone.state !== "collecting") {
      throw new Error(`Drone ${droneId} is not collecting`);
    }
    const space = this.spec.cargoCapacity - drone.cargo;
    const actual = Math.min(amount, space);
    drone.cargo += actual;

    // Auto-return when cargo ratio exceeds returnThreshold relative to capacity
    if (drone.cargo / this.spec.cargoCapacity >= 1 - this.spec.returnThreshold) {
      drone.state = "returning";
    }
    return actual;
  }

  /**
   * Return drone to hub, offload cargo, and set to idle.
   * @param {string} droneId
   * @returns {number} cargo offloaded
   */
  returnToHub(droneId) {
    const drone = this._getDrone(droneId);
    if (drone.state !== "returning" && drone.state !== "collecting") {
      throw new Error(`Drone ${droneId} cannot return (state: ${drone.state})`);
    }
    const offloaded = drone.cargo;
    drone.cargo = 0;
    drone.position = { x: 0, y: 0, z: 0 };
    drone.state = "idle";
    drone.routeId = null;
    return offloaded;
  }

  /**
   * Get snapshot of a drone's status.
   * @param {string} droneId
   */
  getDroneStatus(droneId) {
    return { ...this._getDrone(droneId) };
  }

  /**
   * Return how many drones are currently idle.
   * @returns {number}
   */
  idleCount() {
    let count = 0;
    for (const [, d] of this.drones) {
      if (d.state === "idle") count++;
    }
    return count;
  }

  /** @private */
  _getDrone(id) {
    const d = this.drones.get(id);
    if (!d) throw new Error(`Unknown drone: ${id}`);
    return d;
  }
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------
module.exports = {
  PlannerController,
  StructureController,
  StructureState,
  SwarmController,
};
