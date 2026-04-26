#!/usr/bin/env bash
# validate-codex-agents.sh — Structural validation for bundled Codex custom
# subagent templates. These are packaged as TOML files that are copied into
# ~/.codex/agents/ or .codex/agents/ by the install skill.
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

CODEX_AGENTS_DIR="$PLUGIN_ROOT/codex-agents"
CC_AGENTS_DIR="$PLUGIN_ROOT/agents"

AGENTS=(
  autopilot-fast-helper
  clarify-executor
  checklist-executor
  analyze-executor
  implement-executor
  phase-executor
  codebase-analyst
  spec-context-analyst
  domain-researcher
)

CC_ONLY_FIELDS=(tools permissionMode color maxTurns background effort)

extract_toml_string() {
  local file="$1" field="$2"
  sed -n "s/^${field} = \"\\([^\"]*\\)\"$/\\1/p" "$file" | head -1
}

extract_developer_instructions() {
  local file="$1"
  awk '
    /^developer_instructions = """/ { capture=1; next }
    capture && $0 == "\"\"\"" { exit }
    capture { print }
  ' "$file"
}

for agent in "${AGENTS[@]}"; do
  AGENT_FILE="$CODEX_AGENTS_DIR/${agent}.toml"

  section "codex-agents/${agent}.toml"

  set_test "${agent}: TOML file exists"
  assert_file_exists "$AGENT_FILE"

  set_test "${agent}: legacy Markdown file removed"
  assert_file_not_exists "$CODEX_AGENTS_DIR/${agent}.md"

  if [ ! -f "$AGENT_FILE" ]; then
    continue
  fi

  content=$(cat "$AGENT_FILE")

  set_test "${agent}: has name field"
  assert_contains "$content" 'name = "'

  name_val=$(extract_toml_string "$AGENT_FILE" "name")
  set_test "${agent}: name matches filename"
  assert_eq "$agent" "$name_val" "name field must match filename stem"

  set_test "${agent}: has description field"
  assert_contains "$content" 'description = "'

  set_test "${agent}: has model field"
  assert_contains "$content" 'model = "'

  model_val=$(extract_toml_string "$AGENT_FILE" "model")
  set_test "${agent}: model is an officially documented Codex GPT model"
  assert_match "$model_val" '^(gpt-5\.5|gpt-5\.4|gpt-5\.4-mini|gpt-5\.3-codex|gpt-5\.3-codex-spark)$' \
    "model must be an officially documented Codex GPT model"

  set_test "${agent}: has model_reasoning_effort field"
  assert_contains "$content" 'model_reasoning_effort = "'

  effort_val=$(extract_toml_string "$AGENT_FILE" "model_reasoning_effort")
  set_test "${agent}: reasoning effort uses supported values"
  assert_match "$effort_val" '^(minimal|low|medium|high|xhigh)$' \
    "reasoning effort must be minimal, low, medium, high, or xhigh"

  set_test "${agent}: has sandbox_mode field"
  assert_contains "$content" 'sandbox_mode = "'

  sandbox_val=$(extract_toml_string "$AGENT_FILE" "sandbox_mode")
  set_test "${agent}: sandbox_mode uses supported values"
  assert_match "$sandbox_val" '^(read-only|workspace-write)$'

  set_test "${agent}: has developer_instructions block"
  assert_contains "$content" 'developer_instructions = """'

  instructions=$(extract_developer_instructions "$AGENT_FILE")
  instructions_trimmed=$(echo "$instructions" | sed '/^[[:space:]]*$/d')
  set_test "${agent}: developer_instructions body is non-empty"
  if [ -n "$instructions_trimmed" ]; then
    _pass
  else
    _fail "developer_instructions block is empty"
  fi

  set_test "${agent}: no Claude Code-only fields"
  bad_fields=""
  for field in "${CC_ONLY_FIELDS[@]}"; do
    if echo "$content" | grep -qE "^${field}[[:space:]]*="; then
      bad_fields="$bad_fields $field"
    fi
  done
  if [ -z "$bad_fields" ]; then
    _pass
  else
    _fail "Claude Code-only fields found:$bad_fields"
  fi

  if [ "$agent" != "autopilot-fast-helper" ]; then
    set_test "${agent}: corresponding Claude agent exists in agents/"
    assert_file_exists "$CC_AGENTS_DIR/${agent}.md"
  else
    set_test "autopilot-fast-helper: intentionally Codex-only"
    if [ -f "$CC_AGENTS_DIR/${agent}.md" ]; then
      _fail "autopilot-fast-helper should remain Codex-only; do not add a Claude twin"
    else
      _pass
    fi
  fi

  case "$agent" in
    autopilot-fast-helper)
      set_test "autopilot-fast-helper: uses Spark latency-first advisory profile"
      if [ "$model_val" = "gpt-5.3-codex-spark" ] && [ "$effort_val" = "low" ] && [ "$sandbox_val" = "read-only" ]; then
        _pass
      else
        _fail "expected gpt-5.3-codex-spark / low / read-only, got $model_val / $effort_val / $sandbox_val"
      fi
      ;;
    phase-executor)
      set_test "phase-executor: uses fast Codex worker profile"
      if [ "$model_val" = "gpt-5.4-mini" ] && [ "$effort_val" = "low" ] && [ "$sandbox_val" = "workspace-write" ]; then
        _pass
      else
        _fail "expected gpt-5.4-mini / low / workspace-write, got $model_val / $effort_val / $sandbox_val"
      fi
      ;;
    clarify-executor|checklist-executor|analyze-executor)
      set_test "${agent}: uses high-effort GPT-5.5 executor profile"
      if [ "$model_val" = "gpt-5.5" ] && [ "$effort_val" = "high" ] && [ "$sandbox_val" = "workspace-write" ]; then
        _pass
      else
        _fail "expected gpt-5.5 / high / workspace-write, got $model_val / $effort_val / $sandbox_val"
      fi
      ;;
    implement-executor)
      set_test "implement-executor: uses coding-focused GPT-5.5 profile"
      if [ "$model_val" = "gpt-5.5" ] && [ "$effort_val" = "medium" ] && [ "$sandbox_val" = "workspace-write" ]; then
        _pass
      else
        _fail "expected gpt-5.5 / medium / workspace-write, got $model_val / $effort_val / $sandbox_val"
      fi
      ;;
    codebase-analyst|spec-context-analyst|domain-researcher)
      set_test "${agent}: uses read-only GPT-5.5 consensus profile"
      if [ "$model_val" = "gpt-5.5" ] && [ "$effort_val" = "medium" ] && [ "$sandbox_val" = "read-only" ]; then
        _pass
      else
        _fail "expected gpt-5.5 / medium / read-only, got $model_val / $effort_val / $sandbox_val"
      fi
      ;;
  esac
done

section "codex-agents runtime packaging"

set_test "codex-agents/openai.yaml removed"
assert_file_not_exists "$CODEX_AGENTS_DIR/openai.yaml"

set_test "codex-agents directory contains TOML files only"
non_toml=$(find "$CODEX_AGENTS_DIR" -maxdepth 1 -type f ! -name '*.toml' | wc -l | tr -d ' ')
assert_eq "0" "$non_toml" "only standalone TOML custom-agent files are allowed"

test_summary
