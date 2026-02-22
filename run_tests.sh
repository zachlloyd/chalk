#!/usr/bin/env bash
# Run test suites for World of Warp
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TESTS_DIR="$SCRIPT_DIR/tests"

suite="${1:-all}"
EXIT_CODE=0

run_suite() {
  local name=$1
  local dir=$2
  echo ""
  echo "========================================"
  echo "  Running $name tests"
  echo "========================================"
  for test_file in "$dir"/test_*.sh; do
    if [ -f "$test_file" ]; then
      echo ""
      echo ">>> $test_file"
      bash "$test_file" || EXIT_CODE=1
    fi
  done
}

case "$suite" in
  schema)
    run_suite "Schema" "$TESTS_DIR/schema"
    ;;
  sim)
    run_suite "Sim" "$TESTS_DIR/sim"
    ;;
  render)
    run_suite "Render" "$TESTS_DIR/render"
    ;;
  all)
    run_suite "Schema" "$TESTS_DIR/schema"
    run_suite "Sim" "$TESTS_DIR/sim"
    run_suite "Render" "$TESTS_DIR/render"
    ;;
  *)
    echo "Usage: $0 [schema|sim|render|all]"
    exit 1
    ;;
esac

echo ""
if [ "$EXIT_CODE" -eq 0 ]; then
  echo "All test suites passed."
else
  echo "Some tests FAILED."
fi
exit $EXIT_CODE
