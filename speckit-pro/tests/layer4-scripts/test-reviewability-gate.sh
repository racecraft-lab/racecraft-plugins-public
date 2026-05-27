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

set_test "Tasks mode requires tasks.md"
result=0
output=$("$SCRIPT" tasks "$feature") || result=$?
assert_eq "2" "$result" "exit code"

set_test "Missing tasks.md emits JSON error"
assert_json_field "$output" "error" "required tasks file not readable: $feature/tasks.md"

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

clock_feature="$FIXTURE_DIR/specs/002-clock"
mkdir -p "$clock_feature"
cat > "$clock_feature/tasks.md" <<'EOF'
# Tasks
- [ ] T001 Update src/clock.ts
EOF

set_test "Tasks mode counts clock source as production"
result=0
output=$("$SCRIPT" tasks "$clock_feature") || result=$?
assert_eq "0" "$result" "exit code"

set_test "Clock source is not excluded as a lockfile"
assert_json_field "$output" "production_files" "1"

lock_feature="$FIXTURE_DIR/specs/003-lockfile"
mkdir -p "$lock_feature"
cat > "$lock_feature/tasks.md" <<'EOF'
# Tasks
- [ ] T001 Update pnpm-lock.yaml
EOF

set_test "Tasks mode excludes explicit lockfile basename"
result=0
output=$("$SCRIPT" tasks "$lock_feature") || result=$?
assert_eq "0" "$result" "exit code"

set_test "Lockfile is excluded from production count"
assert_json_field "$output" "production_files" "0"

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

exception_repo="$FIXTURE_DIR/exception-repo"
mkdir -p "$exception_repo/docs" "$exception_repo/src"
git -C "$exception_repo" init >/dev/null
git -C "$exception_repo" config user.email support@openai.com
git -C "$exception_repo" config user.name Test
git -C "$exception_repo" config commit.gpgsign false
printf 'base\n' > "$exception_repo/docs/review.md"
git -C "$exception_repo" add .
git -C "$exception_repo" commit -m init >/dev/null
{
  printf 'Transition exception: accepted for this large review packet.\n'
  seq 1 900
} >> "$exception_repo/docs/review.md"
for i in $(seq 1 9); do
  printf 'export const value%s = %s;\n' "$i" "$i" > "$exception_repo/src/file$i.ts"
done

set_test "Diff block with transition exception exits 0"
result=0
output=$(cd "$exception_repo" && "$SCRIPT" diff HEAD) || result=$?
assert_eq "0" "$result" "exit code"

set_test "Diff block with transition exception reports exception"
assert_json_field "$output" "status" "exception"

set_test "Diff invalid range exits 2"
result=0
output=$(cd "$repo" && "$SCRIPT" diff does-not-exist...HEAD) || result=$?
assert_eq "2" "$result" "exit code"

set_test "Diff invalid range emits JSON error"
assert_json_field "$output" "error" "git diff range could not be resolved: does-not-exist...HEAD"

test_summary
