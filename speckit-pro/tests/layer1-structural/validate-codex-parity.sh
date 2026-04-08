#!/usr/bin/env bash
# validate-codex-parity.sh — Cross-platform parity checks ensuring Claude Code
# and Codex files stay in sync.
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

CC_PLUGIN="$PLUGIN_ROOT/.claude-plugin/plugin.json"
CODEX_PLUGIN="$PLUGIN_ROOT/.codex-plugin/plugin.json"
AGENTS_DIR="$PLUGIN_ROOT/agents"
CODEX_AGENTS_DIR="$PLUGIN_ROOT/codex-agents"
SKILLS_DIR="$PLUGIN_ROOT/skills"
CODEX_SKILLS_DIR="$PLUGIN_ROOT/codex-skills"

# ===========================================================================
# Version Parity
# ===========================================================================
section "Version Parity"

set_test "both plugin.json files exist"
if [ -f "$CC_PLUGIN" ] && [ -f "$CODEX_PLUGIN" ]; then
  _pass
else
  _fail "missing one or both plugin.json files (CC: $CC_PLUGIN, Codex: $CODEX_PLUGIN)"
fi

if [ -f "$CC_PLUGIN" ] && [ -f "$CODEX_PLUGIN" ]; then
  cc_version=$(jq -r '.version' "$CC_PLUGIN")
  codex_version=$(jq -r '.version' "$CODEX_PLUGIN")

  set_test "CC and Codex plugin.json versions match ($cc_version)"
  assert_eq "$cc_version" "$codex_version" "versions must match: CC=$cc_version, Codex=$codex_version"
fi

# ===========================================================================
# Agent Parity — CC agents → Codex agents
# ===========================================================================
section "Agent Parity (CC → Codex)"

# Agents that are intentionally CC-only (use CC-specific capabilities like
# shell-based gate validation or multi-agent consensus synthesis).
CC_ONLY_AGENTS=(gate-validator consensus-synthesizer)

is_cc_only() {
  local name="$1"
  for cc_only in "${CC_ONLY_AGENTS[@]}"; do
    [ "$name" = "$cc_only" ] && return 0
  done
  return 1
}

if [ -d "$AGENTS_DIR" ] && [ -d "$CODEX_AGENTS_DIR" ]; then
  for cc_agent_file in "$AGENTS_DIR"/*.md; do
    [ -f "$cc_agent_file" ] || continue
    agent_name=$(basename "$cc_agent_file" .md)
    if is_cc_only "$agent_name"; then
      continue
    fi
    set_test "codex-agents/${agent_name}.md exists for CC agent"
    assert_file_exists "$CODEX_AGENTS_DIR/${agent_name}.md"
  done
else
  set_test "agents/ and codex-agents/ directories exist"
  _fail "one or both agent directories missing (CC: $AGENTS_DIR, Codex: $CODEX_AGENTS_DIR)"
fi

# ===========================================================================
# Agent Parity — Codex agents → CC agents
# ===========================================================================
section "Agent Parity (Codex → CC)"

if [ -d "$AGENTS_DIR" ] && [ -d "$CODEX_AGENTS_DIR" ]; then
  for codex_agent_file in "$CODEX_AGENTS_DIR"/*.md; do
    [ -f "$codex_agent_file" ] || continue
    agent_name=$(basename "$codex_agent_file" .md)
    set_test "agents/${agent_name}.md exists for Codex agent"
    assert_file_exists "$AGENTS_DIR/${agent_name}.md"
  done
fi

# ===========================================================================
# Skill Parity — CC skills → Codex skills
# ===========================================================================
section "Skill Parity (CC → Codex)"

if [ -d "$SKILLS_DIR" ] && [ -d "$CODEX_SKILLS_DIR" ]; then
  for cc_skill_dir in "$SKILLS_DIR"/*/; do
    [ -d "$cc_skill_dir" ] || continue
    skill_name=$(basename "$cc_skill_dir")
    set_test "codex-skills/${skill_name}/ directory exists"
    if [ -d "$CODEX_SKILLS_DIR/${skill_name}" ]; then
      _pass
    else
      _fail "missing codex-skills/${skill_name}/"
    fi

    set_test "codex-skills/${skill_name}/SKILL.md exists"
    assert_file_exists "$CODEX_SKILLS_DIR/${skill_name}/SKILL.md"
  done
else
  set_test "skills/ and codex-skills/ directories exist"
  _fail "one or both skills directories missing (CC: $SKILLS_DIR, Codex: $CODEX_SKILLS_DIR)"
fi

# ===========================================================================
# Shared Reference Integrity — Codex skills reference CC references/
# ===========================================================================
section "Shared Reference Integrity"

if [ -d "$CODEX_SKILLS_DIR" ]; then
  for codex_skill_dir in "$CODEX_SKILLS_DIR"/*/; do
    [ -d "$codex_skill_dir" ] || continue
    skill_name=$(basename "$codex_skill_dir")
    cc_refs="$SKILLS_DIR/${skill_name}/references"

    set_test "${skill_name}: CC skill references/ directory exists"
    if [ -d "$cc_refs" ]; then
      _pass
    else
      _fail "missing skills/${skill_name}/references/"
      continue
    fi

    set_test "${skill_name}: CC skill references/ has at least one file"
    ref_count=$(find "$cc_refs" -maxdepth 1 -type f | wc -l | tr -d ' ')
    if [ "$ref_count" -gt 0 ]; then
      _pass
    else
      _fail "skills/${skill_name}/references/ exists but contains no files"
    fi
  done
fi

test_summary
