---
topic: "Optional gh-stack stack manager integration"
slug: "prsg-014-optional-gh-stack-stack-manager-integration"
date: "2026-06-13"
mode: "setup"
spec_id: "PRSG-014"
source_input:
  type: "topic"
  ref: "docs/ai/specs/pr-size-governance-technical-roadmap.md#prsg-014"
question_count: 5
stop_reason: "natural"
---

# Design Concept: Optional gh-stack stack manager integration

> **Source:** docs/ai/specs/pr-size-governance-technical-roadmap.md#prsg-014
> **Date:** 2026-06-13
> **Questions asked:** 5
> **Stop reason:** natural

## Goals

- Add optional `gh-stack` support for stack-aware PR creation, sync, and restack when deterministic support checks prove the repo and installed extension are safe to use.
- Preserve explicit `gh pr create/edit --base --head` behavior as the canonical fallback for unsupported, missing, or ambiguous `gh-stack` environments.
- Implement a small shared `detect-stack-manager.sh` decision point consumed by both emission and restack, with deterministic fake-CLI Layer 4 coverage.
- Record stack-manager evidence in emission/restack state, including availability, support result, reason, selected manager, command plan, version/support outcome, fallback reason, and PR/branch topology.
- Allow fallback only before irreversible mutation; after any partial `gh-stack` mutation, block with recoverable state instead of mixing stack managers.
- Keep behavior single-copy in shared scripts while updating both Claude Code and Codex guidance plus L8 parity expectations.
- Treat PRSG-014 as one implementation spec. Advisory size estimate: `estimated_loc=325`, `suggested_slices=1`, `status=ok`.

## Non-goals

- Do not make `gh-stack` a required dependency for autopilot or for repositories that do not support it.
- Do not retry with explicit `gh` after a partial `gh-stack` mutation has changed branch or PR topology.
- Do not duplicate stack-manager scripts under `codex-skills/`.
- Do not stop at detection-only or plan-only behavior; PRSG-014 covers create/sync and restack when support checks pass.
- Do not add unrelated stack-management features beyond PR creation/sync, post-squash restack, fallback, evidence, and safety.

## Design Tree (Q&A log)

### Q1. Should PRSG-014 treat gh-stack as an optional strategy selected only after deterministic support checks, with explicit gh base/head emission remaining the canonical fallback?

**Branch:** Stack manager contract

**Recommended answer:** Optional strategy
> The roadmap says `gh-stack` is opportunistic and explicit GitHub bases remain canonical. This keeps existing PRSG-009, PRSG-012, and PRSG-013 behavior reliable in every repository.

**Alternatives offered:**
- gh-stack first: Makes `gh-stack` the primary path and uses explicit `gh` only after failures, increasing dependency and mutation risk.
- Detection only: Records `gh-stack` support evidence now but defers actual create/sync/restack behavior to a later spec.

**User's answer:** Optional strategy

---

### Q2. Where should PRSG-014 put gh-stack support detection so emission and restack use the same decision record?

**Branch:** Detection ownership

**Recommended answer:** Shared script
> A small `detect-stack-manager.sh` has two callers, avoids divergent shell probes, and can be unit-tested with fake `gh-stack` and fake `gh`. This is one of the cases where a helper is justified because it removes real duplication.

**Alternatives offered:**
- Inline probes: Keep detection inside `multi-pr-emission.sh` and `restack.sh`, which is simpler per file but risks behavior drift.
- Schema only: Define evidence fields first and leave runtime detection implementation for a later follow-up.

**User's answer:** Shared script

---

### Q3. When should PRSG-014 allow fallback from gh-stack to explicit gh during create/sync/restack operations?

**Branch:** Mutation and fallback safety

**Recommended answer:** Before mutation only
> Fallback is safe while still planning or dry-running. After any `gh-stack` mutation, switching managers can create ambiguous PR and branch topology, so the safer behavior is to block with recoverable state.

**Alternatives offered:**
- Always retry fallback: Maximizes forward progress, but can create ambiguous topology after partial `gh-stack` changes.
- Never fallback: Keeps stack-manager behavior strict, but loses the roadmap requirement that unsupported or ambiguous repos still use explicit `gh`.

**User's answer:** Before mutation only

---

### Q4. Which gh-stack operations should PRSG-014 implement when support detection passes?

**Branch:** Operation scope

**Recommended answer:** Create and restack
> This covers stack-aware PR creation/sync plus post-squash restack, matching roadmap US2 and US3 without adding unrelated stack features.

**Alternatives offered:**
- Create only: Smaller first change, but leaves the manual restack burden that the roadmap specifically calls out.
- Plan only: Records `gh-stack` command plans but does not execute them, reducing risk while postponing the main value.

**User's answer:** Create and restack

---

### Q5. How should PRSG-014 handle Claude Code and Codex parity for stack-manager behavior?

**Branch:** Runtime parity

**Recommended answer:** Shared scripts plus mirrored guidance
> Detection, emission, and restack logic should stay single-copy under the shared skill scripts. Both Claude Code and Codex guidance need matching operator behavior, and L8 fixtures should prove the parity contract.

**Alternatives offered:**
- Duplicate Codex scripts: Makes Codex behavior explicit but creates two implementations that can drift.
- Claude only: Smaller scope, but violates the roadmap's PRSG-001 through PRSG-014 parity expectation.

**User's answer:** Shared scripts plus mirrored guidance

---

## Open Questions

- **What:** Exact `gh-stack` command and version capability matrix for create/sync/restack operations.
  **Why deferred:** The installed extension behavior and dry-run semantics need codebase and CLI inspection during Plan.
  **Suggested next step:** Resolve in `/speckit-plan` research before implementation tasks are generated.
- **What:** Final schema field names for stack-manager evidence across emission and restack state.
  **Why deferred:** The plan should inspect existing emission/restack schemas and choose the smallest compatible extension.
  **Suggested next step:** Resolve in `/speckit-plan`; then validate with Layer 4 fake-CLI fixtures.

## Recommended Next Step

Run setup-produced workflow with:

```bash
$speckit-autopilot docs/ai/specs/.process/PRSG-014-workflow.md
```
