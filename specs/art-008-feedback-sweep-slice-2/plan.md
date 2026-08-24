# Implementation Plan: ART-008 slice 2 — Artifact Freshness

**Branch**: `art-008-feedback-sweep-slice-2` | **Date**: 2026-08-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/art-008-feedback-sweep-slice-2/spec.md`

## Summary

Slice 1 gave the autopilot run a pull-request feedback sweep that amends the
planning artifacts and then stops for re-review. It leaves the reviewer looking
at draft artifact pages and a draft pull-request description that both describe
the plan the sweep just amended away, and it says so out loud: the stop report
carries a sentence promising that the pages regenerate once slice 2 lands.

This slice replaces that promise with the act. Three things go in, and every one
of them reuses machinery that already ships:

1. **A freshness verdict.** One new read-only runner helper joins
   `read_only.py` beside `sweep_pr_feedback`. It reads the `Feedback Sweep Log`
   from the workflow file it is given, joins each `amended` row's `Commit`
   against ancestry facts the orchestrator supplies as data, and returns one of
   four verdicts. It runs no `git`, no `gh`, and no network call.
2. **A regeneration trigger.** On a `stale` verdict the run re-dispatches the
   shipped `artifact-author` agent against the amended planning record, deletes
   the pages re-selection no longer names, commits the artifacts directory
   alone, pushes, and then refreshes the pull-request description through
   ART-007's create-or-refresh path. No new page-authoring code, no new
   emission code.
3. **One honest report.** Per-page outcomes, the regeneration commit's sha, and
   the refresh result land in the run report every sweep leg already builds, and
   the two slice-1 promise passages come out on both platform surfaces.

The seam this slice does **not** cross is the emission machinery itself. Slice 2
supplies the trigger and the timing. Selection, authoring, on-disk verification,
the three shortfall sinks, the `Draft PR` row's single writer, and the fail-open
posture are ART-007's and stay exactly as they are.

## Technical Context

**Language/Version**: Python 3.11+, standard library only. No third-party
runtime dependency, no Bash, no `jq`, no shell fallback.

**Primary Dependencies**: None added. The helper joins the existing
`speckit_pro_runner` surface and reuses two shipped pure functions verbatim —
`corroborate_draft_pr` and `workflow_draft_pr_row`.

**Storage**: None. The `Feedback Sweep Log` in the workflow file is the sole
record (FR-003). No state file, no mirror, no cache.

**Testing**: `python3 tests/speckit-pro/run-all.py` (Layers 1, 4, 5). New Layer 4
fixture-driven unit coverage under `tests/speckit-pro/unit/`, declared in
`tests/speckit-pro/suite-manifest.json`.

**Target Platform**: Both distributions. Claude Code autopilot references under
`speckit-pro/skills/speckit-autopilot/references/` and Codex mirrors under
`speckit-pro/codex-skills/speckit-autopilot/references/`.

**Project Type**: Plugin harness and adapter. Deterministic runner helper plus
orchestrator reference prose.

**Performance Goals**: Not a factor. The helper reads one Markdown file and
walks a table whose row count is the number of comments a sweep has ever
handled on this feature.

**Constraints**: The helper is offline and deterministic (FR-004). The workflow
file is the only path it reads. Every git fact and the pre-regeneration page
inventory arrive as request data (FR-004a). Commit recency is encoded as
ancestry, never as a timestamp or a sha-string comparison (FR-004a, FR-008).

**Scale/Scope**: 46 functional requirements, 3 user stories, 5 production files,
7 test and fixture files.

No unresolved clarification marker remains. Three Clarify sessions closed every open
question the design concept carried; `spec.md` §Clarifications records the
answers and supersedes the design concept where the two differ.

## Declared File Operations

The plan-phase reviewability estimator (`estimate-reviewable-loc`) parses this
block to project the slice's production-LOC footprint before `tasks.md` exists.
List one entry per file on its own line, each starting with a `- ` list marker:
`- NEW <repo-relative-path>` for a new file or `- MODIFIED <repo-relative-path>`
for an existing one.

Production surface (authored, reviewable):

- MODIFIED speckit-pro/speckit_pro_runner/helpers/read_only.py
- MODIFIED speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED speckit-pro/skills/speckit-autopilot/references/phase-execution.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md
- MODIFIED speckit-pro/skills/speckit-autopilot/SKILL.md

Test and fixture surface (authored, verification):

- NEW tests/speckit-pro/unit/test-artifact-freshness.py
- NEW tests/speckit-pro/unit/fixtures/artifact-freshness/freshness-cases.json
- NEW tests/speckit-pro/unit/fixtures/artifact-freshness/expected-envelopes.json
- NEW tests/speckit-pro/unit/fixtures/read-only-helpers/requests/check-artifact-freshness.json
- MODIFIED tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py
- MODIFIED tests/speckit-pro/unit/fixtures/read-only-helpers/fixture-manifest.json
- MODIFIED tests/speckit-pro/suite-manifest.json

Generated surface (regenerate, never hand-edit, not counted as reviewable):

- MODIFIED dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py
- MODIFIED dist/claude/speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED dist/claude/speckit-pro/skills/speckit-autopilot/references/phase-execution.md
- MODIFIED dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md
- MODIFIED dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py
- MODIFIED dist/codex/speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED dist/codex/speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md
- MODIFIED dist/codex/speckit-pro/skills/speckit-autopilot/references/phase-execution.md
- MODIFIED dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- MODIFIED speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/skills/speckit-autopilot/references/phase-execution.md
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md
- MODIFIED docs-site/src/content/docs/reference/tests.md

The `dist/` and installed-cache entries are byte-identical copies produced by
`python3 scripts/refresh-release-artifacts.py`, which recomputes the runner
trust metadata, rebuilds both payloads, content-syncs the installed-cache
fixtures, and refreshes the proof tree hashes. `spec.md` §Assumptions records
this as required rather than optional, and CI's `artifact-consistency` job fails
the pull request when it is skipped. The docs reference page enumerates test
paths, so a new test module and a new fixture directory restale it; refresh it
with `pnpm --dir docs-site reference:generate` after
`pnpm --dir docs-site install --frozen-lockfile`.

### Four files deliberately absent from this block

- **`speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md`
  and its Codex mirror.** Slice 2 adds no workflow-file entry. It reads the
  `Feedback Sweep Log` slice 1 already documented, writes no row of its own
  (`spec.md` Key Entities: "This slice never writes a row"), and FR-022 forbids
  a second writer of the `Draft PR` row. There is no grammar to add, so there
  is nothing to document.
- **`speckit-pro/codex-skills/speckit-autopilot/SKILL.md`.** Measured with the
  Layer 1 validator's own `_body` helper
  (`tests/speckit-pro/layer1-structural/validate-codex-skills.py:29,177-181`),
  its body is **7998 of its 8000-word cap** — two words of headroom. FR-030
  permits adding to it only after words are freed first, and nothing here needs
  to be added. FR-033b's second scoping edit binds the literal phrase
  "one read-only observation per run", which occurs exactly once in the tree, at
  `speckit-pro/skills/speckit-autopilot/SKILL.md:372`. The Codex skill's
  parallel wording at `codex-skills/speckit-autopilot/SKILL.md:596` reads
  "take exactly **one** read-only observation, scoped to the head branch" inside
  the Step 0.6c bullet itself, so it already carries the scoping FR-033b asks
  for and makes no unqualified per-run claim. FR-029's parity obligation is
  discharged by the scoping sentence added to
  `phase-execution-codex.md:1048`, which is where the behavior lives on that
  surface.
- **`speckit-pro/speckit_pro_runner/helpers/install.py`.** Slice 2 ships no new
  agent definition on either platform, so the Codex installer's closed
  `REQUIRED_CODEX_AGENT_NAMES` inventory is untouched. The regeneration
  dispatch is the shipped `speckit-pro:artifact-author` agent, unchanged.

## Reviewability Budget, derived by hand

### The estimator returns an absent measurement, not a pass

`estimate-reviewable-loc` projects from production files only, and counts a file
as production only when its path sits under `src/`, `app/`, `lib/`, or
`scripts/`, or when it ends in a JavaScript, TypeScript, or SQL extension. Every
production path above fails both tests: the runner helpers sit under
`speckit-pro/speckit_pro_runner/`, and the three reference and skill files are
Markdown.

Run against this plan, verbatim:

```json
{"tool":"estimate-reviewable-loc","status":"pass","projected":0,
 "declared_files":{"production":0,"new":4,"modified":26,"total_entries":30},
 "greenfield":false,
 "thresholds":{"warn":400,"block":800,"greenfield_multiplier":1.5,
               "base_warn":400,"base_block":800}}
