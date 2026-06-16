#!/usr/bin/env bash
# confidence-gate.sh — Read the synthesizer's pre-Implement confidence emit
# and decide whether the autopilot may proceed to Phase 7 (Implement).
#
# The emit format (set by speckit-autopilot/references/consensus-protocol.md
# §Pre-Implement Confidence Emit) is, on its own lines in the input file:
#
#   📊 Confidence: 0.92
#
#   - Task understanding: 0.95
#   - Approach clarity: 0.90
#   - Requirements alignment: 0.92
#   - Risk assessment: 0.88
#   - Completeness: 0.95
#
# Usage:
#   confidence-gate.sh <workflow-file> [--threshold 0.90] [--mode advisory|strict]
#
# Output:
#   JSON on stdout with composite, criteria, pass, threshold, mode,
#   recommended_action. Human-readable status on stderr.
#
# Exit:
#   0 — PASS (composite >= threshold)
#   1 — NO_DATA (no confidence emit found; soft-skip; or usage / read error)
#   2 — FAIL (composite < threshold)
#
# The mode flag affects the JSON `recommended_action` field but NOT the exit
# code on FAIL. The autopilot body reads the JSON and chooses what to do:
#   - advisory: log + continue to Phase 7
#   - strict:   STOP
# In both modes, iteration-driven remediation may run before re-checking.

set -euo pipefail

WORKFLOW_FILE=""
THRESHOLD="0.90"
MODE="advisory"

# Allow tests / callers to override the input path via env without a flag.
WORKFLOW_FILE="${CONFIDENCE_GATE_INPUT:-}"

usage() {
  printf '{"error":"Usage: confidence-gate.sh <workflow-file> [--threshold N.NN] [--mode advisory|strict]"}\n'
}

while [ $# -gt 0 ]; do
  case "$1" in
    --threshold)
      THRESHOLD="${2:-}"
      shift 2
      ;;
    --threshold=*)
      THRESHOLD="${1#*=}"
      shift
      ;;
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --mode=*)
      MODE="${1#*=}"
      shift
      ;;
    -h|--help)
      usage
      exit 1
      ;;
    --*)
      printf '{"error":"unknown option: %s"}\n' "$1" >&2
      usage
      exit 1
      ;;
    *)
      if [ -z "$WORKFLOW_FILE" ]; then
        WORKFLOW_FILE="$1"
      else
        printf '{"error":"unexpected positional arg: %s"}\n' "$1" >&2
        usage
        exit 1
      fi
      shift
      ;;
  esac
done

if [ -z "$WORKFLOW_FILE" ]; then
  usage
  exit 1
fi

if [ ! -f "$WORKFLOW_FILE" ]; then
  printf '{"error":"workflow file not found: %s"}\n' "$WORKFLOW_FILE" >&2
  exit 1
fi

case "$MODE" in
  advisory|strict) : ;;
  *)
    printf '{"error":"invalid --mode: %s (must be advisory or strict)"}\n' "$MODE" >&2
    exit 1
    ;;
esac

if ! [[ "$THRESHOLD" =~ ^[01]\.[0-9]{1,2}$ ]] && ! [[ "$THRESHOLD" =~ ^[01]$ ]]; then
  printf '{"error":"invalid --threshold: %s (must be 0.00-1.00)"}\n' "$THRESHOLD" >&2
  exit 1
fi

# The most recent '📊 Confidence: X.XX' line wins (handles multi-pass Analyze).
composite_line="$(grep -E '^📊 Confidence: [01]\.[0-9]{2}$' "$WORKFLOW_FILE" 2>/dev/null | tail -1 || true)"

if [ -z "$composite_line" ]; then
  printf 'confidence-gate: NO_DATA — no synthesizer confidence emit found in %s\n' "$WORKFLOW_FILE" >&2
  jq -cn \
    --arg threshold "$THRESHOLD" \
    --arg mode "$MODE" \
    --arg file "$WORKFLOW_FILE" \
    '{
      pass: null,
      composite: null,
      criteria: {},
      threshold: ($threshold | tonumber),
      mode: $mode,
      recommended_action: "soft_skip",
      reason: "no confidence emit found",
      input: $file
    }'
  exit 1
