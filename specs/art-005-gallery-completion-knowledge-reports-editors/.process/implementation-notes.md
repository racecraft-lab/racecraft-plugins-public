# Implementation Notes: ART-005

### T001

**Deviations/Edge cases/Surprises:** None

### T002

**Deviations/Edge cases/Surprises:** None

### T003

**Deviations/Edge cases/Surprises:** Initial Layer 4 baseline passed 5,764 of 5,766 checks; both failures were the privacy scanner detecting an absolute local home path in quickstart.md. The path was replaced with a repository-root command before any implementation file changed.

### T003

**Deviations/Edge cases/Surprises:** After the quickstart repair, Layer 1 passed 1,448/1,448, Layer 4 passed 5,766/5,766, and the default suite passed 7,400/7,400.

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

**Deviations/Edge cases/Surprises:** None

### T011

**Deviations/Edge cases/Surprises:** None. The declared Slice 1 ledger remains exactly seven implementation-authored paths with a projected 670 reviewable LOC, leaving 130 LOC below the mandatory 800-LOC stop threshold.

### T012

**Deviations/Edge cases/Surprises:** First executor attempt produced no file change or structured task result within the task timebox and was interrupted before any mutation. T012 remained incomplete and was retried once per recovery policy.

### T012

**Deviations/Edge cases/Surprises:** The retry produced a partial 392-line test-only draft, exceeding the entire Slice 1 incremental-test budget of 155 LOC, and did not return a structured result within its tightened timebox. It was interrupted and replaced through the direct fallback with a smaller contract check that reuses existing scanner helpers.

### T012

**Deviations/Edge cases/Surprises:** Direct fallback completed with 151 added test lines, preserving four lines of the 155-LOC incremental-test budget for the fill inventory. The focused module reported the intended RED result, 487/488 passed, because `slide-deck` remains planned and its artifact is absent.

### T013

**Deviations/Edge cases/Surprises:** First executor attempt added the two exact floor/list rows, but the focused module remained green at 54/54 because all existing real-gallery fill checks are deliberately gated on `status == "shipped"` while `slide-deck` is still planned. A retry was required to add a minimal missing-template non-vacuity assertion without exceeding the 155-LOC test budget.

### T013

**Deviations/Edge cases/Surprises:** Retry completed the RED contract with exactly four added lines in the fill module. The focused module reported 54/55 passed, failing only because `templates/slide-deck.html` and its declared inventory do not exist; the two test-module additions total the planned 155 LOC exactly.

### T014

**Deviations/Edge cases/Surprises:** None. Formal RED proof produced 487/488 in the gallery module and 54/55 in the fill module. Direct diagnostics confirmed the row is `planned`, the reader artifact is absent, the fill-inventory template is absent, and the pinned floor/list-slot literals are active.

### T015

**Deviations/Edge cases/Surprises:** The executor's first local composition attempt used an unsupported `Path.read_text(newline=...)` argument and stopped before writing; the corrected attempt created only the template. The pinned digest reverified, both canonical regions are byte-identical, the fill module is green at 55/55, and the new reader contract now fails only on the T016-owned planned status. The file is 969 physical lines, 511 after excluding the 458 canonical lines, leaving the implementation projection at 666/670 with tests.

### T016

**Deviations/Edge cases/Surprises:** The executor briefly applied an over-broad status patch, detected it through the exact diff, and corrected it before returning. The final manifest diff is only `slide-deck.status: planned -> shipped`; source identity and `exports: []` are unchanged. `check_l1` is green, with the full gallery module retaining only four T021-owned generated-payload parity failures.

### T017

**Deviations/Edge cases/Surprises:** All new Slice 1 assertions are green: `check_l1` returned no failures, fill checks R1-R7 all returned empty lists, and the fill module passed 55/55. The complete gallery module reported 484/488 only because F1-F4 require T021's not-yet-regenerated Claude/Codex payload mirrors; this expected generated-state RED is outside the new reader assertions and was retained rather than bypassed.

### T018

