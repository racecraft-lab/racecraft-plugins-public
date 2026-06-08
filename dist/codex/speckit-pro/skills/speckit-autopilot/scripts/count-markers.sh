#!/usr/bin/env bash
# count-markers.sh — Deterministic marker counting for agent validation
#
# Usage: count-markers.sh <type> <feature_dir>
# Types: gaps, findings, clarifications, all
# Output: JSON with counts per file and total
# Exit:   0 = success, 2 = usage error
#
# Agents should call this instead of manually scanning for markers.
# Code is deterministic; language interpretation isn't.

set -euo pipefail

TYPE="${1:-}"
FEATURE_DIR="${2:-}"

if [ -z "$TYPE" ] || [ -z "$FEATURE_DIR" ]; then
  printf '{"error":"Usage: count-markers.sh <gaps|findings|clarifications|all> <feature_dir>"}\n'
  exit 2
fi

SPEC="$FEATURE_DIR/spec.md"
PLAN="$FEATURE_DIR/plan.md"
TASKS="$FEATURE_DIR/tasks.md"
CHECKLISTS_DIR="$FEATURE_DIR/checklists"

count_in_file() {
  local file="$1" pattern="$2" result
  if [ -f "$file" ]; then
    result=$(grep -c "$pattern" "$file" 2>/dev/null) || result=0
    echo "$result"
  else
    echo "0"
  fi
}

count_in_dir() {
  local dir="$1" pattern="$2" result
  if [ -d "$dir" ]; then
    result=$(grep -r -c "$pattern" "$dir" 2>/dev/null | awk -F: '{s+=$NF} END{print s+0}') || result=0
    echo "$result"
  else
    echo "0"
  fi
}

list_in_file() {
  local file="$1" pattern="$2"
  if [ -f "$file" ]; then
    grep -n "$pattern" "$file" 2>/dev/null | head -20 | jq -R . | jq -s '.' || echo "[]"
  else
    echo "[]"
  fi
}

case "$TYPE" in
  gaps)
    spec_gaps=$(count_in_file "$SPEC" "\\[Gap\\]")
    plan_gaps=$(count_in_file "$PLAN" "\\[Gap\\]")
    checklist_gaps=$(count_in_dir "$CHECKLISTS_DIR" "\\[Gap\\]")
    total=$((spec_gaps + plan_gaps + checklist_gaps))
    details=$(list_in_file "$SPEC" "\\[Gap\\]")
    jq -cn \
      --arg type "gaps" \
      --argjson total "$total" \
      --argjson spec "$spec_gaps" \
      --argjson plan "$plan_gaps" \
      --argjson checklists "$checklist_gaps" \
      --argjson details "$details" \
      '{"type":$type,"total":$total,"spec":$spec,"plan":$plan,"checklists":$checklists,"details":$details}'
    ;;

  findings)
    spec_crit=$(count_in_file "$SPEC" "\\[CRITICAL\\]")
    spec_high=$(count_in_file "$SPEC" "\\[HIGH\\]")
    spec_med=$(count_in_file "$SPEC" "\\[MEDIUM\\]")
    spec_low=$(count_in_file "$SPEC" "\\[LOW\\]")
    plan_crit=$(count_in_file "$PLAN" "\\[CRITICAL\\]")
    plan_high=$(count_in_file "$PLAN" "\\[HIGH\\]")
    plan_med=$(count_in_file "$PLAN" "\\[MEDIUM\\]")
    plan_low=$(count_in_file "$PLAN" "\\[LOW\\]")
    tasks_crit=$(count_in_file "$TASKS" "\\[CRITICAL\\]")
    tasks_high=$(count_in_file "$TASKS" "\\[HIGH\\]")
    tasks_med=$(count_in_file "$TASKS" "\\[MEDIUM\\]")
    tasks_low=$(count_in_file "$TASKS" "\\[LOW\\]")
    total_crit=$((spec_crit + plan_crit + tasks_crit))
    total_high=$((spec_high + plan_high + tasks_high))
    total_med=$((spec_med + plan_med + tasks_med))
    total_low=$((spec_low + plan_low + tasks_low))
    total=$((total_crit + total_high + total_med + total_low))
    jq -cn \
      --arg type "findings" \
      --argjson total "$total" \
      --argjson critical "$total_crit" \
      --argjson high "$total_high" \
      --argjson medium "$total_med" \
      --argjson low "$total_low" \
      '{"type":$type,"total":$total,"critical":$critical,"high":$high,"medium":$medium,"low":$low}'
    ;;

  clarifications)
    spec_nc=$(count_in_file "$SPEC" "\\[NEEDS CLARIFICATION\\]")
    plan_nc=$(count_in_file "$PLAN" "\\[NEEDS CLARIFICATION\\]")
    total=$((spec_nc + plan_nc))
    details=$(list_in_file "$SPEC" "\\[NEEDS CLARIFICATION\\]")
    jq -cn \
      --arg type "clarifications" \
      --argjson total "$total" \
      --argjson spec "$spec_nc" \
      --argjson plan "$plan_nc" \
      --argjson details "$details" \
      '{"type":$type,"total":$total,"spec":$spec,"plan":$plan,"details":$details}'
    ;;

  all)
    # Run all three types and combine
    gaps=$(count_in_file "$SPEC" "\\[Gap\\]")
    gaps=$((gaps + $(count_in_file "$PLAN" "\\[Gap\\]")))
    gaps=$((gaps + $(count_in_dir "$CHECKLISTS_DIR" "\\[Gap\\]")))
    nc=$(count_in_file "$SPEC" "\\[NEEDS CLARIFICATION\\]")
    nc=$((nc + $(count_in_file "$PLAN" "\\[NEEDS CLARIFICATION\\]")))
    crit=$(count_in_file "$SPEC" "\\[CRITICAL\\]")
    crit=$((crit + $(count_in_file "$PLAN" "\\[CRITICAL\\]") + $(count_in_file "$TASKS" "\\[CRITICAL\\]")))
    high=$(count_in_file "$SPEC" "\\[HIGH\\]")
    high=$((high + $(count_in_file "$PLAN" "\\[HIGH\\]") + $(count_in_file "$TASKS" "\\[HIGH\\]")))
    med=$(count_in_file "$SPEC" "\\[MEDIUM\\]")
    med=$((med + $(count_in_file "$PLAN" "\\[MEDIUM\\]") + $(count_in_file "$TASKS" "\\[MEDIUM\\]")))
    low=$(count_in_file "$SPEC" "\\[LOW\\]")
    low=$((low + $(count_in_file "$PLAN" "\\[LOW\\]") + $(count_in_file "$TASKS" "\\[LOW\\]")))
    jq -cn \
      --argjson gaps "$gaps" \
      --argjson clarifications "$nc" \
      --argjson critical "$crit" \
      --argjson high "$high" \
      --argjson medium "$med" \
      --argjson low "$low" \
      '{"gaps":$gaps,"clarifications":$clarifications,"critical":$critical,"high":$high,"medium":$medium,"low":$low}'
    ;;

  *)
    printf '{"error":"Unknown type: %s. Valid types: gaps, findings, clarifications, all"}\n' "$TYPE"
    exit 2
    ;;
esac
