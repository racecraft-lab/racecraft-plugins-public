---
topic: "Layer-planner: tasks.md to ordered increments"
slug: "prsg-008-layer-planner"
date: "2026-06-09"
mode: "setup"
spec_id: "PRSG-008"
source_input:
  type: "topic"
  ref: "docs/ai/specs/pr-size-governance-technical-roadmap.md (PRSG-008 scope)"
question_count: 24
stop_reason: "natural"
---

# Design Concept: Layer-planner — tasks.md to ordered increments

> **Source:** PR-Size Governance technical roadmap — PRSG-008 scope (Phase 4 · P1)
> **Date:** 2026-06-09
> **Questions asked:** 24
> **Stop reason:** natural (planner contract, parser strictness, diagnostics, fixtures, and scope cuts are resolved)

## Goals

- Ship `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh` as a read-only planner that takes a feature directory and emits stable JSON to stdout (Q1, Q2, Q12).
- Parse `tasks.md` into ordered increments using SpecKit story phases: `Foundation`, each user-story phase in dependency order, and `Polish` (Q4).
- Use explicit `## Dependencies & Execution Order` and `### Incremental Delivery` sections as the primary dependency source, then validate them against task order (Q7).
- Include enough structure for PRSG-009 to consume safely: increment IDs/names, ordered task IDs, task checkbox status, `parallel` metadata, repo-relative file/test paths, source line numbers, dependencies, warnings, and advisory size metadata (Q5, Q6, Q10, Q15, Q21, Q22).
- Fail fast on malformed or impossible plans with machine-readable JSON diagnostics and concise stderr summaries (Q3, Q13, Q18, Q20, Q23).
- Add a schema-backed planner output contract under `specs/prsg-008-layer-planner/contracts/` so downstream specs can rely on a stable shape (Q9, Q17).
- Wire planner execution into `speckit-autopilot` after PRSG-007 atomicity routing and before implementation, but keep `plan-layers.sh` independent from `atomicity-route.sh` (Q8, Q14).
- Validate with Layer 4 fixtures that combine real SpecKit `tasks.md` examples with targeted malformed cases (Q16).

## Non-goals

- No branch creation, PR body generation, restacking, or multi-PR emission. PRSG-008 is planner-only; PRSG-009 owns branch topology and PR emission (Q24).
- No internal call to `atomicity-route.sh`; orchestration decides whether the planner is relevant (Q8).
- No hard reviewability gate in the planner. Size data is advisory metadata only; PRSG-006 remains the authoritative budget gate (Q15).
- No repository mutation from `plan-layers.sh`; it writes no files and changes no workflow state directly (Q12).
- No inference of missing file/test ownership from neighboring tasks; absent file/test references are allowed with warnings rather than invented (Q11).
- No task-per-PR or heading-per-PR slicing. The increment unit is the SpecKit phase/story structure, not every checkbox or every Markdown heading (Q4).

## Design Tree (Q&A log)

### Q1. What should `plan-layers.sh` emit as its primary output?

**Branch:** Output contract

**Recommended answer:** Stable JSON to stdout
> Stable JSON is deterministic, fixture-testable, and directly consumable by `speckit-autopilot` and PRSG-009.

**Alternatives offered:**
- Markdown plan only: easier to read but harder to consume reliably.
- Both JSON and Markdown: more complete but larger scope.

**User's answer:** Stable JSON to stdout (Recommended)

---

### Q2. What should `plan-layers.sh` take as its primary input?

**Branch:** CLI contract

**Recommended answer:** Feature directory
> `plan-layers.sh <feature-dir>` can read `<feature-dir>/tasks.md` and resolve related spec/plan/test paths consistently.

**Alternatives offered:**
- Tasks file path: simpler, but loses feature-directory context.
- Stdin: pipeline-friendly but awkward for fixtures and downstream emission.

**User's answer:** Feature directory (Recommended)

---

### Q3. How strict should the planner be when `tasks.md` is missing expected sections?

**Branch:** Parser strictness

**Recommended answer:** Fail with clear diagnostics
> Bad plans should not flow into PRSG-009. Structured errors make malformed task files actionable.

**Alternatives offered:**
- Best-effort partial plan: convenient but hides missing structure.
- Fallback single increment: operationally safe but weakens the split-PR engine.

**User's answer:** Fail with clear diagnostics (Recommended)

---

### Q4. What should count as one planner increment?

**Branch:** Increment model

**Recommended answer:** SpecKit phase/story increments
> Foundation, user-story phases, and Polish match the way SpecKit tasks are authored and reviewed.

**Alternatives offered:**
- One task per increment: too granular for PR review.
- One increment per heading: risks treating support sections as deliverable slices.

**User's answer:** SpecKit phase/story increments (Recommended)

---

### Q5. What should each JSON increment include?

**Branch:** Consumer payload

**Recommended answer:** Tasks, files, tests, dependencies
> PRSG-009 needs ordered task IDs, file/test ownership, and dependency edges without re-parsing prose.

