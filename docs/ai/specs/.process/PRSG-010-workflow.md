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
| Specify | `/speckit-specify` | Complete | Seed from roadmap PRSG-010 plus the design concept decisions above |
| Clarify | `/speckit-clarify` | Complete | Focus on re-slicing packet, O5 schema, and high-confidence probe evidence |
| Plan | `/speckit-plan` | Complete | Plain bash + jq + Markdown; split-stack delivery expected |
| Checklist | `/speckit-checklist` | Complete | Run error-handling, data-integrity, developer-experience, and backward-compatibility |
| Tasks | `/speckit-tasks` | Complete | TDD-first, story-organized, split-PR-aware |
| Analyze | `/speckit-analyze` | Complete | 3 findings remediated; marker counter clean; G6 passed |
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

**Constitution Check:** Verified 2026-06-11. Baseline Layer 1 passed
`915/915`; Layer 4 passed `1195/1195`.

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
| Functional Requirements | 23 |
| User Stories | 3 |
| Acceptance Criteria | 9 |
| Success Criteria | 8 |
| `[NEEDS CLARIFICATION]` markers | 0 |
| Quality checklist | Passed |
| Validation evidence | G1 validator passed; Layer 1 passed `915/915` |

### Files Generated

- [x] `specs/prsg-010-harden-the-hatch/spec.md`
- [x] `specs/prsg-010-harden-the-hatch/SPEC-MOC.md`
- [x] `specs/prsg-010-harden-the-hatch/checklists/requirements.md`

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
| 1 | Backstop and re-slicing packet | 5 | Accepted gate outcome matrix, stop-before-any-emission rule, top-level `final_reviewability_gate` state, JSON re-slicing packet fields, and consensus-backed exception provenance rule. |
| 2 | O5 parent/child schema and status rollup | 5 | Accepted `o5-parent-manifest.json` as CONTRACT data, `PRSG-010A`/`prsg-010a-*` child naming, curated child MOC body links, independent child scaffolds, and computed read-only status rollup. |
| 3 | High-confidence contextual probes | 5 | Accepted high-confidence flag, release-cadence, and branch-by-abstraction thresholds; weak evidence stays hint-only; router schema remains flat and extends existing signal enums while closing `hints[]`. |

### Clarify Session 1 Consensus

| Item | Round | Routed Categories | Outcome | Analysts Used |
|------|-------|-------------------|---------|---------------|
| Operator-owned typed exception provenance | 1 | codebase, spec | A valid exception is an exact branch-added Markdown pragma in a committed, review-visible, non-generated CONTRACT artifact; `.process`, templates, generated zones/boilerplate, PR bodies, commit messages, code fences, and mutable/generated provenance are rejected and recorded in failed-gate evidence. | codebase-analyst, spec-context-analyst |
| O5 parent manifest contract | 1 | codebase, spec | The parent manifest lives at `specs/<parent-branch>/o5-parent-manifest.json` as review-visible CONTRACT data with `schemaVersion: 1`, ordered children, shared links, nullable retrospective, and optional declared rollup status. | codebase-analyst, spec-context-analyst |
| O5 flat child naming and order | 1 | codebase, spec | Child IDs use `PRSG-010A`-style suffixes with paths/branches like `specs/prsg-010a-<slug>`; `children[]` order is authoritative and `depends_on[]` can reference only earlier sibling IDs. | codebase-analyst, spec-context-analyst |
| O5 shared MOC links | 1 | codebase, spec | Child `SPEC-MOC.md` keeps `up:` pointed at the roadmap and adds curated body links to parent manifest and shared design concept; retrospective links are added only after the target exists. | codebase-analyst, spec-context-analyst |
| O5 status rollup | 1 | codebase, spec | `speckit-status` validates topology first, computes child states read-only in manifest order, applies precedence `invalid topology > blocked/failed > in_progress > pending > complete`, and reports drift against optional declared status. | codebase-analyst, spec-context-analyst |
| High-confidence flag-system routing | 1 | codebase, spec, domain | Repo-local flag/evaluation evidence plus current guard/test tasks emits `context:flag-system:guarded-cutover` and routes non-hard-atomic guarded cutovers to `one-navigable-PR`, without overriding hard-atomic or proven additive split evidence. | codebase-analyst, spec-context-analyst, domain-researcher |
| No-flag release-cadence routing | 1 | codebase, spec, domain | Proven no-flag release-held cutovers emit `context:release-cadence:release-held-cutover` and route `single-atomic-PR`; this does not automatically set `releasable:false`. | codebase-analyst, spec-context-analyst, domain-researcher |
| Router schema vocabulary | 1 | codebase, spec, domain | Keep flat routing JSON, promote or add production `routing-decision.schema.json`, extend existing PRSG-007 signal enums, and close `hints[]` with stable tokens for weak/conflicting contextual evidence. | codebase-analyst, spec-context-analyst, domain-researcher |

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
| `plan.md` | Complete | Split stack: PRSG-010A final hatch, PRSG-010B contextual router, PRSG-010C O5, PRSG-010D docs/parity/polish |
| `research.md` | Complete | Records final backstop, O5, and contextual routing decisions |
| `data-model.md` | Complete | Defines final gate state, re-slicing packet, O5 manifest/rollup, contextual evidence, and routing decision |
| `contracts/` | Complete | 4 JSON contracts: final gate state, re-slicing packet, O5 parent manifest, routing decision |
| `quickstart.md` | Complete | Fixture-backed verification path and split-stack review flow |

