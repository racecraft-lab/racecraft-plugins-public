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
benefits from parallel dispatch. Tasks **15-20 are unaffected** — they
remain strictly sequential because of hard dependencies (Cleanup edits
code, PR Body needs Cleanup done, PR Creation needs PR Body, Review
Remediation needs PR URL, Retrospective needs all of the above).

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
13 Code Review                    — reads diff, no deps

→ all 5 complete before 15 Cleanup begins
```

**Three parallel tracks** (same in both code paths):

- Track A: `10 Doctor` (singleton, read-only)
- Track B: `13 Code Review` (singleton, reads diff)
- Track C: `11 Verify` → `12 Verify-Tasks` → `14 Integration Suite`
  (chained — shared test fixtures, serialize within track)

Wall-clock = `max(track A, track B, track C)` for either code path,
versus the older `sum(tasks 10-14)` of strictly-sequential dispatch.

### Path A: Agent Teams (when `AGENT_TEAMS_AVAILABLE=true`)

The lead spawns ONE Agent Team for tasks 10-14, waits for all
teammates to complete, synthesizes findings into the workflow file,
runs `Clean up the team`, then continues serially from task 15.

**Why a team here:** the docs' [parallel code review](https://code.claude.com/docs/en/agent-teams#use-case-examples)
example is a 1:1 match — independent reviewers each apply a distinct
lens, lead synthesizes. The team adds inter-teammate messaging (a
verifier can ask the reviewer "did you see the regression in
`src/foo.ts:42`?") and a shared task list with file-locked claiming.

**Team spawn (natural-language prompt to the lead):**

```text
Create an agent team for SPEC-XXX post-implementation validation.
Spawn 3 teammates, all using the speckit-pro:phase-executor subagent type.
**Use Sonnet for each teammate** — these are focused execution
tasks (run a slash command, report results), no opus reasoning
needed. The lead stays on opus for synthesis.

- Name: "doctor"   — Task: Run /<doctor-cmd> for SPEC-XXX. Report
                     extension health and any blocking issues.
- Name: "reviewer" — Task: Run /<review-cmd> for SPEC-XXX. Report
                     code-review findings by severity.
- Name: "verifier" — Tasks (chain in order):
                     1. Run /<verify-cmd> for SPEC-XXX
                     2. Run /<verify-tasks-cmd> for SPEC-XXX
                     3. Run <INTEGRATION_TEST command from PROJECT_COMMANDS>
                     Report each step's pass/fail and any regressions.

Task dependencies (set on the shared task list):
  - "verifier-verify-tasks" blockedBy "verifier-verify"
  - "verifier-integration"  blockedBy "verifier-verify-tasks"

