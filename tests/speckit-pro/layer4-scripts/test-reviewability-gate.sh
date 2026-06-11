#!/usr/bin/env bash
# test-reviewability-gate.sh — Unit tests for reviewability-gate.sh

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"
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

set_test "Setup block with typed exception pragma passes as exception"
roadmap="$FIXTURE_DIR/roadmap-exception.md"
cat > "$roadmap" <<'EOF'
Primary surface: API, UI
Projected reviewable LOC: 900
Projected production files: 9
Projected total files: 26
Reviewability-Exception: refactor
EOF
result=0
output=$("$SCRIPT" setup "$roadmap") || result=$?
assert_eq "0" "$result" "exit code"

set_test "Setup exception status"
assert_json_field "$output" "status" "exception"

set_test "Setup exception_honored is true"
assert_json_field "$output" "exception_honored" "True"

set_test "Setup exception_class is refactor"
assert_json_field "$output" "exception_class" "refactor"

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

set_test "Tasks with multiple surfaces warns but does not block (FR-010)"
result=0
output=$("$SCRIPT" tasks "$feature") || result=$?
assert_eq "0" "$result" "exit code"

set_test "Tasks multiple-surface status is warn not block"
assert_json_field "$output" "status" "warn"

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

# Block-sized slice (9 production files > block threshold 8) carrying only a legacy
# phrase. Production files are COMMITTED so they appear in the diff against the base
# (untracked files are invisible to `git diff`). The diff range is base...HEAD.
exception_repo="$FIXTURE_DIR/exception-repo"
mkdir -p "$exception_repo/docs" "$exception_repo/src"
git -C "$exception_repo" init >/dev/null
git -C "$exception_repo" config user.email support@openai.com
git -C "$exception_repo" config user.name Test
git -C "$exception_repo" config commit.gpgsign false
printf 'base\n' > "$exception_repo/docs/review.md"
git -C "$exception_repo" add .
git -C "$exception_repo" commit -m init >/dev/null
exception_base=$(git -C "$exception_repo" rev-parse HEAD)
printf 'Transition exception: accepted for this large review packet.\n' >> "$exception_repo/docs/review.md"
for i in $(seq 1 9); do
  printf 'export const value%s = %s;\n' "$i" "$i" > "$exception_repo/src/file$i.ts"
done
git -C "$exception_repo" add .
git -C "$exception_repo" commit -m "large slice" >/dev/null

set_test "Diff block with legacy phrase only stays block (FR-013)"
result=0
output=$(cd "$exception_repo" && "$SCRIPT" diff "$exception_base"...HEAD) || result=$?
assert_eq "1" "$result" "exit code"

set_test "Diff legacy phrase does not flip to exception"
assert_json_field "$output" "status" "block"

set_test "Diff legacy phrase leaves exception_honored false"
assert_json_field "$output" "exception_honored" "False"

set_test "Diff invalid range exits 2"
result=0
output=$(cd "$repo" && "$SCRIPT" diff does-not-exist...HEAD) || result=$?
assert_eq "2" "$result" "exit code"

set_test "Diff invalid range emits JSON error"
assert_json_field "$output" "error" "git diff range could not be resolved: does-not-exist...HEAD"

# ──────────────────────────────────────────────────────────────────────────────
# US2 reworked-gate fixtures (PRSG-006): production-only metric (FR-008),
# greenfield allowance (FR-009), surface-as-warning (FR-010), typed exception
# pragma replacing the legacy keyword at all three modes (FR-011/012/013).
# Production files are COMMITTED and the gate is run over base...HEAD so they
# appear in the diff (untracked files are invisible to `git diff`).
# ──────────────────────────────────────────────────────────────────────────────

