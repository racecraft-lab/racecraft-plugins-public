#!/usr/bin/env bash
# test-generate-pr-body.sh — Unit tests for host-template PR body generation

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

TEST_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$TEST_DIR/../../.." && pwd)"
PLUGIN_ROOT="$REPO_ROOT/speckit-pro"
SCRIPT="$PLUGIN_ROOT/skills/speckit-autopilot/scripts/generate-pr-body.sh"
PRSG_012_FEATURE_REL="specs/prsg-012-reviewer-ready-pr-packet-contract"
PRSG_012_FEATURE_FIXTURE="$TEST_DIR/fixtures/prsg-012-feature/prsg-012-reviewer-ready-pr-packet-contract"
PR_PACKET_FIXTURE_REL="tests/speckit-pro/layer4-scripts/fixtures/pr-packet"
script_source="$(cat "$SCRIPT")"

section "script contract"

set_test "Generator does not fall back to an all-zero packet body fingerprint"
assert_not_contains "$script_source" "%064d"

assert_json_file_value() {
  local json_file="$1" field="$2" expected="$3" msg="${4:-}"
  local actual
  actual=$(
    python3 - "$json_file" "$field" 2>/dev/null <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)

value = data
for key in sys.argv[2].split("."):
    if isinstance(value, list):
        value = value[int(key)]
    else:
        value = value[key]

if isinstance(value, list):
    print("|".join(str(item) for item in value))
elif isinstance(value, bool):
    print("true" if value else "false")
else:
    print(value)
PY
  ) || {
    _fail "${msg:+$msg: }failed to parse JSON field '$field' from $json_file"
    return
  }

  if [ "$expected" = "$actual" ]; then
    _pass
  else
    _fail "${msg:+$msg: }field '$field': expected '$expected', got '$actual'"
  fi
}

assert_body_h2_sequence() {
  local body_file="$1" expected="$2" msg="${3:-body heading order}"
  if [ ! -f "$body_file" ]; then
    _fail "$msg: body file not found: $body_file"
    return
  fi

  if python3 - "$body_file" "$expected" <<'PY' >/dev/null 2>&1
import re
import sys

expected = sys.argv[2].split("|")
canonical = []
with open(sys.argv[1], encoding="utf-8") as handle:
    for line in handle:
        match = re.match(r"^## ([^#].*?)\s*$", line.rstrip("\n"))
        if match:
            heading = match.group(1).strip()
            if heading in expected:
                canonical.append(heading)

if canonical != expected:
    raise SystemExit(1)
PY
  then
    _pass
  else
    _fail "$msg"
  fi
}

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

repo="$FIXTURE_DIR/repo"
feature="$repo/specs/001-demo"
mkdir -p "$repo/.github" "$feature" "$feature/.process" "$repo/docs"
git -C "$repo" init >/dev/null
git -C "$repo" config user.email support@openai.com
git -C "$repo" config user.name Test
git -C "$repo" config commit.gpgsign false

cat > "$repo/.github/pull_request_template.md" <<'EOF'
# What
Host-required what section.

# Host Required
- [ ] Keep this checklist.
EOF

cat > "$feature/spec.md" <<'EOF'
# Feature Specification: Demo

## Summary
Implement a focused demo capability.

### Details
Keep nested details with the summary section.

## Non-goals
Do not add unrelated runtime behavior.
EOF

cat > "$feature/plan.md" <<'EOF'
# Plan
Primary surface: docs/process
EOF

printf 'base\n' > "$repo/docs/guide.md"
git -C "$repo" add .
git -C "$repo" commit -m init >/dev/null
printf 'change\n' >> "$repo/docs/guide.md"

section "host template detection"

set_test "Generator succeeds with host template"
output_file="$FIXTURE_DIR/pr-body.md"
result=0
(cd "$repo" && "$SCRIPT" "$repo" "$feature" "$output_file" HEAD) || result=$?
assert_eq "0" "$result" "exit code"

body=$(cat "$output_file")

