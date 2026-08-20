# Implementation Plan: ART-005 - Gallery Completion - Knowledge, Reports & Editors

**Branch**: `art-005-gallery-completion-knowledge-reports-editors` | **Date**: 2026-08-17 | **Spec**: `specs/art-005-gallery-completion-knowledge-reports-editors/spec.md`

**Input**: Feature specification from `specs/art-005-gallery-completion-knowledge-reports-editors/spec.md`

## Summary

ART-005 ports seven planned knowledge, report, and editor gallery templates as
complete standalone Racecraft artifacts. The old combined-slice stop is resolved
by the operator's seven-slice topology: one ART-005 specification and workflow,
seven sequential stacked PR slices, exactly one template per slice in manifest
order.

Planning reverified the pinned upstream bytes from
`anthropics/html-effectiveness@58c305be97f47b26b678f2c07dec01d4242268ec` and
projects every slice independently. All seven individual slices warn on
reviewable LOC and pass the 800-LOC block threshold. Their maximum full physical
footprint can still exceed the 25-file block through required generated outputs
and one `tasks.md` control-plane path; that projected size-only outcome is
recorded separately and routed through the operator-ratified branch stack.

## Technical Context

**Language/Version**: Standalone HTML5, CSS, and vanilla browser JavaScript in
one file per gallery artifact; Python 3.11+ standard-library repository tests
and scripts for validation.

**Primary Dependencies**: None for runtime. Existing repository validation,
payload refresh, and docs reference tooling only.

**Storage**: Editor working state is memory-only per page session. Existing
theme preference remains owned by the canonical gallery head block.

**Testing**: Layer 4 gallery/fill-region assertions, Layer 1 structural
validation, full `python3 tests/speckit-pro/run-all.py`, payload consistency
through `python3 scripts/refresh-release-artifacts.py --check`, docs reference
generation after test changes, and tracked manual `file://` UAT.

**Target Platform**: Browser opening local files over `file://`, with no server,
bundler, package install, sibling asset, or network dependency for content or
controls.

**Project Type**: Public plugin gallery artifact ports.

**Performance Goals**: Each artifact remains readable and responsive directly
from disk with network unavailable; keyboard and clipboard recovery paths do not
depend on asynchronous external services.

**Constraints**: Seven sequential stacked PR slices; no shared gallery
foundation edits; no workflow-stage routing; no export-vocabulary change; no
JSON export kind; no download/import/persistence/URL/server behavior; no repair
to existing shipped templates; source-derived payloads and proofs are regenerated
from source rather than hand edited.

**Scale/Scope**: Seven net-new artifact files, seven manifest `planned` to
`shipped` flips, incremental Layer 4 gallery and fill-region coverage, generated
Claude/Codex payload mirrors, installed-cache fixture/proof refresh, docs test
reference refresh, and cumulative UAT evidence.

## Reviewability Checkpoint

### Preserved Combined Stop History

The prior combined plan measured the seven pinned upstream sources at 4,042
lines and 120,618 bytes. The conservative combined projection was 2,856
reviewable LOC, and the ART-003-average projection was 4,356 reviewable LOC.
Both exceed the 800-LOC block threshold. The runner's `0` LOC diagnostic remains
an advisory blind spot for net-new files and does not override the measured
evidence.

The operator resolved that stop by selecting seven sequential slices. This is a
topology decision, not a reviewability exception.

### Reverified Upstream Measurement

Local reverify source: `/private/tmp/art-005-upstream-58c305be97f47b26b678f2c07dec01d4242268ec/`

