---
topic: "PRSG-009 multi-PR emission"
slug: "prsg-009-multi-pr-emission"
date: "2026-06-10"
mode: "setup"
spec_id: "PRSG-009"
source_input:
  type: "topic"
  ref: "PRSG-009 roadmap entry: Multi-PR emission (post-implementation rewrite)"
question_count: 7
stop_reason: "natural"
---

# Design Concept: PRSG-009 multi-PR emission

> **Source:** PRSG-009 roadmap entry: Multi-PR emission (post-implementation rewrite)
> **Date:** 2026-06-10
> **Questions asked:** 7
> **Stop reason:** natural

## Goals

- Stop flattening post-implementation output into one pull request when the layer plan contains multiple reviewable slices.
- Emit N pull requests in PRSG-008 layer-plan dependency order using a Style B incremental stack.
- Carry each slice's scoped tests and per-slice PR body into the corresponding pull request.
- Update the spec MOC generated PR table incrementally with `slice -> PR# -> SHA` after each successful PR creation.
- Provide squash-merge restack support with `gh-stack` when available and a deterministic `restack.sh` fallback otherwise.
- Keep full-suite verification as a base/last-merge gate while each slice PR gates on its scoped tests.

## Non-goals

- New review-routing heuristics are out of scope; PRSG-009 consumes PRSG-008 layer plans and does not invent new slicing rules (Q7).
- Creating PRs before the full implementation and verification pass is out of scope for this scaffolded behavior (Q3).
- Continuing past a slice with failed scoped tests is out of scope; emission stops at the failed slice and records evidence (Q4).
- Replacing PRSG-008 `plan-layers.sh` as the ordering source is out of scope (Q2).

## Design Tree (Q&A log)

### Q1. For PRSG-009, what should the default multi-PR branch topology be when a spec has multiple planned slices?

**Branch:** Branch topology

**Recommended answer:** Incremental stack
> Create slice branches in dependency order, with each slice branch based on the previous slice so reviewers see small ordered PRs. This matches the roadmap's Style B incremental stack and avoids presenting dependent slices as independent when they are not.

**Alternatives offered:**
- Parallel branches: Create every slice branch from the original base; simpler git shape, but dependencies between slices are harder to represent.
- Single branch fallback: Keep one branch unless the operator explicitly opts into multiple PRs; lowest behavior change, but it delays the PRSG-009 headline win.

**User's answer:** Incremental stack

---

### Q2. How should PRSG-009 decide which planned slice gets emitted as which PR?

**Branch:** Slice ordering

**Recommended answer:** Use the PRSG-008 layer plan order
> Preserve `plan-layers.sh` dependency order as the source of truth for PR emission. PRSG-008 already owns deterministic layer planning, so PRSG-009 should consume that contract instead of deriving a second ordering model.

**Alternatives offered:**
- Use task-file order: Emit PRs based on the order of tasks in `tasks.md`; simpler, but weaker dependency guarantees.
- Require manual ordering: Ask the operator to approve or reorder slices before PR creation.

**User's answer:** Use the PRSG-008 layer plan order

---

### Q3. When should PRSG-009 create the slice PRs?

**Branch:** Emission timing

**Recommended answer:** After full implementation and verification
> Run implementation once, verify the full stack, then emit N ordered PRs from the finished slice branches. This keeps PR creation in post-implementation where the existing workflow already runs verification and has enough context to map tests to slices.

**Alternatives offered:**
- As each slice finishes: Create each PR immediately after its slice passes scoped tests; faster feedback, but more resume/recovery complexity.
- Operator-triggered only: Prepare branch metadata, but require an explicit command before opening PRs.

**User's answer:** After full implementation and verification

---

### Q4. If one slice fails its scoped tests during multi-PR emission, what should the autopilot do?

**Branch:** Failure handling

**Recommended answer:** Stop before opening that slice's PR
> Keep already-created earlier PRs, do not create later PRs, and record the failed slice/test evidence in the workflow and `autopilot-state.json`. This preserves a truthful stack and avoids publishing known-bad review units.

**Alternatives offered:**
- Open a draft PR with failure evidence: Makes the failure visible on GitHub, but creates review noise for a known-bad slice.
- Skip the failed slice and continue: Maximizes progress, but risks producing a misleading or broken stack.

**User's answer:** Stop before opening that slice's PR

---

### Q5. What should happen to the spec MOC's generated PR table during emission?

**Branch:** MOC state

**Recommended answer:** Update after each successfully created PR
> Record `slice -> PR# -> SHA` incrementally so resume/recovery has durable state. This matches the generated PRS table's role as the review navigation record.

**Alternatives offered:**
- Update only after all PRs are created: Cleaner final write, but recovery after partial emission is weaker.
- Do not update during PR creation: Leave the MOC table to a separate follow-up command.

**User's answer:** Update after each successfully created PR

---

### Q6. How should PRSG-009 handle restacking after squash merges?

**Branch:** Restack

**Recommended answer:** Document and automate a `restack.sh` fallback
> Use `gh-stack` when available, otherwise provide a deterministic rebase/cherry-pick helper for the review loop. This avoids a hard external dependency while still reducing manual maintainer work.

**Alternatives offered:**
- Document manual restack only: Less code in PRSG-009, but pushes more operational burden onto the maintainer.
- Require `gh-stack`: Simpler implementation path, but adds a hard external dependency.

**User's answer:** Document and automate a `restack.sh` fallback

---

### Q7. What should PRSG-009 explicitly not implement?

**Branch:** Scope boundary

**Recommended answer:** No new review-routing heuristics
> Only consume PRSG-008 layer plans and implement PR emission/restack behavior; leave new slicing heuristics to PRSG-010. This follows the constitution's KISS/YAGNI principle and keeps the spec on the roadmap's intended behavior change.

**Alternatives offered:**
- No CI mapping changes: Focus only on opening PRs, leaving scoped-test/full-suite mapping for a later spec.
- No branch topology changes: Only generate PR bodies for planned slices; defer actual multi-branch behavior.

**User's answer:** No new review-routing heuristics

## Slice Sizing

- Estimator command: `bash speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh --user-stories 3 --files 4 --frs 9 --new-vs-modify modify`
- Result: `{"estimated_loc":185,"suggested_slices":1,"status":"ok"}`
- Decision: no scaffold-time split is required. PRSG-009 is itself the implementation of multi-PR emission behavior; it should still use the PRSG-008 layer plan at runtime for downstream specs that do split.

## Open Questions

- **What:** Exact CLI flags and output schema for `restack.sh`.
  **Why deferred:** Better resolved during Plan after the implementation surface is read in detail.
  **Suggested next step:** Define the script contract in `specs/prsg-009-multi-pr-emission/contracts/restack.output.md` or equivalent during Plan.
- **What:** Exact per-slice test metadata shape in `autopilot-state.json`.
  **Why deferred:** Depends on the existing PRSG-008 layer plan envelope and post-implementation state shape.
  **Suggested next step:** Resolve during Plan and keep the schema backward-compatible with PRSG-008 output.

## Recommended Next Step

Run setup completion for PRSG-009, then run `$speckit-autopilot docs/ai/specs/.process/PRSG-009-workflow.md` from the `prsg-009-multi-pr-emission` worktree.
