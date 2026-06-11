---
topic: "PRSG-010 harden the hatch and O5 monster-epics"
slug: "prsg-010-harden-the-hatch"
date: "2026-06-11"
mode: "setup"
spec_id: "PRSG-010"
source_input:
  type: "topic"
  ref: "PRSG-010 roadmap entry: Harden the hatch + O5 monster-epics"
question_count: 8
stop_reason: "natural"
---

# Design Concept: PRSG-010 harden the hatch and O5 monster-epics

> **Source:** PRSG-010 roadmap entry: Harden the hatch + O5 monster-epics
> **Date:** 2026-06-11
> **Questions asked:** 8
> **Stop reason:** natural

## Goals

- Make the final reviewability diff gate a real backstop: if the block threshold is exceeded without an explicit valid typed exception, autopilot stops before PR creation and records a re-slicing packet that routes back through PRSG-007, PRSG-008, and PRSG-009.
- Remove live generated exception boilerplate from roadmap/template content so new specs do not inherit copy-paste bypass text.
- Preserve explicit typed exceptions as rare operator-owned overrides for `refactor`, `infra`, and `upgrade`.
- Add an O5 monster-epic model with a durable parent manifest and flat sibling child spec directories linked by that parent, so current `specs/*` lint and index assumptions stay intact.
- Promote the flag-system, release-cadence, and consumer-locality probes in `atomicity-route.sh` only when deterministic evidence is high confidence; otherwise fail closed to existing conservative route behavior.
- Dogfood the PRSG-009 split-PR path for PRSG-010 itself as an ordered stack: hatch backstop, contextual probes, O5 scaffold/status, then polish/parity.

## Non-goals

- Disable all reviewability exceptions. The gate's typed exception mechanism remains for explicit, rare operator ownership; only generated boilerplate is removed.
- Add speculative routing behavior when evidence is weak. Contextual probes must not force `branch-by-abstraction` or split decisions from shallow keyword hits.
- Use nested O5 child directories in v1. Flat siblings avoid broad lint/index churn.
- Defer O5 entirely. Monster-epics are part of PRSG-010's roadmap scope.
- Rework PRSG-009 multi-PR emission semantics. PRSG-010 consumes that path; it does not redesign PR emission.

## Design Tree (Q&A log)

### Q1. When the final reviewability diff gate exceeds the block threshold, what should autopilot do before PR creation?

**Branch:** Backstop behavior

**Recommended answer:** Stop and re-slice.
> This makes the hatch real only after PRSG-009 has supplied a small-PR path. It prevents a flattened oversized PR from being created and directs the run back through the existing router, layer planner, and multi-PR emitter.

**Alternatives offered:**
- Allow typed exception: Keeps operator override available, but weakens PRSG-010's goal of making the hatch real.
- Warn only: Least disruptive, but preserves the current defeated detective-control behavior.

**User's answer:** Stop and re-slice (Recommended)

---

### Q2. How should PRSG-010 change the reviewability exception boilerplate in generated roadmap/template content?

**Branch:** Template and exception boilerplate

**Recommended answer:** Remove live boilerplate.
> Generated roadmaps should not carry rubber-stamp exception text. Reference documentation can keep non-live placeholder syntax, but generated governance artifacts should not include a valid pragma by default.

**Alternatives offered:**
- Keep typed examples: Documents valid refactor/infra/upgrade exceptions near users, but leaves copy-paste risk in generated specs.
- Move to comment only: Keeps nearby guidance as comments, but comments can still be copied into committed Markdown.

**User's answer:** Remove live boilerplate (Recommended)

---

### Q3. What should the first O5 monster-epic implementation model be?

**Branch:** Monster-epic model

**Recommended answer:** Parent plus child specs.
> A parent epic marker/manifest gives `speckit-status` a deterministic rollup target while child specs remain thin, executable units.

**Alternatives offered:**
- Docs convention only: Simpler to ship, but scaffold/status cannot reliably automate or validate O5 behavior.
- Separate specs only: Uses existing workflow shape, but loses the explicit shared-epic artifact contract.

**User's answer:** Parent plus child specs (Recommended)

---

### Q4. How should PRSG-010 deepen the flag-system, release-cadence, and consumer-locality probes in `atomicity-route.sh`?

**Branch:** Contextual routing probes

**Recommended answer:** High-confidence only.
> PRSG-007 intentionally kept these as hints because shallow keyword hits are unsafe. PRSG-010 should promote them only when deterministic evidence is strong enough to route, and otherwise keep conservative existing behavior.

**Alternatives offered:**
- Always decide route: Maximizes automation, but risks false `branch-by-abstraction` or unsafe split decisions.
- Keep advisory: Lowest risk to routing behavior, but does not satisfy the roadmap's US3 hardening goal.

**User's answer:** High-confidence only (Recommended)

---

### Q5. How should PRSG-010 itself be delivered now that PRSG-009 supports split-PR emission?

**Branch:** Delivery shape and slice sizing

**Recommended answer:** Split stack.
> PRSG-010 crosses gate, router, scaffold, status, templates, and tests. Using an ordered stack dogfoods the new PRSG-009 path and keeps review scope small.

**Alternatives offered:**
- One PR: Simpler setup, but likely too broad across multiple shared surfaces.
- Defer O5: Keeps the first PR smaller, but contradicts the roadmap scope for PRSG-010.

**User's answer:** Split stack (Recommended)

---

### Q6. Should PRSG-010 preserve valid explicit typed exceptions after removing the generated boilerplate?

**Branch:** Exception policy

**Recommended answer:** Preserve explicit exceptions.
> PRSG-006 created typed exceptions for legitimate refactor, infra, and upgrade cases. PRSG-010 should remove generated pressure to use them, not delete the mechanism.

**Alternatives offered:**
- Disable all exceptions: Makes the backstop strict, but may block legitimate work the gate cannot fairly size.
- Require approval step: Adds governance around exceptions, but expands scope beyond the current shell/template surfaces.

**User's answer:** Preserve explicit exceptions (Recommended)

---

### Q7. What artifact shape should O5 parent and child specs use?

**Branch:** O5 artifact contract

**Recommended answer:** Parent manifest plus child dirs.
> The parent artifact makes the epic durable and rollup-friendly. Child specs remain independent enough for normal SpecKit phases and split-PR emission.

**Alternatives offered:**
- Flat sibling dirs: Easier for current lints and worktrees, but the parent/child relationship is less structurally obvious.
- Parent doc only: Minimal file churn, but status rollup and recovery are harder to make deterministic.

**User's answer:** Parent manifest plus child dirs (Recommended)

---

### Q8. Should O5 child specs be nested under the parent directory or be flat sibling spec directories linked by a parent manifest?

**Branch:** O5 directory shape

**Recommended answer:** Flat siblings linked.
> Current MOC, stale-index, and `specs/*` assumptions are already tuned for flat spec directories. A parent manifest can establish hierarchy without changing every tree scanner in v1.

**Alternatives offered:**
- Nested children: More visually obvious hierarchy, but risks changing MOC/lint/index assumptions across the spec tree.
- Decide in plan: Defers the shape, but leaves scaffold/status prompts less actionable.

**User's answer:** Flat siblings linked (Recommended)

## Open Questions

None. Clarify should still verify exact schema names, emitted JSON fields, and status rollup wording against implementation constraints before Plan.

## Recommended Next Step

Run `$speckit-autopilot docs/ai/specs/.process/PRSG-010-workflow.md` from the `prsg-010-harden-the-hatch` worktree.
