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

## Use-site map

| # | Use site | Status | Anthropic-docs use case | Implementation reference |
|---|----------|--------|--------------------------|--------------------------|
| 1 | **Post-implementation parallel group** (tasks 10/11/12/13/14) | ✅ Shipped | [Run a parallel code review](https://code.claude.com/docs/en/agent-teams#use-case-examples) | [`post-implementation.md`](./post-implementation.md) §Path A |
| 2 | **Consensus debate** (Clarify/Checklist/Analyze unresolved items) | 📐 Designed; impl pending WS-D1 | [Investigate with competing hypotheses](https://code.claude.com/docs/en/agent-teams#use-case-examples) | This doc §Use site 2 (forward design) |
| 3 | **Phase 7 `[P]` task team** (parallel-safe implementation tasks) | 📐 Designed; impl pending WS-D2 | [Cross-layer coordination](https://code.claude.com/docs/en/agent-teams#when-to-use-agent-teams) + [New modules or features](https://code.claude.com/docs/en/agent-teams#when-to-use-agent-teams) | This doc §Use site 3 (forward design) |
| 4 | **Parallel checklist/analyze** (per-domain or per-finding teammates) | ⏳ Blocked on executor refactor (WS-E2/E3) | [Avoid file conflicts](https://code.claude.com/docs/en/agent-teams#best-practices) — needs propose-then-apply first | This doc §Use site 4 (blocked) |

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

### Use site 3: Phase 7 `[P]` task team 📐

**Status:** Designed; implementation pending **WS-D2** (honor `[P]`
markers in tasks.md).

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

## Source-of-truth references

- [Agent Teams overview](https://code.claude.com/docs/en/agent-teams)
- [When to use agent teams](https://code.claude.com/docs/en/agent-teams#when-to-use-agent-teams)
- [Start your first agent team](https://code.claude.com/docs/en/agent-teams#start-your-first-agent-team)
- [Control your agent team](https://code.claude.com/docs/en/agent-teams#control-your-agent-team)
- [Best practices](https://code.claude.com/docs/en/agent-teams#best-practices)
- [Subagent vs Agent team comparison](https://code.claude.com/docs/en/features-overview#subagent-vs-agent-team) — *"Transition point: If you're running parallel subagents but hitting context limits, or if your subagents need to communicate with each other, agent teams are the natural next step."*
