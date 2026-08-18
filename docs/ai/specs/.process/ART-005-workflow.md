# SpecKit Workflow: ART-005 — Gallery Completion — Knowledge, Reports & Editors

**Template Version**: 1.0.0
**Created**: 2026-08-17
**Purpose**: Execute ART-005 through the SpecKit workflow on branch `art-005-gallery-completion-knowledge-reports-editors`.

---

## How to Use This Template

1. Start every phase from the dedicated ART-005 worktree and verify the active
   branch is `art-005-gallery-completion-knowledge-reports-editors`.
2. Re-read the design concept before each phase. Its Q&A log is the source of
   truth for human-approved scoping decisions.
3. Run the phases through `$speckit-autopilot` with this workflow file. Scaffold
   does not run planning or implementation itself.
4. Keep ART-005 as one combined review/merge unit unless the plan-time
   reviewability gate blocks. A block requires an explicit operator decision;
   it does not authorize an automatic split.
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
| Specify | `/speckit-specify` | ✅ Complete | 3 stories, 20 current FRs, 8 scenarios, and 8 success criteria; the intentional marker was resolved in Clarify |
| Clarify | `/speckit-clarify` | ✅ Complete | Three sessions resolved source/fidelity/fill, editor exports, UAT evidence, and block routing; no consensus needed |
| Plan | `/speckit-plan` | ⚠️ Blocked | 4,042 upstream LOC; conservative projection 2,856 reviewable LOC exceeds the 800 block; awaiting explicit topology decision |
| Checklist | `/speckit-checklist` | ⏳ Pending | Accessibility, UX, data-integrity, and error-handling |
| Tasks | `/speckit-tasks` | ⏳ Pending | TDD ordering across seven templates and shared integration surfaces |
| Analyze | `/speckit-analyze` | ⏳ Pending | Check all artifacts against the design concept |
| Confidence Gate | G6.5 | ⏳ Pending | Pre-Implement composite confidence |
| Implement | `/speckit-implement` | ⏳ Pending | One combined branch and review unit |
| Post | Post-Implementation | ⏳ Pending | Canonical closeout plus tracked `file://` UAT results |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⏭️ Skipped | ⚠️ Blocked

G6.5 is advisory by default. Record its verdict in Phase 6.5 when it runs.

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | All seven templates and three outcome groups are covered; no `[NEEDS CLARIFICATION]` marker remains unless deliberately routed to Clarify |
| G2 | After Clarify | Pinned-source policy, semantic read-only classification, fill slots, export schemas, UAT record, and reviewability uncertainty have an explicit disposition |
| G3 | After Plan | Constitution gates pass; the immutable upstream revision is recorded; declared file operations and a measured reviewability projection exist |
| G4 | After Checklist | Every `[Gap]` from the four selected domains is fixed or explicitly deferred to a named owner |
| G5 | After Tasks | Requirements map to ordered TDD tasks; the combined-slice checkpoint is explicit |
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
- Required branch: `art-005-gallery-completion-knowledge-reports-editors`
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
| **Branch** | `art-005-gallery-completion-knowledge-reports-editors` |
| **Stage** | `plan` |
| **Dependencies** | ART-001; dependency is satisfied on `main` |
| **Enables** | Gallery completeness |
| **Priority** | P2 |
| **Roadmap** | `docs/ai/specs/html-artifacts-technical-roadmap.md` § ART-005 |
| **Reviewability** | Fresh estimate: 555 LOC, warn, suggested two slices; user chose one combined slice |
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

Make each story independently testable while keeping implementation in the
single combined slice selected by the operator.

### Human-Validated Decisions — Do Not Re-litigate
- Q1: "One combined slice."
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
with two slices suggested. The operator deliberately selected one combined
slice. Require a plan-time file-by-file measurement of the pinned sources and
declared operations. If the final projection blocks, stop for an operator
topology decision; do not silently split or invent an exception.

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
| Functional Requirements | 20 current after Clarify |
| User Stories | 3 |
| Acceptance Criteria | 8 scenarios |
| Reviewability result | 555/560 LOC warn; operator-selected one combined slice retained with a plan-time block stop |

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
- Q1 says "One combined slice." Plan one spec, one branch, one implementation
  review. Do not create child specs or branches.
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
- Declare each of the seven NEW template paths individually.
- Declare manifest.json and every modified Layer 4 test file individually. The
  seven template files and their seven `planned` → `shipped` status flips are
  one atomic gallery-contract operation.
