#!/usr/bin/env bash
# run-efficiency-benchmarks.sh — Layer 6: Agent Efficiency Benchmarks
#
# Usage:
#   bash run-efficiency-benchmarks.sh                          # Run all Claude agents
#   bash run-efficiency-benchmarks.sh --agent <name>           # Single Claude agent
#   bash run-efficiency-benchmarks.sh --agent <name> --sweep   # Claude model sweep
#
#   bash run-efficiency-benchmarks.sh --codex                  # Run all Codex agents
#   bash run-efficiency-benchmarks.sh --codex --agent <name>   # Single Codex agent
#   bash run-efficiency-benchmarks.sh --codex --agent <name> --sweep
#                                                              # Codex effort sweep
#                                                              # (xhigh / high / medium / low)
#
# Requires:
#   - Claude path: `claude -p`, fixtures under fixtures/<agent>/
#   - Codex path:  `codex exec`, fixtures under fixtures-codex/<agent>/
#
# Results land in results/<timestamp>.json (Claude) or
# results-codex/<timestamp>.json (Codex). The two runtimes use separate
# results directories so the JSON shape per record stays unambiguous
# about which runtime produced it.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"
PLUGIN_ROOT="${PLUGIN_ROOT:-$(cd "$SCRIPT_DIR/../../../speckit-pro" && pwd)}"

# Runtime defaults to Claude; --codex below switches to Codex.
RUNTIME="claude"
CODEX_BIN="${CODEX_BIN:-codex}"

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
    --codex)
      RUNTIME="codex"
      shift
      ;;
    *) echo "Unknown flag: $1"; exit 2 ;;
  esac
done

# Resolve fixture + results dirs AFTER args. The L4 unit test sets
# these via env vars to point at synthetic fixtures; the default
# locations are `$SCRIPT_DIR/{fixtures,results}` for Claude and
# `$SCRIPT_DIR/{fixtures-codex,results-codex}` for Codex.
if [ "$RUNTIME" = "codex" ]; then
  FIXTURES_DIR="${L6_FIXTURES_DIR:-$SCRIPT_DIR/fixtures-codex}"
  RESULTS_DIR="${L6_RESULTS_DIR:-$SCRIPT_DIR/results-codex}"
else
  FIXTURES_DIR="${L6_FIXTURES_DIR:-$SCRIPT_DIR/fixtures}"
  RESULTS_DIR="${L6_RESULTS_DIR:-$SCRIPT_DIR/results}"
fi

# Verify the runtime CLI is available before doing any benchmark work.
if [ "$RUNTIME" = "claude" ]; then
  if ! command -v claude &>/dev/null; then
    echo "ERROR: claude CLI not found. Layer 6 (Claude) requires 'claude -p'."
    exit 1
  fi
else
  if ! command -v "$CODEX_BIN" &>/dev/null; then
    echo "ERROR: $CODEX_BIN CLI not found. Layer 6 (Codex) requires 'codex exec'."
    exit 1
  fi
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

