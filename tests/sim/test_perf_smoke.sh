#!/usr/bin/env bash
# Per-tick performance smoke benchmark
# Ensures the addition of neon_light_strip_v2 does not introduce meaningful
# per-tick perf regression. Measures jq processing time as a proxy for
# catalog/sim data complexity.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CATALOG="$REPO_ROOT/services/sector-sim/data/catalog.json"
TICK_CONTRACT="$REPO_ROOT/services/sector-sim/sim/tick_contract.json"
RENDER_META="$REPO_ROOT/services/sector-sim/render/render_metadata.json"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }

echo "=== Per-Tick Performance Smoke Test ==="

# Measure time to process full catalog (simulates per-tick data access)
# Threshold: must complete 100 iterations in under 5 seconds
echo ""
echo "-- Catalog access benchmark (100 iterations) --"

start_time=$(date +%s%N)
for i in $(seq 1 100); do
  jq -r '.primitives | keys[]' "$CATALOG" > /dev/null 2>&1
done
end_time=$(date +%s%N)
elapsed_ms=$(( (end_time - start_time) / 1000000 ))

echo "  Elapsed: ${elapsed_ms}ms for 100 catalog reads"
[ "$elapsed_ms" -lt 5000 ] \
  && pass "catalog read benchmark within 5s threshold (${elapsed_ms}ms)" \
  || fail "catalog read benchmark exceeded 5s threshold (${elapsed_ms}ms)"

# Measure time to resolve all tick rules
echo ""
echo "-- Tick rule resolution benchmark (100 iterations) --"

start_time=$(date +%s%N)
for i in $(seq 1 100); do
  jq -r '.tick_rules | to_entries[] | .key' "$TICK_CONTRACT" > /dev/null 2>&1
done
end_time=$(date +%s%N)
elapsed_ms=$(( (end_time - start_time) / 1000000 ))

echo "  Elapsed: ${elapsed_ms}ms for 100 tick rule reads"
[ "$elapsed_ms" -lt 5000 ] \
  && pass "tick rule benchmark within 5s threshold (${elapsed_ms}ms)" \
  || fail "tick rule benchmark exceeded 5s threshold (${elapsed_ms}ms)"

# Measure time to resolve render fallback chain
echo ""
echo "-- Render fallback resolution benchmark (100 iterations) --"

start_time=$(date +%s%N)
for i in $(seq 1 100); do
  for prim in $(jq -r '.primitives | keys[]' "$CATALOG"); do
    fb=$(jq -r ".primitives[\"$prim\"].render.fallback" "$CATALOG")
    jq -e ".fallback_registry[\"$fb\"]" "$RENDER_META" > /dev/null 2>&1
  done
done
end_time=$(date +%s%N)
elapsed_ms=$(( (end_time - start_time) / 1000000 ))

echo "  Elapsed: ${elapsed_ms}ms for 100 full render fallback resolutions"
[ "$elapsed_ms" -lt 30000 ] \
  && pass "render fallback benchmark within 30s threshold (${elapsed_ms}ms)" \
  || fail "render fallback benchmark exceeded 30s threshold (${elapsed_ms}ms)"

# Verify primitive count hasn't exploded (sanity check)
echo ""
echo "-- Primitive count sanity --"

prim_count=$(jq '.primitives | keys | length' "$CATALOG")
echo "  Primitive count: $prim_count"
[ "$prim_count" -le 20 ] \
  && pass "primitive count ($prim_count) is reasonable" \
  || fail "primitive count ($prim_count) seems too high"

# Summary
echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
