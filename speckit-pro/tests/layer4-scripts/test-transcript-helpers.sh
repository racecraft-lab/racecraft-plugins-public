#!/usr/bin/env bash
# Layer 4 unit tests for transcript-helpers.sh
#
# Validates the parser that extracts orchestrator dispatch info from
# `claude -p --output-format stream-json` JSONL transcripts. Tests run
# against committed synthetic fixtures so they are deterministic and
# never require live LLM calls.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LIB="$TESTS_ROOT/layer7-integration/lib/transcript-helpers.sh"
FIX="$TESTS_ROOT/layer7-integration/test-fixtures"

source "$TESTS_ROOT/lib/assertions.sh"

[ -f "$LIB" ] || { echo "FATAL: $LIB not found"; exit 2; }
# shellcheck disable=SC1090
source "$LIB"

section "extract_orchestrator_dispatches: counts"

set_test "single-dispatch returns 1 dispatch"
result=$(extract_orchestrator_dispatches "$FIX/single-dispatch.jsonl" | jq 'length')
assert_eq "1" "$result"

set_test "multi-dispatch returns 3 dispatches"
result=$(extract_orchestrator_dispatches "$FIX/multi-dispatch.jsonl" | jq 'length')
assert_eq "3" "$result"

set_test "sidechain-noise returns only 1 (top-level) dispatch"
result=$(extract_orchestrator_dispatches "$FIX/sidechain-noise.jsonl" | jq 'length')
assert_eq "1" "$result"

set_test "no-dispatch returns 0 dispatches"
result=$(extract_orchestrator_dispatches "$FIX/no-dispatch.jsonl" | jq 'length')
assert_eq "0" "$result"

set_test "redelegation-chain returns 4 dispatches"
result=$(extract_orchestrator_dispatches "$FIX/redelegation-chain.jsonl" | jq 'length')
assert_eq "4" "$result"

section "extract_orchestrator_dispatches: subagent_type field"

set_test "single-dispatch subagent_type is codebase-analyst"
result=$(extract_orchestrator_dispatches "$FIX/single-dispatch.jsonl" | jq -r '.[0].subagent_type')
assert_eq "speckit-pro:codebase-analyst" "$result"

set_test "multi-dispatch subagent_type set"
types=$(extract_orchestrator_dispatches "$FIX/multi-dispatch.jsonl" | jq -r '.[].subagent_type' | sort | tr '\n' ',')
assert_eq "speckit-pro:codebase-analyst,speckit-pro:consensus-synthesizer,speckit-pro:domain-researcher," "$types"

section "dispatch_order: preserves chronological order"

set_test "redelegation-chain dispatch order"
order=$(extract_dispatch_order "$FIX/redelegation-chain.jsonl" | tr '\n' ',')
expected="speckit-pro:clarify-executor,speckit-pro:codebase-analyst,speckit-pro:domain-researcher,speckit-pro:consensus-synthesizer,"
assert_eq "$expected" "$order"

section "assert_dispatched_to / assert_not_dispatched_to"

set_test "assert_dispatched_to passes when type present"
assert_exit_code 0 assert_dispatched_to "$FIX/single-dispatch.jsonl" "speckit-pro:codebase-analyst"

set_test "assert_dispatched_to fails when type absent"
assert_exit_code 1 assert_dispatched_to "$FIX/single-dispatch.jsonl" "speckit-pro:domain-researcher"

set_test "assert_not_dispatched_to passes when type absent"
assert_exit_code 0 assert_not_dispatched_to "$FIX/single-dispatch.jsonl" "speckit-pro:domain-researcher"

set_test "assert_not_dispatched_to fails when type present"
assert_exit_code 1 assert_not_dispatched_to "$FIX/single-dispatch.jsonl" "speckit-pro:codebase-analyst"

set_test "grill-me is never dispatched in autopilot transcripts"
assert_exit_code 0 assert_not_dispatched_to "$FIX/redelegation-chain.jsonl" "speckit-pro:grill-me"

section "find_forbidden_agent_spawns: subagents must not spawn Agent()"

set_test "forbidden-spawn fixture detects 1 violation"
count=$(find_forbidden_agent_spawns "$FIX/forbidden-spawn.jsonl" | jq 'length')
assert_eq "1" "$count"

set_test "single-dispatch has 0 violations"
count=$(find_forbidden_agent_spawns "$FIX/single-dispatch.jsonl" | jq 'length')
assert_eq "0" "$count"

set_test "redelegation-chain has 0 violations"
count=$(find_forbidden_agent_spawns "$FIX/redelegation-chain.jsonl" | jq 'length')
assert_eq "0" "$count"

set_test "sidechain-noise has 0 violations (sidechain Bash is allowed)"
count=$(find_forbidden_agent_spawns "$FIX/sidechain-noise.jsonl" | jq 'length')
assert_eq "0" "$count"

set_test "assert_no_forbidden_spawns passes for legal transcript"
assert_exit_code 0 assert_no_forbidden_spawns "$FIX/redelegation-chain.jsonl"

set_test "assert_no_forbidden_spawns fails for forbidden-spawn"
assert_exit_code 1 assert_no_forbidden_spawns "$FIX/forbidden-spawn.jsonl"

