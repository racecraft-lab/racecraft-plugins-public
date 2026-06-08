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
    */.process/*|.process/*) return 0 ;;
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
  # FR-008: count production-code additions only — a file must be a production
  # file (is_production_file) and not excluded/generated. Documentation, tests,
  # and config no longer contribute to the LOC metric. git numstat never lists a
  # path twice, so each production path is summed once (the gate's no-double-count
  # guarantee for diff mode; setup/tasks modes de-duplicate via `sort -u`).
  local sum=0 additions deletions path
  while IFS=$'\t' read -r additions deletions path; do
    [ -n "${path:-}" ] || continue
    [ "$additions" != "-" ] || continue
    [[ "$additions" =~ ^[0-9]+$ ]] || continue
    if is_production_file "$path" && ! is_excluded_generated "$path"; then
      sum=$((sum + additions))
    fi
  done
  printf '%s\n' "$sum"
}

# FR-011/012/013: the single shared typed-exception matcher, reused by all three
# modes (setup/tasks/diff) to prevent regex-engine drift. POSIX ERE via `grep -E`
# (never bash `[[ =~ ]]` over multi-line strings, never BRE). Reads candidate
# lines on stdin; echoes the matched class (refactor|infra|upgrade) for the first
# line matching the canonical pragma, or nothing. Line-anchored, case-sensitive,
# exact closed enum, no trailing content; the trailing `[[:space:]]*$` both rejects
# appended text (`refactor # ok`) and absorbs a CRLF `\r`. The legacy three-phrase
# keyword (split/transition/ratified exception) is honored by NO mode (FR-013).
match_exception_pragma() {
  { grep -E '^[[:space:]]*Reviewability-Exception:[[:space:]]+(refactor|infra|upgrade)[[:space:]]*$' || true; } \
    | sed -E 's/^[[:space:]]*Reviewability-Exception:[[:space:]]+([a-z]+)[[:space:]]*$/\1/' \
    | head -n1
}

# FR-009: a slice is greenfield iff every non-excluded changed path is git
# add-status `A` (a modified non-excluded file — doc, test, config, or production
# — disqualifies; a modified *excluded/generated* file such as a lockfile does
# NOT). Rename/copy detection is pinned off (`--no-renames`) so an ambient
# `diff.renames` git config cannot reclassify an add as a rename and vary the
# boolean. Echoes "true" or "false".
greenfield_from_diff() {
  local range="$1"
  local status path saw_any=false
  while IFS=$'\t' read -r status path; do
    [ -n "${status:-}" ] || continue
    [ -n "${path:-}" ] || continue
    if is_excluded_generated "$path"; then
      continue
    fi
    saw_any=true
    if [ "$status" != "A" ]; then
      printf 'false\n'
      return
    fi
  done < <(git diff --name-status --no-renames "$range" --)
  if [ "$saw_any" = "true" ]; then
    printf 'true\n'
  else
    printf 'false\n'
  fi
}

emit_result() {
  local mode="$1" loc="$2" prod_files="$3" total_files="$4" surfaces_text="$5" exception_class="$6" greenfield="$7"

  # FR-009: greenfield (all-new slice) scales ONLY the two reviewable_loc
  # thresholds ×1.5 (warn 400→600, block 800→1200). The production_files,
  # total_files, and primary_surfaces thresholds are unchanged by greenfield.
  local warn_loc="$WARN_LOC" block_loc="$BLOCK_LOC"
  if [ "$greenfield" = "true" ]; then
    warn_loc=$((WARN_LOC * 3 / 2))
    block_loc=$((BLOCK_LOC * 3 / 2))
  fi

  local warnings=() blockers=()

  if [ "$loc" -gt "$warn_loc" ]; then warnings+=("reviewable LOC ${loc} exceeds warn threshold ${warn_loc}"); fi
  if [ "$prod_files" -gt "$WARN_PROD_FILES" ]; then warnings+=("production files ${prod_files} exceeds warn threshold ${WARN_PROD_FILES}"); fi
  if [ "$total_files" -gt "$WARN_TOTAL_FILES" ]; then warnings+=("total files ${total_files} exceeds warn threshold ${WARN_TOTAL_FILES}"); fi

  local surface_count
  surface_count=$(printf '%s\n' "$surfaces_text" | sed '/^$/d' | sort -u | wc -l | tr -d ' ')
  # FR-010: a primary-surface count > 1 is a WARNING only — never a blocker.
  if [ "$surface_count" -gt 1 ]; then
    warnings+=("primary surfaces ${surface_count} exceeds warn threshold 1")
  fi

  if [ "$loc" -gt "$block_loc" ]; then blockers+=("reviewable LOC ${loc} exceeds block threshold ${block_loc}"); fi
  if [ "$prod_files" -gt "$BLOCK_PROD_FILES" ]; then blockers+=("production files ${prod_files} exceeds block threshold ${BLOCK_PROD_FILES}"); fi
  if [ "$total_files" -gt "$BLOCK_TOTAL_FILES" ]; then blockers+=("total files ${total_files} exceeds block threshold ${BLOCK_TOTAL_FILES}"); fi

  local status="pass"
  if [ "${#warnings[@]}" -gt 0 ]; then status="warn"; fi
  if [ "${#blockers[@]}" -gt 0 ]; then status="block"; fi

  # FR-011/012: a block carrying a valid typed pragma is flipped to an honored
  # exception. exception_honored is true ONLY when a block is flipped.
  local exception_honored=false
  if [ "$status" = "block" ] && [ -n "$exception_class" ]; then
    status="exception"
    exception_honored=true
  fi

  local warnings_json blockers_json surfaces_json class_json
  warnings_json=$(printf '%s\n' "${warnings[@]:-}" | sed '/^$/d' | json_array)
  blockers_json=$(printf '%s\n' "${blockers[@]:-}" | sed '/^$/d' | json_array)
  surfaces_json=$(printf '%s\n' "$surfaces_text" | sed '/^$/d' | sort -u | json_array)
  if [ -n "$exception_class" ]; then
    class_json=$(printf '%s' "$exception_class" | jq -R .)
  else
    class_json=null
  fi

  jq -cn \
    --arg mode "$mode" \
    --arg status "$status" \
    --argjson reviewable_loc "$loc" \
    --argjson production_files "$prod_files" \
    --argjson total_files "$total_files" \
    --argjson primary_surface_count "$surface_count" \
    --argjson primary_surfaces "$surfaces_json" \
    --argjson greenfield "$greenfield" \
    --argjson warn_loc "$warn_loc" \
    --argjson block_loc "$block_loc" \
    --argjson exception_honored "$exception_honored" \
    --argjson exception_class "$class_json" \
    --argjson warnings "$warnings_json" \
    --argjson blockers "$blockers_json" \
    '{
      mode: $mode,
      status: $status,
      pass: ($status == "pass" or $status == "warn" or $status == "exception"),
      reviewable_loc: $reviewable_loc,
      production_files: $production_files,
      total_files: $total_files,
      primary_surface_count: $primary_surface_count,
      primary_surfaces: $primary_surfaces,
      greenfield: $greenfield,
      thresholds: {
        warn: {reviewable_loc: $warn_loc, production_files: 6, total_files: 15, primary_surfaces: 1},
        block: {reviewable_loc: $block_loc, production_files: 8, total_files: 25, primary_surfaces: 1}
      },
      exception_honored: $exception_honored,
      exception_class: $exception_class,
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

  local loc prod total exception_class surfaces
  loc=$(grep -Eio '(projected reviewable loc|reviewable loc)[^0-9]{0,40}[0-9]+' "$file" | grep -Eo '[0-9]+' | tail -1 || true)
  prod=$(grep -Eio '(projected production files|production files)[^0-9]{0,40}[0-9]+' "$file" | grep -Eo '[0-9]+' | tail -1 || true)
  total=$(grep -Eio '(projected total files|total files)[^0-9]{0,40}[0-9]+' "$file" | grep -Eo '[0-9]+' | tail -1 || true)
  surfaces=$(grep -Eio '(primary surface|primary surfaces)[^:]*:[[:space:]]*[A-Za-z/ ,_-]+' "$file" | sed 's/.*:[[:space:]]*//' | tr ',' '\n' | sed 's/^ *//;s/ *$//' || true)

  loc="${loc:-0}"
  prod="${prod:-0}"
  total="${total:-0}"
  if [ -z "$surfaces" ]; then surfaces="docs/process"; fi

  # FR-011/013: honor only the typed pragma (the legacy three-phrase keyword is
  # honored by no mode). setup mode has no git add-status → greenfield is false.
  exception_class=$(match_exception_pragma < "$file")

  emit_result "setup" "$loc" "$prod" "$total" "$surfaces" "$exception_class" false
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

  local files_text surfaces_text loc prod total exception_class
  files_text=$(grep -hEo '([A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+' "${input_files[@]}" 2>/dev/null | sort -u || true)
  surfaces_text=$(printf '%s\n' "$files_text" | while read -r file; do [ -n "$file" ] && surface_for_path "$file"; done || true)
  total=$(printf '%s\n' "$files_text" | sed '/^$/d' | wc -l | tr -d ' ')
  prod=$(printf '%s\n' "$files_text" | while read -r file; do
    [ -n "$file" ] || continue
    if is_production_file "$file" && ! is_excluded_generated "$file"; then echo "$file"; fi
  done | wc -l | tr -d ' ')
  loc=$(grep -E '^\- \[[ x]\] T[0-9]' "$tasks" 2>/dev/null | wc -l | tr -d ' ')
  # KEEP IN SYNC with estimate-reviewable-loc.sh: this ×40 is per-tasks.md-line
  # (a task-count heuristic); the estimator's PROD_LOC_PER_FILE is per-file (same
  # magnitude, different unit). They are deliberately NOT a shared variable — see
  # PRSG-006 spec FR-007. The L1 drift guard asserts this comment marker is present
  # in both files (comment-presence only, not numeric value-equality).
  loc=$((loc * 40))
  # FR-011/013: honor only the typed pragma (the legacy three-phrase keyword is
  # honored by no mode). tasks mode has no git add-status → greenfield is false.
  exception_class=$(cat "${input_files[@]}" 2>/dev/null | match_exception_pragma || true)

  emit_result "tasks" "$loc" "$prod" "$total" "$surfaces_text" "$exception_class" false
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

  local files_text surfaces_text numstat loc prod total exception_class greenfield
  files_text=$(git diff --name-only "$range" --)
  numstat=$(git diff --numstat "$range" --)
  loc=$(printf '%s\n' "$numstat" | reviewable_loc_from_numstat)
  total=$(printf '%s\n' "$files_text" | sed '/^$/d' | wc -l | tr -d ' ')
  prod=$(printf '%s\n' "$files_text" | while read -r file; do
    [ -n "$file" ] || continue
    if is_production_file "$file" && ! is_excluded_generated "$file"; then echo "$file"; fi
  done | wc -l | tr -d ' ')
  surfaces_text=$(printf '%s\n' "$files_text" | while read -r file; do [ -n "$file" ] && surface_for_path "$file"; done || true)
  # FR-012: read the pragma ONLY from ADDED (`+`) lines of committed Markdown in
  # the diff range — never the PR description or commit messages (both mutable).
  # `grep -v '^+++'` drops the unified-diff header so a +++ b/<file> path that
  # resembles the pragma cannot self-satisfy the matcher; `sed 's/^+//'` strips the
  # leading `+`. A pragma on a context/removed line is not an added line → no flip.
  exception_class=$(git diff "$range" -- '*.md' 2>/dev/null | grep '^+' | grep -v '^+++' | sed 's/^+//' | match_exception_pragma || true)
  greenfield=$(greenfield_from_diff "$range")

  emit_result "diff" "$loc" "$prod" "$total" "$surfaces_text" "$exception_class" "$greenfield"
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
