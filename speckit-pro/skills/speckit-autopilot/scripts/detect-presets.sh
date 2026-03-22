#!/usr/bin/env bash
# detect-presets.sh — Detect installed presets and extensions
#
# Usage: detect-presets.sh
# Output: JSON with preset info, extensions, template resolution
# Exit:   0 = success (even if no presets found)

set -euo pipefail

# Detect presets
presets="[]"
if ls .specify/presets/*/preset.yml >/dev/null 2>&1; then
  preset_items=()
  for preset_file in .specify/presets/*/preset.yml; do
    preset_dir=$(dirname "$preset_file")
    preset_name=$(basename "$preset_dir")
    # Extract key fields from YAML (basic parsing without yq)
    version=$(grep -m1 'version:' "$preset_file" 2>/dev/null | sed 's/.*version: *"\?\([^"]*\)"\?.*/\1/' || echo "unknown")
    description=$(grep -m1 'description:' "$preset_file" 2>/dev/null | sed 's/.*description: *"\?\(.*\)"\?/\1/' | head -c 200 || echo "")
    # Find template overrides
    templates=$(grep -A1 'replaces:' "$preset_file" 2>/dev/null | grep -v 'replaces:' | sed 's/.*"\([^"]*\)".*/\1/' | tr '\n' ',' | sed 's/,$//' || echo "")
    preset_items+=("{\"name\":\"$preset_name\",\"version\":\"$version\",\"templates\":\"$templates\"}")
  done
  presets="[$(IFS=','; echo "${preset_items[*]}")]"
fi

# Detect extensions from .registry (most authoritative)
extensions="[]"
if [ -f ".specify/extensions/.registry" ]; then
  # Extract extension names and enabled status
  ext_items=()
  while IFS= read -r line; do
    ext_name=$(echo "$line" | sed 's/.*"\([^"]*\)".*/\1/')
    ext_items+=("$ext_name")
  done < <(grep -o '"[a-z-]*":' .specify/extensions/.registry 2>/dev/null | grep -v '"extensions"' | grep -v '"version"' | grep -v '"source"' || true)

  # Simpler: just report the raw registry content exists
  extensions="\"see .specify/extensions/.registry\""
elif ls .specify/extensions/*/extension.yml >/dev/null 2>&1; then
  ext_names=()
  for ext_file in .specify/extensions/*/extension.yml; do
    ext_names+=("$(basename "$(dirname "$ext_file")")")
  done
  extensions="[$(printf '"%s",' "${ext_names[@]}" | sed 's/,$//')]"
fi

# Check hooks configuration
hooks="none"
if [ -f ".specify/extensions.yml" ]; then
  hook_count=$(grep -c 'before_\|after_' .specify/extensions.yml 2>/dev/null || echo "0")
  if [ "$hook_count" -gt 0 ]; then
    hooks="$hook_count hook events configured"
  fi
fi

# Template resolution (if specify CLI available)
tasks_template="default"
spec_template="default"
plan_template="default"
if command -v specify >/dev/null 2>&1; then
  tasks_template=$(specify preset resolve tasks-template 2>/dev/null || echo "default")
  spec_template=$(specify preset resolve spec-template 2>/dev/null || echo "default")
  plan_template=$(specify preset resolve plan-template 2>/dev/null || echo "default")
fi

has_presets="false"
if [ "$presets" != "[]" ]; then
  has_presets="true"
fi

printf '{"has_presets":%s,"presets":%s,"extensions":%s,"hooks":"%s","templates":{"tasks":"%s","spec":"%s","plan":"%s"}}\n' \
  "$has_presets" "$presets" "$extensions" "$hooks" \
  "$tasks_template" "$spec_template" "$plan_template"
