# Agent Teams Integration — Speckit-Pro Use-Site Map

## Why this doc exists

Anthropic's [Agent Teams](https://code.claude.com/docs/en/agent-teams) is an
experimental Claude Code capability that lets a lead session coordinate
multiple independent Claude Code instances with shared task lists and
peer-to-peer messaging. Speckit-pro **uses Agent Teams wherever the
[official use cases](https://code.claude.com/docs/en/agent-teams#when-to-use-agent-teams)
apply** — and falls back to highly-parallel subagents when Agent Teams
isn't enabled on the user's machine.

This doc is the **canonical map** of every Agent Teams use site in the
autopilot workflow: shipped, designed, and planned. Authors of new
workstreams (D1, D2, E2/E3, …) should consult this doc before extending
multi-agent dispatch.

## Contents

- [Capability detection](#capability-detection) — the Step 0.6 probe that
  drives every routing decision
- [Use-site map](#use-site-map) — table of every place teams help in
  speckit-pro, with status + Anthropic-docs use-case mapping
- [Lifecycle policy](#one-team-at-a-time-lifecycle-policy) — how we
  honor Anthropic's one-team-per-lead limit across multiple use sites
- [Design principles](#design-principles) — the rules every workstream
  must follow when adding a new Agent Teams use site
- [Use-site details](#use-site-details) — one section per use site with
  current status and forward design

## Blocking semantics — foreground vs background subagents

A natural concern when first reading the autopilot architecture:
*"If the orchestrator spawns a phase-executor as a foreground subagent,
the orchestrator is blocked — so how does parallelism work at all?"*
The answer is in the per-dispatch foreground/background choice, plus
the distinction between subagents and Agent Teams.

### The platform contract

Per [Anthropic's sub-agent docs](https://code.claude.com/docs/en/sub-agents#run-subagents-in-foreground-or-background):

> *"**Foreground subagents** block the main conversation until complete.
> Permission prompts are passed through to you as they come up."*
>
> *"**Background subagents** run concurrently while you continue working.
> They run with the permissions already granted in the session and
> auto-deny any tool call that would otherwise prompt."*

The orchestrator picks per dispatch by passing `run_in_background: true`
(or not). The agent's frontmatter `background: true` field would force
background always — none of speckit-pro's agents set this; the
orchestrator decides per call.

### How speckit-pro uses each mode

| Dispatch site | Mode | Rationale |
|---------------|------|-----------|
| Phase executors (Specify → Clarify → … → Implement, one phase at a time) | **Foreground** | Phases are data-dependent — Clarify reads spec.md (Specify), Plan reads both, etc. The orchestrator can't usefully parallelize across phases. Blocking is correct. |
| Consensus analysts (3 routed per unresolved item) | **Background** (`run_in_background: true` × N in one message) | Independent perspectives on the same item; isolated subagent contexts; merge via the synthesizer. |
| Post-impl Path B (Doctor / Code Review / Verify-chain tracks) | **Background** (3 in one message) | Independent work, isolated contexts, merge in the lead. Layer 7 fixture 18 enforces. |
| Phase 7 `[P]` tasks (WS-D2 forward design) | **Background** | Per-task parallelism for `[P]`-tagged tasks; serial for non-`[P]`. |
| Post-impl serial tail (15 Cleanup → 16 Reviewability → 17 PR Body → 18 PR Creation → 19 Loop → 20 Retrospective) | **Foreground** | Hard dependency chain — Cleanup mutates code; Reviewability reads the resulting diff; PR Body needs both; etc. |
| Gate validators | **Foreground** | One gate per phase, sequenced explicitly. |

The architecture intentionally uses foreground for sequentially-dependent
work and background for independent parallel work. The orchestrator
spawning a phase-executor as foreground is not a flaw; it's the right
choice for inter-phase dependencies.

### Within-message parallelism — the key pattern

When the orchestrator needs to fan out N parallel subagents (consensus,
post-impl tracks, `[P]` tasks), it spawns all N **in a single assistant
message**, each with `run_in_background: true`. The next user message
returns all N results together. This is the canonical Anthropic pattern
for parallel subagent dispatch — and it's why all our parallel sites
spawn within one tool turn rather than serially.

### Agent Teams have different blocking semantics

Per [Anthropic's Agent Teams docs](https://code.claude.com/docs/en/agent-teams#context-and-communication):

> *"Each teammate is a full, independent Claude Code session... Automatic
> message delivery: when teammates send messages, they're delivered
> automatically to recipients."*

Teams are **persistent structures**, not blocking calls. Once created
by the lead, teammates run in their own independent sessions. The lead
is not "blocked on the team" — it can continue dispatching work,
foreground-block on a phase executor, or await teammate results at
synchronization points.

This means a team spanning phases 2-6 (Use site 2 forward design) can
coexist with foreground phase-executor dispatches: the team is alive
in the background; teammates self-coordinate on the shared task list
while the lead works through phase executors. The team is checked in
on between phases.

**Open research question** (to be answered during WS-D1/WS-D2
implementation): does spawning a foreground subagent from a team-lead
session truly leave teammates running, or is there a serialization
constraint we haven't found in the docs? Test before designing on this
assumption. The post-impl team (Use site 1) sidesteps the question
entirely — it's created AFTER all phases complete, so no phase
executor is active concurrently with the team.

### Why this isn't a fundamental architectural problem

Three orthogonal axes of parallelism the orchestrator already uses or
will use:

1. **Sequential phases, parallel within-phase** — phase executors run
   foreground (sequential); within each phase, consensus or task fan-out
   uses background batching.
2. **Within-message batching** — N background subagents in one tool
   turn → N parallel concurrent contexts → all results in next message.
3. **Persistent teams** — created by the lead, live independently of
   the lead's foreground/background subagent state, sync at task
   completion boundaries.

These three patterns compose. The phase-executor-blocks-orchestrator
constraint applies only to axis 1, where blocking is the correct
behavior because phases are sequential anyway.

## Capability detection

`AGENT_TEAMS_AVAILABLE` is set at Step 0.6 of the autopilot pre-flight
sequence based on a two-check probe:

1. `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` env var is set
   (per [Anthropic's Agent Teams setup](https://code.claude.com/docs/en/agent-teams#enable-agent-teams))
2. `claude --version` returns ≥ `2.1.32`

See [`prerequisites.md`](./prerequisites.md) §Agent Teams capability probe
for the probe command and fallback semantics. **Users do not opt-in** —
if Anthropic has enabled Agent Teams on the machine, speckit-pro uses it
wherever the use case applies.

## Single orchestrator invariant

**The autopilot main session is THE orchestrator for the entire
workflow run.** All dispatch decisions, all subagent spawns, all
Agent Team creation, all model-routing decisions, all lifecycle
sequencing — happen in this one place.

### Why this invariant exists

Claude Code's platform imposes two hard architectural limits that
together force a single-orchestrator design:

1. **Subagents cannot spawn other subagents.** Per
   [Anthropic's sub-agent docs](https://code.claude.com/docs/en/sub-agents):
   *"Subagents work within a single session."* The `Agent` tool is
   omitted from every speckit-pro phase agent's frontmatter — Layer 5
   tool scoping verifies this on every test run. The runtime, not
   just convention, prevents nesting.
2. **Subagents cannot create Agent Teams.** Per
   [Anthropic's Agent Teams architecture](https://code.claude.com/docs/en/agent-teams#architecture):
   *"Team lead: The main Claude Code session that creates the team,
   spawns teammates, and coordinates work."* Team creation requires
   team-management tools (`TeamCreate`, upgraded `Task`, `sendMessage`,
   `taskUpdate`) which are not in any speckit-pro subagent's allowlist.

Anthropic's own framing makes this a three-tier model that subagents
can NOT collapse:

> *"Subagents work within a single session. To run many independent
> sessions in parallel and monitor them from one place, see
> [background agents](https://code.claude.com/docs/en/agent-view).
> For sessions that communicate with each other, see
> [agent teams](https://code.claude.com/docs/en/agent-teams)."*

A subagent cannot upgrade itself to either tier. Only the main session
can.

### What the orchestrator owns

Every one of these decisions happens in the autopilot main session,
never in a subagent:

| Decision | Where it lives |
|----------|---------------|
| Which executor agent for each phase (specify/plan/tasks → phase-executor; clarify → clarify-executor; etc.) | `SKILL.md` §Phase Dispatch table + Rule 2 |
| Parallel vs sequential dispatch (3 analysts in parallel for consensus; 3 tracks in parallel for post-impl) | `SKILL.md` Rule 6 + `phase-execution.md` Phase-by-Phase Execution |
| Agent Team vs parallel-subagents fallback (Path A vs Path B routing on `AGENT_TEAMS_AVAILABLE`) | `post-implementation.md` §Post-Implementation Parallel Group |
| Model routing for teammates — fit-based (opus for heavy reasoning, sonnet for read-and-report), `effort: max` mandatory on every teammate | Design principle #8 above; encoded in subagent definitions |
| Team lifecycle sequencing (consensus team → `[P]` team → post-impl team, never overlapping) | [Lifecycle policy](#one-team-at-a-time-lifecycle-policy) |
| Consensus dispatch routing (`[codebase]` → codebase-analyst only, `[security]` → all 3, etc.) | `consensus-protocol.md` §Category-Routed Dispatch |
| Gate validation invocation between phases | `SKILL.md` Step 2 + `gate-validation.md` |
| Auto-fix retry vs stop on gate failure | Settings `gate-failure` from Step 0.6 |
| Workflow file updates after every phase | `workflow-file-protocol.md` |
| Error recovery (resume, fallback, escalate to user) | `error-recovery.md` |

### What the orchestrator does NOT delegate

The phase executors and analysts have rich tools (Read, Write, Edit,
Bash, WebSearch, MCP tools) — but the **dispatch authority** does not
leave the orchestrator. A `checklist-executor` runs `/speckit-checklist`,
does its own research, applies its own patches to spec.md — but if
unresolved items remain, it returns a summary; the **orchestrator**
spawns the consensus analysts, not the executor.

This is the flat orchestrator-worker pattern from Anthropic's
[Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)
guide. Layered orchestration (sub-orchestrators that themselves
dispatch) is not possible on Claude Code's runtime; the flat pattern
isn't a design preference, it's the only valid topology.

### Enforcement

- **Layer 5 (tool scoping) — machine-verified:** every agent under
  `agents/*.md` is universally checked for absence of:
  - `Agent` (subagent-nesting prevention — runtime-enforced)
  - `TeamCreate` (no team-lead capability)
  - `SendMessage` (no team-mailbox participation)

  See `tests/layer5-tool-scoping/validate-tool-scoping.sh` §"Single
  orchestrator invariant — universal denial." Run via
  `bash tests/run-all.sh --layer 5`. Any future agent added to
  `agents/` that violates these denials fails the test.

- **Code review:** any PR that adds an agent definition must keep
  these three tools out of the allowlist. The Layer 5 universal
  check catches it automatically, but reviewers should call this out
  explicitly so the design intent is visible in the PR conversation.

- **Runtime self-check:** SKILL.md's §Codex Skill-Selection Guard plus
  the *"If this skill is ever loaded inside a subagent context"*
  refusal in §Architectural Constraint catch the case where this
  skill is mistakenly loaded into a non-main-session.

- **Forward-looking:** if Anthropic adds new team-management tools
  beyond `TeamCreate` and `SendMessage` (e.g., a `TaskClaim` or
  `TeamShutdown` primitive), add them to the universal denylist in
  Layer 5 within the same release window.

### Implications for new workstreams

Any new Agent Teams use site (B1/B2/B3 in the audit; future Use sites
beyond) MUST add its dispatch logic to the **orchestrator** (SKILL.md
+ relevant reference doc), never to a phase executor. The pattern is:

1. Orchestrator detects condition (e.g., `[P]`-tagged tasks in tasks.md)
2. Orchestrator decides path (Agent Team if `AGENT_TEAMS_AVAILABLE`,
   else parallel background subagents)
3. Orchestrator dispatches per the chosen path
4. Orchestrator collects results, applies edits, advances

The phase executor's body NEVER reads `AGENT_TEAMS_AVAILABLE` or
contains conditional dispatch logic. That is the orchestrator's job.

## Use-site map

| # | Use site | Status | Anthropic-docs use case | Implementation reference |
|---|----------|--------|--------------------------|--------------------------|
| 1 | **Post-implementation parallel group** (tasks 10/11/12/13/14) | ✅ Shipped | [Run a parallel code review](https://code.claude.com/docs/en/agent-teams#use-case-examples) | [`post-implementation.md`](./post-implementation.md) §Path A |
| 2 | **Consensus debate** (Clarify/Checklist/Analyze unresolved items) | 📐 Designed; impl pending WS-D1 | [Investigate with competing hypotheses](https://code.claude.com/docs/en/agent-teams#use-case-examples) | This doc §Use site 2 (forward design) |
| 3 | **Phase 7 `[P]` task team** (parallel-safe implementation tasks) | ✅ Shipped (WS-D2, 2026-05-24) | [Cross-layer coordination](https://code.claude.com/docs/en/agent-teams#when-to-use-agent-teams) + [New modules or features](https://code.claude.com/docs/en/agent-teams#when-to-use-agent-teams) | `phase-execution.md` §Phase 7 Step 3 + Layer 7 fixture 19 |
| 4 | **Parallel checklist/analyze** (per-domain or per-finding teammates) | ⏳ Blocked on executor refactor (WS-E2/E3) | [Avoid file conflicts](https://code.claude.com/docs/en/agent-teams#best-practices) — needs propose-then-apply first | This doc §Use site 4 (blocked) |
| 5 | **Cross-item consensus batching** (Clarify/Checklist/Analyze across N unresolved items) | ✅ Shipped (WS-D1, 2026-05-24) | [Subagent → team transition point](https://code.claude.com/docs/en/features-overview#subagent-vs-agent-team) — batched fan-out captures the parallelism win | [`consensus-protocol.md`](./consensus-protocol.md) §Batched Dispatch + Layer 7 fixture 20 |
| 6 | **Parallel PR review remediation** (resolve-pr threads grouped by file) | ✅ Shipped (WS-F1, 2026-05-24) | [Run a parallel code review](https://code.claude.com/docs/en/agent-teams#use-case-examples) inverse — parallel code FIX | `commands/resolve-pr.md` §4 + Codex variant + `post-implementation.md` §3.3 + Layer 7 fixture 21 |

Every use site below has a **subagents fallback** that achieves the same
wall-clock parallelism via `Agent(..., run_in_background: true)` in one
tool turn — Agent Teams adds inter-teammate messaging and shared task
lists on top of that baseline, not in place of it.

## One-team-at-a-time lifecycle policy

Anthropic's [limitations](https://code.claude.com/docs/en/agent-teams#limitations)
state: *"One team at a time: a lead can only manage one team. Clean up
the current team before creating a new one."* Speckit-pro honors this
across multiple use sites by sequencing team lifecycles within a single
autopilot run:

```text
Step 0 (pre-flight)
   ↓
Phase 1 Specify          — no team
   ↓
Phase 2 Clarify          ─┐
Phase 3 Plan             ─┼── consensus team active (Use site 2, WS-D1)
Phase 4 Checklist        ─┤    teammates persist across phases 2-6
Phase 5 Tasks            ─┤    one team handles all consensus rounds
Phase 6 Analyze          ─┘
   ↓ Clean up consensus team
Phase 7 Implement        — `[P]` task team active (Use site 3, WS-D2)
   ↓ Clean up [P] team
Step 3.0 Post-impl       — post-impl team active (Use site 1, ✅ shipped)
   ↓ Clean up post-impl team
Step 3.1+ serial tail    — no team
```

Use sites that won't both be active simultaneously can each have a
dedicated team. Use sites that span overlapping phases (like Use site 2
across phases 2-6) use a **single long-lived team** for the duration of
their span — analysts and the synthesizer accumulate context across
rounds, which is also a quality win (analysts learn the spec as they
go).

## Design principles

Every Agent Teams use site in speckit-pro MUST:

1. **Be capability-detected, not user-opt-in.** No `*-mode` setting.
   Branch on `AGENT_TEAMS_AVAILABLE` from Step 0.6.
2. **Provide a parallel-subagents fallback** that delivers the same
   contract (same parallelism, same outputs). Sequential fallback is
   never acceptable — the whole point of these workstreams is
   parallelism.
3. **Reuse existing plugin subagent definitions as teammate types** per
   [Anthropic's "Use subagent definitions for teammates"](https://code.claude.com/docs/en/agent-teams#use-subagent-definitions-for-teammates).
   Do not duplicate agent files; teammates inherit `tools` and `model`
   from the subagent def.
4. **Honor the one-team-at-a-time policy.** Coordinate with other use
   sites' team lifecycles via the sequencing in [Lifecycle policy](#one-team-at-a-time-lifecycle-policy).
5. **Avoid file conflicts.** Per [Anthropic best practices](https://code.claude.com/docs/en/agent-teams#avoid-file-conflicts):
   *"Two teammates editing the same file leads to overwrites. Break the
   work so each teammate owns a different set of files."* Where the
   work-unit naturally touches shared files (e.g., consensus
   resolutions all edit `spec.md`), use propose-then-apply — teammates
   return patches, lead applies serially.
6. **Have a Layer 7 fixture for the subagents fallback** and (when
   live infrastructure exists) a Layer 8 parity fixture proving teams
   and fallback paths produce equivalent outcomes.
7. **Be documented in this map's use-site table** before merging the
   implementation. Forward design is acceptable; silent additions are
   not.
8. **Route models for fit, not for cost — and always pin max thinking.**
   Per [Anthropic's "Specify teammates and models"](https://code.claude.com/docs/en/agent-teams#specify-teammates-and-models):
   *"Teammates don't inherit the lead's /model selection by default."*
   The lead is opus at `effort: max` (autopilot prereq); each teammate
   inherits the model + effort from its underlying subagent definition
   (see [Anthropic's "Use subagent definitions for teammates"](https://code.claude.com/docs/en/agent-teams#use-subagent-definitions-for-teammates)).
   Every bundled speckit-pro subagent ships with `effort: max` per the
   plugin's policy of **max thinking on every agent, regardless of
   model**. Model choice is per-agent fit (opus for heavy reasoning,
   sonnet for focused read-and-report work, gpt-5.5 + xhigh on Codex)
   — and the thinking budget is never lowered *unless* a Layer 6
   efficiency benchmark empirically proves that the agent reaches
   quality=1.0 at a lower effort on its scored fixtures (see
   `tests/layer6-efficiency/results-codex/*.json`). In that case the
   agent may be dialed down to the cheapest L6-validated 100%-quality
   level. Verified quality always trumps reasoning headroom, but
   unverified reasoning headroom never trumps verified quality.
   Quality is paramount; cost is reduced only where quality is proven
   to be equivalent.

## When to use what — Anthropic decision framework

Per [Anthropic's Agent Teams docs](https://code.claude.com/docs/en/agent-teams#compare-with-subagents) and [the subagent-vs-team comparison](https://code.claude.com/docs/en/features-overview#subagent-vs-agent-team), the canonical decision tree:

| Situation | Pattern | Why | Speckit-pro example |
|-----------|---------|-----|---------------------|
| Single prompt, single file fix | **Regular session** (no agents) | Tool-call overhead outweighs the work | grill-me Q&A loop, coach response, status read |
| 3 independent tasks, no dependencies | **Parallel subagents** (`run_in_background: true` × N in one tool turn) | Fast fan-out, results merge in lead context | Within-item consensus (3 analysts), post-impl Path B (3 tracks) |
| Repeatable workflow with consistent contract | **Subagents with YAML config** | YAML pins tools allowlist + model; same behavior every time | All phase executors (phase-executor, clarify-executor, etc.) |
| Multi-file work that needs cross-teammate coordination | **Agent Teams** | Shared task list + mailbox for inter-teammate messaging | Post-impl Path A (Use site 1); planned Use sites 2/3 |
| Overnight backlog drain | **Headless mode + `--max-budget-usd`** | Budget cap prevents runaway spend on long-running runs | Recommended for autopilot runs scheduled via cron or `/loop` |

**Anti-patterns** (from rody): *"The wrong orchestration mode wastes
both time and tokens. Independent tasks don't need Agent Teams
coordination. Dependent tasks shouldn't run in isolated Agent View
sessions."* Speckit-pro avoids both by branching dispatch by phase
type — Specify/Plan/Tasks are independent enough for serial subagents,
post-impl's 3 tracks are independent enough for parallel-subagents-or-team,
and Phase 7 `[P]` tasks are explicitly annotated for parallel safety
by `/speckit-tasks`.

## Headless / budget-capped operation

For autopilot runs invoked from cron, GitHub Actions, or the
`/loop` review-remediation flow, set a budget ceiling at invocation:

```bash
claude -p --max-budget-usd 25 \
  /speckit-pro:autopilot path/to/workflow.md
```

Anthropic's `--max-budget-usd` flag caps total LLM spend across the
parent session AND all its subagents/teammates. A 7-phase autopilot
run with consensus + parallel post-impl typically spends $5-15;
$25 is a comfortable ceiling that surfaces a clean stop if the run
goes haywire (e.g., infinite gate-fail loop).

For team-using runs (`AGENT_TEAMS_AVAILABLE=true`), the budget cap
applies to ALL teammates collectively — Anthropic's runtime
enforces the limit across the team mailbox. Note that every teammate
runs at `effort: max` per Design Principle #8, so a single run is
more expensive than a cost-optimized configuration would be; the
budget cap is sized to that policy. The user has explicitly accepted
this tradeoff (quality > cost).

**Coach trigger:** users asking *"how do I run autopilot overnight"*
or *"set a budget"* should be routed to this section per the
[coach SKILL.md](../../speckit-coach/SKILL.md) trigger table.

## Use-site details

### Use site 1: Post-implementation parallel group ✅

**Status:** Shipped in [PR #58](https://github.com/racecraft-lab/racecraft-plugins-public/pull/58).

**Anthropic pattern:** [Run a parallel code review](https://code.claude.com/docs/en/agent-teams#use-case-examples).

**Summary:** 3 teammates (Doctor / Code Review / Verify-chain) run
post-implementation tasks 10/11/12/13/14 in parallel after G7 passes.
Lead synthesizes findings, cleans up team, continues serial tail
(tasks 15-20).

**Implementation reference:** [`post-implementation.md`](./post-implementation.md)
§Post-Implementation Parallel Group.

### Use site 2: Consensus debate 📐

**Status:** Designed; implementation pending **WS-D1** (batched
consensus dispatch).

**Anthropic pattern:** [Investigate with competing hypotheses](https://code.claude.com/docs/en/agent-teams#use-case-examples):
*"With multiple independent investigators actively trying to disprove
each other, the theory that survives is much more likely to be the
actual root cause."* This is literally the design intent of the
3-analyst consensus protocol — which today produces isolated reports
and votes via the synthesizer, but does NOT have analysts debate.

**Forward design:**

```text
Team lifecycle: active across phases 2-6 (Clarify, Checklist, Analyze)
Teammates: 4 (one per existing subagent type)
  - codebase-analyst    (reuses plugin subagent def)
  - spec-context-analyst (reuses plugin subagent def)
  - domain-researcher   (reuses plugin subagent def)
  - consensus-synthesizer (reuses plugin subagent def, acts as judge)

Per consensus item:
  1. Lead adds a task to the shared task list with the unresolved item
  2. Routed analysts (per the [<categories>] prefix) CLAIM the task
  3. Analysts post initial findings to the team mailbox
  4. Each analyst is prompted to CHALLENGE the others' findings —
     this is the debate phase (the docs' "scientific debate" example)
  5. Synthesizer reads the full debate, applies the consensus rules
     (2-of-3 majority, escape-hatch, [HUMAN REVIEW NEEDED]), and
     posts the resolution to the workflow file
  6. Lead applies the resolution's Artifact Edit (serially, to avoid
     write conflicts on spec.md/plan.md)
```

**Why teams here adds value over batched subagents:**
The current protocol's failure mode is anchoring — three analysts
asked separately may all latch onto the same plausible-but-wrong
interpretation. Anthropic's "scientific debate" framing directly
addresses this. Teams' inter-teammate messaging is the enabling
primitive.

**Subagents fallback (WS-D1):** batched dispatch across items + within
items — fire all `N × analysts` `Agent(..., run_in_background: true)`
calls in ONE message, await all, then run N synthesizers. No debate,
but identical wall-clock parallelism to today's per-item-serial
dispatch.

**Implementation reference (when shipped):** [`consensus-protocol.md`](./consensus-protocol.md)
§Path A (teams debate) and §Path B (batched parallel subagents).

### Use site 3: Phase 7 `[P]` task team ✅

**Status:** Shipped 2026-05-24 via WS-D2. Implementation reference:
[`phase-execution.md`](./phase-execution.md) §Phase 7 Step 3.
Layer 7 fixture 19 (`19-implement-parallel-p-tasks`) enforces the
"3 parallel `[P]` tasks in ONE assistant message with `isolation:
worktree`" shape. Closed the documented-vs-shipped gap that the
audit B1 finding originally surfaced.

**Anthropic pattern:** [Cross-layer coordination](https://code.claude.com/docs/en/agent-teams#when-to-use-agent-teams):
*"changes that span frontend, backend, and tests, each owned by a
different teammate"* + [New modules or features](https://code.claude.com/docs/en/agent-teams#when-to-use-agent-teams):
*"teammates can each own a separate piece without stepping on each
other."*

**Forward design:**

```text
For each phase group in tasks.md (US1, US2, …):
  Partition tasks into runs:
    - Consecutive [P]-marked tasks form a parallel run
    - Non-[P] tasks form singleton serial runs
  For each parallel run with >1 task:
    Spawn a team with up to 5 teammates (per Anthropic's 3-5 sweet spot)
    Each teammate claims a [P] task; teammates message each other when
      they need to coordinate (e.g., "I'm changing the auth interface,
      heads up")
    Lead waits for all to complete, merges results into COMPLETED_TASKS
    Clean up the team before the next parallel run
  For singleton runs:
    Spawn one implement-executor subagent (no team needed)
```

**Why teams here adds value over batched subagents:**
`[P]` tasks may need light coordination ("did anyone register the new
middleware yet?"). Teams' mailbox gives that primitive. Subagents
fallback works without it but loses the cross-teammate signal.

**Subagents fallback (WS-D2):** dispatch all `[P]` tasks in a parallel
run as `Agent(..., run_in_background: true)` in ONE message. Same
parallelism, no inter-task coordination — relies on `/speckit-tasks`
having correctly identified `[P]`-safe tasks (which is its job).

**Risk:** `/speckit-tasks` `[P]` annotation must be trustworthy.
Mitigation: after a parallel run completes, run TYPECHECK + UNIT_TEST;
on regression, log it and fall back to serial re-run for the offending
group.

**Implementation reference (when shipped):** [`phase-execution.md`](./phase-execution.md)
§Phase 7 — `[P]` Task Dispatch (to be added in WS-D2).

### Use site 4: Parallel checklist/analyze ⏳

**Status:** Blocked on **WS-E2/E3** — `checklist-executor` and
`analyze-executor` write directly to `spec.md` / `plan.md` /
`tasks.md` today. Per [Anthropic's avoid-file-conflicts rule](https://code.claude.com/docs/en/agent-teams#avoid-file-conflicts),
parallel teammates editing the same file overwrite each other.

**Prerequisite:** Refactor `checklist-executor` and `analyze-executor`
to **return patches instead of writing directly**. The orchestrator
applies patches serially. This is the same propose-then-apply pattern
the consensus-synthesizer already uses for Artifact Edits.

**Forward design (after WS-E2/E3 unblock):**

- **Checklist team:** one teammate per domain (api-workaround,
  type-safety, requirements, etc.). Each teammate runs its domain
  checklist, returns gap patches. Lead applies patches serially.
- **Analyze team:** one teammate per finding-group (grouped by file).
  Each teammate remediates its group, returns patches. Lead applies
  serially.

**Subagents fallback:** same propose-then-apply pattern via background
subagents. Already a substantial speedup over today's per-domain
serial dispatch.

**Implementation references (when shipped):** dedicated
`references/parallel-checklist.md` and `references/parallel-analyze.md`
(to be created in WS-E2/E3).

### Use site 5: Cross-item consensus batching ✅

**Status:** Shipped 2026-05-24 via WS-D1. Implementation reference:
[`consensus-protocol.md`](./consensus-protocol.md) §Batched Dispatch.
Layer 7 fixture 20 (`20-consensus-multi-item-batch`) enforces the
"all routed analysts in ONE assistant message" shape with 9
dispatches for 3 `[ambiguous]`-tagged items.

**Anthropic pattern:** [Subagent → team transition point](https://code.claude.com/docs/en/features-overview#subagent-vs-agent-team) — *"If you're running parallel subagents but hitting context limits, or if your subagents need to communicate with each other, agent teams are the natural next step."* Today within-item is correctly parallel (3 analysts via `run_in_background: true`); across N items is serially looped.

**Forward design:**

```text
Parse all "Unresolved for consensus" items from the executor summary.
For each item: parse [<categories>] prefix → routed analyst set Nx.
TOTAL_ANALYSTS = Σ Nx (across all items).

Stage 1 (one assistant message):
  Spawn ALL TOTAL_ANALYSTS Agent(..., run_in_background: true) calls
  for the routed analyst per item.

Stage 2 (one assistant message): await all → spawn N synthesizers
  (one per item, also background since they don't write).

Stage 3 (sequential): apply each synthesizer's Artifact Edit to
  spec.md/plan.md/tasks.md in order. Serial application is mandatory
  to avoid Edit-tool write contention on the same files.
```

**Why this is independent of Use site 2:** Use site 2 (consensus debate
via teams mailbox) is the upgrade path when `AGENT_TEAMS_AVAILABLE`.
Use site 5 is the subagents fallback that delivers parallelism even
without teams. Both should land — site 5 is the cheaper win that
doesn't depend on Anthropic's mailbox API stabilizing.

**Risk:** Concurrent agent count rises (5 items × 2-3 analysts = 10-15
background subagents in one turn). Anthropic's platform handles this,
but worth measuring on long Clarify sessions.

**Implementation reference (when shipped):** [`consensus-protocol.md`](./consensus-protocol.md)
§Phase-Specific Consensus Flows (rewrite outer "for each item" loop as
a batched stage-1/stage-2/stage-3 fan-out).

### Use site 6: Parallel PR review remediation ✅

**Status:** Shipped 2026-05-24 via WS-F1.

**Implementation references:**
- `commands/resolve-pr.md` §4 (Process Comments — Partition by File, Parallel Across Files)
- `codex-skills/speckit-resolve-pr/SKILL.md` (Codex variant)
- `references/post-implementation.md` §3.3 /loop body (same pattern inside the recurring remediation loop)
- Layer 7 fixture 21 (`21-resolve-pr-parallel-files`) — enforces parallel dispatch across file partitions

**Shipped algorithm:** scan threads for cross-file hints; partition
non-cross-file threads by file path; dispatch ALL partitions in one
assistant message via background subagents; serial cross-file tail;
lead posts replies + resolves threads via gh API serially (cheap,
ordered).

**Anthropic pattern:** [Run a parallel code review](https://code.claude.com/docs/en/agent-teams#use-case-examples) inverse — parallel code FIX. Reviewers
look at the same PR through different lenses; remediators FIX the same
PR through partitioned file ownership.

**Forward design:**

```text
After fetching N unresolved PR review threads (via gh GraphQL):
  PARTITION threads by file path.
  Within a partition (same file): remediate threads SERIALLY (avoids
    Edit-tool conflicts on the same file).
  Across partitions (different files): dispatch as parallel
    background subagents in ONE assistant message.

For each partition (parallel-safe):
  Agent(subagent_type: "general-purpose",
        run_in_background: true,
        description: "Resolve PR #N comments on <file>",
        prompt: "Fix the following threads on <file>. After all
                 fixes, run BUILD + TYPECHECK + UNIT_TEST. Commit
                 with message ... Reply to each thread via gh API.
                 Threads: ...")

Lead collects results, then for each result serially calls
gh GraphQL resolveReviewThread (writes are cheap/ordered).

When AGENT_TEAMS_AVAILABLE=true:
  Spawn a review-remediation team with one teammate per file
  partition. Mailbox lets teammates coordinate cross-file changes
  ("I'm changing the auth interface; please update your callers").
```

**Caveat:** Some review comments cross files ("rename function and
update all callers"). Detect via comment body — if cross-file hints
present, serialize that comment; default-parallel for thread-local
fixes.

**Implementation reference (when shipped):**
- `commands/resolve-pr.md` Step 4 ("Process Each Comment") — partition logic
- `codex-skills/speckit-resolve-pr/SKILL.md` — parity
- `references/post-implementation.md` §3.3 `/loop` body — same pattern inside the recurring remediation loop
- Layer 7 fixture `21-resolve-pr-parallel-files`

## Dispatch audit summary — documented vs shipped

A full dispatch-point audit (24 entry points across all skills) was
performed against the design principles above. Headline findings:

| Finding | Type | Status |
|---------|------|--------|
| Phase 7 `[P]` parallel reads as live in phase-execution.md but is NOT shipped (use-site map admits, no fixture exists) | Documented ≠ shipped contradiction | Surface in WS-D2 PR |
| Consensus across-items serial (within-item correct) | B finding (audit) | Use site 5 above |
| resolve-pr per-comment serial (parallel-safe partitions exist) | B finding (audit) | Use site 6 above |
| Layer 7 fixtures 13/14/15 cap `max_dispatch_count: 1-2`, would FALSE-PASS regressions in B1/B2/B3 | Test coverage gap | Add companion fixtures 13b/19/20/21 |

**24 dispatch points classified as "already optimal"** including
per-phase executors, within-item consensus parallel, post-impl Path B
parallel group, post-impl serial tail (real dependency chain),
gate-validator, grill-me HITL, and all the no-dispatch skills
(coach/install/upgrade/status). The subagent-nesting prevention via
tools-list omission is runtime-enforced, not just convention.

**Recommended sequencing** (from highest-value, lowest-effort first):
1. Use site 5 (consensus batching) — fires multiple times per phase
2. Use site 6 (resolve-pr parallel) — direct user benefit, new workstream
3. Use site 3 (Phase 7 `[P]`) — biggest single-spec wall-clock win, larger code change
4. Use site 2 (consensus debate) — gated on Anthropic mailbox stabilization
5. Use site 4 (parallel checklist/analyze) — gated on executor refactor (WS-E2/E3)

## Source-of-truth references

- [Agent Teams overview](https://code.claude.com/docs/en/agent-teams)
- [When to use agent teams](https://code.claude.com/docs/en/agent-teams#when-to-use-agent-teams)
- [Start your first agent team](https://code.claude.com/docs/en/agent-teams#start-your-first-agent-team)
- [Control your agent team](https://code.claude.com/docs/en/agent-teams#control-your-agent-team)
- [Best practices](https://code.claude.com/docs/en/agent-teams#best-practices)
- [Subagent vs Agent team comparison](https://code.claude.com/docs/en/features-overview#subagent-vs-agent-team) — *"Transition point: If you're running parallel subagents but hitting context limits, or if your subagents need to communicate with each other, agent teams are the natural next step."*
