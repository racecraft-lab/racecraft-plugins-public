#!/usr/bin/env bash
# transcript-helpers.sh — Parse claude -p stream-json transcripts for Layer 7
#
# Source from a test:
#   source "$PLUGIN_ROOT/tests/layer7-integration/lib/transcript-helpers.sh"
#
# Stream-json schema (verified empirically):
#   - Top-level events have a `type` field: assistant, user, system, result, ...
#   - Assistant messages contain content blocks; one block type is "tool_use".
#   - An Agent dispatch is: type=tool_use, name="Agent",
#       input.subagent_type=<routed agent>, input.description, input.prompt.
#   - `isSidechain` distinguishes orchestrator events (false) from
#     subagent-internal events (true). Orchestrator dispatches are the
#     only routing decisions we care about.
#
# All functions return JSON arrays on stdout (jq-friendly) or exit-code
# signals for assertions. Pure parsing — no side effects, no LLM calls.

# extract_orchestrator_dispatches <transcript.jsonl>
#   stdout: JSON array of dispatches in chronological order, each
#   {subagent_type, description, prompt, id}.
extract_orchestrator_dispatches() {
  local transcript="$1"
  jq -cs '
    [
      .[]
      | select(.type == "assistant")
      | select((.isSidechain // false) == false)
      | (.message.content // [])[]
      | select(.type == "tool_use" and .name == "Agent")
      | {
          subagent_type: .input.subagent_type,
          description:   (.input.description // ""),
          prompt:        (.input.prompt // ""),
          id:            .id
        }
    ]
  ' "$transcript"
}

# extract_dispatch_order <transcript.jsonl>
#   stdout: newline-separated subagent_type values in dispatch order.
extract_dispatch_order() {
  local transcript="$1"
  extract_orchestrator_dispatches "$transcript" | jq -r '.[].subagent_type'
}

# count_dispatches_to <transcript.jsonl> <subagent_type>
#   stdout: integer count of dispatches to the given subagent_type.
count_dispatches_to() {
  local transcript="$1" target="$2"
  extract_orchestrator_dispatches "$transcript" \
    | jq --arg t "$target" '[.[] | select(.subagent_type == $t)] | length'
}

# assert_dispatched_to <transcript.jsonl> <subagent_type>
#   exit 0 if dispatched at least once, else exit 1.
assert_dispatched_to() {
  local transcript="$1" target="$2"
  local n
  n=$(count_dispatches_to "$transcript" "$target")
  [ "$n" -gt 0 ]
}

# assert_not_dispatched_to <transcript.jsonl> <subagent_type>
#   exit 0 if never dispatched, else exit 1.
assert_not_dispatched_to() {
  local transcript="$1" target="$2"
  local n
  n=$(count_dispatches_to "$transcript" "$target")
  [ "$n" -eq 0 ]
}

# find_forbidden_agent_spawns <transcript.jsonl>
#   stdout: JSON array of Agent tool_uses that occurred inside a sidechain
#   (subagent context). Anthropic's documented constraint is that
#   subagents cannot spawn other subagents — any match here is a violation.
find_forbidden_agent_spawns() {
  local transcript="$1"
  jq -cs '
    [
      .[]
      | select(.type == "assistant")
      | select((.isSidechain // false) == true)
      | (.message.content // [])[]
      | select(.type == "tool_use" and .name == "Agent")
      | {
          subagent_type: .input.subagent_type,
          id:            .id
        }
    ]
  ' "$transcript"
}

# assert_no_forbidden_spawns <transcript.jsonl>
#   exit 0 if no subagent spawned an Agent, else exit 1.
assert_no_forbidden_spawns() {
  local transcript="$1"
  local n
  n=$(find_forbidden_agent_spawns "$transcript" | jq 'length')
  [ "$n" -eq 0 ]
}

# extract_dispatched_set <transcript.jsonl>
#   stdout: newline-separated *unique* subagent_type values (sorted).
extract_dispatched_set() {
  local transcript="$1"
  extract_dispatch_order "$transcript" | sort -u
}

# extract_subagent_responses <transcript.jsonl>
#   stdout: JSON array of {subagent_type, content} pairs, joining each
#   orchestrator Agent dispatch (tool_use) with its corresponding
#   tool_result (matched by tool_use_id) at the orchestrator level.
extract_subagent_responses() {
  local transcript="$1"
  jq -cs '
    # Collect all orchestrator-level tool_uses (Agent dispatches)
    (
      [
        .[]
        | select(.type == "assistant")
        | select((.isSidechain // false) == false)
        | (.message.content // [])[]
        | select(.type == "tool_use" and .name == "Agent")
        | {id: .id, subagent_type: .input.subagent_type}
      ]
    ) as $dispatches
    |
    # Collect all orchestrator-level tool_results
    (
      [
        .[]
        | select(.type == "user")
        | select((.isSidechain // false) == false)
        | (.message.content // [])[]
        | select(.type == "tool_result")
        | {
            tool_use_id: .tool_use_id,
            content: (
              if (.content | type) == "string" then .content
              else (.content | map(.text // "") | join("\n"))
              end
            )
          }
      ]
    ) as $results
    |
    [
      $dispatches[]
      | . as $d
      | ($results[] | select(.tool_use_id == $d.id) | {subagent_type: $d.subagent_type, content: .content})
    ]
  ' "$transcript"
}

# get_response_content <transcript.jsonl> <subagent_type>
#   stdout: concatenated response content of the given subagent_type
#   (joined across multiple invocations with a separator).
get_response_content() {
  local transcript="$1" target="$2"
  extract_subagent_responses "$transcript" \
    | jq -r --arg t "$target" '
        [.[] | select(.subagent_type == $t) | .content] | join("\n---\n")
      '
}

# assert_response_contains <transcript.jsonl> <subagent_type> <substring>
#   exit 0 if any response from <subagent_type> contains <substring>.
assert_response_contains() {
  local transcript="$1" target="$2" needle="$3"
  local content
  content=$(get_response_content "$transcript" "$target")
  [[ "$content" == *"$needle"* ]]
}