set_test "Preserves host-required section"
assert_contains "$body" "# Host Required"

set_test "Appends Anything reviewers should know section"
assert_contains "$body" "# Anything reviewers should know"

set_test "Extracts section content from level-two spec headings"
assert_contains "$body" "Do not add unrelated runtime behavior."

set_test "Appends collapsed reviewer checklist & scope details block"
assert_contains "$body" "<summary>Reviewer checklist"

set_test "Does not emit governance as a top-level heading"
assert_not_contains "$body" "# Scope Budget"

set_test "Records host template source"
assert_contains "$body" "template: .github/pull_request_template.md"

section "fallback template"

rm "$repo/.github/pull_request_template.md"
set_test "Generator succeeds without host template"
fallback_file="$FIXTURE_DIR/pr-body-fallback.md"
result=0
(cd "$repo" && "$SCRIPT" "$repo" "$feature" "$fallback_file" HEAD) || result=$?
assert_eq "0" "$result" "exit code"

fallback_body=$(cat "$fallback_file")

set_test "Fallback body leads with the plain-English What changed heading"
assert_contains "$fallback_body" "# What changed"

set_test "Fallback body includes the collapsed reviewer checklist block"
assert_contains "$fallback_body" "<summary>Reviewer checklist"

set_test "Fallback body includes review packet source marker"
assert_contains "$fallback_body" "speckit-pro-review-packet-source"

section "generic future title support"

script_source=$(cat "$SCRIPT")

set_test "Generator does not special-case current PRSG-012 display title"
assert_not_contains "$script_source" "Reviewer-ready PR packet contract"

set_test "Slice renderer does not special-case current PRSG-012 slice title"
assert_not_contains "$script_source" "Add reviewer packet validation contract"

set_test "Slice renderer does not special-case PRSG-012 title-emission slice"
assert_not_contains "$script_source" "Generate packet-owned conventional PR titles"

section "slice packet option validation"

packet_fixture_root="$(cd "$(dirname "$0")/fixtures/multi-pr-emission/slice-packets" && pwd)"
valid_packet="$packet_fixture_root/valid-foundation.json"
invalid_packet="$packet_fixture_root/invalid-missing-slice-id.json"
malformed_packet="$packet_fixture_root/malformed.json"
missing_packet="$FIXTURE_DIR/missing-slice-packet.json"
protected_file="$FIXTURE_DIR/protected-pr-body.md"
printf 'keep existing body\n' > "$protected_file"

set_test "Valid --slice-packet renders slice PR body sections"
slice_body_file="$FIXTURE_DIR/pr-body-slice.md"
result=0
(cd "$repo" && "$SCRIPT" --slice-packet "$valid_packet" "$repo" "$feature" "$slice_body_file" HEAD) || result=$?
assert_eq "0" "$result" "exit code"

slice_body=$(cat "$slice_body_file")

set_test "Slice packet body opens with reviewer-readable summary"
assert_contains "$slice_body" "This PR covers one reviewer-ready slice:"

set_test "Slice packet body omits raw packet appendix headings"
assert_not_contains "$slice_body" "## Slice summary"

set_test "Slice packet body omits review-order appendix"
assert_not_contains "$slice_body" "## Review order"

set_test "Slice packet body avoids raw declared file paths"
assert_not_contains "$slice_body" "speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh"

set_test "Slice packet body avoids raw verification evidence paths"
assert_not_contains "$slice_body" "specs/prsg-009-multi-pr-emission/.process/emission/foundation/layer4.log"

set_test "Slice packet body keeps high-level traceability"
assert_contains "$slice_body" "Traceability:"

set_test "Slice packet body omits restack appendix"
assert_not_contains "$slice_body" "## Restack or rollback"

set_test "Slice packet body includes Known gaps"
assert_contains "$slice_body" "## Known Gaps"

set_test "Slice packet body omits full regression evidence path"
assert_not_contains "$slice_body" "specs/prsg-009-multi-pr-emission/.process/emission/default-verify.log"

