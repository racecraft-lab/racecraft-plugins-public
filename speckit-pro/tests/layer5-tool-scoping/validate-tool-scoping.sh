#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

# Override _pass/_fail to avoid ((x++)) returning 1 when x is 0 under set -e
_pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  if [ "$VERBOSE" = "true" ]; then
    printf "${GREEN}PASS${RESET}\n"
  fi
}
_fail() {
  local msg="${1:-}"
  FAIL_COUNT=$((FAIL_COUNT + 1))
  if [ "$VERBOSE" = "true" ]; then
    printf "${RED}FAIL${RESET}\n"
    [ -n "$msg" ] && printf "    ${RED}%s${RESET}\n" "$msg"
  else
    printf "${RED}FAIL${RESET}: %s\n" "$TEST_NAME"
    [ -n "$msg" ] && printf "  ${RED}%s${RESET}\n" "$msg"
  fi
}

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
AGENTS_DIR="$PLUGIN_ROOT/agents"

# ---------------------------------------------------------------------------
# Helper: extract tools list from YAML frontmatter
# ---------------------------------------------------------------------------
extract_tools() {
  local file="$1"
  sed -n '/^---$/,/^---$/p' "$file" | \
    sed -n '/^tools:/,/^[a-z]/p' | \
    grep '^ *- ' | \
    sed 's/^ *- //'
}

# ---------------------------------------------------------------------------
# Helper: extract a scalar YAML field from frontmatter
# ---------------------------------------------------------------------------
extract_field() {
  local file="$1" field="$2"
  sed -n '/^---$/,/^---$/p' "$file" | \
    grep "^${field}:" | \
    head -1 | \
    sed "s/^${field}:[[:space:]]*//"
}

# ---------------------------------------------------------------------------
# Helper: assert a tool IS present in the tools list
# ---------------------------------------------------------------------------
assert_tool_present() {
  local tools="$1" tool="$2" agent="$3"
  local found=false
  while IFS= read -r line; do
    if [ "$line" = "$tool" ]; then
      found=true
      break
    fi
  done <<< "$tools"
  if [ "$found" = "true" ]; then
    _pass
  else
    _fail "$agent must have tool '$tool' but it is missing"
  fi
}

# ---------------------------------------------------------------------------
# Helper: assert a tool is NOT present in the tools list
# ---------------------------------------------------------------------------
assert_tool_absent() {
  local tools="$1" tool="$2" agent="$3"
  local found=false
  while IFS= read -r line; do
    if [ "$line" = "$tool" ]; then
      found=true
      break
    fi
  done <<< "$tools"
  if [ "$found" = "false" ]; then
    _pass
  else
    _fail "$agent must NOT have tool '$tool' but it is present"
  fi
}

# ---------------------------------------------------------------------------
# Helper: assert NO mcp__ tools are present
# ---------------------------------------------------------------------------
assert_no_mcp_tools() {
  local tools="$1" agent="$2"
  local mcp_found=""
  while IFS= read -r line; do
    if [[ "$line" == mcp__* ]]; then
      mcp_found="$line"
      break
    fi
  done <<< "$tools"
  if [ -z "$mcp_found" ]; then
    _pass
  else
    _fail "$agent must NOT have any mcp__ tools but found '$mcp_found'"
  fi
}

# ===========================================================================
# phase-executor
# ===========================================================================
section "phase-executor"

AGENT_FILE="$AGENTS_DIR/phase-executor.md"
TOOLS=$(extract_tools "$AGENT_FILE")

for tool in Skill Read Write Edit Bash Grep Glob; do
  set_test "phase-executor has $tool"
  assert_tool_present "$TOOLS" "$tool" "phase-executor"
done

set_test "phase-executor has no mcp__ tools"
assert_no_mcp_tools "$TOOLS" "phase-executor"

set_test "phase-executor permissionMode is acceptEdits"
mode=$(extract_field "$AGENT_FILE" "permissionMode")
assert_eq "acceptEdits" "$mode"

set_test "phase-executor maxTurns exists and is positive"
max_turns=$(extract_field "$AGENT_FILE" "maxTurns")
assert_gt "$max_turns" 0

