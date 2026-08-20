# ART-005 UAT Runbook

Feature: ART-005 gallery completion knowledge reports/editors
Artifact: `slide-deck`
Driver: `manual`
Template path: `speckit-pro/artifact-gallery/templates/slide-deck.html`
Results path: `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md`
JSON path: `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.json`

T019 created the active UAT carriers. T022 executed the Slice 1 row set against
source checkpoint `660bfe9ce8365afbe6d98af28dd26eccf46a2c9e` on
2026-08-18. The connected browser was unavailable, so the operator-authorized
Playwright MCP fallback supplied browser interaction and observation while the
contract driver remained `manual`.

## Manual Setup

1. Check out the source checkpoint commit produced for T022.
2. From the repository root, resolve the template URL as
   `file://<repo-root>/speckit-pro/artifact-gallery/templates/slide-deck.html`.
3. Open that exact `file://` URL in the selected browser.
4. Record the operating system, browser name/version, network condition, theme
   condition, reduced-motion condition, color-mode condition, and viewport width.
5. Record executable rows in
   `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md`.
6. Record only executable rows with real `pass` or `fail` evidence in the JSON
   after T022. Keep source-backed `not_applicable` rows distinct from browser
   observations.

## Slice 1 Executable Rows

SD-UAT-001 through SD-UAT-018 passed at the Slice 1 source checkpoint. The
steps below remain the reusable cumulative procedure for later slice
checkpoints; the normalized observations are in `uat-results.json`.

### SD-UAT-001 Direct file open

1. Open
   `file://<repo-root>/speckit-pro/artifact-gallery/templates/slide-deck.html`.
2. Confirm the document title is `Slide Deck - RACE-421 Release Confidence`.
3. Confirm the visible deck title is `RACE-421 Release Confidence`.
4. Confirm the page loads without a server and without a visible error state.

### SD-UAT-002 Complete representative fills

1. Open the same `file://` URL.
2. Confirm `deck-title` content is present: release review kicker, title,
   audience/date/presenter context, and subtitle.
3. Confirm at least two anchored slide articles exist; the expected Slice 1 set
   is `#slides-readiness-map`, `#slides-evidence-lane`, and
   `#slides-release-call`.
4. Confirm speaker notes are present under `#speaker-notes-title` and match the
   visible slide order.

### SD-UAT-003 Named slide navigation

1. Locate `nav.deck-nav`.
2. Confirm it has the accessible name `Slide deck navigation`.
3. Confirm `#previous-slide` has accessible name `Previous slide` and controls
   `#deck-stage`.
4. Confirm `#next-slide` has accessible name `Next slide` and controls
   `#deck-stage`.
5. Confirm `#slide-count` is visible and has a polite status/live-region
   disposition.

### SD-UAT-004 Previous/next and keyboard/wheel navigation

1. Start on `Slide 1 of 3`.
2. Activate `Next` and confirm slide 2 becomes visible.
3. Activate `Previous` and confirm slide 1 becomes visible.
4. Use `ArrowRight`, `ArrowDown`, and `PageDown` to move forward.
5. Use `ArrowLeft`, `ArrowUp`, and `PageUp` to move backward.
6. Use `Home` and `End` to jump to the first and last slides.
7. Use a wheel or trackpad gesture over `#deck-stage`; confirm one bounded
   slide step per accepted gesture.

### SD-UAT-005 Current-position updates

1. Start on slide 1 and confirm `#slide-count` reads `Slide 1 of 3`.
2. Navigate to slide 2 and confirm `#slide-count` reads `Slide 2 of 3`.
3. Navigate to slide 3 and confirm `#slide-count` reads `Slide 3 of 3`.
4. Attempt to move before slide 1 or after slide 3 and confirm the position text
   remains clamped to the valid range.

### SD-UAT-006 Control vs non-control focus

1. Focus `#next-slide`, activate it, and confirm focus remains on the invoked
   button after the control-driven slide change.
2. Focus `#previous-slide`, activate it, and confirm focus remains on the
   invoked button after the control-driven slide change.
3. Use keyboard navigation over the document and confirm focus moves to the
   active `.slide`.
4. Use wheel navigation over `#deck-stage` and confirm focus moves to the active
   `.slide`.

### SD-UAT-007 Hidden slide accessibility

1. Start on slide 1.
2. Inspect inactive slide articles.
3. Confirm inactive slides carry `hidden`, `inert`, and `aria-hidden="true"`.
4. Confirm the active slide carries `aria-hidden="false"` and is not hidden or
   inert.
5. Traverse keyboard focus and confirm inactive slide content is not reachable.

### SD-UAT-008 No autorotation

1. Open the deck and leave it idle on slide 1 for 30 seconds.
2. Confirm `#slide-count` remains `Slide 1 of 3`.
3. Confirm no automatic timer advances the slide or changes focus.
4. Repeat while focused on `#deck-stage`.

