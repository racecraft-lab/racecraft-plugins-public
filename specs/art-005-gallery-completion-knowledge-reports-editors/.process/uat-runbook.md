# ART-005 UAT Runbook

Feature: ART-005 gallery completion knowledge reports/editors
Artifacts: `slide-deck`, `concept-explainer`, `status-report`, `incident-report`, `triage-board`, `feature-flags`, `prompt-tuner`
Driver: `manual`
Template paths:
- `speckit-pro/artifact-gallery/templates/slide-deck.html`
- `speckit-pro/artifact-gallery/templates/concept-explainer.html`
- `speckit-pro/artifact-gallery/templates/status-report.html`
- `speckit-pro/artifact-gallery/templates/incident-report.html`
- `speckit-pro/artifact-gallery/templates/triage-board.html`
- `speckit-pro/artifact-gallery/templates/feature-flags.html`
- `speckit-pro/artifact-gallery/templates/prompt-tuner.html`
Results path: `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md`
JSON path: `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.json`

T019 created the active UAT carriers. T109 re-executed the complete cumulative
Slice 1-7 row set against source checkpoint
`f85ed14c89a5f71bb041e49930647dbc93ec8560` on 2026-08-18. The first four
reader templates were rebound by exact source-hash identity and the three editor
harnesses were rerun at 36/36 each. The current session's
fresh connected-browser inventory was empty and `getForUrl` was unavailable, so
the operator-authorized Playwright MCP fallback supplied browser interaction and
observation while the contract driver remained `manual`.

## Manual Setup

1. Check out the source checkpoint named above.
2. From the repository root, resolve each listed template path as a direct
   `file://<repo-root>/<template-path>` URL.
3. Open each exact `file://` URL in the selected browser.
4. Record the operating system, browser name/version, network condition, theme
   condition, reduced-motion condition, color-mode condition, and viewport width.
5. Record executable rows in
   `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md`.
6. Record only executable rows with real `pass` or `fail` evidence in the JSON.
   Keep source-backed `not_applicable` rows distinct from browser observations.

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

## Slice 2 Executable Rows

CE-UAT-001 through CE-UAT-018 passed at the Slice 2 source checkpoint. These
steps are the reusable cumulative procedure for later checkpoints.

### CE-UAT-001 Direct file open

1. Open `file://<repo-root>/speckit-pro/artifact-gallery/templates/concept-explainer.html`.
2. Confirm the document title is `Concept Explainer - Consistent Hashing`.
3. Confirm the visible h1 is `Consistent hashing, in one ring`.
4. Confirm the page renders without a server or visible error state.

### CE-UAT-002 Complete representative fills

1. Confirm `concept-title`, `principles`, `worked-example`, and
   `simulation-scenarios` content is present.
2. Confirm the three principle headings are complete.
3. Confirm both modulo and consistent-hashing comparison cards are complete.
4. Confirm the anchored Node loss and Scale out scenarios both include visible
   `Watch:` guidance.

### CE-UAT-003 Named simulation controls and status

1. Confirm the control group is named `Consistent hashing simulation controls`.
2. Confirm the sliders are named `Nodes` and `Keys`.
3. Confirm buttons are named `Remove a node`, `Add a node`, and
   `Reset simulation`.
4. Confirm `#simulation-status` exposes role `status`, `aria-live="polite"`, and
   the visible current counts.

### CE-UAT-004 Deterministic ring rendering

1. Record the default ring drawing, four node labels, and 32 square key markers.
2. Reload the file without changing a control.
3. Confirm the drawing and ownership markup is identical after reload.

### CE-UAT-005 Add and remove nodes

1. Activate Add and confirm the visible node count and markers change 4 to 5.
2. Confirm the status reports the add and moved-key count.
3. Activate Remove from five nodes and confirm the count returns to 4.
4. Confirm enabled invoked controls retain focus after each change.

### CE-UAT-006 Visible minimum and maximum feedback

1. Set Nodes to 2; confirm Remove is disabled and the status says
   `Minimum 2 nodes reached.`
2. Set Nodes to 8; confirm Add is disabled and the status says
   `Maximum 8 nodes reached.`
3. Set Keys to 10 and then 60; confirm the outputs/markers match and the status
   says `Minimum 10 keys reached.` and `Maximum 60 keys reached.` respectively.

### CE-UAT-007 Reset simulation

1. Change both sliders and node count.
2. Activate Reset.
3. Confirm 4 nodes, 32 keys, matching markers, zero moved keys, and the visible
   `Reset complete.` message.

### CE-UAT-008 Session-only reload

1. Change the simulation to 6 nodes and 50 keys.
2. Reload the exact file URL.
3. Confirm the simulation returns to 4 nodes and 32 keys.
4. Confirm no simulation-state local-storage key exists; only the canonical
   gallery theme key may persist.

### CE-UAT-009 Offline reload

