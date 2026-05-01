#!/usr/bin/env bash
# run-all-fixtures.sh — Run every Layer 7 fixture (Class 1, 2, 3).
#
# Usage:
#   bash run-all-fixtures.sh                # all classes, replay
#   bash run-all-fixtures.sh --live         # all classes, live (real LLM, $$)
#   bash run-all-fixtures.sh --class 1      # only Class 1
#   bash run-all-fixtures.sh --class 1 --live

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODE_FLAG=""
SELECTED_CLASS="all"

while [ $# -gt 0 ]; do
  case "$1" in
    --replay) MODE_FLAG="--replay"; shift ;;
    --live)   MODE_FLAG="--live"; shift ;;
    --class)  SELECTED_CLASS="$2"; shift 2 ;;
    *) shift ;;
  esac
done

declare -A RUNNERS=(
  [1]="$SCRIPT_DIR/run-dispatch-fixtures.sh"
  [2]="$SCRIPT_DIR/run-return-format-fixtures.sh"
  [3]="$SCRIPT_DIR/run-e2e-fixtures.sh"
)

OVERALL_FAIL=0

run_class() {
  local class="$1"
  local runner="${RUNNERS[$class]}"
  printf "\n══════════════════════════════════════════════════════════════════\n"
  printf "  Layer 7 — Class %s\n" "$class"
  printf "══════════════════════════════════════════════════════════════════\n"
  if ! bash "$runner" $MODE_FLAG; then
    OVERALL_FAIL=1
  fi
}

if [ "$SELECTED_CLASS" = "all" ]; then
  for c in 1 2 3; do run_class "$c"; done
else
  run_class "$SELECTED_CLASS"
fi

printf "\n══════════════════════════════════════════════════════════════════\n"
if [ "$OVERALL_FAIL" -eq 0 ]; then
  printf "  Layer 7 PASSED\n"
else
  printf "  Layer 7 FAILED\n"
fi
printf "══════════════════════════════════════════════════════════════════\n"

exit "$OVERALL_FAIL"
