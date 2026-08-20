# ART-005 UAT Runbook

Feature: ART-005 gallery completion knowledge reports/editors
Artifacts: `slide-deck`, `concept-explainer`, `status-report`, `incident-report`, `triage-board`, `feature-flags`, `prompt-tuner`
Driver: manual browser review
Results path: `docs/ai/specs/.process/ART-005-uat-results.md`
JSON path: `docs/ai/specs/.process/ART-005-uat-results.json`

Use this runbook to confirm that the seven new gallery artifacts work as local
HTML files, present complete sample content, and keep editor exports safe when
clipboard access succeeds or fails.

## Manual Setup

Work from the ART-005 worktree and open the files directly from
`speckit-pro/artifact-gallery/templates/` in a browser; the address bar should
show a local `file://` URL, and no local server is needed. There is no build,
typecheck, or lint step for these standalone HTML artifacts; the main repository
check is `python3 tests/speckit-pro/run-all.py`, with focused checks available as
`python3 tests/speckit-pro/unit/test-artifact-gallery.py` and
`python3 tests/speckit-pro/unit/test-artifact-fill-regions.py`.

Before you start, record the operating system, browser name and version, network
condition, light or dark theme, reduced-motion setting, and approximate browser
width. For layout checks, resize the browser once to a narrow phone-sized width
near 360 CSS pixels and once to a desktop width near 1280 CSS pixels.

For editor clipboard failure checks, use one editor page at a time. Open the
browser developer console, paste one snippet, click `Copy as Markdown`, record
what you see, then reload the page before the next snippet.

```javascript
Object.defineProperty(navigator, "clipboard", { value: undefined, configurable: true });
```

```javascript
Object.defineProperty(navigator, "clipboard", { value: { writeText: "not callable" }, configurable: true });
```

```javascript
Object.defineProperty(navigator, "clipboard", { value: { writeText: () => Promise.reject(new DOMException("Denied", "NotAllowedError")) }, configurable: true });
```

```javascript
Object.defineProperty(navigator, "clipboard", { value: { writeText: () => Promise.reject(new Error("Copy failed")) }, configurable: true });
```

```javascript
Object.defineProperty(navigator, "clipboard", { value: { writeText: () => { throw new Error("Copy failed"); } }, configurable: true });
```

## Slice 1 Executable Rows

Acceptance check for `slide-deck`.

1. Open `speckit-pro/artifact-gallery/templates/slide-deck.html` from the local
   checkout. You should see a page titled `Slide Deck - RACE-421 Release
   Confidence` with the visible deck title `RACE-421 Release Confidence`.
2. Use the `Next slide` and `Previous slide` buttons. The visible position text
   should move between `Slide 1 of 3`, `Slide 2 of 3`, and `Slide 3 of 3`.
3. Use the keyboard arrows, Page Up/Page Down, Home, and End. The visible slide
   should change in the same bounded way, and it should not move before the first
   slide or after the last slide.
4. Leave the first slide idle for 30 seconds. The deck should stay on the same
   slide; it should not auto-advance.
5. Tab through the page. The theme control and deck controls should show a clear
   focus outline, and hidden slide content should not receive focus.
6. Toggle the dark theme, then reload. The same deck content and controls should
   remain visible and usable.
7. Turn the network off or use browser offline mode, then reload the same local
   file. The deck content, notes, theme control, and slide controls should still
   work.
8. Review the page at a narrow phone-sized width and at a desktop width. Text,
   controls, notes, and slide content should not overlap, clip, or create
   page-level horizontal scrolling.
9. Open `speckit-pro/artifact-gallery/manifest.json` and search for
   `slide-deck`. The entry should be marked `shipped`, point to
   `09-slide-deck.html`, and list no exports.

- [ ] The slide deck opens from disk, presents complete content, works by mouse
      and keyboard, stays readable offline and at both review widths, and remains
      a read-only artifact.

## Slice 2 Executable Rows

Acceptance check for `concept-explainer`.

1. Open `speckit-pro/artifact-gallery/templates/concept-explainer.html` from the
   local checkout. You should see a page titled `Concept Explainer - Consistent
   Hashing` with the visible heading `Consistent hashing, in one ring`.
2. Confirm the page includes the concept title, principles, worked example, and
   at least two simulation scenarios with visible `Watch:` guidance.
3. Use the `Nodes` and `Keys` sliders. The ring drawing, counts, key markers, and
   status text should update together.
4. Click `Add a node`, `Remove a node`, and `Reset simulation`. The visible node
   count should change, the status message should describe the action, and Reset
   should return to 4 nodes and 32 keys.
5. Try the lower and upper limits for nodes and keys. The page should explain the
   minimum or maximum in visible text, and the simulation should stay within its
   allowed range.
