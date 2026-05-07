#!/usr/bin/env bash
# reviewability-gate.sh — Enforce reviewability budgets for SpecKit workflows.
#
# Usage:
#   reviewability-gate.sh setup <roadmap-or-workflow-file>
#   reviewability-gate.sh tasks <feature-dir>
#   reviewability-gate.sh diff [git-range]
#
# Exit:
#   0 = within budget
#   1 = block threshold exceeded
#   2 = usage or unreadable input

set -euo pipefail

MODE="${1:-}"
TARGET="${2:-}"

WARN_LOC=400
WARN_PROD_FILES=6
WARN_TOTAL_FILES=15
BLOCK_LOC=800
BLOCK_PROD_FILES=8
BLOCK_TOTAL_FILES=25

usage() {
  printf '{"error":"Usage: reviewability-gate.sh <setup|tasks|diff> <path-or-range>"}\n'
}

json_array() {
  jq -R . | jq -s .
}

surface_for_path() {
  local path="$1"
  case "$path" in
    *.sql|*migrations*|*schema*) echo "schema/migration" ;;
    src/app/api/*|openapi.json|*contracts*) echo "API" ;;
    *.tsx|src/components/*|src/app/*|*.stories.tsx|tests/e2e/*|tests/visual/*) echo "UI" ;;
    *scheduler*|*dispatch*|*runner*|*cron*|*workflow*) echo "scheduler/runtime" ;;
    *adapter*|*harness*|*openclaw*) echo "harness/adapter" ;;
    *seed*|*.json|*.yaml|*.yml|*.toml|*.env*) echo "seed/config" ;;
    docs/*|*.md|.specify/*|specs/*) echo "docs/process" ;;
    *) echo "other" ;;
  esac
}

is_excluded_generated() {
  local path="$1"
  case "$path" in
    pnpm-lock.yaml|*/pnpm-lock.yaml|package-lock.json|*/package-lock.json|npm-shrinkwrap.json|*/npm-shrinkwrap.json|yarn.lock|*/yarn.lock|bun.lock|*/bun.lock|bun.lockb|*/bun.lockb|Cargo.lock|*/Cargo.lock|Gemfile.lock|*/Gemfile.lock|Pipfile.lock|*/Pipfile.lock|poetry.lock|*/poetry.lock|composer.lock|*/composer.lock) return 0 ;;
    *.snap|*.snapshot|__snapshots__/*|snapshots/*) return 0 ;;
    vendor/*|vendors/*|third_party/*|generated/*|dist/*|build/*) return 0 ;;
    docs/ai/workflows/*/exports/*) return 0 ;;
    *) return 1 ;;
  esac
}

is_production_file() {
  local path="$1"
  case "$path" in
    src/*|app/*|lib/*|scripts/*|*.ts|*.tsx|*.js|*.jsx|*.mjs|*.cjs|*.sql) return 0 ;;
    *) return 1 ;;
  esac
}

reviewable_loc_from_numstat() {
  local sum=0 additions deletions path
  while IFS=$'\t' read -r additions deletions path; do
    [ -n "${path:-}" ] || continue
    [ "$additions" != "-" ] || continue
    [[ "$additions" =~ ^[0-9]+$ ]] || continue
    if ! is_excluded_generated "$path"; then
      sum=$((sum + additions))
    fi
  done
  printf '%s\n' "$sum"
}

emit_result() {
  local mode="$1" loc="$2" prod_files="$3" total_files="$4" surfaces_text="$5" exception="$6"
  local warnings=() blockers=()

  if [ "$loc" -gt "$WARN_LOC" ]; then warnings+=("reviewable LOC ${loc} exceeds warn threshold ${WARN_LOC}"); fi
  if [ "$prod_files" -gt "$WARN_PROD_FILES" ]; then warnings+=("production files ${prod_files} exceeds warn threshold ${WARN_PROD_FILES}"); fi
  if [ "$total_files" -gt "$WARN_TOTAL_FILES" ]; then warnings+=("total files ${total_files} exceeds warn threshold ${WARN_TOTAL_FILES}"); fi

  local surface_count
  surface_count=$(printf '%s\n' "$surfaces_text" | sed '/^$/d' | sort -u | wc -l | tr -d ' ')
  if [ "$surface_count" -gt 1 ]; then
    warnings+=("primary surfaces ${surface_count} exceeds warn threshold 1")
  fi

  if [ "$loc" -gt "$BLOCK_LOC" ]; then blockers+=("reviewable LOC ${loc} exceeds block threshold ${BLOCK_LOC}"); fi
  if [ "$prod_files" -gt "$BLOCK_PROD_FILES" ]; then blockers+=("production files ${prod_files} exceeds block threshold ${BLOCK_PROD_FILES}"); fi
  if [ "$total_files" -gt "$BLOCK_TOTAL_FILES" ]; then blockers+=("total files ${total_files} exceeds block threshold ${BLOCK_TOTAL_FILES}"); fi
  if [ "$surface_count" -gt 1 ]; then blockers+=("more than one primary surface requires split or exception"); fi

  local status="pass"
  if [ "${#warnings[@]}" -gt 0 ]; then status="warn"; fi
  if [ "${#blockers[@]}" -gt 0 ]; then status="block"; fi
  if [ "$status" = "block" ] && [ "$exception" = "true" ]; then status="exception"; fi

  local warnings_json blockers_json surfaces_json
  warnings_json=$(printf '%s\n' "${warnings[@]:-}" | sed '/^$/d' | json_array)
  blockers_json=$(printf '%s\n' "${blockers[@]:-}" | sed '/^$/d' | json_array)
  surfaces_json=$(printf '%s\n' "$surfaces_text" | sed '/^$/d' | sort -u | json_array)

  jq -cn \
    --arg mode "$mode" \
    --arg status "$status" \
    --argjson reviewable_loc "$loc" \
    --argjson production_files "$prod_files" \
    --argjson total_files "$total_files" \
    --argjson primary_surface_count "$surface_count" \
    --argjson primary_surfaces "$surfaces_json" \
    --argjson warnings "$warnings_json" \
    --argjson blockers "$blockers_json" \
    --argjson exception "$exception" \
    '{
      mode: $mode,
      status: $status,
      pass: ($status == "pass" or $status == "warn" or $status == "exception"),
      reviewable_loc: $reviewable_loc,
      production_files: $production_files,
      total_files: $total_files,
      primary_surface_count: $primary_surface_count,
      primary_surfaces: $primary_surfaces,
      thresholds: {
        warn: {reviewable_loc: 400, production_files: 6, total_files: 15, primary_surfaces: 1},
        block: {reviewable_loc: 800, production_files: 8, total_files: 25, primary_surfaces: 1}
      },
      transition_exception: $exception,
      warnings: $warnings,
      blockers: $blockers
    }'

  if [ "$status" = "block" ]; then exit 1; fi
}

parse_declared_scope() {
  local file="$1"
  if [ ! -f "$file" ]; then
    printf '{"error":"file not found: %s"}\n' "$file"
    exit 2
  fi

  local loc prod total exception surfaces
  loc=$(grep -Eio '(projected reviewable loc|reviewable loc)[^0-9]{0,40}[0-9]+' "$file" | grep -Eo '[0-9]+' | tail -1 || true)
  prod=$(grep -Eio '(projected production files|production files)[^0-9]{0,40}[0-9]+' "$file" | grep -Eo '[0-9]+' | tail -1 || true)
  total=$(grep -Eio '(projected total files|total files)[^0-9]{0,40}[0-9]+' "$file" | grep -Eo '[0-9]+' | tail -1 || true)
  surfaces=$(grep -Eio '(primary surface|primary surfaces)[^:]*:[[:space:]]*[A-Za-z/ ,_-]+' "$file" | sed 's/.*:[[:space:]]*//' | tr ',' '\n' | sed 's/^ *//;s/ *$//' || true)

  loc="${loc:-0}"
  prod="${prod:-0}"
  total="${total:-0}"
  if [ -z "$surfaces" ]; then surfaces="docs/process"; fi

  exception=false
  if grep -Eiq 'transition exception|split exception|ratified exception' "$file"; then
    exception=true
  fi

  emit_result "setup" "$loc" "$prod" "$total" "$surfaces" "$exception"
}

