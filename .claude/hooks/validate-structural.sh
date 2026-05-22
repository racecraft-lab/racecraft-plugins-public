#!/usr/bin/env bash
# PostToolUse hook: when Claude edits a SKILL.md, plugin manifest, or marketplace registry,
# run the Layer 1 structural test for the affected plugin. Fast (~5s), catches
# missing frontmatter / invalid JSON before commit.
#
# Receives Claude Code hook JSON on stdin:
#   { "tool_name": "Edit"|"Write", "tool_input": { "file_path": "...", ... }, ... }
#
# Exit codes:
#   0 = pass (or no-op if file doesn't match)
#   2 = surface stderr to user (validation failed)
set -euo pipefail

# Find repo root from this script's location
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Parse stdin JSON; tolerate jq missing (degrade to no-op)
if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

payload="$(cat)"
file_path="$(printf '%s' "$payload" | jq -r '.tool_input.file_path // empty')"

if [[ -z "$file_path" ]]; then
  exit 0
fi

# Match the file path against the structural-test trigger patterns.
# We only care about files inside the repo.
case "$file_path" in
  *"/SKILL.md"|\
  *"/.claude-plugin/plugin.json"|\
  *"/.codex-plugin/plugin.json"|\
  *"/.claude-plugin/marketplace.json"|\
  *"/release-please-config.json"|\
  *"/.release-please-manifest.json"|\
  *"/commands/"*.md)
    ;;
  *)
    exit 0
    ;;
esac

# Determine which plugin to validate.
# For files under <plugin>/.../  pick that plugin.
# For top-level files (release config, manifest, marketplace), validate the whole marketplace via speckit-pro tests.
plugin_dir=""
rel_path="${file_path#"$REPO_ROOT"/}"

case "$rel_path" in
  speckit-pro/*) plugin_dir="speckit-pro" ;;
  *)
    # Top-level file or unknown plugin — default to speckit-pro (only plugin currently)
    plugin_dir="speckit-pro"
    ;;
esac

target="$REPO_ROOT/$plugin_dir"
if [[ ! -d "$target" ]] || [[ ! -f "$target/tests/run-all.sh" ]]; then
  exit 0
fi

# Run Layer 1 only — fast, deterministic, no AI cost.
# Suppress passing output to keep the hook quiet; only surface on failure.
output="$(cd "$target" && bash tests/run-all.sh --layer 1 2>&1)" || {
  printf '⚠️  Layer 1 structural test failed for %s after edit to %s:\n\n%s\n' \
    "$plugin_dir" "$rel_path" "$output" >&2
  exit 2
}

exit 0
