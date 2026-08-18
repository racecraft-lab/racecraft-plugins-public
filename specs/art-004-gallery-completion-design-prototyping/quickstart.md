# Quickstart: ART-004 Gallery Completion - Design & Prototyping

This guide validates the approved three-slice ART-004 plan.

## Plan Gate

Run each setup-mode reviewability gate with the fixed runner:

```bash
cd /Users/fredrickgabelmann/Documents/Business_Documents/RSE_Documents/Projects/racecraft-plugins-public/.worktrees/art-004-gallery-completion-design-prototyping
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner
```

Use helper `reviewability-gate`, `mode_name=setup`, and these targets:

- `specs/art-004-gallery-completion-design-prototyping/contracts/reviewability-slice-1-keyboard-foundation.md`
- `specs/art-004-gallery-completion-design-prototyping/contracts/reviewability-slice-2-read-only-ports.md`
- `specs/art-004-gallery-completion-design-prototyping/contracts/reviewability-slice-3-decision-ports.md`

Also run helper `estimate-reviewable-loc` against `specs/art-004-gallery-completion-design-prototyping/plan.md`; record its classifier limitation because it does not count this repository's HTML/Python review surface.

Do not run a separate tasks-mode reviewability gate. The installed runner
supports setup mode for this helper, so the recorded fallback remains the G0
setup evidence, the three G3 slice results (`160/pass`, `590/warn`,
`520/warn`), and the human-approved split.

## Slice 1 Validation

Expected authored files:

- `speckit-pro/artifact-gallery/templates/code-approaches.html`
- `speckit-pro/artifact-gallery/templates/implementation-plan.html`
- `speckit-pro/artifact-gallery/templates/module-map.html`
- `tests/speckit-pro/unit/test-artifact-gallery.py`

Expected checks:

- Red proof catches the five existing affected containers before repair.
- Green proof confirms declared regions are focusable, named, and swept.
- The global guard rejects positive `tabindex` in shipped artifacts and keeps the
  negative fixture proving a declared region without `tabindex="0"` fails.
- Manual `file://` UAT confirms focused horizontal regions scroll by keyboard,
  show visible focus, expose specific names, and remain reachable in source
  order in Safari using Tab or Option-Tab according to the active browser
  setting.

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

- Four files load directly over `file://` while offline, including readable
  text and functional controls when brand typefaces are unavailable.
- Each required fill region and list-slot rule is covered.
- No read-only port exposes prompt, Markdown, or other export affordances.
- All read-only controls, including sliders, task/easing controls, linked-screen
  or reorder controls, reset paths, theme controls, and horizontal-scroll
  regions, are keyboard operable with visible focus, names, roles, states, and
  labels or instructions where applicable.
- Both themes retain audited brand-kit WCAG AA pairings, convey meaning without
  color alone, and suppress template-added motion when reduced motion is
  requested.

## Slice 3 Validation

Expected authored files:

- `speckit-pro/artifact-gallery/templates/visual-designs.html`
- `speckit-pro/artifact-gallery/templates/component-variants.html`
- `speckit-pro/artifact-gallery/manifest.json`
- `tests/speckit-pro/unit/test-artifact-gallery.py`
- `tests/speckit-pro/unit/test-artifact-fill-regions.py`

Expected checks:

- Both files load directly over `file://` while offline, including readable text
  and functional controls when brand typefaces are unavailable.
- Decision radio state, rationale validation, prompt export, Markdown export,
  clipboard refusal fallback for unavailable API, rejected write, denied
  permission, and local-file restriction paths, stale fallback invalidation, and
  stale-copy protection work from live state.
- Manifest changes are the two remaining status flips only.
- Radio groups, rationale fields, copy controls, fallback textarea, reset paths,
  and horizontal-scroll regions are keyboard operable with visible focus,
  logical focus order, names, roles, states, visible labels or instructions, and
  no positive `tabindex`.
- `#export-status` is a polite atomic live status region; invalid input, copy
  success, clipboard refusal, fallback reveal, and stale-attempt suppression
  update status text without moving focus except for the focused fallback
  textarea on clipboard refusal.

## Manual file:// UAT Interaction Matrix

