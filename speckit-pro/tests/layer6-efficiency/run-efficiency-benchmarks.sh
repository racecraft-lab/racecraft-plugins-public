#!/usr/bin/env bash
# run-efficiency-benchmarks.sh — Layer 6: Agent Efficiency Benchmarks
#
# Usage:
#   bash run-efficiency-benchmarks.sh                          # Run all agents
#   bash run-efficiency-benchmarks.sh --agent <name>           # Run single agent
#   bash run-efficiency-benchmarks.sh --agent <name> --sweep   # Sweep model combos
#
# Requires: claude CLI with -p flag, fixtures in fixtures/<agent-name>/
#
# Results are saved to results/<timestamp>.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FIXTURES_DIR="$SCRIPT_DIR/fixtures"
RESULTS_DIR="$SCRIPT_DIR/results"
LIB_DIR="$SCRIPT_DIR/lib"
PLUGIN_ROOT="${PLUGIN_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

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

# JSON utility functions for writing results
json_escape() {
  local value="${1-}"
  value=${value//\\/\\\\}
  value=${value//\"/\\\"}
  value=${value//$'\n'/\\n}
  value=${value//$'\r'/\\r}
  value=${value//$'\t'/\\t}
  printf '%s' "$value"
}

append_result_record() {
  local agent="$1"
  local model="$2"
  local tokens="$3"
  local wall_time="$4"
  local quality="$5"
  local exit_code="$6"

  if [ "${RESULTS_FILE_INITIALIZED:-false}" != "true" ]; then
    printf '[\n' >"$RESULTS_FILE"
    RESULTS_FILE_INITIALIZED=true
    RESULTS_FILE_HAS_RECORDS=false
  fi

  if [ "$RESULTS_FILE_HAS_RECORDS" = "true" ]; then
    printf ',\n' >>"$RESULTS_FILE"
  fi

  printf '  {"agent":"%s","model":"%s","tokens":%s,"wall_time":%s,"quality":%s,"exit_code":%s}' \
    "$(json_escape "$agent")" \
    "$(json_escape "$model")" \
    "${tokens:-0}" \
    "${wall_time:-0}" \
    "${quality:-0}" \
    "${exit_code:-0}" >>"$RESULTS_FILE"

  RESULTS_FILE_HAS_RECORDS=true
}

finalize_results_file() {
  if [ "${RESULTS_FILE_INITIALIZED:-false}" != "true" ]; then
    printf '[\n]\n' >"$RESULTS_FILE"
    return
  fi

  if [ "${RESULTS_FILE_FINALIZED:-false}" = "true" ]; then
    return
  fi

  printf '\n]\n' >>"$RESULTS_FILE"
  RESULTS_FILE_FINALIZED=true
}

RESULTS_FILE_INITIALIZED=false
RESULTS_FILE_HAS_RECORDS=false
RESULTS_FILE_FINALIZED=false
trap finalize_results_file EXIT

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

# Model combinations for sweep mode.
# Effort is configured in agent definition frontmatter, not via a CLI flag.
SWEEP_CONFIGS=(
  "opus"
  "sonnet"
  "haiku"
)

run_benchmark() {
  local agent="$1" model="${2:-}"
  local fixture_dir="$FIXTURES_DIR/$agent"
  local input_file="$fixture_dir/input-prompt.md"
  local expected_file="$fixture_dir/expected-output.md"

  if [ ! -f "$input_file" ]; then
    printf "  ${YELLOW}SKIP${RESET} %s (no input-prompt.md)\n" "$agent"
    return
  fi

  # Load agent definition body (after frontmatter) to include as system context
  local agent_file="$PLUGIN_ROOT/agents/${agent}.md"
  local prompt
  if [ -f "$agent_file" ]; then
    local agent_body
    agent_body=$(awk 'BEGIN{fm=0} /^---$/{fm++; next} fm>=2{print}' "$agent_file")
    prompt=$(printf '%s\n\n---\n\n%s' "$agent_body" "$(cat "$input_file")")
  else
    prompt=$(cat "$input_file")
  fi

  # Build claude command
  local cmd="claude -p --output-format json"
  [ -n "$model" ] && cmd="$cmd --model $model"

  local label="${agent}"
  [ -n "$model" ] && label="${agent} (${model})"

  printf "  Running ${BOLD}%s${RESET} ... " "$label"

  local output exit_code=0
  local stderr_file stderr=""
  stderr_file=$(mktemp)
  local start_time
  start_time=$(date +%s)
  output=$(echo "$prompt" | $cmd 2>"$stderr_file") || exit_code=$?
  local end_time
  end_time=$(date +%s)
  local wall_time=$((end_time - start_time))
  if [ -s "$stderr_file" ]; then
    stderr=$(cat "$stderr_file")
  fi
  rm -f "$stderr_file"

  if [ "$exit_code" -ne 0 ]; then
    printf "${RED}ERROR${RESET} (exit %d)\n" "$exit_code"
    if [ -n "$stderr" ]; then
      printf "    claude stderr:\n"
      printf '%s\n' "$stderr" | sed 's/^/      /'
    fi
    append_result_record "$agent" "$model" "0" "$wall_time" "0" "$exit_code"
    return
  fi

  # Parse tokens
  local tokens_json total_tokens
  tokens_json=$(echo "$output" | bash "$LIB_DIR/token-counter.sh")
  total_tokens=$(echo "$tokens_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_tokens', 0))" 2>/dev/null || echo "0")

  # Score quality if expected output exists
  local quality='{"structural_score": -1, "content_score": -1, "overall": -1}'
  if [ -f "$expected_file" ]; then
    local actual_text
    actual_text=$(echo "$output" | python3 -c "import sys,json; print(json.load(sys.stdin).get('result',''))" 2>/dev/null || echo "")
    local tmp_actual
    tmp_actual=$(mktemp)
    echo "$actual_text" > "$tmp_actual"
    quality=$(bash "$LIB_DIR/quality-scorer.sh" "$tmp_actual" "$expected_file")
    rm -f "$tmp_actual"
  fi

  local overall_score
  overall_score=$(echo "$quality" | python3 -c "import sys,json; print(json.load(sys.stdin)['overall'])")

  append_result_record "$agent" "$model" "$total_tokens" "$wall_time" "$overall_score" "0"

  if [ "$overall_score" = "-1" ]; then
    printf "${YELLOW}OK${RESET} (no baseline) | %ss | %s tokens\n" "$wall_time" "$total_tokens"
  elif python3 -c "exit(0 if $overall_score >= 0.7 else 1)"; then
    printf "${GREEN}PASS${RESET} (%.0f%%) | %ss | %s tokens\n" "$(python3 -c "print($overall_score * 100)")" "$wall_time" "$total_tokens"
  else
    printf "${RED}FAIL${RESET} (%.0f%%) | %ss | %s tokens\n" "$(python3 -c "print($overall_score * 100)")" "$wall_time" "$total_tokens"
  fi
}

printf "\n${BOLD}${CYAN}Layer 6: Agent Efficiency Benchmarks${RESET}\n"
printf "%s\n" "--------------------------------------------"

if [ "$SWEEP_MODE" = "true" ] && [ -n "$TARGET_AGENT" ]; then
  printf "Sweep mode: testing %s across %d model configurations\n\n" "$TARGET_AGENT" "${#SWEEP_CONFIGS[@]}"
  for config in "${SWEEP_CONFIGS[@]}"; do
    run_benchmark "$TARGET_AGENT" "$config"
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
