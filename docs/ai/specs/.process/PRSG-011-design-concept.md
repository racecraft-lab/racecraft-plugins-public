---
topic: "Retro-migration: version marker and state-keyed backfill/relocate"
slug: "prsg-011-retro-migration"
date: "2026-06-08"
mode: "setup"
spec_id: "PRSG-011"
source_input:
  type: "file"
  ref: "docs/ai/specs/pr-size-governance-technical-roadmap.md (### PRSG-011); docs/prd-pr-size-governance.md (section 3.11); docs/ai/specs/PRSG-001-design-concept.md Open Questions"
question_count: 11
stop_reason: "natural"
---

# Design Concept: Retro-migration: version marker and state-keyed backfill/relocate

> **Source:** PR-size governance roadmap PRSG-011, PRD section 3.11, and deferred PRSG-001 open questions
> **Date:** 2026-06-08
> **Questions asked:** 11
> **Stop reason:** natural

## Goals

- Add the backward/contract half for PR-size governance so existing projects do not remain split-brain after PRSG-001 through PRSG-010.
- Introduce a repo-level `.specify/structure-version.json` high-water marker and deterministic migration runner for Tier-1 repo edits plus Tier-0 navigation backfill.
- Add an on-demand Tier-2 relocate codemod that moves legacy PROCESS artifacts into `.process/` only when a frozen legacy spec is explicitly thawed.
- Preserve legacy exemption-by-absence: completed historical specs get navigability without mass stamping or file moves.
- Keep migration behavior deterministic, script-first, and covered by Layer 4 fixtures, with Layer 3 skill behavior and Layer 8 Codex parity for skill registration changes.
- Keep PRSG-011 as one spec, but order implementation as two internal vertical increments: Tier-1/Tier-0 migration first, then Tier-2 relocation and registration.

## Non-goals

- No history rewrite and no destructive cleanup of legacy artifacts outside the explicit Tier-2 allow-list.
- No migration of in-flight specs listed in `.specify/feature.json`; they are skipped in every tier with a clear frozen/in-flight reason.
- No frontmatter stamp during Tier-0; legacy specs remain exempt by marker-absence until Tier-2 thaw.
- No support for non-SpecKit/date-named legacy namespaces in v1.
- No auto-run of the relocate codemod from scaffold/autopilot; those flows only suggest the explicit dry-run/apply path.
- No split of PRSG-011 into separate roadmap specs unless implementation proves the one-spec budget unworkable.

## Design Tree (Q&A log)

### Q1. Should the PRD/roadmap's six recommended PRSG-011 defaults be treated as already accepted, so this interview focuses only on the remaining unresolved relocation/naming details?

**Branch:** Scope envelope

**Recommended answer:** Yes, lock those defaults.
> The PRD and roadmap already record those defaults as accepted catalog input. Treating them as locked keeps this setup pass focused on decisions that were explicitly deferred from PRSG-001 or that affect implementation contracts.

**Alternatives offered:**
- Re-walk each default: safer if the operator wants a fresh decision log, but adds setup time without new source uncertainty.
- Lock only obvious defaults: useful if any specific default feels weak, but no such weak default was identified.

**User's answer:** A — lock the six PRD/roadmap defaults.

---

### Q2. Which review-packet filename contract should PRSG-011 use for migration?

**Branch:** PROCESS artifact naming

**Recommended answer:** Canonicalize on `pr-review-packet.md`, but make the Tier-2 relocate codemod recognize both `pr-review-packet.md` and legacy `peer-review-*` files.
> The PRSG-011 roadmap already names `pr-review-packet.md`, while PRSG-001 used `peer-review-*` wording. Recognition should be broad enough for transitional files; emitted/canonical output should be singular.

**Alternatives offered:**
- Canonicalize on `peer-review-*` only: aligns with PRSG-001 wording, but conflicts with the PRSG-011 allow-list.
- Recognize only `pr-review-packet.md`: simpler, but risks missing historical files named from PRSG-001 language.

