# SpecKit Workflow: PRSG-010 - Harden the hatch + O5 monster-epics

**Template Version**: 1.0.0
**Created**: 2026-06-11
**Purpose**: Execute PRSG-010, making the reviewability hatch a real post-implementation backstop, adding O5 monster-epic scaffolding/status semantics, and deepening contextual atomicity probes after the small-PR path exists.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`$speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/PRSG-010-design-concept.md
```

Re-read it before each phase. The locked setup decisions:

1. Over-budget final diff gate results stop before PR creation and produce a re-slicing packet through PRSG-007/008/009.
2. Generated roadmap/template content loses live exception boilerplate.
3. Explicit typed exceptions remain rare operator-owned overrides.
4. O5 uses a parent manifest plus flat sibling child spec directories linked by the parent.
5. Contextual probes become decisive only with high-confidence deterministic evidence.
6. PRSG-010 itself should dogfood split-PR delivery as an ordered stack.

> **Note:** Grill Me is human-in-the-loop only. It is not part of the
> autopilot loop. Once the workflow file is populated and autopilot begins,
> clarifications happen via `/speckit-clarify` and the consensus protocol.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | Pending | Seed from roadmap PRSG-010 plus the design concept decisions above |
| Clarify | `/speckit-clarify` | Pending | Focus on re-slicing packet, O5 schema, and high-confidence probe evidence |
| Plan | `/speckit-plan` | Pending | Plain bash + jq + Markdown; split-stack delivery expected |
| Checklist | `/speckit-checklist` | Pending | Run error-handling, data-integrity, developer-experience, and backward-compatibility |
| Tasks | `/speckit-tasks` | Pending | TDD-first, story-organized, split-PR-aware |
| Analyze | `/speckit-analyze` | Pending | Check roadmap/design/spec/plan/tasks consistency and PRSG-010 boundaries |
| Implement | `/speckit-implement` | Pending | Execute as ordered split stack unless G5 routing says otherwise |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | Backstop, O5, and probe stories are explicit; no `[NEEDS CLARIFICATION]` markers remain |
| G2 | After Clarify | Re-slicing packet, O5 schema, branch/status rollup, and probe evidence thresholds are pinned |
| G3 | After Plan | Architecture keeps current lints/index assumptions intact; no generated exception boilerplate remains |
| G4 | After Checklist | All `[Gap]` markers addressed or explicitly scoped out |
| G5 | After Tasks | Task coverage maps to all PRSG-010 stories and is ordered for split-PR delivery |
| G6 | After Analyze | No CRITICAL/HIGH drift from roadmap or design concept |
| G7 | After Implementation | Relevant L1/L4/L8 and any declared eval evidence pass |

---

## Prerequisites

### Constitution Validation

Verify against `.specify/memory/constitution.md` before G1:

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Plugin Structure Compliance | Skill/template/script edits keep valid plugin layout | `bash tests/speckit-pro/run-all.sh --layer 1` |
| Script Safety | New/edited bash is `set -euo pipefail`, quoted, and uses `jq` for JSON | `bash tests/speckit-pro/run-all.sh --layer 4` plus `bash -n` where focused |
| Test Coverage Before Merge | New deterministic behavior has Layer 4 fixtures; mirrored skill prose has Layer 1/Codex parity and Layer 8 when required | `bash tests/speckit-pro/run-all.sh`, plus Layer 8 dry-run if mirrored skill prose changes |
| KISS / YAGNI | No broad tree-shape rewrite for O5 v1; no speculative low-confidence routing | Plan and Analyze review |

**Constitution Check:** Pending

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | PRSG-010 |
| **Name** | Harden the hatch + O5 monster-epics |
| **Branch** | `prsg-010-harden-the-hatch` |
| **Dependencies** | PRSG-001 through PRSG-009 complete; PRSG-011 complete |
| **Enables** | Fully enforced PR-size governance backstop and O5 monster-epic fallback |
| **Priority** | P2, Phase 5, LAST |

### Success Criteria Summary

- [ ] Final post-implementation diff gate blocks oversized unexcepted PR creation and records a re-slicing packet that points back to PRSG-007/008/009.
- [ ] Generated roadmap/template content no longer carries valid live reviewability exception boilerplate.
- [ ] Valid typed exceptions still work only when explicitly authored by the operator.
- [ ] `speckit-scaffold-spec` can describe or create the O5 parent/child schema without nesting child specs under the parent directory.
- [ ] `speckit-status` rolls up O5 parent and child spec status from deterministic parent/child metadata.
- [ ] `atomicity-route.sh` promotes flag-system, release-cadence, and consumer-locality evidence to decisive signals only when deterministic confidence is high; otherwise it preserves conservative existing behavior.
- [ ] PRSG-010 execution uses a split-PR-oriented task plan unless the router classifies it otherwise.

