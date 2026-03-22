#!/usr/bin/env bash
# validate-hooks.sh — Structural validation for hooks/hooks.json
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

HOOKS_FILE="$PLUGIN_ROOT/hooks/hooks.json"

section "hooks/hooks.json — File Existence"

set_test "hooks.json exists"
assert_file_exists "$HOOKS_FILE"

section "hooks/hooks.json — Valid JSON"

set_test "hooks.json is valid JSON"
if python3 -m json.tool "$HOOKS_FILE" >/dev/null 2>&1; then
  _pass
else
  _fail "hooks.json is not valid JSON"
fi

CONTENT=$(cat "$HOOKS_FILE")

section "hooks/hooks.json — Structure"

set_test "has top-level hooks key"
assert_json_field_exists "$CONTENT" "hooks"

set_test "SessionStart event exists under hooks"
assert_json_field_exists "$CONTENT" "hooks.SessionStart"

set_test "SessionStart has hooks array"
has_hooks_array=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
arr = data['hooks']['SessionStart']
print('true' if isinstance(arr, list) and len(arr) > 0 else 'false')
" 2>/dev/null)
assert_eq "true" "$has_hooks_array" "SessionStart must have a non-empty array"

set_test "Hook entries have hooks array"
has_inner_hooks=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
entry = data['hooks']['SessionStart'][0]
print('true' if 'hooks' in entry and isinstance(entry['hooks'], list) else 'false')
" 2>/dev/null)
assert_eq "true" "$has_inner_hooks" "hook entry must have hooks array"

set_test "Each hook entry has type field"
has_type=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
hooks = data['hooks']['SessionStart'][0]['hooks']
all_have_type = all('type' in h for h in hooks)
print('true' if all_have_type else 'false')
" 2>/dev/null)
assert_eq "true" "$has_type" "every hook must have a type field"

set_test "Hook type is command"
hook_type=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
h = data['hooks']['SessionStart'][0]['hooks'][0]
print(h.get('type', ''))
" 2>/dev/null)
assert_eq "command" "$hook_type"

set_test "Command field is non-empty"
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

test_summary
