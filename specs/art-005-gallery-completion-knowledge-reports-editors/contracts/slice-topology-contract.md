# Contract: Slice Topology

ART-005 has one specification and one workflow. Delivery uses seven sequential
stacked PR slices, one template per slice.

## Stack Order

| Slice | Branch | Template | Parent |
|---:|---|---|---|
| 1 | `art-005-gallery-completion-knowledge-reports-editors` | `slide-deck` | current feature branch |
| 2 | `art-005-gallery-completion-knowledge-reports-editors-slice-2` | `concept-explainer` | slice 1 branch after PR 1 opens |
| 3 | `art-005-gallery-completion-knowledge-reports-editors-slice-3` | `status-report` | slice 2 branch after PR 2 opens |
| 4 | `art-005-gallery-completion-knowledge-reports-editors-slice-4` | `incident-report` | slice 3 branch after PR 3 opens |
| 5 | `art-005-gallery-completion-knowledge-reports-editors-slice-5` | `triage-board` | slice 4 branch after PR 4 opens |
| 6 | `art-005-gallery-completion-knowledge-reports-editors-slice-6` | `feature-flags` | slice 5 branch after PR 5 opens |
| 7 | `art-005-gallery-completion-knowledge-reports-editors-slice-7` | `prompt-tuner` | slice 6 branch after PR 6 opens |

## Atomic Slice Rule

Each slice contains exactly:

- one new `speckit-pro/artifact-gallery/templates/<id>.html`
- one corresponding `manifest.json` status flip from `planned` to `shipped`
- incremental Layer 4 gallery coverage
- incremental fill-region coverage
- source-derived payload, installed-cache, proof, evidence, and docs reference
  regeneration
- slice-specific active UAT evidence

This is seven reviewability-counted authored paths per slice: the template, the
source manifest, `tests/speckit-pro/unit/test-artifact-gallery.py`,
`tests/speckit-pro/unit/test-artifact-fill-regions.py`, and the three active
UAT files under
`specs/art-005-gallery-completion-knowledge-reports-editors/.process/`. Slice 1
creates the active UAT files; later slices modify them.

No slice may change a later template, a later manifest row, shared foundation
files, export vocabulary, workflow-stage routing, or existing shipped templates.

## Generated Footprint

Generated operations are regeneration/check steps, not authored edits. They are
excluded from the reviewability authored-path count because the repository marks
`dist/**`, docs reference output, installed-cache mirrors, proof fixtures, and
XPLAT evidence as generated in `.gitattributes`, and requires regeneration from
source after merges.

Each slice can physically affect up to 25 generated/check paths: four
Claude/Codex dist gallery mirror paths, four Claude/Codex installed-cache gallery
mirror paths, twelve `installed-cache-proof*.json` fixtures, four XPLAT-009
evidence files, and `docs-site/src/content/docs/reference/tests.md`. Together
with the seven authored paths, the maximum expected physical Git-path footprint
is 32 paths per slice. Byte-identical generated outputs are valid and must not
be claimed as changed.

## Reviewability Gate

Every slice is evaluated independently against:

- warn above 400 reviewable LOC
- block above 800 reviewable LOC
- warn above 6 production files
- block above 8 production files
- warn above 15 total files
- block above 25 total files
- block above one primary surface without a ratified exception

If a slice reaches a block threshold, planning or implementation stops that
slice for an operator decision. A blocked slice is not split automatically, and
no exception is inferred from the seven-slice topology.

Implementation must measure each slice before generated refresh and before PR
creation. If actual authored LOC plus remaining declared work would reach 800 or
more, the slice stops before crossing the block threshold.
