#!/usr/bin/env bash
# scrub-transcript.sh — Strip PII and machine-specific metadata from a
# captured `claude -p --output-format stream-json` transcript while
# preserving every field the L7 parser depends on.
#
# What's removed/replaced (PII / machine-specific):
#   - Any absolute home/tmp path             → `<HOME>` / `<TMP>` / `<REPO>`
#   - cwd field                              → "<scrubbed>"
#   - sessionId / session_id field           → "<scrubbed-session>"
#   - gitBranch field                        → "<scrubbed-branch>"
#   - requestId / uuid / hook_id fields      → "<scrubbed>"
#   - timestamps and timing fields           → "<scrubbed>"
#   - streamed partial_json/signature chunks → "<scrubbed>"
#   - userType / origin / entrypoint fields  → "<scrubbed>"
#   - inference_geo                          → "<scrubbed>"
#   - usage, cost, quota, agent output paths → "<scrubbed>"
#   - System events with plugin/tool         → reduced to {type, subtype}
#     inventories (these are huge and        only — drops the inventory
#     environment-specific)                    payload entirely
#   - Stream events                          → reduced to {type, subtype}
#     (redundant for parser assertions)
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
#   TRANSCRIPT_SCRUB_EXTRA_REGEX='...' bash scrub-transcript.sh <file>
#
# Exit codes: 0 ok, 1 bad input, 2 jq missing.

set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
  echo "scrub-transcript.sh: jq is required" >&2
  exit 2
fi

