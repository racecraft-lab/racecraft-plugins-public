#!/usr/bin/env bash
# sync-marketplace-versions.sh -- Sync plugin versions from plugin.json to marketplace.json
#
# Reads each plugin's version from its plugin.json and updates the matching
# entry in .claude-plugin/marketplace.json. Registry-driven: iterates over
# marketplace.json plugins array, not filesystem scanning.
#
# Usage: Run from repository root
#   bash scripts/sync-marketplace-versions.sh
#
# Output: Sync summary to stdout (only when changes made)
# Errors: All error/info messages to stderr
# Exit:   0 = success (with or without changes), 1 = fatal error

set -euo pipefail

MARKETPLACE=".claude-plugin/marketplace.json"

# ─────────────────────────────────────────
# Prerequisite checks
# ─────────────────────────────────────────

# 1. jq dependency (must come first -- all subsequent operations need jq)
if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required but not found. Install it: brew install jq (macOS) or apt-get install jq (Linux)" >&2
  exit 1
fi

# 2. Working directory -- must be repo root
if [ ! -f "$MARKETPLACE" ]; then
  echo "Error: $MARKETPLACE not found. Run this script from the repository root." >&2
  exit 1
fi

# ─────────────────────────────────────────
# Parse and validate marketplace.json
# ─────────────────────────────────────────

# Validate plugins array exists
if ! jq -e '.plugins' "$MARKETPLACE" >/dev/null 2>&1; then
  echo "Error: $MARKETPLACE does not contain a 'plugins' array." >&2
  exit 1
fi

# Handle empty plugins array
plugin_count=$(jq '.plugins | length' "$MARKETPLACE")
if [ "$plugin_count" -eq 0 ]; then
  echo "Info: No plugins in $MARKETPLACE -- nothing to sync." >&2
  exit 0
fi

# ─────────────────────────────────────────
# Iterate plugins, read versions, build updated JSON
# ─────────────────────────────────────────

updated_json=$(cat "$MARKETPLACE")
changes=()

for i in $(seq 0 $((plugin_count - 1))); do
  # Extract source field
  source_field=$(jq -r ".plugins[$i].source // empty" "$MARKETPLACE")

  if [ -z "$source_field" ]; then
    entry_name=$(jq -r ".plugins[$i].name // \"index $i\"" "$MARKETPLACE")
    echo "Error: Plugin entry '$entry_name' (index $i) is missing the 'source' field." >&2
    exit 1
  fi

  # Skip non-relative sources (external repos)
  if [[ "$source_field" != ./* ]]; then
    echo "Info: Skipping non-relative source '$source_field' (index $i)." >&2
    continue
  fi

  # Resolve plugin.json path: strip leading ./ and append /.claude-plugin/plugin.json
  plugin_dir="${source_field#./}"
  plugin_json="${plugin_dir}/.claude-plugin/plugin.json"

  # Validate plugin.json exists
  if [ ! -f "$plugin_json" ]; then
    echo "Error: Plugin file not found: $plugin_json (referenced by marketplace entry at index $i)." >&2
    exit 1
  fi

  # Read version from plugin.json
  version=$(jq -e -r '.version' "$plugin_json" 2>/dev/null) || {
    echo "Error: No 'version' field in $plugin_json." >&2
    exit 1
  }

  # Validate semver format
  if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Invalid semver in $plugin_json: '$version'. Expected format: X.Y.Z" >&2
    exit 1
  fi

  # Read current marketplace version for comparison
  current_version=$(jq -r ".plugins[$i].version // empty" "$MARKETPLACE")

  # Update the in-memory JSON with the version from plugin.json
  updated_json=$(printf '%s' "$updated_json" | jq --arg ver "$version" --argjson idx "$i" '.plugins[$idx].version = $ver')

  # Track changes for summary
  if [ "$current_version" != "$version" ]; then
    changes+=("synced ${plugin_dir}: ${current_version:-<none>} -> ${version}")
  fi
done

# ─────────────────────────────────────────
# Idempotent write
# ─────────────────────────────────────────

existing_content=$(cat "$MARKETPLACE")

if [ "$updated_json" = "$existing_content" ]; then
  # No changes needed -- exit silently
  exit 0
fi

# Write updated content
printf '%s\n' "$updated_json" > "$MARKETPLACE"

# Print sync summary to stdout
for change in "${changes[@]}"; do
  echo "$change"
done
