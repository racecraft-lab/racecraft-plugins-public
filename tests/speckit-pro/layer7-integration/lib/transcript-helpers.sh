#!/usr/bin/env bash
# transcript-helpers.sh — Parse claude -p stream-json transcripts for Layer 7
#
# Source from a test:
#   source "$PLUGIN_ROOT/../tests/speckit-pro/layer7-integration/lib/transcript-helpers.sh"
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

# extract_skill_invocations <transcript.jsonl> [scope]
#   scope: "orchestrator" (only top-level) or "all" (default).
#   stdout: JSON array of {skill, args, isSidechain} for every Skill tool_use.
#
#   Skills are invoked via the `Skill` tool — distinct from Agent
#   dispatches. `grill-me` is a SKILL, not an Agent subagent, so the
#   HITL boundary check needs to look here, not in extract_orchestrator_dispatches.
extract_skill_invocations() {
  local transcript="$1"
  local scope="${2:-all}"
  jq -cs --arg scope "$scope" '
    [
      .[]
      | select(.type == "assistant")
      | (if $scope == "orchestrator"
         then select((.isSidechain // false) == false)
         else .
         end)
      | . as $event
      | (.message.content // [])[]
      | select(.type == "tool_use" and .name == "Skill")
      | {
          skill: (.input.skill // ""),
          args:  (.input.args // ""),
          isSidechain: ($event.isSidechain // false)
        }
    ]
  ' "$transcript"
}

# count_skill_invocations <transcript.jsonl> <skill_pattern> [scope]
#   stdout: count of Skill invocations matching the regex.
#   skill_pattern is a regex (case-insensitive) applied to the skill field.
#   Examples:
#     count_skill_invocations transcript.jsonl "grill-me"     # any namespace
#     count_skill_invocations transcript.jsonl "^speckit\."   # only speckit.* skills
count_skill_invocations() {
  local transcript="$1" skill_pattern="$2" scope="${3:-all}"
  extract_skill_invocations "$transcript" "$scope" \
    | jq --arg p "$skill_pattern" \
        '[.[] | select(.skill | test($p; "i"))] | length'
}

# assert_skill_not_invoked <transcript.jsonl> <skill_pattern> [scope]
#   exit 0 if no Skill invocation matches the pattern, else exit 1.
#   This is the canonical HITL boundary check for grill-me.
assert_skill_not_invoked() {
  local transcript="$1" skill_pattern="$2" scope="${3:-all}"
  local n
  n=$(count_skill_invocations "$transcript" "$skill_pattern" "$scope")
  [ "$n" -eq 0 ]
}

# assert_skill_invoked <transcript.jsonl> <skill_pattern> [scope]
#   exit 0 if at least one Skill invocation matches.
assert_skill_invoked() {
  local transcript="$1" skill_pattern="$2" scope="${3:-all}"
  local n
  n=$(count_skill_invocations "$transcript" "$skill_pattern" "$scope")
  [ "$n" -gt 0 ]
}

# assert_transcript_contains_term <transcript.jsonl> <literal>
#   exit 0 if the transcript contains the exact literal term.
assert_transcript_contains_term() {
  local transcript="$1" term="$2"
  grep -F -q -- "$term" "$transcript"
}

# assert_transcript_not_contains_term <transcript.jsonl> <literal>
#   exit 0 if the transcript does not contain the exact literal term.
assert_transcript_not_contains_term() {
  local transcript="$1" term="$2"
  ! grep -F -q -- "$term" "$transcript"
}

# ===========================================================================
# Tool-usage observability + grounding (capability-discovery / grounding.md)
# ===========================================================================

# extract_tool_uses <transcript.jsonl> [scope]
#   scope: "orchestrator" (isSidechain false), "sidechain" (true), or "all".
#   stdout: JSON array of EVERY tool_use (not just Agent/Skill) as
#   {name, id, isSidechain}. This is the "what tools did the agents actually
#   invoke" report — the observability the grounding proof is built on.
extract_tool_uses() {
  local transcript="$1" scope="${2:-all}"
  jq -cs --arg scope "$scope" '
    [
      .[]
      | select(.type == "assistant")
      | (if $scope == "orchestrator" then select((.isSidechain // false) == false)
         elif $scope == "sidechain" then select((.isSidechain // false) == true)
         else . end)
      | . as $e
      | (.message.content // [])[]
      | select(.type == "tool_use")
      | {name: .name, id: .id, isSidechain: ($e.isSidechain // false)}
    ]
  ' "$transcript"
}

# extract_tool_use_names <transcript.jsonl> [scope]
#   stdout: newline-separated unique tool names actually invoked.
extract_tool_use_names() {
  local transcript="$1" scope="${2:-all}"
  extract_tool_uses "$transcript" "$scope" | jq -r '.[].name' | sort -u
}

# tool_invoked <transcript.jsonl> <name> [scope]
#   exit 0 if a tool_use with exactly <name> appears in scope, else exit 1.
tool_invoked() {
  local transcript="$1" name="$2" scope="${3:-all}"
  extract_tool_use_names "$transcript" "$scope" | grep -qxF "$name"
}

# extract_completed_tool_names <transcript.jsonl> [scope]
#   stdout: newline-separated unique tool names whose tool_use `id` has a
#   matching `tool_result.tool_use_id` — i.e. the tool was invoked AND returned
#   a result. A call that errored, was interrupted, or never returned is NOT
#   listed, so grounding cannot rest on a tool that produced nothing.
extract_completed_tool_names() {
  local transcript="$1" scope="${2:-all}"
  jq -rs --arg scope "$scope" '
    ( [ .[]
        | select(.type == "user")
        | (.message.content // [])[]
        | select(.type == "tool_result")
        | select((.is_error // false) == false)   # a FAILED call grounds nothing
        | .tool_use_id ] ) as $results
    | [ .[]
        | select(.type == "assistant")
        | (if $scope == "orchestrator" then select((.isSidechain // false) == false)
           elif $scope == "sidechain" then select((.isSidechain // false) == true)
           else . end)
        | (.message.content // [])[]
        | select(.type == "tool_use")
        | select(.id as $id | ($results | index($id)) != null)
        | .name ]
    | unique | .[]
  ' "$transcript" 2>/dev/null
}

# extract_assistant_text <transcript.jsonl>
#   stdout: every assistant `text` block — the agent's own answer text, where a
#   grounded claim and its Evidence note live (never tool results or prompts).
extract_assistant_text() {
  local transcript="$1"
  jq -r '
    select(.type == "assistant")
    | (.message.content // [])[]
    | select(.type == "text")
    | .text
  ' "$transcript" 2>/dev/null
}

# The strict, full grounding Evidence-note shape. A "Capability path:" note that
# does not match this is MALFORMED (missing the `-> <source>`, `; Evidence:`, or
# `; Confidence:` segment).
GROUNDING_NOTE_RE='Capability path:[^;]*->[[:space:]]*[^;[:space:]]+;[[:space:]]*Evidence:[^;]*;[[:space:]]*Confidence:'

# extract_capability_citations <transcript.jsonl>
#   stdout: newline-separated unique cited capability <source> tokens, parsed
#   ONLY from the agent's own answer (assistant `text` blocks) and ONLY from
#   well-formed notes matching GROUNDING_NOTE_RE.
extract_capability_citations() {
  local transcript="$1"
  extract_assistant_text "$transcript" \
    | grep -oE "$GROUNDING_NOTE_RE" \
    | sed -E 's/.*->[[:space:]]*//; s/;.*//; s/[[:space:]]+$//' \
    | grep -v '^$' | sort -u || true
}

# has_malformed_citation <transcript.jsonl>
#   exit 0 if the agent answer contains a "Capability path:" note that does NOT
#   match the full required structure. A malformed note must not be silently
#   ignored — otherwise it would pass as "no citation -> grounded" while actually
#   asserting an unverifiable fact.
has_malformed_citation() {
  local transcript="$1" text all wf
  text=$(extract_assistant_text "$transcript")
  all=$(printf '%s\n' "$text" | grep -cE 'Capability path:' || true)
  wf=$(printf '%s\n' "$text" | grep -oE "$GROUNDING_NOTE_RE" | grep -c . || true)
  [ "${all:-0}" -gt "${wf:-0}" ]
}

# grounding_verdict <transcript.jsonl>
#   stdout: "grounded" if every well-formed citation maps to a tool that was
#   actually invoked AND returned a NON-ERROR result (see
#   extract_completed_tool_names); "ungrounded" if any citation has no such
#   completed invocation (fabricated / errored / non-returning), OR if the answer
#   contains a malformed "Capability path:" note. An answer with no capability
#   notes at all is "grounded" (it asserted nothing it had to back — e.g. a
#   correct abstention).
grounding_verdict() {
  local transcript="$1"
  local completed cite
  # A malformed grounding note is a grounding failure, not a free pass.
  if has_malformed_citation "$transcript"; then
    printf 'ungrounded\n'
    return 0
  fi
  completed=$(extract_completed_tool_names "$transcript" "all")
  while read -r cite; do
    [ -z "$cite" ] && continue
    if ! printf '%s\n' "$completed" | grep -qxF "$cite"; then
      printf 'ungrounded\n'
      return 0
    fi
  done < <(extract_capability_citations "$transcript")
  printf 'grounded\n'
}
