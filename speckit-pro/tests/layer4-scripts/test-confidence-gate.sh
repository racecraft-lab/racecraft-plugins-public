#!/usr/bin/env bash
# test-confidence-gate.sh — Unit tests for confidence-gate.sh
#
# Covers: PASS, FAIL advisory, FAIL strict, NO_DATA, boundary 0.90,
# --threshold override, --mode override, --threshold=value form,
# multiple confidence lines (use most recent), malformed input,
# missing file, missing args, invalid mode, invalid threshold.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$PLUGIN_ROOT/skills/speckit-autopilot/scripts/confidence-gate.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

# Helper: write a synthetic workflow file with a confidence emit.
write_emit() {
  local file="$1" composite="$2"
  cat > "$file" <<EOF
## Consensus Resolution Log

| # | Type | Outcome |
|---|------|---------|
| 1 | Finding | 3/3 |

📊 Confidence: ${composite}

- Task understanding: 0.95
- Approach clarity: 0.90
- Requirements alignment: 0.92
- Risk assessment: 0.88
- Completeness: 0.95
EOF
}

# ─────────────────────────────────────────
section "Usage and input validation"
# ─────────────────────────────────────────

set_test "No arguments → exit 1"
result=0
output=$("$SCRIPT" 2>/dev/null) || result=$?
assert_eq "1" "$result" "exit code"

set_test "Missing workflow file → exit 1"
result=0
output=$("$SCRIPT" "$FIXTURE_DIR/does-not-exist.md" 2>/dev/null) || result=$?
assert_eq "1" "$result" "exit code"

set_test "Invalid --mode → exit 1"
file="$FIXTURE_DIR/empty.md" && : > "$file"
result=0
output=$("$SCRIPT" "$file" --mode chaos 2>/dev/null) || result=$?
assert_eq "1" "$result" "exit code"

set_test "Invalid --threshold → exit 1"
result=0
output=$("$SCRIPT" "$file" --threshold abc 2>/dev/null) || result=$?
assert_eq "1" "$result" "exit code"

set_test "Unknown long option → exit 1"
result=0
output=$("$SCRIPT" "$file" --frob 2>/dev/null) || result=$?
assert_eq "1" "$result" "exit code"

# ─────────────────────────────────────────
section "PASS — composite at or above threshold"
# ─────────────────────────────────────────

set_test "Composite 0.92 default threshold → exit 0"
file="$FIXTURE_DIR/pass-92.md" && write_emit "$file" "0.92"
result=0
output=$("$SCRIPT" "$file") || result=$?
assert_eq "0" "$result" "exit code"

set_test "PASS JSON pass field is true"
assert_json_field "$output" "pass" "True"

set_test "PASS JSON composite is 0.92"
assert_json_field "$output" "composite" "0.92"

set_test "PASS JSON recommended_action is proceed"
assert_json_field "$output" "recommended_action" "proceed"

set_test "PASS JSON criteria.task_understanding is 0.95"
assert_json_field "$output" "criteria.task_understanding" "0.95"

set_test "Boundary 0.90 default threshold → exit 0 (>= comparison)"
file="$FIXTURE_DIR/boundary.md" && write_emit "$file" "0.90"
result=0
output=$("$SCRIPT" "$file") || result=$?
assert_eq "0" "$result" "exit code"

set_test "Boundary 0.90 JSON pass field is true"
assert_json_field "$output" "pass" "True"

# ─────────────────────────────────────────
section "FAIL advisory — composite below threshold, mode=advisory (default)"
# ─────────────────────────────────────────

set_test "Composite 0.85 → exit 2"
file="$FIXTURE_DIR/fail-85.md" && write_emit "$file" "0.85"
result=0
output=$("$SCRIPT" "$file") || result=$?
assert_eq "2" "$result" "exit code"

set_test "FAIL advisory JSON pass field is false"
assert_json_field "$output" "pass" "False"

set_test "FAIL advisory JSON composite is 0.85"
assert_json_field "$output" "composite" "0.85"

set_test "FAIL advisory JSON recommended_action is continue_with_warning"
assert_json_field "$output" "recommended_action" "continue_with_warning"