# Helper: build a fresh git repo whose base commit is empty-ish, then on a second
# commit add the given production line-count plus a Markdown file with $md_body.
# Echoes "base_sha" on stdout; the caller diffs "$base"...HEAD.
make_slice_repo() {
  local dir="$1" prod_files="$2" prod_lines="$3" md_path="$4" md_body="$5"
  mkdir -p "$dir/src" "$(dirname "$dir/$md_path")"
  git -C "$dir" init -q
  git -C "$dir" config user.email support@openai.com
  git -C "$dir" config user.name T
  git -C "$dir" config commit.gpgsign false
  printf 'seed\n' > "$dir/SEED"
  git -C "$dir" add .
  git -C "$dir" commit -qm init
  git -C "$dir" rev-parse HEAD
  local i
  for i in $(seq 1 "$prod_files"); do
    seq 1 "$prod_lines" | sed "s/^/const f${i}_/" > "$dir/src/file$i.ts"
  done
  if [ -n "$md_body" ]; then
    printf '%s\n' "$md_body" > "$dir/$md_path"
  fi
  git -C "$dir" add .
  git -C "$dir" commit -qm slice >/dev/null
}

section "diff mode — production-only metric (FR-008 / SC-003)"

# Production additions (1 file × 100 lines = 100 < 400 warn) but total additions
# (with a 500-line doc) = 600 > 400. Production-only metric must NOT warn.
metric_repo="$FIXTURE_DIR/metric-repo"
metric_base=$(make_slice_repo "$metric_repo" 1 100 "docs/big.md" "")
seq 1 500 | sed 's/^/doc line /' > "$metric_repo/docs/big.md"
git -C "$metric_repo" add .
git -C "$metric_repo" commit -qm bigdoc >/dev/null

set_test "Production-only metric: docs do not inflate reviewable_loc"
result=0
output=$(cd "$metric_repo" && "$SCRIPT" diff "$metric_base"...HEAD) || result=$?
assert_eq "0" "$result" "exit code"

set_test "Production-only metric: reviewable_loc counts production only (100, not 600)"
assert_json_field "$output" "reviewable_loc" "100"

set_test "Production-only metric: no reviewable-LOC warning despite 600 total additions"
assert_not_contains "$output" "reviewable LOC" "production-only metric must not warn on LOC"

section "diff mode — greenfield allowance (FR-009)"

# All-new production: 1 file × 500 lines. 500 > base warn 400 but < greenfield warn 600.
greenfield_repo="$FIXTURE_DIR/greenfield-repo"
greenfield_base=$(make_slice_repo "$greenfield_repo" 1 500 "" "")

set_test "Greenfield: all add-status A → greenfield true"
result=0
output=$(cd "$greenfield_repo" && "$SCRIPT" diff "$greenfield_base"...HEAD) || result=$?
assert_eq "0" "$result" "exit code"
assert_json_field "$output" "greenfield" "True"

set_test "Greenfield: reviewable_loc 500 within scaled warn → status pass"
assert_json_field "$output" "reviewable_loc" "500"

set_test "Greenfield: warn LOC threshold scaled 400→600"
assert_json_field "$output" "thresholds.warn.reviewable_loc" "600"

set_test "Greenfield: block LOC threshold scaled 800→1200"
assert_json_field "$output" "thresholds.block.reviewable_loc" "1200"

set_test "Greenfield: production_files warn threshold UNCHANGED (6)"
assert_json_field "$output" "thresholds.warn.production_files" "6"

set_test "Greenfield: total_files warn threshold UNCHANGED (15)"
assert_json_field "$output" "thresholds.warn.total_files" "15"

set_test "Greenfield: production_files block threshold UNCHANGED (8)"
assert_json_field "$output" "thresholds.block.production_files" "8"

set_test "Greenfield: primary_surfaces warn threshold UNCHANGED (1)"
assert_json_field "$output" "thresholds.warn.primary_surfaces" "1"

# One MODIFIED non-excluded file disqualifies greenfield.
modified_repo="$FIXTURE_DIR/modified-repo"
mkdir -p "$modified_repo/src"
git -C "$modified_repo" init -q
git -C "$modified_repo" config user.email support@openai.com
git -C "$modified_repo" config user.name T
git -C "$modified_repo" config commit.gpgsign false
printf 'export const existing = 0;\n' > "$modified_repo/src/existing.ts"
git -C "$modified_repo" add .
git -C "$modified_repo" commit -qm init
modified_base=$(git -C "$modified_repo" rev-parse HEAD)
printf 'export const added = 1;\n' > "$modified_repo/src/added.ts"
printf 'export const existing = 0;\nexport const more = 2;\n' > "$modified_repo/src/existing.ts"
git -C "$modified_repo" add .
git -C "$modified_repo" commit -qm change >/dev/null

