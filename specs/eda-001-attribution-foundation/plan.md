# Implementation Plan: Attribution Foundation

**Branch**: `eda-001-attribution-foundation` | **Date**: 2026-09-25 | **Spec**: [spec.md](spec.md)

**Input**: `specs/eda-001-attribution-foundation/spec.md`; Phase 3 prompt in `docs/ai/specs/.process/EDA-001-workflow.md`; design concept with its superseding provenance note.

## Summary

Ship a Matt Pocock MIT notice and a closed, canonical 38-row JSON ledger in both plugin payloads. A Python 3.11+ standard-library attribution test checks the inventory, ownership, notices, and file credits even before any real row lands. A second vertical slice adds the exact HumanLayer `show-me` MIT notice and enforces its linkage from `pr`.

The historical Apache notice and repository-head fallback are superseded by completed Clarify Session 1. This plan adds no derivative skill content. EDA-002 through EDA-010 own delivery; EDA-011 owns close-out.

## Technical Context

**Language/Version**: Markdown and UTF-8 JSON content; Python 3.11+ standard-library validation.

**Primary Dependencies**: Existing `unittest`, `json`, and `pathlib`; existing release-artifact and docs reference generators. No new dependency or runtime service.

**Storage**: Authored notices and `ledger.json` under the existing coach references tree; frozen evidence and synthetic cases under the test's own fixtures.

**Testing**: `test-upstream-skill-attribution.py`, registered in `suite-manifest.json`; positive and isolated negative cases; default quick and CI suites.

**Target Platform**: Existing Claude Code and Codex payloads; cross-platform repository Python tooling.

**Project Type**: Plugin reference content and deterministic repository-only contract test.

**Performance Goals**: Offline validation of a fixed 38-row inventory plus authored files selected by landed destinations. No latency or throughput requirement and no network calls in the test.

**Constraints**: Closed JSON fields; fixed formatting; raw license bytes; file-level headers; quoted string metadata; no spec-directory reads in tests; no new packaging or skill-validator behavior; no generated-file hand edits.

**Scale/Scope**: 38 rows, four buckets (18/7/4/9), 14 IGNORE rows, 24 delivery rows, three partial absorptions, two MIT holders, three stories, 19 functional requirements, two PR slices.

**Reviewability Budget**: Primary `docs/process`; secondary `harness/adapter` and `seed/config`. Scoping evidence is 625 estimated LOC with `warn` and two suggested slices; the spec carries approximately 650 LOC. Neither is a measured final diff. This plan enumerates 11 authored implementation files (four production content files, two test/registration files, five fixture files), plus seven Plan artifacts. Generated copies are counted separately after regeneration. The Markdown/JSON reviewability estimator's `not_estimated` is not a within-budget pass. Preserve the two-slice decision and recount each concrete PR before review; no typed budget exception is requested.

## Module and Interface Deltas

- `speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/UPSTREAM-NOTICE.md` — new: source and fork URLs, baseline tag and SHA, modified-derivative explanation, ledger link, and one byte-exact MIT license block (FR-001).
- `speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/ledger.json` — new: closed 38-row interface for later EDA owners and the attribution test; never assigned `merge=generated` (FR-002–FR-008).
- `speckit-pro/skills/speckit-coach/references/upstream/humanlayer-show-me/UPSTREAM-NOTICE.md` — new in slice 2: exact `humanlayer/skills` commit/path and separate HumanLayer MIT block (FR-014–FR-016).
- File-level credit header — new interface for EDA-002–EDA-011: fixed ordered provenance lines, format-specific comments, and loader-safe placement (FR-009–FR-010).
- `SKILL.md` `metadata.credits` — new interface: one quoted string of sorted source identifiers matching the file header; no host display assumption (FR-011).
- `tests/speckit-pro/unit/test-upstream-skill-attribution.py` — new: deterministic schema, inventory, ownership, notice-byte, destination, header, and metadata validation (FR-012, FR-017).
- `tests/speckit-pro/unit/fixtures/upstream-skill-attribution/` — new: holder-specific licenses, frozen inventory/owner evidence, valid zero-landed ledger, and synthetic credit cases. Negative variants are isolated in-memory mutations.
- `tests/speckit-pro/suite-manifest.json` — changed: register the attribution test in the repository's existing unit layer/default dispatch.
- `speckit-pro/README.md` — changed: Matt Pocock acknowledgment linking directly to the authored MIT notice (FR-019).
- `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/` — changed by regeneration: ship notices and ledger through the existing payload inclusion path.
- Docs test and Plugin Authoring Source reference pages — changed by reference regeneration: reflect the new test and README.
- Unchanged grey boxes: `payloads.py`, skill-contract validators, existing skill behavior, fork contents, plugin versions, and other roadmap budgets.

## Declared File Operations

