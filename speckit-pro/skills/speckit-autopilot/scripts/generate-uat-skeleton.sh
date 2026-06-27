#!/usr/bin/env bash
# generate-uat-skeleton.sh — Render a deterministic UAT runbook skeleton from spec.md.
#
# Usage:
#   generate-uat-skeleton.sh <spec-path> <output-path> [--workflow-file <path>]
#
# Parses ### User Story / Functional Requirements / Measurable Outcomes / Edge Cases
# headings from spec.md and renders them against uat-runbook-template.md. The Env Setup
# section is a pure formatter over the UAT_PROJECT_COMMANDS env var. Output is written
# once, deterministically (overwrite, no merge), and the script is silent on stdout.
#
# Exit codes: 0 success | 2 usage error | 1 unreadable/missing spec.

set -euo pipefail

# Copied verbatim from generate-pr-body.sh lines 45-65 (FR-002). Keep in sync if that helper changes.
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

# --- argv / usage validation (FR-006: usage error → exit 2, before spec check) ---
SPEC_PATH=""
OUTPUT_PATH=""
WORKFLOW_FILE=""
positional=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --workflow-file)
      if [ "$#" -lt 2 ]; then
        printf 'Usage: generate-uat-skeleton.sh <spec-path> <output-path> [--workflow-file <path>]\n' >&2
        exit 2
      fi
      WORKFLOW_FILE="$2"
      shift 2
      ;;
    --workflow-file=*)
      WORKFLOW_FILE="${1#--workflow-file=}"
      shift
      ;;
    -*)
      printf 'Error: unknown flag %s\n' "$1" >&2
      printf 'Usage: generate-uat-skeleton.sh <spec-path> <output-path> [--workflow-file <path>]\n' >&2
      exit 2
      ;;
    *)
      positional+=("$1")
      shift
      ;;
  esac
done

if [ "${#positional[@]}" -ne 2 ]; then
  printf 'Usage: generate-uat-skeleton.sh <spec-path> <output-path> [--workflow-file <path>]\n' >&2
  exit 2
fi
SPEC_PATH="${positional[0]}"
OUTPUT_PATH="${positional[1]}"

# --- spec readability (FR-006: unreadable spec → exit 1, no partial runbook) ---
if [ ! -r "$SPEC_PATH" ]; then
  printf 'Error: spec not readable: %s\n' "$SPEC_PATH" >&2
  exit 1
fi

FEATURE_DIR="$(dirname "$SPEC_PATH")"
PLAN_PATH="$FEATURE_DIR/plan.md"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE="$SCRIPT_DIR/../templates/uat-runbook-template.md"

# --- derived header values (deterministic: timestamp from spec mtime, FR-007) ---
spec_id="$(basename "$FEATURE_DIR")"
spec_timestamp="$(date -r "$SPEC_PATH" -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || true)"
if [ -z "$spec_timestamp" ]; then spec_timestamp="$spec_id/spec.md"; fi
branch="$spec_id"
pr_placeholder='Pending until PR is opened'

# ---------------------------------------------------------------------------
# Parse user stories (FR-001). Non-truncating awk scan — must NOT use the
# bounded extract_heading_section helper, which caps at head -40 and would drop
# stories past line 40 of the source spec.
# ---------------------------------------------------------------------------
story_titles=()
while IFS= read -r line; do
  story_titles+=("$line")
done < <(grep -E '^### User Story [0-9]' "$SPEC_PATH" || true)

# --- Per-Story Acceptance Tests + FR Coverage Matrix (US1) ---
per_story=""
fr_matrix=""
header_note=""

if [ "${#story_titles[@]}" -gt 0 ]; then
  fr_matrix+=$'| Story | Acceptance test |\n'
  fr_matrix+=$'|-------|-----------------|\n'
  idx=0
  for title in "${story_titles[@]}"; do
    idx=$((idx + 1))
    # Strip the leading "### " marker for display.
    display="$(printf '%s' "$title" | sed -E 's/^#{1,6}[[:space:]]+//')"
    per_story+="### ${display}"$'\n\n'
    per_story+="- [ ] Walk this story end to end and confirm the observable behavior the spec promises."$'\n\n'
    fr_matrix+="| ${display} | see the Per-Story Acceptance Tests block above |"$'\n'
  done
fi

# ---------------------------------------------------------------------------
# Zero-stories fallback (FR-003): key the Per-Story section by FR/SC bullets when
# no ### User Story headings exist. Bullets are extracted with a non-truncating awk
# scan scoped to their parent section (NOT the bounded extract_heading_section).
# Each parsed bullet's body (including nested/continuation lines) is reproduced
# verbatim as indented continuation lines.
# ---------------------------------------------------------------------------

