#!/usr/bin/env bash
# run-all.sh — speckit-pro plugin test suite orchestrator
#
# Usage:
#   tests/run-all.sh              # Layers 1, 4, 5 (deterministic, synthetic)
#   tests/run-all.sh --live       # Layers 1, 4, 5 + live project tests
#   tests/run-all.sh --layer 2    # Layer 2 only (trigger evals, requires claude -p)
#   tests/run-all.sh --layer 3    # Layer 3 only (functional evals, requires claude -p)
#   tests/run-all.sh --layer 6    # Layer 6 only (efficiency benchmarks, requires claude -p)
#   tests/run-all.sh --ci         # CI mode: layers 1, 4, 5 synthetic only
#   tests/run-all.sh --all        # All 6 layers + live project tests
#
# Run from the project directory (e.g., racecraft-plugins-public/) so live tests
# can access .specify/, specs/, and other SpecKit artifacts.
#
# Environment:
#   PLUGIN_ROOT           Path to speckit-pro plugin (auto-detected)
#   PROJECT_ROOT          Path to SpecKit project for live tests (defaults to cwd)
#   SKILL_CREATOR_ROOT    Path to skill-creator plugin (for layers 2, 3)
#   VERBOSE               Set to "true" for per-test output

set -euo pipefail

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$TESTS_DIR/.." && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
export PLUGIN_ROOT PROJECT_ROOT

# Parse arguments
RUN_LIVE=false
RUN_LAYER=""
RUN_ALL=false
CI_MODE=false
RUN_CODEX=false

while [ $# -gt 0 ]; do
  case "$1" in
    --live) RUN_LIVE=true; shift ;;
    --layer) RUN_LAYER="$2"; shift 2 ;;
    --all) RUN_ALL=true; RUN_LIVE=true; shift ;;
    --ci) CI_MODE=true; shift ;;
    --codex) RUN_CODEX=true; shift ;;
    --verbose) export VERBOSE=true; shift ;;
    *) echo "Unknown flag: $1"; exit 2 ;;
  esac
done

# Colors
if [ -t 1 ]; then
  BOLD='\033[1m' GREEN='\033[0;32m' RED='\033[0;31m'
  YELLOW='\033[0;33m' CYAN='\033[0;36m' RESET='\033[0m'
else
  BOLD='' GREEN='' RED='' YELLOW='' CYAN='' RESET=''
fi

TOTAL_PASS=0
TOTAL_FAIL=0
LAYER_RESULTS=()

run_layer() {
  local layer_num="$1" layer_name="$2"
  shift 2
  local scripts=("$@")

  printf "\n${BOLD}${CYAN}Layer %s: %s${RESET}\n" "$layer_num" "$layer_name"
  printf "%s\n" "────────────────────────────────────────"

  local layer_pass=0 layer_fail=0

  for script in "${scripts[@]}"; do
    if [ ! -f "$script" ]; then
      printf "  ${YELLOW}SKIP${RESET}: %s (not found)\n" "$(basename "$script")"
      continue
    fi

    local output exit_code=0
    output=$(bash "$script" 2>&1) || exit_code=$?

    # Extract pass/fail from the summary line (format: "name: X/Y passed")
    local summary
    summary=$(echo "$output" | grep -E '[0-9]+/[0-9]+ passed' | tail -1)
    if [ -n "$summary" ]; then
      local passed total
      passed=$(echo "$summary" | grep -oE '[0-9]+/[0-9]+' | head -1 | cut -d/ -f1)
      total=$(echo "$summary" | grep -oE '[0-9]+/[0-9]+' | head -1 | cut -d/ -f2)
      local failed=$((total - passed))
      layer_pass=$((layer_pass + passed))
      layer_fail=$((layer_fail + failed))

      if [ "$failed" -eq 0 ]; then
        printf "  ${GREEN}PASS${RESET} %s (%d/%d)\n" "$(basename "$script" .sh)" "$passed" "$total"
      else
        printf "  ${RED}FAIL${RESET} %s (%d/%d, %d failed)\n" \
          "$(basename "$script" .sh)" "$passed" "$total" "$failed"
        # Show failure details
        echo "$output" | grep -E 'FAIL' | head -5 | while read -r line; do
          printf "       %s\n" "$line"
        done
      fi
    else
      # No summary line — script may have crashed
      if [ "$exit_code" -eq 0 ]; then
        printf "  ${GREEN}PASS${RESET} %s (no summary)\n" "$(basename "$script" .sh)"
      else
        printf "  ${RED}FAIL${RESET} %s (exit %d)\n" "$(basename "$script" .sh)" "$exit_code"
        echo "$output" | tail -3 | while read -r line; do
          printf "       %s\n" "$line"
        done
        ((layer_fail++))
      fi
    fi
  done

  TOTAL_PASS=$((TOTAL_PASS + layer_pass))
  TOTAL_FAIL=$((TOTAL_FAIL + layer_fail))
  LAYER_RESULTS+=("L${layer_num}: ${layer_pass}/$((layer_pass + layer_fail))")
}

