---
topic: "TACD-001 Platform Mechanics Spike"
slug: "tacd-001-platform-mechanics-spike"
date: "2026-06-17"
mode: "setup"
spec_id: "TACD-001"
source_input:
  type: "topic"
  ref: "Tool-Agnostic Capability Discovery roadmap entry for TACD-001"
question_count: 5
stop_reason: "natural"
---

# Design Concept: TACD-001 Platform Mechanics Spike

> **Source:** Tool-Agnostic Capability Discovery roadmap entry for TACD-001
> **Date:** 2026-06-17
> **Questions asked:** 5
> **Stop reason:** natural

## Goals

- Produce a spike report plus minimal reproducible probes where needed.
- Audit current named optional-tool references across active Claude and Codex runtime guidance, prerequisite messaging, plugin limitation docs, and tests/evals.
- Verify both Claude Code and Codex mechanics for discovering installed tools, MCP/app connectors, skills/plugins, and repo-local helpers without hardcoding a vendor-specific MCP list.
- Recommend whether a shared directive reference plus per-agent pointers is reliable enough for TACD-002.
- Define active-vs-historical named-tool reference categories so TACD-004 can later enforce the right contract without erasing provenance.
- Keep TACD-001 as a research spike; do not rewrite shipped runtime behavior, prerequisite messaging, or enforcement tests in this slice.

## Non-goals

- Implementing the capability-discovery directive in active agents; TACD-002 owns behavior changes.
- Replacing the prerequisite MCP report with the generic advisory; TACD-003 owns user-facing prerequisite and docs messaging changes.
- Adding final deterministic enforcement or functional eval updates; TACD-004 owns those.
- Running live AI evals as a setup prerequisite.
- Bundling, installing, or recommending replacement third-party tools.
- Removing historical changelog, archive, provenance, or intentionally historical fixture references.

## Design Tree (Q&A log)

### Q1. What should TACD-001 produce as its primary deliverable?

**Branch:** Deliverable

**Recommended answer:** Spike report
> A decision record that audits current references, verifies platform mechanics, and recommends the directive home without changing runtime behavior.

**Alternatives offered:**
- Report plus probes: Adds minimal test/probe fixtures where needed, increasing confidence but raising scope for a spike.
- Implement directive: Starts rewriting active guidance now, faster but conflicts with the roadmap's spike-first risk control.

**User's answer:** Report plus probes

---

### Q2. What evidence should be enough for TACD-001 to recommend a shared directive reference plus pointers?

**Branch:** Proof bar

**Recommended answer:** Static plus eval plan
> A static audit and planned eval coverage fit the spike scope: enough evidence to choose the directive home without prematurely running live AI evals or rewriting behavior.

**Alternatives offered:**
- Static only: Faster and deterministic, but may miss whether agents actually apply the directive in behavior.
- Live eval required: Highest confidence, but turns the spike into slower live AI-eval work before the directive exists.

**User's answer:** Static plus eval plan (Recommended)

---

### Q3. Which runtime mechanics should TACD-001 verify before later specs change guidance?

**Branch:** Runtime scope

**Recommended answer:** Both runtimes
> The roadmap explicitly targets Claude and Codex parity. Verifying only one runtime would leave TACD-002 exposed to rework.

**Alternatives offered:**
- Codex first: Focuses on the current desktop surface but leaves Claude parity unresolved until a later slice.
- Docs only: Audits current files and docs without checking runtime mechanics, which is quicker but weaker for TACD-002.

**User's answer:** Both runtimes (Recommended)

---

### Q4. How strict should TACD-001 be when it classifies named-tool references like Tavily, Context7, and RepoPrompt?

**Branch:** Allowlist policy

**Recommended answer:** Active vs historical
> Active runtime guidance should become vendor-neutral later, while changelogs, archives, fixtures, and provenance may need to preserve exact historical names.

**Alternatives offered:**
- Strict repo ban: Simpler to test but likely over-removes useful historical provenance and fixture text.
- Advisory only: Captures findings without producing enforceable categories for TACD-004.

**User's answer:** Active vs historical (Recommended)

---

### Q5. Where should TACD-001 put any minimal probes it needs for platform mechanics?

**Branch:** Probe boundary

**Recommended answer:** Research appendix
> Reproducible probe commands and results in the spike report buy down uncertainty while keeping TACD-001 out of shipped behavior and final enforcement.

**Alternatives offered:**
- Temporary fixtures: Add small committed fixtures only when static validation cannot be reasoned about from existing files.
- New enforcement tests: Starts TACD-004 early and may overgrow the spike scope.

**User's answer:** Research appendix (Recommended)

## Open Questions

- **What:** Whether the spike can prove a shared directive reference plus per-agent pointers is reliable enough for both Claude and Codex.
  **Why deferred:** TACD-001 exists to answer this with the audit, mechanics probe appendix, deterministic-check design, and eval-plan recommendation.
  **Suggested next step:** Resolve in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`.

- **What:** Exact file-category allowlist for TACD-004 enforcement.
  **Why deferred:** The final allowlist must come from the TACD-001 audit, not a broad string search.
  **Suggested next step:** Record categories in the spike report, distinguishing active guidance from historical/provenance/fixture references.

## Slice-Size Advisory

- Estimator command: `estimate-spec-size.sh --user-stories 1 --files 3 --frs 4 --new-vs-modify new --spike`
- Estimator result: `{"estimated_loc":0,"suggested_slices":1,"status":"ok"}`
- Decision: keep TACD-001 as one spike slice. LOC sizing is not applicable to research-only work.

## Recommended Next Step

Run `$speckit-autopilot docs/ai/specs/.process/TACD-001-workflow.md` from the TACD-001 worktree.
