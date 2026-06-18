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
| 16 | Final Reviewability Backstop | (none) | `final-reviewability-backstop.sh --feature-dir specs/<feature> --feature-branch <branch> ...` |
| 17 | PR Packet/Body Generation | final backstop proceeded | `generate-pr-body.sh --packet-output .git/speckit-pr-packet.json "$PWD" specs/<feature> .git/speckit-pr-body.md origin/main...HEAD` |
| 18 | PR Creation | current packet validation passed | single-PR path only when no split route and no current `pr_marker_plan`; `multi-pr-emission.sh` for split-PR routes or marker-ready plans |
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

Dispatch the 3 tracks via `spawn_agent`, then `wait_agent` for each and
`close_agent` it as soon as its result is recorded. Three tracks fits within
the default `agents.max_threads` (6); if the session's cap is lower, dispatch
in cap-bounded waves rather than all at once. The Lead synthesizes findings
into the workflow file's Post-Implementation Checklist, then continues serial
tail (15 → 16 → 17 → 18 → 19 → 20).

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
- **Agent-thread sweep before completion:** as part of the same pre-final audit,
  call `list_agents` and `close_agent` any thread still open from this run. No
  completed agent thread should outlive the run — leaked open threads consume
  the session's `agents.max_threads` budget and starve later spawns.

## PR Body Generation Workflow

Before creating or updating PRs after G7, the parent session runs:

```text
skills/speckit-autopilot/scripts/final-reviewability-backstop.sh --feature-dir specs/<feature> --feature-branch <branch> --diff-range origin/main...HEAD --state-output specs/<feature>/.process/final-reviewability/gate-state.json --packet-output specs/<feature>/.process/final-reviewability/reslicing-packet.json ...
skills/speckit-autopilot/scripts/generate-pr-body.sh --packet-output .git/speckit-pr-packet.json "$PWD" specs/<feature> .git/speckit-pr-body.md origin/main...HEAD
skills/speckit-autopilot/scripts/validate-pr-packet.sh .git/speckit-pr-packet.json
git diff --name-only origin/main...HEAD > .git/speckit-pr-changed-files.txt
skills/speckit-autopilot/scripts/validate-pr-workflow-contract.sh --title "$(jq -r '.generated_title.value' .git/speckit-pr-packet.json)" --changed-files .git/speckit-pr-changed-files.txt
```

`final-reviewability-backstop.sh` is the mandatory stop-before-PR boundary.
It runs the diff gate, writes top-level `final_reviewability_gate` state, and
returns 0 only for `pass`, `warn`, honored typed-exception outcomes, or final
`marker_split` when a valid current `pr_marker_plan` is present. If a current
`pr_marker_plan` exists, marker-based PR emission is the downstream PR path
after any successful final backstop result; do not fall back to a single
all-changes PR just because the final full-diff gate is `pass` or `warn`. A
valid current size-only block also continues into marker emission; it is not a
manual re-slicing stop. If it returns 1 for an unexcepted
correctness block or missing/stale marker plan, do not generate a PR body, do
not invoke any `gh pr create` variant, and do not run `multi-pr-emission.sh`
yet. This blocks only PR side effects. It is not a final response condition:
read `autopilot_continuation`, the `reslicing_required` packet, and the named
PRSG-007/008/009 operator step, then continue internally until a valid slice PR
stack is emitted or a typed exception is committed. Never report completion while
`autopilot_continuation.required=true`. If it returns 2, stop as a gate error;
no re-slicing packet is valid for that run.

For marker-aware PR preparation, record gate status/mode/exit/evidence path,
fingerprint status, ordered marker IDs, checkpoints, warnings, final
marker_split or marker-plan-ready handoff, packet validation, and PR mappings
before PR side effects. All evidence paths must be repo-relative.

`generate-pr-body.sh --packet-output` uses the host repository's pull request
template if it exists, preserves unknown host-required sections, appends
missing review-packet sections, and falls back to the bundled template when the
host has none. It writes packet-owned metadata for target base/head, generated
conventional title, rendered body path, shared schema reference, validation
result path, editable fields, scope, verification, and UAT evidence.

