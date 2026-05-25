#!/usr/bin/env bash
# test-l8-extractors.sh — Unit tests for Layer 8 section/table extractors.
#
# Exercises extract_section, extract_table_row_count, and extract_table_column
# directly against synthetic workflow.md fixtures. CI never exercises these
# via the L8 runner (dry-run skips compare_field; --live mode is opt-in only),
# so this is the only deterministic check on the extractor code.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=../../tests/layer8-parity/lib/extractors.sh
source "$PLUGIN_ROOT/tests/layer8-parity/lib/extractors.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

# Fixture: a representative workflow.md with multiple H2 sections, tables
# of varying row counts, and an H3 subsection nested under one H2.
FIXTURE="$FIXTURE_DIR/workflow.md"
cat >"$FIXTURE" <<'EOF'
# Workflow Overview

| Phase | Status | Notes |
|-------|--------|-------|
| Specify | PASS | ok |
| Plan | FAIL | bad |

## Post-Implementation Checklist

| Task | Status | Findings |
|------|--------|----------|
| 10 | PASS | doctor clean |
| 11 | PASS | review approved |
| 12 | FAIL | regression in foo |

### Notes Subsection

This H3 must remain inside the H2 body.

## Consensus Resolution Log

| Item | Round | Result |
|------|-------|--------|
| Q1 | 1 | resolved |
| Q2 | 2 | resolved |
EOF

# ─────────────────────────────────────────
section "extract_section: H2 bounds"
# ─────────────────────────────────────────

set_test "stops at next H2, includes H3 subsection inside body"
output=$(extract_section "$FIXTURE" "Post-Implementation Checklist")
assert_contains "$output" "regression in foo"
assert_contains "$output" "### Notes Subsection"
assert_contains "$output" "This H3 must remain inside"
assert_not_contains "$output" "Consensus Resolution Log"

set_test "missing section emits nothing (rc=0)"
output=$(extract_section "$FIXTURE" "Nonexistent Section")
assert_eq "" "$output"

# ─────────────────────────────────────────
section "extract_table_row_count"
# ─────────────────────────────────────────

set_test "first H2 section (Post-Implementation Checklist) → 3 data rows"
result=$(extract_table_row_count "$FIXTURE" "Post-Implementation Checklist")
assert_eq "3" "$result"

set_test "second H2 section (Consensus Resolution Log) → 2 data rows"
result=$(extract_table_row_count "$FIXTURE" "Consensus Resolution Log")
assert_eq "2" "$result"

set_test "missing section returns non-zero exit code"
result=0
extract_table_row_count "$FIXTURE" "Nonexistent" >/dev/null || result=$?
assert_eq "1" "$result"

# ─────────────────────────────────────────
section "extract_table_column"
# ─────────────────────────────────────────

set_test "Status column → PASS\\nPASS\\nFAIL (newline-separated)"
result=$(extract_table_column "$FIXTURE" "Post-Implementation Checklist" "Status")
expected=$(printf 'PASS\nPASS\nFAIL')
assert_eq "$expected" "$result"

set_test "Findings column preserves text"
result=$(extract_table_column "$FIXTURE" "Post-Implementation Checklist" "Findings")
assert_contains "$result" "doctor clean"
assert_contains "$result" "regression in foo"

set_test "case-sensitive — wrong casing returns non-zero"
result=0
extract_table_column "$FIXTURE" "Post-Implementation Checklist" "status" >/dev/null || result=$?
assert_eq "1" "$result"

set_test "Consensus Resolution Log: Result column → 2 values"
result=$(extract_table_column "$FIXTURE" "Consensus Resolution Log" "Result")
line_count=$(printf '%s\n' "$result" | wc -l | tr -d ' ')
assert_eq "2" "$line_count"

# ─────────────────────────────────────────
section "edge cases"
# ─────────────────────────────────────────

EMPTY_TABLE_FIXTURE="$FIXTURE_DIR/empty-table.md"
cat >"$EMPTY_TABLE_FIXTURE" <<'EOF'
## Empty Table

| A | B |
|---|---|

## Next Section
EOF

set_test "table with header + separator only → row_count=0"
result=$(extract_table_row_count "$EMPTY_TABLE_FIXTURE" "Empty Table")
assert_eq "0" "$result"

set_test "table with no data rows → column extract emits nothing"
result=$(extract_table_column "$EMPTY_TABLE_FIXTURE" "Empty Table" "A")
assert_eq "" "$result"

# ─────────────────────────────────────────
section "CLI entrypoint"
# ─────────────────────────────────────────

EXTRACTORS_SH="$PLUGIN_ROOT/tests/layer8-parity/lib/extractors.sh"

set_test "CLI subcommand row-count returns expected value"
result=$(bash "$EXTRACTORS_SH" row-count "$FIXTURE" "Post-Implementation Checklist")
assert_eq "3" "$result"

set_test "CLI subcommand column returns expected value"
result=$(bash "$EXTRACTORS_SH" column "$FIXTURE" "Post-Implementation Checklist" "Status")
assert_contains "$result" "PASS"
assert_contains "$result" "FAIL"

set_test "CLI invalid subcommand → exit 2"
result=0
bash "$EXTRACTORS_SH" bogus 2>/dev/null || result=$?
assert_eq "2" "$result"

test_summary