section "count_dispatches_to: handles repeats"

set_test "redelegation-chain has 1 codebase-analyst dispatch"
count=$(count_dispatches_to "$FIX/redelegation-chain.jsonl" "speckit-pro:codebase-analyst")
assert_eq "1" "$count"

set_test "no-dispatch has 0 of any type"
count=$(count_dispatches_to "$FIX/no-dispatch.jsonl" "speckit-pro:codebase-analyst")
assert_eq "0" "$count"

section "dispatch metadata: description and prompt"

set_test "single-dispatch description preserved"
desc=$(extract_orchestrator_dispatches "$FIX/single-dispatch.jsonl" | jq -r '.[0].description')
assert_eq "Codebase analysis" "$desc"

set_test "single-dispatch prompt preserved"
prompt=$(extract_orchestrator_dispatches "$FIX/single-dispatch.jsonl" | jq -r '.[0].prompt')
assert_eq "Analyze the auth module" "$prompt"

section "extract_subagent_responses: joins tool_use to tool_result"

set_test "single-dispatch returns 1 response"
n=$(extract_subagent_responses "$FIX/single-dispatch.jsonl" | jq 'length')
assert_eq "1" "$n"

set_test "single-dispatch response content matches"
content=$(extract_subagent_responses "$FIX/single-dispatch.jsonl" | jq -r '.[0].content')
assert_contains "$content" "Found auth in src/auth.ts"

set_test "multi-dispatch returns 3 paired responses"
n=$(extract_subagent_responses "$FIX/multi-dispatch.jsonl" | jq 'length')
assert_eq "3" "$n"

set_test "redelegation-chain returns 4 paired responses"
n=$(extract_subagent_responses "$FIX/redelegation-chain.jsonl" | jq 'length')
assert_eq "4" "$n"

set_test "no-dispatch returns 0 responses"
n=$(extract_subagent_responses "$FIX/no-dispatch.jsonl" | jq 'length')
assert_eq "0" "$n"

section "assert_response_contains"

set_test "synthesizer response contains 'argon2' (redelegation-chain)"
assert_exit_code 0 assert_response_contains "$FIX/redelegation-chain.jsonl" "speckit-pro:consensus-synthesizer" "argon2"

set_test "synthesizer response does NOT contain 'bcrypt' (redelegation-chain)"
assert_exit_code 1 assert_response_contains "$FIX/redelegation-chain.jsonl" "speckit-pro:consensus-synthesizer" "bcrypt"

set_test "no response from never-dispatched subagent"
assert_exit_code 1 assert_response_contains "$FIX/single-dispatch.jsonl" "speckit-pro:domain-researcher" "anything"

section "extract_skill_invocations + assert_skill_not_invoked"

set_test "skill-invocations fixture: 2 total Skill invocations (default scope=all)"
n=$(extract_skill_invocations "$FIX/skill-invocations.jsonl" | jq 'length')
assert_eq "2" "$n"

set_test "skill-invocations fixture: 1 orchestrator-level Skill invocation"
n=$(extract_skill_invocations "$FIX/skill-invocations.jsonl" "orchestrator" | jq 'length')
assert_eq "1" "$n"

set_test "skill-invocations fixture: orchestrator skill is speckit.specify"
s=$(extract_skill_invocations "$FIX/skill-invocations.jsonl" "orchestrator" | jq -r '.[0].skill')
assert_eq "speckit.specify" "$s"

set_test "count_skill_invocations grill-me at all scope: 1 match (sidechain only)"
n=$(count_skill_invocations "$FIX/skill-invocations.jsonl" "grill-me")
assert_eq "1" "$n"

set_test "count_skill_invocations grill-me at orchestrator scope: 0 (sidechain doesn't count)"
n=$(count_skill_invocations "$FIX/skill-invocations.jsonl" "grill-me" "orchestrator")
assert_eq "0" "$n"

set_test "count_skill_invocations matches namespaced form via regex"
n=$(count_skill_invocations "$FIX/skill-invocations.jsonl" "speckit-pro:grill-me")
assert_eq "1" "$n"

set_test "assert_skill_not_invoked grill-me at all scope FAILS (sidechain has it)"
assert_exit_code 1 assert_skill_not_invoked "$FIX/skill-invocations.jsonl" "grill-me"

set_test "assert_skill_not_invoked grill-me at orchestrator scope PASSES"
assert_exit_code 0 assert_skill_not_invoked "$FIX/skill-invocations.jsonl" "grill-me" "orchestrator"

set_test "assert_skill_invoked speckit.specify at orchestrator scope PASSES"
assert_exit_code 0 assert_skill_invoked "$FIX/skill-invocations.jsonl" "speckit\\.specify" "orchestrator"

set_test "single-dispatch fixture has 0 Skill invocations"
n=$(extract_skill_invocations "$FIX/single-dispatch.jsonl" | jq 'length')
assert_eq "0" "$n"

set_test "assert_skill_not_invoked grill-me on single-dispatch PASSES (no Skill calls)"
assert_exit_code 0 assert_skill_not_invoked "$FIX/single-dispatch.jsonl" "grill-me"

test_summary
