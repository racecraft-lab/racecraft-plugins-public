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
# The Codex hook is scoped via UserPromptSubmit + body-side prompt
# matching (Codex has no UserPromptExpansion equivalent; UserPromptSubmit's
# matcher field is ignored per the docs). The hook command reads stdin,
# extracts the prompt, and only runs the specify check if the prompt
# invokes a speckit-pro skill or SpecKit native command. This matches
# the Claude Code scoping behavior — fires only on plugin invocation.
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

section "codex-hooks.json — Scoping (UserPromptSubmit + body-side prompt match)"

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
assert_eq "false" "$has_session_start" "Codex hook must not register SessionStart (always fires); use UserPromptSubmit with body-side prompt matching"

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

set_test "Hook type is command"
hook_type=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
h = data['hooks']['UserPromptSubmit'][0]['hooks'][0]
print(h.get('type', ''))
" 2>/dev/null)
assert_eq "command" "$hook_type"

set_test "command field is non-empty"
cmd_val=$(printf '%s' "$CONTENT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
h = data['hooks']['UserPromptSubmit'][0]['hooks'][0]
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
h = data['hooks']['UserPromptSubmit'][0]['hooks'][0]
print('true' if 'statusMessage' in h and h['statusMessage'] else 'false')
" 2>/dev/null)
assert_eq "true" "$has_status" "hook must have a non-empty statusMessage field"

section "codex-hooks.json — Body-side prompt-match scoping"

set_test "Command body reads stdin and extracts the prompt via jq"
# Codex UserPromptSubmit fires on every user prompt; the matcher field is
# unused per the Codex docs. The hook must inspect the prompt content via
# jq on stdin to scope to plugin invocation only. Without this, the
# warning fires on every Codex prompt — exactly what we removed.
if [[ "$cmd_val" == *"jq -r"* ]] && [[ "$cmd_val" == *".prompt"* ]]; then
  _pass
else
  _fail "command must extract .prompt from stdin via jq for prompt-match scoping (was: '$cmd_val')"
fi

set_test "Command body greps for plugin-scoping invocation pattern"
if [[ "$cmd_val" == *"speckit-"* ]] && [[ "$cmd_val" == *"grill-me"* ]] && [[ "$cmd_val" == *"/speckit"* ]]; then
  _pass
else
  _fail "command must grep prompt for speckit-/grill-me/SpecKit invocation patterns (was: '$cmd_val')"
fi

test_summary