# extract_section_block <file> <heading-regex> — print every line inside the first
# section whose heading matches, up to the next same-or-higher-level heading. No
# blank-line stripping, no line cap (unlike extract_heading_section).
extract_section_block() {
  local file="$1" heading_re="$2"
  awk -v hre="$heading_re" '
    BEGIN { in_section=0; section_level=0 }
    /^#{1,6}[[:space:]]+/ {
      marker=$1
      level=length(marker)
      if ($0 ~ hre) { in_section=1; section_level=level; next }
      if (in_section && level <= section_level) exit
    }
    in_section { print }
  ' "$file"
}

# annotate_clarifications — append an unresolved-clarification annotation to any line
# carrying the NEEDS CLARIFICATION marker (FR-005, Decision 3: fixed-string match on
# both the bare and colon-question forms). Other lines pass through unchanged.
annotate_clarifications() {
  awk '
    /NEEDS CLARIFICATION/ { print $0 "  **WARN:** unresolved clarification"; next }
    { print }
  '
}

# dedupe_ids — keep the first-seen `- **XX-NNN**:` bullet, drop later duplicates of the
# same ID along with their continuation lines, and emit a plain unprefixed stderr line
# naming each duplicated ID (FR-004; matches confidence-gate.sh's stderr style).
dedupe_ids() {
  awk '
    /^[[:space:]]*-[[:space:]]+\*\*[A-Z]+-[0-9]+\*\*/ {
      id=$0
      sub(/^[[:space:]]*-[[:space:]]+\*\*/, "", id)
      sub(/\*\*.*$/, "", id)
      if (id in seen) {
        printf "duplicate requirement ID %s; keeping first-seen entry\n", id > "/dev/stderr"
        dropping=1
        next
      }
      seen[id]=1
      dropping=0
      print
      next
    }
    # A new bullet (any ID-less or other top-level list item) ends a drop run.
    /^[[:space:]]*-[[:space:]]+/ { dropping=0; print; next }
    # Headings end a drop run.
    /^#{1,6}[[:space:]]+/ { dropping=0; print; next }
    dropping { next }
    { print }
  '
}

if [ "${#story_titles[@]}" -eq 0 ]; then
  header_note="> This spec has no user stories; tests are keyed by FR/SC."
  fr_block="$(extract_section_block "$SPEC_PATH" '[Ff]unctional [Rr]equirements' | dedupe_ids | annotate_clarifications)"
  sc_block="$(extract_section_block "$SPEC_PATH" '[Mm]easurable [Oo]utcomes' | dedupe_ids | annotate_clarifications)"

  per_story+="### FR-keyed Acceptance Tests"$'\n\n'
  if [ -n "$fr_block" ]; then
    per_story+="$fr_block"$'\n\n'
  else
    per_story+="No functional requirements found in spec.md"$'\n\n'
  fi
  per_story+="### SC-keyed Acceptance Tests"$'\n\n'
  if [ -n "$sc_block" ]; then
    per_story+="$sc_block"$'\n\n'
  else
    per_story+="No measurable outcomes found in spec.md"$'\n\n'
  fi

  fr_matrix="_No user stories — see the FR-keyed and SC-keyed Acceptance Tests above._"
fi

# --- Self-Review Findings (FR-009): echo the ## Self-Review block from the workflow
#     file via the copied extract_heading_section helper; graceful stub otherwise. ---
self_review='**Self-Review:** <not available — workflow file not provided>'
if [ -n "$WORKFLOW_FILE" ] && [ -r "$WORKFLOW_FILE" ]; then
  # `|| true`: extract_heading_section ends in `... | head -40`; a large section makes
  # the upstream producer take SIGPIPE (pipeline exit 141), which would abort the whole
  # script under `set -euo pipefail`. Fail open — empty result falls back to the stub.
  self_review_block="$(extract_heading_section "$WORKFLOW_FILE" "Self-Review" || true)"
  if [ -n "$self_review_block" ]; then
    self_review="$self_review_block"
  fi
fi

