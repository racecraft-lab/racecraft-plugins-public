#!/usr/bin/env bash
# estimate-reviewable-loc.sh — Plan-phase reviewability budget estimator (PRSG-006 US1).
#
# Projects a slice's production-LOC footprint at PLAN time from plan.md's
# `## Declared File Operations` block (before tasks.md exists), and emits one JSON
# object to stdout with a three-value status: pass | over_budget | not_estimated.
#
# Advisory, never blocks: the budget verdict is carried in JSON `status`, never in
# the exit code (FR-004/FR-007). Exit 0 for ALL three content statuses; exit 2 only
# for a usage error or an absent/unreadable input file.
#
# Usage:
#   estimate-reviewable-loc.sh <path-to-plan.md>
#
# Exit:
#   0 = ran successfully (status is one of pass | over_budget | not_estimated)
#   2 = usage error (missing/extra args) or unreadable/absent input file
#
# Determinism (FR-002): the same plan.md input produces byte-identical stdout. No
# timestamps, no $RANDOM. Entries are de-duplicated by repo-relative path before
# counting (counterpart to the gate's `sort -u`), so a duplicated declaration is
# stable.

set -euo pipefail

# ── Per-file production-LOC constant ─────────────────────────────────────────
# KEEP IN SYNC with reviewability-gate.sh
#   The gate's `×40` multiplier (reviewability-gate.sh:199) is applied PER TASK
#   (a tasks.md checklist line); this constant is PER FILE (a declared plan.md
#   entry). Same magnitude, DIFFERENT unit — so this is deliberately NOT a shared
#   variable, and the drift guard is the repo's comment-only keep-in-sync
#   convention (an L1 structural check asserts the marker is present in BOTH
#   scripts), NOT numeric value-equality (the per-file value is a tunable
#   heuristic; equality would false-fail on a legitimate tune — FR-007).
PROD_LOC_PER_FILE=40

# ── Base reviewability thresholds (production-only metric) ────────────────────
# Retained at the gate's warn=400 / block=800 numbers (cutover continuity); the
# greenfield allowance scales ONLY these two when every declared entry is NEW.
BASE_WARN_LOC=400
BASE_BLOCK_LOC=800
GREENFIELD_MULTIPLIER=1.5

usage() {
  printf '{"error":"Usage: estimate-reviewable-loc.sh <plan.md>"}\n' >&2
}

# ── Reusable classification predicates ───────────────────────────────────────
# Copied from reviewability-gate.sh (is_production_file, is_excluded_generated)
# so the plan-time production-only metric matches the gate's diff-time metric —
# INCLUDING the `*/.process/*` exclusion arm the gate carries (PRSG-001/#111), so
# the estimator and gate agree on a production-ish file declared under `.process/`.
# Reused as-is (no signature change) per the spec's Assumptions and tasks T002/T011.
#
# KNOWN LIMITATION (recorded per spec §Assumptions; do NOT "fix" here):
#   is_production_file matches src/ app/ lib/ scripts/ prefixes + JS/TS/SQL
#   extensions. It does NOT match this repo's own plugin production code (`.sh`
#   under speckit-pro/skills/), so plugin-script slices — including PRSG-006's
#   own — under-count to production:0. Broadening this predicate to plugin-script
#   paths is PRSG-001 scope, out of scope here; it is reused unchanged on purpose.
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

# ── Argument parsing (exactly one readable file) ─────────────────────────────
if [ "$#" -ne 1 ]; then
  usage
  exit 2
fi

PLAN="$1"
if [ ! -f "$PLAN" ] || [ ! -r "$PLAN" ]; then
  printf '{"error":"plan file not readable: %s"}\n' "$PLAN" >&2
  exit 2
fi

# ── Declared-files parser ────────────────────────────────────────────────────
# Parse ONLY the section under the `## Declared File Operations` heading. The
# contract is: with no such heading block, the result is not_estimated. Scoping
# to the section (rather than grepping the whole file) enforces that and stops a
# stray `- NEW ...` bullet elsewhere in the plan from being counted. The section
# runs from that h2 to the next h2 (or EOF); `### ` subsections do not end it.
#
# Within the section, count only lines matching the entry grammar (POSIX ERE):
#   ^[[:space:]]*[-*][[:space:]]+(NEW|MODIFIED)[[:space:]]+([^[:space:]]+)[[:space:]]*$
# Group 1 = STATUS (NEW|MODIFIED); group 2 = repo-relative path. All other lines
# (prose, blank, headings, comments) are ignored. The full path is required so
# is_production_file's prefix arm can classify (plan.md Decision 1).
ENTRY_RE='^[[:space:]]*[-*][[:space:]]+(NEW|MODIFIED)[[:space:]]+([^[:space:]]+)[[:space:]]*$'

