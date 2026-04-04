#!/usr/bin/env bash
# validate-agents.sh — Structural validation for all agent files
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

AGENTS_DIR="$PLUGIN_ROOT/agents"
AGENTS=(
  phase-executor
  clarify-executor
  checklist-executor
  analyze-executor
  implement-executor
  codebase-analyst
  spec-context-analyst
  domain-researcher
  gate-validator
)

for agent in "${AGENTS[@]}"; do
  AGENT_FILE="$AGENTS_DIR/${agent}.md"

  section "agents/${agent}.md"

  set_test "${agent}: file exists"
  assert_file_exists "$AGENT_FILE"

  if [ ! -f "$AGENT_FILE" ]; then
    continue
  fi

  content=$(cat "$AGENT_FILE")
  first_line=$(head -n1 "$AGENT_FILE")

  set_test "${agent}: starts with --- (YAML frontmatter)"
  assert_eq "---" "$first_line" "first line must be ---"

  set_test "${agent}: has closing ---"
  fence_count=$(grep -c '^---$' "$AGENT_FILE") || fence_count=0
  if [ "$fence_count" -ge 2 ]; then
    _pass
  else
    _fail "expected at least 2 '---' lines, found $fence_count"
  fi

  # Extract frontmatter (between first and second ---)
  frontmatter=$(awk '/^---$/{n++; if(n==1){next} if(n==2){exit}} n==1{print}' "$AGENT_FILE")

  set_test "${agent}: has name: field"
  assert_contains "$frontmatter" "name:"

  # Extract name value
  name_val=$(echo "$frontmatter" | grep -m1 '^name:' | sed 's/^name:[[:space:]]*//' | tr -d '"' | tr -d "'")

  set_test "${agent}: name is valid format (alphanumeric + hyphens, 3-50 chars)"
  if [[ "$name_val" =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{2,49}$ ]]; then
    _pass
  else
    _fail "name '$name_val' must be 3-50 chars, alphanumeric + hyphens"
  fi

  set_test "${agent}: has description: field"
  assert_contains "$frontmatter" "description:"

  set_test "${agent}: has model: field"
  assert_contains "$frontmatter" "model:"

  # Extract model value
  model_val=$(echo "$frontmatter" | grep -m1 '^model:' | sed 's/^model:[[:space:]]*//' | tr -d '"' | tr -d "'")

  set_test "${agent}: model is valid (opus|sonnet|haiku|inherit)"
  assert_match "$model_val" '^(opus|sonnet|haiku|inherit)$' "model must be opus, sonnet, haiku, or inherit"

  set_test "${agent}: system prompt body exists (after frontmatter)"
  body=$(awk 'BEGIN{n=0} /^---$/{n++; if(n==2){found=1; next}} found{print}' "$AGENT_FILE")
  body_trimmed=$(echo "$body" | sed '/^[[:space:]]*$/d')
  if [ -n "$body_trimmed" ]; then
    _pass
  else
    _fail "no system prompt body after frontmatter"
  fi

  set_test "${agent}: system prompt length > 20 chars"
  body_len=${#body_trimmed}
  if [ "$body_len" -gt 20 ]; then
    _pass
  else
    _fail "system prompt is only $body_len chars (need > 20)"
  fi
done

test_summary
