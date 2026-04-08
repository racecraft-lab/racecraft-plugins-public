#!/usr/bin/env bash
# validate-codex-hooks.sh — Structural validation for codex-hooks.json
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

HOOKS_FILE="$PLUGIN_ROOT/codex-hooks.json"

section "codex-hooks.json — File Existence"

set_test "codex-hooks.json exists"
assert_file_exists "$HOOKS_FILE"

if [ ! -f "$HOOKS_FILE" ]; then
  test_summary
  exit
fi

section "codex-hooks.json — Valid JSON"

set_test "codex-hooks.json is valid JSON"
if python3 -m json.tool "$HOOKS_FILE" >/dev/null 2>&1; then
  _pass
else
  _fail "codex-hooks.json is not valid JSON"
fi

CONTENT=$(cat "$HOOKS_FILE")

section "codex-hooks.json — Structure"

set_test "has top-level hooks key"
assert_json_field_exists "$CONTENT" "hooks"

set_test "SessionStart event exists under hooks"
assert_json_field_exists "$CONTENT" "hooks.SessionStart"

set_test "SessionStart has non-empty hooks array"
has_hooks_array=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
arr = data['hooks']['SessionStart']
print('true' if isinstance(arr, list) and len(arr) > 0 else 'false')
" 2>/dev/null)
assert_eq "true" "$has_hooks_array" "SessionStart must have a non-empty array"

set_test "Hook entry has matcher field"
has_matcher=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
entry = data['hooks']['SessionStart'][0]
print('true' if 'matcher' in entry else 'false')
" 2>/dev/null)
assert_eq "true" "$has_matcher" "hook entry must have a matcher field"

set_test "Hook entry has hooks array"
has_inner_hooks=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
entry = data['hooks']['SessionStart'][0]
print('true' if 'hooks' in entry and isinstance(entry['hooks'], list) else 'false')
" 2>/dev/null)
assert_eq "true" "$has_inner_hooks" "hook entry must have hooks array"

set_test "Hook type is command"
hook_type=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
h = data['hooks']['SessionStart'][0]['hooks'][0]
print(h.get('type', ''))
" 2>/dev/null)
assert_eq "command" "$hook_type"

set_test "command field is non-empty"
cmd_val=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
h = data['hooks']['SessionStart'][0]['hooks'][0]
print(h.get('command', ''))
" 2>/dev/null)
if [ -n "$cmd_val" ]; then
  _pass
else
  _fail "command field is empty"
fi

set_test "has statusMessage field"
has_status=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
h = data['hooks']['SessionStart'][0]['hooks'][0]
print('true' if 'statusMessage' in h and h['statusMessage'] else 'false')
" 2>/dev/null)
assert_eq "true" "$has_status" "hook must have a non-empty statusMessage field"

test_summary