---

## Phase 1: Specify

**When to run:** Start of PRSG-010. Focus on WHAT and WHY. Output: `specs/prsg-010-harden-the-hatch/spec.md`.

### Specify Prompt

```bash
/speckit-specify

## Feature: PRSG-010 harden the hatch + O5 monster-epics

### Problem Statement
The PR-size governance roadmap now has relocation, navigation, upstream sizing,
atomicity routing, layer planning, and multi-PR emission in place. The remaining
hatch is still too easy to bypass or ignore: generated template text can carry
exception boilerplate, final diff-gate failures can be treated as advisory, and
the router's contextual probes are only shallow hints. PRSG-010 makes the final
backstop real and adds the reserved O5 monster-epic fallback for work that cannot
fit the normal O4 split path.

### Users
- Maintainers reviewing speckit-pro-generated PRs who need oversized PRs stopped before creation.
- Operators running autopilot who need actionable re-slicing instructions instead of a blind block.
- Spec authors who need an O5 parent/child model for genuine monster epics.
- Maintainers of `atomicity-route.sh`, `reviewability-gate.sh`, `speckit-scaffold-spec`, and `speckit-status`.

### User Stories
- [US1] Real hatch backstop: when the final diff gate blocks without an explicit valid typed exception, autopilot stops before PR creation and records a re-slicing packet that routes through PRSG-007/008/009.
- [US2] O5 monster-epics: scaffold/status support a parent manifest with flat sibling child specs, shared design concept/retrospective links, dependency order, and deterministic status rollup.
- [US3] Deep contextual routing probes: promote flag-system, release-cadence, and consumer-locality evidence from advisory hints to decisive routing signals only when deterministic evidence is high confidence.

### Constraints
- Preserve the gate's typed `Reviewability-Exception: refactor|infra|upgrade` mechanism for explicit operator-owned overrides.
- Remove live exception boilerplate from generated roadmap/template content; do not replace it with a different copy-pasteable bypass.
- Keep O5 child specs as flat siblings linked by a parent manifest. Do not introduce nested `specs/<parent>/<child>` scanning in v1.
- Use plain bash + jq for deterministic scripts.
- Avoid speculative routing. If contextual evidence is weak, keep the existing conservative route.
- Dogfood split-PR delivery for this spec: plan the work as an ordered stack of small slices.

### Out of Scope
- Disabling all typed exceptions.
- Redesigning PRSG-009 multi-PR emission or restacking.
- Rewriting every MOC/index lint to support nested child directories.
- Treating shallow keyword hits as decisive contextual routing evidence.
- Migrating old specs into the O5 model.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | Pending |
| User Stories | Pending |
| Acceptance Criteria | Pending |

### Files Generated

- [ ] `specs/prsg-010-harden-the-hatch/spec.md`
- [x] `specs/prsg-010-harden-the-hatch/SPEC-MOC.md`

---

## Phase 2: Clarify

**When to run:** After Specify. Use Clarify to pin contracts, not to reopen roadmap scope.

### Clarify Prompts

#### Session 1: Backstop and re-slicing packet

```bash
/speckit-clarify Focus on US1: exact final diff-gate handling before PR creation, how an unexcepted block is recorded in workflow/autopilot-state, the re-slicing packet fields, and whether the stop path exits before any gh pr create or multi-pr-emission call.
```

#### Session 2: O5 parent/child schema and status rollup

```bash
/speckit-clarify Focus on US2: parent manifest filename/schema, flat sibling child naming, shared design-concept and retrospective links, child dependency order, branch/worktree expectations, SPEC-MOC links, and how speckit-status rolls parent and child statuses up without nested spec directories.
```

#### Session 3: High-confidence contextual probes

```bash
/speckit-clarify Focus on US3: deterministic evidence thresholds for flag-system, release-cadence, and consumer-locality; when branch-by-abstraction may be emitted; how weak evidence preserves existing conservative routes; and the exact JSON signal/hint vocabulary.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Backstop and re-slicing packet | Pending | Pending |
| 2 | O5 parent/child schema and status rollup | Pending | Pending |
| 3 | High-confidence contextual probes | Pending | Pending |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/prsg-010-harden-the-hatch/plan.md`.

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Repository type: Claude Code / Codex plugin marketplace.
- Runtime: Markdown skills, YAML/plugin manifests, plain bash + jq scripts.
- Core scripts in scope: `reviewability-gate.sh`, `atomicity-route.sh`, likely `multi-pr-emission.sh` or post-implementation references for the stop-before-PR behavior.
- Skill/docs surfaces in scope: `speckit-autopilot`, `speckit-scaffold-spec`, `speckit-status`, roadmap/template references, Codex mirrors when corresponding Claude skill prose changes.
- Tests: shell Layer 1 structural tests, Layer 4 script fixtures, Layer 8 parity when mirrored skill prose changes, Layer 3 descriptors/evals when skill behavior changes.

## Design Concept Source
Use `docs/ai/specs/.process/PRSG-010-design-concept.md` as the source of truth for scoping decisions:
- stop and re-slice before PR creation on unexcepted final diff-gate block;
- remove generated live exception boilerplate while preserving explicit typed exceptions;
- O5 parent manifest plus flat sibling child specs;
- contextual probes decisive only with high-confidence deterministic evidence;
- split-stack delivery for PRSG-010 itself.

## Declared File Operations
Fill this block during Plan with NEW/MODIFIED paths so `estimate-reviewable-loc.sh` can parse it deterministically. Expected surfaces include:
- MODIFIED `speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh` only if gate behavior changes are required; otherwise keep gate stable and wire handling in autopilot.
- MODIFIED `speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh`.
- MODIFIED `speckit-pro/skills/speckit-autopilot/SKILL.md` and Codex mirror/reference surfaces for final backstop behavior.
- MODIFIED `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` and Codex mirror for O5 schema guidance.
- MODIFIED `speckit-pro/skills/speckit-status/SKILL.md` for O5 rollup.
- MODIFIED roadmap/template files that currently emit live exception boilerplate.
- NEW/UPDATED Layer 4 fixtures and Layer 1/8 tests as required.

## Constraints
- Do not nest O5 child specs under a parent directory in v1.
- Do not disable typed exceptions.
- Do not treat weak keyword evidence as decisive routing.
- Do not redesign PRSG-009 PR emission.
- Keep deterministic behavior in scripts with fixture coverage.

## Architecture Notes
- Prefer wiring stop-before-PR behavior in autopilot/post-implementation orchestration while preserving `reviewability-gate.sh`'s existing exit contract.
- The re-slicing packet should be machine-readable enough for resume/status and human-readable enough for an operator to act on.
- The contextual-probe work must preserve dogfood safety: scripts that mention auth, locks, release cadence, or branch-by-abstraction as detector vocabulary must not self-classify as risky behavior.
- O5 status rollup should read parent/child metadata rather than inferring hierarchy from nested paths.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Pending | |
| `research.md` | Pending | |
| `data-model.md` | Pending | |
| `contracts/` | Pending | re-slicing packet, O5 parent manifest, routing decision delta likely |
| `quickstart.md` | Pending | |

---

## Phase 4: Domain Checklists

### Recommended Domains

| Domain | Why |
|--------|-----|
| error-handling | US1 introduces a blocking stop path and resume/recovery packet |
| data-integrity | O5 parent/child metadata and generated index/status rollups must not drift |
| developer-experience | Operators need clear re-slicing and monster-epic guidance |
| backward-compatibility | Existing specs, generated maps, and typed exception behavior must keep working |

### Checklist Prompts

#### 1. error-handling Checklist

```bash
/speckit-checklist error-handling