1. Open the reader once online, then put the browser context offline.
2. Reload the exact local file and activate Add.
3. Confirm local content, theme, ring, status, and controls remain usable.
4. Confirm a separate remote probe fails because the context is offline.

### CE-UAT-010 Complete keyboard traversal

1. Reload the reader and start at the browser viewport.
2. Record forward Tab order through Dark theme, Nodes, Keys, Remove a node, Add
   a node, and Reset simulation.
3. Traverse backward with Shift+Tab and confirm the reverse order.

### CE-UAT-011 Focus visibility

1. Keyboard-focus the theme control, both sliders, and all three simulation
   buttons.
2. Confirm every stop has a visible solid focus outline in light and dark modes.

### CE-UAT-012 Light/dark parity

1. Record complete content and controls in light mode.
2. Toggle Dark theme and confirm content, controls, status, and focus remain.
3. Reload and confirm dark persists, then return the reader to light.

### CE-UAT-013 Reduced motion

1. Enable `prefers-reduced-motion: reduce` and reload.
2. Confirm transition and animation duration is effectively removed.
3. Activate Add and confirm all visible state and status behavior still works.

### CE-UAT-014 Color-independent meaning

1. Confirm nodes carry visible `N1`-style labels and keys use square markers.
2. Confirm the legend names both shapes.
3. Confirm Node loss and Scale out use headings and visible `Watch:` text.

### CE-UAT-015 Horizontal scroll actual-element check

1. Confirm source has no `overflow-x:auto` or `overflow-x:scroll` declaration.
2. At both review widths, compare document client and scroll widths.
3. Confirm no actual user-scroll element has horizontal overflow.

### CE-UAT-016 360 CSS px layout

1. Set the viewport to exactly 360 CSS px wide and reload.
2. Confirm the heading, grids, ring, sliders, buttons, status, and scenarios stay
   inside the viewport without clipping or overlap.
3. Confirm there is no page-level horizontal overflow.

### CE-UAT-017 >=1280 CSS px layout

1. Set the viewport to at least 1280x900 CSS px and reload.
2. Confirm the heading, grids, ring, controls, status, and scenarios stay inside
   the viewport without clipping or overlap.
3. Confirm there is no page-level horizontal overflow.

### CE-UAT-018 Manifest parity

1. Confirm `id` is `concept-explainer` and title is `Concept Explainer`.
2. Confirm the pinned upstream source is `15-research-concept-explainer.html`.
3. Confirm role is reader, status is `shipped`, and `exports` is `[]`.

## Slice 3 Executable Rows

SR-UAT-001 through SR-UAT-018 passed at the Slice 3 source checkpoint. These
steps remain the reusable cumulative procedure for later slice checkpoints.

### SR-UAT-001 Direct file open

1. Open `file://<repo-root>/speckit-pro/artifact-gallery/templates/status-report.html`.
2. Confirm the title is `Status Report - Artifact Gallery Delivery`.
3. Confirm the visible h1 is `Artifact Gallery Status` and the page needs no server.

### SR-UAT-002 Complete representative fills

1. Confirm the `summary`, `landed`, `in-flight`, `blocked`, and `next-actions`
   fill regions contain complete representative content.
2. Confirm each list fill contains at least two anchored items.

### SR-UAT-003 Semantic section structure

1. Confirm one `main` landmark contains five sections.
2. Confirm their h2 headings are Summary, Landed, In flight, Blocked, and Next actions.
3. Confirm every heading labels its section programmatically.

### SR-UAT-004 Summary metrics

1. Confirm the summary exposes the current state `On track`.
2. Confirm the visible counts are 2 landed, 1 in flight, and 1 blocked.

### SR-UAT-005 Landed outcomes

1. Confirm `#landed-slide-deck` and `#landed-concept-explainer` are present.
2. Confirm both expose the visible text cue `Status: Complete`.

### SR-UAT-006 In-flight work

1. Confirm `#in-flight-status-reader` and `#in-flight-cumulative-uat` are present.
2. Confirm their visible cues are `Status: Building` and `Status: Scheduled`.

### SR-UAT-007 Blocked work

1. Confirm `#blocked-physical-footprint` and `#blocked-connected-browser` are present.
2. Confirm their visible cues are `Status: Size-only` and `Status: Fallback ready`.

### SR-UAT-008 Next actions

1. Confirm `#next-actions-verify-reader` and `#next-actions-open-pr` are present.
2. Confirm their visible cues are `Next: Finalize source checkpoint` and
   `Next: Publish evidence`.

### SR-UAT-009 Offline reload

1. Put the browser context offline and reload the exact local file.
2. Confirm title, heading, sections, content, and theme control remain usable.
3. Restore the online condition after the observation.

### SR-UAT-010 Complete keyboard traversal

1. Reload and begin at the browser viewport.
2. Press Tab and confirm the theme control is the sole authored keyboard stop.
3. Confirm the report has no disguised interactive controls.

### SR-UAT-011 Focus visibility

