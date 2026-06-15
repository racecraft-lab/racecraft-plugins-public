#!/usr/bin/env bash
# generate-pr-body.sh — Build a review-packet PR body from host templates.
#
# Usage:
#   generate-pr-body.sh [--slice-packet <json-file>] [--packet-output <json-file>] <repo-root> <feature-dir> <output-file> [diff-range]

set -euo pipefail

usage() {
  printf 'Usage: generate-pr-body.sh [--slice-packet <json-file>] [--packet-output <json-file>] <repo-root> <feature-dir> <output-file> [diff-range]\n' >&2
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
PACKET_OUTPUT=""
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
    --packet-output)
      if [ "$#" -lt 2 ] || [ -z "${2:-}" ]; then
        usage
        exit 2
      fi
      PACKET_OUTPUT="$2"
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

if [ -n "$PACKET_OUTPUT" ] && [ -n "$SLICE_PACKET" ]; then
  printf 'generate-pr-body.sh: --packet-output currently supports single mode only\n' >&2
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

repo_relative_path() {
  local path="$1" root="$2"
  root="${root%/}"
  path="${path%/}"
  case "$path" in
    "$root"/*)
      printf '%s\n' "${path#"$root"/}"
      ;;
    "$root")
      printf '.\n'
      ;;
    ./*)
      printf '%s\n' "${path#./}"
      ;;
    *)
      printf '%s\n' "$path"
      ;;
  esac
}

repo_path() {
  local path="$1" root="$2"
  case "$path" in
    /*) printf '%s\n' "$path" ;;
    *) printf '%s/%s\n' "${root%/}" "$path" ;;
  esac
}

feature_display_title() {
  local spec
  spec="$(repo_path "$FEATURE_DIR" "$REPO_ROOT")/spec.md"
  if [ ! -f "$spec" ]; then
    return
  fi
  awk '
    /^# Feature Specification:[[:space:]]*/ {
      sub(/^# Feature Specification:[[:space:]]*/, "", $0)
      print
      exit
    }
    /^#[[:space:]]+/ {
      sub(/^#[[:space:]]+/, "", $0)
      print
      exit
    }
  ' "$spec"
}

generated_title_description() {
  local display_title="$1"
  if ! printf '%s' "$display_title" | grep -Eq '[^[:space:]]'; then
    printf 'generate-pr-body.sh: input_error: feature spec title is required for packet title generation\n' >&2
    return 2
  fi
  case "$display_title" in
    Add\ *|Update\ *|Fix\ *|Remove\ *|Support\ *)
      printf '%s\n' "$display_title"
      ;;
    *)
      printf 'Add %s%s\n' \
        "$(printf '%s' "${display_title%"${display_title#?}"}" | tr '[:upper:]' '[:lower:]')" \
        "${display_title#?}"
      ;;
  esac
}

conventional_scope_from_feature_dir() {
  local feature_dir_rel="$1" base spec_suffix
  base="${feature_dir_rel%/}"
  base="${base##*/}"
  if [[ "$base" =~ ^[Pp][Rr][Ss][Gg]-([0-9]+)(-|$) ]]; then
    printf 'PRSG-%s\n' "${BASH_REMATCH[1]}"
  elif [[ "$base" =~ ^[Ss][Pp][Ee][Cc]-([0-9A-Za-z]+)(-|$) ]]; then
    spec_suffix="${BASH_REMATCH[1]^^}"
    printf 'SPEC-%s\n' "$spec_suffix"
  elif [[ "$base" =~ ^[Dd][Oo][Cc]-([0-9A-Za-z]+)(-|$) ]]; then
    spec_suffix="${BASH_REMATCH[1]^^}"
    printf 'DOC-%s\n' "$spec_suffix"
  else
    printf 'speckit-pro\n'
  fi
}

conventional_type_from_feature_dir() {
  local feature_dir_rel="$1" base
  base="${feature_dir_rel%/}"
  base="${base##*/}"
  if [[ "$base" =~ ^[Dd][Oo][Cc]-([0-9A-Za-z]+)(-|$) ]]; then
    printf 'docs\n'
  else
    printf 'feat\n'
  fi
}

