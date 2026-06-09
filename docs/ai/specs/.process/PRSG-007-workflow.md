# SpecKit Workflow: PRSG-007 — Atomicity-test router (read-only classifier)

**Template Version**: 1.0.0
**Created**: 2026-06-08
**Purpose**: Autopilot-ready workflow for PRSG-007. The phase prompts below were enriched from the Grill Me interview (14 questions) captured in the Design Concept doc.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/PRSG-007-design-concept.md
```

Re-read it before each phase if you need to disambiguate a prompt. The
Specify and Clarify Prompts below were populated from that interview,
so the design concept doc is the source of truth for any decision
captured during scoping.

> **Note:** Grill Me is human-in-the-loop only. It is **not** part of
> the autopilot loop. Once the workflow file is populated and autopilot
> begins, clarifications happen via `/speckit-clarify` and the
> consensus protocol — never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | 15 FRs, 2 US (P1), 9 acceptance scenarios, 7 SCs; 0 [NEEDS CLARIFICATION]. Branch-aware (no new branch/dir). |
| Clarify | `/speckit-clarify` | ⏳ Pending | Open Questions: branch-by-abstraction trigger, JSON schema, roadmap gap-closure |
| Plan | `/speckit-plan` | ⏳ Pending | |
| Checklist | `/speckit-checklist` | ⏳ Pending | Recommended domains: error-handling, api-contracts (the JSON output contract) |
| Tasks | `/speckit-tasks` | ⏳ Pending | One L4 fixture per change class; Codex-mirror tasks |
| Analyze | `/speckit-analyze` | ⏳ Pending | |
| Implement | `/speckit-implement` | ⏳ Pending | |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates (SpecKit Best Practice)

Each phase requires **human review and approval** before proceeding:

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | All user stories clear, no `[NEEDS CLARIFICATION]` markers remain |
| G2 | After Clarify | The 3 Open Questions resolved (or deferred with defaults) |
| G3 | After Plan | bash+jq approach approved; constitution gates pass; no edit to the shipped reviewability-gate.sh |
| G4 | After Checklist | All `[Gap]` markers addressed |
| G5 | After Tasks | Every FR + user story has a task; Codex-mirror tasks present; one L4 fixture per change class |
| G6 | After Analyze | No `CRITICAL`; design-concept drift checked |
| G7 | After Each Implementation Phase | L1 + L4 green; validate-codex-skills.sh green |

---

## Prerequisites

### Constitution Validation

**Before starting any workflow phase**, verify alignment with the project constitution (`.specify/memory/constitution.md`):

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| II. Script Safety | `#!/usr/bin/env bash` + `set -euo pipefail`; quoted vars; `chmod +x`; `bash -n` clean | `bash -n scripts/atomicity-route.sh` |
| IV. Test Coverage | New script has a Layer-4 unit test; L1 passes | `bash tests/speckit-pro/run-all.sh --layer 4` / `--layer 1` |
| VI. KISS / YAGNI | Simplest approach; duplicate a small matcher rather than abstract; no probe over-build | Code review + ~400 LOC budget |

**Constitution Check:** ✅ (G0 — 2026-06-08) — baseline `bash tests/speckit-pro/run-all.sh` green: **1958/1958** (L1 459+428, L4 881, L5 190). Script-safety / test-coverage gates re-checked at implement time against the new `atomicity-route.sh`. PROJECT_COMMANDS for this repo = `bash tests/speckit-pro/run-all.sh --layer 1` / `--layer 4` (detect-commands returns N/A — no Node/Rust/Go stack).

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | PRSG-007 |
| **Name** | Atomicity-test router (read-only classifier) |
| **Branch** | `prsg-007-atomicity-router` |
| **Dependencies** | PRSG-006 (benefits — reviewability budget; no hard dependency, no internal call) |
| **Enables** | PRSG-008 (layer-planner consumes the route), PRSG-009 (multi-PR emission) |
| **Priority** | P1 — Phase 4 engine MVP |

### Success Criteria Summary

