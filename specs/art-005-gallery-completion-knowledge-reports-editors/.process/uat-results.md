# ART-005 UAT Results

Feature: ART-005 gallery completion knowledge reports/editors
Artifact: `slide-deck`
Template path: `speckit-pro/artifact-gallery/templates/slide-deck.html`
Runbook path: `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-runbook.md`
JSON path: `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.json`
Driver: `manual`
Status: T019 carrier creation; manual `file://` execution remains pending for
T022.

## Source Checkpoint vs Evidence Commit

The source checkpoint is the future T022 commit containing the source template,
manifest, tests, generated outputs, and existing evidence carriers to be tested.
The evidence commit is the later commit that records manual UAT results. The
JSON top-level `sourceCommit` must name the source checkpoint, not the evidence
commit.

T019 has no source checkpoint and no manual browser execution. The JSON therefore
uses honest pending placeholders for `sourceCommit` and `executedAt`, records no
pass verdicts, and includes only evidence-backed `not_applicable` rows.

## Row Totals

- Total Slice 1 rows: 36
- Pending executable rows: 18
- Evidence-backed N/A rows in JSON: 18
- JSON rows currently recorded: 18
- Pass verdicts: 0
- Fail verdicts: 0
- Not-applicable verdicts: 18

No pass verdicts are recorded in T019. Executable rows stay out of the JSON
because the closed schema allows only `pass`, `fail`, or `not_applicable`.

## Pending Executable Matrix

| Row | Claim | Current treatment |
|---|---|---|
| SD-UAT-001 | Direct file open loads the deck from `file://` with no server. | Pending T022 manual execution. |
| SD-UAT-002 | Complete representative fills cover `deck-title`, three anchored slides, and speaker notes. | Pending T022 manual execution. |
| SD-UAT-003 | Named slide navigation exposes the `Slide deck navigation` group and named controls. | Pending T022 manual execution. |
| SD-UAT-004 | Previous/next and keyboard/wheel navigation move through the bounded slide set. | Pending T022 manual execution. |
| SD-UAT-005 | Current-position updates report `Slide X of 3` after every slide change. | Pending T022 manual execution. |
| SD-UAT-006 | Control-triggered changes keep focus on the invoked control; keyboard/wheel changes focus the active slide. | Pending T022 manual execution. |
| SD-UAT-007 | Hidden slides are inaccessible until active. | Pending T022 manual execution. |
| SD-UAT-008 | No autorotation changes slide state while idle. | Pending T022 manual execution. |
| SD-UAT-009 | Offline reload preserves local reader usability. | Pending T022 manual execution. |
| SD-UAT-010 | Complete keyboard traversal records selector, role, name, and focus evidence for every stop. | Pending T022 manual execution. |
| SD-UAT-011 | Focus visibility is present for controls and programmatically focused slides. | Pending T022 manual execution. |
| SD-UAT-012 | Light/dark parity preserves content, controls, focus, and slide state. | Pending T022 manual execution. |
| SD-UAT-013 | Reduced-motion mode preserves behavior without meaningful animation. | Pending T022 manual execution. |
| SD-UAT-014 | Color-independent meaning is preserved by text and shape. | Pending T022 manual execution. |
| SD-UAT-015 | Horizontal scroll actual-element check follows the source-backed N/A route unless runtime finds a real scroll element. | Source-backed N/A row is in JSON; runtime layout confirmation remains part of T022 responsive review. |
| SD-UAT-016 | 360 CSS px layout has no page overflow, clipping, or overlap. | Pending T022 manual execution. |
| SD-UAT-017 | >=1280 CSS px layout has no page overflow, clipping, or overlap. | Pending T022 manual execution. |
| SD-UAT-018 | Manifest parity matches the ART-005 ID/source/role/status/export table. | Pending T022 manual execution; manifest parity is applicable for readers. |

## Evidence-Backed N/A Matrix

