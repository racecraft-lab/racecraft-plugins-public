# Implementation Plan: ART-004 Gallery Completion - Design & Prototyping

**Branch**: `art-004-gallery-completion-design-prototyping` | **Date**: 2026-08-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/art-004-gallery-completion-design-prototyping/spec.md`

**Status**: G3 blocked pending human-approved split. Plan artifacts are complete; Checklist and Tasks generation must not proceed from this combined slice.

## Summary

Complete the six planned design and prototyping gallery entries as Racecraft-branded, browser-native, self-contained HTML artifacts, while absorbing ART-020's horizontal-scroll accessibility repair and global guard. The architecture keeps each new artifact as its own single-file vertical capability, copies canonical `BRAND-KIT` and `GALLERY-HEAD` blocks verbatim, adapts the pinned upstream mechanisms to the existing gallery contract, flips only six manifest statuses, and verifies the combined slice through Layer 1, Layer 4, direct `file://` UAT, and generated-artifact consistency.

The selected interview answers are binding design rationale: "Functional fidelity", "Pin one commit", "Base variant", "One direction", "Absorb ART-020", "Mark superseded", "One combined slice", and "Stop and split".

## Technical Context

**Language/Version**: Browser-native HTML, CSS, and JavaScript for gallery artifacts; Python 3.11+ standard library for repository validation.

**Primary Dependencies**: None for the shipped artifacts. No framework, bundler, package install, sibling asset, active Bash dependency, or `jq`.

**Storage**: In-memory DOM state only for artifact controls and decisions. Catalog state remains the existing JSON manifest with exactly six status-only flips.

**Testing**: Python 3.11+ standard-library Layer 1 and Layer 4 suites through `python3 tests/speckit-pro/run-all.py`; direct `file://` browser UAT for controls, sliders, linked screens, clipboard fallback, focus order, and horizontal keyboard scrolling.

**Target Platform**: Local browser over `file://` and the repository's Claude/Codex generated plugin payloads.

**Project Type**: Static single-file artifact gallery plus repository validation.

**Performance Goals**: Each artifact opens directly from disk without network access or build work; interaction feedback is immediate in the browser; no runtime persistence.

**Constraints**: Preserve all functional sections and interactions from the pinned sources; only repeated sample volume may shrink. Apply ART-020's repair before using its pattern in new ports. Do not centralize a production helper because the single-file rule requires local behavior; keep the global keyboard rule in repository validation.

**Scale/Scope**: Six new ad-hoc gallery artifacts, five existing horizontal-scroll repairs across three shipped artifacts, one manifest status-only update set, one Layer 4 guard expansion, release payload/proof regeneration, and generated docs reference refresh.

**Reviewability Budget**: Primary surface: UI gallery artifacts. Secondary surfaces: harness/adapter verification, seed/config catalog metadata, generated release artifacts, and generated docs reference. Projected reviewable LOC: 865. Projected production files: 9. Projected total files: 11 authored files, with generated files listed separately below. Budget result: block for one combined slice because reviewable LOC exceeds 800 and production files exceed 8.

## Declared File Operations

Authored implementation operations:

- NEW speckit-pro/artifact-gallery/templates/visual-designs.html
- NEW speckit-pro/artifact-gallery/templates/design-system.html
- NEW speckit-pro/artifact-gallery/templates/component-variants.html
- NEW speckit-pro/artifact-gallery/templates/animation-prototype.html
- NEW speckit-pro/artifact-gallery/templates/interaction-prototype.html
- NEW speckit-pro/artifact-gallery/templates/svg-illustrations.html
- MODIFIED speckit-pro/artifact-gallery/templates/code-approaches.html
- MODIFIED speckit-pro/artifact-gallery/templates/implementation-plan.html
- MODIFIED speckit-pro/artifact-gallery/templates/module-map.html
- MODIFIED speckit-pro/artifact-gallery/manifest.json
- MODIFIED tests/speckit-pro/unit/test-artifact-gallery.py

Generated operations from `scripts/refresh-release-artifacts.py` and `pnpm --dir docs-site reference:generate`; do not hand-edit these paths:

