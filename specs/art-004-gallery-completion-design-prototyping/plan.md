# Implementation Plan: ART-004 Gallery Completion - Design & Prototyping

**Branch**: `art-004-gallery-completion-design-prototyping` | **Date**: 2026-08-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/art-004-gallery-completion-design-prototyping/spec.md`

**Status**: Active Plan topology revised after human approval: three ordered slices. The failed combined-slice gate remains historical evidence only.

## Summary

Complete the six planned design and prototyping gallery entries as Racecraft-branded, browser-native, self-contained HTML artifacts, while absorbing ART-020's horizontal-scroll repair and global guard. The active implementation topology is now three serial slices: keyboard foundation, four read-only ports, and two decision/export ports.

The selected interview answers remain binding design rationale: "Functional fidelity", "Pin one commit", "Base variant", "One direction", "Absorb ART-020", "Mark superseded", "One combined slice", and "Stop and split". The first topology is preserved as history: the combined slice blocked at G3, then the user approved "approve three slices" on 2026-08-17.

## Technical Context

**Language/Version**: Browser-native HTML, CSS, and JavaScript for gallery artifacts; Python 3.11+ standard library for repository validation.

**Primary Dependencies**: None. No dependency, framework, build step, sibling asset, active Bash dependency, or `jq`.

**Storage**: In-memory DOM state only. The catalog remains the existing JSON manifest with six status-only flips across slices 2 and 3.

**Testing**: Python 3.11+ standard-library Layer 1 and Layer 4 suites through `python3 tests/speckit-pro/run-all.py`; manual direct `file://` UAT for controls, sliders, linked screens, clipboard fallback across absent API, rejected write, denied permission, and local-file restriction paths, focus order, horizontal keyboard scrolling, Safari keyboard reachability, visible focus, names/roles/states, live status, reduced motion, non-color meaning, typeface fallback readability, and both-theme contrast.

**Target Platform**: Local browser over `file://`, plus regenerated Claude and Codex plugin payloads.

**Project Type**: Static single-file artifact gallery plus repository validation.

**Performance Goals**: Each artifact opens directly from disk without network access or build work; interaction feedback is immediate in the browser; no runtime persistence.

**Constraints**: Preserve every distinct upstream section, state, motion timing, decision surface, and interaction. Only repeated sample volume named in the spec may shrink. For read-only rows whose manifest `exports` value is `[]`, preserve upstream informational content but omit upstream export, copy, and download controls instead of rendering active, disabled, or placeholder affordances. Apply the ART-020 repair before new ports inherit the keyboard-scroll pattern. Every interactive control must be keyboard operable, visibly focused, named, stateful where applicable, and free of positive `tabindex`; Safari UAT records the active Tab or Option-Tab path. Theme/color work uses audited brand-kit WCAG AA pairings, preserves non-color meaning, uses canonical brand-kit system/generic font fallbacks for offline typeface failure, and suppresses template-added motion under reduced-motion preference. Centralize no new production helper.

**Scale/Scope**: Three ordered slices:

1. Keyboard foundation: ART-020's five repairs across three existing templates, the global guard, its synthetic negative fixture, and keyboard UAT.
2. Read-only ports: `design-system`, `animation-prototype`, `interaction-prototype`, and `svg-illustrations`.
3. Decision ports: `visual-designs` and `component-variants`, live-state prompt/Markdown exports, validation, and clipboard fallback.

**Reviewability Budget**: Active topology gates per slice. Combined historical estimate: 865 reviewable LOC, 9 production files, 11 authored files, blocked. Approved slice estimates: slice 1 = 160 reviewable LOC / 3 production files / 4 authored files; slice 2 = 590 reviewable LOC / 4 production files / 7 authored files; slice 3 = 520 reviewable LOC / 2 production files / 5 authored files.

## Historical Combined Gate

