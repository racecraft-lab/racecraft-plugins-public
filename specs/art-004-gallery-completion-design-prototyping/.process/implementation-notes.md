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

**Deviations/Edge cases/Surprises:** Partial. The full suite passed 7418/7418 and the docs reference check passed after the UAT remediation. `refresh-release-artifacts.py --check` correctly remains red while regenerated payload and proof paths are uncommitted; rerun it after the Slice 1 checkpoint commit.
