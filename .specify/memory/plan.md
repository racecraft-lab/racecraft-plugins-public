# Project Memory: Implementation Plans

Durable, distilled record of merged feature implementation plans — dependencies,
structure, configuration, and test strategy. Appended per archived feature.

---

## Artifact relocation — tiering, .process/, collapse

[Source: specs/007-artifact-relocation]
**Branch**: `007-artifact-relocation` · **Status**: Completed · **Archived**: 2026-06-05

### Dependencies & Versions

- **Language/Runtime**: Bash (macOS/Linux) + `jq` for JSON. Python 3 only where
  `ensure-reviewability-preset.sh` already uses it (its heredoc). No compiled
  runtime — this is a Claude Code plugin marketplace, not an application.
- **Primary dependencies**: `git` (linguist reads repo-root `.gitattributes`),
  `jq`, GitHub linguist (`linguist-generated` collapse mechanism). No package
  manager, no Node/Rust/Go build.
- **Storage**: Files on disk. No database, no persisted state. Relocated exhaust
  lives under `docs/ai/specs/.process/` and `specs/<NNN>/.process/`.

### Architecture / Approach

- **US1 (redirect)**: path-string edits in markdown skill files plus identical
  mirrors in the Codex skill counterparts — no new abstraction layer.
- **US2 (collapse + gate + lint)**: one new repo-root `.gitattributes` rule
  (`**/.process/** linguist-generated=true`), one idempotent append into the
  consuming project's `.gitattributes` (folded into the existing scaffold-time
  `ensure-reviewability-preset.sh`, NOT a new script), one new `case` arm in the
  gate's `is_excluded_generated()`, and one new Layer-1 structural lint proving
  every `linguist-generated` rule is scoped to `.process/`.
- US2 is inert until US1 writes under `.process/`, so US1 sequences first.

### Files Touched (production)

- `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` + Codex mirror
  `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md` — redirect scaffold
  exhaust to `docs/ai/specs/.process/`.
- `speckit-pro/skills/speckit-coach/templates/workflow-template.md` — self-ref
  redirects.
- `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh` — repoint UAT
  read path + link to `specs/<NNN>/.process/`; keep `## UAT Runbook` rendering.
- `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` —
  UAT generator output path + git add → `.process/`.
- `.gitattributes` (NEW repo root) — single `**/.process/** linguist-generated=true`
  rule.
- `speckit-pro/skills/speckit-coach/scripts/ensure-reviewability-preset.sh` —
  idempotent safe-write append of the rule to the consumer's `.gitattributes`.
- `speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh` — one new
  `is_excluded_generated()` arm for `/.process/`.

### Configuration Changes

- New repository-root `.gitattributes` collapse rule (linguist-generated, NOT
  `-diff`). Mirrored idempotently into consumer repos by the scaffold ensure-step.

### Consumer `.gitattributes` Safe-Write (consensus-pinned)

The consumer ensure-step MUST:
1. Detect presence with `grep -qxF "$rule" "$file"` — fixed-string (`-F`, the rule
   contains `*` glob metacharacters), whole-line (`-x`) match; short-circuit if
   already present.
2. Normalize the trailing newline before appending (if last byte ≠ `\n`, add one)
   so the rule never silently concatenates onto the last existing line.
3. Write atomically: copy existing content into a SAME-DIRECTORY temp file
   (`mktemp "${file}.XXXXXX"` — same dir keeps `mv` atomic on macOS), append the
   rule, then `mv` over the target; `trap 'rm -f "$tmp"' EXIT` to avoid orphans.

~10 LOC, matches the repo's temp-then-rename convention, adds no new
script/abstraction (constitution Principle VI).

### Test Strategy

- Shell-script test layers via `bash speckit-pro/tests/run-all.sh`. CI runs
  Layers 1 (structural), 4 (script unit), 5 (tool scoping).
- NEW Layer-1 lint: `tests/layer1-structural/validate-process-gitattributes.sh`
  (modeled on `validate-pr-checks-sentinel.sh`), registered in the run-all.sh L1
  array — proves SC-005.
- EXTENDED `tests/unit/test-reviewability-gate.sh` — diff-mode:
  `.process/` excluded, spec counted (SC-003).
- EXTENDED `tests/unit/test-ensure-reviewability-preset.sh` —
  idempotency + safe-write of the consumer append (SC-004).
- Codex parity covered by the existing `validate-codex-skills.sh` + Layer-8 parity
  fixtures (SC-006).

### Constitution Compliance

PASS on all core principles (I–VI). One declared **split exception** for the
reviewability surface budget: the gate's `surface_for_path()` heuristic computes
≥2 primary surfaces purely from filenames (`workflow-template.md` → false
"scheduler/runtime"; `*.md` → "docs/process"; `.sh`/`.gitattributes` → "other"),
tripping the ">1 primary surface" blocker. This is one logical surface (the
speckit-pro PR-exhaust pathway) artificially sharded by filename patterns;
splitting US1/US2 would not lower the count (each half still touches `.sh` + `.md`).
The constitution-sanctioned `split exception` was ratified in plan.md (grepped by
the gate to clear the block). Not a core-principle violation.

### Known Gaps / Notes

- A pre-existing dead-code arm in the gate (`docs/ai/workflows/*/exports/*`, a
  directory that does not exist) was left untouched per the surgical-edit rule
  (mention, do not delete).
- `data-model.md`, `contracts/`, and `quickstart.md` were correctly N/A (no data
  model, no API, no user-facing runtime).
- Authoritative design rationale lived at `docs/ai/specs/PRSG-001-design-concept.md`
  (four-agent grounding pass + Q&A log); `research.md` was a thin pointer to it.

---

## Atomicity-test router (read-only classifier)

[Source: specs/prsg-007-atomicity-router]
**Branch**: `prsg-007-atomicity-router` · **Status**: Completed · **Archived**: 2026-06-09

### Dependencies & Versions

- Bash + `jq` only; no package manager or compiled build step.
- Reads local `tasks.md`, `plan.md`, and `spec.md`; no network, GitHub, or
  reviewability-gate dependency.

### Architecture / Approach

- One production script:
  `speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh`.
- Small duplicated surface/path matchers rather than a shared abstraction with
  `reviewability-gate.sh`.
- Autopilot documentation records the post-Tasks/G5 route handoff; Codex skill
  prose mirrors the Claude skill prose.

### Test Strategy

- `bash tests/speckit-pro/run-all.sh --layer 4` covers router fixtures and
  dogfood behavior.
- `bash tests/speckit-pro/run-all.sh --layer 1` covers structural and Codex
  parity checks.
- PR #133 CI recorded validate-plugins, test(speckit-pro), detect,
  validate-pr-title, and CodeQL as successful.

### Cleanup Notes

`specs/prsg-007-atomicity-router` was removed from active `specs/**` cleanup on
2026-06-09 after PR #136 moved the dogfood/schema tests to committed fixtures
independent of the active spec tree.

---

## Retro-migration: version marker + state-keyed backfill/relocate

[Source: specs/prsg-011-retro-migration]
**Branch**: `prsg-011-retro-migration` · **Status**: Completed · **Archived**: 2026-06-09

### Dependencies & Versions

- Bash + `jq` only; no package manager or compiled build step.
- Reuses `generate-spec-index.sh` and the MOC ID/frontmatter helper libraries.
- Mirrors archive-extension safety: dry-run/apply separation, clean-tree guards,
  backups, and recovery commands.

### Architecture / Approach

- `migrate-structure.sh`: repo-level structure marker, Tier-1 edits, and Tier-0
  navigation backfill.
- `relocate-process-artifacts.sh`: explicit Tier-2 relocation for thawed legacy
  specs only.
- `speckit-upgrade`, `speckit-scaffold-spec`, and `speckit-autopilot` document
  the new behavior; scaffold/autopilot suggest the codemod but never auto-run it.

### Test Strategy

- Layer 4 covers migration dry-run/apply, idempotency, dirty-tree failure,
  backup behavior, relocation allow-list, collisions, and ID normalization.
- Layer 3/8 fixtures cover Claude/Codex guidance parity for Tier-2 suggestions.
- PR #132 CI recorded validate-plugins, test(speckit-pro), detect, CodeQL, and
  code scanning as successful; `validate-pr-title` failed on the already-merged
  title and is recorded as a metadata gate exception.

### Cleanup Notes

The source spec folder was removed from active `specs/**` cleanup on 2026-06-09
after PR #136 decoupled Layer 4 dogfood/schema tests from the live PRSG-007
directory and the cleanup gate recorded `safeToApplyCleanup=true`.

---

## Layer-planner: tasks.md to ordered increments

[Source: specs/prsg-008-layer-planner]
**Branch**: `prsg-008-layer-planner` · **Status**: Completed · **Archived**: 2026-06-10

### Dependencies & Versions

- Bash + `jq` only; no package manager, compiled build step, Python runtime, or
  network dependency in the shipped planner.
- Reads a local feature directory's `tasks.md` and emits JSON to stdout.
- Autopilot orchestration persists successful layer-plan envelopes to existing
  workflow/state surfaces when the PRSG-007 route is exactly `split-PR`.

### Architecture / Approach

- One production script:
  `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh`.
- One schema-backed output contract under the archived PRSG-008 spec artifacts,
  with the Layer 4 test harness carrying a vendored schema fixture after cleanup.
- Deterministic Bash parsing of headings, checkbox tasks, dependency order,
  incremental delivery order, file/test references, and warning/error envelopes.
- Autopilot prose in Claude and Codex surfaces runs the planner only after
  post-G5 atomicity routing and before Analyze/implementation when route is
  `split-PR`; all other routes skip layer planning.

### Test Strategy

- `bash tests/speckit-pro/unit/test-plan-layers.sh` covers planner
  contract behavior and passed `66/66`.
- `bash tests/speckit-pro/run-all.sh --layer 4` passed `1029/1029`.
- `bash tests/speckit-pro/run-all.sh --layer 1` passed `887/887`.
- `bash tests/speckit-pro/run-all.sh` passed `2106/2106`.
- PR #138 post-merge main checks passed Release and CodeQL runs for merge commit
  `deccd8a2a9916e11edfad43df8ceef95a756dc04`.

### Cleanup Notes

`specs/prsg-008-layer-planner` was removed from active `specs/**` cleanup on
2026-06-10 after the planner schema was vendored under
`tests/speckit-pro/unit/fixtures/plan-layers/contracts/` and focused
planner tests passed from the fixture-backed schema.

---

## Multi-PR emission (post-implementation rewrite)

[Source: specs/prsg-009-multi-pr-emission]
**Branch**: `prsg-009-multi-pr-emission` · **Status**: Completed · **Archived**: 2026-06-11

### Dependencies & Versions