# Determine which layers to run
should_run() {
  local layer="$1"
  if [ -n "$RUN_LAYER" ]; then
    [ "$RUN_LAYER" = "$layer" ]
  elif [ "$RUN_ALL" = "true" ]; then
    return 0
  elif [ "$layer" = "2" ] || [ "$layer" = "3" ] || [ "$layer" = "6" ]; then
    return 1  # Skip expensive layers by default
  else
    return 0
  fi
}

# ─────────────────────────────────────────
# Layer 1: Structural Validation
# ─────────────────────────────────────────

if should_run 1; then
  run_layer 1 "Structural Validation" \
    "$TESTS_DIR/layer1-structural/validate-plugin.sh" \
    "$TESTS_DIR/layer1-structural/validate-commands.sh" \
    "$TESTS_DIR/layer1-structural/validate-agents.sh" \
    "$TESTS_DIR/layer1-structural/validate-skills.sh" \
    "$TESTS_DIR/layer1-structural/validate-hooks.sh" \
    "$TESTS_DIR/layer1-structural/validate-scripts.sh" \
    "$TESTS_DIR/layer1-structural/validate-pr-checks-sentinel.sh"

  # Codex structural tests (run with --codex or --all)
  if [ "$RUN_CODEX" = "true" ] || [ "$RUN_ALL" = "true" ]; then
    run_layer 1 "Codex Structural Validation" \
      "$TESTS_DIR/layer1-structural/validate-codex-plugin.sh" \
      "$TESTS_DIR/layer1-structural/validate-codex-marketplace.sh" \
      "$TESTS_DIR/layer1-structural/validate-codex-agents.sh" \
      "$TESTS_DIR/layer1-structural/validate-codex-skills.sh" \
      "$TESTS_DIR/layer1-structural/validate-codex-hooks.sh" \
      "$TESTS_DIR/layer1-structural/validate-codex-commands.sh" \
      "$TESTS_DIR/layer1-structural/validate-codex-parity.sh"
  fi
fi

# ─────────────────────────────────────────
# Layer 2: Trigger Evaluation
# ─────────────────────────────────────────

if should_run 2; then
  SKILL_CREATOR="${SKILL_CREATOR_ROOT:-$HOME/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator}"
  if [ -f "$SKILL_CREATOR/scripts/run_eval.py" ]; then
    printf "\n${BOLD}${CYAN}Layer 2: Trigger Evaluation${RESET}\n"
    printf "%s\n" "────────────────────────────────────────"
    printf "  Run manually:\n"
    printf "    ${BOLD}bash %s/tests/layer2-trigger/run-trigger-evals.sh speckit-coach${RESET}\n" "$PLUGIN_ROOT"
    printf "    ${BOLD}bash %s/tests/layer2-trigger/run-trigger-evals.sh speckit-autopilot${RESET}\n" "$PLUGIN_ROOT"
  else
    printf "\n${YELLOW}Layer 2: SKIP — skill-creator not found at %s${RESET}\n" "$SKILL_CREATOR"
  fi
fi

# ─────────────────────────────────────────
# Layer 3: Functional Evals
# ─────────────────────────────────────────

if should_run 3; then
  printf "\n${BOLD}${CYAN}Layer 3: Functional Evaluation${RESET}\n"
  printf "%s\n" "────────────────────────────────────────"
  printf "  Eval files:\n"
  printf "    %s/tests/layer3-functional/evals/speckit-coach-evals.json\n" "$PLUGIN_ROOT"
  printf "    %s/tests/layer3-functional/evals/speckit-autopilot-evals.json\n" "$PLUGIN_ROOT"
  printf "  Run via skill-creator eval workflow or manually.\n"
fi

# ─────────────────────────────────────────
# Layer 4: Script Unit Tests
# ─────────────────────────────────────────