**Refine only sanctioned prose fields — write for a non-expert public reader.**
The generator emits exact full-line editable marker pairs for `summary`,
`what_changed`, and `why_it_matters`. Edit only the prose between these marker
pairs. The shared validator elides those three regions before checking the
protected-body fingerprint, so sanctioned prose edits pass while changes to
generated source markers, UAT content, traceability, scope, verification
evidence, known gaps, headings, or unknown HTML comments fail.

Style rules:

- **Lead with what the change does, in human terms.** A reader who has never
  seen this repo should understand it at a glance.
- **No internal jargon.** Drop requirement IDs (`FR-009`), internal layer
  numbers (`Layer 4`), workstream/codenames, and process jargon (`consensus`,
  `tolerance arm`, `gate`).
- **Keep governance terse and collapsed.** Do NOT promote the
  `<details>Reviewer checklist &amp; scope details</details>` block to top-level
  headings, and do NOT pad it.
- **Do not touch protected generated sections** such as `How To Review`,
  `How To UAT`, `Verification`, `Scope`, `Known Gaps`, `## UAT Runbook`, or
  the `speckit-pro-review-packet-source` marker.
- Do not add template comments, hidden TODOs, or ad hoc HTML comments; they
  are treated as stale generated-body content and block PR creation.

Validate the current packet before any single-PR create attempt. Continue only
when this just-run `validate-pr-packet.sh` invocation exits 0 and writes a
matching `status: "passed"` result to the packet's current
`validation_result_path`. Never treat a pre-existing validation JSON file as
authorization to create a PR; stale passed or failed records are evidence only
until the current packet is validated again. Validation failure exits 1,
writes packet-specific remediation JSON, appends workflow evidence, and blocks
before PR creation. Input error exits 2 and must also stop before PR creation.

Validate the PR workflow contract before any single-PR create attempt. The
shared `validate-pr-workflow-contract.sh` checks the actual PR title against the
changed spec scope and rejects aggregate single-PR creation when changed files
contain multi-PR candidate commands or multi-marker final split evidence. A
`DOC-*` spec title must be `docs(DOC-XXX): ...`; `feat(speckit-pro): ...` is
only valid for non-spec plugin changes. Any split-contract failure means the
single-PR path is forbidden: run `multi-pr-emission.sh` with the current layer or
marker plan, or stop blocked with the validator output.

Create the single PR from packet fields, never from branch-derived title text
or hand-written body content:

```bash
gh pr create \
  --base "$(jq -r '.target.base_branch' .git/speckit-pr-packet.json)" \
  --head "$(jq -r '.target.head_branch' .git/speckit-pr-packet.json)" \
  --title "$(jq -r '.generated_title.value' .git/speckit-pr-packet.json)" \
  --body-file "$(jq -r '.body_file' .git/speckit-pr-packet.json)"
```

## Multi-PR Emission Workflow

For specs whose atomicity route is `split-PR`, Post item 18 is multi-PR
emission. The PRSG-008 `plan-layers.sh` output is the authoritative source of
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
   workflow evidence. It must be the exact `plan-layers.sh` envelope with
   `status=ok`.
4. After the final backstop proceeds, run
   `skills/speckit-autopilot/scripts/multi-pr-emission.sh` with the layer or
   marker plan path, durable state path, feature branch, integration base, base
   SHA, full verification evidence path, and optional changed-file scope
   evidence. Marker packets must validate against current marker evidence
   before PR body generation, `gh pr create`, or equivalent PR side effects.
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
5. Before any stack-manager mutation, rely on the shared
   `skills/speckit-autopilot/scripts/detect-stack-manager.sh` helper and the
   shared
   `skills/speckit-autopilot/contracts/stack-manager-decision.schema.json`
   contract. `gh-stack` is selected only after deterministic version,
   read-only proof, packet validation, and topology checks pass. Missing,
   unsupported, ambiguous, unsafe, or topology-incompatible environments use
   explicit `gh pr create/edit --base --head --title --body-file` fallback
   before mutation. After any partial `gh-stack` mutation, block with recovery
   evidence instead of mixing managers.
