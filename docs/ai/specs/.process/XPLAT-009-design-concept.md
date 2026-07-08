---
topic: "XPLAT-009 Plugin Source and Payload Bash Eradication"
slug: "xplat-009-plugin-source-and-payload-bash-eradication"
date: "2026-07-07"
mode: "setup"
spec_id: "XPLAT-009"
source_input:
  type: "file"
  ref: "docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md"
question_count: 8
stop_reason: "natural"
---

# Design Concept: XPLAT-009 Plugin Source and Payload Bash Eradication

> **Source:** `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`
> **Date:** 2026-07-07
> **Questions asked:** 8
> **Stop reason:** natural

## Goals

- Remove every live `.sh` file from `speckit-pro/` after active behavior is ported
  into Python runner, helper, or gate paths.
- Keep one XPLAT-009 workflow, but plan two vertical, PR-ready slices.
- Slice 1 removes active plugin-source Bash behavior and active Bash-oriented
  source guidance.
- Slice 2 rebuilds Claude/Codex payloads, proves generated and installed-cache
  zero-Bash state, and adds or tightens no-shell/no-jq guards.
- Preserve the XPLAT-008 installed-runtime behavior: direct Python 3.11+
  `speckit_pro_runner` invocation, no Bash fallback, no `jq` runtime path, and
  no public native-platform overclaiming.
- Use integration, reliability, and security checklist focus areas.

## Non-goals

- Do not scaffold child specs for XPLAT-009 unless later Plan/Tasks evidence proves
  the accepted two-slice route cannot stay reviewable. See Q1 and Q7.
- Do not keep a live Bash fallback, wrapper, or staged deprecation path in source
  or generated payloads. See Q2 and Q4.
- Do not include repository-wide shell harness cleanup under `tests/**`,
  top-level `scripts/**`, hooks outside the plugin package, `.specify/**`, or
  GitHub Actions workflow dispatch glue. XPLAT-010 owns that. See Q4.
- Do not repeat full native Claude/Codex UAT. XPLAT-008 owns native operator UAT;
  XPLAT-009 only needs payload/cache zero-Bash proof. See Q6.
- Do not rewrite historical/archive prose solely to erase past Bash behavior.

## Design Tree (Q&A log)

### Q1. How should XPLAT-009 be scoped for scaffold?

**Branch:** Scope shape

**Recommended answer:** One workflow, slices
> The roadmap makes XPLAT-009 one dependency that unblocks XPLAT-010. One
> workflow with internal review slices keeps that dependency clear while still
> respecting the setup reviewability warning.

**Alternatives offered:**
- Split into child specs: Lowers per-PR size but adds coordination and may
  duplicate zero-Bash guard work.
- Single aggregate PR: Simplest setup, but higher reviewability risk given the
  setup gate warning.

**User's answer:** One workflow, slices

---

### Q2. What should happen to the remaining plugin Bash scripts as active behavior is migrated?

**Branch:** Porting strategy

**Recommended answer:** Port then remove
> The roadmap's done condition is zero `.sh` files under `speckit-pro/`, so
> wrappers around shell scripts would preserve the wrong substrate. Porting active
> behavior first keeps functionality reviewable before deletion.

**Alternatives offered:**
- Wrap with Python: Faster but fails the zero `.sh` source target.
- Delete unused only: Lower risk but leaves active Bash cleanup unfinished.

**User's answer:** Port then remove

---

### Q3. Which implementation order should the workflow prefer?

**Branch:** Slice ordering

**Recommended answer:** Active references first
> The highest user-facing risk is an active skill, agent, or gate still telling a
> maintainer to run Bash. Removing active references before raw file-count cleanup
> reduces live fallback risk earliest.

**Alternatives offered:**
- Largest helper family first: Reduces file count quickly but can defer active
  user-facing guidance fixes.
- Guards first: Strong TDD signal, but many guards will fail until ports and
  deletions catch up.