measure_feature_dir() {
  local dir="$1"
  if [ ! -d "$dir" ]; then
    printf '{"error":"feature directory not found: %s"}\n' "$dir"
    exit 2
  fi

  local tasks="$dir/tasks.md"
  local plan="$dir/plan.md"
  if [ ! -f "$tasks" ] || [ ! -r "$tasks" ]; then
    printf '{"error":"required tasks file not readable: %s"}\n' "$tasks"
    exit 2
  fi
  if [ -e "$plan" ] && { [ ! -f "$plan" ] || [ ! -r "$plan" ]; }; then
    printf '{"error":"optional plan file not readable: %s"}\n' "$plan"
    exit 2
  fi

  local input_files=("$tasks")
  if [ -f "$plan" ]; then
    input_files+=("$plan")
  fi

  local files_text surfaces_text loc prod total exception
  files_text=$(grep -hEo '([A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+' "${input_files[@]}" 2>/dev/null | sort -u || true)
  surfaces_text=$(printf '%s\n' "$files_text" | while read -r file; do [ -n "$file" ] && surface_for_path "$file"; done || true)
  total=$(printf '%s\n' "$files_text" | sed '/^$/d' | wc -l | tr -d ' ')
  prod=$(printf '%s\n' "$files_text" | while read -r file; do
    [ -n "$file" ] || continue
    if is_production_file "$file" && ! is_excluded_generated "$file"; then echo "$file"; fi
  done | wc -l | tr -d ' ')
  loc=$(grep -E '^\- \[[ x]\] T[0-9]' "$tasks" 2>/dev/null | wc -l | tr -d ' ')
  loc=$((loc * 40))
  exception=false
  if grep -Eiq 'transition exception|split exception|ratified exception' "${input_files[@]}" 2>/dev/null; then
    exception=true
  fi

  emit_result "tasks" "$loc" "$prod" "$total" "$surfaces_text" "$exception"
}

