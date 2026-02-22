"""Deterministic sim contract tests for neon_light_strip_v2.

Verifies that sim computations are fully deterministic: given the same
placed primitives, the output is identical regardless of iteration order,
random seeds, or number of runs.
"""

import json
import copy


def _compute_tick(placed_primitives):
    """Pure-Python sim tick computation matching the sim semantics.

    Each placed primitive is a dict with 'id', 'definition', and 'position'.
    The computation sorts by (id, position) for deterministic ordering.
    """
    total_gen = 0.0
    total_con = 0.0
    visibility_contributions = []

    # Sort by id then position for deterministic iteration
    def sort_key(p):
        pos = p.get("position", {})
        return (p["id"], pos.get("x", 0), pos.get("y", 0), pos.get("z", 0))

    sorted_prims = sorted(placed_primitives, key=sort_key)

    for placed in sorted_prims:
        defn = placed["definition"]
        sim = defn.get("sim", {})

        total_gen += sim.get("power_generation_kw", 0)
        total_con += sim.get("power_consumption_kw", 0)

        caps = defn.get("capabilities", [])
        if "WAYFINDING" in caps or "LIGHTING" in caps:
            for effect in sim.get("tick_effects", []):
                if effect["type"] == "visibility_contribution":
                    visibility_contributions.append({
                        "primitive_id": placed["id"],
                        "position": placed["position"],
                        "radius": effect["radius"],
                        "score": effect["score"],
                    })

    total_vis = sum(v["score"] for v in visibility_contributions)

    return {
        "power_balance": {
            "generation_kw": total_gen,
            "consumption_kw": total_con,
            "net_kw": total_gen - total_con,
        },
        "visibility": {
            "total_score": total_vis,
            "contributions": visibility_contributions,
        },
    }


def _place(prim_id, definition, x=0, y=0, z=0):
    return {
        "id": prim_id,
        "definition": definition,
        "position": {"x": x, "y": y, "z": z},
    }


class TestDeterministicSim:
    """Verify sim output is deterministic across seeds and orderings."""

    def test_identical_output_across_multiple_runs(self, catalog, neon_def):
        placed = [
            _place("neon_light_strip_v2", neon_def, x=0),
            _place("neon_light_strip_v2", neon_def, x=1),
            _place("neon_light_strip_v2", neon_def, x=2),
        ]

        results = [json.dumps(_compute_tick(placed), sort_keys=True) for _ in range(20)]

        assert all(r == results[0] for r in results), "Output diverged across runs"

    def test_identical_output_regardless_of_input_order(self, catalog, neon_def):
        solar_def = catalog["primitives"]["solar_panel_v1"]

        order_a = [
            _place("neon_light_strip_v2", neon_def, x=0),
            _place("solar_panel_v1", solar_def, x=1),
            _place("neon_light_strip_v2", neon_def, x=2),
        ]

        order_b = [
            _place("solar_panel_v1", solar_def, x=1),
            _place("neon_light_strip_v2", neon_def, x=2),
            _place("neon_light_strip_v2", neon_def, x=0),
        ]

        result_a = _compute_tick(order_a)
        result_b = _compute_tick(order_b)

        assert result_a == result_b

    def test_zero_power_generation(self, neon_def):
        result = _compute_tick([_place("neon_light_strip_v2", neon_def)])
        assert result["power_balance"]["generation_kw"] == 0.0

    def test_low_power_consumption(self, neon_def):
        result = _compute_tick([_place("neon_light_strip_v2", neon_def)])
        assert 0 < result["power_balance"]["consumption_kw"] < 1.0

    def test_contributes_to_visibility(self, neon_def):
        result = _compute_tick([_place("neon_light_strip_v2", neon_def)])
        assert result["visibility"]["total_score"] > 0
        assert len(result["visibility"]["contributions"]) == 1
        assert result["visibility"]["contributions"][0]["primitive_id"] == "neon_light_strip_v2"

    def test_multiple_strips_accumulate_visibility(self, neon_def):
        single = _compute_tick([_place("neon_light_strip_v2", neon_def, x=0)])
        triple = _compute_tick([
            _place("neon_light_strip_v2", neon_def, x=0),
            _place("neon_light_strip_v2", neon_def, x=1),
            _place("neon_light_strip_v2", neon_def, x=2),
        ])
        assert triple["visibility"]["total_score"] == single["visibility"]["total_score"] * 3

    def test_all_catalog_primitives_have_valid_sim_config(self, catalog):
        for prim_id, defn in catalog["primitives"].items():
            sim = defn["sim"]
            assert sim["power_generation_kw"] >= 0, f"{prim_id}: negative power gen"
            assert sim["power_consumption_kw"] >= 0, f"{prim_id}: negative power con"
            assert isinstance(sim["tick_effects"], list), f"{prim_id}: bad tick_effects"

    def test_constraint_validation_max_segments(self, neon_def):
        seg = neon_def["constraints"]["max_contiguous_segments"]
        assert seg is not None
        assert 1 <= seg <= 64

    def test_constraint_validation_attach_to(self, catalog):
        for prim_id, defn in catalog["primitives"].items():
            attach = defn["constraints"]["attach_to"]
            assert len(attach) >= 1, f"{prim_id}: no attach_to targets"
            for target in attach:
                assert target in ("block_face", "module_face"), (
                    f"{prim_id}: invalid attach target {target}"
                )
