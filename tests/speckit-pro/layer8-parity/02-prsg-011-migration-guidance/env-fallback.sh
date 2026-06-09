#!/usr/bin/env bash
# Path B (parallel subagents fallback) - force AGENT_TEAMS_AVAILABLE=false.

unset CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS
export -n CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS 2>/dev/null || true