1. Keyboard-focus the Dark theme control.
2. Confirm a visible solid 2px outline with 2px offset.

### SR-UAT-012 Light/dark parity

1. Record the complete report in light mode, then toggle Dark theme.
2. Confirm all five sections, eight list items, metrics, and status text remain.
3. Reload to confirm dark persistence, then return the report to light.

### SR-UAT-013 Reduced motion

1. Enable `prefers-reduced-motion: reduce` and reload.
2. Confirm transition and animation durations are effectively removed and no
   animation remains running after settle.

### SR-UAT-014 Color-independent meaning

1. Confirm all status and next-action states use visible text rather than hue alone.
2. Confirm the eight cues remain understandable in both themes.

### SR-UAT-015 Horizontal scroll actual-element check

1. Confirm source has no `overflow-x:auto` or `overflow-x:scroll` declaration.
2. At both review widths, compare document client and scroll widths.
3. Confirm no actual user-scroll element has horizontal overflow.

### SR-UAT-016 360 CSS px layout

1. Set the viewport to exactly 360 CSS px and reload.
2. Confirm all sections and lists remain inside the viewport without clipping.
3. Confirm there is no page-level horizontal overflow.

### SR-UAT-017 >=1280 CSS px layout

1. Set the viewport to at least 1280 CSS px and reload.
2. Confirm all sections and lists remain inside the viewport without clipping.
3. Confirm there is no page-level horizontal overflow.

### SR-UAT-018 Manifest parity

1. Confirm `id` is `status-report` and title is `Status Report`.
2. Confirm the pinned upstream source is `11-status-report.html`.
3. Confirm role is reader, status is `shipped`, and `exports` is `[]`.

## Slice 4 Executable Rows

IR-UAT-001 through IR-UAT-018 passed at the Slice 4 source checkpoint. These
steps remain the reusable cumulative procedure for later slice checkpoints.

### IR-UAT-001 Direct file open

1. Open `file://<repo-root>/speckit-pro/artifact-gallery/templates/incident-report.html`.
2. Confirm the title is `INC-2025-0412 - Elevated 502s on task sync`.
3. Confirm the h1 is `Elevated 502s on task sync` and no server is required.

### IR-UAT-002 Complete representative fills

1. Confirm `summary`, `timeline`, `impact`, `root-cause`, and `follow-ups` are complete.
2. Confirm at least two stable anchors exist in timeline and follow-ups.

### IR-UAT-003 Named report navigation

1. Locate the navigation named `Incident report sections`.
2. Activate Summary, Timeline, Impact, Root cause, and Follow-ups.
3. Confirm every link targets the matching stable section.

### IR-UAT-004 Summary identity and state

1. Confirm incident ID `INC-2025-0412`, `SEV-2`, and `Resolved` are visible.
2. Confirm duration, detection time, owner, error peak, mitigation, and no-data-loss text.

### IR-UAT-005 Anchored timeline

1. Confirm the timeline is an ordered semantic list.
2. Confirm seven anchored events run from the 14:02 rollout through 14:49 resolution.
3. Confirm impact, alert, diagnosis, mitigation, and resolution are stated in text.

### IR-UAT-006 Quantified impact

1. Confirm failed requests, peak error rate, affected workspaces, data loss, SLA, and recovery.
2. Confirm each value remains visible and associated with its label.

### IR-UAT-007 Root-cause chain

1. Confirm the retained value 8 versus inherited value 64 is explicit.
2. Confirm missing magnitude validation and the separate-pipeline diagnosis delay are explicit.

### IR-UAT-008 Owned follow-ups

1. Confirm four anchored remediation items are present.
2. Confirm every item exposes visible Status, Owner, and Due text.

### IR-UAT-009 Offline reload

1. Put the browser context offline and reload the exact local file.
2. Confirm title, h1, navigation, five sections, timeline, follow-ups, and theme remain usable.
3. Confirm a disposable remote probe fails with `net::ERR_INTERNET_DISCONNECTED`.

### IR-UAT-010 Complete keyboard traversal

1. Reload and start from the browser viewport.
2. Confirm forward order: Dark theme, Summary, Timeline, Impact, Root cause, Follow-ups.
3. Traverse backward and confirm the same six controls remain reachable.

### IR-UAT-011 Focus visibility

1. Keyboard-focus the Dark theme control and a report navigation link.
2. Confirm the theme control has a 2px solid outline with 2px offset.
3. Confirm navigation links have a 3px solid outline with 3px offset.

### IR-UAT-012 Light/dark parity

1. Record all incident content in light mode, then toggle Dark theme.
2. Confirm all five sections, seven timeline events, and four follow-ups remain.
3. Reload to confirm dark persistence, then return to light.

### IR-UAT-013 Reduced motion

1. Enable `prefers-reduced-motion: reduce` and reload.
2. Confirm transition and animation durations are effectively removed.
3. Confirm no animation remains running after settle.

### IR-UAT-014 Color-independent meaning

