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

# Validate marketplace.json is valid JSON first
if ! jq -e '.' "$MARKETPLACE" >/dev/null 2>&1; then
  echo "Error: $MARKETPLACE contains invalid JSON." >&2
  exit 1
fi

# Validate plugins array exists and is an array
if ! jq -e '.plugins | type == "array"' "$MARKETPLACE" >/dev/null 2>&1; then
  if jq -e '.plugins' "$MARKETPLACE" >/dev/null 2>&1; then
    echo "Error: $MARKETPLACE has a 'plugins' field but it is not an array." >&2
  else
    echo "Error: $MARKETPLACE does not contain a 'plugins' array." >&2
  fi
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

for ((i=0; i<plugin_count; i++)); do
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

  # Reject sources with path traversal segments to prevent reading outside the repo
  if [[ "$plugin_dir" == *..* ]]; then
    echo "Error: Source path '$source_field' (index $i) contains illegal '..' segments." >&2
    exit 1
  fi

  plugin_json="${plugin_dir}/.claude-plugin/plugin.json"

  # Validate plugin.json exists
  if [ ! -f "$plugin_json" ]; then
    echo "Error: Plugin file not found: $plugin_json (referenced by marketplace entry at index $i)." >&2
    exit 1
  fi

  # Validate plugin.json is valid JSON before reading fields
  if ! jq -e '.' "$plugin_json" >/dev/null 2>&1; then
    echo "Error: $plugin_json contains invalid JSON." >&2
    exit 1
  fi

  # Read version from plugin.json
  version=$(jq -r '.version // empty' "$plugin_json") || {
    echo "Error: Failed to read $plugin_json." >&2
    exit 1
  }
  if [ -z "$version" ]; then
    echo "Error: No 'version' field in $plugin_json." >&2
    exit 1
  fi

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

existing_content=$(jq '.' "$MARKETPLACE")

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
