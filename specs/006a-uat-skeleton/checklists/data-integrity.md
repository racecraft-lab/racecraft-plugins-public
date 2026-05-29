# Data Integrity Checklist: Deterministic UAT Runbook Skeleton + PR Body Integration

**Purpose**: Unit-test the *requirements writing* for the script's data-handling guarantees: deterministic overwrite across autopilot resumes, the frozen vendored fixture (no live read of `specs/004`), faithful reproduction of multi-line/nested bullets, the `extract_heading_section()` boundary semantics, and path resolution when the script runs from a worktree. These are where deterministic-overwrite-vs-merge and content-corruption bugs typically land.
**Created**: 2026-05-28
**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md) · [contracts/generate-uat-skeleton-cli.md](../contracts/generate-uat-skeleton-cli.md)
**Domain**: data-integrity · **Audience**: PR reviewer · **Depth**: formal release gate

**Note**: These are "unit tests for the English." Each item is a yes/no quality assertion about the spec/plan/contract — not an implementation task. A checked box means the requirement text already answers the question; an unchecked gap-marked item means it does not, and the item is escalated for consensus.

## Deterministic Overwrite (FR-007)

- [x] CHK001 - Is deterministic overwrite specified explicitly as: no merge with reviewer hand-edits, no append, no skip-if-present? [Completeness, Spec §FR-007]
- [x] CHK002 - Is the run-twice-identical property specified (two runs against an unchanged spec produce byte-identical output)? [Measurability, Spec §FR-007, Spec §US3]
- [x] CHK003 - Is the hand-edit-overwrite scenario specified (a reviewer-edited runbook is overwritten on the next run, not merged)? [Coverage, Spec §US3]
- [x] CHK004 - Is determinism specified against non-deterministic content sources — e.g., is the generation timestamp in the Header reconciled with the byte-identical guarantee (so the timestamp does not silently break run-twice equality)? [Consistency, Spec §FR-010, Spec §FR-007]
- [x] CHK005 - Is it specified that the deterministic-overwrite property holds across autopilot *resumes*, not just back-to-back local runs? [Coverage, Spec §US3]

## Vendored Fixture Stability (no live coupling)

- [x] CHK006 - Is the vendored full-spec fixture specified as a frozen snapshot committed at `fixtures/spec-full-snapshot.md`, read by the test and never read live? [Completeness, Spec §FR-015, Spec §Assumptions]
- [x] CHK007 - Is the rationale for vendoring (live `specs/004` is a moving target once archived/cleaned) recorded so a future maintainer does not "simplify" back to a live read? [Clarity, Design Concept Q4]
- [x] CHK008 - Is it specified which fixtures stay inline (zero-stories, duplicate-FR, clarification-marker, missing-spec) versus vendored (full-spec snapshot), so fixture provenance is unambiguous? [Consistency, Spec §FR-015, Design Concept Q4]
- [x] CHK009 - Is the vendored fixture classified as fixture *data* (excluded from the reviewable-LOC count), so the budget accounting is consistent? [Consistency, Spec §Reviewability Budget, Plan §Reviewability Budget]

## Content Fidelity — Multi-line / Nested Bullets

- [x] CHK010 - Is faithful reproduction of multi-line or nested bullets specified (reproduced verbatim as indented continuation lines, not flattened or joined)? [Completeness, Spec §FR-001]
- [x] CHK011 - Is the nested-bullet fidelity requirement specific enough to be testable (indentation/structure preserved, not collapsed to a single line)? [Measurability, Spec §FR-001]
- [x] CHK012 - Is the interaction between nested-bullet reproduction and the clarification-marker annotation specified (a nested bullet carrying a marker still reproduces its structure)? [Coverage, Spec §FR-001, Spec §FR-005]

## `extract_heading_section()` Boundary Semantics