Focus on PRSG-010 requirements:
- final diff-gate block stops before any PR creation command;
- valid explicit typed exceptions still behave as operator-owned overrides;
- re-slicing packet includes enough context to resume through PRSG-007/008/009;
- weak contextual-probe evidence fails closed instead of misrouting.
```

#### 2. data-integrity Checklist

```bash
/speckit-checklist data-integrity

Focus on PRSG-010 requirements:
- O5 parent manifest schema deterministically links flat sibling child specs;
- status rollup cannot silently omit failed, pending, or blocked child specs;
- generated MOC/index zones remain regenerated by the existing generator, not hand-patched;
- route signal vocabulary remains stable and JSON-valid.
```

#### 3. developer-experience Checklist

```bash
/speckit-checklist developer-experience

Focus on PRSG-010 requirements:
- blocked operators receive concrete re-slicing next steps;
- scaffold guidance explains when to use O5 and when normal split-PR is enough;
- removal of boilerplate does not hide how explicit exceptions work when truly needed.
```

#### 4. backward-compatibility Checklist

```bash
/speckit-checklist backward-compatibility

Focus on PRSG-010 requirements:
- current flat `specs/*` assumptions keep working;
- existing typed exception fixtures still pass unless intentionally updated;
- PRSG-007/008/009 fixtures remain valid;
- Codex and Claude skill mirrors stay semantically equivalent.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| error-handling | Pending | Pending | |
| data-integrity | Pending | Pending | |
| developer-experience | Pending | Pending | |
| backward-compatibility | Pending | Pending | |

---

## Phase 5: Tasks

