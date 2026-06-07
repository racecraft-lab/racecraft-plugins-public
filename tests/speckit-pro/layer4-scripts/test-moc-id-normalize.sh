#!/usr/bin/env bash
# test-moc-id-normalize.sh — Unit tests for the shared namespace-aware ID normalizer
#
# Asserts the canonical grammar table from
# specs/prsg-002-moc-templates/contracts/id-normalization-grammar.md.
# Covers FR-017 (namespace-aware normalization) and FR-018 (opaque
# whole-segment comparison; no [0-9]+[a-z]* sub-parse).
#
# Contract exercised:
#   moc_normalize <value>        → echoes "<namespace> <number-suffix>"
#   moc_id_match  <value-a> <b>  → exit 0 on match, 1 on no-match

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
# The canonical normalizer ships inside the plugin (FR-004); the test tree does not
# ship, so source it from its shipped home, not from this test tree's lib/.
source "$(dirname "$0")/../../../speckit-pro/skills/speckit-autopilot/scripts/lib/moc-id-normalize.sh"

# ─────────────────────────────────────────
section "Normalize: value → (namespace, number-suffix)"
# ─────────────────────────────────────────

set_test "prsg-002-moc-templates → (prsg, 002)"
assert_eq "prsg 002" "$(moc_normalize "prsg-002-moc-templates")"

set_test "PRSG-002 → (prsg, 002) [lowercased]"
assert_eq "prsg 002" "$(moc_normalize "PRSG-002")"

set_test "002-pr-checks-workflow → (spec, 002) [no alpha prefix]"
assert_eq "spec 002" "$(moc_normalize "002-pr-checks-workflow")"

set_test "SPEC-002 → (spec, 002)"
assert_eq "spec 002" "$(moc_normalize "SPEC-002")"

set_test "006a-uat-skeleton → (spec, 006a)"
assert_eq "spec 006a" "$(moc_normalize "006a-uat-skeleton")"

set_test "013a → (spec, 013a) [whole segment]"
assert_eq "spec 013a" "$(moc_normalize "013a")"

set_test "013a1 → (spec, 013a1) [whole segment, not truncated to 013a]"
assert_eq "spec 013a1" "$(moc_normalize "013a1")"

# ─────────────────────────────────────────
section "Match: requires BOTH namespace AND exact-segment number-suffix"
# ─────────────────────────────────────────

set_test "PRSG-002 ↔ prsg-002-moc-templates → MATCH"
assert_exit_code 0 moc_id_match "PRSG-002" "prsg-002-moc-templates"

set_test "PRSG-002 ↔ SPEC-002 → NO MATCH (different namespace)"
assert_exit_code 1 moc_id_match "PRSG-002" "SPEC-002"

set_test "PRSG-002 ↔ 002-pr-checks-workflow → NO MATCH (different namespace)"
assert_exit_code 1 moc_id_match "PRSG-002" "002-pr-checks-workflow"

set_test "013a ↔ 013a1 → NO MATCH (different number-suffix segment)"
assert_exit_code 1 moc_id_match "013a" "013a1"

set_test "013a1 ↔ 013a → NO MATCH (symmetric near-miss)"
assert_exit_code 1 moc_id_match "013a1" "013a"

# ─────────────────────────────────────────
section "Totality: degenerate inputs yield an empty number-suffix"
# ─────────────────────────────────────────
# Per the grammar contract, a missing/empty selected number-suffix segment is
# the empty string. An empty number-suffix can never byte-equal a well-formed
# directory's number-suffix, so a degenerate value never yields a false match.

set_test "empty value → empty number-suffix (spec, '')"
assert_eq "spec " "$(moc_normalize "")"

set_test "lone '-' → empty number-suffix (spec, '')"
assert_eq "spec " "$(moc_normalize "-")"

set_test "all-alpha 'prsg' → empty number-suffix (prsg, '')"
assert_eq "prsg " "$(moc_normalize "prsg")"

set_test "trailing-dash 'prsg-' → empty number-suffix (prsg, '')"
assert_eq "prsg " "$(moc_normalize "prsg-")"

set_test "leading-dash '-002-x' → empty first segment ⇒ (spec, '')"
# Leading dash: first segment is empty, which is NOT all-alpha, so
# namespace=spec and number-suffix=the (empty) first segment.
assert_eq "spec " "$(moc_normalize "-002-x")"

# ─────────────────────────────────────────
section "Totality: degenerate values never match a well-formed directory"
# ─────────────────────────────────────────

set_test "empty ↔ prsg-002-moc-templates → NO MATCH"
assert_exit_code 1 moc_id_match "" "prsg-002-moc-templates"

set_test "lone '-' ↔ 002-pr-checks-workflow → NO MATCH"
assert_exit_code 1 moc_id_match "-" "002-pr-checks-workflow"

set_test "all-alpha 'prsg' ↔ prsg-002-moc-templates → NO MATCH (empty suffix)"
assert_exit_code 1 moc_id_match "prsg" "prsg-002-moc-templates"

set_test "trailing-dash 'prsg-' ↔ prsg-002-moc-templates → NO MATCH (empty suffix)"
assert_exit_code 1 moc_id_match "prsg-" "prsg-002-moc-templates"

set_test "leading-dash '-002-x' ↔ 002-pr-checks-workflow → NO MATCH (empty suffix)"
assert_exit_code 1 moc_id_match "-002-x" "002-pr-checks-workflow"

test_summary