6. Reload the file after changing the simulation. The page should return to the
   representative starting state; the temporary simulation changes should not
   persist.
7. Tab through the theme control, sliders, and buttons. Every reachable control
   should have a clear name and visible focus.
8. Turn the network off or use browser offline mode, then reload the local file.
   The explanation, ring, controls, status text, and theme control should remain
   usable.
9. Review the page at a narrow phone-sized width and at a desktop width. The
   heading, grids, ring, sliders, buttons, status text, and scenario cards should
   stay inside the viewport without overlap or page-level horizontal scrolling.
10. Open `speckit-pro/artifact-gallery/manifest.json` and search for
    `concept-explainer`. The entry should be marked `shipped`, point to
    `15-research-concept-explainer.html`, and list no exports.

- [ ] The concept explainer opens from disk, shows complete content, explains
      control limits, resets temporary state on reload, stays usable offline and
      at both review widths, and remains a read-only artifact.

## Slice 3 Executable Rows

Acceptance check for `status-report`.

1. Open `speckit-pro/artifact-gallery/templates/status-report.html` from the
   local checkout. You should see a page titled `Status Report - Artifact Gallery
   Delivery` with the visible heading `Artifact Gallery Status`.
2. Confirm the report has Summary, Landed, In flight, Blocked, and Next actions
   sections.
3. Confirm each list section contains at least two anchored items with visible
   status or next-action text.
4. Confirm the summary shows the current state `On track` and the visible counts
   for landed, in-flight, and blocked work.
5. Tab through the page. The theme control should be the only authored keyboard
   stop, and it should show a clear focus outline.
6. Toggle the dark theme, then reload. The same report content, section headings,
   metrics, and status text should remain visible.
7. Turn the network off or use browser offline mode, then reload the same local
   file. The report should still render without missing content.
8. Review the page at a narrow phone-sized width and at a desktop width. The
   sections and lists should remain readable without clipping, overlap, or
   page-level horizontal scrolling.
9. Open `speckit-pro/artifact-gallery/manifest.json` and search for
   `status-report`. The entry should be marked `shipped`, point to
   `11-status-report.html`, and list no exports.

- [ ] The status report opens from disk, presents complete report content, has no
      disguised editor controls, stays readable offline and at both review
      widths, and remains a read-only artifact.

## Slice 4 Executable Rows

Acceptance check for `incident-report`.

1. Open `speckit-pro/artifact-gallery/templates/incident-report.html` from the
   local checkout. You should see a page titled `INC-2025-0412 - Elevated 502s on
   task sync` with the visible heading `Elevated 502s on task sync`.
2. Confirm the report includes Summary, Timeline, Impact, Root cause, and
   Follow-ups sections.
3. Use the report navigation links for Summary, Timeline, Impact, Root cause,
   and Follow-ups. Each link should move to the matching section.
4. Confirm the summary shows the incident ID, severity, resolved state, duration,
   owner, peak error rate, mitigation, and no-data-loss message.
5. Confirm the timeline is ordered and runs from rollout through resolution, and
   that follow-up items each show visible Status, Owner, and Due text.
6. Tab through the page. The theme control and report navigation links should be
   reachable and should show clear focus outlines.
7. Toggle the dark theme, then reload. The same incident content, navigation,
   timeline, impact details, and follow-ups should remain visible.
8. Turn the network off or use browser offline mode, then reload the same local
   file. The full report should still render without missing content.
9. Review the page at a narrow phone-sized width and at a desktop width. The
   navigation, report sections, timeline, and follow-ups should not clip,
   overlap, or create page-level horizontal scrolling.
10. Open `speckit-pro/artifact-gallery/manifest.json` and search for
    `incident-report`. The entry should be marked `shipped`, point to
    `12-incident-report.html`, and list no exports.

- [ ] The incident report opens from disk, presents complete incident content,
      supports keyboard navigation, stays readable offline and at both review
      widths, and remains a read-only artifact.

## Slice 5 Executable Rows

Acceptance check for `triage-board`.

1. Open `speckit-pro/artifact-gallery/templates/triage-board.html` from the
   local checkout. You should see `Release triage board`, four columns, six
   tickets, a filter, reset control, and `Copy as Markdown`.
2. Edit a ticket title. The ticket name and status message should update, and
   the page should make clear that the change is only in memory.
3. Move a ticket with the keyboard arrow controls. The ticket should move to the
   new visible column or position, focus should stay with the moved ticket, and a
   status message should describe the move.
4. Select a filter that hides tickets. Columns with no matching tickets should
   show explicit empty text instead of silently disappearing.
