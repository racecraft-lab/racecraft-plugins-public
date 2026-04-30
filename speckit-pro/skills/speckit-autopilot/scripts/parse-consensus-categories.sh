#!/usr/bin/env bash
# parse-consensus-categories.sh — Deterministic category parser for
# the Tier A consensus-routing dispatch.
#
# Usage: parse-consensus-categories.sh "<unresolved item line>"
# Output: JSON with parsed categories, the analyst dispatch list, the
#         round (always 1 — Round 2 escalation is the orchestrator's
#         decision), and a reason code for the dispatch.
# Exit:   0 = success, 2 = usage error
#
# Single source of truth for the routing rules in
# `references/consensus-protocol.md` §"Category-Routed Dispatch".
# The orchestrator skills (Claude + Codex `speckit-autopilot`) MUST
# match this script's behavior; Layer 4 tests guard the parsing.

set -euo pipefail

LINE="${1-}"

if [ "$#" -lt 1 ]; then
  printf '{"error":"Usage: parse-consensus-categories.sh \\"<unresolved item line>\\""}\n'
  exit 2
fi

ALL_ANALYSTS='["codebase-analyst","spec-context-analyst","domain-researcher"]'

emit() {
  # emit <categories_json_array> <analysts_json_array> <raw_prefix> <reason>
  jq -cn \
    --argjson categories "$1" \
    --argjson analysts "$2" \
    --arg raw_prefix "$3" \
    --arg reason "$4" \
    '{categories:$categories,analysts:$analysts,round:1,raw_prefix:$raw_prefix,reason:$reason}'
}

# Strip leading whitespace.
TRIMMED="$(printf '%s' "$LINE" | sed -E 's/^[[:space:]]+//')"

# Also strip an optional Markdown bullet ("- ", "* ", "+ ").
TRIMMED="$(printf '%s' "$TRIMMED" | sed -E 's/^[-*+][[:space:]]+//')"

# Pull the leading [<categories>] prefix using a portable regex.
# Matches the OPENING bracket and everything up to (but not including)
# the FIRST closing bracket — multi-tag like [codebase, domain] is one prefix.
RAW_PREFIX=""
INNER=""
if [[ "$TRIMMED" =~ ^\[([^][]*)\] ]]; then
  INNER="${BASH_REMATCH[1]}"
  RAW_PREFIX="[${INNER}]"
fi

# No prefix → safe default (all 3, untagged).
if [ -z "$RAW_PREFIX" ]; then
  emit '[]' "$ALL_ANALYSTS" "" "untagged-safe-default"
  exit 0
fi

# Split inner on commas, normalise whitespace and case, drop empties.
# `grep -v ''` returns exit 1 on empty input; tolerate that with `|| true`
# so empty / whitespace-only brackets fall through to the empty-default branch.
CATEGORIES_JSON="$(
  {
    printf '%s' "$INNER" \
      | tr ',' '\n' \
      | sed -E 's/^[[:space:]]+|[[:space:]]+$//g' \
      | tr '[:upper:]' '[:lower:]' \
      | grep -v '^$' || true
  } | jq -R . | jq -cs '.'
)"

# Empty bracket "[]" or whitespace-only "[ ]" → safe default.
if [ "$CATEGORIES_JSON" = "[]" ]; then
  emit '[]' "$ALL_ANALYSTS" "$RAW_PREFIX" "empty-prefix-safe-default"
  exit 0
fi

# Security defense-in-depth: any [security] tag forces all 3 regardless
# of co-tags. Even "[security, codebase]" → all 3.
if printf '%s' "$CATEGORIES_JSON" | jq -e 'index("security")' >/dev/null; then
  emit "$CATEGORIES_JSON" "$ALL_ANALYSTS" "$RAW_PREFIX" "security-defense-in-depth"
  exit 0
fi

# [ambiguous] → safe default (all 3).
if printf '%s' "$CATEGORIES_JSON" | jq -e 'index("ambiguous")' >/dev/null; then
  emit "$CATEGORIES_JSON" "$ALL_ANALYSTS" "$RAW_PREFIX" "ambiguous-safe-default"
  exit 0
fi

# Map known categories to analysts. Unknown tags trigger safe default.
HAS_CODEBASE=$(printf '%s' "$CATEGORIES_JSON" | jq 'index("codebase") != null')
HAS_SPEC=$(printf '%s' "$CATEGORIES_JSON" | jq 'index("spec") != null')
HAS_DOMAIN=$(printf '%s' "$CATEGORIES_JSON" | jq 'index("domain") != null')
UNKNOWN=$(printf '%s' "$CATEGORIES_JSON" \
  | jq -c 'map(select(. != "codebase" and . != "spec" and . != "domain")) | length')

if [ "$UNKNOWN" -gt 0 ]; then
  emit "$CATEGORIES_JSON" "$ALL_ANALYSTS" "$RAW_PREFIX" "unknown-tag-safe-default"
  exit 0
fi

# Build the routed analyst list deterministically (codebase, spec, domain order).
ANALYSTS='[]'
if [ "$HAS_CODEBASE" = "true" ]; then
  ANALYSTS=$(printf '%s' "$ANALYSTS" | jq -c '. + ["codebase-analyst"]')
fi
if [ "$HAS_SPEC" = "true" ]; then
  ANALYSTS=$(printf '%s' "$ANALYSTS" | jq -c '. + ["spec-context-analyst"]')
fi
if [ "$HAS_DOMAIN" = "true" ]; then
  ANALYSTS=$(printf '%s' "$ANALYSTS" | jq -c '. + ["domain-researcher"]')
fi

REASON="category-routed"
N=$(printf '%s' "$ANALYSTS" | jq 'length')
if [ "$N" -eq 3 ]; then
  REASON="all-categories-routed"
fi

emit "$CATEGORIES_JSON" "$ANALYSTS" "$RAW_PREFIX" "$REASON"
