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
mkdir -p "$repo/.github" "$feature" "$repo/docs"
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

set_test "Appends Non-goals section"
assert_contains "$body" "# Non-goals"

set_test "Extracts section content from level-two spec headings"
assert_contains "$body" "Do not add unrelated runtime behavior."

set_test "Appends Scope Budget section"
assert_contains "$body" "# Scope Budget"

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

set_test "Fallback body includes Review Order"
assert_contains "$fallback_body" "# Review Order"

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

test_summary
