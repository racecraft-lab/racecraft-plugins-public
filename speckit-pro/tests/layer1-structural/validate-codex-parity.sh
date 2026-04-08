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
COMMANDS_DIR="$PLUGIN_ROOT/commands"
SHARED_SKILLS=(speckit-autopilot speckit-coach)
COMMAND_SKILL_MAP=(
  "autopilot:speckit-autopilot"
  "coach:speckit-coach"
  "setup:speckit-setup"
  "status:speckit-status"
  "resolve-pr:speckit-resolve-pr"
)

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
# Shared Skill Parity — CC skills → Codex skills
# ===========================================================================
section "Shared Skill Parity (CC → Codex)"

if [ -d "$SKILLS_DIR" ] && [ -d "$CODEX_SKILLS_DIR" ]; then
  for skill_name in "${SHARED_SKILLS[@]}"; do
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
# Claude Command Coverage — CC commands → Codex skills
# ===========================================================================
section "Claude Command Coverage (CC → Codex skills)"

if [ -d "$COMMANDS_DIR" ] && [ -d "$CODEX_SKILLS_DIR" ]; then
  for mapping in "${COMMAND_SKILL_MAP[@]}"; do
    cmd_name="${mapping%%:*}"
    skill_name="${mapping##*:}"
    set_test "commands/${cmd_name}.md exists"
    assert_file_exists "$COMMANDS_DIR/${cmd_name}.md"

    set_test "codex-skills/${skill_name}/SKILL.md exists for CC command ${cmd_name}"
    assert_file_exists "$CODEX_SKILLS_DIR/${skill_name}/SKILL.md"
  done
else
  set_test "commands/ and codex-skills/ directories exist for command coverage"
  _fail "one or both directories missing (commands: $COMMANDS_DIR, codex-skills: $CODEX_SKILLS_DIR)"
fi

# ===========================================================================
# Codex Skill Source Coverage
# ===========================================================================
section "Codex Skill Source Coverage"

if [ -d "$CODEX_SKILLS_DIR" ]; then
  for mapping in "${COMMAND_SKILL_MAP[@]}"; do
    cmd_name="${mapping%%:*}"
    skill_name="${mapping##*:}"

    if [ "$skill_name" = "speckit-autopilot" ] || [ "$skill_name" = "speckit-coach" ]; then
      set_test "${skill_name}: corresponding CC skill exists"
      assert_file_exists "$SKILLS_DIR/${skill_name}/SKILL.md"
    else
      set_test "${skill_name}: corresponding CC command exists"
      assert_file_exists "$COMMANDS_DIR/${cmd_name}.md"
    fi
  done
else
  set_test "codex-skills/ directory exists for source coverage"
  _fail "codex-skills directory missing: $CODEX_SKILLS_DIR"
fi

# ===========================================================================
# Shared Reference Integrity — shared Codex skills reference CC references/
# ===========================================================================
section "Shared Reference Integrity"

if [ -d "$CODEX_SKILLS_DIR" ]; then
  for skill_name in "${SHARED_SKILLS[@]}"; do
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

    # Per-file check: every ../../skills/*/references/*.md path linked from the
    # Codex SKILL.md must resolve to an actual file under skills/.
    codex_skill_file="$CODEX_SKILLS_DIR/${skill_name}/SKILL.md"
    if [ -f "$codex_skill_file" ]; then
      ref_paths=$(grep -oE '\.\./\.\./skills/[^)]+\.md' "$codex_skill_file" | sort -u)
      while IFS= read -r rel_path; do
        [ -z "$rel_path" ] && continue
        # Strip the leading ../../ — paths are relative to the Codex skill dir,
        # which is two levels below the plugin root.
        resolved="$PLUGIN_ROOT/${rel_path#../../}"
        set_test "${skill_name}: referenced file exists (${rel_path#../../})"
        assert_file_exists "$resolved"
      done <<< "$ref_paths"
    fi
  done
fi

test_summary