set_test "Greenfield: a modified non-excluded file disqualifies → greenfield false"
result=0
output=$(cd "$modified_repo" && "$SCRIPT" diff "$modified_base"...HEAD) || result=$?
assert_json_field "$output" "greenfield" "False"

set_test "Greenfield false: warn LOC threshold stays base 400"
assert_json_field "$output" "thresholds.warn.reviewable_loc" "400"

# A modified EXCLUDED lockfile alone (plus only new files) is STILL greenfield.
lockgreen_repo="$FIXTURE_DIR/lockgreen-repo"
mkdir -p "$lockgreen_repo/src"
git -C "$lockgreen_repo" init -q
git -C "$lockgreen_repo" config user.email support@openai.com
git -C "$lockgreen_repo" config user.name T
git -C "$lockgreen_repo" config commit.gpgsign false
printf 'lockfile: 1\n' > "$lockgreen_repo/pnpm-lock.yaml"
git -C "$lockgreen_repo" add .
git -C "$lockgreen_repo" commit -qm init
lockgreen_base=$(git -C "$lockgreen_repo" rev-parse HEAD)
printf 'export const fresh = 1;\n' > "$lockgreen_repo/src/fresh.ts"
printf 'lockfile: 1\nlockfile: 2\n' > "$lockgreen_repo/pnpm-lock.yaml"
git -C "$lockgreen_repo" add .
git -C "$lockgreen_repo" commit -qm change >/dev/null

set_test "Greenfield: a modified EXCLUDED lockfile does not disqualify → greenfield true"
result=0
output=$(cd "$lockgreen_repo" && "$SCRIPT" diff "$lockgreen_base"...HEAD) || result=$?
assert_json_field "$output" "greenfield" "True"

# --no-renames pins the boolean against an ambient diff.renames config. With
# rename detection ON, a delete+add could be reported as a rename (R) and slip
# the all-A predicate; --no-renames keeps it A so the greenfield boolean is stable.
renames_repo="$FIXTURE_DIR/renames-repo"
make_slice_repo "$renames_repo" 1 50 "" "" >/dev/null
renames_base=$(git -C "$renames_repo" rev-parse HEAD~1)
git -C "$renames_repo" config diff.renames true

set_test "Greenfield: --no-renames pins greenfield true under ambient diff.renames"
result=0
output=$(cd "$renames_repo" && "$SCRIPT" diff "$renames_base"...HEAD) || result=$?
assert_json_field "$output" "greenfield" "True"

section "diff mode — surface count is a warning, not a block (FR-010 / SC-004)"

# Two primary surfaces (API + UI), small production LOC. Must WARN, never block on
# surface. Surface count + list still reported.
surface_repo="$FIXTURE_DIR/surface-repo"
mkdir -p "$surface_repo/src/app/api/x" "$surface_repo/src/components"
git -C "$surface_repo" init -q
git -C "$surface_repo" config user.email support@openai.com
git -C "$surface_repo" config user.name T
git -C "$surface_repo" config commit.gpgsign false
printf 'seed\n' > "$surface_repo/SEED"
git -C "$surface_repo" add .
git -C "$surface_repo" commit -qm init
surface_base=$(git -C "$surface_repo" rev-parse HEAD)
printf 'export const route = 1;\n' > "$surface_repo/src/app/api/x/route.ts"
printf 'export const Comp = 2;\n' > "$surface_repo/src/components/widget.tsx"
git -C "$surface_repo" add .
git -C "$surface_repo" commit -qm twosurfaces >/dev/null

set_test "Multi-surface diff slice does not block (FR-010)"
result=0
output=$(cd "$surface_repo" && "$SCRIPT" diff "$surface_base"...HEAD) || result=$?
assert_eq "0" "$result" "exit code"

set_test "Multi-surface diff slice status is warn"
assert_json_field "$output" "status" "warn"

set_test "Multi-surface diff retains primary_surface_count >= 2"
surf_count=$(printf '%s' "$output" | python3 -c 'import sys,json; print(json.load(sys.stdin)["primary_surface_count"])')
assert_gt "$surf_count" "1" "primary_surface_count"

