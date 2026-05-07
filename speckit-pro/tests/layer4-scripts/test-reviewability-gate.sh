#!/usr/bin/env bash
# test-reviewability-gate.sh — Unit tests for reviewability-gate.sh

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$PLUGIN_ROOT/skills/speckit-autopilot/scripts/reviewability-gate.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

section "reviewability-gate usage"

set_test "No arguments exits 2"
result=0
output=$("$SCRIPT" 2>/dev/null) || result=$?
assert_eq "2" "$result" "exit code"

section "setup mode"

set_test "Setup within budget passes"
roadmap="$FIXTURE_DIR/roadmap-pass.md"
cat > "$roadmap" <<'EOF'
Primary surface: docs/process
Projected reviewable LOC: 120
Projected production files: 2
Projected total files: 4
EOF
result=0
output=$("$SCRIPT" setup "$roadmap") || result=$?
assert_eq "0" "$result" "exit code"

set_test "Setup pass status is pass"
assert_json_field "$output" "status" "pass"

set_test "Setup over block without exception fails"
roadmap="$FIXTURE_DIR/roadmap-block.md"
cat > "$roadmap" <<'EOF'
Primary surface: API, UI
Projected reviewable LOC: 900
Projected production files: 9
Projected total files: 26
EOF
result=0
output=$("$SCRIPT" setup "$roadmap") || result=$?
assert_eq "1" "$result" "exit code"

set_test "Setup block status is block"
assert_json_field "$output" "status" "block"

set_test "Setup block with transition exception passes as exception"
roadmap="$FIXTURE_DIR/roadmap-exception.md"
cat > "$roadmap" <<'EOF'
Primary surface: API, UI
Projected reviewable LOC: 900
Projected production files: 9
Projected total files: 26
Transition exception: PR #30 only.
EOF
result=0
output=$("$SCRIPT" setup "$roadmap") || result=$?
assert_eq "0" "$result" "exit code"

set_test "Setup exception status"
assert_json_field "$output" "status" "exception"

section "tasks mode"

feature="$FIXTURE_DIR/specs/001-demo"
mkdir -p "$feature"
cat > "$feature/tasks.md" <<'EOF'
# Tasks
- [ ] T001 Update docs/guide.md
- [ ] T002 Update src/app/api/demo/route.ts
- [ ] T003 Update src/components/demo.tsx
EOF

set_test "Tasks with multiple surfaces blocks"
result=0
output=$("$SCRIPT" tasks "$feature") || result=$?
assert_eq "1" "$result" "exit code"

set_test "Tasks reports multiple surfaces"
assert_json_field "$output" "primary_surface_count" "3"

section "diff mode"

repo="$FIXTURE_DIR/repo"
mkdir -p "$repo/src/app/api/demo" "$repo/docs"
git -C "$repo" init >/dev/null
git -C "$repo" config user.email support@openai.com
git -C "$repo" config user.name Test
git -C "$repo" config commit.gpgsign false
printf 'base\n' > "$repo/docs/guide.md"
git -C "$repo" add .
git -C "$repo" commit -m init >/dev/null
printf 'change\n' >> "$repo/docs/guide.md"

set_test "Diff docs-only passes"
result=0
output=$(cd "$repo" && "$SCRIPT" diff HEAD) || result=$?
assert_eq "0" "$result" "exit code"

set_test "Diff mode field"
assert_json_field "$output" "mode" "diff"

test_summary
