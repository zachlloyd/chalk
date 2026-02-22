# World of Warp

Sector simulation platform for the World of Warp universe.

## Structure

- `services/sector-sim/` – core sector simulation service
  - `data/catalog.json` – primitive definitions catalog
  - `sim/` – simulation semantics (capabilities, tick logic)
  - `render/` – render metadata and asset descriptors
- `tests/` – validation, smoke, and benchmark tests
- `primitives/` – primitive specs and backlog

## Testing

```bash
# Run all tests
./run_tests.sh

# Schema validation only
./run_tests.sh schema

# Sim smoke tests
./run_tests.sh sim

# Render smoke tests
./run_tests.sh render
```