| Slice | Artifact | Upstream source | Lines | Bytes | SHA-256 | Role |
|---:|---|---|---:|---:|---|---|
| 1 | `slide-deck` | `09-slide-deck.html` | 592 | 16,527 | `e191d49c28569e5f2ae09ed3bc4dc3f8ef25f90f1c842b1458f7b43ef5153291` | Reader |
| 2 | `concept-explainer` | `15-research-concept-explainer.html` | 368 | 13,558 | `5dd7d3a3866d123fdea1199a3e20d3a31d6305916013b4a2a4a83018765384b3` | Reader |
| 3 | `status-report` | `11-status-report.html` | 528 | 16,382 | `6468f720bab1d016657a9ed25c1049ec42f1810b230f486a5f3130427614bc7c` | Reader |
| 4 | `incident-report` | `12-incident-report.html` | 596 | 15,491 | `e787d6a64eca1ccd77fd9fa18849400356895ed2717ceb26dad2638fcc3261a9` | Reader |
| 5 | `triage-board` | `18-editor-triage-board.html` | 573 | 18,577 | `a2a4ba2691c2532dbe67da5bbeb183bbdee5e9027c7006fba6dce18de7347988` | Producer |
| 6 | `feature-flags` | `19-editor-feature-flags.html` | 663 | 18,908 | `8fd1aa16175614bea196672cd8f9b119b4ddb5b4768bf0bcb4bb05d6588787ab` | Producer |
| 7 | `prompt-tuner` | `20-editor-prompt-tuner.html` | 722 | 21,175 | `b2e1e46643bb908cb01e73600f40a5506a175869a65ad446992f22eacd0b0877` | Producer |

### Projection Method

Assumptions:

- Reviewable LOC counts authored artifact implementation and incremental test
  source, excluding byte-identical canonical block copies and generated mirrors.
- The seven reviewability-counted authored paths in every slice are the new
  template, the source manifest row flip, the two focused test modules, and the
  three active UAT evidence files. Generated paths are a larger physical
  footprint but are source-derived and excluded from reviewable authored counts.
- `tasks.md` checkbox updates are one control-plane path when present. They are
  excluded from the seven implementation-authored paths and path-scoped authored
  LOC, but included in the full physical Git-path count and PR packet.
- ART-003 is the closest realized evidence: one-template slices landed under
  their declared ceilings at 735/758, 724/750, and 408/460 reviewable LOC, all
  warn and none block.
- Readers with no export path use the ART-003 `flowchart` reader as the lower
  local analogue, adjusted for source size and interaction complexity.
- Producers use the ART-003 exporting-template range, with extra budget for the
  ART-005 live-state/fallback schemas while removing upstream `execCommand`,
  extra copy buttons, and undeclared download/import paths.
- Manifest, fill-region literal, docs reference, payload, proof, and UAT files
  are shared or generated surfaces and are serialized in stack order. Their
  existence affects file-count discipline but does not justify parallel edits.
- Projection components below are implementation ceilings. Canonical
  byte-identical gallery blocks, generated payload mirrors, installed-cache
  mirrors, proof/evidence JSON, and docs reference output are excluded. The
  manifest status flip and active `.process` UAT evidence contribute to total
  file count; implementation LOC measurement must separately report whether the
  local reviewability tool counts any of those lines.
- Accessibility checklist remediation adds explicit implementation budget only
  where it changes per-template behavior: slice 1 gains named slide controls,
  current-position text, deterministic focus handling, and focused tests; slice 5
  gains keyboard ticket movement/reordering, movement status, and focused tests.
  Producer status-region and clipboard fallback semantics for slices 6 and 7
  were already budgeted under semantic status and visible fallback coverage, so
  their ceilings do not change. Every revised slice remains below the 800-LOC
  block threshold.
- UX checklist remediation adds explicit implementation budget only where it
  changes per-template behavior: slice 2 gains visible current-count and min/max
  helper/status feedback for concept controls; slice 5 gains visible empty-column
  and filtered-empty feedback. Feature-flag and prompt-tuner empty, invalid,
  dependency, issue, and preview states were already budgeted under schema edge
  coverage and semantic status-region coverage, so their ceilings do not change.
  Responsive review bounds are UAT measurement criteria within existing CSS
  budgets. Every revised slice remains below the 800-LOC block threshold.
- Data-integrity checklist remediation selects exact issue schemas, issue
  ordering, raw/normalized representation, live-export freshness proof,
  clipboard/fallback equality proof, and stale/superseded-attempt evidence
  already included in the producer schema-edge, deterministic export,
  clipboard-fallback, semantic-status, and focused-test budgets. It adds no new
  runtime surface, export kind, persistence, import, download, URL state, server
  behavior, shared foundation change, or implementation feature. The projected
  ceilings remain unchanged: `triage-board` 785, `feature-flags` 780, and
  `prompt-tuner` 790 reviewable LOC.
