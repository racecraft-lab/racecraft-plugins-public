#!/usr/bin/env bash
# validate-plugin.sh — Structural validation for .claude-plugin/plugin.json
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

PLUGIN_JSON="$PLUGIN_ROOT/.claude-plugin/plugin.json"

section "plugin.json — File Existence"

set_test "plugin.json exists"
assert_file_exists "$PLUGIN_JSON"

section "plugin.json — Valid JSON"

set_test "plugin.json is valid JSON"
if python3 -m json.tool "$PLUGIN_JSON" >/dev/null 2>&1; then
  _pass
else
  _fail "plugin.json is not valid JSON"
fi

CONTENT=$(cat "$PLUGIN_JSON")

section "plugin.json — Required Fields"

set_test "name field exists"
assert_json_field_exists "$CONTENT" "name"

set_test "name matches speckit-pro"
assert_json_field "$CONTENT" "name" "speckit-pro"

set_test "name is kebab-case"
name_val=$(printf '%s' "$CONTENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['name'])" 2>/dev/null)
assert_match "$name_val" '^[a-z][a-z0-9]*(-[a-z0-9]+)*$' "name must be kebab-case"

set_test "version field exists and is semver"
version_val=$(printf '%s' "$CONTENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])" 2>/dev/null)
assert_match "$version_val" '^[0-9]+\.[0-9]+\.[0-9]+$' "version must be X.Y.Z"

set_test "description field exists and is non-empty"
desc_val=$(printf '%s' "$CONTENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['description'])" 2>/dev/null)
if [ -n "$desc_val" ]; then
  _pass
else
  _fail "description is empty"
fi

set_test "author field exists"
assert_json_field_exists "$CONTENT" "author"

test_summary
