# SpecKit Workflow: ART-005 — Gallery Completion — Knowledge, Reports & Editors

**Template Version**: 1.0.0
**Created**: 2026-08-17
**Purpose**: Execute ART-005 through the SpecKit workflow on the seven-slice stack rooted at `art-005-gallery-completion-knowledge-reports-editors`.

---

## How to Use This Template

1. Start every phase from the dedicated ART-005 worktree and verify the active
   branch matches the active slice in the stack contract.
2. Re-read the design concept before each phase. Its Q&A log is the source of
   truth for human-approved scoping decisions.
3. Run the phases through `$speckit-autopilot` with this workflow file. Scaffold
   does not run planning or implementation itself.
4. Keep one ART-005 spec and workflow, but deliver seven sequential stacked
   review slices in manifest order, one template per slice. The operator chose
   this topology after the combined plan-time reviewability gate blocked.
5. Update the status tables and evidence links as each phase completes.

---

## Design Concept

This workflow was enriched from the Grill Me interview run during
`$speckit-pro:speckit-scaffold-spec ART-005`. The full Q&A log, Goals,
Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/ART-005-design-concept.md
```

Re-read it before each phase if a prompt can be interpreted more than one way.
The Specify and Clarify prompts below carry the interview decisions, and the
design concept remains authoritative for decisions captured during scoping. A
remedial blind-spot pass surfaced five findings and set one aside; four map to
existing scaffold decisions, while the semantic read-only/export classification
for four artifacts is now an explicit Open Question.

> **Note:** Grill Me is human-in-the-loop only. It is not part of the autopilot
> loop. Later ambiguity is handled by `/speckit-clarify` and the consensus
> protocol, never by rerunning Grill Me autonomously.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | 3 stories, 24 current FRs, 8 scenarios, and 12 success criteria after checklist remediation |
| Clarify | `/speckit-clarify` | ✅ Complete | Three sessions resolved source/fidelity/fill, editor exports, UAT evidence, and block routing; no consensus needed |
| Plan | `/speckit-plan` | ✅ Complete | Seven authored-LOC ceilings are 535-790; full physical diffs carry an explicit generated/control-plane size-only risk |
| Checklist | `/speckit-checklist` | ✅ Complete | 120 items; 24 initial gaps remediated; G4 passes with 0 remaining gaps |
| Tasks | `/speckit-tasks` | ✅ Complete | 119 ordered tasks; G5 and phantom-completion checks pass |
| Analyze | `/speckit-analyze` | ✅ Complete | Six findings remediated; G6 passes with 0 CRITICAL/HIGH findings |
| Confidence Gate | G6.5 | ✅ Complete | Advisory PASS at 0.98 against the 0.90 threshold |
| Implement | `/speckit-implement` | 🔄 In Progress | Slices 1-5 complete in PRs #444, #446, #447, #448, and #452; Slice 6 feature-flags formal RED proven and T085 GREEN active |
| Post | Post-Implementation | ⏳ Pending | Canonical closeout plus tracked `file://` UAT results |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⏭️ Skipped | ⚠️ Blocked

G6.5 ran in advisory mode and passed at 0.98 against the 0.90 threshold.

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | All seven templates and three outcome groups are covered; no `[NEEDS CLARIFICATION]` marker remains unless deliberately routed to Clarify |
| G2 | After Clarify | Pinned-source policy, semantic read-only classification, fill slots, export schemas, UAT record, and reviewability uncertainty have an explicit disposition |
| G3 | After Plan | Constitution gates pass; the immutable upstream revision is recorded; declared file operations and a measured reviewability projection exist |
| G4 | After Checklist | Every `[Gap]` from the four selected domains is fixed or explicitly deferred to a named owner |
| G5 | After Tasks | Requirements map to ordered TDD tasks; all seven atomic slice boundaries and per-slice reviewability checkpoints are explicit |
| G6 | After Analyze | No CRITICAL issue remains; HIGH/WARNING findings are resolved or accepted with evidence |
| G6.5 | Before Implement | Composite confidence meets the autonomous implementation threshold |
| G7 | After Each Implementation Phase | Focused tests pass, no shared-contract drift appears, and the completed templates work over `file://` |

---

## Prerequisites

### Constitution Validation

Before starting any workflow phase, verify alignment with
`.specify/memory/constitution.md`:

| Principle | ART-005 requirement | Verification |
|-----------|---------------------|--------------|
| I. Plugin Structure Compliance | Gallery files remain inside the plugin; repository-only tests stay under `tests/speckit-pro/` | `python3 tests/speckit-pro/run-all.py --layer 1` |
| II. Cross-Platform Runtime & Script Safety | Add no repository Bash, `jq`, build step, or non-standard-library repository tooling | Layer 4 active-path and Bash-confinement gates |
| IV. Test Coverage Before Merge | Extend Layer 4 gallery/fill-region coverage and pass the Python-authoritative suite | `python3 tests/speckit-pro/run-all.py` |
| V. Conventional Commits | Commits and final PR title use `type(lowercase-scope): plain English description` | release-readiness/PR-title validation |
| VI. KISS, Simplicity & YAGNI | Keep seven standalone ports explicit; add no shared abstraction, storage layer, import workflow, or undeclared export kind | Plan and code review |

**Constitution Check:** ✅ Verified at G0 with `7400/7400` passing
(`L1 1448/1448`, `L4 5766/5766`, `L5 186/186`); re-check after Plan.

### Worktree and Bootstrap Record

- Required worktree: `.worktrees/art-005-gallery-completion-knowledge-reports-editors`
- Active branch: `art-005-gallery-completion-knowledge-reports-editors-slice-3`
- Stack root: `art-005-gallery-completion-knowledge-reports-editors`
- Base at scaffold: `origin/main` at `1cf86bddecbca620234657f6e59a48991eabbc88`
- Docs dependency bootstrap completed: `pnpm --dir docs-site install --frozen-lockfile`
- Repository test suite needs no bootstrap: run `python3 tests/speckit-pro/run-all.py`
- Generated merge driver verified: `merge.generated.driver=exit 0`

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | ART-005 |
| **Name** | Gallery Completion — Knowledge, Reports & Editors |
| **Branch** | `art-005-gallery-completion-knowledge-reports-editors-slice-2` |
| **Stage** | `implement` |
| **Dependencies** | ART-001; dependency is satisfied on `main` |
| **Enables** | Gallery completeness |
| **Priority** | P2 |
| **Roadmap** | `docs/ai/specs/html-artifacts-technical-roadmap.md` § ART-005 |
| **Reviewability** | Combined projection blocked at 2,856 LOC; operator selected seven independently measured slices |
| **Blind-spot pass** | Ran remedially: 5 findings surfaced, 1 set aside; one new Open Question |

