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

### User Story 3 - Find the separate HumanLayer notice (Priority: P2; Slice 2)

As a redistributor, I find a separate MIT notice for HumanLayer `show-me` text copied into upstream `pr`, linked from that row and pinned to the identified source.

**Why this priority**: The transitive holder needs its own notice before `pr` derivatives land.

**Independent Test**: Inspect each installed payload and test that a missing or malformed link, source pin, or notice fails validation.

**Acceptance Scenarios**:

1. **Given** either installed payload, **When** I follow `pr`'s transitive source, **Then** I find the separate unaltered MIT notice crediting Copyright (c) 2026 HumanLayer.
2. **Given** the `pr` row, **When** validation runs, **Then** it requires the separate notice and pinned humanlayer source.
3. **Given** the identified `show-me` source, **When** the notice is prepared, **Then** it records the exact `humanlayer/skills` commit and path rather than the retired repository-head fallback.

### Edge Cases

- A 38-row ledger with one substituted path still fails against the frozen baseline.
- `IGNORE` cannot carry a destination or status and needs an ignore reason.
- A credit on one file cannot stand in for a different derivative file; a credit with the wrong path, SHA, modified state, or notice fails.
- The MIT notice cannot substitute for the separate humanlayer notice.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Both installed payloads MUST include a Matt Pocock `UPSTREAM-NOTICE.md` under `speckit-pro/skills/speckit-coach/references/upstream/` with the pinned upstream repository, fork, tag, and commit. Its sole `## License` section MUST contain exactly one fenced `text` block whose enclosed raw bytes, including the final newline, equal the frozen upstream MIT LICENSE fixture; missing, duplicate, or altered blocks fail validation.
- **FR-002**: A `ledger.json` beside that notice MUST be a JSON object with only an `entries` array of exactly 38 row objects, sorted lexicographically by full `upstream_path`. It MUST use UTF-8, LF line endings, two-space indentation, one final newline, and a fixed order for present row keys: `upstream_path`, `bucket`, `disposition`, `destination`, `owner_spec`, `status` or `ignore_reason`, `not_ported`, `transitive_sources`. Each key occupies its own line; a row flip changes only that row.
- **FR-003**: Each row MUST contain string `upstream_path`, `bucket`, `disposition`, and `owner_spec`; `destination` as a repository-relative path string or `null`; `not_ported` as a substantive string or `null`; and `transitive_sources` as an array, plus its disposition-dependent fields. `bucket` MUST be `engineering`, `productivity`, `misc`, or `in-progress`, matching the directory immediately after `skills/` in its pinned `upstream_path`. Each transitive source MUST contain only string `project`, `commit`, `path`, `license`, `holder`, and `notice_path` keys. The root, rows, and transitive sources MUST reject unknown keys.
- **FR-004**: `disposition` MUST be `ABSORB`, `NEW`, or `IGNORE`. `ABSORB` and `NEW` MUST have a non-null destination and `status` of `planned` or `landed`, with no `ignore_reason`. `IGNORE` MUST have a null destination, no `status`, and a substantive `ignore_reason`.
- **FR-005**: Every row MUST identify exactly one `owner_spec` matching a frozen, exact `upstream_path`-to-owner mapping derived from the roadmap Disposition Summary and stored with the durable attribution test or its fixtures. The 14 `IGNORE` rows belong to EDA-001; `ABSORB` and `NEW` rows belong to their assigned EDA-002 through EDA-010 delivery specs; EDA-011 owns no row and performs close-out. Validation MUST reject a mismatched owner even when no row is landed. This checks declared ownership, not Git branch or commit authorship.
- **FR-006**: Exactly `ask-matt`, `wayfinder`, and `triage` MUST have substantive `not_ported` strings; every other row MUST set `not_ported` to `null`. No `PARTIAL` disposition is allowed.
- **FR-007**: Validation MUST compare each ledger path and bucket with a frozen 38-path inventory from commit `c55ee46073ed923f86ce59a5eb3b6d895095d1b7`, rejecting missing, duplicate, extra, unordered, or misbucketed paths even if no row is landed. The inventory has 18 `engineering`, 7 `productivity`, 4 `misc`, and 9 `in-progress` paths; those counts do not replace the exact path checks.
- **FR-008**: Validation MUST reject invalid root or row fields, types, values, owner references, disposition-specific combinations, and noncanonical ordering or formatting before landed-row checks. A missing ledger or unparseable ledger JSON MUST fail before row checks with a nonzero result naming the ledger file and the input defect. Every guarded defect MUST produce a nonzero result naming the affected file and, where available, the row/path and failed field; input failures before row parsing MUST NOT invent a row identity or silently skip validation.
- **FR-009**: For every `landed` row, validation MUST require the declared destination to exist. A file destination checks that file; a directory destination recursively checks every authored `.md`, `.toml`, and `.py` file beneath it and fails if that eligible set is empty. Generated files, vendored files, test fixtures, and attribution notices are excluded. Every checked derivative file MUST carry its own matching file-level credit header.
- **FR-010**: Each derivative header MUST have these exact lines in order: `Upstream repository: mattpocock/skills`; one `Upstream skill: <upstream_path>` line per represented row in sorted path order; `Pinned commit: c55ee46073ed923f86ce59a5eb3b6d895095d1b7`; `Modified derivative: yes`; and `License notice: speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/UPSTREAM-NOTICE.md`. Wrap them in one HTML comment for Markdown, or prefix each line with `# ` for TOML and Python. Put the header in the first nonblank body block after Markdown frontmatter, if any; Python may place a shebang and encoding declaration before it. When present, Markdown frontmatter MUST remain the first content, before the header. Validation MUST reject absent, misplaced, wrong-syntax, or mismatched fields.
- **FR-011**: Each derivative `SKILL.md` MUST include `metadata.credits` as one quoted YAML string. For each represented source, it MUST contain `mattpocock/skills@c55ee46073ed923f86ce59a5eb3b6d895095d1b7:<upstream_path>`; multiple entries MUST be sorted by upstream path and joined with `; `. The value MUST match the file credit header. Repository validation enforces this format; no host display or interpretation of `credits` is required.
- **FR-012**: Fixtures MUST demonstrate a valid 38-row zero-landed ledger and positive landed Markdown, TOML, and Python cases, including SKILL.md metadata. Isolated negative cases MUST cover missing or empty destinations; absent, misplaced, wrong-syntax, or mismatched headers; missing or mismatched metadata credits; malformed ledger inventory, schema, bucket, or owner; and missing, duplicate, or byte-altered MIT blocks. In-memory mutations MAY keep fixtures small, but each case MUST assert its targeted failure, each positive landed case MUST check at least one file, and the complete inventory MUST be 38 rows. Isolated negatives MUST also cover a missing required notice file, missing ledger file, and unparseable ledger JSON, asserting the affected filename and input defect. Frontmatter-bearing Markdown and SKILL.md fixtures MUST pass with the header as the first nonblank body block after closed frontmatter and fail with the header before or inside frontmatter, after body text, or with unclosed frontmatter; placement failures MUST identify the landed row, selected file, and placement defect.
- **FR-013**: Slice 1 MUST deliver the MIT notice, complete ledger, and validation before EDA-002 through EDA-011 add derivatives.
- **FR-014**: Slice 2 MUST deliver `references/upstream/humanlayer-show-me/UPSTREAM-NOTICE.md` in both payloads with the pinned source identity, including the public URL `https://github.com/humanlayer/skills/blob/bba9d13ab34f0a87f1cc33df4dd196372393ddfc/plugins/show-me/skills/show-me/SKILL.md` to the exact copied source, and exactly one `## License` fenced `text` block whose enclosed raw bytes, including the final newline, equal the frozen MIT LICENSE from `humanlayer/skills@bba9d13ab34f0a87f1cc33df4dd196372393ddfc/LICENSE` with Copyright (c) 2026 HumanLayer.
- **FR-015**: Slice 2 MUST put the pinned `humanlayer/skills` source in `pr`'s `transitive_sources` as one entry with `project`, `commit`, `path`, `license`, `holder`, and `notice_path`; all other initial rows have an empty array. Validation MUST reject an absent or malformed required transitive source, MIT license identification, notice, or pin.
- **FR-016**: The `pr` transitive-source entry MUST identify `humanlayer/skills` at commit `bba9d13ab34f0a87f1cc33df4dd196372393ddfc`, path `plugins/show-me/skills/show-me/SKILL.md`, as the exact copied `show-me` source.
- **FR-017**: The repository test MUST be named `test-upstream-skill-attribution.py`, use only the Python 3.11+ standard library, and never read a `specs/<feature>/` path at run time.
- **FR-018**: Shipped notices and credits MUST contain no shell-specific execution instructions, private home or temporary paths, or machine-specific identifiers. The feature MUST add no derivative content or fork edits.
- **FR-019**: `speckit-pro/README.md` MUST acknowledge Matt Pocock's upstream skills and link directly to the MIT `UPSTREAM-NOTICE.md` included by this feature.

