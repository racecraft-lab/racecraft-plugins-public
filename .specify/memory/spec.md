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

The active spec folder was removed from `specs/**` cleanup on 2026-06-09 after
PR #136 decoupled `test-atomicity-route.sh` from the live
`specs/prsg-007-atomicity-router` directory by vendoring a dogfood/schema fixture.

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

---

## Layer-planner: tasks.md to ordered increments

[Source: specs/prsg-008-layer-planner]
**Branch**: `prsg-008-layer-planner` · **Status**: Completed · **Archived**: 2026-06-10

### Summary

Adds a read-only PRSG-008 planner for the PR-size governance split-PR engine.
`plan-layers.sh` accepts a feature directory, parses its `tasks.md`, and emits a
deterministic versioned JSON layer plan to stdout with no repository writes. The
planner remains independent from PRSG-007 routing and PRSG-009 branch/PR
emission.

### User Stories

- **US1 — Stable layer-plan envelope.** `speckit-autopilot` can pass one feature
  directory and receive stable JSON with `ok`, `invalid_plan`, or `input_error`
  status and concise stderr diagnostics.
- **US2 — Ordered increment parser.** Foundation, user-story, and Polish sections
  are grouped into semantic increments such as `foundation`, `us1`, `us2`, and
  `polish`, using `## Dependencies & Execution Order` plus
  `### Incremental Delivery` as authoritative ordering.
- **US3 — Structured diagnostics.** Malformed task plans fail with schema-backed
  machine-readable errors, while missing file/test references remain warnings.
- **US4 — Autopilot gate.** Autopilot runs the planner after PRSG-007 route
  recording only for `split-PR`, persists successful envelopes, and stops before
  implementation on planner errors.

### Functional Requirements

- The CLI is
  `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh <feature-dir>`.
- Successful plans write stable JSON to stdout and no files.
- Usage/input errors exit `2`; invalid task plans exit `1`; success exits `0`.
- Output uses a single versioned envelope with increments, tasks, warnings,
  errors, summary counts, repo-relative paths, source line numbers, checkbox
  state, `[P]` metadata, dependencies, and counts-only advisory size metadata.
- Invalid-plan diagnostics use stable codes/details for missing headings, empty
  increments, unknown increments, dependency cycles, contradictory ordering,
  duplicate IDs, and malformed task-like lines.
- Path fields are normalized relative to the worktree root with leading `./` and
  redundant `.` segments removed.
- PRSG-008 does not create branches, PR bodies, restack metadata, or multi-PR
  topology; PRSG-009 owns emission.

### Success Criteria

- Layer 4 planner fixtures validate stable success, warnings, invalid-plan,
  input-error, read-only, determinism, schema, and generated 200-task behavior.
- Direct PRSG-008 dogfood planning returned `status=ok`, 6 increments, and 45
  tasks during implementation validation.
- PR #138 CI recorded successful PR Checks, CodeQL, and post-merge main checks.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup on 2026-06-10 after
the Layer 4 planner harness was decoupled from the live spec schema by vendoring
`tests/speckit-pro/layer4-scripts/fixtures/plan-layers/contracts/plan-layers.schema.json`.

---

## Multi-PR emission (post-implementation rewrite)

[Source: specs/prsg-009-multi-pr-emission]
**Branch**: `prsg-009-multi-pr-emission` · **Status**: Completed · **Archived**: 2026-06-11

### Summary

Adds PRSG-009's post-implementation split-PR emission path. The implementation
consumes PRSG-008 layer-plan output, emits ordered Style B slice PRs with
explicit `gh pr create --base --head --body-file` arguments, records schema v2
PRS rows, writes durable resume state, isolates failed slice verification, and
provides dry-run-first restack recovery.

### User Stories

- **US1 - Emit ordered slice PRs.** A verified implementation can produce one
  branch and one PR per PRSG-008 layer in dependency order.
- **US2 - Persist PR table and resume evidence.** After each successful slice,
  `.process/prs.json`, the Spec MOC PRS table, workflow evidence, and
  `autopilot-state.json` contain enough data to resume without duplicate PRs.
