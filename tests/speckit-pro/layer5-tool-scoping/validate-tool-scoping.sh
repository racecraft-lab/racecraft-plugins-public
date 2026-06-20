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

PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"
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
# Helper: extract a scalar TOML string field
# ---------------------------------------------------------------------------
extract_toml_field() {
  local file="$1" field="$2"
  sed -n "s/^${field} = \"\\([^\"]*\\)\"$/\\1/p" "$file" | head -1
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

set_test "phase-executor maxTurns exists and is positive"
max_turns=$(extract_field "$AGENT_FILE" "maxTurns")
assert_gt "$max_turns" 0

set_test "phase-executor effort field exists"
effort=$(extract_field "$AGENT_FILE" "effort")
assert_not_contains "" "$effort" "effort must not be empty"

set_test "phase-executor effort is max (max-thinking policy)"
effort=$(extract_field "$AGENT_FILE" "effort")
assert_eq "max" "$effort"

# ===========================================================================
# clarify-executor
# ===========================================================================
section "clarify-executor"

AGENT_FILE="$AGENTS_DIR/clarify-executor.md"
TOOLS=$(extract_tools "$AGENT_FILE")

for tool in Read Bash Grep Glob WebSearch WebFetch; do
  set_test "clarify-executor has $tool"
  assert_tool_present "$TOOLS" "$tool" "clarify-executor"
done

for tool in Skill Write Edit; do
  set_test "clarify-executor does NOT have $tool"
  assert_tool_absent "$TOOLS" "$tool" "clarify-executor"
done

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

# Research tools — generic web capability only. The named vendor MCP set
# (Tavily/Context7/RepoPrompt) was removed per TACD-004 FR-002 so the
# tool-scoping contract no longer requires a specific vendor MCP set by
# name; capability discovery (not a hardcoded tool list) governs which
# optional tools an agent reaches for. The named-tool prose guard below
# enforces that the removed preference does not creep back into guidance.
for tool in WebSearch WebFetch; do
  set_test "implement-executor has $tool (research capability)"
  assert_tool_present "$TOOLS" "$tool" "implement-executor"
done

set_test "implement-executor does NOT have Skill"
assert_tool_absent "$TOOLS" "Skill" "implement-executor"

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

set_test "gate-validator model is sonnet (max-thinking policy: haiku does not support max)"
model=$(extract_field "$AGENT_FILE" "model")
assert_eq "sonnet" "$model"

set_test "gate-validator effort is max (max-thinking policy)"
effort=$(extract_field "$AGENT_FILE" "effort")
assert_eq "max" "$effort"

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

set_test "consensus-synthesizer model is sonnet"
model=$(extract_field "$AGENT_FILE" "model")
assert_eq "sonnet" "$model"

set_test "consensus-synthesizer effort is max (max-thinking policy)"
effort=$(extract_field "$AGENT_FILE" "effort")
assert_eq "max" "$effort"

set_test "consensus-synthesizer maxTurns exists and is positive"
max_turns=$(extract_field "$AGENT_FILE" "maxTurns")
assert_gt "$max_turns" 0

# ===========================================================================
# uat-runbook-author
# ===========================================================================
section "uat-runbook-author"

AGENT_FILE="$AGENTS_DIR/uat-runbook-author.md"
TOOLS=$(extract_tools "$AGENT_FILE")

for tool in Read Edit Write Bash Grep Glob; do
  set_test "uat-runbook-author has $tool"
  assert_tool_present "$TOOLS" "$tool" "uat-runbook-author"
done

set_test "uat-runbook-author does NOT have Skill (terminal worker)"
assert_tool_absent "$TOOLS" "Skill" "uat-runbook-author"

set_test "uat-runbook-author has no mcp__ tools"
assert_no_mcp_tools "$TOOLS" "uat-runbook-author"

set_test "uat-runbook-author model is sonnet (read-and-synthesize task)"
model=$(extract_field "$AGENT_FILE" "model")
assert_eq "sonnet" "$model"

set_test "uat-runbook-author effort is max (max-thinking policy)"
effort=$(extract_field "$AGENT_FILE" "effort")
assert_eq "max" "$effort"

set_test "uat-runbook-author maxTurns exists and is positive"
max_turns=$(extract_field "$AGENT_FILE" "maxTurns")
assert_gt "$max_turns" 0

# ===========================================================================
# Universal: single orchestrator invariant — no subagent may dispatch
# ===========================================================================
# Enforces the architectural rule documented in
# references/agent-teams-integration.md §Single orchestrator invariant:
# only the main session (which loads the speckit-autopilot skill) may
# spawn subagents or create Agent Teams. Phase agents are terminal
# workers — they MUST NOT have the Agent tool (subagent nesting) or
# any team-management tool (team creation).
section "Single orchestrator invariant — universal denial"

for agent_file in "$AGENTS_DIR"/*.md; do
  agent_name=$(basename "$agent_file" .md)
  TOOLS=$(extract_tools "$agent_file")

  # Subagent-nesting prevention
  set_test "$agent_name does NOT have Agent tool (subagents cannot nest)"
  assert_tool_absent "$TOOLS" "Agent" "$agent_name"

  # Team-creation prevention — denylist known team-management tools.
  # Per Anthropic's Agent Teams docs, team-lead is the main session;
  # only it can create teams. Any subagent with these tools could
  # attempt to upgrade itself to a team-lead, violating the invariant.
  for team_tool in TeamCreate SendMessage; do
    set_test "$agent_name does NOT have $team_tool (team-lead is main session only)"
    assert_tool_absent "$TOOLS" "$team_tool" "$agent_name"
  done
done

# ─────────────────────────────────────────
# Codex Agent Sandbox Mode Validation
# ─────────────────────────────────────────

CODEX_AGENTS_DIR="$PLUGIN_ROOT/codex-agents"

if [ -d "$CODEX_AGENTS_DIR" ]; then

  section "Codex Agent Sandbox Mode Scoping"

  # Read-only analysts and question-prep agents must have sandbox_mode: read-only
  for agent in codebase-analyst spec-context-analyst domain-researcher clarify-executor; do
    AGENT_FILE="$CODEX_AGENTS_DIR/${agent}.toml"
    if [ -f "$AGENT_FILE" ]; then
      sandbox=$(extract_toml_field "$AGENT_FILE" "sandbox_mode")
      set_test "codex ${agent}: sandbox_mode is read-only"
      assert_eq "read-only" "$sandbox" "${agent} must be read-only"

      model=$(extract_toml_field "$AGENT_FILE" "model")
      set_test "codex ${agent}: model is gpt-5.5"
      assert_eq "gpt-5.5" "$model" "${agent} must use gpt-5.5"

      # Plugin policy: every Codex agent defaults to xhigh reasoning. Lower
      # effort is acceptable only when a Layer 6 efficiency benchmark proves
      # quality=1.0 at the lower level on the agent's scored fixtures
      # (tests/layer6-efficiency/results-codex/*.json).
      effort=$(extract_toml_field "$AGENT_FILE" "model_reasoning_effort")
      case "$agent" in
        codebase-analyst|spec-context-analyst)
          # L6-validated: quality=1.0 at low and xhigh on 2026-05-25 smoke.
          set_test "codex ${agent}: reasoning is L6-validated (low or xhigh)"
          if [ "$effort" = "low" ] || [ "$effort" = "xhigh" ]; then
            _pass
          else
            _fail "${agent} reasoning must be low (L6-validated 100%) or xhigh (policy default), got '$effort'"
          fi
          ;;
        *)
          # No L6 evidence of quality=1.0 at lower effort — must remain xhigh.
          set_test "codex ${agent}: reasoning is xhigh (max-thinking policy, no L6 carve-out)"
          assert_eq "xhigh" "$effort" "${agent} must use xhigh reasoning per plugin policy"
          ;;
      esac
    fi
  done

  # clarify-executor read-only sandbox check (effort + model already verified
  # in the read-only-analysts loop above)
  for agent in clarify-executor; do
    AGENT_FILE="$CODEX_AGENTS_DIR/${agent}.toml"
    if [ -f "$AGENT_FILE" ]; then
      sandbox=$(extract_toml_field "$AGENT_FILE" "sandbox_mode")
      set_test "codex ${agent}: sandbox_mode is read-only"
      assert_eq "read-only" "$sandbox" "${agent} must be read-only"
    fi
  done

  # Write agents must have sandbox_mode: workspace-write
  for agent in checklist-executor analyze-executor implement-executor phase-executor uat-runbook-author; do
    AGENT_FILE="$CODEX_AGENTS_DIR/${agent}.toml"
    if [ -f "$AGENT_FILE" ]; then
      sandbox=$(extract_toml_field "$AGENT_FILE" "sandbox_mode")
      set_test "codex ${agent}: sandbox_mode is workspace-write"
      assert_eq "workspace-write" "$sandbox" "${agent} must be workspace-write"

      model=$(extract_toml_field "$AGENT_FILE" "model")
      effort=$(extract_toml_field "$AGENT_FILE" "model_reasoning_effort")
      set_test "codex ${agent}: model is gpt-5.5"
      assert_eq "gpt-5.5" "$model" "${agent} must use gpt-5.5"

      set_test "codex ${agent}: reasoning is xhigh (max-thinking policy)"
      assert_eq "xhigh" "$effort" "${agent} must use xhigh reasoning per plugin policy"
    fi
  done

fi

# ===========================================================================
# Named-tool regression guard (TACD-004 FR-001 / US1)
# ===========================================================================
# Fails when an ACTIVE agent's guidance PROSE reintroduces a hardcoded named
# optional-tool preference (a vendor-qualified `mcp__<vendor>__<tool>` token).
# ANY vendor-qualified token found in prose is a violation unless it is an exact
# literal entry in PROSE_TOKEN_ALLOWLIST (an enumerated token list, empty by
# default — there is no category or heuristic matching here). This locks the
# vendor-neutral capability-discovery decision (TACD-002): a future edit that
# re-teaches a specific vendor tool by name in agent guidance is caught
# automatically.
#
# What is scanned (prose only):
#   - Claude: the markdown BODY of speckit-pro/agents/*.md (everything AFTER
#     the closing `---` of the YAML frontmatter).
#   - Codex:  the instruction PROSE of speckit-pro/codex-agents/*.toml (the
#     `developer_instructions = """ ... """` block, NOT the structured
#     name/model/sandbox config keys).
#
# False-positive carve-outs honored BY CONSTRUCTION (spike-approved categories,
# docs/ai/research/tool-agnostic-capability-discovery-spike.md §"TACD-004
# Allowlist Recommendation" — reused, not redefined):
#   - generic `mcp`/`MCP` vocabulary: a bare token with no `__<vendor>__`
#     qualifier never matches the vendor-qualified pattern below;
#   - runtime/dependency metadata IDs (the frontmatter `tools:` list, e.g.
#     implement-executor's mcp__* entries): excluded because only the body/
#     prose is scanned, never the frontmatter or TOML config keys;
#   - fixtures and historical/provenance mentions: out of scope because only
#     ACTIVE agent source is scanned (not tests/**/fixtures/** or docs/**).
# An explicit literal allowlist (PROSE_TOKEN_ALLOWLIST) covers the rare case of
# an active-agent prose token that is legitimate metadata; it is an enumerated
# set (not a heuristic) and is empty by default — no active-agent prose
# currently needs a vendor-qualified token.
section "Named-tool regression guard (vendor-qualified tokens in agent prose)"

# CODEX_AGENTS_DIR is already set above (Codex sandbox section).

# Vendor-qualified detection shape: mcp__<vendor>__<tool>. A bare `mcp`/`MCP`
# word with no `__<vendor>__` qualifier is allowed by construction.
NAMED_TOOL_PATTERN='mcp__[A-Za-z0-9-]+__[A-Za-z0-9_-]+'

# Literal, enumerated allowlist of vendor-qualified tokens that are legitimate
# WHERE THEY APPEAR IN PROSE (e.g. an exact dependency/metadata identifier a
# runtime requires). Kept minimal and auditable; empty by default. Do NOT
# widen this to silence an agent that simply re-teaches a named preference.
PROSE_TOKEN_ALLOWLIST=()

# Extract the Claude markdown body: everything after the 2nd `---` line.
extract_md_body() {
  local file="$1"
  awk 'BEGIN{d=0} /^---$/{d++; next} d>=2{print}' "$file"
}

# Extract the Codex developer_instructions prose: the lines between the
# `developer_instructions = """` opener and its closing `"""`.
extract_toml_prose() {
  local file="$1"
  awk '
    /^developer_instructions = """/ { ins=1; next }
    ins && /^"""[[:space:]]*$/      { ins=0; next }
    ins                            { print }
  ' "$file"
}

# Returns the first non-allowlisted vendor-qualified token in $1, else empty.
first_named_tool_violation() {
  local text="$1" tok allowed
  while IFS= read -r tok; do
    [ -z "$tok" ] && continue
    allowed=false
    for a in ${PROSE_TOKEN_ALLOWLIST+"${PROSE_TOKEN_ALLOWLIST[@]}"}; do
      if [ "$tok" = "$a" ]; then allowed=true; break; fi
    done
    if [ "$allowed" = "false" ]; then
      printf '%s' "$tok"
      return
    fi
  done < <(printf '%s\n' "$text" | grep -oE "$NAMED_TOOL_PATTERN" | sort -u)
}

# Fail-closed: build the active-agent file list and assert it is non-empty so
# the guard can never pass vacuously by scanning nothing (FR-012).
named_guard_files=()
for f in "$AGENTS_DIR"/*.md; do
  [ -e "$f" ] && named_guard_files+=("$f")
done
if [ -d "$CODEX_AGENTS_DIR" ]; then
  for f in "$CODEX_AGENTS_DIR"/*.toml; do
    [ -e "$f" ] && named_guard_files+=("$f")
  done
fi

set_test "named-tool guard: active-agent set is non-empty (fail-closed)"
if [ "${#named_guard_files[@]}" -gt 0 ]; then
  _pass
else
  _fail "no active agents matched speckit-pro/agents/*.md or codex-agents/*.toml — guard would pass vacuously"
fi

for agent_file in "${named_guard_files[@]}"; do
  agent_name=$(basename "$agent_file")
  case "$agent_file" in
    *.md)   prose=$(extract_md_body "$agent_file") ;;
    *.toml) prose=$(extract_toml_prose "$agent_file") ;;
  esac

  set_test "$agent_name guidance prose has no hardcoded named vendor tool"
  violation=$(first_named_tool_violation "$prose")
  if [ -z "$violation" ]; then
    _pass
  else
    _fail "$agent_name prose names vendor-qualified optional tool '$violation' — use capability discovery, not a hardcoded tool (TACD-004 FR-001)"
  fi
done

# ===========================================================================
test_summary