- Error-handling checklist remediation makes the already-budgeted recovery matrix
  explicit: invocation-time absent/non-callable checks, permission and generic
  rejections, synchronous throw, latest-attempt focus/fallback transitions, and
  both superseded-settlement directions. These are parameterized cases within the
  existing clipboard-fallback and stale-attempt test budget, not new runtime
  surfaces or export paths, so all seven projected ceilings remain unchanged.

| Slice | Artifact | Markup/content | CSS | Behavior JS | Incremental tests | Projected reviewable LOC | Production files | Authored file count | Verdict |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `slide-deck` | 255 | 155 | 105 | 155 | 670 | 1 | 7 | Warn: LOC above 400; authored LOC passes; full-diff path risk is size-only |
| 2 | `concept-explainer` | 205 | 120 | 105 | 105 | 535 | 1 | 7 | Warn: LOC above 400; authored LOC passes; full-diff path risk is size-only |
| 3 | `status-report` | 255 | 140 | 20 | 145 | 560 | 1 | 7 | Warn: LOC above 400; authored LOC passes; full-diff path risk is size-only |
| 4 | `incident-report` | 285 | 150 | 45 | 140 | 620 | 1 | 7 | Warn: LOC above 400; authored LOC passes; full-diff path risk is size-only |
| 5 | `triage-board` | 240 | 145 | 230 | 170 | 785 | 1 | 7 | Warn: LOC above 400; authored LOC passes with 15 LOC headroom; full-diff path risk is size-only |
| 6 | `feature-flags` | 230 | 150 | 245 | 155 | 780 | 1 | 7 | Warn: LOC above 400; authored LOC passes with 20 LOC headroom; full-diff path risk is size-only |
| 7 | `prompt-tuner` | 235 | 145 | 255 | 155 | 790 | 1 | 7 | Warn: LOC above 400; authored LOC passes with 10 LOC headroom; full-diff path risk is size-only |

File thresholds: each slice stays at one production file and below the 6-file
production warning. Each slice has exactly seven reviewability-counted authored
changed paths: one template, one manifest row, two test modules, and three
active UAT evidence files. Slice 1 creates the UAT files; later slices modify
the same three files, so the authored total remains seven rather than growing a
new evidence hierarchy per slice.

Early measurement rule: implementation must measure a slice after template
scaffolding, after focused tests are added, before generated refresh, and again
before PR open. If actual authored LOC plus remaining declared component budget
would reach 800 or more, or if the measured final slice reaches 800 or more,
that slice stops for operator topology review before any branch/PR continuation.
No template is split automatically, and the seven-slice decision is not a size
exception.

The pre-refresh measurements use an explicit pathspec containing only the seven
implementation-authored paths. The pre-PR measurement also runs against the
complete slice diff, counts `tasks.md` and every changed generated output, and
records both ledgers. A complete-diff total-file block may continue only when
every excess path is classified as required source-derived output or the single
control-plane carrier and no other blocker exists.

No individual slice projects an authored-LOC or production-file block. The
maximum physical footprint does project a possible total-file block; the
full-diff result must be recorded honestly as size-only when its excess paths
are exclusively required generated outputs and `tasks.md` control-plane state.
Any authored, correctness, or non-size blocker stops the slice.

## Slice Stack And Branch Plan

Planning only records branch topology; it creates no branch or PR.