set_test "phase-executor effort field exists"
effort=$(extract_field "$AGENT_FILE" "effort")
assert_not_contains "" "$effort" "effort must not be empty"

set_test "phase-executor effort is low"
effort=$(extract_field "$AGENT_FILE" "effort")
assert_eq "low" "$effort"

# ===========================================================================
# clarify-executor
# ===========================================================================
section "clarify-executor"

AGENT_FILE="$AGENTS_DIR/clarify-executor.md"
TOOLS=$(extract_tools "$AGENT_FILE")

for tool in Skill Read Write Edit Bash Grep Glob WebSearch WebFetch; do
  set_test "clarify-executor has $tool"
  assert_tool_present "$TOOLS" "$tool" "clarify-executor"
done

set_test "clarify-executor permissionMode is acceptEdits"
mode=$(extract_field "$AGENT_FILE" "permissionMode")
assert_eq "acceptEdits" "$mode"

set_test "clarify-executor maxTurns exists and is positive"
max_turns=$(extract_field "$AGENT_FILE" "maxTurns")
assert_gt "$max_turns" 0

set_test "clarify-executor effort field exists"
effort=$(extract_field "$AGENT_FILE" "effort")
assert_not_contains "" "$effort" "effort must not be empty"

# ===========================================================================
# checklist-executor
# ===========================================================================
section "checklist-executor"

AGENT_FILE="$AGENTS_DIR/checklist-executor.md"
TOOLS=$(extract_tools "$AGENT_FILE")

for tool in Skill Read Write Edit Bash Grep Glob WebSearch WebFetch; do
  set_test "checklist-executor has $tool"
  assert_tool_present "$TOOLS" "$tool" "checklist-executor"
done

set_test "checklist-executor permissionMode is acceptEdits"
mode=$(extract_field "$AGENT_FILE" "permissionMode")
assert_eq "acceptEdits" "$mode"

set_test "checklist-executor maxTurns exists and is positive"
max_turns=$(extract_field "$AGENT_FILE" "maxTurns")
assert_gt "$max_turns" 0

set_test "checklist-executor effort field exists"
effort=$(extract_field "$AGENT_FILE" "effort")
assert_not_contains "" "$effort" "effort must not be empty"

# ===========================================================================
# analyze-executor
# ===========================================================================
section "analyze-executor"

AGENT_FILE="$AGENTS_DIR/analyze-executor.md"
TOOLS=$(extract_tools "$AGENT_FILE")

for tool in Skill Read Write Edit Bash Grep Glob WebSearch WebFetch; do
  set_test "analyze-executor has $tool"
  assert_tool_present "$TOOLS" "$tool" "analyze-executor"
done

set_test "analyze-executor permissionMode is acceptEdits"
mode=$(extract_field "$AGENT_FILE" "permissionMode")
assert_eq "acceptEdits" "$mode"

set_test "analyze-executor maxTurns exists and is positive"
max_turns=$(extract_field "$AGENT_FILE" "maxTurns")
assert_gt "$max_turns" 0

set_test "analyze-executor effort field exists"
effort=$(extract_field "$AGENT_FILE" "effort")
assert_not_contains "" "$effort" "effort must not be empty"

# ===========================================================================
# implement-executor
# ===========================================================================
section "implement-executor"

AGENT_FILE="$AGENTS_DIR/implement-executor.md"
TOOLS=$(extract_tools "$AGENT_FILE")

for tool in Read Write Edit Bash Grep Glob; do
  set_test "implement-executor has $tool"
  assert_tool_present "$TOOLS" "$tool" "implement-executor"
done

set_test "implement-executor does NOT have Skill"
assert_tool_absent "$TOOLS" "Skill" "implement-executor"

set_test "implement-executor permissionMode is acceptEdits"
mode=$(extract_field "$AGENT_FILE" "permissionMode")
assert_eq "acceptEdits" "$mode"

set_test "implement-executor maxTurns exists and is positive"
max_turns=$(extract_field "$AGENT_FILE" "maxTurns")
assert_gt "$max_turns" 0

