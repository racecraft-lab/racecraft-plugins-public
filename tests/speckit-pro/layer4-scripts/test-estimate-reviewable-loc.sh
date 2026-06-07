#!/usr/bin/env bash
# test-estimate-reviewable-loc.sh — Unit tests for estimate-reviewable-loc.sh (PRSG-006 US1)
#
# Each content-status fixture asserts a KNOWN expected value (parsed file count AND
# projected production-LOC), not merely two-run equality (FR-002). The estimator is
# advisory: every content status returns exit 0; only file-level/usage errors exit 2.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"
SCRIPT="$PLUGIN_ROOT/skills/speckit-autopilot/scripts/estimate-reviewable-loc.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

# ─────────────────────────────────────────────────────────────────────────────
# T004 — Determinism + known-value (FR-002, SC-001)
# A representative non-empty `## Declared File Operations` block: 8 all-NEW
# production files under src/. Assert the parsed planned-file count AND projected
# equal a hardcoded KNOWN value, then assert run-2 stdout is byte-identical to run-1.
# 8 production files × PROD_LOC_PER_FILE(40) = 320 (mirrors the contract example).
# ─────────────────────────────────────────────────────────────────────────────
section "T004 determinism + known-value"

plan_known="$FIXTURE_DIR/plan-known.md"
cat > "$plan_known" <<'EOF'
# Implementation Plan

Some prose describing the approach. KISS/YAGNI noted here as a decoy token.

## Declared File Operations

- NEW src/feature/alpha.ts
- NEW src/feature/beta.ts
- NEW src/feature/gamma.ts
- NEW src/feature/delta.ts
- NEW src/feature/epsilon.ts
- NEW src/feature/zeta.ts
- NEW src/feature/eta.ts
- NEW src/feature/theta.ts

## Some Other Section

- this is not an entry
EOF

set_test "Known-value run exits 0"
result=0
output=$("$SCRIPT" "$plan_known") || result=$?
assert_eq "0" "$result" "exit code"

set_test "Known-value: total_entries parsed == 8"
assert_json_field "$output" "declared_files.total_entries" "8"

set_test "Known-value: production count == 8"
assert_json_field "$output" "declared_files.production" "8"

set_test "Known-value: projected == 320 (8 x 40)"
assert_json_field "$output" "projected" "320"

set_test "Known-value: status pass"
assert_json_field "$output" "status" "pass"

set_test "Determinism: run-2 is byte-identical to run-1"
run1=$("$SCRIPT" "$plan_known")
run2=$("$SCRIPT" "$plan_known")
assert_eq "$run1" "$run2" "byte-identical stdout"

# ─────────────────────────────────────────────────────────────────────────────
# T005 — Three-value status (FR-003, SC-002)
#   under-budget block  -> status "pass",         integer projected, exit 0
#   over-budget block   -> status "over_budget",  integer projected, exit 0 (advisory)
#   no/garbage block    -> status "not_estimated", projected null, declared_files zero
# ─────────────────────────────────────────────────────────────────────────────
section "T005 three-value status"

# --- pass arm: 3 NEW production files = 120 LOC, well under greenfield block 1200
plan_pass="$FIXTURE_DIR/plan-pass.md"
cat > "$plan_pass" <<'EOF'
## Declared File Operations

- NEW src/a.ts
- NEW src/b.ts
- NEW src/c.ts
EOF

set_test "pass arm exits 0"
result=0
output=$("$SCRIPT" "$plan_pass") || result=$?
assert_eq "0" "$result" "exit code"

set_test "pass arm status pass"
assert_json_field "$output" "status" "pass"

set_test "pass arm projected == 120"
assert_json_field "$output" "projected" "120"

# --- over_budget arm: 20 NEW + 1 MODIFIED production files (NOT greenfield, block=800)
#     21 production files x 40 = 840 > 800 -> over_budget, exit 0 (advisory).
plan_over="$FIXTURE_DIR/plan-over.md"
{
  printf '## Declared File Operations\n\n'
  for i in $(seq 1 20); do printf -- '- NEW src/over/file%s.ts\n' "$i"; done
  printf -- '- MODIFIED src/over/existing.ts\n'
} > "$plan_over"

set_test "over_budget arm exits 0 (advisory, never blocks)"
result=0
output=$("$SCRIPT" "$plan_over") || result=$?
assert_eq "0" "$result" "exit code"

set_test "over_budget arm status over_budget"
assert_json_field "$output" "status" "over_budget"

set_test "over_budget arm projected == 840"
assert_json_field "$output" "projected" "840"

set_test "over_budget arm production count == 21"
assert_json_field "$output" "declared_files.production" "21"

# --- not_estimated arm: a readable plan.md with no parseable declared-files block
plan_none="$FIXTURE_DIR/plan-none.md"
cat > "$plan_none" <<'EOF'
# Implementation Plan

