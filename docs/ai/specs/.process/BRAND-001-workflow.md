# SpecKit Workflow: BRAND-001 — Brand brief and concept exploration

**Template Version**: 1.0.0
**Created**: 2026-07-16
**Purpose**: Autopilot-ready workflow for defining the Racecraft identity brief
and producing four comparable original SVG concept families without selecting a winner.

---

## Design Concept

This workflow was enriched from the required Grill Me interview. The complete
decision log, goals, non-goals, concept territories, rubric, and open questions are in:

```text
docs/ai/specs/.process/BRAND-001-design-concept.md
```

Treat that file as the scoping source of truth. In particular, preserve these decisions:

1. Evolve recognizable Racecraft cues instead of starting from zero or tracing
   the current mark.
2. Lead with abstract precision-system geometry rather than literal motorsport
   or generic developer-tool imagery.
3. Use shared geometry and neutrals with Racecraft crimson and SpecKit Pro
   indigo accents; every concept must also work in monochrome.
4. Require `SpecKit Pro by Racecraft` on first-touch lockups while allowing a
   compact product mark in constrained contexts.
5. Build from the existing self-hosted type system with limited custom details
   and an explicit license/path-conversion record.
6. Optimize for confident precision and small-size clarity.
7. Stop BRAND-001 after four comparable concept families. BRAND-002 owns blind
   critique and human selection; BRAND-003 owns canonical master production.
8. Design first for hands-on founders, technical leads, and staff engineers
   standardizing serious agentic software delivery.
9. Anchor the identity in the promise: turn product intent into reviewable,
   reliable agent execution across Claude Code and Codex.

Grill Me is human-in-the-loop setup, not an autopilot phase. Once execution
starts, use `/speckit-clarify` and the normal consensus protocol for any remaining
ambiguity. Do not rerun the interview inside autopilot.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|---|---|---|---|
| Specify | `/speckit-specify` | ⏳ Pending | Define the brief and four-family comparison contract |
| Clarify | `/speckit-clarify` | ⏳ Pending | Resolve asset-audit, geometry, and provenance details only |
| Plan | `/speckit-plan` | ⏳ Pending | Declare files, creation roles, rendering evidence, and review order |
| Checklist | `/speckit-checklist` | ⏳ Pending | Brand quality, accessibility, and LLM-assisted creation |
| Tasks | `/speckit-tasks` | ⏳ Pending | One independently reviewable concept-exploration slice |
| Analyze | `/speckit-analyze` | ⏳ Pending | Prove scope, traceability, and role separation |
| Implement | `/speckit-implement` | ⏳ Pending | Create brief, concepts, previews, and rationale packet |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates

| Gate | Checkpoint | Approval criteria |
|---|---|---|
| G1 | After Specify | AC-1.1 through AC-1.3 are measurable; no clarification markers remain |
| G2 | After Clarify | Existing-asset cues, family-sheet contract, and provenance rules are explicit |
| G3 | After Plan | Declared files fit the budget; author and conformance-review inputs are separated |
| G4 | After Checklist | Every genuine gap is remediated or explicitly out of scope |
| G5 | After Tasks | Brief, four families, comparisons, rationales, and handoff evidence are covered |
| G6 | After Analyze | No CRITICAL/HIGH drift; no task selects or canonizes a family |
| G7 | After Implementation | All four families render in every required context and the handoff packet is complete |

---

## Prerequisites

### Worktree and branch

- Repository root: `/Users/fredrickgabelmann/Documents/Business_Documents/RSE_Documents/Projects/racecraft-plugins-public/.worktrees/brand-001-racecraft-identity-system`
- Branch: `brand-001-racecraft-identity-system`
- Starting commit: `1df48912`
- No repository-specific dependency bootstrap was documented for this planning
  slice; do not infer a package install.
- Codex agent preflight completed with `status: ok`, `mutation_status: no_op`,
  and all ten installed agent definitions current.

Before every phase, verify the active root and branch. Fail closed if the workflow
is launched from another checkout.

### Preset resolution

The following commands resolved successfully to the repository's
`speckit-pro-reviewability` preset v1.0.0:

```text
specify preset resolve spec-template
specify preset resolve plan-template
specify preset resolve tasks-template
```

The generated spec, plan, and tasks must retain their Reviewability Budget and
PR Packet sections.

### Constitution validation