### Success Criteria Summary

- [ ] All seven named template files exist as branded standalone HTML artifacts,
  and their own manifest rows change from `planned` to `shipped`.
- [ ] The four entries currently declared with `exports: []` are classified
  against their pinned upstream interaction and SPA-CONTRACT.md semantics. True
  readers remain export-free; any state-producing conflict is reconciled before
  implementation rather than silently preserving or changing the declaration.
- [ ] `triage-board`, `feature-flags`, and `prompt-tuner` each expose exactly one
  keyboard-operable `Copy as Markdown` control derived from live session state.
- [ ] Any additional template classified as state-producing during Clarify has
  its roadmap, manifest, UI, and acceptance contract reconciled before work
  begins; no export change is inferred from wording alone.
- [ ] Feature-flags and prompt-tuner serialize structured state as deterministic
  fenced JSON inside Markdown; no JSON export kind is added.
- [ ] Clipboard refusal or failure reveals and focuses the exact export text in
  a labeled selectable fallback field.
- [ ] Every new horizontal scroll region is keyboard reachable and named; all
  interaction status is semantic, focus is visible, and reduced motion is honored.
- [ ] Layer 1, Layer 4, the default suite, generated-artifact checks, and docs
  reference generation pass after payload regeneration.
- [ ] A tracked runbook and durable result record show all seven templates
  passing manual `file://` acceptance, including genuine clipboard and forced
  fallback paths for every confirmed state-producing artifact.

---

## Phase 1: Specify

**When to run:** At the start of planning. Focus on WHAT and WHY. Output:
`specs/art-005-gallery-completion-knowledge-reports-editors/spec.md`.

### Specify Prompt

```text
/speckit-specify

## Feature: ART-005 — Gallery Completion — Knowledge, Reports & Editors

Read these sources before writing the specification:
- docs/ai/specs/html-artifacts-technical-roadmap.md § ART-005
- docs/ai/specs/.process/ART-005-design-concept.md
- speckit-pro/artifact-gallery/SPA-CONTRACT.md
- speckit-pro/artifact-gallery/manifest.json entries for slide-deck,
  concept-explainer, status-report, incident-report, triage-board,
  feature-flags, and prompt-tuner

### Problem Statement
The gallery already catalogs seven knowledge, report, and editor templates as
planned, but their standalone artifacts do not exist and their rows remain
`planned`. The roadmap currently treats four as read-only and three as editors;
the pinned upstream interaction must verify that semantic classification before
implementation. ART-005 completes this catalog segment with branded, accessible
ports, atomic file/status delivery, and every contract-required export loop.

### Users and User Stories
1. A reader opens a deck or concept explainer over file:// and can understand
   its representative content; Clarify confirms whether the interaction is
   consumption-only before fixing the export requirement.
2. A reader opens a status or incident report over file:// and can inspect a
   complete, representative report; any state-producing behavior is reconciled
   with the export contract before implementation.
3. An operator edits a triage board, feature-flag configuration, or prompt,
   then copies deterministic Markdown derived from current session state and
   can recover the same text manually when clipboard access fails.

Make each story independently testable while keeping one ART-005 spec and
workflow across seven sequential stacked slices, one template per slice.

### Human-Validated Decisions — Do Not Re-litigate
- Q1: "One combined slice" was the initial answer; after the measured block,
  the operator superseded it with "Seven slices."
- Q2: "Fenced JSON in Markdown (Recommended)."
- Q3: "Pin one commit (Recommended)."
- Q4: "Session only (Recommended)."
- Q5: "Visible fallback field (Recommended)."
- Q6: "Functional fidelity (Recommended)."
- Q7: "Tracked runbook and results (Recommended)."
- Q8: "Enforce current baseline (Recommended)."

### Functional Boundaries
- Port exactly seven upstream files identified by the existing manifest, all
  from one immutable upstream commit resolved during planning.
- Preserve the core upstream content/interaction model, but apply Racecraft
  branding, canonical embedded blocks, the single-file contract, accessibility,
  and gallery fill-region conventions.
- The four entries currently declared with exports: [] are confirmed semantic
  readers from pinned upstream evidence and retain that declaration. The three
  known editors retain exports: ["markdown"] and use the exact label Copy as
  Markdown.
- Feature-flags and prompt-tuner put lossless structured state in fenced JSON
  inside Markdown. Triage-board exports human-readable Markdown by column.
- Editor content is memory-only and resets on reload; existing theme preference
  behavior is unaffected.
- Every export is generated from live state. Clipboard unavailable, rejected,
  or synchronously throwing must reveal and focus a labeled manual-copy field.
- New horizontal scroll regions are focusable and named; controls have visible
  focus and accessible names; status is announced as text; reduced motion is
  respected; color is never the sole carrier of meaning.
- Preserve a tracked plain-English file:// UAT runbook and a durable per-check
  result record covering all seven artifacts.

### Reviewability Budget
Record both estimates: roadmap 560 LOC and fresh estimator 555 LOC, each warn
with two slices suggested. Preserve the later combined measurement and its
2,856-LOC block. The operator resolved that block with seven slices. Require a
file-by-file projection for every slice and stop any individually blocked slice
for an operator decision; do not split a template or invent an exception.

### Out of Scope
- Workflow-stage routing.
- JSON export kinds, automatic downloads, import-back, persistent editor
  content, shareable URL state, or server storage.
- Pixel-perfect upstream styling or a ground-up redesign.
- Shared gallery foundation changes or repairs to already-shipped templates.
- Export controls on any template confirmed as a semantic reader, and any
  export-declaration change made without resolving the pinned-source conflict.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 24 current after checklist remediation |
| User Stories | 3 |
| Acceptance Criteria | 8 scenarios |
| Reviewability result | Initial 555/560 LOC warning; combined projection later blocked at 2,856 LOC; operator selected seven slices |

### Files Generated

- [x] `specs/art-005-gallery-completion-knowledge-reports-editors/spec.md`

### SpecKit Traceability Markers

| Marker | Purpose | ART-005 use |
|--------|---------|-------------|
| `[US1]`, `[US2]`, `[US3]` | User-story reference | Knowledge/deck, reports, interactive editors |
| `[FR-xxx]` | Functional requirement | Map every gallery, export, accessibility, and UAT obligation |
| `[NEEDS CLARIFICATION]` | Deliberate Clarify input | Only the six Open Questions from the design concept |
| `[P]` | Parallel-safe task | Different template files only; never shared manifest/test/generated surfaces |
| `[Gap]` | Missing coverage | Must be closed before implementation |

---

## Phase 2: Clarify

**When to run:** After Specify. Ask no more than five targeted questions per
session and write every accepted answer back into `spec.md`.

### Clarify Prompts

#### Session 1: Source, Fidelity, and Fill Regions

```text
/speckit-clarify