1. Confirm severity, status, duration, owner, timeline order, and milestone text are visible.
2. Confirm follow-up Status, Owner, and Due labels carry meaning without hue.

### IR-UAT-015 Horizontal scroll actual-element check

1. Confirm source has no `overflow-x:auto` or `overflow-x:scroll` declaration.
2. At both review widths, compare document client and scroll widths.
3. Confirm no actual user-scroll element has horizontal overflow.

### IR-UAT-016 360 CSS px layout

1. Set the viewport to exactly 360 CSS px and reload.
2. Confirm navigation, sections, timeline, impact, cause, and follow-ups remain inside the viewport.
3. Confirm there is no page-level horizontal overflow or clipped reviewed node.

### IR-UAT-017 >=1280 CSS px layout

1. Set the viewport to at least 1280 CSS px and reload.
2. Confirm navigation and all report sections remain visible without clipping.
3. Confirm there is no page-level horizontal overflow.

### IR-UAT-018 Manifest parity

1. Confirm `id` is `incident-report` and title is `Incident Report`.
2. Confirm the pinned upstream source is `12-incident-report.html`.
3. Confirm role is reader, status is `shipped`, and `exports` is `[]`.

## Slice 5 Executable Rows

TB-UAT-001 through TB-UAT-018 and TB-UAT-020 through TB-UAT-036 passed at the
Slice 5 source checkpoint. TB-UAT-019 is the evidence-backed horizontal-scroll
not-applicable route required when no actual user-scroll element exists.

### TB-UAT-001 Direct file open

1. Open the exact triage-board.html file URL.
2. Confirm title Triage Board — Cycle 14, h1 Release triage board, and no visible error.

### TB-UAT-002 Complete representative fills

1. Confirm Now, Next, Later, and Cut are present.
2. Confirm six anchored tickets and all id, title, tag, estimate, and owner fields.

### TB-UAT-003 Named board controls and status

1. Confirm the board is a named group.
2. Confirm the labeled filter, Clear filter, Reset board, Copy as Markdown, named tickets/fields, and polite status region.

### TB-UAT-004 Keyboard movement and reorder

1. Focus RC-421 and use ArrowRight, ArrowUp, ArrowLeft, and ArrowUp.
2. Confirm Next order RC-440, RC-421, RC-447; restored Now order RC-421, RC-433; focus retention; and exact boundary messages.

### TB-UAT-005 Live contenteditable update

1. Edit RC-421 title to Keyboard-edited title.
2. Confirm the ticket accessible name updates and status says Ticket updated in memory.

### TB-UAT-006 Empty-column feedback

1. Move the only Later ticket to Cut with ArrowRight.
2. Confirm Later shows No tickets in this column. and the movement is announced.

### TB-UAT-007 Filtered-no-result feedback

1. Select Bug and confirm two visible tickets plus three filtered-empty messages.
2. Change all tags to other, select Bug, and confirm all four columns show No tickets match this filter.

### TB-UAT-008 Reset and session-only state

1. Reset after edits/moves/filtering and confirm the six-ticket seed returns.
2. Edit a title, reload, and confirm seed content and empty status return with no editor persistence.

### TB-UAT-009 Offline reload

1. Set the browser context offline and reload the exact local file.
2. Confirm title, board, tickets, controls, editing, and copy fallback remain usable; confirm a disposable remote probe fails.

### TB-UAT-010 Complete keyboard traversal

1. Tab from the viewport through the full editor and record every stop.
2. Confirm 41 ordered stops: theme, filter, three buttons, then each ticket and its five fields; reverse with Shift+Tab.

### TB-UAT-011 Focus visibility

1. Keyboard-focus all 41 stops and the failure fallback.
2. Confirm every stop has a 3px solid outline with 3px offset and fallback is focused and fully selected.

### TB-UAT-012 Light/dark parity

1. Exercise light, dark, persisted-dark reload, and return-to-light.
2. Confirm identical board content, controls, state meaning, and focus visibility.

### TB-UAT-013 Reduced motion

1. Emulate prefers-reduced-motion: reduce and reload.
2. Confirm 0.01ms transition/animation durations, zero running animations, and complete keyboard/control behavior.

### TB-UAT-014 Color-independent meaning

1. Review columns, ticket metadata, empty/filter states, and copy states.
2. Confirm every state is named by visible text and does not depend on hue.

### TB-UAT-015 Horizontal-scroll actual-element check

1. At 360 and 1280 CSS px compare document clientWidth and scrollWidth.
2. Confirm responsive 4/2/1-column layout creates no actual horizontal user-scroll region.

### TB-UAT-016 360 CSS px layout

1. Set the viewport to exactly 360 by 900 CSS px and reload.
2. Confirm clientWidth=scrollWidth=345, one-column board, no clipped reviewed node, and capture a full-page screenshot.

### TB-UAT-017 1280 CSS px layout

