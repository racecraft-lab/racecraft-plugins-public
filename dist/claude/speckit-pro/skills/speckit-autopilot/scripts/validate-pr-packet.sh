#!/usr/bin/env bash
# validate-pr-packet.sh - Validate rendered PR packet metadata before PR creation.

set -euo pipefail

SCRIPT_NAME="validate-pr-packet.sh"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

failures_file="$tmp_dir/failures.jsonl"
remediation_file="$tmp_dir/remediation.jsonl"
: > "$failures_file"
: > "$remediation_file"

json_array_from_jsonl() {
  if [ -s "$1" ]; then
    jq -s . "$1"
  else
    printf '[]\n'
  fi
}

json_quote() {
  jq -Rn --arg value "$1" '$value'
}

persist_text_atomic() {
  local target="$1" content="$2" dir tmp
  dir="$(dirname "$target")"
  mkdir -p "$dir" || return 1
  if [ -e "$target" ] && [ ! -f "$target" ]; then
    return 1
  fi
  tmp="$(mktemp "$dir/.tmp.$(basename "$target").XXXXXX")" || return 1
  printf '%s\n' "$content" > "$tmp" || {
    rm -f "$tmp"
    return 1
  }
  mv -f "$tmp" "$target" || {
    rm -f "$tmp"
    return 1
  }
}

add_failure() {
  local rule_id="$1" affected_field="$2" message="$3" remediation="$4"
  jq -cn \
    --arg rule "$rule_id" \
    --arg field "$affected_field" \
    --arg message "$message" \
    '{
      rule: $rule,
      field: $field,
      message: $message
    }' >> "$failures_file"
  printf '[%s] %s\n' "$rule_id" "$remediation" | jq -R . >> "$remediation_file"
}

jq_get() {
  local packet="$1" expr="$2"
  jq -r "$expr // \"\"" "$packet" 2>/dev/null || true
}

packet_id_from_path() {
  local path="$1" base
  base="$(basename "$path")"
  printf '%s\n' "${base%.json}"
}

