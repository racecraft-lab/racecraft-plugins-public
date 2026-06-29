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
- EXTENDED `tests/layer4-scripts/test-reviewability-gate.sh` — diff-mode:
  `.process/` excluded, spec counted (SC-003).
- EXTENDED `tests/layer4-scripts/test-ensure-reviewability-preset.sh` —
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

- `bash tests/speckit-pro/layer4-scripts/test-plan-layers.sh` covers planner
  contract behavior and passed `66/66`.
- `bash tests/speckit-pro/run-all.sh --layer 4` passed `1029/1029`.
- `bash tests/speckit-pro/run-all.sh --layer 1` passed `887/887`.
- `bash tests/speckit-pro/run-all.sh` passed `2106/2106`.
- PR #138 post-merge main checks passed Release and CodeQL runs for merge commit
  `deccd8a2a9916e11edfad43df8ceef95a756dc04`.

### Cleanup Notes

`specs/prsg-008-layer-planner` was removed from active `specs/**` cleanup on
2026-06-10 after the planner schema was vendored under
`tests/speckit-pro/layer4-scripts/fixtures/plan-layers/contracts/` and focused
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

- `bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh` passed `81/81`.
- `bash tests/speckit-pro/layer4-scripts/test-restack.sh` passed `32/32`.
- `bash tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh` passed `44/44`.
- `bash tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh` passed `86/86`.
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

- `bash tests/speckit-pro/layer4-scripts/test-final-reviewability-backstop.sh`
  passed `31/31`.
- `bash tests/speckit-pro/layer4-scripts/test-atomicity-route.sh` passed
  `109/109`.
- `bash tests/speckit-pro/layer4-scripts/test-o5-topology.sh` passed `25/25`.
- `bash tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh` passed
  `87/87`.
- `bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run --fixture 03-prsg-010-backstop-o5-routing`
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
    fixtures under `tests/speckit-pro/layer4-scripts/fixtures/`.
  - SPEC-006a already used the vendored full-spec snapshot fixture.
- Regenerate generated roadmap-MOC INDEX content after active spec removal so
  generated links do not point to archived spec folders.

### Test Strategy

- Pre-cleanup fixture verification:
  - `bash tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh` passed
    `85/85`.
  - `bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh` passed
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