Focus on ART-005 source and content contracts. Read
docs/ai/specs/.process/ART-005-design-concept.md first.

Resolve only ambiguities that remain after inspecting the upstream repository:
- the one immutable upstream commit shared by all seven ports;
- exact source paths and a reproducible digest/identity record;
- whether slide-deck, concept-explainer, status-report, and incident-report are
  semantic readers or state-producing tools under SPA-CONTRACT.md; preserve
  exports: [] only for readers, and stop for contract reconciliation if any
  pinned source produces durable user-authored state;
- each template's preserved core mechanism and intentionally changed behavior;
- exact fill-region slot inventory, slot cardinality, and minimum representative
  sample content for all seven templates;
- whether any pinned upstream behavior conflicts with SPA-CONTRACT.md.

Do not reopen the functional-fidelity decision or propose a full redesign.
```

#### Session 2: Editor State and Export Contracts

```text
/speckit-clarify

Focus on deterministic live-state exports for triage-board, feature-flags, and
prompt-tuner. Preserve the chosen markdown-only, session-only design.

Resolve:
- a complete example Markdown export for each editor;
- stable field and column ordering;
- fenced-JSON schema/version markers for feature-flags and prompt-tuner;
- representation of empty, invalid, duplicate, and special-character values;
- one consistent clipboard success and visible fallback behavior under file://.

Do not add JSON export, download, persistence, import-back, or server behavior.
```

#### Session 3: Acceptance Evidence and Reviewability

```text
/speckit-clarify

Focus on durable acceptance evidence and the combined-slice risk.

Resolve:
- repository-conventional locations and formats for the tracked UAT runbook and
  result record;
- mandatory environment, commit, template, step, and verdict fields;
- checks for genuine clipboard success versus forced fallback;
- coverage for keyboard traversal, named scroll regions, visible focus,
  reduced motion, theme parity, offline behavior, and representative content;
- the plan-time reviewability response if the combined projection reaches block.

The operator selected one combined slice. A measured block is an explicit stop
for operator review, not permission to split automatically.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Source, fidelity, fill regions | 5 | Pinned commit and digests; four readers confirmed; preservation boundaries and seven fill inventories recorded; no consensus needed |
| 2 | Editor state and exports | 5 | Three complete Markdown contracts, stable ordering and edge rules, and one visible focused fallback behavior; no consensus needed |
| 3 | UAT evidence and reviewability | 5 | Active and archival evidence paths; mandatory run/row fields; genuine clipboard success plus three forced failures; seven-artifact matrix; explicit stop on block; no consensus needed |

After Plan triggered Session 3's stop, the operator selected seven sequential
stacked slices, one template each. That later decision supersedes the historical
one-combined-slice text inside the Session 3 prompt.

**G2 result:** ✅ Pass — zero `[NEEDS CLARIFICATION]` markers remain and all
three Clarify sessions have an explicit disposition.

---

## Phase 3: Plan

**When to run:** After specification and clarification are complete. Output:
`specs/art-005-gallery-completion-knowledge-reports-editors/plan.md` and its
supporting design artifacts.

### Plan Prompt