set_test "Invalid --slice-packet exits 2"
packet_stderr="$FIXTURE_DIR/packet-invalid.stderr"
result=0
(cd "$repo" && "$SCRIPT" --slice-packet "$invalid_packet" "$repo" "$feature" "$protected_file" HEAD >/dev/null 2>"$packet_stderr") || result=$?
assert_eq "2" "$result" "exit code"

set_test "Invalid --slice-packet emits deterministic stderr prefix"
packet_error=$(cat "$packet_stderr")
assert_contains "$packet_error" "generate-pr-body.sh: invalid slice packet:"

set_test "Missing jq for --slice-packet exits 2 with deterministic stderr"
no_jq_bin="$FIXTURE_DIR/no-jq-bin"
mkdir -p "$no_jq_bin"
ln -s /usr/bin/dirname "$no_jq_bin/dirname"
missing_jq_stderr="$FIXTURE_DIR/packet-missing-jq.stderr"
result=0
(cd "$repo" && env PATH="$no_jq_bin" /bin/bash "$SCRIPT" --slice-packet "$valid_packet" "$repo" "$feature" "$FIXTURE_DIR/missing-jq-output.md" HEAD >/dev/null 2>"$missing_jq_stderr") || result=$?
assert_eq "2" "$result" "exit code"
missing_jq_error=$(cat "$missing_jq_stderr")
assert_contains "$missing_jq_error" "generate-pr-body.sh: invalid slice packet: jq is required"
assert_not_contains "$missing_jq_error" "command not found"

set_test "Invalid --slice-packet leaves existing output unchanged"
assert_eq "keep existing body" "$(cat "$protected_file")" "protected PR body"

set_test "Malformed --slice-packet exits 2"
malformed_stderr="$FIXTURE_DIR/packet-malformed.stderr"
result=0
(cd "$repo" && "$SCRIPT" --slice-packet "$malformed_packet" "$repo" "$feature" "$FIXTURE_DIR/malformed-output.md" HEAD >/dev/null 2>"$malformed_stderr") || result=$?
assert_eq "2" "$result" "exit code"

set_test "Missing --slice-packet exits 2"
missing_stderr="$FIXTURE_DIR/packet-missing.stderr"
result=0
(cd "$repo" && "$SCRIPT" --slice-packet "$missing_packet" "$repo" "$feature" "$FIXTURE_DIR/missing-output.md" HEAD >/dev/null 2>"$missing_stderr") || result=$?
assert_eq "2" "$result" "exit code"

set_test "Missing --slice-packet leaves target absent"
assert_file_not_exists "$FIXTURE_DIR/missing-output.md"

section "host headings at alternate levels"

cat > "$repo/.github/pull_request_template.md" <<'EOF'
## What
Host-required what section.
EOF

set_test "Generator recognizes existing level-two host heading"
level_two_file="$FIXTURE_DIR/pr-body-level-two.md"
result=0
(cd "$repo" && "$SCRIPT" "$repo" "$feature" "$level_two_file" HEAD) || result=$?
assert_eq "0" "$result" "exit code"

level_two_body=$(cat "$level_two_file")

set_test "Does not duplicate host What section"
what_count=$(grep -Ec '^#{1,6}[[:space:]]+What$' "$level_two_file")
assert_eq "1" "$what_count" "What heading count"

section "UAT Runbook embed (FR-013)"

# (a) runbook present and under 50,000 chars → full content embedded via cat,
#     blank lines preserved (Decision 2).
cat > "$feature/.process/uat-runbook.md" <<'EOF'
# UAT Runbook: 001-demo

| Field | Value |
|-------|-------|
| Spec | 001-demo |

## Per-Story Acceptance Tests

- [ ] Walk story one end to end.

UAT_SENTINEL_UNDER_THRESHOLD
EOF

