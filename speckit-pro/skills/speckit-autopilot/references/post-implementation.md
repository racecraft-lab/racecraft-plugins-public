# Post-Implementation Reference

Detailed procedures for Steps 3.0-3.3 of the autopilot workflow. Run these
items only after all seven SDD phases complete and G7 passes. They remain part
of the same durable plan and are mirrored in `autopilot-state.json`.

Read [Bounded Execution and Verification](./execution-efficiency.md) before
Post dispatch: all tracks share the same reservations. Post
Code Review is the single final integration review. Verify-chain consumes
validated final snapshot evidence rather than running unchanged checks again.
The parent validates genuine native producer observations; a worker's claimed
pass or receipt alone cannot satisfy a gate.

For enabled formal selection, run the `post` checkpoint after the Integration
Suite's producing tests and before that item completes, with `state_file` and
the declared implementation scope. Follow [Selected formal checkpoints](formal-methods.md#later-planning-implementation-and-closeout).
This selected prerequisite is blocking, including when a parallel Post track
fails or other extension findings are advisory. Coverage validation requires
current final/Post evidence and the matching durable state mirror.

On resume, all seven SDD phases being complete is not sufficient to stop.
If any Post item is missing, pending, or in progress, rebuild the durable plan
and continue with the first incomplete Post item. Never report completion while
a Post item is incomplete or `autopilot_continuation.required=true`.

## Contents

<!-- host:codex: Codex numbers its 13-row Post plan -->
- [Canonical Post Items (10-19)](#canonical-post-items-10-19) — full numbered table with runtime + command per row, and the supporting rows beside it
<!-- /host -->
- [How Extension Commands Become Available](#how-extension-commands-become-available) — extension skills installed by `specify extension add`
- [Post-Implementation Parallel Group](#post-implementation-parallel-group) — capability-driven dispatch for tasks 10/11/12/13/14
- [Post Rules](#post-rules) — extension dispatch, parent-session ownership, PR body, missing-extension behavior, pre-final audit
- [3.1 Full Integration / E2E Suite Verification](#31-full-integration--e2e-suite-verification)
- [3.2 PR Creation](#32-pr-creation) — fail-closed single-PR and multi-PR emission
<!-- host:claude: Claude remediates review feedback through a scheduled Copilot loop -->
- [3.3 Copilot Review Remediation Loop](#33-copilot-review-remediation-loop)
<!-- /host -->
<!-- host:codex: Codex remediates review feedback in the parent session -->
- [3.3 Review Remediation Loop](#33-review-remediation-loop)
<!-- /host -->
- [UAT Runbook Generation](#uat-runbook-generation)

<!-- host:codex: Codex numbers its 13-row Post plan -->
## Canonical Post Items (10-19)

Every row below is an item that MUST appear in `update_plan` and
`autopilot-state.json` (Step 1.1's Canonical Post-Implementation Task List). Run
in order; do not collapse or defer.

| # | Item | Requires | Command |
|---|------|----------|---------|
| 10 | Doctor Extension Check | doctor / speckit-utils ext | `$speckit-speckit-utils-doctor` (or `$speckit-doctor`) |
| 11 | Verify Implementation | verify ext | `$speckit-verify` |
| 12 | Verify Tasks Phantom Check | verify-tasks ext | `$speckit-verify-tasks` |
| 13 | Code Review | (none) — built-in | spawn a subagent to independently review the diff `origin/main...HEAD`; report findings by severity |
| 14 | Integration Suite | (none) | `PROJECT_COMMANDS.FULL_VERIFY` or detected full test command, then every populated quality-gate slot (`COMPLEXITY`, `MUTATION`, `DEPENDENCY_RULES`) with `{paths}` (space-separated) and `{paths_csv}` (comma-separated) = changed source files in `origin/main...HEAD` (when that list is empty, skip `COMPLEXITY` and `MUTATION` and record `n/a: no source files changed`); when `MUTATION` is populated, run the hardener once per spec between its run and its block decision per [Hardener Delegation](./hardener-delegation.md) (delegation gateway on `route: "auto"` when `delegate_health` is good, else the primary model; tests-only writes; stop at floor or cap; record the `Hardener` line); a populated slot that still fails blocks; record each result in the Quality Gates table |
| 15 | Final Reviewability Backstop | (none) | deferred helper; use current committed evidence, or hold PR side effects and regenerate the committed reviewability evidence |
| 16 | PR Packet/Body Generation | final backstop proceeded | emit or refresh current `specs/<feature>/.process/pr-packets/<packet-id>.json` with `pr-packet-output` `dry_run` then `apply`; on failure, regenerate the packet from the diagnostics and revalidate |
| 17 | PR Creation | current packet validation passed | single-PR path only when no split route and no current `pr_marker_plan`; `multi-pr-emission` for split-PR routes or marker-ready plans |
| 18 | Review Remediation | (none) | parent session loop — inspect PR feedback, dispatch fixes as needed |
| 19 | Retrospective | retrospective ext | `$speckit-retrospective-analyze` (FINAL STEP) |

### Combined Durable Plan

The numbered 10-19 gates and the supporting task-list rows are both
authoritative. Codex materializes **13 distinct Post rows** in `update_plan` and
`autopilot-state.json`: every numbered gate above, plus these three supporting
evidence steps:

```text
Post: Reviewability Diff Gate
Post: UAT Runbook Generation
Post: PR Body Generation
```

The diff gate and UAT rows feed numbered Post 15; the body row
feeds numbered Post 16. Never delete the supporting rows because the numbered
table groups their ownership, and never delete `Final Reviewability Backstop`
or `PR Packet/Body Generation` because the supporting rows expose their work.

Extension items (10 Doctor, 11 Verify, 12 Verify-Tasks, 19
Retrospective): Spawn `phase-executor` with instructions to run the
`$speckit-*` extension skill for SPEC-XXX and return a summary.
Code Review (13) is built-in — no extension; it runs as the
parallel-group Track B subagent (see below), reviewing the diff and
reporting findings by severity.
Non-extension items 15, 16, 17, 18 and the supporting rows: execute directly in the parent
session. (Item 14 Integration Suite is also non-extension but runs in
the parallel group's Track C verify-chain subagent — see below — not the
parent session.)
<!-- /host -->

## How Extension Commands Become Available

<!-- host:claude: Claude names extension commands with a slash and a dot -->
Commands like `/speckit.verify`, `/speckit.verify-tasks`,
`/speckit.doctor`, and `/speckit.retrospective.analyze` are INSTALLED by
<!-- /host -->
<!-- host:codex: Codex names extension skills with a dollar sign -->
Commands like `$speckit-verify`, `$speckit-verify-tasks`,
`$speckit-doctor`, `$speckit-retrospective-analyze` are INSTALLED by
<!-- /host -->
`specify extension add <name>`. The CLI creates command files in the
project's commands directory (`.codex/commands/` for Codex CLI,
`.claude/commands/` for Claude Code). These commands then appear as
invocable skills.

If Step 0.12 detected the extension in `.registry` as enabled, its
commands ARE available — run the item. If an extension is NOT in
`.registry` and NOT found via search, log a warning and mark that specific
item `skipped: <ext> not installed` (do NOT fail the entire autopilot). The
item MUST still appear in the plan — never drop it silently. Recommend:
`specify extension add <name>`.

**CRITICAL:** Use subagents only for extension-backed items and the
parallel-group tracks defined below. Parent-session items stay in the parent
session so durable state, PR side effects, and final reporting remain under
the orchestrator's control.

## Post-Implementation Parallel Group

<!-- host:claude: Agent Teams is a Claude Code capability -->
This is **Use site 1** of the [Agent Teams use-site map](./agent-teams-integration.md)
in speckit-pro — the first place the autopilot leverages Anthropic's
Agent Teams when available. See that doc for the full map (current +
planned), capability detection, and lifecycle policy across other use
sites (consensus debate, Phase 7 `[P]` tasks, parallel
checklist/analyze).
<!-- /host -->

Tasks 10/11/12/13/14 are independent post-implementation work that
benefits from parallel dispatch. The serial tail after them is
**not** part of that parallel group: each step stays strictly sequential
because of hard dependencies (Reviewability reads the resulting diff, PR
Body needs the reviewability result, PR Creation needs
PR Body, Review Remediation needs the PR URL, Retrospective needs all of
the above).

<!-- host:claude: Agent Teams is a Claude Code capability -->
**Both code paths are parallel.** The autopilot auto-routes based on
`AGENT_TEAMS_AVAILABLE` from Step 0.6's capability probe — there is
no user-facing opt-in. Agent Teams adds inter-teammate messaging and
shared task-list coordination; the subagents fallback achieves the
same wall-clock parallelism via background dispatch.
<!-- /host -->

### Dependency graph

```text
10 Doctor Extension Check        — reads project state, no deps
11 Verify Implementation         ─┐
12 Verify Tasks Phantom Check    ─┼── may share test fixtures
14 Integration Suite             ─┘   (chain serially within this group)
13 Code Review                    — built-in independent review of the diff, no deps

→ all 5 complete before the serial tail begins
```

**Three parallel tracks:**

- Track A: `10 Doctor` (singleton, read-only)
- Track B: `13 Code Review` (singleton, independent review of the diff)
- Track C: `11 Verify` → `12 Verify-Tasks` → `14 Integration Suite`
  (chained — shared test fixtures, serialize within track)

Wall-clock = `max(track A, track B, track C)`.

<!-- host:claude: Claude resolves its Agent or renamed Task launcher, which may be deferred behind ToolSearch -->
**Resolve the native launcher before dispatch:** use `Agent` when the current
Claude tool inventory exposes `Agent`; when the runtime instead exposes the
renamed `Task` tool, use `Task` with the same subagent fields. `TaskCreate`,
`TaskUpdate`, `TaskGet`, and `TaskList` only manage the shared task list. They
never count as worker dispatch and never authorize parent execution of a
track. When `Task` is listed but deferred, first call `ToolSearch` with the
exact query `select:Task`, then issue the three `Task` launches together in
one assistant message. Loading `TaskCreate` or `TaskUpdate` alone does not load
the subagent launcher. If neither `Agent` nor `Task` is available, checkpoint the unavailable
capability instead of running the three tracks in the parent.
<!-- /host -->

<hard_constraints>

**Three-worker ownership before any track work:** The first Post action is to
resolve the host-native subagent launcher and dispatch exactly three workers:
Doctor, Code Review, and Verify. The lead MUST NOT execute any track-owned
Task 10-14 action itself, either before dispatch or while the workers run. If a
worker cannot be launched, checkpoint the unavailable capability and stop; do
not absorb that track into the lead.

**Join barrier before the serial tail:** After dispatching these tracks, the
lead's only permitted actions are waiting for, collecting, and reconciling
their terminal results. Launch acknowledgement is not a result. While any
track result is outstanding, the lead MUST NOT invoke another parent-owned
tool, derive routing, update durable workflow state, create a checkpoint, or
start Task 15 or any later Post item. Consume and attribute every successful,
nonempty final report before the first parent-owned serial action. If the host
cannot wait for or return a terminal result, record a checkpoint with unknown
effects; never continue past the join barrier on a claim, task count, or
launch receipt.

</hard_constraints>

<!-- host:claude: Agent Teams, named Agent calls, and background subagents are Claude Code dispatch mechanics -->
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
being marked complete. Surface the regression to the lead for a localized
repair reservation; the hook does not grant another execution.

**Path A failure modes:**

- **A teammate stops on error:** allow one read-only result/effect reconciliation.
  If effects remain unknown, checkpoint; never fall through to a replacement
  Path B launch. Record known results and owned cleanup.
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

**Background dispatch (single tool turn, using the resolved `Agent` or `Task`
launcher):**

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
               fresh-eyes review. No extension required.")

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

- **A track subagent errors:** independent tracks may finish. Reconcile missing results read-only once; unknown effects require
  a checkpoint, never automatic re-spawn. Record failed/unfinished work honestly.
  Required verification or security failures block PR preparation.
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
<!-- /host -->
<!-- host:codex: Codex has no Agent Teams primitive and dispatches installed or built-in agents with spawn_agent -->
### Codex dispatch: parallel `spawn_agent`

Codex CLI does not have Agent Teams primitives — Codex always uses the
parallel `spawn_agent` pattern below:

- **Track A:** Doctor (item 10) — spawn `phase-executor` for
  `$speckit-doctor`
- **Track B:** Code Review (item 13) — spawn the built-in `default` subagent to
  independently review the diff
  `origin/main...HEAD` and report findings by severity (no extension)
- **Track C:** Verify-chain (items 11 → 12 → 14) — spawn one built-in `default`
  subagent without a model or reasoning-effort override. It reconciles the
  three results sequentially (shared test fixtures); the parent validates
  native proof and executes only checks without reusable evidence

Dispatch the 3 tracks via `spawn_agent`, then loop bounded `wait_agent` calls
until each track's actual result is consumed. A terminal status corroborates
completion but cannot replace the result. Record each result and call
`close_agent` only when the current surface exposes it. If derived
`subagent_slots` is lower, dispatch in cap-bounded waves rather than all at
once. The Lead synthesizes findings
into the workflow file's Post-Implementation Checklist, then continues the serial
tail (15 → 16 → 17 → 18 → 19, with the supporting rows in plan order).
<!-- /host -->

## Post Rules

<!-- host:claude: Claude runs extension commands through a subagent with a slash command -->
- Extension commands run in a subagent with the exact `/speckit.*` command
  and SPEC context, never through `Skill()` in the parent.
<!-- /host -->
<!-- host:codex: Codex runs extension skills in the installed phase-executor with a dollar sigil -->
- Extension commands run in `phase-executor` with the exact `$speckit-*`
  skill sigil and SPEC context.
<!-- /host -->
- Built-in verification, git, push, PR creation, and review polling stay in the
  parent session so the orchestrator owns durable state and final reporting.
- PR creation requires a current schema-valid feature-local packet and the
  repo-relative body file it references. The active `golden_only`
  `pr-packet-output` helper creates or refreshes packet JSON and packet-owned
  body content; `validate-pr-packet-write` persists validation only after
  rerunning current read-only validation.
- Pass every auto-applied fallback and every deferred item to
  `pr-packet-output` as `known_gaps`, so the PR body lists them under
  `## Known Gaps`.
- Missing optional extensions are logged and skipped. Do not fail the entire
  autopilot because an optional extension command is unavailable.
- Never mark the workflow complete until every planned Post item is completed or
  explicitly logged as skipped.
- **Pre-final completion audit:** Before any final user-facing response,
  re-read `autopilot-state.json`, reconcile it with the visible progress plan, and verify
  the canonical Post list. A completion response is forbidden while any `Post:` item is pending,
  in_progress, or missing. `execution_control.disposition=checkpoint_required`
  permits a checkpoint explicitly saying the run is not complete, retaining
  all pending work, consumed budget and unknown effects. `disposition=defer`
  is not a stop: it defers one unit whose allowance is spent. When every runnable
  item has finished and deferred items remain, the read-only `finalize-run`
  helper decides the end, as the phase-execution reference's blocked-action
  rule states. Human UAT is the only gate a run may defer: with every required
  gate green at every PR head, the stack goes ready for review, the top PR body opens with
  `deferred_items` and each of `decisions` in its Deferred / not verified section, and the goal is
  marked complete. Only a required gate that is not green after its escalation
  tiers is one human stop. The end-of-run request is plain text in the final
  message, never a question tool call, and lists every fallback taken and every
  deferred item. Run every
  Post item that does not depend on deferred work first. Otherwise continue
  with the first incomplete item. `Post: Retrospective` remains the final Post item and
  must be completed or explicitly skipped before completion can be reported.
<!-- host:claude: Claude audits the workers it launched through Agent or Task -->
- **Worker sweep before completion:** as part of the same pre-final audit,
  audit every tracked worker and consume every required final report. Cleanup
  is best-effort when the host exposes it; do not retry-loop an already-gone
  worker. A single wait timeout never authorizes interruption; interrupt only a
  confirmed stuck turn, then reconcile read-only and checkpoint unknown effects.
  No interruption authorizes a replacement launch.
<!-- /host -->
<!-- host:codex: list_agents and close_agent are optional Codex collaboration actions -->
- **Agent-thread sweep before completion:** as part of the same pre-final audit,
  call `list_agents` when exposed; otherwise audit tracked dispatch IDs and
  consumed results. Every required dispatch must have a real result. When
  `close_agent` is exposed, close remaining current-run threads best-effort.
  A single wait timeout never authorizes interruption; interrupt only a
  confirmed stuck turn, then reconcile read-only and checkpoint unknown effects.
  No interruption authorizes a replacement launch. Hosted completed threads remain inspectable and are
  managed by the host; their absence of explicit closure is not a failure.
<!-- /host -->
- **Drain final tool work:** give each final local gate one owner and run each
  gate exactly once as a separately attributable foreground command. Consume
  one gate's completed result before starting the next; do not launch an
  overlapping copy while an equivalent gate is pending. Reuse completed gate
  evidence only when its command, configuration, baseline, working directory,
  and relevant source and fixture state are unchanged. A final or checkpoint
  response is forbidden while any started tool item remains in progress; wait
  on that exact native handle for its terminal result and reconcile it first.

## 3.1 Full Integration / E2E Suite Verification

Integration tests for the spec are created DURING the Implement
phase (the implement-executor agent creates them as part of TDD).
This step requires FULL-suite proof to catch regressions from other specs.
Validate the final snapshot's existing result before executing; unchanged G7
proof is reusable only under the shared native-observation contract.

**Step 1 — Verify spec-specific tests exist:**

<!-- host:claude: Claude searches files with the Glob tool -->
```text
Glob("tests/integration/*<spec-name>*")  <- TOOL CALL
Glob("tests/e2e/*<spec-name>*")          <- TOOL CALL
```
<!-- /host -->
<!-- host:codex: Codex searches files with its exposed search tool -->
Search the repository for `tests/integration/*<spec-name>*` and
`tests/e2e/*<spec-name>*` with the current surface's search tool.
<!-- /host -->

If no spec-specific tests exist, the implement-executor failed to
create them. Spawn it again to fix:

<!-- host:claude: Claude dispatches the namespaced plugin agent with Agent and passes a Reference dir -->
```text
Agent(
  subagent_type: "speckit-pro:implement-executor",
  description: "SPEC-XXX missing integration tests",
  prompt: """
    The implementation phase did not create integration
    tests for SPEC-XXX. G7 cannot pass until they exist.

    1. Read existing integration tests to understand the
       pattern (test structure, setup, teardown)
    2. Create spec-specific integration tests covering
       the P1 user stories from spec.md
    3. Follow TDD: write tests -> verify FAIL -> write
       implementation stubs if needed -> verify PASS

    Spec: specs/<number>-<name>/spec.md
    Plan: specs/<number>-<name>/plan.md
    Reference dir: <plugin_root>/skills/speckit-autopilot/references/
  """
)
```
<!-- /host -->
<!-- host:codex: Codex dispatches the installed agent with spawn_agent and waits with wait_agent -->
```text
spawn_agent("implement-executor", prompt="""
  The implementation phase did not create integration
  tests for SPEC-XXX. G7 cannot pass until they exist.

  1. Read existing integration tests to understand the
     pattern (test structure, setup, teardown)
  2. Create spec-specific integration tests covering
     the P1 user stories from spec.md
  3. Follow TDD: write tests -> verify FAIL -> write
     implementation stubs if needed -> verify PASS

  Spec: specs/<number>-<name>/spec.md
  Plan: specs/<number>-<name>/plan.md
""")
wait_agent(...)
```
<!-- /host -->

**Step 2 — Validate or execute the FULL suite:** Use `validate-execution-record`
with actual native observation. On `reusable=false`, execute ALL integration
tests through `execute-verification`, not just the new ones:

For Docker v2, revalidate current inputs and runtime dependencies even if G7
accepted this execution. Pass the same independently retained observation to
the validator; never copy G7's Boolean decision or reconstruct native proof
from retained record files. This validation does not consume the observation.

<!-- host:claude: Claude names the native command placeholder Command -->
```text
Command("<INTEGRATION_TEST command>")     <- TOOL CALL
```
<!-- /host -->
<!-- host:codex: Codex runs commands through its exposed command tool -->
Run `<INTEGRATION_TEST command>` through the current surface's command tool.
<!-- /host -->

If any fail -> reserve localized corrective work in the same ledger. Commit fixes
before proceeding.

**Step 3 — Record results** in the workflow file: integration
test count, pass/fail, regressions found.

## 3.2 PR Creation

Before deriving the PR route, invoke the authoritative `atomicity-route`
read-only helper with both exact path inputs:

```json
{
  "helper_id": "atomicity-route",
  "operation": "atomicity-route",
  "mode": "read_only",
  "inputs": {
    "feature_dir": "<feature-dir>",
    "workflow_file": "<current workflow file>"
  }
}
```

In addition to the established `.process` and `.autopilot-requests`
control trees, the helper excludes only that resolved repository-relative
workflow file and its exact sibling `autopilot-state.json` from change-shape
classification. Never pass a substitute path to hide another change. A
lookalike filename outside those control trees or any other non-control change
remains part of the route decision.

For specs whose atomicity route is `split-PR`, PR creation is multi-PR
emission. The `plan-layers` output is the authoritative source of
review order and slice membership. The post-implementation phase MUST NOT infer, reroute, or re-slice
work from changed files, reviewability warnings, or fallback heuristics.

For non-split routes with no current `pr_marker_plan`, keep the existing
single-PR behavior. For split-PR routes or any current `pr_marker_plan` marked
emission-ready, the previous all-changes PR path is forbidden, even when the
layer/marker plan has only one slice. A one-slice plan still goes through the
same emission contract and opens one slice PR.

```text
1. Validate existing final-snapshot evidence; execute only ineligible checks:
   <BUILD> && <TYPECHECK> && <LINT> && <UNIT_TEST> && <INTEGRATION_TEST>
   then <COMPLEXITY> && <MUTATION> && <DEPENDENCY_RULES> for every
   populated slot, with {paths} and {paths_csv} = changed source files; when
   that list is empty, skip COMPLEXITY and MUTATION and record
   `n/a: no source files changed`
   (use PROJECT_COMMANDS discovered in Step 0; a populated slot
   that fails blocks).
<!-- host:claude: Claude runs the mutation hardener in Phase 7 Final Verification -->
   The hardener already ran once in Phase 7
   Step 4; read its recorded line, do not run it again.
<!-- /host -->
<!-- host:codex: Codex runs the mutation hardener inside Post item 14 -->
   The hardener already ran once inside Post item 14 (Integration Suite);
   read its recorded line, do not run it again.
<!-- /host -->
2. Detect remote: git remote -v
3. Capture the full-suite evidence path under
   specs/<feature>/.process/emission/.
4. Read the persisted layer plan from autopilot-state.json or the workflow
   evidence. It must be the exact `plan-layers` envelope with
   status=ok.
5. Apply the final reviewability boundary using current committed evidence. If
   no current evidence exists, hold `generate-pr-body`, any
   `gh pr create` variant, and `multi-pr-emission` because
   `final-reviewability-backstop` is deferred for installed workflows, and
   regenerate the committed reviewability evidence through the Reviewability Diff Gate task;
   run the repair loop within its allowance, then defer per the Failure Escalation Protocol. Proceed
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
   `autopilot_continuation.required=true`; on gate error, write state only
   and no packet, then rerun the gate; run the repair loop within its allowance, then defer per the Failure Escalation Protocol. Correctness blocks include
   malformed/stale marker state, failed verification, invalid packet, unsafe
   output, unusable gate evidence, invalid JSON, missing status/mode, and stale
   fingerprints.
5b. For a marker-aware proceed result, record
   gate status/mode/exit/evidence path, fingerprint status, ordered marker IDs,
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
   `golden_only` operation and cannot replace the packet. Its complete input
   contract is only `output_path`, `title`, and `sections`; it writes one
   Markdown body and no packet metadata, template markers, validation
   evidence, or PR commands, and its output alone never authorizes PR
   creation. Do not pass it packet JSON, raw gate
   output, full test logs, internal evidence records, or any other undeclared
   field. Include one plain-English `how_to_review` line saying the domain
   checklist boxes under `specs/<feature>/checklists/` are left unticked for the
   reviewer, as the Implement Checklist Gate recorded.
6b. Require the emitted packet's repo-relative `body_file` to be present and
   readable. If body prose needs refinement, edit only the declared editable
   regions described below, then rerun validation before PR creation.
6c. **Refine only declared editable prose in plain English.** If the current
   packet declares editable fields and its existing body contains their exact
   marker pairs, edit only those regions with content drawn from `spec.md`,
   `plan.md`, and the diff. Otherwise leave the body unchanged and fail closed
   if required reviewer content is absent. The packet-owned title and body must
   describe the actual change in strict, unpatronizing, ELI5-style plain
   English. Style rules:
   - **Lead with what the change does, in human terms.** A reader who has never
     seen this repo should understand it at a glance.
   - **No internal jargon.** Drop requirement IDs (`FR-009`), internal layer
     numbers (`Layer 4`), workstream/codenames, and process jargon
     (`consensus`, `tolerance arm`, `gate`). Say what happened in English.
   - **No evidence dump.** Summarize the verified outcome and reviewer-relevant
     risk in plain English. Do not dump commands, file paths, packet
     mechanics, or raw evidence into PR prose: no raw commands, transcripts,
     hashes, grader output, internal state JSON, or exhaustive test logs in
     editable prose; packet-owned evidence fields remain the structured audit
     record.
   - **Keep governance terse and collapsed.** Do NOT promote the
     `<details>Reviewer checklist &amp; scope details</details>` block to
     top-level headings, and do NOT pad it — the auto-filled numbers plus a
     one-line rollback are enough.
   - **Do not touch protected packet-owned sections or markers**, such as
     `How To Review`, `How To UAT`, `Verification`, `Scope`, `Known Gaps`,
     `## UAT Runbook`, or the `speckit-pro-review-packet-source` marker.
   - Do not add template comments, hidden TODOs, or ad hoc HTML comments.
   - Omit **Anything reviewers should know** entirely if there is nothing real
     to say. An empty section is worse than no section.
6d. Validate the packet before any single-PR create attempt with one runner JSON
   request using `helper_id=validate-pr-packet-read-only`, the same operation,
   `mode=read_only`, and
   `inputs.packet_path=specs/<feature>/.process/pr-packets/<packet-id>.json`.
   Consume the current response's `data.stdout_json` in memory and durable
   workflow state. Continue only when `data.stdout_json.status=passed`,
   `data.stdout_json.pr_blocked=false`, and response `data.writes_state=false`.
   If any required packet is absent or invalid, regenerate it with `pr-packet-output` from the validator diagnostics,
   then revalidate; run the repair loop within its allowance, then defer per the Failure Escalation Protocol.
   No PR is created until validation passes. Commit or otherwise checkpoint the packet/body
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
   split evidence. A documentation spec such as `SPEC-704` uses the derived
   lowercase spec scope required by release readiness, `docs(spec-704): ...`,
   for example `docs(spec-704): document the marketplace installation path`;
   `docs(SPEC-704): ...` and `docs(DOC-704): ...` are invalid for that
   spec-backed implementation. Likewise,
   `feat(speckit-pro): ...` is only valid for non-spec plugin changes. Any
   split-contract failure means the single-PR path is forbidden: run
   `multi-pr-emission` with the current layer or marker plan, or route the
   validator output to the packet regenerator and revalidate; run the repair loop within its allowance, then defer per the Failure Escalation Protocol.
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
   persisted current validation evidence before PR side effects. If
   emission or validation fails, route the diagnostics to the packet regenerator and rerun; run the repair loop within its allowance, then defer per the Failure Escalation Protocol.
   For marker emission, `--feature-branch` is the emitted branch prefix. If
   that prefix would collide with an existing parent branch ref, pass a
   non-conflicting prefix through `--feature-branch` and the authoritative
   source spec directory through `--source-feature-dir specs/<feature>`.
   Full verification evidence, scoped evidence, PRS, and MOC files stay under
   the source feature directory while emitted head/base refs use the safe branch
   prefix.
   Live marker emission requires each marker checkpoint to record
   `implementation_checkpoint.head_sha` or
   `implementation_checkpoint.commit_sha`; without those commit SHAs, hold
   branch and PR mutation and record the marker checkpoint commit SHAs through the orchestrator, then rerun;
   run the repair loop within its allowance, then defer per the Failure Escalation Protocol.
7b. Run `detect-stack-manager-plan` in `dry_run` mode per
   [Optional stack manager](stack-manager.md). It qualifies CLI **and** skill,
   repository and owned topology, respects operator fallback, and blocks manager
   switching after mutation. Preserve packet-owned PR creation and refresh;
   selected gh-stack links verified existing PR URLs only after packet checks.
   Resume partial mutation through its recorded manager; never mix managers or
   recreate PRs. After a partial `gh-stack` mutation, block with recovery
   evidence instead of mixing managers, unless read-only proof matches every
   recorded PR: then rerun detection with `previous_decision` and
   `reverify_recovery=true` and retry the existing-PR link through the same
   manager. Defer per the Failure Escalation Protocol when it does not match.
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
9. The per-slice order is exact and fail-closed.
   Apply this exact fail-closed sequence independently to every planned slice;
   do not open any slice PR until all preceding steps for that slice pass:
   1. validate the current `pr_marker_plan`, source fingerprint, marker order,
      checkpoint commit, and final `marker_split`/emission-ready status;
   2. derive that slice's packet ID, title, body path, base/head, and file scope
      from its marker/layer-plan record—never from a branch name, changed-file
      guess, aggregate candidate command, or another slice's packet;
   3. run every required non-UAT gate (the full suite, the checks CI requires,
      and any per-commit identity or evidence check the repository defines) at
      the slice's own head, bottom-up, and run or record the slice's required
      scoped verification; never carry another head's evidence to a slice. On
      a failed required command, hold `gh pr create`; record the command, exit
      status, evidence path, stderr/stdout tail, and keep `next_slice_id` on
      the blocked slice. Then route the failing command to the implement-executor,
      rerun it, and run the repair loop within its allowance, then defer per the Failure Escalation Protocol
      while independent slices keep moving;
   4. emit or refresh that slice's feature-local packet with `pr-packet-output`.
      Its verification cites only the evidence produced at that slice's own
      head. Reject generic foundation/story/slice titles, hardcoded plugin
      scopes for spec PRs, packet-mechanics prose, and raw evidence dumps
      before any slice PR is opened;
   5. Run a fresh `validate-pr-packet-read-only` request, consume its current
      `data.stdout_json` in memory/state, and require `data.writes_state=false`.
      The read-only validator writes no state or validation file. If any
      required packet is absent or invalid, regenerate it with
      `pr-packet-output` from the validator diagnostics and revalidate; no PR
      is created until it passes;
   6. checkpoint the packet/body artifacts so the worktree is clean, then run
      `validate-pr-packet-write`; its apply mode must rerun current read-only
      validation before persisting `validation_result_path`;
   7. Run `validate-pr-workflow-contract` against the packet title and current
      changed-file evidence. Any title, scope, or split-contract failure blocks
      before PR creation;
   8. only then create or refresh the PR with the validated packet's
      `--base`, `--head`, `--title`, and `--body-file` values; and
   9. persist the successful PRS row, regenerated SPEC-MOC table,
      `multi_pr_emission` state, and workflow evidence before advancing
      `next_slice_id`.
   Each slice title and body must describe that marker's own outcome and scope
   in plain English; normalize raw `Foundation`, `User Story`, and `slice`
   labels into a specific change description and derive the lowercase title
   scope from the spec ID. Never reuse an aggregate or neighboring slice
   title/body, and never create first and repair title, body, membership, or
   splitting afterward. A validation failure blocks on the same slice without
   opening or repairing a PR; there is no post-create auto-repair fallback. A
   `multi-pr-emission` candidate command plan is planning evidence,
   not packet validation or authorization for a PR side effect.
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

**Lower-layer fixes:** a fix made on a lower slice must propagate it upward by
merge: merge each fixed branch into the slice above it, bottom-up, never by
rebase or force-push. Then re-verify every affected head: rerun every non-UAT
gate at each head the merge changed and refresh that PR's body evidence, so
`finalize-run` receives a current result for every gate at every head.

<!-- host:claude: Claude remediates review feedback through a scheduled Copilot loop -->
## 3.3 Copilot Review Remediation Loop
<!-- /host -->
<!-- host:codex: Codex remediates review feedback in the parent session -->
## 3.3 Review Remediation Loop
<!-- /host -->

After review edits, renew affected selected formal checkpoints per
[Selected formal checkpoints](formal-methods.md#later-planning-implementation-and-closeout).
Model/catalog/spec/plan changes first require planning reconciliation. Run final
and Post checks after their producing tests before reporting review fixes complete.

<!-- host:codex: Codex has no /loop scheduler, so the parent session runs the remediation loop itself -->
Review Remediation is a parent-session loop: inspect PR feedback, dispatch
fixes as needed, and keep the item open until the feedback is handled.
<!-- /host -->
<!-- host:claude: Claude schedules the remediation loop with the /loop skill and background subagents -->
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

  Step 3 -- Partition by file, parallel across files:

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
<!-- /host -->

## UAT Runbook Generation

Immediately after the Reviewability Diff Gate and before PR-body generation
(between `Post: Reviewability Diff Gate` and `Post: PR Body Generation`), the
orchestrator records UAT runbook status. This row and the generation attempt are
mandatory. Invoke the registered `generate-uat-skeleton` mutation helper in `dry_run` and then
`apply` mode with:

- `spec_path=<feature-dir>/spec.md`
- `output_path=<feature-dir>/.process/uat-runbook.md`
- `workflow_file=<current workflow file>` when available
- `project_commands=<PROJECT_COMMANDS object>`

**Terms lint (advisory).** When `docs/ai/specs/ubiquitous-language.md` exists,
run
<!-- host:claude: Claude resolves plugin files through CLAUDE_PLUGIN_ROOT -->
`resolved_python ${CLAUDE_PLUGIN_ROOT}/scripts/ubiquitous-language-lint.py --base origin/main`
<!-- /host -->
<!-- host:codex: Codex has no plugin-root variable -->
`resolved_python <plugin-root>/scripts/ubiquitous-language-lint.py --base origin/main`
<!-- /host -->
and record its one-line note plus each unmapped identifier (file:line) in the
workflow log. Without the document, record `Terms lint: no terms document`. The
lint exits 0 by design; an unmapped identifier is a suggestion for a term or a
rename, never a gate.

Before `dry_run`, checkpoint the just-recorded terms-lint note and UAT-pending
state by staging only the current workflow and autopilot-state files and committing
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

<!-- host:claude: Claude dispatches the namespaced plugin agent with Agent and passes a Reference dir -->
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

    Reference dir: <plugin_root>/skills/speckit-autopilot/references/

    Apply all three mandatory rewrites — plain-prose Env Setup, concrete
    do-this-see-that per-story steps, and a real (or removed) FR Coverage
    Matrix — per your agent instructions. Edit in place; do not create a
    new file.
  """
)
```
<!-- /host -->
<!-- host:codex: Codex dispatches the installed agent with spawn_agent and waits with wait_agent -->
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
<!-- /host -->

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
invalid, hold PR-body generation and PR creation, route the validator diagnostics to the uat-runbook-author to rewrite the runbook,
and revalidate; run the repair loop within its allowance, then defer per the Failure Escalation Protocol. Missing output after a recorded generation failure is never sent
to validation and never blocks.

If generation or authoring changed the runbook, auto-commit that change:

```text
git add <feature-dir>/.process/uat-runbook.md
git commit -m "docs(SPEC-XXX): add UAT runbook"
```