```text
/speckit-plan

Read spec.md, docs/ai/specs/.process/ART-005-design-concept.md, the ART-005
roadmap entry, SPA-CONTRACT.md, the seven existing manifest rows, the nearest
shipped templates, and the ART-003 post-merge hygiene report.

## Tech Stack
- Runtime: standalone HTML5, CSS, and vanilla browser JavaScript in one file per
  artifact; no build step, bundler, preprocessor, or post-processing.
- Styling: embed the exact canonical Racecraft brand-kit and theme-toggle blocks;
  do not edit the shared foundation files.
- State: in-memory per page session only; existing theme preference remains as-is.
- Data: existing JSON manifest plus deterministic Markdown serialization; fenced
  JSON is content inside Markdown, not a new export kind.
- Testing: Python 3.11+ standard-library Layer 4 tests, Layer 1 validation, full
  repository suite, generated-artifact consistency, and manual file:// UAT.
- Delivery: plugin payload regenerated through authoritative repository scripts.

## Required Research
- Resolve and record one immutable commit in anthropics/html-effectiveness that
  contains all seven manifest source files. Record repository, commit, retrieval
  date, file paths, and digests. The source bytes are absent from the working
  tree and git history, so retrieval must be explicit and reproducible. Keep
  retrieved upstream bytes outside the repo.
- Inspect each source and state exactly which content/interaction mechanism is
  preserved and what changes to meet Racecraft contracts.
- For slide-deck, concept-explainer, status-report, and incident-report, record
  whether the pinned interaction is consumption-only or lets the user produce
  durable state. Reconcile any state-producing result with the roadmap,
  manifest, UI, and acceptance contract before design completion.
- Inspect shipped templates for canonical block placement, fill markers,
  accessible export/fallback behavior, keyboard scroll regions, theme behavior,
  and representative sample-content patterns.
- Locate the current repository convention for UAT runbooks and durable result
  records; do not invent a new evidence hierarchy without need.

## Constraints and Chosen Answers
- Q1's initial "One combined slice" answer was superseded after its measured
  block. The operator selected seven sequential stacked review slices, one
  template per slice, while retaining one ART-005 spec and workflow. Slice 1
  uses the current branch; each later branch is cut from its predecessor after
  the predecessor PR is open. Plan the stack, but do not create branches or PRs.
- Q2 says "Fenced JSON in Markdown (Recommended)." Define exact deterministic
  Markdown contracts without changing manifest exports.
- Q3 says "Pin one commit (Recommended)." No floating upstream main.
- Q4 says "Session only (Recommended)." No content persistence or import.
- Q5 says "Visible fallback field (Recommended)." Match the shipped recovery
  pattern and derive the value from live state at invocation.
- Q6 says "Functional fidelity (Recommended)." Preserve mechanisms, not pixels.
- Q7 says "Tracked runbook and results (Recommended)." Plan both artifacts.
- Q8 says "Enforce current baseline (Recommended)." Prevent new keyboard-scroll,
  focus, status, color-only, and reduced-motion gaps.

## Required Architecture and File Operations
- Declare each of the seven NEW template paths individually and assign exactly
  one to each slice in this order: `slide-deck`, `concept-explainer`,
  `status-report`, `incident-report`, `triage-board`, `feature-flags`, and
  `prompt-tuner`.
- For each slice, declare its incremental `manifest.json` status flip and every
  incremental Layer 4 and fill-region test change individually. Each template,
  its own `planned` → `shipped` flip, its tests, generated outputs, and its UAT
  evidence form one atomic slice.
- Declare the chosen UAT runbook and result-record paths, including how shared
  records grow serially across the seven slices.
- Identify both Claude and Codex payload copies plus reference/proof files as
  generated operations, never hand-edited sources of truth.
- Keep all template implementations independent. Shared integration changes are
  serialized: manifest rows, fill-region literals, payload generation, docs test
  reference generation, and final suite execution.
- Do not modify brand-kit.css, theme-toggle.html, SPA-CONTRACT.md, existing
  shipped templates, export vocabulary, or workflow-stage routing.

## Reviewability Gate Before Design Completion
The setup estimator returned 555 LOC, warn, suggested two slices; the roadmap
declares 560, warn, suggested two. Preserve the measured combined result: seven
pinned sources total 4,042 lines and 120,618 bytes, and the conservative combined
projection of 2,856 reviewable LOC exceeds the 800 block. The operator resolved
that stop by selecting seven slices. Project each slice independently from its
pinned source and declared incremental operations, compare it with realized
ART-002/ART-003 port data, and record a verdict per slice. If any slice reaches
block, stop that slice for an operator decision. Do not split a template or
invent a typed exception.

## Verification Design
- Write or extend focused Layer 4 assertions before each implementation group.
- Cover manifest/file agreement, canonical blocks, fill inventories and minimums,
  semantic reader/producer export agreement, exact labels, live-state exports,
  fallback fields, keyboard/named scroll regions including the ART-020 failure
  pattern, semantic status, and prohibited constructs.
- Define manual file:// checks for every artifact and behavioral checks for every
  confirmed state-producing artifact, including the three known editors.
- Regenerate release artifacts with scripts/refresh-release-artifacts.py after
  source changes; regenerate docs test references after tests/speckit-pro changes.
- End with Layer 1, Layer 4, the full suite, generated-artifact consistency, and
  a tracked UAT result tied to the tested commit.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ✅ Complete | Seven-slice stack, component ceilings, exact authored/generated operations, and per-slice stop rules |
| `research.md` | ✅ Complete | Pinned upstream, semantic roles, exports, state, gallery grammar, UAT, and topology decisions |
| `data-model.md` | ✅ Complete | Gallery, source, fill, editor/export, UAT, and `ReviewSlice` entities |
| `contracts/` | ✅ Complete | Slice topology, gallery template, editor export, and UAT evidence contracts |
| `quickstart.md` | ✅ Complete | Per-slice validation, regeneration, and `file://` acceptance route |

### Prior Combined Plan Reviewability Stop

- Pinned-source measurement: 7 files, 4,042 lines, 120,618 bytes; every digest
  reverified against the official upstream bytes.
- Conservative realized-port projection: 2,856 reviewable LOC; ART-003-average
  projection: 4,356 reviewable LOC. Both exceed the 800-LOC block.
- Runner estimator diagnostic: recognized 10 NEW and 3 MODIFIED declarations,
  but returned `production: 0`, `projected: 0`, `pass` because the seven net-new
  production files do not yet exist. This advisory blind spot does not override
  the explicit measured checkpoint.
- At the stop, the runner G3 syntax diagnostic passed only because `plan.md`
  existed with zero unresolved markers; workflow G3 correctly remained blocked
  because design outputs were absent and the reviewability rule had stopped.
- Operator resolution (2026-08-17): seven sequential stacked slices, one
  template per slice, under the same ART-005 spec and workflow. Replan with an
  independent projection and verdict for every slice. No combined-slice
  exception was granted.

### Seven-Slice Plan Completion

| Slice | Artifact | Component ceiling | Authored paths | Maximum physical paths | Verdict |
|---:|---|---:|---:|---:|---|
| 1 | `slide-deck` | 670 LOC | 7 | 33 | Authored LOC warns/passes; full-diff file-count may size-block |
| 2 | `concept-explainer` | 535 LOC | 7 | 33 | Authored LOC warns/passes; full-diff file-count may size-block |
| 3 | `status-report` | 560 LOC | 7 | 33 | Authored LOC warns/passes; full-diff file-count may size-block |
| 4 | `incident-report` | 620 LOC | 7 | 33 | Authored LOC warns/passes; full-diff file-count may size-block |
| 5 | `triage-board` | 785 LOC | 7 | 33 | Authored LOC warns/passes with 15 LOC headroom; full-diff file-count may size-block |
| 6 | `feature-flags` | 780 LOC | 7 | 33 | Authored LOC warns/passes with 20 LOC headroom; full-diff file-count may size-block |
| 7 | `prompt-tuner` | 790 LOC | 7 | 33 | Authored LOC warns/passes with 10 LOC headroom; full-diff file-count may size-block |