- [ ] `speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh <feature-dir>` emits a single JSON object to stdout (`route`, `releasable`, `signals`/`hints`, `warnings`) and writes nothing.
- [ ] `route ∈ {split-PR, one-navigable-PR, branch-by-abstraction, single-atomic-PR, out-of-scope}`; default/abstain = `one-navigable-PR`; precedence: hard-atomic→`single-atomic-PR`; proven-safe-additive-with-seams→`split-PR`; else→`one-navigable-PR`; not-applicable→`out-of-scope`.
- [ ] Splittability decided by **structural seams**, not LOC.
- [ ] Advisory-only: **always exit 0** on a successful classification; **exit 2** only on usage / unreadable input. Never a gate.
- [ ] Safety-floor probes implemented to full depth: hard-atomic overrides + `tasks.md`-shape + additive-vs-modify grep. Contextual probes (flag-system / release-cadence / consumer-locality) emitted as **advisory hints only**.
- [ ] `releasable: true|false` + a `warnings[]` entry when destructive-migration / concurrency signatures are detected ("CI-green ≠ releasable").
- [ ] Generic path/surface classification (TS/SQL/UI/migrations/config/docs), via a **small duplicated matcher** — the shipped `reviewability-gate.sh` is NOT edited.
- [ ] A new `## Atomicity Route` section added to `speckit-pro/skills/speckit-coach/templates/workflow-template.md`.
- [ ] The post-Tasks router step documented in the Claude `speckit-autopilot/SKILL.md` + the relevant `references/` doc AND mirrored into `codex-skills/speckit-autopilot/SKILL.md`; `validate-codex-skills.sh` (L1) stays green.
- [ ] Layer-4 unit test `tests/speckit-pro/layer4-scripts/test-atomicity-route.sh` with **one fixture per change class**; Layer-1 structural validation passes.

---

## Phase 1: Specify

**When to run:** At the start. Focus on **WHAT** and **WHY**. Output: `specs/prsg-007-atomicity-router/spec.md`

### Specify Prompt

```bash
/speckit-specify

## Feature: Atomicity-test router (read-only classifier) — PRSG-007

### Problem Statement
Phase 4 of PR-Size Governance is the split-PR engine. Before any PR emission is
wired (PRSG-008 layer-planner, PRSG-009 multi-PR emission), we need the "brain"
that decides whether a change can be split SAFELY. PRSG-007 ships that brain as a
read-only classifier: given a feature's tasks.md/plan.md/spec.md, it emits a routing
decision. It changes nothing and blocks nothing — it only classifies and records.

### Users
The speckit-autopilot workflow (Claude Code + Codex), which runs the classifier
after the Tasks phase (gate G5) and records the route in the workflow file for the
downstream layer-planner and emission specs to read.

### User Stories
- [US1] Classifier: emit a route ∈ {split-PR, one-navigable-PR, branch-by-abstraction,
  single-atomic-PR, out-of-scope}. Detection order: tasks.md shape →
  additive-vs-modify (grep UPDATE/DELETE/DROP/CHECK vs CREATE TABLE / nullable adds)
  → flag-system probe → release cadence → consumer locality. Splittability is decided
  by STRUCTURAL SEAMS (multiple independent additive capabilities/surfaces), NOT by LOC.
- [US2] Hard-atomic + releasability detect-and-route: hard-atomic override
  (exported-symbol rename, global version pin, destructive migration,
  mutual-exclusion/auth/payment primitive, out-of-tree contract break) → single-atomic-PR.
  Detect destructive-migration / concurrency signatures → emit releasable:false +
  a warning that CI-green ≠ releasable for those classes.

### Key Decisions (from the Design Concept interview)
- Read-only: emit ONE JSON object to stdout; write nothing (Q1).
- The speckit-autopilot SKILL — not the script — records the route into the workflow
  file's "## Atomicity Route" section (Q2, Q11).
- Advisory-only: always exit 0 on success, exit 2 on usage/unreadable; never a gate (Q3).
- Generic across stacks, like reviewability-gate.sh's surface taxonomy (Q4).
- Default/abstain route = one-navigable-PR; never auto-split on uncertainty (Q6).
- Runs after the Tasks phase / G5 (Q8). Independent of reviewability-gate.sh — no
  internal call (Q9). Splittability = seams, not size; the autopilot combines this
  route with reviewability-gate.sh sizing to decide whether to actually split (Q10).

### Constraints
- bash + jq only (constitution: Script Safety, KISS). ~400 reviewable-LOC budget.
- MVP probe depth: implement hard-atomic overrides + tasks.md-shape + additive-vs-modify
  FULLY; emit flag-system / release-cadence / consumer-locality as advisory hints only.

### Out of Scope
- No PR emission, branch creation, or multi-PR rewrite (PRSG-008/009).
- No blocking/gating behavior. No LOC/sizing computation (that is reviewability-gate.sh).
- No deep implementation of the three contextual probes (hints only this spec).
- No internal call to, and no edits of, reviewability-gate.sh. No shared-lib extraction.
- Route is NOT stored in SPEC-MOC.md.
```

### Files Generated

- [x] `specs/prsg-007-atomicity-router/spec.md` (301 lines; + `checklists/requirements.md`, 16/16 quality items pass)

---

## Phase 2: Clarify

**When to run:** To resolve the Open Questions the interview deferred. Max 5 targeted questions per session.

### Clarify Prompts

#### Session 1: Route taxonomy & JSON contract