1. Set the viewport to 1280 by 900 CSS px and reload.
2. Confirm clientWidth=scrollWidth=1280, no clipped reviewed node, and capture a full-page screenshot.

### TB-UAT-018 Manifest parity

1. Read the triage-board manifest row.
2. Confirm id/title/source, producer role, shipped status, and exports=[markdown].

### TB-UAT-019 Horizontal-scroll N/A classification

1. Confirm source has no overflow-x:auto or overflow-x:scroll path.
2. Record not_applicable with source and runtime evidence because no meaningful horizontal scroll element exists.

### TB-UAT-020 Live export freshness

1. Export after setting the visible title to FRESHNESS-OLD-triage-board.
2. Change it to FRESHNESS-NEW-triage-board and export again; require different bytes, new sentinel present, and old sentinel absent.

### TB-UAT-021 Empty values and collections

1. Empty a ticket id/title and confirm ordered empty_required_value issues with raw empty strings.
2. Filter every ticket out and confirm four explicit - _No tickets._ entries plus deterministic Issues output.

### TB-UAT-022 Current visible ticket order

1. Move/reorder RC-421 and export.
2. Confirm Next order RC-440, RC-421, RC-447; filter Bug and confirm only RC-421 and RC-433 are serialized.

### TB-UAT-023 Deterministic column and field order

1. Export the representative board.
2. Confirm Now, Next, Later, Cut, Issues order and id/title/tag/estimate/owner ticket field order.

### TB-UAT-024 Duplicate identifiers

1. Change a Next-column ticket ID to RC-421, duplicating the Now ticket.
2. Confirm both tickets remain and duplicate_identifier points occurrence 3 to occurrence 1.

### TB-UAT-025 Special-character round trip

1. Type multiline Unicode plus quotes, backticks, pipe, slash, backslash, tab, and a real line break into the visible ticket contenteditable.
2. Export and confirm the browser-created line break and raw meaning are preserved with deterministic Markdown escaping and continuation indentation.

### TB-UAT-026 Multiple issue order

1. Combine a cross-column duplicate with empty estimate and owner values.
2. Confirm issue order follows entity order, field order, and condition order, and every issue field uses the declared schema order.

### TB-UAT-027 Clipboard/fallback exact equality

1. Capture the exact attempted Markdown on success and every fallback class.
2. Require byte equality between the invocation export and clipboard or fallback text.

### TB-UAT-028 Superseded-attempt data integrity

1. Run older-success-after-newer-failure and older-failure-after-newer-success races.
2. Confirm the older settlement never restores stale status, fallback content/visibility, or focus.

### TB-UAT-029 Genuine clipboard success

1. Install a callable resolving writeText capability and invoke Copy as Markdown.
2. Confirm exactly one write, exact 935-byte text, normalized success status, hidden fallback, and copy-button focus.

### TB-UAT-030 Clipboard absent

1. Remove clipboard capability and invoke copy.
2. Confirm zero writes and exact labeled, focused, fully selected fallback.

### TB-UAT-031 Method non-callable

1. Expose a non-callable writeText value and invoke copy.
2. Confirm zero writes and the same exact fallback recovery.

### TB-UAT-032 Permission denied

1. Reject one write with NotAllowedError.
2. Confirm one attempt, normalized failure text, no exception leak, and exact focused fallback.

### TB-UAT-033 Generic rejection

1. Reject one write with a generic Error.
2. Confirm one attempt, normalized failure text, no exception leak, and exact focused fallback.

### TB-UAT-034 Synchronous throw

1. Throw synchronously from one writeText call.
2. Confirm one attempt, normalized failure text, no exception leak, and exact focused fallback.

### TB-UAT-035 Failure-success-failure sequence

1. Use three distinct live titles across failure, success, and failure invocations.
2. Confirm one write per invocation, success clears fallback, and final fallback contains only the newest failed export.

### TB-UAT-036 Both superseded races and reset invalidation

1. Resolve an older success after a newer failure, then reject an older failure after a newer success.
2. Confirm the newer state wins in both directions; also reset during a pending success and confirm its later settlement is ignored.

## Slice 6 Executable Rows

FF-UAT-001 through FF-UAT-018 and FF-UAT-020 through FF-UAT-036 passed at
the Slice 6 source checkpoint. FF-UAT-019 is the evidence-backed
horizontal-scroll not-applicable route required when no actual user-scroll
element exists.

### FF-UAT-001 Direct file open

1. Open the exact feature-flags.html file URL.
2. Confirm title Feature Flag Editor — Production, h1 Feature flag configuration, and no visible error.

### FF-UAT-002 Complete representative fills

1. Confirm four ordered groups, six named flags, and the intentional empty Internal group.
2. Confirm every group and flag exposes its complete labeled field set.

### FF-UAT-003 Named controls and status

1. Confirm the named reset and Copy as Markdown controls, ordered-groups label, summary, and polite status region.
2. Confirm all 41 controls have accessible names.

### FF-UAT-004 Live group and flag editing