Require all three teammates to complete before I synthesize findings.
Do not let any teammate edit src/, tests/, or specs/ files — they
should only run commands and report results.
```

**Why sonnet teammates here (not for cost):** Per
[Anthropic's "Specify teammates and models"](https://code.claude.com/docs/en/agent-teams#specify-teammates-and-models),
teammates don't inherit the lead's model selection. Each teammate
reuses a bundled subagent definition — gate-validator-style sonnet
for these read-and-report tasks, opus for heavy-reasoning executors.
**Every teammate runs at `effort: max` per the plugin's
max-thinking-on-every-agent policy** (see
[agent-teams-integration.md](./agent-teams-integration.md)
§Design principles #8). The post-impl tasks here are mechanical
(run a command, parse output, report) so sonnet is the right
*model fit* — and the thinking budget is never lowered unless
Layer 6 fixtures empirically prove quality=1.0 at a lower effort
(see `tests/layer6-efficiency/results-codex/*.json`). Quality is
paramount; cost is reduced only where quality is proven to be
equivalent.

Substitute the actual extension command names (e.g., `/speckit.doctor`
vs `/speckit.speckit-utils.doctor`) based on Step 0.12 extension
detection. Use the host project's `PROJECT_IMPLEMENTATION_AGENT`
subagent type for any teammate where one is registered —
`speckit-pro:phase-executor` is the safe fallback.

**Reusing existing subagent definitions:** per Anthropic's "Use
subagent definitions for teammates," the teammate types here reference
plugin-scoped subagent definitions. `tools` and `model` carry over
from the definition. `skills` and `mcpServers` do NOT — teammates
load skills/MCP from project + user settings same as a regular
session, so the `/speckit.*` extension commands remain invocable.

**Lead synthesis after team completes:**

```text
1. Wait for all 3 teammates to mark their tasks completed
2. Collect each teammate's final report (read via team mailbox or
   ask the lead to summarize each teammate's findings)
3. Write a consolidated Post-Implementation Checklist entry to the
   workflow file with one row per task (10/11/12/13/14):
     | Task | Status | Findings | Action Needed |
4. Ask the lead: "Clean up the team"
5. Continue to Task 15 (Cleanup) — Path B subagents mode for the
   serial tail
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
            "command": "grep -q 'PASS' /tmp/speckit-integration-result || exit 2"
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

- **A teammate stops on error:** message the teammate directly to
  recover, or spawn a replacement (per Agent Teams troubleshooting
  guidance). If unrecoverable, abandon the team and fall through to
  Path B for the rest of this run; log the failure.
- **Lead shuts down team early:** tell the lead "wait for your
  teammates to complete their tasks before proceeding."
- **Task status lags** (known Agent Teams limitation): if a teammate
  has clearly finished but its task is still `in_progress`, nudge
  the teammate or manually mark complete.
- **Team cleanup fails** (active teammates remain): shut down any
  remaining teammates first, then retry cleanup.

### Path B: Parallel subagents (when `AGENT_TEAMS_AVAILABLE=false`)

Same three tracks, dispatched as background subagents in ONE message.
Each track is a `general-purpose` subagent that runs its track's
commands (singleton or chain) and returns a summary. The lead awaits
all three, then synthesizes.

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
      prompt: "Run /<review-cmd> for SPEC-XXX. Return findings by
               severity (CRITICAL/HIGH/MEDIUM/LOW).")

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
3. Continue to Task 15 (Cleanup) — serial
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

If a future Claude Code release deprecates the env var (Agent Teams
exits experimental and becomes default-on), the probe in
`prerequisites.md` §Agent Teams capability probe should be relaxed
to a single version check.

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
Bash("<INTEGRATION_TEST command>")     <- TOOL CALL
```

If any fail -> fix and re-run (max 2 attempts). Commit fixes
before proceeding.

**Step 3 — Record results** in the workflow file: integration
test count, pass/fail, regressions found.

## 3.2 PR Creation

For specs whose atomicity route is `split-PR`, PR creation is multi-PR
emission. The PRSG-008 `plan-layers.sh` output is the authoritative source of
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
   evidence. It must be the exact PRSG-008 plan-layers.sh envelope with
   status=ok.
5. Run the final reviewability backstop:
   `skills/speckit-autopilot/scripts/final-reviewability-backstop.sh ...`
   with the feature dir, feature branch, diff range, final state path,
   packet path, persisted PRSG-007 route/sizing result, PRSG-008 layer plan,
   changed-files evidence, and full verification evidence. This MUST run before
   `generate-pr-body.sh`, any `gh pr create` variant, or
   `multi-pr-emission.sh`. Proceed only on `pass`, `warn`, honored
   typed-exception, or final `marker_split` when the current `pr_marker_plan`
   is valid. If a current `pr_marker_plan` exists, marker-based PR emission is
   the downstream PR path after any successful final backstop result; do not
   fall back to a single all-changes PR just because the final full-diff gate is
   `pass` or `warn`. A valid current size-only final block also continues into
   marker emission; it is not a manual re-slicing stop. On an unexcepted
   correctness block, stop with
   `final_reviewability_gate.status=block` plus a `reslicing_required` packet;
   on gate error, stop with state only and no packet. Correctness stops include
   malformed/stale marker state, failed verification, invalid packet, unsafe
   output, unusable gate evidence, invalid JSON, missing status/mode, and stale
   fingerprints.
5b. For a marker-aware proceed result, record gate
   status/mode/exit/evidence path, fingerprint status, ordered marker IDs,
   checkpoints, warnings, final marker_split or marker-plan-ready handoff,
   packet validation, and PR mappings before any PR side effect. All evidence
   paths must be repo-relative.
6. Generate the base review packet only after the backstop proceeds:
   `skills/speckit-autopilot/scripts/generate-pr-body.sh --packet-output .git/speckit-pr-packet.json "$PWD" specs/<number>-<name> .git/speckit-pr-body.md origin/main...HEAD`
   The generator writes packet-owned metadata, including the PR target,
   generated conventional title, rendered body path, validation result path,
   reviewer headings, editable fields, scope, verification, and UAT evidence.
   The rendered body path in the packet is the only body file that may be
   passed to PR creation. With `--packet-output`, the generator replaces the
   template body with the canonical packet-owned reviewer body. The packet body
   preserves only the sanctioned editable fields and reviewer sections.
6b. Verify the body is script-generated (non-blocking self-check):
   confirm `.git/speckit-pr-body.md` contains the
   `speckit-pro-review-packet-source` marker comment AND a `## UAT Runbook`
   heading. If either is missing, the body was hand-written or is stale —
   re-run the step-5 command once. NEVER open the PR with a body written
   from scratch or an inline `--body`; the body MUST be the packet-owned
   `.git/speckit-pr-body.md`. If the marker is still absent after the
   re-run, log a loud warning to the workflow log and proceed (fail-open
   — this never blocks PR creation).
6c. **Fill the body in plain English — write for a non-expert public reader.**
   The generator emits the structure with placeholder comments. Edit
   `.git/speckit-pr-body.md` in place to replace the `<!-- ... -->` comments
   under **What changed**, **Why it matters**, and **Anything reviewers should
   know** with real content drawn from `spec.md`, `plan.md`, and the diff. This
   is the ONE sanctioned edit of the generated body — everything below stays
   as generated. Style rules (the PR page is the public face of the plugin):
   - **Lead with what the change does, in human terms.** A reader who has never
     seen this repo should understand it at a glance.
   - **No internal jargon.** Drop requirement IDs (`FR-009`), internal layer
     numbers (`Layer 4`), workstream/codenames, and process jargon
     (`consensus`, `tolerance arm`, `gate`). Say what happened in English.
   - **Keep governance terse and collapsed.** Do NOT promote the
     `<details>Reviewer checklist &amp; scope details</details>` block to
     top-level headings, and do NOT pad it — the auto-filled numbers plus a
     one-line rollback are enough.
   - **Do not touch the `## UAT Runbook` section or the
     `speckit-pro-review-packet-source` marker** — leave both exactly as the
     generator produced them.
   - Omit **Anything reviewers should know** entirely if there is nothing real
     to say. An empty section is worse than no section.
6d. Validate the packet before any single-PR create attempt:
   `skills/speckit-autopilot/scripts/validate-pr-packet.sh .git/speckit-pr-packet.json`
   Continue only when this just-run validator invocation exits 0 and writes a
   matching `status: "passed"` result to the packet's current
   `validation_result_path`. Never treat a pre-existing validation JSON file as
   authorization to create a PR; stale passed or failed records are evidence
   only until the current packet is validated again. A validation failure exits
   1, writes packet-specific remediation JSON to the packet's
   `validation_result_path`, appends workflow evidence, and blocks before PR
   creation. An input error exits 2 and must also stop before PR creation.
6e. Create the single PR from packet fields, never from branch-derived title
   text or hand-written body content:
   ```bash
   gh pr create \
     --base "$(jq -r '.target.base_branch' .git/speckit-pr-packet.json)" \
     --head "$(jq -r '.target.head_branch' .git/speckit-pr-packet.json)" \
     --title "$(jq -r '.generated_title.value' .git/speckit-pr-packet.json)" \
     --body-file "$(jq -r '.body_file' .git/speckit-pr-packet.json)"
   ```
7. For split-PR routes, marker_split final-backstop outcomes, or any current
   `pr_marker_plan` marked emission-ready, run multi-pr-emission.sh with the
   layer/marker plan evidence, durable state path,
   feature branch, integration base, base SHA, full verification evidence path,
   and optional changed-file scope evidence only after the final backstop
   proceeds. The emitted packets must validate against the marker evidence
   before PR body generation, `gh pr create`, or equivalent PR side effects.
   Live marker emission requires each marker checkpoint to record
   `implementation_checkpoint.head_sha` or
   `implementation_checkpoint.commit_sha`; without those commit SHAs, stop
   before branch or PR mutation and repair the marker checkpoints.
8. For each planned slice, multi-pr-emission.sh creates the Style B branch
   topology and PR packet:
   - slice 1 base: <integration-base>
   - slice N base: <previous-slice-branch>
   - marker-aware live branches are forced to the recorded checkpoint commit
     for that marker; never infer slice contents from changed-file globs
   - PR command shape:
     gh pr create --base <base> --head <head> --body-file <body-file> --title <generated-title>
9. Each slice must pass or record scoped verification before PR creation. A
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

**Scoped CI boundary:** PRSG-009 scoped CI is recorded reviewer evidence in slice
packets, PR bodies, `.process/prs.json`, workflow evidence, and
`autopilot-state.json`. It MUST NOT modify `.github/workflows/pr-checks.yml`;
the existing PR Checks workflow remains unchanged.

**Restack after lower squash merges:** Use `gh-stack` only when it is installed
and safe non-mutating inspection confirms an existing active stack. Otherwise
use `skills/speckit-autopilot/scripts/restack.sh`, which is dry-run by default
and requires `--apply` for mutation. Restack preserves each remaining slice's
declared file scope, retargets the first remaining open slice to the integration
base, retargets each later slice to the immediately preceding remaining slice
branch, records recovery evidence on failure, and requires a fresh
DEFAULT_VERIFY before final merge evidence is considered current.

## 3.3 Copilot Review Remediation Loop

**This step is MANDATORY after PR creation.** Use the `/loop`
command to schedule recurring review comment monitoring.

**Before invoking `/loop`, extract these values and substitute
them as LITERAL STRINGS into the loop prompt. The `/loop` fires
in a fresh context -- template placeholders will NOT be resolved.
You MUST substitute actual values.**

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
  Bash('gh api graphql -f query="query {
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

  a. Bash('git push')  -- single push for all partition commits
  b. For each thread (parallel partitions + serial cross-file), in
     deterministic thread.id order:
       Reply: Bash('gh api repos/owner/repo/pulls/42/comments
         -X POST
         -f body=\"<reply text from subagent>\"
         -f in_reply_to=<comment_id>')
       Resolve: Bash('gh api graphql -f query=\"mutation {
         resolveReviewThread(input:{threadId:\"<thread_id>\"})
         { thread { isResolved } }}\"')

  Step 5 -- After all comments addressed, report summary.
")
```

**CRITICAL:** The example above uses LITERAL values (42,
owner/repo, pnpm build, etc.) for illustration. YOU must
substitute the ACTUAL values extracted above. Do NOT leave
any angle-bracket placeholders in the /loop prompt.

**Why `/loop`:** The loop runs every 5 minutes in the background,
checking for new review comments from GitHub Copilot or human
reviewers. It automatically expires after 3 days (Claude Code's
built-in safety limit). The autopilot doesn't need to wait --
it schedules the loop and reports completion.

**Critical:** The loop prompt must be **self-contained** -- each
cron fire runs in a fresh context with no memory of prior
iterations. All values (PR number, repo, branch) must be
hardcoded in the prompt, not referenced as variables.

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

4. **Follow-up?** Are there `[TODO]`, `[DEFERRED]`, or
   `[OUT-OF-SCOPE]` markers in `spec.md`, `plan.md`, `tasks.md`,
   or commit messages? Each one needs an explicit landing place
   — a new spec entry on the technical roadmap, a tracked issue,
   or a clearly-marked section in the PR body. Silent deferral
   is a defect.

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

**Follow-up:** 1 deferred item — `[DEFERRED] Postgres connection
pooling under load testing`. Landed in PR body §Out of scope.
No silent deferrals.
```

**On gap detection:** the self-review **does not gate PR
creation.** Any gaps it surfaces (`[edge-case-gap]`, orphan FR,
silent TODO) are recorded in the workflow log and reproduced in
the `## Self-Review Findings` section of the generated PR body,
where a human reviewer (or the post-PR review-remediation loop)
can act on them. Running the self-review is mandatory — the
finding is the deliverable. The PR opens regardless of what the
review surfaces.

The self-review is part of the canonical post-implementation
task list (see `task-list-canonical.md`) and runs whether the
operator configured strict mode for G6.5 or not. It is a
reporting step, not a gate — its value is putting the four
answers in writing so anyone reviewing the PR sees them.

## UAT Runbook Generation

Immediately after Self-Review and before PR-body generation
(between `Post: Self-Review` and `Post: PR Body Generation`), the
orchestrator generates a deterministic UAT runbook from `spec.md` so
the PR ships with a story-by-story acceptance artifact. The runbook is
EXHAUST, so it is written under the feature's own `.process/` directory;
create that directory first (it may not exist), then run the bundled
skeleton script:

```text
Bash("mkdir -p <feature-dir>/.process && \
  UAT_PROJECT_COMMANDS='<PROJECT_COMMANDS as JSON>' \
  bash '<SKILL_SCRIPTS>/generate-uat-skeleton.sh' \
  <feature-dir>/spec.md <feature-dir>/.process/uat-runbook.md \
  --workflow-file <workflow-file>")
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
log a warning to the workflow log and continue. The guarantee is
compositional — on a nonzero exit the script writes no partial
`uat-runbook.md` (FR-006), so the downstream `generate-pr-body.sh`
absent-file path fires and still emits the `## UAT Runbook` heading
with a one-line stub note. The heading is therefore always present in
the PR body whether the generator succeeded, failed, or never ran;
the failure detail lives in the workflow log, not the artifact.

After the skeleton is written, **spawn the `speckit-pro:uat-runbook-author`
subagent to rewrite it in place** so the runbook reads in plain English
and a non-engineer can actually execute it:

```text
Agent(
  subagent_type: "speckit-pro:uat-runbook-author",
  description: "SPEC-XXX UAT runbook authoring",
  prompt: """
    Rewrite the UAT runbook skeleton in place so a non-engineer can
    follow it. Edit ONLY this file: <feature-dir>/.process/uat-runbook.md

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
  """
)
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
