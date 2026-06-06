#!/usr/bin/env bash
# generate-pr-body.sh — Build a review-packet PR body from host templates.
#
# Usage:
#   generate-pr-body.sh <repo-root> <feature-dir> <output-file> [diff-range]

set -euo pipefail

REPO_ROOT="${1:-}"
FEATURE_DIR="${2:-}"
OUTPUT_FILE="${3:-}"
DIFF_RANGE="${4:-origin/main...HEAD}"

if [ -z "$REPO_ROOT" ] || [ -z "$FEATURE_DIR" ] || [ -z "$OUTPUT_FILE" ]; then
  printf 'Usage: generate-pr-body.sh <repo-root> <feature-dir> <output-file> [diff-range]\n' >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
FALLBACK_TEMPLATE="$PLUGIN_ROOT/skills/speckit-autopilot/templates/pr-description-template.md"

detect_host_template() {
  local root="$1"
  local candidate
  for candidate in \
    "$root/.github/pull_request_template.md" \
    "$root/.github/PULL_REQUEST_TEMPLATE.md" \
    "$root/docs/pull_request_template.md" \
    "$root/pull_request_template.md"; do
    if [ -f "$candidate" ]; then
      printf '%s\n' "$candidate"
      return
    fi
  done
  if [ -d "$root/.github/PULL_REQUEST_TEMPLATE" ]; then
    candidate=$(find "$root/.github/PULL_REQUEST_TEMPLATE" -maxdepth 1 -type f -name '*.md' | sort | head -1)
    if [ -n "$candidate" ]; then
      printf '%s\n' "$candidate"
      return
    fi
  fi
}

