#!/usr/bin/env bash
# sync-marketplace-versions.sh -- Sync plugin versions from plugin.json to marketplace.json
#
# Registry-driven: iterates over marketplace.json plugins arrays, reads each
# local plugin's platform manifest, and updates the marketplace entry version.
# Supports Claude marketplace string source fields and Codex marketplace
# source.path object fields.
#
# Usage: Run from repository root
#   bash scripts/sync-marketplace-versions.sh
#
# Output: Sync summary to stdout (only when changes made)
# Errors: All error/info messages to stderr
# Exit:   0 = success (with or without changes), 1 = fatal error

set -euo pipefail

MARKETPLACES=(
  ".claude-plugin/marketplace.json:.claude-plugin/plugin.json"
  ".agents/plugins/marketplace.json:.codex-plugin/plugin.json"
)

# ─────────────────────────────────────────
# Prerequisite checks
# ─────────────────────────────────────────

if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required but not found. Install it: brew install jq (macOS) or apt-get install jq (Linux)" >&2
  exit 1
fi

marketplace_found=false
for entry in "${MARKETPLACES[@]}"; do
  marketplace="${entry%%:*}"
  if [ -f "$marketplace" ]; then
    marketplace_found=true
  fi
done

if [ "$marketplace_found" != "true" ]; then
  echo "Error: no supported marketplace.json found. Run this script from the repository root." >&2
  exit 1
fi

sync_marketplace() {
  local marketplace="$1"
  local manifest_rel="$2"

  if [ ! -f "$marketplace" ]; then
    return 0
  fi

  # Validate marketplace.json is valid JSON first
  if ! jq -e '.' "$marketplace" >/dev/null 2>&1; then
    echo "Error: $marketplace contains invalid JSON." >&2
    exit 1
  fi

  # Validate plugins array exists and is an array
  if ! jq -e '.plugins | type == "array"' "$marketplace" >/dev/null 2>&1; then
    if jq -e '.plugins' "$marketplace" >/dev/null 2>&1; then
      echo "Error: $marketplace has a 'plugins' field but it is not an array." >&2
    else
      echo "Error: $marketplace does not contain a 'plugins' array." >&2
    fi
    exit 1
  fi

  local plugin_count
  plugin_count=$(jq '.plugins | length' "$marketplace")
  if [ "$plugin_count" -eq 0 ]; then
    echo "Info: No plugins in $marketplace -- nothing to sync." >&2
    return 0
  fi

  local updated_json
  updated_json=$(cat "$marketplace")
  local changes_text=""
  local change_count=0

  for ((i=0; i<plugin_count; i++)); do
    local source_field
    source_field=$(jq -r ".plugins[$i].source | if type == \"string\" then . elif type == \"object\" then (.path // empty) else empty end" "$marketplace")

    if [ -z "$source_field" ]; then
      local entry_name
      entry_name=$(jq -r ".plugins[$i].name // \"index $i\"" "$marketplace")
      echo "Error: Plugin entry '$entry_name' (index $i) is missing the 'source' field or source.path." >&2
      exit 1
    fi

    # Skip non-relative sources (external repos)
    if [[ "$source_field" != ./* ]]; then
      echo "Info: Skipping non-relative source '$source_field' (index $i)." >&2
      continue
    fi

    local plugin_dir
    plugin_dir="${source_field#./}"

    # Reject sources with path traversal segments to prevent reading outside the repo
    if [[ "$plugin_dir" == *..* ]]; then
      echo "Error: Source path '$source_field' (index $i) contains illegal '..' segments." >&2
      exit 1
    fi

    local plugin_json
    plugin_json="${plugin_dir}/${manifest_rel}"

    if [ ! -f "$plugin_json" ]; then
      echo "Error: Plugin file not found: $plugin_json (referenced by marketplace entry at index $i)." >&2
      exit 1
    fi

    if ! jq -e '.' "$plugin_json" >/dev/null 2>&1; then
      echo "Error: $plugin_json contains invalid JSON." >&2
      exit 1
    fi

    local version
    version=$(jq -r '.version // empty' "$plugin_json") || {
      echo "Error: Failed to read $plugin_json." >&2
      exit 1
    }
    if [ -z "$version" ]; then
      echo "Error: No 'version' field in $plugin_json." >&2
      exit 1
    fi

    if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
      echo "Error: Invalid semver in $plugin_json: '$version'. Expected format: X.Y.Z" >&2
      exit 1
    fi

    local current_version
    current_version=$(jq -r ".plugins[$i].version // empty" "$marketplace")

    updated_json=$(printf '%s' "$updated_json" | jq --arg ver "$version" --argjson idx "$i" '.plugins[$idx].version = $ver')

    if [ "$current_version" != "$version" ]; then
      changes_text="${changes_text}synced ${plugin_dir}: ${current_version:-<none>} -> ${version}
"
      change_count=$((change_count + 1))
    fi
  done

  if [ "$change_count" -eq 0 ]; then
    return 0
  fi

  printf '%s\n' "$updated_json" > "$marketplace"
  printf '%s' "$changes_text"
}

for entry in "${MARKETPLACES[@]}"; do
  marketplace="${entry%%:*}"
  manifest_rel="${entry#*:}"
  sync_marketplace "$marketplace" "$manifest_rel"
done
