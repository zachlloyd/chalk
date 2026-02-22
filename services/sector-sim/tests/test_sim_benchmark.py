"""Sim benchmark smoke test.

Ensures that adding neon_light_strip_v2 primitives does not cause
meaningful per-tick performance regression.
"""

import time
from test_sim_deterministic import _compute_tick, _place


MAX_AVG_TICK_MS = 5.0
TICK_COUNT = 100
PRIMITIVE_COUNT = 500


class TestSimBenchmark:
    """Smoke benchmark: no meaningful per-tick regression."""

    def test_mixed_sector_within_tick_budget(self, catalog):
        """Compute TICK_COUNT ticks of PRIMITIVE_COUNT mixed primitives within budget."""
        all_ids = list(catalog["primitives"].keys())
        all_defs = list(catalog["primitives"].values())

        placed = []
        for i in range(PRIMITIVE_COUNT):
            idx = i % len(all_ids)
            placed.append(_place(
                all_ids[idx],
                all_defs[idx],
                x=i % 50,
                y=i // 50,
            ))

        start = time.perf_counter()
        for _ in range(TICK_COUNT):
            _compute_tick(placed)
        elapsed_s = time.perf_counter() - start

        avg_ms = (elapsed_s / TICK_COUNT) * 1000
        assert avg_ms < MAX_AVG_TICK_MS, (
            f"Average tick {avg_ms:.3f}ms exceeds ceiling {MAX_AVG_TICK_MS}ms"
        )

    def test_neon_heavy_sector_no_regression_vs_baseline(self, catalog):
        """Neon-heavy sector should not be meaningfully slower than baseline."""
        solar_def = catalog["primitives"]["solar_panel_v1"]
        neon_def = catalog["primitives"]["neon_light_strip_v2"]

        count = 200
        ticks = 50

        baseline = [_place("solar_panel_v1", solar_def, x=i) for i in range(count)]
        neon_sector = [_place("neon_light_strip_v2", neon_def, x=i) for i in range(count)]

        # Warm up
        _compute_tick(baseline)
        _compute_tick(neon_sector)

        start = time.perf_counter()
        for _ in range(ticks):
            _compute_tick(baseline)
        base_elapsed = time.perf_counter() - start

        start = time.perf_counter()
        for _ in range(ticks):
            _compute_tick(neon_sector)
        neon_elapsed = time.perf_counter() - start

        # Allow up to 3x overhead (generous for smoke test)
        ratio = neon_elapsed / base_elapsed if base_elapsed > 0 else 1.0
        assert ratio < 3.0, (
            f"Neon sector is {ratio:.2f}x slower than baseline (max 3x)"
        )