measure_diff() {
  local range="$1"
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    printf '{"error":"diff mode must run inside a git worktree"}\n'
    exit 2
  fi

  if ! git diff --name-only "$range" -- >/dev/null 2>&1; then
    printf '{"error":"git diff range could not be resolved: %s"}\n' "$range"
    exit 2
  fi

  local files_text surfaces_text numstat loc prod total exception
  files_text=$(git diff --name-only "$range" --)
  numstat=$(git diff --numstat "$range" --)
  loc=$(printf '%s\n' "$numstat" | reviewable_loc_from_numstat)
  total=$(printf '%s\n' "$files_text" | sed '/^$/d' | wc -l | tr -d ' ')
  prod=$(printf '%s\n' "$files_text" | while read -r file; do
    [ -n "$file" ] || continue
    if is_production_file "$file" && ! is_excluded_generated "$file"; then echo "$file"; fi
  done | wc -l | tr -d ' ')
  surfaces_text=$(printf '%s\n' "$files_text" | while read -r file; do [ -n "$file" ] && surface_for_path "$file"; done || true)
  exception=false
  if git diff "$range" -- '*.md' 2>/dev/null | grep -Eiq 'transition exception|split exception|ratified exception'; then
    exception=true
  fi

  emit_result "diff" "$loc" "$prod" "$total" "$surfaces_text" "$exception"
}

case "$MODE" in
  setup)
    [ -n "$TARGET" ] || { usage; exit 2; }
    parse_declared_scope "$TARGET"
    ;;
  tasks)
    [ -n "$TARGET" ] || { usage; exit 2; }
    measure_feature_dir "$TARGET"
    ;;
  diff)
    RANGE="${TARGET:-origin/main...HEAD}"
    measure_diff "$RANGE"
    ;;
  *)
    usage
    exit 2
    ;;
esac