**User's answer:** A — canonicalize on `pr-review-packet.md` and recognize both names.

---

### Q3. What shape should PRSG-011 use for verification evidence during Tier-2 relocation?

**Branch:** PROCESS artifact naming

**Recommended answer:** Canonicalize on an `evidence/` directory, and migrate `verification-evidence.md` into `evidence/verification-evidence.md` when present.
> PRSG-011 already includes `evidence/` in the PROCESS allow-list. Normalizing the single-file case into the directory preserves current evidence while leaving room for multi-file verification output.

**Alternatives offered:**
- Canonicalize on `verification-evidence.md` only: simpler, but too narrow for future evidence artifacts.
- Recognize both without normalization: lowest immediate risk, but preserves split-brain layout.

**User's answer:** A — use `evidence/` and normalize the single file into it.

---

### Q4. Should PRSG-011's PROCESS relocation allow-list include legacy `design-concept.md` and `workflow.md` files?

**Branch:** PROCESS artifact allow-list

**Recommended answer:** Yes, include `design-concept.md`, `*-design-concept.md`, `workflow.md`, and `*-workflow.md` as PROCESS artifacts, while keeping current CONTRACT artifacts in place.
> PRSG-001 established design-concept and workflow files as EXHAUST for new specs. The retro-migration codemod should bring legacy scaffolds into that same `.process/` layout when Tier-2 is explicitly applied.

**Alternatives offered:**
- Leave legacy design concept and workflow files in place: mechanically safer, but keeps the old review-noise pattern.
- Include only exact names: smaller allow-list, but likely misses historical prefixed scaffold output.

**User's answer:** A — include exact and prefixed design concept/workflow names.

---

### Q5. Should PRSG-011 dogfood the Tier-2 relocation on this repo's own historical PRSG-001 scaffold artifacts as part of implementation validation?

**Branch:** Validation strategy

**Recommended answer:** Yes, but only through a deterministic fixture or dry-run/apply test case, not by moving historical repo docs during the feature PR.
> This proves the deferred PRSG-001 artifact cases without mixing product migration churn into the plugin implementation branch.

**Alternatives offered:**
- Move the real PRSG-001 historical files in this PR: stronger live proof, but unrelated doc churn.
- Skip dogfooding: smaller PR, but weaker coverage for the deferred artifact cases.

**User's answer:** A — dogfood in deterministic fixtures/tests, not by moving real historical docs.

---

### Q6. How should `migrate-structure.sh` handle dirty trees for `--dry-run` versus `--apply`?

**Branch:** Migration safety

**Recommended answer:** Allow `--dry-run` on a dirty tree when it only reads state and prints pending migrations; hard-fail `--apply` and Tier-2 relocation on any dirty tree before backup or mutation.
> Safe inspection should be available during diagnosis. Mutation still needs the same gated-safety posture as `speckit-upgrade` backup/restore and the archive-style dry-run/apply split.

**Alternatives offered:**
- Hard-fail both modes on dirty trees: strict, but less useful for debugging.
- Allow both and rely on backups: too weak for a `git mv` migration.

**User's answer:** A — dirty-tree dry-run is allowed; all mutation hard-fails when dirty.

---

### Q7. For Tier-0 navigation backfill, should PRSG-011 include archived/completed historical specs in the generated roadmap-MOC index?

**Branch:** Navigation backfill

**Recommended answer:** Yes, include completed/archived historical specs as index rows when they can be ID-normalized, but do not stamp or move their files.
> This realizes the roadmap's eager Tier-0 navigability while preserving the legacy exemption-by-absence safety model.

**Alternatives offered:**
- Include only active specs: leaves most legacy work invisible.
- Include every non-SpecKit artifact: likely creates noisy or incorrect join keys.

**User's answer:** A — include ID-normalizable completed/archived specs without stamping or moving them.

---

### Q8. How should PRSG-011 handle in-flight specs listed in `.specify/feature.json`?