6. Record each slice outcome in `update_plan`, `autopilot-state.json`, and the
   workflow evidence before advancing the next Post item.

For each planned slice, `multi-pr-emission.sh` creates the Style B branch
topology and PR packet:

```text
slice 1 base: <integration-base>
slice N base: <previous-slice-branch>
marker-aware live head: <recorded marker checkpoint commit>
gh pr create --base <base> --head <head> --body-file <body-file> --title <packet-title>
```

Each slice must pass or record scoped verification before PR creation. A failing
required scoped command must stop before `gh pr create`, record the failed
command, exit status, evidence path, stderr/stdout tail, and keep
`next_slice_id` on the blocked slice. Each generated slice packet must also
pass the shared `validate-pr-packet.sh` before `gh pr create`; a validation
failure writes packet remediation evidence and blocks on the same slice without
opening or repairing a PR. A later failed slice must not rewind,
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

**Restack after lower squash merges:** Use `gh-stack` only when the shared
`detect-stack-manager.sh` helper selects it from deterministic version,
read-only proof, and topology checks. Otherwise use `restack.sh --apply`, which
retargets bases with explicit `gh pr edit --base` fallback. Restack is dry-run
by default, preserves each remaining slice's declared file scope, retargets the
first remaining open slice to the integration base, retargets each later slice
to the immediately preceding remaining slice branch, records recovery evidence
on failure, persists `stack_manager_decision` / `stack_manager_evidence_path`,
and requires a fresh DEFAULT_VERIFY before final merge evidence is considered
current. If a prior `gh-stack` mutation crossed the mutation boundary, resume
with same-manager recovery evidence or block; never switch to explicit fallback
after the boundary.

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
PR ships with a story-by-story acceptance artifact. The runbook is
EXHAUST, so it is written under the feature's own `.process/` directory;
create that directory first (it may not exist), then invoke the shared
skeleton script by its `skills/...` path (the same single copy the Claude
Code variant uses — there is no Codex copy of the script):

```text
mkdir -p <feature-dir>/.process && \
  UAT_PROJECT_COMMANDS='<PROJECT_COMMANDS as JSON>' \
  skills/speckit-autopilot/scripts/generate-uat-skeleton.sh \
  <feature-dir>/spec.md <feature-dir>/.process/uat-runbook.md \
  --workflow-file <workflow-file>
```

- `UAT_PROJECT_COMMANDS` is the discovered `PROJECT_COMMANDS`
  (Step 0.11) serialized to JSON — the script formats the Env Setup
  table from it and never re-runs `detect-commands.sh`.
- `--workflow-file <workflow-file>` lets the script echo the
  `## Self-Review` block written just above into the runbook's
  Self-Review Findings section.
- Output is written exactly once to `<feature-dir>/.process/uat-runbook.md`
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

After the skeleton is written, **spawn the `uat-runbook-author` agent to
rewrite it in place** so the runbook reads in plain English and a
non-engineer can actually execute it:

```text
spawn_agent("uat-runbook-author", prompt="""
  Rewrite the UAT runbook skeleton in place so a non-engineer can follow
  it. Edit ONLY this file: <feature-dir>/.process/uat-runbook.md

  Inputs:
  - Skeleton: <feature-dir>/.process/uat-runbook.md
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

- **Pass PROJECT_COMMANDS to the agent.** This is what lets it write a
  real Env Setup instead of the skeleton's `<unknown>` rows — the same
  gap that produced the meaningless Env Setup table in earlier PRs.
- **This step is FAIL-OPEN too.** If the author agent errors or returns
  without editing, leave the deterministic skeleton in place and continue
  — never block PR creation. A plain skeleton is an acceptable fallback.

Then auto-commit whatever runbook resulted (authored or skeleton):

```text
git add <feature-dir>/.process/uat-runbook.md
git commit -m "docs(SPEC-XXX): add UAT runbook"
```
