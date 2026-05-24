#!/usr/bin/env bash
# Layer 8 — Parity Fixtures Runner
#
# Verifies that two code paths (Agent Teams path vs parallel-subagents
# fallback) produce equivalent outcomes for the same workflow input.
#
# Modes:
#   --dry-run (default): validates fixture structure only; no claude -p
#   --live:              actually runs claude -p twice per fixture and
#                        compares outcomes. COSTS LLM TOKENS.
#
# Usage:
#   bash tests/layer8-parity/run-parity-fixtures.sh [--dry-run|--live]
#                                                    [--fixture <name>]
#                                                    [--budget-usd <N>]
#
# Environment:
#   L8_FIXTURE_BUDGET_USD  Per-fixture-pair budget cap (default: 20)
#   CLAUDE_BIN             claude executable (default: claude)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Defaults
MODE="dry-run"
FIXTURE_FILTER=""
L8_FIXTURE_BUDGET_USD="${L8_FIXTURE_BUDGET_USD:-20}"
CLAUDE_BIN="${CLAUDE_BIN:-claude}"

# Colors
if [ -t 1 ]; then
  RED='\033[31m'
  GREEN='\033[32m'
  YELLOW='\033[33m'
  RESET='\033[0m'
else
  RED='' GREEN='' YELLOW='' RESET=''
fi

# Parse args
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) MODE="dry-run"; shift ;;
    --live) MODE="live"; shift ;;
    --fixture) FIXTURE_FILTER="$2"; shift 2 ;;
    --budget-usd) L8_FIXTURE_BUDGET_USD="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,20p' "$0"
      exit 0
      ;;
    *) echo "Unknown flag: $1" >&2; exit 2 ;;
  esac
done

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

_pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf "  ${GREEN}PASS${RESET} %s\n" "$1"; }
_fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf "  ${RED}FAIL${RESET} %s\n    ${RED}%s${RESET}\n" "$1" "${2:-}"; }
_skip() { SKIP_COUNT=$((SKIP_COUNT + 1)); printf "  ${YELLOW}SKIP${RESET} %s\n    ${YELLOW}%s${RESET}\n" "$1" "${2:-}"; }

# ---------------------------------------------------------------------------
# Dry-run validation: every fixture must have these files
# ---------------------------------------------------------------------------
validate_fixture_structure() {
  local fixture_dir="$1"
  local fixture_id
  fixture_id="$(basename "$fixture_dir")"
  local ok=true

  for required in README.md workflow.md env-fallback.sh env-teams.sh tolerance.json expected-equivalence.json; do
    if [ ! -f "$fixture_dir/$required" ]; then
      _fail "$fixture_id: missing $required" "every parity fixture must provide $required"
      ok=false
    fi
  done

  if [ "$ok" = "true" ]; then
    _pass "$fixture_id: fixture structure complete"
  fi

  # Validate tolerance.json + expected-equivalence.json are well-formed JSON
  if [ -f "$fixture_dir/tolerance.json" ]; then
    if jq empty "$fixture_dir/tolerance.json" 2>/dev/null; then
      _pass "$fixture_id: tolerance.json parses"
    else
      _fail "$fixture_id: tolerance.json invalid JSON"
    fi
  fi
  if [ -f "$fixture_dir/expected-equivalence.json" ]; then
    if jq empty "$fixture_dir/expected-equivalence.json" 2>/dev/null; then
      _pass "$fixture_id: expected-equivalence.json parses"
    else
      _fail "$fixture_id: expected-equivalence.json invalid JSON"
    fi
  fi
}

# ---------------------------------------------------------------------------
# Live mode: run claude -p twice and compare outcomes
# ---------------------------------------------------------------------------
run_fixture_live() {
  local fixture_dir="$1"
  local fixture_id
  fixture_id="$(basename "$fixture_dir")"

  if ! command -v "$CLAUDE_BIN" >/dev/null 2>&1; then
    _skip "$fixture_id: live mode" "$CLAUDE_BIN not on PATH"
    return
  fi

  # NOTE: The full live execution is intentionally NOT implemented in this
  # initial scaffold. It requires:
  #
  #   1. A tmpdir per run with the fixture's workflow.md copied in
  #   2. Sourcing env-fallback.sh OR env-teams.sh to set/unset
  #      CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS
  #   3. Invoking claude -p --max-budget-usd "$L8_FIXTURE_BUDGET_USD" with
  #      a prompt that loads the speckit-pro plugin and runs
  #      /speckit-pro:autopilot path/to/workflow.md
  #   4. Capturing the produced artifacts (spec.md, plan.md, tasks.md,
  #      workflow.md final state)
  #   5. Diffing per expected-equivalence.json with tolerance.json
  #
  # This is deferred until the runner has been reviewed and the LLM
  # token budget is approved. Implementation belongs in a follow-up PR.
  _skip "$fixture_id: live mode" "live execution not yet implemented — see TODO in script"
}

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
printf "Layer 8: Parity Fixtures (mode=%s)\n" "$MODE"
printf "%s\n" "────────────────────────────────────────"

shopt -s nullglob
for fixture_dir in "$SCRIPT_DIR"/*/; do
  fixture_dir="${fixture_dir%/}"
  fixture_id="$(basename "$fixture_dir")"

  # Skip helper dirs (lib, etc.) — they don't have README.md OR they're not parity fixtures
  if [ ! -f "$fixture_dir/README.md" ]; then
    continue
  fi

  if [ -n "$FIXTURE_FILTER" ] && [ "$fixture_id" != "$FIXTURE_FILTER" ]; then
    continue
  fi

  printf "\n%s\n" "$fixture_id"
  validate_fixture_structure "$fixture_dir"
  if [ "$MODE" = "live" ]; then
    run_fixture_live "$fixture_dir"
  fi
done

printf "\n%s\n" "════════════════════════════════════════"
printf "Layer 8 (parity): %d passed, %d failed, %d skipped\n" \
  "$PASS_COUNT" "$FAIL_COUNT" "$SKIP_COUNT"

if [ "$FAIL_COUNT" -gt 0 ]; then
  exit 1
fi
exit 0
