# Neon Light Strip Primitive Spec

## Goal
Add a new primitive called `neon_light_strip_v2` for decorative and directional lighting.

## Requirements
- Category: `ENTITY`
- Capabilities:
  - `AESTHETIC`
  - `LIGHTING`
  - `WAYFINDING`
- Render requirements:
  - bright emissive strip fallback render
  - configurable color palette and glow intensity metadata
- Sim requirements:
  - zero power generation
  - low power consumption
  - contributes to local visibility score used by drone traffic heuristics
- Constraints:
  - must attach to existing block or module face
  - maximum contiguous strip length of 32 segments

## Validation requirements
- schema validation passes
- deterministic sim contract test verifies no non-deterministic output across seeds
- render fallback smoke test confirms unknown renderer gracefully displays as emissive strip
- no meaningful per-tick perf regression in smoke benchmark

## Rollout
Default target rollout: `EXPERIMENTAL`.
