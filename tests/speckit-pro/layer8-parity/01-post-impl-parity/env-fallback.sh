#!/usr/bin/env bash
# Path B (parallel subagents fallback) — force AGENT_TEAMS_AVAILABLE=false
# by ensuring the env var is unset.

unset CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS

# Exported so child processes (claude -p) see the unset state.
export -n CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS 2>/dev/null || true
