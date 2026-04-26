#!/usr/bin/env bash
# test-install-codex-agents.sh — Regression tests for the Codex subagent installer
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$PLUGIN_ROOT/codex-skills/install/scripts/install-codex-agents.sh"

EXPECTED_AGENTS=(
  autopilot-fast-helper.toml
  phase-executor.toml
  clarify-executor.toml
  checklist-executor.toml
  analyze-executor.toml
  implement-executor.toml
  codebase-analyst.toml
  spec-context-analyst.toml
  domain-researcher.toml
)

TMP_ROOT=$(mktemp -d)
trap 'rm -rf "$TMP_ROOT"' EXIT

DEST_DIR="$TMP_ROOT/codex-agents-dest"

section "Installer script shape"

set_test "installer script exists"
assert_file_exists "$SCRIPT"

set_test "installer script is executable"
assert_file_executable "$SCRIPT"

section "Fresh install"

set_test "installer succeeds on empty destination"
result=0
output=$("$SCRIPT" "$DEST_DIR" 2>&1) || result=$?
assert_eq "0" "$result" "exit code"

set_test "installer output reports destination"
assert_contains "$output" "Destination: $DEST_DIR"

set_test "installer output requests Codex restart"
assert_contains "$output" "Restart Codex now"

set_test "installer output reports GPT-5.5 tiered model policy"
assert_contains "$output" "Model policy: GPT-5.5"

for agent in "${EXPECTED_AGENTS[@]}"; do
  set_test "fresh install copied ${agent}"
  assert_file_exists "$DEST_DIR/$agent"
done

section "Refresh install"

printf 'stale\n' > "$DEST_DIR/analyze-executor.toml"
printf 'unrelated\n' > "$DEST_DIR/custom-user-agent.toml"

set_test "refresh install succeeds on existing destination"
result=0
output=$("$SCRIPT" "$DEST_DIR" 2>&1) || result=$?
assert_eq "0" "$result" "exit code"

refreshed_content=$(cat "$DEST_DIR/analyze-executor.toml")
set_test "refresh install overwrites same-named SpecKit files"
assert_contains "$refreshed_content" 'name = "analyze-executor"'

set_test "refresh install preserves unrelated user files"
assert_file_exists "$DEST_DIR/custom-user-agent.toml"

test_summary
