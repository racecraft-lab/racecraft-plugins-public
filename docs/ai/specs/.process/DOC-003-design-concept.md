---
topic: "Claude Code marketplace installation path"
slug: "doc-003-claude-code-marketplace-installation-path"
date: "2026-06-14"
mode: "setup"
spec_id: "DOC-003"
source_input:
  type: "topic"
  ref: "DOC-003 roadmap entry in docs/ai/specs/interactive-documentation-technical-roadmap.md"
question_count: 9
stop_reason: "natural"
---

# Design Concept: Claude Code Marketplace Installation Path

> **Source:** DOC-003 roadmap entry in `docs/ai/specs/interactive-documentation-technical-roadmap.md`
> **Date:** 2026-06-14
> **Questions asked:** 9
> **Stop reason:** natural

## Goals

- Make `docs-site/src/content/docs/install/claude-code.md` the canonical Claude Code install route for SpecKit Pro.
- Cover the full Claude Code install lifecycle: add marketplace, install, reload plugins, verify, update, uninstall, marketplace removal, and reinstall checks.
- Consolidate user-facing wording around Claude Code plugin **skills** rather than deprecated command-folder language.
- Use both official Claude Code plugin docs and this repository's source/generated payload files as install authority.
- Include a deeper Claude-specific trust section covering marketplace trust, skills, agents, hooks, MCP/settings, generated payloads, and managed marketplace considerations.
- Keep DOC-003 as one vertical slice: docs page, terminology consistency, verification, and trust detail.

## Non-goals

- Codex install instructions beyond a cross-link to the Codex install route - answered in Q5.
- Full troubleshooting matrix, rollback playbook, and every failure mode - answered in Q3.
- Side-by-side Claude and Codex command comparison - answered in Q5.
- Plugin behavior changes, generated payload regeneration, version bumps, or install runtime changes.

## Design Tree (Q&A log)

### Q1. For DOC-003, what should be the primary deliverable?

**Branch:** Deliverable shape

**Recommended answer:** Full route page
> Build the Claude install docs page as the canonical user path, with README changes only when needed for consistency. This matches DOC-002's route shell and keeps the docs-site install route as the user-facing surface.

**Alternatives offered:**
- README first: Make README and `speckit-pro/README.md` the canonical install guide, then point the docs site at them.
- Both equally: Update the docs page and README surfaces in the same depth, increasing the review surface.

**User's answer:** Full route page.

---

### Q2. How should DOC-003 handle legacy or inconsistent README/AGENTS wording about command folders and plugin surfaces?

**Branch:** Terminology consistency

**Recommended answer:** Patch blockers
> Fix only wording that would mislead Claude install users, and leave broader source cleanup to later reference or hygiene work. This keeps the first pass focused on install accuracy.

**Alternatives offered:**
- Flag only: Document the inconsistency in the Claude install page but do not touch README or AGENTS in this PR.
- Rewrite broadly: Normalize README, AGENTS, and docs-site wording together, but expand the review surface.

**User's answer:** Rewrite broadly, with the clarification that everything needs to consolidate on consistent use of skills rather than commands because commands have been deprecated.

**Notes:** This decision expands DOC-003's terminology work beyond the minimum patch-blockers recommendation.

---

### Q3. Which Claude Code lifecycle steps should DOC-003 cover in the first implementation?

**Branch:** Install lifecycle coverage

**Recommended answer:** Install-update-remove
> Document add marketplace, install, verify, update, uninstall, marketplace removal, and reinstall checks without building the full troubleshooting matrix. This maps directly to the roadmap's install/update/remove outcome while preserving DOC-008 for deep troubleshooting.

**Alternatives offered:**
- Install only: Keep the page focused on first install and verification, deferring update and removal to DOC-008.
- Full operations: Include install, update, remove, rollback, cache behavior, and detailed failure modes, increasing overlap with DOC-008.

**User's answer:** Install-update-remove.

---

### Q4. What should the Claude Code install guide use as the main success check after install?

**Branch:** Verification path

**Recommended answer:** Run status
> Use `/speckit-pro:speckit-status` as the concrete namespaced skill check because it is low-risk and proves routing works.

**Alternatives offered:**
- Open plugin UI: Use `/plugin` marketplace UI inspection as the main check, avoiding running a SpecKit skill.
- Run coach: Use `/speckit-pro:speckit-coach` as the check, which is helpful but less deterministic for install verification.