| Principle | BRAND-001 requirement | Verification |
|---|---|---|
| I. Plugin Structure Compliance | Do not edit plugin or generated-payload structure in this spec | Declared-file review and `git diff --name-only` |
| II. Cross-Platform Runtime & Script Safety | Add no Bash or runtime tooling; SVGs have no external runtime dependency | Declared-file review and SVG source inspection |
| III. Semantic Versioning | Make no manifest, marketplace, tag, changelog, or release-version edits | Version-bearing diff scan |
| IV. Test Coverage Before Merge | Use requirements checks plus render evidence appropriate to visual assets | Checklist evidence and required-context render inventory |
| V. Conventional Commits | Use a scoped conventional commit and PR title | Git history and PR-title check |
| VI. KISS, Simplicity & YAGNI | Four clear concepts, one comparison system, no premature export pipeline | Plan and code/artifact review |

**Constitution Check:** pending at G1; the scaffold introduces only planning
artifacts and the implementation scope explicitly excludes plugin/runtime/version changes.

### Reviewability budget

The original combined identity scope produced an advisory estimate of 950 and
three suggested slices. The user chose three roadmap specs:

- BRAND-001 — brief and concept exploration.
- BRAND-002 — rationale-blind critique and human selection.
- BRAND-003 — canonical master production.

The revised BRAND-001 signal is one user story, eight core authored files, and
three functional requirements. The estimator returned `estimated_loc: 390`,
`suggested_slices: 1`, `status: ok`.

| Metric | BRAND-001 budget |
|---|---:|
| Projected reviewable production LOC | 0 |
| Projected production files | 0 |
| Core BRAND-001 implementation files | 8 |
| Projected total branch files | 23-25 including scaffold and generated workflow artifacts |
| Primary surfaces | `docs/process`, `visual/assets` |
| Exception | None |

The setup gate over the full seven-spec roadmap returned a non-blocking warning
because the roadmap intentionally describes four downstream surfaces. It returned
no blockers. BRAND-001 itself is expected to warn because its committed scaffold
and visual assets span two surfaces, but it must remain at or below the 25-file
block threshold without an exception.

---

## Specification Context

### Basic information

| Field | Value |
|---|---|
| Spec ID | BRAND-001 |
| Name | Brand brief and concept exploration |
| Branch | `brand-001-racecraft-identity-system` |
| Dependencies | None |
| Enables | BRAND-002 |
| Priority | P1 |
| Parent roadmap | `docs/ai/specs/racecraft-identity-system-technical-roadmap.md` |
| Design Concept | `docs/ai/specs/.process/BRAND-001-design-concept.md` |
| Feature directory | `specs/brand-001-racecraft-identity-system/` |

### Success criteria summary

- [ ] `brand/brief.md` defines audience, promise, architecture, personality,
  approved direction, prohibited motifs, type/color strategy, required contexts,
  originality rules, minimum sizes, and the weighted rubric.
- [ ] Four structurally distinct, original SVG family sheets exist as editable
  geometry rather than raster traces or font-dependent source.
- [ ] Each family shows Racecraft, Racecraft Plugins, and SpecKit Pro by
  Racecraft directions in identical light, dark, monochrome, 16/24/32 px,
  README, docs-header, and plugin-list frames.
- [ ] Each family has a section in the private author-rationale record containing
  provenance and a candid known weakness; this file is excluded from the
  BRAND-002 allowed-input manifest.
- [ ] The comparison inventory is complete and neutral; no file, prose, score,
  or ordering declares a winner.
- [ ] No plugin, docs-site, generated payload, release, or version file changes.

### Artifact contract

The plan may refine names, but it must preserve this bounded shape:

```text
brand/
├── README.md
├── brief.md
├── concepts/
│   ├── family-01-apex-gate.svg
│   ├── family-02-tuned-trajectory.svg
│   ├── family-03-modular-standard.svg
│   ├── family-04-shared-negative-space.svg
│   └── comparison-board.svg
└── review/
    └── author-rationales.md
```

`brand/README.md` is the neutral handoff manifest. It lists and hashes the brief,
four family SVGs, and comparison board as the only allowed BRAND-002 critic
inputs; it explicitly excludes `brand/review/author-rationales.md`.