set_test "Multi-surface diff retains primary_surfaces list"
assert_json_field_exists "$output" "primary_surfaces"

set_test "Multi-surface diff: no surface-attributable blocker"
assert_not_contains "$output" "more than one primary surface" "surface blocker removed"

section "diff mode — typed exception bypass list (FR-011/012 / SC-005)"

# A block-sized base (9 production files > block threshold 8). For each bypass
# variant the gate must STAY block (exit 1, exception_honored false). Then the
# POSITIVE: a valid pragma on an added .md line flips block → exception.
# bypass_check <label> <md-body> ; asserts the slice stays block.
bypass_n=0
bypass_check() {
  local label="$1" md_body="$2"
  bypass_n=$((bypass_n + 1))
  local d="$FIXTURE_DIR/bypass-$bypass_n"
  local base
  base=$(make_slice_repo "$d" 9 1 "docs/gov.md" "$md_body")
  local r=0 out
  out=$(cd "$d" && "$SCRIPT" diff "$base"...HEAD) || r=$?
  set_test "Bypass: $label → stays block (exit 1)"
  assert_eq "1" "$r" "exit code"
  set_test "Bypass: $label → exception_honored false"
  assert_json_field "$out" "exception_honored" "False"
}

bypass_check "class outside the set (hotfix)"        "Reviewability-Exception: hotfix"
bypass_check "extended class (refactoring)"          "Reviewability-Exception: refactoring"
bypass_check "abbreviated class (ref)"               "Reviewability-Exception: ref"
bypass_check "comma-joined classes"                  "Reviewability-Exception: refactor,infra"
bypass_check "case variant in class (Refactor)"      "Reviewability-Exception: Refactor"
bypass_check "upcased key (REVIEWABILITY-EXCEPTION)" "REVIEWABILITY-EXCEPTION: refactor"
bypass_check "trailing content (refactor # ok)"      "Reviewability-Exception: refactor # ok"
bypass_check "no space after colon"                  "Reviewability-Exception:refactor"

template_repo="$FIXTURE_DIR/template-provenance-repo"
template_base=$(make_slice_repo "$template_repo" 9 1 ".specify/templates/spec-template.md" "Reviewability-Exception: refactor")

set_test "Bypass: pragma in generated/template provenance -> stays block"
result=0
output=$(cd "$template_repo" && "$SCRIPT" diff "$template_base"...HEAD) || result=$?
assert_eq "1" "$result" "exit code"
assert_json_field "$output" "exception_honored" "False"

code_fence_repo="$FIXTURE_DIR/code-fence-provenance-repo"
code_fence_base=$(make_slice_repo "$code_fence_repo" 9 1 "docs/gov.md" $'```text\nReviewability-Exception: refactor\n```')

set_test "Bypass: pragma inside Markdown code fence -> stays block"
result=0
output=$(cd "$code_fence_repo" && "$SCRIPT" diff "$code_fence_base"...HEAD) || result=$?
assert_eq "1" "$result" "exit code"
assert_json_field "$output" "exception_honored" "False"

# Pragma only in the (mutable) PR body / commit message — never read by the gate.
# Modelled as the pragma in the COMMIT MESSAGE, with no pragma in any tracked file.
prbody_repo="$FIXTURE_DIR/prbody-repo"
prbody_base=$(make_slice_repo "$prbody_repo" 9 1 "docs/gov.md" "no pragma here")
git -C "$prbody_repo" commit -q --amend -m "slice

Reviewability-Exception: refactor" >/dev/null

set_test "Bypass: pragma only in commit message → stays block"
result=0
output=$(cd "$prbody_repo" && "$SCRIPT" diff "$prbody_base"...HEAD) || result=$?
assert_eq "1" "$result" "exit code"
assert_json_field "$output" "exception_honored" "False"

