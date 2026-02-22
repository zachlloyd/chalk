#!/usr/bin/env bash
# Schema validation tests for catalog.json
# Validates structure, required fields, enums, and constraints for all primitives.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CATALOG="$REPO_ROOT/services/sector-sim/data/catalog.json"
SCHEMA="$REPO_ROOT/services/sector-sim/data/catalog_schema.json"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }

echo "=== Catalog Schema Validation Tests ==="

# --- Basic structure ---
echo ""
echo "-- Basic structure --"

jq -e '.version' "$CATALOG" > /dev/null 2>&1 && pass "has version field" || fail "missing version field"
jq -e '.primitives | keys | length > 0' "$CATALOG" > /dev/null 2>&1 && pass "has at least one primitive" || fail "no primitives defined"
jq -e '.version | test("^[0-9]+\\.[0-9]+\\.[0-9]+$")' "$CATALOG" > /dev/null 2>&1 && pass "version is semver" || fail "version is not semver"

# --- Valid enums from schema ---
VALID_CATEGORIES=$(jq -r '.definitions.primitive.properties.category.enum[]' "$SCHEMA")
VALID_CAPABILITIES=$(jq -r '.definitions.primitive.properties.capabilities.items.enum[]' "$SCHEMA")
VALID_ROLLOUTS=$(jq -r '.definitions.primitive.properties.rollout.enum[]' "$SCHEMA")
VALID_ATTACH=$(jq -r '.definitions.primitive.properties.constraints.properties.attach_to.items.enum[]' "$SCHEMA")

# --- Per-primitive validation ---
for prim in $(jq -r '.primitives | keys[]' "$CATALOG"); do
  echo ""
  echo "-- Primitive: $prim --"

  # Required fields
  for field in category capabilities rollout constraints sim render; do
    jq -e ".primitives[\"$prim\"].$field" "$CATALOG" > /dev/null 2>&1 \
      && pass "$prim has $field" \
      || fail "$prim missing $field"
  done

  # Category enum
  cat_val=$(jq -r ".primitives[\"$prim\"].category" "$CATALOG")
  echo "$VALID_CATEGORIES" | grep -qx "$cat_val" \
    && pass "$prim category '$cat_val' is valid" \
    || fail "$prim category '$cat_val' is not in schema enum"

  # Capabilities enum
  caps=$(jq -r ".primitives[\"$prim\"].capabilities[]" "$CATALOG")
  all_caps_valid=true
  for cap in $caps; do
    if ! echo "$VALID_CAPABILITIES" | grep -qx "$cap"; then
      fail "$prim capability '$cap' is not in schema enum"
      all_caps_valid=false
    fi
  done
  $all_caps_valid && pass "$prim all capabilities are valid"

  # Unique capabilities
  cap_count=$(jq ".primitives[\"$prim\"].capabilities | length" "$CATALOG")
  unique_count=$(jq ".primitives[\"$prim\"].capabilities | unique | length" "$CATALOG")
  [ "$cap_count" = "$unique_count" ] \
    && pass "$prim capabilities are unique" \
    || fail "$prim has duplicate capabilities"

  # Rollout enum
  rollout_val=$(jq -r ".primitives[\"$prim\"].rollout" "$CATALOG")
  echo "$VALID_ROLLOUTS" | grep -qx "$rollout_val" \
    && pass "$prim rollout '$rollout_val' is valid" \
    || fail "$prim rollout '$rollout_val' is not in schema enum"

  # Constraints
  attach_vals=$(jq -r ".primitives[\"$prim\"].constraints.attach_to[]" "$CATALOG")
  all_attach_valid=true
  for att in $attach_vals; do
    if ! echo "$VALID_ATTACH" | grep -qx "$att"; then
      fail "$prim attach_to value '$att' is not in schema enum"
      all_attach_valid=false
    fi
  done
  $all_attach_valid && pass "$prim all attach_to values are valid"

  # max_contiguous_length: null or positive int
  mcl=$(jq ".primitives[\"$prim\"].constraints.max_contiguous_length" "$CATALOG")
  if [ "$mcl" = "null" ] || (echo "$mcl" | grep -qE '^[1-9][0-9]*$'); then
    pass "$prim max_contiguous_length ($mcl) is valid"
  else
    fail "$prim max_contiguous_length ($mcl) must be null or positive integer"
  fi

  # Sim fields
  for sim_field in power_generation_kw power_consumption_kw visibility_contribution; do
    val=$(jq ".primitives[\"$prim\"].sim.$sim_field" "$CATALOG")
    if [ "$val" != "null" ]; then
      is_non_negative=$(echo "$val >= 0" | bc -l 2>/dev/null || echo "0")
      [ "$is_non_negative" = "1" ] \
        && pass "$prim sim.$sim_field ($val) >= 0" \
        || fail "$prim sim.$sim_field ($val) must be >= 0"
    else
      fail "$prim sim.$sim_field is missing"
    fi
  done

  # Render fields
  jq -e ".primitives[\"$prim\"].render.fallback | length > 0" "$CATALOG" > /dev/null 2>&1 \
    && pass "$prim has non-empty render fallback" \
    || fail "$prim render fallback is empty or missing"

  jq -e ".primitives[\"$prim\"].render.metadata | keys | length > 0" "$CATALOG" > /dev/null 2>&1 \
    && pass "$prim has render metadata" \
    || fail "$prim render metadata is empty or missing"
done

# --- neon_light_strip_v2 specific checks ---
echo ""
echo "-- neon_light_strip_v2 specific --"

jq -e '.primitives.neon_light_strip_v2' "$CATALOG" > /dev/null 2>&1 \
  && pass "neon_light_strip_v2 exists in catalog" \
  || fail "neon_light_strip_v2 not found in catalog"

jq -e '.primitives.neon_light_strip_v2.capabilities | contains(["AESTHETIC","LIGHTING","WAYFINDING"])' "$CATALOG" > /dev/null 2>&1 \
  && pass "neon_light_strip_v2 has required capabilities" \
  || fail "neon_light_strip_v2 missing required capabilities"

jq -e '.primitives.neon_light_strip_v2.rollout == "EXPERIMENTAL"' "$CATALOG" > /dev/null 2>&1 \
  && pass "neon_light_strip_v2 rollout is EXPERIMENTAL" \
  || fail "neon_light_strip_v2 rollout is not EXPERIMENTAL"

jq -e '.primitives.neon_light_strip_v2.constraints.max_contiguous_length == 32' "$CATALOG" > /dev/null 2>&1 \
  && pass "neon_light_strip_v2 max_contiguous_length is 32" \
  || fail "neon_light_strip_v2 max_contiguous_length is not 32"

jq -e '.primitives.neon_light_strip_v2.sim.power_generation_kw == 0' "$CATALOG" > /dev/null 2>&1 \
  && pass "neon_light_strip_v2 zero power generation" \
  || fail "neon_light_strip_v2 power generation is not zero"

jq -e '.primitives.neon_light_strip_v2.sim.power_consumption_kw > 0' "$CATALOG" > /dev/null 2>&1 \
  && pass "neon_light_strip_v2 has positive power consumption" \
  || fail "neon_light_strip_v2 power consumption should be > 0"

jq -e '.primitives.neon_light_strip_v2.sim.visibility_contribution > 0' "$CATALOG" > /dev/null 2>&1 \
  && pass "neon_light_strip_v2 has positive visibility contribution" \
  || fail "neon_light_strip_v2 visibility contribution should be > 0"

# Summary
echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
