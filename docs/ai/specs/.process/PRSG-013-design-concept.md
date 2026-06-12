---
topic: "Autopilot reviewability markers"
slug: "PRSG-013-reviewability-markers"
date: "2026-06-12"
mode: "standalone"
source_input:
  type: "topic"
  ref: "Fix autopilot reviewability sizing so it never stops implementation and emits scoped PRs at user-story boundaries."
question_count: 13
stop_reason: "natural"
---

# Design Concept: Autopilot Reviewability Markers

> **Source:** Fix autopilot reviewability sizing so it never stops implementation and emits scoped PRs at user-story boundaries.
> **Date:** 2026-06-12
> **Questions asked:** 13
> **Stop reason:** natural

## Goals

- Autopilot must never stop implementing a spec because of reviewability sizing.
- Reviewability sizing becomes planning and emission input, not a blocking gate.
- Autopilot creates durable PR markers at task user-story boundaries after Tasks.
- The Implement phase executes and checkpoints work in PR-marker order.
- PR emission consumes the persisted markers so created PRs are bounded and scoped to Foundation or a user story.
- Oversized user-story markers are subdivided inside the story when safe task-cluster boundaries exist.
- Hard-atomic or release-sensitive hazards can collapse markers into one PR, but must not stop implementation.

## Non-goals

- Do not remove correctness gates. Malformed plans, failed verification, invalid PR packets, and similar hard failures may still stop.
- Do not change the stable `reviewability-gate.sh tasks` script contract just to avoid stops.
- Do not rewrite `tasks.md` with marker comments as the authoritative marker store.
- Do not fold this behavior into PRSG-012; create PRSG-013 as a prerequisite spec and resume PRSG-012 afterward.

## Design Tree (Q&A log)

### Q1. Should the no-stop rule apply to every reviewability sizing boundary, including both the post-G5 task gate and the final pre-PR reviewability backstop?

**Branch:** Reviewability gate semantics

**Recommended answer:** All reviewability gates
> Reviewability is a sizing and PR-shaping concern, not a correctness concern. The existing post-G5 and final backstop behavior can block productive implementation, which conflicts with the desired split-PR architecture.

**Alternatives offered:**
- Post-G5 only: Autopilot implements after Tasks, but the final pre-PR backstop may still stop before PR creation.
- Final gate only: Task sizing can still block before implementation, but final PR emission becomes marker-based.

**User's answer:** All reviewability gates

---

### Q2. What should be the authoritative source for PR markers after Tasks completes?

**Branch:** Marker source

**Recommended answer:** User-story sections
> The repo already organizes SpecKit tasks by Foundation, user stories, and Polish, and PRSG-008's layer planner parses that structure. Relying on user-story boundaries makes PR scope explainable to reviewers.

**Alternatives offered:**
- Atomicity route only: Only create markers when the classifier returns split-PR; modify-heavy specs may still flatten into one PR.
- Manual markers: Require the task generator or operator to add explicit marker syntax before PR emission can split.

**User's answer:** User-story sections

---

### Q3. When atomicity detects hard-atomic or release-sensitive hazards, should it be allowed to collapse user-story PR markers into one PR?

**Branch:** Hazard handling

**Recommended answer:** Warn, do not collapse
> This would maximize review slicing and keep reviewability fully non-blocking. It is the most aggressive version of split-by-default.

**Alternatives offered:**
- Collapse to one PR: Hard-atomic signals override user-story markers and produce one PR for safety.
- Stop for operator: Autopilot pauses before implementation or PR creation when hard-atomic hazards appear.

**User's answer:** Collapse to one PR

---

### Q4. If a single user-story PR marker is still over the reviewability budget, what should autopilot do?

**Branch:** Oversized marker handling

**Recommended answer:** Subdivide within story
> This preserves the user's story-scoped review model while giving the system a fallback for very large stories. The split should only happen when task clusters provide safe internal boundaries.

**Alternatives offered:**
- Keep story marker: Emit one oversized but story-scoped PR with an explicit reviewability warning.
- Collapse full spec: If any story is oversized, emit one full-spec PR with warnings.

**User's answer:** Subdivide within story

---

### Q5. Where should autopilot persist the PR markers that drive emission?

**Branch:** Marker storage

**Recommended answer:** Layer plan state
> Persisting markers in `autopilot-state.json` and workflow evidence keeps `tasks.md` as the source task list and avoids mutating generated task prose. This matches the existing layer-plan pattern.

**Alternatives offered:**
- Inside tasks.md: Rewrite the generated task list with explicit PR marker comments for later phases to consume.
- Both places: Write markers into `tasks.md` and also duplicate them into state/workflow evidence.

**User's answer:** Layer plan state

---

### Q6. Should `reviewability-gate.sh tasks` itself stop returning exit 1 on block, or should only autopilot change how it handles that result?

**Branch:** Gate API compatibility

**Recommended answer:** Autopilot handling only
> Keeping the script contract stable reduces blast radius. Autopilot can guard the call, capture the JSON, and convert `block` into marker-sizing input without changing lower-level tests or tools.

**Alternatives offered:**
- Change script exit code: Make tasks mode return 0 for block/warn so callers cannot accidentally stop.
- Add new mode: Keep existing tasks behavior and add a separate non-blocking marker-sizing mode for autopilot.