| Slice | Branch | Base when created | Template |
|---:|---|---|---|
| 1 | `art-005-gallery-completion-knowledge-reports-editors` | current branch | `slide-deck` |
| 2 | `art-005-gallery-completion-knowledge-reports-editors-slice-2` | slice 1 branch after PR 1 is open | `concept-explainer` |
| 3 | `art-005-gallery-completion-knowledge-reports-editors-slice-3` | slice 2 branch after PR 2 is open | `status-report` |
| 4 | `art-005-gallery-completion-knowledge-reports-editors-slice-4` | slice 3 branch after PR 3 is open | `incident-report` |
| 5 | `art-005-gallery-completion-knowledge-reports-editors-slice-5` | slice 4 branch after PR 4 is open | `triage-board` |
| 6 | `art-005-gallery-completion-knowledge-reports-editors-slice-6` | slice 5 branch after PR 5 is open | `feature-flags` |
| 7 | `art-005-gallery-completion-knowledge-reports-editors-slice-7` | slice 6 branch after PR 6 is open | `prompt-tuner` |

Shared files are owned serially in stack order:

- `speckit-pro/artifact-gallery/manifest.json`
- `tests/speckit-pro/unit/test-artifact-gallery.py`
- `tests/speckit-pro/unit/test-artifact-fill-regions.py`
- `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-runbook.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.json`
- generated payload, installed-cache, proof, evidence, and docs-reference files

## Declared File Operations

The following bare entries are the canonical parser-facing ledger for the
complete seven-slice stack. Detailed per-slice ownership and generated
operations follow below.

- NEW speckit-pro/artifact-gallery/templates/slide-deck.html
- NEW speckit-pro/artifact-gallery/templates/concept-explainer.html
- NEW speckit-pro/artifact-gallery/templates/status-report.html
- NEW speckit-pro/artifact-gallery/templates/incident-report.html
- NEW speckit-pro/artifact-gallery/templates/triage-board.html
- NEW speckit-pro/artifact-gallery/templates/feature-flags.html
- NEW speckit-pro/artifact-gallery/templates/prompt-tuner.html
- MODIFIED speckit-pro/artifact-gallery/manifest.json
- MODIFIED tests/speckit-pro/unit/test-artifact-gallery.py
- MODIFIED tests/speckit-pro/unit/test-artifact-fill-regions.py
- NEW specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-runbook.md
- NEW specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md
- NEW specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.json

Generated operations are source-derived and must be produced by
`python3 scripts/refresh-release-artifacts.py` and
`pnpm --dir docs-site reference:generate`; they are never hand-edited. These are
declared generated/check operations: an idempotent run can leave an output
byte-identical, and a byte-identical output should not be claimed as changed.
Generated mirrors, installed-cache fixtures, proof files, XPLAT evidence, and
docs references are never export-data sources for ART-005 UAT; export evidence
must come from the current source artifact opened directly over `file://`.

The generated-path exclusion follows the repository generated-artifact rule in
`.gitattributes`, which marks `dist/**`, docs reference output, installed-cache
mirrors, proof fixtures, and XPLAT evidence with `merge=generated`, and the
`AGENTS.md` precedent that generated artifacts are a pure function of source and
must be regenerated rather than hand-resolved.

For every slice, the expected generated/check disposition is:

- `python3 scripts/refresh-release-artifacts.py`: rebuild/check the Claude and
  Codex payloads and installed-cache mirrors. Expected ART-005 Git-path deltas,
  if content changes, are:
  - `dist/claude/speckit-pro/artifact-gallery/manifest.json`
  - `dist/claude/speckit-pro/artifact-gallery/templates/<artifact>.html`
  - `dist/codex/speckit-pro/artifact-gallery/manifest.json`
  - `dist/codex/speckit-pro/artifact-gallery/templates/<artifact>.html`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/manifest.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/<artifact>.html`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/manifest.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/<artifact>.html`
