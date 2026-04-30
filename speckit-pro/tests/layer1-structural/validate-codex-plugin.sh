#!/usr/bin/env bash
# validate-codex-plugin.sh — Structural validation for .codex-plugin/plugin.json
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

CODEX_JSON="$PLUGIN_ROOT/.codex-plugin/plugin.json"

section ".codex-plugin/plugin.json — File Existence"

set_test ".codex-plugin/plugin.json exists"
assert_file_exists "$CODEX_JSON"

section ".codex-plugin/plugin.json — Valid JSON"

set_test ".codex-plugin/plugin.json is valid JSON"
if python3 -m json.tool "$CODEX_JSON" >/dev/null 2>&1; then
  _pass
else
  _fail ".codex-plugin/plugin.json is not valid JSON"
fi

CONTENT=$(cat "$CODEX_JSON")
REQUIRED_SKILLS=(speckit-autopilot speckit-coach speckit-setup speckit-status speckit-resolve-pr install grill-me)

section ".codex-plugin/plugin.json — Required Fields"

set_test "name field exists"
assert_json_field_exists "$CONTENT" "name"

set_test "name matches speckit-pro"
assert_json_field "$CONTENT" "name" "speckit-pro"

set_test "version is semver X.Y.Z"
version_val=$(printf '%s' "$CONTENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])" 2>/dev/null)
assert_match "$version_val" '^[0-9]+\.[0-9]+\.[0-9]+$' "version must be X.Y.Z"

set_test "description is non-empty"
desc_val=$(printf '%s' "$CONTENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['description'])" 2>/dev/null)
if [ -n "$desc_val" ]; then
  _pass
else
  _fail "description is empty"
fi

set_test "homepage field exists"
assert_json_field_exists "$CONTENT" "homepage"

set_test "skills field equals ./codex-skills/"
assert_json_field "$CONTENT" "skills" "./codex-skills/"

set_test "interface.displayName exists"
assert_json_field_exists "$CONTENT" "interface.displayName"

set_test "interface.category exists"
assert_json_field_exists "$CONTENT" "interface.category"

set_test "interface.defaultPrompt exists"
assert_json_field_exists "$CONTENT" "interface.defaultPrompt"

section ".codex-plugin — Directory Structure"

set_test "codex-skills/ directory exists"
if [ -d "$PLUGIN_ROOT/codex-skills" ]; then
  _pass
else
  _fail "codex-skills/ directory not found at $PLUGIN_ROOT/codex-skills"
fi

for skill in "${REQUIRED_SKILLS[@]}"; do
  set_test "codex-skills/$skill/ directory exists"
  if [ -d "$PLUGIN_ROOT/codex-skills/$skill" ]; then
    _pass
  else
    _fail "codex-skills/$skill/ directory not found"
  fi

  set_test "codex-skills/$skill/SKILL.md exists"
  assert_file_exists "$PLUGIN_ROOT/codex-skills/$skill/SKILL.md"
done

section ".codex-plugin/plugin.json — Version Consistency"

set_test "version matches .claude-plugin/plugin.json"
claude_json="$PLUGIN_ROOT/.claude-plugin/plugin.json"
if [ -f "$claude_json" ]; then
  claude_version=$(python3 -c "import json; print(json.load(open('$claude_json'))['version'])" 2>/dev/null)
  codex_version=$(printf '%s' "$CONTENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])" 2>/dev/null)
  if [ "$claude_version" = "$codex_version" ]; then
    _pass
  else
    _fail "version mismatch: .claude-plugin/plugin.json='$claude_version', .codex-plugin/plugin.json='$codex_version'"
  fi
else
  _fail ".claude-plugin/plugin.json not found — cannot compare versions"
fi

test_summary
