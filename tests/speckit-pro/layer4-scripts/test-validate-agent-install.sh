#!/usr/bin/env bash
# test-validate-agent-install.sh - Regression tests for runtime agent completeness checks.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"
SCRIPT="$PLUGIN_ROOT/skills/speckit-autopilot/scripts/validate-agent-install.sh"

TMP_ROOT=$(mktemp -d)
trap 'rm -rf "$TMP_ROOT"' EXIT

section "Validator script shape"

set_test "validator script exists"
assert_file_exists "$SCRIPT"

set_test "validator script is executable"
assert_file_executable "$SCRIPT"

section "Claude package completeness"

set_test "source Claude package contains every bundled agent"
result=0
output=$("$SCRIPT" --surface claude --plugin-root "$PLUGIN_ROOT" 2>&1) || result=$?
assert_eq "0" "$result" "exit code"

set_test "Claude package reports eleven bundled agents"
assert_contains "$output" "11 bundled agents"

claude_bad="$TMP_ROOT/claude-bad"
mkdir -p "$claude_bad/agents"
cp "$PLUGIN_ROOT"/agents/*.md "$claude_bad/agents/"
rm "$claude_bad/agents/uat-runbook-author.md"

set_test "Claude package check fails when a bundled agent is missing"
result=0
output=$("$SCRIPT" --surface claude --plugin-root "$claude_bad" 2>&1) || result=$?
assert_eq "1" "$result" "exit code"

set_test "Claude missing-agent output names the missing agent"
assert_contains "$output" "uat-runbook-author.md"

section "Codex runtime completeness"

codex_dest="$TMP_ROOT/codex-agents"
mkdir -p "$codex_dest"
cp "$PLUGIN_ROOT"/codex-agents/*.toml "$codex_dest/"

set_test "Codex runtime check passes with every bundled TOML installed"
result=0
output=$("$SCRIPT" --surface codex --plugin-root "$PLUGIN_ROOT" --dest "$codex_dest" 2>&1) || result=$?
assert_eq "0" "$result" "exit code"

set_test "Codex runtime reports ten bundled agents"
assert_contains "$output" "10 bundled agents"

rm "$codex_dest/uat-runbook-author.toml"

set_test "Codex runtime check fails when UAT author is missing"
result=0
output=$("$SCRIPT" --surface codex --plugin-root "$PLUGIN_ROOT" --dest "$codex_dest" 2>&1) || result=$?
assert_eq "1" "$result" "exit code"

set_test "Codex missing-agent output names the missing TOML"
assert_contains "$output" "uat-runbook-author.toml"

set_test "Codex autoheal restores missing bundled agents"
result=0
output=$(SPECKIT_SKIP_PLUGIN_SYNC=1 "$SCRIPT" --surface codex --plugin-root "$PLUGIN_ROOT" --dest "$codex_dest" --autoheal 2>&1) || result=$?
assert_eq "0" "$result" "exit code"

set_test "Codex autoheal restored uat-runbook-author"
assert_file_exists "$codex_dest/uat-runbook-author.toml"

test_summary
