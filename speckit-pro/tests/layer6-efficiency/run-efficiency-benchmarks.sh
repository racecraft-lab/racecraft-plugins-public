#!/usr/bin/env bash
# run-efficiency-benchmarks.sh — Layer 6: Agent Efficiency Benchmarks
#
# Usage:
#   bash run-efficiency-benchmarks.sh                          # Run all agents
#   bash run-efficiency-benchmarks.sh --agent <name>           # Run single agent
#   bash run-efficiency-benchmarks.sh --agent <name> --sweep   # Sweep model/effort combos
#
# Requires: claude CLI with -p flag, fixtures in fixtures/<agent-name>/
#
# Results are saved to results/<timestamp>.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FIXTURES_DIR="$SCRIPT_DIR/fixtures"
RESULTS_DIR="$SCRIPT_DIR/results"
LIB_DIR="$SCRIPT_DIR/lib"

# Colors
if [ -t 1 ]; then
  BOLD='\033[1m' GREEN='\033[0;32m' RED='\033[0;31m'
  YELLOW='\033[0;33m' CYAN='\033[0;36m' RESET='\033[0m'
else
  BOLD='' GREEN='' RED='' YELLOW='' CYAN='' RESET=''
fi

# Parse arguments
TARGET_AGENT=""
SWEEP_MODE=false

while [ $# -gt 0 ]; do
  case "$1" in
    --agent) TARGET_AGENT="$2"; shift 2 ;;
    --sweep) SWEEP_MODE=true; shift ;;
    *) echo "Unknown flag: $1"; exit 2 ;;
  esac
done

# Verify claude CLI is available
if ! command -v claude &>/dev/null; then
  echo "ERROR: claude CLI not found. Layer 6 requires 'claude -p'."
  exit 1
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S")
RESULTS_FILE="$RESULTS_DIR/${TIMESTAMP}.json"
mkdir -p "$RESULTS_DIR"

# Collect agent fixtures
if [ -n "$TARGET_AGENT" ]; then
  AGENTS=("$TARGET_AGENT")
else
  AGENTS=()
  for dir in "$FIXTURES_DIR"/*/; do
    [ -d "$dir" ] && AGENTS+=("$(basename "$dir")")
  done
fi

if [ ${#AGENTS[@]} -eq 0 ]; then
  echo "No agent fixtures found in $FIXTURES_DIR/"
  echo "Create fixtures/<agent-name>/input-prompt.md to get started."
  exit 0
fi

# Model/effort combinations for sweep mode
SWEEP_CONFIGS=(
  "opus:high"
  "opus:medium"
  "sonnet:high"
  "sonnet:medium"
  "haiku:high"
  "haiku:medium"
  "haiku:low"
)

run_benchmark() {
  local agent="$1" model="${2:-}" effort="${3:-}"
  local fixture_dir="$FIXTURES_DIR/$agent"
  local input_file="$fixture_dir/input-prompt.md"
  local expected_file="$fixture_dir/expected-output.md"

  if [ ! -f "$input_file" ]; then
    printf "  ${YELLOW}SKIP${RESET} %s (no input-prompt.md)\n" "$agent"
    return
  fi

  local prompt
  prompt=$(cat "$input_file")

  # Build claude command
  local cmd="claude -p --output-format json"
  [ -n "$model" ] && cmd="$cmd --model $model"

  local label="${agent}"
  [ -n "$model" ] && label="${agent} (${model}/${effort})"

  printf "  Running ${BOLD}%s${RESET} ... " "$label"

  local output exit_code=0
  local start_time=$(date +%s)
  output=$(echo "$prompt" | $cmd 2>/dev/null) || exit_code=$?
  local end_time=$(date +%s)
  local wall_time=$((end_time - start_time))

  if [ "$exit_code" -ne 0 ]; then
    printf "${RED}ERROR${RESET} (exit %d)\n" "$exit_code"
    return
  fi

  # Parse tokens
  local tokens
  tokens=$(echo "$output" | bash "$LIB_DIR/token-counter.sh")

  # Score quality if expected output exists
  local quality='{"structural_score": -1, "content_score": -1, "overall": -1}'
  if [ -f "$expected_file" ]; then
    local actual_text
    actual_text=$(echo "$output" | python3 -c "import sys,json; print(json.load(sys.stdin).get('result',''))" 2>/dev/null || echo "")
    local tmp_actual=$(mktemp)
    echo "$actual_text" > "$tmp_actual"
    quality=$(bash "$LIB_DIR/quality-scorer.sh" "$tmp_actual" "$expected_file")
    rm -f "$tmp_actual"
  fi

  local overall_score
  overall_score=$(echo "$quality" | python3 -c "import sys,json; print(json.load(sys.stdin)['overall'])")

  if [ "$overall_score" = "-1" ]; then
    printf "${YELLOW}OK${RESET} (no baseline) | %ss | %s\n" "$wall_time" "$tokens"
  elif python3 -c "exit(0 if $overall_score >= 0.7 else 1)"; then
    printf "${GREEN}PASS${RESET} (%.0f%%) | %ss | %s\n" "$(python3 -c "print($overall_score * 100)")" "$wall_time" "$tokens"
  else
    printf "${RED}FAIL${RESET} (%.0f%%) | %ss | %s\n" "$(python3 -c "print($overall_score * 100)")" "$wall_time" "$tokens"
  fi
}

printf "\n${BOLD}${CYAN}Layer 6: Agent Efficiency Benchmarks${RESET}\n"
printf "%s\n" "--------------------------------------------"

if [ "$SWEEP_MODE" = "true" ] && [ -n "$TARGET_AGENT" ]; then
  printf "Sweep mode: testing %s across %d configurations\n\n" "$TARGET_AGENT" "${#SWEEP_CONFIGS[@]}"
  for config in "${SWEEP_CONFIGS[@]}"; do
    model="${config%%:*}"
    effort="${config##*:}"
    run_benchmark "$TARGET_AGENT" "$model" "$effort"
  done
elif [ "$SWEEP_MODE" = "true" ]; then
  echo "ERROR: --sweep requires --agent <name>"
  exit 2
else
  for agent in "${AGENTS[@]}"; do
    run_benchmark "$agent"
  done
fi

printf "\nResults saved to: %s\n" "$RESULTS_FILE"