set_test "Generator succeeds with a small runbook present"
uat_small_file="$FIXTURE_DIR/pr-body-uat-small.md"
result=0
(cd "$repo" && "$SCRIPT" "$repo" "$feature" "$uat_small_file" HEAD) || result=$?
assert_eq "0" "$result" "exit code"

uat_small_body=$(cat "$uat_small_file")

set_test "Embeds the literal H2 UAT Runbook heading"
uat_heading_count=$(grep -Ec '^## UAT Runbook$' "$uat_small_file" || true)
assert_eq "1" "$uat_heading_count" "## UAT Runbook heading count"

set_test "Embeds full runbook content (cat, not truncated)"
assert_contains "$uat_small_body" "UAT_SENTINEL_UNDER_THRESHOLD"

set_test "Preserves blank lines from the runbook (Header table renders)"
assert_contains "$uat_small_body" "| Spec | 001-demo |"

set_test "Small-runbook embed omits the Full runbook link"
assert_not_contains "$uat_small_body" "[Full runbook](./.process/uat-runbook.md)"

# (b) runbook at/over 50,000 chars → head -60 + relative link.
{
  printf '# UAT Runbook: 001-demo\n\n'
  printf 'UAT_SENTINEL_FIRST_LINE\n'
  # pad well past 60 lines and well past 50,000 chars
  for i in $(seq 1 2000); do
    printf 'Padding line %04d %s\n' "$i" "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  done
  printf 'UAT_SENTINEL_LAST_LINE_PAST_HEAD60\n'
} > "$feature/.process/uat-runbook.md"

set_test "Generator succeeds with a large runbook present"
uat_big_file="$FIXTURE_DIR/pr-body-uat-big.md"
result=0
(cd "$repo" && "$SCRIPT" "$repo" "$feature" "$uat_big_file" HEAD) || result=$?
assert_eq "0" "$result" "exit code"

uat_big_body=$(cat "$uat_big_file")

set_test "Large-runbook embed includes the opening excerpt"
assert_contains "$uat_big_body" "UAT_SENTINEL_FIRST_LINE"

set_test "Large-runbook embed truncates at head -60 (last line absent)"
assert_not_contains "$uat_big_body" "UAT_SENTINEL_LAST_LINE_PAST_HEAD60"

set_test "Large-runbook embed appends the Full runbook link"
assert_contains "$uat_big_body" "[Full runbook](./.process/uat-runbook.md)"

# (c) runbook absent → heading + one-line stub (fail-open).
rm -f "$feature/.process/uat-runbook.md"

set_test "Generator succeeds with no runbook present (fail-open)"
uat_absent_file="$FIXTURE_DIR/pr-body-uat-absent.md"
result=0
(cd "$repo" && "$SCRIPT" "$repo" "$feature" "$uat_absent_file" HEAD) || result=$?
assert_eq "0" "$result" "exit code"

uat_absent_body=$(cat "$uat_absent_file")

set_test "Absent runbook still emits the H2 UAT Runbook heading"
assert_contains "$uat_absent_body" "## UAT Runbook"

set_test "Absent runbook emits a stub note instead of content"
assert_contains "$uat_absent_body" "uat-runbook.md"

section "PRSG-012 generated packet metadata"

packet_repo="$FIXTURE_DIR/prsg-012-repo"
packet_feature="$packet_repo/$PRSG_012_FEATURE_REL"
packet_output_rel="$PR_PACKET_FIXTURE_REL/valid-single.json"
body_output_rel="$PR_PACKET_FIXTURE_REL/bodies/valid-single.md"
packet_output="$packet_repo/$packet_output_rel"
body_output="$packet_repo/$body_output_rel"
required_headings="Summary|What Changed|Why It Matters|How To Review|How To UAT|Verification|Scope|Known Gaps"

mkdir -p "$packet_repo/specs" "$packet_repo/docs" "$(dirname "$packet_output")" "$(dirname "$body_output")"
cp -R "$PRSG_012_FEATURE_FIXTURE" "$packet_repo/specs/"