extract_heading_section() {
  local file="$1" heading="$2"
  if [ ! -f "$file" ]; then return; fi
  awk -v heading="$heading" '
    BEGIN { in_section=0; section_level=0 }
    /^#{1,6}[[:space:]]+/ {
      marker=$1
      level=length(marker)
      current=$0
      sub(/^#{1,6}[[:space:]]+/, "", current)
      sub(/[[:space:]]+#+[[:space:]]*$/, "", current)
      if (tolower(current) == tolower(heading)) {
        in_section=1
        section_level=level
        next
      }
      if (in_section && level <= section_level) exit
    }
    in_section { print }
  ' "$file" | sed '/^[[:space:]]*$/d' | head -40
}

has_heading() {
  local file="$1" heading="$2"
  if [ ! -f "$file" ]; then return 1; fi
  awk -v heading="$heading" '
    /^#{1,6}[[:space:]]+/ {
      current=$0
      sub(/^#{1,6}[[:space:]]+/, "", current)
      sub(/[[:space:]]+#+[[:space:]]*$/, "", current)
      if (tolower(current) == tolower(heading)) found=1
    }
    END { exit found ? 0 : 1 }
  ' "$file"
}

spec_value() {
  local heading="$1"
  extract_heading_section "$FEATURE_DIR/spec.md" "$heading"
}

reviewability_json='{}'
if [ -x "$SCRIPT_DIR/reviewability-gate.sh" ]; then
  set +e
  reviewability_json=$("$SCRIPT_DIR/reviewability-gate.sh" diff "$DIFF_RANGE" 2>/dev/null)
  set -e
fi

reviewable_loc=$(printf '%s' "$reviewability_json" | jq -r '.reviewable_loc // ""' 2>/dev/null || true)
production_files=$(printf '%s' "$reviewability_json" | jq -r '.production_files // ""' 2>/dev/null || true)
total_files=$(printf '%s' "$reviewability_json" | jq -r '.total_files // ""' 2>/dev/null || true)
budget_status=$(printf '%s' "$reviewability_json" | jq -r '.status // ""' 2>/dev/null || true)
surfaces=$(printf '%s' "$reviewability_json" | jq -r '(.primary_surfaces // []) | join(", ")' 2>/dev/null || true)

what=$(spec_value "Summary")
why=$(spec_value "Problem Statement")
non_goals=$(spec_value "Non-goals")
if [ -z "$what" ]; then what="See the linked spec, plan, and task artifacts for the implemented scope."; fi
if [ -z "$why" ]; then why="See the spec goals and workflow rationale for the problem this PR addresses."; fi
if [ -z "$non_goals" ]; then non_goals="No additional non-goals were extracted automatically. Review the spec and workflow for deferred work."; fi

review_packet=$(mktemp)
trap 'rm -f "$review_packet"' EXIT
cat > "$review_packet" <<EOF
# What
$what

# Why
$why

# Non-goals
$non_goals

# Review Order
1. Start with \`$FEATURE_DIR/spec.md\`, \`$FEATURE_DIR/plan.md\`, and \`$FEATURE_DIR/tasks.md\`.
2. Review production files by primary surface: ${surfaces:-unknown}.
3. Confirm verification evidence, known gaps, and rollback/flag notes before approval.

# Scope Budget
- Reviewable LOC: ${reviewable_loc:-unknown}
- Production files: ${production_files:-unknown}
- Total files: ${total_files:-unknown}
- Primary surfaces touched: ${surfaces:-unknown}
- Budget result: ${budget_status:-unknown}
- Split or exception rationale: Fill from workflow if the result is not within budget.

# Traceability
| Requirement / Goal | Changed files | Verification |
|---|---|---|
| Spec requirements | \`$FEATURE_DIR/spec.md\`, implementation diff | Commands listed below |

# Verification
- [ ] Build passes
- [ ] Typecheck passes
- [ ] Lint passes
- [ ] Tests pass
- [ ] Visual review completed or N/A

Commands run and results:
- Fill with final local and CI evidence.

# Known Gaps
Fill with skipped checks, baseline failures, or deferred follow-up from the workflow.

# Rollback / Flags
Fill with feature flags, rollout scope, rollback files, or N/A.
EOF

template=$(detect_host_template "$REPO_ROOT" || true)
if [ -z "$template" ]; then
  template="$FALLBACK_TEMPLATE"
fi

cp "$template" "$OUTPUT_FILE"

append_missing_section() {
  local heading="$1"
  if ! has_heading "$OUTPUT_FILE" "$heading"; then
    {
      printf '\n# %s\n' "$heading"
      extract_heading_section "$review_packet" "$heading"
      printf '\n'
    } >> "$OUTPUT_FILE"
  fi
}

for heading in "What" "Why" "Non-goals" "Review Order" "Scope Budget" "Traceability" "Verification" "Known Gaps" "Rollback / Flags"; do
  append_missing_section "$heading"
done

# Dedicated, size-aware UAT Runbook block (FR-013). Deliberately NOT routed through
# the heading loop / append_missing_section / extract_heading_section above — those
# truncate at head -40 and strip blank lines. Emitted at H2 (## UAT Runbook); SC-005
# greps for that exact literal. Fail-open: an absent runbook still emits the heading.
uat_runbook="$FEATURE_DIR/.process/uat-runbook.md"
{
  printf '\n## UAT Runbook\n\n'
  if [ -f "$uat_runbook" ]; then
    uat_size=$(wc -c < "$uat_runbook")
    if [ "$uat_size" -lt 50000 ]; then
      cat "$uat_runbook"
    else
      head -60 "$uat_runbook"
      printf '\n[Full runbook](./.process/uat-runbook.md)\n'
    fi
  else
    # shellcheck disable=SC2016  # backticks are literal Markdown, not a shell expansion
    printf '%s\n' 'No UAT runbook was generated for this feature (expected at `.process/uat-runbook.md`).'
  fi
} >> "$OUTPUT_FILE"

{
  printf '\n<!-- speckit-pro-review-packet-source\n'
  printf 'template: %s\n' "$template"
  printf 'feature_dir: %s\n' "$FEATURE_DIR"
  printf 'diff_range: %s\n' "$DIFF_RANGE"
  printf 'reviewability: %s\n' "$(printf '%s' "$reviewability_json" | tr '\n' ' ')"
  printf '%s\n' '-->'
} >> "$OUTPUT_FILE"