1. Edit group IDs/labels and flag key/description/enabled/requires/rollout controls.
2. Confirm the status reports in-memory updates and later exports use current visible values.

### FF-UAT-005 Typed rollout feedback

1. Enter valid numeric, empty, and invalid rollout values.
2. Confirm numbers remain numbers, empty/invalid export as null, and invalid feedback is visible.

### FF-UAT-006 Dependency feedback

1. Exercise valid, invalid, unavailable, and disabled-prerequisite dependencies.
2. Confirm normalized values and visible text distinguish all four states.

### FF-UAT-007 Empty-group feedback

1. Inspect the fourth representative group with no flags.
2. Confirm No flags in this group. is visible and the group remains in export order.

### FF-UAT-008 Reset and session-only state

1. Reset after group/flag edits and confirm the representative seed returns.
2. Edit a description, reload, and confirm the seed returns with no persisted editor state.

### FF-UAT-009 Offline reload

1. Set the browser context offline and reload the exact local file.
2. Confirm editing and fallback export remain usable while a disposable remote probe fails.

### FF-UAT-010 Complete keyboard traversal

1. Tab through the editor, then traverse in reverse with Shift+Tab.
2. Confirm 41 unique ordered stops and exact forward/reverse parity.

### FF-UAT-011 Focus visibility

1. Keyboard-focus representative controls and the failure fallback.
2. Confirm a 3px solid outline with 3px offset and focused selectable fallback.

### FF-UAT-012 Light/dark parity

1. Exercise light, dark, persisted-dark reload, and return-to-light.
2. Confirm identical fields, state meaning, feedback, and focus visibility.

### FF-UAT-013 Reduced motion

1. Emulate prefers-reduced-motion: reduce and reload.
2. Confirm durations do not exceed 0.01ms, no animation remains running, and controls still work.

### FF-UAT-014 Color-independent meaning

1. Review enabled controls, dependency/rollout feedback, empty state, status, and fallback.
2. Confirm each state is named in text rather than depending on hue.

### FF-UAT-015 Horizontal-scroll actual-element check

1. At 360 and 1280 CSS px compare document clientWidth and scrollWidth.
2. Confirm no actual horizontal user-scroll region exists.

### FF-UAT-016 360 CSS px layout

1. Set the viewport to 360 by 900 CSS px and reload.
2. Confirm every group, flag, control, message, and fallback remains unclipped and capture a full-page screenshot.

### FF-UAT-017 1280 CSS px layout

1. Set the viewport to 1280 by 900 CSS px and reload.
2. Confirm every reviewed node remains unclipped and capture a full-page screenshot.

### FF-UAT-018 Manifest parity

1. Read the feature-flags manifest row.
2. Confirm id/title/source, producer role, shipped status, and exports=[markdown].

### FF-UAT-019 Horizontal-scroll N/A classification

1. Confirm source has no overflow-x:auto or overflow-x:scroll path.
2. Record not_applicable with source and runtime evidence because no meaningful horizontal scroll element exists.

### FF-UAT-020 Live export freshness

1. Export after setting one description to OLD snapshot, then change it to NEW snapshot and export again.
2. Require different bytes, the new sentinel present, and the old sentinel absent.

### FF-UAT-021 Empty values and collections

1. Empty group id/label and flag key/description while leaving requires/rollout empty.
2. Confirm empty strings, null optionals, the empty group, and ordered empty_required_value issues.

### FF-UAT-022 Current group and flag order

1. Export the representative state.
2. Confirm onboarding, sync, billing, internal order and the six exact visible flag keys in DOM order.

### FF-UAT-023 Deterministic schema and field order

1. Extract the single fenced JSON value and reserialize with JSON.stringify(value, null, 2).
2. Confirm byte equality and exact root, group, flag, and issue field order.

### FF-UAT-024 Duplicate identifiers

1. Duplicate one group ID and one flag key.
2. Confirm both values remain and ordered duplicate_identifier issues point to their first visible occurrence.

### FF-UAT-025 Special-character round trip

1. Enter multiline Unicode, emoji, backticks, pipe, slash, backslash, and tab in visible controls.
2. Confirm JSON parsing reproduces every value exactly.

### FF-UAT-026 Multiple issue order

1. Combine invalid requires/rollout and unavailable dependencies with the representative seed issue.
2. Confirm deterministic entity, field, and condition order and all ten issue fields.

### FF-UAT-027 Clipboard/fallback exact equality

1. Capture the exact current Markdown on success and every fallback class.
2. Require byte equality between the invocation export and clipboard or fallback text.

### FF-UAT-028 Superseded-attempt data integrity

1. Run both older/newer settlement directions with distinct visible data.
2. Confirm stale status, fallback content/visibility, and focus never return.

### FF-UAT-029 Genuine clipboard success

1. Install a callable resolving writeText capability and invoke Copy as Markdown.
2. Confirm exactly one exact write, normalized success status, hidden fallback, and copy-button focus.