These are implementation declarations, not files written during Plan. The fifth fixture is added only in slice 2. Synthetic Markdown/TOML/Python file bodies are held in `credit-cases.json`, not spread across many new fixture files.

- NEW speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/UPSTREAM-NOTICE.md
- NEW speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/ledger.json
- NEW speckit-pro/skills/speckit-coach/references/upstream/humanlayer-show-me/UPSTREAM-NOTICE.md
- NEW tests/speckit-pro/unit/test-upstream-skill-attribution.py
- NEW tests/speckit-pro/unit/fixtures/upstream-skill-attribution/mattpocock-LICENSE.txt
- NEW tests/speckit-pro/unit/fixtures/upstream-skill-attribution/inventory.json
- NEW tests/speckit-pro/unit/fixtures/upstream-skill-attribution/valid-ledger.json
- NEW tests/speckit-pro/unit/fixtures/upstream-skill-attribution/credit-cases.json
- NEW tests/speckit-pro/unit/fixtures/upstream-skill-attribution/humanlayer-LICENSE.txt
- MODIFIED tests/speckit-pro/suite-manifest.json
- MODIFIED speckit-pro/README.md

Generated payload and docs file operations are regeneration outputs, not independent authored edits. Their exact path/count inventory must come from the actual regeneration receipt rather than guessed copies.

## Constitution Check

Pre-research design check and post-design check both pass for the proposed architecture. These are planning assessments; implementation and release checks have not run in this phase.

| Principle | Design evidence | Implementation verification |
| --- | --- | --- |
| I. Plugin structure | Notices remain within an existing skill's references; repository tests remain outside install-facing plugin content | Layer 1; inspect both regenerated payloads |
| II. Cross-platform safety | Python 3.11+ stdlib, structured JSON and path APIs, raw-byte I/O, no runtime network or shell instructions | Layer 4 and active-path/privacy guards |
| III. Semantic versioning | No authored version changes; release-please remains owner | Layer 1 version check; artifact consistency |
| IV. Test coverage | Frozen inventory plus positive and targeted negative fixture cases; suite-manifest registration | Focused attribution test, quick suite, CI suite |
| V. Conventional commits | Parent owns commits/PRs; final titles use plugin scope, e.g. `feat(speckit-pro): add upstream attribution foundation` | Validate each actual final title and release-note body |
| VI. KISS/YAGNI | One JSON sidecar and one repository test with small local validation seams; no service, new dependency, general YAML parser, or wrapper framework | Code review of each slice |

The reviewability preset warns above 400 reviewable LOC, six production files, 15 total files, or multiple primary surfaces; blocks above 800 LOC, eight production files, 25 total files, or multiple primary surfaces without a ratified split exception. EDA-001 has one primary surface and a scoping LOC warning answered by two vertical slices. The larger enumerated fixture/document footprint replaces the spec's coarse seven-file estimate. Actual generated-file totals remain to be measured; this plan makes no unsupported budget-pass claim.

### Split decision and dependency boundary

| Slice | Stories | Complete behavior | Deferred work |
| --- | --- | --- | --- |
| 1 | US1 + US2 | Matt notice; all 38 canonical rows; zero-landed and synthetic landed validation; test registration; README acknowledgment; regenerated outputs | HumanLayer notice and required exact transitive linkage belong to slice 2 of EDA-001 |
| 2 | US3 | HumanLayer MIT notice and frozen license; exact `pr` transitive entry; missing/malformed notice, pin, and linkage rejection; regenerated outputs | Derivatives remain EDA-002–EDA-010; close-out EDA-011 |

Slice 2 depends on slice 1 and uses the same test. Slice 1 keeps `transitive_sources` as a typed array but does not require a `pr` notice that has not shipped; its arrays start empty. Slice 2 fills `pr` with its one exact source and requires it. This follows the explicitly slice-2 requirements FR-014–FR-016 and prevents a temporarily dangling shipped link. No user-facing flag or conditional runtime policy is introduced. The complete EDA-001 foundation includes both notices before derivative delivery.

Each slice is its own PR in the EDA gh-stack above `docs/engineering-discipline-adoption`. PR creation, branch splitting, gates, and commits are owned by the parent and are not performed by Plan.

### PR review packet source

Use this plan and [quickstart.md](quickstart.md) for what changed, purpose, non-goals, split/budget evidence, verification commands and limitations. Review order: frozen source evidence → notice/license blocks → ledger and its contract → fixture/test failure proofs → registration/README → regeneration receipts. [data-model.md](data-model.md) and the contracts bind requirements to fields and behavior. Record actual red/green and gate outcomes rather than listing intended commands as passes. Known limits: fresh broker documentation was unavailable during Plan; final diff totals and packaging remain unverified. Rollback is the slice's content/test/registration revert followed by regeneration; no flags or migration exist. Later EDA derivatives depend on this foundation, so avoid removing its notice/ledger after dependent work ships.

