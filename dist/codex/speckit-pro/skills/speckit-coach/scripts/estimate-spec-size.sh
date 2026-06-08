#!/usr/bin/env bash
# estimate-spec-size.sh — Deterministic, advisory vertical-slice size estimator.
#
# The single shared, runtime-agnostic estimator used by speckit-prd and grill-me
# (Claude Code) and both Codex mirrors via
#   ${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/scripts/estimate-spec-size.sh
#
# It turns structured, pre-implementation size signals into a forward LOC guess
# and an ok|warn status relative to the documented reviewable-LOC ceiling. The
# guidance, weights, and boundary rule are documented in the single source of
# truth: skills/speckit-coach/references/slicing-heuristics.md
#
# ADVISORY-ONLY (FR-011): this script exits 0 on every successful estimate,
# including `warn`. `warn` is informational; it is NEVER a non-zero/blocking
# exit. Callers MUST NOT read the exit code as a gate.
#
# Usage:
#   estimate-spec-size.sh [--user-stories N] [--files N] [--frs N] \
#                         [--new-vs-modify new|modify] [--spike]
#
# Output (compact JSON on stdout, via jq):
#   {"estimated_loc": <int>=0>, "suggested_slices": <int>=1>, "status": "ok|warn"}

set -euo pipefail

# Single source-of-truth reviewable-LOC ceiling.
# keep in sync with the documented ceiling in slicing-heuristics.md
readonly CEILING=400

# Per-signal LOC weights (the documented heuristic).
# keep in sync with the weights table in slicing-heuristics.md
readonly LOC_PER_USER_STORY=25
readonly LOC_PER_FILE=40
readonly LOC_PER_FR=15

# Raw inputs (defaults per the contract: counts 0, new-vs-modify `new`, spike off).
user_stories="0"
files="0"
frs="0"
new_vs_modify="new"
spike="false"

# Parse flags. Each value is taken verbatim as the next token, so non-numeric,
# negative, or decimal values are accepted here and normalized to 0 below
# (FR-016) rather than being mistaken for another flag or crashing the parser.
while [ "$#" -gt 0 ]; do
  case "$1" in
    --user-stories)
      user_stories="${2:-}"
      shift 2 || shift
      ;;
    --files)
      files="${2:-}"
      shift 2 || shift
      ;;
    --frs)
      frs="${2:-}"
      shift 2 || shift
      ;;
    --new-vs-modify)
      new_vs_modify="${2:-new}"
      shift 2 || shift
      ;;
    --spike)
      spike="true"
      shift
      ;;
    *)
      # Unknown tokens are ignored — advisory-only, never crash on input.
      shift
      ;;
  esac
done

# Normalize a numeric signal: a non-negative integer passes through; anything
# missing, negative, decimal, or non-numeric becomes 0 (FR-016). This is one
# shared path, not a separate error branch.
normalize_count() {
  local value="${1:-}"
  if [[ "$value" =~ ^[0-9]+$ ]]; then
    printf '%s' "$value"
  else
    printf '0'
  fi
}

# Emit the compact JSON result in the contract's key order and exit 0.
emit() {
  local loc="$1" slices="$2" status="$3"
  jq -cn \
    --argjson estimated_loc "$loc" \
    --argjson suggested_slices "$slices" \
    --arg status "$status" \
    '{estimated_loc: $estimated_loc, suggested_slices: $suggested_slices, status: $status}'
  exit 0
}

# Spike (FR-017): a research-only slice is sized by timebox, not LOC. Skip the
# LOC-threshold comparison entirely and return the fixed triple. `ok` here means
# "LOC sizing is not applicable", not "small".
if [ "$spike" = "true" ]; then
  emit 0 1 "ok"
fi

user_stories="$(normalize_count "$user_stories")"
files="$(normalize_count "$files")"
frs="$(normalize_count "$frs")"

# Weighted sum of the structured size signals (the documented heuristic).
estimated_loc=$(( (user_stories * LOC_PER_USER_STORY) \
                + (files * LOC_PER_FILE) \
                + (frs * LOC_PER_FR) ))

# Modify discount: modifying existing code is typically a smaller reviewable
# surface than building net-new, so halve the estimate (integer division). Any
# value other than the literal `modify` keeps the net-new estimate as-is.
if [ "$new_vs_modify" = "modify" ]; then
  estimated_loc=$(( estimated_loc / 2 ))
fi

# suggested_slices = ceil(estimated_loc / ceiling), minimum 1.
if [ "$estimated_loc" -le 0 ]; then
  suggested_slices=1
else
  suggested_slices=$(( (estimated_loc + CEILING - 1) / CEILING ))
fi

# At-ceiling boundary (FR-006, FR-008): ok at exactly the ceiling; warn only when
# strictly over.
if [ "$estimated_loc" -gt "$CEILING" ]; then
  status="warn"
else
  status="ok"
fi

emit "$estimated_loc" "$suggested_slices" "$status"
