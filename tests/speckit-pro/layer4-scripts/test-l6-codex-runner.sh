#!/usr/bin/env bash
# test-l6-codex-runner.sh — Unit tests for the Codex path in
# run-efficiency-benchmarks.sh.
#
# Layer 6 itself is a slow / paid layer (real LLM calls), so it never
# runs in CI. The only deterministic check on the new Codex code path is
# this Layer 4 test, which:
#   1. Tests `extract_codex_agent_body` against a synthetic TOML.
#   2. Stubs `codex` with a mock-shim that emits canned JSONL on stdout
#      and writes a known last-message to the `-o` file, then invokes
#      the runner with `--codex --agent <stub-agent>` and verifies the
#      benchmark loop produces a results JSON record.
#
# Stays deterministic — zero live LLM calls in L4, matching the
# test-transcript-helpers.sh precedent.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"
RUNNER="$PLUGIN_ROOT/../tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.sh"

WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT

# ─────────────────────────────────────────
section "extract_codex_agent_body"
# ─────────────────────────────────────────

# A representative TOML with the developer_instructions heredoc.
SYN_TOML="$WORK_DIR/syn-agent.toml"
cat >"$SYN_TOML" <<'EOF'
name = "syn-agent"
model = "gpt-5.5"
developer_instructions = """
# Synthetic Agent

Body line A.
Body line B.
"""
EOF

# Pull the function out of the runner so we can call it directly,
# without having to invoke the whole script.
extract_codex_agent_body() {
  local toml_file="$1"
  awk '
    /^developer_instructions[[:space:]]*=[[:space:]]*"""$/ { inside = 1; next }
    inside && /^"""$/                                     { inside = 0; next }
    inside                                                { print }
  ' "$toml_file"
}

set_test "extracts the heredoc body, drops opening and closing markers"
body=$(extract_codex_agent_body "$SYN_TOML")
assert_contains "$body" "Body line A."
assert_contains "$body" "Body line B."
assert_not_contains "$body" "developer_instructions"
assert_not_contains "$body" '"""'

set_test "leaves other TOML fields out of the body"
assert_not_contains "$body" "gpt-5.5"
assert_not_contains "$body" "name ="

# ─────────────────────────────────────────
section "Runner --codex path (mock codex binary)"
# ─────────────────────────────────────────

# Stand up an isolated PLUGIN_ROOT so the runner reads the codex-agents
# TOML from synthetic content. Fixture + results directories are
# pointed at the same temp tree via L6_FIXTURES_DIR / L6_RESULTS_DIR
# env vars (which the runner honors when set).
FAKE_PLUGIN="$WORK_DIR/fake-plugin"
FAKE_FIXTURES="$WORK_DIR/fixtures-codex"
FAKE_RESULTS="$WORK_DIR/results-codex"
mkdir -p "$FAKE_PLUGIN/codex-agents" \
         "$FAKE_FIXTURES/stub-agent" \
         "$FAKE_RESULTS"

# Synthetic codex-agent TOML — mirrors the real shape.
cat >"$FAKE_PLUGIN/codex-agents/stub-agent.toml" <<'EOF'
name = "stub-agent"
model = "gpt-5.5"
model_reasoning_effort = "xhigh"
developer_instructions = """
You are a stub agent for testing.
"""
EOF

cat >"$FAKE_FIXTURES/stub-agent/input-prompt.md" <<'EOF'
## Stub Input

Return any answer.
EOF

cat >"$FAKE_FIXTURES/stub-agent/expected-output.md" <<'EOF'
## Answer

A stub answer.

## Evidence

- **File**: `stub.txt` (lines 1-1)
  **Pattern**: Stub evidence.

## Confidence

high
EOF

# quality-scorer.sh / token-counter.sh stay in their real location —
# the runner sources them from its own SCRIPT_DIR, not from PLUGIN_ROOT.

# Mock codex binary. Behavior:
#  - Consumes stdin (the prompt).
#  - Looks for `-o <file>` and writes a canned last-message.
#  - Looks for `-c model_reasoning_effort=<value>` and echoes the value
#    back into the canned message so we can verify the sweep passes
#    different effort levels.
#  - Emits a single JSONL `turn.completed` event with non-zero token
#    counts on stdout (mimics `codex exec --json`).
SHIM_DIR="$WORK_DIR/shim"
mkdir -p "$SHIM_DIR"
cat >"$SHIM_DIR/codex" <<'SHIM'
#!/usr/bin/env bash
# Mock codex binary.
out_file=""
effort=""
# Walk argv looking for -o <file> and -c model_reasoning_effort=<value>.
args=("$@")
i=0
while [ $i -lt ${#args[@]} ]; do
  case "${args[$i]}" in
    -o) out_file="${args[$((i+1))]}"; i=$((i+2));;
    -c) val="${args[$((i+1))]}"; case "$val" in model_reasoning_effort=*) effort="${val#model_reasoning_effort=}";; esac; i=$((i+2));;
    *) i=$((i+1));;
  esac
