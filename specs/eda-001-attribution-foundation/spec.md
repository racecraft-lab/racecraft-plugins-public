# Feature Specification: Attribution Foundation

**Feature Branch**: `eda-001-attribution-foundation`
**Created**: 2026-09-25
**Status**: Draft
**Input**: Attribution foundation for 38 `mattpocock/skills` skills, forked to `racecraft-lab/skills` and pinned by `speckit-pro-baseline` at `c55ee46073ed923f86ce59a5eb3b6d895095d1b7`, before EDA-002 through EDA-011 add derivatives.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find the MIT notice and skill inventory (Priority: P1; Slice 1)

As a plugin user or redistributor, I find the complete MIT notice and an inventory of all 38 upstream skills in either installed payload, so I can identify their source and terms.

**Why this priority**: The notice and inventory must be present before derivative content ships.

**Independent Test**: Inspect both installed payloads for the byte-exact notice and the complete pinned inventory.

**Acceptance Scenarios**:

1. **Given** either installed payload, **When** I inspect its upstream reference, **Then** I find unaltered MIT license text and the upstream repository, fork, tag, and commit.
2. **Given** the pinned baseline, **When** I inspect the ledger, **Then** its 38 rows match the 38 upstream paths exactly once in path order, with a disposition and owner for each.
3. **Given** a deliberately ignored or partly absorbed skill, **When** I inspect its row, **Then** I can see why it is ignored or what will not be ported.
4. **Given** the SpecKit Pro repository README, **When** I look for upstream attribution, **Then** I find an acknowledgment of Matt Pocock's work and a working link to the MIT notice.

---

### User Story 2 - Reject missing derivative credits (Priority: P1; Slice 1)

As a maintainer, I mark a ledger row landed and receive a failing attribution check when its destination or credit is missing. A malformed ledger also fails before any row lands.

**Why this priority**: Later specs need an enforceable gate from their first derivative.

**Independent Test**: Run the initial planned ledger and pass/fail landed-row fixtures without marking a real row landed.

**Acceptance Scenarios**:

1. **Given** a valid ledger with no landed rows, **When** attribution validation runs, **Then** it checks all 38 paths and schema rules and passes.
2. **Given** a missing, duplicate, extra, or unordered path or a malformed row, **When** validation runs with no landed rows, **Then** it fails with a useful row or field diagnostic.
3. **Given** a landed row whose declared destination path does not exist, **When** validation runs, **Then** it fails and identifies that row.
4. **Given** a landed row whose derivative file lacks a matching header or whose `SKILL.md` lacks matching `metadata.credits`, **When** validation runs, **Then** it fails; the correctly credited fixture passes.

---

### User Story 3 - Find the transitive Apache notice (Priority: P2; Slice 2)

As a redistributor, I find a separate Apache-2.0 notice for humanlayer `show-me` text copied into upstream `pr`, linked from that row and pinned to a source.

**Why this priority**: The transitive holder needs its own notice before `pr` derivatives land.

**Independent Test**: Inspect each installed payload and test that a missing or malformed link, source pin, or notice fails validation.

**Acceptance Scenarios**:

1. **Given** either installed payload, **When** I follow `pr`'s transitive source, **Then** I find the separate unaltered Apache-2.0 notice crediting Copyright (c) 2024, humanlayer Authors.
2. **Given** the `pr` row, **When** validation runs, **Then** it requires the separate notice and pinned humanlayer source.
3. **Given** the exact copied source cannot be established, **When** the notice is prepared, **Then** a humanlayer repository head is pinned and the exact-source gap is disclosed.

### Edge Cases