**User's answer:** Cover all three checks.

**Notes:** The implementation should verify plugin UI visibility, a namespaced status skill, and a coach-oriented sanity check.

---

### Q5. How should the Claude Code page handle Codex-specific install details?

**Branch:** Platform separation

**Recommended answer:** Cross-link only
> Mention Codex only as a separate path and link to the Codex install page, preventing command leakage.

**Alternatives offered:**
- Warn clearly: Include a short wrong-path warning that Codex uses `$skill-name` and custom-agent setup, then link away.
- Compare both: Show Claude and Codex commands side by side, useful but likely duplicative with DOC-004 and reference pages.

**User's answer:** Cross-link only.

---

### Q6. Which files should DOC-003 treat as source evidence for Claude Code install behavior?

**Branch:** Source authority

**Recommended answer:** Source plus dist
> Cite authoring files and generated `dist/claude` payloads so users can see both maintained source and installed shape.

**Alternatives offered:**
- Source only: Use `speckit-pro/` and marketplace JSON as the truth, avoiding generated payload references.
- Dist only: Document only what Claude Code installs, but make maintainer source paths harder to trace.

**User's answer:** Source plus dist.

---

### Q7. How much trust/security detail should DOC-003 include about agents, hooks, MCP/settings, and managed marketplaces?

**Branch:** Trust depth

**Recommended answer:** Concise trust box
> Add a short pre-install trust checklist and link deeper topics to security/reference pages owned by later DOCs.

**Alternatives offered:**
- Minimal note: Only mention that hooks and agents exist, leaving trust and managed marketplace detail to DOC-008.
- Deep section: Explain hooks, agents, MCP/settings, managed marketplaces, and rollback in detail, expanding beyond DOC-003.

**User's answer:** Deep section.

**Notes:** The implementation should include deep Claude-specific trust context, but avoid turning this into the full DOC-008 troubleshooting and rollback matrix.

---

### Q8. Given the DOC-003 estimate is one slice, should this stay as one vertical implementation spec?

**Branch:** Slice sizing

**Recommended answer:** One slice
> Keep DOC-003 as one Claude install path slice covering docs page, terminology consistency, verification, and trust detail.

**Alternatives offered:**
- Split trust out: Move the deeper trust/security material to a follow-up slice to reduce DOC-003 scope.
- Split README out: Keep the docs page in DOC-003 and move README/AGENTS terminology consolidation to a separate hygiene slice.

**User's answer:** One slice.

**Notes:** Advisory estimator input: 5 user stories, 6 files/surfaces, 5 functional requirements, modify existing docs. Output: `{"estimated_loc":220,"suggested_slices":1,"status":"ok"}`.

---

### Q9. How should the DOC-003 page cite install authority for Claude Code behavior?

**Branch:** Citation policy

**Recommended answer:** Official plus repo
> Use official Claude Code docs for platform behavior and repo files for this marketplace/plugin's exact paths. This keeps platform behavior current while grounding SpecKit Pro details in repository truth.

**Alternatives offered:**
- Repo only: Cite only repository files, reducing external dependency but weakening platform accuracy.
- Official only: Cite only official Claude docs, which misses this plugin's specific manifest and payload details.

**User's answer:** Official plus repo.

## Open Questions

- **What:** Exact final placement of the deep trust section within the Claude install page.
  **Why deferred:** This is a content-architecture detail best resolved while editing the page around the existing DOC-002 shell.
  **Suggested next step:** In implementation, place trust guidance before install commands if it affects user consent, or after verification if it reads better as reference.
- **What:** Whether every README/AGENTS terminology issue can fit cleanly in DOC-003.
  **Why deferred:** The user chose broad consolidation, but implementation should still avoid unrelated rewrites.
  **Suggested next step:** Patch all install-relevant command-to-skill wording and leave any unrelated repository-maintainer wording for DOC-007 or docs hygiene.

## Recommended Next Step

Continue `$speckit-scaffold-spec DOC-003`: generate the workflow file from this design concept, write the `SPEC-MOC.md` marker, mark DOC-003 in progress on the worktree branch, then run `$speckit-autopilot docs/ai/specs/.process/DOC-003-workflow.md`.
