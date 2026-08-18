# Reviewability Slice 1: Keyboard Foundation

## Scope

ART-020's five existing horizontal-scroll repairs across `code-approaches`, `implementation-plan`, and `module-map`, plus the manifest-wide Layer 4 guard, synthetic negative fixture, and keyboard UAT.

## Authored File Operations

- MODIFIED speckit-pro/artifact-gallery/templates/code-approaches.html
- MODIFIED speckit-pro/artifact-gallery/templates/implementation-plan.html
- MODIFIED speckit-pro/artifact-gallery/templates/module-map.html
- MODIFIED tests/speckit-pro/unit/test-artifact-gallery.py

## Generated File Operations

Generated payload, installed-cache, proof, release-readiness, and docs-reference paths are listed in `plan.md` under Slice 1. They are derived outputs and must not be hand-edited.

## Estimate Rationale

The only production files are the three existing templates receiving five keyboard-scroll repairs. The Layer 4 guard and fixture are reviewable test work but not production gallery surface. No ART-004 upstream template source lines are added in this slice.

## Final Gate Inputs

- Primary surface: UI gallery artifacts
- Projected reviewable LOC: 160
- Projected production files: 3
- Projected total files: 4