git -C "$packet_repo" init >/dev/null
git -C "$packet_repo" checkout -b main >/dev/null 2>&1
git -C "$packet_repo" config user.email support@openai.com
git -C "$packet_repo" config user.name Test
git -C "$packet_repo" config commit.gpgsign false
printf 'base\n' > "$packet_repo/docs/prsg-012.md"
git -C "$packet_repo" add .
git -C "$packet_repo" commit -m init >/dev/null
git -C "$packet_repo" checkout -b prsg-012-reviewer-ready-pr-packet-contract >/dev/null 2>&1
printf 'change\n' >> "$packet_repo/docs/prsg-012.md"

set_test "Generator writes PRSG-012 packet metadata with --packet-output"
result=0
(cd "$packet_repo" && "$SCRIPT" --packet-output "$packet_output" "$packet_repo" "$packet_feature" "$body_output" main...HEAD) || result=$?
assert_eq "0" "$result" "exit code"

set_test "Generated packet metadata file exists"
assert_file_exists "$packet_output"

set_test "Generated rendered body file exists"
assert_file_exists "$body_output"

set_test "Generated packet records single mode"
assert_json_file_value "$packet_output" "mode" "single"

set_test "Generated packet records source feature dir"
assert_json_file_value "$packet_output" "source_feature_dir" "$PRSG_012_FEATURE_REL"

set_test "Generated packet records target base branch"
assert_json_file_value "$packet_output" "target.base_branch" "main"

set_test "Generated packet records target head branch"
assert_json_file_value "$packet_output" "target.head_branch" "prsg-012-reviewer-ready-pr-packet-contract"

set_test "Generated packet owns a reviewer-ready title"
assert_json_file_value "$packet_output" "generated_title.value" "feat(PRSG-012): Add reviewer-ready PR packet contract"

set_test "Generated packet records title type"
assert_json_file_value "$packet_output" "generated_title.type" "feat"

set_test "Generated packet records title scope"
assert_json_file_value "$packet_output" "generated_title.scope" "PRSG-012"

set_test "Generated packet records title source evidence"
assert_json_file_value "$packet_output" "generated_title.source_evidence.kind" "feature_spec"

set_test "Generated packet records repo-relative rendered body path"
assert_json_file_value "$packet_output" "body_file" "$body_output_rel"

set_test "Generated packet records validation result path"
assert_json_file_value "$packet_output" "validation_result_path" "$PRSG_012_FEATURE_REL/.process/pr-packets/valid-single/validation.json"

set_test "Generated packet records canonical reviewer headings"
assert_json_file_value "$packet_output" "required_headings" "$required_headings"

set_test "Generated packet records editable summary field"
assert_json_file_value "$packet_output" "editable_fields.0.field_id" "summary"

set_test "Generated packet records editable what_changed field"
assert_json_file_value "$packet_output" "editable_fields.1.field_id" "what_changed"

set_test "Generated packet records editable why_it_matters field"
assert_json_file_value "$packet_output" "editable_fields.2.field_id" "why_it_matters"

set_test "Generated packet records editable summary start marker"
assert_json_file_value "$packet_output" "editable_fields.0.start_marker" "<!-- speckit-pro-editable:summary:start -->"

set_test "Rendered body uses canonical reviewer heading order"
assert_body_h2_sequence "$body_output" "$required_headings"

generated_body=""
if [ -f "$body_output" ]; then
  generated_body=$(cat "$body_output")
fi

set_test "Rendered body includes editable summary markers"
assert_contains "$generated_body" "<!-- speckit-pro-editable:summary:start -->"

set_test "Rendered body includes editable what_changed markers"
assert_contains "$generated_body" "<!-- speckit-pro-editable:what_changed:start -->"

set_test "Rendered body includes editable why_it_matters markers"
assert_contains "$generated_body" "<!-- speckit-pro-editable:why_it_matters:start -->"

set_test "Rendered body preserves UAT Runbook compatibility heading"
assert_contains "$generated_body" "## UAT Runbook"