5. Click `Reset board`. The original six-ticket sample board should return.
   After editing again and reloading, the original sample board should return
   again; edited board state should not persist.
6. With clipboard access allowed, click `Copy as Markdown`, then paste into any
   plain-text field. The text should start with `# Triage Board Export`, group
   tickets under Now, Next, Later, and Cut, and include the latest visible ticket
   changes in the current order.
7. Run each clipboard failure snippet from Manual Setup, one at a time. After
   each failure, the page should show only `Copy failed. The Markdown export is
   available below for manual copy.`, reveal a labeled selectable text area with
   the exact Markdown export, and move focus to that field.
8. Try bad or unusual board data: empty a required ticket value, duplicate a
   ticket ID, and enter multiline text with Unicode, quotes, backticks, pipes,
   slashes, tabs, and line breaks. The export should keep the visible values in
   order and add a readable Issues section instead of deleting, renaming, or
   silently changing the input.
9. Change a ticket, click copy, change it again, and click copy again quickly.
   The visible status and any manual-copy field should describe only the newest
   copy attempt; older copy attempts should not bring back stale text.
10. Turn the network off or use browser offline mode, then reload the same local
    file. Editing, reset, copy, and manual-copy fallback should remain usable.
11. Review the page at a narrow phone-sized width and at a desktop width. The
    board, tickets, controls, messages, and fallback field should not clip,
    overlap, or create page-level horizontal scrolling.
12. Open `speckit-pro/artifact-gallery/manifest.json` and search for
    `triage-board`. The entry should be marked `shipped`, point to
    `18-editor-triage-board.html`, and list Markdown as its export.

- [ ] The triage board opens from disk, supports keyboard editing and movement,
      exports the current board as deterministic Markdown, recovers safely when
      clipboard copy fails, resets memory-only state on reload, and stays usable
      offline and at both review widths.

## Slice 6 Executable Rows

Acceptance check for `feature-flags`.

1. Open `speckit-pro/artifact-gallery/templates/feature-flags.html` from the
   local checkout. You should see `Feature flag configuration`, ordered groups,
   named flags, reset control, and `Copy as Markdown`.
2. Edit a group label, flag key, description, enabled state, dependency, and
   rollout value. The visible fields and status text should update immediately.
3. Try rollout values that are valid, empty, and invalid. Valid numbers should
   remain numbers; empty or invalid values should be shown as needing attention
   and export as `null` rather than being guessed or clamped.
4. Try valid, invalid, unavailable, and disabled-prerequisite dependencies. The
   page should distinguish those states with visible text.
5. Confirm the empty representative group says `No flags in this group.` and
   still appears in the export order.
6. Click Reset. The sample flag configuration should return. After editing again
   and reloading, the original sample configuration should return again; edited
   flag state should not persist.
7. With clipboard access allowed, click `Copy as Markdown`, then paste into any
   plain-text field. The text should start with `# Feature Flags Export`, contain
   one fenced JSON block, and include the latest visible values in the current
   group and flag order.
8. Run each clipboard failure snippet from Manual Setup, one at a time. After
   each failure, the page should show only `Copy failed. The Markdown export is
   available below for manual copy.`, reveal a labeled selectable text area with
   the exact Markdown export, and move focus to that field.
9. Try bad or unusual flag data: empty required group and flag text, duplicate a
   group ID, duplicate a flag key, enter invalid dependency and rollout text, and
   enter multiline Unicode or punctuation-heavy text. The export should preserve
   the raw visible values, keep duplicates in order, and add ordered issue
   records instead of deleting, renaming, or silently changing the input.
10. Extract the JSON block from the export and parse it in the browser console
    with `JSON.parse`. It should parse successfully, and the root, group, flag,
    and issue fields should stay in the visible order described by the page.
11. Change a flag, click copy, change it again, and click copy again quickly.
    The visible status and any manual-copy field should describe only the newest
    copy attempt; older copy attempts should not bring back stale text.
12. Turn the network off or use browser offline mode, then reload the same local
    file. Editing, reset, copy, and manual-copy fallback should remain usable.
13. Review the page at a narrow phone-sized width and at a desktop width. Groups,
    flags, controls, messages, and fallback field should not clip, overlap, or
    create page-level horizontal scrolling.
14. Open `speckit-pro/artifact-gallery/manifest.json` and search for
    `feature-flags`. The entry should be marked `shipped`, point to
    `19-editor-feature-flags.html`, and list Markdown as its export.

- [ ] The feature flag editor opens from disk, keeps visible editing feedback,
      exports current state as deterministic Markdown with JSON, recovers safely
      when clipboard copy fails, preserves bad input as explicit issue data,
      resets memory-only state on reload, and stays usable offline and at both
      review widths.