- `python3 scripts/refresh-release-artifacts.py`: refresh all current
  installed-cache proof fixtures matched by
  `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof*.json`:
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-file-root.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-mutable.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-source-root.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-mutable.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-partial-root.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-root-mismatch.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-same-root.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-single-product.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-source-mismatch.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-stale-hash.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-traversal-root.json`
- `python3 scripts/refresh-release-artifacts.py`: regenerate XPLAT-009 evidence
  as applicable:
  - `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`
  - `docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json`
  - `docs/ai/specs/.process/XPLAT-009-zero-bash-guard-result.json`
  - `docs/ai/specs/.process/XPLAT-009-release-readiness-result.json`
- `pnpm --dir docs-site reference:generate`: regenerate:
  - `docs-site/src/content/docs/reference/tests.md`

Maximum expected physical Git-path footprint per slice is 33 paths: seven
implementation-authored paths, up to 25 generated/check output paths listed
above, and one possible `tasks.md` checkbox control-plane path. The
payload builder physically rewrites payload directories while rebuilding, but
ART-005 expects tracked content deltas only on the gallery manifest/template
mirrors plus proof/evidence/docs outputs. Any additional generated content diff
must be explained before the slice proceeds.

### Slice 1 - `slide-deck`

Authored operations:

- **NEW** `speckit-pro/artifact-gallery/templates/slide-deck.html`
- MODIFIED `speckit-pro/artifact-gallery/manifest.json`: flip only `slide-deck.status` from `planned` to `shipped`; keep `exports: []`
- MODIFIED `tests/speckit-pro/unit/test-artifact-gallery.py`: add `slide-deck` reader/static contract coverage and any generic ART-005 scanner helpers needed for later slices
- MODIFIED `tests/speckit-pro/unit/test-artifact-fill-regions.py`: add `FLOOR["slide-deck"] = ("deck-title", "slides", "speaker-notes")` and `LIST_SLOTS["slide-deck"] = ("slides",)`
- **NEW** `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-runbook.md`
- **NEW** `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md`
- **NEW** `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.json`

Generated operations: replace `<artifact>` with `slide-deck` in the common
generated path list above.

UAT increment: direct `file://` open, named slide navigation group, named
previous/next or direct-slide controls, current-position text such as `Slide X of
Y`, deterministic focus behavior after control and non-control slide changes, no
auto-rotation, slide navigation by keyboard and scroll, representative content
for `deck-title`, at least two anchored `slides`, speaker notes, offline reload,
complete keyboard traversal, focus visibility, light/dark parity, reduced motion,
color-independent meaning, and responsive review at 360 CSS px and at least 1280
CSS px. Horizontal scroll region checks are recorded as present or
evidence-backed not applicable with selector, role, name, `tabindex`, and
actual-scroll-element evidence.

### Slice 2 - `concept-explainer`

Authored operations:

- **NEW** `speckit-pro/artifact-gallery/templates/concept-explainer.html`
- MODIFIED `speckit-pro/artifact-gallery/manifest.json`: flip only `concept-explainer.status` from `planned` to `shipped`; keep `exports: []`
- MODIFIED `tests/speckit-pro/unit/test-artifact-gallery.py`: add `concept-explainer` reader coverage and transient simulation control checks
- MODIFIED `tests/speckit-pro/unit/test-artifact-fill-regions.py`: add `FLOOR["concept-explainer"] = ("concept-title", "principles", "worked-example", "simulation-scenarios")` and `LIST_SLOTS["concept-explainer"] = ("simulation-scenarios",)`
- MODIFIED `.process/uat-runbook.md`, `.process/uat-results.md`, and `.process/uat-results.json` under the ART-005 feature directory

Generated operations: replace `<artifact>` with `concept-explainer` in the
common generated path list above.

UAT increment: direct `file://` open, transient add/remove/reset and slider
simulation behavior, representative content for all fill slots with at least
two anchored simulation scenarios, offline reload, keyboard traversal, focus,
theme parity, reduced motion, color-independent meaning, and scroll-region
disposition. Boundary-state checks cover visible current-count and min/max
helper/status feedback for add/remove/slider limits, and responsive review at
360 CSS px and at least 1280 CSS px.

### Slice 3 - `status-report`

Authored operations:

- **NEW** `speckit-pro/artifact-gallery/templates/status-report.html`
- MODIFIED `speckit-pro/artifact-gallery/manifest.json`: flip only `status-report.status` from `planned` to `shipped`; keep `exports: []`
- MODIFIED `tests/speckit-pro/unit/test-artifact-gallery.py`: add `status-report` reader coverage and static report no-export checks
- MODIFIED `tests/speckit-pro/unit/test-artifact-fill-regions.py`: add `FLOOR["status-report"] = ("summary", "landed", "in-flight", "blocked", "next-actions")` and `LIST_SLOTS["status-report"] = ("landed", "in-flight", "blocked", "next-actions")`
- MODIFIED `.process/uat-runbook.md`, `.process/uat-results.md`, and `.process/uat-results.json` under the ART-005 feature directory