**User's answer:** Autopilot handling only

---

### Q7. Should non-reviewability gates still be allowed to stop autopilot before implementation or PR creation?

**Branch:** Blocking boundary

**Recommended answer:** Yes, correctness gates stay
> The bug is reviewability sizing stopping implementation, not every gate stopping. Correctness and safety gates still need authority to prevent malformed or invalid output.

**Alternatives offered:**
- No stops at all: Autopilot should continue through every gate failure and only report problems later.
- Only tests stop: Spec/analyze/planner failures become warnings, but failed verification still blocks.

**User's answer:** Yes, correctness gates stay

---

### Q8. When the final pre-PR reviewability backstop sees the full diff is too large, what should happen?

**Branch:** Final backstop behavior

**Recommended answer:** Emit marked PRs
> The final backstop should consume the persisted marker plan, not require the operator to re-slice manually. Oversize evidence belongs in the PR packet as reviewer context.

**Alternatives offered:**
- Regenerate markers then emit: If the full diff is too large, rerun marker planning at the final phase before PR creation.
- Single PR with warning: Do not stop, but ignore markers and create one full-spec PR with a reviewability warning.

**User's answer:** Emit marked PRs

---

### Q9. Should the Implement phase execute and checkpoint work in PR-marker order so emission has clean per-marker diffs?

**Branch:** Implementation ordering

**Recommended answer:** Yes, marker order
> Per-marker implementation checkpoints make scoped PR emission deterministic. Emission should not have to infer slice membership from one large mixed diff after implementation.

**Alternatives offered:**
- No, implement freely: Let implementation happen in any order and have emission infer per-marker changes afterward.
- Only checkpoint tests: Implement freely, but record scoped verification evidence per marker for reviewers.

**User's answer:** Yes, marker order

---

### Q10. How should non-user-story phases like Foundation and Polish map to PR markers?

**Branch:** Marker phase mapping

**Recommended answer:** Foundation plus stories
> A Foundation marker is useful when shared setup exists. Small polish should be folded into the nearest story or final marker so PR count does not grow for cleanup-only work.

**Alternatives offered:**
- Stories only: Fold Foundation into US1 and Polish into the last user-story PR so every PR is strictly story-named.
- Every phase marker: Emit separate PRs for Foundation, each user story, and Polish even when polish is small.

**User's answer:** Foundation plus stories

---

### Q11. Where should this reviewability-marker behavior be captured for implementation?

**Branch:** Spec destination

**Recommended answer:** New prerequisite spec
> The behavior changes autopilot sizing, layer planning, implementation ordering, and PR emission. That is a prerequisite to PRSG-012, not a safe addition to the reviewer-packet spec.

**Alternatives offered:**
- Pivot PRSG-012: Change the current PRSG-012 scaffold from reviewer-ready packets into this reviewability-marker fix.
- Fold into PRSG-012: Keep PRSG-012 as reviewer packets but add this behavior into its scope.

**User's answer:** New prerequisite spec

---

### Q12. What ID should the new prerequisite spec use?

**Branch:** Roadmap identity

**Recommended answer:** PRSG-013
> PRSG-013 is the next roadmap ID and avoids mutating the already scaffolded PRSG-012 identity. PRSG-012 can be paused until PRSG-013 lands.

**Alternatives offered:**
- PRSG-012A: Make it a child/prelude of the current PRSG-012 work rather than a new roadmap item.
- Rename PRSG-012: Reuse the current PRSG-012 ID for this prerequisite and move reviewer packets later.

**User's answer:** PRSG-013

---

### Q13. What proof should PRSG-013 require to show the bug is fixed?

**Branch:** Verification proof

**Recommended answer:** Layer 4 plus L3
> Layer 4 gives deterministic shell coverage for marker planning and non-stopping reviewability handling. L3 covers the autopilot behavior contract so future guidance does not regress into stopping.

**Alternatives offered:**
- Layer 4 only: Use shell fixtures as the sole proof; faster, but less coverage of agent guidance behavior.
- Full dogfood run: Require a live autopilot dogfood run that emits user-story PRs before the spec is considered done.

**User's answer:** Layer 4 plus L3

## Open Questions

- **What:** Exact shape of the persisted marker object in `autopilot-state.json`.
  **Why deferred:** This belongs in PRSG-013 planning/contracts.
  **Suggested next step:** Define the schema during PRSG-013 Plan and cover it with Layer 4 fixtures.
- **What:** Exact subdivision algorithm for oversized single user stories.
  **Why deferred:** The interview locked the behavior but not the internal heuristic.
  **Suggested next step:** Start from task dependency clusters and only subdivide when the plan has safe internal boundaries.
- **What:** How hard-atomic collapse interacts with marker-order implementation checkpoints.
  **Why deferred:** The user chose collapse-to-one-PR for hazards while retaining non-stopping implementation.
  **Suggested next step:** PRSG-013 should define this as "implement in marker order, emit one hazard-collapsed PR when required."

## Recommended Next Step

Add PRSG-013 to the PR-size governance roadmap as a prerequisite to resuming
PRSG-012, then scaffold PRSG-013 and run autopilot on that spec.
