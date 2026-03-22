#!/usr/bin/env bash
# validate-commands.sh — Structural validation for all command files
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

COMMANDS_DIR="$PLUGIN_ROOT/commands"
COMMANDS=(autopilot coach setup status resolve-pr)

for cmd in "${COMMANDS[@]}"; do
  CMD_FILE="$COMMANDS_DIR/${cmd}.md"

  section "commands/${cmd}.md"

  set_test "${cmd}: file exists"
  assert_file_exists "$CMD_FILE"

  # Skip remaining checks if file does not exist
  if [ ! -f "$CMD_FILE" ]; then
    continue
  fi

  content=$(cat "$CMD_FILE")
  first_line=$(head -n1 "$CMD_FILE")

  set_test "${cmd}: starts with --- (YAML frontmatter)"
  assert_eq "---" "$first_line" "first line must be ---"

  set_test "${cmd}: has closing ---"
  # Count lines that are exactly "---"; need at least 2 (open + close)
  fence_count=$(grep -c '^---$' "$CMD_FILE") || fence_count=0
  if [ "$fence_count" -ge 2 ]; then
    _pass
  else
    _fail "expected at least 2 '---' lines, found $fence_count"
  fi

  set_test "${cmd}: has description: field"
  assert_contains "$content" "description:"

  set_test "${cmd}: has allowed-tools: field"
  assert_contains "$content" "allowed-tools:"

  set_test "${cmd}: has body content after frontmatter"
  # Extract body after second ---
  body=$(awk 'BEGIN{n=0} /^---$/{n++; if(n==2){found=1; next}} found{print}' "$CMD_FILE")
  body_trimmed=$(echo "$body" | sed '/^[[:space:]]*$/d')
  if [ -n "$body_trimmed" ]; then
    _pass
  else
    _fail "no body content after frontmatter"
  fi
done

test_summary
