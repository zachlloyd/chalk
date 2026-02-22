#!/usr/bin/env bash
# Render fallback smoke test
# Confirms unknown renderer gracefully displays neon_light_strip_v2 as emissive strip.
# Validates render metadata consistency between catalog and render_metadata.json.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CATALOG="$REPO_ROOT/services/sector-sim/data/catalog.json"
RENDER_META="$REPO_ROOT/services/sector-sim/render/render_metadata.json"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }

echo "=== Render Fallback Smoke Tests ==="

# Every primitive's catalog fallback must exist in the fallback registry
echo ""
echo "-- Fallback registry coverage --"

for prim in $(jq -r '.primitives | keys[]' "$CATALOG"); do
  fb=$(jq -r ".primitives[\"$prim\"].render.fallback" "$CATALOG")
  jq -e ".fallback_registry[\"$fb\"]" "$RENDER_META" > /dev/null 2>&1 \
    && pass "$prim fallback '$fb' exists in registry" \
    || fail "$prim fallback '$fb' not found in fallback_registry"
done

# Every primitive should have a matching render profile
echo ""
echo "-- Render profile coverage --"

for prim in $(jq -r '.primitives | keys[]' "$CATALOG"); do
  jq -e ".primitive_render_profiles[\"$prim\"]" "$RENDER_META" > /dev/null 2>&1 \
    && pass "$prim has render profile" \
    || fail "$prim missing render profile in render_metadata.json"
done

# Catalog fallback must match render profile fallback
echo ""
echo "-- Catalog/render profile consistency --"

for prim in $(jq -r '.primitives | keys[]' "$CATALOG"); do
  cat_fb=$(jq -r ".primitives[\"$prim\"].render.fallback" "$CATALOG")
  profile_fb=$(jq -r ".primitive_render_profiles[\"$prim\"].fallback" "$RENDER_META" 2>/dev/null || echo "MISSING")
  [ "$cat_fb" = "$profile_fb" ] \
    && pass "$prim catalog fallback matches render profile" \
    || fail "$prim catalog fallback ($cat_fb) != render profile ($profile_fb)"
done

# --- neon_light_strip_v2 specific ---
echo ""
echo "-- neon_light_strip_v2 render fallback --"

# Fallback is emissive_strip
fb=$(jq -r '.primitives.neon_light_strip_v2.render.fallback' "$CATALOG")
[ "$fb" = "emissive_strip" ] \
  && pass "neon_light_strip_v2 fallback is 'emissive_strip'" \
  || fail "neon_light_strip_v2 fallback expected 'emissive_strip', got '$fb'"

# emissive_strip fallback must be emissive (safe display for unknown renderers)
is_emissive=$(jq -r '.fallback_registry.emissive_strip.emissive' "$RENDER_META")
[ "$is_emissive" = "true" ] \
  && pass "emissive_strip fallback is emissive" \
  || fail "emissive_strip fallback must be emissive for safe display"

# emissive_strip type is elongated_quad (strip-like shape)
strip_type=$(jq -r '.fallback_registry.emissive_strip.type' "$RENDER_META")
[ "$strip_type" = "elongated_quad" ] \
  && pass "emissive_strip type is elongated_quad" \
  || fail "emissive_strip type expected 'elongated_quad', got '$strip_type'"

# Render metadata has color palette
jq -e '.primitives.neon_light_strip_v2.render.metadata.color_palette | length > 0' "$CATALOG" > /dev/null 2>&1 \
  && pass "neon_light_strip_v2 has color_palette" \
  || fail "neon_light_strip_v2 missing color_palette in render metadata"

# Render metadata has glow intensity
jq -e '.primitives.neon_light_strip_v2.render.metadata.glow_intensity > 0' "$CATALOG" > /dev/null 2>&1 \
  && pass "neon_light_strip_v2 has positive glow_intensity" \
  || fail "neon_light_strip_v2 missing or non-positive glow_intensity"

# Render metadata emissive flag
jq -e '.primitives.neon_light_strip_v2.render.metadata.emissive == true' "$CATALOG" > /dev/null 2>&1 \
  && pass "neon_light_strip_v2 render metadata emissive is true" \
  || fail "neon_light_strip_v2 render metadata emissive should be true"

# Simulate unknown renderer: verify fallback provides all needed fields
echo ""
echo "-- Unknown renderer graceful display --"

# An unknown renderer should be able to display using only fallback_registry info
for field in type emissive default_color; do
  jq -e ".fallback_registry.emissive_strip.$field" "$RENDER_META" > /dev/null 2>&1 \
    && pass "emissive_strip fallback has '$field' for unknown renderer" \
    || fail "emissive_strip fallback missing '$field' needed by unknown renderer"
done

# Summary
echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
