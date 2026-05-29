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
- **Pre-final completion audit:** Before any final user-facing response,
  re-read `autopilot-state.json`, reconcile it with `update_plan`, and verify
  the canonical Post list. You MUST NOT send a final response while any `Post:`
  item is `pending`, `in_progress`, or missing; equivalently, while any Post
  item is pending, in_progress, or missing. Continue with the first
  incomplete item instead. `Post: Retrospective` remains the final Post item and
  must be completed or explicitly skipped before completion can be reported.

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

## Self-Review Before Finalizing

After G7 passes and before opening the PR (between `Post: Integration Suite`
and `Post: PR Body Generation`), the orchestrator runs a four-question
self-review and records the answers in the workflow log under a `Self-Review`
block. This catches end-of-run failure modes that gate validation alone
doesn't reach: tests that didn't actually run, edge cases the spec called
out but the implementation skipped, requirements silently dropped, and TODOs
the autopilot meant to leave behind.

Questions (Codex orchestrator answers each in order):

1. **Tests executed?** Did `BUILD`, `TYPECHECK`, `LINT`, `UNIT_TEST`, and
   `INTEGRATION_TEST` each actually run this session and exit zero — or did
   the autopilot infer "no errors reported" from a phase that never invoked
   them? Cite the most recent test run with timestamp from the workflow log.

2. **Edge cases?** Walk the acceptance-criteria list in `spec.md`. Name the
   test (file:line) covering each criterion's non-happy path (error inputs,
   empty inputs, concurrency, auth failure, schema mismatch). Criteria with
   only happy-path tests → flag as `[edge-case-gap]`.

3. **Requirements matched?** Cross-walk `spec.md`'s FR-XXX list against
   `tasks.md`. Every FR must trace to at least one `[X]` task, and every
   `[X]` task must have implementation evidence (commit hash + passing
   test). List any orphans in either direction.

4. **Follow-up?** Are there `[TODO]`, `[DEFERRED]`, or `[OUT-OF-SCOPE]`
   markers in `spec.md`, `plan.md`, `tasks.md`, or commit messages? Each
   one needs an explicit landing place — a roadmap entry, a tracked issue,
   or a clearly-marked section in the PR body. Silent deferral is a defect.

Block format in the workflow log mirrors
[post-implementation.md §Self-Review Before Finalizing](../../skills/speckit-autopilot/references/post-implementation.md#self-review-before-finalizing)
so a single review template serves both runtimes.

**The self-review does not gate PR creation.** Gaps it surfaces
(`[edge-case-gap]`, orphan FR, silent TODO) are written to the workflow
log and reproduced in the generated PR body's `## Self-Review Findings`
section. The PR opens regardless of what the review reports — the
finding itself is the deliverable, surfaced so a human reviewer (or
the post-PR review-remediation loop) can act on it.

The self-review is mandatory and lives in the canonical
post-implementation item list (`task-list-canonical-codex.md`). It
runs whether the operator configured strict mode for G6.5 or not. It
is a reporting step, not a gate.

## UAT Runbook Generation

Immediately after Self-Review and before PR-body generation (between
`Post: Self-Review` and `Post: PR Body Generation`), the parent
session generates a deterministic UAT runbook from `spec.md` so the
PR ships with a story-by-story acceptance artifact. Codex invokes the
shared skeleton script by its `skills/...` path (the same single copy
the Claude Code variant uses — there is no Codex copy of the script):

```text
UAT_PROJECT_COMMANDS='<PROJECT_COMMANDS as JSON>' \
  skills/speckit-autopilot/scripts/generate-uat-skeleton.sh \
  <feature-dir>/spec.md <feature-dir>/uat-runbook.md \
  --workflow-file <workflow-file>
```

- `UAT_PROJECT_COMMANDS` is the discovered `PROJECT_COMMANDS`
  (Step 0.11) serialized to JSON — the script formats the Env Setup
  table from it and never re-runs `detect-commands.sh`.
- `--workflow-file <workflow-file>` lets the script echo the
  `## Self-Review` block written just above into the runbook's
  Self-Review Findings section.
- Output is written exactly once to `<feature-dir>/uat-runbook.md`
  (deterministic overwrite, no merge); the script is silent on stdout.

**This step is FAIL-OPEN.** A nonzero exit (e.g., exit 1 on an
unreadable spec) or a missing output file NEVER blocks PR creation:
log a warning and continue. The guarantee is compositional — on a
nonzero exit the script writes no partial `uat-runbook.md`, so the
downstream `generate-pr-body.sh` absent-file path fires and still
emits the `## UAT Runbook` heading with a one-line stub note. The
heading is therefore always present in the PR body whether the
generator succeeded, failed, or never ran; the failure detail lives
in the workflow log, not the artifact.

After the script runs, auto-commit the artifact:

```text
git add <feature-dir>/uat-runbook.md
git commit -m "docs(SPEC-XXX): add UAT runbook"
```

**SPEC-006a scope:** this item runs the deterministic skeleton script
ONLY. The LLM-authored narrative test prose and the UAT author agent
are deferred to SPEC-006b — do not spawn an author agent here.
