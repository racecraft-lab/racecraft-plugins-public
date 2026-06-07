#!/usr/bin/env bash
# moc-id-normalize.sh — Shared namespace-aware ID normalizer.
#
# Implements the grammar in
# specs/prsg-002-moc-templates/contracts/id-normalization-grammar.md.
# Sourced by both the version-gated lints (the spec_id join check, FR-019)
# and by its own Layer-4 unit test (test-moc-id-normalize.sh).
# Covers FR-017 (namespace-aware normalization) and FR-018 (opaque
# whole-segment number-suffix comparison; NO [0-9]+[a-z]* sub-parse).
#
# This file defines functions only — sourcing it has no side effects.

set -euo pipefail

# moc_normalize <value>
# Reduce a value to "<namespace> <number-suffix>" (space-separated).
#   1. Lowercase the value.
#   2. Split on "-".
#   3. If the first segment is all-alpha (^[a-z]+$): it is the namespace and
#      the next segment is the number-suffix.
#   4. Else: namespace="spec" and the first segment is the number-suffix.
# The grammar is TOTAL: any input yields a defined pair. A missing or empty
# selected number-suffix segment yields the empty string.
moc_normalize() {
  local value="$1"
  local lowered
  lowered="$(printf '%s' "$value" | tr '[:upper:]' '[:lower:]')"

  local parts=()
  IFS='-' read -ra parts <<<"$lowered"

  local first="${parts[0]:-}"
  local namespace number_suffix

  if [[ "$first" =~ ^[a-z]+$ ]]; then
    namespace="$first"
    number_suffix="${parts[1]:-}"
  else
    namespace="spec"
    number_suffix="$first"
  fi

  printf '%s %s' "$namespace" "$number_suffix"
}

# moc_id_match <value-a> <value-b>
# Exit 0 if the two values normalize to the same (namespace, number-suffix)
# pair; exit 1 otherwise. Match requires BOTH namespace equality AND
# exact, opaque whole-segment number-suffix equality (byte-equal the entire
# segment — 013a1 is never truncated to 013a).
moc_id_match() {
  local a b
  a="$(moc_normalize "$1")"
  b="$(moc_normalize "$2")"
  [[ "$a" == "$b" ]]
}

# Guard: do nothing when sourced. No main/demo to run on direct execution.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  :
fi
