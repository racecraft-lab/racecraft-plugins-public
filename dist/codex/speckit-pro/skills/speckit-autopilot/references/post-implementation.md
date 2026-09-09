# Post-Implementation Reference

Detailed procedures for Steps 3.0-3.3 of the autopilot workflow.

## Contents

- [Post-Implementation Parallel Group](#post-implementation-parallel-group) — capability-driven dispatch for tasks 10/11/12/13/14
- [3.1 Full Integration / E2E Suite Verification](#31-full-integration--e2e-suite-verification)
- [3.2 PR Creation](#32-pr-creation)
- [3.3 Copilot Review Remediation Loop](#33-copilot-review-remediation-loop)

## Post-Implementation Parallel Group

This is **Use site 1** of the [Agent Teams use-site map](./agent-teams-integration.md)
in speckit-pro — the first place the autopilot leverages Anthropic's
Agent Teams when available. See that doc for the full map (current +
planned), capability detection, and lifecycle policy across other use
sites (consensus debate, Phase 7 `[P]` tasks, parallel
checklist/analyze).

Tasks 10/11/12/13/14 are independent post-implementation work that
benefits from parallel dispatch. The serial tail — tasks 15-19 — is
**not** part of that parallel group: each step stays strictly sequential
because of hard dependencies (Reviewability reads the resulting diff, PR
Body needs the reviewability result and Self-Review, PR Creation needs
PR Body, Review Remediation needs the PR URL, Retrospective needs all of
the above).

**Both code paths are parallel.** The autopilot auto-routes based on
`AGENT_TEAMS_AVAILABLE` from Step 0.6's capability probe — there is
no user-facing opt-in. Agent Teams adds inter-teammate messaging and
shared task-list coordination; the subagents fallback achieves the
same wall-clock parallelism via background dispatch.

### Dependency graph (both paths)

```text
10 Doctor Extension Check        — reads project state, no deps
11 Verify Implementation         ─┐
12 Verify Tasks Phantom Check    ─┼── may share test fixtures
14 Integration Suite             ─┘   (chain serially within this group)
13 Code Review                    — built-in independent review of the diff, no deps

→ all 5 complete before 15 Reviewability Diff Gate begins
```

**Three parallel tracks** (same in both code paths):

- Track A: `10 Doctor` (singleton, read-only)
- Track B: `13 Code Review` (singleton, independent review of the diff)
- Track C: `11 Verify` → `12 Verify-Tasks` → `14 Integration Suite`
  (chained — shared test fixtures, serialize within track)

Wall-clock = `max(track A, track B, track C)` for either code path.

### Path A: Agent Teams (when `AGENT_TEAMS_AVAILABLE=true`)

The lead issues three named `Agent` calls for tasks 10-14, waits for every
teammate report, requests graceful shutdown, confirms automatic cleanup, and
then continues serially from task 15. The runtime resolver enables this path
only for a positively interactive, team-enabled, exact-client-UAT-verified
session. No legacy team-management tool is invoked.

**Why a team here:** the docs' [parallel code review](https://code.claude.com/docs/en/agent-teams#use-case-examples)
example is a 1:1 match — independent reviewers each apply a distinct
lens, lead synthesizes. The team adds inter-teammate messaging (a
verifier can ask the reviewer "did you see the regression in
`src/foo.ts:42`?") and a shared task list with file-locked claiming.

**Team spawn (named Agent semantics):**

```text
Agent(team_name: "SPEC-XXX-post-implementation", name: "doctor",
      subagent_type: "general-purpose",
      prompt: "Run /<doctor-cmd> for SPEC-XXX. Report extension health and blockers. Read only.")
Agent(team_name: "SPEC-XXX-post-implementation", name: "reviewer",
      subagent_type: "general-purpose",
      prompt: "Review spec.md, plan.md, and origin/main...HEAD. Report findings by severity. Read only.")
Agent(team_name: "SPEC-XXX-post-implementation", name: "verifier",
      subagent_type: "general-purpose",
      prompt: "Run /<verify-cmd>, then /<verify-tasks-cmd>, then <INTEGRATION_TEST>. Report each result. Read only.")

Use the same `team_name` and a unique `name` for every teammate. Do not set
`run_in_background` on teammate calls. Require all three final reports before
synthesis. If the exact client cannot prove the read-only/tool contract, set
`team_contract_verified=false` and use Path B.
```

Substitute the actual extension command names (e.g., `/speckit.doctor`
vs `/speckit.speckit-utils.doctor`) based on Step 0.12 extension
detection. Teammate effort follows the lead. Do not claim that subagent-only
`skills`, `disallowedTools`, `memory`, or `maxTurns` fields apply to teammates.

**Lead synthesis after team completes:**

```text
1. Wait for all 3 teammates to mark their tasks completed
2. Collect each teammate's final report (read via team mailbox or
   ask the lead to summarize each teammate's findings)
3. Write a consolidated Post-Implementation Checklist entry to the
   workflow file with one row per task (10/11/12/13/14):
     | Task | Status | Findings | Action Needed |
4. Request graceful teammate shutdown and confirm automatic cleanup
5. Continue to Task 15 (Reviewability Diff Gate) — serial tail in the
   parent session
```

**Quality gate via `TaskCompleted` hook (optional but recommended):**

Place this in `.claude/hooks/hooks.json` (project-level) to block any
teammate from marking its task complete if Integration Suite reported
a regression:

```json
{
  "hooks": {
    "TaskCompleted": [
      {
        "matcher": "verifier-integration",
        "hooks": [
          {
            "type": "command",
            "command": "check integration result for PASS"
          }
        ]
      }
    ]
  }
}
```

Exit code 2 sends feedback to the teammate and prevents the task from
being marked complete. The teammate must re-run the integration suite
or surface the regression to the lead.

**Path A failure modes:**

- **A teammate stops on error:** message it once to recover. If unrecoverable,
  request shutdown and fall through to Path B; log the failure.
- **Lead shuts down team early:** tell the lead "wait for your
  teammates to complete their tasks before proceeding."
- **Task status lags**: if a teammate
  has clearly finished but its task is still `in_progress`, nudge
  the teammate or manually mark complete.
- **Shutdown/cleanup is unconfirmed:** do not start another team. Record the
  lifecycle failure and use ordinary subagents for the rest of the run.

### Path B: Parallel subagents (when `AGENT_TEAMS_AVAILABLE=false`)

Same three tracks, dispatched as background subagents in ONE message.
Each track is a `general-purpose` subagent that runs its track's
commands (singleton or chain) and returns a summary. The lead awaits
all three, then synthesizes.

Ordinary calls MUST omit `name`, which prevents accidental teammate promotion
in a team-enabled interactive session.

**Background dispatch (single tool turn):**

```text
Agent(subagent_type: "general-purpose",
      run_in_background: true,
      description: "SPEC-XXX Doctor",
      prompt: "Run /<doctor-cmd> for SPEC-XXX. Return a summary of
               extension health and any blocking issues.")

Agent(subagent_type: "general-purpose",
      run_in_background: true,
      description: "SPEC-XXX Code Review",
      prompt: "Independently review the implemented change for SPEC-XXX
               against spec.md/plan.md and the diff origin/main...HEAD —
               correctness, regressions, scope, missed edge cases. Return
               findings by severity (CRITICAL/HIGH/MEDIUM/LOW). This is a
               fresh-eyes review, distinct from the orchestrator's
               Self-Review. No extension required.")

Agent(subagent_type: "general-purpose",
      run_in_background: true,
      description: "SPEC-XXX Verify Chain",
      prompt: "Run these 3 commands in sequence — STOP on first
               failure and report which step failed:
               1. /<verify-cmd> for SPEC-XXX
               2. /<verify-tasks-cmd> for SPEC-XXX
               3. <INTEGRATION_TEST command from PROJECT_COMMANDS>
               Report pass/fail per step and any regressions.")
```

All three `Agent()` calls go in **one assistant message** so they
dispatch concurrently. The orchestrator then awaits all three
results (Claude Code's background-agent return mechanism) before
synthesizing.

**Lead synthesis after background subagents complete:**

```text
1. Receive all 3 subagent results as tool responses
2. Write a consolidated Post-Implementation Checklist entry to the
   workflow file with one row per task (10/11/12/13/14):
     | Task | Status | Findings | Action Needed |
3. Continue to Task 15 (Reviewability Diff Gate) — serial
```

**Path B failure modes:**

- **A track subagent errors:** the other two tracks still complete.
  Re-spawn the failed track (sequential retry, not in background).
  If it fails again, mark the task `failed: <reason>` in the
  Post-Implementation Checklist and surface to the user — do NOT
  block PR creation on a non-fatal post-impl failure.
- **Verify chain stops mid-chain (e.g., verify-tasks fails):** the
  subagent reports which step failed. Mark the chain `failed at
  step N` and skip step N+1 (don't run Integration Suite if
  Verify-Tasks already showed phantom tasks — fix those first).
- **Integration Suite test-fixture conflict** (rare): if the
  integration suite shares a mutable working directory with the
  verify extension (e.g., shared `target/` for Rust projects),
  Track C's serial chain already handles this. The race only
  appears if a user wires verify/review to also run integration
  tests independently — uncommon and out of scope.

### Why no user-facing `post-impl-mode` setting

Agent Teams is a **capability** provided by Claude Code, not a
preference. Either the user has enabled it per
[Anthropic's docs](https://code.claude.com/docs/en/agent-teams) (env
var + version) or they haven't. Speckit-pro uses it when available
and uses parallel subagents otherwise — both paths deliver the same
contract (3 parallel tracks, lead synthesizes, then serial tail).
Users do not need to know about a setting; the autopilot adapts.

## 3.1 Full Integration / E2E Suite Verification

Integration tests for the spec are created DURING the Implement
phase (the `speckit-pro:implement-executor` agent creates them as part of TDD).
This step runs the FULL suite to catch regressions from other specs.

**Step 1 — Verify spec-specific tests exist:**

```text
Glob("tests/integration/*<spec-name>*")  <- TOOL CALL
Glob("tests/e2e/*<spec-name>*")          <- TOOL CALL
```

If no spec-specific tests exist, the `speckit-pro:implement-executor` failed to
create them. Spawn it again to fix:

```text
Agent(
  subagent_type: "speckit-pro:implement-executor",
  description: "SPEC-XXX missing integration tests",
  prompt: """
    The implementation phase did not create integration
    tests for SPEC-XXX. This is NON-NEGOTIABLE.

    1. Read existing integration tests to understand the
       pattern (test structure, setup, teardown)
    2. Create spec-specific integration tests covering
       the P1 user stories from spec.md
    3. Follow TDD: write tests -> verify FAIL -> write
       implementation stubs if needed -> verify PASS

    Spec: specs/<number>-<name>/spec.md
    Plan: specs/<number>-<name>/plan.md
  """
)
```

**Step 2 — Run the FULL suite:** Run ALL integration tests,
not just the new ones:

```text
Command("<INTEGRATION_TEST command>")     <- TOOL CALL
```

If any fail -> fix and re-run (max 2 attempts). Commit fixes
before proceeding.

**Step 3 — Record results** in the workflow file: integration
test count, pass/fail, regressions found.

## 3.2 PR Creation

For specs whose atomicity route is `split-PR`, PR creation is multi-PR
emission. The `plan-layers` output is the authoritative source of
review order and slice membership. The post-implementation phase MUST NOT infer, reroute, or re-slice
work from changed files, reviewability warnings, or fallback heuristics.

For non-split routes, keep the existing single-PR behavior. For split-PR routes,
the previous all-changes PR path is forbidden, even when the layer plan has only
one slice. A one-slice plan still goes through the same emission contract and
opens one slice PR.

```text
1. Run final verification once for the completed implementation:
   <BUILD> && <TYPECHECK> && <LINT> && <UNIT_TEST> && <INTEGRATION_TEST>
   (use PROJECT_COMMANDS discovered in Step 0)
2. Detect remote: git remote -v
3. Capture the full-suite evidence path under
   specs/<feature>/.process/emission/.
4. Read the persisted layer plan from autopilot-state.json or the workflow
   evidence. It must be the exact `plan-layers` envelope with
   status=ok.
5. Apply the final reviewability boundary using current committed evidence. If
   no current evidence exists, stop before `generate-pr-body`, any
   `gh pr create` variant, or `multi-pr-emission` because
   `final-reviewability-backstop` is deferred for installed workflows. Proceed
   only on `pass`, `warn`, honored typed-exception, or final `marker_split`
   when the current `pr_marker_plan`
   is valid. If a current `pr_marker_plan` exists, marker-based PR emission is
   the downstream PR path after any successful final backstop result; do not
   fall back to a single all-changes PR just because the final full-diff gate is
   `pass` or `warn`. A valid current size-only final block also continues into
   marker emission; it is not a manual re-slicing stop. On an unexcepted
   correctness block, block only PR body generation and PR side effects with
   `final_reviewability_gate.status=block` plus a `reslicing_required` packet.
   This is an internal continuation boundary, not a final operator handoff: read
   `autopilot_continuation`, `operator_steps`, and `resume.resume_from`, then
   continue through reviewability routing, layer planning, and split-PR emission until a valid slice PR stack is emitted or a
   typed exception is committed. Never end the run or report completion while
   `autopilot_continuation.required=true`; on gate error, stop with state only
   and no packet. Correctness stops include
   malformed/stale marker state, failed verification, invalid packet, unsafe
   output, unusable gate evidence, invalid JSON, missing status/mode, and stale
   fingerprints.
5b. For a marker-aware proceed result, record gate
   status/mode/exit/evidence path, fingerprint status, ordered marker IDs,
   checkpoints, warnings, final marker_split or marker-plan-ready handoff,
   packet validation, and PR mappings before any PR side effect. All evidence
   paths must be repo-relative.
6. After the backstop proceeds, emit or refresh the packet at
   `specs/<feature>/.process/pr-packets/<packet-id>.json` with the runner
   mutation helper `pr-packet-output`. The packet ID and title evidence must
   come from current workflow or marker-plan evidence; do not choose an
   arbitrary stale file. Run `pr-packet-output` in `dry_run` first, then
   `apply` only with current packet path, body path, base/head target, title,
   changed-file scope, verification evidence, UAT text, non-goals, and known
   gaps. The helper writes the packet JSON and packet-owned body file, and
   declares the validation-result path. `generate-pr-body` is a body-only
   `golden_only` operation and cannot replace the packet.
6b. Require the emitted packet's repo-relative `body_file` to be present and
   readable. If body prose needs refinement, edit only the declared editable
   regions described below, then rerun validation before PR creation.
6c. **Refine only declared editable prose in plain English.** If the current
   packet declares editable fields and its existing body contains their exact
   marker pairs, edit only those regions with content drawn from `spec.md`,
   `plan.md`, and the diff. Otherwise leave the body unchanged and fail closed
   if required reviewer content is absent. Style rules:
   - **Lead with what the change does, in human terms.** A reader who has never
     seen this repo should understand it at a glance.
   - **No internal jargon.** Drop requirement IDs (`FR-009`), internal layer
     numbers (`Layer 4`), workstream/codenames, and process jargon
     (`consensus`, `tolerance arm`, `gate`). Say what happened in English.
   - **Keep governance terse and collapsed.** Do NOT promote the
     `<details>Reviewer checklist &amp; scope details</details>` block to
     top-level headings, and do NOT pad it — the auto-filled numbers plus a
     one-line rollback are enough.
   - **Do not touch protected packet-owned sections or markers.**
   - Omit **Anything reviewers should know** entirely if there is nothing real
     to say. An empty section is worse than no section.
6d. Validate the packet before any single-PR create attempt with one runner JSON
   request using `helper_id=validate-pr-packet-read-only`, the same operation,
   `mode=read_only`, and
   `inputs.packet_path=specs/<feature>/.process/pr-packets/<packet-id>.json`.
   Consume the current response's `data.stdout_json` in memory and durable
   workflow state. Continue only when `data.stdout_json.status=passed`,
   `data.stdout_json.pr_blocked=false`, and response `data.writes_state=false`.
   If any required packet is absent or invalid, stop before PR creation with
   the validator diagnostics. Commit or otherwise checkpoint the packet/body
   artifacts so the worktree is clean, then run `validate-pr-packet-write`;
   apply mode reruns read-only validation before persisting the packet's
   `validation_result_path`. Prior validation artifacts never authorize PR
   creation. Exit 1 or 2 blocks before PR creation with the returned
   diagnostics.
6e. Validate the PR workflow contract before any single-PR create attempt:
   send one read-only runner request for `validate-pr-workflow-contract` with
   `inputs.title=<packet.generated_title.value>` and `inputs.repo_root=.`. Let
   the helper inspect the current `origin/main...HEAD` diff, or pass a current
   repo-relative changed-files evidence path when one already exists.
   Continue only when this just-run validator exits 0. It checks the actual PR
   title against changed spec scope and rejects aggregate single-PR creation
   when changed files contain multi-PR candidate commands or multi-marker final
   split evidence. A `DOC-*` spec title must be `docs(DOC-XXX): ...`;
   `feat(speckit-pro): ...` is only valid for non-spec plugin changes. Any
   split-contract failure means the single-PR path is forbidden: run
   `multi-pr-emission` with the current layer or marker plan, or stop
   blocked with the validator output.
6f. Create the single PR from packet fields, never from branch-derived title
   text or hand-written body content:
   ```text
   gh pr create \
     --base <packet.target.base_branch> \
     --head <packet.target.head_branch> \
     --title <packet.generated_title.value> \
     --body-file <packet.body_file>
   ```
7. For split-PR routes, marker_split final-backstop outcomes, or any current
   `pr_marker_plan` marked emission-ready, use the layer/marker plan as the only
   ordering and membership source after the final backstop proceeds.
   `multi-pr-emission` is `golden_only` command-plan capture: it does not emit
   packets or execute live PR mutations. Every slice packet must be emitted or
   refreshed at `specs/<feature>/.process/pr-packets/<packet-id>.json` with
   `pr-packet-output`, rerun through read-only validation, and paired with
   persisted current validation evidence before PR side effects. Stop only if
   emission or validation fails.
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
7b. `detect-stack-manager-plan` is out of scope and must not be invoked as an
   installed runner helper. Use explicit packet-owned
   `gh pr create --base --head --title --body-file` commands for creation and
   explicit `gh pr edit <number> --base <branch>` commands for retargeting.
   If a prior `gh-stack` mutation already occurred, block with recovery evidence
   rather than mixing managers.
7c. Persist stack-manager evidence in the emission state, command log, and PRS
   records: `selected_manager`, `fallback_reason`, `mutation_boundary`,
   `gh_stack.available`, `gh_stack.supported`, `gh_stack.reason`,
   `topology_compatibility`, `command_plan`, and `stack_manager_evidence_path`.
   The shared schema is
   `skills/speckit-autopilot/contracts/stack-manager-decision.schema.json`.
8. For each planned slice, preserve the Style B branch topology from the plan
   and consume the existing validated packet:
   - slice 1 base: <integration-base>
   - slice N base: <previous-slice-branch>
   - marker-aware live branches are forced to the recorded checkpoint commit
     for that marker; never infer slice contents from changed-file globs
   - PR command shape:
     gh pr create --base <base> --head <head> --body-file <body-file> --title <generated-title>
9. Each slice must pass or record scoped verification before PR creation and
   its existing packet must pass a fresh `validate-pr-packet-read-only` request
   whose `data.stdout_json` is consumed in memory/state. If any required packet
   is absent or invalid, stop before PR creation with the validator diagnostics.
   The read-only validator writes no state or validation file. A
   failing required scoped command must stop before `gh pr create`, record the
   failed command, exit status, evidence path, stderr/stdout tail, and keep
   `next_slice_id` on the blocked slice.
10. After each successful slice PR, persist reviewer and resume surfaces before
    the next slice starts:
    - specs/<feature>/.process/prs.json with `schemaVersion: 2`
    - specs/<feature>/SPEC-MOC.md regenerated from that manifest
    - docs/ai/specs/.process/autopilot-state.json top-level
      `multi_pr_emission` object
    - workflow evidence naming slice_id, order, branch/base, head SHA, PR URL
      or number, scoped verification evidence, PRS path, MOC regeneration
      evidence, and resulting next_slice_id
11. On resume, reconcile expected local/remote branches and GitHub PRs by
    expected head/base before creating anything. Existing matching PRs are
    authoritative for PR existence; malformed JSON or duplicate slice keys
    block instead of guessing.
12. A later slice failure must not rewind, invalidate, or mark earlier opened
    slice PRs as blocked.
```

If `gh` is not installed, push the branch and tell the user
to create the missing slice PRs manually using the same explicit base/head/body
shape.

**Scoped CI boundary:** Scoped CI is recorded reviewer evidence in slice
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

## 3.3 Copilot Review Remediation Loop

**This step is MANDATORY after PR creation.** Use the `/loop`
command to schedule recurring review comment monitoring.

Before invoking `/loop`, extract these values and substitute them
as literal strings into the loop prompt.

```text
PR_NUMBER = <from gh pr create output>
REPO = <owner/name from git remote -v>
BRANCH = <current branch name>
BUILD_CMD = PROJECT_COMMANDS.BUILD
TEST_CMD = PROJECT_COMMANDS.UNIT_TEST
INT_TEST_CMD = PROJECT_COMMANDS.INTEGRATION_TEST
LINT_FIX_CMD = PROJECT_COMMANDS.LINT_FIX
```

**Substitute ALL values, then execute:**

```text
Skill("loop", args: "5m
  Check PR #42 in owner/repo for unresolved review
  comments and resolve them.

  Step 1 -- Fetch unresolved review threads via GraphQL:
  Command('gh api graphql -f query="query {
    repository(owner: \"owner\", name: \"repo\") {
      pullRequest(number: 42) {
        reviewThreads(first: 100) {
          nodes {
            id
            isResolved
            path
            line
            comments(first: 10) {
              nodes { id databaseId body author { login } }
            }
          }
        }
      }
    }
  }"')
  Filter to threads where isResolved == false.

  Step 2 -- If 0 unresolved comments, report 'No unresolved
  comments on PR #42' and stop.

  Step 3 -- Partition by file, parallel across files (WS-F1 / Use site 6):

  a. Scan each thread.body for cross-file hints (rename, "update all
     callers", references to other paths). Mark cross_file = true if so.
  b. Build PARTITIONS = {file_path -> [threads]} for non-cross-file
     threads. CROSS_FILE = [serialized threads].
  c. If PARTITIONS has >=2 entries, dispatch ALL partitions in ONE
     assistant message via background subagents:

       For each (file_path, threads) in PARTITIONS:
         Agent(
           subagent_type: \"general-purpose\",
           run_in_background: true,
           description: \"Resolve PR #42 comments on <file_path>\",
           prompt: \"\"\"
             Fix the following review threads on <file_path>. Threads
             ordered by line number; address them in order.

             PROJECT_COMMANDS:
               BUILD: <BUILD_CMD>
               TYPECHECK: <TYPECHECK_CMD>
               TEST: <TEST_CMD>
               INT_TEST: <INT_TEST_CMD>
               LINT_FIX: <LINT_FIX_CMD>

             Threads (thread_id, line, comment_id, comment_body):
             <list>

             For each thread: code fix (Edit + verify), style (LINT_FIX),
             question/false-positive (prepare reply). Commit all fixes
             for THIS file in ONE commit:
               git add <file_path>
               git commit -m \"fix(SPEC-XXX): address review - <summary>\"
             Do NOT push, post replies, or resolve threads.
             Return: per-thread action, commit SHA, verification result,
             per-thread reply text for the lead to post.
           \"\"\")

     If PARTITIONS has 1 entry, process directly in the orchestrator
     (no parallelism win).

  d. After all partition subagents return, process CROSS_FILE threads
     serially in the lead (each touches multiple files; serial prevents
     race).

  Step 4 -- Push, reply, resolve (lead, serial):

  a. Command('git push')  -- single push for all partition commits
  b. For each thread (parallel partitions + serial cross-file), in
     deterministic thread.id order:
       Reply: Command('gh api repos/owner/repo/pulls/42/comments
         -X POST
         -f body=\"<reply text from subagent>\"
         -f in_reply_to=<comment_id>')
       Resolve: Command('gh api graphql -f query=\"mutation {
         resolveReviewThread(input:{threadId:\"<thread_id>\"})
         { thread { isResolved } }}\"')

  Step 5 -- After all comments addressed, report summary.
")
```

**Critical:** The loop prompt must be **self-contained**. All values
(PR number, repo, branch) must be hardcoded in the prompt, not referenced as
variables.

**After scheduling the loop, the autopilot is DONE.** Report the
final summary with PR URL and note that review remediation is
running in the background via `/loop`.

## Self-Review Before Finalizing

Immediately after G7 passes and before opening the PR (between
`Post: Integration Suite` and `Post: PR Body Generation`), the
orchestrator answers four short questions and records the answers
in the workflow log under a `Self-Review` block. This catches the
common end-of-run failure modes that gate validation alone
doesn't reach: tests that didn't actually run, edge cases the
spec called out but the implementation skipped, requirements
silently dropped, and TODOs the autopilot meant to leave behind.

The four questions, in order:

1. **Tests executed?** Did each of `BUILD`, `TYPECHECK`, `LINT`,
   `UNIT_TEST`, and `INTEGRATION_TEST` actually run in this
   session and exit zero, or did the autopilot infer "no errors
   reported" from a phase that never invoked them? Cite the most
   recent test run with timestamp from the workflow log.

2. **Edge cases?** Walk the acceptance-criteria list in
   `spec.md`. For each criterion, name the test (file:line) that
   exercises its **non-happy** path — error inputs, empty inputs,
   concurrency, auth failure, schema mismatch. If a criterion has
   only a happy-path test, flag it as `[edge-case-gap]`.

3. **Requirements matched?** Cross-walk `spec.md`'s FR-XXX list
   against `tasks.md`. Every FR must trace to at least one
   `[X]` task, and every `[X]` task must have implementation
   evidence (commit hash + passing test). List any orphans in
   either direction.

4. **Follow-up & tidiness?** Are there `[TODO]`, `[DEFERRED]`, or
   `[OUT-OF-SCOPE]` markers in `spec.md`, `plan.md`, `tasks.md`,
   or commit messages? Each one needs an explicit landing place
   — a new spec entry on the technical roadmap, a tracked issue,
   or a clearly-marked section in the PR body. Silent deferral
   is a defect. Also scan the diff for leftover scaffolding —
   debug logging, commented-out code, stray `console.log`/`print`,
   temporary fixtures, or files the change orphaned — and flag each
   with a `[tidiness]` note so it is cleaned up or explicitly
   called out before the PR opens.

**Block format in the workflow log:**

```markdown
### Self-Review (auto-generated)

**Tests executed:** All five (BUILD, TYPECHECK, LINT, UNIT_TEST,
INTEGRATION_TEST) ran at 2026-05-25T17:42:11Z and exited zero.
Evidence: workflow log §G7 Verification.

**Edge cases:** All 7 acceptance criteria have non-happy-path
tests. No `[edge-case-gap]` markers.

**Requirements matched:** FR-001 → T015, T022. FR-002 → T030.
... [enumerate all]. No orphans.

**Follow-up & tidiness:** 1 deferred item — `[DEFERRED] Postgres
connection pooling under load testing`. Landed in PR body §Out of
scope. No silent deferrals. No leftover scaffolding or debug code in
the diff — no `[tidiness]` flags.
```

**On gap detection:** the self-review **does not gate PR creation.** Any gaps it
surfaces (`[edge-case-gap]`, orphan FR, silent TODO) are recorded in the
workflow log. If the already-existing packet-owned body declares an editable
`## Self-Review Findings` region, mirror the findings there without changing
protected packet content. Running the self-review is mandatory; the finding is
the deliverable. Packet availability and validation remain separate fail-closed
PR boundaries.

The self-review is part of the canonical post-implementation
task list (see `task-list-canonical.md`) and runs whether the
operator configured strict mode for G6.5 or not. It is a
reporting step, not a gate — its value is putting the four
answers in writing so anyone reviewing the PR sees them.

## UAT Runbook Generation

Immediately after Self-Review and before PR-body generation (between
`Post: Self-Review` and `Post: PR Body Generation`), the orchestrator records
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

When the helper writes the runbook, **spawn the
`speckit-pro:uat-runbook-author` subagent to rewrite it in place** so the
runbook reads in plain English and a non-engineer can actually execute it:

```text
Agent(
  subagent_type: "speckit-pro:uat-runbook-author",
  description: "SPEC-XXX UAT runbook authoring",
  prompt: """
    Rewrite the committed source-derived UAT runbook in place so a non-engineer can
    follow it. Edit ONLY this file: <feature-dir>/.process/uat-runbook.md

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
  """
)
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