| Artifact | Interaction | Observable outcome | Reset or cleanup outcome |
|---|---|---|---|
| `visual-designs` | Change light/dark background | The checked background option changes and every visible stage reflects the selected theme. | Selecting the alternate background updates the same stages again; reload returns any non-persistent state to the authored default. |
| `visual-designs` | Select a visual direction and enter rationale | Exactly one direction radio is checked, the visible direction label/note are the export source, and a non-whitespace rationale is accepted. | Selecting another direction replaces the active decision; clearing rationale blocks export and focuses the rationale field. |
| `component-variants` | Move padding slider | `#pad-out`, the live card padding, and the snippet padding line all show the new value. | Reset returns padding to `20px` and refreshes card/snippet/export context. |
| `component-variants` | Change border and shadow controls | The checked border option, shadow checkbox state, live card treatment, and snippet lines agree. | Reset returns border to `hairline`, shadow to `shown`, clears transient hover-only emphasis, and refreshes card/snippet/export context. |
| `component-variants` | Select base variant and rationale | All six states remain visible while exactly one base-variant radio plus rationale define the export payload. | Selecting another base variant replaces the active decision; clearing rationale blocks export and focuses the rationale field. |
| `animation-prototype` | Activate task completion | The task row visibly changes to the done state and the staged/keyframe context remains visible. | Activating the task again returns the row to the initial not-done state while preserving selected easing. |
| `animation-prototype` | Change easing | The active easing button and timing/snippet context reflect the selected easing. | Selecting a different easing visibly replaces the active choice; task reset does not change easing. |
| `interaction-prototype` | Reorder retained views or linked screens | The current order or active screen is visible; drag exposes an insertion indicator and the DOM/order changes on drop. | Cleanup removes `.dragging`/indicator state; reset returns to the initial retained order or first retained screen. |
| `svg-illustrations` | Inspect Queue, Retry, and Fan-out/Fan-in illustrations | All three concepts, captions, palette rules, and inline SVG content are visible without external assets. | Read-only; no reset is required and no download/export/copy control is present. |
| Exportable artifacts | Use prompt and Markdown copy controls after a valid decision | Status text announces the copy result and the payload reflects current visible state, selection, and rationale. Unavailable Clipboard API, missing or non-callable `writeText`, synchronous exception, rejected write, denied permission, and local-file restriction outcomes use the same refusal message and fallback path. | A newer copy attempt wins over older pending results; clipboard refusal reveals and focuses the selectable fallback payload without retrying or reporting success. |
| Exportable artifacts | Attempt export with missing choice or rationale | The page announces the exact missing input, focuses the first missing control, and does not call the clipboard. | Completing the missing input enables the next valid copy attempt; any prior fallback is hidden and cleared before the validation status so stale payload text is not visible beside invalid state. |
| Exportable artifacts | Inspect status and fallback semantics | `#export-status` exposes `role="status"`, `aria-live="polite"`, and `aria-atomic="true"`; fallback textarea has a label and the same payload as the refused copy. | Advisory status changes do not move focus; only fallback reveal focuses the textarea for manual copy. |
| Exportable artifacts | Change selection, rationale, live controls, or reset after a fallback is visible | The prior fallback is hidden and `#fallback-field` is cleared before the changed state can be copied or rejected. | The next valid refused copy reveals a freshly serialized payload from the current visible state. |
| Horizontal-scroll regions | Focus a declared wide region and press the horizontal arrow key | Scroll position changes, visible focus remains present, and the region keeps its specific accessible name. | Moving focus away leaves content readable; reload returns browser scroll state to default. |
| Horizontal-scroll regions in Safari | Reach each declared wide region through sequential keyboard navigation | Each region is reached in source order using Tab or Option-Tab according to the active Safari keyboard-navigation setting; no positive `tabindex` is present. | Focus can leave the region by keyboard and no trap is observed. |
| All interactive controls | Navigate by keyboard only | Selection, slider, linked-screen or reorder, copy, fallback, reset, theme, and horizontal-scroll controls are reached in logical order, operate without pointer input, expose visible focus, and expose name/role/state/value where applicable. | Focus can leave each control path; reload or reset restores authored defaults. |
| Both themes | Inspect text, controls, focus indicators, status/error text, and SVG/palette annotations | Light and dark themes use audited brand-kit WCAG AA pairings or measured equivalents: 4.5:1 for normal text and 3:1 for large text or meaningful non-text indicators. | Switching themes preserves readable content, focus visibility, and the same semantic state. |
| Offline typeface failure | Review all six artifacts with brand typefaces unavailable | Text and controls remain readable through canonical brand-kit system or generic font stacks; hierarchy and state meaning do not depend on brand face identity, icon fonts, or private-use glyphs. | Restoring network font availability changes only typeface rendering, not available content, controls, labels, status, or export payload fields. |
| Non-color meaning | Inspect selected, active, invalid, disabled/loading, drag insertion, SVG/palette, and theme/background states | Each state has text, shape, icon, border, pattern, position, control state, or other non-color cue in addition to color. | Removing color distinction does not remove the state meaning needed for review. |
| Reduced motion | Review artifacts with reduced motion requested | Template-added animation, transitions, smooth scrolling, and motion-like feedback are removed or replaced while current state, reset outcome, and control meaning remain visible. | Restoring normal motion does not change saved in-page state or export payload content. |

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
Manifest drift and stale, missing, extra, truncated, rewritten, or
byte-mismatched generated outputs are blocking failures until the authoritative
source is corrected and the generated checks pass.
