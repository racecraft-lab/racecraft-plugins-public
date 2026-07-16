---
topic: "G56R-001 candidate route baseline and role contracts"
slug: "g56r-001-candidate-route-baseline"
date: "2026-07-15"
mode: "setup"
spec_id: "G56R-001"
source_input:
  type: "file"
  ref: "docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md"
question_count: 6
stop_reason: "natural"
---

# Design Concept: G56R-001 candidate route baseline and role contracts

> **Source:** `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md`
> **Date:** 2026-07-15
> **Questions asked:** 6
> **Stop reason:** natural

## 2026-07-16 Evidence-Parity Amendment

The original interview remains the historical G56R-001 setup record. The
approved CAR/G56R parity plan supersedes only Q3's packaging decision: the
canonical human report now has one schema-v2 planning-manifest companion at
`docs/ai/research/codex-agent-route-candidate-manifest.json`. The companion
validates against the shared planning schema and contract, is not runtime
configuration, and does not affect installers, payloads, caches, or versions.

- Shared contract: `docs/ai/specs/agent-routing-parity-contract.md`
- Shared schema: `docs/ai/research/agent-route-candidate-manifest.schema.json`
- Historical integrity: the original answer and alternatives below remain
  unchanged as execution evidence.

## Goals

- Ground every Codex platform fact and candidate admission in current official OpenAI documentation only.
- Revalidate official sources when G56R-001 executes, record retrieval dates, and freeze that evidence for the spec.
- Treat the five roadmap model IDs as a seed that may change only when execution-time official documentation supports the change.
- Publish one canonical human research report and one schema-v2 planning manifest containing the official-source ledger, all twelve project-input role contracts, provisional candidate routes, fixture backlog, and G56R-002 handoff.
- Define executable fixture specifications without creating or running live fixture payloads.
- Require strict claim-to-source and role-contract traceability, plus the full operational requirement-quality checklist set.

## Non-goals

- Freezing a scaffold-time evidence snapshot or continuously changing the evidence set during the spec - answered in Q1 (Doc snapshot).
- Treating the roadmap's five candidate IDs as permanently fixed or admitting unrelated models without role-contract filtering - answered in Q2 (Candidates).
- Splitting the research handoff across several documents or adding a runtime JSON manifest - answered in Q3 (Artifacts).
- Proving candidate executability, qualification, or preferred ordering through live runs in G56R-001 - answered in Q4 (Exit gate).
- Creating or executing fixture payloads during this research spike - answered in Q5 (Fixtures).
- Limiting requirement-quality review to LLM routing alone - answered in Q6 (Checklists).

## Design Tree (Q&A log)

### Q1. When should G56R-001 freeze the official-documentation evidence it will evaluate?

**Branch:** Evidence lifecycle

**Recommended answer:** Execution snapshot (Recommended)
> The roadmap requires the official-source ledger to be revalidated before each consuming scaffold and makes changed documentation an invalidation trigger. Freezing a dated execution snapshot keeps the evidence current without introducing continuous churn.

**Alternatives offered:**
- Scaffold snapshot: Freeze the sources available during scaffolding, which may be stale by execution time.
- Continuous refresh: Keep refreshing evidence through implementation and merge, increasing churn and review scope.

**User's answer:** Execution snapshot (Recommended)

---

### Q2. Should the five model IDs in the roadmap be a fixed candidate set or a seed for the execution-time official-doc review?

**Branch:** Candidate admission

**Recommended answer:** Seed and refresh (Recommended)
> The roadmap calls the table an official candidate seed rather than an approved route table. Execution-time official documentation is the sole authority for adding, retaining, or removing a model candidate.

**Alternatives offered:**
- Freeze five IDs: Evaluate exactly the five roadmap IDs even if official documentation has changed.
- All documented models: Include every officially documented model without first filtering for the agent-role contract.

**User's answer:** Seed and refresh (Recommended)

---

