# Research: ART-005 - Gallery Completion - Knowledge, Reports & Editors

## Decision: Pin The Existing Upstream Snapshot

Use `anthropics/html-effectiveness@58c305be97f47b26b678f2c07dec01d4242268ec`
for all seven ART-005 derivatives. The commit timestamp is
`2026-05-15T16:09:53Z`, and the local retrieved bytes were reverified on
2026-08-17 under `/private/tmp/art-005-upstream-58c305be97f47b26b678f2c07dec01d4242268ec/`.

Rationale: One immutable commit gives every slice the same reproducible source
baseline and lets the manifest source filenames, attribution headers, and
reviewability measurement agree.

Retrieval contract: the `/private/tmp/` directory is a scratch cache, not the
source of truth. If it is absent, fetch `anthropics/html-effectiveness`, detach
at commit `58c305be97f47b26b678f2c07dec01d4242268ec`, copy or read the seven named
root HTML files from that commit, and accept them only after all seven recorded
SHA-256 digests match. A floating branch or digest mismatch is a hard stop.

Alternatives considered:

- Floating upstream `main`: rejected because implementation and review could use
  different bytes.
- Roadmap-only recreation: rejected because it weakens provenance and functional
  fidelity.

## Decision: Preserve Reader/Producer Classification

`slide-deck`, `concept-explainer`, `status-report`, and `incident-report` remain
semantic readers with `exports: []`. `triage-board`, `feature-flags`, and
`prompt-tuner` remain semantic producers with `exports: ["markdown"]`.

Rationale: The pinned reader sources expose consumption or transient teaching
interactions only. Slide navigation, report anchors, and the concept explainer's
temporary simulation controls do not create durable user-authored output that
must leave the SPA. The three editor sources let the operator configure or edit
state and therefore require a Markdown export path.

Alternatives considered:

- Add exports to all interactive sources: rejected because it would change the
  manifest contract for true readers.
- Preserve upstream copy buttons exactly: rejected because upstream labels,
  hidden `execCommand` fallbacks, and multiple copy affordances conflict with
  the gallery contract.

## Decision: Use Markdown Wrappers With Fenced JSON For Structured Editors

`feature-flags` and `prompt-tuner` export deterministic Markdown documents that
contain exactly one fenced JSON block. `triage-board` exports deterministic
human-readable Markdown grouped by board column.

Rationale: The manifest export vocabulary remains closed and declares only
`markdown` for these editors. Fenced JSON inside Markdown preserves typed,
lossless structured state without inventing a `json` export kind.

Alternatives considered:

- Markdown tables for every editor: rejected for nested feature-flag and prompt
  tuner state because tables lose type and null/empty distinctions.
- A second JSON export: rejected because it changes the manifest vocabulary and
  UI contract.

## Decision: Apply The One-Attempt Clipboard Protocol

Each editor has exactly one control labeled `Copy as Markdown`. On invocation,
it clears stale fallback, generates the export once from live state, attempts
`navigator.clipboard.writeText()` once when available, and either reports the
success text or reveals/focuses the manual-copy textarea with the exact attempted
string.

Rationale: Existing shipped templates already use a visible fallback pattern, and
ART-003 proved `file://` clipboard behavior must be tested on the real scheme.
The ART-005 spec further fixes the exact success and failure messages and the
unavailable-clipboard probe.

Alternatives considered:

- Hidden `execCommand` fallback: rejected because it hides recovery and can
  create false success.
- Automatic download: rejected because it is an undeclared export path.

## Decision: Keep State Session-Only

Editor state initializes from representative sample data, changes in memory, and
resets on reload. Existing theme preference behavior remains owned by the
canonical gallery head block.

Rationale: The export is the explicit persistence boundary. Local storage, URL
state, or server state would create schemas and privacy/reset semantics outside
ART-005 scope.

Alternatives considered:

- `localStorage` editor content: rejected for stale schema and reset ambiguity.
- Shareable URL state: rejected for size, validation, and content sensitivity.

## Decision: Use Existing Gallery Contracts And Fill Grammar

Every new artifact embeds the canonical `GALLERY-HEAD` and `BRAND-KIT` regions
byte-for-byte, carries the upstream attribution header, places the fill inventory
comment immediately after the attribution header, and declares fill regions using
the existing `FILL:<slot>:START` / `FILL:<slot>:END` grammar.

Rationale: `SPA-CONTRACT.md`, `test-artifact-gallery.py`, and
`test-artifact-fill-regions.py` already validate this structure. Reusing the
existing grammar avoids creating another authoring interface for gallery fills.

Alternatives considered:

- A new ART-005-specific fill schema: rejected because it would bypass existing
  validation and increase agent-facing surface.
- Editing canonical blocks: rejected because ART-005 has no shared foundation
  change.

## Decision: Use Tracked Active UAT Files And Post-Merge Archival Paths

During active work, UAT lives under
`specs/art-005-gallery-completion-knowledge-reports-editors/.process/`. After
merge, the same evidence is preserved under `docs/ai/specs/.process/ART-005-*`.

Rationale: The spec fixes active and archival locations, and prior ART-002/ART-003
evidence shows durable runbook/result records are needed for later review and
post-merge hygiene.

Alternatives considered:

- PR checklist only: rejected because it is not durable after review.
- Screenshots only: rejected because they cannot prove keyboard traversal,
  clipboard read-back, or fallback focus.

## Decision: Seven Sequential Review Slices

Keep one ART-005 spec and workflow, but deliver one template per sequential
stacked PR slice in manifest order.

Rationale: The combined seven-template projection blocked. ART-003 one-template
slices landed under the 800 block, while ART-002 multi-template slices blocked
after merge measurement. Shared manifest/test/generated/UAT files are serialized
by stacking.

Alternatives considered:

- One combined slice: rejected by measured block.
- Split an individual template: rejected because the operator selected one
  template per slice and no individual slice currently blocks.