set_test "implement-executor effort field exists"
effort=$(extract_field "$AGENT_FILE" "effort")
assert_not_contains "" "$effort" "effort must not be empty"

# ===========================================================================
# codebase-analyst
# ===========================================================================
section "codebase-analyst"

AGENT_FILE="$AGENTS_DIR/codebase-analyst.md"
TOOLS=$(extract_tools "$AGENT_FILE")

for tool in Read Glob Grep; do
  set_test "codebase-analyst has $tool"
  assert_tool_present "$TOOLS" "$tool" "codebase-analyst"
done

for tool in Write Edit Bash; do
  set_test "codebase-analyst does NOT have $tool"
  assert_tool_absent "$TOOLS" "$tool" "codebase-analyst"
done

set_test "codebase-analyst permissionMode is NOT acceptEdits"
mode=$(extract_field "$AGENT_FILE" "permissionMode")
if [ "$mode" != "acceptEdits" ]; then
  _pass
else
  _fail "codebase-analyst permissionMode should not be acceptEdits, got '$mode'"
fi

set_test "codebase-analyst maxTurns exists and is positive"
max_turns=$(extract_field "$AGENT_FILE" "maxTurns")
assert_gt "$max_turns" 0

set_test "codebase-analyst effort field exists"
effort=$(extract_field "$AGENT_FILE" "effort")
assert_not_contains "" "$effort" "effort must not be empty"

# ===========================================================================
# spec-context-analyst
# ===========================================================================
section "spec-context-analyst"

AGENT_FILE="$AGENTS_DIR/spec-context-analyst.md"
TOOLS=$(extract_tools "$AGENT_FILE")

for tool in Read Glob Grep; do
  set_test "spec-context-analyst has $tool"
  assert_tool_present "$TOOLS" "$tool" "spec-context-analyst"
done

for tool in Write Edit Bash; do
  set_test "spec-context-analyst does NOT have $tool"
  assert_tool_absent "$TOOLS" "$tool" "spec-context-analyst"
done

set_test "spec-context-analyst permissionMode is NOT acceptEdits"
mode=$(extract_field "$AGENT_FILE" "permissionMode")
if [ "$mode" != "acceptEdits" ]; then
  _pass
else
  _fail "spec-context-analyst permissionMode should not be acceptEdits, got '$mode'"
fi

set_test "spec-context-analyst maxTurns exists and is positive"
max_turns=$(extract_field "$AGENT_FILE" "maxTurns")
assert_gt "$max_turns" 0

set_test "spec-context-analyst effort field exists"
effort=$(extract_field "$AGENT_FILE" "effort")
assert_not_contains "" "$effort" "effort must not be empty"

# ===========================================================================
# domain-researcher
# ===========================================================================
section "domain-researcher"

AGENT_FILE="$AGENTS_DIR/domain-researcher.md"
TOOLS=$(extract_tools "$AGENT_FILE")

for tool in Read WebSearch WebFetch; do
  set_test "domain-researcher has $tool"
  assert_tool_present "$TOOLS" "$tool" "domain-researcher"
done

for tool in Write Edit Bash Glob Grep; do
  set_test "domain-researcher does NOT have $tool"
  assert_tool_absent "$TOOLS" "$tool" "domain-researcher"
done

set_test "domain-researcher permissionMode is NOT acceptEdits"
mode=$(extract_field "$AGENT_FILE" "permissionMode")
if [ "$mode" != "acceptEdits" ]; then
  _pass
else
  _fail "domain-researcher permissionMode should not be acceptEdits, got '$mode'"
fi

set_test "domain-researcher maxTurns exists and is positive"
max_turns=$(extract_field "$AGENT_FILE" "maxTurns")
assert_gt "$max_turns" 0

set_test "domain-researcher effort field exists"
effort=$(extract_field "$AGENT_FILE" "effort")
assert_not_contains "" "$effort" "effort must not be empty"

# ===========================================================================
# gate-validator
# ===========================================================================
section "gate-validator"

AGENT_FILE="$AGENTS_DIR/gate-validator.md"
TOOLS=$(extract_tools "$AGENT_FILE")