- Declare the chosen UAT runbook and result-record paths.
- Identify both Claude and Codex payload copies plus reference/proof files as
  generated operations, never hand-edited sources of truth.
- Keep all template implementations independent. Shared integration changes are
  serialized: manifest rows, fill-region literals, payload generation, docs test
  reference generation, and final suite execution.
- Do not modify brand-kit.css, theme-toggle.html, SPA-CONTRACT.md, existing
  shipped templates, export vocabulary, or workflow-stage routing.

## Reviewability Gate Before Design Completion
The setup estimator returned 555 LOC, warn, suggested two slices; the roadmap
declares 560, warn, suggested two. Measure the pinned upstream files and project
the complete reviewable surface using the plan's declared operations. Compare
against realized ART-002/ART-003 port data. If the combined plan reaches block,
stop and request the operator's topology decision. No typed exception currently
applies, and the one-slice interview answer cannot be silently overwritten.

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
| `plan.md` | ⚠️ Blocked | STOP record: seven pinned sources measure 4,042 LOC / 120,618 bytes; conservative projection 2,856 reviewable LOC exceeds the 800 block |
| `research.md` | ⏭️ Not created | Reviewability checkpoint stopped Phase 0/Phase 1 design completion |
| `data-model.md` | ⏭️ Not created | Reviewability checkpoint stopped Phase 0/Phase 1 design completion |
| `contracts/` | ⏭️ Not created | Reviewability checkpoint stopped Phase 0/Phase 1 design completion |
| `quickstart.md` | ⏭️ Not created | Reviewability checkpoint stopped Phase 0/Phase 1 design completion |

### Plan Reviewability Stop

- Pinned-source measurement: 7 files, 4,042 lines, 120,618 bytes; every digest
  reverified against the official upstream bytes.
- Conservative realized-port projection: 2,856 reviewable LOC; ART-003-average
  projection: 4,356 reviewable LOC. Both exceed the 800-LOC block.
- Runner estimator diagnostic: recognized 10 NEW and 3 MODIFIED declarations,
  but returned `production: 0`, `projected: 0`, `pass` because the seven net-new
  production files do not yet exist. This advisory blind spot does not override
  the explicit measured checkpoint.
- Runner G3 syntax diagnostic: pass because `plan.md` exists with zero unresolved
  markers. Workflow G3 is **not cleared**: design outputs are intentionally absent
  and the human-approved reviewability rule is blocked.
- Required disposition: record the measured projection and wait. Do not continue
  to Checklist, Tasks, Analyze, Confidence Gate, or Implementation; do not split
  automatically and do not treat the earlier one-slice selection as an exception.

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
| accessibility | Pending | Pending | Pending |
| ux | Pending | Pending | Pending |
| data-integrity | Pending | Pending | Pending |
| error-handling | Pending | Pending | Pending |
| **Total** | Pending | Pending | Pending |

### Addressing Gaps

For each `[Gap]`: decide whether it is a genuine missing requirement, update
`spec.md` or `plan.md`, re-run the checklist, and name a follow-up owner for any
intentional deferral. No unresolved gap reaches Tasks.

---

## Phase 5: Tasks

**When to run:** After all checklist gaps are closed. Output:
`specs/art-005-gallery-completion-knowledge-reports-editors/tasks.md`.

### Tasks Prompt