- GENERATED NEW dist/claude/speckit-pro/artifact-gallery/templates/visual-designs.html
- GENERATED NEW dist/claude/speckit-pro/artifact-gallery/templates/design-system.html
- GENERATED NEW dist/claude/speckit-pro/artifact-gallery/templates/component-variants.html
- GENERATED NEW dist/claude/speckit-pro/artifact-gallery/templates/animation-prototype.html
- GENERATED NEW dist/claude/speckit-pro/artifact-gallery/templates/interaction-prototype.html
- GENERATED NEW dist/claude/speckit-pro/artifact-gallery/templates/svg-illustrations.html
- GENERATED NEW dist/codex/speckit-pro/artifact-gallery/templates/visual-designs.html
- GENERATED NEW dist/codex/speckit-pro/artifact-gallery/templates/design-system.html
- GENERATED NEW dist/codex/speckit-pro/artifact-gallery/templates/component-variants.html
- GENERATED NEW dist/codex/speckit-pro/artifact-gallery/templates/animation-prototype.html
- GENERATED NEW dist/codex/speckit-pro/artifact-gallery/templates/interaction-prototype.html
- GENERATED NEW dist/codex/speckit-pro/artifact-gallery/templates/svg-illustrations.html
- GENERATED MODIFIED dist/claude/speckit-pro/artifact-gallery/templates/code-approaches.html
- GENERATED MODIFIED dist/claude/speckit-pro/artifact-gallery/templates/implementation-plan.html
- GENERATED MODIFIED dist/claude/speckit-pro/artifact-gallery/templates/module-map.html
- GENERATED MODIFIED dist/claude/speckit-pro/artifact-gallery/manifest.json
- GENERATED MODIFIED dist/codex/speckit-pro/artifact-gallery/templates/code-approaches.html
- GENERATED MODIFIED dist/codex/speckit-pro/artifact-gallery/templates/implementation-plan.html
- GENERATED MODIFIED dist/codex/speckit-pro/artifact-gallery/templates/module-map.html
- GENERATED MODIFIED dist/codex/speckit-pro/artifact-gallery/manifest.json
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/visual-designs.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/design-system.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/component-variants.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/animation-prototype.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/interaction-prototype.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/svg-illustrations.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/visual-designs.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/design-system.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/component-variants.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/animation-prototype.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/interaction-prototype.html
- GENERATED NEW tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/svg-illustrations.html
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/code-approaches.html
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/implementation-plan.html
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/module-map.html
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/manifest.json
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/code-approaches.html
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/implementation-plan.html
- GENERATED MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/module-map.html
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

Declared authored counts: 6 new, 5 modified, 11 total authored files. Generated integration declaration: 24 generated new paths and 34 generated modified paths, 58 generated paths total.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Pre-design check:

- **I. Plugin Structure Compliance**: Pass. The plan keeps repository-only tests under `tests/speckit-pro/` and gallery source under `speckit-pro/artifact-gallery/`.
- **II. Cross-Platform Runtime & Script Safety**: Pass. New validation remains Python 3.11+ standard library. No active Bash or `jq` dependency is introduced.
- **III. Semantic Versioning**: Pass. No manual version edits are planned.
- **IV. Test Coverage Before Merge**: Pass with required evidence. The feature adds Layer 4 guard coverage and relies on the existing Layer 1/4/5 default suite before completion.
- **V. Conventional Commits**: Not applicable in this phase because no commit is allowed.
- **VI. KISS, Simplicity & YAGNI**: Pass for architecture. The plan uses local single-file behavior instead of a new shared runtime. The reviewability budget blocks the combined slice and prevents implementation from proceeding without a new split decision.

Post-design check:

- Design artifacts keep the same constraints: no dependencies, no shared production helper, structured JSON manifest update, Python standard-library tests, and generated outputs derived only from source.
- Reviewability is blocking: 865 projected reviewable LOC and 9 production files exceed the block thresholds. No typed exception is present or honored. The split decision is the recorded answer "Stop and split"; ART-004 remains full fidelity and ART-020 remains absorbed.

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
    `-- keyboard-scroll-guard-contract.md
```

### Source Code (repository root)

```text
speckit-pro/artifact-gallery/
|-- manifest.json
`-- templates/
    |-- visual-designs.html
    |-- design-system.html
    |-- component-variants.html
    |-- animation-prototype.html
    |-- interaction-prototype.html
    |-- svg-illustrations.html
    |-- code-approaches.html
    |-- implementation-plan.html
    `-- module-map.html

tests/speckit-pro/unit/
`-- test-artifact-gallery.py

dist/
|-- claude/speckit-pro/artifact-gallery/
`-- codex/speckit-pro/artifact-gallery/

tests/speckit-pro/unit/fixtures/plugin-bash-confinement/
`-- installed-cache/
    |-- claude/speckit-pro/artifact-gallery/
    `-- codex/speckit-pro/artifact-gallery/
```

**Structure Decision**: Use the existing artifact-gallery source tree and existing unit test file. Each new HTML file is a self-contained vertical capability in the one combined delivery slice, while shared manifest, test, payload, proof, and generated-doc work is serialized.

## Architecture

1. Repair the ART-020 horizontal-scroll pattern first in `code-approaches`, `implementation-plan`, and `module-map`, then reuse that contract in every new port.
2. Port the six pinned upstream templates from commit `58c305be97f47b26b678f2c07dec01d4242268ec`, carrying the exact attribution header and source filename in the manifest.
3. Copy the canonical `BRAND-KIT` and `GALLERY-HEAD` blocks verbatim into each new artifact.
4. Keep each artifact's behavior local: controls, selection, rationale, fallback, slider state, drag state, and inline SVG references all live in the same HTML file.
5. Preserve all functional sections and interactions. Compact only repeated sample groups allowed by the Functional Fidelity Inventory.
6. Flip exactly six manifest `status` values from `planned` to `shipped`; leave identifiers, categories, stages, triggers, sources, usage text, signal vocabulary, and export declarations unchanged.
7. Extend the Layer 4 guard so every shipped artifact with horizontal overflow must declare keyboard reachability and an accessible name. Add the synthetic negative fixture for a declared region missing `tabindex`.
8. Regenerate release payloads and generated references from source; do not hand-edit generated mirrors.