This plan has no Declared File Operations block at all, only prose mentioning
src/foo.ts inline and a stray "NEW idea" that must not be parsed as an entry.
EOF

set_test "not_estimated arm exits 0"
result=0
output=$("$SCRIPT" "$plan_none") || result=$?
assert_eq "0" "$result" "exit code"

set_test "not_estimated arm status not_estimated"
assert_json_field "$output" "status" "not_estimated"

set_test "not_estimated arm projected is null"
assert_json_field "$output" "projected" "None"

set_test "not_estimated arm total_entries == 0"
assert_json_field "$output" "declared_files.total_entries" "0"

set_test "not_estimated arm production == 0"
assert_json_field "$output" "declared_files.production" "0"

set_test "not_estimated arm greenfield false"
assert_json_field "$output" "greenfield" "False"

# ─────────────────────────────────────────────────────────────────────────────
# T006 — File-level error + errexit crash-safety (FR-003 file-level path, Edge Cases)
#   absent/unreadable plan.md  -> exit 2
#   usage error (missing args) -> exit 2
#   usage error (extra args)   -> exit 2
#   the three content statuses keep exit 0 (verdict carried in JSON status only).
# ─────────────────────────────────────────────────────────────────────────────
section "T006 file-level error + crash-safety"

set_test "Absent plan.md exits 2"
result=0
output=$("$SCRIPT" "$FIXTURE_DIR/does-not-exist.md" 2>/dev/null) || result=$?
assert_eq "2" "$result" "exit code"

set_test "Missing args exits 2"
result=0
output=$("$SCRIPT" 2>/dev/null) || result=$?
assert_eq "2" "$result" "exit code"

set_test "Extra args exits 2"
result=0
output=$("$SCRIPT" "$plan_pass" extra-arg 2>/dev/null) || result=$?
assert_eq "2" "$result" "exit code"

set_test "Unreadable plan.md exits 2"
plan_unreadable="$FIXTURE_DIR/plan-unreadable.md"
cat > "$plan_unreadable" <<'EOF'
## Declared File Operations

- NEW src/x.ts
EOF
chmod 000 "$plan_unreadable"
result=0
output=$("$SCRIPT" "$plan_unreadable" 2>/dev/null) || result=$?
chmod 644 "$plan_unreadable"
assert_eq "2" "$result" "exit code"

set_test "content status pass keeps exit 0"
result=0
output=$("$SCRIPT" "$plan_pass") || result=$?
assert_eq "0" "$result" "exit code"

set_test "content status over_budget keeps exit 0"
result=0
output=$("$SCRIPT" "$plan_over") || result=$?
assert_eq "0" "$result" "exit code"

set_test "content status not_estimated keeps exit 0"
result=0
output=$("$SCRIPT" "$plan_none") || result=$?
assert_eq "0" "$result" "exit code"

# ─────────────────────────────────────────────────────────────────────────────
# T007 — Greenfield + dedupe (FR-006, FR-008 no-double-counting)
#   all-NEW block          -> greenfield true, thresholds scaled x1.5 (600/1200)
#   NEW+MODIFIED mix        -> greenfield false, thresholds 400/800
#   path listed twice       -> counted ONCE in declared_files.* and projected
#   same path NEW+MODIFIED  -> de-duplicated to MODIFIED -> NOT greenfield
# ─────────────────────────────────────────────────────────────────────────────
section "T007 greenfield + dedupe"

# --- all-NEW: greenfield true, thresholds scaled x1.5
plan_green="$FIXTURE_DIR/plan-green.md"
cat > "$plan_green" <<'EOF'
## Declared File Operations

- NEW src/g1.ts
- NEW src/g2.ts
EOF

set_test "all-NEW greenfield true"
output=$("$SCRIPT" "$plan_green")
assert_json_field "$output" "greenfield" "True"

set_test "all-NEW warn threshold scaled to 600"
assert_json_field "$output" "thresholds.warn" "600"

set_test "all-NEW block threshold scaled to 1200"
assert_json_field "$output" "thresholds.block" "1200"

set_test "all-NEW base_warn unscaled 400"
assert_json_field "$output" "thresholds.base_warn" "400"

set_test "all-NEW base_block unscaled 800"
assert_json_field "$output" "thresholds.base_block" "800"

set_test "all-NEW greenfield_multiplier 1.5"
assert_json_field "$output" "thresholds.greenfield_multiplier" "1.5"

# --- NEW+MODIFIED mix: greenfield false, thresholds unscaled
plan_mix="$FIXTURE_DIR/plan-mix.md"
cat > "$plan_mix" <<'EOF'
## Declared File Operations

- NEW src/m1.ts
- MODIFIED src/m2.ts
EOF

set_test "NEW+MODIFIED mix greenfield false"
output=$("$SCRIPT" "$plan_mix")
assert_json_field "$output" "greenfield" "False"