declared_section=$(awk '
  /^##[[:space:]]+Declared File Operations[[:space:]]*$/ { in_section = 1; next }
  in_section && /^##[[:space:]]/ { in_section = 0 }
  in_section { print }
' "$PLAN")

# Extract "STATUS<TAB>path" for each matching line, preserving file order. Use a
# literal tab (printf), NOT sed's `\t` escape — BSD/macOS sed does not expand
# `\t` in the replacement, which would collapse STATUS and path into one field
# and drop every entry. The `IFS=$'\t' read` split below needs a real tab.
TAB=$(printf '\t')
raw_entries=$(printf '%s\n' "$declared_section" | grep -E "$ENTRY_RE" 2>/dev/null \
  | sed -E 's/'"$ENTRY_RE"'/\1'"$TAB"'\2/' || true)

declare -a paths_in_order=()
declare -a statuses_in_order=()

find_path_index() {
  local needle="$1"
  local index
  for index in "${!paths_in_order[@]}"; do
    if [ "${paths_in_order[$index]}" = "$needle" ]; then
      printf '%s' "$index"
      return 0
    fi
  done
  return 1
}

if [ -n "$raw_entries" ]; then
  while IFS=$'\t' read -r status path; do
    [ -n "${path:-}" ] || continue
    if index="$(find_path_index "$path")"; then
      if [ "$status" = "MODIFIED" ]; then
        # De-dup conflict: a path declared both NEW and MODIFIED resolves to
        # MODIFIED (fail-safe toward "an existing file is touched" — so the slice
        # is correctly NOT greenfield; contract §De-duplication, FR-006).
        statuses_in_order[$index]="MODIFIED"
      fi
    else
      paths_in_order+=("$path")
      statuses_in_order+=("$status")
    fi
  done <<< "$raw_entries"
fi

total_entries=${#paths_in_order[@]}

# ── not_estimated: no parseable declared-files entries ───────────────────────
# Distinct from the file-level error path (absent/unreadable file → exit 2). A
# readable plan.md whose declared-files block is absent or empty is a CONTENT
# status: projected null, never recorded as a within-budget pass (vacuous-pass
# guard, FR-003).
if [ "$total_entries" -eq 0 ]; then
  jq -cn \
    --argjson warn "$BASE_WARN_LOC" \
    --argjson block "$BASE_BLOCK_LOC" \
    --argjson gm "$GREENFIELD_MULTIPLIER" \
    --argjson base_warn "$BASE_WARN_LOC" \
    --argjson base_block "$BASE_BLOCK_LOC" \
    '{
      tool: "estimate-reviewable-loc",
      status: "not_estimated",
      projected: null,
      declared_files: { production: 0, new: 0, modified: 0, total_entries: 0 },
      greenfield: false,
      thresholds: {
        warn: $warn,
        block: $block,
        greenfield_multiplier: $gm,
        base_warn: $base_warn,
        base_block: $base_block
      }
    }'
  exit 0
fi

# ── Tally de-duplicated entries ──────────────────────────────────────────────
new_count=0
modified_count=0
production_count=0
greenfield=true

for index in "${!paths_in_order[@]}"; do
  path="${paths_in_order[$index]}"
  status="${statuses_in_order[$index]}"

  if [ "$status" = "NEW" ]; then
    new_count=$((new_count + 1))
  else
    modified_count=$((modified_count + 1))
  fi

  # Greenfield (FR-006): every non-excluded declared entry is NEW and none is
  # MODIFIED — same file-set rule as the gate's diff-mode add-status `A` detector
  # (FR-009). A MODIFIED *excluded/generated* file (e.g. a lockfile) does NOT
  # disqualify; a MODIFIED non-excluded file does.
  if [ "$status" = "MODIFIED" ] && ! is_excluded_generated "$path"; then
    greenfield=false
  fi

  # Production-only metric: production file AND not excluded/generated.
  if is_production_file "$path" && ! is_excluded_generated "$path"; then
    production_count=$((production_count + 1))
  fi
done

# ── Projection + greenfield threshold scaling ────────────────────────────────
projected=$((production_count * PROD_LOC_PER_FILE))

applied_warn=$BASE_WARN_LOC
applied_block=$BASE_BLOCK_LOC
if [ "$greenfield" = "true" ]; then
  # Scale ONLY the LOC thresholds ×1.5 (warn 400→600, block 800→1200). Integer
  # math keeps output deterministic; ×3/2 is exact for these even values.
  applied_warn=$((BASE_WARN_LOC * 3 / 2))
  applied_block=$((BASE_BLOCK_LOC * 3 / 2))
fi

# ── Budget verdict (advisory — all statuses exit 0) ──────────────────────────
if [ "$projected" -gt "$applied_block" ]; then
  status="over_budget"
else
  status="pass"
fi

jq -cn \
  --arg status "$status" \
  --argjson projected "$projected" \
  --argjson production "$production_count" \
  --argjson new "$new_count" \
  --argjson modified "$modified_count" \
  --argjson total_entries "$total_entries" \
  --argjson greenfield "$greenfield" \
  --argjson warn "$applied_warn" \
  --argjson block "$applied_block" \
  --argjson gm "$GREENFIELD_MULTIPLIER" \
  --argjson base_warn "$BASE_WARN_LOC" \
  --argjson base_block "$BASE_BLOCK_LOC" \
  '{
    tool: "estimate-reviewable-loc",
    status: $status,
    projected: $projected,
    declared_files: {
      production: $production,
      new: $new,
      modified: $modified,
      total_entries: $total_entries
    },
    greenfield: $greenfield,
    thresholds: {
      warn: $warn,
      block: $block,
      greenfield_multiplier: $gm,
      base_warn: $base_warn,
      base_block: $base_block
    }
  }'

exit 0
