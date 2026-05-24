# Fixture 18 — Post-Implementation dispatch in subagents mode (default)

Verifies that when `post-impl-mode` is unset (default) or explicitly
`subagents`, post-implementation tasks 10-14 dispatch as sequential
`Agent()` calls to `phase-executor`. This is the regression safety net
for the D3-with-Teams pilot — when teams mode is unavailable (env var
unset, Claude Code < 2.1.32, or user opt-out), the autopilot must
behave exactly as before.

Teams-mode behavior is gated behind
`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` + Claude Code v2.1.32+ and
is validated by a live-mode fixture (follow-up, not in this fixture).

See `skills/speckit-autopilot/references/post-implementation.md`
§Mode Selection for the dispatch design.