**Branch:** Migration state classification

**Recommended answer:** Skip them in every migration tier and print a clear "frozen/in-flight" reason in dry-run output.
> The roadmap says in-flight specs are skipped in every tier. Dry-run output still needs to explain that result so operators do not mistake it for a missing migration.

**Alternatives offered:**
- Include them in Tier-0 index backfill only: better visibility, but violates the roadmap language.
- Prompt interactively per spec: unsuitable for deterministic scripts and CI tests.

**User's answer:** A — skip all in-flight specs in every tier and report why.

---

### Q9. How should PRSG-011 expose the Tier-2 relocate codemod from scaffold/autopilot?

**Branch:** Skill registration

**Recommended answer:** Register it as an explicit suggested next action when scaffold/autopilot detects a thawed legacy spec with relocatable PROCESS files; do not auto-run it.
> The codemod has backup, dirty-tree, dry-run, and apply semantics. Scaffold/autopilot should surface the action and leave execution to an operator-controlled command.

**Alternatives offered:**
- Auto-run dry-run and ask before apply: helpful, but creates HITL complexity inside flows that should remain deterministic.
- Auto-apply when clean: too risky for a `git mv` migration.

**User's answer:** A — suggest the explicit codemod path; never auto-run.

---

### Q10. What `structureVersion` should PRSG-011 write for the first repo-level migration marker?

**Branch:** Version marker model

**Recommended answer:** Use `1` for `.specify/structure-version.json` and SPEC-MOC stamps, matching the existing MOC gate literal. Treat later structural migrations as `2+`.
> The repo already carries `structureVersion: 1` in the MOC templates and lints. Using `1` for the first repo-level migration aligns the marker with the existing v1 structure contract.

**Alternatives offered:**
- Use `2`, reserving `1` for MOC-only gating: clean separation, but confusing because both versions would be current.
- Defer exact number to implementation: flexible, but weakens fixtures and prompts.

**User's answer:** A — use `structureVersion` 1 for the first marker and stamps.

---

### Q11. Should PRSG-011 stay one spec or split into two specs before autopilot?

**Branch:** Slice sizing

**Recommended answer:** Keep PRSG-011 as one spec, but require Tasks to order it as two internal vertical increments: first Tier-1/Tier-0 `migrate-structure.sh`, then Tier-2 `relocate-process-artifacts.sh` plus scaffold/autopilot registration.
> The advisory estimator returned `{"estimated_loc":440,"suggested_slices":2,"status":"warn"}`. That is slightly over the 400 LOC target but below the block threshold, and the roadmap treats marker/backfill/relocate as one migration feature.

**Alternatives offered:**
- Split into PRSG-011A and PRSG-011B: smaller PRs, but introduces roadmap churn and a partially delivered migration surface.
- Convert PRSG-011 into a research spike: unnecessary because the roadmap and Q&A already resolve the major shape.

**User's answer:** A — keep one spec with two ordered internal vertical increments.

## Open Questions

- **What:** Exact CLI surface for invoking the migration scripts from `speckit-upgrade` and from operator-facing instructions.
  **Why deferred:** This is an implementation detail that depends on current `speckit-upgrade` skill structure and script layout.
  **Suggested next step:** Resolve during Specify/Plan and keep the behavior deterministic: dry-run prints pending migrations, apply mutates only after backup and clean-tree checks.

- **What:** Exact ID-normalization helper interface shared by `migrate-structure.sh`, `relocate-process-artifacts.sh`, and `generate-spec-index.sh`.
  **Why deferred:** The existing MOC/index scripts need a source pass before choosing function boundaries.
  **Suggested next step:** During Plan, inspect `speckit-pro/skills/speckit-autopilot/scripts/lib/moc-frontmatter.sh`, `generate-spec-index.sh`, and Layer 4 ID fixtures before naming the helper.

## Recommended Next Step

Run setup through completion, then run `$speckit-autopilot docs/ai/specs/.process/PRSG-011-workflow.md`.