Generated operations: replace `<artifact>` with `status-report` in the common
generated path list above.

UAT increment: direct `file://` open, complete static report content, at least
two anchored items in each list slot, offline reload, keyboard traversal, focus,
theme parity, reduced motion, color-independent meaning, and scroll-region
disposition. Responsive review covers 360 CSS px and at least 1280 CSS px.

### Slice 4 - `incident-report`

Authored operations:

- **NEW** `speckit-pro/artifact-gallery/templates/incident-report.html`
- MODIFIED `speckit-pro/artifact-gallery/manifest.json`: flip only `incident-report.status` from `planned` to `shipped`; keep `exports: []`
- MODIFIED `tests/speckit-pro/unit/test-artifact-gallery.py`: add `incident-report` reader coverage and anchored report navigation checks
- MODIFIED `tests/speckit-pro/unit/test-artifact-fill-regions.py`: add `FLOOR["incident-report"] = ("summary", "timeline", "impact", "root-cause", "follow-ups")` and `LIST_SLOTS["incident-report"] = ("timeline", "follow-ups")`
- MODIFIED `.process/uat-runbook.md`, `.process/uat-results.md`, and `.process/uat-results.json` under the ART-005 feature directory

Generated operations: replace `<artifact>` with `incident-report` in the common
generated path list above.

UAT increment: direct `file://` open, timeline/report navigation, complete
impact/root-cause/follow-up content, at least two anchored timeline and
follow-up items, offline reload, keyboard traversal, focus, theme parity,
reduced motion, color-independent meaning, and scroll-region disposition.
Responsive review covers 360 CSS px and at least 1280 CSS px.

### Slice 5 - `triage-board`

Authored operations:

- **NEW** `speckit-pro/artifact-gallery/templates/triage-board.html`
- MODIFIED `speckit-pro/artifact-gallery/manifest.json`: flip only `triage-board.status` from `planned` to `shipped`; keep `exports: ["markdown"]`
- MODIFIED `tests/speckit-pro/unit/test-artifact-gallery.py`: add `triage-board` producer coverage for exact label `Copy as Markdown`, absence of hidden copy/download paths, live-state export generation hooks, stale/superseded attempt guards, visible fallback field, semantic status, keyboard-accessible board controls, duplicate ticket IDs, issue appendix ordering, and special-character escaping
- MODIFIED `tests/speckit-pro/unit/test-artifact-fill-regions.py`: add `FLOOR["triage-board"] = ("triage-items", "column-labels")` and `LIST_SLOTS["triage-board"] = ("triage-items",)`
- MODIFIED `.process/uat-runbook.md`, `.process/uat-results.md`, and `.process/uat-results.json` under the ART-005 feature directory

Generated operations: replace `<artifact>` with `triage-board` in the common
generated path list above.

UAT increment: direct `file://` open, memory-only board editing, named board,
columns, tickets, filters, reset, and export affordances, keyboard-operable
ticket movement between columns and reordering within a column, visible ticket
ordering by `now`, `next`, `later`, `cut`, movement/filter status announcements,
explicit empty-column and filtered-empty messages, deterministic Markdown export,
duplicate ticket IDs across columns, fixed issue appendix ordering, empty and
all-empty board states, multiline Unicode/special-character escaping, multiple
issue ordering, live-export freshness sentinels, exact per-attempt
clipboard/fallback equality, superseded copy attempts in both settlement
directions, real clipboard success with read-back or paste equality, unavailable
clipboard, rejected promise, synchronous throw, exact focused fallback text,
reset on reload, keyboard traversal, focus, theme parity, reduced motion,
color-independent meaning, responsive review at 360 CSS px and at least 1280 CSS
px, and scroll-region disposition.

