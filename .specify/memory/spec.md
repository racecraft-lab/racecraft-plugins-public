# Project Memory: Specifications

Durable, distilled record of merged feature specifications. Each section is
appended when a feature is archived. Raw spec artifacts remain recoverable from
git (see `.specify/memory/changelog.md` for per-feature recovery commands).

---

## Artifact relocation — tiering, .process/, collapse

[Source: specs/007-artifact-relocation]
**Branch**: `007-artifact-relocation` · **Status**: Completed · **Archived**: 2026-06-05

### Summary

Tier every speckit-pro-authored spec artifact into CONTRACT (review-visible) vs
EXHAUST (scaffolding), redirect the three EXHAUST artifacts speckit-pro itself
authors — the design-concept doc, the workflow file, and the UAT runbook — into a
`.process/` directory, collapse `.process/` out of the review diff via a
repository-root `linguist-generated` rule, and align the reviewability gate's
diff-mode LOC accounting so relocated exhaust drops out of the reviewable count.
No artifact is deleted; every relocated file stays on disk at its new `.process/`
location and remains diffable on demand.

### User Stories

- **US1 (P1) — Tier and redirect speckit-pro-authored exhaust.** Classify every
  speckit-pro spec artifact as CONTRACT or EXHAUST, and redirect the EXHAUST that
  speckit-pro authors into `.process/`: the design-concept doc and workflow file
  land under `docs/ai/specs/.process/`; the UAT runbook lands under the feature's
  own `specs/<NNN>/.process/`. No deletion. Every prose redirect in a Claude skill
  is mirrored identically into its Codex counterpart.
- **US2 (P2) — Collapse, align the gate, and lint the collapse rule.** The
  relocated `.process/` exhaust is collapsed out of the default review diff (marked
  generated, still diffable on demand), the reviewability gate excludes `.process/`
  lines from reviewable-LOC accounting, the collapse rule is written into consuming
  projects' repository roots idempotently, and a guard lint ensures the collapse
  rule can only ever target `.process/` (never a CONTRACT artifact). US2 is inert
  until US1 writes under `.process/`, so US1 sequences first.

### Functional Requirements

- **FR-001**: Define an artifact taxonomy classifying every speckit-pro-authored
  spec artifact as CONTRACT (review-visible, never collapsed) or EXHAUST
  (relocated to `.process/`).
- **FR-002**: Write the design-concept doc and the workflow file under
  `docs/ai/specs/.process/` instead of directly in `docs/ai/specs/`.
- **FR-003**: Write the UAT runbook under the feature's own
  `specs/<NNN>/.process/` directory.
- **FR-004**: Preserve every relocated file (no deletion); each stays present and
  readable at its new `.process/` location so audit/provenance survive.
- **FR-005**: The generated PR body MUST continue to render its UAT-runbook
  section after relocation (reference repointed, not removed).
- **FR-006**: Every prose redirect in a Claude skill MUST be mirrored identically
  into its Codex counterpart (same `.process/` targets, no drift).
- **FR-007**: Carry a repository-root collapse rule marking `.process/` content
  as generated so it collapses out of the default review diff.
- **FR-008**: Collapse marks content generated ONLY (never non-diffable / `-diff`);
  relocated artifacts stay diffable and loadable on demand.
- **FR-009**: Scaffolding inside a consuming project MUST write the same
  `.process/` collapse rule into the consumer's repository-root `.gitattributes`,
  idempotently: (a) create the file if absent; (b) append only if the rule line is
  not already present (exact match, whitespace/trailing-newline tolerant);
  (c) append-only, preserving pre-existing lines byte-for-byte. Both branches
  converge on exactly one copy of the rule.
- **FR-010**: The reviewability gate MUST exclude `/.process/` paths from
  reviewable-LOC accounting while still counting CONTRACT content. Confined to the
  `/.process/` segment: no false exclusion; with zero `.process/` paths the count
  is identical to its pre-feature value (no-op).
- **FR-011**: The gate's `.process/` exclusion MUST be self-contained (it MUST NOT
  parse the repository-root collapse config); the intentional duplication is
  guarded against drift by an automated structural check.