## Project Structure

### Documentation (this feature)

```text
specs/eda-001-attribution-foundation/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── ledger.md
    ├── credits.md
    └── notices.md
```

`tasks.md` and its execution metadata are later phase outputs, not generated here.

### Source Code (repository root)

```text
speckit-pro/
├── README.md
└── skills/speckit-coach/references/upstream/
    ├── mattpocock-skills/
    │   ├── UPSTREAM-NOTICE.md
    │   └── ledger.json
    └── humanlayer-show-me/
        └── UPSTREAM-NOTICE.md
tests/speckit-pro/
├── suite-manifest.json
└── unit/
    ├── test-upstream-skill-attribution.py
    └── fixtures/upstream-skill-attribution/
        ├── mattpocock-LICENSE.txt
        ├── inventory.json
        ├── valid-ledger.json
        ├── credit-cases.json
        └── humanlayer-LICENSE.txt
```

**Structure Decision**: Existing coach references package the notices and ledger; existing unit tests enforce their contract. Keep expected evidence independent from the ledger being tested. No new production module is needed.

## Phase 0: Research decisions

[research.md](research.md) records resolved source choices, ledger shape, stdlib behavior evidence, fixture independence, metadata limits, and the research-broker outage. Completed spec clarifications settle every design choice; there are no open technical clarifications. Exact license bytes and tree inventory must still be extracted from the pinned sources during implementation, not reconstructed from prose or broker summaries.

## Phase 1: Design and validation flow

1. Freeze the two authoritative license files in their respective slices; extract the 38 upstream paths from the pinned tree and join their names to the roadmap's explicit owner/disposition mapping. Fail extraction if the join is missing, duplicate, or ambiguous.
2. Establish a valid 38-row, zero-landed fixture independently of shipped ledger serialization. Keep initial delivery rows planned. Keep synthetic destination contents within the fixture workspace.
3. Write the failing notice/ledger/header tests before the content they guard, then make the smallest content change that turns each unit green. A test that begins green on absent content does not establish the required red proof.
4. Validate inputs in order: files/bytes/JSON parsing → closed schema and canonical formatting → exact path/bucket/disposition-owner rules → Matt notice bytes → selected landed destinations and credits → slice-2 transitive notice and exact pin.
5. Aggregate landed rows by destination/file, so a shared file is checked once against the sorted complete source set selected by those rows. A directory must select at least one eligible authored file; each selected file needs its own header.
6. Validate SKILL metadata against the same expected sources without depending on host behavior or a general YAML library. Decode only the frontmatter metadata scalar required by the credit contract; test both quoted styles and reject ambiguous duplicates.
7. Run isolated mutations for every guarded defect and assert the relevant diagnostic. Require the inventory count of 38 and a nonzero checked-file count for each positive landed case. Zero real landed rows are legitimate and are not treated as positive file coverage.
8. Register the test, link the README acknowledgment, regenerate both payloads and docs references, and execute the relevant release checks for each slice.

The test's small local seams accept an explicit repository root, fixture root/evidence, and parsed inputs. Synthetic tests use temporary repository-shaped trees; production discovery excludes test fixtures. No new public API or runtime validator is shipped. Exclusion rules and metadata/byte contracts are specified in the supporting contracts; failure messages identify a file/path/field without hiding underlying failures.

## Verification and traceability

| Requirement | Design/changed surface | Required evidence |
| --- | --- | --- |
| FR-001, FR-014 | Holder notices; notice contract | Missing/duplicate/changed fenced blocks fail; raw license bytes match; both payload copies present |
| FR-002–FR-008 | Ledger; inventory/owner fixture; ledger contract | Valid zero-landed pass; targeted inventory/schema/owner/format failures |
| FR-009–FR-011 | Credits contract; synthetic cases | Markdown/TOML/Python positive passes; empty destination and header/metadata defects fail |
| FR-012, FR-017 | Stdlib attribution test and fixtures | Nonzero positive selections; isolated diagnostic assertions; no runtime spec reads |
| FR-013 | Slice 1 | Complete foundation validation precedes derivative work |
| FR-015–FR-016 | Slice 2 `pr` entry and HumanLayer fixture | Required source pin, holder, license, path, and separate notice rejection proofs |
| FR-018 | Notices and credits | Active-path/privacy checks; no derivative/fork edits |
| FR-019 | README | Visible acknowledgment and resolved notice link |

[quickstart.md](quickstart.md) supplies runnable validation scenarios and required suite/artifact/docs checks. No implementation verification is claimed here. Formal modeling is not applicable: static authored files and deterministic validation introduce no state machine or concurrency.

## Complexity Tracking

No architecture or constitution violation needs an exception. The existing estimate warning is addressed by the explicit two-slice plan; final budget verification remains a later gate obligation.
