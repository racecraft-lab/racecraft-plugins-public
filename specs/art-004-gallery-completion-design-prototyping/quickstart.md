# Quickstart: ART-004 Gallery Completion - Design & Prototyping

This guide validates the approved three-slice ART-004 plan.

## Plan Gate

Run each setup-mode reviewability gate with the fixed runner:

```bash
cd /Users/fredrickgabelmann/Documents/Business_Documents/RSE_Documents/Projects/racecraft-plugins-public/.worktrees/art-004-gallery-completion-design-prototyping
env PYTHONPATH=/Users/fredrickgabelmann/Documents/Business_Documents/RSE_Documents/Projects/racecraft-plugins-public/.worktrees/fix-codex-same-task-autopilot/speckit-pro /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m speckit_pro_runner
```

Use helper `reviewability-gate`, `mode_name=setup`, and these targets:

- `specs/art-004-gallery-completion-design-prototyping/contracts/reviewability-slice-1-keyboard-foundation.md`
- `specs/art-004-gallery-completion-design-prototyping/contracts/reviewability-slice-2-read-only-ports.md`
- `specs/art-004-gallery-completion-design-prototyping/contracts/reviewability-slice-3-decision-ports.md`

Also run helper `estimate-reviewable-loc` against `specs/art-004-gallery-completion-design-prototyping/plan.md`; record its classifier limitation because it does not count this repository's HTML/Python review surface.

## Slice 1 Validation

Expected authored files:

- `speckit-pro/artifact-gallery/templates/code-approaches.html`
- `speckit-pro/artifact-gallery/templates/implementation-plan.html`
- `speckit-pro/artifact-gallery/templates/module-map.html`
- `tests/speckit-pro/unit/test-artifact-gallery.py`

Expected checks:

- Red proof catches the five existing affected containers before repair.
- Green proof confirms declared regions are focusable, named, and swept.
- Manual `file://` UAT confirms focused horizontal regions scroll by keyboard.

## Slice 2 Validation

Expected authored files:

- `speckit-pro/artifact-gallery/templates/design-system.html`
- `speckit-pro/artifact-gallery/templates/animation-prototype.html`
- `speckit-pro/artifact-gallery/templates/interaction-prototype.html`
- `speckit-pro/artifact-gallery/templates/svg-illustrations.html`
- `speckit-pro/artifact-gallery/manifest.json`
- `tests/speckit-pro/unit/test-artifact-gallery.py`
- `tests/speckit-pro/unit/test-artifact-fill-regions.py`

Expected checks:

- Four files load directly over `file://` while offline.
- Each required fill region and list-slot rule is covered.
- No read-only port exposes prompt, Markdown, or other export affordances.

## Slice 3 Validation

Expected authored files:

- `speckit-pro/artifact-gallery/templates/visual-designs.html`
- `speckit-pro/artifact-gallery/templates/component-variants.html`
- `speckit-pro/artifact-gallery/manifest.json`
- `tests/speckit-pro/unit/test-artifact-gallery.py`
- `tests/speckit-pro/unit/test-artifact-fill-regions.py`

Expected checks:

- Both files load directly over `file://` while offline.
- Decision radio state, rationale validation, prompt export, Markdown export, clipboard refusal fallback, and stale-copy protection work from live state.
- Manifest changes are the two remaining status flips only.

## Common Completion Gates

After each implementation slice, run:

```bash
python3 tests/speckit-pro/run-all.py
python3 scripts/refresh-release-artifacts.py
pnpm --dir docs-site reference:generate
python3 scripts/refresh-release-artifacts.py --check
pnpm --dir docs-site reference:check
```

Generated outputs must be derived from source and not hand-edited.

