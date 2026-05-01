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

GPT55_AGENTS=(
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

set_test "installer output reports gpt-5.5 tiered model policy"
assert_contains "$output" "Model policy: gpt-5.5"

set_test "installer output reports effective default model"
assert_contains "$output" "Executor/consensus model: gpt-5.5"

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

section "Fallback install"

FALLBACK_DEST_DIR="$TMP_ROOT/codex-agents-fallback"

set_test "fallback install succeeds with --model gpt-5.4"
result=0
output=$("$SCRIPT" "$FALLBACK_DEST_DIR" --model gpt-5.4 2>&1) || result=$?
assert_eq "0" "$result" "exit code"

set_test "fallback install reports gpt-5.4 model"
assert_contains "$output" "Executor/consensus model: gpt-5.4"

set_test "fallback install reports rewritten templates"
assert_contains "$output" "Fallback mode: installed templates were rewritten"

for agent in "${GPT55_AGENTS[@]}"; do
  content=$(cat "$FALLBACK_DEST_DIR/$agent")
  set_test "fallback install rewrites ${agent} to gpt-5.4"
  assert_contains "$content" 'model = "gpt-5.4"'
done

phase_content=$(cat "$FALLBACK_DEST_DIR/phase-executor.toml")
set_test "fallback install rewrites phase-executor to gpt-5.4"
assert_contains "$phase_content" 'model = "gpt-5.4"'

spark_content=$(cat "$FALLBACK_DEST_DIR/autopilot-fast-helper.toml")
set_test "fallback install preserves Spark helper model"
assert_contains "$spark_content" 'model = "gpt-5.3-codex-spark"'

set_test "installer rejects unsupported model"
result=0
output=$("$SCRIPT" "$TMP_ROOT/bad-model" --model gpt-5.5-pro 2>&1) || result=$?
assert_eq "2" "$result" "exit code"

test_summary
