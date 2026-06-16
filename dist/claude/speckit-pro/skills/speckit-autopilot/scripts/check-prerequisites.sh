#!/usr/bin/env bash
# check-prerequisites.sh — Verify all autopilot prerequisites
#
# Usage: check-prerequisites.sh [workflow_file]
# Output: JSON to stdout with pass/fail for each check
# Exit:   0 = all pass, 1 = one or more failed, 2 = usage error

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/specify-cli.sh"

WORKFLOW_FILE="${1:-}"

# Helper: emit a single JSON check object, safely escaping all string values
json_result() {
  local check="$1" pass="$2" message="$3" detail="${4:-}"
  jq -cn \
    --arg check "$check" \
    --argjson pass "$pass" \
    --arg message "$message" \
    --arg detail "$detail" \
    '{"check":$check,"pass":$pass,"message":$message,"detail":$detail}'
}

results=()
all_pass=true

# 0.1 SpecKit CLI
if speckit_have_specify; then
  version=$(speckit_specify --version 2>/dev/null || echo "unknown")
  results+=("$(json_result "speckit_cli" "true" "SpecKit CLI installed" "$version")")
else
  results+=("$(json_result "speckit_cli" "false" "SpecKit CLI not found. Install: uv tool install specify-cli --from git+https://github.com/github/spec-kit.git" "")")
  all_pass=false
fi

# 0.2 Project Initialized
if [ -d ".specify" ]; then
  results+=("$(json_result "project_init" "true" "Project initialized" "")")
else
  results+=("$(json_result "project_init" "false" "SpecKit not initialized. Run: specify init --ai claude" "")")
  all_pass=false
fi

# 0.3 Constitution Exists
if [ -f ".specify/memory/constitution.md" ]; then
  results+=("$(json_result "constitution" "true" "Constitution exists" "")")
else
  results+=("$(json_result "constitution" "false" "No constitution found. Run: /speckit-constitution" "")")
  all_pass=false
fi

# 0.4 SpecKit Commands Installed
missing_cmds=()
# SpecKit v0.8.13+ installs the core SDD phases as SKILLS. Autopilot runs under
# both Claude Code (.claude/skills/<cmd>/SKILL.md) and Codex
# (.codex/skills/<cmd>/SKILL.md), and this same script serves both — so a command
# counts as installed if it exists as a skill on EITHER platform. Only the
# project-local install dirs are checked: the plugin's own bundled codex-skills/
# must NOT count, or the gate would false-pass for every project.
for cmd in speckit-specify speckit-plan speckit-tasks speckit-implement; do
  if [ ! -f ".claude/skills/${cmd}/SKILL.md" ] \
    && [ ! -f ".codex/skills/${cmd}/SKILL.md" ]; then
    missing_cmds+=("$cmd")
  fi
done
if [ ${#missing_cmds[@]} -eq 0 ]; then
  results+=("$(json_result "commands" "true" "All SpecKit commands installed" "")")
else
  results+=("$(json_result "commands" "false" "Missing commands: ${missing_cmds[*]}. Run: specify integration install <claude|codex>" "")")
  all_pass=false
fi

# 0.5 Workflow File Exists
if [ -n "$WORKFLOW_FILE" ]; then
  if [ -f "$WORKFLOW_FILE" ]; then
    results+=("$(json_result "workflow_file" "true" "Workflow file exists" "$WORKFLOW_FILE")")
  else
    results+=("$(json_result "workflow_file" "false" "Workflow file not found: $WORKFLOW_FILE" "")")
    all_pass=false
  fi
else
  results+=("$(json_result "workflow_file" "false" "No workflow file path provided" "")")
  all_pass=false
fi

# 0.7 Branch Detection
current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
git_dir=$(git rev-parse --git-dir 2>/dev/null || echo "")
git_common=$(git rev-parse --git-common-dir 2>/dev/null || echo "")

is_worktree="false"
if [ -n "$git_dir" ] && [ -n "$git_common" ] && [ "$git_dir" != "$git_common" ]; then
  is_worktree="true"
fi

on_feature_branch="false"
# Match classic NNN- feature branches AND letter-suffixed spec slices
# (e.g. 006a-, 013b-) that the roadmaps decompose specs into.
if echo "$current_branch" | grep -qE '^[0-9]{3}[A-Za-z0-9]*-'; then
  on_feature_branch="true"
fi

results+=("$(json_result "branch" "true" "Branch: $current_branch" "worktree=$is_worktree,feature=$on_feature_branch")")

# 0.6 Settings (check file existence, content parsed by caller)
settings_file=".claude/speckit-pro.local.md"
if [ -f "$settings_file" ]; then
  results+=("$(json_result "settings" "true" "Settings file exists" "$settings_file")")
else
  results+=("$(json_result "settings" "true" "No settings file — using defaults" "")")
fi

# 0.8 MCP Server Connectivity (informational — not blocking)
# Plugin agents cannot declare their own MCP connections, so
# they depend on the parent session having these servers.
# These are informational: all agents have built-in fallbacks.
mcp_servers=("tavily-mcp" "context7" "RepoPrompt")
mcp_available=()
mcp_missing=()
for server in "${mcp_servers[@]}"; do
  # Check if any MCP tools from this server are available
  # by looking for the server name in the MCP config files
  if [ -f ".mcp.json" ] && jq -e ".mcpServers.\"$server\" // .mcpServers.\"${server}\"" .mcp.json >/dev/null 2>&1; then
    mcp_available+=("$server")
  elif [ -f "$HOME/.claude/.mcp.json" ] && jq -e ".mcpServers.\"$server\" // .mcpServers.\"${server}\"" "$HOME/.claude/.mcp.json" >/dev/null 2>&1; then
    mcp_available+=("$server")
  else
    mcp_missing+=("$server")
  fi
done

if [ ${#mcp_missing[@]} -eq 0 ]; then
  results+=("$(json_result "mcp_servers" "true" "All MCP servers configured: ${mcp_available[*]}" "")")
else
  detail=""
  if [ ${#mcp_available[@]} -gt 0 ]; then
    detail="Available: ${mcp_available[*]}. "
  fi
  detail="${detail}Missing: ${mcp_missing[*]} (agents will use built-in fallbacks)"
  results+=("$(json_result "mcp_servers" "true" "Some MCP servers not configured — agents will use fallbacks" "$detail")")
fi

# Assemble final JSON — use jq to safely combine the pre-built check objects
checks_array=$(printf '%s\n' "${results[@]}" | jq -s '.')
jq -cn \
  --argjson all_pass "$all_pass" \
  --arg branch "$current_branch" \
  --argjson is_worktree "$is_worktree" \
  --argjson on_feature_branch "$on_feature_branch" \
  --argjson checks "$checks_array" \
  '{"all_pass":$all_pass,"branch":$branch,"is_worktree":$is_worktree,"on_feature_branch":$on_feature_branch,"checks":$checks}'

if [ "$all_pass" = "true" ]; then
  exit 0
else
  exit 1
fi
