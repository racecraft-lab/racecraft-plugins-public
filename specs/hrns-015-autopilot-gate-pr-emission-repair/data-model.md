# Data Model: HRNS-015

The feature stores Markdown, JSON, Git-index membership, and GitHub PR state. These entities describe existing records and the new validation contracts; they do not imply a database.

## Roadmap entry and slice budget

**RoadmapEntry**: `spec_id` (case-sensitive string), authored heading `### <spec_id>:`, bounded section text, required reviewable LOC, production-file count, total-file count, primary surfaces, optional typed exception, ordered slice IDs, optional slice budget rows. The section ends at the next peer-level roadmap entry. Values from neighboring entries and generated text never belong to this entity.

**SliceBudget**: unique ID from the ordered list; `estimated_loc`, `production_files`, and `total_files` as nonnegative integers. Exactly one complete row exists for each ID, with no extras or duplicates. Aggregate LOC and file counts are sums of all rows. A split is accepted only if each row is strictly below the applicable block lines and the required entry fields are complete. Greenfield modifies LOC thresholds by 1.5x, not file or surface thresholds. A selected authored, line-anchored exception can use only `refactor`, `infra`, or `upgrade`.

**GateEvaluation**: `status` ∈ {`pass`, `warn`, `block`, `exception`}; `pass` boolean; `reviewable_loc`, `production_files`, `total_files`, `primary_surfaces`, `warnings`, `blockers`, exception class, and per-slice plus aggregate evidence. Missing `spec_id` is an invalid request. Missing named section or budget field produces `block`/false/exit 1 and names the field. A complete valid selected exception produces `status: exception`, `pass: true`, and `exception_class` with its exact class. A malformed, mis-cased, placeholder, or unsupported candidate in the selected authored section is named in `exceptions.rejected`, cannot override the budget, and leaves an over-block result blocked. For a complete split, the existing top-level LOC and file counts are row sums, and `slice_results` is an ordered array of ID, three counts, status, pass, warnings, and blockers; an invalid row blocks with a named diagnostic and exit 1. No split retains the existing response shape. Blocked slice data cannot be converted into a pass by another section.

## Marker and index

**VisibleMarker**: source file, line/position, marker type, bracket content, and visibility. A Gap tag is a single-line non-nested bracket tag whose comma-delimited tokens include exact case-sensitive `Gap` after spaces/tabs are trimmed. Each qualifying bracket tag counts once, including multiple tags on one line. Gap and clarification count/detail paths share a Markdown visibility decision; inline, fenced, and indented code is excluded. Other marker classes keep their current behavior.

**IndexCandidate**: repo-relative path, source Git-index membership, staged/committed state, and extracted backlink/home metadata. A candidate absent from the source index is ineligible even when inside a tracked spec directory. Staged additions are eligible. Generated spec-index output derives only from eligible candidates; the refresh check compares expected output with tracked index files in an isolated copy and names drifted paths.

## Quality command and size estimate

**QualityCommandSlot**: one of `COMPLEXITY`, `MUTATION`, `DEPENDENCY_RULES`, or `DEPENDENCY_AUDIT`; optional nonblank declared command, effective command, and `source`. A declaration replaces detection only for that slot and reports `declared` in an additive `command_sources` map and the slot's quality `gates` record, while `detect-commands.commands` values stay strings. A non-object `commands` value, unknown slot, or blank/non-string command invalidates the config and fails G0 with a nonzero exit and a diagnostic naming the field; detection cannot hide the invalid declaration. Absent `commands` and undeclared slots retain existing detection. The new optional `commands` object lives in `.specify/quality-gates.json` alongside approved thresholds and basis.

**SizeEstimate**: existing `user_stories`, `files`, `frs`, `new_vs_modify`, and `spike` signals plus optional `required_refactor_files`. The new signal is a nonnegative integer for additional required existing-file work not already in `files`. Base formula and modify discount remain unchanged; add 40 LOC per distinct refactor file afterward. `suggested_slices` is ceil(total/400), minimum one. A spike retains its fixed result before all sizing.

## Packet and workflow

**PRPacket**: packet ID, validated feature directory, canonical untracked paths (`<id>.json`, `<id>/body.md`, `<id>/validation.json`), draft/final mode, existing fields, optional nonblank unfenced Markdown-string `release_note`, and rendered body; an explicit invalid note is rejected rather than omitted. The optional final release-note heading follows the eight required headings; only its enclosed body is editable. A draft has no editable fields and no release-note fence. A final packet's protected Verification line carries the current Phase 6.5 Verdict (`proceed`, `remediate`, `stop`). Missing/invalid verdict blocks final emission. The dirty guard ignores only this packet's three canonical paths when they are untracked; tracked changes and all other paths block.

**PostRow**: canonical name from the 13-item `POST_STEPS` source, order, persisted workflow occurrence/status, and state-file occurrence/status. At the full-run success boundary, every canonical row occurs exactly once in both records with matching terminal status. Workflow `✅ Complete` maps to state `completed`. The only other accepted status is identical `skipped: <extension> not installed` for a canonical optional extension-dependent row when supported registry and directory detection both find the named extension absent; it encodes reason `extension_not_installed`. Other skips, missing, duplicate, pending, in-progress, or mismatched rows fail with named diagnostics. A legacy 11-row record remains incomplete: only unique exact-name statuses carry forward, while new or renamed canonical rows begin pending and cannot inherit completion by position or predecessor.

**ExecutorTeamReceipt**: executor/host, child IDs, per-child returned result or supported stop evidence, graceful-shutdown request, no-active-child confirmation, cleanup completion, and unresolved confirmations. A clean completion requires all confirmations. Unknown Codex post-parent lifetime is not substituted for a receipt.

**BlindSpotPass**: `outcome` ∈ {`ran`, `dispatch error`, `empty return`, `operator abandonment`}, nonempty summary when ran, specific reason when proceeding without findings, and source instruction reference for operator abandonment. The existing Design Concept header `Blind-spot pass` line is durable; the operator status echoes the same outcome/reason. Elapsed time is never a state transition.

## Review feedback and workflow link

**ReviewThread**: GraphQL node ID, path/context, resolved state, all paginated comments, thread cursor, and per-thread comment cursor. Incomplete pagination blocks action. A thread moves from collected → fix applied → verified → committed → pushed → remote head matched → replied → resolved → confirmed. A failed verification prevents push, reply, and resolution; earlier local fix commits remain local and the failed gate and commit are reported. A failed push, page, cursor, fresh-head query, or SHA comparison leaves threads pending without reply or resolution, with any retained local commit reported. A retry requires full verification, successful push, and fresh matching remote head before reply.

**WorkflowLink**: roadmap-relative link target, spec ID, whether its existing target is verified, and scaffold output path `docs/ai/specs/.process/<SPEC-ID>-workflow.md`. New links point to output. Existing links are preserved only when they resolve to a real workflow file; broken links are rewritten to the actual output.

## Relationships and invariants

A RoadmapEntry owns zero or more SliceBudgets and one GateEvaluation. A PRPacket belongs to a feature directory and receives one Phase 6.5 Verdict. The completion guard checks PostRows in both workflow and state. An executor owns zero or more child receipts. A ReviewThread owns all comments reached through its independent connection. A WorkflowLink belongs to one roadmap entry. Across all entities, the selected spec ID and current PR/packet identity define scope; neighboring entries, packets, and branches cannot supply missing evidence.
