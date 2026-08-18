# Implementation Notes: ART-004

### T001

**Deviations/Edge cases/Surprises:** None

### T002

**Deviations/Edge cases/Surprises:** None

### T003

**Deviations/Edge cases/Surprises:** None

### T004

**Deviations/Edge cases/Surprises:** None

### T005

**Deviations/Edge cases/Surprises:** None

### T006

**Deviations/Edge cases/Surprises:** None

### T007

**Deviations/Edge cases/Surprises:** None

### T008

**Deviations/Edge cases/Surprises:** None

### T009

**Deviations/Edge cases/Surprises:** None

### T010

**Deviations/Edge cases/Surprises:** Attempt 1 remained file-silent and did not return a progress signal; it was interrupted before any owned-file change, and the task requires a fresh executor.

### T010

**Deviations/Edge cases/Surprises:** An orphaned patch from an interrupted executor already contained the T010 coverage plus T011/T012 assertions; the recovery worker verified the coherent one-file RED state without additional edits.

### T011

**Deviations/Edge cases/Surprises:** The exact T011 fixture already existed in the recovered T010 patch, so verification required no additional file change.

### T012

**Deviations/Edge cases/Surprises:** `annotated-diff` and `flowchart` shipped complete keyboard routes before the explicit data marker existed; a narrowly scoped compatibility set recognizes only those two routes while repaired and future targets still require the declaration.

### T013

**Deviations/Edge cases/Surprises:** The plan counted one CSS overflow site, but that selector creates three runtime scrollers; all three DOM instances required the repair to avoid leaving two inaccessible.

### T014

**Deviations/Edge cases/Surprises:** None

### T015

**Deviations/Edge cases/Surprises:** Two CSS overflow sites produce six runtime scrollers: one diagram plus five reused code blocks; all six DOM instances required the repair.

### T016

**Deviations/Edge cases/Surprises:** None

### T017

**Deviations/Edge cases/Surprises:** None

### T018

**Deviations/Edge cases/Surprises:** The first Playwright `file://` run found that module-map's five code regions received focus but expanded the grid instead of acquiring their own scroll range. Changing the content track from `1fr` to `minmax(0, 1fr)` kept the document at the viewport width; the repeated run passed all 11 repaired regions at 320 by 900.

### T019

**Deviations/Edge cases/Surprises:** Safari initially refused automation until the operator enabled Safari Settings > Developer > Allow remote automation. Safari 26.6.1 then passed all 11 regions over `file://`; this Mac's active route is Tab, and the five module-map disclosures opened with Enter before their code regions entered sequential focus order.

### T020

**Deviations/Edge cases/Surprises:** None

### T021

**Deviations/Edge cases/Surprises:** None

### T022

**Deviations/Edge cases/Surprises:** The full suite passed 7418/7418 after the UAT remediation. After checkpoint `e15e3a6cc`, `refresh-release-artifacts.py --check` confirmed generated release artifacts match source and the docs reference check confirmed reference pages are current.

### T023

**Deviations/Edge cases/Surprises:** Group M's real-gallery RED is intentionally limited to the four planned rows and four missing files; nine synthetic fixtures prove attribution, canonical blocks, disabled export-looking controls, and offline references without vacuity.

### T024

**Deviations/Edge cases/Surprises:** R8 keeps the active Slice 2 floor non-vacuous while R1-R7 continue to defer planned templates. Its sole real-gallery failure enumerates the four planned rows and four missing files.

### T025

**Deviations/Edge cases/Surprises:** The smallest intentional horizontal-region floors are one each for `design-system`, `animation-prototype`, and `svg-illustrations`. `interaction-prototype` has no horizontal-overflow site in the pinned source, and the responsive SVG canvases do not justify a one-per-illustration floor.

### T026

**Deviations/Edge cases/Surprises:** The port passed isolated canonical, fill-region, read-only, and keyboard-scroll checks. Group M5 exposed a shared test false positive for the byte-identical canonical font URL because parsed `&` was compared with raw `&amp;`; the canonical block was correctly left unchanged for T031 to repair the test.

### T027

**Deviations/Edge cases/Surprises:** The task row is a native `aria-pressed` button so completion and reset are keyboard operable; the three easing controls preserve selection while completion resets. The shared M5 entity-decoding false positive also affects this canonical head.

### T028

**Deviations/Edge cases/Surprises:** The compact port retains keyboard move controls alongside pointer drag, at least three anchored views, visible order, insertion state, cleanup, and reset semantics. No owned-file blocker remained.

### T029

**Deviations/Edge cases/Surprises:** The three responsive SVG canvases remain responsive; one intentional gallery-level horizontal region satisfies keyboard access without forcing artificial per-canvas overflow. Upstream `Download SVG` controls were omitted as required.

### T030

**Deviations/Edge cases/Surprises:** The final manifest diff was verified to contain exactly four `planned` to `shipped` changes for the Slice 2 IDs and no other field or row change.

### T031

**Deviations/Edge cases/Surprises:** Group M now parses the canonical head before comparing optional-font references, so HTML entity normalization cannot produce a false positive. Compact M6 inventories preserve the four ports' stable selectors and source capabilities without an exhaustive fixture matrix.

### T032

