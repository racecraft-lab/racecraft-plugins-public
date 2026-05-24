# Post-Implementation Reference

Detailed procedures for Steps 3.0-3.3 of the autopilot workflow.

## Contents

- [Mode Selection](#mode-selection) — `post-impl-mode` setting: `subagents` (default) vs `teams` (opt-in)
- [3.1 Full Integration / E2E Suite Verification](#31-full-integration--e2e-suite-verification)
- [3.2 PR Creation](#32-pr-creation)
- [3.3 Copilot Review Remediation Loop](#33-copilot-review-remediation-loop)

## Mode Selection

The `post-impl-mode` setting from Step 0.6 controls how tasks
10/11/12/13/14 dispatch. **15-20 are unaffected** — they remain
strictly sequential because of hard dependencies (Cleanup edits
code, PR Body needs Cleanup done, PR Creation needs PR Body,
Review Remediation needs PR URL, Retrospective needs all of the
above).

### Dependency graph for the post-impl parallel group

```text
10 Doctor Extension Check        — reads project state, no deps
11 Verify Implementation         ─┐
12 Verify Tasks Phantom Check    ─┼── may share test fixtures
14 Integration Suite             ─┘   (chain serially within this group)
13 Code Review                    — reads diff, no deps

→ all 5 complete before 15 Cleanup begins
```

The conservative grouping is **three parallel tracks**:

- Track A: `10 Doctor` (singleton, read-only)
- Track B: `13 Code Review` (singleton, reads diff)
- Track C: `11 Verify` → `12 Verify-Tasks` → `14 Integration Suite` (chain — shared test fixtures, serialize within track)

This avoids the test-fixture race condition between Verify/Verify-Tasks
and Integration Suite while still parallelizing 3 tracks worth of work.

### subagents mode (default — current behavior)

```text
For each post-impl task in [10, 11, 12, 13, 14, 15, ...]:
  Agent(subagent_type: "phase-executor",
        description: "SPEC-XXX <task>",
        prompt: "Run /<command> for SPEC-XXX. Return summary.")
  Wait for result.
  Update workflow file.
```

Sequential dispatch. Wall-clock = sum(task times). No environment
prerequisites beyond the usual autopilot baseline.

### teams mode (opt-in)

**Requires:** `post-impl-mode: teams` in `.claude/speckit-pro.local.md`,
`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` env var, Claude Code ≥ 2.1.32.
Step 0.6 probe verifies both — falls back to `subagents` mode if either
check fails (warning logged, autopilot continues).

The lead spawns ONE Agent Team for tasks 10-14, waits for all teammates
to complete, synthesizes findings into the workflow file's
Post-Implementation Checklist, runs `Clean up the team`, then continues
serially from task 15.

**Team spawn (natural-language prompt to the lead):**

```text
Create an agent team for SPEC-XXX post-implementation validation.
Spawn 3 teammates, all using the phase-executor subagent type:

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

Substitute the actual extension command names (e.g., `/speckit.doctor`
vs `/speckit.speckit-utils.doctor`) based on Step 0.12 extension
detection. Use the host project's `PROJECT_IMPLEMENTATION_AGENT`
subagent type for any teammate where one is registered — `phase-executor`
is the safe fallback.

**Reusing existing subagent definitions:** per Anthropic's "Use
subagent definitions for teammates," the teammate types here reference
plugin-scoped subagent definitions. `tools` and `model` carry over from
the definition. `skills` and `mcpServers` do NOT — teammates load
skills/MCP from project + user settings same as a regular session, so
the `/speckit.*` extension commands remain invocable.

**Lead synthesis after team completes:**

```text
1. Wait for all 3 teammates to mark their tasks completed
2. Collect each teammate's final report (read via team mailbox or
   ask the lead to summarize each teammate's findings)
3. Write a consolidated Post-Implementation Checklist entry to the
   workflow file with one row per task (10/11/12/13/14):
     | Task | Status | Findings | Action Needed |
4. Ask the lead: "Clean up the team"
5. Continue to Task 15 (Cleanup) in subagents mode (serial)
```

**Quality gate via `TaskCompleted` hook (optional but recommended):**

Place this in `.claude/hooks/hooks.json` (project-level) to block any
teammate from marking its task complete if Integration Suite reported a
regression:

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

**Failure modes:**

- **A teammate stops on error:** message the teammate directly to
  recover, or spawn a replacement (per Agent Teams troubleshooting
  guidance). If unrecoverable, fall back to `subagents` mode for
  this run and log the failure.
- **Lead shuts down team early:** tell the lead "wait for your
  teammates to complete their tasks before proceeding."
- **Task status lags** (known Agent Teams limitation): if a teammate
  has clearly finished but its task is still `in_progress`, nudge the
  teammate or manually mark complete.
- **Team cleanup fails** (active teammates remain): shut down any
  remaining teammates first, then retry cleanup.

**When to disable teams mode:**

If integration tests share mutable working directories with verify or
verify-tasks (rare but possible — e.g., the verify extension writes
to the same `target/` Rust directory), set `post-impl-mode: subagents`
to serialize and avoid the race condition.

## 3.1 Full Integration / E2E Suite Verification

Integration tests for the spec are created DURING the Implement
phase (the implement-executor agent creates them as part of TDD).
This step runs the FULL suite to catch regressions from other specs.

**Step 1 — Verify spec-specific tests exist:**

```text
Glob("tests/integration/*<spec-name>*")  <- TOOL CALL
Glob("tests/e2e/*<spec-name>*")          <- TOOL CALL
```

If no spec-specific tests exist, the implement-executor failed to
create them. Spawn it again to fix:

```text
Agent(
  subagent_type: "implement-executor",
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

```text
1. Run final verification (BOTH test suites):
   <BUILD> && <TYPECHECK> && <LINT> && <UNIT_TEST> && <INTEGRATION_TEST>
   (use PROJECT_COMMANDS discovered in Step 0)
2. Detect remote: git remote -v
3. Push: git push -u <remote> <branch>
4. Run the pre-PR reviewability gate:
   `skills/speckit-autopilot/scripts/reviewability-gate.sh diff origin/main...HEAD`
   must pass or return a documented transition exception. If it blocks, stop
   and split the spec instead of creating the PR.
5. Generate the PR review packet:
   `skills/speckit-autopilot/scripts/generate-pr-body.sh "$PWD" specs/<number>-<name> .git/speckit-pr-body.md origin/main...HEAD`
   The generator uses the host repository's pull request template when present
   and appends any missing review-packet sections. If no host template exists,
   it uses the plugin fallback template.
6. Create PR:
   gh pr create \
     --title "feat(SPEC-XXX): <Spec Name>" \
     --body-file .git/speckit-pr-body.md
7. Update workflow file with PR URL
8. Commit: "feat(SPEC-XXX): open PR for review"
```

If `gh` is not installed, push the branch and tell the user
to create the PR manually.

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

  Step 3 -- For each unresolved comment:
  a. Read the comment body and the file it references
  b. If code fix needed:
     - Edit the file
     - Bash('<BUILD_CMD> && <TYPECHECK_CMD> && <TEST_CMD> && <INT_TEST_CMD>')
     - Bash('git add <file> && git commit -m
       \"fix(SPEC-XXX): address review - <summary>\"')
     - Bash('git push')
     - Reply: Bash('gh api
       repos/owner/repo/pulls/42/comments
       -f body=\"Fixed in $(git rev-parse --short HEAD).
       <explanation>\"
       -f in_reply_to=<comment_id>')
     - Resolve: Bash('gh api graphql -f query=\"mutation {
       resolveReviewThread(input:{threadId:\"<thread_id>\"})
       { thread { isResolved } }}\"')
  c. If style/format:
     - Bash('<LINT_FIX_CMD>')
     - Commit, push, reply, resolve
  d. If question or false positive:
     - Reply with explanation via gh api, then resolve

  Step 4 -- After addressing all comments, report summary.
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
