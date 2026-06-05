# Feature Specification: Artifact relocation — tiering, .process/, collapse

**Feature Branch**: `007-artifact-relocation`

**Created**: 2026-06-05

**Status**: Draft

**Input**: User description: "Artifact relocation — tier spec artifacts into CONTRACT vs EXHAUST, redirect speckit-pro-authored exhaust into a `.process/` directory, collapse `.process/` out of the review diff via `linguist-generated`, and align the reviewability gate's LOC accounting — without deleting any artifact."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tier and redirect speckit-pro-authored exhaust (Priority: P1)

A reviewer opens a feature pull request produced by speckit-pro. Today, roughly a third of that diff is auto-generated process exhaust — the design-concept doc, the workflow file, and the UAT runbook — which buries the contract artifacts (spec, plan, tasks) and the code the reviewer actually needs to read. With this story shipped, every artifact speckit-pro writes is classified as either CONTRACT (review-visible, the reviewer's actual subject) or EXHAUST (the scaffolding that produced it), and the EXHAUST that speckit-pro itself authors is written into a `.process/` directory instead of alongside the contract artifacts. The design-concept doc and workflow file land under `docs/ai/specs/.process/`; the UAT runbook lands under the feature's own `specs/<NNN>/.process/`. No artifact is deleted — every file still exists on disk at its new location, so audit and provenance survive. Because speckit-pro ships for two coding agents, each prose change to a Claude skill is mirrored identically into its Codex counterpart so both agents redirect exhaust to the same place.

**Why this priority**: This is the source-side change that makes the entire feature possible. Without redirecting the authored exhaust into `.process/`, there is nothing for the collapse rule in User Story 2 to act on, and the review diff stays cluttered. It is independently valuable even before collapse ships: the exhaust is at least segregated into a clearly-named directory a reviewer can mentally skip.

**Independent Test**: Scaffold a brand-new spec and run a feature through to the point where the UAT runbook is generated; confirm the design-concept doc and workflow file are written under `docs/ai/specs/.process/`, the UAT runbook is written under `specs/<NNN>/.process/`, every redirected file still exists and is readable, the PR body still renders its UAT section from the relocated runbook, and the corresponding Codex skill redirects to the identical path.

**Acceptance Scenarios**:

1. **AC-1.1**: **Given** a reviewer needs to know which artifacts are review-visible, **When** they consult the artifact taxonomy this feature defines, **Then** every speckit-pro spec artifact is unambiguously classified as either CONTRACT (review-visible, never collapsed) or EXHAUST (relocated to `.process/`), with the contract set (spec, plan, tasks, and their supporting design artifacts) staying review-visible at its existing location.

2. **AC-1.2**: **Given** scaffold-spec runs for a new spec, **When** it writes the design-concept doc and the workflow file, **Then** both files are written under `docs/ai/specs/.process/` rather than directly in `docs/ai/specs/`, and both still exist and are readable after the run (no deletion).

3. **AC-1.3**: **Given** a feature run reaches UAT-runbook generation, **When** the runbook is written, **Then** it is written under the feature's own `specs/<NNN>/.process/` directory, it still exists and is readable, and the generated PR body still renders its UAT-runbook section from the relocated file (no broken reference).

4. **AC-1.4 (Codex parity)**: **Given** every prose edit that redirects exhaust in a Claude skill, **When** the change ships, **Then** the corresponding Codex skill variant carries the identical redirect so both coding agents write exhaust to the same `.process/` paths, with no Claude-only or Codex-only drift in the redirect targets.

---

### User Story 2 - Collapse, align the gate, and lint the collapse rule (Priority: P2)

A reviewer (in this plugin repo or in a consuming project) opens a feature PR and the relocated exhaust under `.process/` is collapsed out of the default review diff by construction — it is marked generated, so the platform hides it from the diff while keeping it fully diffable and loadable on demand. A maintainer who relies on the reviewability gate's line-of-code accounting sees the relocated exhaust drop out of the reviewable-LOC count, so the gate measures only what a reviewer actually reviews. The collapse reaches consuming projects, not just this plugin's own repository, because the collapse rule is written into the consuming project's own repository root as part of scaffolding a new spec. A guard test ensures the collapse rule can only ever target `.process/` and can never accidentally hide a CONTRACT artifact.

**Why this priority**: This is what actually removes the exhaust from the reviewer's diff and from the gate's accounting. It depends on User Story 1 having relocated the exhaust into `.process/` first, which is why it is P2. It is independently testable: given files already under `.process/`, the collapse rule, the gate alignment, and the lint can each be verified on their own.

**Independent Test**: In a repository that contains both a `.process/` file and a contract artifact with known line counts, confirm the gate counts only the contract lines as reviewable and excludes the `.process/` lines; confirm the collapse rule exists at the repository root and is scoped to `.process/`; confirm scaffolding a new spec writes the same collapse rule into a consuming project's repository root idempotently (running it twice does not duplicate the rule); and confirm the guard test fails if the collapse rule is ever broadened beyond `.process/`.

**Acceptance Scenarios**:

1. **AC-2.1 (collapse, diff-preserving)**: **Given** a feature PR whose diff includes files under a `.process/` directory, **When** a reviewer views the PR, **Then** those files are collapsed out of the default review diff as generated content while remaining fully diffable and loadable on demand (collapse only — never rendered non-diffable).

2. **AC-2.2 (gate alignment)**: **Given** the reviewability gate computes the reviewable line count for a change, **When** the change includes files under `.process/`, **Then** the gate excludes those `.process/` lines from the reviewable-LOC total while still counting CONTRACT-artifact lines, so the gate's accounting matches what is actually shown to a reviewer.

3. **AC-2.3 (reach into consuming projects)**: **Given** a new spec is scaffolded inside a consuming project, **When** scaffolding completes, **Then** the consuming project's own repository root carries the `.process/` collapse rule, and re-running the scaffold does not add a duplicate rule (idempotent).

4. **AC-2.4 (lint guards scope)**: **Given** an automated structural check of the collapse configuration, **When** the check runs, **Then** it passes only when every collapse rule is scoped to `.process/` and fails if any collapse rule is broadened to a path that could include a CONTRACT artifact.

---

### Edge Cases

- **A `.process/` directory does not yet exist when exhaust is first written.** The redirect must create the `.process/` directory as needed so the first design-concept doc, workflow file, or UAT runbook of a new spec lands in the right place rather than failing or falling back to the old location.
- **The collapse rule is present in the plugin repo but absent from a consuming project.** Because the platform reads each repository's own collapse configuration, a plugin-only rule would collapse only the plugin's own PRs. The consuming-project ensure-step closes this gap; if it is skipped, the consuming project's new-spec exhaust stays visible (a degraded but non-broken state).
- **The consumer `.gitattributes` write is interrupted partway.** The ensure-step's edit to the consumer `.gitattributes` MUST be safe under interruption: an interrupted run MUST NOT leave the file truncated, half-written, or otherwise corrupted (upholding FR-009 clause (c)). A subsequent re-run MUST be able to complete the edit idempotently and arrive at the same single-rule end state. Corruption also includes silently concatenating the new rule onto a pre-existing final line that lacks a trailing newline, so the write MUST normalize the trailing newline before appending. (The concrete safe-write mechanism was resolved during Checklist consensus — write to a same-directory temp file then atomic rename, with a fixed-string whole-line presence guard — and is pinned in plan.md; the requirement here remains the no-partial-file, no-concatenation outcome.)
- **The collapse rule and the gate's exclusion list disagree.** The two are intentionally maintained in two places (the repository-root collapse configuration and the gate's own exclusion logic). The lint exists specifically to catch drift between them so a reviewer is never shown something the gate counts, or vice versa.
- **A PR-body section references a relocated file.** Relocating the UAT runbook must not break the PR body's rendering of its UAT section; the reference is repointed to the new `.process/` location so the section still renders.
- **An existing (legacy) spec directory is present.** This feature is new-specs-only and must not touch or migrate any existing `specs/<NNN>/` directory; legacy relocation is owned by a separate, later spec.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST define an artifact taxonomy that classifies every speckit-pro-authored spec artifact as either CONTRACT (review-visible, never collapsed) or EXHAUST (relocated to `.process/`).
- **FR-002**: speckit-pro MUST write the design-concept doc and the workflow file it authors under `docs/ai/specs/.process/` instead of directly in `docs/ai/specs/`.
- **FR-003**: speckit-pro MUST write the UAT runbook it authors under the feature's own `specs/<NNN>/.process/` directory.
- **FR-004**: Relocating exhaust MUST preserve every relocated file (no deletion) so audit and provenance survive; each relocated artifact remains present and readable at its new `.process/` location.
- **FR-005**: The generated PR body MUST continue to render its UAT-runbook section after the runbook is relocated (the reference is repointed, not removed).
- **FR-006**: Every prose change that redirects exhaust in a Claude skill MUST be mirrored identically into its Codex counterpart so both coding agents redirect exhaust to the same `.process/` paths.
- **FR-007**: The repository MUST carry a repository-root collapse rule that marks `.process/` content as generated so it is collapsed out of the default review diff.
- **FR-008**: The collapse rule MUST mark `.process/` content as generated only (it MUST NOT render the content non-diffable); relocated artifacts stay diffable and loadable on demand.
- **FR-009**: Scaffolding a new spec inside a consuming project MUST write the same `.process/` collapse rule into the consuming project's own repository-root `.gitattributes`, and MUST do so idempotently (re-running it MUST NOT create a duplicate rule). Specifically: (a) when the consuming repo has no repository-root `.gitattributes`, the ensure-step MUST create the file containing the rule; (b) when the file already exists, the ensure-step MUST append the rule only if the rule is not already present, decided by an exact match on the rule line (whitespace- and trailing-newline-tolerant, so a rule already present with differing surrounding blank lines is recognized as present and NOT re-appended); and (c) the edit MUST be append-only — it MUST preserve every pre-existing line of the consumer `.gitattributes` byte-for-byte and MUST NOT truncate, rewrite, or reorder existing content. Both the create and append branches MUST converge on the same end state: the consumer `.gitattributes` contains exactly one copy of the `.process/` collapse rule.
- **FR-010**: The reviewability gate MUST exclude `.process/` content from its reviewable-LOC accounting while still counting CONTRACT-artifact content, so the gate's count matches what is shown to a reviewer. The exclusion MUST be confined to paths carrying the `/.process/` segment: a changed path with no `/.process/` segment MUST NOT be excluded (no false exclusion), and a change containing zero `.process/` paths MUST leave the reviewable-LOC count identical to its pre-feature value (the exclusion arm degrades to a no-op).
- **FR-011**: The gate's `.process/` exclusion MUST be self-contained (it MUST NOT depend on reading the repository-root collapse configuration); the resulting duplication between the gate and the collapse configuration is intentional and MUST be guarded against drift by an automated structural check.
- **FR-012**: An automated structural check (lint) MUST confirm every collapse rule is scoped to `.process/` and MUST fail if any collapse rule is broadened to a path that could include a CONTRACT artifact.
- **FR-013**: The feature MUST be new-specs-only: it MUST NOT migrate, move, or otherwise mutate any existing `specs/<NNN>/` directory. This non-mutation guarantee extends to the pre-existing documents that already live in the `docs/ai/specs/` tree the new scaffold exhaust now targets at `docs/ai/specs/.process/` — specifically the legacy `docs/ai/specs/SPEC-*-workflow.md` files and any other pre-existing non-`.process/` file in that tree (design-concept docs, the pipeline-verification runbook, the technical-roadmap files): none of them are moved, relocated into `.process/`, frontmatter-stamped, or otherwise rewritten by this feature. They remain review-visible at their current paths because the collapse glob and gate exclusion match the `/.process/` segment ONLY (a path they lack); any frontmatter-stamp or file move of legacy artifacts is owned by a separate, later retro-migration spec.
- **FR-014**: The redirect MUST create the `.process/` directory when it does not yet exist, so the first exhaust artifact of a new spec lands at the correct location.
- **FR-015**: The change MUST NOT regress the pre-existing test suite: the already-wired Layer-1 (structural, including the Codex parity validators), Layer-4 (script-unit), and Layer-5 (tool-scoping) checks MUST continue to pass after the change, in addition to the feature's own new checks. The feature's new Layer-1 lint MUST be added by EXTENDING the existing structural layer (registered alongside the existing validators) rather than replacing or renumbering any existing validator, and the two extended Layer-4 tests MUST be additive (new assertions appended; existing assertions preserved) so pre-existing gate and ensure-step coverage stays intact.

