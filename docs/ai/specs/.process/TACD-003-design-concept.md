---
topic: "TACD-003 Prerequisite and Documentation Messaging"
slug: "tacd-003-prerequisite-and-documentation-messaging"
date: "2026-06-18"
mode: "setup"
spec_id: "TACD-003"
source_input:
  type: "file"
  ref: "docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md"
question_count: 6
stop_reason: "natural"
---

# Design Concept: TACD-003 Prerequisite and Documentation Messaging

> **Source:** docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md
> **Date:** 2026-06-18
> **Questions asked:** 6
> **Stop reason:** natural

## Goals

- Replace the hardcoded optional-tool prerequisite report with a generic, non-blocking capability advisory.
- Align active user-facing prerequisite, limitation, and coaching documentation with the TACD-002 capability-first directive.
- Keep active guidance focused on capability categories instead of concrete optional tool IDs.
- Preserve concrete identifiers only where platform metadata, exact file references, or historical provenance require them.
- Explain that missing optional capabilities may lower confidence or trigger escalation when no acceptable evidence path exists, but must not fail setup by itself.
- Include focused deterministic coverage for changed prerequisite output or docs references, while leaving broad static and eval enforcement to TACD-004.
- Keep TACD-003 as one vertical implementation slice; the forward size estimate is 142 LOC, one suggested slice, status `ok`.

## Non-goals

- Reworking active agent behavior already handled by TACD-002.
- Adding broad vendor-neutral static enforcement or functional eval coverage; TACD-004 owns that.
- Adding a tool installer, marketplace integration, or fixed recommended optional-tool set.
- Rewriting historical archive/changelog references, generated source-derived payloads, or fixture text unless they are active user-facing guidance.
- Applying a strict string ban to all concrete tool names.

## Design Tree (Q&A log)

### Q1. For TACD-003, what should the scaffold treat as the primary outcome?

**Branch:** Scope

**Recommended answer:** Advisory + docs
> The roadmap names both prerequisite behavior and user-facing docs as TACD-003 scope. Updating only one would leave either setup output or documentation stale.

**Alternatives offered:**
- Docs only: Avoid script behavior changes and only update prerequisite/coaching documentation; lower risk but leaves stale setup output.
- Script only: Change prerequisite output now and defer docs wording; smaller diff but users still see old guidance elsewhere.

**User's answer:** Advisory + docs

---

### Q2. How strict should TACD-003 be about avoiding concrete optional tool names in active guidance?

**Branch:** Wording

**Recommended answer:** Capabilities only
> TACD-001's allowlist separates active guidance from metadata and history. Capability wording solves the vendor-neutral problem without creating false positives around exact schema IDs or evidence links.

**Alternatives offered:**
- Neutral examples allowed: Permit named examples when clearly marked optional; easier for users but weaker vendor-neutral contract.
- Strict string ban: Remove all concrete names from active and historical text; simple to enforce but likely creates false positives and churn.

**User's answer:** Capabilities only

---

### Q3. What should the prerequisite advisory say when optional research/context capabilities are missing?

**Branch:** Fallback behavior

**Recommended answer:** Non-blocking confidence note
> This matches the TACD-001/TACD-002 direction: setup should continue, while downstream agents make evidence quality visible when they use built-in or lower-confidence fallback paths.

**Alternatives offered:**
- Install suggestion: Continue but recommend installing stronger capabilities; more actionable, but can read like a fixed tool requirement.
- Silent fallback: Continue with no advisory; avoids noise, but hides evidence-quality degradation from users.

**User's answer:** Non-blocking confidence note

---

### Q4. Where should TACD-003 draw the line on tests for this messaging change?

**Branch:** Verification boundary

**Recommended answer:** Focused tests now
> The constitution expects changed script behavior to have focused deterministic coverage. TACD-004 still owns the broader vendor-neutral enforcement suite and functional eval updates.

**Alternatives offered:**
- All tests deferred: Keep TACD-003 implementation/docs only; smaller slice but weaker confidence until TACD-004.
- Full enforcement now: Add broad static and eval enforcement in TACD-003; stronger but duplicates TACD-004 and risks oversizing the slice.

**User's answer:** Focused tests now

---

### Q5. How broad should the user-facing documentation pass be for TACD-003?

**Branch:** Documentation surface

**Recommended answer:** Active prereq docs
> The roadmap key files point at the active prerequisite, limitation, and coaching surfaces users see before running autopilot. Archives and generated duplicates should not be hand-edited in this slice.

**Alternatives offered:**
- All mentions: Search and rewrite every mention across active docs, generated payloads, archives, and fixtures; comprehensive but noisy and risky.
- Minimum docs: Only touch the exact docs listed in the roadmap; less churn but may leave adjacent active guidance stale.

**User's answer:** Active prereq docs

---

### Q6. Should TACD-003 stay as one implementation slice?

**Branch:** Slice sizing

**Recommended answer:** One slice
> The shared estimator returned `{"estimated_loc":142,"suggested_slices":1,"status":"ok"}` for one user story, five touched files, four acceptance criteria, and modify-mode work. The roadmap also records the TACD-003 budget as within budget.

**Alternatives offered:**
- Split script/docs: Separate prerequisite script behavior from docs wording; clearer ownership but adds coordination overhead.
- Decide later: Record the split decision as open and let autopilot revisit if implementation grows.

**User's answer:** One slice

## Open Questions

- **What:** Exact phrasing of the generic prerequisite advisory.
  **Why deferred:** The implementation should derive final copy from the actual `check-prerequisites.sh` JSON shape and existing docs language.
  **Suggested next step:** Resolve during Specify/Plan by keeping the advisory capability-based, non-blocking, and confidence-oriented.

- **What:** Exact deterministic test files to update.
  **Why deferred:** The implementation should inspect existing Layer 4/Layer 5 coverage before editing tests.
  **Suggested next step:** Add focused tests where existing prerequisite or docs-reference assertions already live; leave broad static/eval enforcement to TACD-004.

## Recommended Next Step

Continue `$speckit-scaffold-spec TACD-003` by generating the setup workflow and SPEC-MOC marker, then run `$speckit-autopilot docs/ai/specs/.process/TACD-003-workflow.md`.
