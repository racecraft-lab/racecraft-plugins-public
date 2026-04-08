#!/usr/bin/env bash
# validate-codex-agents.sh — Structural validation for Codex agent files
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

CODEX_AGENTS_DIR="$PLUGIN_ROOT/codex-agents"
CC_AGENTS_DIR="$PLUGIN_ROOT/agents"

AGENTS=(
  clarify-executor
  checklist-executor
  analyze-executor
  implement-executor
  phase-executor
  codebase-analyst
  spec-context-analyst
  domain-researcher
)

# Claude Code-only fields that must NOT appear in Codex agents
CC_ONLY_FIELDS=(tools permissionMode color maxTurns background)

for agent in "${AGENTS[@]}"; do
  AGENT_FILE="$CODEX_AGENTS_DIR/${agent}.md"

  section "codex-agents/${agent}.md"

  set_test "${agent}: file exists"
  assert_file_exists "$AGENT_FILE"

  if [ ! -f "$AGENT_FILE" ]; then
    continue
  fi

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

  set_test "${agent}: has description: field"
  assert_contains "$frontmatter" "description:"

  set_test "${agent}: has model: field"
  assert_contains "$frontmatter" "model:"

  # Extract model value
  model_val=$(echo "$frontmatter" | grep -m1 '^model:' | sed 's/^model:[[:space:]]*//' | tr -d '"' | tr -d "'")

  set_test "${agent}: model starts with gpt-"
  assert_match "$model_val" '^gpt-' "model must start with gpt-"

  set_test "${agent}: has sandbox_mode: field"
  assert_contains "$frontmatter" "sandbox_mode:"

  set_test "${agent}: no Claude Code-only fields"
  bad_fields=""
  for field in "${CC_ONLY_FIELDS[@]}"; do
    if echo "$frontmatter" | grep -qE "^${field}:"; then
      bad_fields="$bad_fields $field"
    fi
  done
  if [ -z "$bad_fields" ]; then
    _pass
  else
    _fail "Claude Code-only fields found:$bad_fields"
  fi

  set_test "${agent}: system prompt body exists (after frontmatter)"
  body=$(awk 'BEGIN{n=0} /^---$/{n++; if(n==2){found=1; next}} found{print}' "$AGENT_FILE")
  body_trimmed=$(echo "$body" | sed '/^[[:space:]]*$/d')
  if [ -n "$body_trimmed" ]; then
    _pass
  else
    _fail "no system prompt body after frontmatter"
  fi

  set_test "${agent}: corresponding CC agent exists in agents/"
  assert_file_exists "$CC_AGENTS_DIR/${agent}.md"
done

section "codex-agents/openai.yaml"

OPENAI_YAML="$CODEX_AGENTS_DIR/openai.yaml"

set_test "openai.yaml exists"
assert_file_exists "$OPENAI_YAML"

test_summary