# Pragma on a REMOVED (-) line: present on the base, deleted by the slice. The
# removed line must NOT flip. Base has the valid pragma; slice deletes it.
removed_repo="$FIXTURE_DIR/removed-repo"
mkdir -p "$removed_repo/src" "$removed_repo/docs"
git -C "$removed_repo" init -q
git -C "$removed_repo" config user.email support@openai.com
git -C "$removed_repo" config user.name T
git -C "$removed_repo" config commit.gpgsign false
printf 'Reviewability-Exception: refactor\n' > "$removed_repo/docs/gov.md"
git -C "$removed_repo" add .
git -C "$removed_repo" commit -qm init
removed_base=$(git -C "$removed_repo" rev-parse HEAD)
printf 'now without the pragma\n' > "$removed_repo/docs/gov.md"
for i in $(seq 1 9); do printf 'export const r%s = %s;\n' "$i" "$i" > "$removed_repo/src/file$i.ts"; done
git -C "$removed_repo" add .
git -C "$removed_repo" commit -qm slice >/dev/null

set_test "Bypass: pragma on a removed (-) line → stays block"
result=0
output=$(cd "$removed_repo" && "$SCRIPT" diff "$removed_base"...HEAD) || result=$?
assert_eq "1" "$result" "exit code"
assert_json_field "$output" "exception_honored" "False"

# Pragma on a CONTEXT (unchanged) line: pre-existing on the base, untouched by the
# slice. Over base...HEAD it appears as context, NOT an added line → must NOT flip.
context_repo="$FIXTURE_DIR/context-repo"
mkdir -p "$context_repo/src" "$context_repo/docs"
git -C "$context_repo" init -q
git -C "$context_repo" config user.email support@openai.com
git -C "$context_repo" config user.name T
git -C "$context_repo" config commit.gpgsign false
printf 'Reviewability-Exception: refactor\nkeep this file non-empty\n' > "$context_repo/docs/gov.md"
git -C "$context_repo" add .
git -C "$context_repo" commit -qm init
context_base=$(git -C "$context_repo" rev-parse HEAD)
for i in $(seq 1 9); do printf 'export const c%s = %s;\n' "$i" "$i" > "$context_repo/src/file$i.ts"; done
git -C "$context_repo" add .
git -C "$context_repo" commit -qm slice >/dev/null

set_test "Bypass: pre-existing pragma on a context line → stays block"
result=0
output=$(cd "$context_repo" && "$SCRIPT" diff "$context_base"...HEAD) || result=$?
assert_eq "1" "$result" "exit code"
assert_json_field "$output" "exception_honored" "False"

# The unified-diff +++ b/<path> header for a file path that resembles the pragma
# must NOT self-satisfy the matcher. A new file literally named like the pragma
# token; its +++ header is filtered out before matching.
header_repo="$FIXTURE_DIR/header-repo"
mkdir -p "$header_repo/src"
git -C "$header_repo" init -q
git -C "$header_repo" config user.email support@openai.com
git -C "$header_repo" config user.name T
git -C "$header_repo" config commit.gpgsign false
printf 'seed\n' > "$header_repo/SEED"
git -C "$header_repo" add .
git -C "$header_repo" commit -qm init
header_base=$(git -C "$header_repo" rev-parse HEAD)
# A markdown file whose path resembles the pragma token (so the +++ header line
# reads like "+++ b/...Reviewability-Exception: refactor..."), with benign content.
mkdir -p "$header_repo/docs"
printf 'benign content\n' > "$header_repo/docs/Reviewability-Exception: refactor.md"
for i in $(seq 1 9); do printf 'export const h%s = %s;\n' "$i" "$i" > "$header_repo/src/file$i.ts"; done
git -C "$header_repo" add .
git -C "$header_repo" commit -qm slice >/dev/null

set_test "Bypass: +++ header resembling the pragma → stays block"
result=0
output=$(cd "$header_repo" && "$SCRIPT" diff "$header_base"...HEAD) || result=$?
assert_eq "1" "$result" "exit code"
assert_json_field "$output" "exception_honored" "False"

# POSITIVE: a valid pragma on an ADDED (+) line of a committed .md flips block →
# exception. Same block-sized base; the .md carries the exact valid pragma.
positive_repo="$FIXTURE_DIR/positive-repo"
positive_base=$(make_slice_repo "$positive_repo" 9 1 "docs/gov.md" "Reviewability-Exception: refactor")

set_test "Positive: valid pragma on added .md line flips block → exception"
result=0
output=$(cd "$positive_repo" && "$SCRIPT" diff "$positive_base"...HEAD) || result=$?
assert_eq "0" "$result" "exit code"

