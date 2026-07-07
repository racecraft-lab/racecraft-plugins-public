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
# Tool-surface doctrine (operator-owned availability)
# ---------------------------------------------------------------------------
# The plugin never pins which tools an agent MAY use. Per the official Claude
# Code docs (code.claude.com/docs/en/subagents: "Inherits all tools if
# omitted" — including MCP tools; and the parent conversation's permission
# rules govern subagent tool calls), omitting `tools:` gives every agent the
# operator's full installed surface — present and future — governed by the
# operator's own permission configuration. This matches the Codex side of the
# same plugin, where agent TOMLs have no tool-restriction field at all and
# per-tool governance is operator machinery (config layers, rules, hooks —
# all trust-gated; developers.openai.com/codex/subagents, /codex/config-reference).
#
# What the plugin DOES pin, via `disallowedTools` (a comma-separated scalar per
# code.claude.com/docs/en/subagents; supported for plugin agents per
# /docs/en/plugins-reference), is built-in ROLE-INTEGRITY denials only:
#   - Single orchestrator invariant: subagents can nest as of Claude Code
#     v2.1.172 (depth-limited, not prevented), so every phase agent must
#     explicitly deny Agent + team tools — only the main-session orchestrator
#     fans out (references/agent-teams-integration.md).
#   - Read-only consensus roles deny the built-in mutation primitives
#     (Write/Edit/NotebookEdit/Bash) — the Claude twin of the Codex agents'
#     kept `sandbox_mode = "read-only"`. Consensus integrity depends on
#     analysts not mutating artifacts mid-round.
#   - Workflow discipline: terminal workers deny Skill so a single-task agent
#     cannot re-enter /speckit-* phases recursively.
# Denials name BUILT-IN tools only — never a vendor-qualified MCP tool. An
# unknown installed capability is never blocked by this plugin.

ORCHESTRATION_DENIALS=(Agent TeamCreate SendMessage)
MUTATION_DENIALS=(Write Edit NotebookEdit Bash)

# ---------------------------------------------------------------------------
# Helper: extract YAML frontmatter (between the first pair of --- lines)
# ---------------------------------------------------------------------------
extract_frontmatter() {
  local file="$1"
  awk 'BEGIN{d=0} /^---$/{d++; if(d==2) exit; next} d==1{print}' "$file"
}

