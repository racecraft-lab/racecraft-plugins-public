# Post-Implementation for Codex

Run these items only after all seven SDD phases complete and G7 passes. They
remain part of the same durable plan and must be mirrored in
`autopilot-state.json`.

On resume, all seven SDD phases being complete is not sufficient to stop.
If any Post item is missing, pending, or in progress, rebuild the durable plan
and continue with the first incomplete Post item.

## Contents

- [Canonical Post Items (10-19)](#canonical-post-items-10-19) — full numbered table with runtime + command per row
- [Combined Durable Plan](#combined-durable-plan) — two supporting rows that remain visible beside the numbered gates
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
| 15 | Reviewability Diff Gate | (none) | use current committed evidence or stop before PR side effects |
| 16 | PR Body Generation | reviewability, self-review, and UAT proceeded | run `pr-packet-output` for a grounded single packet; split packet output remains deferred |
| 17 | PR Creation | current packet validation passed | single-PR path only when no split route and no current `pr_marker_plan`; `multi-pr-emission` for split-PR routes or marker-ready plans |
| 18 | Review Remediation | (none) | parent session loop — inspect PR feedback, dispatch fixes as needed |
| 19 | Retrospective | retrospective ext | `$speckit-retrospective-analyze` (FINAL STEP) |

## Combined Durable Plan

The numbered 10-19 gates and the supporting task-list rows are both
authoritative. Codex materializes the same **12 distinct Post rows** as Claude
Code in `update_plan` and `autopilot-state.json`: every numbered gate above,
plus these two supporting evidence steps:

```text
Post: Self-Review
Post: UAT Runbook Generation
```

Self-review and UAT feed numbered Post 16 after numbered Post 15 establishes
the reviewability boundary. Never delete the supporting rows because each
records independent evidence before packet/body generation.

Extension items (10 Doctor, 11 Verify, 12 Verify-Tasks, 19
Retrospective): Spawn `phase-executor` with instructions to run the
`$speckit-*` extension skill for SPEC-XXX and return a summary.
Code Review (13) is built-in — no extension; it runs as the
parallel-group Track B subagent (see below), reviewing the diff and
reporting findings by severity.
Non-extension items 15, 16, 17, 18 and both supporting rows: execute directly in the parent
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
- Single-route PR creation generates a schema-valid feature-local packet and
  referenced body through `pr-packet-output`, then requires fresh read-only
  validation. Split packet generation remains unavailable.
- Missing optional extensions are logged and skipped only where their procedure
  explicitly declares a fail-open boundary. Do not generalize that permission
  to packet generation, push, PR creation, or PR reconciliation.
- `Post: PR Body Generation` and `Post: PR Creation` are non-skippable.
  A packet, push, authentication, network, or create/reconcile failure leaves
  the first affected row `in_progress` or `blocked`; it never becomes `skipped`
  and the workflow never becomes complete.
- Never mark the workflow complete until every required Post item is completed,
  every optional skip is explicitly authorized by its named procedure, and PR
  Creation records a verified GitHub PR number, URL, head, and base.
- **Pre-final completion audit:** Before any final user-facing response,
  re-read `autopilot-state.json`, reconcile it with `update_plan`, and verify
  the canonical Post list. You MUST NOT send a final response while any `Post:`
  item is `pending`, `in_progress`, or missing; equivalently, while any Post
  item is pending, in_progress, missing, or PR Creation lacks verified PR
  evidence. Continue with the first
  incomplete item instead. `Post: Retrospective` remains the final Post item and
  must be completed before completion can be reported.
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
for a single route, run pr-packet-output in apply mode with grounded structured evidence
require its derived specs/<feature>/.process/pr-packets/<packet-id>.json and body_file to exist
refine only sanctioned prose, then git add only the packet and body and commit them as the single direct child of the recorded source revision
run validate-pr-packet-read-only for those committed, clean artifacts and consume response data.stdout_json in memory/state
require data.stdout_json.status=passed, data.stdout_json.pr_blocked=false, and response data.writes_state=false
rerun full final verification, the final reviewability boundary, validate-pr-packet-read-only, and validate-pr-workflow-contract
push the packet commit
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

`pr-packet-output` is a `golden_only`, single-packet producer. Prepare it with
`helper_id=pr-packet-output`, the same operation, and only these
grounded input groups: source feature/packet/base refs; conventional title
parts; summary/change/why/review prose; UAT text and repo-relative source;
verification evidence; scope metrics, budget result, and non-goals; known gaps;
source markers; and a release note for `feat` or `fix`. It rejects caller-owned
output paths, raw content, operations, and split metadata. It derives the
current head, immutable base/source HEAD SHAs, source-diff fingerprint,
changed files, total file count, fixed body/packet/validation paths, headings,
editable markers, and versioned protected fingerprint, then uses atomic
file writes in body-then-packet order. If the generated packet or body is stale,
malformed, or unreadable, stop before `gh pr create`. Split packet output and
`validate-pr-packet-write` remain deferred.

`base_ref` accepts only the exact `<base_branch>` or
`origin/<base_branch>` form; object IDs and other remote/full-ref forms are
rejected. Both `dry_run` and `apply` require a clean committed worktree because
scope is derived from `base...HEAD`. On resume, inspect the derived body and
packet paths first. If either output already exists, never validate it for reuse and never overwrite
it. Inspect and remove both body and packet artifacts. If either is tracked,
commit its deletion, restore a clean committed worktree, and regenerate both
from the grounded request.
Run the same grounded request in `dry_run` first. Commit an otherwise
packet-free source checkpoint carrying the response's exact
`required_source_commit_trailer`, rerun dry-run, and require the predicted
fingerprint to be unchanged before apply. Apply fails closed with
`protected_body_authorization_missing` unless the source commit independently
authorizes the protected body. Apply mode also fails closed with
`secure_atomic_writes_unavailable` when
descriptor-relative no-follow writes and atomic no-clobber installation are
unavailable. Do not substitute a path-based write; resume the same clean source
revision in a supported POSIX environment.

`generate-pr-body` is a body-only `golden_only` operation. Its complete input
contract is `output_path`, `title`, and `sections`, and it writes one Markdown
body. It does not create or update packet JSON, packet metadata, template
markers, validation evidence, or PR commands. Its output alone never authorizes
PR creation.

**Refine only sanctioned prose fields — write for a non-expert public reader.**
If the generated packet declares editable fields and its body contains
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

Stage only `packet.body_file` and the generated packet path, then commit those
artifacts as the single direct child of the recorded source revision. The
packet and body must be tracked and the worktree clean. Validate the current
packet before any single-PR create attempt with one runner JSON request using
`helper_id=validate-pr-packet-read-only`, the same operation,
`mode=read_only`, and the established feature-local packet path. Consume the
current response's `data.stdout_json` in memory and durable workflow state.
Continue only when it reports `status=passed` and `pr_blocked=false`, while the
outer response reports `data.writes_state=false`. The helper does not persist
`validation.json` or `validation_result_path`; prior validation artifacts never
authorize PR creation. Exit 1 or 2 blocks before PR creation with the returned
diagnostics.

Validate the PR workflow contract before any single-PR create attempt. The
read-only `validate-pr-workflow-contract` helper checks the actual PR title against the
changed spec scope and rejects aggregate single-PR creation when changed files
contain multi-PR candidate commands or multi-marker final split evidence. A
`DOC-*` spec title must be `docs(DOC-XXX): ...`; `feat(speckit-pro): ...` is
only valid for non-spec plugin changes. Any split-contract failure means the
single-PR path is forbidden. Continue only through the split workflow below,
or stop blocked with the validator output.

Re-run the full final verification suite and final reviewability
boundary against the committed artifacts. Re-run
`validate-pr-packet-read-only` and `validate-pr-workflow-contract`; if any
remediation changes repository bytes or packet evidence, remove the stale
packet artifacts and regenerate from a clean worktree. Detect the remote and
push the packet commit only after every repeated check passes.

Before creating, require `gh --version` and `gh auth status`. Reconcile GitHub
by the packet's exact head and base using `gh pr list --state open --head
<head> --base <base> --json number,url,headRefName,baseRefName`. One exact match
is authoritative and must be reused; more than one is an ambiguity block. With
zero matches, create the single PR from packet fields, never from branch-derived
title text or hand-written body content:

```text
gh pr create \
  --base <packet.target.base_branch> \
  --head <packet.target.head_branch> \
  --title <packet.generated_title.value> \
  --body-file <packet.body_file>
```

After reuse, a successful create, or an ambiguous create failure, run the same
exact head/base lookup again before retrying. Verify the single result with
`gh pr view <number> --json
number,url,state,headRefName,baseRefName,title,body`; require an open PR with the
packet-owned head/base. Read `packet.body_file` as UTF-8 and compare the live
title and body exactly with `packet.generated_title.value` and that file. If
either differs, the current validated packet authorizes exactly one
`gh pr edit <number> --title <packet.generated_title.value> --body-file
<packet.body_file>` reconciliation. Re-read the same fields after editing and
require exact equality; a failed edit or residual mismatch leaves `Post: PR
Creation` incomplete. Persist the number, URL, verified title, SHA-256 digest
of the re-read UTF-8 body as `live_body_sha256`, and verification timestamp in
the workflow and `autopilot-state.json`. Zero matches, multiple matches, failed
auth, an unreadable packet body, or a mismatched view must not be reported as a
completed autopilot run.
A failed or ambiguous outcome leaves PR Creation incomplete and cannot be
converted to a skip.

## Multi-PR Emission Workflow

For specs whose atomicity route is `split-PR`, `Post: PR Creation` (item 17) is multi-PR
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
4. After the reviewability, self-review, and UAT boundary proceeds, treat `multi-pr-emission` only as
   `golden_only` command-plan capture. It does not emit packets or execute live
   PR mutations. Every slice packet must already exist at
   `specs/<feature>/.process/pr-packets/<packet-id>.json` and validate against
   current marker evidence before `gh pr create` or equivalent PR side effects.
   If any required packet is absent or invalid, stop and report that split
   packet output remains deferred; the promoted helper is single-only.
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
written. A validation failure blocks on the same slice without opening or
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
[post-implementation.md §Self-Review Before Finalizing](../../skills/speckit-autopilot/references/post-implementation.md#self-review-before-finalizing)
so a single review template serves both runtimes.

**The self-review does not gate PR creation.** Gaps it surfaces
(`[edge-case-gap]`, orphan FR, silent TODO) are written to the workflow log. If
the packet-owned body declares an editable
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
UAT runbook status. This row is mandatory, but its deferred capability boundary
is fail-open. The runner helper `generate-uat-skeleton` is registered as
deferred for installed workflows, so never invoke it as an active helper.

Reuse a committed source-derived `<feature-dir>/.process/uat-runbook.md` when
present. If none exists, log `skipped: generate-uat-skeleton deferred`, mark the
UAT row skipped with that evidence, and continue to PR-body generation and PR
creation. Missing deferred output alone never marks the row failed and never
blocks PR side effects.

When the committed runbook exists, **spawn the `uat-runbook-author` agent to
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
diagnostics. Missing deferred output is never sent to validation and never
blocks.

If authoring changed the existing runbook, auto-commit that change:

```text
git add <feature-dir>/.process/uat-runbook.md
git commit -m "docs(SPEC-XXX): add UAT runbook"
```
