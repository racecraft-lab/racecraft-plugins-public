#!/usr/bin/env bash
# test-aggregate-crl.sh — Unit tests for the Tier A re-evaluation
# trigger metric. Validates that aggregate-crl.sh parses workflow file
# Consensus Resolution Log tables correctly and computes the
# escape-hatch rate against the 10% threshold.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$PLUGIN_ROOT/skills/speckit-autopilot/scripts/aggregate-crl.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

# Helper: write a workflow file with the given CRL body and run the script.
make_workflow() {
  local path="$1"; shift
  cat > "$path" <<EOF
# Workflow

## Some prior section

### Consensus Resolution Log

| # | Type    | Question/Gap/Finding         | Categories         | Round | Outcome        | Resolution     | Analysts Used     |
|---|---------|------------------------------|--------------------|-------|----------------|----------------|-------------------|
$@

## Next section
EOF
}

run() { bash "$SCRIPT" "$1"; }
field() { printf '%s' "$1" | jq -r "$2"; }

# ─────────────────────────────────────────
section "Canonical CRL parsing"
# ─────────────────────────────────────────

set_test "5-row mixed CRL — total_items=5"
WF="$FIXTURE_DIR/canonical.md"
make_workflow "$WF" \
"| 1 | Clarify | Token format    | [domain]           | 1     | high-confidence| JWT 24h        | domain-researcher |
| 2 | Gap     | Rate thresholds | [codebase, domain] | 1     | both-agree     | Spec §4.2      | codebase + domain |
| 3 | Finding | Missing tests   | [ambiguous]        | 2     | 3/3            | T050           | All               |
| 4 | Clarify | Hashing scheme  | [codebase]         | 1→2   | escape-hatch   | argon2         | All               |
| 5 | Finding | OAuth callback  | [security]         | 2     | [HUMAN REVIEW] | Surfaced       | All               |"
out=$(run "$WF")
assert_eq "5" "$(field "$out" '.total_items')"

set_test "5-row mixed CRL — round_1=2"
assert_eq "2" "$(field "$out" '.round_1')"

set_test "5-row mixed CRL — round_2=3 (includes 1→2 escapes)"
assert_eq "3" "$(field "$out" '.round_2')"

set_test "5-row mixed CRL — escape_hatch=1"
assert_eq "1" "$(field "$out" '.escape_hatch')"

set_test "5-row mixed CRL — escape_rate_percent=20.0"
assert_eq "20.0" "$(field "$out" '.escape_rate_percent')"

set_test "5-row mixed CRL — exceeds_threshold=true (20% > 10%)"
assert_eq "true" "$(field "$out" '.exceeds_threshold')"

set_test "5-row mixed CRL — threshold_percent=10 (default)"
assert_eq "10" "$(field "$out" '.threshold_percent')"

# ─────────────────────────────────────────
section "Threshold edge cases"
# ─────────────────────────────────────────

set_test "Exactly 10% (1 escape / 10 items) → does NOT exceed (strict greater-than)"
WF="$FIXTURE_DIR/exactly-10.md"
rows=""
for i in 1 2 3 4 5 6 7 8 9; do
  rows+="| $i | Clarify | item$i | [codebase] | 1 | high-confidence | r$i | codebase-analyst |
"
done
rows+="| 10 | Clarify | item10 | [codebase] | 1→2 | escape-hatch | r10 | All |"
make_workflow "$WF" "$rows"
out=$(run "$WF")
assert_eq "10.0" "$(field "$out" '.escape_rate_percent')"
assert_eq "false" "$(field "$out" '.exceeds_threshold')"

set_test "1 escape / 9 items (~11.1%) → exceeds_threshold=true"
WF="$FIXTURE_DIR/over-10.md"
rows=""
for i in 1 2 3 4 5 6 7 8; do
  rows+="| $i | Clarify | item$i | [codebase] | 1 | high-confidence | r$i | codebase-analyst |
"
done
rows+="| 9 | Clarify | item9 | [codebase] | 1→2 | escape-hatch | r9 | All |"
make_workflow "$WF" "$rows"
out=$(run "$WF")
assert_eq "true" "$(field "$out" '.exceeds_threshold')"

