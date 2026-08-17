---
topic: "Gallery Completion — Knowledge, Reports & Editors"
slug: "art-005-gallery-completion-knowledge-reports-editors"
date: "2026-08-17"
mode: "setup"
spec_id: "ART-005"
source_input:
  type: "topic"
  ref: "docs/ai/specs/html-artifacts-technical-roadmap.md § ART-005: Gallery Completion — Knowledge, Reports & Editors"
question_count: 8
stop_reason: "natural"
---

# Design Concept: Gallery Completion — Knowledge, Reports & Editors

> **Source:** `docs/ai/specs/html-artifacts-technical-roadmap.md` § ART-005
> **Date:** 2026-08-17
> **Questions asked:** 8
> **Stop reason:** natural — the scope, export contract, provenance, state model, failure path, port fidelity, UAT evidence, and accessibility baseline are resolved
> **Blind-spot pass:** did not run — dispatch error: Full-history forked agents inherit the parent agent type; omit agent_type, or spawn without a full-history fork.

## Goals

- Port all seven ART-005 templates as branded, standalone gallery artifacts:
  `slide-deck`, `concept-explainer`, `status-report`, `incident-report`,
  `triage-board`, `feature-flags`, and `prompt-tuner`.
- Deliver the seven ports as **one combined review and merge slice** (Q1),
  preserving the roadmap's existing one-slice topology despite both the roadmap
  and fresh estimator recommending two slices.
- Resolve one immutable commit from `anthropics/html-effectiveness` during Plan
  research and use that same revision for all seven derivatives (Q3).
- Keep the four read-only templates free of export controls and give the three
  editors exactly one `Copy as Markdown` affordance, matching their manifest
  declarations.
- Serialize structured feature-flag and prompt-tuner state as a Markdown
  document containing fenced JSON, preserving lossless structured data without
  inventing a second export kind (Q2).
- Keep editor working state session-only, apart from the gallery's existing
  theme preference; export is the deliberate persistence boundary (Q4).
- Reuse the shipped visible clipboard-fallback behavior (Q5): announce failure,
  reveal the generated text in a selectable field, and move focus to the
  recovery path.
- Preserve each upstream template's core content and interaction model while
  applying Racecraft branding, gallery contracts, and accessibility behavior
  (Q6).
- Preserve manual `file://` acceptance as a tracked runbook plus a durable
  pass/fail result covering all seven templates (Q7).
- Enforce the current accessibility baseline on every new port, including
  keyboard-reachable named scroll regions, visible focus, semantic status
  messages, and reduced-motion handling (Q8).

## Non-goals

- Workflow-stage routing; all seven catalog entries remain `ad-hoc`.
- A JSON export kind or a second editor export control. Structured data remains
  inside the declared Markdown export.
- Persistent editor content in `localStorage`, shareable URL state, server-side
  storage, or an import-back workflow.
- Pixel-for-pixel reproduction of upstream styling or a ground-up redesign.
- Export affordances on `slide-deck`, `concept-explainer`, `status-report`, or
  `incident-report`; their manifest entries declare `exports: []`.
- Shared gallery-foundation changes. Each port embeds the canonical blocks and
  changes only its own catalog `status`, as required by `SPA-CONTRACT.md:60-71`.
- Repairs to already-shipped templates owned by ART-020. ART-005 applies the
  corrected pattern only to its seven net-new ports.

## Size Estimate and Review Risk

The shared estimator was run after the interview with these scoping-time
signals:

- `user_stories: 3` — the roadmap's three outcome groups: knowledge, reports,
  and editors.
- `files: 9` — the roadmap's seven production files plus approximately two
  shared test/catalog surfaces (`html-artifacts-technical-roadmap.md:419-425`).
- `frs: 8` — port completion, source provenance, export shape, clipboard
  recovery, state persistence, fidelity, accessibility, and durable UAT.
- `new_vs_modify: new` — all seven production templates are net-new.

Result:

```json
{"estimated_loc":555,"suggested_slices":2,"status":"warn"}
```

