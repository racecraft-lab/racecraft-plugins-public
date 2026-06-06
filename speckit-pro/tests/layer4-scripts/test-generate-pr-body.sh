#!/usr/bin/env bash
# test-generate-pr-body.sh — Unit tests for host-template PR body generation

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
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
