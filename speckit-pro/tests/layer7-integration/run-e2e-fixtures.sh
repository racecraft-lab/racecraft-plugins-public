#!/usr/bin/env bash
# run-e2e-fixtures.sh — Layer 7 Class 3 (end-to-end) fixture runner
#
# Two modes:
#   --replay (default): parses committed transcript.jsonl and asserts.
#                       Free, fast, deterministic. Catches PARSER drift,
#                       NOT routing drift.
#   --live:             invokes claude -p, captures transcript, then
#                       asserts. Costs real LLM tokens. Catches ROUTING
#                       drift in the orchestrator.
#
# Usage:
#   bash run-e2e-fixtures.sh                              # all e2e fixtures, replay
#   bash run-e2e-fixtures.sh 01-autopilot-minimal-smoke   # one fixture, replay
#   bash run-e2e-fixtures.sh --live                       # all e2e fixtures, live
#   bash run-e2e-fixtures.sh --live 02-autopilot-extended-pipeline
#
# Cost guard: --live wraps each invocation with --max-budget-usd 10.00 by
# default (Class 3 fixtures are full-pipeline runs and need more budget
# than Class 1's $1 default). Override via E2E_FIXTURE_BUDGET_USD env var.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGIN_ROOT="$(cd "$TESTS_ROOT/.." && pwd)"
LIB="$SCRIPT_DIR/lib/transcript-helpers.sh"
FIXTURES_DIR="$SCRIPT_DIR/e2e-fixtures"

# shellcheck disable=SC1091
source "$TESTS_ROOT/lib/assertions.sh"
# shellcheck disable=SC1090
source "$LIB"

MODE="replay"
SELECTED=""
BUDGET_USD="${E2E_FIXTURE_BUDGET_USD:-10.00}"

while [ $# -gt 0 ]; do
  case "$1" in
    --replay) MODE="replay"; shift ;;
    --live)   MODE="live"; shift ;;
    -h|--help)
      sed -n '2,20p' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *) SELECTED="$1"; shift ;;
  esac
done

# ── Helpers ──────────────────────────────────────────────────────────────

# Resolve the list of fixture directories to run.
collect_fixtures() {
  if [ -n "$SELECTED" ]; then
    if [ -d "$FIXTURES_DIR/$SELECTED" ]; then
      printf '%s\n' "$FIXTURES_DIR/$SELECTED"
    else
      printf "ERROR: fixture not found: %s\n" "$SELECTED" >&2
      exit 2
    fi
  else
    find "$FIXTURES_DIR" -mindepth 1 -maxdepth 1 -type d | sort
  fi
}

# Run claude -p for one fixture, capture transcript, then scrub PII.
capture_live() {
  local fixture_dir="$1"
  local prompt_file="$fixture_dir/prompt.txt"
  local transcript_file="$fixture_dir/transcript.jsonl"

  if ! command -v claude >/dev/null 2>&1; then
    printf "  SKIP (claude CLI not found)\n"
    return 2
  fi

  printf "  Capturing live transcript (budget: \$%s)...\n" "$BUDGET_USD"
  if ! claude -p \
    --output-format stream-json \
    --include-partial-messages \
    --verbose \
    --max-budget-usd "$BUDGET_USD" \
    --no-session-persistence \
    < "$prompt_file" > "$transcript_file" 2>/dev/null; then
    printf "  WARN: claude -p exited non-zero — partial transcript may have been captured\n"
  fi
  # Scrub PII (cwd paths, sessionId, plugin inventories) immediately.
  if [ -s "$transcript_file" ]; then
    bash "$SCRIPT_DIR/scrub-transcript.sh" "$transcript_file" >/dev/null
  fi
  printf "  Saved scrubbed transcript to %s\n" "$transcript_file"
}