### Key Entities *(include if feature involves data)*

- **CONTRACT artifact**: A review-visible spec artifact a reviewer is expected to read. The CONTRACT set is: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `contracts/**`, `checklists/**`, `SPEC-MOC.md`, and `docs/ai/specs/*-technical-roadmap.md`. Never collapsed; never relocated by this feature; stays at its existing location. The `*-technical-roadmap.md` files are called out explicitly because they live in the SAME `docs/ai/specs/` tree as the relocated scaffold-time exhaust (`docs/ai/specs/.process/`); they stay safe from collapse precisely because the collapse glob and the gate exclusion match on the `/.process/` path segment ONLY, and a roadmap path carries no `/.process/` segment. No CONTRACT file is ever matched by the `.process/`-anchored rule.
- **EXHAUST artifact**: An auto-generated scaffolding artifact that documents how a contract artifact was produced (design-concept doc, workflow file, UAT runbook). Relocated into `.process/`, collapsed out of the review diff, and excluded from the gate's reviewable-LOC accounting — but never deleted.
- **`.process/` directory**: The relocation target for EXHAUST artifacts. Exists in two trees — `docs/ai/specs/.process/` (for scaffold-time exhaust) and `specs/<NNN>/.process/` (for per-feature exhaust). The single anchor that the collapse rule, the gate exclusion, and the lint all key on.
- **Collapse rule**: A repository-root configuration entry that marks `.process/` content as generated so the platform hides it from the default review diff while keeping it diffable. Mirrored into consuming projects' repository roots by the scaffold ensure-step.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a newly scaffolded feature, none of the three speckit-pro-authored exhaust artifacts (design-concept doc, workflow file, UAT runbook) appear in the default review diff of the feature PR — they are collapsed by construction.
- **SC-002**: 100% of the speckit-pro-authored exhaust artifacts that are relocated still exist and are readable at their new `.process/` location after a run (zero data loss).
- **SC-003**: The reviewability gate's reviewable-LOC count for a change excludes 100% of `.process/` lines while including 100% of CONTRACT-artifact lines, verified by a deterministic test that adds known line counts to both a `.process/` file and a contract artifact.
- **SC-004**: A consuming project that scaffolds a new spec receives the `.process/` collapse rule in its own repository root, and re-running the scaffold leaves exactly one copy of the rule (idempotency verified).
- **SC-005**: The collapse-scope lint fails whenever a collapse rule is broadened beyond `.process/` and passes when all collapse rules are scoped to `.process/`, verified by both a positive and a negative test case.
- **SC-006**: Every redirect prose edit in a Claude skill has an identical counterpart in its Codex variant, with zero drift in redirect targets between the two.
- **SC-007**: After the change, `bash speckit-pro/tests/run-all.sh` reports zero failures across the pre-existing Layer-1/4/5 checks, and the suite's passing count is greater than or equal to its pre-change baseline (every previously-passing check still passes; the new Layer-1 lint and the extended Layer-4 assertions add to the count rather than replacing existing checks).

