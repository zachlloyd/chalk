# World of Warp

Server-side simulation and rendering primitives for the World of Warp platform.

## Structure

- `schemas/` — JSON Schema definitions for primitives
- `services/sector-sim/` — Sector simulation service
  - `data/catalog.json` — Primitive catalog
  - `sim/` — Simulation tick-effect handlers
  - `render/` — Render fallback and metadata resolvers
  - `tests/` — Test suite

## Running tests

```bash
pip install pytest jsonschema
pytest services/sector-sim/tests/ -v
```