- Every component ceiling is the sum of authored markup/content, CSS, behavior
  JavaScript, and incremental test LOC. Canonical copied blocks and generated
  mirrors are excluded from authored LOC. The 33-path maximum separately counts
  seven implementation-authored paths, up to 25 generated paths, and one
  possible `tasks.md` control-plane path.
- The parser-facing ledger reports 10 NEW and 3 MODIFIED paths. The advisory
  estimator still returns `production: 0`, `projected: 0`, `pass` because it
  does not classify these net-new HTML gallery files as production. The measured
  per-slice component ceilings control the reviewability decision.
- Implementation measures each slice after scaffolding, after focused tests,
  before generated refresh, and before PR open. Reaching 800 authored LOC or any
  non-size/correctness block stops that slice. A generated/control-plane-only
  total-file block is recorded as size-only in the slice packet and follows the
  operator-ratified branch stack; it is not a typed exception.
- Current G3: ✅ Pass. `plan.md`, `research.md`, `data-model.md`, four contracts,
  and `quickstart.md` exist; the constitution re-check passes; zero unresolved
  markers remain; the runner reports `plan.md exists with 0 unresolved markers`.

---

## Phase 4: Domain Checklists

**When to run:** After Plan. Run all four enriched domains because they map to
the highest-risk design branches.

### Recommended Domains

| Domain | Why it applies |
|--------|----------------|
| accessibility | Seven user-facing SPAs, three editors, keyboard scroll/focus, semantic status, color, theme, and reduced motion |
| ux | Functional-fidelity ports must remain understandable, interactive, and honest about read-only versus state-producing behavior |
| data-integrity | Three editor exports must represent complete live state deterministically, including fenced JSON and ordering |
| error-handling | Clipboard access can be absent, rejected, or throw under file:// and must always recover without losing content |

### Enriched Checklist Prompts

#### 1. accessibility

```text
/speckit-checklist accessibility

Focus on ART-005 requirements:
- keyboard traversal and visible focus for all controls;
- focusable, named horizontal scroll regions;
- semantic success/failure status and fallback focus movement;
- dark/light theme parity, contrast, color-independent meaning, and reduced motion;
- accessible structure for slide navigation, reports, board columns, flags, and
  prompt editing.
Pay special attention to preventing the keyboard-scroll defect documented by ART-020.
```

#### 2. ux

```text
/speckit-checklist ux

Focus on ART-005 requirements:
- functional fidelity for each pinned upstream source without pixel-copying;
- representative sample content and clear empty/boundary states;
- evidence-backed reader/producer classification rather than trusting the four
  current empty export arrays by declaration alone;
- session reset behavior and explicit Copy as Markdown feedback;
- consistent gallery branding, responsive layouts, and file:// usability.
Pay special attention to whether each editor makes the exported state predictable.
```

#### 3. data-integrity

```text
/speckit-checklist data-integrity

Focus on ART-005 requirements:
- export derives from current state at invocation time;
- stable ordering and complete field coverage;
- lossless typed feature-flag and prompt-tuner values inside fenced JSON;
- deterministic handling of empty, duplicate, multiline, Unicode, and special
  characters;
- manifest exports remain exactly ["markdown"] for editors and [] for readers.
Pay special attention to silent state omission or stale precomputed exports.
```

#### 4. error-handling

```text
/speckit-checklist error-handling

Focus on ART-005 requirements:
- clipboard API absent, permission rejected, promise rejected, and synchronous throw;
- selectable labeled fallback contains the exact attempted export and receives focus;
- repeated success/failure transitions do not leave stale status or text;
- file:// behavior is tested directly rather than inferred from http://;
- no automatic download, silent failure, or undeclared recovery mechanism.
Pay special attention to recovery that remains usable by keyboard and screen reader.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| accessibility | 32 | 0 | FR-014, SC-005-SC-007, accessibility contract detail, gallery/UAT contracts |
| ux | 28 | 0 | FR-021-FR-022, SC-009-SC-010, UX boundary/responsive contracts |
| data-integrity | 30 | 0 | FR-008-FR-011, FR-023-FR-024, SC-011-SC-012, editor/UAT contracts |
| error-handling | 30 | 0 | FR-011, SC-004, SC-007, clipboard attempt/UAT contracts |
| **Total** | **120** | **0** | All 24 initial gaps remediated; no consensus escalation required |

### Addressing Gaps

For each `[Gap]`: decide whether it is a genuine missing requirement, update
`spec.md` or `plan.md`, re-run the checklist, and name a follow-up owner for any
intentional deferral. No unresolved gap reaches Tasks.

**Gate G4:** ✅ PASS — runner `validate-gate` reported `0 [Gap] markers`.
The data-integrity executor's result channel and both error-handling executor
attempts hit model capacity; the documented Codex recovery path directly
validated the preserved/remediated artifacts with the same marker and diff gates.

---

## Phase 5: Tasks

**When to run:** After all checklist gaps are closed. Output:
`specs/art-005-gallery-completion-knowledge-reports-editors/tasks.md`.

### Tasks Prompt

```text
/speckit-tasks

Read spec.md, plan.md, research.md, contracts/, quickstart.md, and
docs/ai/specs/.process/ART-005-design-concept.md. The design concept is the
source of truth for the eight human-approved answers, the later seven-slice
operator resolution, and the six Open Questions including semantic
reader/producer classification.

## Task Structure
- Use strict RED → GREEN → REFACTOR ordering for every behavior.
- Give every task an exact repo-relative path and requirement/story reference.
- Different standalone template files may be [P] only after their failing tests
  and source contracts exist. Never mark shared manifest, shared test literals,
  generated artifacts, or final integration commands parallel.
- Organize work into seven sequential slice groups in the recorded order. Add a
  pre-implementation reviewability checkpoint for each slice using the Plan
  measurement. Stop an individually blocked slice; do not split its template.