set_test "Positive: status is exception"
assert_json_field "$output" "status" "exception"

set_test "Positive: exception_honored true"
assert_json_field "$output" "exception_honored" "True"

set_test "Positive: exception_class is refactor"
assert_json_field "$output" "exception_class" "refactor"

# All three classes flip a block equally in v1.
for cls in infra upgrade; do
  cls_repo="$FIXTURE_DIR/positive-$cls"
  cls_base=$(make_slice_repo "$cls_repo" 9 1 "docs/gov.md" "Reviewability-Exception: $cls")
  set_test "Positive: class $cls flips block → exception"
  result=0
  output=$(cd "$cls_repo" && "$SCRIPT" diff "$cls_base"...HEAD) || result=$?
  assert_eq "0" "$result" "exit code"
  set_test "Positive: class $cls recorded in exception_class"
  assert_json_field "$output" "exception_class" "$cls"
done

section "setup + tasks modes — legacy phrase honored by no mode (FR-013 / SC-006)"

# setup mode: a block-sized roadmap carrying only a legacy phrase stays block.
legacy_setup="$FIXTURE_DIR/legacy-setup.md"
cat > "$legacy_setup" <<'EOF'
Primary surface: API, UI
Projected reviewable LOC: 900
Projected production files: 9
Projected total files: 26
split exception
transition exception
ratified exception
EOF
set_test "Legacy (setup): phrases do not flip block"
result=0
output=$("$SCRIPT" setup "$legacy_setup") || result=$?
assert_eq "1" "$result" "exit code"
assert_json_field "$output" "status" "block"

# tasks mode: a block-sized feature dir carrying only a legacy phrase stays block.
legacy_feature="$FIXTURE_DIR/specs/legacy-tasks"
mkdir -p "$legacy_feature"
{
  printf '# Tasks\n'
  printf 'split exception\n'
  for i in $(seq 1 30); do printf -- '- [ ] T%03d Update src/mod%s.ts\n' "$i" "$i"; done
} > "$legacy_feature/tasks.md"
set_test "Legacy (tasks): phrase does not flip block"
result=0
output=$("$SCRIPT" tasks "$legacy_feature") || result=$?
assert_eq "1" "$result" "exit code"
assert_json_field "$output" "status" "block"

section "diff mode — fenced-code pragma rejection (PRSG-010A)"

# PRSG-010A closes the old line-scoped limitation: a valid-looking pragma inside
# a fenced code block in committed Markdown is generated/prose evidence and must
# not flip the block.
fenced_repo="$FIXTURE_DIR/fenced-repo"
fenced_md=$(printf '```\nReviewability-Exception: refactor\n```')
fenced_base=$(make_slice_repo "$fenced_repo" 9 1 "docs/gov.md" "$fenced_md")

set_test "Fenced-code pragma stays block"
result=0
output=$(cd "$fenced_repo" && "$SCRIPT" diff "$fenced_base"...HEAD) || result=$?
assert_eq "1" "$result" "exit code"
assert_json_field "$output" "exception_honored" "False"
section "diff mode — .process/ exclusion under the production-only metric (FR-008/FR-010, reconciled with PR #111)"

# PRSG-006 makes reviewable_loc PRODUCTION-only (FR-008), superseding PR #111's
# markdown-counting fixtures (which expected spec.md/plan.md lines to count). The
# .process/ exhaust-exclusion guarantee #111 added — the `*/.process/*` arm of
# is_excluded_generated, PRSG-001's deliverable, reused here as-is — still holds,
# now exercised with PRODUCTION files: a production file under specs/<NNN>/.process/
# is EXCLUDED; production code elsewhere is counted.
process_repo="$FIXTURE_DIR/process-repo"
mkdir -p "$process_repo/src" "$process_repo/specs/007-demo/.process"
git -C "$process_repo" init >/dev/null
git -C "$process_repo" config user.email support@openai.com
git -C "$process_repo" config user.name Test
git -C "$process_repo" config commit.gpgsign false
printf 'const base=0\n' > "$process_repo/src/keep.ts"
printf 'const base=0\n' > "$process_repo/specs/007-demo/.process/gen.ts"
git -C "$process_repo" add .
git -C "$process_repo" commit -m init >/dev/null
# Add 5 production lines to src/ (counted) and 30 to a .process/ production file
# (excluded). A regression in the .process/ glob would count all 35.
seq 1 5 | sed 's/^/const a/' >> "$process_repo/src/keep.ts"
seq 1 30 | sed 's/^/const b/' >> "$process_repo/specs/007-demo/.process/gen.ts"

