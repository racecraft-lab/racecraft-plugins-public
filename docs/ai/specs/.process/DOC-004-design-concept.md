---
topic: "Codex marketplace installation path"
slug: "doc-004-codex-marketplace-installation-path"
date: "2026-06-14"
mode: "setup"
spec_id: "DOC-004"
source_input:
  type: "file"
  ref: "docs/ai/specs/interactive-documentation-technical-roadmap.md"
question_count: 7
stop_reason: "natural"
---

# Design Concept: Codex Marketplace Installation Path

> **Source:** docs/ai/specs/interactive-documentation-technical-roadmap.md
> **Date:** 2026-06-14
> **Questions asked:** 7
> **Stop reason:** natural

## Goals

- Expand the existing Codex install route into one focused end-to-end page that covers install, update/remove orientation, custom-agent registration, restart, and verification (Q1).
- Present repo-scoped, personal, and CLI marketplace paths as separate install contexts, with `dist/codex/speckit-pro/` clearly identified as the generated install payload for personal/local plugin use (Q2).
- Include a practical custom-agent registration checklist with `@SpecKit Pro -> install`, `$install`, restart guidance, destination checks, and the expected TOML agent files (Q3).
- Keep Codex sandbox, approval, cache, and trust-boundary guidance bounded to install safety, with deeper troubleshooting, update, rollback, and full trust analysis deferred to DOC-008 (Q4).
- Refresh current official OpenAI Codex plugin, build-plugin, skills, subagents, and approvals/security docs before writing final command/path wording (Q5).
- Update README, `speckit-pro/README.md`, and the docs-site Codex page together so users do not see conflicting Codex install guidance across entry points (Q6).
- Require the full repo validation suite plus docs-site build/link checks and manual command-snippet review before the implementation PR is ready (Q7).
- Keep DOC-004 as one slice. The advisory size estimate was 260 reviewable LOC, 1 suggested slice, status `ok`.

## Non-goals

- Do not document Claude Code installation details beyond cross-linking to the Claude path where helpful; DOC-003 owns Claude content (roadmap, Q1).
- Do not change Codex manifests, generated payload behavior, installer behavior, or custom-agent templates as part of DOC-004 unless a direct docs contradiction exposes a small, necessary source correction (Q3, Q6).
- Do not build the full troubleshooting, update, rollback, cache-diagnosis, or security/trust model; DOC-008 owns that depth (Q4).
- Do not create multiple Codex install/reference pages in this slice; reference-library depth belongs to DOC-007 and troubleshooting depth belongs to DOC-008 (Q1, Q4).
- Do not execute marketplace installs, modify a user's Codex configuration from the docs site, or add a live doctor command (roadmap, Q4).

## Design Tree (Q&A log)

### Q1. How should DOC-004 structure the Codex install content in the existing docs site?

**Branch:** Documentation architecture

**Recommended answer:** One focused page
> The existing DOC-002 shell already created `docs-site/src/content/docs/install/codex.md`. Expanding that route keeps the slice task-first and avoids spreading install content across reference/troubleshooting pages before DOC-007 and DOC-008 exist.

**Alternatives offered:**
- Multiple Codex pages: Clearer long-term, but likely bloats this slice beyond the roadmap budget.
- Minimal shell only: Lower risk, but DOC-004 may not satisfy its end-to-end install outcome.

**User's answer:** One focused page (Recommended)

---

### Q2. How should the docs present repo-scoped, personal, and CLI marketplace install paths?

**Branch:** Install path model

**Recommended answer:** Separate path matrix
> The PRD and roadmap explicitly call out repo-scoped, personal, and CLI marketplace paths as a confusion point. A matrix lets the docs keep official Codex terminology, the repo marketplace file, and the generated payload warning distinct.

**Alternatives offered:**
- Repo path first only: Simpler, but leaves the known personal-path wording risk underexplained.
- Official docs first: Safer for platform terminology, but less task-first for Racecraft users.

**User's answer:** Separate path matrix (Recommended)

---

### Q3. What level of custom-agent registration detail belongs in DOC-004?

**Branch:** Custom-agent verification

**Recommended answer:** Checklist with files
> Codex skills and custom agents are separate runtime surfaces in this repo. A checklist gives users enough proof that the install skill copied TOML agents and that restart is required, without turning DOC-004 into a full internals reference.

**Alternatives offered:**
- Command only: Shorter, but does not explain why skills and custom agents are separate in Codex.
- Full internals: Useful, but likely belongs in reference/troubleshooting slices.

**User's answer:** Checklist with files (Recommended)

---

### Q4. How much sandbox, approval, cache, and trust-boundary detail should DOC-004 include?

**Branch:** Trust and safety scope

**Recommended answer:** Bounded warning
> DOC-004 must make install safe enough for a first-time Codex user, but DOC-008 owns the full security, cache, update, rollback, and troubleshooting model. Keeping this bounded protects the review surface and avoids duplicate future content.

**Alternatives offered:**
- Full trust model: Comprehensive, but overlaps DOC-008 and may oversize DOC-004.
- Defer trust entirely: Smaller, but weakens install safety for first-time Codex users.

**User's answer:** Bounded warning (Recommended)

---

### Q5. How should DOC-004 handle official Codex docs that may have changed since the PRD was written?

**Branch:** Source freshness

**Recommended answer:** Refresh before writing
> Codex plugin behavior and path wording are version-sensitive. The implementation should verify current official OpenAI Codex docs before finalizing marketplace, cache, skills, subagents, and approval terminology.

**Alternatives offered:**
- Use PRD snapshot: Faster, but risks stale Codex install/path wording.
- Leave as open question: Safest on accuracy, but DOC-004 would not be ready to implement.

**User's answer:** Refresh before writing (Recommended)

---

### Q6. Should DOC-004 update README/plugin README install wording, or keep implementation limited to the docs site unless a direct conflict blocks the page?

**Branch:** Source documentation scope

**Recommended answer:** Site first, fix conflicts
> This would keep the docs-site Codex page as the primary deliverable and patch README wording only when directly contradictory.

**Alternatives offered:**
- Update all docs now: Cleaner end state, but broader diff and more review surface.
- Docs site only: Narrowest scope, but may leave users with conflicting install guidance.

**User's answer:** Update all docs now

**Notes:** This answer broadens DOC-004 beyond the recommended narrow docs-site-first scope. The workflow should still keep the edits documentation-only and avoid manifest, installer, payload, or behavior changes.

---

### Q7. What validation should DOC-004 require before the implementation PR is considered ready?

**Branch:** Validation scope

**Recommended answer:** Docs build plus links
> A docs-site build, link checks, repo structural validation for changed plugin docs, and manual command review would normally be enough for a docs-first slice.

**Alternatives offered:**
- Docs build only: Faster, but weaker for command/link/path drift in install docs.
- Full repo suite: Strongest signal, but heavier than needed for a docs-first slice unless plugin surfaces change.

**User's answer:** Full repo suite

**Notes:** This answer sets a stricter validation bar than the recommendation. The workflow should include the full repo suite plus docs-site checks and manual Codex command-snippet review.

---

## Open Questions

- No deferred product decisions block setup.
- Implementation must still refresh current official OpenAI Codex docs before final command/path wording, especially personal marketplace path examples and cache terminology.

## Recommended Next Step

Continue setup by generating `docs/ai/specs/.process/DOC-004-workflow.md`, writing `specs/doc-004-codex-marketplace-installation-path/SPEC-MOC.md`, committing the scaffold artifacts, and then running `$speckit-autopilot docs/ai/specs/.process/DOC-004-workflow.md`.