### Reviewability Notes

- Fixed row order and formatting keep distinct row edits reviewable and usually text-mergeable; stacked branches may still need rebasing. Credit syntax supports later EDA updates. No typed reviewability exception is requested.

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
- Slice 2 MUST identify the verified `humanlayer/skills` source commit and path and the separate MIT notice.

### Key Entities

- **Upstream skill row**: One pinned path, bucket, disposition, owner, destination or ignore reason, landing status if applicable, omission note, and transitive sources.
- **Upstream notice**: Holder-specific license text with source identity and pin in both installed payloads.
- **Derivative credit**: Per-file provenance header, plus matching metadata for derivative skill entry points.
- **Transitive source**: A pinned source copied into an upstream skill, linked to its own holder's notice.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Redistributors can locate the complete MIT notice and all 38 records in each of two installed payloads.
- **SC-002**: The ledger accounts for 100% of pinned upstream skill paths exactly once, with a reviewable disposition and owner for each.
- **SC-003**: Validation rejects all specified malformed-ledger, missing-credit, and license-byte cases, including zero-landed-row cases and empty destination selections, and accepts the valid Markdown, TOML, and Python landed fixtures.
- **SC-004**: In Slice 2, redistributors can trace `pr` to one separate MIT notice and the exact pinned `humanlayer/skills` source in each payload.
- **SC-005**: Before EDA-002 begins, maintainers can demonstrate one passing and one failing landed-row case without editing the real ledger.
- **SC-006**: The SpecKit Pro README contains one visible upstream acknowledgment with a working link to the MIT notice.