## Source Evidence

Pinned upstream source baseline:

| Artifact | Upstream file | Required planning lines | Local `wc -l` evidence |
|---|---|---:|---:|
| `visual-designs` | `02-exploration-visual-designs.html` | 516 | 515 |
| `design-system` | `05-design-system.html` | 630 | 629 |
| `component-variants` | `06-component-variants.html` | 606 | 605 |
| `animation-prototype` | `07-prototype-animation.html` | 456 | 455 |
| `interaction-prototype` | `08-prototype-interaction.html` | 397 | 396 |
| `svg-illustrations` | `10-svg-illustrations.html` | 493 | 492 |
| **Total** | | **3,098** | **3,092** |

The reconciliation uses the ART-004 design-concept baseline of 3,098 lines because it is the fixed planning input. The local `git -C .specify/presets/.cache/art004-upstream/repo show <commit>:<file> | wc -l` commands report 3,092 newline-terminated lines; this does not reduce the reviewability concern because the forward estimate is still 865 projected reviewable LOC.

## Reviewability Gate Evidence

Machine-readable gate inputs:

- Primary surface: UI gallery artifacts
- Projected reviewable LOC: 865
- Projected production files: 9
- Projected total files: 11

Run the plan-time helpers after this plan is written:

- `python3 -m speckit_pro_runner` with helper `estimate-reviewable-loc`, input `{"plan_file":"specs/art-004-gallery-completion-design-prototyping/plan.md"}`
- `python3 -m speckit_pro_runner` with helper `reviewability-gate`, input `{"mode_name":"setup","target":"specs/art-004-gallery-completion-design-prototyping/plan.md"}`

Recorded helper results:

- Initial `estimate-reviewable-loc` runner status: `ok`; helper stdout status: `pass`; projected: `0`; declared files: `new=6`, `modified=5`, `total_entries=11`, `production=0`. Reconciled as insufficient to unblock because the current helper classifier does not count the HTML gallery artifacts or Python unit test that define this feature's reviewable surface.
- Initial `reviewability-gate` runner status: `ok`; helper stdout status: `warn`; parsed `reviewable_loc=9`, `production_files=8`, `total_files=11`. Reconciled as a parsing artifact from threshold prose, not the ART-004 budget, so the plan now records the machine-readable gate inputs above and must be rerun.
- Final `reviewability-gate` runner status: `expected_failure`; helper exit code: `1`; helper stdout status: `block`; parsed `reviewable_loc=865`, `production_files=9`, `total_files=11`, `primary_surfaces=["UI gallery artifacts"]`.
- Final blockers: `reviewable LOC 865 exceeds block threshold 800`; `production files 9 exceeds block threshold 8`.

G3 result: blocked. The binding recorded decision is "Stop and split"; Checklist, Tasks, and implementation must not proceed from this combined-slice plan unless the parent records a new human-approved split or updated gate evidence.

## Verification Design

- Red test: today's five existing horizontal scroll containers fail the new global assertion before repair.
- Green test: all existing and new horizontal overflow containers are focusable, named, and declared; the synthetic negative fixture still proves the guard rejects a declared region without a keyboard route.
- Per-port Layer 4 checks: manifest/file presence, attribution header, canonical-block markers, fill-region inventory, export declaration, and offline constraints.
- Manual `file://` UAT matrix: both themes, keyboard-only operation, slider behavior, linked screens, live selection/rationale exports, clipboard refusal fallback, focus order, and horizontal arrow-key scrolling.
- Completion gates: `python3 tests/speckit-pro/run-all.py`, `scripts/refresh-release-artifacts.py`, `pnpm --dir docs-site reference:generate` when tracked test/source inputs change, and generated-artifact consistency checks.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| One combined slice exceeds reviewability block thresholds: 865 projected reviewable LOC and 9 production files. | The setup interview selected "One combined slice" while also choosing "Absorb ART-020" and full "Functional fidelity". | Reducing fidelity or removing ART-020 would contradict the recorded answers. The accepted fallback is "Stop and split", so this violation is not approved for implementation from this plan. |

## Final Plan Gate Inputs

These values are repeated at the end of the plan so the `reviewability-gate` helper reads the ART-004 budget values rather than nearby threshold prose:

- Primary surface: UI gallery artifacts
- Projected reviewable LOC: 865
- Projected production files: 9
- Projected total files: 11