Before G3, count every scaffold, generated SpecKit, evidence, and brand file in
the projected branch diff. If it exceeds 25, consolidate optional artifacts or
surface the blocker. Do not add a typed exception merely to preserve exports.

### Role and information boundaries

- **Concept author:** receives the brief and Design Concept; creates all four
  families and the private rationale record.
- **Conformance reviewer:** receives the brief and rendered family sheets;
  verifies completeness, SVG editability, equal contexts, and prohibited motifs.
  This role does not score preference or receive the private rationale record.
- **Human selector:** does not act in BRAND-001. Selection is a required gate in
  BRAND-002 after a separate rationale-blind critique.

Agent contexts share a filesystem, so prompt separation alone is insufficient.
For conformance review, pass only the allowed-input manifest contents into the
review context and record the manifest hashes. BRAND-002 must create a clean
critic snapshot from those exact hashed inputs before preference scoring. Never
pass or reference `brand/review/author-rationales.md` in either reviewer prompt.

---

## Phase 1: Specify

**When to run:** Start here. Define what the identity packet must communicate and
what evidence makes the four families comparable. Output:
`specs/brand-001-racecraft-identity-system/spec.md`.

### Specify prompt

```text
/speckit-specify

## Feature: BRAND-001 — Brand brief and concept exploration

### Problem statement
Racecraft's public repository, documentation, and SpecKit Pro product currently
lack one coherent identity. Existing marks, names, and colors drift, and there is
no SpecKit Pro-specific mark. Before any integration work, the project needs an
approved brief and four original, structurally different SVG concept families
that can be evaluated fairly without author-rationale bias.

### Primary user story
As a hands-on founder, technical lead, or staff engineer standardizing serious
agentic delivery, I can recognize Racecraft as the system that turns product
intent into reviewable, reliable agent execution across Claude Code and Codex.
As the launch decision-maker, I can compare four genuinely different identity
families in identical contexts without accidental preference cues.

### Functional requirements
1. Define the complete one-page brief and weighted evaluation rubric.
2. Create four structurally distinct concept families matching the four Design
   Concept territories, each covering parent, repository/docs, product, and
   first-touch endorsement relationships.
3. Provide equal light/dark/monochrome, 16/24/32 px, README, docs-header, and
   plugin-list comparison evidence plus separated rationale/provenance records.

### Settled design constraints
- Evolutionary continuity; do not trace the legacy mark.
- Abstract precision-system metaphor; prohibit literal racing and generic code clichés.
- Racecraft crimson and SpecKit Pro indigo accents with shared neutrals/geometry.
- Monochrome family resemblance is mandatory.
- First-touch `SpecKit Pro by Racecraft`; compact standalone mark allowed when constrained.
- Existing self-hosted type with limited custom details and recorded licensing.
- Confident precision at small sizes.

### Out of scope
- Blind critique, scoring, selection, or winner language (BRAND-002).
- Canonical source-master refinement (BRAND-003).
- SVG sanitization/export pipeline (BRAND-004).
- README/docs/plugin integration (BRAND-005/006).
- Release/version changes (BRAND-007).
- Final trademark clearance.

Re-read docs/ai/specs/.process/BRAND-001-design-concept.md and preserve every
settled decision. Express requirements as measurable outcomes, not a prescribed
final silhouette.
```

### Specify results

| Metric | Expected at G1 |
|---|---|
| Functional requirements | Three or more, fully traceable to AC-1.1 through AC-1.3 |
| User stories | One independently testable P1 story; add another only for a distinct user outcome |
| Acceptance scenarios | Brief completeness, four-family structural difference, comparison parity, rationale isolation |
| Clarification markers | Zero before G1 passes |

### Files generated

- [ ] `specs/brand-001-racecraft-identity-system/spec.md`
- [ ] `specs/brand-001-racecraft-identity-system/checklists/requirements.md`

---

## Phase 2: Clarify

**When to run:** Only after `spec.md` exists. Do not reopen settled Grill Me
decisions. Resolve implementation-relevant ambiguity in at most five questions
per session.

### Session 1 — Legacy cues and brief precision

```text
/speckit-clarify Focus on the current-asset audit and brief: identify exactly
which existing color, proportion, or motion cues count as continuity; define how
the brief prevents tracing; make prohibited motifs and the weighted rubric
objective enough that a separate critic can apply them consistently.
```

### Session 2 — Family-sheet and comparison parity

