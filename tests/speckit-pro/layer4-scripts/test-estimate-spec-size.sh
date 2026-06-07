#!/usr/bin/env bash
# test-estimate-spec-size.sh — Unit tests for estimate-spec-size.sh
#
# Pins the deterministic estimator contract (contracts/estimate-spec-size.md):
#   - byte-identical stdout for repeated identical inputs (determinism, FR-007)
#   - at-ceiling boundary: estimated_loc == ceiling → ok; strictly over → warn
#     (FR-006, FR-008)
#   - spike triple: --spike → {"estimated_loc":0,"suggested_slices":1,"status":"ok"}
#     (FR-017)
#   - bad-input pin: missing/zero/negative/malformed numeric signals normalize
#     to 0; status follows the at-ceiling rule on the result; non-crashing
#     (FR-016)
#   - status is never any value other than ok|warn
#   - advisory-only: exit 0 even on warn (FR-011)
#
# Input→expected-JSON fixtures live under fixtures/estimate-spec-size/ as
# <name>.args (one line of CLI arguments) + <name>.json (expected compact stdout).

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"
SCRIPT="$PLUGIN_ROOT/skills/speckit-coach/scripts/estimate-spec-size.sh"
FIXTURE_DIR="$(cd "$(dirname "$0")" && pwd)/fixtures/estimate-spec-size"

# Run the estimator with a raw argument string (word-split intentionally, the
# args fixtures are plain flags). Prints stdout and RETURNS the script's exit
# code so callers can guard with `|| rc=$?` (the test-validate-gate.sh pattern).
# Guarding at the call site is what keeps a missing/failing script producing
# clean assertion failures (RED) instead of aborting the test under set -e.
run_est() {
  local args="$1"
  # shellcheck disable=SC2086
  "$SCRIPT" $args 2>/dev/null
}

# ─────────────────────────────────────────
section "Fixtures: input → expected compact JSON"
# ─────────────────────────────────────────

for args_file in "$FIXTURE_DIR"/*.args; do
  name="$(basename "$args_file" .args)"
  json_file="$FIXTURE_DIR/$name.json"

  # Read the single argument line (may be empty for the all-absent case).
  args="$(head -n1 "$args_file" 2>/dev/null || true)"
  # Expected stdout, trailing newline trimmed for a byte-clean comparison.
  expected="$(cat "$json_file" 2>/dev/null)"

  rc=0
  output="$(run_est "$args")" || rc=$?

  set_test "fixture '$name' → exit 0"
  assert_eq "0" "$rc" "exit code (advisory-only: never blocks)"

  set_test "fixture '$name' → expected JSON"
  assert_eq "$expected" "$output" "stdout"
done

# ─────────────────────────────────────────
section "Determinism: byte-identical output for identical inputs (FR-007)"
# ─────────────────────────────────────────

set_test "repeated identical inputs → byte-identical stdout"
out1="$(run_est "--user-stories 2 --files 3 --frs 4" || true)"
out2="$(run_est "--user-stories 2 --files 3 --frs 4" || true)"
assert_eq "$out1" "$out2" "two runs must match byte-for-byte"

set_test "second determinism sample (over-ceiling) → byte-identical stdout"
a="$(run_est "--files 11" || true)"
b="$(run_est "--files 11" || true)"
assert_eq "$a" "$b" "two runs must match byte-for-byte"

# ─────────────────────────────────────────
section "At-ceiling boundary (FR-006, FR-008)"
# ─────────────────────────────────────────

set_test "estimated_loc == ceiling → status ok"
output="$(run_est "--files 10" || true)"
assert_json_field "$output" "estimated_loc" "400"
assert_json_field "$output" "status" "ok"

set_test "strictly over ceiling → status warn"
output="$(run_est "--files 11" || true)"
assert_json_field "$output" "status" "warn"

# ─────────────────────────────────────────
section "Spike triple (FR-017)"
# ─────────────────────────────────────────

set_test "--spike → {estimated_loc:0, suggested_slices:1, status:ok}"
output="$(run_est "--spike" || true)"
assert_eq '{"estimated_loc":0,"suggested_slices":1,"status":"ok"}' "$output" "spike triple"

set_test "--spike overrides large signals (spike precedence)"
output="$(run_est "--user-stories 99 --files 99 --frs 99 --spike" || true)"
assert_eq '{"estimated_loc":0,"suggested_slices":1,"status":"ok"}' "$output" "spike triple"

# ─────────────────────────────────────────
section "Robustness: bad/missing signals → 0, non-crashing (FR-016)"
# ─────────────────────────────────────────

set_test "no arguments → estimated_loc 0, status ok, exit 0"
rc=0
output="$(run_est "")" || rc=$?
assert_eq "0" "$rc" "exit code"
assert_json_field "$output" "estimated_loc" "0"
assert_json_field "$output" "status" "ok"

set_test "malformed/negative/decimal signals normalize to 0"
rc=0
output="$(run_est "--user-stories abc --files -5 --frs 3.5")" || rc=$?
assert_eq "0" "$rc" "exit code (never crash)"
assert_json_field "$output" "estimated_loc" "0"
assert_json_field "$output" "status" "ok"

set_test "mixed valid + bad keeps valid signals"
output="$(run_est "--user-stories 4 --files abc --frs -2" || true)"
assert_json_field "$output" "estimated_loc" "100"
assert_json_field "$output" "status" "ok"

# ─────────────────────────────────────────
section "status enum is exactly ok|warn (never a third value)"
# ─────────────────────────────────────────

# Sweep a representative spread of inputs and assert status is always ok or warn.
set_test "status is always ok or warn across an input sweep"
status_violation=""
for args in \
  "" \
  "--files 10" \
  "--files 11" \
  "--files 20" \
  "--user-stories 2 --files 3 --frs 4" \
  "--files 10 --new-vs-modify modify" \
  "--spike" \
  "--user-stories 99 --files 99 --frs 99 --spike" \
  "--user-stories abc --files -5 --frs 3.5" \
  "--user-stories 4 --files abc --frs -2"; do
  s="$(run_est "$args" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("status",""))' 2>/dev/null || true)"
  if [ "$s" != "ok" ] && [ "$s" != "warn" ]; then
    status_violation="args='$args' status='$s'"
    break
  fi
done
assert_eq "" "$status_violation" "every status must be ok or warn"

# ─────────────────────────────────────────
section "suggested_slices = ceil(estimated_loc / ceiling), min 1"
# ─────────────────────────────────────────

set_test "under ceiling → 1 slice"
output="$(run_est "--user-stories 2 --files 3 --frs 4" || true)"
assert_json_field "$output" "suggested_slices" "1"

set_test "440 LOC → 2 slices"
output="$(run_est "--files 11" || true)"
assert_json_field "$output" "suggested_slices" "2"

set_test "800 LOC → 2 slices"
output="$(run_est "--files 20" || true)"
assert_json_field "$output" "suggested_slices" "2"

test_summary