## Implementation Phases
1. Shared baseline and contracts: record pinned upstream evidence and finalize
   fill, export, generated-artifact, and UAT contracts before Slice 1.
2. Slice 1 - `slide-deck`: RED tests, template, one status flip, incremental
   shared integration/regeneration, focused/full verification, and UAT evidence.
3. Slice 2 - `concept-explainer`: repeat the atomic slice pattern on its branch.
4. Slice 3 - `status-report`: repeat the atomic slice pattern on its branch.
5. Slice 4 - `incident-report`: repeat the atomic slice pattern on its branch.
6. Slice 5 - `triage-board`: include live Markdown, clipboard success, all
   forced fallback paths, keyboard checks, and edge tests.
7. Slice 6 - `feature-flags`: repeat the editor slice pattern with fenced JSON.
8. Slice 7 - `prompt-tuner`: repeat the editor slice pattern with fenced JSON,
   then complete stack-wide traceability and closeout evidence.

## Non-goal Guardrails
- No workflow routing, JSON export kind, download, persistent content, import,
  URL state, server storage, shared gallery abstraction, shared foundation edit,
  existing-template repair, or export-control change without a resolved semantic
  classification and reconciled contract.
- Preserve functional fidelity without carrying upstream visual defects.
- Do not hand-edit payloads, installed-cache proofs, generated reference pages,
  or generated spec-index zones.

## Required Verification Tasks
- Focused Layer 4 gallery and fill-region tests fail before implementation and
  pass afterward.
- Tests prove each template file lands atomically with its `planned` → `shipped`
  manifest update, semantic export agreement, and the ART-020 keyboard-scroll
  prevention rule.
- Layer 1, Layer 4, full suite, payload consistency, and generated docs reference
  checks pass on final bytes.
- Manual file:// UAT grows incrementally in each slice and covers its template;
  editor slices include genuine clipboard success plus unavailable, rejected,
  and synchronous-throw recovery. Each slice records its tested commit.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | 119 (T001-T119, contiguous) |
| **Phases** | 10: setup, foundational, 7 sequential slices, stack-wide closeout |
| **Parallel Opportunities** | T002 and T003 only; both are read-only baseline checks |
| **User Stories Covered** | US1-US3 across all seven operator-selected slices |

### Tasks Validation

- G5 runner validation passed with `119 tasks found`, `markers: 0`, and
  `task_count: 119`.
- The mandatory Verify Tasks check found 0 phantom completions: all 119 tasks
  are intentionally unchecked and no implementation-path change exists.
- The phase executor and one fresh retry made no progress. The orchestrator
  followed `error-recovery-codex.md`, ran the `speckit-tasks` workflow directly,
  and applied the same formatting, traceability, and gate checks.
- All 24 FRs and 12 SCs have task references; spec-index write/check and the
  workflow/state coverage guard pass.
- Tasks-mode `reviewability-gate` remains unavailable in the installed runner,
  so it was not invoked. The fallback evidence chain is the scaffold
  `status=pass` / `verdict=warn` result at 555 LOC, the advisory Plan estimator
  result (`status=pass`, projected 0 because HTML is not classified as
  production), and the operator-ratified seven-slice measurements of 535-790
  LOC. Each slice retains its explicit pre-refresh and final stop at 800 LOC.
- Task-checkbox changes are control-plane metadata. They are reported
  separately from the seven declared authored-path LOC ledgers and included in
  the complete physical Git-path ledger. With up to 25 generated paths, the
  33-path maximum is an explicit projected size-only risk rather than an
  unqualified reviewability pass.

---

## Atomicity Route

After Tasks/G5, run the read-only classifier against:

```text
runner helper atomicity-route specs/art-005-gallery-completion-knowledge-reports-editors
```

The classifier reports its current structural heuristic. It is advisory and
does not authorize a different topology or override the operator-selected
seven-slice navigation. Record its machine-readable decision here:

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | `one-navigable-PR` | Current classifier output; the explicit seven-slice stack remains the delivery topology |
| **Releasable** | `true` | No release-risk detector applied |
| **Signals** | `change-shape:modify-heavy` | Current decisive detector finding |
| **Warnings** | `[]` | No release-safety warnings |

The classifier reads the repeated shared-file modifications as modify-heavy;
it does not model the seven independently measured template seams ratified by
the operator. Analyze must preserve this tension as explicit evidence rather
than silently treating the advisory route as a topology change.

## Layer Plan

| Field | Value |
|-------|-------|
| **Status** | `skipped` |
| **Reason** | `atomicity-route` returned `one-navigable-PR`; the helper contract runs `plan-layers-feature-dir` only for an exact `split-PR` route |
| **Delivery topology** | Seven sequential stacked slices remain operator-ratified in `plan.md` and `contracts/slice-topology-contract.md` |

No layer-planner helper was invoked, and no implementation branch or PR was
created during the Plan stage.

---

## Phase 6: Analyze

**When to run:** Always after Tasks.

### Analyze Prompt

```text
/speckit-analyze

Analyze spec.md, plan.md, tasks.md, research.md, contracts/, quickstart.md, and
docs/ai/specs/.process/ART-005-design-concept.md as one system.

Focus on:
1. Constitution alignment and SPA-CONTRACT.md compliance.
2. Complete traceability for all seven templates, the resolved semantic
   reader/producer classifications, every required export, accessibility,
   generated artifacts, and durable UAT.
3. Drift from the design concept's Goals, Non-goals, Q1-Q8 answers, or Open
   Questions. The design concept wins for human-approved scoping decisions.
4. Whether the pinned source evidence, fill inventories, export examples, and
   declared file operations are concrete and mutually consistent.
5. Whether Tasks preserve RED → GREEN → REFACTOR and serialize all shared files.
6. Whether the prior combined block and operator-selected seven-slice topology
   are preserved, and every slice has an honest independent projection. Treat an
   unhandled per-slice block or topology drift as CRITICAL.
7. Whether generated surfaces are regenerated from source rather than hand-edited.
8. Whether the runbook and result record prove real file:// behavior, genuine
   clipboard success, and forced recovery.

Remediate every finding with evidence. Do not weaken requirements merely to make
artifacts agree.
```

