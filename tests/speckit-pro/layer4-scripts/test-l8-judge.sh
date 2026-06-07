#!/usr/bin/env bash
# test-l8-judge.sh — Unit tests for the Layer 8 semantic-equivalent judge.
#
# The judge wraps `claude -p --json-schema` with a constrained verdict
# schema. CI must never make a live LLM call from Layer 4 (the existing
# test-transcript-helpers.sh comment is explicit: "Tests run against
# committed synthetic fixtures so they are deterministic and never require
# live LLM calls.") — so this test substitutes a fake claude binary via
# the CLAUDE_BIN env var, which the judge module honors.
#
# Each case writes a one-off shim, exports CLAUDE_BIN to point at it, and
# exercises semantic_equivalent_judge directly.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"
# shellcheck source=../../tests/layer8-parity/lib/judge.sh
source "$PLUGIN_ROOT/../tests/speckit-pro/layer8-parity/lib/judge.sh"

SHIM_DIR=$(mktemp -d)
trap 'rm -rf "$SHIM_DIR"' EXIT

# write_shim <name> <stdout-payload-or-cmd>
# The shim is a tiny bash script invoked in place of `claude`. We don't
# care what flags the judge passes — we only need to control stdout/exit.
write_shim() {
  local name="$1" body="$2"
  local path="$SHIM_DIR/$name"
  cat >"$path" <<EOF
#!/usr/bin/env bash
$body
EOF
  chmod +x "$path"
  echo "$path"
}

# ─────────────────────────────────────────
section "Happy path: EQUIVALENT verdict"
# ─────────────────────────────────────────

set_test "judge returns EQUIVALENT JSON when shim emits canned EQUIVALENT"
shim=$(write_shim "claude-eq" 'echo "{\"verdict\":\"EQUIVALENT\",\"reason\":\"both list the same findings\"}"')
result=0
output=$(CLAUDE_BIN="$shim" semantic_equivalent_judge "value A" "value B" "rationale") || result=$?
assert_eq "0" "$result" "exit code"
verdict=$(echo "$output" | jq -r '.verdict')
assert_eq "EQUIVALENT" "$verdict"
reason=$(echo "$output" | jq -r '.reason')
assert_contains "$reason" "same findings"

# ─────────────────────────────────────────
section "NOT_EQUIVALENT verdict"
# ─────────────────────────────────────────

set_test "judge returns NOT_EQUIVALENT JSON when shim emits NOT_EQUIVALENT"
shim=$(write_shim "claude-neq" 'echo "{\"verdict\":\"NOT_EQUIVALENT\",\"reason\":\"A flagged a regression that B did not\"}"')
result=0
output=$(CLAUDE_BIN="$shim" semantic_equivalent_judge "A" "B" "rat") || result=$?
assert_eq "0" "$result" "exit code"
verdict=$(echo "$output" | jq -r '.verdict')
assert_eq "NOT_EQUIVALENT" "$verdict"

# ─────────────────────────────────────────
section "Malformed JSON → exit 1"
# ─────────────────────────────────────────

set_test "judge rejects non-JSON stdout"
shim=$(write_shim "claude-bad" 'echo "this is not JSON at all"')
result=0
output=$(CLAUDE_BIN="$shim" semantic_equivalent_judge "A" "B" "rat" 2>&1) || result=$?
assert_eq "1" "$result" "exit code"

set_test "judge rejects JSON missing 'verdict'"
shim=$(write_shim "claude-missing-verdict" 'echo "{\"reason\":\"x\"}"')
result=0
output=$(CLAUDE_BIN="$shim" semantic_equivalent_judge "A" "B" "rat" 2>&1) || result=$?
assert_eq "1" "$result" "exit code"

set_test "judge rejects JSON with unknown verdict value"
shim=$(write_shim "claude-bad-verdict" 'echo "{\"verdict\":\"MAYBE\",\"reason\":\"x\"}"')
result=0
output=$(CLAUDE_BIN="$shim" semantic_equivalent_judge "A" "B" "rat" 2>&1) || result=$?
assert_eq "1" "$result" "exit code"

# ─────────────────────────────────────────
section "Subprocess failure → exit 1"
# ─────────────────────────────────────────

set_test "judge exits 1 when shim exits non-zero"
shim=$(write_shim "claude-fail" 'echo "{\"verdict\":\"EQUIVALENT\",\"reason\":\"x\"}"; exit 42')
result=0
output=$(CLAUDE_BIN="$shim" semantic_equivalent_judge "A" "B" "rat" 2>&1) || result=$?
assert_eq "1" "$result" "exit code"

set_test "judge exits 1 when CLAUDE_BIN points to a missing executable"
result=0
output=$(CLAUDE_BIN="/no/such/path/that/exists/$$" semantic_equivalent_judge "A" "B" "rat" 2>&1) || result=$?
assert_eq "1" "$result" "exit code"

# ─────────────────────────────────────────
section "Timeout"
# ─────────────────────────────────────────

set_test "judge exits 1 when shim exceeds L8_JUDGE_TIMEOUT_S"
# shim sleeps longer than the timeout; the wrapping `timeout(1)` should
# kill it and the judge should return exit 1.
shim=$(write_shim "claude-hang" 'sleep 5; echo "{\"verdict\":\"EQUIVALENT\",\"reason\":\"x\"}"')
result=0
output=$(L8_JUDGE_TIMEOUT_S=1 CLAUDE_BIN="$shim" semantic_equivalent_judge "A" "B" "rat" 2>&1) || result=$?
assert_eq "1" "$result" "exit code"

# ─────────────────────────────────────────
section "Prompt content reaches the shim"
# ─────────────────────────────────────────

set_test "shim sees the rationale + both values on stdin"
# This shim captures stdin to a temp file and emits a fixed verdict.
captured="$SHIM_DIR/captured-prompt.txt"
shim=$(write_shim "claude-capture" "cat > \"$captured\"; echo '{\"verdict\":\"EQUIVALENT\",\"reason\":\"ok\"}'")
CLAUDE_BIN="$shim" semantic_equivalent_judge \
  "doctor clean; review approved" \
  "doctor passes; reviewer signed off" \
  "Allow paraphrase but require semantic equivalence" >/dev/null
assert_file_exists "$captured"
prompt_content=$(cat "$captured")
assert_contains "$prompt_content" "Allow paraphrase but require semantic equivalence"
assert_contains "$prompt_content" "doctor clean; review approved"
assert_contains "$prompt_content" "doctor passes; reviewer signed off"
assert_contains "$prompt_content" "EQUIVALENT"  # decision protocol enumerates the choices

test_summary
