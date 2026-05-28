# Dynamic Workflows Adoption Implementation Roadmap

**Upgrade SpecKit-Pro to express its autonomous orchestration as Claude Code Dynamic Workflows — moving phase dispatch, gate-retry, and multi-agent consensus out of model-interpreted prose and into a deterministic JavaScript orchestration script that holds the loop, branching, and intermediate results.** This roadmap covers full Dynamic Workflows adoption for the two non-interactive plugin skills where workflows pay off:

- **`speckit-autopilot`** — the **full autonomous SDD lifecycle**, not merely the 7 SDD phases: a ~13-step pre-flight (capability/command/preset/extension/hook detection), the main loop where each phase is bracketed by user-installed `before_/after_` extension hooks (plus consensus, the G6.5 confidence gate, and gate-retry), and the post-implementation lifecycle (a parallel verify/review group + a serial cleanup → reviewability → self-review → PR → review-loop → retrospective tail). Primary target. See [§ Full Autopilot Lifecycle](#full-autopilot-lifecycle-scope-of-the-port) for the authoritative inventory the specs map onto.
- **`speckit-resolve-pr`** — file-partitioned PR review remediation (parallel fix across file partitions). Self-contained, file-mutating, independent of the autopilot track.

First initiative: port the multi-agent consensus fan-out (the lowest-risk, non-interactive, read-only-analyst pattern) into a workflow behind a capability flag, then extend the same dual-path discipline across the **whole** autopilot lifecycle — the hook-bracketed main loop, parallel implementation tasks, the post-implementation parallel-group + serial-tail, and (independently) parallel PR-review remediation. Extensions, presets, hooks, and the confidence gate are honored inside the workflow, never bypassed.

This document defines the specification roadmap for the Dynamic Workflows Adoption workstream. Each specification is executed end-to-end through the SpecKit workflow (specify → clarify → plan → checklist → tasks → analyze → implement) before moving to the next.

**Current Status:** Research complete (2026-05-28) — Dynamic Workflows feature verified against primary Anthropic docs plus first-party tool evidence from two live in-session workflow runs. Architectural decisions grounded in research are ratified below; per-spec scope decisions are **not yet locked** and require interactive lock-in via `/speckit-pro:grill-me` before scaffolding. No spec in this roadmap is ready for `/speckit-pro:speckit-scaffold-spec` until its scope Q&A completes.

**Parent Branch:** `feat/dynamic-workflows-adoption` (not yet created)
**Per-spec branches:** `007-workflow-capability-detection`, `008-consensus-fanout-workflow`, `009-autopilot-main-loop-workflow`, `010-parallel-implement-workflow`, `011-resolve-pr-workflow`, `012-post-impl-lifecycle-workflow`

> **Feature maturity caveat:** Dynamic Workflows are a Claude Code **research preview** requiring **v2.1.154+**. The feature, its limits, and especially the authoring API may change before GA. Every spec in this roadmap is gated behind capability detection and ships a parallel-subagents fallback — the plugin must never hard-fork onto the preview API. Verification current as of 2026-05-28.

---

## Ratified Architectural Decisions

These decisions are settled by the research and the existing plugin architecture; they constrain every spec below and do **not** need to be re-litigated during per-spec grill-me.

| Decision | Value | Grounding |
|---|---|---|
| Adoption is capability-gated | Add `WORKFLOWS_AVAILABLE` to the Step 0.6 capability probe, mirroring `AGENT_TEAMS_AVAILABLE`. Never assume the feature. | Research preview, v2.1.154+ requirement ([workflows doc](https://code.claude.com/docs/en/workflows)) |
| Workflows are **additive**, never a wholesale replacement | The parallel-subagents fallback (Path B) is retained permanently, not deprecated. | Dynamic Workflows are Claude-Code-only; the Codex integration has no equivalent and stays on Path B forever |
| Delivery vehicle is in-skill inline authoring | `speckit-autopilot` SKILL.md instructs Claude to author-and-run the workflow via the Workflow tool. No plugin-shipped workflow file is required. | The Workflow tool's own opt-in rules include "a skill whose instructions tell you to call Workflow"; proven this session |
| Reuse existing agent definitions | Workflow `agent()` calls pass `{agentType: '<existing-agent>'}` (e.g. `phase-executor`, `codebase-analyst`, `consensus-synthesizer`) rather than duplicating agent files. | Workflow tool `agentType` resolves from the same registry as the Agent tool; honors existing dual-path principle |
| Skill invocation inside workflow agents is supported | Workflow subagents **have the `Skill` tool** and can invoke `speckit.*` skills programmatically (instruction-injection, same mechanism `phase-executor` uses today). | Empirically verified this session via a one-agent probe workflow — `Skill({skill:"speckit.speckit-utils.doctor"})` resolved and injected with no error |
| Single-orchestrator invariant is preserved | The workflow script IS the orchestrator. Workflow `agent()` subagents still cannot nest; Layer 5 deny-lists (`Agent`/`TeamCreate`/`SendMessage`) remain enforced. | Subagents cannot spawn subagents ([sub-agents doc](https://code.claude.com/docs/en/sub-agents)); `workflow()` nesting is one level only |
| No interactive skill is ported | `grill-me` and `speckit-scaffold-spec` stay regular interactive skills. Only non-interactive autopilot phases become workflows. | Workflows take no mid-run user input; only permission prompts pause a run ([workflows doc](https://code.claude.com/docs/en/workflows)) |
| Pre-flight stays in the main session, feeds the workflow via `args` | The ~13-step pre-flight (Step -1 archive sweep, 0.0–0.12: capability probes, `check-prerequisites.sh`, `detect-commands.sh`, `detect-presets.sh`, `resolve-confidence-mode.sh`, constitution validation) runs in the skill's main session. Its resolved outputs — `PROJECT_COMMANDS`, `PRESET_CONVENTIONS`, the resolved hook map, `AGENT_TEAMS_AVAILABLE`, `WORKFLOWS_AVAILABLE`, `CONFIDENCE_GATE_MODE`, template-resolution results — are passed into the workflow as `args`. The workflow does **not** re-run detection. | Cleanly separates detection/IO (main session) from deterministic orchestration (script); `args` is the documented input channel; avoids re-probing on resume |
| Extension hooks run **inside** the workflow at the documented points | The workflow honors `before_<phase>`/`after_<phase>` hooks from `.specify/extensions.yml` by invoking each accepted hook via an `agent()` call (agents have `Bash` + `Skill`) at the same brackets the prose loop uses today. The accept/skip/duplicate rules and the 8 hook events are preserved. | Autopilot only accepts non-destructive hooks (no mid-run input needed); the script body has no Bash, so hooks run through agents — matches the existing acceptance protocol |
| Presets/templates/conventions are honored, not bypassed | The resolved template sources and `PRESET_CONVENTIONS` (from `detect-presets.sh`) are passed in `args` and injected into every executor `agent()` prompt, exactly as the prose loop does. Preset-overridden artifact structures are parsed accordingly. | Presets override (don't merge) templates; executors must know the conventions to produce conformant artifacts |
| Extension-dependent steps skip gracefully | Post-implementation tasks that depend on an extension (Doctor, Verify, Verify-Tasks, Code Review, Cleanup, Retrospective) are marked `skipped: <ext> not installed` inside the workflow when absent — never fail the run. | Mirrors today's runtime extension-availability check; the workflow reads the passed extension registry |

**Key fit finding (corrects the naive read of the "no mid-run input" limit):** Autopilot is *already* non-interactive — it forbids `grill-me` and resolves clarifications via the consensus protocol, and its gates are settings (`stop`/`continue`), not prompts. So the most-cited adoption constraint barely bites the autopilot. It only blocks the interactive scaffolding skills, which were never autonomous.

---

## Table of Contents

1. [Roadmap Overview](#roadmap-overview)
2. [Full Autopilot Lifecycle (Scope of the Port)](#full-autopilot-lifecycle-scope-of-the-port)
3. [Reviewability Contract](#reviewability-contract)
4. [Dependency Graph](#dependency-graph)
5. [Progress Tracking](#progress-tracking)
6. [Specification Sections](#specification-sections)
7. [Decomposition Principles](#decomposition-principles)
8. [Environment & Deployment Context](#environment--deployment-context)
9. [References](#references)

---

## Roadmap Overview

The initiative is decomposed into **6 specifications** across **3 dependency tiers**, organized as a shared foundation feeding two independent skill tracks:

| Tier | Specs | Track | Purpose | Parallelization |
|------|-------|-------|---------|-----------------|
| **1** | SPEC-007 | Foundation | Workflow capability detection + dual-path scaffolding + the **pre-flight→`args` contract** (passes commands, presets, hook map, capability flags, confidence mode into workflows) + `references/workflows-integration.md`. No behavior change. | Sequential (foundation — all specs depend on it) |
| **2** | SPEC-008 | Autopilot | Consensus fan-out as a workflow (analysts → synthesizer). Lowest-risk first behavioral adoption — analysts are read-only. Nests inside the Clarify/Checklist/Analyze phases of SPEC-009. | Sequential (depends on 007) |
| **3** | SPEC-009 | Autopilot | **Full hook-bracketed main loop** as a workflow: 7 phases each with `before_/after_` extension hooks, the G6.5 confidence gate, verify-tasks, gate-retry as a JS loop, and preset-convention propagation. (Segment B.) | Depends on SPEC-008 + live parity trial |
| **3** | SPEC-010 | Autopilot | Parallel `[P]` implementation tasks (Phase 7) with worktree isolation. | Depends on SPEC-009 |
| **3** | SPEC-012 | Autopilot | **Post-implementation lifecycle** as a workflow: the parallel verify/review group (tasks 10–14) + serial tail (15–21), with extension-dependent graceful skipping. (Segment C.) | Depends on SPEC-009 |
| **3** | SPEC-011 | Resolve-PR | `speckit-resolve-pr` file-partitioned remediation as a workflow (parallel fix across file partitions with worktree isolation). | Independent track — depends only on SPEC-007; parallelizable with the autopilot track |

**Execution Order:** SPEC-007 → SPEC-008 → { SPEC-009 → (SPEC-010 ‖ SPEC-012) } ‖ SPEC-011

(`‖` = parallelizable. The Resolve-PR track runs alongside the autopilot track once SPEC-007 lands; SPEC-010 and SPEC-012 both depend on the SPEC-009 main loop but not on each other.)

**Dependency Constraints:**
- SPEC-008/009/010/011/012 all require SPEC-007's `WORKFLOWS_AVAILABLE` probe, the dual-path documentation scaffold, **and the pre-flight→`args` contract** — without the passed commands/presets/hook-map/capability flags, no ported segment can run correctly.
- SPEC-008 (consensus) is sequenced before SPEC-009 (main loop) deliberately: consensus fan-out is non-interactive and read-only at the analyst layer, so it is the safest place to prove the workflow round-trip, parity test, and `agentType` reuse before the loop depends on those patterns.
- SPEC-009 ports the **full hook-bracketed main loop** (Segment B) including per-phase `before_/after_` hooks, the G6.5 confidence gate, and preset-convention propagation — not the bare 7 phases. SPEC-008 nests as its consensus stage.
- SPEC-010 (Phase-7 `[P]` tasks) and SPEC-012 (post-implementation lifecycle) both require SPEC-009's main loop. They are independent of each other and can proceed in parallel. Splitting Phase-7 `[P]` (010) from post-impl (012) keeps each PR within the reviewability budget.
- SPEC-011 (resolve-pr) depends only on SPEC-007. It is a self-contained skill, so it does **not** wait on the autopilot loop — but it should follow SPEC-008's merge so it can reuse the proven worktree-parity fixture discipline. Recommended sequencing: start SPEC-011 after SPEC-008 lands, in parallel with SPEC-009.
- **Go/no-go gate before SPEC-009:** the main-loop-as-workflow rewrite is gated on a live trial — one real spec executed end-to-end as a workflow (incl. its extension hooks) with its artifacts diffed against a Path-B run (Layer 8 parity). If parity or cost regresses, SPEC-009/010/012 are deferred and the plugin keeps consensus-only adoption from SPEC-008. **SPEC-011 is not gated by this trial** — its smaller, self-contained fan-out is validated by its own parity fixture.

---

## Full Autopilot Lifecycle (Scope of the Port)

"Port the autopilot" means the **entire** lifecycle below — not the 7 SDD phases in isolation. This inventory is the authoritative scope; every segment is mapped to the spec that ports it (or to the main session, which keeps it). Sourced from `speckit-autopilot/SKILL.md`, `references/phase-execution.md`, `references/post-implementation.md`, and `references/task-list-canonical.md`.

### Segment A — Pre-flight (Step -1 through Step 0.12) — **stays in the main session**

Runs **before** the workflow is authored; its outputs are passed into the workflow as `args`. Not ported (it is detection/IO, not orchestration).

| Step | Purpose | Feeds workflow as |
|------|---------|-------------------|
| -1 | Archive sweep (if archive extension present) | (side effect; recorded in workflow file) |
| 0.0 | Resolve `SKILL_SCRIPTS` path | script base path |
| 0.1–0.7 | `check-prerequisites.sh` → branch/worktree state | `ON_FEATURE_BRANCH`, `IS_WORKTREE` |
| 0.6 | Load settings + Agent Teams probe + **Workflows probe (SPEC-007)** | `AGENT_TEAMS_AVAILABLE`, `WORKFLOWS_AVAILABLE`, `gate-failure`, `auto-commit`, `consensus-mode` |
| 0.6b | `resolve-confidence-mode.sh` | `CONFIDENCE_GATE_MODE` (advisory/strict) |
| 0.9 | Constitution validation + `/speckit.doctor` + G0 baselines | `PROJECT_COMMANDS` baselines |
| 0.10 | Detect implementation agent | `PROJECT_IMPLEMENTATION_AGENT` |
| 0.11 | `detect-commands.sh` | `PROJECT_COMMANDS` |
| 0.12 | `detect-presets.sh` → presets, extensions, **hook map**, template resolution | `PRESET_CONVENTIONS`, resolved hook map, extension registry |

→ **Covered by SPEC-007** (defines the `args` contract the workflow consumes).

### Segment B — Main loop (per phase, hook-bracketed) — **ported by SPEC-009**

For **each** of the 7 phases, the loop runs: `before_<phase>` hooks → phase executor (invokes `/speckit.*` via Skill) → consensus (Clarify/Checklist/Analyze only) → `after_<phase>` hooks → gate validation + auto-fix → auto-commit → advance.

| Phase | Gate | Hooks (from `.specify/extensions.yml`) | Consensus | Notes |
|-------|------|----------------------------------------|-----------|-------|
| 0 Prerequisites | G0 | — | — | baselines (in pre-flight) |
| 1 Specify | G1 | `before/after_specify` | — | branch-aware |
| 2 Clarify | G2 | `before/after_clarify` | **per session** | SPEC-008 |
| 3 Plan | G3 | `before/after_plan` | — | |
| 4 Checklist | G4 | `before/after_checklist` | **per domain** | SPEC-008 |
| 5 Tasks | G5 | `before/after_tasks` | — | + verify-tasks phantom check; + reviewability-gate `tasks`; optional tasks-to-issues |
| 6 Analyze | G6 | `before/after_analyze` | **once** | SPEC-008 |
| **6.5 Confidence Gate** | **G6.5** | — | remediation if FAIL | `confidence-gate.sh`, iterate ≤3×, advisory/strict |
| 7 Implement | G7 | `before/after_implement` | — | task-level `[P]` dispatch → SPEC-010 |

8 hook events total; accept-non-destructive / skip-duplicate / honor `enabled`+`optional` rules preserved. Gate-retry = "auto-fix ≤2 attempts then honor `gate-failure`."

→ **SPEC-009** ports the loop incl. per-phase hooks, G6.5, verify-tasks, preset-convention propagation. **SPEC-008** nests as the consensus stage. **SPEC-010** is the Phase-7 `[P]` fan-out.

### Segment C — Post-implementation lifecycle (12 canonical tasks) — **ported by SPEC-012**

After G7 passes. Parallel group (already Use Site 1, Path A/B) then a hard-sequential serial tail.

| Task | Step | Group | Extension-gated? |
|------|------|-------|------------------|
| 10 Doctor Extension Check | 3.0 | **Parallel** A | yes (`doctor`/`speckit-utils`) |
| 11 Verify Implementation | 3.0 | **Parallel** C-1 | yes (`verify`) |
| 12 Verify Tasks Phantom Check | 3.0 | **Parallel** C-2 (after 11) | yes (`verify-tasks`) |
| 13 Code Review | 3.0 | **Parallel** B | yes (`review`) |
| 14 Integration Suite | 3.0/3.1 | **Parallel** C-3 (after 12) | no (always) |
| 15 Cleanup | 3.x | Serial | yes (`cleanup`) |
| 16 Reviewability Diff Gate | 3.2 | Serial | no |
| 17 Self-Review (4-question) | 3.x | Serial | no |
| 18 PR Body Generation | 3.2 | Serial | no |
| 19 PR Creation | 3.2 | Serial | no |
| 20 Review Remediation Loop (`/loop`) | 3.3 | Serial | no |
| 21 Retrospective | 3.x | Serial (FINAL) | yes (`retrospective`) |

Wall-clock of the parallel group = `max(A, B, C-chain)`; the serial tail is a hard dependency chain. Extension-gated tasks skip gracefully when the extension is absent. (The reviewer-experience roadmap adds a UAT Runbook step here — SPEC-012 must compose with it.)

→ **SPEC-012** ports the parallel group (Path C) + serial tail. **Note:** Task 20's `/loop` review-remediation reuses the same partition logic as `speckit-resolve-pr` (SPEC-011), but `/loop` itself is a fresh-context recurring mechanism scheduled by the serial tail — it is *not* the in-run workflow and is out of scope for the workflow port (documented in SPEC-012).

### Segment D — Cross-cutting: extensions, presets, hooks, durable state

Honored throughout, not at a single point: hooks bracket every phase (B); presets resolve templates + conventions (A→B); extension availability gates post-impl tasks (C); the workflow file + per-phase `checkpoint.commit` remain the durable/resume state (workflow resume is only a within-session convenience).

→ **SPEC-007** passes the hook map / presets / registry via `args`; **SPEC-009/012** consume and honor them.

---

## Reviewability Contract

Every spec in this roadmap must fit a human review budget before setup and again before PR creation.

- Warn above 400 reviewable LOC, 6 production files, 15 total files, or more than one primary surface.
- Block above 800 reviewable LOC, 8 production files, 25 total files, or more than one primary surface unless this roadmap records a ratified split exception.
- Primary surfaces: schema/migration, API, UI, scheduler/runtime, harness/adapter, seed/config, docs/process.
- PR descriptions are review packets — what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, rollback/flag notes.

**Anticipated split risk (SPEC-009):** the hook-bracketed main loop (per-phase `before_/after_` hooks, gate-retry, the G6.5 confidence gate, verify-tasks, preset propagation) is the largest single spec and is projected at/over the block threshold. The decomposition already isolates consensus (008), the Phase-7 `[P]` fan-out (010), and the entire post-implementation lifecycle (012) into their own specs so SPEC-009 carries only the main-loop bracket. If its projected LOC still exceeds 800 at plan time, split into **009a** (phase loop + per-phase hook execution + preset propagation) and **009b** (gate-retry JS loop + G6.5 confidence-gate iteration + verify-tasks) — record the exception here before scaffolding.

---

## Dependency Graph

```text
SPEC-007 (Capability Detection + Dual-Path Scaffolding + pre-flight→args contract)
    │
    └──► SPEC-008 (Consensus Fan-Out Workflow)   ◄── shared proving ground (read-only)
              │
              ├──────────────────────────────────────────────┐
              │ AUTOPILOT TRACK                                │ RESOLVE-PR TRACK (parallel)
              ▼                                                ▼
   [GO/NO-GO LIVE PARITY TRIAL]                     SPEC-011 (Resolve-PR Remediation Workflow)
              │                                                │
              ▼                                                │
   SPEC-009 (Full Hook-Bracketed Main Loop Workflow)           │
              │  (7 phases + before/after hooks + G6.5)        │
              ├───────────────────────────┐                   │
              ▼                            ▼                   │
   SPEC-010 (Parallel [P]        SPEC-012 (Post-Impl           │
   Implementation Tasks)         Lifecycle: parallel           │
              │                  group + serial tail)          │
              │                            │                   │
              └──────────────┬─────────────┴───────────────────┘
                             ▼
              ─── DYNAMIC WORKFLOWS ADOPTION v1 COMPLETE ───
              (both speckit-autopilot AND speckit-resolve-pr fully on Path C,
               with extensions/presets/hooks honored end-to-end)
```

---

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|------|------|--------|---------------|------------|
| SPEC-007 | Workflow Capability Detection + Dual-Path Scaffolding | ⏳ Pending | `SPEC-007-workflow.md` (not yet scaffolded) | `/speckit-pro:grill-me` to lock scope, then `/speckit-pro:speckit-scaffold-spec SPEC-007` |
| SPEC-008 | Consensus Fan-Out Workflow | ⏳ Pending | `SPEC-008-workflow.md` (not yet scaffolded) | Blocked by SPEC-007 |
| SPEC-009 | Full Hook-Bracketed Main Loop Workflow | ⏳ Pending | `SPEC-009-workflow.md` (not yet scaffolded) | Blocked by SPEC-008 + live parity trial |
| SPEC-010 | Parallel `[P]` Implementation Tasks | ⏳ Pending | `SPEC-010-workflow.md` (not yet scaffolded) | Blocked by SPEC-009 |
| SPEC-012 | Post-Implementation Lifecycle Workflow | ⏳ Pending | `SPEC-012-workflow.md` (not yet scaffolded) | Blocked by SPEC-009 (parallel with SPEC-010) |
| SPEC-011 | Resolve-PR Remediation Workflow | ⏳ Pending | `SPEC-011-workflow.md` (not yet scaffolded) | Blocked by SPEC-007 (parallel track; recommended after SPEC-008) |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

---

## Specification Sections

### SPEC-007: Workflow Capability Detection + Dual-Path Scaffolding

**Priority:** P1 | **Depends On:** None | **Enables:** SPEC-008, SPEC-009, SPEC-010

**Goal:** Detect whether Dynamic Workflows are available on the running Claude Code (`WORKFLOWS_AVAILABLE`), document the third orchestration path, define the **pre-flight→`args` contract** that hands the workflow everything it needs (resolved commands, presets, hook map, capability flags, confidence mode), and establish the routing scaffold — with **zero behavior change** to existing dispatch. This is the foundation every later spec routes through.

**Reviewability Budget:** Primary surface: docs/process (capability probe script + reference doc + SKILL.md Step 0.6 edits + args-contract schema) |
Projected reviewable LOC: ~520 |
Production files: 4 (probe helper in/near `scripts/`, modified Step 0.6 in SKILL.md, args-contract schema doc, Layer 4 test) |
Total files: ~10 (production + new reference doc + Codex-variant note + CLAUDE.md update) |
Budget result: within budget

**Scope:**
- Extend the Step 0.6 capability probe (currently sets `AGENT_TEAMS_AVAILABLE`) to also set `WORKFLOWS_AVAILABLE`, gated on Claude Code version ≥ `2.1.154`. Mirror the existing `claude --version` parse already used for the Agent Teams ≥ `2.1.32` check.
- New reference doc `speckit-pro/skills/speckit-autopilot/references/workflows-integration.md` documenting: the Workflow authoring model (`export const meta` literal first, `agent()`/`parallel()`/`pipeline()`/`phase()`/`log()`), the verified hard limits (16 concurrent / 1,000 total agents, 524 KB script size, `budget.total` as a hard ceiling), session-scoped resume via `resumeFromRunId`, the `agentType`/`schema`/`isolation`/`model` options, and the three-path decision matrix (regular session → parallel subagents/Agent Teams → workflow). This is the single source of truth later specs cite. **Source material already authored:** `docs/ai/specs/dynamic-workflows-authoring-guide.md` — a first-party + empirically-probed authoring guide (verified primitives, gotchas, and worked examples for each spec's fan-out). SPEC-007 formalizes that companion doc into the plugin reference with Layer 1/4 coverage.
- Define the three-path routing rule as an extension of the existing Path A (Agent Teams) / Path B (parallel-subagents fallback) framework in `references/agent-teams-integration.md`: add **Path C (Workflow)** as the preferred path when `WORKFLOWS_AVAILABLE` AND the use-site is non-interactive and fan-out-heavy; Path A/B remain the fallback ladder. Document that Codex always uses Path B (no workflow equivalent).
- **Define the pre-flight→`args` contract** (the load-bearing scaffold for SPEC-009/010/012): pre-flight (Step -1 through 0.12) keeps running in the skill's main session; its resolved outputs are serialized into the workflow's `args` object. Specify the schema: `PROJECT_COMMANDS`, `PRESET_CONVENTIONS`, the resolved **hook map** (`before_/after_<phase>` entries from `.specify/extensions.yml` with their accept/skip/`optional`/`enabled` flags), the **extension registry** (for graceful skipping), template-resolution results, `AGENT_TEAMS_AVAILABLE`, `WORKFLOWS_AVAILABLE`, `CONFIDENCE_GATE_MODE`, `PROJECT_IMPLEMENTATION_AGENT`, `ON_FEATURE_BRANCH`. The workflow consumes `args` and never re-runs detection. Document this contract in `workflows-integration.md`.
- Update the use-site map in `agent-teams-integration.md` to add a "Path C status" column for the 6 existing dispatch sites.
- New Layer 4 unit test for the version-gated probe logic (mirrors existing capability-detection script tests): asserts `WORKFLOWS_AVAILABLE=true` only at version ≥ 2.1.154, false below, and false when the version string is unparseable.
- Update `CLAUDE.md` test-layer/orchestration notes to mention Path C.

**Out of Scope:**
- Any actual workflow authoring or dispatch (deferred to SPEC-008+).
- Codex-variant workflow support (none exists; Codex stays Path B — documented, not implemented).
- Plugin-shipped named workflow files (open question — see References; inline authoring is the ratified vehicle).

**Open Scope Decisions (lock via grill-me before scaffolding):**
- Whether `WORKFLOWS_AVAILABLE` is purely version-gated or also probes for an enablement signal (no enablement env var was found — the community-sourced `CLAUDE_CODE_WORKFLOWS=1` was refuted 0-3; default to version-only unless a first-party signal is identified).
- Whether Path C is preferred over Path A by default when both are available, or whether the plugin keeps Agent Teams primary until the live trial validates workflow parity.

**Key Files:**
- `speckit-pro/skills/speckit-autopilot/SKILL.md` — Modified: Step 0.6 capability probe
- `speckit-pro/skills/speckit-autopilot/references/workflows-integration.md` — New: authoring model + limits + three-path matrix
- `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` — Modified: add Path C, use-site map column
- `speckit-pro/skills/speckit-autopilot/scripts/` — Modified/new: version-gated probe helper
- `speckit-pro/tests/layer4-scripts/` — New: probe unit test
- `speckit-pro/codex-skills/speckit-autopilot/` — Modified: parallel note that Codex remains Path B

---

### SPEC-008: Consensus Fan-Out Workflow

**Priority:** P1 | **Depends On:** SPEC-007 | **Enables:** SPEC-009 (proves the workflow round-trip + parity discipline)

**Goal:** Port the multi-agent consensus protocol's per-phase fan-out (Clarify/Checklist/Analyze unresolved items → routed analysts → synthesizer) into a Dynamic Workflow when `WORKFLOWS_AVAILABLE`, keeping the batched-subagent Path B as the fallback and the permanent Codex path. This is the safest first behavioral adoption: analysts only read/research/report, so a regression cannot corrupt artifacts.

**Reviewability Budget:** Primary surface: harness/adapter (consensus dispatch wiring) |
Projected reviewable LOC: ~600 |
Production files: 4 (workflow-authoring section in `consensus-protocol.md`, SKILL.md dispatch wiring, Layer 7 fixture, Layer 8 parity fixture) |
Total files: ~10 |
Budget result: within budget

**Scope:**
- Add a Path C branch to the consensus dispatch in `references/consensus-protocol.md`: when `WORKFLOWS_AVAILABLE`, the orchestrator authors a workflow that expresses the existing batched fan-out as a pipeline —
  ```js
  const resolved = await pipeline(unresolvedItems,
    item => parallel(routeAnalysts(item).map(a =>
      () => agent(analystPrompt(item, a), {agentType: a, phase: 'Consensus', schema: ANALYST}))),
    (responses, item) => agent(synthPrompt(item, responses),
      {agentType: 'consensus-synthesizer', schema: VERDICT}));
  ```
  with the orchestrator applying artifact edits serially from `resolved` (unchanged from today). The `[category]`-routing (`parse-consensus-categories.sh`) and two-round escape-hatch logic are preserved — round 1 routes a subset, round 2 fans out the rest — expressed as workflow control flow rather than batched-message prose.
- Pass analyst/synthesizer outputs through `schema` so the workflow returns validated objects (no parse step); intermediate analyst text stays in script variables, not the orchestrator context — the core context-isolation win.
- Path B (batched background subagents in one message) is retained verbatim as the fallback and the Codex path; the dispatch site branches on `WORKFLOWS_AVAILABLE`.
- New Layer 7 integration fixture proving the Path C dispatch shape (analysts per item, synthesizer per item, serial edits) parses correctly in replay mode.
- New Layer 8 parity fixture proving Path C and Path B produce equivalent resolution outcomes (same edits applied, same escape-hatch routing) within the existing tolerance framework.

**Out of Scope:**
- Porting the autopilot phase loop itself (SPEC-009).
- Changing the consensus *logic* (routing table, 2-of-3 majority, confidence thresholds) — this spec is a dispatch-mechanism port only, behavior held constant for parity.

**Open Scope Decisions (lock via grill-me before scaffolding):**
- Whether each phase's consensus runs as its own short workflow, or all three consensus phases share one workflow invocation per autopilot run (resume/journaling implications).
- Whether `budget` is wired in to cap consensus fan-out, or left unbounded under the 1,000-agent cap (consensus fan-out is small — `Σ items × routed analysts` — so likely unbounded is fine).

**Key Decisions:**

**[Consensus-First Adoption] Decision (2026-05-28):** Port consensus before the backbone. Analysts are read-only (read code / research / report), so a Path C defect degrades to "worse analysis," never "corrupted artifact." This makes consensus the lowest-blast-radius site to prove the workflow round-trip, `agentType` reuse, schema-validated returns, and the Layer 7/8 fixture discipline that SPEC-009 then depends on.
Alternatives considered: backbone-first (higher blast radius before the round-trip is proven); parallel `[P]` tasks first (mutate files — highest blast radius, wrong place to start).

**[Behavior-Held-Constant Port] Decision (2026-05-28):** This spec changes only the dispatch mechanism, not consensus logic, so Layer 8 parity can assert equivalence against the established Path B baseline. Logic changes, if any, come in a later spec with their own parity baseline.
Alternatives considered: combine a logic refactor with the port (defeats parity — can't tell a dispatch regression from a logic change).

**Key Files:**
- `speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md` — Modified: Path C workflow-authoring section
- `speckit-pro/skills/speckit-autopilot/SKILL.md` — Modified: consensus dispatch branches on `WORKFLOWS_AVAILABLE`
- `speckit-pro/tests/layer7-integration/<class>/consensus-workflow-dispatch/` — New: replay fixture
- `speckit-pro/tests/layer8-parity/` — New: Path C vs Path B parity fixture
- `speckit-pro/codex-skills/speckit-autopilot/references/consensus-protocol.md` — Modified: note Codex stays Path B

---

### SPEC-009: Full Hook-Bracketed Main Loop Workflow

**Priority:** P2 | **Depends On:** SPEC-008 + live parity trial | **Enables:** SPEC-010, SPEC-012

**Goal:** Express the **full main loop (Segment B)** as a Dynamic Workflow when `WORKFLOWS_AVAILABLE` — not the bare 7 phases. The workflow consumes the SPEC-007 `args` contract and, for each phase, runs: `before_<phase>` hooks → phase executor → consensus (where applicable) → `after_<phase>` hooks → gate-retry → auto-commit. It also runs the **G6.5 confidence gate** (iterate ≤3×, advisory/strict) and the post-Tasks **verify-tasks** check, and propagates `PRESET_CONVENTIONS` to every executor. Path B (today's prose orchestration) is the fallback and Codex path. Phase-7 `[P]` parallelization is SPEC-010; post-implementation is SPEC-012.

**Reviewability Budget:** Primary surface: harness/adapter (autopilot main-loop orchestration) |
Projected reviewable LOC: ~800 (at-risk) |
Production files: 5 (workflow body authoring in SKILL.md, phase-execution.md, gate-validation.md, Layer 7 fixture, Layer 8 parity fixture) |
Total files: ~13 |
Budget result: **at/over the block threshold — plan to split into 009a (phase loop + per-phase hooks + preset propagation) and 009b (gate-retry loop + G6.5 confidence gate + verify-tasks)** unless plan-time LOC lands under 800. Record the split exception in the Reviewability Contract before scaffolding.

**Scope:**
- Add a Path C branch to the Step 2 main execution loop in `SKILL.md`: when `WORKFLOWS_AVAILABLE`, the orchestrator authors a workflow whose body iterates the 7 phases **with the full per-phase bracket**. Each phase executor is an `agent()` call using the existing executor as `agentType` (`phase-executor` for Specify/Plan/Tasks; `clarify-executor`/`checklist-executor`/`analyze-executor` for consensus phases), invoking the relevant `speckit.*` skill via the `Skill` tool, with `PRESET_CONVENTIONS` injected into the prompt.
- **Per-phase extension hooks:** before and after each phase, run the accepted `before_/after_<phase>` hooks from the passed hook map. Each hook executes via an `agent()` call (agents have `Bash`+`Skill`) — the script body cannot run Bash directly. Preserve the accept-non-destructive / skip-duplicate / honor-`enabled`+`optional` rules and all 8 hook events. Hooks with no entries are a no-op.
- **Gate-retry as a JS loop:** express `validate-gate.sh` G0–G7 + "auto-fix ≤2 attempts then honor `gate-failure`" as a `while` loop around a `gate-validator` `agent()`; `stop`/`continue` map to `throw`/`continue`.
- **G6.5 confidence gate:** after Analyze, run `confidence-gate.sh` (mode from `CONFIDENCE_GATE_MODE` in `args`); on FAIL iterate ≤3× (focused consensus round on the lowest-scoring criterion → re-synthesize → re-score); then advisory=advance / strict=throw.
- **Verify-tasks** after G5 (phantom-completion check) and the post-Tasks **reviewability-gate `tasks`** call, expressed as `agent()`/script steps.
- Nest the SPEC-008 consensus pipeline inside Clarify/Checklist/Analyze.
- Phases are data-dependent → sequential `await`; `phase()` groups them for progress display.
- Resume/checkpoint: workflow resume is session-scoped, so per-phase `speckit.checkpoint.commit` auto-commit remains the durability mechanism — not workflow journaling.
- New Layer 7 fixture (main-loop dispatch shape **including a hook bracket**) + Layer 8 parity fixture (Path C vs Path B artifacts + hook-execution equivalence for a reference spec **with a test extension installed**).

**Out of Scope:**
- Parallel `[P]` implementation tasks (SPEC-010) and the post-implementation lifecycle (SPEC-012).
- Interactive phases / human sign-off (out of scope by ratified decision — autopilot is non-interactive).
- Any change to gate *thresholds*, hook *acceptance rules*, or phase *logic* — mechanism port only, for parity.

**Open Scope Decisions (lock via grill-me before scaffolding):**
- One workflow for the whole loop vs grouped per-phase workflows (cleanest gate-retry/resume vs finer checkpoint boundaries + smaller blast radius).
- How a destructive or long-running user hook is handled inside a workflow (today autopilot only *accepts* non-destructive hooks; confirm the same filter applies and that an accepted hook never needs mid-run input).
- Whether `budget` caps the run (only very large specs approach the 1,000-agent cap; decide on a budget-aware early-stop).
- Go/no-go criteria for the live parity trial (artifact byte- vs semantic-equivalence; acceptable cost delta; **hook-execution parity** must be part of it).

**Key Decisions:**

**[Gate-Retry as JS Loop] Decision (2026-05-28):** The single biggest qualitative win. Today the "auto-fix ≤2 attempts, then honor `gate-failure`" rule is English prose the model must interpret every run; as a workflow it is a literal `while (attempts < 2 && !pass)`. The "a script, not Claude's judgment, holds the plan" case the feature targets.
Alternatives considered: keep gates in prose even under Path C (forfeits the main determinism benefit).

**[Hooks Run via Agents, Not Script Bash] Decision (2026-05-28):** The workflow honors user `before_/after_<phase>` hooks by dispatching each accepted hook through an `agent()` (which has `Bash`+`Skill`), because the workflow script body has no filesystem/Bash access. The acceptance protocol (non-destructive only, skip duplicates) is unchanged, so no hook needs mid-run input.
Alternatives considered: run hooks in the main session around the workflow (breaks the per-phase bracket — hooks must fire between phases *inside* the loop); skip hooks under Path C (silently drops user-installed behavior — unacceptable, and the whole reason this spec was widened).

**[Checkpoint Durability Stays Per-Phase] Decision (2026-05-28):** Workflow resume is session-scoped; a real run spans hours, so per-phase `speckit.checkpoint.commit` remains the crash-recovery mechanism, not workflow journaling.
Alternatives considered: rely on workflow resume (fails across a Claude Code restart — loses hours of work).

**Key Files:**
- `speckit-pro/skills/speckit-autopilot/SKILL.md` — Modified: Step 2 main-loop Path C branch
- `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` — Modified: Path C phase dispatch **+ per-phase hook execution**
- `speckit-pro/skills/speckit-autopilot/references/gate-validation.md` — Modified: gate-retry-as-JS-loop **+ G6.5 confidence-gate iteration**
- `speckit-pro/tests/layer7-integration/<class>/main-loop-workflow/` — New: replay fixture (incl. hook bracket)
- `speckit-pro/tests/layer8-parity/` — New: main-loop Path C vs Path B parity fixture (incl. hook execution)
- `speckit-pro/codex-skills/speckit-autopilot/` — Modified: note Codex stays Path B

---

### SPEC-010: Parallel `[P]` Implementation Tasks

**Priority:** P2 | **Depends On:** SPEC-009 | **Enables:** Dynamic Workflows Adoption v1 complete

**Goal:** Within the SPEC-009 workflow body, run Phase 7's parallel-safe (`[P]`-tagged) implementation tasks concurrently using `parallel()` with `isolation: 'worktree'` — the purpose-built primitive for parallel file mutation without conflict — replacing the current propose-then-apply background-subagent fallback when `WORKFLOWS_AVAILABLE`.

**Reviewability Budget:** Primary surface: harness/adapter (Phase 7 parallel dispatch) |
Projected reviewable LOC: ~450 |
Production files: 4 (Phase 7 Path C section in `phase-execution.md`, SKILL.md wiring, Layer 7 fixture, Layer 8 parity fixture) |
Total files: ~9 |
Budget result: within budget

**Scope:**
- Add a Path C branch to Phase 7 Step 3 in `references/phase-execution.md`: `[P]`-tagged tasks dispatch as `parallel(tasks.map(t => () => agent(implementPrompt(t), {agentType: 'implement-executor', isolation: 'worktree'})))`; non-`[P]` tasks stay sequential. Each parallel task owns a fresh git worktree, eliminating the file-conflict risk the current fallback mitigates with propose-then-apply.
- Preserve the strict TDD contract (`implement-executor` RED→GREEN→REFACTOR) unchanged inside each worktree task.
- Document the worktree cost (~200-500ms + disk per agent; auto-removed if unchanged) and the rule that worktree isolation is reserved for genuinely `[P]`-safe tasks — which the `[P]` tag already marks.
- New Layer 7 fixture (parallel `[P]` dispatch shape) + Layer 8 parity fixture (Path C worktree run vs Path B propose-then-apply produce equivalent final tree).

**Out of Scope:**
- Re-tagging or re-deriving `[P]` safety (tasks.md `[P]` marking is upstream and unchanged).
- Cross-task coordination beyond worktree isolation (no shared mailbox; tasks are independent by `[P]` definition).

**Open Scope Decisions (lock via grill-me before scaffolding):**
- The worktree merge-back strategy after parallel tasks complete (sequential fast-forward apply vs the existing reviewability-gated diff assembly).
- Concurrency tuning: rely on the runtime `min(16, cores-2)` cap, or cap `[P]` fan-out lower to bound local resource use on developer machines.

**Key Decisions:**

**[Worktree Isolation for [P] Tasks] Decision (2026-05-28):** Use the native `isolation: 'worktree'` option rather than the propose-then-apply fallback when on Path C. This is the use-site where workflows most outperform the existing fallback — the docs cite "a 500-file migration" as canonical, and parallel file mutation without conflict is precisely the propose-then-apply pain point.
Alternatives considered: keep propose-then-apply even under Path C (forfeits the native isolation benefit); no isolation (parallel file writes conflict — unsafe).

**Key Files:**
- `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` — Modified: Phase 7 Step 3 Path C parallel dispatch
- `speckit-pro/skills/speckit-autopilot/SKILL.md` — Modified: Phase 7 wiring
- `speckit-pro/tests/layer7-integration/<class>/parallel-implement-workflow/` — New: replay fixture
- `speckit-pro/tests/layer8-parity/` — New: worktree vs propose-then-apply parity fixture
- `speckit-pro/codex-skills/speckit-autopilot/` — Modified: note Codex stays Path B

---

### SPEC-012: Post-Implementation Lifecycle Workflow

**Priority:** P2 | **Depends On:** SPEC-009 (parallel with SPEC-010) | **Enables:** `speckit-autopilot` fully on Path C end-to-end

**Goal:** Express the **post-implementation lifecycle (Segment C)** as a Dynamic Workflow when `WORKFLOWS_AVAILABLE`: the parallel verify/review group (tasks 10–14) followed by the hard-sequential serial tail (tasks 15–21), with extension-dependent tasks skipping gracefully. This is the existing Use Site 1 (Path A/B, shipped) plus the serial tail, ported to Path C. Path B (batched background subagents / Agent Team) remains the fallback and Codex path.

**Reviewability Budget:** Primary surface: harness/adapter (post-implementation dispatch) |
Projected reviewable LOC: ~600 |
Production files: 4 (Path C section in `post-implementation.md`, SKILL.md Step 3 wiring, Layer 7 fixture, Layer 8 parity fixture) |
Total files: ~11 |
Budget result: within budget

**Scope:**
- Add a Path C branch to Step 3 in `references/post-implementation.md` + `SKILL.md`. When `WORKFLOWS_AVAILABLE`, the orchestrator authors a workflow that runs the **parallel group as a `parallel()` barrier** over the three tracks —
  ```js
  phase('Post: parallel group')
  const [doctor, review, verifyChain] = await parallel([
    () => agent(doctorPrompt,  { agentType: 'speckit-pro:gate-validator', schema: REPORT }),   // task 10
    () => agent(reviewPrompt,  { agentType: REVIEW_AGENT, schema: REPORT }),                    // task 13
    () => runVerifyChain(),    // tasks 11 → 12 → 14 chained serially inside one thunk (shared fixtures)
  ])
  // BARRIER — all five tasks done; then the serial tail:
  phase('Post: serial tail')
  await cleanup(); await reviewabilityGate(); await selfReview()
  await prBody(); await createPR(); await scheduleReviewLoop(); await retrospective()
  ```
  Wall-clock of the group = `max(doctor, review, verifyChain)`; the tail is a strict dependency chain (Cleanup → Reviewability → Self-Review → PR Body → PR Creation → Review Loop → Retrospective).
- **Extension-dependent graceful skipping:** tasks 10/11/12/13/15/21 read the extension registry (passed in `args`); when the required extension is absent, mark the task `skipped: <ext> not installed` and continue — never fail the run. Always-required tasks (14 Integration, 16 Reviewability, 17 Self-Review, 18 PR Body, 19 PR Creation, 20 Review Loop) always run.
- **Compose with the reviewer-experience roadmap:** that roadmap inserts a UAT Runbook step into the serial tail. SPEC-012 must place the UAT step in the same position and not regress it. (Cross-roadmap coordination noted; resolve sequencing at plan time.)
- **Task 20 boundary:** the `/loop` review-remediation it schedules runs in fresh recurring context **after** the workflow returns — it is *not* part of the in-run workflow and stays as-is. The workflow's job ends at scheduling it (+ retrospective). This is the one Segment-C step that is deliberately not a workflow agent.
- New Layer 7 fixture (post-impl dispatch shape: parallel group + serial tail + a skipped extension) + Layer 8 parity fixture (Path C vs Path B equivalent outcomes, incl. graceful skip).

**Out of Scope:**
- The main loop (SPEC-009) and Phase-7 `[P]` tasks (SPEC-010).
- Changing the post-impl dependency graph, task set, or extension-gating logic — mechanism port only, for parity.
- Re-implementing `/loop` as a workflow (it is fresh-context recurring; out of scope by design).

**Open Scope Decisions (lock via grill-me before scaffolding):**
- Whether the verify-chain (11→12→14) runs as one thunk (shared fixtures, simpler) or three pipelined `agent()` calls.
- Whether Self-Review (17) stays an orchestrator-direct step or becomes an `agent()` (it is a 4-question audit written to the workflow file).
- UAT Runbook sequencing relative to the reviewer-experience roadmap (which ships independently).

**Key Decisions:**

**[Barrier Group → Serial Tail] Decision (2026-05-28):** The parallel group is a `parallel()` **barrier** because the serial tail (Cleanup onward) operates on the unified post-implementation state and must wait for all verify/review tracks. The tail is a genuine hard-dependency chain, expressed as sequential `await`s — not a pipeline.
Alternatives considered: pipeline the whole of Segment C (incorrect — the tail's PR creation depends on every verify/review result + cleanup).

**[Graceful Skip Reads the Passed Registry] Decision (2026-05-28):** Extension availability is resolved in pre-flight and passed in `args`; the workflow reads it to skip absent-extension tasks, mirroring today's runtime check. No detection inside the workflow.
Alternatives considered: probe extensions inside the workflow (violates the pre-flight→args contract; re-does IO).

**Key Files:**
- `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` — Modified: Step 3 Path C parallel-group + serial-tail
- `speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md` — Referenced: the 12-task canonical sequence the workflow mirrors
- `speckit-pro/skills/speckit-autopilot/SKILL.md` — Modified: Step 3 Path C wiring
- `speckit-pro/tests/layer7-integration/<class>/post-impl-workflow/` — New: replay fixture (parallel group + serial tail + skip)
- `speckit-pro/tests/layer8-parity/` — New: post-impl Path C vs Path B parity fixture
- `speckit-pro/codex-skills/speckit-autopilot/` — Modified: note Codex stays Path B

---

### SPEC-011: Resolve-PR Remediation Workflow

**Priority:** P2 | **Depends On:** SPEC-007 (parallel track; recommended after SPEC-008) | **Enables:** `speckit-resolve-pr` fully on Path C — second skill complete

**Goal:** Express `speckit-resolve-pr`'s entire remediation flow as a Dynamic Workflow when `WORKFLOWS_AVAILABLE`: fetch unresolved review threads → partition by file → run remediation **in parallel across file partitions** with `isolation: 'worktree'` (serial within a partition) → barrier → serial verify → commit → push → per-thread reply + resolve via `gh`. This fully exploits the feature for the second target skill: the existing Path B (batched background subagents per file partition, Use Site 6 / shipped WS-F1) is retained as the fallback and the permanent Codex path.

**Reviewability Budget:** Primary surface: harness/adapter (resolve-pr remediation dispatch) |
Projected reviewable LOC: ~500 |
Production files: 4 (Path C section in `speckit-resolve-pr/SKILL.md`, `post-implementation.md` §3.3 note, extended Layer 7 fixture 21, Layer 8 parity fixture) |
Total files: ~9 |
Budget result: within budget

**Scope:**
- Add a Path C branch to the "Process Comments — Partition by File, Parallel Across Files" step in `speckit-pro/skills/speckit-resolve-pr/SKILL.md`. When `WORKFLOWS_AVAILABLE`, the orchestrator authors a workflow that expresses the existing partition algorithm as a parallel fan-out —
  ```js
  const partitions = partitionThreadsByFile(unresolvedThreads); // cross-file threads → serial tail
  const fixed = await parallel(partitions.map(p =>
    () => agent(remediatePrompt(p), {agentType: '<remediation-executor>', isolation: 'worktree', schema: FIX})));
  // BARRIER reached — all partitions remediated. Then serial tail on the unified tree:
  //   run project verification → assemble/commit → push → for each thread: gh reply + gh resolve
  ```
  Within a partition (same file) threads remediate **serially** inside the agent (avoids intra-file conflict); across partitions they run **in parallel** with a worktree per partition. Cross-file threads (detected by the existing cross-file-hint scan) are handled in the serial tail, not parallelized — unchanged behavior.
- The post-remediation sequence (verification → commit → push → per-thread `gh` reply + resolve) runs **after** the `parallel()` barrier because it operates on the unified tree and depends on every partition completing — `parallel()` is a barrier, which is the correct primitive here (not `pipeline()`).
- Path B (batched dispatch per file partition in one message) is retained verbatim as the fallback and the Codex path; the dispatch site branches on `WORKFLOWS_AVAILABLE`.
- Extend the existing Layer 7 fixture `21-resolve-pr-parallel-files` to cover the Path C dispatch shape (parallel partitions, serial tail) in addition to the current Path B shape.
- New Layer 8 parity fixture proving Path C (worktree partitions) and Path B (propose-then-apply) produce an equivalent final tree and resolve the same set of threads.

**Out of Scope:**
- Changing the thread-partitioning or cross-file-detection logic (mechanism port only — behavior held constant for parity, same discipline as SPEC-008).
- Any interactive confirmation step (resolve-pr is non-interactive by design — it fixes, commits, pushes, and resolves in one pass).
- Touching the autopilot post-implementation resolve-pr invocation beyond a §3.3 note (the §3.3 path inherits the same Path C branch through the shared skill).

**Open Scope Decisions (lock via grill-me before scaffolding):**
- The remediation-executor `agentType`: reuse an existing agent, or does resolve-pr need a dedicated remediation executor? (Resolve at plan time by inspecting whether today's Path B spawns a named agent or inline subagents.)
- Commit granularity: one squash commit after the barrier, vs per-partition commits merged from worktrees.
- Worktree merge-back strategy for the parallel file fixes (fast-forward apply vs reviewability-gated diff assembly — should match SPEC-010's resolution for consistency).

**Key Decisions:**

**[Barrier After Remediation, Not Pipeline] Decision (2026-05-28):** Use `parallel()` (a barrier) for the partition fan-out, not `pipeline()`. The verify/commit/push/resolve tail operates on the unified working tree and must wait for **all** partitions — this is the textbook case where a barrier is genuinely required (cross-partition dependency on the merged result), unlike SPEC-008's consensus where per-item streaming is fine.
Alternatives considered: pipeline the partitions into the commit stage (incorrect — commit/push can't run per-partition without a merge-back barrier; would corrupt the tree).

**[Worktree-per-Partition Isolation] Decision (2026-05-28):** Each file partition remediates in its own git worktree, eliminating the parallel-write conflict the current propose-then-apply fallback mitigates manually. Same rationale and merge-back discipline as SPEC-010.
Alternatives considered: keep propose-then-apply under Path C (forfeits native isolation); no isolation (parallel writes to the same tree conflict — unsafe).

**[Reuse Use-Site-6 Partition Algorithm] Decision (2026-05-28):** Path C reuses the shipped WS-F1 partition algorithm (scan cross-file hints, partition non-cross-file threads by path, serial within / parallel across) verbatim — only the dispatch mechanism changes. This keeps the Layer 8 parity baseline valid.
Alternatives considered: redesign partitioning for workflows (defeats parity; no evidence the shipped algorithm is wrong).

**Key Files:**
- `speckit-pro/skills/speckit-resolve-pr/SKILL.md` — Modified: Process-Comments step Path C branch
- `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` — Modified: §3.3 note that the resolve-pr invocation inherits Path C
- `speckit-pro/skills/speckit-autopilot/references/workflows-integration.md` — Referenced: shared authoring guide from SPEC-007 (no new authoring doc)
- `speckit-pro/codex-skills/speckit-resolve-pr/SKILL.md` — Modified: note Codex stays Path B
- `speckit-pro/tests/layer7-integration/dispatch-fixtures/21-resolve-pr-parallel-files/` — Modified: add Path C dispatch-shape assertions
- `speckit-pro/tests/layer8-parity/` — New: resolve-pr Path C vs Path B parity fixture

---

## Decomposition Principles

When breaking this initiative into specs:

1. **Capability-gated, never assumed.** Every workflow use-site branches on `WORKFLOWS_AVAILABLE`; the plugin must run correctly with the feature absent. The preview API is never hard-coded as a hard dependency.
2. **Every workflow use-site ships a parallel-subagents fallback (Path B) + a Layer 7 fixture + a Layer 8 parity proof.** This is the existing plugin design principle, now extended to a third path. Path B is permanent, not transitional — it is the Codex execution path forever.
3. **Lowest blast radius first.** Read-only consensus (008) before the backbone (009) before file-mutating parallel tasks (010). Prove the round-trip where a defect cannot corrupt artifacts.
4. **Mechanism port holds behavior constant.** Each adoption spec changes dispatch only, so Layer 8 parity can assert equivalence against the established Path B baseline. Logic changes get their own spec and baseline.
5. **Reuse, don't duplicate.** Workflow `agent()` calls reference existing agent definitions via `agentType`; no new agent files unless a genuinely new role appears.
6. **Honor the whole lifecycle — hooks, presets, and extensions are never bypassed.** A workflow port that drops `before_/after_<phase>` hooks, preset-resolved templates/conventions, the G6.5 confidence gate, or extension-gated post-impl tasks is a *regression*, not a port. Pre-flight detection stays in the main session and feeds the workflow via `args`; the workflow runs hooks via `agent()` and skips absent-extension tasks gracefully. Layer 8 parity must include a run with a test extension installed.

---

## Environment & Deployment Context

### Existing Infrastructure (No Changes Needed)

| Resource | Detail |
|----------|--------|
| Workflow tool | Available in Claude Code ≥ v2.1.154 (research preview); verified working this session (deep-research run + capability probe) |
| Capability probe | Step 0.6 in `SKILL.md` already sets `AGENT_TEAMS_AVAILABLE` from a `claude --version` parse — extended for `WORKFLOWS_AVAILABLE` in SPEC-007 |
| Dual-path framework | `references/agent-teams-integration.md` already defines Path A / Path B with a 6-site use-site map, foreground/background dispatch rules, and one-team-at-a-time lifecycle — Path C extends it |
| Agent roster | `agents/*.md` (phase-executor, clarify/checklist/analyze/implement-executor, codebase/spec-context/domain analysts, consensus-synthesizer, gate-validator) — reused as workflow `agentType`s, no new files |
| Consensus dispatch | `references/consensus-protocol.md` batched fan-out + `parse-consensus-categories.sh` routing — ported to a pipeline in SPEC-008 |
| Gate validation | `scripts/validate-gate.sh` (G0–G7) + `references/gate-validation.md` — wrapped in a JS retry loop in SPEC-009 |
| Resolve-PR partition algorithm | `skills/speckit-resolve-pr/SKILL.md` (Use Site 6, shipped WS-F1) — partition-by-file + serial-within/parallel-across; ported to `parallel()` in SPEC-011 |
| Resolve-PR Layer 7 fixture | `tests/layer7-integration/dispatch-fixtures/21-resolve-pr-parallel-files/` — extended with Path C dispatch assertions in SPEC-011 |
| Pre-flight detection scripts | `scripts/check-prerequisites.sh`, `detect-commands.sh`, `detect-presets.sh`, `resolve-confidence-mode.sh` — stay in the main session; outputs feed the workflow via `args` (SPEC-007 contract) |
| Extension hook protocol | `references/phase-execution.md` §hooks — 8 `before_/after_<phase>` events from `.specify/extensions.yml`, accept/skip/`enabled`/`optional` rules; honored inside the workflow (SPEC-009) |
| Confidence gate | `scripts/confidence-gate.sh` + G6.5 in `gate-validation.md` — iterate ≤3×, advisory/strict; ported in SPEC-009 |
| Post-impl canonical sequence | `references/post-implementation.md` + `task-list-canonical.md` (12 tasks, parallel group + serial tail, extension-gated) — ported in SPEC-012 |
| Test layers | `tests/run-all.sh` covers Layers 1/4/5 by default, `--integration` for Layer 7, Layer 8 parity fixtures under `tests/layer8-parity/` — the parity discipline Path C plugs into |
| Per-phase durability | `speckit.checkpoint.commit` auto-commit — remains the crash-recovery mechanism (workflow resume is session-scoped) |

### Changes Required

| Change | Where | Detail |
|--------|-------|--------|
| `WORKFLOWS_AVAILABLE` probe | `SKILL.md` Step 0.6 + `scripts/` | Version-gated (≥ 2.1.154), mirrors Agent Teams probe (SPEC-007) |
| Pre-flight→`args` contract | `SKILL.md` Step 0.x + `workflows-integration.md` | Serialize commands/presets/hook-map/registry/flags/confidence-mode into workflow `args` (SPEC-007) |
| Path C documentation | new `references/workflows-integration.md` + `agent-teams-integration.md` | Authoring model, verified limits, three-path matrix, args contract (SPEC-007) |
| Consensus Path C branch | `references/consensus-protocol.md` + `SKILL.md` | Pipeline fan-out when `WORKFLOWS_AVAILABLE` (SPEC-008) |
| Main-loop Path C branch | `SKILL.md` Step 2 + `phase-execution.md` + `gate-validation.md` | Hook-bracketed phase loop + gate-retry JS loop + G6.5 + verify-tasks + preset propagation (SPEC-009) |
| Parallel `[P]` Path C branch | `phase-execution.md` Phase 7 | `parallel()` + worktree isolation (SPEC-010) |
| Post-impl Path C branch | `post-implementation.md` Step 3 + `SKILL.md` | `parallel()` group + serial tail + graceful extension skip (SPEC-012) |
| Resolve-PR Path C branch | `speckit-resolve-pr/SKILL.md` + `post-implementation.md` §3.3 | `parallel()` partition fan-out + worktree isolation + serial verify/commit/push/resolve tail (SPEC-011) |

### Local Development Setup

| Requirement | How |
|-------------|-----|
| Claude Code ≥ v2.1.154 | Required to exercise any Path C code; older versions exercise only Path A/B (the test suite must pass on both) |
| Bash + jq | Already required by every existing speckit-pro script |
| GitHub CLI (gh) v2+ | Already required for PR creation in post-implementation |
| Codex CLI | Optional — Codex always runs Path B; useful to verify the fallback path is unaffected |

---

## References

- **Authoring guide (how to write these workflows):** `docs/ai/specs/dynamic-workflows-authoring-guide.md` — first-party Workflow tool spec + empirically-probed primitives, gotchas, and per-spec worked examples; the source material SPEC-007 ships as the plugin reference
- **Research synthesis (this initiative's evidence base):** deep-research run 2026-05-28 — 5 angles, 17 sources, 80 claims → 20 verified; plus first-party in-session evidence from three live workflow runs (99-agent deep-research; Skill-tool capability probe `wf_3687ca2f-bd2`; primitives/environment probe `wf_d0743c15-87a`)
- **Dynamic Workflows announcement:** https://claude.com/blog/introducing-dynamic-workflows-in-claude-code — feature overview, adversarial-convergence framing
- **Workflows documentation:** https://code.claude.com/docs/en/workflows — core model (script holds the loop), behavior & limits (16 concurrent / 1,000 total, no mid-run input, session-scoped resume), when-to-use guidance
- **Sub-agents documentation:** https://code.claude.com/docs/en/sub-agents — no-nesting invariant, plugin-agent ignored fields (`hooks`/`mcpServers`/`permissionMode`), fresh isolated context
- **Headless documentation:** https://code.claude.com/docs/en/headless — user-invoked slash commands unavailable in `-p` (note: the `Skill` tool itself works — verified empirically)
- **Agents (parallelism) documentation:** https://code.claude.com/docs/en/agents — "Run agents in parallel" decision matrix (subagents vs workflows)
- **Costs documentation:** https://code.claude.com/docs/en/costs — Agent Teams ~7x token cost (the contrast case workflows improve on via script-variable intermediate results)
- **Community API reverse-engineering (secondary, superseded by first-party tool evidence):** https://github.com/ray-amjad/claude-code-workflow-creator — DSL signatures; treat as preview-grade
- **Existing dual-path design:** `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` — Path A/B framework, use-site map, design principles Path C extends
- **Constitution:** `.specify/memory/constitution.md`
- **Project Standards:** `CLAUDE.md`, `AGENTS.md`
- **Related existing roadmaps:** `docs/ai/specs/cicd-release-pipeline-technical-roadmap.md`, `docs/ai/specs/reviewer-experience-technical-roadmap.md`
