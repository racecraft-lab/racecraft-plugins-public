# ART-005 UAT Results

Feature: ART-005 gallery completion knowledge reports/editors
Artifact: `slide-deck`
Template path: `speckit-pro/artifact-gallery/templates/slide-deck.html`
Runbook path: `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-runbook.md`
JSON path: `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.json`
Driver: `manual`
Status: T022 complete; all 36 Slice 1 rows are bound to source checkpoint
`660bfe9ce8365afbe6d98af28dd26eccf46a2c9e`.

## Source Checkpoint vs Evidence Commit

The source checkpoint is
`660bfe9ce8365afbe6d98af28dd26eccf46a2c9e`. It contains the source template,
manifest, tests, generated outputs, and pre-execution evidence carriers that
were tested. The later evidence commit records these results without changing
the tested source bytes. The JSON correctly names the source checkpoint rather
than the evidence commit.

The connected browser returned `No browser is available`. Per the operator's
fallback instruction, Playwright MCP supplied browser interaction and
observation. No repository browser harness was committed, so the contract
driver remains `manual`.

## Execution Environment

- Executed at: `2026-08-18T17:07:11Z`
- OS: macOS 26.6.2, Build 25G82, arm64
- Browser: Google Chrome 151.0.7922.138
- Scheme: direct `file://`
- Viewports: 360x800 and 1280x900 CSS px
- Network: online baseline plus context-offline reload with
  `net::ERR_INTERNET_DISCONNECTED` remote probe
- Themes: light and dark, including persisted-dark reload
- Motion: no-preference plus `prefers-reduced-motion: reduce`
- Color-independent review: Ready/Watch/Stop text plus circle/square/block

## Row Totals

- Total Slice 1 rows: 36
- Executed pass rows: 18
- Evidence-backed N/A rows in JSON: 18
- JSON rows currently recorded: 36
- Pass verdicts: 18
- Fail verdicts: 0
- Not-applicable verdicts: 18

Every executable row passed; no result is omitted from the normalized JSON.

## Executed Matrix

| Row | Verdict | Evidence summary |
|---|---|---|
| SD-UAT-001 | Pass | Exact repository-relative template opened over `file://`; expected title/h1 rendered; zero final-load console errors. |
| SD-UAT-002 | Pass | `deck-title`, all three anchored slides, and three ordered speaker notes were complete. |
| SD-UAT-003 | Pass | Named navigation, named controls, shared `aria-controls`, and polite position region were exposed. |
| SD-UAT-004 | Pass | Buttons, all declared keys, Home/End, and trusted bounded wheel input navigated correctly. |
| SD-UAT-005 | Pass | `Slide 1/2/3 of 3` tracked state and clamped at both boundaries. |
| SD-UAT-006 | Pass | Enabled invoked controls retained focus; keyboard/wheel changes focused the active article. |
| SD-UAT-007 | Pass | Inactive articles stayed hidden, inert, aria-hidden, and absent from traversal. |
| SD-UAT-008 | Pass | Two 30-second observations held at slide 1 with BODY and stage focus respectively. |
| SD-UAT-009 | Pass | Offline remote probe failed as expected while local content, controls, theme, and navigation remained usable. |
| SD-UAT-010 | Pass | Complete forward/backward stop order was recorded for first, middle, and last slide control states. |
| SD-UAT-011 | Pass | Theme control, enabled nav controls, and each focused slide showed measured outlines. |
| SD-UAT-012 | Pass | Light/dark content and state matched; dark persisted across reload; dark focus remained visible. |
| SD-UAT-013 | Pass | Reduce mode computed 0.01ms durations, zero running animations, and complete navigation. |
| SD-UAT-014 | Pass | Ready/Watch/Stop used visible text and circle/square/block shapes. |
| SD-UAT-015 | Pass | Source and runtime found no meaningful horizontal-scroll element at either width. |
| SD-UAT-016 | Pass | All slides passed at 360 CSS px with no page overflow, hidden clipping, or visual overlap. |
| SD-UAT-017 | Pass | All slides passed at 1280 CSS px with no page overflow, hidden clipping, or visual overlap. |
| SD-UAT-018 | Pass | Manifest matched ID, title, pinned source, reader role, shipped status, and `exports: []`. |

## Evidence-Backed N/A Matrix

| Row | Case | JSON treatment | Evidence basis |
|---|---|---|---|
| SD-UAT-019 | `horizontal_scroll_region` | `not_applicable` with `accessibilityObservation.notApplicableReason` | Source has no `overflow-x:auto` or `overflow-x:scroll`; `html` and `body` use `overflow-x:hidden`; 360 and 1280 CSS px runtime review found no actual scroll element. |
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

## Source and Browser Evidence Used For T022

- `specs/art-005-gallery-completion-knowledge-reports-editors/contracts/uat-evidence-contract.md` defines the active paths, JSON schema, row schema, required matrix, and reader `not_applicable` rules.
- `specs/art-005-gallery-completion-knowledge-reports-editors/plan.md` Slice 1 defines the `slide-deck` UAT increment and active UAT carriers.
- `speckit-pro/artifact-gallery/manifest.json:170-178` declares `slide-deck`, source `09-slide-deck.html`, status `shipped`, and `exports: []`.
- `speckit-pro/artifact-gallery/templates/slide-deck.html:805-889` shows the reader content, three slide articles, speaker notes, and navigation controls.
- `speckit-pro/artifact-gallery/templates/slide-deck.html:486-492` sets `overflow-x:hidden` on `html` and `body`; source search found no `overflow-x:auto` or `overflow-x:scroll`.
- Playwright accessibility snapshots and runtime state checks covered navigation
  naming, focus order, hidden/inert state, live position text, responsive
  geometry, reduced motion, theme parity, and zero final-load console errors.