**User's answer:** Active references first

---

### Q4. Should any live Bash fallback remain after XPLAT-009?

**Branch:** Fallback policy

**Recommended answer:** No live fallback
> XPLAT-008 established installed-runtime Python runner behavior. XPLAT-009 should
> allow historical/archive evidence only, not a source or payload path that users
> can still treat as current guidance.

**Alternatives offered:**
- Temporary fallback: Safer short-term but conflicts with the zero-Bash
  plugin-source goal.
- Docs exception: Easier support wording, but risks public claims drifting from
  XPLAT-008.

**User's answer:** No live fallback

---

### Q5. What guard shape should XPLAT-009 add or tighten?

**Branch:** Guard design

**Recommended answer:** Python gates, allowlist
> Python-backed runner gates are reusable in release-readiness and CI. A narrow
> allowlist keeps historical/archive prose from blocking while still failing
> active source, generated payload, `.sh`, and `jq` regressions.

**Alternatives offered:**
- Simple scans only: Quicker, but less reusable and easier to bypass in
  release-readiness gates.
- Release gate only: Smaller surface, but misses fast feedback during normal
  repo validation.

**User's answer:** Python gates, allowlist

---

### Q6. How much payload and installed-cache proof should XPLAT-009 require?

**Branch:** Payload proof

**Recommended answer:** Rebuild plus cache proof
> The roadmap already says generated payloads are clean today, so the valuable
> proof is that the rebuilt payloads and an installed-cache artifact produced
> from them remain clean after source script removal. Full native UAT would
> duplicate XPLAT-008.

**Alternatives offered:**
- Generated payloads only: Faster but leaves the installed-cache claim less
  direct.
- Full native UAT: Strongest proof, but duplicates XPLAT-008 UAT and broadens
  scope.

**User's answer:** Rebuild plus cache proof

---

### Q7. How should XPLAT-009 handle the estimator warning?

**Branch:** Slice sizing

**Recommended answer:** Two vertical slices
> The advisory estimator returned `{"estimated_loc":527,"suggested_slices":2,"status":"warn"}`
> from three user stories, about twenty files/surfaces, twelve functional
> requirements, and modifying existing code. Two vertical slices match the
> estimator while avoiding child-spec overhead.

**Alternatives offered:**
- Three smaller slices: Easier reviews but more coordination.
- No planned split: Simpler but higher reviewability risk.

**User's answer:** Two vertical slices

---

### Q8. Which checklist focus should the workflow seed for XPLAT-009?

**Branch:** Checklist focus

**Recommended answer:** Integration, reliability, security
> Integration validates source, generated payload, installed-cache proof, and
> release gates as one runtime path. Reliability and security cover guard quality,
> unsafe fallback prevention, and public trust-claim drift.

**Alternatives offered:**
- Integration only: Narrower and faster, but may miss release-blocking safety
  and guard-quality gaps.
- Security heavy: Useful for trust claims, but less coverage of helper behavior
  and payload rebuild consistency.

**User's answer:** Integration, reliability, security

## Open Questions

- **What:** Exact Python operation names for each ported helper family.
  **Why deferred:** This depends on Plan reading the helper registry and existing
  runner modules.
  **Suggested next step:** Resolve during `$speckit-plan` and bind in `research.md`
  or `contracts/` if new runner request shapes are needed.
- **What:** Whether any historical/archive prose needs an explicit allowlist.
  **Why deferred:** The active-instruction scan should first classify real hits.
  **Suggested next step:** Resolve during Clarify or Plan with a documented
  allowlist that cannot satisfy release readiness.

## Recommended Next Step

Run setup continuation through `$speckit-scaffold-spec XPLAT-009`; in setup mode
this design concept feeds the generated workflow. After scaffold completes, run
`$speckit-autopilot` with `docs/ai/specs/.process/XPLAT-009-workflow.md`.