## Assumptions

- The stated 38-skill count and Matt Pocock SHA are authoritative for this spec; implementation extracts the frozen path list from that commit.
- A destination names a derivative file or directory whose authored derivative files each need credit. Later specs mark their rows landed. The test freezes the upstream path, bucket, and owner mapping under its own fixtures and never reads a temporary feature spec at run time.
- All initial non-`IGNORE` rows are planned; fixtures prove landed behavior.
- The exact copied `show-me` source was located in `humanlayer/skills`; the repository-head fallback is not needed for this source.
- Existing payload builders include the specified upstream reference directory.

## Clarifications

### Session 1: Provenance — resolved

- The pinned upstream `pr` skill credits `humanlayer/skills/plugins/show-me/skills/show-me/SKILL.md`; its adjacent credits say the text was reproduced almost word for word. That file exists at commit `bba9d13ab34f0a87f1cc33df4dd196372393ddfc`, before the upstream copy commit. The exact-source fallback is retired.
- The identified source repository's `LICENSE` at that commit is MIT, Copyright (c) 2026 HumanLayer. The 15-line Apache-2.0 header belongs to a separate repository, `humanlayer/humanlayer`, at the previously proposed head pin.
- The operator answered `MIT` in the active Codex chat. The feature keeps two notices: Matt Pocock's MIT notice and a separate HumanLayer MIT notice from the identified source repository. The earlier Apache-2.0 premise and repository-head fallback are superseded.
- Primary evidence: [upstream `pr` metadata](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/in-progress/pr/SKILL.md), [upstream credits](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/in-progress/pr/CREDITS.md), [exact `show-me` source](https://github.com/humanlayer/skills/blob/bba9d13ab34f0a87f1cc33df4dd196372393ddfc/plugins/show-me/skills/show-me/SKILL.md), [its MIT LICENSE](https://github.com/humanlayer/skills/blob/bba9d13ab34f0a87f1cc33df4dd196372393ddfc/LICENSE), and [the separate Apache LICENSE](https://github.com/humanlayer/humanlayer/blob/99abe673498cf8bdcd5f989aebe9406a27185b3b/LICENSE).

### Session 2: Ledger contract — resolved

- `ledger.json` has a closed `entries` root, typed rows, fixed key order, two-space indentation, LF line endings, and one final newline. `IGNORE` has `destination: null`, omits `status`, and requires an `ignore_reason`; the three partial absorptions have substantive `not_ported` strings and all other rows use `null`.
- The pinned upstream tree contains 38 `SKILL.md` paths in four buckets: 18 `engineering`, 7 `productivity`, 4 `misc`, and 9 `in-progress`. Each ledger bucket must match the directory immediately after `skills/` in its exact pinned path. [Pinned tree](https://api.github.com/repos/mattpocock/skills/git/trees/c55ee46073ed923f86ce59a5eb3b6d895095d1b7?recursive=1).
- `owner_spec` is checked against a frozen path-to-owner mapping: 14 `IGNORE` rows are EDA-001; other rows use their roadmap delivery owner in EDA-002–EDA-010. EDA-011 verifies close-out and owns no row. This validates the declaration, not Git authorship.
- Distinct row edits remain reviewable and can text-merge, while stacked branches may still require rebasing. The ledger stays outside the generated merge driver.

### Session 3: Test and credit header — resolved

- Every derivative file uses one fixed-order file-level header with repository, sorted source paths, pinned SHA, `Modified derivative: yes`, and the repo-relative notice path. Markdown wraps the lines in one HTML comment after frontmatter; TOML and Python use `# ` lines, with Python shebang and encoding declaration allowed first.
- A derivative `SKILL.md` additionally uses one quoted string at `metadata.credits`: `mattpocock/skills@c55ee46073ed923f86ce59a5eb3b6d895095d1b7:<upstream_path>` per source, sorted and separated by `; `. This is a repository-checked string field, not a host presentation requirement. The [Agent Skills specification](https://agentskills.io/specification) defines metadata as string keys to string values; [Claude Code skills documentation](https://code.claude.com/docs/en/skills) accepts the metadata map without acting on its contents.
- Each notice has exactly one `## License` fenced `text` block. The validator compares only the enclosed raw bytes, including the last newline, to its own frozen MIT LICENSE fixture and rejects missing, duplicate, or changed blocks.
- Positive zero-landed and landed-file cases, plus isolated targeted negative mutations, prove that the inventory, destination selection, header, metadata, and license checks cannot pass on an empty set.

## Out of Scope

- Derivative content assigned to EDA-002 through EDA-011; edits to the `racecraft-lab/skills` fork.
- Section-level markers or a `PARTIAL` disposition.
- Changes to other roadmap entries' reviewability budgets.
