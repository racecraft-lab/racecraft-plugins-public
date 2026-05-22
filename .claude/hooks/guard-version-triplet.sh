#!/usr/bin/env bash
# PreToolUse hook: warn before editing the version-load-bearing JSON triplet.
# These files are normally only written by release-please. Manual edits should
# go through "Adding a New Plugin to Release Automation" or a Scenario 1-6
# recovery procedure in CLAUDE.md.
#
# Receives Claude Code hook JSON on stdin:
#   { "tool_name": "Edit"|"Write", "tool_input": { "file_path": "...", ... }, ... }
#
# Exit codes:
#   0 = allow
#   2 = block tool call, surface stderr to user (user can re-run to override after reading the warning)
set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

payload="$(cat)"
file_path="$(printf '%s' "$payload" | jq -r '.tool_input.file_path // empty')"

if [[ -z "$file_path" ]]; then
  exit 0
fi

case "$file_path" in
  *"/release-please-config.json"|\
  *"/.release-please-manifest.json"|\
  *"/.claude-plugin/marketplace.json")
    cat <<'EOF' >&2
⚠️  Editing version-load-bearing file

This file is normally only written by release-please or the marketplace-sync workflow.
Manual edits cascade silently — see CLAUDE.md:
  - "Adding a New Plugin to Release Automation" (legitimate manual edit)
  - "Recovery & Rollback" Scenarios 1-6 (recovery from a bad state)

If this is intentional, ask the user to confirm before retrying the edit.
EOF
    exit 2
    ;;
esac

exit 0