The first Plan attempt kept "One combined slice". The plan-time gate blocked that topology because it reconciled the six pinned upstream sources totaling 3,098 lines with a forward estimate of 865 reviewable LOC and 9 production files. The binding fallback answer was "Stop and split". The user then approved three ordered slices on 2026-08-17. The combined slice is no longer active implementation scope.

## Declared File Operations

Generated paths are declared with `GENERATED` and must be derived from `scripts/refresh-release-artifacts.py` or `pnpm --dir docs-site reference:generate`, never hand-edited. Shared manifest, test, payload, proof, and generated-doc paths are assigned serially; repeated modifications across ordered slices are explicit and not parallel-safe.

### Slice 1: Keyboard Foundation

Authored operations:

- MODIFIED speckit-pro/artifact-gallery/templates/code-approaches.html
- MODIFIED speckit-pro/artifact-gallery/templates/implementation-plan.html
- MODIFIED speckit-pro/artifact-gallery/templates/module-map.html
- MODIFIED tests/speckit-pro/unit/test-artifact-gallery.py

Generated operations:

- GENERATED MODIFIED dist/claude/speckit-pro/artifact-gallery/templates/code-approaches.html
- GENERATED MODIFIED dist/claude/speckit-pro/artifact-gallery/templates/implementation-plan.html
- GENERATED MODIFIED dist/claude/speckit-pro/artifact-gallery/templates/module-map.html
- GENERATED MODIFIED dist/codex/speckit-pro/artifact-gallery/templates/code-approaches.html
- GENERATED MODIFIED dist/codex/speckit-pro/artifact-gallery/templates/implementation-plan.html
- GENERATED MODIFIED dist/codex/speckit-pro/artifact-gallery/templates/module-map.html
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/code-approaches.html
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/implementation-plan.html
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/module-map.html
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/code-approaches.html
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/implementation-plan.html
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/module-map.html
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-file-root.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-mutable.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-source-root.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-mutable.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-partial-root.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-root-mismatch.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-same-root.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-single-product.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-source-mismatch.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-stale-hash.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-traversal-root.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof.json
- GENERATED MODIFIED docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json
- GENERATED MODIFIED docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json
- GENERATED MODIFIED docs/ai/specs/.process/XPLAT-009-zero-bash-guard-result.json
- GENERATED MODIFIED docs/ai/specs/.process/XPLAT-009-release-readiness-result.json
- GENERATED MODIFIED docs-site/src/content/docs/reference/tests.md
- GENERATED MODIFIED docs-site/src/content/docs/reference/source-vs-dist.md

Gate input: [contracts/reviewability-slice-1-keyboard-foundation.md](./contracts/reviewability-slice-1-keyboard-foundation.md)

### Slice 2: Read-Only Ports

Authored operations:

- NEW speckit-pro/artifact-gallery/templates/design-system.html
- NEW speckit-pro/artifact-gallery/templates/animation-prototype.html
- NEW speckit-pro/artifact-gallery/templates/interaction-prototype.html
- NEW speckit-pro/artifact-gallery/templates/svg-illustrations.html
- MODIFIED speckit-pro/artifact-gallery/manifest.json
- MODIFIED tests/speckit-pro/unit/test-artifact-gallery.py
- MODIFIED tests/speckit-pro/unit/test-artifact-fill-regions.py

Generated operations:

- GENERATED NEW dist/claude/speckit-pro/artifact-gallery/templates/design-system.html
- GENERATED NEW dist/claude/speckit-pro/artifact-gallery/templates/animation-prototype.html
- GENERATED NEW dist/claude/speckit-pro/artifact-gallery/templates/interaction-prototype.html
- GENERATED NEW dist/claude/speckit-pro/artifact-gallery/templates/svg-illustrations.html
- GENERATED NEW dist/codex/speckit-pro/artifact-gallery/templates/design-system.html
- GENERATED NEW dist/codex/speckit-pro/artifact-gallery/templates/animation-prototype.html
- GENERATED NEW dist/codex/speckit-pro/artifact-gallery/templates/interaction-prototype.html
- GENERATED NEW dist/codex/speckit-pro/artifact-gallery/templates/svg-illustrations.html
- GENERATED MODIFIED dist/claude/speckit-pro/artifact-gallery/manifest.json
- GENERATED MODIFIED dist/codex/speckit-pro/artifact-gallery/manifest.json
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/design-system.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/animation-prototype.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/interaction-prototype.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/svg-illustrations.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/design-system.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/animation-prototype.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/interaction-prototype.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/svg-illustrations.html
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/manifest.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/manifest.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-file-root.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-mutable.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-source-root.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-mutable.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-partial-root.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-root-mismatch.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-same-root.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-single-product.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-source-mismatch.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-stale-hash.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-traversal-root.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof.json
- GENERATED MODIFIED docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json
- GENERATED MODIFIED docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json
- GENERATED MODIFIED docs/ai/specs/.process/XPLAT-009-zero-bash-guard-result.json
- GENERATED MODIFIED docs/ai/specs/.process/XPLAT-009-release-readiness-result.json
- GENERATED MODIFIED docs-site/src/content/docs/reference/tests.md
- GENERATED MODIFIED docs-site/src/content/docs/reference/source-vs-dist.md

Gate input: [contracts/reviewability-slice-2-read-only-ports.md](./contracts/reviewability-slice-2-read-only-ports.md)

### Slice 3: Decision Ports

Authored operations:

- NEW speckit-pro/artifact-gallery/templates/visual-designs.html
- NEW speckit-pro/artifact-gallery/templates/component-variants.html
- MODIFIED speckit-pro/artifact-gallery/manifest.json
- MODIFIED tests/speckit-pro/unit/test-artifact-gallery.py
- MODIFIED tests/speckit-pro/unit/test-artifact-fill-regions.py

Generated operations:

- GENERATED NEW dist/claude/speckit-pro/artifact-gallery/templates/visual-designs.html
- GENERATED NEW dist/claude/speckit-pro/artifact-gallery/templates/component-variants.html
- GENERATED NEW dist/codex/speckit-pro/artifact-gallery/templates/visual-designs.html
- GENERATED NEW dist/codex/speckit-pro/artifact-gallery/templates/component-variants.html
- GENERATED MODIFIED dist/claude/speckit-pro/artifact-gallery/manifest.json
- GENERATED MODIFIED dist/codex/speckit-pro/artifact-gallery/manifest.json
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/visual-designs.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/component-variants.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/visual-designs.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/component-variants.html
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/manifest.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/manifest.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-file-root.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-mutable.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-source-root.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-mutable.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-partial-root.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-root-mismatch.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-same-root.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-single-product.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-source-mismatch.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-stale-hash.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-traversal-root.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof.json
- GENERATED MODIFIED docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json
- GENERATED MODIFIED docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json
- GENERATED MODIFIED docs/ai/specs/.process/XPLAT-009-zero-bash-guard-result.json
- GENERATED MODIFIED docs/ai/specs/.process/XPLAT-009-release-readiness-result.json
- GENERATED MODIFIED docs-site/src/content/docs/reference/tests.md
- GENERATED MODIFIED docs-site/src/content/docs/reference/source-vs-dist.md

Gate input: [contracts/reviewability-slice-3-decision-ports.md](./contracts/reviewability-slice-3-decision-ports.md)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Pre-design check:

- **I. Plugin Structure Compliance**: Pass. Source remains under `speckit-pro/`; repository-only tests remain under `tests/speckit-pro/`.
- **II. Cross-Platform Runtime & Script Safety**: Pass. Test and helper work stays Python 3.11+ standard library. No active Bash or `jq` dependency is added.
- **III. Semantic Versioning**: Pass. No manual version edits are planned.
- **IV. Test Coverage Before Merge**: Pass. The plan uses existing registered Layer 4 files: `test-artifact-gallery.py` and `test-artifact-fill-regions.py`; `suite-manifest.json` already lists both.
- **V. Conventional Commits**: Not applicable in this executor phase because commits are forbidden.
- **VI. KISS, Simplicity & YAGNI**: Pass. Each artifact keeps local single-file behavior; no shared production runtime is introduced.