```

Read it closely. The block parsed correctly — all **30** entries were seen, 4
new and 26 modified, which is every line of the Declared File Operations block
including the generated surface — and **`production` is 0**. The helper is not
failing to read the plan; it is reading it correctly and finding nothing it
recognizes as production code. `projected` is therefore 0 and `status` is `pass`
against a warn line of 400 it never had a chance to cross. **That `pass` is an absent measurement and MUST NOT be cited as evidence
this slice is within budget.** The tables below are the measurement.

### The counting rule, stated before the numbers

Two different bases are in play and mixing them silently would make the figure
meaningless.

- **Production-only** is the basis the gate's own estimator uses and the basis
  slice 1's plan derivation table used. It counts the five production paths and
  excludes tests, fixtures, and generated copies.
- **Production plus verification** is the basis `spec.md`'s current
  Reviewability Budget bullet states ("plus Layer 4 unit tests and fixtures").

**Production-only is the binding declaration here**, because the constitution's
400 and 800 thresholds are the ones the estimator scores and the ones slice 1
recorded against. The verification figure is reported below it so the spec's
stated basis is corrected rather than dropped.

### Derivation A — anchored to shipped analogues

Every anchor below is a measured line count from the file the new code joins.

| Item | Low | High | Anchor |
|---|---:|---:|---|
| `read_only.py` — verdict surface | 170 | 230 | Two shipped clusters cover its two halves. The corroboration cluster (`read_only.py:1300-1466`) is **167 lines** for a closed-vocabulary classification over one supplied observation with a five-key record builder and three observation validators. The heading-anchored log reader (`sweep_table_cells`, `sweep_is_table_rule`, `sweep_logged_comment_ids`, `:1774-1815`) is **42 lines** for a single-column read. The verdict surface is that classification plus that read, with a three-cell dual-anchored extraction and a per-row reason list where the shipped reader has one key. |
| `read_only.py` — removal-diff surface | 30 | 50 | A pure set difference over two supplied lists with input validation and an envelope. Nearest analogues: `sweep_export_anchors` (22 lines), `observed_identity` (8 lines), plus the validation prologue shape `sweep_check_target` uses. |
| `read_only.py` — refresh-corroboration surface | 35 | 55 | Wiring, not logic: read the workflow file, blank HTML comment spans, call `workflow_draft_pr_row` and `corroborate_draft_pr` verbatim, wrap the record. The equivalent call inside `resolve_autopilot_stage` (`:1513-1518`) is 6 lines; the rest is the validation prologue and envelope every surface carries. |
| `read_only.py` — named-surface router and module constants | 30 | 45 | `sweep_pr_feedback`'s router is **25 lines** (`:1881-1905`). Constants: the heading name, the column names, the closed four-verdict tuple, and the request keys, in the `SWEEP_*` style. |
| `read_only.py` — registration touch points | 6 | 10 | `path_keys_by_helper` entry (1 line, near `:260`), argument-derivation branch (the `sweep-pr-feedback` branch at `:356-359` is 4 lines), dispatch-table entry (1 line, near `:5419`). |
| `registry.py` | 8 | 10 | One `HelperEntry`, matching the `sweep-pr-feedback` shape at `:189-196` (**8 lines**). |
| `phase-execution.md` | 150 | 230 | The nearest shipped analogue for a sequence carrying commits, a push, and create-or-refresh is the plan-stage emission terminal step (`:788-1055`, **267 lines**). Slice 2's sequence is comparable in shape but reuses that machinery by reference rather than restating it, and adds the freshness step and the report extension. |
| `phase-execution-codex.md` | 125 | 190 | Measured mirror ratio: slice 1 added 704 Claude lines and 585 Codex lines to these two files, **83%**. The whole-file ratio is 98,880 against 124,355 bytes, **80%**. |
| `speckit-pro/skills/speckit-autopilot/SKILL.md` | 2 | 5 | One scoping clause on the sentence at `:372`. Body is 6846 of 8000 words, ample headroom. |
| **Total** | **556** | **825** | Midpoint **≈ 690** |

### Derivation B — slice 1's realized density, as a cross-check

Derivation A is the same *kind* of estimate slice 1's plan made, and slice 1's
plan ran low. Recorded here so the risk is visible rather than discovered:

| File | Slice 1 plan-time estimate | Slice 1 actual | Factor |
|---|---:|---:|---:|
| `read_only.py` | 245–313 | 953 | 3.0–3.9× |
| `phase-execution.md` | 110–170 | 704 | 4.1–6.4× |
| `phase-execution-codex.md` | 90–150 | 585 | 3.9–6.5× |

Applying slice 1's **realized** density rather than its estimating style:
`phase-execution.md` gained 704 lines across roughly twelve new subsections,
about 59 lines each. Slice 2 adds five subsections (freshness evaluation;
regeneration, commit, and push; the refresh call site; the record commit; the
report extension) plus four small edits, which at that density is **250–380**,
with the Codex mirror at 83% giving **210–315**. `read_only.py` at the same
correction sits at **271–390**.

Derivation B totals **741–1100, midpoint ≈ 920**.

**Why A is the binding figure and B is not.** Slice 1 authored the sweep from
nothing: the trust filter, the classification vocabulary, consensus routing,
amendment commits, replies, reply reconciliation, the redaction call points, and
the byproduct directory were all new prose with no shipped precedent to point
at. Slice 2's five subsections are dominated by "invoke the machinery already
described in §Draft-PR emission at this new point, under these rules", which is
citation rather than restatement. The correction factor that fits new prose does
not fit reuse prose. Derivation A is declared; **derivation B is recorded as the
risk band, and if implementation lands above 800 the crossing is size-only and
takes the acceptance path in Complexity Tracking below.**

### The verification figure, for the spec's stated basis

Test and fixture lines, anchored on the two shipped analogues:
`tests/speckit-pro/unit/test-autopilot-stage-resolution.py` is **1765 lines**
covering `resolve-autopilot-stage` including its six-status matrix;
`test-feedback-sweep-parse.py` is **3190 lines** plus 26,948 fixture lines, an
outlier driven by the redaction corpus that slice 2 has no equivalent of.

| Item | Low | High |
|---|---:|---:|
| `test-artifact-freshness.py` | 600 | 1100 |
| `fixtures/artifact-freshness/*.json` | 150 | 350 |
| Registration-inventory edits (`test-speckit-pro-read-only-helpers.py`, `fixture-manifest.json`, `requests/*.json`, `suite-manifest.json`) | 45 | 70 |
| **Verification total** | **795** | **1520** |

**Production plus verification: 1350 to 2345, midpoint ≈ 1850.**

### Corroborate or correct: this corrects the spec

`spec.md` §Reviewability Budget currently projects **~450 reviewable LOC**
including tests and fixtures, 5 production files, ~10 total files, and
"within budget". Three of those five figures are wrong and this plan corrects
them:

1. **Reviewable LOC.** ~450 on a with-tests basis is low by roughly a factor of
   four against derivation A plus the verification table. Corrected to
   **556–825 production-only, midpoint ~690** (the binding figure), and
   **1350–2345 with verification**. The spec anchored on nothing measurable;
   this plan anchors every line on a counted shipped cluster.
2. **Budget result.** "Within budget" does not survive. 690 production-only
   crosses the 400 warn line. Corrected to **WARN on reviewable LOC**, no block,
   with derivation B recorded as the block-risk band.
3. **Projected total files.** ~10 is corrected to **12** (5 production, 7 test
   and fixture), still under the 15 warn.

Two figures stand: **5 production files** (the spec's count is right, though its
membership is not — the suite manifest is verification, and the Claude
`SKILL.md` takes its place), and **1 primary surface**.

### Budget result against the constitution thresholds

| Dimension | Value | Warn | Block | Result |
|---|---:|---:|---:|---|
| Reviewable LOC (production-only) | ~690 (556–825) | 400 | 800 | **WARN** |
| Production files | 5 | 6 | 8 | pass |
| Total authored files | 12 | 15 | 25 | pass |
| Primary surfaces | 1 | >1 | >1 | pass |

One warn, no block. The warn is size-only and is accepted rather than re-sliced,
for the reason argued below.

**Delta from the error-handling checklist remediation.** Four requirements were
added after this table was derived — FR-012b, FR-015a, FR-015b, FR-034a — plus
wording corrections to FR-019a, FR-036, FR-038, FR-039, and SC-001. None adds a
file: every landing site is already declared MODIFIED above. FR-012b is the only
one with an executable footprint, a conditional delete inside a step that
already deletes the removal set, at roughly 8-15 lines across the two reference
surfaces. The rest is scoping and reporting prose, roughly 25-45 lines across
`phase-execution.md` and its Codex mirror. That moves the production-only
midpoint from ~690 to roughly **720**, still a warn and still under the 800
block; the high end moves from 825 to about 885, and the split lever below is
unchanged and remains rejected on the same merit. Re-derive rather than trust
this note if the Analyze phase disputes the figure.

### The split lever, named because the high end reaches 800

Derivation A's high end is 825 and derivation B's midpoint is 920, so the lever
is named rather than left implicit.

**The one clean seam** is the description-refresh half: FR-014, FR-019a's
refresh leg, and FR-033 through FR-039. Deferring it into a stacked slice 3
would leave slice 2 as detect, regenerate, remove, commit, push, and report.
The saving is real and derivable line by line:

| Deferred item | Saving (low–high) |
|---|---:|
| `read_only.py` refresh-corroboration surface | 35–55 |
| `phase-execution.md` refresh call site and record commit | 60–100 |
| `phase-execution-codex.md` mirror of the same | 50–85 |
| `SKILL.md` scoping edit (FR-033b) removed entirely | 2–5 |
| Fixture and test coverage for the third surface | 120–250 |
| **Production-only saving** | **147–245** |

That takes the production-only midpoint from ~690 to roughly **495**, still a
warn, still above 400. **The lever does not reach the warn line, and it costs
half of SC-001.**

**It is rejected on merit.** SC-001 requires the reviewer at the re-review stop
to read pages *and a description* that describe the amended plan. A slice that
regenerates the pages and leaves the description stale ships a pull request
whose body describes the plan that was amended away, linking to pages that
describe the plan that replaced it. That is a worse reading experience than
slice 1's honest promise sentence, because the two halves now actively
contradict each other and nothing says which is current. Worse, FR-001's join
would read the artifacts directory as current the moment the regeneration commit
lands, so the deferred refresh has **no repair path**: slice 3 would arrive to
find every feature's join already satisfied and no trigger left to fire on.

A second lever exists and is worse: deferring FR-012a's removal diff. It saves
30–50 production lines and 40–80 test lines, and it costs FR-012 entirely,
leaving pages the manifest no longer selects on disk and linked from the
description. Not recommended.

**No split reaches 400 while shipping a freshness guarantee that holds.** The
drivers are the verdict surface (170–230) and the two phase-execution references
(275–420 together), and those are the feature: a slice without the verdict
cannot decide, and a slice without the references cannot run on either platform.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution version as shipped in `.specify/memory/constitution.md`.

| Principle | Assessment | Gate |
|---|---|---|
| I. Plugin Structure Compliance | PASS. No new plugin component type. The helper joins the existing `speckit_pro_runner` surface; every new test lives under `tests/speckit-pro/`, outside the install-facing plugin directory. | `run-all.py --layer 1` |
| II. Cross-Platform Runtime & Script Safety | PASS. Python 3.11+ standard library only. No Bash, no `jq`, no PowerShell. Structured JSON in and out, `shell=False`, argument arrays, deterministic UTF-8. The helper derives **no** CLI arguments at all (its whole request arrives on stdin), which is the strongest form of the rule. | `run-all.py --layer 4` |
| III. Semantic Versioning | PASS. No manual version edit; release-please owns the bump. | Layer 1 `validate-plugin` |
| IV. Test Coverage Before Merge | PASS. The new helper carries Layer 4 fixture-driven unit coverage per FR-031, a `suite-manifest.json` membership entry, and an entry in the read-only helper inventory. | `run-all.py` |
| V. Conventional Commits | PASS. Three commit shapes, all conventional: the artifacts commit is `docs(<scope>): ...` (FR-018), the record commit is the shipped `chore(<scope>): record the draft pull request` reused verbatim (FR-039), and slice 1's bookkeeping commit is untouched (FR-020). | CI `validate-pr-title` |
| VI. KISS, Simplicity & YAGNI | PASS with two judgments recorded below. | Plan and code review |

**Reviewability, per the preset's added obligations:**

- **Primary surface**: harness/adapter — the deterministic freshness helper and
  its Layer 4 coverage. **Secondary surfaces**: docs/process — the Claude and
  Codex phase-execution references and the one scoping clause in the Claude
  autopilot `SKILL.md`.
- **Within budget?** One warn, no block. Reviewable LOC ~690 against a 400 warn
  and an 800 block; 5 production files against a 6 warn; 12 authored files
  against a 15 warn; one primary surface. The warn is size-only, accepted, and
  its rejected split lever is derived above.
- **Split decision**: ART-008 was split into two vertical slices before
  implementation began. Slice 1 (the checkpoint) merged. **This is slice 2 and
  it stays one spec.** Splitting further would separate the freshness decision
  from the regeneration it exists to trigger, leaving a helper nothing calls,
  and the one seam that would technically fit is rejected above because it has
  no repair path.
- **PR review packet source**: `spec.md` §PR Review Packet Requirements, plus
  the traceability table in `quickstart.md`.

**KISS judgment 1: one registration, three named surfaces, not three
registrations.** The three surfaces share the workflow-file read boundary, the
request-validation prologue, and the envelope shape. FR-012a already pins the
removal diff to "a second named surface of the same freshness-helper
registration"; adding the refresh corroboration as a third keeps one allowed-
inputs entry, one dispatch entry, one `HelperEntry`, and one fixture-manifest
row instead of three of each. `sweep-pr-feedback` is the shipped precedent for
exactly this shape.

**KISS judgment 2: the verdict surface returns a verdict, and the orchestrator
acts.** The helper never selects pages, never deletes a file, never commits, and
never decides whether the run stops. That division is `sweep_pr_feedback`'s —
"Reports; never decides" — and keeping it is what leaves every decision in this
slice testable offline against a fixture.

**Post-design re-check.** Re-evaluated after Phase 1. The design artifacts
introduced no new violation. `data-model.md` and the contract keep the helper
read-only, offline, and standard-library-only; no new plugin component type
appeared; no Bash or `jq` dependency was introduced; the three commit shapes all
stayed conventional. The reviewability warn stands as recorded, unchanged by the
design.

## Architecture

### The one new registration: `check-artifact-freshness`

One `HelperEntry` in `speckit-pro/speckit_pro_runner/helpers/registry.py`,
shaped exactly like `sweep-pr-feedback` at `:189-196`:

```python
"check-artifact-freshness": HelperEntry(
    "check-artifact-freshness",
    "check-artifact-freshness",
    None,                      # no deleted .sh predecessor to record
    "python_authoritative",
    "python_only",
    authoritative_request("check-artifact-freshness"),
),
```

The name is capability-shaped and carries no spec id, per the repository's
naming rule. `script` is `None` and `comparison_mode` is `python_only` for the
same reason `sweep-pr-feedback` uses them: this is new behavior with no Bash
ancestor, and inventing a `source_script` would record a lie in a provenance
manifest. The helper id therefore joins `NO_BASH_ANCESTOR` in
`tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:86`.

### Three named surfaces, routed by `named_surface`

`sweep_pr_feedback` is the shipped router precedent (`read_only.py:1881-1905`):
an absent `named_surface` means the default surface, and a value outside the
closed set is a malformed request rather than a surface to discover.

| `named_surface` | Requirement | What it does |
|---|---|---|
| `verdict` (default) | FR-004, FR-004a, FR-005 to FR-009 | Reads the `Feedback Sweep Log` from the workflow file, joins each `amended` row against supplied ancestry records, returns one of four verdicts and echoes the supplied page set. |
| `removal_diff` | FR-012a | Pure set difference: pages present in the supplied pre-regeneration inventory and absent from the supplied re-selection id list, matched by filename stem. Reads no file. Deletes nothing. |
| `corroborate_refresh` | FR-033a | Reads the `Draft PR` row from the same workflow file and classifies it against a supplied live observation, through the shipped six-status logic reused verbatim. |

### Why the third surface lives here rather than on `resolve-autopilot-stage`

FR-033a leaves the registration to Plan and pins only that the vocabulary,
precedence, and observation-as-data contract are shared rather than re-derived.
Three options were weighed:

- **Reuse `resolve-autopilot-stage`.** Rejected. That operation's request
  requires `autopilot_args` and a parseable `## Workflow Overview` table, and it
  exits 2 with a one-line diagnostic when either is malformed
  (`read_only.py:1487-1505`). The refresh call site sits deep inside Phase 7,
  has no argv to parse, and must never turn a bad request into a run-stopping
  exit — FR-035 requires a failure there to end the refresh attempt only.
  Its envelope also carries `stage`, `source`, `basis`, `recorded_stage`,
  `planning_complete`, and `from_phase`, every one of which is noise at this
  call site and every one of which a reader would have to be told to ignore.
- **A fourth registration of its own.** Rejected under KISS. It would duplicate
  the allowed-inputs entry, the dispatch entry, the registry entry, the fixture
  manifest row, and the request fixture, to host roughly forty lines of wiring.
- **A third named surface here.** Chosen. The classification's one file input is
  the workflow file, which is already this registration's single permitted read
  path under FR-004, so the read boundary stays exactly one path for the whole
  registration.

**The reuse is literal.** The surface calls the shipped
`workflow_draft_pr_row(HTML_COMMENT_RE.sub("", text).splitlines())` and
`corroborate_draft_pr(row, observation)` — the same two functions
`resolve_autopilot_stage` calls at `:1513-1518` — and adds no branch of its own.
`corroborate_draft_pr` is already pure and standalone: it takes a row and an
observation and returns a five-key record, touching no global state. The
HTML-comment blanking is not optional and is carried across for the reason the
shipped call records: a commented-out row must never become evidence.

The observation shape is the entry gate's, unchanged: `gh pr list --head
<branch> --state all --json number,url,state,isDraft,headRefName`, passed as
data with `ok` set to the JSON literal `true` only when the query exited zero
**and** parsed. `observation_pull_requests` (`:1353-1409`) already enforces the
literal-`true` rule and rejects a malformed entry by rejecting the whole array,
so `skipped` rather than a false `pr_missing` is what an unreliable tool
produces.

### The Commit-cell extraction hazard, and the dual-anchored read

This is the one place where reusing the shipped table reader unchanged would be
wrong, and it is worth stating precisely.

The `Feedback Sweep Log` header is
`| # | Comment ID | Surface | Author | Class | Disposition | Commit | CRL # |`.
`sweep_table_cells` (`read_only.py:1594`) splits a row on the **bare** pipe with
no escape handling:

```python
[cell.strip() for cell in row.strip().strip("|").split("|")]
```

Slice 1's protocol requires the `Disposition` cell to escape a pipe as `\|`
(`workflow-file-protocol.md` §The Feedback Sweep Log). That escaping makes the
row render correctly in Markdown, but it does **not** make this splitter produce
eight cells: `a\|b` still splits into `a\` and `b`. A disposition carrying one
pipe therefore shifts every column to its right by one position, and a
left-anchored index for `Commit` would read the wrong cell — silently, and in
the direction that reads a stale page set as current.

**The rule: anchor columns before `Disposition` from the left, and columns after
it from the right.** Both offsets are derived from the header row rather than
hard-coded, so inserting a column stays safe:

| Column | Anchor | Why it is safe |
|---|---|---|
| `#` | header index from the left | sits at position 0, ahead of the free-prose cell |
| `Class` | header index from the left | sits ahead of `Disposition` |
| `Commit` | `-2` from the row's end | second-from-last in the header; a sha carries no pipe |
| `CRL #` | `-1` from the row's end | last in the header; a row number carries no pipe |

A data row with **fewer** cells than the header has is malformed: its `Commit`
is unreadable and the row is undeterminable under FR-006. A row with **more**
cells is the pipe-in-disposition case, which right-anchoring handles correctly
and which must not be reported as an error.

Everything else about the read is the shipped reader's, unchanged: heading
anchoring on `Feedback Sweep Log`, breaking `inside` on any line starting with
`#`, skipping the table rule row, and finding the header by column name.

### The freshness join, encoded as ancestry

FR-004a fixes the encoding and FR-008 says why. The `Commit` cell may hold an
abbreviated sha while the artifacts commit is supplied in full, so string
equality would report a matching commit as stale, and a timestamp comparison
would be wrong across a rebase. The orchestrator therefore supplies, per
`amended` row, one record keyed by that row's `Commit` cell text **verbatim**:

```json
{"cell": "a1b2c3d", "resolved": true, "is_ancestor_of_artifacts_commit": true}
```

The helper never resolves a sha, never orders two commits, and never runs
`git merge-base --is-ancestor` itself. A row whose cell text matches no supplied
record is undeterminable, exactly as an unresolvable one is: both mean the join
could not be made, and FR-006 forbids dropping either.

**Equality needs no separate rule.** A commit is its own ancestor, so a row
naming the artifacts commit itself already reads as not-newer under this
encoding. FR-008's requirement is satisfied by construction rather than by a
branch that could be written wrong.

**Two encoding facts FR-007b pins, because FR-007a's reading turns on them.**
A row is *joinable* only when its cell matched a supplied record **and** that
record resolved; a matched-but-unresolved row is not joinable, because FR-006
already makes it unable to prove freshness either way and the other reading
would let it prove staleness instead. And when `last_artifacts_commit` is null,
every resolved row's `is_ancestor_of_artifacts_commit` is supplied as `false`:
there is no commit for it to be an ancestor of, so without a pinned value the
one case FR-007a exists to govern would leave the Layer 4 fixtures nothing to
assert. With it pinned, the ordinary `stale` test decides that case directly and
the null-commit disjunct in the verdict table restates the rule rather than
adding a second branch to implement.

### Verdict precedence, and why `undeterminable` acts on nothing

Four verdicts, evaluated in this order (FR-005):

1. **`no_pages`** — the artifacts directory is absent or empty, regardless of
   the log (FR-007). A run blocked in strict mode never reached emission, so
   there are no pages to judge and no pull request to attach a regeneration to.
2. **`stale`** — any `amended` row resolved to a commit that is **not** an
   ancestor of the last artifacts commit (FR-008, FR-009). One such row decides
   the verdict alone; the rows need no ordering against one another.
3. **`undeterminable`** — any `amended` row missing, empty, unresolvable, or
   matching no supplied record (FR-004a, FR-006). The verdict names each such
   row's `#` and its reason.
4. **`current`** — none of the above applies to any row.

A directory holding pages that no commit has ever touched reads **`stale`** when
a joinable `amended` row exists, not `no_pages` (FR-007a). Those are real pages
describing the pre-amendment plan, written by a run that died before its commit,
and one regeneration converges them.

`undeterminable` **reports loudly and acts never** (FR-005a). It triggers no
regeneration, no refresh, and no commit, and it moves the stop-or-proceed
decision in neither direction. The reason is convergence: this slice writes no
`Feedback Sweep Log` row and FR-003 forbids a second store, so nothing in scope
can ever clear the condition that produced the verdict. An action keyed to it
would repeat on every later clean sweep without end — the same non-convergence
slice 1's self-reply exclusion exists to prevent. Because `stale` is evaluated
first, a row that actually proves staleness has already regenerated through the
ordinary path, so no genuinely stale page stands behind only a report line.

**An unusable observation returns `undeterminable`, not an input error.** The
observation must carry `ok` as the literal `true` to be read at all, following
`observation_pull_requests`' rule. Any other value is an unusable observation,
and FR-023 forbids a failed gather from blocking the run, so the surface answers
with the verdict that acts on nothing rather than with exit 2.

### The regeneration sequence, and its three commit shapes

The sequence runs inside Phase 7's sweep, after amending and before the
stop-or-proceed decision (FR-015), and it is evaluated on **every** leg the
sweep reaches, including the leg that amends nothing and the leg that handles no
comment at all (FR-016).

```text
0. Slice 1's reply point: every reply this run owes is already posted (FR-015a).
1. Evaluate freshness (verdict surface).
2. On `stale`: re-dispatch speckit-pro:artifact-author against the amended record.
3. Compute the removal set (removal_diff surface) and delete those files.
3b. Delete the superseded file behind each per-page gap (FR-012b); skip this
    entirely on a whole-set gap.
4. Verify the written pages on disk (ART-007's two positive tests).
5. Commit specs/<feature>/artifacts/ alone, `docs:` type — only if step 3, 3b,
   or the regeneration changed something under it.
6. Push. A failed push ends the sequence here.
7. Take the refresh call site's own live observation; classify it.
8. Refresh the description through ART-007 create-or-refresh.
9. When the `Draft PR` cell actually changed, take the shipped record commit.
```

**Step 0 is a placement, not a new step.** FR-015a fixes the whole sequence
after slice 1's reply point, which the shipped rule puts "at the end of the
run, after every bookkeeping commit this run takes has landed"
(`phase-execution.md:1812-1814`). Neither commit this sequence takes is a
bookkeeping commit (FR-020), so the shipped sentence places neither, and the
order had to be chosen rather than inherited. Running after the reply point is
the choice that leaves slice 1's reply behavior untouched, which `spec.md`
§Assumptions already claims: every reply is posted before step 6, the first
point at which this slice can stop an amended run.

**Step 3b is why the gap shapes diverge.** A per-page gap beside a generated
page leaves a superseded file the run would otherwise commit and the join would
then read as current forever, so FR-012b deletes it, on the same ground the
shipped verification gives for deleting a page that fails its two tests
(`phase-execution.md:936-942`). A whole-set gap is excluded: it generated
nothing, so skipping the deletion is what leaves the directory unmoved, the
commit untaken, and the next leg free to retry.

**Three commit shapes, kept apart, and none may absorb another:**

| Commit | Stages | Type | Requirement |
|---|---|---|---|
| Regeneration | `specs/<feature>/artifacts/` and nothing else | `docs` | FR-018, FR-019 |
| Record | the workflow file path alone | `chore` | FR-039, reusing the plan-stage terminal step's own commit verbatim |
| Slice-1 bookkeeping | the workflow file path alone | `chore` | FR-020, untouched |

The regeneration commit stages the artifacts directory **alone** because that is
what makes FR-001's join exact: any other staged path would move the directory's
last-touched commit for reasons unrelated to page content. It is taken only when
regeneration produced a change under that directory — an empty commit records
nothing and cannot move the join. It is **not** the bookkeeping commit slice 1
declines to write on the no-comment leg, and writing it there does not
contradict slice 1's rule, which governs the bookkeeping commit only (FR-020).

**FR-018a extends both halves of that guarantee, because neither held on its
own.** The first half is exclusivity in the other direction: from the sweep
onward the regeneration commit must be the only commit that stages a path under
the artifacts directory, not merely a commit that stages nothing else. The rule
does not reach backward to the plan-stage boundary commit, which legitimately
carries the first generation through its own `specs/` path set
(`phase-execution.md:788-805`, "plan stage only"). Phase 7 ends in
`git add -A && git commit` (`phase-execution.md:2219`), which runs on the
proceed leg after the sweep, so anything the sweep left uncommitted under the
directory rides into a commit touching it and moves the join. The second half
is that "unmoved" has to bind the working tree, not the commit. The reused
machinery writes each page directly into `specs/<feature>/artifacts/`
(`phase-execution.md:924`) and deletes every written page that fails its two
tests (`phase-execution.md:937-938`), and FR-011 makes those writes whole-file,
so a pre-existing page is overwritten and then deleted **before** the commit
decision exists. On either zero-generated path the directory can therefore end
changed, or empty; an emptied directory reads `no_pages` on the next join,
which outranks `stale`, and the retry FR-038 promises never fires. FR-018a's
obligation is to leave the directory as the pre-regeneration inventory FR-004
observed and to report any restoration performed. The mechanism is open and is
not free: on the FR-007a history no commit has ever touched the directory, so
git holds no copy to restore from and a `git`-only mechanism does not cover the
case.

**FR-039's record commit is reused, never redefined.** When the refresh actually
changes the `Draft PR` cell, that write rides the same separate,
workflow-file-path-alone `chore:` commit the plan-stage terminal sequence
already takes (`phase-execution.md:823-831`). It is taken only when the cell
actually changed; a refresh leaving the cell as found stages nothing, which is
the same no-op the machinery already applies when a re-run finds nothing left to
stage. A failure of this commit or its push is reported through the refresh
outcome and never blocks the run, but the report **must not** claim the row
repairs itself. The machinery's repair rule recovers an unwritten row only on a
later refresh that reaches this step, and FR-036 establishes that no later sweep
reaches it once the regeneration commit has landed, so inside this slice that
path is unreachable. The pull request itself is correct on the remote and only
the record is unwritten, so FR-039 names the resume path the way FR-036 names
its own: repair the row by hand, or leave it to a later run that reaches the
plan-stage create-or-refresh step, which this slice never schedules.

### FR-019a: the push is inside the step, and the leg decides the stop

The dedicated artifacts commit is not complete until it is on the remote. A
failed push **ends the emission sequence at that point**: the refresh must not
run against pages the remote does not show, which is the same sequencing
ART-007 already applies between its own push and its create-or-refresh step
(`phase-execution.md:816-820`). Because the refresh never ran, the shortfall
reaches the run report alone, naming the unpushed commit's sha, exactly as the
reused machinery's unreached-sink rule already treats a failed branch push.

**The leg decides what happens next, and the two legs differ:**

- **On a sweep that amended** (FR-015), a failed push **stops the run
  immediately**. SC-001 requires the pages the re-review stop's pull request
  shows to already be current, and they are not.
- **On a leg that amended nothing** (FR-017), a failed push **does not** convert
  the proceed into a stop. The local commit stands and rides up with the
  branch's next push.

**On both legs the condition is unrecoverable inside this slice, and the report
must say so.** The commit is local and complete, so the FR-001 join reads the
directory as current on the next run: no later sweep regenerates, and none
attempts the refresh this failure skipped. That is the same shape FR-036 names
for a refresh that ran and failed, so FR-019a now carries the same two
obligations — the non-repair statement and a manual resume path, here naming
both steps the operator owes: push the branch, then refresh the description
directly.

**Two shipped closed enumerations stop being exact here, and FR-015b scopes
both** by the added-sentence technique FR-033b already uses, never by rewriting
shipped text:

| Surface | Line | Enumeration | Why it needs scoping |
|---|---:|---|---|
| `phase-execution.md` | 1821-1824 | the stops that abort before the reply point and post no reply, "a failed push" its sixth and last member | FR-015a puts the artifacts push **after** the reply point, so this push is not one of them |

**The first edit needs two clauses, not one.** That sentence is an exhaustive
dichotomy — three named stops after the reply point, "every other stop" before
it — so merely saying FR-019a's push is not the failed push in the member list
leaves it caught by "every other stop". The added sentence has to place it
positively, on the side where every owed reply is already posted. Both clauses
are statements about where a new stop falls; neither touches what either list
already contains, which is what keeps the edit inside FR-015b's own rule.
| `phase-execution-codex.md` | 1468-1471 | the same enumeration | FR-029 parity |
| `phase-execution.md` | 1307-1314 | the conditions that end a run in this sequence, "a failed push" its seventh member | FR-017 makes the artifacts push non-run-ending on the leg that amended nothing, while the shipped list is unconditional |
| `phase-execution-codex.md` | 1034-1041 | the same enumeration | FR-029 parity |

Neither edit adds or removes a member; each adds one sentence saying which push
the existing member means. Both files already stand as MODIFIED in the file
operations block, so this adds no file to the budget.

### The refresh call site takes its own observation

FR-033 requires a live read at the moment of the refresh rather than a reuse of
the entry gate's. A pull request can be closed or replaced while the sweep runs,
and the later read is the current evidence. This is not a new kind of
observation: ART-007's create-or-refresh terminal step already takes a second
live read distinct from Step 0.6c's, on exactly this documented principle
(`phase-execution.md:1211-1216`). FR-033 extends the same shipped principle to a
third read.

Each status takes the behavior the ART-007 contract already assigns it at its
terminal step (FR-034), which is why the classification must be the same code
rather than the same words: `match` refreshes; `no_record` falls through to the
live by-branch existence test; `skipped` never creates and reports through the
could-not-be-opened shape naming which of the four causes occurred; `pr_closed`,
`pr_missing`, and `identity_mismatch` each end the refresh attempt, create
nothing, and leave the `Draft PR` row exactly as found. **No status opens a
second pull request.**

**Two of the six cannot classify here at all, and FR-034a says so** rather than
leaving the shipped table's create-capable branch importable into Phase 7:

- **`no_record` is unreachable.** It means an absent `Draft PR` row, but FR-016
  reaches the sweep only on an entry-gate `match`, which requires the row, and
  FR-022 forbids the sweep writing it. Nothing between the gate and the refresh
  can clear it. This matters because the shipped row's behavior is "fall through
  to the live by-branch existence test above, **then create or refresh**"
  (`phase-execution.md:1181`), and creation is not something this slice does on
  any path.
- **`skipped` has one live branch, not two.** The shipped row carries a
  conditional — refresh the recorded pull request when the tool can be reached,
  report through the could-not-be-opened path when it cannot
  (`phase-execution.md:1183-1187`). At this call site the classifier's input
  *is* the observation FR-033a takes at that moment, so a `skipped`
  classification is itself the evidence the tool could not be reached. The
  reachable branch is dead by construction, which is why FR-034's single stated
  behavior is the whole of the contract here rather than a narrowing of it.

Stating this is what keeps FR-034's "takes the behavior the contract already
assigns it" from reading as a contradiction against a table that visibly
assigns `skipped` two.

**Where slice 2 diverges from ART-007** (FR-035): ART-007's terminal step sits
at a stage boundary the run stops at regardless, while the sweep may proceed
into task work. So a discrepancy or an unreachable tool here ends the refresh
attempt **only** — it does not change the stop-or-proceed decision, does not
unwind a regeneration commit that already landed, and is never reported as a
page failure.

**FR-036's non-repair statement is mandatory in the report.** Once the
regeneration commit has landed, FR-001's join reads the artifacts directory as
current, so no later sweep regenerates or re-attempts the refresh. The report
must say that in as many words and name the operator's manual resume path.

**The resume path is per-status, not one generic line.** The shipped
corroboration gate already states the reason — "each stopping status names its
own resume path, because the four have different fixes and one shared path would
send an operator to the wrong repair" (`phase-execution.md:1337-1338`, mirror
`phase-execution-codex.md:1060-1061`) — and the terminal-step table already
practises it, naming each status's path in its own row prose rather than in a
summary line (`phase-execution.md:1181-1188`). Slice 1 is where that rule was
made explicit, in its own FR-019 and FR-019b
(`specs/art-008-feedback-sweep/spec.md:2587-2601,2622-2632`), the second of
which turns on precisely the status slice 2 also has to keep separate:
collapsing `skipped` into the discrepancy wording "costs the operator the
ability to tell a broken tool from a real discrepancy, and those have different
fixes." FR-036 reuses all of that rather than inventing a rule: "refresh the description directly" is simply not a repair for
a pull request that is closed or gone. FR-036 therefore
binds four: `skipped` names fixing the tool; `pr_closed` names reopening the
pull request; `pr_missing` names correcting or clearing the `Draft PR` row; and
a refresh that failed against a reachable pull request names refreshing the
description directly, outside the automated sequence. When the failure traces to
disagreeing identities, both are named.

### Reporting: one report, one extension, two removals

The page outcomes, the regeneration commit's sha, and the refresh outcome land
in the **what-already-landed** part of the run report every sweep leg already
builds, extending that part's closed enumeration once in the shared report-shape
section (`phase-execution.md:1279-1282`, Codex mirror `:1013-1015`) rather than
in the amended-leg bullet — because FR-016 runs the evaluation on every leg, and
a change made in the amended-leg bullet would miss the recovery path that is the
whole of User Story 2. A failure's manual resume path (FR-036, FR-005a) belongs
in the **resume-path** part.

Every shortfall regeneration produces still reaches ART-007's three sinks
(FR-021), with one substitution named explicitly: at this Phase 7 call site the
third sink is the run report, because the plan-stage stop report the shipped
sink table names does not exist here.

**The two gap shapes are reported apart, because they differ in repairability
rather than in severity** (FR-038). What decides whether a later leg retries is
whether the artifacts commit was taken, and FR-018 ties that to whether anything
under the directory changed:

| Shortfall | Directory moved? | Commit | Next leg |
|---|---|---|---|
| per-page gap beside a generated page | yes | taken | does not retry; the gap is the operator's |
| whole-set gap (FR-037) | no, and FR-012b deletes nothing | not taken | regenerates the set again |
| deselection removal landing alone | yes | taken | does not retry; the report names the removal as the reason |

A report that called both of the first two rows "gap" and stopped there would
leave an operator unable to tell work that will be retried from work that will
not, which is the distinction SC-002 asks them to make in under 30 seconds.

On a sweep that amended nothing and found the pages already current, the
freshness contribution collapses to **one line** naming the commit the pages are
current as of (FR-026). The report's other mandatory parts are unchanged.

**Both slice-1 promise passages come out, on both surfaces** (FR-027), at four
line-cited sites:

| Surface | Line | Passage |
|---|---:|---|
| `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` | 1857-1858 | the stop-report clause "states that the draft artifact pages regenerate once slice 2 lands" |
| same file | 1874-1876 | the meta-paragraph "The regeneration sentence is an interface slice 2 replaces…" |
| `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md` | 1495-1496 | the same clause |
| same file | 1506-1509 | the same meta-paragraph |

### FR-033b's two scoping edits

The existing sentence "Step 0.6c classifies the recorded `Draft PR` row and
reports one of them, and the sweep reads that report rather than taking an
observation of its own" sits at `phase-execution.md:1323-1326` and
`phase-execution-codex.md:1046-1049`. **Both get an added sentence** scoping it
to the entry gate's sweep-or-not decision alone — the one decision Step 0.6c's
pre-phase observation was taken for — so it is not read as forbidding the
refresh call site deeper inside Phase 7, which runs only after the gate has
passed and the sweep has already amended.

The Claude autopilot `SKILL.md:372` phrase "one read-only observation per run"
gets the same scoping, to Step 0.6c's own step rather than every corroboration
read a run may take. That phrase occurs exactly once in the tree.

### Codex parity: what FR-029 actually constrains

The structural parity validator compares file-level structure only, so no new
Codex file is required (`spec.md` §Clarifications). Two real constraints bind
the mirror prose:

1. **The Claude-only-vocabulary regex** runs over the **concatenated** Codex
   runtime documents — the skill body plus `phase-execution-codex.md`,
   `post-implementation-codex.md`, and `error-recovery-codex.md`
   (`tests/speckit-pro/layer1-structural/validate-codex-skills.py:244-252`,
   `:368-372`). It rejects `TaskCreate`, `TaskUpdate`, `Agent(`, `Bash(`,
   `Opus-class`, `Opus 4.6`, `/model opus`, `/effort max`, `/speckit.` or
   `/speckit:`, `run /<command>`, and `general-purpose agent`. The regeneration
   step is a subagent dispatch, so the Claude prose will carry an `Agent(` block
   and **the Codex mirror must describe the same dispatch in Codex-native terms
   without that literal**.
2. **Three pinned strings in the phase-execution mirror** must survive:
   `estimate-reviewable-loc`, `over_budget`, and `not_estimated`
   (`validate-codex-skills.py:386-395`). None sits in the region this slice
   edits, but the assertions are file-wide, so an edit that removed a
   surrounding block would trip them.

## Project Structure

### Documentation (this feature)

```text
specs/art-008-feedback-sweep-slice-2/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── check-artifact-freshness.md
├── checklists/
├── SPEC-MOC.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
speckit-pro/
├── speckit_pro_runner/
│   └── helpers/
│       ├── read_only.py          # + check_artifact_freshness(): router, verdict,
│       │                         #   removal_diff, corroborate_refresh, constants,
│       │                         #   3 registration touch points
│       └── registry.py           # + one HelperEntry
├── skills/speckit-autopilot/
│   ├── SKILL.md                  # + FR-033b scoping clause at the Step 0.6c bullet
│   └── references/
│       └── phase-execution.md    # + freshness evaluation, regeneration sequence,
│                                 #   refresh call site, record commit, report
│                                 #   extension; - 2 promise passages
└── codex-skills/speckit-autopilot/references/
    └── phase-execution-codex.md  # mirror of the same, Codex-native dispatch prose

tests/speckit-pro/
├── suite-manifest.json                       # + one membership entry
└── unit/
    ├── test-speckit-pro-read-only-helpers.py # EXPECTED_HELPERS, NO_BASH_ANCESTOR, HELPER_CASES
    ├── test-artifact-freshness.py            # NEW: Layer 4 fixture-driven coverage
    └── fixtures/
        ├── artifact-freshness/               # NEW: cases + expected envelopes
        └── read-only-helpers/
            ├── fixture-manifest.json         # order-sensitive; append to match EXPECTED_HELPERS
            └── requests/check-artifact-freshness.json
```

**Structure Decision**: No new directory under plugin source. The helper joins
`read_only.py` beside `sweep_pr_feedback`, which is the operation it is modeled
on: both take an orchestrator-supplied observation, read one workflow file,
classify offline, and report without deciding. One new fixture directory,
`tests/speckit-pro/unit/fixtures/artifact-freshness/`, named for the durable
behavior rather than for the spec id.

**Two ordering hazards in the test surface, named so they are not discovered by
failing:** `tests/speckit-pro/unit/fixtures/read-only-helpers/fixture-manifest.json`
is compared for **exact list equality** against `EXPECTED_HELPERS`
(`test-speckit-pro-read-only-helpers.py:396`), so the new entry must be appended
in the same position in both. The same test asserts the bash-reference id list
equals `EXPECTED_HELPERS` minus `NO_BASH_ANCESTOR` (`:397`), so the new helper
must be added to `NO_BASH_ANCESTOR` at `:86` or that assertion fails.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violation. The single reviewability warn is not one: the
preset's thresholds warn above 400 reviewable LOC, 6 production files, and 15
authored files, and block above 800, 8, and 25. This slice crosses **one** warn
(reviewable LOC at ~690) and no block, on 5 production files and 12 authored
files, with one primary surface.

The warn is size-only. Its derivation, the two-basis counting rule, the
correction it makes to `spec.md`, the risk band from slice 1's realized density,
and the split lever that was derived and rejected are all in "Reviewability
Budget, derived by hand" above.

**If implementation lands above the 800 block**, which derivation B's midpoint
of ~920 makes plausible, the crossing is size-only and takes the recorded
acceptance path rather than a mid-implementation re-slice: the freshness
decision is not separable from the regeneration it exists to trigger, and the
one seam that would fit has no repair path. The precedent for continuing past a
recorded size-only block is `docs/ai/specs/.process/PRSG-013-workflow.md:570`,
which recorded `status=block, is_size_only=true, reviewable_loc=1800,
total_files=78` and continued with the crossing captured as marker-planning
input. Recorded, not hidden.
