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
2026-06-11 after the PRSG-009 contract schemas were vendored under
`tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/contracts/` and the
emitter's schema path reporting was repointed to those durable fixtures.