set_test "Custom THRESHOLD_PERCENT=25 changes exceeds_threshold for 20% rate"
WF="$FIXTURE_DIR/custom-threshold.md"
make_workflow "$WF" \
"| 1 | Clarify | a | [codebase] | 1 | high-confidence | r1 | codebase-analyst |
| 2 | Clarify | b | [codebase] | 1 | high-confidence | r2 | codebase-analyst |
| 3 | Clarify | c | [codebase] | 1 | high-confidence | r3 | codebase-analyst |
| 4 | Clarify | d | [codebase] | 1 | high-confidence | r4 | codebase-analyst |
| 5 | Clarify | e | [codebase] | 1→2 | escape-hatch | r5 | All |"
out=$(THRESHOLD_PERCENT=25 bash "$SCRIPT" "$WF")
assert_eq "20.0" "$(field "$out" '.escape_rate_percent')"
assert_eq "false" "$(field "$out" '.exceeds_threshold')"
assert_eq "25" "$(field "$out" '.threshold_percent')"

# ─────────────────────────────────────────
section "Empty and missing CRL"
# ─────────────────────────────────────────

set_test "CRL section exists but has no rows → total_items=0"
WF="$FIXTURE_DIR/empty-crl.md"
make_workflow "$WF" ""
out=$(run "$WF")
assert_eq "0" "$(field "$out" '.total_items')"
assert_eq "false" "$(field "$out" '.exceeds_threshold')"

set_test "Empty CRL → escape_rate_percent=0"
assert_eq "0" "$(field "$out" '.escape_rate_percent')"

set_test "Workflow file with no CRL section → total_items=0 with note"
WF="$FIXTURE_DIR/no-crl.md"
cat > "$WF" <<EOF
# Workflow with no CRL

## Specify Results
Not relevant.
EOF
out=$(run "$WF")
assert_eq "0" "$(field "$out" '.total_items')"
assert_contains "$out" "No Consensus Resolution Log entries found."

# ─────────────────────────────────────────
section "Round-value variants"
# ─────────────────────────────────────────

set_test "Both '1→2' and '1->2' arrows count as Round-2 escape"
WF="$FIXTURE_DIR/arrow-variants.md"
make_workflow "$WF" \
"| 1 | Clarify | a | [codebase] | 1→2 | escape-hatch | r1 | All |
| 2 | Clarify | b | [codebase] | 1->2 | escape-hatch | r2 | All |
| 3 | Clarify | c | [codebase] | 1 | high-confidence | r3 | codebase-analyst |"
out=$(run "$WF")
assert_eq "3" "$(field "$out" '.total_items')"
assert_eq "1" "$(field "$out" '.round_1')"
assert_eq "2" "$(field "$out" '.round_2')"
assert_eq "2" "$(field "$out" '.escape_hatch')"

# ─────────────────────────────────────────
section "Output schema"
# ─────────────────────────────────────────

set_test "Output has all required fields"
WF="$FIXTURE_DIR/canonical.md"
make_workflow "$WF" \
"| 1 | Clarify | a | [codebase] | 1 | high-confidence | r | codebase-analyst |"
out=$(run "$WF")
for fname in file total_items round_1 round_2 escape_hatch escape_rate_percent threshold_percent exceeds_threshold; do
  set_test "Has field: $fname"
  assert_json_field_exists "$out" "$fname"
done

# ─────────────────────────────────────────
section "Usage and error handling"
# ─────────────────────────────────────────

set_test "No arguments → exit code 2"
assert_exit_code 2 bash "$SCRIPT"

set_test "Missing workflow file → exit code 3"
assert_exit_code 3 bash "$SCRIPT" "$FIXTURE_DIR/does-not-exist.md"

set_test "Missing workflow file → JSON error message"
out=$(bash "$SCRIPT" "$FIXTURE_DIR/does-not-exist.md" || true)
assert_contains "$out" "Workflow file not found"

# ─────────────────────────────────────────
test_summary