This corroborates the roadmap's earlier 560-LOC warning rather than replacing
it (`html-artifacts-technical-roadmap.md:419-425`). The user nevertheless chose
one combined slice in Q1. Plan must therefore measure the pinned upstream files
and project the complete reviewable surface before implementation begins.

That check is material: ART-002 declared 530 LOC per slice and realized 1494
and 2027, while ART-003's one-template slices landed at 735, 724, and 408 after
re-estimation (`.specify/memory/archive-reports/2026-08-14-art-003-post-merge-hygiene.md:88-103`).
If the combined plan crosses the final reviewability block, planning must stop
and surface the conflict rather than silently overriding either the user's
one-slice decision or the repository gate.

## Design Tree (Q&A log)

### Q1. How should ART-005's seven template ports be packaged for review and merge?

**Branch:** Slice sizing and execution topology

**Recommended answer:** One template per slice.

> ART-003 is the closest realized evidence: one-template slices measured 735,
> 724, and 408 reviewable LOC, while ART-002's multi-template slices measured
> 1494 and 2027 (`.specify/memory/archive-reports/2026-08-14-art-003-post-merge-hygiene.md:88-103`).
> The seven ports also converge on the same manifest and fill-region test
> literals, which ART-003 identifies as shared conflict surfaces
> (`.specify/memory/archive-reports/2026-08-14-art-003-post-merge-hygiene.md:105-108`).

**Alternatives offered:**
- Two slices, 4 + 3: the roadmap's fallback and fewer reviews, but still exposes
  each PR to the multi-template overrun pattern.
- One combined slice: preserves the roadmap's original shape and avoids stacked
  merge overhead, but carries the highest reviewability and integration risk.

**User's answer:** One combined slice.

**Consequence:** ART-005 remains one spec, one implementation branch, and one
review/merge unit. The plan-time reviewability measurement is a hard decision
checkpoint, not permission to split automatically.

---

### Q2. For feature-flags and prompt-tuner, how should structured editor state be represented in the exported Markdown?

**Branch:** Export serialization

**Recommended answer:** Fenced JSON in Markdown.

> The catalog declares only `markdown` for all three editors
> (`speckit-pro/artifact-gallery/manifest.json:214-244`), and the export
> vocabulary is closed (`SPA-CONTRACT.md:117-124`). A Markdown document with a
> short human-readable heading and a fenced JSON block preserves typed,
> structured state without falsely adding `json` to the manifest.

**Alternatives offered:**
- Markdown tables: easier to scan, but unreliable for nested values, explicit
  types, and lossless round-tripping.
- Separate JSON export: more native for structured data, but changes the
  roadmap, manifest, UI, and acceptance contract.

**User's answer:** Fenced JSON in Markdown (Recommended).

**Consequence:** `feature-flags` and `prompt-tuner` export deterministic
Markdown documents containing fenced JSON. `triage-board` remains ordinary
Markdown organized by board column; its exact headings are a Plan detail.

---

### Q3. What upstream source baseline should the ART-005 implementation use?

**Branch:** Provenance and reproducibility

**Recommended answer:** Pin one commit.

> The manifest identifies seven upstream filenames but carries no immutable
> revision (`manifest.json:170-244`), and none of those upstream HTML files is
> vendored locally. Resolving one commit during research makes the derivative
> inputs repeatable and keeps every port in the combined review on the same
> source baseline.

**Alternatives offered:**
- Follow upstream `main`: obtains the latest source but can change between
  implementation, review, and later reproduction.
- Recreate from the roadmap: avoids retrieval but weakens derivative fidelity
  and source traceability.

**User's answer:** Pin one commit (Recommended).

**Consequence:** Plan records the upstream repository, commit SHA, per-file
paths, and retrieval date. Only branded derivatives are committed; retrieved
source bytes remain outside the repository.

---

### Q4. Beyond existing theme preferences, should the three interactive editors persist their working state after a reload?

**Branch:** Editor state model

**Recommended answer:** Session only.

> ART-005 promises an export-back feedback loop, not storage
> (`html-artifacts-technical-roadmap.md:427-437`). Session-only state makes `Copy
> as Markdown` the explicit persistence boundary and avoids inventing storage
> schemas, migration, privacy, and reset semantics for standalone HTML files.