| Row | Case | JSON treatment | Evidence basis |
|---|---|---|---|
| SD-UAT-019 | `horizontal_scroll_region` | `not_applicable` with `accessibilityObservation.notApplicableReason` | Source has no `overflow-x:auto` or `overflow-x:scroll`; `html` and `body` use `overflow-x:hidden`; no runtime scroll element is claimed. |
| SD-UAT-020 | `live_export_freshness` | `not_applicable` with `dataIntegrityObservation.notApplicableReason` | `slide-deck` is a reader; manifest `exports` is `[]`; template has no export control. |
| SD-UAT-021 | `empty_values` | `not_applicable` with `dataIntegrityObservation.notApplicableReason` | No producer-owned serialized fields or export payload exist. |
| SD-UAT-022 | `invalid_raw_value` | `not_applicable` with `dataIntegrityObservation.notApplicableReason` | No producer-owned raw input parsing exists. |
| SD-UAT-023 | `unavailable_normalized_value` | `not_applicable` with `dataIntegrityObservation.notApplicableReason` | No producer-owned normalization exists. |
| SD-UAT-024 | `duplicate_identifiers` | `not_applicable` with `dataIntegrityObservation.notApplicableReason` | No producer-owned entity collection is exported. |
| SD-UAT-025 | `special_character_round_trip` | `not_applicable` with `dataIntegrityObservation.notApplicableReason` | No structured export round trip exists. |
| SD-UAT-026 | `multiple_issue_order` | `not_applicable` with `dataIntegrityObservation.notApplicableReason` | No editor issue list exists. |
| SD-UAT-027 | `clipboard_exact_equality` | `not_applicable` with `dataIntegrityObservation.notApplicableReason` | No clipboard or fallback export is attempted by this reader. |
| SD-UAT-028 | `superseded_copy_attempt` | `not_applicable` with `dataIntegrityObservation.notApplicableReason` | No copy attempt or stale export race surface exists. |
| SD-UAT-029 | `genuine_success` | `not_applicable` with `errorHandlingObservation.notApplicableReason` | No clipboard success path exists for this reader. |
| SD-UAT-030 | `clipboard_absent` | `not_applicable` with `errorHandlingObservation.notApplicableReason` | No clipboard fallback path exists for this reader. |
| SD-UAT-031 | `method_non_callable` | `not_applicable` with `errorHandlingObservation.notApplicableReason` | No clipboard method is called by this reader. |
| SD-UAT-032 | `permission_denied` | `not_applicable` with `errorHandlingObservation.notApplicableReason` | No permission-denied clipboard branch exists for this reader. |
| SD-UAT-033 | `generic_rejection` | `not_applicable` with `errorHandlingObservation.notApplicableReason` | No rejected-promise clipboard branch exists for this reader. |
| SD-UAT-034 | `synchronous_throw` | `not_applicable` with `errorHandlingObservation.notApplicableReason` | No synchronous clipboard call exists for this reader. |
| SD-UAT-035 | `sequential_transition` | `not_applicable` with `errorHandlingObservation.notApplicableReason` | No failure-success-failure transition surface exists for this reader. |
| SD-UAT-036 | `superseded_attempt` | `not_applicable` with `errorHandlingObservation.notApplicableReason` | No superseded clipboard attempt race exists for this reader. |

## Source Evidence Used For T019 Classifications

- `specs/art-005-gallery-completion-knowledge-reports-editors/contracts/uat-evidence-contract.md` defines the active paths, JSON schema, row schema, required matrix, and reader `not_applicable` rules.
- `specs/art-005-gallery-completion-knowledge-reports-editors/plan.md` Slice 1 defines the `slide-deck` UAT increment and active UAT carriers.
- `speckit-pro/artifact-gallery/manifest.json:170-178` declares `slide-deck`, source `09-slide-deck.html`, status `shipped`, and `exports: []`.
- `speckit-pro/artifact-gallery/templates/slide-deck.html:805-889` shows the reader content, three slide articles, speaker notes, and navigation controls.
- `speckit-pro/artifact-gallery/templates/slide-deck.html:486-492` sets `overflow-x:hidden` on `html` and `body`; source search found no `overflow-x:auto` or `overflow-x:scroll`.

## Slice 1 Pre-Generation Reviewability Measurement

Slice base: `1cf86bddecbca620234657f6e59a48991eabbc88` (the merge base of
`origin/main` and the Slice 1 branch).

The working-tree measurement used an explicit pathspec for exactly the seven
implementation-authored paths. The four new paths were first marked
intent-to-add so `git diff --numstat` included their uncommitted content.

| Authored path | Added | Deleted | Reviewable component LOC |
|---|---:|---:|---:|
| `speckit-pro/artifact-gallery/manifest.json` | 1 | 1 | 0 |
| `speckit-pro/artifact-gallery/templates/slide-deck.html` | 969 | 0 | 511 |
| `.process/uat-results.json` | 448 | 0 | 0 |
| `.process/uat-results.md` | 128 | 0 | 0 |
| `.process/uat-runbook.md` | 220 | 0 | 0 |
| `tests/speckit-pro/unit/test-artifact-fill-regions.py` | 4 | 0 | 4 |
| `tests/speckit-pro/unit/test-artifact-gallery.py` | 151 | 0 | 151 |

Physical seven-path result after this record: `1921` additions,
1 deletion. The raw `git diff --numstat` ledger therefore counts canonical and
evidence-carrier lines; it is reported rather than presented as reviewable LOC.

The plan-approved component method excludes the 458 byte-identical canonical
block lines and the manifest/UAT carrier lines, then counts the 511
non-canonical template lines plus 155 incremental test lines.

- Actual reviewable implementation LOC: **666**
- Remaining declared implementation LOC: **0**
- Final projected reviewable implementation LOC: **666**
- Slice 1 component ceiling: **670** (4 LOC headroom)
- Mandatory block threshold: **800** (134 LOC headroom)
- Verdict: **WARN / PASS** — above the 400 warning, below the 800 block; proceed
  to generated refresh.

The advisory runner's HTML classifier remains `production: 0`, `projected: 0`
as recorded in `plan.md`; it does not count these HTML implementation lines, so
the measured component result above controls this checkpoint.
