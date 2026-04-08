#!/usr/bin/env bash
# validate-codex-commands.sh — Structural validation for Codex command files
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

CODEX_COMMANDS_DIR="$PLUGIN_ROOT/codex-commands"
COMMANDS=(autopilot coach setup status resolve-pr)

# Claude Code-only frontmatter keys that must NOT appear in Codex commands
CC_ONLY_KEYS=(allowed-tools argument-hint)

section "codex-commands/ directory"

set_test "codex-commands/ directory exists"
if [ -d "$CODEX_COMMANDS_DIR" ]; then
  _pass
else
  _fail "codex-commands/ directory not found"
  test_summary
fi

for cmd in "${COMMANDS[@]}"; do
  CMD_FILE="$CODEX_COMMANDS_DIR/${cmd}.md"

  section "codex-commands/${cmd}.md"

  set_test "${cmd}: file exists"
  assert_file_exists "$CMD_FILE"

  if [ ! -f "$CMD_FILE" ]; then
    continue
  fi

  content=$(cat "$CMD_FILE")
  first_line=$(head -n1 "$CMD_FILE")

  set_test "${cmd}: starts with # (markdown heading, no YAML frontmatter)"
  if [[ "$first_line" == "# "* ]]; then
    _pass
  else
    _fail "first line must start with '# ', got: $first_line"
  fi

  set_test "${cmd}: no YAML frontmatter delimiters"
  fence_count=$(grep -c '^---$' "$CMD_FILE") || fence_count=0
  if [ "$fence_count" -eq 0 ]; then
    _pass
  else
    _fail "Codex commands must not have YAML frontmatter (found $fence_count '---' lines)"
  fi

  set_test "${cmd}: no Claude Code-only frontmatter keys"
  bad_keys=""
  for key in "${CC_ONLY_KEYS[@]}"; do
    if echo "$content" | grep -qE "^${key}:" ; then
      bad_keys="$bad_keys $key"
    fi
  done
  if [ -z "$bad_keys" ]; then
    _pass
  else
    _fail "Claude Code-only keys found:$bad_keys"
  fi

  set_test "${cmd}: has ## Arguments section"
  assert_contains "$content" "## Arguments"

  set_test "${cmd}: has ## Workflow section"
  assert_contains "$content" "## Workflow"

  set_test "${cmd}: body word count at least 30"
  word_count=$(wc -w < "$CMD_FILE" | tr -d ' ')
  if [ "$word_count" -ge 30 ]; then
    _pass
  else
    _fail "body is $word_count words (need at least 30)"
  fi

  set_test "${cmd}: no CC-specific tool references (Skill(), Agent())"
  if echo "$content" | grep -qE 'Skill\(|Agent\(\{'; then
    _fail "found Claude Code-specific tool references (Skill() or Agent())"
  else
    _pass
  fi
done

test_summary