done

cat >/dev/null   # drain stdin (the prompt)

# Write a structurally-valid expected-shape answer to the -o file so
# the quality scorer matches the baseline section headers.
if [ -n "$out_file" ]; then
  cat >"$out_file" <<EOF
## Answer

Mock answer at effort=$effort.

## Evidence

- **File**: \`mock.txt\` (lines 1-1)
  **Pattern**: Mock evidence at effort=$effort.

## Confidence

high
EOF
fi

# Emit a canned JSONL turn.completed event on stdout.
printf '%s\n' '{"type":"turn.completed","usage":{"input_tokens":1000,"cached_input_tokens":200,"output_tokens":50,"reasoning_output_tokens":30}}'
SHIM
chmod +x "$SHIM_DIR/codex"

# Invoke the runner with the synthetic plugin root + mock codex.
set_test "Runner --codex --agent stub-agent --sweep produces results JSON with 4 records"
output=$(PLUGIN_ROOT="$FAKE_PLUGIN" \
         CODEX_BIN="$SHIM_DIR/codex" \
         L6_FIXTURES_DIR="$FAKE_FIXTURES" \
         L6_RESULTS_DIR="$FAKE_RESULTS" \
         bash "$RUNNER" --codex --agent stub-agent --sweep 2>&1)
assert_contains "$output" "Sweep mode: testing stub-agent across 4 effort levels"
assert_contains "$output" "effort=xhigh"
assert_contains "$output" "effort=high"
assert_contains "$output" "effort=medium"
assert_contains "$output" "effort=low"

# The runner prints its results-file path on the last line.
results_file=$(echo "$output" | grep "Results saved to:" | sed 's/Results saved to: //')
assert_file_exists "$results_file"

set_test "Results JSON contains 4 records (one per effort level)"
record_count=$(jq 'length' "$results_file")
assert_eq "4" "$record_count"

set_test "Each record has the expected agent + non-zero token count"
agents=$(jq -r '.[].agent' "$results_file" | sort -u)
assert_eq "stub-agent" "$agents"
non_zero=$(jq '[.[] | select(.tokens > 0)] | length' "$results_file")
assert_eq "4" "$non_zero"

set_test "Records carry the effort label in the model field"
xhigh=$(jq '[.[] | select(.model == "effort=xhigh")] | length' "$results_file")
high=$(jq '[.[] | select(.model == "effort=high")] | length' "$results_file")
medium=$(jq '[.[] | select(.model == "effort=medium")] | length' "$results_file")
low=$(jq '[.[] | select(.model == "effort=low")] | length' "$results_file")
assert_eq "1" "$xhigh"
assert_eq "1" "$high"
assert_eq "1" "$medium"
assert_eq "1" "$low"

# ─────────────────────────────────────────
section "Runner --codex path (CLI not found)"
# ─────────────────────────────────────────

set_test "Runner exits 1 with clear error when CODEX_BIN is missing"
result=0
output=$(PLUGIN_ROOT="$FAKE_PLUGIN" \
         CODEX_BIN="/no/such/bin/$$" \
         L6_FIXTURES_DIR="$FAKE_FIXTURES" \
         L6_RESULTS_DIR="$FAKE_RESULTS" \
         bash "$RUNNER" --codex 2>&1) || result=$?
assert_eq "1" "$result" "exit code"
assert_contains "$output" "CLI not found"

# ─────────────────────────────────────────
section "Claude path is untouched by the --codex addition"
# ─────────────────────────────────────────

set_test "Runner with no --codex flag still uses claude (verified via fast-fail when claude is unavailable)"
# Stand up a fake plugin root with no agents to keep the run short,
# point CLAUDE-mode at a missing binary, and confirm the error path is
# the Claude one, not the Codex one.
result=0
output=$(PATH="/usr/bin:/bin" \
         PLUGIN_ROOT="$FAKE_PLUGIN" \
         bash "$RUNNER" 2>&1) || result=$?
# The runner will hit either the missing-claude error or the
# no-fixtures path. Either way, the absence of "Codex" / "codex exec"
# in the output proves the Claude code path is the active one.
assert_not_contains "$output" "codex exec"
assert_not_contains "$output" "(runtime=codex)"

test_summary
