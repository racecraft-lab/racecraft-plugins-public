#!/usr/bin/env bash
# validate-codex-hooks.sh — Structural validation for codex-hooks.json
#
# Codex's plugin loader (codex-rs/core-plugins/src/loader.rs) defaults to
# `hooks/hooks.json` if no manifest override is set. speckit-pro keeps its
# Codex hook at the root as `codex-hooks.json` so it lives next to the
# Claude Code hook (`hooks/hooks.json`) without collision; the manifest
# `hooks` field overrides the default path. This validator asserts both
# the file location AND the manifest pointer so a stale rename can't
# silently disable Codex hook loading.
#
# The Codex hook uses UserPromptSubmit because Codex has no
# UserPromptExpansion equivalent. XPLAT-008 deliberately keeps the hook
# command list empty: a static hook command cannot perform the platform-
# specific Python discovery that installed skills and agents perform before
# invoking the runner. This prevents non-portable preflight failures before
# the real runner discovery path is reached.
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"

HOOKS_FILE="$PLUGIN_ROOT/codex-hooks.json"
MANIFEST_FILE="$PLUGIN_ROOT/.codex-plugin/plugin.json"

section "codex-hooks.json — File Existence"

set_test "codex-hooks.json exists"
assert_file_exists "$HOOKS_FILE"

section "codex-hooks.json — Manifest pointer"

set_test ".codex-plugin/plugin.json declares hooks pointer"
if [ -f "$MANIFEST_FILE" ]; then
  hooks_ptr=$(python3 -c "
import sys, json
with open('$MANIFEST_FILE') as f:
    data = json.load(f)
print(data.get('hooks', ''))
" 2>/dev/null)
  if [ "$hooks_ptr" = "./codex-hooks.json" ]; then
    _pass
  else
    _fail "manifest hooks field must be \"./codex-hooks.json\" (was: \"$hooks_ptr\"). Codex's plugin loader defaults to hooks/hooks.json; without this manifest pointer the codex-hooks.json file at root will not load."
  fi
else
  _fail ".codex-plugin/plugin.json missing"
fi

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

section "codex-hooks.json — Prompt hook shape"

set_test "has top-level hooks key"
assert_json_field_exists "$CONTENT" "hooks"

set_test "UserPromptSubmit event exists under hooks"
assert_json_field_exists "$CONTENT" "hooks.UserPromptSubmit"

set_test "NO SessionStart hook (would fire on every session — regression guard)"
has_session_start=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('true' if 'SessionStart' in data.get('hooks', {}) else 'false')
" 2>/dev/null)
assert_eq "false" "$has_session_start" "Codex hook must not register SessionStart; use UserPromptSubmit for the runner availability check"

set_test "UserPromptSubmit has non-empty hooks array"
has_hooks_array=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
arr = data['hooks']['UserPromptSubmit']
print('true' if isinstance(arr, list) and len(arr) > 0 else 'false')
" 2>/dev/null)
assert_eq "true" "$has_hooks_array" "UserPromptSubmit must have a non-empty array"

set_test "Hook entry has hooks array"
has_inner_hooks=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
entry = data['hooks']['UserPromptSubmit'][0]
print('true' if 'hooks' in entry and isinstance(entry['hooks'], list) else 'false')
" 2>/dev/null)
assert_eq "true" "$has_inner_hooks" "hook entry must have hooks array"

set_test "Hook entry has an empty command list"
empty_inner_hooks=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
hooks = data['hooks']['UserPromptSubmit'][0]['hooks']
print('true' if isinstance(hooks, list) and len(hooks) == 0 else 'false')
" 2>/dev/null)
assert_eq "true" "$empty_inner_hooks" "Codex plugin hook must not run a static interpreter command; skills own runner discovery"

test_summary
