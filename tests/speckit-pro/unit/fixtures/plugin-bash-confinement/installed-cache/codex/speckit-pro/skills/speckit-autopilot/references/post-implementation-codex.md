# Post-Implementation for Codex

Run these items only after all seven SDD phases complete and G7 passes. They
remain part of the same durable plan and must be mirrored in
`autopilot-state.json`.

On resume, all seven SDD phases being complete is not sufficient to stop.
If any Post item is missing, pending, or in progress, rebuild the durable plan
and continue with the first incomplete Post item.

## Contents

- [Canonical Post Items (10-19)](#canonical-post-items-10-19) — full numbered table with runtime + command per row
- [Combined Durable Plan](#combined-durable-plan) — four supporting rows that remain visible beside the numbered gates
- [How Extension Commands Become Available](#how-extension-commands-become-available) — `$speckit-*` installation via `specify extension add`
- [Parallel Group (Items 10-14)](#parallel-group-items-10-14) — Codex always uses parallel `spawn_agent` (no Agent Teams primitive)
- [Rules](#rules) — extension dispatch, parent-session ownership, PR body, missing-extension behavior
- [PR Packet Validation Workflow](#pr-packet-validation-workflow) — fail-closed pre-PR sequence

## Canonical Post Items (10-19)

Every row below is an item that MUST appear in `update_plan` and
`autopilot-state.json` (Step 1.1's Canonical Post-Implementation Item List). Run
in order; do not collapse or defer.

| # | Item | Requires | Command |
|---|------|----------|---------|
| 10 | Doctor Extension Check | doctor / speckit-utils ext | `$speckit-speckit-utils-doctor` (or `$speckit-doctor`) |
| 11 | Verify Implementation | verify ext | `$speckit-verify` |
| 12 | Verify Tasks Phantom Check | verify-tasks ext | `$speckit-verify-tasks` |
| 13 | Code Review | (none) — built-in | spawn a subagent to independently review the diff `origin/main...HEAD`; report findings by severity |
| 14 | Integration Suite | (none) | `PROJECT_COMMANDS.FULL_VERIFY` or detected full test command |
| 15 | Final Reviewability Backstop | (none) | deferred helper; use current committed evidence or stop before PR side effects |
| 16 | PR Packet/Body Generation | final backstop proceeded | emit or refresh current `specs/<feature>/.process/pr-packets/<packet-id>.json` with `pr-packet-output` `dry_run` then `apply`; stop if emission or validation fails |
| 17 | PR Creation | current packet validation passed | single-PR path only when no split route and no current `pr_marker_plan`; `multi-pr-emission` for split-PR routes or marker-ready plans |
| 18 | Review Remediation | (none) | parent session loop — inspect PR feedback, dispatch fixes as needed |
| 19 | Retrospective | retrospective ext | `$speckit-retrospective-analyze` (FINAL STEP) |

## Combined Durable Plan

The numbered 10-19 gates and the supporting task-list rows are both
authoritative. Codex materializes **14 distinct Post rows** in `update_plan` and
`autopilot-state.json`: every numbered gate above, plus these four supporting
evidence steps:

```text
Post: Reviewability Diff Gate
Post: Self-Review
Post: UAT Runbook Generation
Post: PR Body Generation
```

The diff gate, self-review, and UAT rows feed numbered Post 15; the body row
feeds numbered Post 16. Never delete the supporting rows because the numbered
table groups their ownership, and never delete `Final Reviewability Backstop`
or `PR Packet/Body Generation` because the supporting rows expose their work.

Extension items (10 Doctor, 11 Verify, 12 Verify-Tasks, 19
Retrospective): Spawn `phase-executor` with instructions to run the
`$speckit-*` extension skill for SPEC-XXX and return a summary.
Code Review (13) is built-in — no extension; it runs as the
parallel-group Track B subagent (see below), reviewing the diff and
reporting findings by severity.
Non-extension items 15, 16, 17, 18 and all four supporting rows: execute directly in the parent
session. (Item 14 Integration Suite is also non-extension but runs in
the parallel group's Track C verify-chain subagent — see below — not the
parent session.)
Missing extension: log warning and mark the item `skipped: <ext> not
installed`. The item MUST still appear in the plan — never drop it silently.

## How Extension Commands Become Available

Commands like `$speckit-verify`, `$speckit-verify-tasks`,
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

**CRITICAL:** Use subagents only for extension-backed items and the
parallel-group tracks defined below. Parent-session items stay in the parent
session so durable state, PR side effects, and final reporting remain under
the orchestrator's control.

## Parallel Group (Items 10-14)

After G7 passes, items 10-14 form a parallel group. Codex CLI does not
have Agent Teams primitives — Codex always uses the parallel
`spawn_agent` pattern below:

- **Track A:** Doctor (item 10) — spawn `phase-executor` for
  `$speckit-doctor`
- **Track B:** Code Review (item 13) — spawn a `general-purpose` (or
  `phase-executor`) subagent to independently review the diff
  `origin/main...HEAD` and report findings by severity (no extension)
- **Track C:** Verify-chain (items 11 → 12 → 14) — single subagent that
  runs the 3 commands sequentially in its own context (shared test fixtures)

Dispatch the 3 tracks via `spawn_agent`, then loop bounded `wait_agent` calls
until each track's actual result is consumed. A terminal status corroborates
completion but cannot replace the result. Record each result and call
`close_agent` only when the current surface exposes it. Three tracks fits the
hosted Responses default of three active subagents; if derived
`subagent_slots` is lower, dispatch in cap-bounded waves rather than all at
once. The Lead synthesizes findings
into the workflow file's Post-Implementation Checklist, then continues serial
tail (15 → 16 → 17 → 18 → 19).

The Claude Code variant capability-detects Anthropic's Agent Teams
(env var + version) and routes to a team when available, with parallel
background subagents as the fallback path. The 3-track structure
(Doctor / Code Review / Verify-chain) is identical across all paths.

## Rules

- Extension commands run in `phase-executor` with the exact `$speckit-*`
  skill sigil and SPEC context.
- Built-in verification, git, push, PR creation, and review polling stay in the
  parent session so the orchestrator owns durable state and final reporting.
- PR creation requires a current schema-valid feature-local packet and the
  repo-relative body file it references. The active `golden_only`
  `pr-packet-output` helper creates or refreshes packet JSON and packet-owned
  body content; `validate-pr-packet-write` persists validation only after
  rerunning current read-only validation.
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
- **Agent-thread sweep before completion:** as part of the same pre-final audit,
  call `list_agents` when exposed; otherwise audit tracked dispatch IDs and
  consumed results. Every required dispatch must have a real result. When
  `close_agent` is exposed, close remaining current-run threads best-effort.
  A single wait timeout never authorizes interruption; interrupt only a
  confirmed stuck turn, then re-spawn that required item and consume its result
  before completion. Hosted completed threads remain inspectable and are
  managed by the host; their absence of explicit closure is not a failure.

## PR Packet Validation Workflow

Before creating or updating PRs after G7, the parent session applies this
fail-closed sequence:

```text
final-reviewability boundary: use current committed reviewability evidence; if none is current, stop before PR side effects
emit or refresh specs/<feature>/.process/pr-packets/<packet-id>.json with pr-packet-output dry_run then apply
run validate-pr-packet-read-only for that packet and consume response data.stdout_json in memory/state
require data.stdout_json.status=passed, data.stdout_json.pr_blocked=false, and response data.writes_state=false
checkpoint packet/body artifacts so validate-pr-packet-write runs from a clean worktree
run validate-pr-packet-write; apply mode reruns read-only validation before persisting validation_result_path
run validate-pr-workflow-contract with the packet title and current repository diff
create only with packet-owned --base, --head, --title, and --body-file values
```

`final-reviewability-backstop` is deferred, so the mandatory stop-before-PR
boundary uses current committed reviewability evidence. Continue only for
`pass`, `warn`, honored typed-exception outcomes, or final `marker_split` when a
valid current `pr_marker_plan` is present. If a current `pr_marker_plan` exists,
marker-based PR emission remains the downstream path; do not fall back to a
single all-changes PR. An unexcepted correctness block or missing/stale marker
plan blocks every PR side effect and continues internally through the recorded
`autopilot_continuation` and `reslicing_required` state. Never report completion while
`autopilot_continuation.required=true`.

For marker-aware PR preparation, record gate status/mode/exit/evidence path,
fingerprint status, ordered marker IDs, checkpoints, warnings, final
marker_split or marker-plan-ready handoff, packet validation, and PR mappings
before PR side effects. All evidence paths must be repo-relative.

Use `pr-packet-output` to emit or refresh the current feature-local packet and
packet-owned body before `gh pr create`. The packet path remains
`specs/<feature>/.process/pr-packets/<packet-id>.json`, and the packet ID,
title, target branches, changed-file scope, verification evidence, UAT text,
non-goals, and known gaps must come from current workflow or marker-plan
evidence. Run `pr-packet-output` in `dry_run` first, then `apply`. Do not choose
an arbitrary older packet.

`generate-pr-body` is a body-only `golden_only` operation. Its complete input
contract is `output_path`, `title`, and `sections`, and it writes one Markdown
body. It does not create or update packet JSON, packet metadata, template
markers, validation evidence, or PR commands. Its output alone never authorizes
PR creation.

**Refine only sanctioned prose fields — write for a non-expert public reader.**
If the existing packet declares editable fields and its existing body contains
their exact marker pairs, edit only those regions. Otherwise leave the body
unchanged and fail closed if required reviewer content is absent.

Style rules:

- **Lead with what the change does, in human terms.** A reader who has never
  seen this repo should understand it at a glance.
- **No internal jargon.** Drop requirement IDs (`FR-009`), internal layer
  numbers (`Layer 4`), workstream/codenames, and process jargon (`consensus`,
  `tolerance arm`, `gate`).
- **Keep governance terse and collapsed.** Do NOT promote the
  `<details>Reviewer checklist &amp; scope details</details>` block to top-level
  headings, and do NOT pad it.
- **Do not touch protected packet-owned sections** such as `How To Review`,
  `How To UAT`, `Verification`, `Scope`, `Known Gaps`, `## UAT Runbook`, or
  the `speckit-pro-review-packet-source` marker.
- Do not add template comments, hidden TODOs, or ad hoc HTML comments.

Validate the current packet before any single-PR create attempt with one runner
JSON request using `helper_id=validate-pr-packet-read-only`, the same operation,
`mode=read_only`, and the established feature-local packet path. Consume the
current response's `data.stdout_json` in memory and durable workflow state.
Continue only when it reports `status=passed` and `pr_blocked=false`, while the
outer response reports `data.writes_state=false`. If any required packet is
absent or invalid, stop before PR creation with the validator diagnostics.
Commit or otherwise checkpoint the packet/body artifacts so the worktree is
clean, then run `validate-pr-packet-write`; apply mode reruns read-only
validation before persisting the packet's `validation_result_path`. Prior
validation artifacts never authorize PR creation. Exit 1 or 2 blocks before PR
creation with the returned diagnostics.

Validate the PR workflow contract before any single-PR create attempt. The
read-only `validate-pr-workflow-contract` helper checks the actual PR title against the
changed spec scope and rejects aggregate single-PR creation when changed files
contain multi-PR candidate commands or multi-marker final split evidence. A
`DOC-*` spec title must be `docs(DOC-XXX): ...`; `feat(speckit-pro): ...` is
only valid for non-spec plugin changes. Any split-contract failure means the
single-PR path is forbidden. Continue only through the split workflow below,
or stop blocked with the validator output.

Create the single PR from packet fields, never from branch-derived title text
or hand-written body content:

```text
gh pr create \
  --base <packet.target.base_branch> \
  --head <packet.target.head_branch> \
  --title <packet.generated_title.value> \
  --body-file <packet.body_file>
```

## Multi-PR Emission Workflow

For specs whose atomicity route is `split-PR`, Post item 18 is multi-PR
emission. The PRSG-008 `plan-layers` output is the authoritative source of
review order and slice membership. Codex MUST NOT infer, reroute, or re-slice
work from changed files, reviewability warnings, or fallback heuristics.

For non-split routes with no current `pr_marker_plan`, keep the existing
single-PR behavior. For split-PR routes or any current `pr_marker_plan` marked
emission-ready, the previous all-changes PR path is forbidden, even when the
layer/marker plan has only one slice. A one-slice plan still goes through the
same emission contract and opens one slice PR.

Codex parent-session responsibilities:

1. Keep every canonical `Post:` item in `update_plan` and
   `autopilot-state.json` until it is completed or explicitly skipped.
2. Run full verification once for the completed implementation and capture the
   evidence path under `specs/<feature>/.process/emission/`.
3. Read the persisted PRSG-008 layer plan from `autopilot-state.json` or the
   workflow evidence. It must be the exact `plan-layers` envelope with
   `status=ok`.
4. After the final backstop proceeds, treat `multi-pr-emission` only as
   `golden_only` command-plan capture. It does not emit packets or execute live
   PR mutations. Every slice packet must be emitted or refreshed at
   `specs/<feature>/.process/pr-packets/<packet-id>.json` with
   `pr-packet-output`, validated against current marker evidence, and paired
   with persisted current validation evidence before `gh pr create` or
   equivalent PR side effects. Stop only if emission or validation fails.
   For marker emission, `--feature-branch` is the emitted branch prefix. If
   that prefix would collide with an existing parent branch ref, pass a
   non-conflicting prefix through `--feature-branch` and the authoritative
   source spec directory through `--source-feature-dir specs/<feature>`.
   Full verification evidence, scoped evidence, PRS, and MOC files stay under
   the source feature directory while emitted head/base refs use the safe branch
   prefix.
   Live marker emission requires each marker checkpoint to record
   `implementation_checkpoint.head_sha` or
   `implementation_checkpoint.commit_sha`; without those commit SHAs, stop
   before branch or PR mutation and repair the marker checkpoints.
5. `detect-stack-manager-plan` is out of scope and must not be invoked as an
   installed runner helper. Use explicit packet-owned
   `gh pr create --base --head --title --body-file` commands for creation and
   explicit `gh pr edit <number> --base <branch>` commands for retargeting.
   After any partial `gh-stack` mutation, block with recovery evidence instead
   of mixing managers.
6. Record each slice outcome in `update_plan`, `autopilot-state.json`, and the
   workflow evidence before advancing the next Post item.

For each planned slice, preserve the Style B branch topology from the layer
plan and consume the existing validated packet:

```text
slice 1 base: <integration-base>
slice N base: <previous-slice-branch>
marker-aware live head: <recorded marker checkpoint commit>
gh pr create --base <base> --head <head> --body-file <body-file> --title <packet-title>
```

Each slice must pass or record scoped verification before PR creation. A failing
required scoped command must stop before `gh pr create`, record the failed
command, exit status, evidence path, stderr/stdout tail, and keep
`next_slice_id` on the blocked slice. Each existing slice packet must also pass
a fresh `validate-pr-packet-read-only` request before `gh pr create`; consume
`data.stdout_json` in memory/state and do not claim a validation file was
written. If any required packet is absent or invalid, stop before PR creation
with the validator diagnostics. A validation failure blocks on the same slice without opening or
repairing a PR. A later failed slice must not rewind,
invalidate, or mark earlier opened slice PRs as blocked.

After each successful slice PR, persist reviewer and resume surfaces before the
next slice starts:

- `specs/<feature>/.process/prs.json` with `schemaVersion: 2`
- `specs/<feature>/SPEC-MOC.md` regenerated from that manifest
- `docs/ai/specs/.process/autopilot-state.json` top-level
  `multi_pr_emission` object
- workflow evidence naming slice_id, order, branch/base, head SHA, PR URL or
  number, scoped verification evidence, PRS path, MOC regeneration evidence,
  and resulting `next_slice_id`

On resume, reconcile expected local/remote branches and GitHub PRs by expected
head/base before creating anything. Existing matching PRs are authoritative for
PR existence; malformed JSON or duplicate slice keys block instead of guessing.

**Scoped CI boundary:** PRSG-009 scoped CI is recorded reviewer evidence in slice
packets, PR bodies, `.process/prs.json`, workflow evidence, and
`autopilot-state.json`. It MUST NOT modify `.github/workflows/pr-checks.yml`;
the existing PR Checks workflow remains unchanged.

**Restack after lower squash merges:** The runner `restack` operation is
deferred, has no authoritative request, and must not be invoked in any mode.
Use explicit packet-owned `gh pr edit <number> --base <branch>` commands:
retarget the first remaining open slice to the integration base and each later
slice to the immediately preceding remaining slice branch. Preserve each
slice's declared scope, record command results and recovery evidence, and run a
fresh DEFAULT_VERIFY before final merge evidence is considered current. If a
prior `gh-stack` mutation crossed its mutation boundary, resume with
same-manager recovery evidence or block; do not mix managers.

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

4. **Follow-up & tidiness?** Are there `[TODO]`, `[DEFERRED]`, or
   `[OUT-OF-SCOPE]` markers in `spec.md`, `plan.md`, `tasks.md`, or commit
   messages? Each one needs an explicit landing place — a roadmap entry, a
   tracked issue, or a clearly-marked section in the PR body. Silent
   deferral is a defect. Also scan the diff for leftover scaffolding —
   debug logging, commented-out code, stray prints, temporary fixtures, or
   orphaned files — and flag each with a `[tidiness]` note before the PR
   opens.

Block format in the workflow log mirrors
[post-implementation.md §Self-Review Before Finalizing](post-implementation.md#self-review-before-finalizing)
so a single review template serves both runtimes.

**The self-review does not gate PR creation.** Gaps it surfaces
(`[edge-case-gap]`, orphan FR, silent TODO) are written to the workflow log. If
the already-existing packet-owned body declares an editable
`## Self-Review Findings` region, mirror the findings there without changing
protected packet content. The finding itself is the deliverable; packet
availability and validation remain separate fail-closed PR boundaries.

The self-review is mandatory and lives in the canonical
post-implementation item list (`task-list-canonical-codex.md`). It
runs whether the operator configured strict mode for G6.5 or not. It
is a reporting step, not a gate.

## UAT Runbook Generation

Immediately after Self-Review and before PR-body generation (between
`Post: Self-Review` and `Post: PR Body Generation`), the parent session records
UAT runbook status. This row and the generation attempt are mandatory. Invoke
the registered `generate-uat-skeleton` mutation helper in `dry_run` and then
`apply` mode with:

- `spec_path=<feature-dir>/spec.md`
- `output_path=<feature-dir>/.process/uat-runbook.md`
- `workflow_file=<current workflow file>` when available
- `project_commands=<PROJECT_COMMANDS object>`

Before `dry_run`, checkpoint the just-recorded Self-Review and UAT-pending state
by staging only the current workflow and autopilot-state files and committing
them when that scoped index is non-empty. Do not stage unrelated changes. The
mutation helper intentionally rejects a dirty worktree, so this checkpoint is
part of the mandatory generation attempt rather than an optional cleanup.

The helper deterministically overwrites the output from current source inputs;
do not preserve or synthesize a stale skeleton. If generation returns a failure
or the output is absent, log `failed-open: generate-uat-skeleton` with the exact
diagnostic, record the UAT row's fail-open outcome, skip authoring and
validation, and continue. A genuine generation failure does not block PR side
effects, but helper promotion status is never a reason to skip the attempt.

When the helper writes the runbook, **spawn the `uat-runbook-author` agent to
rewrite it in place** so the runbook reads in plain English and a non-engineer
can actually execute it:

```text
spawn_agent("uat-runbook-author", prompt="""
  Rewrite the committed source-derived UAT runbook in place so a non-engineer can follow
  it. Edit ONLY this file: <feature-dir>/.process/uat-runbook.md

  Inputs:
  - Runbook: <feature-dir>/.process/uat-runbook.md
  - Spec: <feature-dir>/spec.md
  - Plan: <feature-dir>/plan.md
  - Quickstart (if present): <feature-dir>/quickstart.md
  - PROJECT_COMMANDS: <PROJECT_COMMANDS as JSON>
  - Diff range: origin/main...HEAD
  - Feature dir: <feature-dir>

  Apply all three mandatory rewrites — plain-prose Env Setup, concrete
  do-this-see-that per-story steps, and a real (or removed) FR Coverage
  Matrix — per your agent instructions. Edit in place; do not create a
  new file.
""")
wait_agent(...)
```

- **Pass PROJECT_COMMANDS to the agent.** This lets it replace unknown setup
  rows with executable project commands.
- If the author agent errors or returns without editing, log the outcome and
  continue fail-open with the committed source-derived runbook unchanged.

Never invoke `validate-uat-runbook`: that helper is not registered. Before any
UAT quality validation, inspect the live registered helper metadata. If no
actual registered UAT-validation path exists, log
`skipped: UAT validation unavailable` and continue fail-open. If a registered
validation path exists, run that registered validator against the existing
runbook. If and only if that just-run validator reports the existing runbook
invalid, STOP before PR-body generation or PR creation and report its
diagnostics. Missing output after a recorded generation failure is never sent
to validation and never blocks.

If generation or authoring changed the runbook, auto-commit that change:

```text
git add <feature-dir>/.process/uat-runbook.md
git commit -m "docs(SPEC-XXX): add UAT runbook"
```