set_test "NEW+MODIFIED mix warn threshold unscaled 400"
assert_json_field "$output" "thresholds.warn" "400"

set_test "NEW+MODIFIED mix block threshold unscaled 800"
assert_json_field "$output" "thresholds.block" "800"

# --- dedupe: same path listed twice (both NEW) -> counted ONCE
plan_dup="$FIXTURE_DIR/plan-dup.md"
cat > "$plan_dup" <<'EOF'
## Declared File Operations

- NEW src/dup.ts
- NEW src/dup.ts
EOF

set_test "duplicate path total_entries == 1"
output=$("$SCRIPT" "$plan_dup")
assert_json_field "$output" "declared_files.total_entries" "1"

set_test "duplicate path production == 1"
assert_json_field "$output" "declared_files.production" "1"

set_test "duplicate path projected == 40 (counted once)"
assert_json_field "$output" "projected" "40"

set_test "duplicate path (both NEW) greenfield true"
assert_json_field "$output" "greenfield" "True"

# --- dedupe conflict: same path as NEW and MODIFIED -> dedup to MODIFIED -> NOT greenfield
plan_conflict="$FIXTURE_DIR/plan-conflict.md"
cat > "$plan_conflict" <<'EOF'
## Declared File Operations

- NEW src/conflict.ts
- MODIFIED src/conflict.ts
EOF

set_test "NEW+MODIFIED same path total_entries == 1"
output=$("$SCRIPT" "$plan_conflict")
assert_json_field "$output" "declared_files.total_entries" "1"

set_test "NEW+MODIFIED same path counts as modified == 1"
assert_json_field "$output" "declared_files.modified" "1"

set_test "NEW+MODIFIED same path new == 0"
assert_json_field "$output" "declared_files.new" "0"

set_test "NEW+MODIFIED same path greenfield false (fail-safe to MODIFIED)"
assert_json_field "$output" "greenfield" "False"

# ── PR #119 review (PRRT_kwDORvqw086HoVpq): section-scoping ───────────────────
# Contract: no `## Declared File Operations` heading -> not_estimated. A grammar-
# matching `- NEW ...` bullet that lives OUTSIDE that section (no heading at all,
# or under a different heading) must NOT be counted.
plan_noheading="$FIXTURE_DIR/plan-noheading.md"
cat > "$plan_noheading" <<'EOF'
# Implementation Plan

Some prose. An unrelated checklist that happens to match the entry grammar:

- NEW src/should_not_count.ts
- MODIFIED src/also_not.ts
EOF

set_test "no Declared File Operations heading -> not_estimated despite stray NEW bullets"
output=$("$SCRIPT" "$plan_noheading")
assert_json_field "$output" "status" "not_estimated"

set_test "no heading -> projected null"
assert_json_field "$output" "projected" "None"

set_test "no heading -> total_entries == 0 (stray bullets not counted)"
assert_json_field "$output" "declared_files.total_entries" "0"

# A heading IS present, but a stray entry after a later h2 is out of section.
plan_outofsection="$FIXTURE_DIR/plan-outofsection.md"
cat > "$plan_outofsection" <<'EOF'
## Declared File Operations

- NEW src/counted.ts

## Notes

- NEW src/out_of_section.ts
EOF

set_test "entry after a later h2 is out of section (total_entries == 1)"
output=$("$SCRIPT" "$plan_outofsection")
assert_json_field "$output" "declared_files.total_entries" "1"

set_test "out-of-section entry not counted (projected 40, one file)"
assert_json_field "$output" "projected" "40"

# ── PR #119 review (PRRT_kwDORvqw086HoVps): .process/ exclusion parity with gate ─
# is_excluded_generated carries the gate's `*/.process/*` arm so the estimator and
# gate agree: a production-ish file declared under specs/<NNN>/.process/ is excluded
# from the production count; production code elsewhere is counted.
plan_process="$FIXTURE_DIR/plan-process.md"
cat > "$plan_process" <<'EOF'
## Declared File Operations

- NEW src/real.ts
- NEW specs/007-demo/.process/generated.ts
EOF

set_test ".process/ production file excluded (production == 1, not 2)"
output=$("$SCRIPT" "$plan_process")
assert_json_field "$output" "declared_files.production" "1"

set_test ".process/ production file excluded (projected 40, not 80)"
assert_json_field "$output" "projected" "40"

# A dir merely ENDING in .process (foo.process/) is NOT the exhaust dir → counted.
plan_endsprocess="$FIXTURE_DIR/plan-endsprocess.md"
cat > "$plan_endsprocess" <<'EOF'
## Declared File Operations

- NEW src/foo.process/mod.ts
EOF

set_test "dir ending in .process (foo.process/) is not excluded (production == 1)"
output=$("$SCRIPT" "$plan_endsprocess")
assert_json_field "$output" "declared_files.production" "1"

test_summary
