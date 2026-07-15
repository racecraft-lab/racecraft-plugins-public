---
topic: "Harness surface inventory and gap taxonomy"
slug: "hrns-001-harness-surface-inventory-gap-taxonomy"
date: "2026-07-15"
mode: "setup"
spec_id: "HRNS-001"
source_input:
  type: "file"
  ref: "docs/ai/specs/harness-engineering-uplift-technical-roadmap.md (HRNS-001 section)"
question_count: 9
stop_reason: "natural"
---

# Design Concept: Harness surface inventory and gap taxonomy

> **Source:** `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md` (HRNS-001 section)
> **Date:** 2026-07-15
> **Questions asked:** 9
> **Stop reason:** natural

## Goals

- Inventory the verified merged `origin/main` baseline without blocking on active CAR or G56R work.
- Create one canonical, reviewable Markdown planning artifact that inventories harness surfaces, evidence classes, retained gaps, owner workflows, downstream ownership, and external candidates.
- Give every retained gap one stable `HRNS-GAP` identifier and one canonical row with surface tags, lifecycle state, owner workflow, and downstream HRNS ownership.
- Keep the taxonomy living and review-controlled so later specs can close or revise gaps without replacing stable identities.
- Evaluate external candidates from dated primary sources without installing, prototyping, or making any candidate a runtime dependency in HRNS-001.
- Treat unclear self-improvement approval boundaries as unknown and non-promotable until a later safety spec proves a bounded control path.
- Prove completion through an AC-1.1 through AC-1.10 crosswalk, enumerated coverage, link checks, and applicable repository documentation validation.
- Keep HRNS-001 as one docs/process slice. The advisory estimator used one user story, four files, and ten functional requirements and returned `{"estimated_loc":335,"suggested_slices":1,"status":"ok"}`.

## Non-goals

- Waiting for CAR or G56R to merge before inventory work begins (Q1).
- Treating unmerged branch content as authoritative current state (Q1).
- Creating a machine-readable taxonomy registry or generated runtime metadata (Q2, Q5).
- Installing or prototyping external candidates during HRNS-001 (Q4).
- Authorizing any external candidate as a required runtime dependency without a dedicated downstream decision (Q4, Q9).
- Assuming that PR review alone proves a workflow is human-in-the-loop (Q6).
- Building a new taxonomy validator, runtime helper, policy, trace, or eval behavior (Q7).
- Absorbing CAR/G56R-owned work into the HRNS lane or omitting it from the inventory (Q8).

## Design Tree (Q&A log)

### Q1. What should HRNS-001 treat as its authoritative current-state cutoff while CAR and G56R work may still be active?

**Branch:** Baseline and dependencies

**Recommended answer:** Merged baseline
> Inventory the verified `origin/main` baseline now, classify unmerged CAR/G56R material as planned reference evidence, and do not block HRNS-001. The roadmap declares `Depends On: None`, and repository source evidence is the authoritative factual baseline.

**Alternatives offered:**
- Wait for routing: Block HRNS-001 until CAR and G56R are merged, producing a later but more settled baseline.
- Include branches: Treat active CAR/G56R branch content as current state, accepting a volatile and harder-to-reproduce baseline.

**User's answer:** Merged baseline (Recommended)

---

### Q2. What should be the canonical deliverable for HRNS-001's inventory, taxonomy, and candidate evaluation matrix?

**Branch:** Artifact ownership

**Recommended answer:** One Markdown artifact
> Keep one reviewable docs/process file as the canonical planning artifact, with all tables embedded and downstream specs linking to it. This follows the roadmap's explicit decision that the taxonomy is a planning artifact rather than a runtime registry.

**Alternatives offered:**
- Markdown plus data: Add a machine-readable JSON or YAML companion now, increasing files and schema decisions before a runtime consumer exists.
- Roadmap sections only: Keep the taxonomy inside the roadmap, reducing files but making the roadmap oversized and harder for downstream specs to cite.

**User's answer:** One Markdown artifact (Recommended)

---

### Q3. How should downstream HRNS specs refer to individual gaps without duplicating or renaming them?

**Branch:** Gap identity and traceability

**Recommended answer:** Stable gap IDs
> Assign each retained gap one stable `HRNS-GAP` identifier with surface tags, state, owner workflow, and downstream ownership in a canonical row. Stable identities make the roadmap's downstream ownership and closure requirements reviewable over time.

**Alternatives offered:**
- Named rows only: Use descriptive row names without IDs, which is simpler but makes cross-spec traceability more fragile.
- Per-surface lists: Repeat gaps under each surface, improving local scanning while creating duplicate ownership and state records.

**User's answer:** Stable gap IDs (Recommended)

---

### Q4. How deep should HRNS-001 evaluate external schema, orchestration, trace, eval, guardrail, workflow, and knowledge-format candidates?

**Branch:** External-candidate evaluation

**Recommended answer:** Evidence matrix only
> Use current primary sources to compare fit, privacy, license, supply-chain, maturity, compatibility gaps, and recommendation without installing or prototyping candidates. This preserves the roadmap's docs/process boundary and keeps dependency adoption with later dedicated decisions.