**Deviations/Edge cases/Surprises:** The generic list-slot floor remains two; only `interaction-prototype.views` requires three anchored entries to preserve the approved retained-view contract.

### T033

**Deviations/Edge cases/Surprises:** Group M and Group L passed 26 focused tests, and the fill-region suite passed 62/62. The four remaining full-gallery failures were generated-payload parity checks intentionally deferred to T035.

### T034

**Deviations/Edge cases/Surprises:** Chromium UAT found one real 360px overflow in the interaction port. Zero-minimum grid/content tracks plus wrapping for the pinned source note restored document-width parity without changing desktop layout. Chromium then passed the full offline matrix. Safari 26.6.1 required Option-Tab for native controls in the active browser setting; isolated `file://` runs passed all four ports, including focus exit, keyboard interactions, reset/cleanup, theme toggle, and ArrowRight scrolling. A bounded page-load wait prevented the optional remote font stylesheet from blocking the offline Safari harness.

### T035

**Deviations/Edge cases/Surprises:** None

### T036

**Deviations/Edge cases/Surprises:** None

### T037

**Deviations/Edge cases/Surprises:** The full suite passed 7450/7450. The release `--check` intentionally rejects any generated-path Git status, even when regeneration is correct, so it was rerun after Slice 2 checkpoint `01e97ad65`; the isolated regeneration comparison and docs reference check then passed on a clean tree.

### T038

**Deviations/Edge cases/Surprises:** Group N reuses generalized status-baseline, attribution/canonical, control, and offline helpers from Group M. Eight fixtures pass; the real gallery fails only because the two rows remain planned and the two files are absent.

### T039

**Deviations/Edge cases/Surprises:** R9 pins all four required markers for each decision port plus the exact `directions` and `variants` list slots. Thirty-four fixtures pass; the only real failure reports the two planned rows and two missing files.

### T040

**Deviations/Edge cases/Surprises:** Group O statically pins the decision-export structure, exact payload and validation contract, one guarded clipboard-write path, shared refusal handling, fallback invalidation, and stale invocation suppression. All twelve fixtures pass; the real gallery fails only O1 for the two missing decision-port files. Runtime behavior remains deliberately assigned to T048.

### T041

**Deviations/Edge cases/Surprises:** Group P checks planned decision files directly so labelled native controls, state/value semantics, logical focus order, audited token colors, non-color component-state markers, and local reduced-motion overrides cannot pass vacuously before the manifest flip. Group L additionally requires the component snippet's one intentional horizontal-scroll declaration. Seventeen shared decision fixtures pass; the real gallery remains RED only on the two missing files and the not-yet-shipped snippet route.

### T042

**Deviations/Edge cases/Surprises:** The visual-design port preserves four directions and the background comparison while deriving both exports from the selected direction, rationale, and live background. Its refusal path is shared locally by the two copy controls without introducing cross-file runtime code.

### T043

**Deviations/Edge cases/Surprises:** The component port preserves six visible state families and live padding, border, and shadow controls. The reset path resolves the currently selected base variant before refreshing the snippet, preventing reset from silently returning export context to the first card.

### T044

**Deviations/Edge cases/Surprises:** The manifest diff contains only the two intended `planned` to `shipped` changes for `visual-designs` and `component-variants`.

### T045

**Deviations/Edge cases/Surprises:** Refactoring remained inside each standalone HTML file. No shared runtime or new abstraction was introduced.

### T046

**Deviations/Edge cases/Surprises:** The tightened contract requires one exact refusal message, one guarded `writeText` call, three invocation checks plus the declaration, one focus/select operation, and suppression of stale success after a newer attempt.

### T047

**Deviations/Edge cases/Surprises:** Fill-region coverage passed 70/70 and all focused Group N/O/P/L checks passed. The full gallery passed 563/567; only the four generated-payload parity checks remained for T050.

### T048

**Deviations/Edge cases/Surprises:** Playwright Chromium/WebKit passed seventeen decision-export scenario groups, including the six refusal modes, exact prompt/Markdown order, validation without clipboard calls, fallback parity and focus, invalidation, and stale-settle protection. The installed MCP profile was already in use, so the approved isolated Playwright fallback preserved the active browser session.

### T049

**Deviations/Edge cases/Surprises:** Chromium passed the complete offline accessibility matrix at 360 px. Safari 26.6.1 used Option-Tab and passed both ports, including native ArrowRight snippet scrolling from 0 to 29. Headless WebKit did not synthesize the generic scroller's default key action, so that single native-engine path is supported by the real Safari result rather than inferred from the headless runner.

### T050

**Deviations/Edge cases/Surprises:** Authoritative regeneration added both decision templates to the Claude and Codex payloads and installed-cache fixtures, then refreshed the manifest copies and proof-chain records. No generated surface was hand-edited.

### T051

**Deviations/Edge cases/Surprises:** Reference generation completed for all seven pages. The generated pages were already byte-current, so no docs reference diff remained.

### T052

**Deviations/Edge cases/Surprises:** Focused gallery and fill suites passed 567/567 and 70/70. The full suite passed 7496/7496. After checkpoint `0a8228a8c`, release-artifact and docs-reference checks both passed on a clean tree.