fi

composite="${composite_line#📊 Confidence: }"

# Pull the 5 criterion lines that follow the composite emit (best-effort: walk
# the file once and grab the most recent block). Keep this Bash 3.2-compatible:
# macOS still ships Bash 3.2, which does not support associative arrays.
criterion_value() {
  local name="$1"
  local pattern value
  pattern="^- ${name}: ([01]\\.[0-9]{2})$"
  value="$(grep -E "$pattern" "$WORKFLOW_FILE" 2>/dev/null | tail -1 | sed -E "s/^- ${name}: ([01]\\.[0-9]{2})\$/\\1/" || true)"
  printf '%s' "${value:-}"
}

task_understanding="$(criterion_value "Task understanding")"
approach_clarity="$(criterion_value "Approach clarity")"
requirements_alignment="$(criterion_value "Requirements alignment")"
risk_assessment="$(criterion_value "Risk assessment")"
completeness="$(criterion_value "Completeness")"

# Build criteria JSON object.
criteria_json="$(
  jq -n \
    --arg tu  "$task_understanding" \
    --arg ac  "$approach_clarity" \
    --arg ra  "$requirements_alignment" \
    --arg ri  "$risk_assessment" \
    --arg cp  "$completeness" \
    '{
      task_understanding:     (if $tu == "" then null else ($tu | tonumber) end),
      approach_clarity:       (if $ac == "" then null else ($ac | tonumber) end),
      requirements_alignment: (if $ra == "" then null else ($ra | tonumber) end),
      risk_assessment:        (if $ri == "" then null else ($ri | tonumber) end),
      completeness:           (if $cp == "" then null else ($cp | tonumber) end)
    }'
)"

# Numeric comparison: use awk so we don't depend on bc.
pass_bool="$(awk -v c="$composite" -v t="$THRESHOLD" 'BEGIN { print (c+0 >= t+0) ? "true" : "false" }')"

if [ "$pass_bool" = "true" ]; then
  printf 'confidence-gate: PASS — composite %s >= threshold %s\n' "$composite" "$THRESHOLD" >&2
  jq -cn \
    --arg composite "$composite" \
    --arg threshold "$THRESHOLD" \
    --arg mode "$MODE" \
    --arg file "$WORKFLOW_FILE" \
    --argjson criteria "$criteria_json" \
    '{
      pass: true,
      composite: ($composite | tonumber),
      criteria: $criteria,
      threshold: ($threshold | tonumber),
      mode: $mode,
      recommended_action: "proceed",
      reason: "composite at or above threshold",
      input: $file
    }'
  exit 0
fi

# FAIL — composite below threshold.
if [ "$MODE" = "strict" ]; then
  printf 'confidence-gate: FAIL — composite %s < threshold %s (mode=strict, STOP)\n' "$composite" "$THRESHOLD" >&2
  action="stop"
  reason="composite below threshold in strict mode"
else
  printf 'confidence-gate: FAIL — composite %s < threshold %s (mode=advisory, log + continue)\n' "$composite" "$THRESHOLD" >&2
  action="continue_with_warning"
  reason="composite below threshold in advisory mode"
fi

jq -cn \
  --arg composite "$composite" \
  --arg threshold "$THRESHOLD" \
  --arg mode "$MODE" \
  --arg file "$WORKFLOW_FILE" \
  --arg action "$action" \
  --arg reason "$reason" \
  --argjson criteria "$criteria_json" \
  '{
    pass: false,
    composite: ($composite | tonumber),
    criteria: $criteria,
    threshold: ($threshold | tonumber),
    mode: $mode,
    recommended_action: $action,
    reason: $reason,
    input: $file
  }'

exit 2
