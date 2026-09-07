# Fixture 18 — Post-Impl parallel-subagents fallback dispatch

Verifies that the recorded `AGENT_TEAMS_AVAILABLE=false` fixture condition
dispatches the post-implementation 3-track group as background subagents in
**ONE assistant message** (not sequentially).

The fixture asserts:

- ≥3 subagent dispatches happen
- The dispatches go to `general-purpose` (or `phase-executor` as a
  fallback) — NOT to `clarify-executor`, NOT to `grill-me`
- All 3 occur in a single assistant message (background fan-out, not
  sequential await)
- No forbidden spawns (subagents do not spawn other Agents)
- The parent-owned serial tail keeps reviewer-ready packet ordering after
  the parallel group: final backstop before packet generation, fresh
  `validate-pr-packet.sh` before every `gh pr create --base --head --title
  --body-file`, and no post-create repair fallback for invalid packets

This replay fixture does not qualify live host behavior.

See `skills/speckit-autopilot/references/post-implementation.md`
§Post-Implementation Parallel Group for the full design.