# --- Env Setup (FR-008): pure formatter over the UAT_PROJECT_COMMANDS JSON. Never
#     re-runs detect-commands.sh. Unset OR malformed JSON → unknown placeholders
#     (fail-soft); a key present with literal N/A → "not available for this project",
#     distinct from the unset placeholder. ---
format_env_setup() {
  local raw="${UAT_PROJECT_COMMANDS:-}"
  local placeholder='<unknown — autopilot did not pass PROJECT_COMMANDS>'
  local keys="BUILD TYPECHECK LINT LINT_FIX UNIT_TEST INTEGRATION_TEST SINGLE_FILE_INTEGRATION"
  local out="| Command | Value |"$'\n'"|---------|-------|"$'\n'
  local key val parsed_ok=0

  # Validate the JSON once. Empty (unset) or unparseable → fall through to placeholders.
  if [ -n "$raw" ]; then
    if printf '%s' "$raw" | jq -e . >/dev/null 2>&1; then
      parsed_ok=1
    fi
  fi

  for key in $keys; do
    if [ "$parsed_ok" -eq 1 ]; then
      val=""
      val=$(printf '%s' "$raw" | jq -r --arg k "$key" '.[$k] // "__UNSET__"' 2>/dev/null || true)
      if [ "$val" = "N/A" ]; then
        out+="| ${key} | _not available for this project_ |"$'\n'
      elif [ "$val" = "__UNSET__" ] || [ -z "$val" ]; then
        out+="| ${key} | ${placeholder} |"$'\n'
      else
        out+="| ${key} | \`${val}\` |"$'\n'
      fi
    else
      out+="| ${key} | ${placeholder} |"$'\n'
    fi
  done
  printf '%s' "$out"
}

env_setup="$(format_env_setup)"

# --- Rollback (FR-012): extract ## Rollback from spec.md, else plan.md, else a
#     synthesized stanza. Uses the copied extract_heading_section helper. The `|| true`
#     guards against a SIGPIPE abort on a large Rollback section (same reason as the
#     Self-Review echo above) — an empty result falls through to the synthesized stanza. ---
rollback="$(extract_heading_section "$SPEC_PATH" "Rollback" || true)"
if [ -z "$rollback" ]; then
  rollback="$(extract_heading_section "$PLAN_PATH" "Rollback" || true)"
fi
if [ -z "$rollback" ]; then
  rollback="git revert <SHA>; see plan.md for data-migration considerations"
fi

# --- Negative-Path Tests (FR-001, FR-005, FR-010): parse the ### Edge Cases bullets
#     with the non-truncating section extractor (full content, nested lines preserved)
#     and annotate any NEEDS CLARIFICATION marker. The stub line is emitted ONLY when
#     the ### Edge Cases section is absent or empty. ---
edge_block="$(extract_section_block "$SPEC_PATH" '[Ee]dge [Cc]ases' | annotate_clarifications)"
# Treat a block with no non-blank lines as empty.
if printf '%s' "$edge_block" | grep -q '[^[:space:]]'; then
  negative_path="$edge_block"
else
  negative_path="No edge cases identified in spec.md"
fi

# ---------------------------------------------------------------------------
# Render the template by substituting {{TOKEN}} markers. Build in memory; write
# argv[2] exactly once at the end (FR-006: no partial runbook on any error path).
# ---------------------------------------------------------------------------
# Read the template, dropping its leading HTML provenance comment (it documents the
# template file, not the rendered runbook). The comment runs from the first line
# `<!--` through the line containing the closing `-->`.
render="$(awk '
  NR==1 && $0 ~ /^<!--/ { stripping=1; next }
  stripping && $0 ~ /-->/ { stripping=0; next }
  stripping { next }
  { print }
' "$TEMPLATE")"
# Drop a single leading blank line left after the stripped comment, if present.
render="${render#$'\n'}"

substitute() {
  # substitute <token> <value> — replace every {{token}} with value (literal, multi-line safe).
  local token="$1" value="$2"
  local marker="{{${token}}}"
  local before after out=""
  local remaining="$render"
  while [[ "$remaining" == *"$marker"* ]]; do
    before="${remaining%%"$marker"*}"
    after="${remaining#*"$marker"}"
    out+="${before}${value}"
    remaining="$after"
  done
  out+="$remaining"
  render="$out"
}

substitute "SPEC_ID" "$spec_id"
substitute "BRANCH" "$branch"
substitute "PR_PLACEHOLDER" "$pr_placeholder"
substitute "SPEC_TIMESTAMP" "$spec_timestamp"
substitute "HEADER_NOTE" "$header_note"
substitute "ENV_SETUP" "$env_setup"
substitute "PER_STORY" "$per_story"
substitute "FR_MATRIX" "$fr_matrix"
substitute "NEGATIVE_PATH" "$negative_path"
substitute "SELF_REVIEW" "$self_review"
substitute "ROLLBACK" "$rollback"

printf '%s\n' "$render" > "$OUTPUT_PATH"
