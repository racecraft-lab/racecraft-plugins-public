#!/usr/bin/env bash
# validate-codex-marketplace.sh — Structural validation for .agents/plugins/marketplace.json
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REPO_ROOT="$(cd "$PLUGIN_ROOT/.." && pwd)"

MARKETPLACE_JSON="$REPO_ROOT/.agents/plugins/marketplace.json"

section ".agents/plugins/marketplace.json — File Existence"

set_test ".agents/plugins/marketplace.json exists"
assert_file_exists "$MARKETPLACE_JSON"

section ".agents/plugins/marketplace.json — Valid JSON"

set_test ".agents/plugins/marketplace.json is valid JSON"
if python3 -m json.tool "$MARKETPLACE_JSON" >/dev/null 2>&1; then
  _pass
else
  _fail ".agents/plugins/marketplace.json is not valid JSON"
fi

CONTENT=$(cat "$MARKETPLACE_JSON")

section ".agents/plugins/marketplace.json — Required Fields"

set_test "name field exists"
assert_json_field_exists "$CONTENT" "name"

set_test "plugins array exists"
if printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
plugins = data['plugins']
assert isinstance(plugins, list), 'plugins must be an array'
" 2>/dev/null; then
  _pass
else
  _fail "plugins field is missing or not an array"
fi

set_test "first plugin name is speckit-pro"
first_name=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['plugins'][0]['name'])
" 2>/dev/null)
if [ "$first_name" = "speckit-pro" ]; then
  _pass
else
  _fail "expected first plugin name 'speckit-pro', got '$first_name'"
fi

section ".agents/plugins/marketplace.json — Source Path"

set_test "source.path resolves to existing directory"
source_path=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['plugins'][0]['source']['path'])
" 2>/dev/null)
resolved_path="$REPO_ROOT/$source_path"
# Strip leading ./ if present so path resolution works correctly
resolved_path=$(python3 -c "
import os
print(os.path.normpath('$resolved_path'))
" 2>/dev/null)
if [ -d "$resolved_path" ]; then
  _pass
else
  _fail "source.path '$source_path' does not resolve to an existing directory (checked: $resolved_path)"
fi

section ".agents/plugins/marketplace.json — Policy"

set_test "policy.installation field exists"
if printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
val = data['plugins'][0]['policy']['installation']
assert val, 'policy.installation must not be empty'
" 2>/dev/null; then
  _pass
else
  _fail "policy.installation field is missing or empty"
fi

test_summary
