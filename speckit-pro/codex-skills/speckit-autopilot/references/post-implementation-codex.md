# Post-Implementation for Codex

Run these items only after all seven SDD phases complete and G7 passes. They
remain part of the same durable plan and must be mirrored in
`autopilot-state.json`.

On resume, all seven SDD phases being complete is not sufficient to stop.
If any Post item is missing, pending, or in progress, rebuild the durable plan
and continue with the first incomplete Post item.

## Contents

- [Canonical Post Items (10-20)](#canonical-post-items-10-20) — full numbered table with runtime + command per row
- [How Extension Commands Become Available](#how-extension-commands-become-available) — `$speckit-*` installation via `specify extension add`
- [Parallel Group (Items 10-14)](#parallel-group-items-10-14) — Codex always uses parallel `spawn_agent` (no Agent Teams primitive)
- [Rules](#rules) — extension dispatch, parent-session ownership, PR body, missing-extension behavior
- [PR Body Generation Workflow](#pr-body-generation-workflow) — script invocation order pre-PR

## Canonical Post Items (10-20)

Every row below is an item that MUST appear in `update_plan` and
`autopilot-state.json` (Step 1.1's Canonical Post-Implementation Item List). Run
in order; do not collapse or defer.

| # | Item | Requires | Command |
|---|------|----------|---------|
| 10 | Doctor Extension Check | doctor / speckit-utils ext | `$speckit-speckit-utils-doctor` (or `$speckit-doctor`) |
| 11 | Verify Implementation | verify ext | `$speckit-verify` |
| 12 | Verify Tasks Phantom Check | verify-tasks ext | `$speckit-verify-tasks` |
| 13 | Code Review | review ext | `$speckit-review` |
| 14 | Integration Suite | (none) | `PROJECT_COMMANDS.FULL_VERIFY` or detected full test command |
| 15 | Cleanup | cleanup ext | `$speckit-cleanup` |
| 16 | Reviewability Diff Gate | (none) | `reviewability-gate.sh diff origin/main...HEAD` |
| 17 | PR Body Generation | (none) | `generate-pr-body.sh "$PWD" specs/<feature> .git/speckit-pr-body.md origin/main...HEAD` |
| 18 | PR Creation | (none) | `git`, verified remote, `gh pr create --body-file` where available |
| 19 | Review Remediation | (none) | parent session loop — inspect PR feedback, dispatch fixes as needed |
| 20 | Retrospective | retrospective ext | `$speckit-retrospective-analyze` (FINAL STEP) |

Extension items: Spawn `phase-executor` with instructions to run the
`$speckit-*` extension skill for SPEC-XXX and return a summary.
Non-extension items (14, 16, 17, 18, 19): execute directly in the parent
session.
Missing extension: log warning and mark the item `skipped: <ext> not
installed`. The item MUST still appear in the plan — never drop it silently.

## How Extension Commands Become Available

Commands like `$speckit-verify`, `$speckit-review`, `$speckit-cleanup`,
`$speckit-doctor`, `$speckit-retrospective-analyze` are INSTALLED by
`specify extension add <name>`. The CLI creates command files in the
project's commands directory (`.codex/commands/` for Codex CLI,
`.claude/commands/` for Claude Code). These commands then appear as
invocable skills.

If Step 0.12 detected the extension in `.registry` as enabled, its
commands ARE available — run the item. If an extension is NOT in
`.registry` and NOT found via search, log a warning and skip that
specific item (do NOT fail the entire autopilot). Recommend:
`specify extension add <name>`.

**CRITICAL:** Use subagents for ALL post-implementation items — NEVER
invoke skills directly in your context. Rule 1 applies here too.

## Parallel Group (Items 10-14)

After G7 passes, items 10-14 form a parallel group. Codex CLI does not
have Agent Teams primitives — Codex always uses the parallel
`spawn_agent` pattern below:

- **Track A:** Doctor (item 10) — spawn `phase-executor` for
  `$speckit-doctor`
- **Track B:** Code Review (item 13) — spawn `phase-executor` for
  `$speckit-review`
- **Track C:** Verify-chain (items 11 → 12 → 14) — single subagent that
  runs the 3 commands sequentially in its own context (shared test fixtures)

Dispatch the 3 tracks in ONE tool turn via `spawn_agent`, then
`wait_agent` on all three. The Lead synthesizes findings into the
workflow file's Post-Implementation Checklist, then continues serial tail
(15 → 16 → 17 → 18 → 19 → 20).

The Claude Code variant capability-detects Anthropic's Agent Teams
(env var + version) and routes to a team when available, with parallel
background subagents as the fallback path. The 3-track structure
(Doctor / Code Review / Verify-chain) is identical across all paths.

## Rules

- Extension commands run in `phase-executor` with the exact `$speckit-*`
  skill sigil and SPEC context.
- Built-in verification, git, push, PR creation, and review polling stay in the
  parent session so the orchestrator owns durable state and final reporting.
- PR body generation MUST use the host repository's pull request template when
  one exists. Preserve unknown host-required sections and append any missing
  review-packet sections. If no host template exists, use the bundled fallback.
- Missing optional extensions are logged and skipped. Do not fail the entire
  autopilot because an optional extension command is unavailable.
- Never mark the workflow complete until every planned Post item is completed or
  explicitly logged as skipped.

## PR Body Generation Workflow

Before creating or updating a PR after G7, the parent session runs:

```text
skills/speckit-autopilot/scripts/reviewability-gate.sh diff origin/main...HEAD
skills/speckit-autopilot/scripts/generate-pr-body.sh "$PWD" specs/<feature> .git/speckit-pr-body.md origin/main...HEAD
```

`generate-pr-body.sh` uses the host repository's pull request template if it
exists, preserves unknown host-required sections, appends missing review-packet
sections, and falls back to the bundled template when the host has none. Use
`gh pr create --body-file .git/speckit-pr-body.md`, not an inline placeholder.
