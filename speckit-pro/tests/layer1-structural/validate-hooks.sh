#!/usr/bin/env bash
# validate-hooks.sh — Structural validation for hooks/hooks.json
#
# The plugin hook is scoped via UserPromptExpansion with a matcher that
# only fires on speckit-pro / SpecKit / bundled-skill command invocations
# — NOT a global SessionStart hook that would fire on every Claude Code
# session. This validator asserts the scoping shape so future edits can't
# silently broaden it back to always-fires behavior.
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

section "hooks/hooks.json — Scoping (UserPromptExpansion, NOT SessionStart)"

set_test "has top-level hooks key"
assert_json_field_exists "$CONTENT" "hooks"

set_test "UserPromptExpansion event exists under hooks"
assert_json_field_exists "$CONTENT" "hooks.UserPromptExpansion"

set_test "NO SessionStart hook (would fire on every session — regression guard)"
has_session_start=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('true' if 'SessionStart' in data.get('hooks', {}) else 'false')
" 2>/dev/null)
assert_eq "false" "$has_session_start" "plugin must not register a global SessionStart hook"

set_test "NO UserPromptSubmit hook (would fire on every prompt — regression guard)"
has_user_prompt_submit=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('true' if 'UserPromptSubmit' in data.get('hooks', {}) else 'false')
" 2>/dev/null)
assert_eq "false" "$has_user_prompt_submit" "plugin must not register a global UserPromptSubmit hook"

section "hooks/hooks.json — UserPromptExpansion shape"

set_test "UserPromptExpansion is a non-empty array"
has_hooks_array=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
arr = data['hooks']['UserPromptExpansion']
print('true' if isinstance(arr, list) and len(arr) > 0 else 'false')
" 2>/dev/null)
assert_eq "true" "$has_hooks_array" "UserPromptExpansion must have a non-empty array"

set_test "Hook entry has matcher field (scopes to plugin command_name)"
has_matcher=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
entry = data['hooks']['UserPromptExpansion'][0]
print('true' if 'matcher' in entry and entry['matcher'] else 'false')
" 2>/dev/null)
assert_eq "true" "$has_matcher" "hook entry must have a non-empty matcher"

set_test "Matcher contains plugin-scoping regex (speckit-pro: or speckit. or speckit- or grill-me)"
matcher_val=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['hooks']['UserPromptExpansion'][0].get('matcher', ''))
" 2>/dev/null)
if [[ "$matcher_val" == *"speckit-pro:"* ]] || [[ "$matcher_val" == *"speckit"* ]] || [[ "$matcher_val" == *"grill-me"* ]]; then
  _pass
else
  _fail "matcher must scope to plugin commands (was: '$matcher_val')"
fi

set_test "Hook entry has hooks array"
has_inner_hooks=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
entry = data['hooks']['UserPromptExpansion'][0]
print('true' if 'hooks' in entry and isinstance(entry['hooks'], list) else 'false')
" 2>/dev/null)
assert_eq "true" "$has_inner_hooks" "hook entry must have hooks array"

set_test "Each hook entry has type field"
has_type=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
hooks = data['hooks']['UserPromptExpansion'][0]['hooks']
print('true' if all('type' in h for h in hooks) else 'false')
" 2>/dev/null)
assert_eq "true" "$has_type" "every hook must have a type field"

set_test "Hook type is command"
hook_type=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
h = data['hooks']['UserPromptExpansion'][0]['hooks'][0]
print(h.get('type', ''))
" 2>/dev/null)
assert_eq "command" "$hook_type"

set_test "Command field is non-empty"
cmd_val=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
h = data['hooks']['UserPromptExpansion'][0]['hooks'][0]
print(h.get('command', ''))
" 2>/dev/null)
if [ -n "$cmd_val" ]; then
  _pass
else
  _fail "command field is empty"
fi

test_summary