if should_run 4; then
  LIVE_FLAG=""
  [ "$RUN_LIVE" = "true" ] && LIVE_FLAG="--live"

  layer4_scripts=(
    "$TESTS_DIR/layer4-scripts/test-validate-gate.sh"
    "$TESTS_DIR/layer4-scripts/test-detect-commands.sh"
    "$TESTS_DIR/layer4-scripts/test-check-prerequisites.sh"
    "$TESTS_DIR/layer4-scripts/test-detect-presets.sh"
    "$TESTS_DIR/layer4-scripts/test-sync-marketplace-versions.sh"
  )

  if [ -n "$LIVE_FLAG" ]; then
    # Run with --live flag by wrapping each script
    printf "\n${BOLD}${CYAN}Layer 4: Script Unit Tests (+ live)${RESET}\n"
    printf "%s\n" "────────────────────────────────────────"
    layer4_pass=0 layer4_fail=0
    for script in "${layer4_scripts[@]}"; do
      if [ ! -f "$script" ]; then continue; fi
      local_output=$(bash "$script" "$LIVE_FLAG" 2>&1) || true
      summary=$(echo "$local_output" | grep -E '[0-9]+/[0-9]+ passed' | tail -1)
      if [ -n "$summary" ]; then
        passed=$(echo "$summary" | grep -oE '[0-9]+/[0-9]+' | head -1 | cut -d/ -f1)
        total=$(echo "$summary" | grep -oE '[0-9]+/[0-9]+' | head -1 | cut -d/ -f2)
        failed=$((total - passed))
        layer4_pass=$((layer4_pass + passed))
        layer4_fail=$((layer4_fail + failed))
        TOTAL_PASS=$((TOTAL_PASS + passed))
        TOTAL_FAIL=$((TOTAL_FAIL + failed))
        if [ "$failed" -eq 0 ]; then
          printf "  ${GREEN}PASS${RESET} %s (%d/%d)\n" "$(basename "$script" .sh)" "$passed" "$total"
        else
          printf "  ${RED}FAIL${RESET} %s (%d/%d, %d failed)\n" \
            "$(basename "$script" .sh)" "$passed" "$total" "$failed"
          echo "$local_output" | grep -E 'FAIL' | head -5 | while read -r line; do
            printf "       %s\n" "$line"
          done
        fi
      else
        # No summary — script may have crashed before test_summary was reached
        printf "  ${RED}FAIL${RESET} %s (no summary — script may have crashed)\n" \
          "$(basename "$script" .sh)"
        echo "$local_output" | tail -3 | while read -r line; do
          printf "       %s\n" "$line"
        done
        ((layer4_fail++))
        ((TOTAL_FAIL++))
      fi
    done
    LAYER_RESULTS+=("L4: ${layer4_pass}/$((layer4_pass + layer4_fail))")
  else
    run_layer 4 "Script Unit Tests" "${layer4_scripts[@]}"
  fi
fi

# ─────────────────────────────────────────
# Layer 5: Agent Tool Scoping
# ─────────────────────────────────────────

if should_run 5; then
  run_layer 5 "Agent Tool Scoping" \
    "$TESTS_DIR/layer5-tool-scoping/validate-tool-scoping.sh"
fi

# ─────────────────────────────────────────
# Layer 6: Agent Efficiency Benchmarks
# ─────────────────────────────────────────

if should_run 6; then
  L6_SCRIPT="$TESTS_DIR/layer6-efficiency/run-efficiency-benchmarks.sh"
  if [ -f "$L6_SCRIPT" ]; then
    printf "\n${BOLD}${CYAN}Layer 6: Agent Efficiency Benchmarks${RESET}\n"
    printf "%s\n" "────────────────────────────────────────"
    printf "  Run manually:\n"
    printf "    ${BOLD}bash %s${RESET}\n" "$L6_SCRIPT"
    printf "    ${BOLD}bash %s --agent gate-validator${RESET}\n" "$L6_SCRIPT"
    printf "    ${BOLD}bash %s --agent gate-validator --sweep${RESET}\n" "$L6_SCRIPT"
  else
    printf "\n${YELLOW}Layer 6: SKIP — run-efficiency-benchmarks.sh not found${RESET}\n"
  fi
fi

# ─────────────────────────────────────────
# Summary
# ─────────────────────────────────────────

GRAND_TOTAL=$((TOTAL_PASS + TOTAL_FAIL))

printf "\n${BOLD}%s${RESET}\n" "════════════════════════════════════════"
printf "${BOLD}speckit-pro test suite${RESET}: "
if [ "$TOTAL_FAIL" -eq 0 ] && [ "$GRAND_TOTAL" -gt 0 ]; then
  printf "${GREEN}%d/%d passed${RESET}\n" "$TOTAL_PASS" "$GRAND_TOTAL"
else
  printf "${RED}%d/%d passed (%d failed)${RESET}\n" \
    "$TOTAL_PASS" "$GRAND_TOTAL" "$TOTAL_FAIL"
fi

for lr in "${LAYER_RESULTS[@]}"; do
  printf "  %s\n" "$lr"
done
printf "\n"

[ "$TOTAL_FAIL" -eq 0 ]
