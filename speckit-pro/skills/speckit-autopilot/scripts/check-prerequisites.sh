#!/usr/bin/env bash
# check-prerequisites.sh — Verify all autopilot prerequisites
#
# Usage: check-prerequisites.sh [workflow_file]
# Output: JSON to stdout with pass/fail for each check
# Exit:   0 = all pass, 1 = one or more failed, 2 = usage error

set -euo pipefail

WORKFLOW_FILE="${1:-}"

# Helper: emit JSON result
json_result() {
  local check="$1" pass="$2" message="$3" detail="${4:-}"
  printf '{"check":"%s","pass":%s,"message":"%s","detail":"%s"}\n' \
    "$check" "$pass" "$message" "$detail"
}

results=()
all_pass=true

# 0.1 SpecKit CLI
if command -v specify >/dev/null 2>&1; then
  version=$(specify --version 2>/dev/null || echo "unknown")
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
  results+=("$(json_result "constitution" "false" "No constitution found. Run: /speckit.constitution" "")")
  all_pass=false
fi

# 0.4 SpecKit Commands Installed
missing_cmds=()
for cmd in speckit.specify speckit.plan speckit.tasks speckit.implement; do
  if [ ! -f ".claude/commands/${cmd}.md" ]; then
    missing_cmds+=("$cmd")
  fi
done
if [ ${#missing_cmds[@]} -eq 0 ]; then
  results+=("$(json_result "commands" "true" "All SpecKit commands installed" "")")
else
  results+=("$(json_result "commands" "false" "Missing commands: ${missing_cmds[*]}. Run: specify init --ai claude" "")")
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
if echo "$current_branch" | grep -qE '^[0-9]{3}-'; then
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

# Assemble final JSON
printf '{"all_pass":%s,"branch":"%s","is_worktree":%s,"on_feature_branch":%s,"checks":[' \
  "$all_pass" "$current_branch" "$is_worktree" "$on_feature_branch"
for i in "${!results[@]}"; do
  [ "$i" -gt 0 ] && printf ','
  printf '%s' "${results[$i]}"
done
printf ']}\n'

if [ "$all_pass" = "true" ]; then
  exit 0
else
  exit 1
fi