set_test "Rendered body includes feature source marker"
assert_contains "$generated_body" "Source: feature specification defines reviewer-ready PR packet behavior."

set_test "Rendered body includes schema source marker"
assert_contains "$generated_body" "Source: schema contract defines editable field markers."

set_test "Rendered body uses packet source marker for verification"
assert_contains "$generated_body" "Source: generated PR packet."

set_test "Rendered body includes traceability mapping"
assert_contains "$generated_body" "Traceability:"

set_test "Rendered body omits raw verification command evidence"
assert_not_contains "$generated_body" "bash tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh"

set_test "Rendered body omits raw changed-file scope evidence"
assert_not_contains "$generated_body" "Changed files:"

set_test "Rendered body includes Known Gaps section content"
assert_contains "$generated_body" "No known gaps"

section "future spec generated packet metadata"

future_feature_rel="specs/spec-014c-future-title-contract"
future_feature="$packet_repo/$future_feature_rel"
future_packet_output_rel="$PR_PACKET_FIXTURE_REL/future-spec-single.json"
future_body_output_rel="$PR_PACKET_FIXTURE_REL/bodies/future-spec-single.md"
future_packet_output="$packet_repo/$future_packet_output_rel"
future_body_output="$packet_repo/$future_body_output_rel"
mkdir -p "$future_feature" "$(dirname "$future_packet_output")" "$(dirname "$future_body_output")"
cat > "$future_feature/spec.md" <<'EOF'
# Feature Specification: Future title contract
EOF
cat > "$future_feature/plan.md" <<'EOF'
# Plan
Primary surface: docs/future
EOF

set_test "Generator writes future SPEC-scoped packet metadata"
result=0
(cd "$packet_repo" && "$SCRIPT" --packet-output "$future_packet_output" "$packet_repo" "$future_feature" "$future_body_output" main...HEAD) || result=$?
assert_eq "0" "$result" "exit code"

set_test "Future generated packet uses derived SPEC scope"
assert_json_file_value "$future_packet_output" "generated_title.scope" "SPEC-014C"

set_test "Future generated packet title uses derived SPEC scope"
assert_json_file_value "$future_packet_output" "generated_title.value" "feat(SPEC-014C): Add future title contract"

set_test "Future generated packet does not use current spec scope"
assert_not_contains "$(cat "$future_packet_output")" "PRSG-012"

set_test "Future generated packet does not fall back to plugin scope"
assert_not_contains "$(cat "$future_packet_output")" "feat(speckit-pro):"

missing_title_feature_rel="specs/spec-014d-missing-title"
missing_title_feature="$packet_repo/$missing_title_feature_rel"
missing_title_packet_output_rel="$PR_PACKET_FIXTURE_REL/missing-title-single.json"
missing_title_body_output_rel="$PR_PACKET_FIXTURE_REL/bodies/missing-title-single.md"
missing_title_packet_output="$packet_repo/$missing_title_packet_output_rel"
missing_title_body_output="$packet_repo/$missing_title_body_output_rel"
missing_title_stderr="$FIXTURE_DIR/missing-title.stderr"
mkdir -p "$missing_title_feature" "$(dirname "$missing_title_packet_output")" "$(dirname "$missing_title_body_output")"
cat > "$missing_title_feature/spec.md" <<'EOF'
This spec intentionally has no Markdown title.
EOF
cat > "$missing_title_feature/plan.md" <<'EOF'
# Plan
Primary surface: docs/missing-title
EOF

set_test "Generator rejects packet metadata when the feature title is missing"
result=0
(cd "$packet_repo" && "$SCRIPT" --packet-output "$missing_title_packet_output" "$packet_repo" "$missing_title_feature" "$missing_title_body_output" main...HEAD) 2>"$missing_title_stderr" || result=$?
assert_eq "2" "$result" "exit code"

set_test "Missing feature title failure is explicit"
assert_contains "$(cat "$missing_title_stderr")" "feature spec title is required"

test_summary