**Alternatives offered:**
- Tasks and dependencies only: smaller but pushes parsing downstream.
- Full task text snapshots: self-contained but brittle.

**User's answer:** Tasks, files, tests, dependencies (Recommended)

---

### Q6. How should the planner treat `[P]` parallel tasks inside an increment?

**Branch:** Parallelism

**Recommended answer:** Preserve them as parallelizable metadata
> Keep delivery order stable while retaining safe parallelism information already encoded in `tasks.md`.

**Alternatives offered:**
- Flatten everything into strict order: simpler but loses useful safety metadata.
- Split parallel tasks into separate increments: too many slices and unclear review order.

**User's answer:** Preserve them as parallelizable metadata (Recommended)

---

### Q7. How should the planner build the dependency DAG?

**Branch:** Dependency model

**Recommended answer:** Explicit sections first
> `## Dependencies & Execution Order` and `### Incremental Delivery` are authored for this purpose; task order is a validation cross-check.

**Alternatives offered:**
- Task order only: simpler but ignores richer guidance.
- Infer from files touched: brittle and out of scope for v1.

**User's answer:** Explicit sections first (Recommended)

---

### Q8. How should `plan-layers.sh` relate to PRSG-007's `atomicity-route.sh`?

**Branch:** Script coupling

**Recommended answer:** Stay independent
> PRSG-007 decides whether split planning is relevant; PRSG-008 parses layers. Keeping the scripts separate preserves testability.

**Alternatives offered:**
- Call `atomicity-route.sh` internally: couples two scripts.
- Require routing JSON input: cleaner orchestration but makes every planner run depend on PRSG-007 output shape.

**User's answer:** Stay independent (Recommended)

---

### Q9. Should PRSG-008 define a formal JSON schema for the planner output?

**Branch:** Contract strength

**Recommended answer:** Schema-backed contract
> PRSG-009 should depend on a stable, review-visible schema rather than implied prose.

**Alternatives offered:**
- Documented shape only: faster but easier to drift.
- No fixed schema yet: flexible but weak as a downstream foundation.

**User's answer:** Schema-backed contract (Recommended)

---

### Q10. How should file and test paths be represented in planner JSON?

**Branch:** Path normalization

**Recommended answer:** Repo-relative paths
> Repo-relative paths are stable across worktrees, fixtures, and future branch/PR emission.

**Alternatives offered:**
- Feature-dir-relative paths: ambiguous for production/test files outside the spec dir.
- Preserve text exactly: downstream consumers must normalize again.

**User's answer:** Repo-relative paths (Recommended)

---

### Q11. How should the planner handle tasks that do not mention any files or tests?

**Branch:** Missing ownership metadata

**Recommended answer:** Allow with warnings
> Coordination, review, and verification tasks can be valid without direct file paths; the warning preserves visibility.

**Alternatives offered:**
- Fail the whole plan: too strict for valid non-code tasks.
- Infer from neighboring tasks: risks inaccurate ownership.

**User's answer:** Allow with warnings (Recommended)

---

### Q12. Should `plan-layers.sh` mutate any repository files?

**Branch:** Side effects

**Recommended answer:** Read-only script
> JSON to stdout and diagnostics to stderr make the script deterministic and safe for Layer 4 fixtures.

**Alternatives offered:**
- Write a plan artifact: useful but adds lifecycle management.
- Update the workflow file directly: too coupled to autopilot internals.

**User's answer:** Read-only script (Recommended)

---

### Q13. What exit codes should `plan-layers.sh` use?

**Branch:** CLI errors

**Recommended answer:** 0 success, 1 invalid plan, 2 usage/input error
> Tests and callers can distinguish malformed `tasks.md` from bad invocation.

**Alternatives offered:**
- 0 success, nonzero failure only: simpler but less diagnostic.
- Always 0 with JSON status: too easy for automation to miss failure.

**User's answer:** 0 success, 1 invalid plan, 2 usage/input error (Recommended)

---

### Q14. Where should PRSG-008 wire the planner into `speckit-autopilot`?

**Branch:** Autopilot lifecycle

**Recommended answer:** After atomicity route, before implementation
> Autopilot can call the planner only when PRSG-007 routing says split planning is relevant, then carry the layer plan into implementation context.

**Alternatives offered:**
- Only expose the script for now: smaller, but unused until PRSG-009.
- During post-implementation only: too late to shape implementation and test order.

**User's answer:** After atomicity route, before implementation (Recommended)

---

### Q15. Should the planner estimate reviewability size per increment?

**Branch:** Size metadata

**Recommended answer:** Advisory metadata only
> Task/file counts and optional reviewable-LOC hints help PR review packets without duplicating PRSG-006's gate.

**Alternatives offered:**
- Hard gate per increment: scope creep into sizing policy.
- No size data: smaller output but less useful downstream.

**User's answer:** Advisory metadata only (Recommended)

---

### Q16. What should PRSG-008 use as its canonical Layer 4 fixtures?

**Branch:** Test realism