# Sweep axes per runtime.
# Claude varies the model (effort is baked into the agent frontmatter).
# Codex varies `model_reasoning_effort` via `codex exec -c` override, with
# the model held constant from the .toml agent definition. The two
# runtimes are intentionally NOT unified — they vary different axes.
SWEEP_CONFIGS=(
  "opus"
  "sonnet"
  "haiku"
)
CODEX_SWEEP_CONFIGS=(
  "xhigh"
  "high"
  "medium"
  "low"
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

  # Load agent definition body (after frontmatter) to include as system context.
  # Prepending the agent definition ensures the benchmark tests the actual agent
  # behavior, not just prompt-only responses. The '---' separator visually
  # delimits the agent system context from the user-facing input prompt.
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

# Extract the `developer_instructions = """..."""` block from a Codex
# agent TOML file. This is the Codex analog of awk-stripping YAML
# frontmatter from a Claude .md agent: it returns just the prompt body
# that goes into the model's developer-instructions context.
extract_codex_agent_body() {
  local toml_file="$1"
  awk '
    /^developer_instructions[[:space:]]*=[[:space:]]*"""$/ { inside = 1; next }
    inside && /^"""$/                                     { inside = 0; next }
    inside                                                { print }
  ' "$toml_file"
}

run_benchmark_codex() {
  local agent="$1" effort="${2:-}"
  local fixture_dir="$FIXTURES_DIR/$agent"
  local input_file="$fixture_dir/input-prompt.md"
  local expected_file="$fixture_dir/expected-output.md"

  if [ ! -f "$input_file" ]; then
    printf "  ${YELLOW}SKIP${RESET} %s (no input-prompt.md)\n" "$agent"
    return
  fi

  # Compose the developer prompt: agent body (from TOML) followed by the
  # fixture input. Mirrors the Claude path's "agent body + ---  + input"
  # pattern so the model sees its full instructions before the user task.
  local agent_file="$PLUGIN_ROOT/codex-agents/${agent}.toml"
  local prompt
  if [ -f "$agent_file" ]; then
    local agent_body
    agent_body=$(extract_codex_agent_body "$agent_file")
    prompt=$(printf '%s\n\n---\n\n%s' "$agent_body" "$(cat "$input_file")")
  else
    prompt=$(cat "$input_file")
  fi

  local label="${agent}"
  [ -n "$effort" ] && label="${agent} (effort=${effort})"

  printf "  Running ${BOLD}%s${RESET} ... " "$label"

  local jsonl_file stderr_file last_message_file exit_code=0
  jsonl_file=$(mktemp)
  stderr_file=$(mktemp)
  last_message_file=$(mktemp)

  local start_time end_time wall_time
  start_time=$(date +%s)

  # codex exec consumes prompt from stdin when --no argument is given,
  # but the binary also accepts the prompt via stdin if explicitly piped.
  # -c model_reasoning_effort=<level> overrides the per-call effort
  # without mutating the .toml; -o writes the final agent message; --json
  # streams events so we can extract token usage from `turn.completed`.
  local effort_arg=()
  [ -n "$effort" ] && effort_arg=(-c "model_reasoning_effort=$effort")
  printf '%s' "$prompt" \
    | "$CODEX_BIN" exec \
        "${effort_arg[@]}" \
        --json \
        -o "$last_message_file" \
        - \
        >"$jsonl_file" 2>"$stderr_file" \
    || exit_code=$?

  end_time=$(date +%s)
  wall_time=$((end_time - start_time))

  if [ "$exit_code" -ne 0 ]; then
    printf "${RED}ERROR${RESET} (exit %d)\n" "$exit_code"
    if [ -s "$stderr_file" ]; then
      printf "    codex stderr:\n"
      sed 's/^/      /' "$stderr_file"
    fi
    append_result_record "$agent" "effort=$effort" "0" "$wall_time" "0" "$exit_code"
    rm -f "$jsonl_file" "$stderr_file" "$last_message_file"
    return
  fi

  # Parse total tokens from the last `turn.completed.usage` event. Codex
  # accounts for cached_input_tokens separately from input_tokens; we
  # report the sum the same way the Claude path's token-counter.sh does
  # (input_tokens + cache + output_tokens).
  local total_tokens
  total_tokens=$(python3 - "$jsonl_file" <<'PY'
import json, sys
total = 0
with open(sys.argv[1]) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue
        if evt.get("type") == "turn.completed":
            usage = evt.get("usage", {}) or {}
            total = (usage.get("input_tokens", 0)
                     + usage.get("cached_input_tokens", 0)
                     + usage.get("output_tokens", 0)
                     + usage.get("reasoning_output_tokens", 0))
print(total)
PY
)

  # Quality score against the expected-output.md baseline. The Codex
  # `-o` flag wrote the final agent message to last_message_file; the
  # quality scorer is the same script the Claude path uses.
  local quality='{"structural_score": -1, "content_score": -1, "overall": -1}'
  if [ -f "$expected_file" ] && [ -s "$last_message_file" ]; then
    quality=$(bash "$LIB_DIR/quality-scorer.sh" "$last_message_file" "$expected_file")
  fi

  local overall_score
  overall_score=$(echo "$quality" | python3 -c "import sys,json; print(json.load(sys.stdin)['overall'])")

  append_result_record "$agent" "effort=$effort" "$total_tokens" "$wall_time" "$overall_score" "0"

  if [ "$overall_score" = "-1" ]; then
    printf "${YELLOW}OK${RESET} (no baseline) | %ss | %s tokens\n" "$wall_time" "$total_tokens"
  elif python3 -c "exit(0 if $overall_score >= 0.7 else 1)"; then
    printf "${GREEN}PASS${RESET} (%.0f%%) | %ss | %s tokens\n" "$(python3 -c "print($overall_score * 100)")" "$wall_time" "$total_tokens"
  else
    printf "${RED}FAIL${RESET} (%.0f%%) | %ss | %s tokens\n" "$(python3 -c "print($overall_score * 100)")" "$wall_time" "$total_tokens"
  fi

  rm -f "$jsonl_file" "$stderr_file" "$last_message_file"
}

printf "\n${BOLD}${CYAN}Layer 6: Agent Efficiency Benchmarks (runtime=%s)${RESET}\n" "$RUNTIME"
printf "%s\n" "--------------------------------------------"

if [ "$RUNTIME" = "claude" ]; then
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
else
  if [ "$SWEEP_MODE" = "true" ] && [ -n "$TARGET_AGENT" ]; then
    printf "Sweep mode: testing %s across %d effort levels\n\n" "$TARGET_AGENT" "${#CODEX_SWEEP_CONFIGS[@]}"
    for effort in "${CODEX_SWEEP_CONFIGS[@]}"; do
      run_benchmark_codex "$TARGET_AGENT" "$effort"
    done
  elif [ "$SWEEP_MODE" = "true" ]; then
    echo "ERROR: --sweep requires --agent <name>"
    exit 2
  else
    for agent in "${AGENTS[@]}"; do
      run_benchmark_codex "$agent"
    done
  fi
fi

printf "\nResults saved to: %s\n" "$RESULTS_FILE"