```text
/speckit-clarify Focus on the four-family artifact contract: define what makes
the silhouettes structurally different rather than styling variants; set equal
viewBox/frame, light/dark/monochrome, 16/24/32 px, README, docs-header, and
plugin-list comparison rules; define how compact and endorsed product lockups
appear without selecting a winner.
```

### Session 3 — Provenance, typography, and information separation

```text
/speckit-clarify Focus on provenance and role isolation: define acceptable
inspiration logging, prohibited tracing, font/license evidence, path-conversion
expectations, the combined author-rationale record, the exact hashed allowed-input
manifest, and the conformance reviewer's no-rationale/no-preference boundary.
```

### Clarify results

Record the actual questions and consensus outcomes in the generated spec. G2
passes only when the asset contract, provenance record, and role boundary can be
implemented without inventing a selection criterion later.

---

## Phase 3: Plan

**When to run:** After G2. Output the implementation blueprint and complete the
reviewability sections from the active preset.

### Plan prompt

```text
/speckit-plan

## Source format and repository constraints
- SVG source: editable XML with stable viewBox values and explicit vector geometry.
- No scripts, event handlers, DTDs, foreignObject, animation, external URLs,
  embedded raster images, or remote fonts in concept source.
- Do not add a production SVG validator or export pipeline; BRAND-004 owns it.
- Do not depend on installed fonts for the family sheets. Record source font and
  license, then outline any customized display geometry used in SVG.
- Keep all work under brand/ plus the generated specs/brand-001-* artifacts.

## Creative-production approach
- Use AI visual generation only as ideation support; final concept sources must
  be intentional, editable SVG geometry with documented provenance.
- Use one isolated author context for all four families so the shared brand
  architecture stays coherent while the structures remain distinct.
- Use a separate conformance-review context containing only the hashed allowed
  inputs from brand/README.md. It verifies completeness and parity, not preference.
- Preserve one known weakness per family for the later independent critic.

## Evidence and review order
1. Read brand/brief.md.
2. Review the four family SVGs in neutral numeric order.
3. Review comparison-board.svg for equal contexts and small-size behavior.
4. Verify the brand/README.md allowed-input manifest and hashes.
5. Review author-rationales.md last; never use it in BRAND-001 conformance review.

## Reviewability
- Declare every NEW/MODIFIED file in the plan.
- Target exactly eight core brand implementation files, zero production files,
  zero production LOC, and no more than 25 total branch files.
- If the projected branch diff exceeds 25 files, consolidate optional generated
  artifacts or stop for re-slicing.
- No reviewability exception is authorized.

## Verification
- Parse every SVG as XML.
- Confirm stable viewBox, no prohibited/external constructs, and no raster trace.
- Render every family in each required comparison frame and inspect at 16/24/32 px.
- Confirm monochrome relationship does not rely on crimson/indigo alone.
- Confirm the private rationale file is absent from the allowed-input manifest
  and verify every manifest hash.
- Confirm the git diff contains no docs-site, plugin, generated payload, or version file.
```

### Plan results

| Artifact | G3 expectation |
|---|---|
| `plan.md` | Complete technical context, role separation, file declarations, review order, and budget |
| `research.md` | Current-asset inventory, type/license evidence, SVG authoring decisions, originality references |
| `data-model.md` | Optional; use only if it clarifies Family, Variant, Context Frame, and Provenance Record |
| `contracts/` | Optional; use only for a compact concept-packet schema that reduces ambiguity |
| `quickstart.md` | Exact commands/steps for rendering and inspecting the four-family packet |

---

## Phase 4: Domain Checklists

Run three enriched requirements checklists after `spec.md` and `plan.md` exist.
These check requirement quality, not the artwork itself.

### 1. Brand-quality checklist

```text
/speckit-checklist brand-quality

Focus on BRAND-001 requirements:
- Is the parent/repository/product hierarchy explicit in every required family?
- Is structural distinctness defined independently from color and surface styling?
- Are prohibited motifs, originality risk, and the weighted rubric measurable?
- Are the identical comparison frames and neutral ordering fully specified?
- Pay special attention to preventing winner language or selection work from
  leaking into BRAND-001.
```

### 2. Accessibility checklist