### SD-UAT-009 Offline reload

1. Open the deck once from `file://`.
2. Disable the network connection or use the browser's offline mode.
3. Reload the same `file://` URL.
4. Confirm the deck content, navigation controls, theme control, and slide
   behavior still work. Remote fonts may fall back; the UAT claim is local
   artifact usability, not font fetch success.

### SD-UAT-010 Complete keyboard traversal

1. Reload the deck.
2. Press `Tab` from the browser viewport.
3. Record every keyboard stop in order, including selector, role, accessible
   name, and visible focus evidence.
4. Use `Shift+Tab` to traverse backward.
5. Navigate all slides and repeat traversal where the enabled/disabled state of
   `Previous` and `Next` changes.

### SD-UAT-011 Focus visibility

1. Keyboard-focus the theme toggle.
2. Keyboard-focus each enabled deck navigation button.
3. Use keyboard or wheel navigation to programmatically focus each active slide.
4. Confirm every focused control or slide has a visible focus indicator.

### SD-UAT-012 Light/dark parity

1. Open the deck in the default theme.
2. Capture the active theme state and visible content.
3. Toggle `Dark theme`.
4. Confirm the same content, controls, focus indicators, and slide states remain
   available in light and dark modes.
5. Reload and confirm the stored or system theme path still presents a usable
   deck.

### SD-UAT-013 Reduced motion

1. Enable the operating system or browser `prefers-reduced-motion: reduce`
   condition.
2. Reload the `file://` URL.
3. Navigate through all slides.
4. Confirm slide changes remain functional and no motion is required to
   understand state.
5. Confirm reduced-motion CSS removes meaningful transition/animation duration.

### SD-UAT-014 Color-independent meaning

1. Open slide 3.
2. Inspect `Status: Ready`, `Status: Watch`, and `Status: Stop`.
3. Confirm the state is conveyed by visible text.
4. Confirm the status legend also uses distinct shapes: circle, square, and
   block.
5. Confirm the decision remains understandable without relying on hue alone.

### SD-UAT-015 Horizontal scroll actual-element check

1. Before browser execution, confirm the source still has no
   `overflow-x: auto` or `overflow-x: scroll` declarations.
2. Confirm the source uses `overflow-x: hidden` only on `html` and `body`.
3. In the browser, check both 360 CSS px and desktop width for page-level
   horizontal overflow.
4. If no meaningful horizontal scroll region exists, keep the source-backed
   `not_applicable` JSON row and record that no actual scroll element exists.
5. If a meaningful horizontal scroll region appears, replace the N/A row with a
   real observation that names the selector, role, accessible name, `tabindex`,
   horizontal-overflow evidence, and actual scroll element.

### SD-UAT-016 360 CSS px layout

1. Set the viewport width to exactly 360 CSS px.
2. Reload the `file://` URL.
3. Navigate all slides.
4. Confirm there is no page-level horizontal overflow.
5. Confirm no visible text, controls, notes, or slide content are clipped or
   overlapping.
6. Record any named horizontal scroll exceptions. The expected Slice 1 route is
   none unless SD-UAT-015 finds a real scroll region.

### SD-UAT-017 >=1280 CSS px layout

1. Set the viewport width to at least 1280 CSS px.
2. Reload the `file://` URL.
3. Navigate all slides.
4. Confirm there is no page-level horizontal overflow.
5. Confirm no visible text, controls, notes, or slide content are clipped or
   overlapping.
6. Record any named horizontal scroll exceptions. The expected Slice 1 route is
   none unless SD-UAT-015 finds a real scroll region.

### SD-UAT-018 Manifest parity

1. Compare the Slice 1 manifest row for `slide-deck` with the exhaustive
   ART-005 ID/source/role/status/export table.
2. Confirm `id` is `slide-deck`.
3. Confirm `title` is `Slide Deck`.
4. Confirm `source.origin` is `upstream` and `source.file` is
   `09-slide-deck.html`.
5. Confirm `status` is `shipped`.
6. Confirm `exports` is an empty array because `slide-deck` is a reader.

## Source-Backed Not Applicable Rows

The cumulative JSON retains rows that honestly carry
`verdict: not_applicable` after source and browser execution.

1. SD-UAT-019 records the horizontal-scroll N/A route from source and runtime
   evidence: there is no `overflow-x: auto` or `overflow-x: scroll`; `html` and
   `body` use `overflow-x: hidden`; 360 and 1280 CSS px observations found no
   actual user-scroll element.
2. SD-UAT-020 through SD-UAT-028 record producer-only data-integrity/export
   cases that do not apply to the reader because the manifest declares
   `exports: []` and the template has no export surface.
3. SD-UAT-029 through SD-UAT-036 record producer-only clipboard/recovery/race
   cases that do not apply to the reader because the template has only slide
   navigation and theme controls.
