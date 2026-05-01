#!/usr/bin/env bash
# scrub-transcript.sh — Strip PII and machine-specific metadata from a
# captured `claude -p --output-format stream-json` transcript while
# preserving every field the L7 parser depends on.
#
# What's removed/replaced (PII / machine-specific):
#   - Any `/Users/<username>` path           → `<HOME>`
#   - cwd field                              → "<scrubbed>"
#   - sessionId / session_id field           → "<scrubbed-session>"
#   - gitBranch field                        → "<scrubbed-branch>"
#   - requestId field                        → "<scrubbed>"
#   - userType / origin / entrypoint fields  → "<scrubbed>"
#   - inference_geo                          → "<scrubbed>"
#   - System events with plugin/tool         → reduced to {type, subtype}
#     inventories (these are huge and        only — drops the inventory
#     environment-specific)                    payload entirely
#
# What's preserved (L7 parser depends on these):
#   - type, subtype                          (event routing)
#   - isSidechain                            (orchestrator vs sub-agent)
#   - message.role, message.content          (tool_use/tool_result blocks)
#   - input.subagent_type, input.skill,      (Agent + Skill dispatch identity)
#     input.prompt, input.description,
#     input.args
#   - tool_use_id                            (joining dispatch → response)
#   - tool_use id                            (same)
#
# Usage:
#   bash scrub-transcript.sh <file>             # in-place scrub
#   bash scrub-transcript.sh < input > output   # stdin → stdout
#
# Exit codes: 0 ok, 1 bad input, 2 jq missing.

set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
  echo "scrub-transcript.sh: jq is required" >&2
  exit 2
fi

# The jq filter is the heart of the scrubber. Walk every value:
#   - strings: replace /Users/<x>/... and absolute home paths
#   - objects: rewrite fields that hold PII
JQ_FILTER='
def scrub_string:
  if type == "string" then
    gsub("/Users/[^/[:space:]\"]+"; "<HOME>")
    | gsub("/home/[^/[:space:]\"]+"; "<HOME>")
  else .
  end;

def scrub_object:
  if type == "object" then
    .
    | if has("cwd")           then .cwd = "<scrubbed>"           else . end
    | if has("sessionId")     then .sessionId = "<scrubbed-session>" else . end
    | if has("session_id")    then .session_id = "<scrubbed-session>" else . end
    | if has("gitBranch")     then .gitBranch = "<scrubbed-branch>" else . end
    | if has("requestId")     then .requestId = "<scrubbed>"     else . end
    | if has("userType")      then .userType = "<scrubbed>"      else . end
    | if has("origin")        then .origin = "<scrubbed>"        else . end
    | if has("entrypoint")    then .entrypoint = "<scrubbed>"    else . end
    | if has("inference_geo") then .inference_geo = "<scrubbed>" else . end
  else .
  end;

# System hook events and init events carry plugin inventories — strip
# them down to {type, subtype} so the structure is preserved but the
# environment-specific payload is gone.
def reduce_system_event:
  if .type == "system" then
    {type: .type, subtype: (.subtype // "")}
  else .
  end;

. as $event
| reduce_system_event
| walk(scrub_object)
| walk(scrub_string)
'

scrub_stream() {
  jq -c "$JQ_FILTER"
}

if [ $# -eq 0 ]; then
  # stdin → stdout
  scrub_stream
else
  for f in "$@"; do
    if [ ! -f "$f" ]; then
      echo "scrub-transcript.sh: $f: not a file" >&2
      exit 1
    fi
    tmp="$(mktemp)"
    if scrub_stream <"$f" >"$tmp"; then
      mv "$tmp" "$f"
      echo "scrubbed: $f"
    else
      rm -f "$tmp"
      echo "scrub-transcript.sh: failed to scrub $f" >&2
      exit 1
    fi
  done
fi