- **FR-012**: A structural lint MUST confirm every collapse rule is scoped to
  `.process/` and MUST fail if any rule is broadened to a path that could include a
  CONTRACT artifact.
- **FR-013**: New-specs-only: MUST NOT migrate, move, or mutate any existing
  `specs/<NNN>/` directory, nor the pre-existing non-`.process/` files in the
  `docs/ai/specs/` tree (legacy `SPEC-*-workflow.md`, design-concept docs, the
  pipeline-verification runbook, the technical-roadmap files). Legacy migration is
  owned by a separate, later retro-migration spec.
- **FR-014**: The redirect MUST create the `.process/` directory when it does not
  yet exist, so the first exhaust artifact of a new spec lands correctly.
- **FR-015**: MUST NOT regress the pre-existing test suite (Layer-1 structural
  incl. Codex parity validators, Layer-4 script-unit, Layer-5 tool-scoping). The
  new Layer-1 lint EXTENDS the existing structural layer (not a replacement/renumber);
  the two extended Layer-4 tests are additive (new assertions appended).

### Key Entities

- **CONTRACT artifact**: A review-visible spec artifact a reviewer is expected to
  read. Set: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`,
  `contracts/**`, `checklists/**`, `SPEC-MOC.md`, `docs/ai/specs/*-technical-roadmap.md`.
  Never collapsed; never relocated by this feature. Roadmap files stay safe because
  the collapse glob and gate exclusion match the `/.process/` segment ONLY.
- **EXHAUST artifact**: An auto-generated scaffolding artifact documenting how a
  contract artifact was produced (design-concept doc, workflow file, UAT runbook).
  Relocated into `.process/`, collapsed out of the review diff, excluded from the
  gate's reviewable-LOC accounting — never deleted.
- **`.process/` directory**: The relocation target for EXHAUST. Exists in two trees
  — `docs/ai/specs/.process/` (scaffold-time exhaust) and `specs/<NNN>/.process/`
  (per-feature exhaust). The single anchor the collapse rule, gate exclusion, and
  lint all key on.
- **Collapse rule**: A repository-root `.gitattributes` entry marking `.process/`
  content as generated so the platform hides it from the default diff while keeping
  it diffable. Mirrored into consuming projects' repo roots by the scaffold ensure-step.

### Edge Cases

- `.process/` directory absent on first write → redirect creates it (FR-014).
- Collapse rule present in plugin repo but absent from a consuming project →
  consumer ensure-step closes the gap; if skipped, consumer exhaust stays visible
  (degraded, not broken).
- Consumer `.gitattributes` write interrupted partway → safe-write (temp file in
  same directory + atomic rename, trailing-newline normalized before append) so the
  file is never truncated, half-written, or silently concatenated (FR-009c).
- Collapse rule and gate exclusion list disagree → the lint catches the drift
  (the two are intentionally maintained separately).
- PR-body section references a relocated file → reference repointed to the new
  `.process/` location so the section still renders.
- Legacy spec directory present → new-specs-only; must not touch/migrate it.

### Success Criteria

- **SC-001**: For a newly scaffolded feature, none of the three exhaust artifacts
  appear in the default review diff (collapsed by construction).
- **SC-002**: 100% of relocated exhaust artifacts still exist and are readable at
  their new `.process/` location (zero data loss).
- **SC-003**: Gate reviewable-LOC excludes 100% of `.process/` lines while
  including 100% of CONTRACT lines (deterministic test, known line counts).
- **SC-004**: A consuming project that scaffolds a spec receives the collapse rule
  in its own repo root; re-running leaves exactly one copy (idempotency).
- **SC-005**: The collapse-scope lint fails when a rule is broadened beyond
  `.process/` and passes when all rules are scoped to it (positive + negative case).
- **SC-006**: Every redirect prose edit in a Claude skill has an identical Codex
  counterpart (zero drift in redirect targets).
- **SC-007**: `bash speckit-pro/tests/run-all.sh` reports zero failures across the
  pre-existing Layer-1/4/5 checks, and passing count ≥ pre-change baseline.

### Out of Scope

- Redirecting extension-authored exhaust (retrospective report, verify-tasks
  report) — written by external SpecKit extensions, not speckit-pro; post-merge
  cleanup owned by the installed `archive` extension. No `git mv` sweep.
- Moving the CONTRACT set.
- Migrating any legacy/existing spec (owned by a later retro-migration spec).
- Rendering artifacts non-diffable (`-diff`) — collapse is generated-only.
- Map-of-content templates and gate-threshold rework (separate, later specs).

---

## Atomicity-test router (read-only classifier)

[Source: specs/prsg-007-atomicity-router]
**Branch**: `prsg-007-atomicity-router` · **Status**: Completed · **Archived**: 2026-06-09

### Summary

Adds a read-only routing classifier for the PR-size governance split-PR engine.
`atomicity-route.sh` inspects a feature directory's task/plan/spec evidence and
emits advisory JSON for downstream planner/emission phases. It never mutates
files and exits successfully for every valid classification.

### User Stories

- **US1 — Classifier.** Emit a route from the locked enum
  `split-PR`, `one-navigable-PR`, reserved `branch-by-abstraction`,
  `single-atomic-PR`, or `out-of-scope`, using structural seams rather than LOC.
- **US2 — Safety routing.** Override to `single-atomic-PR` for hard-atomic
  signatures and emit `releasable:false` warnings for destructive migration or
  concurrency classes where green CI is not enough.

### Functional Requirements

- The CLI is `speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh <feature-dir>`.
- Successful classifications write one JSON object to stdout and no files.
- Usage or unreadable input exits 2 with an error JSON object.
- Missing or empty `tasks.md` routes to `out-of-scope`.
- Autopilot records the result in the workflow file's `## Atomicity Route`
  section after Tasks/G5; PRSG-008/009 consume it later.

### Success Criteria

- Layer 4 router fixtures cover every route and hard-atomic class.
- Dogfood on PRSG-007 routes to a non-split route with `releasable:true`.
- Layer 1 Codex parity and structural validation remain green.

### Cleanup Note

The active spec folder remains in `specs/**` for now because
`test-atomicity-route.sh` reads `specs/prsg-007-atomicity-router` directly as a
dogfood/schema fixture.

---

## Retro-migration: version marker + state-keyed backfill/relocate

[Source: specs/prsg-011-retro-migration]
**Branch**: `prsg-011-retro-migration` · **Status**: Completed · **Archived**: 2026-06-09

### Summary

Adds deterministic structure-migration tooling so existing SpecKit projects can
adopt PRSG-001/002/003 layout rules without mass-stamping or moving legacy specs.
The migration path mirrors the archive extension's dry-run/apply safety model and
keeps Tier-2 PROCESS relocation operator-triggered only.

### User Stories

- **US1 — Repo migration.** `migrate-structure.sh --dry-run` reports ordered
  pending migrations; `--apply` on a clean tree writes the structure marker,
  Tier-1 repo edits, and Tier-0 navigation backfill.
- **US2 — Thawed legacy relocation.** `relocate-process-artifacts.sh` moves only
  PROCESS artifacts into `.process/`, stamps `structureVersion: 1`, and preserves
  recovery through forced backups.
- **US3 — Suggestion-only registration.** Scaffold/autopilot can suggest the
  codemod for thawed candidates but must not auto-run it.

### Functional Requirements

- Dirty-tree dry-runs are read-only; all mutation paths hard-fail on dirty trees.
- `.specify/feature.json` marks in-flight specs as frozen and skipped.
- Tier-0 does not stamp or move legacy specs.
- Tier-2 protects CONTRACT paths and normalizes legacy evidence/review packet
  names into `.process/`.

### Success Criteria

- Layer 4 validates dry-run, idempotency, backup, move-set, and ID-normalization
  fixtures.
- Layer 3/8 guidance confirms scaffold/autopilot only suggest the codemod.
- Layer 1 structural checks pass for fresh and grandfathered legacy layouts.