derive_validation_result_path() {
  local packet="$1" packet_id="$2" configured source_feature_dir derived
  configured="$(jq_get "$packet" '.validation_result_path')"
  source_feature_dir="$(jq_get "$packet" '.source_feature_dir')"
  if [[ "$source_feature_dir" == specs/* ]] && [ -n "$packet_id" ]; then
    derived="$source_feature_dir/.process/pr-packets/$packet_id/validation.json"
    if [ -n "$configured" ] && [ "$configured" != "$derived" ]; then
      printf '%s\n' "no-path"
      return
    fi
    printf '%s\n' "$derived"
    return
  fi

  printf '%s\n' "no-path"
}

workflow_id_from_feature_dir() {
  local feature_dir="$1" feature_slug
  feature_slug="${feature_dir#specs/}"
  if [[ "$feature_slug" =~ ^([A-Za-z]+)-([0-9]+) ]]; then
    printf '%s-%s\n' "${BASH_REMATCH[1]^^}" "${BASH_REMATCH[2]}"
  elif [[ "$feature_slug" =~ ^([0-9]+) ]]; then
    printf '%s\n' "${BASH_REMATCH[1]}"
  else
    printf '%s\n' "$feature_slug"
  fi
}

feature_dir_from_result_path() {
  local result_path="$1"
  if [[ "$result_path" =~ ^(specs/[^/]+)/\.process/pr-packets/[^/]+/validation\.json$ ]]; then
    printf '%s\n' "${BASH_REMATCH[1]}"
  fi
}

upsert_workflow_event() {
  local packet="$1" packet_id="$2" validation_result_path="$3"
  local feature_dir workflow_id workflow_path rules marker event current filtered next
  feature_dir="$(jq_get "$packet" '.source_feature_dir')"
  if [ -z "$feature_dir" ]; then
    feature_dir="$(feature_dir_from_result_path "$validation_result_path")"
  fi
  [ -n "$feature_dir" ] || return 0

  workflow_id="$(workflow_id_from_feature_dir "$feature_dir")"
  workflow_path="$REPO_ROOT/docs/ai/specs/.process/${workflow_id}-workflow.md"
  [ -f "$workflow_path" ] || return 0

  rules="$(jq -r -s 'map(.rule_id) | unique | join(",")' "$failures_file")"
  marker="<!-- speckit-pro-pr-packet-validation:event-id=$packet_id -->"
  event="- $marker Blocked PR packet validation for \`$packet_id\`; result \`$validation_result_path\`; rules: \`${rules:-unknown}\`."
  current="$(cat "$workflow_path" 2>/dev/null || true)"
  filtered="$(printf '%s\n' "$current" | awk -v marker="$marker" 'index($0, marker) == 0 { print }')"

  if [[ "$filtered" == *"### PR packet validation events"* ]]; then
    next="${filtered}"$'\n'"${event}"
  else
    next="${filtered}"$'\n\n'"### PR packet validation events"$'\n'"${event}"
  fi
  persist_text_atomic "$workflow_path" "$next" >/dev/null 2>&1 || true
}

emit_result() {
  local status="$1"
  local error_class="$2"
  local exit_code="$3"
  local packet_id="$4"
  local mode="$5"
  local title_value="$6"
  local body_file="$7"
  local validation_result_path="$8"
  local pr_blocked="$9"
  local stderr_line="${10:-}"
  local target_base="${11:-}"
  local target_head="${12:-}"

  local failures_json remediation_json output_file
  failures_json="$(json_array_from_jsonl "$failures_file")"
  remediation_json="$(json_array_from_jsonl "$remediation_file")"
  output_file="$tmp_dir/result.json"

  jq -n \
    --arg schema_version "1.0.0" \
    --arg packet_id "$packet_id" \
    --arg mode "$mode" \
    --arg status "$status" \
    --arg error_class "$error_class" \
    --argjson exit_code "$exit_code" \
    --arg stderr_line "$stderr_line" \
    --arg target_base "$target_base" \
    --arg target_head "$target_head" \
    --arg title_value "$title_value" \
    --arg body_file "$body_file" \
    --arg timestamp "1970-01-01T00:00:00Z" \
    --argjson pr_blocked "$pr_blocked" \
    --argjson failures "$failures_json" \
    --argjson remediation_evidence "$remediation_json" \
    '{
      schema_version: $schema_version,
      error_class: $error_class,
      exit_code: $exit_code,
      stderr_line: $stderr_line,
      packet_id: $packet_id,
      mode: (if $mode == "" then null else $mode end),
      target: (
        if $target_base == "" and $target_head == "" then
          null
        else
          {base_branch: $target_base, head_branch: $target_head}
        end
      ),
      status: $status,
      title_value: (if $title_value == "" then null else $title_value end),
      body_file: (if $body_file == "" then null else $body_file end),
      rule_outcomes: (
        if ($failures | length) > 0 then
          $failures | map({rule: .rule, status: "failed", evidence: .field})
        else
          [{rule: "packet.validation", status: "passed", evidence: "no failures"}]
        end
      ),
      pr_blocked: $pr_blocked,
      failures: $failures,
      remediation_evidence: $remediation_evidence,
      timestamp: $timestamp
    }' > "$output_file"

  if [ -n "$validation_result_path" ] && [ "$validation_result_path" != "no-path" ]; then
    mkdir -p "$(dirname "$REPO_ROOT/$validation_result_path")"
    cp "$output_file" "$REPO_ROOT/$validation_result_path"
  fi

  cat "$output_file"
}

emit_input_error() {
  local packet_id="$1" message="$2"
  local stderr_line
  add_failure "input.error" "packet" "$message" "Provide a readable JSON PR packet with a feature-local validation_result_path."
  stderr_line="$SCRIPT_NAME: input_error: $packet_id: input.error: no-path"
  emit_result "failed" "input_error" 2 "$packet_id" "" "" "" "no-path" true "$stderr_line"
  printf '%s\n' "$stderr_line" >&2
  exit 2
}

require_nonempty() {
  local value="$1" field="$2"
  if [ -z "$value" ]; then
    add_failure "packet.required" "$field" "Required packet field is empty: $field" "Populate $field in the generated packet before validation."
  fi
}

require_jq_true() {
  local packet="$1" expr="$2" rule_id="$3" field="$4" message="$5" remediation="$6"
  if ! jq -e "$expr" "$packet" >/dev/null 2>&1; then
    add_failure "$rule_id" "$field" "$message" "$remediation"
  fi
}

contains_banned_text() {
  local value="$1"
  [[ "$value" =~ (ELI5|Plain-English[[:space:]]Summary|TODO|refs/heads/|refs/remotes/|refs/tags/|PRSG-[0-9]+|SPEC-[0-9A-Za-z_-]+|FR-[0-9A-Za-z_-]+|SC-[0-9A-Za-z_-]+|L[0-9]+|\{\{|\}\}|\$\{|<!--[[:space:]]*[^>]*-->|Example:) ]]
}

contains_generic_title_text() {
  local value="$1"
  printf '%s\n' "$value" | grep -Eiq '(^|: )[[:space:]]*(Foundation|User[[:space:]]+Story|US[0-9]+|us[0-9]+|full-spec|slice)([[:space:]:-]|$)|\(Priority:|(^|[^A-Za-z])MVP([^A-Za-z]|$)|foundation[[:space:]]+slice|Describe reviewer-visible change'
}

protected_body_sha() {
  local path="$1"
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
  ' "$path" | sha256_from_stdin
}

sha256_from_stdin() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 | awk '{print $1}'
  else
    printf '%s\n' "sha256sum or shasum is required for packet body fingerprinting" >&2
    return 2
  fi
}

validate_required_headings() {
  local packet="$1"
  require_jq_true "$packet" '
    .required_headings == [
      "Summary",
      "What Changed",
      "Why It Matters",
      "How To Review",
      "How To UAT",
      "Verification",
      "Scope",
      "Known Gaps"
    ]
  ' "body.required_headings" "required_headings" \
    "Packet required_headings must match the canonical reviewer section order." \
    "Regenerate the PR packet with all canonical reviewer headings in stable order."
}

validate_editable_fields() {
  local packet="$1"
  require_jq_true "$packet" '
    .editable_fields | length == 3
    and .[0].field_id == "summary"
    and .[0].start_marker == "<!-- speckit-pro-editable:summary:start -->"
    and .[0].end_marker == "<!-- speckit-pro-editable:summary:end -->"
    and .[1].field_id == "what_changed"
    and .[1].start_marker == "<!-- speckit-pro-editable:what_changed:start -->"
    and .[1].end_marker == "<!-- speckit-pro-editable:what_changed:end -->"
    and .[2].field_id == "why_it_matters"
    and .[2].start_marker == "<!-- speckit-pro-editable:why_it_matters:start -->"
    and .[2].end_marker == "<!-- speckit-pro-editable:why_it_matters:end -->"
  ' "body.editable_fields" "editable_fields" \
    "Editable fields must be exactly summary, what_changed, and why_it_matters with full-line marker pairs." \
    "Regenerate editable field metadata from the canonical packet renderer."
}

write_visible_markdown() {
  local input="$1" output="$2"
  awk '
    BEGIN { in_fence=0; in_comment=0 }
    {
      line=$0
      trimmed=line
      sub(/^[ \t]+/, "", trimmed)
      sub(/[ \t\r]+$/, "", trimmed)

      if (in_comment) {
        if (trimmed ~ /-->/) in_comment=0
        next
      }
      if (!in_fence && trimmed ~ /^<!--/) {
        if (trimmed !~ /-->/) in_comment=1
        next
      }
      if (trimmed ~ /^(```|~~~)/) {
        in_fence = !in_fence
        next
      }
      if (in_fence) next
      print line
    }
  ' "$input" > "$output"
}

validate_body_file() {
  local body_file="$1" packet="$2" body_abs="$REPO_ROOT/$body_file"
  if [ -z "$body_file" ]; then
    add_failure "body.path" "body_file" "body_file is required." "Write a rendered PR body and record its repo-relative path."
    return
  fi
  case "$body_file" in
    /*|../*|*/../*|*/..|..)
      add_failure "body.path" "body_file" \
        "Rendered body file path must be repo-relative and stay inside the repository: $body_file" \
        "Regenerate the packet with a repo-relative body_file path that does not contain parent-directory traversal."
      return
      ;;
  esac
  if [ ! -f "$body_abs" ]; then
    add_failure "body.path" "body_file" "Rendered body file is missing: $body_file" "Regenerate the rendered PR body before validation."
    return
  fi

  local visible_body expected headings
  visible_body="$tmp_dir/body-visible.md"
  write_visible_markdown "$body_abs" "$visible_body"

  expected="Summary|What Changed|Why It Matters|How To Review|How To UAT|Verification|Scope|Known Gaps"
  headings="$(
    awk '
      /^## [^#]/ {
        heading=$0
        sub(/^##[[:space:]]+/, "", heading)
        sub(/[[:space:]]+$/, "", heading)
        if (heading == "Summary" || heading == "What Changed" || heading == "Why It Matters" ||
            heading == "How To Review" || heading == "How To UAT" || heading == "Verification" ||
            heading == "Scope" || heading == "Known Gaps") {
          if (seen++) printf "|"
          printf "%s", heading
        }
      }
    ' "$visible_body"
  )"
  if [ "$headings" != "$expected" ]; then
    add_failure "body.heading_order" "body_file" \
      "Rendered body headings are missing, duplicated, or out of canonical order." \
      "Render Summary, What Changed, Why It Matters, How To Review, How To UAT, Verification, Scope, and Known Gaps in order."
  fi

  if grep -Eq 'Plain-English[[:space:]]+Summary|TODO|\{\{|\}\}|\$\{|<!--[[:space:]]*TODO|Example:' "$body_abs"; then
    add_failure "body.banned_or_placeholder" "body_file" \
      "Rendered body contains stale placeholder, hidden TODO, unexpanded variable, or example text." \
      "Regenerate the body from finalized packet evidence before PR creation."
  fi

  if grep -Eiq 'Adds reviewer-ready split PR packet evidence for|Prepared `[^`]+` for review against|Slice PR body placeholder|^slice_id:|^slice_packet:' "$visible_body"; then
    add_failure "body.generic_packet_prose" "body_file" \
      "Rendered body describes packet mechanics instead of the reviewer-visible change." \
      "Rewrite Summary, What Changed, and Why It Matters in strict plain English that names the actual change and preserves technical evidence below."
  fi

  local field start_count end_count start_line end_line
  for field in summary what_changed why_it_matters; do
    start_count="$(grep -Fxc "<!-- speckit-pro-editable:$field:start -->" "$body_abs" || true)"
    end_count="$(grep -Fxc "<!-- speckit-pro-editable:$field:end -->" "$body_abs" || true)"
    start_line="$(grep -Fn "<!-- speckit-pro-editable:$field:start -->" "$body_abs" | head -1 | cut -d: -f1 || true)"
    end_line="$(grep -Fn "<!-- speckit-pro-editable:$field:end -->" "$body_abs" | head -1 | cut -d: -f1 || true)"
    if [ "$start_count" != "1" ] || [ "$end_count" != "1" ] || [ -z "$start_line" ] || [ -z "$end_line" ] || [ "$start_line" -ge "$end_line" ]; then
      add_failure "body.editable_boundaries" "body_file" \
        "Editable field markers are missing, duplicated, malformed, or out of order." \
        "Regenerate exact full-line editable marker pairs for summary, what_changed, and why_it_matters."
      break
    fi
  done

  if awk '
    BEGIN { legacy=0; bad=0 }
    {
      line=$0
      sub(/[ \t\r]+$/, "", line)
      trimmed=line
      sub(/^[ \t]+/, "", trimmed)
      if (legacy) {
        if (trimmed == "-->") legacy=0
        next
      }
      if (trimmed ~ /^<!--[[:space:]]*speckit-pro-review-packet-source/) {
        if (trimmed !~ /-->$/) legacy=1
        next
      }
      if (line ~ /^<!-- speckit-pro-editable:(summary|what_changed|why_it_matters):(start|end) -->$/) next
      if (line ~ /<!--/) { bad=1; exit }
    }
    END { if (legacy) bad=1; exit bad ? 0 : 1 }
  ' "$body_abs"; then
    add_failure "body.unknown_comment" "body_file" \
      "Rendered body contains an unknown or stale HTML comment outside allowed packet markers." \
      "Remove template comments and keep only editable-boundary comments plus the legacy packet-source marker."
  fi

  if ! grep -Fq "Traceability:" "$visible_body"; then
    add_failure "body.traceability" "body_file" \
      "Rendered body is missing traceability evidence." \
      "Render a Traceability line that maps source evidence, verification, and scope to the packet."
  fi

  for marker in \
    "<!-- speckit-pro-editable:summary:start -->" \
    "<!-- speckit-pro-editable:summary:end -->" \
    "<!-- speckit-pro-editable:what_changed:start -->" \
    "<!-- speckit-pro-editable:what_changed:end -->" \
    "<!-- speckit-pro-editable:why_it_matters:start -->" \
    "<!-- speckit-pro-editable:why_it_matters:end -->"; do
    if ! grep -Fq "$marker" "$body_abs"; then
      add_failure "body.required_content" "body_file" \
        "Rendered body is missing required content: $marker" \
        "Regenerate the body with canonical sections, editable markers, UAT compatibility, and source evidence."
    fi
  done

  for marker in "## UAT Runbook" "Source:"; do
    if ! grep -Fq "$marker" "$visible_body"; then
      add_failure "body.required_content" "body_file" \
        "Rendered body is missing required content: $marker" \
        "Regenerate the body with canonical sections, editable markers, UAT compatibility, and source evidence."
    fi
  done

  local expected_fingerprint actual_fingerprint
  expected_fingerprint="$(jq_get "$packet" '.protected_body_fingerprint.value')"
  actual_fingerprint="$(protected_body_sha "$body_abs")"
  if [ -n "$expected_fingerprint" ] && [ "$actual_fingerprint" != "$expected_fingerprint" ]; then
    add_failure "body.protected_fingerprint" "body_file" \
      "Protected body fingerprint changed outside sanctioned editable prose fields." \
      "Restore generated governance/evidence sections or regenerate the packet after intentional protected changes."
  fi
}

