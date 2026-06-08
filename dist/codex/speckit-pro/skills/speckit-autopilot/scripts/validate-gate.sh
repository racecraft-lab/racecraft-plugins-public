#!/usr/bin/env bash
# validate-gate.sh — Validate a specific autopilot gate
#
# Usage: validate-gate.sh <gate> <feature_dir> [extra_args...]
# Gates: G1 G2 G3 G4 G5 G6 G7
# Output: JSON with pass/fail, marker count, details
# Exit:   0 = pass, 1 = fail, 2 = usage error

set -euo pipefail

GATE="${1:-}"
FEATURE_DIR="${2:-}"

if [ -z "$GATE" ] || [ -z "$FEATURE_DIR" ]; then
  printf '{"error":"Usage: validate-gate.sh <gate> <feature_dir>"}\n'
  exit 2
fi

SPEC="$FEATURE_DIR/spec.md"
PLAN="$FEATURE_DIR/plan.md"
TASKS="$FEATURE_DIR/tasks.md"

count_markers() {
  local file="$1" pattern="$2" result
  if [ -f "$file" ]; then
    result=$(grep -c "$pattern" "$file" 2>/dev/null) || result=0
    echo "$result"
  else
    echo "0"
  fi
}

list_markers() {
  local file="$1" pattern="$2"
  if [ -f "$file" ]; then
    grep -n "$pattern" "$file" 2>/dev/null | head -20 || true
  fi
}