## Slice 7 Executable Rows

Acceptance check for `prompt-tuner`.

1. Open `speckit-pro/artifact-gallery/templates/prompt-tuner.html` from the
   local checkout. You should see `Support reply prompt tuner`, a prompt
   template, ordered slots, three samples, live previews, reset control, and
   `Copy as Markdown`.
2. Edit the template and a sample field. The preview for that sample should
   update immediately from the current visible values.
3. Duplicate a slot name, then enter an invalid slot name. The page should keep
   the raw visible text, show feedback for the duplicate or invalid slot, and not
   silently rename it.
4. Empty the template or a sample value. The page should show the empty state as
   intentional text or feedback instead of hiding the problem.
5. Click Reset. The sample prompt session should return. After editing again and
   reloading, the original sample session should return again; edited prompt
   state should not persist.
6. With clipboard access allowed, click `Copy as Markdown`, then paste into any
   plain-text field. The text should start with `# Prompt Tuner Export`, contain
   one fenced JSON block, and include the latest template, slots, samples, and
   previews in visible order.
7. Run each clipboard failure snippet from Manual Setup, one at a time. After
   each failure, the page should show only `Copy failed. The Markdown export is
   available below for manual copy.`, reveal a labeled selectable text area with
   the exact Markdown export, and move focus to that field.
8. Try bad or unusual prompt data: empty required text, duplicate slot and sample
   identifiers, invalid slot text, and multiline Unicode or punctuation-heavy
   values. The export should preserve the raw visible values, keep duplicates in
   order, preserve derived previews, and add ordered issue records instead of
   deleting, renaming, or silently changing the input.
9. Extract the JSON block from the export and parse it in the browser console
   with `JSON.parse`. It should parse successfully, and the root, slot, sample,
   field, preview, and issue order should match the visible page state.
10. Change the template, click copy, change it again, and click copy again
    quickly. The visible status and any manual-copy field should describe only
    the newest copy attempt; older copy attempts should not bring back stale
    text.
11. Turn the network off or use browser offline mode, then reload the same local
    file. Editing, previews, reset, copy, and manual-copy fallback should remain
    usable.
12. Review the page at a narrow phone-sized width and at a desktop width.
    Template fields, slots, samples, previews, controls, messages, and fallback
    field should not clip, overlap, or create page-level horizontal scrolling.
13. Open `speckit-pro/artifact-gallery/manifest.json` and search for
    `prompt-tuner`. The entry should be marked `shipped`, point to
    `20-editor-prompt-tuner.html`, and list Markdown as its export.

- [ ] The prompt tuner opens from disk, updates live previews, exports current
      state as deterministic Markdown with JSON, recovers safely when clipboard
      copy fails, preserves bad input as explicit issue data, resets memory-only
      state on reload, and stays usable offline and at both review widths.

## Source-Backed Not Applicable Rows

Record these as not applicable only when the source file and browser view both
show why the check does not apply.

1. Horizontal-scroll checks are not applicable for an artifact only when the
   page has no meaningful horizontal scroll region. The reviewer should still
   confirm at both review widths that there is no page-level horizontal overflow
   and no hidden scrollable content that a keyboard user needs to reach.
2. Producer export and clipboard checks are not applicable for `slide-deck`,
   `concept-explainer`, `status-report`, and `incident-report` because those
   four artifacts have no `Copy as Markdown` control and their manifest entries
   list no exports.
3. Reader-only status is not enough for the three editors. `triage-board`,
   `feature-flags`, and `prompt-tuner` must run the success, failure, bad-input,
   reset, and latest-copy checks in their sections above.

### Coverage Map

| Promise to verify | Where to check it |
|---|---|
| All seven local HTML artifacts open from disk and show complete sample content. | Step 1 and the content checks in each slice section. |
| The four reader artifacts have no export surface. | Final manifest step in Slices 1-4 plus not-applicable row 2 above. |
| The three editor artifacts export Markdown from the current visible state. | Clipboard success and live-edit checks in Slices 5-7. |
| Clipboard failure exposes exact manual-copy text and focus. | Clipboard failure snippet checks in Slices 5-7. |
| Editor state is memory-only and resets on reload. | Reset and reload checks in Slices 5-7. |
| Empty, invalid, duplicate, unavailable, and unusual values stay visible and are reported safely. | Bad-input checks in Slices 5-7 and limit checks in Slice 2. |
| Keyboard, focus, reduced-motion, color-independent meaning, and responsive behavior are covered. | Keyboard, theme, offline, and narrow/desktop width checks in every slice section. |
| Catalog entries match the shipped files and export classification. | Manifest step at the end of each slice section. |