**Alternatives offered:**
- Matrix plus spikes: Prototype selected candidates during HRNS-001, yielding stronger evidence but expanding a docs/process inventory into implementation research.
- Names and links: Record only candidate names and references, staying small but leaving downstream dependency decisions under-grounded.

**User's answer:** Evidence matrix only (Recommended)

---

### Q5. After HRNS-001 establishes the baseline, how should the taxonomy evolve as later HRNS specs change harness surfaces or close gaps?

**Branch:** Artifact lifecycle

**Recommended answer:** Living reviewed artifact
> Treat it as a committed planning baseline that later specs update through normal review while preserving stable IDs and change history. A living artifact prevents downstream specs from rediscovering stale boundaries without turning the document into runtime state.

**Alternatives offered:**
- Frozen snapshot: Freeze HRNS-001 at completion and make later specs create separate delta documents, preserving history but fragmenting current truth.
- Generated registry: Regenerate it from code and manifests, which would make it operational metadata and conflict with the roadmap's planning-artifact decision.

**User's answer:** Living reviewed artifact (Recommended)

---

### Q6. How should HRNS-001 classify a workflow that can influence future harness behavior when its approval boundary is unclear?

**Branch:** Self-improvement safety

**Recommended answer:** Unknown and non-promotable
> Record the loop as unknown and prohibit automated promotion until a later safety spec proves a bounded human-control path. This preserves AC-1.4's distinction between missing evidence and a deliberate prohibition while failing closed on control changes.

**Alternatives offered:**
- Disallowed immediately: Classify every unclear loop as disallowed, maximizing safety but losing the distinction between missing evidence and a deliberate prohibition.
- HITL by assumption: Assume human-in-the-loop when a PR review exists, which is optimistic and may miss earlier automated mutations.

**User's answer:** Unknown and non-promotable (Recommended)

---

### Q7. What proof should make HRNS-001 complete without turning this docs/process spec into runtime implementation?

**Branch:** Verification and completion

**Recommended answer:** Traceable docs proof
> Require an AC-1.1 through AC-1.10 crosswalk, enumerated surface/evidence coverage, link checks, and applicable repository documentation validation. This makes omissions visible while respecting the roadmap's implementation exclusions.

**Alternatives offered:**
- Manual review only: Rely on reviewer inspection with no explicit crosswalk, keeping effort low but making omissions harder to detect.
- New validator code: Build a taxonomy schema and automated validator now, adding runtime/test surfaces that the roadmap explicitly defers.

**User's answer:** Traceable docs proof (Recommended)

---

### Q8. When HRNS-001 finds a harness gap already owned by CAR or G56R, how should the taxonomy record it?

**Branch:** Cross-roadmap ownership

**Recommended answer:** Cross-reference owner
> Keep one HRNS gap record marked planned or external-owner, link CAR/G56R evidence, and avoid duplicating or blocking that work. This preserves inventory completeness while keeping implementation ownership in its existing lane.

**Alternatives offered:**
- Defer the row: Omit the gap until CAR/G56R finishes, reducing provisional records but making the inventory knowingly incomplete.
- Absorb into HRNS: Move the work into a downstream HRNS spec, creating overlapping ownership and roadmap churn.

**User's answer:** Cross-reference owner (Recommended)

---

### Q9. What evidence standard should support each external-candidate recommendation?

**Branch:** External evidence quality

**Recommended answer:** Dated primary sources
> Cite current official specifications, documentation, repositories, and license material with an as-of date; mark any unsupported field unknown. External maturity, versions, licenses, and product behavior can drift, so row-level primary evidence is required for reproducibility.

**Alternatives offered:**
- Mixed web sources: Allow articles and vendor comparisons for faster breadth, accepting weaker authority and possible staleness.
- Maintainer judgment: Record recommendations without row-level citations, keeping the matrix compact but reducing auditability.

**User's answer:** Dated primary sources (Recommended)

## Open Questions

- **What:** The exact starting set of external candidates and normative revisions to include in the matrix.
  **Why deferred:** The PRD names candidate families and examples, but current versions, maturity, and licensing require live primary-source research during execution.
  **Suggested next step:** Start from PRD OQ-6 and AC-1.10, verify every retained candidate against current official sources, and record an as-of date plus unknowns.
- **What:** The final field names and numbering format for `HRNS-GAP` rows.
  **Why deferred:** Stable identity and required semantics are settled; exact table columns belong in Specify and Plan.
  **Suggested next step:** Define one canonical row schema that covers AC-1.2 through AC-1.5, ownership, evidence, and lifecycle without creating a machine-readable registry.
- **What:** The exact applicable documentation-validation and link-check commands.
  **Why deferred:** The repository documents no root bootstrap/install/build/index command, and HRNS-001 must select existing checks without adding tooling.
  **Suggested next step:** During Plan, inspect the suite manifest and existing docs validation surfaces, then record the smallest relevant commands in the task and PR packets.

## Recommended Next Step

Continue setup by creating `docs/ai/specs/.process/HRNS-001-workflow.md` and the feature SPEC-MOC, then run setup-mode autopilot from the dedicated worktree with:

```text
$speckit-autopilot docs/ai/specs/.process/HRNS-001-workflow.md
```
