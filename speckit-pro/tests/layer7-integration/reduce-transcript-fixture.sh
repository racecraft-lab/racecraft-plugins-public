#!/usr/bin/env bash
# reduce-transcript-fixture.sh — Convert a scrubbed stream-json transcript into
# a minimal parser replay fixture.
#
# The replay parser only needs Agent/Skill tool_use blocks, matching
# tool_result blocks, and isSidechain. This reducer drops prompts, model
# metadata, tool inventories, internal sidechain chatter, and raw response
# bodies so committed fixtures stay deterministic and low-risk.

set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
  echo "reduce-transcript-fixture.sh: jq is required" >&2
  exit 2
fi

if [ $# -ne 2 ]; then
  echo "Usage: reduce-transcript-fixture.sh <scrubbed-transcript.jsonl> <expected.json>" >&2
  exit 2
fi

transcript="$1"
expected="$2"

if [ ! -f "$transcript" ]; then
  echo "reduce-transcript-fixture.sh: transcript not found: $transcript" >&2
  exit 1
fi

if [ ! -f "$expected" ]; then
  echo "reduce-transcript-fixture.sh: expected.json not found: $expected" >&2
  exit 1
fi

jq -cs --slurpfile expected "$expected" '
  def pad3($n):
    ("000" + ($n | tostring))[-3:];

  def next_id($n):
    "tool-" + pad3($n);

  def response_keywords($subagent_type):
    [
      ($expected[0].response_assertions // [])[]
      | select(.subagent_type == $subagent_type)
      | ((.must_contain_any // [])[0:1] + (.must_contain_section_keywords // []))[]
    ];

  def reduced_response($subagent_type):
    (response_keywords($subagent_type)) as $keywords
    | if ($keywords | length) > 0 then
        "Reduced parser fixture response for \($subagent_type): " + ($keywords | join(" "))
      else
        "Reduced parser fixture response for \($subagent_type)"
      end;

  reduce .[] as $event (
    {events: [], idmap: {}, agent_for: {}, n: 0};

    if $event.type == "assistant" then
      reduce (($event.message.content // [])[]) as $block (. + {blocks: []};
        if ($block.type == "tool_use" and ($block.name == "Agent" or $block.name == "Skill")) then
          .n += 1
          | (next_id(.n)) as $id
          | .idmap[$block.id] = $id
          | if $block.name == "Agent" then
              .agent_for[$id] = ($block.input.subagent_type // "")
              | .blocks += [{
                  type: "tool_use",
                  id: $id,
                  name: "Agent",
                  input: {
                    subagent_type: ($block.input.subagent_type // ""),
                    description: ($block.input.description // ""),
                    prompt: ""
                  }
                }]
            else
              .blocks += [{
                  type: "tool_use",
                  id: $id,
                  name: "Skill",
                  input: {
                    skill: ($block.input.skill // ""),
                    args: ""
                  }
                }]
            end
        else
          .
        end
      )
      | if (.blocks | length) > 0 then
          .events += [{
            type: "assistant",
            isSidechain: ($event.isSidechain // false),
            message: {
              role: "assistant",
              content: .blocks
            }
          }]
        else
          .
        end
      | del(.blocks)

    elif $event.type == "user" then
      . as $state
      | [
          ($event.message.content // [])[]
          | select(.type == "tool_result")
          | (.tool_use_id // "") as $old_id
          | ($state.idmap[$old_id] // null) as $new_id
          | select($new_id != null)
          | ($state.agent_for[$new_id] // "") as $subagent_type
          | {
              type: "tool_result",
              tool_use_id: $new_id,
              content: reduced_response($subagent_type)
            }
        ] as $results
      | if ($results | length) > 0 then
          .events += [{
            type: "user",
            isSidechain: ($event.isSidechain // false),
            message: {
              role: "user",
              content: $results
            }
          }]
        else
          .
        end

    else
      .
    end
  )
  | .events[]
' "$transcript"
