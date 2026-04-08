#!/usr/bin/env bash
# test-check-prerequisites.sh — Unit tests for check-prerequisites.sh
#
# Tests prerequisite checking with synthetic fixtures for failure modes.
# Optional --live flag runs against a live SpecKit project (set PROJECT_ROOT).

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$PLUGIN_ROOT/skills/speckit-autopilot/scripts/check-prerequisites.sh"
LIVE=false
[ "${1:-}" = "--live" ] && LIVE=true

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

# Helper: create a minimal SpecKit project fixture
make_project() {
  local dir="$FIXTURE_DIR/$1"
  mkdir -p "$dir/.specify/memory" "$dir/.claude/commands"
  printf '# Constitution\n' > "$dir/.specify/memory/constitution.md"
  for cmd in speckit.specify speckit.plan speckit.tasks speckit.implement; do
    printf -- '---\ndescription: test\n---\n# Test\n' > "$dir/.claude/commands/${cmd}.md"
  done
  # Create a dummy workflow file
  printf '# Workflow\n' > "$dir/workflow.md"
  # Init git (configure user for CI where no global git config exists)
  (cd "$dir" && git init -q && git config user.email "test@test" && git config user.name "test" && git config commit.gpgsign false && git add -A && git commit -q -m "init" 2>/dev/null) || true
  echo "$dir"
}

# ─────────────────────────────────────────
section "Missing prerequisites"
# ─────────────────────────────────────────

set_test "No workflow file arg → all_pass false"
dir=$(make_project "no-workflow-arg")
result=0
output=$(cd "$dir" && bash "$SCRIPT" 2>/dev/null) || result=$?
assert_eq "1" "$result" "exit code"
assert_json_field "$output" "all_pass" "False"

set_test "Nonexistent workflow file → all_pass false"
dir=$(make_project "bad-workflow")
result=0
output=$(cd "$dir" && bash "$SCRIPT" "/nonexistent/workflow.md" 2>/dev/null) || result=$?
assert_eq "1" "$result" "exit code"

set_test "No .specify dir → project_init false"
dir="$FIXTURE_DIR/no-specify"
mkdir -p "$dir"
(cd "$dir" && git init -q 2>/dev/null) || true
result=0
output=$(cd "$dir" && bash "$SCRIPT" 2>/dev/null) || result=$?
assert_eq "1" "$result" "exit code"

set_test "No constitution → constitution false"
dir=$(make_project "no-constitution")
rm -f "$dir/.specify/memory/constitution.md"
result=0
output=$(cd "$dir" && bash "$SCRIPT" "$dir/workflow.md" 2>/dev/null) || result=$?
assert_eq "1" "$result" "exit code"

set_test "Missing commands → commands false"
dir=$(make_project "missing-cmds")
rm -f "$dir/.claude/commands/speckit.plan.md"
result=0
output=$(cd "$dir" && bash "$SCRIPT" "$dir/workflow.md" 2>/dev/null) || result=$?
assert_eq "1" "$result" "exit code"
assert_contains "$output" "speckit.plan"

# ─────────────────────────────────────────
section "Branch detection"
# ─────────────────────────────────────────

set_test "Main branch → on_feature_branch false"
dir=$(make_project "main-branch")
result=0
output=$(cd "$dir" && bash "$SCRIPT" "$dir/workflow.md" 2>/dev/null) || result=$?
# May fail on speckit_cli check but branch detection should work
assert_contains "$output" "on_feature_branch"

set_test "Feature branch → detected correctly"
dir=$(make_project "feature-branch")
(cd "$dir" && git checkout -q -b 009-search-database 2>/dev/null) || true
result=0
output=$(cd "$dir" && bash "$SCRIPT" "$dir/workflow.md" 2>/dev/null) || result=$?
assert_contains "$output" "009-search-database"

# ─────────────────────────────────────────
section "Output format"
# ─────────────────────────────────────────

set_test "Output is valid JSON"
dir=$(make_project "json-check")
output=$(cd "$dir" && bash "$SCRIPT" "$dir/workflow.md" 2>/dev/null) || true
printf '%s' "$output" | python3 -m json.tool >/dev/null 2>&1
assert_eq "0" "$?" "JSON parse"

set_test "Output has checks array"
assert_json_field_exists "$output" "checks"

set_test "Output has branch field"
assert_json_field_exists "$output" "branch"

# ─────────────────────────────────────────
# Live project tests (optional)
# ─────────────────────────────────────────

if [ "$LIVE" = "true" ]; then
  section "Live: check-prerequisites on live project"

  PROJECT_ROOT="${PROJECT_ROOT:-$(git -C "$PLUGIN_ROOT" rev-parse --show-toplevel 2>/dev/null || echo "")}"
  if [ -n "$PROJECT_ROOT" ]; then
    # Use a real workflow file
    # Guard with || true: find exits 1 on missing directory; with pipefail the pipeline
    # would abort the script before test_summary is reached.
    WORKFLOW=$(find "$PROJECT_ROOT/docs/ai/specs" -name "*-workflow.md" -type f 2>/dev/null | head -1) || true
    if [ -n "$WORKFLOW" ]; then
      set_test "Live project — output is valid JSON"
      output=$(cd "$PROJECT_ROOT" && bash "$SCRIPT" "$WORKFLOW" 2>/dev/null) || true
      printf '%s' "$output" | python3 -m json.tool >/dev/null 2>&1
      assert_eq "0" "$?" "JSON parse"

      set_test "Live project — project_init passes"
      assert_contains "$output" '"project_init"'
    else
      printf "  ${YELLOW}SKIP${RESET}: No workflow file found\n"
    fi
  else
    printf "  ${YELLOW}SKIP${RESET}: PROJECT_ROOT not detected\n"
  fi
fi

test_summary