**Deviations/Edge cases/Surprises:** No-op refactor review. The 511 non-canonical template lines are already flat and explicit; candidate reductions would weaken named focus/navigation, semantic hooks, or readable layout structure. Canonical agreement, reader checks, and fill R1-R7 remain green, and the Slice 1 implementation projection remains 666/670.

### T019

**Deviations/Edge cases/Surprises:** The executor initially created the three carriers in the parent checkout, then moved them into the dedicated worktree and verified no parent copies remained. The final carriers define 36 Slice 1 rows: 18 pending executable rows and 18 honest source-backed `not_applicable` rows (one scroll disposition, nine producer-only data-integrity cases, and eight clipboard/recovery cases). JSON parses with all required top-level fields and no fabricated pass/fail verdicts.

### T020

**Deviations/Edge cases/Surprises:** The explicit seven-path `git diff --numstat` ledger reports 1,921 physical additions and one deletion because it includes 458 canonical-copy lines plus the manifest and active UAT carriers. Applying the plan-approved component method yields 511 non-canonical template LOC plus 155 incremental test LOC = 666 actual/final reviewable LOC, with zero remaining work, four lines below the 670 ceiling and 134 below the 800 block. The raw physical and reviewable ledgers are both recorded in `uat-results.md`.

### T021

**Deviations/Edge cases/Surprises:** Authoritative release regeneration and docs `reference:generate` both completed; the docs generator rewrote seven reference pages byte-identically. Gallery parity is now green at 488/488. A pre-commit `refresh-release-artifacts.py --check` reports the newly generated uncommitted paths as drift by design; T022 will commit the source checkpoint, after which the clean-tree check can pass. No generated mirror was hand-edited.

### T022

**Deviations/Edge cases/Surprises:** First direct attempt passed focused 488/488 and 55/55, Layer 1 1448/1448, Layer 4 5769/5769, full suite 7403/7403, generator idempotence, post-commit generated check, and spec-index check; source checkpoint `660bfe9ce8365afbe6d98af28dd26eccf46a2c9e` is clean. Manual UAT did not start because browser selection returned `No browser is available` and the one permitted availability inspection returned an empty list. T022 remains incomplete pending a connected browser in this session; no pass/fail UAT verdict was fabricated.

### T022 (resumed)

**Deviations/Edge cases/Surprises:** The operator clarified that Playwright or Chrome DevTools MCP is the fallback only when connected browser/computer-use is unavailable, so the prior `No browser is available` result activated Playwright MCP. Its safe navigation wrapper blocked `file://`; the narrow Playwright code action opened only the exact local template. Google Chrome 151.0.7922.138 then completed all 36 rows at source checkpoint `660bfe9ce8365afbe6d98af28dd26eccf46a2c9e`: 18 pass, 18 evidence-backed `not_applicable`, zero fail. Coverage included trusted wheel input, complete keyboard/focus traversal, two 30-second no-autorotation observations, context-offline reload, light/dark persistence, reduced motion, color-independent cues, and all slides at 360 and 1280 CSS px. The cumulative JSON is checkpoint-bound and the tested source bytes remain unchanged.

### T023

**Deviations/Edge cases/Surprises:** Source and generated gallery paths remained unchanged after checkpoint `660bfe9ce`. The final rerun passed focused 488/488 and 55/55, Layer 1 1448/1448, Layer 4 5769/5769, full suite 7403/7403, generated-artifact check, and spec-index check. The implementation interval contains seven authored paths, 24 generated paths, and four required process/prerequisite paths; the full PR boundary is 57 paths because the same branch carries the prerequisite ART-005 scaffold and plan. This is recorded as a total-file size-only block with 666 reviewable LOC and no correctness or non-size blocker. Runner-emitted packet `art-005-slice-1-slide-deck` passed read-only and persisted validation, workflow-title validation, exact CI release-readiness title validation, and release-note policy. Push advanced the remote head to evidence checkpoint `373881395f40115dd80953c4b8892dc79346ce22`, and PR #444 opened at https://github.com/racecraft-lab/racecraft-plugins-public/pull/444.