# The jq filter is the heart of the scrubber. Walk every value:
#   - strings: replace absolute paths and split path/user fragments
#   - objects: rewrite fields that hold PII
JQ_FILTER='
def scrub_string:
  if type == "string" then
    if (test("<system-reminder>") and test("transcript\\.jsonl")) then
      "<scrubbed-transcript-dump>"
    else
      gsub("[[:xdigit:]]{8}-[[:xdigit:]]{4}-[[:xdigit:]]{4}-[[:xdigit:]]{4}-[[:xdigit:]]{12}"; "<scrubbed-uuid>")
    | gsub("\"session_id\":\"[^\"]+\""; "\"session_id\":\"<scrubbed-session>\"")
    | gsub("\"sessionId\":\"[^\"]+\""; "\"sessionId\":\"<scrubbed-session>\"")
    | gsub("\"requestId\":\"[^\"]+\""; "\"requestId\":\"<scrubbed>\"")
    | gsub("\"hook_id\":\"[^\"]+\""; "\"hook_id\":\"<scrubbed-hook>\"")
    | gsub("\"uuid\":\"[^\"]+\""; "\"uuid\":\"<scrubbed-uuid>\"")
    | gsub("\"signature\":\"[^\"]*\""; "\"signature\":\"<scrubbed-signature>\"")
    | gsub("\"partial_json\":\"[^\"]*\""; "\"partial_json\":\"<scrubbed-partial-json>\"")
    | gsub("\"timestamp\":\"[^\"]+\""; "\"timestamp\":\"<scrubbed-timestamp>\"")
    | gsub("\"agentId\":\"[^\"]+\""; "\"agentId\":\"<scrubbed-agent>\"")
    | gsub("\"outputFile\":\"[^\"]+\""; "\"outputFile\":\"<scrubbed-path>\"")
    | gsub("\"output_file\":\"[^\"]+\""; "\"output_file\":\"<scrubbed-path>\"")
    | gsub("\"total_cost_usd\":[0-9.]+"; "\"total_cost_usd\":\"<scrubbed>\"")
    | gsub("\"total_cost_usd\":\"[^\"]+\""; "\"total_cost_usd\":\"<scrubbed>\"")
    | gsub("\"usage\":\\{[^\\n]*\\}"; "\"usage\":\"<scrubbed-usage>\"")
    | gsub("\"modelUsage\":\\{[^\\n]*\\}"; "\"modelUsage\":\"<scrubbed>\"")
    | gsub("\"rate_limit_info\":\\{[^\\n]*\\}"; "\"rate_limit_info\":\"<scrubbed>\"")
    | gsub("\"tools\":\\[[^\\]]*\\]"; "\"tools\":\"<scrubbed>\"")
    | gsub("\"mcp_servers\":\\[[^\\]]*\\]"; "\"mcp_servers\":\"<scrubbed>\"")
    | gsub("\"slash_commands\":\\[[^\\]]*\\]"; "\"slash_commands\":\"<scrubbed>\"")
    | gsub("\"agents\":\\[[^\\]]*\\]"; "\"agents\":\"<scrubbed>\"")
    | gsub("\"skills\":\\[[^\\]]*\\]"; "\"skills\":\"<scrubbed>\"")
    | gsub("\"plugins\":\\[[^\\]]*\\]"; "\"plugins\":\"<scrubbed>\"")
    | gsub("\"memory_paths\":\\{[^\\}]*\\}"; "\"memory_paths\":\"<scrubbed>\"")
    | gsub("<TMP>-[^[:space:]\"]+"; "<TMP>")
    | gsub(("/private/var/" + "folders/[^[:space:]\"]+"); "<TMP>")
    | gsub(("/" + "Users/[^/[:space:]\"]+"); "<HOME>")
    | gsub("/home/[^/[:space:]\"]+"; "<HOME>")
    | gsub("<HOME>/Documents/[^[:space:]\"]*/racecraft-plugins-public"; "<REPO>")
    | gsub("<HOME>/Documents/[^[:space:]\"]+"; "<PROJECTS>")
    | gsub("-Users-[^[:space:]\"]+"; "<HOME>")
    | gsub("(?i)[[:alnum:]]{2,}[-_ ]documents"; "<PATH>")
    | if $extra_scrub_regex == "" then . else gsub($extra_scrub_regex; "<USER>") end
    | gsub("agentId: [[:alnum:]_-]+"; "agentId: <scrubbed-agent>")
    | gsub("agent [[:xdigit:]]{16}"; "agent <scrubbed-agent>")
    | gsub("Command running in background with ID: [[:alnum:]_-]+"; "Command running in background with ID: <scrubbed-job>")
    | gsub("Use SendMessage with to: [^[:space:]]+"; "Use SendMessage with to: <scrubbed-agent>")
      | gsub("msg_[[:alnum:]]+"; "msg_<scrubbed>")
    end
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
    | if has("hook_id")       then .hook_id = "<scrubbed-hook>" else . end
    | if has("uuid")          then .uuid = "<scrubbed-uuid>"     else . end
    | if has("timestamp")     then .timestamp = "<scrubbed-timestamp>" else . end
    | if has("signature")     then .signature = "<scrubbed-signature>" else . end
    | if has("partial_json")  then .partial_json = "<scrubbed-partial-json>" else . end
    | if has("ttft_ms")       then .ttft_ms = "<scrubbed-duration>" else . end
    | if has("duration_ms")   then .duration_ms = "<scrubbed-duration>" else . end
    | if has("duration_api_ms") then .duration_api_ms = "<scrubbed-duration>" else . end
    | if has("userType")      then .userType = "<scrubbed>"      else . end
    | if has("origin")        then .origin = "<scrubbed>"        else . end
    | if has("entrypoint")    then .entrypoint = "<scrubbed>"    else . end
    | if has("inference_geo") then .inference_geo = "<scrubbed>" else . end
    | if has("usage")         then .usage = "<scrubbed-usage>"   else . end
    | if has("modelUsage")    then .modelUsage = "<scrubbed>"    else . end
    | if has("rate_limit_info") then .rate_limit_info = "<scrubbed>" else . end
    | if has("total_cost_usd") then .total_cost_usd = "<scrubbed>" else . end
    | if has("outputFile")    then .outputFile = "<scrubbed-path>" else . end
    | if has("output_file")   then .output_file = "<scrubbed-path>" else . end
    | if has("agentId")       then .agentId = "<scrubbed-agent>" else . end
    | if has("tools")         then .tools = "<scrubbed>" else . end
    | if has("mcp_servers")   then .mcp_servers = "<scrubbed>" else . end
    | if has("slash_commands") then .slash_commands = "<scrubbed>" else . end
    | if has("agents")        then .agents = "<scrubbed>" else . end
    | if has("skills")        then .skills = "<scrubbed>" else . end
    | if has("plugins")       then .plugins = "<scrubbed>" else . end
    | if has("memory_paths")  then .memory_paths = "<scrubbed>" else . end
    | if has("apiKeySource")  then .apiKeySource = "<scrubbed>" else . end
    | if has("analytics_disabled") then .analytics_disabled = "<scrubbed>" else . end
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

def reduce_stream_event:
  if .type == "stream_event" then
    {type: .type, subtype: (.event.type // "")}
  else .
  end;

. as $event
| reduce_system_event
| reduce_stream_event
| walk(scrub_object)
| walk(scrub_string)
'

scrub_stream() {
  jq --arg extra_scrub_regex "${TRANSCRIPT_SCRUB_EXTRA_REGEX:-}" -c "$JQ_FILTER"
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