**Alternatives offered:**
- Browser local storage: convenient across reloads, but adds storage lifecycle
  and stale-schema behavior.
- Shareable URL state: makes state portable, but adds validation, URL-size, and
  sensitive-content concerns.

**User's answer:** Session only (Recommended).

**Consequence:** Editor content initializes from representative sample data,
changes only in memory, and resets on reload. Existing theme persistence is not
part of this decision.

---

### Q5. What should happen when Copy as Markdown cannot write to the clipboard under file:// or browser restrictions?

**Branch:** Export failure recovery

**Recommended answer:** Visible fallback field.

> The gallery contract requires a selectable manual-copy field when clipboard
> access fails, especially over `file://`, and requires live-state exports plus
> textual success reporting (`SPA-CONTRACT.md:372-382`). ART-003's acceptance
> pass confirmed that the failure path must be exercised on the real scheme
> because `http://` changes clipboard permissions
> (`.specify/memory/archive-reports/2026-08-14-art-003-post-merge-hygiene.md:110-124`).

**Alternatives offered:**
- Status message only: reports the failure but strands the generated content.
- Automatic download: recovers content but adds a second undeclared export
  mechanism.

**User's answer:** Visible fallback field (Recommended).

**Consequence:** Each editor reads `navigator.clipboard` at invocation time,
handles unavailable, rejected, and synchronously throwing clipboard access,
then reveals and focuses a labeled field containing the exact export text.

---

### Q6. How closely should the seven ports preserve their upstream designs?

**Branch:** Porting fidelity

**Recommended answer:** Functional fidelity.

> ART-005 explicitly asks for branded derivatives of seven named upstream
> sources (`html-artifacts-technical-roadmap.md:438-440`). The single-file and
> canonical-block contracts constrain implementation structure
> (`SPA-CONTRACT.md:17-25`, `:60-71`), so fidelity means preserving each source's
> core content model and distinguishing interaction—not retaining conflicting
> styling or inaccessible mechanics.

**Alternatives offered:**
- Pixel-close port: visually conservative, but can preserve upstream behavior
  that conflicts with gallery branding or accessibility.
- Full redesign: maximizes local freedom but weakens the derivative's traceable
  relationship to its named source.

**User's answer:** Functional fidelity (Recommended).

**Consequence:** Plan must state the preserved interaction/content mechanism
and the intentionally changed gallery-contract behavior for each of the seven
ports.

---

### Q7. How should the required manual file:// acceptance testing be preserved for reviewers?

**Branch:** Acceptance evidence

**Recommended answer:** Tracked runbook and results.

> The roadmap requires manual editor export verification over `file://`
> (`html-artifacts-technical-roadmap.md:446-449`). ART-003 executed 176 checks
> successfully but merged no acceptance-result record; its preserved runbook
> covered only one of three templates
> (`.specify/memory/archive-reports/2026-08-14-art-003-post-merge-hygiene.md:209-221`).

**Alternatives offered:**
- PR checklist only: compact, but not durable or independently executable after
  the review closes.
- Screenshots only: useful visual evidence, but cannot prove keyboard behavior,
  live-state serialization, or clipboard recovery.

**User's answer:** Tracked runbook and results (Recommended).

**Consequence:** Implementation must preserve both the executable plain-English
procedure and a durable result record for all seven templates. The result must
distinguish genuine clipboard success from the forced manual-copy fallback.

---

### Q8. What accessibility baseline should ART-005 enforce on its seven new templates?

**Branch:** Accessibility scope

**Recommended answer:** Enforce current baseline.

> ART-020 exists specifically to keep ART-004 and ART-005 from repeating the
> gallery's keyboard-scroll defect. It requires focusable, named horizontal
> scroll regions and a Layer 4 assertion (`html-artifacts-technical-roadmap.md:1357-1401`).
> The gallery contract separately requires keyboard-operable exports and
> textual status (`SPA-CONTRACT.md:372-380`).

**Alternatives offered:**
- Defer to ART-020: keeps this port narrower but knowingly risks adding more
  instances for a later repair.