### Q3. How should G56R-001 package its source ledger, role contracts, candidate routes, and fixture backlog?

**Branch:** Artifact structure

**Recommended answer:** One canonical report (Recommended)
> One report keeps the versioned IDs and their evidence bindings reviewable as a single research handoff. It also preserves the roadmap's documentation-only scope and approximately three-file budget.

**Alternatives offered:**
- Separate documents: Create independent documents for sources, roles, candidates, and fixtures, increasing cross-file coordination.
- Report plus JSON: Add a machine-readable candidate manifest now, expanding the research spike beyond documentation-only output.

**User's answer:** One canonical report (Recommended)

**2026-07-16 supersession:** Preserve the canonical report, and add exactly one
machine-readable planning manifest governed by the shared CAR/G56R schema. The
original rejection of a *runtime* JSON manifest remains in force.

---

### Q4. What must be complete before G56R-001 can hand off candidate routes to G56R-002?

**Branch:** Completion gate

**Recommended answer:** Strict traceability (Recommended)
> AC-1.* requires each platform claim and candidate to bind official evidence and every named agent to have a role contract. Missing support must remain explicit and fail closed; runtime executability belongs to G56R-002.

**Alternatives offered:**
- Allow open gaps: Permit partially sourced candidates or role contracts when follow-up issues are recorded.
- Require live proof: Require runtime model execution evidence now, pulling qualification work from G56R-002 into this spike.

**User's answer:** Strict traceability (Recommended)

---

### Q5. How detailed should the G56R-001 fixture backlog be while keeping live corpus work out of scope?

**Branch:** Fixture handoff

**Recommended answer:** Executable specifications (Recommended)
> Stable fixture IDs, representative inputs, expected signals, and ownership give G56R-003 an actionable backlog while preserving G56R-001's no-execution boundary.

**Alternatives offered:**
- Category list: Record only broad fixture categories and defer exact acceptance signals to G56R-002.
- Build fixtures now: Create and execute fixture payloads during G56R-001, expanding beyond the research-only scope.

**User's answer:** Executable specifications (Recommended)

---

### Q6. Which requirement-quality checklists should the scaffold require for this official-source research spike?

**Branch:** Requirement-quality validation

**Recommended answer:** LLM + evidence + errors (Recommended)
> LLM-routing, evidence-integrity, and fail-closed behavior are the direct risks in this spike. The broader operational domains are useful when the user wants downstream constraints audited before runtime design begins.

**Alternatives offered:**
- LLM only: Review routing requirements without dedicated evidence-integrity or error-handling audits.
- Full operational set: Also add security, observability, and resilience checklists despite no runtime behavior changing in this spec.

**User's answer:** Full operational set

## Open Questions

- **What:** Which model IDs, documented defaults, supported efforts, and client surfaces remain current when execution begins?
  **Why deferred:** The user selected an execution-time official-source snapshot in Q1 and a refreshed seed in Q2.
  **Suggested next step:** Resolve from current official OpenAI documentation during Specify and bind every retained fact to `official_source_ledger_id`.
- **What:** Which documented custom-agent capabilities can express the two Claude-derived orchestration-support contracts without platform-specific weakening?
  **Why deferred:** The answer depends on the execution-time official custom-agent documentation and the project-input parity definitions.
  **Suggested next step:** Record supported fields, explicit divergence, and every `undocumented` gap in the canonical report; defer runtime availability to G56R-002.
- **What:** Which capability and telemetry questions require runtime discovery after the document-eligible candidate set is frozen?
  **Why deferred:** Runtime verification is explicitly outside G56R-001's authority and scope.
  **Suggested next step:** Include a complete, source-bound question backlog and independent go/no-go handoff for G56R-002.

## Recommended Next Step

**Execute the scaffolded workflow.** Run `$speckit-autopilot docs/ai/specs/.process/G56R-001-workflow.md` from the dedicated G56R-001 worktree after scaffold validation and push complete.