### Slice 6 - `feature-flags`

Authored operations:

- **NEW** `speckit-pro/artifact-gallery/templates/feature-flags.html`
- MODIFIED `speckit-pro/artifact-gallery/manifest.json`: flip only `feature-flags.status` from `planned` to `shipped`; keep `exports: ["markdown"]`
- MODIFIED `tests/speckit-pro/unit/test-artifact-gallery.py`: add `feature-flags` producer coverage for exact label `Copy as Markdown`, single fenced JSON block in Markdown, field/order/schema expectations, JSON round-trip, duplicate group/flag identifiers, raw invalid rollout/dependency values, deterministic issue recording, stale/superseded attempt guards, visible fallback field, semantic status, and no hidden copy/download paths
- MODIFIED `tests/speckit-pro/unit/test-artifact-fill-regions.py`: add `FLOOR["feature-flags"] = ("flags", "environment-notes")` and `LIST_SLOTS["feature-flags"] = ("flags",)`
- MODIFIED `.process/uat-runbook.md`, `.process/uat-results.md`, and `.process/uat-results.json` under the ART-005 feature directory

Generated operations: replace `<artifact>` with `feature-flags` in the common
generated path list above.

UAT increment: direct `file://` open, memory-only flag toggles and dependency
warnings, deterministic Markdown wrapper with one JSON block, null/empty/invalid
edge representation, duplicate group and flag IDs, invalid rollout text,
unavailable dependency text, raw/null issue proof, empty groups/flags, JSON
round-trip byte equality, multiple issue ordering, live-export freshness
sentinels, exact per-attempt clipboard/fallback equality, superseded copy
attempts in both settlement directions, real clipboard success,
unavailable/rejected/throw fallback paths, status-region semantics for copy,
dependency, validation, and issue messages, reset on reload, keyboard traversal,
focus, theme parity, reduced motion, color-independent meaning, responsive
review at 360 CSS px and at least 1280 CSS px, and scroll-region disposition.

### Slice 7 - `prompt-tuner`

Authored operations:

- **NEW** `speckit-pro/artifact-gallery/templates/prompt-tuner.html`
- MODIFIED `speckit-pro/artifact-gallery/manifest.json`: flip only `prompt-tuner.status` from `planned` to `shipped`; keep `exports: ["markdown"]`
- MODIFIED `tests/speckit-pro/unit/test-artifact-gallery.py`: add `prompt-tuner` producer coverage for exact label `Copy as Markdown`, single fenced JSON block in Markdown, template/slot/sample/preview order, first-occurrence field ordering, JSON round-trip, duplicate slot/sample identifiers, raw invalid slot text, deterministic issue recording, stale/superseded attempt guards, visible fallback field, semantic status, and no hidden copy/download paths
- MODIFIED `tests/speckit-pro/unit/test-artifact-fill-regions.py`: add `FLOOR["prompt-tuner"] = ("prompt-variants", "evaluation-notes")` and `LIST_SLOTS["prompt-tuner"] = ("prompt-variants",)`
- MODIFIED `.process/uat-runbook.md`, `.process/uat-results.md`, and `.process/uat-results.json` under the ART-005 feature directory

Generated operations: replace `<artifact>` with `prompt-tuner` in the common
generated path list above.

UAT increment: direct `file://` open, memory-only prompt editing and derived
previews, deterministic Markdown wrapper with one JSON block, slot/sample/order
preservation, first-occurrence field ordering, duplicate slots and sample IDs,
raw invalid slot text, empty template/collections/fields/previews, multiline
Unicode/special-character round-trip, JSON round-trip byte equality, multiple
issue ordering, live-export freshness sentinels, exact per-attempt
clipboard/fallback equality, superseded copy attempts in both settlement
directions, real clipboard success, unavailable/rejected/throw fallback paths,
status-region semantics for copy, validation, editor-state, and preview
messages, reset on reload, keyboard traversal, focus, theme parity, reduced
motion, color-independent meaning, responsive review at 360 CSS px and at least
1280 CSS px, scroll-region disposition, and stack-wide closeout totals.