### FF-UAT-030 Clipboard absent

1. Remove clipboard capability and invoke copy.
2. Confirm zero writes and exact labeled, focused, selectable fallback.

### FF-UAT-031 Method non-callable

1. Expose a non-callable writeText value and invoke copy.
2. Confirm zero writes and the same exact fallback recovery.

### FF-UAT-032 Permission denied

1. Reject one write with NotAllowedError.
2. Confirm one attempt, normalized failure text, no exception leak, and exact focused fallback.

### FF-UAT-033 Generic rejection

1. Reject one write with a generic Error.
2. Confirm one attempt, normalized failure text, no exception leak, and exact focused fallback.

### FF-UAT-034 Synchronous throw

1. Throw synchronously from one writeText call.
2. Confirm one attempt, normalized failure text, no exception leak, and exact focused fallback.

### FF-UAT-035 Failure-success-failure sequence

1. Invoke failure, success, then failure over current visible state.
2. Confirm success clears fallback and the final failure contains only the newest export.

### FF-UAT-036 Both superseded races and reset invalidation

1. Resolve older success after newer failure, then reject older failure after newer success.
2. Confirm the newer state wins in both directions; reset during pending success and confirm later settlement is ignored.

## Slice 7 Executable Rows

PT-UAT-001 through PT-UAT-018 and PT-UAT-020 through PT-UAT-036 passed at
the Slice 7 source checkpoint. PT-UAT-019 is the evidence-backed
horizontal-scroll not-applicable route required when no actual user-scroll
element exists.

### PT-UAT-001 Direct file open

1. Open the exact prompt-tuner.html file URL.
2. Confirm title Prompt Tuner — Support Reply, h1 Support reply prompt tuner, three previews, and no page error.

### PT-UAT-002 Complete representative fills

1. Confirm the prompt template, five ordered slots, three anchored samples, fifteen sample fields, and three derived previews.
2. Confirm the prompt-variants and evaluation-notes fills are complete.

### PT-UAT-003 Named controls and status

1. Confirm every input, textarea, and button has a visible or programmatic name.
2. Confirm the copy and preview status regions expose their messages.

### PT-UAT-004 Live template and sample editing

1. Edit the template and sample fields.
2. Confirm each named preview updates immediately from current visible values.

### PT-UAT-005 Slot ordering and first occurrence

1. Confirm customer_name, plan_tier, ticket_subject, ticket_body, and tone remain in visible order.
2. Duplicate a valid slot and confirm only its first occurrence becomes an exported field key.

### PT-UAT-006 Invalid-slot feedback

1. Enter raw invalid slot text.
2. Confirm the raw text remains visible, the unresolved token remains in preview, and invalid/unavailable feedback is exposed.

### PT-UAT-007 Empty-state feedback

1. Empty the prompt template and a sample value, then remove all slot/sample rows in the disposable page state.
2. Confirm explicit empty template, preview, collections, and ordered issue output.

### PT-UAT-008 Reset and session-only state

1. Reset after edits and confirm the representative seed returns.
2. Edit the template, reload, and confirm no editor state persists.

### PT-UAT-009 Offline reload

1. Set the browser context offline and reload the exact local file.
2. Confirm controls, previews, reset, and copy fallback remain usable while a disposable remote probe fails.

### PT-UAT-010 Complete keyboard traversal

1. Tab through the complete editor and record every stop.
2. Confirm all 33 unique stops in forward order and the exact reverse order with Shift+Tab.

### PT-UAT-011 Focus visibility

1. Keyboard-focus representative shared and editor controls plus the failure fallback.
2. Confirm solid visible focus with at least 2px width/offset and exact focused fallback selection.

### PT-UAT-012 Light/dark parity

1. Exercise light, dark, persisted-dark reload, and return-to-light.
2. Confirm identical prompt, controls, previews, status meaning, and focus behavior.

### PT-UAT-013 Reduced motion

1. Emulate prefers-reduced-motion: reduce and reload.
2. Confirm 0.01ms transition/animation durations, zero running animations, and usable controls.

### PT-UAT-014 Color-independent meaning

1. Review valid/invalid slot, derived preview, empty, issue, copy, and reset states.
2. Confirm every state is named by visible text and does not depend on hue.

### PT-UAT-015 Horizontal-scroll actual-element check

1. At 360 and 1280 CSS px compare document clientWidth and scrollWidth.
2. Confirm no actual horizontal user-scroll region exists.

### PT-UAT-016 360 CSS px layout

1. Set the viewport to exactly 360 by 900 CSS px and reload.
2. Confirm every prompt, slot, sample, preview, control, and fallback remains unclipped and capture a full-page screenshot.

### PT-UAT-017 1280 CSS px layout

1. Set the viewport to 1280 by 900 CSS px and reload.
2. Confirm every reviewed node remains unclipped and capture a full-page screenshot.

### PT-UAT-018 Manifest parity