```text
/speckit-checklist accessibility

Focus on BRAND-001 visual requirements:
- Are light, dark, and monochrome behavior requirements explicit?
- Are the 16 px, 24 px, and 32 px inspection conditions defined consistently?
- Are contrast, legibility, silhouette integrity, and non-color family cues measurable?
- Are alt text or accessible descriptions required for comparison evidence?
- Pay special attention to small-size marks and product endorsement readability.
```

### 3. LLM-integration checklist

```text
/speckit-checklist llm-integration

Focus on AI-assisted BRAND-001 creation:
- Are author and conformance-review prompts, inputs, and prohibited context explicit?
- Does the hashed allowed-input manifest exclude the private rationale record?
- Are provenance, originality, and human-review limits stated without claiming clearance?
- Are unexpected low-quality, derivative, or non-editable outputs rejected by measurable rules?
- Pay special attention to keeping AI ideation subordinate to editable SVG source and human gates.
```

### Checklist results

| Checklist | Status before G4 | Required resolution |
|---|---|---|
| brand-quality | Pending | Remediate every genuine gap in spec or plan |
| accessibility | Pending | Remediate every genuine gap in spec or plan |
| llm-integration | Pending | Remediate every genuine gap in spec or plan |

At least 80% of checklist items must carry a spec traceability marker. Document
intentional non-goals instead of silently marking them satisfied.

---

## Phase 5: Tasks

**When to run:** After all G4 gaps are resolved.

### Tasks prompt

```text
/speckit-tasks

## Task structure
- Small, independently verifiable tasks with FR and user-story references.
- Declare exact file paths and NEW/MODIFIED status.
- Mark parallel-safe work [P] only when it cannot cause geometry or style drift.
- Keep conformance review limited to the hashed allowed-input manifest.

## Implementation phases
1. Foundation — audit existing assets; write brand/README.md and brand/brief.md.
2. Concept authoring — create four structurally distinct SVG family sheets in
   neutral numeric order, each with parent/repository/product directions.
3. Comparison evidence — build one equal-frame comparison board covering
   light/dark/monochrome, 16/24/32 px, README, docs-header, and plugin-list contexts.
4. Provenance and handoff — write one private rationale/provenance record with a
   section per family, then add the rationale-free allowed-input manifest and
   hashes to brand/README.md for BRAND-002.
5. Conformance verification — inspect XML, prohibited constructs, context parity,
   artifact completeness, and scope boundaries without scoring a winner.

## Hard boundaries
- No independent preference critique or human selection.
- No canonical-master claim.
- No docs-site, README integration, plugin manifests, payloads, or version files.
- No production export automation.
```

### Tasks results

Populate total tasks, phases, parallel opportunities, user-story coverage, and
declared file count after `/speckit-tasks`. G5 fails if any AC-1 criterion or
Design Concept decision lacks a task.

---

## Atomicity Route

After G5, run the registered atomicity classifier against:

```text
specs/brand-001-racecraft-identity-system
```

| Field | Current value |
|---|---|
| Route | Pending — classifier runs after tasks exist |
| Releasable | Pending — classifier runs after tasks exist |
| Signals | Current planning signal is one coherent concept-comparison packet |
| Warnings | Original three-phase identity scope was split at user direction |

The generic size estimator now recommends one BRAND-001 slice. The structural
classifier remains authoritative for PR routing after tasks exist.

---

## Phase 6: Analyze

**When to run:** Always after tasks.

### Analyze prompt

```text
/speckit-analyze

Focus on:
1. Constitution alignment and exact declared-file scope.
2. Traceability from AC-1.1 through AC-1.3 and every Design Concept decision to tasks.
3. Structural distinctness: four concepts must not be cosmetic variants of one mark.
4. Comparison parity: every family receives identical contexts, scale, labels, and ordering treatment.
5. Information isolation: the private author-rationale record is absent from the
   hashed conformance/critic input manifest.
6. Scope drift: flag any selection, canonical-master, export-pipeline, integration,
   release, or version task as CRITICAL.
7. Reviewability: confirm zero production LOC/files, exactly eight core brand
   files, and no more than 25 total branch files or surface a blocker.
```

G6 requires zero CRITICAL/HIGH findings. Review every warning rather than
silently downgrading it.

---

## Phase 7: Implement

**When to run:** After G6 passes.

### Implement prompt