### Archival Evidence Contract

Active UAT files grow serially during the seven implementation slices:

- `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-runbook.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.json`

Each slice first commits a source checkpoint after source, tests, generated
outputs, and the existing evidence carriers are stable. UAT then re-executes
the complete cumulative row set for every artifact shipped through that slice,
sets the JSON's top-level `sourceCommit` to that checkpoint, and records results
in a later evidence commit. This prevents rows tested on an older branch head
from being presented under a newer cumulative run identity.

Post-merge archival preserves the same evidence under:

- `docs/ai/specs/.process/ART-005-uat-runbook.md`
- `docs/ai/specs/.process/ART-005-uat-results.md`
- `docs/ai/specs/.process/ART-005-uat-results.json`
- `docs/ai/specs/.process/ART-005-uat-harness/` if an implementation harness is committed

Accessibility evidence rows keep the human-readable `observedResult` and include
structured fields for focus order, focused fallback targets, scroll-region
selector/role/name/`tabindex` and actual-scroll-element evidence, status-region
semantics, and audited-token or measured contrast evidence when the row exercises
those requirements.

UX evidence rows record the exercised viewport width, page-level horizontal
overflow result, clipped or overlapping text observation, documented named-scroll
exceptions, and the visible text/status-region feedback for empty, limit,
invalid, dependency, and filtered-no-result states where applicable.

Data-integrity evidence rows record manifest/export parity, baseline and
attempted export text, freshness sentinel comparisons, JSON parse and
`JSON.stringify(value, null, 2)` round-trip equality, expected versus observed
collection/field/issue order, raw and normalized issue values, exact
clipboard/fallback equality for the current invocation, and stale/superseded copy
attempt outcomes.

## Constitution Check

**I. Plugin Structure Compliance**: Pass. Gallery source remains under
`speckit-pro/artifact-gallery/`; repository-only tests remain under
`tests/speckit-pro/`. Slice verification includes Layer 1 structural validation.

**II. Cross-Platform Runtime & Script Safety**: Pass. Runtime artifacts use
single-file browser HTML/CSS/JS only. Repository tooling remains Python 3.11+
standard library; any optional UAT harness must use standard-library Python and
no active Bash or `jq`.

**III. Semantic Versioning**: Pass for planning. No plugin version edit is
planned in ART-005.

**IV. Test Coverage Before Merge**: Pass. Every slice adds or extends focused
Layer 4 gallery and fill-region coverage before implementation, then runs Layer
1, Layer 4, the default suite, generated-artifact checks, docs reference
generation after test edits, and slice-specific UAT evidence.

**V. Conventional Commits**: Pass for planning. No commit is made in this phase.
Implementation PR titles must pass the repository release-readiness title gate.

**VI. KISS, Simplicity & YAGNI**: Pass. The design keeps each artifact
standalone and explicit, adds no shared runtime abstraction, and rejects
speculative storage, import, routing, or export changes.

Post-design re-check: Pass. The Phase 0/Phase 1 design artifacts preserve the
same constraints and introduce no constitution violation.

## Project Structure

### Documentation (this feature)

```text
specs/art-005-gallery-completion-knowledge-reports-editors/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── editor-export-contract.md
│   ├── gallery-template-contract.md
│   ├── slice-topology-contract.md
│   └── uat-evidence-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
speckit-pro/artifact-gallery/
├── SPA-CONTRACT.md
├── brand-kit.css
├── manifest.json
├── theme-toggle.html
└── templates/
    ├── slide-deck.html
    ├── concept-explainer.html
    ├── status-report.html
    ├── incident-report.html
    ├── triage-board.html
    ├── feature-flags.html
    └── prompt-tuner.html

tests/speckit-pro/unit/
├── test-artifact-gallery.py
└── test-artifact-fill-regions.py

dist/
├── claude/speckit-pro/artifact-gallery/
└── codex/speckit-pro/artifact-gallery/
```

**Structure Decision**: Use the existing gallery layout. Each port is one
template file plus one manifest value flip; shared tests, generated payloads,
docs references, and UAT records are serialized by slice.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