Plan validation:

- G3 validator passed with 0 unresolved markers.
- `estimate-reviewable-loc.sh` parsed 30 declared file operations: 14 new, 16 modified, status `pass`, projected `0` under the current plugin-path heuristic.
- Contract JSON parsing passed for all 4 generated schemas.
- Layer 1 passed `915/915`; Layer 4 passed `1195/1195`; default suite passed `2300/2300` in the phase executor.

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
| error-handling | 26 | 6 found, 6 remediated, 0 remaining | Final gate state, re-slicing packet, exception state, PR creation stop, weak probe fallback |
| data-integrity | 24 | 5 found, 5 remediated, 0 remaining | O5 branch/path equality, rollup completeness, generated MOC ownership, router schema fixture validation |
| developer-experience | 27 | 6 found, 6 remediated, 0 remaining | Operator steps, O5 default-boundary guidance, non-boilerplate exception education |
| backward-compatibility | 24 | 4 found, 4 remediated, 0 remaining | Flat spec discovery, typed exception continuity, PRSG-007/008/009 compatibility, Claude/Codex mirror parity |

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
| Total Tasks | 57 |
| Phases | 6: setup, foundational, PRSG-010A, PRSG-010B, PRSG-010C, PRSG-010D |
| Parallel Opportunities | 20 tasks marked `[P]` across setup, tests, contracts, fixtures, and parity setup |
| User Stories Covered | US1 final hatch, US3 contextual router, US2 O5; PRSG-010D covers docs/parity/polish |

### Tasks Validation

- G5 validator passed: `{"gate":"G5","pass":true,"reason":"57 tasks found","markers":0,"task_count":57}`.
- Generated spec index check passed.
- Marker scan found 0 active `[Gap]`, `[NEEDS CLARIFICATION]`, or `[CRITICAL]` markers; matches were only gate/checklist wording.
- Layer 1 passed `915/915`.

---

## Atomicity Route

**When this is filled:** After the Tasks phase / gate G5, autopilot runs the
read-only atomicity classifier and records its decision here.

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | `one-navigable-PR` | Current pre-implementation classifier output; PRSG-010 remains planned as an ordered split stack from reviewability/analyze evidence |
| **Releasable** | `true` | No release-risk detector applied |
| **Signals** | `change-shape:modify-heavy` | Current decisive detector finding |
| **Warnings** | `[]` | No release-safety warnings |
| **Hints** | flag-system, release-cadence, and consumer-locality advisory hints | These are current shallow hints; PRSG-010B implements high-confidence contextual routing |

Confidence gate:

- `confidence-gate.sh docs/ai/specs/.process/PRSG-010-workflow.md` returned `NO_DATA` in advisory mode with recommended action `soft_skip`.
- Implementation proceeds because the confidence gate is advisory and Analyze/G6 passed.

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
| A1 | High | Split-stack order drift: the design concept and Tasks prompt require hatch -> contextual probes -> O5 -> polish, but spec/plan/tasks had O5 before contextual routing. | Remediated in `spec.md`, `plan.md`, and `tasks.md`; PRSG-010B is now contextual routing and PRSG-010C is O5. |
| A2 | Medium | Reviewability/file-operation drift: `plan.md` declared 30 file operations and the spec projected 28 total files, but `tasks.md` plans 39 changed/new files before slicing. | Remediated in `spec.md` and `plan.md`; projected total files now says 39 before slicing and `plan.md` enumerates the missing fixture/test paths by slice. |
| A3 | Low | Workflow metadata drift: Specify/Plan summaries still showed 20 FRs, 6 success criteria, stale split-stack order, and pending analysis results after later checklist/task remediation. | Remediated in this workflow log; FR/SC counts, plan summary, Analyze status, and Analysis Results table are current. |

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
| Foundation | T001-T006 | Complete | Verified corrected split-stack order, reviewed PRSG-010 contracts, confirmed declared file operations, and preserved constitution obligations for script safety/KISS/test-before-merge. |
| US1 hatch backstop | T007-T023 | Complete | Added final reviewability backstop script, production state/re-slicing schemas, typed-exception provenance checks, Claude/Codex guidance, dist mirrors, and Layer 4 fixtures. Validation: `test-final-reviewability-backstop.sh` 31/31, `test-reviewability-gate.sh` 92/92, Layer 4 1230/1230. |
| US3 contextual probes | T024-T032 | Complete | Added guarded cutover, release-held cutover, weak evidence, consumer-locality, out-of-tree, and conflict fixtures; promoted production routing schema; implemented closed contextual signals/hints while preserving hard-atomic and releasability precedence. Validation: `test-atomicity-route.sh` 109/109, `test-plan-layers.sh` 66/66, `test-multi-pr-emission.sh` 81/81. |
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