case "$GATE" in
  G1)
    # G1: Specify complete — spec.md exists, 0 [NEEDS CLARIFICATION] markers
    if [ ! -f "$SPEC" ]; then
      printf '{"gate":"G1","pass":false,"reason":"spec.md not found","markers":0,"details":[]}\n'
      exit 1
    fi
    count=$(count_markers "$SPEC" "\\[NEEDS CLARIFICATION\\]")
    if [ "$count" -eq 0 ]; then
      printf '{"gate":"G1","pass":true,"reason":"spec.md exists with 0 markers","markers":0,"details":[]}\n'
      exit 0
    else
      details_json=$(list_markers "$SPEC" "\\[NEEDS CLARIFICATION\\]" | head -10 | jq -R . | jq -s '.')
      jq -cn \
        --arg gate "G1" \
        --arg reason "${count} [NEEDS CLARIFICATION] markers remain" \
        --argjson markers "$count" \
        --argjson details "$details_json" \
        '{"gate":$gate,"pass":false,"reason":$reason,"markers":$markers,"details":$details}'
      exit 1
    fi
    ;;

  G2)
    # G2: Clarify complete — 0 [NEEDS CLARIFICATION] markers in spec.md
    if [ ! -f "$SPEC" ]; then
      printf '{"gate":"G2","pass":false,"reason":"spec.md not found","markers":0,"details":[]}\n'
      exit 1
    fi
    count=$(count_markers "$SPEC" "\\[NEEDS CLARIFICATION\\]")
    if [ "$count" -eq 0 ]; then
      printf '{"gate":"G2","pass":true,"reason":"0 [NEEDS CLARIFICATION] markers","markers":0,"details":[]}\n'
      exit 0
    else
      details_json=$(list_markers "$SPEC" "\\[NEEDS CLARIFICATION\\]" | head -10 | jq -R . | jq -s '.')
      jq -cn \
        --arg gate "G2" \
        --arg reason "${count} markers remain" \
        --argjson markers "$count" \
        --argjson details "$details_json" \
        '{"gate":$gate,"pass":false,"reason":$reason,"markers":$markers,"details":$details}'
      exit 1
    fi
    ;;

  G3)
    # G3: Plan complete — plan.md exists, 0 NEEDS CLARIFICATION, 0 TODO/TKTK
    if [ ! -f "$PLAN" ]; then
      printf '{"gate":"G3","pass":false,"reason":"plan.md not found","markers":0,"details":[]}\n'
      exit 1
    fi
    nc_count=$(count_markers "$PLAN" "\\[NEEDS CLARIFICATION\\]")
    todo_count=$(count_markers "$PLAN" "TODO\\|TKTK\\|???")
    total=$((nc_count + todo_count))
    if [ "$total" -eq 0 ]; then
      printf '{"gate":"G3","pass":true,"reason":"plan.md exists with 0 unresolved markers","markers":0,"details":[]}\n'
      exit 0
    else
      printf '{"gate":"G3","pass":false,"reason":"%d unresolved markers (NC:%d, TODO:%d)","markers":%d,"details":[]}\n' \
        "$total" "$nc_count" "$todo_count" "$total"
      exit 1
    fi
    ;;

  G4)
    # G4: Checklist complete — 0 [Gap] markers in spec.md and plan.md
    spec_gaps=$(count_markers "$SPEC" "\\[Gap\\]")
    plan_gaps=$(count_markers "$PLAN" "\\[Gap\\]")
    total=$((spec_gaps + plan_gaps))
    if [ "$total" -eq 0 ]; then
      printf '{"gate":"G4","pass":true,"reason":"0 [Gap] markers","markers":0,"details":[]}\n'
      exit 0
    else
      printf '{"gate":"G4","pass":false,"reason":"%d [Gap] markers (spec:%d, plan:%d)","markers":%d,"details":[]}\n' \
        "$total" "$spec_gaps" "$plan_gaps" "$total"
      exit 1
    fi
    ;;

  G5)
    # G5: Tasks complete — tasks.md exists with task entries
    if [ ! -f "$TASKS" ]; then
      printf '{"gate":"G5","pass":false,"reason":"tasks.md not found","markers":0,"details":[]}\n'
      exit 1
    fi
    task_count=$(grep -c '^\- \[ \] T[0-9]' "$TASKS" 2>/dev/null) || task_count=0
    if [ "$task_count" -gt 0 ]; then
      printf '{"gate":"G5","pass":true,"reason":"%d tasks found","markers":0,"task_count":%d}\n' \
        "$task_count" "$task_count"
      exit 0
    else
      printf '{"gate":"G5","pass":false,"reason":"No task entries found in tasks.md","markers":0,"task_count":0}\n'
      exit 1
    fi
    ;;

  G6)
    # G6: Analyze complete — 0 CRITICAL/HIGH findings remain
    # This gate checks for analysis markers in all 3 artifacts
    spec_crit=$(count_markers "$SPEC" "\\[CRITICAL\\]\\|\\[HIGH\\]")
    plan_crit=$(count_markers "$PLAN" "\\[CRITICAL\\]\\|\\[HIGH\\]")
    tasks_crit=$(count_markers "$TASKS" "\\[CRITICAL\\]\\|\\[HIGH\\]")
    total=$((spec_crit + plan_crit + tasks_crit))
    if [ "$total" -eq 0 ]; then
      printf '{"gate":"G6","pass":true,"reason":"0 CRITICAL/HIGH findings","markers":0,"details":[]}\n'
      exit 0
    else
      printf '{"gate":"G6","pass":false,"reason":"%d CRITICAL/HIGH findings remain","markers":%d,"details":[]}\n' \
        "$total" "$total"
      exit 1
    fi
    ;;

  G7)
    # G7: Implement complete — check TDD evidence from agent summaries
    # This gate is validated by the orchestrator from agent return values,
    # not by scanning files. Script returns the task completion status.
    if [ ! -f "$TASKS" ]; then
      printf '{"gate":"G7","pass":false,"reason":"tasks.md not found","markers":0,"details":[]}\n'
      exit 1
    fi
    total=$(grep -c '^\- \[.\] T[0-9]' "$TASKS" 2>/dev/null) || total=0
    done=$(grep -c '^\- \[x\] T[0-9]' "$TASKS" 2>/dev/null) || done=0
    remaining=$((total - done))
    if [ "$remaining" -eq 0 ] && [ "$total" -gt 0 ]; then
      printf '{"gate":"G7","pass":true,"reason":"All %d tasks complete","markers":0,"total":%d,"done":%d}\n' \
        "$total" "$total" "$done"
      exit 0
    else
      printf '{"gate":"G7","pass":false,"reason":"%d of %d tasks incomplete","markers":%d,"total":%d,"done":%d}\n' \
        "$remaining" "$total" "$remaining" "$total" "$done"
      exit 1
    fi
    ;;

  *)
    printf '{"error":"Unknown gate: %s. Valid gates: G1 G2 G3 G4 G5 G6 G7"}\n' "$GATE"
    exit 2
    ;;
esac