```text
/speckit-implement

## Evidence-first visual cycle
For each family:
1. RED — state the family-specific hypothesis, structural difference, required
   contexts, and failure conditions before drawing.
2. GREEN — author the minimum intentional SVG geometry that satisfies the brief.
3. REFACTOR — simplify paths, strengthen silhouette/negative space, and remove noise.
4. VERIFY — parse the SVG, render every required context, inspect 16/24/32 px,
   and record provenance plus one honest weakness.

## Pre-implementation setup
1. Confirm the repository root and branch match this workflow.
2. Confirm `git status --short` contains only the approved scaffold artifacts.
3. Re-read the Design Concept, generated spec, plan, and resolved checklists.
4. Do not install dependencies unless the approved plan demonstrates they are required.

## Creation guidance
- Use platform-native visual/creative tooling for exploration when available,
  but commit intentional editable SVG geometry as the source of truth.
- Keep all four families original and structurally distinct.
- Do not trace, vectorize, or imitate an existing company/open-source mark.
- Do not use a raster image, remote font, URL, script, event, animation,
  foreignObject, or DTD inside an SVG.
- Use the same comparison frame, labels, scale rules, and neutral numeric ordering.
- Keep `brand/review/author-rationales.md` out of the conformance-review input;
  pass only the hashed manifest inputs.
- A separate conformance reviewer may reject incomplete or non-editable output;
  it must not rank, score, or select a family.
- Stop with a neutral handoff packet for BRAND-002.
```

### Implementation progress

| Work package | Tasks | Status | Evidence |
|---|---|---|---|
| Brief and asset audit | Populated after G5 | ⏳ Pending | Brief and audit references |
| Four concept families | Populated after G5 | ⏳ Pending | Editable SVG family sheets |
| Comparison evidence | Populated after G5 | ⏳ Pending | Equal-frame comparison board |
| Rationale/provenance handoff | Populated after G5 | ⏳ Pending | Private rationale record and hashed allowed-input manifest |
| Conformance verification | Populated after G5 | ⏳ Pending | XML, render, parity, and scope evidence |

---

## Post-Implementation Checklist

- [ ] All generated tasks are complete and G7 evidence is recorded.
- [ ] All four concept SVGs parse and have stable `viewBox` values.
- [ ] No SVG contains prohibited, external, raster, or font-runtime dependencies.
- [ ] All four concepts render in identical light, dark, monochrome, 16/24/32 px,
  README, docs-header, and plugin-list frames.
- [ ] Family relationship remains legible in monochrome.
- [ ] Provenance and font/license notes are complete.
- [ ] The hashed allowed-input manifest excludes the private rationale record
  and contains no winner cues.
- [ ] No family is selected or described as canonical.
- [ ] `git diff --check` passes.
- [ ] The diff contains no plugin, docs-site, payload, release, or version file.
- [ ] The active reviewability gate passes without an exception.
- [ ] The focused verification required by the generated plan passes.
- [ ] The PR packet leads reviewers through brief → concepts → comparison → blind handoff.

---

## Lessons Learned

Populate after implementation:

- What produced genuinely different silhouettes.
- Which small-size constraints changed the concepts most.
- Which prompt/context boundaries reduced anchoring or derivative output.
- Which patterns should carry into BRAND-002 critique and BRAND-003 refinement.

---

## Project Structure Reference

```text
docs/
└── ai/specs/.process/
    ├── BRAND-001-design-concept.md
    └── BRAND-001-workflow.md
specs/
└── brand-001-racecraft-identity-system/
    └── SPEC-MOC.md
brand/
├── README.md
├── brief.md
├── concepts/
│   ├── family-01-apex-gate.svg
│   ├── family-02-tuned-trajectory.svg
│   ├── family-03-modular-standard.svg
│   ├── family-04-shared-negative-space.svg
│   └── comparison-board.svg
└── review/
    └── author-rationales.md
```

## Autopilot Handoff

After this scaffold branch is pushed, start a new task rooted at the exact
worktree above and use the platform-native command:

**Claude Code**

```text
/speckit-pro:speckit-autopilot docs/ai/specs/.process/BRAND-001-workflow.md
```

**Codex**

```text
$speckit-autopilot docs/ai/specs/.process/BRAND-001-workflow.md
```

Do not run either command from the main checkout or another feature worktree.

Template based on SpecKit best practices and populated for BRAND-001 from the
Racecraft Identity System PRD, technical roadmap, and setup Design Concept.
