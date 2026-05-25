#!/usr/bin/env bash
# validate-curated-set.sh — Structural validation for scripts/curated-set.json
#
# Asserts the manifest is valid JSON with the schema install-curated-set.sh
# depends on, and that the required curated ids are present.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MANIFEST="$PLUGIN_ROOT/scripts/curated-set.json"

section "manifest file"

set_test "manifest file exists"
assert_file_exists "$MANIFEST"

set_test "manifest parses as JSON"
if jq -e . "$MANIFEST" >/dev/null 2>&1; then _pass; else _fail "invalid JSON"; fi

set_test "manifest has version field set to 1"
manifest_version=$(jq -r '.version // ""' "$MANIFEST")
if [ "$manifest_version" = "1" ]; then _pass; else _fail "version='$manifest_version' (expected 1)"; fi

set_test "manifest has non-empty entries array"
entries_count=$(jq '.entries | length' "$MANIFEST")
if [ "$entries_count" -gt 0 ]; then _pass; else _fail "entries is empty"; fi

section "required curated ids present"

REQUIRED_IDS=(review verify verify-tasks cleanup retrospective claude-ask-questions)

for id in "${REQUIRED_IDS[@]}"; do
  set_test "entry '$id' is present"
  found=$(jq -r --arg id "$id" '.entries[] | select(.id == $id) | .id' "$MANIFEST")
  if [ "$found" = "$id" ]; then _pass; else _fail "missing id '$id'"; fi
done

section "each entry has the required schema"

REQUIRED_FIELDS=(id kind repo recommended_default description min_speckit_version)

while read -r id; do
  for field in "${REQUIRED_FIELDS[@]}"; do
    set_test "entry '$id' has field '$field'"
    value=$(jq -r --arg id "$id" --arg field "$field" '.entries[] | select(.id == $id) | .[$field] // "MISSING"' "$MANIFEST")
    if [ "$value" != "MISSING" ] && [ -n "$value" ]; then _pass; else _fail "missing or empty '$field'"; fi
  done

  set_test "entry '$id' has valid kind (extension or preset)"
  kind=$(jq -r --arg id "$id" '.entries[] | select(.id == $id) | .kind' "$MANIFEST")
  if [ "$kind" = "extension" ] || [ "$kind" = "preset" ]; then _pass; else _fail "kind='$kind' is not extension or preset"; fi

  set_test "entry '$id' has plausibly-shaped repo (owner/name)"
  repo=$(jq -r --arg id "$id" '.entries[] | select(.id == $id) | .repo' "$MANIFEST")
  if [[ "$repo" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then _pass; else _fail "repo='$repo' is not owner/name shape"; fi
done < <(jq -r '.entries[].id' "$MANIFEST")

test_summary
