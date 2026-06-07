# Fixture 18 — Post-Impl parallel-subagents fallback dispatch

Verifies that when Agent Teams is NOT available (the
`AGENT_TEAMS_AVAILABLE` capability probe at Step 0.6 returns false),
the post-implementation parallel group dispatches the 3 tracks as
background subagents in **ONE assistant message** (not sequentially).

This is the fallback path of the capability-driven post-impl design —
when Anthropic's Agent Teams is enabled per their docs, the autopilot
uses a team; otherwise it uses this parallel-subagents pattern. Both
deliver the same 3-track structure (Doctor / Code Review / Verify-chain)
and the same wall-clock parallelism — Agent Teams adds inter-teammate
messaging and shared task lists; subagents just summarize-back-to-lead.

The fixture asserts:

- ≥3 subagent dispatches happen
- The dispatches go to `general-purpose` (or `phase-executor` as a
  fallback) — NOT to `clarify-executor`, NOT to `grill-me`
- All 3 occur in a single assistant message (background fan-out, not
  sequential await)
- No forbidden spawns (subagents do not spawn other Agents)

Live validation of the Agent Teams path is deferred to Layer 8
parity fixtures (see `tests/layer8-parity/README.md`).

See `skills/speckit-autopilot/references/post-implementation.md`
§Post-Implementation Parallel Group for the full design.
