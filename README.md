# World of Warp

Sector simulation and rendering engine for the World of Warp platform.

## Structure

- `services/sector-sim/data/` — Primitive catalog definitions
- `services/sector-sim/sim/` — Simulation semantics and tick logic
- `services/sector-sim/render/` — Render metadata and fallback definitions
- `services/sector-sim/schemas/` — JSON Schema for data validation
- `services/sector-sim/tests/` — Schema validation, sim, and render smoke tests
- `primitives/backlog/` — Primitive specification documents

## Testing

```bash
python3 -m pytest services/sector-sim/tests/ -v
```