- [x] CHK013 - Is the heading-section extraction boundary documented — specifically that the closing boundary EXCLUDES the next same-or-higher-level heading line (the section ends before it)? [Completeness, Plan §Decision 1]
- [x] CHK014 - Is the helper's content-mutating behavior documented (it strips blank lines and caps output at 40 lines), so callers know when it is and is NOT a faithful reader? [Clarity, Plan §Decision 1, Plan §Decision 2]
- [x] CHK015 - Is the copy-verbatim decision (vs. sourcing) and its pinned line range recorded with a re-verify step, so the helper cannot silently drift between the two scripts? [Consistency, Spec §FR-002, Plan §Decision 1]
- [x] CHK016 - Is the helper's reuse for the Self-Review echo specified to use the same boundary semantics (the `## Self-Review` block ends at the next H2), so the echo is bounded correctly? [Consistency, Spec §FR-009, Plan §Decision 1]

## Path Resolution (worktree-safe)

- [x] CHK017 - Is path resolution specified so all input paths derive from the caller-supplied argument (feature dir = `dirname argv[1]`; `plan.md` Rollback fallback read from that derived dir), making the script CWD-independent? [Completeness, Contract §Positional arguments, Contract §Side effects]
- [x] CHK018 - Is the worktree scenario addressed — when the script runs from `.worktrees/<branch>` and the spec is passed by path, resolution does not assume a fixed CWD or a 3-digit branch-name regex? [Coverage, Contract §Invocation]
- [x] CHK019 - Is the `--workflow-file` path resolution specified as caller-supplied (absolute or relative to the caller's CWD), distinct from the feature-dir-derived inputs? [Clarity, Contract §Flags, Contract §Side effects]
- [x] CHK020 - Is the output-path resolution specified as exactly `argv[2]` (no implicit relocation into the feature dir), so the caller controls where the file lands? [Clarity, Contract §Positional arguments, Contract §Side effects]

## Read/Write Surface & Side Effects

- [x] CHK021 - Is the complete set of reads specified (`argv[1]` spec; optional `--workflow-file`; optional `plan.md` Rollback fallback; `UAT_PROJECT_COMMANDS` env)? [Completeness, Contract §Side effects]
- [x] CHK022 - Is the write surface specified as exactly one file (`argv[2]`), with no writes to stdout, the spec, git, or any other path? [Completeness, Contract §Side effects]
- [x] CHK023 - Is the Rollback source precedence specified (`## Rollback` from `spec.md`, else `plan.md`, else synthesized stanza), so the fallback chain is deterministic? [Clarity, Spec §FR-012]
- [x] CHK024 - Is the PR-body consumer's read surface specified (`generate-pr-body.sh` reads `<feature-dir>/uat-runbook.md`), consistent with the skeleton's write target? [Consistency, Spec §FR-013, Contract §Consumer contract]

## Acceptance-Criteria Quality for Data Integrity

- [x] CHK025 - Is the deterministic-overwrite property backed by an objective Layer 4 assertion (run twice, compare byte-for-byte)? [Measurability, Spec §FR-015, Plan §Traceability]
- [x] CHK026 - Is the no-live-read property backed by a check that the test reads the vendored snapshot and not `specs/004-integration-verification/spec.md`? [Measurability, Spec §FR-015, Design Concept Q4]
- [x] CHK027 - Is the full-spec story-count fidelity backed by a measurable check (runbook story count equals `grep -c '^### User Story'` on the source)? [Measurability, Spec §SC-001]

## Notes

- CHK013 surfaced a real gap: the plan pinned the helper's line range and its truncation behavior (Decisions 1–2) but never documented the *boundary semantics* — whether the extracted section includes or excludes the next heading. Resolved in-place by extending Plan Decision 1 to record that the closing boundary excludes the next same-or-higher-level heading (verified against the awk `level <= section_level` exit at `generate-pr-body.sh` line 61).
- CHK017/CHK018 surfaced a real gap: path resolution under a worktree was flagged by the domain prompt but not pinned in spec/plan. Resolved in-place by extending Plan Decision 1's helper notes / adding a path-resolution note to the plan stating all feature-relative inputs derive from `dirname argv[1]` (CWD-independent), so a worktree run with a passed-in path resolves correctly and does not depend on SpecKit's 3-digit branch regex.
- CHK004 (timestamp vs. byte-identical) was already reconcilable: the run-twice-identical assertion in the Layer 4 plan implies the timestamp is held constant or excluded from the comparison; recorded here as a consistency check, no edit required.
- All other data-integrity dimensions were already specified across spec.md, plan.md, and the CLI contract. Zero unresolved gap-marked items remain in this domain.