- **US3 - Define stack topology, scoped CI, and restack.** Slice PR bodies carry
  scoped verification and full-regression evidence, while `restack.sh` plans or
  applies ordered retarget/rebase recovery after lower-stack squash merges.

### Functional Requirements

- The emitter consumes the PRSG-008 layer-plan envelope as the sole slice source
  and adds no new routing or slicing heuristics.
- Slice branches use deterministic `<feature-branch>/<NN>-<slice-id>` names and
  explicit base/head PR creation.
- Scoped verification must pass before a slice PR opens; failed later slices do
  not rewind or relabel earlier opened PRs.
- State persistence uses same-directory temp files and validated JSON candidates
  for `autopilot-state.json`, PRS v2 manifests, and slice packet outputs.
- PRS schema v2 renders bounded reviewer-navigation rows with order, slice, PR,
  status, branch, base, SHA, scope, and verification fields.
- `gh-stack` remains optional; `restack.sh` is the deterministic fallback and is
  dry-run by default.

### Success Criteria

- Layer 4 fixtures validate three-slice emission, single-slice emission, scoped
  verification failure blocking, no-scoped-test evidence, resume reconciliation,
  post-PR persistence failure handling, closed-PR blocking, and restack exit
  semantics.
- PR #145 CI passed PR Checks, CodeQL, Release, `test(speckit-pro)`,
  `validate-plugins`, `validate-pr-title`, and `detect`.
- Post-cleanup `bash tests/speckit-pro/run-all.sh` passed `2300/2300`.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup on 2026-06-11 after
PR #145 merged and the PRSG-009 contract schemas were preserved under
`speckit-pro/skills/speckit-autopilot/contracts/`.
Recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-11-prsg-009-post-merge-hygiene.md`.

---

## Harden the hatch + O5 monster-epics

[Source: specs/prsg-010-harden-the-hatch]
**Branch**: `prsg-010-harden-the-hatch` · **Status**: Completed · **Archived**: 2026-06-11

### Summary

PRSG-010 closes the remaining reviewability hatch after the small-PR path exists.
It adds a final pre-PR backstop with re-slicing guidance, preserves typed
exceptions only when provenance is operator-owned and review-visible, adds an O5
monster-epic parent/child model using flat sibling specs, and promotes contextual
router signals only from deterministic high-confidence evidence.

### User Stories

- **US1 - Stop unreviewable PRs before creation.** Final gate blocks stop before
  PR body generation, `gh pr create`, or multi-PR emission, and write a
  re-slicing packet with PRSG-007/008/009 recovery steps.
- **US2 - Model genuine monster epics without nested specs.** O5 parent
  manifests coordinate flat sibling child specs, dependency order, shared links,
  and read-only status rollup without introducing nested `specs/<parent>/<child>`
  scanning.
- **US3 - Route from strong contextual evidence only.** Flag-system,
  release-cadence, and consumer-locality probes affect routing only when the
  evidence is deterministic and high confidence; weak evidence remains advisory.

### Functional Requirements

- Autopilot runs the final reviewability diff gate after implementation
  verification and before PR body generation, PR creation, or multi-PR emission.
- Blocking final gate results without honored exceptions stop the run and record
  `final_reviewability_gate` state plus a machine-readable re-slicing packet.
- Typed exceptions remain valid only as exact branch-added Markdown pragmas in
  committed, review-visible, non-generated CONTRACT artifacts.
- Generated roadmap, workflow, template, and PR-description content cannot emit
  live copy-pasteable exception override lines.
- O5 parent manifests are review-visible CONTRACT data, children remain flat
  siblings under `specs/`, topology validates before rollup, and status emits one
  row per declared child.
- Atomicity routing promotes only high-confidence contextual evidence into
  closed `signals[]`; weak, stale, fixture-only, code-fence-only, or conflicting
  evidence remains route-neutral in closed `hints[]`.

### Success Criteria

- Final gate block scenarios without a valid typed exception create no pull
  request and record a re-slicing packet.
- Valid typed exception scenarios expose class and provenance in run state and
  review evidence.
- Generated education surfaces contain zero standalone valid exception pragma
  lines.
- O5 rollup output is stable and reserves O5 for cases ordinary O4 routing and
  layer planning cannot slice thin enough.
- Contextual probe fixtures prove weak evidence does not change decisive routes,
  while high-confidence evidence uses documented signal vocabulary.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup on 2026-06-11 after
PRs #149-#155 merged and the PRSG-010 production contracts were preserved under
`speckit-pro/skills/speckit-autopilot/contracts/`.
Recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-11-prsg-010-post-merge-hygiene.md`.

