# Quickstart: ART-004 Gallery Completion - Design & Prototyping

This guide validates the approved three-slice ART-004 plan.

## Plan Gate

Run each setup-mode reviewability gate with the fixed runner:

```bash
cd "$(git rev-parse --show-toplevel)"
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

### Slice 1 `file://` UAT Evidence

Playwright Chromium 151.0.7922.138 exercised the authored source files directly
over `file://` on 2026-08-18 at a 320 by 900 viewport. This run completes the
browser-independent keyboard-scroll matrix in T018. The Safari-specific T019
result is recorded below as a separate browser run.

| Artifact | Regions | Keyboard route | Source order | ArrowRight result | Focus and name | Focus exit | Result |
|---|---:|---|---|---|---|---|---|
| `code-approaches` | 3 | Tab | 1, 2, 3 | Every region moved from `scrollLeft=0` to `40` | Every region exposed its specific `aria-label`, `role="group"`, and a 2 px solid focus outline | Tab left every region | Pass |
| `implementation-plan` | 2 | Tab | 1, 2 | Every region moved from `scrollLeft=0` to `40` | Every region exposed its specific `aria-label`, `role="group"`, and a 2 px solid focus outline | Tab left every region | Pass |
| `module-map` | 6 | Tab; Enter opened each of the five `Show source` disclosures | 1 through 6 | Every region moved from `scrollLeft=0` to `40` | Every region exposed its specific `aria-label`, `role="group"`, and a 2 px solid focus outline | Tab left every region | Pass |

Observed accessible names, in source order:

- `code-approaches`: `Code example for the inline timer approach`, `Code
  example for the shared debounce hook approach`, and `Code example for the
  third-party debounce library approach`.
- `implementation-plan`: `Offline draft sync data flow diagram` and `Risks and
  mitigations for offline draft sync`.
- `module-map`: `Offline draft sync module request path diagram`, `Draft editor
  source example`, `Local draft store source example`, `Push and replay source
  example`, `Drafts table migration source example`, and `Conflict worker
  source example`.

Safari status: pass. Safari 26.6.1 exercised the same authored source files over
`file://` on 2026-08-18 with a requested 320 by 900 window and a measured 336
by 825 content viewport. The active sequential keyboard route was **Tab**.
All 11 regions were reached in source order, exposed the same specific names
and `role="group"`, showed the 2 px solid focus outline, moved from
`scrollLeft=0` to `40` with ArrowRight, and released focus with Tab. The five
`module-map` source disclosures opened with Enter before their code regions
entered the focus sequence. No positive `tabindex` and no keyboard trap were
observed.

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

### Slice 2 `file://` UAT Evidence

Chromium 149.0.7827.55 exercised all four authored source files directly over
`file://` on 2026-08-18 with a 360 by 900 viewport and network access disabled.
The optional canonical Google Fonts request failed as intended; the canonical
system/generic fallback stack remained readable. Light and dark body contrast
measured 16.42:1 and 13.94:1. Every page fit the viewport, exposed no positive
`tabindex` or export-looking control, showed a 2 px solid focus outline, and
suppressed template-added motion when reduced motion was requested.

| Artifact | Keyboard interaction and state | Reset or cleanup | Wide region | Result |
|---|---|---|---|---|
| `design-system` | Tab reached the spacing ruler and demo controls; Space toggled the checkbox | The alternate checkbox state was visible | Ruler `326/752`; ArrowRight moved its own `scrollLeft` | Pass |
| `animation-prototype` | Enter completed and reset the task; Enter selected the linear easing | Task returned to not-done without changing easing | Snippet `326/1066`; ArrowRight moved its own `scrollLeft` | Pass |
| `interaction-prototype` | Enter moved the first retained view down | Reset restored all six views and removed drag/indicator state | No intentional horizontal region | Pass |
| `svg-illustrations` | Tab reached the named read-only illustration strip; all three IDs, captions, and descriptions remained present | Read-only; no reset required | Strip `328/1680`; ArrowRight moved its own `scrollLeft` | Pass |

The first Chromium run found a real interaction-port overflow: the document was
412 px wide at a 360 px viewport. Zero-minimum mobile grid/content tracks and
wrapping for the pinned source note reduced the document to exactly 360 px; the
desktop two-column layout remained intact.

Safari status: pass. Safari 26.6.1 exercised isolated direct `file://` runs on
2026-08-18 with a requested 360 by 900 window and a measured 360 by 825 content
viewport. The active full-control route was **Option-Tab**. All required
controls and named scroll regions were reached in source order, showed a 2 px
solid outline, and released focus. Enter or Space operated theme, checkbox,
task/easing, reorder, and reset paths. The three declared scrollers had real
overflow and moved with ArrowRight. Every page fit within the measured viewport,
used the canonical fallback stack, exposed no positive `tabindex`, and showed
no export-looking control.

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

### Slice 3 `file://` UAT Evidence

Playwright Chromium and WebKit exercised both decision ports directly over
`file://` on 2026-08-18 with network resources blocked. Seventeen scenario
groups passed: exact prompt and Markdown payload order; missing choice, missing
rationale, and whitespace-only rationale validation without a clipboard call;
all six refusal modes (unavailable API, non-callable `writeText`, synchronous
exception, rejected promise, denied permission, and local-file restriction);
focused/selectable fallback parity; stale-fallback clearing; and stale-settle
suppression. Live background, direction, padding, border, shadow, base-variant,
and reset changes were reflected in the next payload.

At a 360 by 900 Chromium viewport, both documents fit the viewport, sequential
keyboard navigation reached and operated the labelled native controls, focus
was visibly outlined, no positive `tabindex` was present, reduced motion was
honored, and the canonical fallback font stack preserved content and controls
offline. Light and dark body contrast measured 16.42:1 and 13.94:1. The
component snippet had real internal overflow and ArrowRight moved its own
scroll position from 0 to 29.

Safari 26.6.1 then exercised both files with a requested 360 by 900 window and
a measured 360 by 825 content viewport. The active full-control route was
**Option-Tab**. Six visual-design controls and fifteen component-variant
controls were reached in logical source order and operated with ArrowRight,
Space, or Enter. The component snippet measured 285 px client width against
401 px scroll width and moved from `scrollLeft=0` to `scrollLeft=29` with an
element-targeted WebDriver ArrowRight key. Headless WebKit completed the
remaining offline, semantics, contrast, and reduced-motion matrix but did not
synthesize a generic scroller's browser-default ArrowRight action; the real
Safari result above is the native-engine evidence for that path.

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