### Analyze Severity Levels

| Severity | Meaning | Action Required |
|----------|---------|-----------------|
| `CRITICAL` | Blocks implementation or violates constitution/contract | Must fix before G6 |
| `HIGH` | Significant coverage, correctness, or reviewability gap | Fix before G6 unless explicitly accepted by owner |
| `MEDIUM` | Improvement opportunity | Review and decide |
| `LOW` | Minor inconsistency | Record or fix |

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| A1 | CRITICAL | Seven-slice evidence claimed no block while its 32-path maximum already exceeded the 25-file threshold and omitted `tasks.md` | Split authored LOC from the complete 33-path ledger; added explicit size-only generated/control-plane routing and non-size stop rules across spec, plan, contract, quickstart, and tasks |
| A2 | HIGH | One cumulative UAT JSON could retain old rows while changing its single top-level `sourceCommit` | Every slice now commits a source checkpoint, re-executes all cumulative rows at it, and records results in a later evidence commit |
| A3 | HIGH | T118 built PR traceability only after all seven PRs were already opened | Each slice boundary now generates and validates its packet before PR creation; T118 is a final audit |
| A4 | MEDIUM | T014 depended on a result file created five tasks later, so its RED proof could not complete in order | RED proof is now immediate and self-contained; durable UAT begins after its carrier files exist |
| A5 | MEDIUM | Upstream reproducibility depended on a purgeable `/private/tmp` cache with no restore route | Research, quickstart, and T002 now rehydrate only the pinned commit and stop on any digest mismatch |
| A6 | LOW | T118 had no FR, SC, or story mapping | Added FR-015-FR-018, FR-024, and SC-007-SC-008 traceability |

Analyze metrics after remediation:

- 36/36 buildable requirements covered (24 FRs and 12 SCs); 119/119 tasks
  have a requirement or story mapping; 0 unmapped tasks.
- 0 unresolved placeholders, 0 constitution conflicts, and 0 unresolved
  CRITICAL/HIGH findings. G3, G5, and G6 runner validation all pass.
- All seven pinned source digests still match `spec.md`, `plan.md`, and the
  retrieved bytes. Manifest source/export classification remains exact.
- The dedicated Analyze executor and one fresh retry remained frozen with no
  result or diff. The orchestrator followed `error-recovery-codex.md`, ran the
  analysis/remediation directly, and applied the same G6 validation.

### Consensus Resolution Log

No unresolved item remained for consensus after direct remediation. The
advisory `one-navigable-PR` classifier result remains recorded without
overriding the operator-ratified seven-branch topology, and the layer planner
remains correctly skipped because its trigger is an exact `split-PR` route.

📊 Confidence: 0.98

- Task understanding: 0.99
- Approach clarity: 0.98
- Requirements alignment: 0.99
- Risk assessment: 0.97
- Completeness: 0.96

---

## Phase 6.5: Confidence Gate

**When to run:** After Analyze commits and before Implement.

| Field | Value |
|-------|-------|
| Mode | advisory |
| Composite confidence | 0.98 |
| Verdict | PASS (`0.98 >= 0.90`) |
| Evidence | `confidence-gate` request `art-005-g6-5`; recommended action `proceed` |

Confidence evidence must include the measured reviewability result, clean
cross-artifact analysis, pinned-source availability, focused baseline tests,
and executable file:// UAT procedure.

---

## Phase 7: Implement

**When to run:** Only after G6/G6.5 and all seven per-slice checkpoints pass.

### Implement Prompt