1. Read the prompt-tuner manifest row.
2. Confirm id/title/source, producer exports, shipped status, and exports=[markdown].

### PT-UAT-019 Horizontal-scroll N/A classification

1. Confirm source has no overflow-x:auto or overflow-x:scroll path.
2. Record not_applicable with source and runtime evidence because no meaningful horizontal scroll element exists.

### PT-UAT-020 Live export freshness

1. Export with FRESHNESS-OLD-prompt-tuner, then change the visible template to FRESHNESS-NEW-prompt-tuner and export again.
2. Require different bytes, the new sentinel present, and the old sentinel absent.

### PT-UAT-021 Empty values and collections

1. Empty the template and representative fields, then exercise empty slots, samples, and previews.
2. Confirm empty strings/arrays remain explicit and ordered empty_required_value issues are preserved.

### PT-UAT-022 Current slot and sample order

1. Export the representative state.
2. Confirm the five exact slots and three exact sample IDs follow current visible DOM order.

### PT-UAT-023 Deterministic schema and field order

1. Extract the single fenced JSON value and reserialize with JSON.stringify(value, null, 2).
2. Confirm byte equality and exact root, sample, field-key, and issue-field order.

### PT-UAT-024 Duplicate identifiers

1. Duplicate one slot and one sample ID.
2. Confirm both raw values remain and ordered duplicate_identifier issues point to their first occurrence.

### PT-UAT-025 Special-character round trip

1. Enter multiline Unicode, emoji, quotes, backticks, pipe, slash, backslash, and tab in the template and sample fields.
2. Confirm JSON parsing reproduces template, fields, and derived preview exactly.

### PT-UAT-026 Multiple issue order

1. Combine invalid/duplicate slots with empty and duplicate sample fields.
2. Confirm deterministic entity, field, and condition order and all ten issue fields.

### PT-UAT-027 Clipboard/fallback exact equality

1. Capture the exact current Markdown on success and every fallback class.
2. Require byte equality between the invocation export and clipboard or fallback text.

### PT-UAT-028 Superseded-attempt data integrity

1. Run both older/newer settlement directions with distinct visible data.
2. Confirm stale status, fallback content/visibility, and focus never return.

### PT-UAT-029 Genuine clipboard success

1. Install a callable resolving writeText capability and invoke Copy as Markdown.
2. Confirm exactly one exact write, normalized success status, hidden fallback, and copy-button focus.

### PT-UAT-030 Clipboard absent

1. Remove clipboard capability and invoke copy.
2. Confirm zero writes and exact labeled, focused, selectable fallback.

### PT-UAT-031 Method non-callable

1. Expose a non-callable writeText value and invoke copy.
2. Confirm zero writes and the same exact fallback recovery.

### PT-UAT-032 Permission denied

1. Reject one write with NotAllowedError.
2. Confirm one attempt, normalized failure text, no exception leak, and exact focused fallback.

### PT-UAT-033 Generic rejection

1. Reject one write with a generic Error.
2. Confirm one attempt, normalized failure text, no exception leak, and exact focused fallback.

### PT-UAT-034 Synchronous throw

1. Throw synchronously from one writeText call.
2. Confirm one attempt, normalized failure text, no exception leak, and exact focused fallback.

### PT-UAT-035 Failure-success-failure sequence

1. Invoke failure, success, then failure over three distinct visible template values.
2. Confirm success clears fallback and the final failure contains only the newest export.

### PT-UAT-036 Both superseded races and reset invalidation

1. Resolve older success after newer failure, then reject older failure after newer success.
2. Confirm the newer state wins in both directions; reset during pending success and confirm later settlement is ignored.

## Source-Backed Not Applicable Rows

The cumulative JSON retains rows that honestly carry
`verdict: not_applicable` after source and browser execution.

1. SD-UAT-019, CE-UAT-019, SR-UAT-019, IR-UAT-019, TB-UAT-019,
   FF-UAT-019, and PT-UAT-019 record the horizontal-scroll N/A route from source
   and runtime evidence: there is no `overflow-x: auto` or `overflow-x: scroll`;
   `html` and `body` use `overflow-x: hidden`; 360 and 1280 CSS px observations
   found no actual user-scroll element.
2. SD-UAT-020 through SD-UAT-028, CE-UAT-020 through CE-UAT-028,
   SR-UAT-020 through SR-UAT-028, and IR-UAT-020 through IR-UAT-028 record
   producer-only data-integrity/export cases that do not apply because all
   four manifests declare `exports: []` and none of the templates has an
   export surface.
3. SD-UAT-029 through SD-UAT-036, CE-UAT-029 through CE-UAT-036,
   SR-UAT-029 through SR-UAT-036, and IR-UAT-029 through IR-UAT-036 record
   producer-only clipboard/recovery/race cases that do not apply because all
   four reader artifacts have no clipboard action; triage-board, feature-flags,
   and prompt-tuner execute the producer rows.