- Bash + `jq`, `git`, and GitHub CLI (`gh`); no package manager, compiled build
  step, Python runtime, or workflow CI changes in the shipped behavior.
- Reuses PRSG-008 layer-plan JSON as the only slice source and the existing
  `generate-spec-index.sh` sentinel generator for schema v2 PRS table rendering.
- `gh-stack` is optional and only used when safely detected for an existing
  active stack; explicit `gh pr create --base --head --body-file` remains the
  required PR creation path.

### Architecture / Approach

- `multi-pr-emission.sh`: validates layer-plan/state inputs, prepares slice
  branches and PR commands, writes candidate state/PRS/command JSON, supports
  fixture-backed PR reconciliation, persists successful slice PR state, and
  blocks on failed scoped verification before opening a PR.
- `generate-pr-body.sh --slice-packet <json-file>`: preserves the legacy
  positional path while adding reviewer-visible slice sections for scope,
  verification, traceability, restack/rollback, known gaps, and full regression
  evidence.
- `generate-spec-index.sh`: renders PRS schemaVersion 2 rows with order, slice,
  PR, status, branch, base, SHA, scope, and verification columns while keeping
  schema v1 compatibility.
- `restack.sh`: provides dry-run-first restack planning/apply behavior with
  deterministic JSON stdout, stable stderr diagnostics, and exit codes for
  success, conflicts, input error, dirty tree, and git/gh failure.
- Claude and Codex post-implementation references were updated together so the
  two runtime surfaces describe the same multi-PR emission contract.

### Test Strategy

- `bash tests/speckit-pro/unit/test-multi-pr-emission.sh` passed `81/81`.
- `bash tests/speckit-pro/unit/test-restack.sh` passed `32/32`.
- `bash tests/speckit-pro/unit/test-generate-pr-body.sh` passed `44/44`.
- `bash tests/speckit-pro/unit/test-generate-spec-index.sh` passed `86/86`.
- `bash tests/speckit-pro/run-all.sh` passed `2300/2300` after active spec cleanup.
- PR #145 CI recorded successful PR Checks, CodeQL, Release, `test(speckit-pro)`,
  `validate-plugins`, `validate-pr-title`, and `detect` for merge commit
  `a3361d50e3dfc5463fb2d5dbb2737a3525637a32`.

### Cleanup Notes

`specs/prsg-009-multi-pr-emission` was removed from active `specs/**` cleanup on
2026-06-11 after the PRSG-009 contract schemas were preserved under
`speckit-pro/skills/speckit-autopilot/contracts/` and the emitter's schema path
reporting was repointed to payload-included contracts.

---

## Harden the hatch + O5 monster-epics

[Source: specs/prsg-010-harden-the-hatch]
**Branch**: `prsg-010-harden-the-hatch` · **Status**: Completed · **Archived**: 2026-06-11

### Dependencies & Versions

- Bash + `jq`, `git`, and GitHub CLI (`gh`) at PR-emission boundaries; no package
  manager or compiled build step.
- Reuses PRSG-007 routing, PRSG-008 layer planning, PRSG-009 multi-PR emission,
  and SPEC-006a/b PR body/UAT evidence surfaces.
- Preserves Claude and Codex skill mirrors for autopilot, scaffold, and status
  guidance.

### Architecture / Approach

- `final-reviewability-backstop.sh`: wraps the final diff gate, blocks before PR
  body generation or PR creation when the gate blocks without an honored typed
  exception, and writes durable gate state plus a re-slicing packet.
- `atomicity-route.sh`: extends the routing decision with high-confidence
  contextual probes while preserving conservative fallback and closed enum
  signal/hint vocabularies.
- `o5-topology.sh`: validates O5 parent manifests, flat sibling child paths,
  dependency order, cycle rules, and computed read-only status rollup.
- Scaffold/status skill updates describe O5 as a fallback after ordinary O4
  split planning cannot produce reviewable slices.
- Template and roadmap guidance remove live generated exception boilerplate
  while still documenting accepted exception classes and provenance rules.

### Test Strategy

- `bash tests/speckit-pro/unit/test-final-reviewability-backstop.sh`
  passed `31/31`.
- `bash tests/speckit-pro/unit/test-atomicity-route.sh` passed
  `109/109`.
- `bash tests/speckit-pro/unit/test-o5-topology.sh` passed `25/25`.
- `bash tests/speckit-pro/unit/test-generate-spec-index.sh` passed
  `87/87`.
- `bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run --fixture 03-reviewability-backstop-parent-child-routing`
  passed `3/3`.
- Post-cleanup `bash tests/speckit-pro/run-all.sh` verification is recorded in
  `.specify/memory/archive-reports/2026-06-11-prsg-010-post-merge-hygiene.md`.

### Cleanup Notes

`specs/prsg-010-harden-the-hatch` was removed from active `specs/**` cleanup on
2026-06-11 after PRs #149-#155 merged and the PRSG-010 contract schemas were
preserved under `speckit-pro/skills/speckit-autopilot/contracts/`.

---

## Vertical-slice sizing heuristics in PRD/grill-me

[Source: specs/prsg-005-slice-sizing-heuristics]
**Branch**: `prsg-005-slice-sizing-heuristics` · **Status**: Completed · **Archived**: 2026-06-12

### Dependencies & Versions

- Bash plus `jq`; no package manager or compiled build step.
- Applies to Claude and Codex `speckit-prd` and `grill-me` skill mirrors.
- Feeds the existing roadmap `Projected reviewable LOC` field without adding a
  new roadmap schema.

### Architecture / Approach

- `estimate-spec-size.sh` provides the shared deterministic advisory estimator.
- `slicing-heuristics.md` is the single source of truth for SPIDR, INVEST, and
  vertical-slicing guidance.
- `speckit-prd` applies the guidance at catalog-authoring time.
- `grill-me` applies the same sizing branch to single-spec scoping and records
  the chosen split for later scaffold/autopilot phases.

### Test Strategy

- PR #120 passed PR Checks, CodeQL, `test(speckit-pro)`,
  `validate-plugins`, `validate-pr-title`, and `detect`.
- Task evidence records `20/23` implementation tasks complete, with Layer 2,
  Layer 3, and Layer 8 developer-local follow-ups intentionally not required as
  merge blockers.
- Post-cleanup verification is recorded in
  `.specify/memory/archive-reports/2026-06-12-prsg-005-013-post-merge-hygiene.md`.

### Cleanup Notes

`specs/prsg-005-slice-sizing-heuristics` was removed from active `specs/**`
cleanup on 2026-06-12 after PR #120 merged and archive recovery commands were
recorded.

---

## Non-stopping reviewability markers

[Source: specs/prsg-013-reviewability-markers]
**Branch**: `prsg-013-reviewability-markers` · **Status**: Completed · **Archived**: 2026-06-12

### Dependencies & Versions

- Bash plus `jq`, `git`, and GitHub CLI at PR-emission boundaries.
- Builds on PRSG-008 layer planning, PRSG-009 multi-PR emission, and PRSG-010
  final reviewability backstop ordering.
- Preserves Claude and Codex autopilot guidance parity.

### Architecture / Approach

- `plan-layers.sh` adds marker-aware planning and persisted source
  fingerprints.
- `final-reviewability-backstop.sh` consumes valid marker plans and returns a
  `marker_split` proceed outcome for full-diff size blocks.
- `multi-pr-emission.sh` validates marker packets, emits scoped marker packets,
  and supports hazard-collapsed full-spec output.
- Workflow/state evidence records marker order, checkpoint expectations,
  warnings, final backstop evidence, and PR-emission mapping.

### Test Strategy

- PR #157 passed PR Checks, CodeQL, `test(speckit-pro)`,
  `validate-plugins`, `validate-pr-title` after title repair, and `detect`.
- Autopilot evidence records the default deterministic suite passing
  `2587/2587` before merge.
- Post-cleanup verification is recorded in
  `.specify/memory/archive-reports/2026-06-12-prsg-005-013-post-merge-hygiene.md`.

### Cleanup Notes

`specs/prsg-013-reviewability-markers` was removed from active `specs/**`
cleanup on 2026-06-12 after PR #157 merged and PRSG-013 contracts/fixtures were
preserved under the autopilot payload and Layer 4 fixtures.

---

## Merged active-spec archive hygiene sweep

[Source: .specify/memory/archive-reports/2026-06-13-merged-specs-post-merge-hygiene.md]
**Branch**: `codex/archive-merged-specs-hygiene` · **Status**: Completed · **Archived**: 2026-06-13

### Scope

This sweep archived and removed the remaining active `specs/**` folders whose
implementation had already merged:

- SPEC-001 repository foundation, SPEC-002 PR checks, SPEC-003 release
  automation, SPEC-004 integration/verification, and SPEC-006a UAT skeleton.
- PRSG-002 MOC templates, PRSG-003 generated spec index, PRSG-004 roadmap-MOC
  home note, PRSG-006 reviewability budget, and PRSG-012 reviewer-ready PR
  packet contract.

### Architecture / Approach

- Treat merge commits as the archive source of truth, with explicit recovery
  commands in the archive report.
- Preserve historical workflow docs under `docs/ai/specs/` and
  `docs/ai/specs/.process/`; remove only active merged `specs/**` folders.
- Decouple tests from live spec folders before cleanup:
  - MOC lints now use committed fixture-backed dogfood assertions instead of
    reading `specs/prsg-002-moc-templates/SPEC-MOC.md`.
  - PRSG-012 PR body and marker-emission regression tests now read vendored
    fixtures under `tests/speckit-pro/unit/fixtures/`.
  - SPEC-006a already used the vendored full-spec snapshot fixture.
- Regenerate generated roadmap-MOC INDEX content after active spec removal so
  generated links do not point to archived spec folders.

### Test Strategy

- Pre-cleanup fixture verification:
  - `bash tests/speckit-pro/unit/test-generate-pr-body.sh` passed
    `85/85`.
  - `bash tests/speckit-pro/unit/test-multi-pr-emission.sh` passed
    `156/156`.
  - `bash tests/speckit-pro/layer1-structural/validate-moc-stale-index.sh`
    passed `11/11`.
  - `bash tests/speckit-pro/layer1-structural/validate-moc-orphan.sh` passed
    `29/29`.
- Post-cleanup `bash tests/speckit-pro/run-all.sh` passed `2915/2915`
  (Layer 1 structural `549/549`, Codex structural `430/430`, Layer 4 script
  unit `1746/1746`, Layer 5 tool scoping `190/190`).

### Cleanup Notes