```text
/speckit-implement

Read tasks.md, plan.md, spec.md, research.md, contracts/, quickstart.md, and
docs/ai/specs/.process/ART-005-design-concept.md. Use the Q&A log for the why
behind test expectations, edge cases, and refactor choices.

## Approach: Strict TDD
For every behavior:
1. RED: write or extend the smallest focused test and prove it fails for the
   intended reason.
2. GREEN: implement only enough standalone HTML/CSS/JS to pass.
3. REFACTOR: simplify while focused tests remain green.
4. VERIFY: exercise the affected template directly over file://.

## Pre-Implementation Setup
1. Confirm the repository root is the ART-005 worktree and the branch matches
   the active slice in `contracts/slice-topology-contract.md`.
2. Confirm git status is clean and the workflow/spec/plan/tasks identify the
   same seven-slice stack and current slice.
3. Confirm the pinned upstream commit and all seven file digests are recorded and
   retrievable; keep upstream bytes outside the worktree.
4. Confirm Clarify reconciled the four provisional `exports: []` declarations
   against the pinned source interactions; stop if any conflict remains open.
5. Run the relevant Layer 1/Layer 4 baseline and record it.
6. Run the applicable slice's reviewability gate. Stop that slice on block
   unless the operator supplies a valid new topology decision or typed
   exception; do not infer either.

## Implementation Guidance
- In each stacked slice, create exactly its one standalone template and change
  exactly its one corresponding manifest status value.
- Embed canonical blocks verbatim. Do not edit shared foundation files or existing
  shipped templates and do not create a common runtime abstraction.
- Preserve representative content and each source's core mechanism while applying
  Racecraft tokens, responsive behavior, accessibility, and fill markers.
- Apply the resolved semantic classification: confirmed readers carry no export
  control; every confirmed producer has its reconciled manifest declaration and
  exactly one contract-compliant Copy as Markdown control using live session
  state. The three known editors remain producers.
- Use deterministic fenced JSON inside Markdown for feature-flags and prompt-tuner;
  use deterministic column-based Markdown for triage-board.
- Handle clipboard unavailable, rejected, and throwing paths with the same exact
  text revealed in a labeled focused fallback field.
- Apply named keyboard scroll regions, visible focus, semantic live status,
  color-independent meaning, dark/light parity, and reduced-motion behavior.
- Serialize shared manifest/test/generated work inside every slice after its
  template-local changes.
- Regenerate both Claude and Codex payload copies plus proofs with python3
  scripts/refresh-release-artifacts.py.
- Because tests/speckit-pro files change, run pnpm --dir docs-site
  reference:generate and keep the generated reference page authoritative.
- Run focused gates while iterating, then Layer 1, Layer 4, and
  python3 tests/speckit-pro/run-all.py on final bytes.
- Execute the tracked UAT runbook over file:// and commit a result record tied to
  the exact tested commit/bytes. Screenshots alone are not behavioral evidence.
- Never hand-edit payloads, installed-cache proofs, generated reference pages, or
  generated spec-index zones.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Shared baseline and contracts | Complete | 10 | Pinned digests match; G4 passes; L1 1448/1448, L4 5766/5766, full 7400/7400 |
| 2 - Slice 1 | Complete | 13 | PR #444 open; source checkpoint `660bfe9ce`; 18 pass, 18 evidence-backed N/A, zero fail; final gates green |
| 3 - Slice 2 | Complete | 13 | PR #446 open; source checkpoint `7c636c361`; cumulative UAT 36 pass, 36 evidence-backed N/A, zero fail; final gates green |
| 4 - Slice 3 | Complete | 13 | PR #447 open; source checkpoint `36ef824de`; cumulative UAT 54 pass, 54 evidence-backed N/A, zero fail; final gates green |
| 5 - Slice 4 | Complete | 13 | PR #448 open; source checkpoint `f27b7833e`; cumulative UAT 72 pass, 72 evidence-backed N/A, zero fail; final gates green |
| 6 - Slice 5 | Complete | 16 | PR #452 open; repaired source checkpoint `69f803d37`; cumulative UAT 107 pass, 73 evidence-backed N/A, zero fail; final gates green |
| 7 - Slice 6 | In Progress | 6 | Formal RED 494/497 gallery and 64/65 fills for intended missing producer; T085 active |
| 8 - Slice 7 | Pending | 0 | prompt-tuner plus incremental integration and closeout |

### Slice PR Stack

| Slice | Branch | Base | Pull request | Status |
|---:|---|---|---|---|
| 1 | `art-005-gallery-completion-knowledge-reports-editors` | `main` | [#444](https://github.com/racecraft-lab/racecraft-plugins-public/pull/444) | Open |
| 2 | `art-005-gallery-completion-knowledge-reports-editors-slice-2` | `art-005-gallery-completion-knowledge-reports-editors` | [#446](https://github.com/racecraft-lab/racecraft-plugins-public/pull/446) | Open |
| 3 | `art-005-gallery-completion-knowledge-reports-editors-slice-3` | `art-005-gallery-completion-knowledge-reports-editors-slice-2` | [#447](https://github.com/racecraft-lab/racecraft-plugins-public/pull/447) | Open |
| 4 | `art-005-gallery-completion-knowledge-reports-editors-slice-4` | `art-005-gallery-completion-knowledge-reports-editors-slice-3` | [#448](https://github.com/racecraft-lab/racecraft-plugins-public/pull/448) | Open |
| 5 | `art-005-gallery-completion-knowledge-reports-editors-slice-5` | `art-005-gallery-completion-knowledge-reports-editors-slice-4` | [#452](https://github.com/racecraft-lab/racecraft-plugins-public/pull/452) | Open |
| 6 | `art-005-gallery-completion-knowledge-reports-editors-slice-6` | `art-005-gallery-completion-knowledge-reports-editors-slice-5` | Pending | Active |

---

## Post-Implementation Checklist

Every canonical row must reach Complete or an explicit Skipped disposition.

| Canonical Item | Status | Evidence |
|---|---|---|
| Post: Doctor Extension Check | ⏳ Pending | |
| Post: Verify Implementation | ⏳ Pending | Seven template and manifest contracts |
| Post: Verify Tasks Phantom Check | ⏳ Pending | |
| Post: Code Review | ⏳ Pending | |
| Post: Integration Suite | ⏳ Pending | Layer 1, Layer 4, full suite, generated artifacts |
| Post: Reviewability Diff Gate | ⏳ Pending | Per-slice measured verdicts |
| Post: Self-Review | ⏳ Pending | |
| Post: UAT Runbook Generation | ⏳ Pending | Tracked seven-template file:// runbook |
| Post: PR Body Generation | ⏳ Pending | Review order, scope, traceability, evidence, gaps, rollback |
| Post: PR Creation | ⏳ Pending | |
| Post: Review Remediation | ⏳ Pending | |
| Post: Retrospective | ⏳ Pending | |

- [ ] All tasks are complete in `tasks.md`.
- [ ] `python3 tests/speckit-pro/run-all.py --layer 1` passes.
- [ ] `python3 tests/speckit-pro/run-all.py --layer 4` passes.
- [ ] `python3 tests/speckit-pro/run-all.py` passes with zero failures.
- [ ] `python3 scripts/refresh-release-artifacts.py` has regenerated payloads and
  proofs, followed by consistency verification.
- [ ] `pnpm --dir docs-site reference:generate` has regenerated test references
  after test-tree changes, and the generated diff is reviewed.
- [ ] Manual file:// verification is complete for all seven templates.
- [ ] The tracked UAT result identifies the tested commit and records every step.
- [ ] Final PR title passes the repository release-readiness title gate.
- [ ] No generated artifact was hand-edited.

---

## Lessons Learned

### What Worked Well

- Pending implementation evidence.

### Challenges Encountered

- Pending implementation evidence.

### Patterns to Reuse

- Pending implementation evidence.

---

## Project Structure Reference

```text
speckit-pro/artifact-gallery/
├── SPA-CONTRACT.md
├── manifest.json
└── templates/
    ├── slide-deck.html
    ├── concept-explainer.html
    ├── status-report.html
    ├── incident-report.html
    ├── triage-board.html
    ├── feature-flags.html
    └── prompt-tuner.html

tests/speckit-pro/unit/
├── test-artifact-gallery.py
└── test-artifact-fill-regions.py

docs/ai/specs/.process/
├── ART-005-design-concept.md
└── ART-005-workflow.md

specs/art-005-gallery-completion-knowledge-reports-editors/
├── SPEC-MOC.md
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/
├── quickstart.md
└── tasks.md
```

---

Populated by `$speckit-pro:speckit-scaffold-spec ART-005` on 2026-08-17 from
the technical roadmap and the Grill Me interview.
