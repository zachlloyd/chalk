# World of Warp

Sector simulation and rendering primitives.

## Structure

- `services/sector-sim/` — Simulation engine (power, visibility, etc.)
- `services/render-engine/` — Render fallback resolver and asset registry
- `schemas/` — JSON Schema definitions for data validation
- `tests/` — Schema, sim, render, and perf tests

## Running Tests

```bash
pip install pytest jsonschema
pytest tests/ -v
```