set_test "Diff: src/ production counts, a production file under .process/ is excluded (reviewable_loc 5, not 35)"
result=0
output=$(cd "$process_repo" && "$SCRIPT" diff HEAD) || result=$?
assert_json_field "$output" "reviewable_loc" "5"

# No-false-exclusion: a production path with NO /.process/ segment is counted.
nonprocess_repo="$FIXTURE_DIR/nonprocess-repo"
mkdir -p "$nonprocess_repo/src"
git -C "$nonprocess_repo" init >/dev/null
git -C "$nonprocess_repo" config user.email support@openai.com
git -C "$nonprocess_repo" config user.name Test
git -C "$nonprocess_repo" config commit.gpgsign false
printf 'const base=0\n' > "$nonprocess_repo/src/plain.ts"
git -C "$nonprocess_repo" add .
git -C "$nonprocess_repo" commit -m init >/dev/null
seq 1 7 | sed 's/^/const c/' >> "$nonprocess_repo/src/plain.ts"

set_test "Diff: production file with no .process/ segment is not excluded (reviewable_loc 7)"
result=0
output=$(cd "$nonprocess_repo" && "$SCRIPT" diff HEAD) || result=$?
assert_json_field "$output" "reviewable_loc" "7"

# Regression guard (PR #111 review): a directory that merely ENDS in ".process"
# (foo.process/) is NOT the .process/ exhaust dir and MUST stay counted. The
# earlier over-broad *.process/* arm wrongly excluded it; the `*/.process/*`
# segment glob counts it. Exercised with a production file under PRSG-006's metric.
endsprocess_repo="$FIXTURE_DIR/endsprocess-repo"
mkdir -p "$endsprocess_repo/src/foo.process"
git -C "$endsprocess_repo" init >/dev/null
git -C "$endsprocess_repo" config user.email support@openai.com
git -C "$endsprocess_repo" config user.name Test
git -C "$endsprocess_repo" config commit.gpgsign false
printf 'const base=0\n' > "$endsprocess_repo/src/foo.process/mod.ts"
git -C "$endsprocess_repo" add .
git -C "$endsprocess_repo" commit -m init >/dev/null
seq 1 9 | sed 's/^/const d/' >> "$endsprocess_repo/src/foo.process/mod.ts"

set_test "Diff: a dir ending in .process (foo.process/) is NOT the .process/ dir — production code counts (reviewable_loc 9)"
result=0
output=$(cd "$endsprocess_repo" && "$SCRIPT" diff HEAD) || result=$?
assert_json_field "$output" "reviewable_loc" "9"

# No-op of the .process/ arm when no .process/ path is present: a mixed change
# (production + markdown, neither under .process/) counts production only — the
# markdown is dropped by the production filter (FR-008), not the .process/ arm.
mixed_repo="$FIXTURE_DIR/mixed-noprocess-repo"
mkdir -p "$mixed_repo/src" "$mixed_repo/docs"
git -C "$mixed_repo" init >/dev/null
git -C "$mixed_repo" config user.email support@openai.com
git -C "$mixed_repo" config user.name Test
git -C "$mixed_repo" config commit.gpgsign false
printf 'const base=0\n' > "$mixed_repo/src/app.ts"
printf 'base\n' > "$mixed_repo/docs/guide.md"
git -C "$mixed_repo" add .
git -C "$mixed_repo" commit -m init >/dev/null
seq 1 4 | sed 's/^/const e/' >> "$mixed_repo/src/app.ts"
seq 1 20 >> "$mixed_repo/docs/guide.md"

set_test "Diff: mixed production+markdown, zero .process/ paths → counts production only (reviewable_loc 4)"
result=0
output=$(cd "$mixed_repo" && "$SCRIPT" diff HEAD) || result=$?
assert_json_field "$output" "reviewable_loc" "4"

test_summary