validate_public_text() {
  local packet="$1" title description source_summary uat_text evidence_summaries marker_text packet_id split_slice title_public_text
  title="$(jq_get "$packet" '.generated_title.value')"
  description="$(jq_get "$packet" '.generated_title.description')"
  source_summary="$(jq_get "$packet" '.generated_title.source_evidence.summary')"
  uat_text="$(jq_get "$packet" '.uat.how_to_uat')"
  evidence_summaries="$(jq -r '(.verification_evidence // [])[]?.summary // empty' "$packet" 2>/dev/null || true)"
  marker_text="$(jq -r '(.source_markers // [])[]?.rendered_text // empty' "$packet" 2>/dev/null || true)"
  packet_id="$(jq_get "$packet" '.packet_id')"
  split_slice="$(jq_get "$packet" '.split_slice.slice_id')"

  title_public_text="$title"
  case "$title_public_text" in
    *": "*) title_public_text="${title_public_text#*: }" ;;
  esac

  for item in "$title_public_text" "$description" "$source_summary" "$uat_text" "$evidence_summaries" "$marker_text"; do
    if contains_banned_text "$item"; then
      add_failure "text.banned_or_placeholder" "generated_title/body_evidence" \
        "Packet contains stale placeholder, internal code, hidden comment, example text, or banned label." \
        "Regenerate public-facing title and body evidence from finalized spec metadata."
      return
    fi
  done

  if contains_generic_title_text "$title" || contains_generic_title_text "$description"; then
    add_failure "title.public_description" "generated_title.description" \
      "Generated title description is a generic workflow label instead of a public action phrase." \
      "Regenerate the title as strict plain English that names the actual reviewer-visible change."
  fi

  if { [ -n "$packet_id" ] && { [ "$description" = "$packet_id" ] || [[ "$title" == *": $packet_id" ]]; }; } \
    || { [ -n "$split_slice" ] && { [ "$description" = "$split_slice" ] || [[ "$title" == *": $split_slice" ]]; }; }; then
    add_failure "title.slice_ref" "generated_title.description" \
      "Generated title description must not be only a packet id or slice id." \
      "Use the packet id or slice id only as metadata; the title must name the public change."
  fi

  local head_branch
  head_branch="$(jq_get "$packet" '.target.head_branch')"
  if [ -n "$head_branch" ] && { [[ "$title" == *"$head_branch"* ]] || [[ "$description" == *"$head_branch"* ]]; }; then
    add_failure "title.branch_ref" "generated_title" \
      "Generated title text must not contain the packet head branch." \
      "Use public-readable source-boundary prose for generated_title.description."
  fi
}

