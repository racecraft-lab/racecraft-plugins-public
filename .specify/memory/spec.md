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

---

## Repository Foundation for CI/CD Pipeline

[Source: specs/001-repository-foundation]
**Branch**: `001-repository-foundation` · **Status**: Completed · **Archived**: 2026-06-13

### Summary

Established the repository release foundation for the plugin marketplace:
release-please configuration, plugin version manifest state, and the marketplace
version synchronization script. The shipped behavior lives in root automation
files and `scripts/sync-marketplace-versions.sh`; the active spec folder was
removed after PR #1 merge provenance and recovery commands were recorded.

### Cleanup Note

Recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-13-merged-specs-post-merge-hygiene.md`.

---

## DOC-003 Claude Code marketplace installation path

[Source: .specify/memory/archive-reports/2026-06-15-doc-003-004-post-merge-hygiene.md]
**Branch**: `doc-003-claude-code-marketplace-installation-path` · **Status**: Completed · **Archived**: 2026-06-15

### Summary

DOC-003 converted the Claude Code install route from a DOC-002 shell into a
source-backed user path for adding the Racecraft marketplace, installing
SpecKit Pro, reloading plugins, verifying namespaced skills, updating,
uninstalling, reinstalling, and reviewing Claude-specific trust surfaces.

### Cleanup Note

The active spec folder was removed after PR #187 merged. Recovery commands and
provenance are recorded in the DOC-003/DOC-004 archive report.

---

## DOC-004 Codex marketplace installation path

[Source: .specify/memory/archive-reports/2026-06-15-doc-003-004-post-merge-hygiene.md]
**Branch**: `doc-004-codex-marketplace-installation-path` · **Status**: Completed · **Archived**: 2026-06-15

### Summary

DOC-004 converted the Codex install route from a DOC-002 shell into a
source-backed user path for repo-scoped, personal/local, and CLI marketplace
installation, generated Codex payload use, installed plugin cache behavior,
`$install` custom-agent registration, restart and verification checks, and
bounded install-safety guidance.

### Cleanup Note

The active spec folder was removed after PR #186 merged. Recovery commands and
provenance are recorded in the DOC-003/DOC-004 archive report.

---

## DOC-005 First successful workflow tutorial and lifecycle explainer

[Source: .specify/memory/archive-reports/2026-06-16-doc-005-post-merge-hygiene.md]
**Branch**: `codex/doc-005-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-16

### Summary

DOC-005 converted the `/first-run` and `/spec-kit-lifecycle` route shells into
source-backed onboarding content. It defines first success as a visible
artifact trail rather than a merged PR, separates Claude Code
`/speckit-pro:<skill>` commands from Codex `$speckit-*` commands, records a
validated Codex `specify init --here --integration codex
--integration-options="--skills" --script sh` snippet, and explains the idea,
PRD, roadmap, scaffold, autopilot, validation, and G1-G7 gate lifecycle.

### User Stories And Requirements

- New Claude Code and Codex users can start from the correct platform install
  route before running a first workflow.
- Users can check Spec Kit CLI, constitution, roadmap, branch, GitHub CLI, and
  JSON tooling prerequisites before scaffolding or running autopilot.
- Users can identify the expected artifacts for PRD, roadmap entry, scaffolded
  workflow/spec, autopilot phase output, and validation evidence.
- The lifecycle explainer exposes phase outputs and gate meanings as visible
  semantic content with a static fallback path.
- Command examples remain platform-specific and avoid browser-executed local
  plugin runs.

### Edge Cases

- Missing roadmap entries route users back to PRD or roadmap creation before
  scaffold.
- Missing scaffold output requires inspecting scaffold evidence and the
  roadmap target before continuing.
- Partial autopilot output uses `autopilot-state.json`, phase artifacts,
  checklists, tasks, and PR-packet evidence to continue from the recorded
  phase.
- Failed validation checkpoints are recorded in review evidence and handed off
  to troubleshooting rather than expanding the first-run route into a full
  diagnostic matrix.

### Success Criteria

- The first-run page identifies success as artifacts plus validation evidence,
  not merged PR completion.
- Claude Code and Codex command surfaces are visually separated.
- The lifecycle page covers idea, PRD, roadmap, scaffold, specify, clarify,
  plan, checklist, tasks, analyze, implement, and G1-G7 gates.
- The lifecycle visualizer works as static HTML with visible text and no client
  JavaScript or shell execution.

### Cleanup Note

The residual DOC-005 PR-packet evidence folder was removed from active
`specs/**` cleanup after PRs #198-#201 merged. Recovery commands and
provenance are recorded in the DOC-005 archive report.

---

## DOC-006 Safe interactive selector and validation aids

