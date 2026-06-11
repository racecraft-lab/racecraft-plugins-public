#!/usr/bin/env bash
# generate-pr-body.sh — Build a review-packet PR body from host templates.
#
# Usage:
#   generate-pr-body.sh [--slice-packet <json-file>] <repo-root> <feature-dir> <output-file> [diff-range]

set -euo pipefail

usage() {
  printf 'Usage: generate-pr-body.sh [--slice-packet <json-file>] <repo-root> <feature-dir> <output-file> [diff-range]\n' >&2
}

invalid_slice_packet() {
  printf 'generate-pr-body.sh: invalid slice packet: %s\n' "$1" >&2
  exit 2
}

require_jq() {
  command -v jq >/dev/null 2>&1 || invalid_slice_packet "jq is required"
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
FALLBACK_TEMPLATE="$PLUGIN_ROOT/skills/speckit-autopilot/templates/pr-description-template.md"

SLICE_PACKET=""
ARGS=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --slice-packet)
      if [ "$#" -lt 2 ] || [ -z "${2:-}" ]; then
        invalid_slice_packet "missing path"
      fi
      SLICE_PACKET="$2"
      shift 2
      ;;
    --)
      shift
      while [ "$#" -gt 0 ]; do
        ARGS+=("$1")
        shift
      done
      ;;
    --*)
      usage
      exit 2
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

REPO_ROOT="${ARGS[0]:-}"
FEATURE_DIR="${ARGS[1]:-}"
OUTPUT_FILE="${ARGS[2]:-}"
DIFF_RANGE="${ARGS[3]:-origin/main...HEAD}"

if [ -z "$REPO_ROOT" ] || [ -z "$FEATURE_DIR" ] || [ -z "$OUTPUT_FILE" ] || [ "${#ARGS[@]}" -gt 4 ]; then
  usage
  exit 2
fi

if [ -n "$SLICE_PACKET" ]; then
  if [ ! -f "$SLICE_PACKET" ]; then
    invalid_slice_packet "file not found: $SLICE_PACKET"
  fi
  require_jq
  if ! jq -e '
    type == "object"
    and (.slice_id | type == "string" and length > 0)
    and (.review_order | type == "number" and . == floor and . >= 1)
    and (.total_slices | type == "number" and . == floor and . >= 1)
    and (.base_branch | type == "string" and length > 0)
    and (.head_branch | type == "string" and length > 0)
    and (.declared_files | type == "array" and all(.[]; type == "string" and length > 0))
    and ((.declared_tests // []) | type == "array" and all(.[]; type == "string" and length > 0))
    and (.scoped_verification | type == "object")
    and (.scoped_verification.commands | type == "array")
    and (.full_verification_evidence | type == "string" and length > 0)
    and (.prs_row | type == "object")
    and (.prs_row.slice_id | type == "string" and length > 0)
    and (.prs_row.branch | type == "string" and length > 0)
    and (.prs_row.base_branch | type == "string" and length > 0)
    and (.prs_row.status | type == "string" and length > 0)
    and (.prs_row.head_sha | type == "string" and length > 0)
  ' "$SLICE_PACKET" >/dev/null 2>&1; then
    invalid_slice_packet "schema validation failed: $SLICE_PACKET"
  fi
fi

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
# What changed
$what

# Why it matters
$why

# Anything reviewers should know
$non_goals
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

for heading in "What changed" "Why it matters" "Anything reviewers should know"; do
  append_missing_section "$heading"
done

append_slice_packet_sections() {
  local packet="$1"
  {
    printf '\n## Slice summary\n\n'
    jq -r '
      "- Slice: `" + .slice_id + "`",
      "- PR row status: `" + .prs_row.status + "`",
      "- Head branch: `" + .head_branch + "`",
      "- Base branch: `" + .base_branch + "`"
    ' "$packet"

    printf '\n## Review order\n\n'
    jq -r '"\(.review_order) of \(.total_slices)"' "$packet"

    printf '\n## Scope\n\n'
    jq -r '
      if (.declared_files | length) == 0 then
        "- No declared files recorded."
      else
        .declared_files[] | "- `" + . + "`"
      end
    ' "$packet"

    printf '\n## Verification\n\n'
    jq -r '
      if (.scoped_verification.commands | length) == 0 then
        "- No scoped verification commands recorded for this slice."
      else
        .scoped_verification.commands[]
        | "- `" + .command + "` (" + .gate_type + ", exit " + (.exit_status | tostring) + ") — " + .evidence_path
      end
    ' "$packet"

    printf '\n## Traceability\n\n'
    jq -r '
      if ((.traceability // []) | length) == 0 then
        "- No traceability rows recorded."
      else
        (.traceability // [])[]
        | "- " + .requirement
          + ": files " + ((.files // []) | join(", "))
          + "; evidence " + ((.evidence // []) | join(", "))
      end
    ' "$packet"

    printf '\n## Restack or rollback\n\n'
    jq -r '.restack_note // "Use the recorded branch/base order for restack or rollback."' "$packet"

    printf '\n## Known gaps\n\n'
    jq -r '
      if ((.known_gaps // []) | length) == 0 then
        "- None recorded."
      else
        (.known_gaps // [])[] | "- " + .
      end
    ' "$packet"

    printf '\n## Full regression evidence\n\n'
    jq -r '"- `" + .full_verification_evidence + "`"' "$packet"
  } >> "$OUTPUT_FILE"
}

if [ -n "$SLICE_PACKET" ]; then
  append_slice_packet_sections "$SLICE_PACKET"
fi

# Reviewer checklist & scope details — appended unconditionally as a collapsed
# <details> block so governance numbers stay out of the reader's way (a reviewer
# expands them only if needed). NOT a Markdown heading, so it is appended directly
# rather than via the append_missing_section / has_heading mechanism above. Numbers
# are pre-filled from the reviewability gate JSON; absent values render as "unknown".
{
  printf '\n<details>\n<summary>Reviewer checklist &amp; scope details</summary>\n\n'
  printf '**Size:** %s reviewable lines across %s files (%s production). Budget: %s.\n' \
    "${reviewable_loc:-unknown}" "${total_files:-unknown}" "${production_files:-unknown}" "${budget_status:-unknown}"
  printf '**Primary surfaces:** %s.\n\n' "${surfaces:-unknown}"
  printf '**Review in this order:**\n'
  printf '1. The spec and plan under `%s`.\n' "$FEATURE_DIR"
  printf '2. The highest-risk production files.\n'
  printf '3. Verification evidence and any known gaps.\n\n'
  printf '**Verification:**\n'
  printf -- '- [ ] Build / Typecheck / Lint / Tests pass (or N/A for this repo)\n'
  printf -- '- [ ] Visual review completed or N/A\n\n'
  printf '**Rollback:** `git revert <SHA>` unless noted otherwise.\n'
  printf '</details>\n'
} >> "$OUTPUT_FILE"

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
