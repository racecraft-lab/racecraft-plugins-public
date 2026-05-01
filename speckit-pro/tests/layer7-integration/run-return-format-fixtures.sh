#!/usr/bin/env bash
# run-return-format-fixtures.sh — Layer 7 Class 2 fixture runner
#
# Class 2 fixtures verify CROSS-AGENT PARSING — that one agent's
# response format is parseable by another agent that consumes it. The
# canonical case is the synthesizer reading analyst markdown and
# emitting a decision artifact.
#
# Modes match Class 1: --replay (default, parser regression) and
# --live (real cross-agent execution, costs LLM tokens).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LIB="$SCRIPT_DIR/lib/transcript-helpers.sh"
FIXTURES_DIR="$SCRIPT_DIR/return-format-fixtures"

# shellcheck disable=SC1091
source "$TESTS_ROOT/lib/assertions.sh"
# shellcheck disable=SC1090
source "$LIB"

MODE="replay"
SELECTED=""
BUDGET_USD="${RETURN_FORMAT_FIXTURE_BUDGET_USD:-1.00}"

while [ $# -gt 0 ]; do
  case "$1" in
    --replay) MODE="replay"; shift ;;
    --live)   MODE="live"; shift ;;
    -h|--help) sed -n '2,12p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) SELECTED="$1"; shift ;;
  esac
done

collect_fixtures() {
  if [ -n "$SELECTED" ]; then
    [ -d "$FIXTURES_DIR/$SELECTED" ] || { echo "ERROR: fixture $SELECTED not found" >&2; exit 2; }
    printf '%s\n' "$FIXTURES_DIR/$SELECTED"
  else
    find "$FIXTURES_DIR" -mindepth 1 -maxdepth 1 -type d | sort
  fi
}

capture_live() {
  local fixture_dir="$1"
  local transcript_file="$fixture_dir/transcript.jsonl"
  if ! command -v claude >/dev/null 2>&1; then
    printf "  SKIP (claude CLI not found)\n"; return 2
  fi
  printf "  Capturing live transcript (budget: \$%s)...\n" "$BUDGET_USD"
  if ! claude -p \
      --output-format stream-json \
      --include-partial-messages \
      --verbose \
      --max-budget-usd "$BUDGET_USD" \
      --no-session-persistence \
      < "$fixture_dir/prompt.txt" > "$transcript_file" 2>/dev/null; then
    printf "  WARN: claude -p exited non-zero — partial transcript may have been captured\n"
  fi
  # Scrub PII (cwd paths, sessionId, plugin inventories) immediately.
  if [ -s "$transcript_file" ]; then
    bash "$SCRIPT_DIR/scrub-transcript.sh" "$transcript_file" >/dev/null
  fi
}

assert_response_contains_any() {
  local transcript="$1" target="$2"; shift 2
  local content
  content=$(get_response_content "$transcript" "$target")
  for needle in "$@"; do
    if [[ "$content" == *"$needle"* ]]; then return 0; fi
  done
  return 1
}

# case-insensitive section-keyword check
assert_response_contains_keyword_ci() {
  local transcript="$1" target="$2" needle="$3"
  local content lower
  content=$(get_response_content "$transcript" "$target")
  lower=$(printf '%s' "$content" | tr '[:upper:]' '[:lower:]')
  needle=$(printf '%s' "$needle" | tr '[:upper:]' '[:lower:]')
  [[ "$lower" == *"$needle"* ]]
}

assert_fixture() {
  local fixture_dir="$1"
  local fixture_id; fixture_id=$(basename "$fixture_dir")
  local expected="$fixture_dir/expected.json"
  local transcript="$fixture_dir/transcript.jsonl"

  [ -f "$expected" ] || { set_test "$fixture_id: expected.json"; _fail "missing"; return; }
  if [ ! -f "$transcript" ]; then
    if [ "$MODE" = "replay" ]; then
      printf "  ${YELLOW}SKIP${RESET} %s: no transcript.jsonl committed\n" "$fixture_id"
      return
    else
      set_test "$fixture_id: transcript captured"; _fail "no transcript"; return
    fi
  fi

  while read -r target; do
    [ -z "$target" ] && continue
    set_test "$fixture_id: dispatched to $target"
    if assert_dispatched_to "$transcript" "$target"; then _pass; else
      _fail "expected dispatch to $target"
    fi
  done < <(jq -r '.must_dispatch_to[]? // empty' "$expected")

  if jq -e '.must_not_have_forbidden_spawns == true' "$expected" >/dev/null 2>&1; then
    set_test "$fixture_id: no subagent spawned an Agent()"
    if assert_no_forbidden_spawns "$transcript"; then _pass; else
      _fail "found subagent spawning Agent"
    fi
  fi

  # must_not_invoke_skill — HITL boundary check (grill-me is a Skill).
  while read -r pattern; do
    [ -z "$pattern" ] && continue
    set_test "$fixture_id: skill never invoked: $pattern (any scope)"
    if assert_skill_not_invoked "$transcript" "$pattern"; then
      _pass
    else
      _fail "skill matching '$pattern' was invoked"
    fi
  done < <(jq -r '.must_not_invoke_skill[]? // empty' "$expected")

  # response_assertions: each is {subagent_type, must_contain_any?, must_contain_section_keywords?}
  local len
  len=$(jq -r '.response_assertions | length // 0' "$expected")
  for ((i=0; i<len; i++)); do
    local sa; sa=$(jq -r ".response_assertions[$i].subagent_type" "$expected")

    if jq -e ".response_assertions[$i].must_contain_any" "$expected" >/dev/null 2>&1; then
      set_test "$fixture_id: $sa response contains any of allowed substrings"
      mapfile -t needles < <(jq -r ".response_assertions[$i].must_contain_any[]" "$expected")
      if assert_response_contains_any "$transcript" "$sa" "${needles[@]}"; then
        _pass
      else
        _fail "none of the expected substrings found in $sa response"
      fi
    fi

    if jq -e ".response_assertions[$i].must_contain_section_keywords" "$expected" >/dev/null 2>&1; then
      mapfile -t kws < <(jq -r ".response_assertions[$i].must_contain_section_keywords[]" "$expected")
      for kw in "${kws[@]}"; do
        set_test "$fixture_id: $sa response contains section keyword '$kw'"
        if assert_response_contains_keyword_ci "$transcript" "$sa" "$kw"; then
          _pass
        else
          _fail "missing keyword '$kw' in $sa response"
        fi
      done
    fi
  done
}

section "Layer 7 Class 2: Return-Format Fixtures (mode: $MODE)"

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