---

## Vertical-slice sizing heuristics in PRD/grill-me

[Source: specs/prsg-005-slice-sizing-heuristics]
**Branch**: `prsg-005-slice-sizing-heuristics` · **Status**: Completed · **Archived**: 2026-06-12

### Summary

PRSG-005 makes right-sized specs more likely at the earliest scoping moment. It
adds shared SPIDR, INVEST, and vertical-slicing guidance, a deterministic
advisory estimator, and mirrored Claude/Codex updates for `speckit-prd` and
`grill-me` so roadmap entries and grilled specs are born as thin vertical
slices.

### User Stories

- **US1 - Catalog-level decomposition in speckit-prd.** The PRD skill decomposes
  raw ideas into thin vertical roadmap entries, populates the existing
  `Projected reviewable LOC` field from the estimator, and keeps over-ceiling
  findings advisory.
- **US2 - Per-spec validation and split in grill-me.** The grill-me skill runs
  the same estimator for a single spec, recommends vertical splits for oversized
  or horizontal scope, and records the selected split in the design concept.

### Functional Requirements

- Shared SPIDR, INVEST, and vertical-slicing guidance lives in one reference
  document, with only short inline summaries in the skill entrypoints.
- The estimator is deterministic, bash plus `jq`, and emits only `ok` or `warn`.
- `warn`, missing estimator output, malformed size signals, and spike slices
  remain advisory and never block the interview or downstream workflow.
- Claude and Codex skill mirrors preserve behavior equivalence without
  duplicating the estimator or the reference guidance.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup on 2026-06-12 after
PR #120 merged and archive provenance/recovery commands were recorded.
Recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-12-prsg-005-013-post-merge-hygiene.md`.

---

## Non-stopping reviewability markers

[Source: specs/prsg-013-reviewability-markers]
**Branch**: `prsg-013-reviewability-markers` · **Status**: Completed · **Archived**: 2026-06-12

### Summary

PRSG-013 fixes the reviewability sizing product bug: autopilot no longer stops
implementation for size alone. Parseable size warnings and size-only blocks are
recorded as durable PR marker evidence, implementation proceeds in marker
order, and final PR emission can consume the marker plan to create bounded
Foundation or user-story scoped PRs.

### User Stories

- **US1 - Continue through reviewability sizing.** Post-task and final
  reviewability size findings become marker-planning input, while malformed
  evidence and correctness failures still stop.
- **US2 - Emit scoped PRs from durable markers.** Marker planning derives
  stable Foundation and user-story boundaries from `tasks.md`, folds small
  Polish work, and records structured warnings for unsafe subdivisions.
- **US3 - Verify marker planning and emission behavior.** Deterministic
  fixtures and functional eval coverage validate non-stopping behavior,
  marker persistence, implementation ordering, hazard collapse, and Claude/Codex
  guidance parity.

### Functional Requirements

- `plan-layers.sh` records marker-aware plans with source fingerprints,
  marker order, folded Polish tasks, safe subdivision, and stale-plan rejection.
- `final-reviewability-backstop.sh` returns `marker_split` for a valid current
  marker plan when the full diff is size-blocked.
- `multi-pr-emission.sh` validates marker packets before PR side effects and
  supports both scoped marker packets and hazard-collapsed full-spec packets.
- Autopilot guidance requires future runs to checkpoint and record evidence in
  marker order instead of treating size-only reviewability findings as manual
  re-slicing stops.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup on 2026-06-12 after
PR #157 merged and PRSG-013 contracts/fixtures were preserved under the
autopilot skill payload and test fixtures.
Recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-12-prsg-005-013-post-merge-hygiene.md`.