```text
/speckit-tasks

Read spec.md, plan.md, research.md, contracts/, quickstart.md, and
docs/ai/specs/.process/ART-005-design-concept.md. The design concept is the
source of truth for the one-slice decision, the eight human-approved answers,
and the six Open Questions including semantic reader/producer classification.

## Task Structure
- Use strict RED → GREEN → REFACTOR ordering for every behavior.
- Give every task an exact repo-relative path and requirement/story reference.
- Different standalone template files may be [P] only after their failing tests
  and source contracts exist. Never mark shared manifest, shared test literals,
  generated artifacts, or final integration commands parallel.
- Add a pre-implementation reviewability checkpoint using the Plan measurement.
  Stop if the combined slice blocks; do not create slices automatically.

## Implementation Phases
1. Baseline and contracts: record pinned upstream evidence, finalize fill/export
   contracts, add failing Layer 4 assertions, and confirm the combined budget.
2. Provisionally read-only knowledge artifacts: after Clarify confirms their
   semantic classification, implement slide-deck and concept-explainer and prove
   each independently over file:// against its resolved export contract.
3. Provisionally read-only reports: after Clarify confirms their semantic
   classification, implement status-report and incident-report and prove each
   independently over file:// against its resolved export contract.
4. Interactive editors: triage-board, feature-flags, and prompt-tuner, each with
   live-state Markdown, clipboard success, forced fallback, keyboard, and edge tests.
5. Serialized integration: flip only the seven status values, complete shared
   fill/gallery coverage, regenerate payloads and docs references, run focused and
   full suites, execute UAT, and commit the durable result record.
6. Review packet and closeout: trace every FR/SC to files and evidence, document
   review order, known gaps, rollback, and the accepted one-slice warning.

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
- Manual file:// UAT covers all seven templates and both clipboard outcomes for
  each confirmed state-producing artifact, with a tracked runbook and
  tested-commit result record.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | Pending |
| **Phases** | Target: 6 |
| **Parallel Opportunities** | Template-local work only; pending classifier |
| **User Stories Covered** | Target: US1-US3 |

---

## Atomicity Route

After Tasks/G5, run the read-only classifier against:

```text
runner helper atomicity-route specs/art-005-gallery-completion-knowledge-reports-editors
```

The classifier informs review navigation but does not override Q1. Record its
machine-readable decision here:

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** |  | `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope` |
| **Releasable** |  | `true` or `false` |
| **Signals** |  | Decisive structural findings |
| **Warnings** |  | Release-safety warnings |

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
6. Whether the combined-slice budget is honestly measured. Treat a block without
   an operator topology decision as CRITICAL.
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
| Pending | Pending | Analyze has not run | Pending |

---

## Phase 6.5: Confidence Gate

**When to run:** After Analyze commits and before Implement.

| Field | Value |
|-------|-------|
| Mode | advisory unless explicitly changed |
| Composite confidence | Pending |
| Verdict | Pending |
| Evidence | Pending |

Confidence evidence must include the measured reviewability result, clean
cross-artifact analysis, pinned-source availability, focused baseline tests,
and executable file:// UAT procedure.

---

## Phase 7: Implement

**When to run:** Only after G6/G6.5 and the combined-slice checkpoint pass.

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
1. Confirm the repository root is the ART-005 worktree and the branch is
   art-005-gallery-completion-knowledge-reports-editors.
2. Confirm git status is clean and the workflow/spec/plan/tasks identify the same
   branch and one-slice topology.
3. Confirm the pinned upstream commit and all seven file digests are recorded and
   retrievable; keep upstream bytes outside the worktree.
4. Confirm Clarify reconciled the four provisional `exports: []` declarations
   against the pinned source interactions; stop if any conflict remains open.
5. Run the relevant Layer 1/Layer 4 baseline and record it.
6. Run the plan reviewability gate. Stop on block unless the operator has supplied
   a valid topology decision; do not invent a typed exception.

## Implementation Guidance
- Create exactly seven standalone template files and change exactly the seven
  corresponding manifest status values.
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
- Serialize shared manifest/test/generated work after template-local changes.
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
| 1 - Baseline and contracts | Pending | 0 | Pinned source, failing tests, budget checkpoint |
| 2 - Knowledge artifacts | Pending | 0 | slide-deck, concept-explainer |
| 3 - Reports | Pending | 0 | status-report, incident-report |
| 4 - Editors | Pending | 0 | triage-board, feature-flags, prompt-tuner |
| 5 - Integration and UAT | Pending | 0 | Shared files, regeneration, full evidence |
| 6 - Review packet | Pending | 0 | Traceability and closeout |

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
| Post: Reviewability Diff Gate | ⏳ Pending | Combined-slice measured verdict |
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
