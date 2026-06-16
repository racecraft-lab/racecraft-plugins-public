#!/usr/bin/env bash
# judge.sh — Layer 8 semantic-equivalent LLM judge wrapper.
#
# The Layer 8 parity runner needs to compare extracted field values that
# are LLM-generated prose (e.g., the "Findings" column of the
# Post-Implementation Checklist). Byte/string equality is too strict —
# paraphrase is fine — but a free-form text diff is too loose.
#
# semantic_equivalent_judge calls `claude -p --json-schema` with a
# constrained {verdict, reason} schema. The schema forces a binary
# decision (EQUIVALENT | NOT_EQUIVALENT) with a one-line audit trail,
# so the caller never has to parse free-form prose.
#
# Function:
#   semantic_equivalent_judge <value_a> <value_b> <rationale>
#
#     Writes a JSON object to stdout of the form:
#       {"verdict": "EQUIVALENT"|"NOT_EQUIVALENT", "reason": "..."}
#     Exit code 0 if a verdict was produced (regardless of which).
#     Exit code 1 on subprocess failure / malformed output / timeout.
#
# Environment:
#   CLAUDE_BIN          claude executable (default: "claude")
#   L8_JUDGE_MODEL      model to use (default: "sonnet" — chosen to
#                       balance reliability and cost for equivalence
#                       judgments, which are a test artifact rather
#                       than a quality-critical agent run).
#   L8_JUDGE_TIMEOUT_S  per-call wall-clock budget in seconds
#                       (default: 60). claude -p can hang; --max-budget-usd
#                       does not bound wall time.
#
# The CLAUDE_BIN escape hatch is what makes L4 unit testing possible: the
# L4 test prepends a fake claude shim to PATH and exercises this code
# path deterministically (zero live LLM calls in L4, consistent with the
# existing test-transcript-helpers.sh precedent).

CLAUDE_BIN="${CLAUDE_BIN:-claude}"
L8_JUDGE_MODEL="${L8_JUDGE_MODEL:-sonnet}"
L8_JUDGE_TIMEOUT_S="${L8_JUDGE_TIMEOUT_S:-60}"

# JSON schema posted to claude --json-schema. EQUIVALENT/NOT_EQUIVALENT
# enum forces a binary choice (no "I can't determine" escape hatch);
# reason is required so a flaky verdict always leaves an audit trail.
_L8_JUDGE_SCHEMA='{"type":"object","required":["verdict","reason"],"properties":{"verdict":{"type":"string","enum":["EQUIVALENT","NOT_EQUIVALENT"]},"reason":{"type":"string"}}}'

_l8_timeout_bin() {
  if command -v timeout >/dev/null 2>&1; then
    command -v timeout
    return 0
  fi
  if command -v gtimeout >/dev/null 2>&1; then
    command -v gtimeout
    return 0
  fi
  return 1
}

semantic_equivalent_judge() {
  local value_a="$1" value_b="$2" rationale="$3"

  if ! command -v "$CLAUDE_BIN" >/dev/null 2>&1; then
    return 1
  fi

  # Compose the user prompt. The rationale is read from the caller (per-
  # field tolerance.json text) so the judge applies the same decision
  # criterion the human author specified.
  local prompt
  prompt=$(cat <<PROMPT
You are judging whether two pieces of text are semantically equivalent
in the context of a software test parity check.

DECISION CRITERION FOR THIS FIELD:
$rationale

DECISION PROTOCOL:
- Return EQUIVALENT only if both values express the same factual claims
  (paraphrase is fine; contradictory claims are not).
- Return NOT_EQUIVALENT if any claim in one contradicts the other, or if
  one contains a finding/status the other omits in a way that changes
  the test outcome.
- The 'reason' field must cite the specific text that drove your verdict
  in one short sentence.

--- VALUE A ---
$value_a

--- VALUE B ---
$value_b
PROMPT
)

  # Run claude -p with structured-output schema and a wall-time bound.
  # We capture stdout + the exit code; stderr is dropped (the schema
  # validator already constrains the output shape).
  local raw rc=0 timeout_bin
  if timeout_bin="$(_l8_timeout_bin)"; then
    raw=$(
      printf '%s' "$prompt" | \
        "$timeout_bin" "$L8_JUDGE_TIMEOUT_S" \
          "$CLAUDE_BIN" -p \
            --model "$L8_JUDGE_MODEL" \
            --json-schema "$_L8_JUDGE_SCHEMA" \
            --output-format text \
            2>/dev/null
    ) || rc=$?
  else
    raw=$(
      printf '%s' "$prompt" | \
        "$CLAUDE_BIN" -p \
          --model "$L8_JUDGE_MODEL" \
          --json-schema "$_L8_JUDGE_SCHEMA" \
          --output-format text \
          2>/dev/null
    ) || rc=$?
  fi

  if [ "$rc" -ne 0 ]; then
    return 1
  fi

  # Validate the response is well-formed JSON with the expected shape.
  # `jq -e` exits non-zero on null/false, which covers both malformed
  # input and missing fields.
  if ! echo "$raw" | jq -e '.verdict and .reason' >/dev/null 2>&1; then
    return 1
  fi

  local verdict
  verdict=$(echo "$raw" | jq -r '.verdict')
  if [ "$verdict" != "EQUIVALENT" ] && [ "$verdict" != "NOT_EQUIVALENT" ]; then
    return 1
  fi

  # Emit the validated JSON for the caller.
  echo "$raw"
}

# CLI entrypoint for one-off use / debugging.
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  if [ $# -lt 3 ]; then
    echo "Usage: $(basename "$0") <value_a_file> <value_b_file> <rationale>" >&2
    exit 2
  fi
  semantic_equivalent_judge "$(cat "$1")" "$(cat "$2")" "$3"
fi