`specs/001-repository-foundation`, `specs/002-pr-checks-workflow`,
`specs/003-release-automation`, `specs/004-integration-verification`,
`specs/006a-uat-skeleton`, `specs/prsg-002-moc-templates`,
`specs/prsg-003-spec-index`, `specs/prsg-004-roadmap-moc-home-note`,
`specs/prsg-006-reviewability-budget`, and
`specs/prsg-012-reviewer-ready-pr-packet-contract` were removed from active
`specs/**` cleanup after provenance, recovery commands, and fixture
decoupling were recorded.

---

## DOC-001 interactive documentation framework and IA spike

[Source: .specify/memory/archive-reports/2026-06-13-doc-001-post-merge-hygiene.md]
**Branch**: `codex/doc-001-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-13

### Scope

DOC-001 was a research-only spike. It selected Astro/Starlight, recorded
report-only DOC-002 package/build/test command roles, and produced the route
level IA handoff for the interactive documentation roadmap.

### Architecture / Approach

- Keep the durable recommendation in
  `docs/ai/research/interactive-documentation-framework-spike.md`.
- Treat the merged PR #163 commit as the recovery authority for raw SpecKit
  artifacts under `specs/doc-001-static-docs-framework-and-ia-spike/**`.
- Preserve DOC-001 workflow/process notes under `docs/ai/specs/.process/`.
- Remove only the completed active spec folder from `specs/**`.
- Mark DOC-001 complete in the interactive documentation roadmaps and
  traceability matrix so DOC-002 can start from the accepted Astro/Starlight
  recommendation and IA skeleton.
- Regenerate the roadmap-MOC generated INDEX after removing the active spec
  folder so generated links do not point to archived specs.

### Test Strategy

- Verify JSON state files parse.
- Verify no active `specs/**` feature directories remain after cleanup.
- Verify no generated roadmap-MOC link points at the removed DOC-001 spec
  folder.
- Run `bash tests/speckit-pro/run-all.sh` after cleanup.

### Cleanup Notes

`specs/doc-001-static-docs-framework-and-ia-spike` was removed from active
`specs/**` cleanup after PR #163 merged. No test fixture or production script
depended on the live DOC-001 spec folder.

---

## DOC-002 Unified Landing Page and IA Shell

[Source: .specify/memory/archive-reports/2026-06-14-doc-002-post-merge-hygiene.md]
**Branch**: `codex/doc-002-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-14

### Scope

DOC-002 converted the DOC-001 Astro/Starlight recommendation and route-level IA
handoff into a concrete docs-site shell. It created the `docs-site/` package,
config, lockfile, content collection, landing page, 11 route shells, sidebar
groups, Pages-ready base path, and link-validation scripts.

### Architecture / Approach

- Use Astro with Starlight under `docs-site/`.
- Keep root README and plugin README as source evidence only.
- Use Pages-base absolute links for GitHub Pages compatibility and
  `starlight-links-validator` compatibility.
- Keep shell content skeletal where DOC-003 through DOC-010 own full content.
- Preserve the source tree versus generated install payload distinction on the
  landing/reference surfaces.

### Test Strategy

- `cd docs-site && pnpm check`
- `cd docs-site && pnpm build`
- `cd docs-site && pnpm validate:links`
- `cd docs-site && pnpm validate`
- In-app browser UAT across all 11 docs routes.
- `bash tests/speckit-pro/run-all.sh`

### Cleanup Notes

`specs/doc-002-unified-landing-page-and-ia-shell` was removed from active
`specs/**` cleanup after PRs #173-#177 merged. The original T041 PR-packet task
remains a historical unchecked task because PR #177 fixed the autopilot
continuation bug that caused the packet path to pause.

---

## PRSG-014 Optional gh-stack stack manager integration

[Source: .specify/memory/archive-reports/2026-06-14-prsg-014-post-merge-hygiene.md]
**Branch**: `codex/post-merge-archive-hygiene` · **Status**: Completed · **Archived**: 2026-06-14

### Scope

PRSG-014 added optional stack-manager support for autopilot create/sync/restack
flows while preserving explicit `gh pr create/edit --base --head` as the
deterministic fallback path.

### Architecture / Approach

- Add one shared `detect-stack-manager.sh` script used by both emission and
  restack flows.
- Persist stack-manager decisions through `stack-manager-decision.schema.json`
  and evidence paths under feature/workflow `.process` directories.
- Select `gh-stack` only after command availability, version/support, read-only
  proof, and topology compatibility checks pass.
- Fall back to explicit `gh` before mutation for missing, unsupported,
  ambiguous, unsafe, or topology-incompatible environments.
- Block with recoverable state after partial or unknown `gh-stack` mutation
  instead of switching managers and risking duplicate or divergent PR topology.
- Keep Codex and Claude guidance in parity while sharing scripts and contracts.

### Test Strategy

- Focused Layer 4 tests: `test-detect-stack-manager` 18/18,
  `test-multi-pr-emission` 159/159, `test-restack` 33/33.
- Broader recorded verification: Layer 1 979/979, Layer 4 1768/1768, Layer 7
  fixtures, Layer 8 parity 12/12, and default suite 2937/2937 before PR #181.
- Post-cleanup validation regenerates Spec-MOC indexes and reruns the default
  deterministic suite.

### Cleanup Notes

`specs/prsg-014-optional-gh-stack-stack-manager-integration` was removed from
active `specs/**` cleanup after PR #181 merged. Recovery commands and provenance
are recorded in the PRSG-014 archive report.

---

## DOC-003 and DOC-004 platform install paths

[Source: .specify/memory/archive-reports/2026-06-15-doc-003-004-post-merge-hygiene.md]
**Branch**: `codex/doc-003-004-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-15

### Scope

DOC-003 and DOC-004 completed the platform-specific install tier for the
interactive documentation roadmap. DOC-003 owns the Claude Code install route;
DOC-004 owns the Codex install route, README alignment, generated payload
documentation sync, and Codex custom-agent registration guidance.

### Architecture / Approach

- Keep `docs-site/src/content/docs/install/claude-code.md` and
  `docs-site/src/content/docs/install/codex.md` structurally aligned while
  preserving platform-specific commands and trust boundaries.
- Retain historical workflow/process evidence under `docs/ai/specs/.process/`.
- Record recovery commands before removing active spec folders.
- Regenerate the roadmap-MOC generated INDEX after cleanup so active links do
  not point at archived spec folders.

### Test Strategy

- Confirm PR #187 and PR #186 are merged to `main`.
- Validate JSON state files after rewriting archive state.
- Regenerate and check SpecKit generated indexes.
- Verify active `specs/**` contains only `specs/.gitkeep` after cleanup.
- Run docs-site validation and the deterministic SpecKit test suite.

### Cleanup Notes

`specs/doc-003-claude-code-marketplace-installation-path` and
`specs/doc-004-codex-marketplace-installation-path` were removed from active
`specs/**` cleanup after PR #187 and PR #186 merged. Recovery commands and
provenance are recorded in the DOC-003/DOC-004 archive report.

---

## DOC-005 first successful workflow tutorial and lifecycle explainer

[Source: .specify/memory/archive-reports/2026-06-16-doc-005-post-merge-hygiene.md]
**Branch**: `codex/doc-005-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-16

### Scope

DOC-005 completed the first-run tier for the interactive documentation roadmap.
It owns the canonical first successful workflow tutorial, lifecycle explainer,
static lifecycle flow component, platform-separated command examples, validated
Codex Spec Kit init snippet, prerequisite checks, first-success checkpoints,
and bounded fallback handoffs.

### Architecture / Approach

- Keep first-run tutorial content in `docs-site/src/content/docs/first-run.md`.
- Keep phase, artifact, and gate explanation in
  `docs-site/src/content/docs/spec-kit-lifecycle.mdx`.
- Render the lifecycle visualizer through
  `docs-site/src/components/LifecycleFlow.astro` as static semantic HTML.
- Treat install pages, `speckit-pro/README.md`, and skill entrypoints as source
  evidence without editing plugin runtime or generated payload surfaces.
- Preserve detailed recovery commands for the residual DOC-005 PR-packet
  evidence before removing it from active `specs/**`.
- Regenerate and check the roadmap-MOC generated INDEX after cleanup.

### Test Strategy

- Confirm PRs #198, #199, #200, and #201 are merged to `main`.
- Validate JSON state files after replacing stale archive state.
- Regenerate and check SpecKit generated indexes.
- Verify active `specs/**` contains only `specs/.gitkeep` after cleanup.
- Run docs-site validation, docs-site link validation, and the deterministic
  SpecKit test suite.

### Cleanup Notes

Residual DOC-005 process evidence under
`specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer` was
removed from active `specs/**` cleanup after PRs #198-#201 merged. Recovery
commands and provenance are recorded in the DOC-005 archive report.

---

## DOC-006 safe interactive selector and validation aids

[Source: .specify/memory/archive-reports/2026-06-17-doc-006-post-merge-hygiene.md]
**Branch**: `codex/doc-006-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-17

### Scope

DOC-006 completed the safe interactive aid tier for the interactive
documentation roadmap. It owns the canonical choose-your-path selector/checker
experience, source-derived safe install metadata helper, accessible generated
payload diagram, first-run checklist, and focused validation harness.

### Architecture / Approach

- Preserve the public choose-your-path route while converting the content source
  to MDX for component placement.
- Render complete static fallback content through
  `docs-site/src/components/SafeInstallAids.astro`.
- Read checked-in repository and generated payload manifests during docs build
  through `docs-site/src/data/safe-install-aids.ts`.
- Keep command sequences, prerequisites, success signals, and handoffs in a
  small docs metadata helper while using manifest-derived values for
  repository consistency facts.
- Validate command boundaries, checker states, safety constraints, handoffs, and
  first-run checkpoint coverage through
  `docs-site/scripts/validate-doc006-safe-aids.mjs`.

### Test Strategy

- Confirm PR #203 merged to `main`.
- Validate JSON state files after replacing active autopilot state.
- Regenerate and check SpecKit generated indexes.
- Verify active `specs/**` contains only `specs/.gitkeep` after cleanup.
- Run DOC-006 focused validation, docs-site validation, docs-site link
  validation, and the deterministic SpecKit test suite.

### Cleanup Notes

`specs/doc-006-safe-interactive-selector-and-validation-aids` was removed from
active `specs/**` cleanup after PR #203 merged. Recovery commands and
provenance are recorded in the DOC-006 archive report.

## DOC-007 command, workflow, manifest, and file-layout reference

[Source: .specify/memory/archive-reports/2026-06-17-doc-007-post-merge-hygiene.md]
**Branch**: `codex/doc-007-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-17

### Scope

DOC-007 completed the reference-library tier for the interactive documentation
roadmap. It owns generated reference pages for skills, agents, manifests,
hooks, scripts, tests, and source-vs-dist layout, plus the deterministic
generator and reference check used by docs validation.

### Architecture / Approach

- Build reference pages from checked-in source files rather than hand-copying
  large inventories into docs content.
- Keep one generator at `docs-site/scripts/generate-reference-pages.mjs`.
- Write generated Markdown under `docs-site/src/content/docs/reference/`.
- Use source citations and inferred notes so reference pages distinguish
  repository facts from practical guidance.
- Link install, first-run, lifecycle, and safe-path docs into generated
  reference anchors.
- Add the `speckit-archive-cleanup` plugin skill so future post-merge archive
  hygiene follows this same branch, memory, cleanup, generation, and
  verification pattern.

### Test Strategy

- Confirm PR #208 merged to `main`.
- Validate JSON state after replacing active DOC-007 autopilot state.
- Regenerate and check SpecKit generated indexes.
- Verify active `specs/**` contains only expected active specs after cleanup.
- Regenerate and check docs-site reference pages.
- Rebuild generated plugin payloads after adding the new skill.
- Run docs-site validation, docs-site link validation, and the deterministic
  SpecKit test suite.

### Cleanup Notes

`specs/doc-007-command-workflow-manifest-and-file-layout-reference` was removed
from active `specs/**` cleanup after PR #208 merged. Recovery commands and
provenance are recorded in the DOC-007 archive report.

## TACD-001 Platform Mechanics Spike

[Source: .specify/memory/archive-reports/2026-06-18-tacd-001-post-merge-hygiene.md]
**Branch**: `codex/tacd-001-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-18

### Scope

TACD-001 completed the platform-risk discovery tier for the
tool-agnostic capability discovery roadmap. It owns the canonical spike report
and downstream handoffs for active agent guidance, prerequisite/user-facing
messaging, and enforcement coverage.

### Architecture / Approach

- Keep TACD-001 report-only: no active runtime guidance, prerequisite behavior,
  generated payload semantics, or final enforcement tests changed in the spike.
- Use local source evidence first, with sanitized probe summaries only where
  source inspection is insufficient.
- Classify named optional-tool references by category rather than using a broad
  string ban.
- Select a shared capability-discovery reference with runtime-specific pointers
  and approved equivalents as the downstream directive structure.
- Leave agent behavior changes to TACD-002, prerequisite/docs messaging to
  TACD-003, and static/eval enforcement to TACD-004.

### Test Strategy

- Confirm PRs #211-#214 and #216 merged to `main`.
- Validate JSON state after replacing active TACD-001 autopilot state.
- Regenerate and check SpecKit generated indexes after active spec removal.
- Verify active `specs/**` contains only expected active specs after cleanup.
- Run `git diff --check` and the deterministic SpecKit test suite.

### Cleanup Notes

`specs/tacd-001-platform-mechanics-spike` was removed from active `specs/**`
cleanup after the canonical report landed at
`docs/ai/research/tool-agnostic-capability-discovery-spike.md` and PR #216
updated the PRD/roadmap to adopt the spike decisions. Recovery commands and
provenance are recorded in the TACD-001 archive report.

## TACD-002 Capability Discovery Directive and Agent Updates

[Source: .specify/memory/archive-reports/2026-06-18-tacd-002-post-merge-hygiene.md]
**Branch**: `codex/tacd-002-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-18

### Scope

TACD-002 completed the active agent-behavior tier for the tool-agnostic
capability discovery roadmap. It owns the shared capability-discovery directive,
Claude and Codex runtime guidance updates, source-derived generated payloads,
and marker-emission hardening required to finish the sliced PR stack.

### Architecture / Approach

- Keep one shared source directive at
  `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`.
- Point Claude agent bodies to the directive and use approved compact
  equivalents in installed Codex TOML agents where direct pointers are not
  stable.
- Preserve exact named IDs only in schema metadata, historical/provenance text,
  or generated runtime evidence.
- Regenerate Claude and Codex payload roots from source through
  `bash scripts/build-plugin-payloads.sh`; do not treat `dist/**` as durable
  source.
- Separate marker-emission source feature directory from emitted branch prefix
  so existing parent branch refs no longer block ordered slice PR creation.
- Leave TACD-003 prerequisite/user-facing messaging and TACD-004 deterministic
  enforcement as separate roadmap specs.

### Test Strategy

- Confirm PRs #221-#226 merged to `main`.
- Validate JSON state after replacing active TACD-002 autopilot state.
- Regenerate and check SpecKit generated indexes after active spec removal.
- Verify active `specs/**` contains only expected active specs after cleanup.
- Run `git diff --check` and the deterministic SpecKit test suite.

### Cleanup Notes

`specs/tacd-002-capability-discovery-directive-and-agent-updates` was removed
from active `specs/**` cleanup after the shared directive, runtime guidance,
generated payloads, marker-emission hardening, and tests landed through PRs
#221-#226. Recovery commands and provenance are recorded in the TACD-002
archive report.

## DOC-008 and DOC-009 Interactive Documentation Post-Merge Archive Hygiene

[Source: .specify/memory/archive-reports/2026-06-18-doc-008-009-post-merge-hygiene.md]
**Branch**: `codex/doc-specs-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-18

### Scope

DOC-008 and DOC-009 completed the remaining trust and maintenance content tier
for the interactive documentation roadmap. DOC-008 owns troubleshooting,
security/trust, update, and rollback guidance. DOC-009 owns the maintainer and
contributor release workflow route. DOC-010 is the next ready docs hardening
slice after these content specs are archived.

### Architecture / Approach

- Keep the cleanup post-merge and archive-only: preserve process evidence under
  `docs/ai/specs/.process/`, remove only the completed active `specs/**`
  folders, and record recovery commands against the merge commits.
- Treat docs-site pages as the canonical shipped artifacts:
  `troubleshooting.md`, `security-and-trust.md`, `update-and-rollback.md`,
  install/reference routes, and `contribute-and-release.md`.
- Update roadmap and traceability state so DOC-008 and DOC-009 are completed
  and DOC-010 is ready to scaffold.
- Regenerate SpecKit indexes after active spec removal so roadmap MOCs no
  longer link to archived spec folders.
- Harden the spec-index generator and generated payload copies for the
  zero-active-spec cleanup state, where `specs/**` contains only
  `specs/.gitkeep` and roadmap-MOC generated zones must clear
  deterministically.

### Test Strategy

- Confirm PR #220 and PR #219 merged to `main`.
- Validate JSON state after replacing archive state.
- Regenerate and check SpecKit generated indexes after active spec removal.
- Verify active `specs/**` contains only `specs/.gitkeep` after cleanup.
- Run focused generator regression coverage for zero active spec directories.
- Run `git diff --check` and the deterministic SpecKit test suite.

### Cleanup Notes

`specs/doc-008-troubleshooting-security-trust-update-rollback` and
`specs/doc-009-maintainer-contributor-release-workflow` were removed from active
`specs/**` cleanup after their docs-site content landed through PR #220 and PR
#219. Recovery commands and provenance are recorded in the DOC-008/DOC-009
archive report.

## TACD-003 Prerequisite and Documentation Messaging

[Source: .specify/memory/archive-reports/2026-06-19-tacd-003-post-merge-hygiene.md]
**Branch**: `codex/tacd-003-archive-cleanup` · **Status**: Completed · **Archived**: 2026-06-19

### Scope

TACD-003 completed the prerequisite/user-facing messaging tier for the
tool-agnostic capability discovery roadmap. It owns the generic
`capability_coverage` advisory, active prerequisite and limitation guidance,
coach/autopilot messaging, source-derived generated payload refresh, and focused
regression tests.

### Architecture / Approach

- Keep `check-prerequisites.sh` JSON-only and deterministic.
- Replace the named optional MCP inventory with one successful advisory whose
  details name capability categories.
- Preserve true prerequisites as blockers and keep optional capability absence
  as confidence-impacting guidance.
- Update active Claude and Codex guidance in source files first, then refresh
  generated payloads from those source changes.
- Keep broad static/eval enforcement separate for TACD-004.

### Test Strategy

- Confirm PR #230 merged to `main`.
- Validate JSON state after replacing active TACD-003 autopilot state.
- Regenerate and check SpecKit generated indexes after active spec removal.
- Verify active `specs/**` contains only expected active specs after cleanup.
- Run `git diff --check` and the deterministic SpecKit test suite.

### Cleanup Notes

`specs/tacd-003-prerequisite-and-documentation-messaging` was removed from
active `specs/**` cleanup after the prerequisite advisory, active guidance,
generated payloads, focused tests, and PR packet evidence landed through PR
#230. Recovery commands and provenance are recorded in the TACD-003 archive
report.

## DOC-010 Interactive Documentation Quality Hardening

[Source: .specify/memory/archive-reports/2026-06-19-doc-010-post-merge-hygiene.md]
**Branch**: `codex/archive-doc-tacd-completed-work` · **Status**: Completed · **Archived**: 2026-06-19

### Scope

DOC-010 completed the final hardening tier for the interactive documentation
roadmap. It owns search/findability improvements, stable deep links, accessible
interactive-aid behavior, responsive/static fallback evidence, one local docs
validation path, a conditional PR Checks docs gate, and compact desktop/mobile
Playwright smoke coverage.

### Architecture / Approach

- Reuse the existing Astro/Starlight docs-site stack and Starlight/Pagefind
  search behavior instead of adding a new search provider or docs-quality route.
- Keep validation inside existing docs-site and PR Checks surfaces:
  `pnpm --dir docs-site validate`, focused safe-aids/docs-quality validators,
  generated reference checks, Astro checks, build/link validation, and
  representative Playwright smoke.
- Add job-level `validate-docs` changed-file detection in PR Checks so docs-site
  validation runs for rendered docs, generated-reference source, and
  docs-validation contract changes without forcing unrelated plugin matrix jobs.
- Keep browser smoke bounded to six logical routes, two viewports, one search
  sample, representative deep links, and focused `SafeInstallAids` /
  `LifecycleFlow` checks.
- Treat screenshots and Playwright reports as short-retention review artifacts,
  not committed durable archive payload.

### Test Strategy

- Confirm PRs #232 through #236 merged to `main`.
- Validate JSON state after replacing active DOC-010 autopilot state.
- Regenerate and check SpecKit generated indexes after active spec removal.
- Verify active `specs/**` contains only `specs/.gitkeep` after cleanup.
- Run `git diff --check` and the deterministic SpecKit test suite.

### Cleanup Notes

`specs/doc-010-search-accessibility-deep-links-docs-validation` was removed
from active `specs/**` cleanup after the docs-site validation path, support
anchors, accessibility/fallback updates, PR Checks docs gate, compact smoke
coverage, and PR packet evidence landed through PRs #232 through #236. Recovery
commands and provenance are recorded in the DOC-010 archive report.

## TACD-004 Verification Coverage

### Scope

Add deterministic verification (Layer 5 named-tool guard + Layer 1
pointer-coverage/target-resolution) and rewritten functional evals that lock the
vendor-neutral optional-tool contract, and fix the `strip_codex_guard` payload
defect with a body-completeness guard. Extend Layers 1/4/5 in place; no new test
layer, no agent-behavior or docs-wording changes.

### Architecture / Approach

- Named-tool guard lives in Layer 5; pointer-coverage and target-resolution in
  Layer 1; behavior expectations in the four eval files.
- The pointer rule is a literal path match to `capability-discovery.md` plus a
  small enumerated approved-equivalent allowlist (empty by design).
- The payload-completeness guard anchors on a structural invariant (last
  non-guard source heading present) rather than an absolute line count.
- `strip_codex_guard` strips from `## Codex Skill-Selection Guard` to the next
  heading or EOF; `dist/` is rebuilt from source.

### Test Strategy

- Confirm PR #240 merged to `main`.
- Validate JSON state after replacing the active autopilot state.
- Regenerate and check SpecKit generated indexes after active spec removal.
- Verify active `specs/**` contains only `specs/.gitkeep` after cleanup.
- Run `git diff --check` and `bash tests/speckit-pro/run-all.sh`.

### Cleanup Notes

`specs/tacd-004-verification-coverage` was removed from active `specs/**`
cleanup after the verification guards, the `strip_codex_guard` fix, rebuilt
payloads, and rewritten evals landed through PR #240. Recovery commands and
provenance are recorded in the TACD-004 archive report.

## DOC-011 GitHub Pages Build-And-Deploy Pipeline

### Scope

Ship the staging GitHub Pages deployment foundation for the existing
Astro/Starlight docs site without expanding into public launch. DOC-011 owns the
deploy workflow, validation-before-upload gate, staging noindex/robots guard,
operator runbook, PR workflow lint coverage, release docs-reference runtime
alignment, and the shared roadmap-MOC index guard hardening discovered during
review.

### Architecture / Approach

- Use standard GitHub Pages Actions in `.github/workflows/deploy-docs.yml`
  rather than a custom deploy script or API-based repository setting mutation.
- Run the existing docs validation path, `pnpm --dir docs-site validate`, before
  uploading `docs-site/dist` as the Pages artifact.
- Keep Pages setup manual in repository settings and document it in
  `docs/ai/specs/cicd-release-pipeline-verification.md`.
- Preserve the current GitHub Pages project-site URL/base assumptions and keep
  `noindex,nofollow` plus `robots.txt` staging protection until DOC-012.
- Add checksum-pinned `actionlint` coverage in PR Checks and keep deploy-related
  workflow changes inside the plugin structural validation trigger surface.
- Keep the shared `generate-spec-index.sh` guard fix in source, synced `dist/**`
  payload copies, and focused tests.

### Test Strategy

- Confirm PR #243 merged to `main`.
- Validate JSON state after replacing the active DOC-011 autopilot state.
- Regenerate and check SpecKit generated indexes after active spec removal.
- Verify active `specs/**` contains only `specs/.gitkeep` after cleanup.
- Run `git diff --check` and `bash tests/speckit-pro/run-all.sh`.
- Record the post-merge `Deploy Docs` failure as an operational Pages setup
  prerequisite until repository Settings -> Pages is configured for GitHub
  Actions.

### Cleanup Notes

`specs/doc-011-github-pages-build-and-deploy-pipeline` was removed from active
`specs/**` cleanup after the deploy workflow, staging indexing guards, CI/CD
runbook, workflow lint gate, release runtime alignment, shared index generator
hardening, synced payloads, tests, and PR packet evidence landed through PR
#243. Recovery commands and provenance are recorded in the DOC-011 archive
report.

## DOC-013 Brand Identity and Marketplace Landing Page

[Source: specs/doc-013-brand-identity-marketplace-landing]

### Dependencies and Environment

- **Runtime/build**: Docs-site JavaScript ESM on Node >=22.12 (nvm `v22.22.2`);
  CSS + Markdown/MDX. No application source language.
- **Primary dependencies**: Astro 6.4.6, Starlight 0.40.0, `starlight-links-validator`
  0.24.1 (all existing); pnpm 10.25.0 via `pnpm --dir docs-site …`. **No new runtime
  dependency** — brand fonts copied verbatim (no subsetting toolchain added).
- **Storage**: checked-in repository files only (CSS, MDX, SVG, woff2, favicon
  PNG/ICO, `site.webmanifest`). No database, browser storage, or runtime state.
- **Target**: static GitHub Pages site under `base: '/racecraft-plugins-public'`,
  `trailingSlash: 'always'`; modern browsers, light + dark mode.

### Architecture / Structure

All changes live under the existing `docs-site/` tree. One new stylesheet
(`src/styles/brand.css`) carries the bulk of the reviewable LOC; `astro.config.mjs`
is edited to wire `customCss`/`logo`/`favicon`/`head` preload+favicon+theme tags;
`src/content/docs/index.mdx` is rewritten to a Starlight-native `template: splash`
+ `hero` + `<CardGrid>`. Brand assets are ported verbatim from `landing-page/website`:
3 logo SVGs → `src/assets/`, 5 woff2 → `public/fonts/`, 10 favicon/manifest files →
`public/` (alongside the existing `robots.txt`, untouched). Two production text
files + one config file + 18 binary assets; `src/styles/` is the only new subdir.

### Testing Strategy

`pnpm --dir docs-site validate` (Astro check + `starlight-links-validator` build +
safe-aids + docs-quality + Playwright smoke-preview) is the gate, run by CI
`validate-docs`. The repo deterministic suite `bash tests/speckit-pro/run-all.sh`
is unaffected (no `speckit-pro/` or `tests/` files touched). PR evidence includes
the build pass plus an enumerated WCAG AA contrast table (link text, body text,
non-text blue accent, focus ring, red punctuation) in both modes.

### Constitution Check

PASS. Principles I–III/N/A (no plugin manifest/script/version touched); IV pass
(docs-site validate is the gate, no Layer-4 owed); V pass (conventional, public-
readable title); VI pass (Starlight-native, no bespoke components, fonts copied
verbatim). Reviewability: ~80 reviewable CSS LOC + small MDX + config — within
budget; single vertical slice, no split. Deferred: DOC-016/017/019/012.

### Cleanup Notes

`specs/doc-013-brand-identity-marketplace-landing` was removed from active
`specs/**` in the post-merge cleanup; only `specs/.gitkeep` remains. Recovery
commands and provenance are recorded in the DOC-013 archive report.

## XPLAT-003 Supply-Chain Security and Consumer Trust Model

[Source: specs/xplat-003-supply-chain-security-and-consumer-trust-model]

### Dependencies and Environment

- **Runtime decision**: Python 3.11+ standard-library runner, aligned with
  official Spec Kit / `specify` prerequisites.
- **Rejected installed-plugin runtime substrates**: Go, Rust, Zig, native
  binaries, Bash, Git Bash, WSL, PowerShell helper scripts, `jq`, Node,
  `pip install`, virtualenv restore, and package restore.
- **Storage**: checked-in repository files and generated Claude/Codex plugin
  payloads only; no database or runtime service state.
- **Target platforms**: native Windows, macOS, and Linux through installed
  Claude Code and Codex plugin caches.

### Architecture / Approach

XPLAT-003 is a decision/control spec. It defines what downstream implementation
must prove before the runtime lane can claim universal installed-plugin support.

- XPLAT-004 owns the Python runner source layout, plugin entrypoint, path/JSON
  envelope helpers, subprocess execution without a shell, platform detection,
  prerequisite checks for Python 3.11+ and `specify`, runner identity/preflight
  output, checksum/manifest files, and Python stdlib test/eval runner patterns.
- XPLAT-005 and XPLAT-006 own behavior ports once the runner foundation exists.
- XPLAT-007 owns Claude Code and Codex cutover, generated payload verification,
  latest tagged release checks, complete bundled-agent/install evidence, native
  platform UAT, update and autoheal proof, consumer-local verification docs, and
  public claim readiness.
- Release automation and public documentation may only claim controls that are
  implemented and verified; SBOMs, attestations, reproducible builds, signatures,
  formal audit, and cryptographic trust-chain verification remain deferred
  hardening unless later promoted.

### Testing Strategy

XPLAT-003 itself is docs/process-only. Verification for the cleanup is archive
state, generated roadmap-MOC index regeneration, JSON validation, active spec
inventory review, whitespace validation, and the focused structural SpecKit Pro
test layer. Downstream XPLAT specs must add Python stdlib unit/parity/eval gates
and native installed-cache UAT before public release claims.

### Constitution Check

PASS. XPLAT-003 did not change plugin runtime behavior, manifests, release
automation, generated payloads, or public docs. It created the policy and
control contract that later implementation specs must satisfy.

### Cleanup Notes

`specs/xplat-003-supply-chain-security-and-consumer-trust-model` was removed
from active `specs/**` in the post-merge cleanup after PR #267 merged. Recovery
commands and provenance are recorded in the XPLAT-003 archive report.

## XPLAT-001 Runtime Inventory and Constraints

[Source: specs/xplat-001-runtime-inventory-constraints]

XPLAT-001 was a docs/process inventory spike. It used repo-local scans and
static invocation-trace review to classify Bash, `.sh`, `jq`, shell quoting,
Unix-path, `chmod`, and line-ending assumptions across tracked text files. The
durable output is `docs/ai/research/cross-platform-runtime-inventory.md`; the
feature did not port helpers, select a runtime, select security controls, or
claim native Windows support. Verification centered on scan reproducibility,
spec-index checks, diff hygiene, and the repository structural suite.

Cleanup note: the active spec folder was removed after PR #263 merged. Recovery
commands and provenance are recorded in the completed-active-specs archive
report.

## XPLAT-002 Runtime Implementation Options and Contract Decision

[Source: specs/xplat-002-runtime-implementation-options-contract-decision]

XPLAT-002 was a decision and contract spike. It preserved historical candidate
evidence, amended the selected runtime to Python 3.11+ standard-library source,
and recorded the `speckit-pro-runner` request/response/diagnostic/exit/path/
subprocess/preflight contract for XPLAT-004. It explicitly avoided runner
implementation, helper ports, generated-payload cutover, release automation, and
public native-platform support claims.

Cleanup note: the active spec folder was removed after PR #266 merged. Recovery
commands and provenance are recorded in the completed-active-specs archive
report.

## DOC-014 SEO and AI Discoverability

[Source: specs/doc-014-seo-and-ai-discoverability]

DOC-014 was a docs-site infrastructure slice on Astro/Starlight. It added
static build-time discoverability outputs: crawler policy, llms digests,
per-page Markdown, schema graph, OG cards, sitemap freshness, descriptions,
quality validation, and SEO Playwright tests. New dependencies were
`starlight-llms-txt`, `astro-og-canvas` plus CanvasKit, and `@astrojs/sitemap`.
Verification used the docs-site validation path and SEO-specific Playwright
coverage. The noindex staging guard remains until DOC-012.

Cleanup note: the active spec folder was removed after PR #264 merged. Recovery
commands and provenance are recorded in the completed-active-specs archive
report.

## XPLAT-004 Cross-Platform Runner Foundation

[Source: specs/xplat-004-cross-platform-runner-foundation]

XPLAT-004 implemented the small Python standard-library runner foundation
required before helper parity work can begin. The source package lives under
`speckit-pro/speckit_pro_runner/` and is invoked with
`<python> -m speckit_pro_runner` from a source checkout using JSON stdin/stdout.
It includes envelope helpers, runtime/preflight reporting, deterministic
diagnostics, typed path records, source metadata verification, and
shell-disabled subprocess fixture records.

### Technical Approach

- Keep the runner source inside the `speckit-pro/` plugin package with no new
  runtime dependency beyond Python 3.11+ standard library and the official
  Spec Kit / `specify` prerequisite boundary.
- Preserve XPLAT-002 JSON envelope, path, subprocess, diagnostic, and exit-code
  contract shape for downstream helper ports.
- Implement only `runtime-info`, `preflight`, and synthetic fixture behavior in
  XPLAT-004; real read-only helpers move to XPLAT-005 and mutation/install/PR
  helpers move to XPLAT-006.
- Store runner identity and checksum metadata in
  `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` and
  `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`.
- Preserve the Windows/Linux source-checkout runbook fixture contract under the
  Layer 4 fixture tree so tests do not depend on active `specs/**` content
  after archive cleanup.
- Preserve the changed-files fallback fixture under the Layer 4 fixture tree so
  no-cutover assertions remain runnable when Git diff context is unavailable.

### Testing Strategy

XPLAT-004 verification uses the runner-specific Layer 4 entrypoint,
`bash tests/speckit-pro/run-all.sh --layer 4`, Layer 1 structural validation,
the default deterministic suite, spec-index checks, diff hygiene, manifest JSON
validation, PR-packet validation, and G7 task validation. Native installed-cache
UAT, generated payload propagation, update/autoheal proof, and public claim
validation remain XPLAT-007 responsibilities.

### Cleanup Notes

`specs/xplat-004-cross-platform-runner-foundation` was removed from active
`specs/**` in the post-merge cleanup after PR #274 merged. Recovery commands
and provenance are recorded in the XPLAT-004 archive report.

## XPLAT-005 Read-Only Helper Port

[Source: specs/xplat-005-read-only-helper-port]

XPLAT-005 implemented the bounded read-only/advisory helper migration on top of
the XPLAT-004 runner. The production surface lives under
`speckit-pro/speckit_pro_runner/helpers/` and extends the runner envelope,
runtime metadata, and dispatch path without changing active installed-plugin
invocation surfaces.

### Technical Approach

- Add a small explicit helper registry rather than dynamic discovery, so
  mutation helpers cannot be exposed by accident.
- Group read-only behavior in `helpers/read_only.py` and preserve current Bash
  helper argv shape, stdout/stderr text, JSON stdout semantics, and exit codes
  through source-checkout Bash-reference comparisons.
- Classify each helper as `python_authoritative`, `bash_reference_only`, or
  `out_of_scope` with authoritative request fixtures and rollback notes.
- Keep `generate-spec-index` limited to `--check` and keep
  `validate-pr-packet` limited to read-only validation output; write,
  persistence, and PR-body generation remain downstream.
- Refresh runner manifest/checksum metadata for the new helper source files.
- Preserve fixture inputs under
  `tests/speckit-pro/unit/fixtures/read-only-helpers/` so Layer 4
  remains runnable after the active XPLAT-005 spec folder is archived.

### Testing Strategy

XPLAT-005 verification uses the read-only helper Layer 4 entrypoint,
`bash tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.sh`,
the runner Layer 4 entrypoint, `bash tests/speckit-pro/run-all.sh --layer 4`,
Layer 1 structural validation, spec-index checks, JSON validation, diff
hygiene, PR-packet validation, workflow-contract validation, and a local macOS
source-checkout runtime-info smoke through the runner fixture suite. Native
installed-cache UAT, generated payload propagation, update/autoheal proof,
mutation-helper verification, and public claim validation remain XPLAT-006 and
XPLAT-007 responsibilities.

### Cleanup Notes

`specs/xplat-005-read-only-helper-port` was removed from active `specs/**` in
the post-merge cleanup after PR #276 merged. Recovery commands and provenance
are recorded in the XPLAT-005 archive report. Minimal spec inputs needed by
helper parity tests were copied to the read-only helper fixture tree before
cleanup.

## XPLAT-006 Mutation, Install, and PR-Emission Helper Port

[Source: specs/xplat-006-mutation-install-pr-emission-helper-port]

XPLAT-006 implemented the mutation-capable runner helper substrate on top of
the XPLAT-004 runner and XPLAT-005 read-only registry. The production surface
lives under `speckit-pro/speckit_pro_runner/helpers/`, with contract and parity
evidence under `tests/speckit-pro/unit/fixtures/mutation-helpers/`.

### Technical Approach

- Extend the explicit helper registry with mutation-capable helper records and
  deferred/out-of-scope handoff metadata instead of dynamic helper discovery.
- Keep promoted runner helper logic in Python 3.11+ standard library code, with
  no shell execution, package restore, or network dependency.
- Add shared mutation primitives in `helpers/mutation.py` for request/result
  normalization, operation records, path-boundary checks, dirty-worktree
  guards, atomic generated-file writes, partial-failure records, and no-op
  handling.
- Add install completeness and fake-home repair proof in `helpers/install.py`
  backed by `install_inventory.json`.
- Add generated PR-body output and dry-run command-plan proof in
  `helpers/pr_emission.py`; live GitHub/repo command-plan apply remains a
  deterministic deferred-live-mutation failure.
- Add `validate-autopilot-phase-coverage.py` and generated Codex/Claude mirrors
  to prevent future autopilot workflows from omitting Phase 6.5 or canonical
  Post steps.
- Preserve XPLAT-006 contract schemas in the mutation-helper fixture tree so
  Layer 4 tests remain runnable after the active spec folder is archived.

### Testing Strategy

XPLAT-006 verification uses Python standard-library focused tests,
`python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`,
`python3 tests/speckit-pro/unit/test-autopilot-phase-coverage.py`,
the runner and read-only helper Layer 4 suites, spec-index checks, JSON
validation, diff hygiene, PR-packet validation, workflow-contract validation,
reviewability gates, and the default deterministic suite. Native installed
Claude/Codex UAT, generated-payload selection/cutover, active repo-local Bash
gate replacement, update/autoheal proof, and public release claims remain
XPLAT-007 and XPLAT-008 responsibilities.

### Cleanup Notes

`specs/xplat-006-mutation-install-pr-emission-helper-port` was removed from
active `specs/**` in the post-merge cleanup after PR #281 merged. Recovery
commands and provenance are recorded in the XPLAT-006 archive report. Contract
schemas needed by helper tests were copied to the mutation-helper fixture tree
before cleanup.

## XPLAT-007 Python Tooling and Release-Gate Migration

[Source: specs/xplat-007-python-tooling-and-release-gate-migration]

XPLAT-007 implemented active repo-local Python gate migration on top of the
XPLAT-004 runner, XPLAT-005 read-only helper records, and XPLAT-006
mutation/install/PR-emission contracts. The production surface lives under
`speckit-pro/speckit_pro_runner/gates/`, with gate request, case, promotion,
and contract evidence under
`tests/speckit-pro/unit/fixtures/runner-gates/`.

### Technical Approach

- Add an explicit `gates/` package rather than a generic command framework, so
  suite, payload, install, release-readiness, and guard behavior remain
  reviewable and bounded.
- Preserve the existing JSON-envelope runner contract, diagnostics, status to
  exit-code mapping, and shell-disabled subprocess policy.
- Promote suite/eval, payload, install-verification, release-readiness, and
  active-path guard operations through `python -m speckit_pro_runner` request
  fixtures.
- Keep release payload behavior limited to test payload evidence and fixture or
  temporary roots; generated release payload selection and publication remain
  XPLAT-008.
- Update plugin PR and release workflows so plugin validation dispatches to
  Python runner gates instead of Bash or `jq` release logic.
- Preserve XPLAT-007 contract schemas in the gate fixture tree so Layer 4 tests
  remain runnable after the active spec folder is archived.

### Testing Strategy

XPLAT-007 verification uses Python standard-library focused tests,
`python3 tests/speckit-pro/unit/test-speckit-pro-gates.py`, runner
request fixtures for default suite, layer, AI-eval, integration, parity,
payload evidence, install verification, release readiness, live release
readiness, and active-path guard behavior, plus the default deterministic
repository suite. GitHub PR checks on #284 through #287 verified the sliced
implementation before archive cleanup.

### Cleanup Notes

`specs/xplat-007-python-tooling-and-release-gate-migration` was removed from
active `specs/**` in the post-merge cleanup after PR #287 merged. Recovery
commands and provenance are recorded in the XPLAT-007 archive report. Contract
schemas needed by gate tests were copied to the XPLAT-007 gate fixture tree
before cleanup. XPLAT-008 is now ready for installed Claude/Codex cutover,
release payload publication, native installed-plugin UAT, update/autoheal, and
public release readiness.

## XPLAT-008 Claude/Codex Cutover and Universal Install Release Gate

[Source: specs/xplat-008-claude-codex-cutover-universal-install-release-gate]

XPLAT-008 implemented the installed Claude/Codex runtime cutover, generated
payload release checks, public docs claim alignment, UAT matrix validation,
release-readiness aggregation, and bounded install-health repair behavior on
top of the XPLAT-004 runner, XPLAT-005 helper registry, XPLAT-006 mutation and
install helpers, and XPLAT-007 gate substrate.

### Technical Approach

- Route active Claude/Codex installed-runtime surfaces through direct
  `python -m speckit_pro_runner` JSON-envelope invocation instead of shell
  helper execution.
- Keep active no-shell/no-jq guard scope focused on installed-runtime source,
  generated payloads, install guidance, and release gates while allowing
  archive/provenance text, fixture text, minimal CI dispatch glue, and upstream
  Spec Kit generated helpers.
- Rebuild generated Claude and Codex payloads from source and compare them
  against source-derived payload inventories, not against the existing `dist/**`
  tree as source of truth.
- Preserve the release-readiness packet, UAT matrix, and partial Codex/macOS
  installed-cache UAT evidence under `docs/ai/specs/.process/` after active
  spec cleanup.
- Preserve XPLAT-008 contract schemas under
  `tests/speckit-pro/unit/fixtures/installed-plugin-release/contracts/` so
  Layer 4 gates no longer depend on active `specs/**` content.

### Testing Strategy

XPLAT-008 verification uses focused Python standard-library Layer 4 gate tests,
payload completeness runner requests, active-runtime guard requests, UAT matrix
requests, install-health repair requests, release-readiness expected-failure
and ready-fixture requests, docs-site validation, generated payload rebuilds,
runner manifest/checksum validation, SpecKit index checks, JSON validation,
diff hygiene, and the default deterministic suite.

### Cleanup Notes

`specs/xplat-008-claude-codex-cutover-universal-install-release-gate` was
removed from active `specs/**` in the post-merge cleanup after PR #292 merged.
Recovery commands and provenance are recorded in the XPLAT-008 archive report.
The release lane remains held by real operator UAT: do not publish native
Windows/macOS/Linux Claude or Codex support claims until
`docs/ai/specs/.process/XPLAT-008-uat-matrix.md` has six passing rows and the
release-readiness gate is rerun against that evidence.

## XPLAT-009 Plugin Source and Payload Bash Eradication

[Source: specs/xplat-009-plugin-source-and-payload-bash-eradication]

XPLAT-009 implemented the plugin-source Bash eradication lane on top of the
XPLAT-004 runner, XPLAT-005/XPLAT-006 helper registries, XPLAT-007 gate
substrate, and XPLAT-008 installed-runtime cutover, using two vertical slices:
active plugin-source Bash removal first, then payload rebuild, installed-cache
proof, and zero-Bash guards.

### Technical Approach

- Port active plugin-source script behavior (autopilot, coach, and install
  skill scripts plus `speckit-pro/scripts/`) to Python runner/helper/gate
  operations and delete the remaining live `.sh` files under `speckit-pro/`.
- Replace active source and generated agent instructions that called Bash
  helpers with Python runner operations or no-shell guidance, keeping
  historical/archive references as prose behind a documented allowlist.
- Rebuild generated Claude and Codex payloads from the updated source surfaces
  and compare them against source-derived inventories.
- Prove source, generated payloads, and a bounded installed-cache artifact pass
  one Python-backed zero-Bash guard, with committed evidence under
  `docs/ai/specs/.process/XPLAT-009-*`.
- Preserve XPLAT-009 contract schemas under
  `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/contracts/` so
  Layer 4 gates no longer depend on active `specs/**` content.

### Testing Strategy

XPLAT-009 verification uses focused Python standard-library Layer 4
runner/helper/gate tests, Layer 1 structural validation, payload-completeness
apply/read-only evidence, installed-cache proof, the active-instruction
no-shell/no-`jq` guard, seeded zero-Bash regression cases, release-readiness
fixture coverage, spec-index checks, JSON validation, diff hygiene, and the
default deterministic suite.

### Cleanup Notes

`specs/xplat-009-plugin-source-and-payload-bash-eradication` was removed from
active `specs/**` in the post-merge cleanup after PR #297 merged and shipped in
speckit-pro 2.18.0. Recovery commands and provenance are recorded in the
XPLAT-009 archive report. Repository-wide Bash confinement and the CI dispatch
guard were completed by XPLAT-010, and public native Windows/macOS/Linux
release claims remain blocked until the preserved XPLAT-008 UAT matrix has six
passing operator rows.

## XPLAT-010 Repository Bash Confinement and CI Dispatch Guard

### Technical Approach

XPLAT-010 used a manifest-driven Python 3.11+ standard-library architecture for
repository-only validation. `tests/speckit-pro/suite-manifest.json` defines the
layers and Python dispatch; shared test-result and baseline helpers preserve
per-check identities; runner gates enumerate tracked files and structurally
inspect executable surfaces; subprocesses use argv arrays and `shell=False`;
and workflow shell remains bounded dispatch glue.

The implementation also added a Docker/QEMU-backed Linux amd64/arm64 preflight
path, direct hosted Windows advisory smoke, stable always-reporting Linux
sentinels, deterministic release-note parsing/composition, immutable release
audit evidence, and the restored `estimate-spec-size` helper operation. The
review topology was an 18-PR no-gap stack with frozen adjacent packets and a
bounded publication tail.

### Testing Strategy

- Preserve exact Bash-to-Python outcome names and counts in purpose-based
  parity baselines and a cumulative count ledger.
- Run focused Python unit/contract suites for each port before the default
  deterministic Layers 1, 4, and 5 suite.
- Run the default suite with Bash and `jq` absent from PATH; final result:
  `2512/2512` (`1373`, `953`, `186`).
- Prove repository confinement with tracked-file enumeration, fixed vendored
  allowlist checks, release-readiness composition, and seeded regressions.
- Prove hosted preflight behavior with relevant-path, docs-only,
  failure-propagation, manual-main, and all four owned PR-trigger canaries.
- Keep Windows preflight explicitly advisory and retain XPLAT-008 operator UAT
  as the only native-platform release-claim gate.
- Validate every adjacent review slice and audit the final merged tree against
  the verified stack tip.

### Cleanup Notes

PRs #311-#328 merged on 2026-07-11, ending at
`ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29`. Live test dependencies were
decoupled into purpose-based fixtures before removing the active XPLAT-010 spec
folder. Process evidence remains under `docs/ai/specs/.process/XPLAT-010-*`,
and raw spec artifacts remain recoverable from the final merge commit. The
separate constitution amendment completed through PR #331 at
`b537e3b43ca20d8f6e8b6e9430d797444462f2e9` before archive cleanup. Public native
claims remain blocked by the XPLAT-008 UAT matrix.

## CAR-001 Candidate Route Baseline and Role Contracts

[Source: specs/car-001-candidate-route-baseline]

CAR-001 completed the first Claude agent-routing research spike. It produced
the durable Markdown research record and JSON candidate-route manifest under
`docs/ai/research/`, leaving shipped plugin bytes unchanged and preserving the
spec workflow/design evidence under `docs/ai/specs/.process/`.

### Technical Approach

- Treat CAR-001 as a documentation research spike: no production-code files, no
  generated payload rebuild, and no agent default mutation.
- Pin route and instruction identity to the consumer-installable
  `speckit-pro-v2.19.1` comparator at
  `e343aa2e4ebcb2d48c501f285d7072cfd55722da`.
- Compute manifest hashes with Python 3.11+ standard-library methods and keep
  hash identity reproducible from the pinned tag.
- Record current platform facts, capability questions, role contracts,
  fixture-backlog requirements, telemetry requirements, and go/no-go handoff
  boundaries for CAR-002/CAR-003/CAR-006.
- Keep executable-route and fallback-ordering claims deferred until downstream
  probing, exact-treatment replay, and qualification specs.

### Testing Strategy

The merged PR verified JSON validity/schema conformance, hash reproducibility,
absolute-path privacy checks, zero shipped-byte change, default deterministic
suite coverage, non-goal guardrails, and PR check gates. The archive cleanup
reruns JSON validation for `autopilot-state.json`, the SpecKit index write/check
operations, active-spec inventory, diff hygiene, and Layer 1 structural
validation.

### Cleanup Notes

`specs/car-001-candidate-route-baseline` was removed from active `specs/**` in
the post-merge cleanup after PR #350 merged on 2026-07-15. The canonical
artifacts are `docs/ai/research/claude-agent-route-candidates.md` and
`docs/ai/research/claude-agent-route-candidate-manifest.json`; CAR-002 is now
the next ready spec in the Claude routing roadmap. Recovery commands and
provenance are recorded in the CAR-001 archive report.

## HRNS-001 Harness Surface Inventory and Gap Taxonomy

[Source: specs/hrns-001-harness-surface-inventory-gap-taxonomy]

### Technical Approach

- Treat verified merged repository state as current authority and classify all
  other evidence by explicit source and lifecycle rules.
- Keep one canonical Markdown taxonomy with stable surface and gap identities.
- Preserve packet-emission runtime behavior in the runner helper registry with
  guarded writes, persisted validation, mutation locks, rollback ownership,
  synchronized Claude/Codex guidance, and parity fixtures.
- Keep later context, capability, permission, eval, trace, orchestration, OKF,
  and drift behavior in HRNS-002 through HRNS-014.

### Testing Strategy

HRNS-001 used source/evidence review, task verification, spec-index checks,
packet helper tests, structural validation, full CI, generated payload parity,
container preflight, and resolved review threads. Post-merge cleanup revalidates
the active-spec index, JSON state, docs references, and deterministic suite.

### Cleanup Notes

The active HRNS-001 directory was removed after PR #357 merged. The taxonomy at
`docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md` and merged runner,
test, payload, and process artifacts are canonical. HRNS-002 and HRNS-003 are
ready; exact recovery is recorded in the HRNS-001 archive report.

## G56R-001 Candidate Route Baseline and Role Contracts

[Source: specs/g56r-001-candidate-route-baseline]

### Technical Approach

- Separate official platform evidence, repository project inputs, runtime
  verification, qualification evidence, and undocumented gaps.
- Bind provisional candidates to stable source, effort-surface, and role
  contract IDs in one schema-v2 planning manifest and one canonical report.
- Preserve role contracts while deferring executable tuples, qualification,
  fallback ordering, resolver behavior, installation, and release policy.
- Fail closed when current official documentation is missing, conflicting, or
  invalidated.

### Testing Strategy

G56R-001 used the shared CAR/G56R parity validator, exact record-count and
reference checks, task verification, Layer 1 and full deterministic suites,
docs reference checks, CodeQL, container preflight, and resolved PR review
threads. Post-merge cleanup reruns the parity validator and repository gates.

### Cleanup Notes

The active G56R-001 directory was removed after PR #360 merged on top of PR
#362. The report, manifest, shared schema, parity contract, roadmap, PRD, and
process files remain canonical. G56R-002 is ready for capability discovery and
telemetry profiling under the preserved no-qualification boundary; exact
recovery is recorded in the G56R-001 archive report.

## Revision 2026-07-24 - CAR-002 and G56R-002 Post-Merge Architecture

### Technical Approach Preserved

- CAR-002 keeps durable capability evidence under `docs/ai/research/`, its
  adapters under `tests/speckit-pro/layer6-efficiency/lib/`, and deterministic
  fixtures and validation under `tests/speckit-pro/unit/`.
- G56R-002 keeps durable capability evidence under `docs/ai/research/`, focused
  capability and treatment modules under `tests/speckit-pro/layer6-efficiency/`,
  contract schemas under `tests/speckit-pro/layer6-efficiency/contracts/`, and
  replay/checkpoint fixtures under `tests/speckit-pro/unit/fixtures/`.
- Completed-marker provenance continues to name its historical spec paths and
  is validated from the recorded git commits, so live tests no longer depend on
  an active completed spec directory.

### Testing and Cleanup

The cleanup migrates only live test-owned contracts and fixtures, removes the
two merged active spec folders, regenerates SpecKit indexes, validates project
state JSON, and runs focused plus repository structural checks. CAR-003 and
G56R-003 may now scaffold against the canonical shipped evidence.

## Revision 2026-07-27 - CAR-003 and G56R-003 Post-Merge Architecture

### Technical Approach Preserved

- CAR-003 keeps its single shipped production module at
  `speckit-pro/speckit_pro_runner/materializer.py`, mirrored into both `dist/`
  payloads, with durable evaluation evidence under `docs/ai/research/`,
  qualification modules under `tests/speckit-pro/layer6-efficiency/lib/`, and
  deterministic fixtures and suites under `tests/speckit-pro/`.
- G56R-003 keeps `speckit-pro/speckit_pro_runner/agent_materialization.py` as
  its shipped surface, its closed schemas under
  `tests/speckit-pro/layer6-efficiency/contracts/`, its `qualification_*`
  modules under `tests/speckit-pro/layer6-efficiency/lib/`, and its twelve
  per-role fixtures behind one shared corpus manifest.
- The two lanes had genuinely different contract layouts, and the archive had to
  reconcile them before either spec folder could be removed. CAR-003 kept one
  spec-scoped copy that a live Layer 6 library read directly; G56R-003 kept a
  runtime copy in the test tree plus a specification copy in its spec folder.
  Both sets were **moved** into the test tree - CAR-003's nine to
  `contracts-claude/`, G56R-003's nine specification copies to
  `contracts-codex-specification/` - so each artifact still has exactly one home
  and no library or test reads from `specs/**`.
- `tests/speckit-pro/layer6-efficiency/contracts/` was deliberately left alone.
  It holds the three shared G56R-002 contracts plus G56R-003's runtime tier, and
  roughly ten readers depend on it; touching it would have added risk the archive
  did not need.
- The runtime-versus-specification pair on the Codex side was preserved, not
  collapsed. Its distinctness assertions are the standing evidence that CAR-012
  and G56R-012 exist to reconcile.

### Testing and Cleanup

The cleanup removes the two merged active spec folders, records the archive
sweep in both lane state files, regenerates the SpecKit index and docs
reference pages, validates project state JSON, and runs structural plus full
deterministic suites. CAR-004 and G56R-004 may now scaffold against the
canonical shipped evidence. The mirrored-contract corrections that each twin
identified remain open as the CAR-012 and G56R-012 joint change.

## Revision 2026-07-28 - CAR-004 Post-Merge Architecture

### Where CAR-004 Lives Now

- Both frozen contracts sit beside the CAR-003 set in
  `tests/speckit-pro/layer6-efficiency/contracts-claude/`:
  `policy-control-registry.schema.json` and `control-comparison.schema.json`.
  Each is content-addressed and resolves references only through local
  `#/$defs/`, so neither reaches outside its own document.
- The four frozen instances live in a new
  `tests/speckit-pro/layer6-efficiency/fixtures-controls/` directory: the
  registry, the comparison rule, the reserved-partition entries, and the
  deterministic replay cases.
- Validation is two Layer 6 modules, `claude_policy_controls.py` and
  `claude_control_comparison.py`, sharing one fail-closed schema engine. The
  engine implements the JSON Schema subset the committed corpus actually uses
  and refuses any keyword it cannot enforce, rather than ignoring it.
- `run-control-smoke.py` is the bounded operator driver. It never runs in CI, is
  registered nowhere in the suite manifest, and writes only into the already
  gitignored `layer6-efficiency/results/`.
- Three durable-named unit modules are registered at Layer 4 in
  `suite-manifest.json`; none couples its filename to the spec ID.

### Why The Archive Was Simple Here

CAR-003's archive had to move eighteen contract schemas out of two spec folders
before either could be removed. CAR-004 needed none of that: its schemas were
authored into the test tree from the start, and the spec-folder `contracts/`
directory held only three Markdown design documents with no readers. The one
genuine relocation was the operator runbook, moved from the feature's `.process/`
directory to `docs/ai/specs/.process/` because it is forward-looking evidence
that outlives the spec folder, not exhaust.

### Testing and Cleanup

The cleanup removes the merged active spec folder, moves the Claude lane state to
CAR-004 archived, regenerates the
SpecKit index and docs reference pages, validates project state JSON, and runs
the structural and full deterministic suites. CAR-005 may now scaffold against
the canonical shipped evidence. CAR-012 remains open as the cross-platform
reconciliation joint change with G56R-012.

## Revision 2026-07-29 - G56R-004 Post-Merge Architecture

### Where G56R-004 Lives Now

- The two closed Codex specification schemas live under
  `tests/speckit-pro/layer6-efficiency/contracts-codex-specification/`.
- The registry, comparison, partition, and replay fixtures live under
  `tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/`.
- `codex_policy_controls.py`, `codex_control_comparison.py`, and
  `codex_control_smoke.py` own fail-closed validation, comparison, deterministic
  replay, bounded non-live smoke planning/sealing, and evidence-derived twin
  reconciliation.
- The existing durable Layer 4 owners remain authoritative:
  `test-policy-control-contracts.py`,
  `test-control-comparison-dominance.py`, and
  `test-twin-handoff-completeness.py`. No suite-manifest change was required.

### Why The Archive Is Safe

All machine-enforced artifacts were authored directly into the test tree.
Nothing in live code or tests reads
`specs/g56r-004-policy-controls-adaptive-comparators`, so the active folder can
be removed without relocating contracts or changing behavior. The one
forward-looking document was its operator-only smoke procedure; that procedure
now lives at `docs/ai/specs/.process/G56R-004-live-smoke-runbook.md`.

### Testing and Cleanup

The cleanup removes only the merged G56R-004 active spec, marks both project
state files completed/archived, regenerates and checks the SpecKit index,
validates JSON and diff hygiene, and runs structural plus full deterministic
suites. G56R-005 may now scaffold against the canonical shipped evidence.
G56R-012 remains the separate paired reconciliation with CAR-012.

## Revision 2026-07-30 - CAR-005 Post-Merge Architecture

### Where CAR-005 Lives Now

- The three closed Claude route contracts live under
  `tests/speckit-pro/layer6-efficiency/contracts-claude/`:
  `route-resolution-report.schema.json`, `route-policy.schema.json`, and
  `environment-snapshot-projection.schema.json`.
- The eighteen-case replay corpus lives at
  `tests/speckit-pro/layer6-efficiency/fixtures-fallback/fallback-scenario-corpus.json`.
- `claude_route_fallback.py` owns route resolution, the bounded fallback walk,
  the closed disqualifier list behind `release_claim_eligible`, override
  disposition, optional-helper accounting, and byte-identical replay. It reuses
  `claude_policy_controls.CONTRACT_ROOT` and its fail-closed schema engine
  rather than re-deriving either.
- `tests/speckit-pro/unit/test-route-fallback-simulation.py` is the durable
  Layer 4 owner. `tests/speckit-pro/suite-manifest.json` gained exactly one
  entry in slice 1 and none in slice 2.

### Why The Archive Is Safe

All machine-enforced artifacts were authored directly into the test tree.
Nothing in live code, tests, or scripts reads
`specs/car-005-availability-fallback-recovery`, so the active folder can be
removed without relocating contracts or changing behavior. The feature carried
no unrun operator procedure — every claim is deterministic and re-runnable from
the committed suite — so unlike CAR-004 and G56R-004 there was nothing
forward-looking to move out of the folder first.

### One Architectural Debt Left In Place

The simulator's accept path is unvalidated: two of the three declared contract
constants are never read, so inputs are trusted while outputs are checked. The
fix is to load both contracts at import and validate `policy` and `snapshot` in
`resolve()` and per case in `load_corpus`, which would also make the loader
docstring true. It is deliberately **not** folded into this cleanup — the
archive commit changes no shipped behavior, and both CAR-005 slices are already
on `main`, so the correction is an ordinary follow-up change rather than a
restack.

### Testing and Cleanup

The cleanup removes only the merged CAR-005 active spec, moves the Claude lane
state to CAR-005 archived, regenerates and checks the SpecKit index, validates
project state JSON and diff hygiene, and runs the structural and full
deterministic suites. CAR-006 may now scaffold against the canonical shipped
evidence. CAR-012 remains the separate paired reconciliation with G56R-012.

## Revision 2026-07-30 - ART-001 Post-Merge Architecture

### Where ART-001 Lives Now

- The authored gallery source lives at `speckit-pro/artifact-gallery/`:
  `brand-kit.css`, `brand-voice.md`, `manifest.json`, `theme-toggle.html`,
  `SPA-CONTRACT.md`, and `UPSTREAM-NOTICE.md`.
- The same six files materialize into `dist/claude/speckit-pro/artifact-gallery/`
  and `dist/codex/speckit-pro/artifact-gallery/`, with the runner manifest and
  `.sha256` regenerated to match.
- `speckit_pro_runner/gates/payloads.py` carries the payload-completeness fix
  that made the gallery directory's absence a failure instead of a silent pass.
- `tests/speckit-pro/unit/test-artifact-gallery.py` is the durable owner and
  holds the SPA-contract scan PR #409 added. The installed-cache-proof fixtures
  under `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/` were
  regenerated to include the gallery.
- The acceptance harness now lives at
  `docs/ai/specs/.process/ART-001-acceptance-harness.html`.

### Why The Archive Is Safe

Every machine-enforced artifact was authored into the plugin source, the payload,
or the test tree. After the harness relocation, nothing in live code, tests,
scripts, workflows, or the docs site reads
`specs/art-001-brand-kit-gallery-foundation`, so the active folder can be removed
without changing behavior.

### Why The Harness Moved And The Quickstart Did Not

This cleanup makes the same call CAR-004 and G56R-004 did, and the opposite call
CAR-005 did, for the same reason each time: relocate what is still needed
forward, delete what is reproducible.

The harness is needed forward twice over — it is the only artifact behind the
12-of-12 manual result, and the roadmap explicitly directs a later spec to reuse
its clipboard-failure and live-state handling rather than re-derive them. Two
files outside the spec folder pointed at it, so deleting would have left dangling
pointers in live documents.

The feature `quickstart.md`, by contrast, is a validation guide for work already
merged, and `retrospective.md` and `.process/changed-files.txt` are run exhaust.
All three are recoverable at the merge commit and were removed with the folder.

### Testing and Cleanup

The cleanup relocates one harness, repoints two references, removes the merged
ART-001 active spec, moves the project archive state to ART-001, regenerates and
checks the SpecKit index, validates project state JSON and diff hygiene, and runs
the structural and full deterministic suites. ART-002 through ART-006 may now
scaffold against the canonical shipped foundation.