```bash
/speckit-clarify Focus on the route taxonomy and output contract: the exact JSON
field names (route, releasable, signals/hints, warnings), and the precise trigger for
the branch-by-abstraction route vs falling through to one-navigable-PR. Align the JSON
shape with reviewability-gate.sh so PRSG-008 can consume it. (Design Concept Open
Questions 2 and 3.)
```

#### Session 2: Hard-atomic & releasability detection

```bash
/speckit-clarify Focus on US2: the concrete, language-agnostic signatures for each
hard-atomic class (exported-symbol rename, global version pin, destructive migration,
mutual-exclusion/auth/payment primitive, out-of-tree contract break) and the
destructive-migration / concurrency signatures that set releasable:false. What evidence
in tasks.md / plan.md / spec.md does each probe read?
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Route taxonomy & JSON contract | | |
| 2 | Hard-atomic & releasability | | |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/prsg-007-atomicity-router/plan.md`

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Language: bash (`#!/usr/bin/env bash`, `set -euo pipefail`), jq for JSON (constitution II + VI).
- New script: speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh
  - CLI: `atomicity-route.sh <feature-dir>` (single positional; the dir holding
    tasks.md/plan.md/spec.md). JSON to stdout. Mirrors the reviewability-gate.sh interface family.
  - Edge cases: missing/empty tasks.md → route out-of-scope (exit 0); unreadable/absent
    feature dir or usage error → exit 2 with {"error": ...}.
- Tests: tests/speckit-pro/layer4-scripts/test-atomicity-route.sh + one fixture per
  change class under tests/speckit-pro/layer4-scripts/fixtures/.

## Architecture Notes / Constraints
- INDEPENDENT of reviewability-gate.sh — no shell-out, no shared lib. DUPLICATE the
  few surface_for_path / is_production_file cases the router needs (Q9, Q12; constitution
  VI "three similar lines beat a premature abstraction"). Do NOT edit the shipped gate.
- Splittability = structural seams (count of independent additive capabilities/surfaces
  in tasks.md), NOT LOC (Q10). The autopilot combines router.route with reviewability-gate.sh
  sizing to decide whether to act on a split.
- Probe depth (Q5): hard-atomic overrides + tasks.md-shape + additive-vs-modify FULL;
  flag-system / release-cadence / consumer-locality emitted as advisory hints only, each
  with a TODO referencing its full-depth home (see Design Concept Open Question 1).
- Artifact: add a "## Atomicity Route" section to
  speckit-pro/skills/speckit-coach/templates/workflow-template.md (route, releasable,
  signals, warnings) — Q11.
- Documentation parity (Q13): document the post-Tasks router step in
  speckit-pro/skills/speckit-autopilot/SKILL.md + the relevant references/ doc
  (gate-validation.md or phase-execution.md) AND mirror it into
  speckit-pro/codex-skills/speckit-autopilot/SKILL.md. The script is shared (single
  scripts/ dir); only prose is mirrored. validate-codex-skills.sh (L1) must stay green.
- Lifecycle: the speckit-autopilot skill runs the script after Tasks/G5 and records the
  JSON into the workflow file (Q2, Q8).
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ⏳ | |
| `research.md` | ⏳ | Only if a probe signature needs justification |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan`. Target 2–3 domains.

### Recommended Domains (from spec analysis)

- **error-handling** — the script's exit-code contract (0 success / 2 usage-or-unreadable),
  missing/empty tasks.md → out-of-scope, and graceful degradation of the advisory hint
  probes are the riskiest parts.
- **api-contracts** — the JSON output IS a contract PRSG-008 will consume; field names,
  enum values, and the releasable/warnings shape must be stable and validated.

### Checklist Prompts

```bash
/speckit-checklist error-handling

Focus on Atomicity-test router requirements:
- Exit 0 on every successful classification; exit 2 only on usage / unreadable input.
- Missing or empty tasks.md routes to out-of-scope (not an error).
- The three advisory-hint probes degrade gracefully (a probe that can't run emits no hint,
  never a failure).
- Pay special attention to: never blocking the workflow under any input.
```

```bash
/speckit-checklist api-contracts

Focus on Atomicity-test router requirements:
- The JSON contract: route enum, releasable boolean, signals/hints array, warnings array.
- Field-name and enum stability so PRSG-008 (layer-planner) can parse it.
- Alignment with reviewability-gate.sh's JSON shape conventions.
- Pay special attention to: the route precedence ladder being unambiguous and total.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| error-handling | | | |
| api-contracts | | | |

---

## Phase 5: Tasks

**When to run:** After checklists complete. Output: `specs/prsg-007-atomicity-router/tasks.md`

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- TDD-first: write the L4 test (one fixture per change class) before the script logic.
- Small, testable chunks; reference FR-xxx; dependency-ordered.
- Organize by user story: US1 (classifier core) then US2 (hard-atomic + releasability),
  then polish (template section + SKILL/Codex docs).

