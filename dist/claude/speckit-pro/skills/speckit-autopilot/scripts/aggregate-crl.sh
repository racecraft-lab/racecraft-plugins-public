#!/usr/bin/env bash
# aggregate-crl.sh — Parse a workflow file's "Consensus Resolution Log"
# table and compute the Tier A re-evaluation trigger metric.
#
# Usage: aggregate-crl.sh <workflow_file>
# Output: JSON with total items, Round 1/2 counts, escape-hatch count,
#         escape rate (percent), threshold, and exceeds_threshold boolean.
# Exit:   0 = success (whether or not the threshold is exceeded),
#         2 = usage error,
#         3 = workflow file missing or no CRL section found.
#
# The 10% escape-hatch threshold is documented in
# `references/consensus-protocol.md` §"Re-evaluation trigger". When the
# rate exceeds the threshold across a 30-day window, the maintainer
# should revert to always-3 dispatch and treat tags as advisory.

set -euo pipefail

WORKFLOW_FILE="${1:-}"
THRESHOLD_PERCENT="${THRESHOLD_PERCENT:-10}"

if [ -z "$WORKFLOW_FILE" ]; then
  printf '{"error":"Usage: aggregate-crl.sh <workflow_file>"}\n'
  exit 2
fi

if [ ! -f "$WORKFLOW_FILE" ]; then
  printf '{"error":"Workflow file not found: %s"}\n' "$WORKFLOW_FILE"
  exit 3
fi

# Extract the table rows under "### Consensus Resolution Log".
# A table row starts with `|` and is not the header (`| #`) or separator
# (`|---`). We capture everything from the section header until the next
# blank line that follows table rows, or the next `## ` / `### ` header.
TABLE_BODY=$(awk '
  /^### Consensus Resolution Log/ { in_section=1; next }
  in_section && /^### / && !/^### Consensus Resolution Log/ { in_section=0 }
  in_section && /^## / { in_section=0 }
  in_section && /^\|/ {
    # Skip the header row (contains "Round" and "Outcome" as column names)
    # and the separator row (starts with |---).
    if ($0 ~ /^\|[[:space:]]*-+/) next
    if ($0 ~ /\|[[:space:]]*Round[[:space:]]*\|/) next
    print
  }
' "$WORKFLOW_FILE")

if [ -z "$TABLE_BODY" ]; then
  jq -cn \
    --arg file "$WORKFLOW_FILE" \
    --argjson threshold "$THRESHOLD_PERCENT" \
    '{file:$file,total_items:0,round_1:0,round_2:0,escape_hatch:0,escape_rate_percent:0,threshold_percent:$threshold,exceeds_threshold:false,note:"No Consensus Resolution Log entries found."}'
  exit 0
fi

# For each row, extract Round and Outcome. Column positions in the spec:
#   1=#  2=Type  3=Question/Gap/Finding  4=Categories  5=Round  6=Outcome  7=Resolution  8=Analysts Used
# Pipe-split with awk; trim whitespace around each field.
ROUND_OUTCOME=$(printf '%s\n' "$TABLE_BODY" | awk -F'|' '
  {
    # Fields are positions 2..9 because of leading | (which produces an empty $1).
    round=$6
    outcome=$7
    gsub(/^[[:space:]]+|[[:space:]]+$/, "", round)
    gsub(/^[[:space:]]+|[[:space:]]+$/, "", outcome)
    if (round == "" && outcome == "") next
    print round "|" outcome
  }
')

TOTAL=0
ROUND_1=0
ROUND_2=0
ESCAPE=0

while IFS='|' read -r round outcome; do
  [ -z "${round}${outcome}" ] && continue
  TOTAL=$((TOTAL + 1))
  case "$round" in
    "1")    ROUND_1=$((ROUND_1 + 1)) ;;
    "2")    ROUND_2=$((ROUND_2 + 1)) ;;
    "1→2"|"1->2")  # Items that escaped Round 1 to Round 2 count as Round 2 (and as escape).
                   ROUND_2=$((ROUND_2 + 1))
                   ;;
    *)      ;;  # Unknown round value — count toward total but not into either bucket.
  esac
  if [ "$outcome" = "escape-hatch" ]; then
    ESCAPE=$((ESCAPE + 1))
  fi
done <<< "$ROUND_OUTCOME"

# Compute escape rate as percentage with one decimal place.
if [ "$TOTAL" -gt 0 ]; then
  RATE=$(awk -v e="$ESCAPE" -v t="$TOTAL" 'BEGIN { printf "%.1f", (e * 100.0) / t }')
else
  RATE="0.0"
fi

EXCEEDS=$(awk -v r="$RATE" -v th="$THRESHOLD_PERCENT" 'BEGIN { print (r+0 > th+0) ? "true" : "false" }')

jq -cn \
  --arg file "$WORKFLOW_FILE" \
  --argjson total "$TOTAL" \
  --argjson r1 "$ROUND_1" \
  --argjson r2 "$ROUND_2" \
  --argjson escape "$ESCAPE" \
  --argjson rate "$RATE" \
  --argjson threshold "$THRESHOLD_PERCENT" \
  --argjson exceeds "$EXCEEDS" \
  '{file:$file,total_items:$total,round_1:$r1,round_2:$r2,escape_hatch:$escape,escape_rate_percent:$rate,threshold_percent:$threshold,exceeds_threshold:$exceeds}'