- Match upstream only: preserves source behavior even when it falls below the
  gallery's current contract.

**User's answer:** Enforce current baseline (Recommended).

**Consequence:** Every new scroll region is keyboard reachable and named; all
controls have visible focus and accessible names; status is semantic and not
color-only; motion respects reduced-motion preferences. ART-005 does not edit
the older templates ART-020 owns.

## Decisions Recorded Without a Question

These points are already fixed by the roadmap or gallery contract and did not
need another interview turn.

- **Catalog routing:** all seven entries remain `ad-hoc` and retain their
  existing identifiers, categories, guidance, triggers, sources, and exports.
  Each port changes only its own `status` from `planned` to `shipped`.
- **Read-only behavior:** `slide-deck`, `concept-explainer`, `status-report`, and
  `incident-report` carry no export control because `exports: []` is an explicit
  read-only declaration (`SPA-CONTRACT.md:384-390`).
- **Standalone delivery:** each artifact is one HTML file with no build step,
  bundler, preprocessing, or post-processing (`SPA-CONTRACT.md:17-25`).
- **Export labels:** the exact control label is `Copy as Markdown`, never a
  generic `Export` label (`SPA-CONTRACT.md:372-375`).
- **Live-state serialization:** every editor export is produced from current UI
  state at invocation time (`SPA-CONTRACT.md:378-382`).
- **No shared-foundation edits:** do not modify `brand-kit.css`,
  `theme-toggle.html`, `SPA-CONTRACT.md`, or another template's catalog row.
- **Payload contract:** shipped gallery bytes affect the plugin payload, so the
  implementation must regenerate release artifacts and installed-cache proofs
  through authoritative repository tooling rather than editing generated files.
- **Automated verification:** extend the Layer 4 gallery and fill-region
  coverage for all seven templates, run Layer 1, and run the repository's
  generated-artifact consistency gates.

## Open Questions

- **What:** Which immutable upstream commit and exact source-file digests form
  the seven-port baseline?
  **Why deferred:** Resolving current external repository state is Plan research,
  and the user chose the immutable policy rather than a specific revision.
  **Suggested next step:** During Plan research, resolve one reachable commit,
  verify all seven manifest paths at it, and record the SHA and digests.

- **What:** What exact fill-region slot inventory and representative sample data
  does each template carry?
  **Why deferred:** Slot names must follow the pinned upstream structures and the
  existing fill-region grammar; inventing them before source retrieval would
  weaken functional fidelity.
  **Suggested next step:** Derive and validate all seven inventories during
  Clarify/Plan after upstream inspection.

- **What:** What exact deterministic Markdown schema does each editor export?
  **Why deferred:** Q2 fixes fenced JSON for `feature-flags` and `prompt-tuner`,
  and Q5 fixes failure behavior, but field names, ordering, schema/version
  markers, and triage-board headings depend on the pinned editor models.
  **Suggested next step:** Specify an example export and stable ordering for
  each editor in Plan contracts.

- **What:** Where do the tracked ART-005 UAT runbook and result record live, and
  what evidence fields are mandatory?
  **Why deferred:** Q7 fixes durability and coverage, while the repository's
  current UAT artifact conventions should be resolved during planning rather
  than guessed in setup.
  **Suggested next step:** Reuse the current UAT runbook/result convention and
  require per-template, per-check verdicts plus environment and commit identity.

- **What:** Can the combined seven-template slice remain below the final
  reviewability block after the pinned upstream files are measured?
  **Why deferred:** Both the 555 forward estimate and the roadmap's 560 value are
  scoping guesses; sibling realized measurements show a material overrun risk.
  **Suggested next step:** Plan must produce a file-by-file reviewable-LOC
  projection before implementation. If it blocks, stop for a topology decision;
  do not split without explicit approval.

## Recommended Next Step

Setup has already run in this dedicated worktree. The scaffold command writes
the ART-005 workflow and SPEC-MOC marker next, then marks ART-005 In Progress in
the technical roadmap.

After scaffold completion, start the planning stage with the rooted handoff
command printed by the scaffold workflow.
