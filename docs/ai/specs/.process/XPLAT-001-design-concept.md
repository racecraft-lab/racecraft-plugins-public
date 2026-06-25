---
topic: "XPLAT-001 - Runtime inventory and constraints"
slug: "xplat-001-runtime-inventory-constraints"
date: "2026-06-25"
mode: "setup"
spec_id: "XPLAT-001"
source_input:
  type: "file"
  ref: "docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md"
question_count: 9
stop_reason: "natural"
---

# Design Concept: XPLAT-001 - Runtime Inventory and Constraints

> **Source:** `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`
> **Date:** 2026-06-25
> **Questions asked:** 9
> **Stop reason:** natural

## Goals

- Produce one concise, review-visible inventory report plus runtime and
  supply-chain evaluation rubrics.
- Run a whole-repo exhaustive scan for Bash, `.sh`, `jq`, shell quoting,
  Unix-path, `chmod`, and line-ending assumptions, while keeping classification
  strict enough to avoid false blockers.
- For every finding, record evidence, runtime relevance, owner bucket, and the
  follow-up spec that owns it.
- Require an invocation trace before marking a reference as an active installed
  runtime dependency.
- Put the durable inventory and rubric report under `docs/ai/research/` in
  Markdown with structured tables, owner buckets, and summary counts.
- Define runtime and supply-chain criteria, must-have gates, and weights, but
  do not score candidates or choose runtime/security models in XPLAT-001.
- Keep verification static and source-traceable. Native Windows UAT, smoke
  probes, runtime decision work, and implementation belong to later XPLAT specs.
- Keep XPLAT-001 as one inventory/rubric spike. The sizing estimator returned
  `{"estimated_loc":0,"suggested_slices":1,"status":"ok"}` for spike mode.

## Non-goals

- Selecting the replacement runtime. That is XPLAT-002.
- Selecting the supply-chain security approach. That is XPLAT-003.
- Porting helpers, changing active Claude/Codex invocations, rebuilding
  generated payloads, or claiming Windows support.
- Treating every whole-repo text match as an active blocker without tracing it
  to an installed runtime surface.
- Adding native Windows UAT or cross-platform runtime probes in this slice.

## Design Tree (Q&A log)

### Q1. What should XPLAT-001 produce as its primary review-visible deliverable?

**Branch:** Output contract

**Recommended answer:** Inventory + rubrics
> The roadmap names XPLAT-001 as the inventory and evaluation-rubric producer,
> and explicitly keeps runtime and security selection in XPLAT-002 and
> XPLAT-003.

**Alternatives offered:**
- Inventory only: Smaller, but XPLAT-002 and XPLAT-003 would need to invent
  their own evaluation criteria.
- Decision-ready report: Useful for speed, but it crosses the roadmap boundary.

**User's answer:** Inventory + rubrics

---

### Q2. How broad should the XPLAT-001 inventory scan be?

**Branch:** Inventory scope

**Recommended answer:** Installed-runtime first
> The roadmap centers active installed Claude/Codex workflows, so an
> installed-runtime-first scan would reduce noise while still classifying
> generated payloads, docs, fixtures, and archives.

**Alternatives offered:**
- Whole repo exhaustive: Scans every Bash or Unix assumption equally, but can
  become noisy without strict classification.
- Skill files only: Fastest, but likely misses agents, hooks, payloads, docs,
  and marketplace metadata.

**User's answer:** Whole repo exhaustive

---

### Q3. How should each found Bash or Unix-runtime assumption be classified in the inventory?

**Branch:** Classification model

**Recommended answer:** Owner + evidence
> XPLAT-005, XPLAT-006, and XPLAT-007 need actionable ownership, not just counts.
> Recording evidence, runtime relevance, owner bucket, and follow-up spec makes
> later work reviewable and avoids re-triage.

**Alternatives offered:**
- Simple category list: Faster, but weaker handoff for later specs.
- Blockers only: Smaller, but inconsistent with the whole-repo scan decision.

**User's answer:** Owner + evidence

---

### Q4. What evidence standard should XPLAT-001 require before marking a reference as an active runtime dependency?

**Branch:** Evidence standard

**Recommended answer:** Trace to invocation
> The capability-discovery and grounding references require claims to be tied to
> real sources. For this inventory, active runtime status should require a trace
> from an installed skill, agent, hook, or generated payload to the dependency.

**Alternatives offered:**
- Text match enough: Maximizes caution, but creates many false positives.
- Maintainer judgment: Faster, but harder to review consistently.

**User's answer:** Trace to invocation

---

### Q5. Where should the inventory and rubrics live after XPLAT-001 runs?

**Branch:** Artifact layout

**Recommended answer:** Spec artifacts
> Keeping durable deliverables under the spec directory would make them travel
> with `spec.md`, `plan.md`, `tasks.md`, and the SPEC-MOC.

**Alternatives offered:**
- Docs research: Easier to browse, but less tied to the active SpecKit artifact
  set.
- Both mirrored: Discoverable, but creates duplicate-maintenance risk.

**User's answer:** Docs research

---

### Q6. What format should the XPLAT-001 inventory use so later specs can consume it reliably?

**Branch:** Report format

**Recommended answer:** Markdown + table
> A Markdown report with structured tables is easiest to review in the PR while
> still giving later specs enough structure to consume owner buckets and summary
> counts.

**Alternatives offered:**
- Markdown + JSON: Better automation, but increases maintenance and validation
  work in this spike.
- CSV appendix: Good for spreadsheet review, but weaker for rationale and
  SpecKit handoff.

**User's answer:** Markdown + table

---

### Q7. How detailed should the runtime and supply-chain rubrics be in XPLAT-001?

**Branch:** Rubric depth

**Recommended answer:** Criteria + weights
> XPLAT-002 and XPLAT-003 need enough structure to evaluate options without
> reopening priority debates, but scoring candidates now would cross the
> roadmap boundary.

**Alternatives offered:**
- Criteria only: Avoids premature weighting, but leaves priority debate for
  later specs.
- Score candidates now: Faster decisions, but crosses into XPLAT-002 and
  XPLAT-003 scope.

**User's answer:** Criteria + weights

---

### Q8. What verification should XPLAT-001 require for the inventory report itself?

**Branch:** Verification scope

**Recommended answer:** Static checks only
> The roadmap keeps runtime decision and UAT work in later specs. XPLAT-001
> should prove its report through repo scans, source traceability, spec-index
> freshness, and normal Markdown/diff checks.

**Alternatives offered:**
- Add smoke probes: Useful evidence, but may blur into XPLAT-002 runtime
  evaluation.
- Manual review only: Faster, but weaker confidence that the inventory is
  complete and traceable.

**User's answer:** Static checks only

---

### Q9. Should XPLAT-001 remain one inventory/rubric spike, or be split before setup?

**Branch:** Slice sizing

**Recommended answer:** One spike
> The roadmap classifies XPLAT-001 as an architecture/inventory spike. The
> shared estimator returned one slice in spike mode, and later specs own
> decisions and implementation.

**Alternatives offered:**
- Split scan/rubrics: Smaller reviews, but delays XPLAT-002 and adds process
  overhead.
- Decide later: Leaves a Clarify decision for autopilot.

**User's answer:** One spike

## Open Questions

- None. Candidate scoring, native runtime probes, security-model selection, and
  public support claims are deliberately deferred to later XPLAT specs, not
  unresolved XPLAT-001 questions.

## Recommended Next Step

Run `$speckit-autopilot docs/ai/specs/.process/XPLAT-001-workflow.md` from the
`codex/xplat-001-runtime-inventory-constraints` worktree.