# ---------------------------------------------------------------------------
# Helper: extract the disallowedTools list (comma-separated scalar), one per line
# ---------------------------------------------------------------------------
extract_disallowed() {
  local file="$1"
  extract_frontmatter "$file" | \
    grep '^disallowedTools:' | \
    head -1 | \
    sed 's/^disallowedTools:[[:space:]]*//' | \
    tr ',' '\n' | \
    sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | \
    grep -v '^$' || true
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
# Helper: assert a tool IS in the disallowedTools list
# ---------------------------------------------------------------------------
assert_denied() {
  local denials="$1" tool="$2" agent="$3"
  local found=false
  while IFS= read -r line; do
    if [ "$line" = "$tool" ]; then
      found=true
      break
    fi
  done <<< "$denials"
  if [ "$found" = "true" ]; then
    _pass
  else
    _fail "$agent must deny '$tool' in disallowedTools but does not"
  fi
}

# ---------------------------------------------------------------------------
# Helper: assert a tool is NOT in the disallowedTools list (the agent needs it)
# ---------------------------------------------------------------------------
assert_not_denied() {
  local denials="$1" tool="$2" agent="$3"
  local found=false
  while IFS= read -r line; do
    if [ "$line" = "$tool" ]; then
      found=true
      break
    fi
  done <<< "$denials"
  if [ "$found" = "false" ]; then
    _pass
  else
    _fail "$agent denies '$tool' but its role requires it"
  fi
}

# ===========================================================================
# Universal: operator-owned tool surface — no allowlist pinning
# ===========================================================================
section "Operator tool surface — no tools: allowlist pinning"

for agent_file in "$AGENTS_DIR"/*.md; do
  agent_name=$(basename "$agent_file" .md)
  FRONTMATTER=$(extract_frontmatter "$agent_file")

  set_test "$agent_name has NO tools: allowlist (inherits the operator's full surface)"
  if printf '%s\n' "$FRONTMATTER" | grep -q '^tools:'; then
    _fail "$agent_name pins a tools: allowlist — availability is operator-owned; use disallowedTools for role denials only"
  else
    _pass
  fi

  set_test "$agent_name declares disallowedTools (role-integrity denials are mandatory)"
  if printf '%s\n' "$FRONTMATTER" | grep -q '^disallowedTools:'; then
    _pass
  else
    _fail "$agent_name is missing disallowedTools — at minimum the single-orchestrator denials are required"
  fi

  # Denials must name built-in tools only. A vendor-qualified token anywhere
  # in frontmatter would reintroduce named-vendor pinning through the back
  # door (blocking one vendor's tool is still a named-vendor contract).
  set_test "$agent_name frontmatter has no vendor-qualified mcp__ token"
  if printf '%s\n' "$FRONTMATTER" | grep -qE 'mcp__[A-Za-z0-9-]+__[A-Za-z0-9_-]+'; then
    _fail "$agent_name frontmatter names a vendor-qualified MCP tool — the plugin neither grants nor blocks named vendor tools"
  else
    _pass
  fi
done

# ===========================================================================
# Universal: single orchestrator invariant — no subagent may dispatch
# ===========================================================================
# Subagents CAN spawn subagents as of Claude Code v2.1.172 (depth-limited to
# 5, not prevented), so with an inherited tool surface this invariant MUST be
# an explicit denial: only the main session (which loads the
# speckit-autopilot skill) may spawn subagents or create Agent Teams. Phase
# agents are terminal workers.
section "Single orchestrator invariant — universal denial"

for agent_file in "$AGENTS_DIR"/*.md; do
  agent_name=$(basename "$agent_file" .md)
  DENIALS=$(extract_disallowed "$agent_file")

  for tool in "${ORCHESTRATION_DENIALS[@]}"; do
    set_test "$agent_name denies $tool (single orchestrator invariant)"
    assert_denied "$DENIALS" "$tool" "$agent_name"
  done
done

# ===========================================================================
# Read-only consensus roles — mutation primitives denied
# ===========================================================================
# The Claude twin of the Codex agents' sandbox_mode = "read-only": consensus
# analysts and question-prep agents must not mutate state mid-round. They
# inherit every installed read/research capability (that is the point), and
# capability-discovery.md's role rule covers tools the platform cannot
# classify; the built-in mutation primitives are denied outright.
section "Read-only roles deny built-in mutation primitives"

for agent in codebase-analyst spec-context-analyst domain-researcher clarify-executor consensus-synthesizer; do
  AGENT_FILE="$AGENTS_DIR/$agent.md"
  DENIALS=$(extract_disallowed "$AGENT_FILE")

  for tool in "${MUTATION_DENIALS[@]}"; do
    set_test "$agent denies $tool (read-only role)"
    assert_denied "$DENIALS" "$tool" "$agent"
  done

  set_test "$agent denies Skill (consensus workers do not re-enter phases)"
  assert_denied "$DENIALS" "Skill" "$agent"
done

# ===========================================================================
# gate-validator — validates, never fixes; needs the shell it runs gates with
# ===========================================================================
section "gate-validator"

AGENT_FILE="$AGENTS_DIR/gate-validator.md"
DENIALS=$(extract_disallowed "$AGENT_FILE")

for tool in Write Edit NotebookEdit Skill; do
  set_test "gate-validator denies $tool (validates, never fixes)"
  assert_denied "$DENIALS" "$tool" "gate-validator"
done

set_test "gate-validator does NOT deny Bash (runs gate scripts)"
assert_not_denied "$DENIALS" "Bash" "gate-validator"

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
# Terminal single-task workers — deny Skill, keep mutation
# ===========================================================================
section "Terminal workers deny Skill, keep their mutation surface"

for agent in implement-executor uat-runbook-author; do
  AGENT_FILE="$AGENTS_DIR/$agent.md"
  DENIALS=$(extract_disallowed "$AGENT_FILE")

  set_test "$agent denies Skill (terminal worker, no phase re-entry)"
  assert_denied "$DENIALS" "Skill" "$agent"

  for tool in Write Edit Bash; do
    set_test "$agent does NOT deny $tool (mutating role requires it)"
    assert_not_denied "$DENIALS" "$tool" "$agent"
  done
done

set_test "uat-runbook-author model is sonnet (read-and-synthesize task)"
model=$(extract_field "$AGENTS_DIR/uat-runbook-author.md" "model")
assert_eq "sonnet" "$model"

# ===========================================================================
# Skill-driven executors — full surface minus orchestration
# ===========================================================================
section "Skill-driven executors keep Skill and their mutation surface"

for agent in phase-executor analyze-executor checklist-executor; do
  AGENT_FILE="$AGENTS_DIR/$agent.md"
  DENIALS=$(extract_disallowed "$AGENT_FILE")

  for tool in Skill Write Edit Bash; do
    set_test "$agent does NOT deny $tool (skill-driven executor requires it)"
    assert_not_denied "$DENIALS" "$tool" "$agent"
  done
done

# ===========================================================================
# Session-shape metadata every agent must carry
# ===========================================================================
section "Session-shape metadata (maxTurns / effort)"

for agent_file in "$AGENTS_DIR"/*.md; do
  agent_name=$(basename "$agent_file" .md)

  set_test "$agent_name maxTurns exists and is positive"
  max_turns=$(extract_field "$agent_file" "maxTurns")
  assert_gt "$max_turns" 0

  set_test "$agent_name effort field exists"
  effort=$(extract_field "$agent_file" "effort")
  assert_not_contains "" "$effort" "effort must not be empty"
done

set_test "phase-executor effort is max (max-thinking policy)"
effort=$(extract_field "$AGENTS_DIR/phase-executor.md" "effort")
assert_eq "max" "$effort"

set_test "consensus-synthesizer model is sonnet"
model=$(extract_field "$AGENTS_DIR/consensus-synthesizer.md" "model")
assert_eq "sonnet" "$model"

set_test "consensus-synthesizer effort is max (max-thinking policy)"
effort=$(extract_field "$AGENTS_DIR/consensus-synthesizer.md" "effort")
assert_eq "max" "$effort"

# ─────────────────────────────────────────
# Codex Agent Sandbox Mode Validation
# ─────────────────────────────────────────
#
# Scope of the read-only guarantee on Codex: `sandbox_mode = "read-only"` is an
# OS-level sandbox over the agent's OWN shell/file operations only. It does NOT
# sandbox MCP server processes — a read-only Codex agent can still cause writes
# through an enabled write-capable MCP tool (confirmed by openai/codex; see the
# operator note in codex-skills/install/SKILL.md). Codex agent TOMLs cannot
# restrict tools (developers.openai.com/codex/subagents documents no per-tool
# allow/deny field), so closing that gap is an OPERATOR responsibility (curate
# write-capable MCP servers out at the profile level via enabled/enabled_tools/
# disabled_tools). This test asserts the filesystem read-only boundary that the
# plugin CAN enforce; the MCP boundary is documented for the operator, not
# enforceable here.

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
#   - fixtures and historical/provenance mentions: out of scope because only
#     ACTIVE agent source is scanned (not tests/**/fixtures/** or docs/**).
# Since the tools: allowlists were retired for an inherited operator surface,
# the frontmatter carries no vendor-qualified IDs either (enforced above by
# the frontmatter guard), so prose and metadata are BOTH vendor-neutral.
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