- A 38-row ledger with one substituted path still fails against the frozen baseline.
- `IGNORE` cannot carry a destination or status and needs an ignore reason.
- A credit on one file cannot stand in for a different derivative file; a credit with the wrong path, SHA, modified state, or notice fails.
- The MIT notice cannot substitute for the separate humanlayer notice.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Both installed payloads MUST include a Matt Pocock `UPSTREAM-NOTICE.md` under `speckit-pro/skills/speckit-coach/references/upstream/` with byte-exact MIT license text and the pinned upstream repository, fork, tag, and commit.
- **FR-002**: A `ledger.json` beside that notice MUST have one object per upstream skill, exactly 38, ordered by upstream path and pretty-printed with one key per line.
- **FR-003**: Each row MUST contain `upstream_path`, `bucket`, `disposition`, `destination`, `owner_spec`, `not_ported`, and `transitive_sources`, plus its disposition-dependent fields.
- **FR-004**: `disposition` MUST be `ABSORB`, `NEW`, or `IGNORE`. `ABSORB` and `NEW` MUST have a non-null destination and `status` of `planned` or `landed`, with no `ignore_reason`. `IGNORE` MUST have a null destination, no `status`, and a substantive `ignore_reason`.
- **FR-005**: Every row MUST identify its EDA-002 through EDA-011 owner and let a reviewer distinguish absorption, newly authored treatment, and deliberate omission.
- **FR-006**: Exactly `ask-matt`, `wayfinder`, and `triage` MUST have substantive `not_ported` notes; every other row MUST have no omission note. No `PARTIAL` disposition is allowed.
- **FR-007**: Validation MUST compare ledger paths with a frozen 38-path list from commit `c55ee46073ed923f86ce59a5eb3b6d895095d1b7` and reject missing, duplicate, extra, or unordered paths even if no row is landed.
- **FR-008**: Validation MUST reject invalid row fields, types, values, owner references, and disposition-specific combinations before landed-row checks.
- **FR-009**: For every `landed` row, validation MUST require the declared destination to exist and each represented derivative file to carry its own matching file-level credit header.
- **FR-010**: Each derivative header MUST use its file type's comment syntax, appear after frontmatter if present, and identify the upstream skill path or paths, pinned SHA, `Modified derivative: yes`, and the notice path.
- **FR-011**: Each derivative `SKILL.md` MUST additionally have `metadata.credits` consistent with its header.
- **FR-012**: Pass and fail credit-header fixtures MUST exercise landed-row enforcement before a real ledger row lands.
- **FR-013**: Slice 1 MUST deliver the MIT notice, complete ledger, and validation before EDA-002 through EDA-011 add derivatives.
- **FR-014**: Slice 2 MUST deliver `references/upstream/humanlayer-show-me/UPSTREAM-NOTICE.md` in both payloads with a separate byte-exact Apache-2.0 notice and Copyright (c) 2024, humanlayer Authors.
- **FR-015**: Slice 2 MUST link that notice and a pinned humanlayer source from `pr`'s `transitive_sources`; validation MUST reject an absent or malformed required transitive source, notice, or pin.
- **FR-016**: The humanlayer pin MUST identify the exact copied `show-me` source if established; otherwise it MUST use a pinned humanlayer repository head and disclose the unresolved exact-source gap. [NEEDS CLARIFICATION: Which exact humanlayer `show-me` commit and path contain the text copied into upstream `pr`? Search in Clarify Session 1 before using the disclosed head-pin fallback.]
- **FR-017**: The repository test MUST be named `test-upstream-skill-attribution.py`, use only the Python 3.11+ standard library, and never read a `specs/<feature>/` path at run time.
- **FR-018**: Shipped notices and credits MUST contain no shell-specific execution instructions, private home or temporary paths, or machine-specific identifiers. The feature MUST add no derivative content or fork edits.
- **FR-019**: `speckit-pro/README.md` MUST acknowledge Matt Pocock's upstream skills and link directly to the MIT `UPSTREAM-NOTICE.md` included by this feature.

### Reviewability Notes

- Explicit row ownership and credit syntax support independent updates by EDA-002 through EDA-011. No typed reviewability exception is requested.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: harness/adapter; seed/config
- **Projected reviewable LOC**: Approximately 650 across two PRs; refine in Plan after enumerating rows and fixtures.
- **Projected production files**: 3 authored upstream-reference files across both slices.
- **Projected total files**: Approximately 7 authored files, including the test and fixtures; generated payload copies excluded.
- **Budget result**: split required
- **Split decision**: Slice 1 is US1 and US2; Slice 2 is US3 and transitive-source enforcement. Each gets its own PR in the EDA stack. Other roadmap budgets remain untouched.

### PR Review Packet Requirements *(mandatory)*

- Each PR description MUST include what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name its owning EDA-002 through EDA-011 spec or issue.
- Slice 2 MUST state whether the exact humanlayer source was verified or the disclosed head-pin fallback was used.

### Key Entities

- **Upstream skill row**: One pinned path, bucket, disposition, owner, destination or ignore reason, landing status if applicable, omission note, and transitive sources.
- **Upstream notice**: Holder-specific license text with source identity and pin in both installed payloads.
- **Derivative credit**: Per-file provenance header, plus matching metadata for derivative skill entry points.
- **Transitive source**: A pinned source copied into an upstream skill, linked to its own holder's notice.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Redistributors can locate the complete MIT notice and all 38 records in each of two installed payloads.
- **SC-002**: The ledger accounts for 100% of pinned upstream skill paths exactly once, with a reviewable disposition and owner for each.
- **SC-003**: Validation rejects all specified malformed-ledger and missing-credit cases, including zero-landed-row cases, and accepts the valid landed fixture.
- **SC-004**: In Slice 2, redistributors can trace `pr` to one separate Apache-2.0 notice and a pinned humanlayer source in each payload; any fallback is visibly disclosed.
- **SC-005**: Before EDA-002 begins, maintainers can demonstrate one passing and one failing landed-row case without editing the real ledger.
- **SC-006**: The SpecKit Pro README contains one visible upstream acknowledgment with a working link to the MIT notice.

## Assumptions

- The stated 38-skill count and Matt Pocock SHA are authoritative for this spec; implementation extracts the frozen path list from that commit.
- A destination names a derivative file or directory whose authored derivative files each need credit. Later specs mark their rows landed.
- All initial non-`IGNORE` rows are planned; fixtures prove landed behavior.
- The exact humanlayer copied source is unresolved evidence for Slice 2. A head pin with explicit disclosure is the agreed fallback.
- Existing payload builders include the specified upstream reference directory.

## Out of Scope

- Derivative content assigned to EDA-002 through EDA-011; edits to the `racecraft-lab/skills` fork.
- Section-level markers or a `PARTIAL` disposition.
- Changes to other roadmap entries' reviewability budgets.