[Source: .specify/memory/archive-reports/2026-06-17-doc-006-post-merge-hygiene.md]
**Branch**: `codex/doc-006-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-17

### Summary

DOC-006 converted the choose-your-path route into a static-first interactive aid
surface. It keeps complete fallback content in semantic HTML while adding
platform and install-scope selection, copyable Claude Code and Codex command
guidance, repository-only manifest consistency checks, a generated payload flow
diagram, first-run checkpoints, and lightweight handoffs for mismatch or caution
states.

### User Stories And Requirements

- New and returning users can select the platform and supported install scope
  that matches their environment.
- Selected path guidance keeps Claude Code and Codex commands separated and
  labels commands as copyable guidance, not browser-executed local actions.
- Maintainers and evaluators can inspect source and generated payload manifest
  consistency for repository files only.
- The generated payload diagram and first-run checklist remain usable without
  browser scripting.
- Focused validation detects command-surface leakage, missing selector fields,
  checker mismatch/unavailable states, unsafe local-diagnostic UI, handoff
  drift, and missing first-run checkpoints.

### Edge Cases

- Unsupported or ambiguous selector states show explicit text and keep the
  complete supported static path guidance reachable.
- Missing metadata renders unavailable states instead of stale generated facts.
- Intentional packaging differences are informational rows, not false
  mismatches.
- Browser behavior does not read user files, accept pasted JSON, write config,
  install plugins, run shell commands, or invoke plugin workflows.

### Success Criteria

- Every supported selector path includes platform, scope, prerequisites,
  commands, success signals, and next docs links.
- Repository checker rows show compared values and consistency rules.
- Static fallback content covers selector guidance, checker facts, payload
  diagram nodes, and first-run checkpoints.
- Keyboard and source review confirm native controls, visible selected state,
  and readable command/checker content.

### Cleanup Note

The DOC-006 workflow and PR-packet evidence folder was removed from active
`specs/**` cleanup after PR #203 merged. Recovery commands and provenance are
recorded in the DOC-006 archive report.

## DOC-007 Command, workflow, manifest, and file-layout reference

[Source: .specify/memory/archive-reports/2026-06-17-doc-007-post-merge-hygiene.md]
**Branch**: `codex/doc-007-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-17

### Summary

DOC-007 added a deterministic generated reference library for the public docs
site. It covers SpecKit Pro skill surfaces, agents and subagents, manifests,
hooks, scripts, tests, and source-vs-dist layout with stable deep links,
source citations, and explicit inferred notes.

### User Stories And Requirements

- Users can look up plugin commands, skills, manifests, and generated payload
  responsibilities from stable documentation links.
- Maintainers can regenerate reference pages and detect drift before generated
  docs fall behind source files.
- Agents can cite exact source and generated payload paths when answering
  workflow, install, or troubleshooting questions.
- Reference pages separate checked source facts from inferred guidance.
- Existing install, first-run, lifecycle, and choose-your-path routes link into
  the reference library instead of duplicating full inventories.

### Edge Cases

- Missing source files are caught by reference generation and docs validation.
- Source-only and generated-payload-only paths remain separate so install docs
  do not tell users to install the mixed authoring tree.
- Source facts and inferred notes remain visibly distinct to reduce accidental
  overstatement.

### Success Criteria

- Generated reference pages exist for skills, agents, manifests, hooks,
  scripts, tests, and source-vs-dist layout.
- Docs validation runs the reference check.
- Existing docs routes deep-link into the generated reference pages.
- Every generated local reference is backed by a checked file path.

### Cleanup Note

The DOC-007 workflow evidence folder was removed from active `specs/**`
cleanup after PR #208 merged. Recovery commands and provenance are recorded in
the DOC-007 archive report.

---

## Optional gh-stack stack manager integration

[Source: specs/prsg-014-optional-gh-stack-stack-manager-integration]
**Branch**: `prsg-014-optional-gh-stack-stack-manager-integration` · **Status**: Completed · **Archived**: 2026-06-14

### Summary

PRSG-014 completed optional stack-manager hardening for autopilot split-PR
emission and restack flows. It added shared deterministic `gh stack` support
detection, a versioned `stack-manager-decision` contract, evidence threading
through `multi-pr-emission.sh` and `restack.sh`, pre-mutation explicit-`gh`
fallback, blocked recovery after partial or unknown `gh-stack` mutation, and
Claude/Codex operator-guidance parity.

The canonical path remains explicit GitHub `--base`/`--head` PR topology.
`gh-stack` is opportunistic and only selected after command availability,
version/support, read-only proof, and topology compatibility checks pass.

### Cleanup Note

The active spec folder was removed after PR #181 merged. Shipped behavior lives
in the shared autopilot scripts/contracts and committed Layer 4, Layer 7, and
Layer 8 fixtures; recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-14-prsg-014-post-merge-hygiene.md`.

---

## DOC-002 Unified Landing Page and IA Shell

[Source: .specify/memory/archive-reports/2026-06-14-doc-002-post-merge-hygiene.md]
**Branch**: `codex/doc-002-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-14

### Summary

DOC-002 created the first usable Astro/Starlight docs-site shell for Racecraft
Public Plugins. It added the `docs-site/` package/config baseline, pnpm lockfile,
landing page, Diataxis sidebar groups, all 11 top-level route shells, a
source-vs-generated-payload explanation, Pages-ready base-path handling, and
internal-link validation through `starlight-links-validator`.

### User Stories

- First-time users can understand the marketplace, `speckit-pro`, supported
  platforms, and next steps from the first page.
- Users can navigate Tutorials, How-to, Reference, and Explanation routes through
  the docs shell.
- Maintainers can validate the shell with docs-site check/build/link scripts
  before later content specs fill in full platform guidance.

### Acceptance Criteria

- AC-2.1: Landing page states marketplace purpose, current plugin, primary
  value, and supported platforms in one screen.
- AC-2.2: IA exposes Tutorials, How-to, Reference, and Explanation sections.
- AC-2.3: Claude Code and Codex paths are selectable from the first interaction.
- AC-2.4: Docs distinguish authoring source `speckit-pro/` from generated
  install payloads under `dist/claude/**` and `dist/codex/**`.
- AC-2.5: Every top-level nav label has a stated purpose and success criterion.

### Cleanup Note

`specs/doc-002-unified-landing-page-and-ia-shell` was removed from active
`specs/**` cleanup after PRs #173-#177 merged and recovery commands were
recorded in
`.specify/memory/archive-reports/2026-06-14-doc-002-post-merge-hygiene.md`.

---

## Interactive documentation framework and IA spike

[Source: specs/doc-001-static-docs-framework-and-ia-spike]
**Branch**: `doc-001-static-docs-framework-and-ia-spike` · **Status**: Completed · **Archived**: 2026-06-13

### Summary

DOC-001 selected **Astro with Starlight** as the default stack for the future
interactive documentation site, with **pnpm** as the report-only package manager
recommendation for DOC-002. The canonical decision record is
`docs/ai/research/interactive-documentation-framework-spike.md`.

The spike compared Docusaurus/MDX, VitePress, Astro/Starlight, and a
repo-native Markdown fallback across static hosting, GitHub Pages deployment,
reusable component interactivity, search, versioning, accessibility, link
checking, docs-as-code workflow fit, maintenance load, package/build/test
command roles, and support class. Docusaurus/MDX remains the first fallback if a
true Astro/Starlight hard blocker appears during DOC-002.

### User Stories

- Maintainers can review one source-backed framework recommendation and see why
  alternatives were rejected or deferred.
- DOC-002 implementers can consume a route-level Diataxis IA skeleton and
  report-only command handoff without reopening stack selection.
- Reviewers can verify the spike remained research-only and did not add a site
  scaffold, package file, lockfile, CI workflow, generated payload, marketplace
  file, README migration, or plugin behavior change.

### Functional Requirements Captured

- Compare all four required candidates with current source evidence and support
  classes.
- Recommend one default stack for DOC-002 unless a hard blocker is recorded.
- Explain non-selected alternatives and fallback order.
- Record package manager, setup, install, development preview, production
  build, local static preview, deployment, and minimum validation command roles.
- Provide an 11-route IA skeleton covering Start, Install: Claude Code, Install:
  Codex, First Run, Choose Your Path, Reference, Troubleshooting, Security &
  Trust, Contribute & Release, Spec Kit Lifecycle, and Glossary.
- Keep DOC-001 research-only and defer docs-site implementation to DOC-002 or
  later DOC specs.

### Entities

- **Framework Candidate**: Docusaurus/MDX, VitePress, Astro/Starlight, or the
  repo-native fallback.
- **Evaluation Criterion**: A scored comparison dimension such as hosting,
  interactivity, search, versioning, accessibility, link checking, workflow fit,
  maintenance load, and commands.
- **IA Route**: A top-level documentation path with Diataxis mode, audience,
  purpose, source evidence, success criterion, shell owner, and content owner.
- **Spike Report**: The durable research artifact that records evidence,
  recommendation, IA, commands, non-goals, and verification scope.

### Edge Cases

- Temporarily unavailable framework docs require recorded evidence gaps rather
  than stale claims.
- If all candidates fail GitHub Pages from this repository, the report must
  record the blocker and use the least-risk fallback.
- Third-party or paid support must be distinguished from built-in or official
  first-party support.
- Conflicting source evidence must prefer the most current official source and
  record the conflict.
- IA routes without source evidence or measurable success criteria must be
  revised or omitted.

### Success Criteria

- The report covers 4 candidate stacks across at least 10 evaluation dimensions.
- A maintainer can identify the recommended stack and alternative rationales in
  under 5 minutes.
- The IA skeleton has no placeholder route values and includes every required
  route field.
- DOC-002 can identify package manager and minimum command roles from the report
  alone.
- The final DOC-001 diff changed 0 package, lockfile, site config, prototype,
  CI, README/plugin README migration, marketplace, generated payload, or plugin
  behavior files.

### Cleanup Note

`specs/doc-001-static-docs-framework-and-ia-spike` was removed from active
`specs/**` cleanup after PR #163 merged and recovery commands were recorded in
`.specify/memory/archive-reports/2026-06-13-doc-001-post-merge-hygiene.md`.

---

## PR Checks Workflow

[Source: specs/002-pr-checks-workflow]
**Branch**: `002-pr-checks-workflow` · **Status**: Completed · **Archived**: 2026-06-13

### Summary

Added the pull-request validation workflow: plugin change detection, matrix
testing, conventional PR title validation, SHA-pinned checkout usage, skip-safe
docs-only behavior, and reviewer-readable failure annotations. The shipped
contract lives in `.github/workflows/pr-checks.yml`.

### Cleanup Note

The active spec folder was removed after PR #2 merge provenance and recovery
commands were recorded.

---

## Release Automation

[Source: specs/003-release-automation]
**Branch**: `003-release-automation` · **Status**: Completed · **Archived**: 2026-06-13

### Summary

Added release automation for `speckit-pro`: GitHub release workflow wiring,
release-please v4 integration, marketplace version sync after release creation,
and release safety documentation. The shipped contract lives in
`.github/workflows/release.yml`, release-please config, and the marketplace sync
script.

### Cleanup Note

The active spec folder was removed after PR #3 merge provenance and recovery
commands were recorded.

---

## Integration and Verification

[Source: specs/004-integration-verification]
**Branch**: `004-integration-verification` · **Status**: Completed · **Archived**: 2026-06-13

### Summary

Captured the repository integration and verification work: branch-protection
expectations, squash-only merge policy, Copilot review setup, CI/CD verification
checklist, and recovery guidance. The historical `tasks.md` ledger remained
unchecked even though PR #5 merged; the merge commit is the source of truth for
archive eligibility.

### Cleanup Note

The active spec folder was removed after PR #5 merge provenance and recovery
commands were recorded.

---

## Deterministic UAT Runbook Skeleton + PR Body Integration

[Source: specs/006a-uat-skeleton]
**Branch**: `006a-uat-skeleton` · **Status**: Completed · **Archived**: 2026-06-13

### Summary

Added deterministic UAT runbook generation and PR-body embedding: a script that
extracts user stories, FR/SC coverage, rollback, clarification markers, and
self-review context into a stable runbook, plus PR-body compatibility handling.
The full-spec test dependency remains preserved in the vendored
`tests/speckit-pro/layer4-scripts/fixtures/spec-full-snapshot.md` fixture.

### Cleanup Note

The active spec folder was removed after PR #99 merge provenance and recovery
commands were recorded.

---

## MOC templates + scaffold-time skeleton + version-gated lints

[Source: specs/prsg-002-moc-templates]
**Branch**: `prsg-002-moc-templates` · **Status**: Completed · **Archived**: 2026-06-13

### Summary

Added the MOC navigation contract: roadmap/spec MOC templates, scaffold-time
`SPEC-MOC.md` creation, version-gated orphan/stale-index lints, namespace-aware
ID normalization, and grandfathering for legacy specs without markers.

### Cleanup Note

The active spec folder was removed after PR #116 merge provenance and recovery
commands were recorded. MOC lint dogfood assertions now use committed fixtures
rather than the live PRSG-002 spec folder.

---

## Generated index/PRs/backlinks + status integration + phase-gate regen

[Source: specs/prsg-003-spec-index]
**Branch**: `prsg-003-spec-index` · **Status**: Completed · **Archived**: 2026-06-13

### Summary

Added deterministic spec index regeneration: generated INDEX, PRS, and BACKLINKS
zones, whole-zone sentinel replacement, stale generated-zone protection, status
integration, and phase-gate regen hooks. The generator and fixtures now carry the
behavior; the active source spec folder is no longer required.

### Cleanup Note

The active spec folder was removed after PR #121 merge provenance and recovery
commands were recorded.

---

## Roadmap-MOC home note from PRD + coach the two-zone structure

[Source: specs/prsg-004-roadmap-moc-home-note]
**Branch**: `prsg-004-roadmap-moc-home-note` · **Status**: Completed · **Archived**: 2026-06-13

### Summary

Added roadmap-MOC home-note support for PRD output and coach guidance: a curated
epics zone, generated INDEX zone, relative reciprocal links, and the two-zone
mental model for generated vs hand-authored navigation. One PR-review-packet
task remained unchecked in `tasks.md`; it was recorded as non-blocking historical
state because PR #129 merged.

### Cleanup Note

The active spec folder was removed after PR #129 merge provenance and recovery
commands were recorded.

---

## Plan-phase reviewability budget + gate threshold rework

[Source: specs/prsg-006-reviewability-budget]
**Branch**: `prsg-006-reviewability-budget` · **Status**: Completed · **Archived**: 2026-06-13

### Summary

Added preventive reviewability sizing: plan-phase LOC estimation, production-only
diff metrics, greenfield allowance, surface count downgraded to warning, and
typed reviewability exceptions. The shipped behavior lives in
`estimate-reviewable-loc.sh`, `reviewability-gate.sh`, templates, guidance, and
Layer 4 fixtures.

### Cleanup Note

The active spec folder was removed after PR #119 merge provenance and recovery
commands were recorded.

---

## Reviewer-ready PR packet contract

[Source: specs/prsg-012-reviewer-ready-pr-packet-contract]
**Branch**: `prsg-012-reviewer-ready-pr-packet-contract` · **Status**: Completed · **Archived**: 2026-06-13

### Summary

PRSG-012 makes autopilot-generated PR packets reviewer-ready before creation. It
adds generated conventional titles with future-spec scope support, structured
neutral PR descriptions, pre-create PR packet validation, split-PR validation
ordering, safe editable prose fields, and regression tests that prevent raw
evidence dumps or patronizing labels from entering PR descriptions.

### Cleanup Note

The active spec folder was removed after PR stack #164-#168 merged. The PRSG-012
feature and marker-plan test dependencies are preserved under
`tests/speckit-pro/layer4-scripts/fixtures/`; recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-13-merged-specs-post-merge-hygiene.md`.

---

## Tool-Agnostic Capability Discovery: platform mechanics spike

[Source: specs/tacd-001-platform-mechanics-spike]
**Branch**: `tacd-001-platform-mechanics-spike` · **Status**: Completed · **Archived**: 2026-06-18

### Summary

TACD-001 completed the platform-mechanics spike for replacing named optional MCP
preferences in SpecKit Pro with installed-capability discovery. The canonical
report audits active Claude and Codex runtime guidance, prerequisite messaging,
dependency metadata, generated payloads, and eval/test expectations; records a
Claude/Codex capability mechanics matrix; recommends a shared
capability-discovery reference with runtime-specific pointers and approved
equivalents; and defines the TACD-004 category allowlist that separates active
guidance from historical/provenance text.

### User Stories

- **US1 - Audit named-tool references.** Maintainers can see which named-tool
  references are active runtime guidance, prerequisite/user-facing messaging,
  runtime/dependency metadata, deterministic/eval expectations, generated
  source-derived duplicates, historical/provenance, fixture-only, or ambiguous.
- **US2 - Recommend directive home.** TACD-002 implementers have a specific
  directive-home decision: shared capability-discovery reference plus
  runtime-specific pointers or approved equivalents, with TACD-004 proving
  pointer coverage, target resolution, and behavior-observable evals.
- **US3 - Define enforcement categories.** TACD-004 authors can enforce
  vendor-neutral active guidance without over-banning archive records,
  generated duplicates, fixtures, or exact metadata IDs that are still required
  by a runtime schema.

### Functional Requirements

- Produce `docs/ai/research/tool-agnostic-capability-discovery-spike.md` as the
  report and decision record.
- Audit Claude and Codex active guidance, skills/references, prerequisite
  checks, plugin limitation docs, dependency metadata, generated payloads, and
  tests/evals for named optional-tool references.
- Record sanitized source/probe evidence for Claude Code and Codex across
  installed tools, MCP/app connectors, skills/plugins, and repo-local helpers.
- Recommend the directive home and downstream TACD-002/TACD-003/TACD-004
  handoffs without changing runtime behavior in TACD-001.
- Preserve historical/provenance references and avoid committing raw runtime
  inventories, local paths, connector lists, transcripts, or identifiers.

### Success Criteria

- The spike report covers both Claude Code and Codex and all four capability
  classes.
- The directive-home recommendation names the proof bar for shared-reference
  adoption.
- TACD-004 receives a category allowlist with blocked, allowed, and review
  classes.
- The TACD-001 diff remains report/process-only and leaves active runtime
  behavior changes to TACD-002/TACD-003/TACD-004.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup after PRs #211-#214
merged the spike stack and PR #216 adopted the spike decisions into the PRD and
roadmap. Recovery commands and provenance are recorded in
`.specify/memory/archive-reports/2026-06-18-tacd-001-post-merge-hygiene.md`.

---

## TACD-002 Capability Discovery Directive and Agent Updates

[Source: specs/tacd-002-capability-discovery-directive-and-agent-updates]
**Branch**: `tacd-002-capability-discovery-directive-and-agent-updates` · **Status**: Completed · **Archived**: 2026-06-18

### Summary

TACD-002 implemented the tool-agnostic capability-discovery directive selected
by TACD-001. The shipped behavior adds the shared directive at
`speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`,
updates scoped Claude and Codex agents to choose research/context help by
capability need, keeps fallback evidence transparent with confidence levels,
preserves exact tool IDs only as metadata or generated runtime evidence, and
refreshes generated Claude/Codex payloads from source.

TACD-002 also hardened marker PR emission after the real post-implementation
flow exposed branch namespace, title-normalization, and changed-file scope
blockers. The emitter now separates emitted branch prefixes from source feature
directories, derives reviewer-safe PR titles from story boundaries, and admits
declared tests, generated payload counterparts, and standard SpecKit process
evidence while still blocking unrelated undeclared files.

### User Stories

- **US1 - Agents choose by capability need.** Operators get guidance that names
  capability categories instead of preferred optional MCP tool sets.
- **US2 - Agents work without optional capabilities.** Agents continue with
  local, native platform, or repo-local fallback evidence and lower-confidence
  disclosure when optional capabilities are missing or unusable.
- **US3 - Runtime guidance stays semantically aligned.** Claude and Codex
  guidance share one semantic directive or an approved installed-runtime
  equivalent.
- **US4 - Generated payloads match source guidance.** Generated Claude and Codex
  payloads are refreshed from source and trace back to source guidance changes.
- **US5 - Marker emission survives branch namespace conflicts.** Ordered marker
  slice PRs can be emitted from a source feature directory even when the emitted
  branch prefix must avoid an existing parent branch ref.

### Functional Requirements

- Active behavior guidance selects capabilities by task need and evidence fit.
- Guidance covers codebase context, spec context, library documentation, web or
  domain research, source extraction, installed skills/plugins, and repo-local
  helpers.
- Claude agents point to the shared directive; Codex TOML agents include the
  approved compact-equivalent marker where direct Markdown pointer resolution is
  not stable.
- Discovery-informed answers report capability path, evidence, and confidence.
- Generated payloads are refreshed from source through
  `bash scripts/build-plugin-payloads.sh`.
- Marker emission supports `--source-feature-dir` separately from emitted
  branch prefix, normalizes public titles, and validates expected generated and
  process evidence.

### Success Criteria

- Scoped source and generated behavior surfaces no longer contain preferred
  named optional-tool wording.
- Source and generated Claude/Codex runtime guidance remain semantically
  aligned.
- Preserved exact IDs are classified as metadata, historical/provenance, or
  generated rewrite evidence rather than active preferred behavior.
- Focused marker-emission regressions and the deterministic SpecKit suite pass.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup after PRs #221-#226
merged the TACD-002 stack. Recovery commands and provenance are recorded in
`.specify/memory/archive-reports/2026-06-18-tacd-002-post-merge-hygiene.md`.

---

## DOC-008 and DOC-009 Interactive Documentation Trust and Release Workflow

[Source: specs/doc-008-troubleshooting-security-trust-update-rollback; specs/doc-009-maintainer-contributor-release-workflow]
**Branches**: `doc-008-troubleshooting-security-trust-update-rollback`, `doc-009-maintainer-contributor-release-workflow` · **Status**: Completed · **Archived**: 2026-06-18

### Summary

DOC-008 completed the troubleshooting, security/trust, update, and rollback
documentation tier for the interactive documentation roadmap. The shipped docs
expand `docs-site/src/content/docs/troubleshooting.md`, deepen
`docs-site/src/content/docs/security-and-trust.md`, add
`docs-site/src/content/docs/update-and-rollback.md`, and connect the install
and reference routes to those support pages.

DOC-009 completed the maintainer and contributor release workflow tier. The
shipped docs deepen `docs-site/src/content/docs/contribute-and-release.md` with
source-of-truth mapping, change-type routing, release-readiness commands,
payload and marketplace sync guidance, version ownership, public-readable PR
expectations, current PR Checks behavior, release automation observations, and
the DOC-010 handoff.

### User Stories

- **DOC-008 US1 - Diagnose a failure symptom.** Users can inspect symptoms,
  likely causes, read-only diagnostic files or commands, and recommended fixes.
- **DOC-008 US2 - Evaluate security and trust boundaries.** Users can
  distinguish official platform behavior, repository facts, installed runtime
  state, and recommended practice without reading the full repository.
- **DOC-008 US3 - Recover from stale or incorrect installs.** Users can follow
  update, refresh, reinstall, remove, rollback, stale-payload, stale-cache, and
  version-sync guidance for Claude Code and Codex.
- **DOC-009 US1 - Classify the change path.** Contributors can identify whether
  a change is docs-only, plugin source, generated payload, marketplace, or
  release automation work and see the expected evidence.
- **DOC-009 US2 - Complete release readiness.** Maintainers can verify parity,
  manifest/version consistency, generated payloads, release-readiness tests, and
  docs-site validation when relevant.
- **DOC-009 US3 - Review PR metadata and evidence.** Reviewers can evaluate
  Conventional Commit titles, public-readable bodies, review order, scope
  budget, traceability, verification, gaps, and rollback notes.
- **DOC-009 US4 - Understand docs-only CI and DOC-010 handoff.** Docs maintainers
  can distinguish current PR Checks behavior from future docs-site CI hardening.

### Functional Requirements

- Troubleshooting rows include symptom, likely cause, diagnostic file or
  command, recommended fix, platform label, and source links.
- Security and trust docs separate official vendor behavior, repository facts,
  generated payloads, installed cache/runtime state, managed policy, and
  recommended practice.
- Update and rollback docs cover marketplace refresh, plugin reinstall/remove,
  rollback boundaries, stale payloads, stale caches, version sync, and platform
  reload/restart needs.
- Contributor/release docs map authoring source, generated payloads,
  marketplace registries, release scripts, tests, docs-site files, generated
  reference pages, CI behavior, release-please, and PR conventions.
- Release-readiness docs explain `bash scripts/build-plugin-payloads.sh`,
  `bash scripts/sync-marketplace-versions.sh`, `bash tests/speckit-pro/run-all.sh`,
  `pnpm --dir docs-site reference:check`, and `pnpm --dir docs-site validate`
  in context.
- DOC-010 owns future search, accessibility, deep-link, responsive, docs-site
  CI, manifest/payload consistency, and safe command-snippet hardening.

### Success Criteria

- DOC-008 AC-8.1 through AC-8.6 are satisfied by static docs-site pages and
  source-backed support links.
- DOC-009 AC-9.1 through AC-9.6 are satisfied by the existing
  `/contribute-and-release` route and linked reference/source evidence.
- Both specs remained docs-only: no plugin behavior, manifests, hooks, generated
  payload semantics, release automation, or CI behavior changed as part of the
  shipped content.

### Cleanup Note

The active DOC-008 and DOC-009 spec folders were removed from `specs/**`
cleanup after PR #220 and PR #219 merged. Recovery commands and provenance are
recorded in
`.specify/memory/archive-reports/2026-06-18-doc-008-009-post-merge-hygiene.md`.

---

## TACD-003 Prerequisite and Documentation Messaging

[Source: specs/tacd-003-prerequisite-and-documentation-messaging]
**Branch**: `tacd-003-prerequisite-and-documentation-messaging-slice/01-foundation` · **Status**: Completed · **Archived**: 2026-06-19

### Summary

TACD-003 completed the prerequisite and user-facing messaging tier for the
tool-agnostic capability discovery roadmap. It replaces the named optional MCP
inventory in `check-prerequisites.sh` with one successful
`capability_coverage` advisory, updates active Claude and Codex prerequisite
guidance to describe capability coverage and fallback confidence, aligns plugin
limitation and coach/autopilot docs with capability-first wording, and refreshes
source-derived generated payloads.

### User Stories

- **US1 - Non-blocking capability advisory.** Operators see optional
  research/context coverage as a successful advisory instead of a setup failure.
- **US2 - Capability-first user guidance.** Active prerequisite and limitation
  docs explain codebase context, library documentation, web or domain research,
  and source extraction without promoting a fixed optional tool set.
- **US3 - Focused regression coverage.** Maintainers have deterministic checks
  for advisory shape, JSON output, missing optional capability success, true
  blocker preservation, and changed active guidance.

### Functional Requirements

- Replace the fixed optional-tool report with one `capability_coverage` check.
- Keep optional capability absence non-blocking when acceptable fallback
  evidence exists.
- Preserve true prerequisite blockers with actionable failure messaging.
- Update active Claude/Codex prerequisite, plugin limitation, coach, and
  autopilot guidance to use capability-first wording.
- Leave broad static enforcement, Layer 3 eval updates, Layer 5 pointer
  coverage, and broad named-tool detection to TACD-004.
- Regenerate generated payload copies from source rather than hand-editing
  `dist/**`.

### Success Criteria

- Missing optional capability paths remain successful and emit one parseable
  `capability_coverage` advisory.
- Changed active guidance contains capability categories instead of a fixed
  optional-tool recommendation.
- Focused Layer 4 and default deterministic test suites pass.
- PR packet evidence and reviewability state identify TACD-004 as the follow-up
  for final enforcement.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup after PR #230 merged.
Recovery commands and provenance are recorded in
`.specify/memory/archive-reports/2026-06-19-tacd-003-post-merge-hygiene.md`.

---

## DOC-010 Search, Accessibility, Deep Links, Docs Validation

[Source: specs/doc-010-search-accessibility-deep-links-docs-validation]
**Branch**: `doc-010-search-accessibility-deep-links-docs-validation` · **Status**: Completed · **Archived**: 2026-06-19

### Summary

DOC-010 completed the final interactive documentation hardening slice. It keeps
the existing Astro/Starlight and Starlight/Pagefind search stack, improves
support-oriented findability, stabilizes shareable anchors and generated
reference links, improves accessible interactive-aid and static fallback
behavior, and adds deterministic docs-site validation plus compact Playwright
smoke evidence.

### User Stories

- **US1 - Find and share support guidance.** First-time users, support
  responders, and maintainers can search, browse glossary entries, and share
  stable links to install, troubleshooting, reference, and release workflow
  content.
- **US2 - Use interactive aids accessibly.** Keyboard and screen-reader-oriented
  users can use `SafeInstallAids` and `LifecycleFlow`, or their static
  fallbacks, without pointer-only or inaccessible dynamic behavior.
- **US3 - Run one matching docs validation path.** Maintainers and contributors
  can run `pnpm --dir docs-site validate` locally and see a matching
  conditional `validate-docs` PR Checks gate.
- **US4 - Review minimal browser evidence.** Reviewers can inspect compact
  desktop and mobile smoke evidence for the six logical DOC-010 routes without
  reviewing a broad visual snapshot suite.

### Functional Requirements

- Preserve the existing docs-site stack, routes, and search provider.
- Provide stable support anchors and deterministic link/anchor validation for
  install, recovery, troubleshooting, glossary, generated reference, and release
  workflow content.
- Preserve or improve keyboard navigation, visible focus, labels, semantic
  controls, polite status announcements, responsive behavior, and static
  fallback content in the interactive docs aids.
- Provide one local docs validation path that runs generated reference checks,
  Astro checks, build/link validation, safe-aids validation, docs-quality
  validation, and minimal Playwright smoke.
- Add a `validate-docs` PR Checks job that uses job-level changed-file
  detection and preserves plugin matrix semantics for plugin-only changes.
- Keep automated validation within checked-in source and local preview
  boundaries; do not execute install snippets, inspect local user state, follow
  marketplace flows, submit analytics, or perform destructive behavior.

### Success Criteria

- DOC-010 designated support anchors, glossary terms, generated reference
  sections, troubleshooting entries, and release workflow details have stable
  links or intentional exceptions.
- Interactive aids retain essential guidance through keyboard-friendly controls
  and static fallback content.
- Local and CI docs validation cover generated references, site checks,
  safe-aids validation, docs-quality validation, and bounded browser smoke.
- Compact browser smoke covers `/`, `/choose-your-path/`,
  `/spec-kit-lifecycle/`, `/glossary/`, `/reference/skills/`, and
  `/contribute-and-release/` across desktop and mobile.
- PR packet evidence records validation, manual accessibility evidence, compact
  smoke artifact behavior, known gaps, automation-safety notes, and rollback
  guidance.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup after PRs #232
through #236 merged. Recovery commands and provenance are recorded in
`.specify/memory/archive-reports/2026-06-19-doc-010-post-merge-hygiene.md`.

## TACD-004 Verification Coverage

### Summary

TACD-004 is the final Tool-Agnostic Capability Discovery spec. It locks the
vendor-neutral optional-tool contract with deterministic guards plus functional
eval coverage, and repairs the Claude payload-build `strip_codex_guard` defect
that installed 8 of 10 Claude skills with empty bodies.

### User Stories

- As a maintainer, I want a deterministic check that fails when active runtime
  guidance reintroduces a hardcoded named optional-tool contract.
- As a maintainer, I want structural checks proving every capability-dependent
  agent points to the shared capability-discovery directive and that the pointer
  resolves from the installed `dist/**` layout.
- As a maintainer, I want the four functional eval expectations rewritten to
  assert both the absence of a named set and an affirmative capability-first
  answer.
- As a consumer, I want every installed skill to ship its full body, with a
  deterministic check that fails if the Claude payload truncates a `SKILL.md`.

### Functional Requirements

- Named-tool guard (Layer 5) plus full removal of the named MCP assertions.
- Pointer-coverage and target-resolution guards (Layer 1) against
  `dist/claude/**` and `dist/codex/**`.
- `strip_codex_guard` section-boundary fix, `dist/` rebuild, and a
  body-completeness guard.
- Vendor-neutral eval rewrites with behavior-observable scenarios and
  Claude/Codex parity, validated by committed fixtures with no live-run merge
  gate.

### Success Criteria

- The default deterministic suite passes: `bash tests/speckit-pro/run-all.sh`.
- Each new guard is non-vacuous: a deliberate regression fails it.
- All 8 truncated Claude skill bodies are restored.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup after PR #240 merged.
Recovery commands and provenance are recorded in
`.specify/memory/archive-reports/2026-06-22-tacd-004-post-merge-hygiene.md`.

## DOC-011 GitHub Pages Build-And-Deploy Pipeline

### Summary

DOC-011 shipped the staging deployment foundation for the Astro/Starlight docs
site. It adds a standard GitHub Pages Actions workflow, validates the docs site
before artifact upload, preserves staging indexing protection with
`noindex,nofollow` and `robots.txt`, documents Pages setup/retry/rollback in the
CI/CD runbook, adds PR workflow lint coverage, aligns release docs-reference
generation with Node 22, and hardens the shared SpecKit roadmap-MOC index guard.

### User Stories

- **US1 - Deploy docs after main merge.** Maintainers can merge docs-impacting
  changes to `main` and receive a staging deploy after docs validation passes,
  once repository Pages is manually configured for GitHub Actions.
- **US2 - Manually retry a deploy.** Maintainers can dispatch the same deploy
  workflow from `main` for transient Actions or Pages failures.
- **US3 - Preview staging without public discovery.** Reviewers can open the
  staging Pages URL while the site still communicates crawler and indexing
  restrictions until DOC-012.
- **US4 - Follow deploy setup and recovery runbook.** Contributors and
  maintainers can find the deploy trigger, validation gate, one-time Pages
  setting, retry path, rollback path, and DOC-012 handoff.

### Functional Requirements

- Define `.github/workflows/deploy-docs.yml` using standard GitHub Pages
  actions, least-privilege `contents: read`, `pages: write`, and
  `id-token: write`, and no repository secrets or custom deploy tokens.
- Validate docs with `pnpm --dir docs-site validate` before uploading the
  generated `docs-site/dist` artifact.
- Support `push` to `main` through explicit docs-impacting path filters and
  `workflow_dispatch` retry from `main`.
- Keep build/upload and deploy as separate jobs, prevent overlapping staging
  deploys, and surface dependency, validation, upload, and deployment failures.
- Preserve staging non-indexing through the Starlight robots meta guard,
  `docs-site/public/robots.txt`, and docs-quality validation.
- Keep repository Pages settings manual, with DOC-012 owning custom domain,
  base-path migration, and removal of the indexing guard.

### Success Criteria

- Maintainers can identify one deploy workflow that validates and publishes the
  docs staging site after docs-impacting changes reach `main`.
- Maintainers can retry the deploy workflow without creating a source-only
  retry commit.
- Reviewers can preview a successful staging deploy while the site still carries
  non-indexing policy.
- The runbook documents setup, retry, rollback, deployment-history evidence, and
  the DOC-012 public-launch boundary.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup after PR #243 merged.
The first post-merge `Deploy Docs` run failed because repository Pages was not
yet enabled/configured for GitHub Actions, which is the documented manual
operator prerequisite. Recovery commands and provenance are recorded in
`.specify/memory/archive-reports/2026-06-23-doc-011-post-merge-hygiene.md`.

## DOC-013 Brand Identity and Marketplace Landing Page

[Source: specs/doc-013-brand-identity-marketplace-landing]

### Summary

Applied the Racecraft visual identity to the `docs-site/` Astro + Starlight site
and turned the stock-Starlight home route into a real marketplace landing page —
brand colors, typography, wordmark/logo, and favicons applied consistently across
light and dark mode while staying WCAG AA accessible. Merged via PR #246
(`6a0516ff`).

### User Stories

- **US1 (P1) — Branded marketplace landing page**: A visitor on the docs home
  route sees a splash-style landing (logo/mark, benefit-led headline, plain-English
  value prop, ~3 value-prop cards, one primary CTA to the getting-started/first-run
  tutorial, one secondary "View on GitHub" CTA) rather than a generic doc article,
  and understands the product and where to start without scrolling — on desktop and
  mobile.
- **US2 (P2) — Consistent, accessible site-wide brand identity**: Every route
  (landing or interior) carries the brand accent on links/active-nav, the brand
  display/body/mono typefaces, the header wordmark, and the favicon set, coherent
  in light and dark mode, with all text/interactive elements meeting WCAG AA.

### Functional Requirements (highlights)

- Home route renders as a Starlight-native `template: splash` landing (no bespoke
  components); the above-the-fold set {logo, benefit headline, value prop, primary
  CTA} fits the first screen on desktop and mobile (FR-001/001a/002).
- Exactly one primary CTA (→ first-run tutorial) + one visually-subordinate
  secondary CTA (→ GitHub); no competing CTAs (FR-003/003a). 2–4 anti-hype
  value-prop cards, 3 by default (FR-004/004a).
- Palette mapped to Starlight `--sl-color-*`: blue accent for links/active-nav;
  red `#dc143c` reserved as punctuation (logo, theme-color, hero CTA fill) and
  **never** failing normal-size text; AA-safe `#2a6a99` link text (FR-005/005a/006).
- Five self-hosted woff2 faces only (Space Grotesk 400/700, Geist 400/600, Fira
  Code regular) with `font-display: swap`; only the two above-the-fold faces
  (Space Grotesk 700 + Geist 400) preloaded, each with `crossorigin` (FR-007/008).
- Light/dark wordmark in header (`replacesTitle`, accessible name preserved), brand
  favicon set + theme color, logomark hero image with explicit `alt` (FR-009/010/011).
- Dark reading surface is soft `#1a1a1a` (true black `#0a0a0a` scoped to the hero
  block only); near-white `#e6e6e6` dark body text; visible focus ring `#3c89c6`
  ≥3:1 both modes; reduced-motion respected (FR-013/014/014a/015).

### Key Entities

Brand color token set (red/blue/AA-safe blue/warm neutrals → accent/link/surface/
theme roles); brand typeface set (display/body/mono + shipped weights); brand logo
assets (light/dark wordmark, logomark, favicon set); landing-page content (hero
headline, value-prop, CTA targets, ~3 card titles/blurbs).

### Success Criteria

First-time comprehension above the fold on desktop and mobile (SC-001); 100% of
routes carry brand accent/typefaces/wordmark/favicon in both modes (SC-002); 100%
of brand-accent text/interactive elements meet WCAG AA against an enumerated ratio
table with red only in passing patterns (SC-003); soft-dark reading surface (SC-004);
no invisible-text font flash + lean local 5-woff2 set with 2 preloads (SC-005);
CTAs resolve with no broken links (SC-006); within reviewability budget, no
out-of-scope leakage (SC-007); docs-site build/validation pass + reduced-motion
honored (SC-008).

### Cleanup Note

Archived into project memory on 2026-06-24 (PR #246, `6a0516ff`). The active
`specs/doc-013-brand-identity-marketplace-landing/` folder was removed from
`specs/**` in the post-merge cleanup; only `specs/.gitkeep` remains. Recovery
commands and provenance are recorded in
`.specify/memory/archive-reports/2026-06-24-doc-013-post-merge-hygiene.md`.

## XPLAT-003 Supply-Chain Security and Consumer Trust Model

[Source: specs/xplat-003-supply-chain-security-and-consumer-trust-model]

### Summary

XPLAT-003 recorded the first-release supply-chain security and consumer-trust
model for the cross-platform runtime lane. It amended the active runtime
direction to a Python 3.11+ standard-library runner aligned with official Spec
Kit / `specify` prerequisites and rejected Go, Rust, Zig, native binaries, Bash,
Git Bash, WSL, PowerShell helper scripts, `jq`, Node, `pip install`, virtualenv
restore, and package restore as required installed-plugin runtime substrates.

The spec is decision/control only. It does not implement the runner, port helper
behavior, rebuild payloads, edit release automation, or make public native
platform claims. XPLAT-004 owns runner source/preflight/integrity controls;
XPLAT-007 owns Claude/Codex cutover, installed plugin UAT, update/autoheal proof,
latest tagged release verification, and public claim readiness.

### User Stories

- **US1 - Maintainer reviews trust baseline**: A maintainer can see which
  first-release controls block public runtime cutover and which hardening items
  stay deferred.
- **US2 - Implementer maps controls to owner specs**: An implementer can tell
  which controls belong in XPLAT-004, XPLAT-007, release automation, or public
  documentation.
- **US3 - Consumer understands local verification and limits**: A consumer can
  understand what an installed plugin can verify locally and which guarantees
  the project intentionally does not claim.

### Functional Requirements (highlights)

- Use Python 3.11+ stdlib as the only planned installed-plugin runtime
  substrate, through the official Spec Kit / `specify` prerequisite boundary.
- Require runner identity/preflight output, plugin-root detection, prerequisite
  checks, artifact-integrity pointers, and SHA-256 manifest/checksum evidence.
- Require source-to-dist drift checks, generated payload completeness evidence,
  install-completeness checks for Claude Code and Codex, and latest tagged
  release verification before public claims.
- Require doctor/autoheal behavior for scaffold/status/autopilot so stale or
  incomplete installs are detected and only safe gaps are auto-repaired.
- Require complete native Windows/macOS/Linux UAT evidence with readable
  runbooks before universal install/full-use claims.
- Treat signatures, SBOMs, provenance attestations, reproducible builds, formal
  audit, and cryptographic trust-chain verification as deferred hardening unless
  later promotion evidence exists.

### Success Criteria

XPLAT-003 is successful when XPLAT-004 can build the Python stdlib runner and
first-release controls without reopening the runtime/package decision, XPLAT-007
knows which installation and public-claim evidence is required, and consumers
receive accurate local verification guidance without overclaimed guarantees.

### Cleanup Note

Archived into project memory on 2026-06-29 (PR #267,
`1ab96b38da7e400b3c8e78b21d92e7b05302cfdd`). The active
`specs/xplat-003-supply-chain-security-and-consumer-trust-model/` folder was
removed from `specs/**` in the post-merge cleanup. Recovery commands and
provenance are recorded in
`.specify/memory/archive-reports/2026-06-29-xplat-003-post-merge-hygiene.md`.

## XPLAT-001 Runtime Inventory and Constraints

[Source: specs/xplat-001-runtime-inventory-constraints]

XPLAT-001 shipped a source-traceable runtime inventory and non-scoring runtime
and supply-chain rubrics for the cross-platform plugin runtime lane. The main
reviewable artifact is `docs/ai/research/cross-platform-runtime-inventory.md`.
It represented 21,162 scoped scan hits across shell substrate, script-file
references, JSON query usage, shell quoting/operators, Unix paths, file-mode
changes, and newline policy. It classified active installed-runtime findings,
generated payload references, public-doc claims, tests/fixtures, repository-only
tooling, and historical/archive material without selecting a replacement
runtime or changing installed invocation paths.

Cleanup note: archived on 2026-06-29 after PR #263 merged at
`a7f9ca97548ebe4b50cf84a19828d745471756a0`. The active
`specs/xplat-001-runtime-inventory-constraints/` folder was removed; recovery
commands are recorded in
`.specify/memory/archive-reports/2026-06-29-completed-active-specs-post-merge-hygiene.md`.

## XPLAT-002 Runtime Implementation Options and Contract Decision

[Source: specs/xplat-002-runtime-implementation-options-contract-decision]

XPLAT-002 shipped the amended runtime implementation decision and
`speckit-pro-runner` command contract. Python 3.11+ standard-library source is
the selected XPLAT implementation substrate because it aligns with official
Spec Kit / `specify` prerequisites. JavaScript/TypeScript and small
per-platform binaries remain historical rejected evidence only; compiled
binaries are not a fallback, compatibility adapter, or downstream
implementation input. The contract covers JSON stdin/stdout, deterministic
stderr diagnostics, exit-code categories, typed path values, shell-disabled
subprocess execution, and `runtime-info`/preflight behavior for XPLAT-004.

Cleanup note: archived on 2026-06-29 after PR #266 merged at
`fff4d6b5e7f4bf5ca85b2e55225417152b70b45f`. The active
`specs/xplat-002-runtime-implementation-options-contract-decision/` folder was
removed; recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-29-completed-active-specs-post-merge-hygiene.md`.

## DOC-014 SEO and AI Discoverability

[Source: specs/doc-014-seo-and-ai-discoverability]

DOC-014 shipped the docs-site discoverability baseline before public launch
while preserving the staging noindex guard. It added a dynamic three-tier
crawler-access policy, `starlight-llms-txt` whole-site digests, per-page
Markdown routes, JSON-LD route-data injection, per-page Open Graph cards,
git-backed sitemap freshness, visible last-updated behavior, meta descriptions
for all content pages, a quality gate requiring descriptions, focused SEO
Playwright coverage, and the AI-discoverability success metric document. DOC-012
still owns the public custom-domain/indexing launch; DOC-015 owns prose and
meta-description quality refresh.

Cleanup note: archived on 2026-06-29 after PR #264 merged at
`6c24f56885f09755dd85e0a451deb923e5ef437a`. The active
`specs/doc-014-seo-and-ai-discoverability/` folder was removed; recovery
commands are recorded in
`.specify/memory/archive-reports/2026-06-29-completed-active-specs-post-merge-hygiene.md`.