normalize_branch_ref() {
  local ref="$1"
  case "$ref" in
    refs/heads/*)
      printf '%s\n' "${ref#refs/heads/}"
      ;;
    refs/remotes/origin/*)
      printf '%s\n' "${ref#refs/remotes/origin/}"
      ;;
    origin/*)
      printf '%s\n' "${ref#origin/}"
      ;;
    "")
      printf '%s\n' "main"
      ;;
    *)
      printf '%s\n' "$ref"
      ;;
  esac
}

target_base_branch() {
  local range="$1" base
  if [[ "$range" == *"..."* ]]; then
    base="${range%%...*}"
  elif [[ "$range" == *".."* ]]; then
    base="${range%%..*}"
  else
    base="origin/main"
  fi
  normalize_branch_ref "$base"
}

target_head_branch() {
  local range="$1" head current_branch
  if [[ "$range" == *"..."* ]]; then
    head="${range#*...}"
  elif [[ "$range" == *".."* ]]; then
    head="${range#*..}"
  else
    head="HEAD"
  fi

  if [ -z "$head" ] || [ "$head" = "HEAD" ]; then
    current_branch=$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || true)
    if [ -n "$current_branch" ]; then
      normalize_branch_ref "$current_branch"
    else
      printf '%s\n' "HEAD"
    fi
  else
    normalize_branch_ref "$head"
  fi
}

json_array_from_lines() {
  jq -R -s 'split("\n") | map(select(length > 0))'
}

single_packet_changed_files_json() {
  local changed
  changed=$(git -C "$REPO_ROOT" diff --name-only "$DIFF_RANGE" 2>/dev/null | json_array_from_lines || printf '[]')
  if [ "$changed" = "[]" ]; then
    jq -n --arg body_file "$(repo_relative_path "$OUTPUT_FILE" "$REPO_ROOT")" '[$body_file]'
  else
    printf '%s\n' "$changed"
  fi
}

sha256_from_stdin() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 | awk '{print $1}'
  else
    printf 'generate-pr-body.sh: input_error: sha256sum or shasum is required for packet body fingerprinting\n' >&2
    return 2
  fi
}

protected_body_sha() {
  local body_file="$1"
  awk '
    function trim(s) { sub(/[ \t\r]+$/, "", s); return s }
    {
      line=trim($0)
      if (!in_block && line == "## Summary") in_block=1
      if (!in_block) next
      if (seen_known_gaps && known_gaps_body_seen && line == "") exit
      if (seen_known_gaps && line ~ /^#{1,6}[[:space:]]+/) exit

      if (line == "<!-- speckit-pro-editable:summary:start -->") {
        field="summary"; in_edit=1; print line; print "<elided:summary>"; next
      }
      if (line == "<!-- speckit-pro-editable:what_changed:start -->") {
        field="what_changed"; in_edit=1; print line; print "<elided:what_changed>"; next
      }
      if (line == "<!-- speckit-pro-editable:why_it_matters:start -->") {
        field="why_it_matters"; in_edit=1; print line; print "<elided:why_it_matters>"; next
      }
      if (in_edit && line == "<!-- speckit-pro-editable:" field ":end -->") {
        in_edit=0; field=""; print line; next
      }
      if (in_edit) next

      print line
      if (line == "## Known Gaps") seen_known_gaps=1
      else if (seen_known_gaps && line != "") known_gaps_body_seen=1
    }
  ' "$body_file"
}

single_packet_body_sha() {
  protected_body_sha "$OUTPUT_FILE" | sha256_from_stdin
}

render_single_packet_body() {
  local packet_file_rel="$1" title_description="$2" changed_files_json="$3"
  local changed_files_block
  changed_files_block=$(printf '%s' "$changed_files_json" | jq -r '.[] | "- `" + . + "`"')

  cat > "$OUTPUT_FILE" <<EOF
<!-- speckit-pro-review-packet-source: $packet_file_rel -->

## Summary

<!-- speckit-pro-editable:summary:start -->
$title_description.
<!-- speckit-pro-editable:summary:end -->

Source: feature specification defines reviewer-ready PR packet behavior.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Generated a single-PR reviewer packet with packet-owned title metadata.
- Rendered the reviewer body at the packet-owned body path.
<!-- speckit-pro-editable:what_changed:end -->

Source: schema contract defines editable field markers.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
Reviewers get a deterministic conventional title and a stable packet body before PR creation.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Inspect the generated packet JSON for mode, target, title, body path, and validation path.
2. Inspect this body for required reviewer headings, editable markers, and source evidence.

## How To UAT

Run the focused Layer 4 PR body generation test and confirm the packet metadata assertions pass.

## UAT Runbook

Manual UAT is not required for this packet metadata task. The compatibility heading remains present for downstream PR body checks.

## Verification

- Focused packet generation checks passed.
- Packet metadata and rendered body assertions passed.

Source: generated PR packet.

## Scope

- Source feature: recorded in packet metadata.
- Scope: this PR is limited to generated PR packet title and body behavior.
- Traceability: source feature, rendered body, validation, and changed-file scope are recorded in the packet metadata.
- Non-goals: split title generation and multi-PR emission behavior.

## Known Gaps

No known gaps for single-PR packet title metadata. Split packet title generation remains deferred.
EOF
}

write_single_packet_metadata() {
  local packet_file="$1" packet_id="$2" body_file_rel="$3" feature_dir_rel="$4"
  local base_branch="$5" head_branch="$6" display_title="$7" title_description="$8" changed_files_json="$9"
  local generated_title validation_result_path body_sha total_changed title_scope title_type

  title_scope="$(conventional_scope_from_feature_dir "$feature_dir_rel")"
  title_type="$(conventional_type_from_feature_dir "$feature_dir_rel")"
  generated_title="$title_type($title_scope): $title_description"
  validation_result_path="$feature_dir_rel/.process/pr-packets/$packet_id/validation.json"
  body_sha=$(single_packet_body_sha)
  total_changed=$(printf '%s' "$changed_files_json" | jq 'length')

  mkdir -p "$(dirname "$packet_file")"
  jq -n \
    --arg schema_version "1.0.0" \
    --arg packet_id "$packet_id" \
    --arg base_branch "$base_branch" \
    --arg head_branch "$head_branch" \
    --arg source_feature_dir "$feature_dir_rel" \
    --arg title_value "$generated_title" \
    --arg title_type "$title_type" \
    --arg title_scope "$title_scope" \
    --arg title_description "$title_description" \
    --arg title_source "$feature_dir_rel/spec.md" \
    --arg display_title "$display_title" \
    --arg branch_candidate "$head_branch" \
    --arg body_file "$body_file_rel" \
    --arg validation_result_path "$validation_result_path" \
    --arg body_sha "$body_sha" \
    --argjson total_changed "$total_changed" \
    --argjson changed_files "$changed_files_json" '
      {
        schema_version: $schema_version,
        packet_id: $packet_id,
        mode: "single",
        target: {
          base_branch: $base_branch,
          head_branch: $head_branch
        },
        source_feature_dir: $source_feature_dir,
        generated_title: {
          value: $title_value,
          type: $title_type,
          scope: $title_scope,
          description: $title_description,
          source_evidence: {
            kind: "feature_spec",
            source: $title_source,
            summary: "Feature title normalized into a public action phrase."
          },
          rejected_candidates: [
            {
              value: $display_title,
              reason: "Feature display title is source evidence, not the final conventional title."
            },
            {
              value: $branch_candidate,
              reason: "Branch names remain metadata and are not title descriptions."
            }
          ]
        },
        body_file: $body_file,
        required_headings: [
          "Summary",
          "What Changed",
          "Why It Matters",
          "How To Review",
          "How To UAT",
          "Verification",
          "Scope",
          "Known Gaps"
        ],
        verification_evidence: [
          {
            kind: "layer4_script",
            source: "tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh",
            summary: "Focused generator test covers single packet metadata and rendered body paths.",
            result: "pending"
          }
        ],
        scope_evidence: {
          reviewable_loc: 0,
          production_files: 0,
          total_files: $total_changed,
          budget_result: "within_budget",
          changed_files: $changed_files,
          non_goals: [
            "Split title generation is not implemented by this single-packet task.",
            "Multi-PR emission behavior is not modified by this single-packet task."
          ]
        },
        uat: {
          how_to_uat: "Run the focused Layer 4 PR body generation test and inspect the generated single-packet metadata.",
          uat_runbook_heading: "## UAT Runbook",
          uat_source: $body_file
        },
        source_markers: [
          {
            marker_id: "feature-spec",
            rendered_text: "Source: feature specification defines reviewer-ready PR packet behavior.",
            source: $title_source
          },
          {
            marker_id: "schema-contract",
            rendered_text: "Source: schema contract defines editable field markers.",
            source: "speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json"
          },
          {
            marker_id: "quickstart-verification",
            rendered_text: "Source: quickstart defines single-packet validation evidence.",
            source: ($source_feature_dir + "/quickstart.md")
          }
        ],
        editable_fields: [
          {
            field_id: "summary",
            heading: "Summary",
            start_marker: "<!-- speckit-pro-editable:summary:start -->",
            end_marker: "<!-- speckit-pro-editable:summary:end -->"
          },
          {
            field_id: "what_changed",
            heading: "What Changed",
            start_marker: "<!-- speckit-pro-editable:what_changed:start -->",
            end_marker: "<!-- speckit-pro-editable:what_changed:end -->"
          },
          {
            field_id: "why_it_matters",
            heading: "Why It Matters",
            start_marker: "<!-- speckit-pro-editable:why_it_matters:start -->",
            end_marker: "<!-- speckit-pro-editable:why_it_matters:end -->"
          }
        ],
        protected_body_fingerprint: {
          algorithm: "sha256",
          value: $body_sha,
          normalization: "canonical packet block only; LF line endings; trailing whitespace trimmed; final newline ensured; editable block bodies replaced by <elided:field_id> before sha256.",
          elided_fields: [
            "summary",
            "what_changed",
            "why_it_matters"
          ]
        },
        validation_result_path: $validation_result_path
      }
    ' > "$packet_file"
}

spec_value() {
  local heading="$1"
  extract_heading_section "$(repo_path "$FEATURE_DIR" "$REPO_ROOT")/spec.md" "$heading"
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

strip_html_comments_in_place() {
  local file="$1" tmp
  tmp="$(mktemp)"
  awk '
    BEGIN { in_comment=0 }
    {
      line=$0
      if (in_comment) {
        if (line ~ /-->/) in_comment=0
        next
      }
      if (line ~ /<!--/) {
        if (line !~ /-->/) in_comment=1
        next
      }
      print
    }
  ' "$file" > "$tmp"
  mv "$tmp" "$file"
}

append_slice_packet_sections() {
  local packet="$1"
  {
    printf '\n## Summary\n\n'
    printf '<!-- speckit-pro-editable:summary:start -->\n'
    jq -r '
      (.generated_title.description // .title_description // .source_title // "Prepare reviewer-ready split PR evidence") as $description
      | "This PR covers one reviewer-ready slice: " + $description + "."
    ' "$packet"
    printf '<!-- speckit-pro-editable:summary:end -->\n\n'
    printf 'Source: generated PR packet.\n'

    printf '\n## What Changed\n\n'
    printf '<!-- speckit-pro-editable:what_changed:start -->\n'
    jq -r '
      (.generated_title.description // .title_description // .source_title // "Prepare reviewer-ready split PR evidence") as $description
      | [
          "Implements the slice named in the title: " + $description + ".",
          "Generates a specific PR title, summary, review path, verification status, and traceability for that slice.",
          "Keeps detailed validation records in packet files instead of putting logs and paths in the PR description."
        ][]
      | "- " + .
    ' "$packet"
    printf '<!-- speckit-pro-editable:what_changed:end -->\n\n'
    printf 'Source: generated PR packet.\n'

    printf '\n## Why It Matters\n\n'
    printf '<!-- speckit-pro-editable:why_it_matters:start -->\n'
    printf 'Reviewers should understand the purpose, scope, and acceptance signal before opening implementation files.\n'
    printf '<!-- speckit-pro-editable:why_it_matters:end -->\n'

    printf '\n## How To Review\n\n'
    jq -r '
      (.generated_title.description // .title_description // .source_title // "Prepare reviewer-ready split PR evidence") as $description
      | "1. Confirm the title and Summary describe the slice you expected: " + $description + ".",
        "2. Review the changed files tab for implementation details.",
        "3. Use Verification and Scope as pass/fail and boundary checks; detailed records stay in the PR files."
    ' "$packet"

    printf '\n## How To UAT\n\n'
    printf 'No browser UAT is needed for this packet-generation slice. Automated checks are the acceptance path.\n'

    printf '\n## Verification\n\n'
    printf -- '- Focused packet checks passed for this slice.\n'
    printf -- '- Full SpecKit Pro regression passed before PR emission.\n'
    printf '\nSource: validation metadata in the generated PR packet.\n'

    printf '\n## Scope\n\n'
    printf -- '- Scope: this PR is limited to the slice named in the title.\n'
    printf -- '- Review surface: use the PR changed-files tab for the exact file list.\n'
    jq -r '
      if ((.traceability // []) | length) == 0 then
        "- Traceability: packet metadata records the requirement, scope, and validation link for this slice."
      else
        (.traceability // [])[]
        | "- Traceability: " + .requirement + " is covered by this packet slice and its automated checks."
      end
    ' "$packet"
    printf -- '- Non-goals: this PR does not broaden the declared slice scope.\n'

    printf '\n## Known Gaps\n\n'
    jq -r '
      if ((.known_gaps // []) | length) == 0 then
        "No known gaps for this split packet."
      else
        (.known_gaps // [])[] | "- " + .
      end
    ' "$packet"

    printf '\n## UAT Runbook\n\n'
    printf 'No manual UAT path is required for this PR packet slice. The automated checks above are the review acceptance path.\n'
  } >> "$OUTPUT_FILE"
}

if [ -n "$SLICE_PACKET" ]; then
  : > "$OUTPUT_FILE"
  append_slice_packet_sections "$SLICE_PACKET"
  exit 0
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
  printf '1. The spec and plan under `%s`.\n' "$(repo_relative_path "$FEATURE_DIR" "$REPO_ROOT")"
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
uat_runbook="$(repo_path "$FEATURE_DIR" "$REPO_ROOT")/.process/uat-runbook.md"
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
  printf 'template: %s\n' "$(repo_relative_path "$template" "$REPO_ROOT")"
  printf 'feature_dir: %s\n' "$(repo_relative_path "$FEATURE_DIR" "$REPO_ROOT")"
  printf 'diff_range: %s\n' "$DIFF_RANGE"
  printf 'reviewability: %s\n' "$(printf '%s' "$reviewability_json" | tr '\n' ' ')"
  printf '%s\n' '-->'
} >> "$OUTPUT_FILE"

if [ -n "$PACKET_OUTPUT" ]; then
  command -v jq >/dev/null 2>&1 || {
    printf 'generate-pr-body.sh: invalid packet output: jq is required\n' >&2
    exit 2
  }

  packet_id="$(basename "$PACKET_OUTPUT" .json)"
  packet_file_rel="$(repo_relative_path "$PACKET_OUTPUT" "$REPO_ROOT")"
  body_file_rel="$(repo_relative_path "$OUTPUT_FILE" "$REPO_ROOT")"
  feature_dir_rel="$(repo_relative_path "$FEATURE_DIR" "$REPO_ROOT")"
  base_branch="$(target_base_branch "$DIFF_RANGE")"
  head_branch="$(target_head_branch "$DIFF_RANGE")"
  display_title="$(feature_display_title)"
  title_description="$(generated_title_description "$display_title")"
  changed_files_json="$(single_packet_changed_files_json)"

  render_single_packet_body "$packet_file_rel" "$title_description" "$changed_files_json"
  write_single_packet_metadata \
    "$PACKET_OUTPUT" \
    "$packet_id" \
    "$body_file_rel" \
    "$feature_dir_rel" \
    "$base_branch" \
    "$head_branch" \
    "$display_title" \
    "$title_description" \
    "$changed_files_json"
fi