**When to run:** After checklists complete. Output: `specs/prsg-010-harden-the-hatch/tasks.md`.

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Organize by user story: US1 hatch backstop, US3 contextual probes, US2 O5 scaffold/status, then polish/parity.
- Use TDD-first for deterministic scripts and schema changes.
- Include Layer 4 fixtures before changing `atomicity-route.sh` or any packet/manifest script behavior.
- Include Layer 1 structural checks for template, MOC, plugin payload, and status/scaffold changes.
- Include Codex mirror and Layer 8 parity tasks when mirrored skill prose changes.
- Mark [P] only for truly independent files. Tasks touching the same script are sequential.

## Expected Split Stack
1. Foundation: contracts/fixtures for re-slicing packet, contextual probe evidence, and O5 manifest.
2. US1: final diff-gate backstop and generated boilerplate removal.
3. US3: high-confidence contextual probe routing.
4. US2: O5 parent/child scaffold guidance and status rollup.
5. Polish: parity, docs, status/index freshness, PR body evidence, full verification.

## Constraints
- Preserve explicit typed exception support.
- Do not nest child specs.
- Do not add low-confidence route decisions.
- Do not redesign multi-PR emission.
- Keep PRSG-010 itself ready for split-PR emission after Tasks/G5.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| Total Tasks | Pending |
| Phases | Pending |
| Parallel Opportunities | Pending |
| User Stories Covered | Pending |

---

## Atomicity Route

**When this is filled:** After the Tasks phase / gate G5, autopilot runs the
read-only atomicity classifier and records its decision here.

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | Pending | Expected to be `split-PR` if tasks preserve the setup decision |
| **Releasable** | Pending | `true`, or `false` if a release-risk detector applies |
| **Signals** | Pending | Decisive detector findings |
| **Warnings** | Pending | Release-safety warnings |

Classifier command:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/prsg-010-harden-the-hatch
```

---

## Phase 6: Analyze

### Analyze Prompt

```bash
/speckit-analyze

Focus on:
1. Roadmap/design consistency: PRSG-010 must cover US1 hatch, US2 O5, and US3 contextual probes without deleting typed exceptions or deferring O5.
2. Split-stack readiness: tasks should be ordered so PRSG-009 can emit small PRs.
3. Backward compatibility: flat spec lints, generated index zones, existing typed exception fixtures, and PRSG-007/008/009 contracts must remain valid.
4. Scope control: no nested O5 child directories, no weak-evidence routing, no PRSG-009 restack redesign.
5. Coverage: every FR/SC must trace to tasks and focused tests; every deterministic behavior has Layer 4 coverage.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| Pending | Pending | Pending | Pending |

---

## Phase 7: Implement

### Implement Prompt

```bash
/speckit-implement

## Approach: TDD-First
1. RED: write or update Layer 4 fixtures for each deterministic contract before implementation.
2. GREEN: implement the smallest script/skill/template change that satisfies the fixture.
3. REFACTOR: keep script changes surgical; do not extract shared libraries unless analysis proves duplication is worse.
4. VERIFY: run focused layer tests after each slice and default verification before PR emission.

### Pre-Implementation Setup
1. Work in branch `prsg-010-harden-the-hatch`.
2. Re-read `docs/ai/specs/.process/PRSG-010-design-concept.md`.
3. Confirm `git status --short` is clean before each slice.
4. Use detected project commands:
   - Structural: `bash tests/speckit-pro/run-all.sh --layer 1`
   - Script unit: `bash tests/speckit-pro/run-all.sh --layer 4`
   - Default verify: `bash tests/speckit-pro/run-all.sh`

### Implementation Notes
- Preserve `reviewability-gate.sh` exit codes unless Plan explicitly proves a script change is required.
- Stop-before-PR behavior belongs in autopilot/post-implementation orchestration, not in GitHub PR creation after the fact.
- O5 parent/child shape is flat sibling specs linked by parent manifest metadata.
- Contextual routing must be evidence-driven and dogfood-safe.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Foundation | Pending | Pending | |
| US1 hatch backstop | Pending | Pending | |
| US3 contextual probes | Pending | Pending | |
| US2 O5 scaffold/status | Pending | Pending | |
| Polish | Pending | Pending | |

---

## Post-Implementation Checklist

- [ ] All tasks complete in `tasks.md`
- [ ] `bash tests/speckit-pro/run-all.sh --layer 1` passes
- [ ] `bash tests/speckit-pro/run-all.sh --layer 4` passes
- [ ] `bash tests/speckit-pro/run-all.sh` passes
- [ ] Layer 8 parity dry-run passes if mirrored skill prose changed
- [ ] Final diff-gate behavior is exercised with an unexcepted block fixture
- [ ] O5 parent/child status rollup is fixture-verified
- [ ] Contextual probes are fixture-verified for high-confidence and weak-evidence cases
- [ ] PRSG-010 split-PR emission evidence is recorded

---

## Lessons Learned

### What Worked Well

- Pending

### Challenges Encountered

- Pending

### Patterns to Reuse

- Pending
