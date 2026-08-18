# Reviewability Slice 3: Decision Ports

## Scope

Two decision/export ART-004 ports: `visual-designs` and `component-variants`. This slice performs the second serial manifest/test/generated integration update for the remaining two status flips and the live-state export/fallback checks.

## Authored File Operations

- NEW speckit-pro/artifact-gallery/templates/visual-designs.html
- NEW speckit-pro/artifact-gallery/templates/component-variants.html
- MODIFIED speckit-pro/artifact-gallery/manifest.json
- MODIFIED tests/speckit-pro/unit/test-artifact-gallery.py
- MODIFIED tests/speckit-pro/unit/test-artifact-fill-regions.py

## Generated File Operations

Generated payload, installed-cache, proof, release-readiness, and docs-reference paths are listed in `plan.md` under Slice 3. They are derived outputs and must not be hand-edited.

## Estimate Rationale

This slice carries 1,122 required planning source lines from pinned upstream templates plus the added decision-export implementation for selection, rationale validation, clipboard success/refusal, and stale-copy protection. Shared manifest and test overhead is assigned serially to this slice.

## Final Gate Inputs

- Primary surface: UI gallery artifacts
- Projected reviewable LOC: 520
- Projected production files: 2
- Projected total files: 5