Post-design check:

- The combined topology remains blocked historical evidence.
- The active three-slice topology is non-blocking if all three slice gate contracts return `pass` or `warn` with no blockers.
- Shared integration files are serial slice ownership, not parallel-safe files.

## Project Structure

### Documentation (this feature)

```text
specs/art-004-gallery-completion-design-prototyping/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
`-- contracts/
    |-- decision-export-contract.md
    |-- gallery-artifact-contract.md
    |-- keyboard-scroll-guard-contract.md
    |-- reviewability-slice-1-keyboard-foundation.md
    |-- reviewability-slice-2-read-only-ports.md
    `-- reviewability-slice-3-decision-ports.md
```

### Source Code (repository root)

```text
speckit-pro/artifact-gallery/
|-- manifest.json
`-- templates/
    |-- code-approaches.html
    |-- implementation-plan.html
    |-- module-map.html
    |-- design-system.html
    |-- animation-prototype.html
    |-- interaction-prototype.html
    |-- svg-illustrations.html
    |-- visual-designs.html
    `-- component-variants.html

tests/speckit-pro/unit/
|-- test-artifact-gallery.py
`-- test-artifact-fill-regions.py
```

**Structure Decision**: Use the existing gallery source tree and existing registered Layer 4 test files. No implementation files are edited during Plan. Implementation slices are ordered and serialized around shared manifest/test/generated paths.

## Architecture

1. Slice 1 repairs the five existing horizontal-scroll regions and lands the global guard before any new ports copy the pattern.
2. Slice 2 ports the four read-only artifacts with functional fidelity and no export affordances; upstream download/export controls become in-page informational content only when their catalog row declares `exports: []`.
3. Slice 3 ports the two decision artifacts with live-state prompt/Markdown exports and clipboard fallback.
4. Each new HTML file remains a self-contained vertical capability; canonical blocks are copied verbatim; no new shared runtime exists.
5. Manifest status flips are serial: four in slice 2, two in slice 3.
6. `test-artifact-fill-regions.py` changes in slices 2 and 3 because ART-004 adds new fill-region floors and list-slot coverage.
7. Payload, proof, and generated-reference work runs after each slice from authoritative source.

## Source Evidence

Pinned upstream source baseline:

| Artifact | Slice | Upstream file | Required planning lines | Local `wc -l` evidence |
|---|---:|---|---:|---:|
| `design-system` | 2 | `05-design-system.html` | 630 | 629 |
| `animation-prototype` | 2 | `07-prototype-animation.html` | 456 | 455 |
| `interaction-prototype` | 2 | `08-prototype-interaction.html` | 397 | 396 |
| `svg-illustrations` | 2 | `10-svg-illustrations.html` | 493 | 492 |
| `visual-designs` | 3 | `02-exploration-visual-designs.html` | 516 | 515 |
| `component-variants` | 3 | `06-component-variants.html` | 606 | 605 |
| **Total** | | | **3,098** | **3,092** |

Slice 1 has no new ART-004 upstream source; it repairs already shipped gallery templates using ART-020 evidence. Slice 2 carries 1,976 required planning source lines and no export code. Slice 3 carries 1,122 required planning source lines plus the decision/export contract. The slice estimates are derived from those surfaces and shared overhead, not by dividing 865 by three.

## Reviewability Gate Evidence

Gate command for each durable input:

```bash
cd "$(git rev-parse --show-toplevel)"
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner
```

Inputs:

- Slice 1 target: `specs/art-004-gallery-completion-design-prototyping/contracts/reviewability-slice-1-keyboard-foundation.md`
- Slice 2 target: `specs/art-004-gallery-completion-design-prototyping/contracts/reviewability-slice-2-read-only-ports.md`
- Slice 3 target: `specs/art-004-gallery-completion-design-prototyping/contracts/reviewability-slice-3-decision-ports.md`
- Plan estimator target: `specs/art-004-gallery-completion-design-prototyping/plan.md`

Recorded results:

| Check | Runner status | Helper status | Parsed values | Warnings | Blockers |
|---|---|---|---|---|---|
| Slice 1 reviewability gate | `ok` | `pass` | `reviewable_loc=160`, `production_files=3`, `total_files=4`, `primary_surfaces=["UI gallery artifacts"]` | none | none |
| Slice 2 reviewability gate | `ok` | `warn` | `reviewable_loc=590`, `production_files=4`, `total_files=7`, `primary_surfaces=["UI gallery artifacts"]` | `reviewable LOC 590 exceeds warn threshold 400` | none |
| Slice 3 reviewability gate | `ok` | `warn` | `reviewable_loc=520`, `production_files=2`, `total_files=5`, `primary_surfaces=["UI gallery artifacts"]` | `reviewable LOC 520 exceeds warn threshold 400` | none |
| Plan `estimate-reviewable-loc` | `ok` | `pass` | `projected=0`, `new=6`, `modified=6`, `total_entries=12`, `production=0` | none | none |

G3 result: non-blocking for the approved three-slice topology. The plan estimator result is recorded only as classifier evidence: it does not count this repository's HTML artifact files or Python test files, so the durable slice gate contracts are the reviewability authority for this revised Plan. Tasks-mode `reviewability-gate` remains deferred by the installed runner; the fallback chain is non-blocking because G0 setup evidence, the three G3 slice results, and the human-approved split remain valid.

## Verification Design

- Red test: today's five existing horizontal scroll containers fail the new global assertion before slice 1 repair.
- Green test: all existing and new horizontal overflow containers are focusable, named, and declared; the negative fixture still proves the guard rejects a declared region without a keyboard route.
- Per-port Layer 4 checks: manifest/file presence, attribution header, canonical-block markers, fill-region inventory, export declaration, and offline constraints.
- Accessibility UAT matrix: every selection, slider, linked-screen or reorder, copy, fallback, reset, theme, and horizontal-scroll control is reachable in logical source order, operable by keyboard, visibly focused, and not trapped. Safari rows state whether Tab or Option-Tab is required under the active Safari keyboard-navigation setting.
- Semantic UAT matrix: every control and custom control group exposes a name, role, state, and value; inputs and choices have visible labels or instructions; export status uses a polite atomic live region; fallback textarea focus is the only copy-status path that intentionally moves focus.
- Presentation UAT matrix: light and dark themes use audited brand-kit WCAG AA pairings or measured equivalents for text, meaningful non-text indicators, focus indicators, status/error text, and SVG/palette annotations; selected, active, invalid, disabled/loading, drag insertion, theme/background, and SVG/palette meaning is also available without color.
- Motion UAT matrix: with reduced motion requested, template-added animation, transitions, smooth scrolling, and motion-like feedback are removed or replaced while the same current state, reset, and control meaning remain visible.
- Manual `file://` UAT matrix: both themes, keyboard-only operation, slider behavior, linked screens or reorderable views, read-only no-export checks, live selection/rationale exports, clipboard refusal fallback across unavailable API, rejected write, denied permission, and local-file restriction paths, focus order, typeface fallback readability, and horizontal arrow-key scrolling. Each row records the precondition, action, expected visible current-state outcome, and reset or cleanup outcome.
- Completion gates per slice: `python3 tests/speckit-pro/run-all.py`, `scripts/refresh-release-artifacts.py`, `pnpm --dir docs-site reference:generate` when tracked source/test inputs change, and generated-artifact consistency checks. Manifest drift and stale, missing, extra, truncated, rewritten, or byte-mismatched generated outputs are blocking failures until regenerated from authoritative source.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Historical combined slice exceeded block thresholds. | The setup interview selected "One combined slice" while also choosing "Absorb ART-020" and "Functional fidelity". | The binding fallback was "Stop and split". The user approved three slices, so the violating combined topology is no longer active. |
