#!/usr/bin/env bash
# test-generate-pr-body.sh — Unit tests for host-template PR body generation

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"
SCRIPT="$PLUGIN_ROOT/skills/speckit-autopilot/scripts/generate-pr-body.sh"

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
assert_contains "$body" "template: $repo/.github/pull_request_template.md"

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

set_test "Slice packet body includes Slice summary"
assert_contains "$slice_body" "## Slice summary"

set_test "Slice packet body includes Review order"
assert_contains "$slice_body" "## Review order"

set_test "Slice packet body renders review order count"
assert_contains "$slice_body" "1 of 3"

set_test "Slice packet body includes Scope with declared files"
assert_contains "$slice_body" "speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh"

set_test "Slice packet body includes Verification with scoped evidence"
assert_contains "$slice_body" "specs/prsg-009-multi-pr-emission/.process/emission/foundation/layer4.log"

set_test "Slice packet body includes Traceability"
assert_contains "$slice_body" "FR-001a"

set_test "Slice packet body includes Restack or rollback"
assert_contains "$slice_body" "## Restack or rollback"

set_test "Slice packet body includes Known gaps"
assert_contains "$slice_body" "## Known gaps"

set_test "Slice packet body renders Full regression evidence"
assert_contains "$slice_body" "specs/prsg-009-multi-pr-emission/.process/emission/default-verify.log"

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

test_summary