- Playwright context offline mode produced
  `net::ERR_INTERNET_DISCONNECTED` for a remote probe while the local deck
  reloaded and navigated successfully.

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

## Slice 1 Final Boundary Ledger (T023)

Remote refs were refreshed immediately before this measurement. `origin/main`
and the branch merge base both resolve to
`1cf86bddecbca620234657f6e59a48991eabbc88`; the Slice 1 source checkpoint is
`660bfe9ce8365afbe6d98af28dd26eccf46a2c9e`.

The post-checkpoint diff contains only the workflow/state, implementation notes,
three UAT carriers, and `tasks.md`. The source template, source manifest, focused
tests, payload mirrors, installed-cache mirrors, and generated proofs are
byte-stable after the tested checkpoint. This proves the UAT result remains
bound to the source bytes that were exercised.

### Implementation-stage interval

The implementation-stage interval begins at `0a8199c58` (`chore(art-005): start
implementation stage`) and contains 35 physical Git paths before PR-packet
generation:

- Seven implementation-authored paths:
  - `speckit-pro/artifact-gallery/manifest.json`
  - `speckit-pro/artifact-gallery/templates/slide-deck.html`
  - `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.json`
  - `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-results.md`
  - `specs/art-005-gallery-completion-knowledge-reports-editors/.process/uat-runbook.md`
  - `tests/speckit-pro/unit/test-artifact-fill-regions.py`
  - `tests/speckit-pro/unit/test-artifact-gallery.py`
- Twenty-four source-derived generated paths:
  - `dist/claude/speckit-pro/artifact-gallery/manifest.json`
  - `dist/claude/speckit-pro/artifact-gallery/templates/slide-deck.html`
  - `dist/codex/speckit-pro/artifact-gallery/manifest.json`
  - `dist/codex/speckit-pro/artifact-gallery/templates/slide-deck.html`
  - `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`
  - `docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json`
  - `docs/ai/specs/.process/XPLAT-009-release-readiness-result.json`
  - `docs/ai/specs/.process/autopilot-state.json`
  - `specs/art-005-gallery-completion-knowledge-reports-editors/SPEC-MOC.md`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-file-root.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-mutable.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-source-root.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-mutable.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-root-mismatch.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-same-root.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-single-product.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-source-mismatch.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-stale-hash.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-traversal-root.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/manifest.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/artifact-gallery/templates/slide-deck.html`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/manifest.json`
  - `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/artifact-gallery/templates/slide-deck.html`
- Four required process/prerequisite paths:
  - `docs/ai/specs/.process/ART-005-workflow.md`
  - `specs/art-005-gallery-completion-knowledge-reports-editors/.process/implementation-notes.md`
  - `specs/art-005-gallery-completion-knowledge-reports-editors/quickstart.md`
  - `specs/art-005-gallery-completion-knowledge-reports-editors/tasks.md`

The 35-path interval exceeds the 25-file block threshold and the projected
33-path maximum by two. The variance is process evidence: the workflow and
implementation-note carriers required by autonomous execution plus the
pre-source privacy correction in `quickstart.md`; it is not another production
surface, later-slice source, or shared gallery runtime change. With 666
reviewable LOC, one production template, one primary surface, and all
correctness gates green, the disposition is **SIZE-ONLY BLOCK / CONTINUE** under
the operator-ratified seven-branch topology. No typed reviewability exception is
claimed.

### Complete PR branch boundary

Against refreshed `origin/main`, the branch contains 57 paths before packet
generation: the seven Slice 1 implementation-authored paths, 28 generated paths,
and 22 ART-005 scaffold/spec/plan/checklist/control-plane paths created by the
prerequisite phases in this same workflow-bearing branch. The 22 additional
foundation paths are:

- `docs/ai/specs/.process/ART-005-design-concept.md`
- `docs/ai/specs/.process/ART-005-workflow.md`
- `docs/ai/specs/html-artifacts-technical-roadmap.md`
- `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/.process/implementation-notes.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/checklists/accessibility.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/checklists/data-integrity.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/checklists/error-handling.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/checklists/requirements.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/checklists/ux.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/contracts/editor-export-contract.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/contracts/gallery-template-contract.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/contracts/slice-topology-contract.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/contracts/uat-evidence-contract.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/data-model.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/plan.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/quickstart.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/research.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/spec.md`
- `specs/art-005-gallery-completion-knowledge-reports-editors/tasks.md`
- `tests/speckit-pro/layer1-structural/validate-codex-skills.py`
- `tests/speckit-pro/parity/bash-to-python/validate-codex-skills-baseline.txt`

The clone-local `.git/info/exclude` intentionally excludes the feature-local
`.process/pr-packets/` directory. The packet JSON, generated body, and validation
JSON are current PR-emission evidence but are not committed PR paths. The final
review boundary therefore remains 57 physical paths. The packet records the
complete 57-path boundary and keeps the result `blocked` for budget evidence,
with the size-only continuation stated in the body.

### Final verification rerun

- Focused gallery module: **488/488**
- Focused fill module: **55/55**
- Layer 1: **1448/1448**
- Layer 4: **5769/5769**
- Full suite: **7403/7403**
- Generated release artifact check: **pass**
- Python-authoritative spec-index check: **pass**
- Source changed after UAT checkpoint: **no**