set_test "FAIL advisory JSON mode is advisory"
assert_json_field "$output" "mode" "advisory"

# ─────────────────────────────────────────
section "FAIL strict — composite below threshold, mode=strict"
# ─────────────────────────────────────────

set_test "Composite 0.85 strict → exit 2"
result=0
output=$("$SCRIPT" "$file" --mode strict) || result=$?
assert_eq "2" "$result" "exit code"

set_test "FAIL strict JSON recommended_action is stop"
assert_json_field "$output" "recommended_action" "stop"

set_test "FAIL strict JSON mode is strict"
assert_json_field "$output" "mode" "strict"

set_test "FAIL strict --mode=value form also works"
result=0
output=$("$SCRIPT" "$file" --mode=strict) || result=$?
assert_eq "2" "$result" "exit code"
assert_json_field "$output" "recommended_action" "stop"

# ─────────────────────────────────────────
section "Threshold override"
# ─────────────────────────────────────────

set_test "Composite 0.85, --threshold 0.80 → exit 0 (PASS)"
result=0
output=$("$SCRIPT" "$file" --threshold 0.80) || result=$?
assert_eq "0" "$result" "exit code"

set_test "--threshold=0.80 form also works"
result=0
output=$("$SCRIPT" "$file" --threshold=0.80) || result=$?
assert_eq "0" "$result" "exit code"

set_test "Composite 0.92, --threshold 0.95 → exit 2 (FAIL)"
file="$FIXTURE_DIR/raised-bar.md" && write_emit "$file" "0.92"
result=0
output=$("$SCRIPT" "$file" --threshold 0.95) || result=$?
assert_eq "2" "$result" "exit code"

set_test "Threshold JSON reflects custom value"
assert_json_field "$output" "threshold" "0.95"

# ─────────────────────────────────────────
section "NO_DATA — no confidence emit found"
# ─────────────────────────────────────────

set_test "Empty file → exit 1"
file="$FIXTURE_DIR/no-emit.md"
printf 'Just a workflow draft. No synthesizer block here.\n' > "$file"
result=0
output=$("$SCRIPT" "$file") || result=$?
assert_eq "1" "$result" "exit code"

set_test "NO_DATA JSON recommended_action is soft_skip"
assert_json_field "$output" "recommended_action" "soft_skip"

set_test "NO_DATA JSON composite is null"
assert_json_field "$output" "composite" "None"

set_test "Malformed emit (not on its own line) → exit 1"
file="$FIXTURE_DIR/malformed.md"
printf 'Inline 📊 Confidence: 0.92 in a sentence does not count.\n' > "$file"
result=0
output=$("$SCRIPT" "$file") || result=$?
assert_eq "1" "$result" "exit code"

# ─────────────────────────────────────────
section "Multiple emits — most recent wins"
# ─────────────────────────────────────────

set_test "Two emits 0.85 then 0.95 → uses 0.95 (PASS)"
file="$FIXTURE_DIR/multi.md"
cat > "$file" <<'EOF'
## First pass

📊 Confidence: 0.85

- Task understanding: 0.80
- Approach clarity: 0.85
- Requirements alignment: 0.85
- Risk assessment: 0.85
- Completeness: 0.90

## Second pass (after remediation)

📊 Confidence: 0.95

- Task understanding: 0.95
- Approach clarity: 0.95
- Requirements alignment: 0.95
- Risk assessment: 0.95
- Completeness: 0.95
EOF
result=0
output=$("$SCRIPT" "$file") || result=$?
assert_eq "0" "$result" "exit code"
assert_json_field "$output" "composite" "0.95"
assert_json_field "$output" "criteria.task_understanding" "0.95"

# ─────────────────────────────────────────
section "CONFIDENCE_GATE_INPUT env override"
# ─────────────────────────────────────────

set_test "Env var supplies workflow file when no positional arg"
file="$FIXTURE_DIR/env-input.md" && write_emit "$file" "0.92"
result=0
output=$(CONFIDENCE_GATE_INPUT="$file" "$SCRIPT") || result=$?
assert_eq "0" "$result" "exit code"
assert_json_field "$output" "composite" "0.92"

test_summary