## Out of Scope

- **Redirecting extension-authored exhaust** (for example, the retrospective report and the verify-tasks report). These files are written by external SpecKit extensions, not by speckit-pro's own prose or scripts, so this feature cannot redirect them via skill edits. They stay visible in the review window, and their POST-MERGE cleanup is owned by the installed `archive` extension (which distills a merged feature's substance into `.specify/memory/` and then performs gated, whole-directory removal). This feature does NOT wire a `git mv` sweep to chase them into `.process/` — that would duplicate the `archive` extension, and the roadmap already defers post-merge relocation to a later version.
- **Moving the CONTRACT set.** The spec, plan, tasks, and their supporting design artifacts stay review-visible at their existing location.
- **Migrating any legacy/existing spec.** This feature is new-specs-only; relocating the existing `specs/<NNN>/` directories is owned by a separate, later spec (retro-migration). This non-mutation boundary also covers the pre-existing non-`.process/` files already living in the `docs/ai/specs/` tree the new scaffold exhaust now targets — the legacy `docs/ai/specs/SPEC-*-workflow.md` files, design-concept docs, the pipeline-verification runbook, and the technical-roadmap files — none of which this feature moves, relocates into `.process/`, frontmatter-stamps, or rewrites (consistent with FR-013); any such legacy move is owned by the same later retro-migration spec.
- **Rendering artifacts non-diffable (`-diff`).** Collapse is generated-only; artifacts remain diffable and loadable on demand.
- **Map-of-content templates** and **gate threshold rework** — both are separate, later specs.

## Assumptions

- The hosting platform honors a repository-root collapse configuration that marks paths as generated and, by default, hides generated paths from the review diff while still allowing them to be loaded on demand. This is the mechanism that achieves collapse without deletion.
- The platform reads each repository's own collapse configuration, so a consuming project must carry its own copy of the rule for its PRs to collapse — hence the consuming-project ensure-step.
- The three exhaust artifacts in scope (design-concept doc, workflow file, UAT runbook) are authored by speckit-pro itself (its prose and its scripts), and are therefore within this feature's control to redirect; the out-of-scope extension-authored artifacts are not.
- The reviewable-LOC impact of relocation is confined to diff-mode markdown accounting; relocated exhaust is documentation, not a production source file, so production-file accounting is unaffected.
- Scripts in this repository are plain shell plus `jq`, with no new abstraction layer or single-call-site flag introduced (per the project constitution and contributing guidelines).
- The implementation effort is targeted at roughly 250 lines of production change as a planning target (not a hard ceiling); the consuming-project ensure-step and the UAT-runbook reference repoint add modestly to that.
- An existing `archive` extension is installed and owns post-merge cleanup of extension-authored exhaust, so this feature deliberately does not duplicate that responsibility.