## Implementation Phases
1. Foundation: atomicity-route.sh skeleton + CLI + JSON emitter + exit-code contract;
   L4 harness + fixtures scaffolding.
2. US1: tasks.md-shape + additive-vs-modify probes + seam-based split/one-navigable/out-of-scope
   routing + advisory-hint probes (flag-system / release-cadence / consumer-locality).
3. US2: hard-atomic override signatures → single-atomic-PR; destructive-migration/concurrency
   → releasable:false + warning.
4. Polish: "## Atomicity Route" section in workflow-template.md; document the post-Tasks step
   in the Claude SKILL.md + references/ doc; MIRROR into codex-skills/speckit-autopilot/SKILL.md.

## Constraints (bound by Design Concept Non-goals)
- Flag any task that wires PR emission/branch creation — that is PRSG-008/009, out of scope.
- Flag any task that edits reviewability-gate.sh or extracts a shared lib — out of scope.
- Include explicit Codex-mirror tasks for every SKILL.md prose change (validate-codex-skills.sh).
- One L4 fixture per change class (each route + each hard-atomic class + a releasability case).
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | |
| **User Stories Covered** | US1, US2 |

---

## Phase 6: Analyze

**When to run:** After generating tasks.

### Analyze Prompt

```bash
/speckit-analyze

Focus on:
1. Constitution alignment — Script Safety (set -euo pipefail, quoting), KISS/YAGNI
   (no probe over-build; matcher duplicated not abstracted), Test Coverage (L4 per change class).
2. Coverage gaps — every FR and both user stories have tasks; one L4 fixture per change class.
3. Design-concept drift — flag any task/plan/spec statement that contradicts the Design
   Concept's Goals/Non-goals (the design concept is source of truth for scoping decisions).
4. Codex parity — confirm a mirror task exists for each SKILL.md prose change.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| | | | |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed.

### Implement Prompt

```bash
/speckit-implement

## Approach: TDD-First
For each task: RED (failing L4 test / fixture) → GREEN (minimum bash) → REFACTOR → VERIFY.

### Pre-Implementation Setup
1. Work in the worktree .worktrees/prsg-007-atomicity-router (pin this absolute path).
2. Run the existing suite green before changes: `bash tests/speckit-pro/run-all.sh`.

### Implementation Notes (consult the Design Concept Q&A for the "why")
- atomicity-route.sh is read-only and advisory: emit JSON, exit 0 on success / 2 on
  usage-or-unreadable, never block.
- Default/abstain route = one-navigable-PR; honor the precedence ladder; splittability = seams.
- Implement hard-atomic + tasks.md-shape + additive-vs-modify fully; emit the three
  contextual probes as advisory hints with TODOs (do NOT build them to full depth here).
- releasable:false + a warnings[] entry on destructive-migration / concurrency signatures.
- Duplicate the small surface/path matcher; do NOT touch reviewability-gate.sh.
- Add the "## Atomicity Route" template section; mirror all SKILL.md prose into the Codex
  mirror; keep validate-codex-skills.sh green.

### Dogfood self-check
Running the finished router on PRSG-007's own feature dir (additive: one new script +
fixtures + docs, single surface) MUST route to single-atomic-PR or one-navigable-PR —
NEVER split-PR. If it routes to split-PR, the precedence is wrong.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Foundation | | | |
| 2 - US1 Classifier | | | |
| 3 - US2 Hard-atomic + releasability | | | |
| 4 - Polish (template + SKILL + Codex mirror) | | | |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in tasks.md
- [ ] `bash -n speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh` clean; script is `chmod +x`
- [ ] Layer 4 passes: `bash tests/speckit-pro/run-all.sh --layer 4`
- [ ] Layer 1 passes (incl. validate-codex-skills.sh): `bash tests/speckit-pro/run-all.sh --layer 1`
- [ ] Dogfood: router on PRSG-007's own feature dir routes to a non-split route
- [ ] Open Question 1 closed: roadmap assigns the deferred contextual-probe depth to PRSG-008/010
- [ ] PR created with a public-readable conventional-commits title

---

## Open Questions carried from the Design Concept

1. **Roadmap gap-closure (load-bearing).** The deferred contextual probes (flag-system /
   release-cadence / consumer-locality) ship as advisory-hint stubs here. Before merge,
   confirm via `/speckit-pro:speckit-coach` that PRSG-008 (layer-planner) and/or PRSG-010
   (harden the hatch) own their full-depth implementation, so the stubs are not orphaned.
2. **branch-by-abstraction trigger** — resolve in Clarify Session 1.
3. **Exact JSON schema** — finalize in Plan / Clarify, aligned with reviewability-gate.sh.

---

Template based on SpecKit best practices. Source of truth for scoping decisions:
`docs/ai/specs/.process/PRSG-007-design-concept.md`.