for tool in Bash Read Grep; do
  set_test "gate-validator has $tool"
  assert_tool_present "$TOOLS" "$tool" "gate-validator"
done

for tool in Write Edit Skill; do
  set_test "gate-validator does NOT have $tool"
  assert_tool_absent "$TOOLS" "$tool" "gate-validator"
done

set_test "gate-validator has no mcp__ tools"
assert_no_mcp_tools "$TOOLS" "gate-validator"

set_test "gate-validator permissionMode is NOT acceptEdits"
mode=$(extract_field "$AGENT_FILE" "permissionMode")
if [ "$mode" != "acceptEdits" ]; then
  _pass
else
  _fail "gate-validator permissionMode should not be acceptEdits, got '$mode'"
fi

set_test "gate-validator model is haiku"
model=$(extract_field "$AGENT_FILE" "model")
assert_eq "haiku" "$model"

set_test "gate-validator effort is low"
effort=$(extract_field "$AGENT_FILE" "effort")
assert_eq "low" "$effort"

set_test "gate-validator maxTurns exists and is positive"
max_turns=$(extract_field "$AGENT_FILE" "maxTurns")
assert_gt "$max_turns" 0

# ===========================================================================
# consensus-synthesizer
# ===========================================================================
section "consensus-synthesizer"

AGENT_FILE="$AGENTS_DIR/consensus-synthesizer.md"
TOOLS=$(extract_tools "$AGENT_FILE")

for tool in Read Grep Glob; do
  set_test "consensus-synthesizer has $tool"
  assert_tool_present "$TOOLS" "$tool" "consensus-synthesizer"
done

for tool in Write Edit Bash Skill; do
  set_test "consensus-synthesizer does NOT have $tool"
  assert_tool_absent "$TOOLS" "$tool" "consensus-synthesizer"
done

set_test "consensus-synthesizer has no mcp__ tools"
assert_no_mcp_tools "$TOOLS" "consensus-synthesizer"

set_test "consensus-synthesizer permissionMode is NOT acceptEdits"
mode=$(extract_field "$AGENT_FILE" "permissionMode")
if [ "$mode" != "acceptEdits" ]; then
  _pass
else
  _fail "consensus-synthesizer permissionMode should not be acceptEdits, got '$mode'"
fi

set_test "consensus-synthesizer model is sonnet"
model=$(extract_field "$AGENT_FILE" "model")
assert_eq "sonnet" "$model"

set_test "consensus-synthesizer effort is high"
effort=$(extract_field "$AGENT_FILE" "effort")
assert_eq "high" "$effort"

set_test "consensus-synthesizer maxTurns exists and is positive"
max_turns=$(extract_field "$AGENT_FILE" "maxTurns")
assert_gt "$max_turns" 0

# ─────────────────────────────────────────
# Codex Agent Sandbox Mode Validation
# ─────────────────────────────────────────

CODEX_AGENTS_DIR="$PLUGIN_ROOT/codex-agents"

if [ -d "$CODEX_AGENTS_DIR" ]; then

  section "Codex Agent Sandbox Mode Scoping"

  # Read-only analysts must have sandbox_mode: read-only
  for agent in codebase-analyst spec-context-analyst domain-researcher; do
    AGENT_FILE="$CODEX_AGENTS_DIR/${agent}.md"
    if [ -f "$AGENT_FILE" ]; then
      sandbox=$(extract_field "$AGENT_FILE" "sandbox_mode")
      set_test "codex ${agent}: sandbox_mode is read-only"
      assert_eq "read-only" "$sandbox" "${agent} must be read-only"
    fi
  done

  # Write agents must have sandbox_mode: workspace-write
  for agent in clarify-executor checklist-executor analyze-executor implement-executor phase-executor; do
    AGENT_FILE="$CODEX_AGENTS_DIR/${agent}.md"
    if [ -f "$AGENT_FILE" ]; then
      sandbox=$(extract_field "$AGENT_FILE" "sandbox_mode")
      set_test "codex ${agent}: sandbox_mode is workspace-write"
      assert_eq "workspace-write" "$sandbox" "${agent} must be workspace-write"
    fi
  done

fi

# ===========================================================================
test_summary