**Recommended answer:** Real SpecKit `tasks.md` fixtures plus malformed cases
> A realistic completed spec proves normal parsing; targeted fixtures cover missing headings, cycles, empty sections, and path extraction.

**Alternatives offered:**
- Only small synthetic fixtures: easier but less realistic.
- Only live repo specs: realistic but brittle as specs are archived.

**User's answer:** Real SpecKit `tasks.md` fixtures plus malformed cases (Recommended)

---

### Q17. Where should the planner contract live?

**Branch:** Contract location

**Recommended answer:** `specs/prsg-008-layer-planner/contracts/plan-layers.output.md` plus schema fixture
> Keeping the contract with the spec artifacts follows local SpecKit patterns and keeps reviewers close to the downstream contract.

**Alternatives offered:**
- Only under tests/fixtures: less visible.
- Only in script help text: weak as a PRSG-009 foundation.

**User's answer:** Contract plus schema fixture under `specs/prsg-008-layer-planner/contracts/` (Recommended)

---

### Q18. How should the planner handle dependency cycles or impossible ordering?

**Branch:** DAG validation

**Recommended answer:** Fail with cycle diagnostics
> A cycle should be fixed in `tasks.md` before implementation or PRSG-009 consumes the plan.

**Alternatives offered:**
- Break cycles by task order: hides a real dependency issue.
- Emit partial order with warnings: useful for review but risky for automation.

**User's answer:** Fail with cycle diagnostics (Recommended)

---

### Q19. How should increment IDs be formed in the JSON output?

**Branch:** Identifier stability

**Recommended answer:** Stable semantic IDs
> IDs like `foundation`, `us1`, `us2`, and `polish` are deterministic and readable in future PR bodies.

**Alternatives offered:**
- Generated numeric IDs: mechanically stable but less meaningful.
- Heading-derived slugs: readable but more likely to drift.

**User's answer:** Stable semantic IDs (Recommended)

---

### Q20. If atomicity routing says split planning is relevant but `plan-layers.sh` returns an invalid plan, what should autopilot do?

**Branch:** Failure policy

**Recommended answer:** Stop before implementation
> A broken layer plan must not flow into implementation or later multi-PR emission.

**Alternatives offered:**
- Fall back to one PR: keeps moving but weakens the safety path.
- Continue without layer context: makes the planner advisory when routing requested it.

**User's answer:** Stop before implementation (Recommended)

---

### Q21. How should the planner treat task checkbox state?

**Branch:** Resume behavior

**Recommended answer:** Parse all tasks and preserve status
> Fixtures may use completed historical specs, while live specs usually start unchecked. Preserving status supports both.

**Alternatives offered:**
- Only include unchecked tasks: loses historical/resume context.
- Fail if completed tasks exist: too brittle.

**User's answer:** Parse all tasks and preserve status (Recommended)

---

### Q22. Should planner JSON include source locations for traceability?

**Branch:** Traceability

**Recommended answer:** Include source line numbers
> Line numbers make diagnostics, PR review packets, and future PRSG-009 comments easier to audit.

**Alternatives offered:**
- No source locations: smaller but harder to debug.
- Only line numbers on errors: less helpful for successful review metadata.

**User's answer:** Include source line numbers (Recommended)

---

### Q23. How should planner diagnostics be formatted?

**Branch:** Diagnostics format

**Recommended answer:** Machine-readable JSON errors plus concise stderr
> Structured errors are fixture-testable; stderr summaries remain useful during manual runs.

**Alternatives offered:**
- Stderr only: simpler but less assertable.
- JSON only: test-friendly but less ergonomic.

**User's answer:** Machine-readable JSON errors plus concise stderr (Recommended)

---

### Q24. Should PRSG-008 create any multi-PR branches or PR bodies?

**Branch:** Scope boundary

**Recommended answer:** No, planner only
> PRSG-008 emits the ordered layer plan and wires it into autopilot context. PRSG-009 owns branch topology, PR body splitting, and restacking.

**Alternatives offered:**
- Create draft branch names only: leaks branch-emission concerns into PRSG-008.
- Create full PR metadata: too much scope for the layer-planner slice.

**User's answer:** No, planner only (Recommended)

## Open Questions

- **What:** Exact planner JSON field names and enum values beyond the interview-level contract.
  **Why deferred:** They should be pinned during Specify/Clarify with a schema and sample fixtures.
  **Suggested next step:** In Phase 1/2, write `contracts/plan-layers.output.md` and a JSON schema fixture before implementation.

- **What:** Whether advisory reviewability metadata should include LOC estimates or only task/file counts.
  **Why deferred:** The planner must not duplicate PRSG-006's gate; the precise advisory fields depend on the plan-phase budget model.
  **Suggested next step:** Clarify during Plan and keep the field optional if the estimator is unavailable.

## Recommended Next Step

Run `$speckit-autopilot` with `docs/ai/specs/.process/PRSG-008-workflow.md` from the `prsg-008-layer-planner` branch.