# Run all assertions in expected.json against transcript.jsonl.
assert_fixture() {
  local fixture_dir="$1"
  local fixture_id
  fixture_id=$(basename "$fixture_dir")
  local expected="$fixture_dir/expected.json"
  local transcript="$fixture_dir/transcript.jsonl"

  if [ ! -f "$expected" ]; then
    set_test "$fixture_id: expected.json present"
    _fail "missing $expected"
    return
  fi
  if [ ! -f "$transcript" ]; then
    if [ "$MODE" = "replay" ]; then
      printf "  ${YELLOW}SKIP${RESET} %s: no transcript.jsonl committed (run with --live to capture)\n" "$fixture_id"
      return
    else
      set_test "$fixture_id: transcript.jsonl produced by --live"
      _fail "no transcript captured"
      return
    fi
  fi

  # must_dispatch_to: every type must appear at least once
  while read -r target; do
    [ -z "$target" ] && continue
    set_test "$fixture_id: dispatched to $target"
    if assert_dispatched_to "$transcript" "$target"; then
      _pass
    else
      _fail "expected dispatch to $target, none found"
    fi
  done < <(jq -r '.must_dispatch_to[]? // empty' "$expected")

  # must_dispatch_to_at_least_one_of: at least one must appear
  if jq -e '.must_dispatch_to_at_least_one_of' "$expected" >/dev/null 2>&1; then
    set_test "$fixture_id: dispatched to at least one of allowed set"
    local found=false
    while read -r target; do
      [ -z "$target" ] && continue
      if assert_dispatched_to "$transcript" "$target"; then
        found=true
        break
      fi
    done < <(jq -r '.must_dispatch_to_at_least_one_of[]?' "$expected")
    if [ "$found" = "true" ]; then _pass; else
      _fail "expected dispatch to at least one of must_dispatch_to_at_least_one_of"
    fi
  fi

  # must_not_dispatch_to: each type must never appear
  while read -r target; do
    [ -z "$target" ] && continue
    set_test "$fixture_id: never dispatched to $target"
    if assert_not_dispatched_to "$transcript" "$target"; then
      _pass
    else
      _fail "$target was dispatched but should not have been"
    fi
  done < <(jq -r '.must_not_dispatch_to[]? // empty' "$expected")

  # must_not_have_forbidden_spawns
  if jq -e '.must_not_have_forbidden_spawns == true' "$expected" >/dev/null 2>&1; then
    set_test "$fixture_id: no subagent spawned an Agent()"
    if assert_no_forbidden_spawns "$transcript"; then
      _pass
    else
      _fail "found subagent that spawned another Agent — forbidden"
    fi
  fi

  # must_not_invoke_skill: array of regex patterns (case-insensitive).
  # HITL boundary check — grill-me is a SKILL, not an Agent subagent_type.
  while read -r pattern; do
    [ -z "$pattern" ] && continue
    set_test "$fixture_id: skill never invoked: $pattern (any scope)"
    if assert_skill_not_invoked "$transcript" "$pattern"; then
      _pass
    else
      _fail "skill matching '$pattern' was invoked at orchestrator or sidechain scope"
    fi
  done < <(jq -r '.must_not_invoke_skill[]? // empty' "$expected")

  # min/max dispatch count
  local total
  total=$(extract_orchestrator_dispatches "$transcript" | jq 'length')
  if jq -e '.min_dispatch_count' "$expected" >/dev/null 2>&1; then
    local min_n
    min_n=$(jq -r '.min_dispatch_count' "$expected")
    set_test "$fixture_id: dispatch count >= $min_n (got $total)"
    if [ "$total" -ge "$min_n" ]; then _pass; else
      _fail "expected >= $min_n, got $total"
    fi
  fi
  if jq -e '.max_dispatch_count' "$expected" >/dev/null 2>&1; then
    local max_n
    max_n=$(jq -r '.max_dispatch_count' "$expected")
    set_test "$fixture_id: dispatch count <= $max_n (got $total)"
    if [ "$total" -le "$max_n" ]; then _pass; else
      _fail "expected <= $max_n, got $total"
    fi
  fi

  # dispatch_order_constraints: before must precede after in dispatch order
  if jq -e '.dispatch_order_constraints' "$expected" >/dev/null 2>&1; then
    local order
    order=$(extract_dispatch_order "$transcript")
    while IFS=$'\t' read -r before after; do
      [ -z "$before" ] && continue
      set_test "$fixture_id: $before precedes $after"
      local before_idx after_idx
      before_idx=$(printf '%s\n' "$order" | grep -n -m1 -F "$before" | cut -d: -f1 || true)
      after_idx=$(printf '%s\n' "$order" | grep -n -m1 -F "$after" | cut -d: -f1 || true)
      if [ -n "$before_idx" ] && [ -n "$after_idx" ] && [ "$before_idx" -lt "$after_idx" ]; then
        _pass
      else
        _fail "order constraint violated (before_idx=$before_idx after_idx=$after_idx)"
      fi
    done < <(jq -r '.dispatch_order_constraints[]? | "\(.before)\t\(.after)"' "$expected")
  fi
}

# ── Main ─────────────────────────────────────────────────────────────────

section "Layer 7 Class 3: End-to-End Fixtures (mode: $MODE)"

if [ "$MODE" = "live" ] && [ -z "${ANTHROPIC_API_KEY:-}" ] && [ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
  printf "${YELLOW}NOTE${RESET}: --live requires claude -p with auth configured.\n"
fi

while read -r fixture_dir; do
  [ -z "$fixture_dir" ] && continue
  fixture_id=$(basename "$fixture_dir")
  printf "\n${BOLD}Fixture: %s${RESET}\n" "$fixture_id"
  if [ "$MODE" = "live" ]; then
    capture_live "$fixture_dir" || true
  fi
  assert_fixture "$fixture_dir"
done < <(collect_fixtures)

test_summary