validate_packet() {
  local packet="$1"
  local packet_id mode title_value body_file validation_result_path
  packet_id="$(jq_get "$packet" '.packet_id')"
  if [ -z "$packet_id" ]; then
    packet_id="$(packet_id_from_path "$packet")"
  fi
  mode="$(jq_get "$packet" '.mode')"
  title_value="$(jq_get "$packet" '.generated_title.value')"
  body_file="$(jq_get "$packet" '.body_file')"
  validation_result_path="$(derive_validation_result_path "$packet" "$packet_id")"

  if [ "$validation_result_path" = "no-path" ]; then
    local stderr_line
    add_failure "input.no_feature_dir" "source_feature_dir" \
      "Unable to derive a feature-local validation result path." \
      "Provide source_feature_dir or validation_result_path under specs/<feature>/.process/pr-packets/<packet_id>/validation.json."
    stderr_line="$SCRIPT_NAME: input_error: $packet_id: input.no_feature_dir: no-path"
    emit_result "failed" "input_error" 2 "$packet_id" "$mode" "$title_value" "$body_file" "no-path" true "$stderr_line" "$(jq_get "$packet" '.target.base_branch')" "$(jq_get "$packet" '.target.head_branch')"
    printf '%s\n' "$stderr_line" >&2
    exit 2
  fi

  require_nonempty "$packet_id" "packet_id"
  require_nonempty "$mode" "mode"
  require_nonempty "$(jq_get "$packet" '.target.base_branch')" "target.base_branch"
  require_nonempty "$(jq_get "$packet" '.target.head_branch')" "target.head_branch"
  require_nonempty "$(jq_get "$packet" '.source_feature_dir')" "source_feature_dir"
  require_nonempty "$title_value" "generated_title.value"
  require_nonempty "$(jq_get "$packet" '.generated_title.type')" "generated_title.type"
  require_nonempty "$(jq_get "$packet" '.generated_title.scope')" "generated_title.scope"
  require_nonempty "$(jq_get "$packet" '.generated_title.description')" "generated_title.description"
  require_nonempty "$validation_result_path" "validation_result_path"

  require_jq_true "$packet" '.schema_version == "1.0.0"' "packet.schema_version" "schema_version" \
    "schema_version must be 1.0.0." "Regenerate the packet with the current PR packet schema."
  require_jq_true "$packet" '.mode == "single" or .mode == "split"' "packet.mode" "mode" \
    "mode must be single or split." "Set mode to single for one PR or split for slice PR emission."
  require_jq_true "$packet" '
    .generated_title.value
    | test("^[a-z]+\\([A-Za-z][A-Za-z0-9-]*\\): [A-Za-z]")
  ' "title.format" "generated_title.value" \
    "generated_title.value must be a conventional title with public-readable description." \
    "Regenerate the title from packet metadata using <type>(<scope>): <description>."
  require_jq_true "$packet" '.generated_title.type as $type | ["feat","fix","chore","docs","refactor","test"] | index($type)' \
    "title.type" "generated_title.type" \
    "generated_title.type must be an allowed conventional commit type." \
    "Use feat, fix, chore, docs, refactor, or test."
  require_jq_true "$packet" '(.generated_title.scope | test("^([a-z][a-z0-9-]*|[A-Z]+-[A-Z0-9][A-Z0-9-]*)$"))' \
    "title.scope" "generated_title.scope" \
    "generated_title.scope must be a public conventional commit scope or spec id." \
    "Use an explicit allowed packet metadata scope such as a spec id or speckit-pro."
  require_jq_true "$packet" '
    .generated_title as $title
    | $title.value
    | startswith($title.type + "(" + $title.scope + "): ")
  ' "title.metadata_consistency" "generated_title" \
    "generated_title.value must use the explicit generated_title.type and generated_title.scope metadata." \
    "Regenerate the title from metadata instead of accepting candidate-only type or scope overrides."
  require_jq_true "$packet" '(.verification_evidence // []) | length > 0' \
    "evidence.verification" "verification_evidence" \
    "Packet must include verification evidence." \
    "Record at least one deterministic verification command and result."
  require_jq_true "$packet" '(.scope_evidence.changed_files // []) | length > 0' \
    "evidence.scope.changed_files" "scope_evidence.changed_files" \
    "Packet must include changed-file scope evidence." \
    "Record changed files that define the packet review scope."
  require_jq_true "$packet" '(.scope_evidence.non_goals // []) | length > 0' \
    "evidence.scope.non_goals" "scope_evidence.non_goals" \
    "Packet must include non-goal scope evidence." \
    "Record non-goals or deferred work so reviewers know the boundary."
  require_jq_true "$packet" '.uat.uat_runbook_heading == "## UAT Runbook" and (.uat.uat_source | type == "string" and length > 0)' \
    "evidence.uat" "uat" \
    "Packet must preserve UAT Runbook compatibility and UAT source evidence." \
    "Regenerate UAT metadata with the literal ## UAT Runbook heading and a source path."
  require_jq_true "$packet" '(.source_markers // []) | length > 0' \
    "evidence.source_markers" "source_markers" \
    "Packet must include rendered source/provenance markers." \
    "Render source markers outside editable prose."
  require_jq_true "$packet" '
    .protected_body_fingerprint.algorithm == "sha256"
    and (.protected_body_fingerprint.value | test("^[0-9a-f]{64}$"))
  ' "body.fingerprint" "protected_body_fingerprint" \
    "Protected body fingerprint must use sha256 and a 64-character lowercase hex digest." \
    "Recompute the protected body fingerprint after rendering the canonical body."

  if [ "$mode" = "split" ]; then
    require_jq_true "$packet" '.split_slice.slice_id and .split_slice.source_boundary.section and .split_slice.source_packet' \
      "split.slice" "split_slice" \
      "Split packets must include split_slice identity and source boundary evidence." \
      "Populate split_slice from the slice packet used to render this PR packet."
  elif [ "$mode" = "single" ]; then
    require_jq_true "$packet" 'has("split_slice") | not' \
      "split.slice" "split_slice" \
      "Single packets must not include split_slice metadata." \
      "Remove split_slice from single-PR packets."
  fi

  validate_required_headings "$packet"
  validate_editable_fields "$packet"
  validate_body_file "$body_file" "$packet"
  validate_public_text "$packet"

  if [ -s "$failures_file" ]; then
    local stderr_line rules
    rules="$(jq -r -s 'map(.rule) | unique | join(",")' "$failures_file")"
    upsert_workflow_event "$packet" "$packet_id" "$validation_result_path"
    stderr_line="$SCRIPT_NAME: validation_failure: $packet_id: ${rules:-validation.failed}: $validation_result_path"
    emit_result "failed" "validation_failure" 1 "$packet_id" "$mode" "$title_value" "$body_file" "$validation_result_path" true "$stderr_line" "$(jq_get "$packet" '.target.base_branch')" "$(jq_get "$packet" '.target.head_branch')"
    printf '%s\n' "$stderr_line" >&2
    exit 1
  fi

  emit_result "passed" "none" 0 "$packet_id" "$mode" "$title_value" "$body_file" "$validation_result_path" false "" "$(jq_get "$packet" '.target.base_branch')" "$(jq_get "$packet" '.target.head_branch')"
  exit 0
}

PACKET_PATH="${1:-}"
if [ -z "$PACKET_PATH" ]; then
  emit_input_error "missing-packet-path" "missing packet path"
fi
if [ "$#" -ne 1 ]; then
  emit_input_error "$(packet_id_from_path "$PACKET_PATH")" "expected exactly one packet path"
fi
if [ ! -f "$PACKET_PATH" ] || [ ! -r "$PACKET_PATH" ]; then
  emit_input_error "$(packet_id_from_path "$PACKET_PATH")" "packet not found or unreadable: $PACKET_PATH"
fi
if ! jq empty "$PACKET_PATH" >/dev/null 2>&1; then
  emit_input_error "$(packet_id_from_path "$PACKET_PATH")" "packet JSON is malformed: $PACKET_PATH"
fi

validate_packet "$PACKET_PATH"
