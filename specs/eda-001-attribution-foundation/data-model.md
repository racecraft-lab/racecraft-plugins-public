# Data Model: Attribution Foundation

## Upstream skill row

Stored at `speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/ledger.json`. Root shape and exact field/format rules are in [contracts/ledger.md](contracts/ledger.md).

| Field | Type | Relationship/validation |
| --- | --- | --- |
| upstream_path | string | Exact identity in the frozen 38-path inventory; unique and ordered |
| bucket | string enum | Directory immediately after `skills/`; engineering/productivity/misc/in-progress |
| disposition | string enum | ABSORB/NEW/IGNORE; matches frozen roadmap mapping |
| destination | string or null | Planned/landed delivery file or directory; null on IGNORE |
| owner_spec | string | Exactly the frozen owner's identifier for this path |
| status | string enum, conditional | planned/landed on delivery rows; absent on IGNORE |
| ignore_reason | string, conditional | Explanatory nonblank reason on IGNORE; absent on delivery rows |
| not_ported | string or null | Explanatory omission only on ask-matt, wayfinder, triage; null otherwise |
| transitive_sources | array | Typed sources; empty on all final initial rows except pr |

No identifier or field creates a Git-authorship assertion. Destination paths are repository-relative and must not escape the repository. A planned destination may not yet exist; a landed one must exist and select authored files.

## Frozen inventory and owner evidence

`inventory.json` belongs to the durable test fixture directory, independent from the ledger. It records pinned source identity and the exact upstream paths with bucket, disposition, and owner. The upstream tree determines paths; the roadmap determines the following join by unique skill name:

| Owner | Disposition | Names | Count |
| --- | --- | --- | --- |
| EDA-001 | IGNORE | setup-matt-pocock-skills, implement, implement-spec, wizard, git-guardrails-claude-code, claude-handoff, teach, wait-what, loop-me, writing-beats, writing-fragments, writing-shape, migrate-to-shoehorn, scaffold-exercises | 14 |
| EDA-002 | ABSORB | grilling, grill-me, to-questionnaire | 3 |
| EDA-003 | ABSORB | grill-with-docs, domain-modeling | 2 |
| EDA-004 | NEW | prototype | 1 |
| EDA-005 | ABSORB | codebase-design, to-spec, to-tickets, wayfinder, triage | 5 |
| EDA-006 | ABSORB | tdd | 1 |
| EDA-007 | NEW | diagnosing-bugs | 1 |
| EDA-008 | ABSORB | code-review, pr, resolving-merge-conflicts, retro | 4 |
| EDA-009 | ABSORB | ask-matt, handoff, writing-for-agents, setup-ts-deep-modules, setup-pre-commit, research | 6 |
| EDA-010 | NEW | improve-codebase-architecture | 1 |

Total: 38; 21 ABSORB, three NEW, 14 IGNORE. EDA-011 owns no row. Buckets are assigned from exact tree paths, not guessed from names: 18 engineering, seven productivity, four misc, nine in-progress. Implementation must reject any missing or ambiguous path/name join. Planned destinations come from the owning roadmap surface; their final files and credit updates belong to those delivery specs, not EDA-001.

## Transitive source

Contained within a row; no extra root registry is introduced.

| Field | Final initial pr value |
| --- | --- |
| project | humanlayer/skills |
| commit | bba9d13ab34f0a87f1cc33df4dd196372393ddfc |
| path | plugins/show-me/skills/show-me/SKILL.md |
| license | MIT |
| holder | HumanLayer |
| notice_path | speckit-pro/skills/speckit-coach/references/upstream/humanlayer-show-me/UPSTREAM-NOTICE.md |

All six fields are required strings, with no unknown keys. The linked notice carries the exact Copyright (c) 2026 HumanLayer line in its frozen MIT bytes. Slice 1 leaves the array empty; slice 2 establishes and enforces this exact record. The notice is required even while pr remains planned.

## Upstream notice

A holder-specific Markdown file owns source identity and one license block. Matt notice links to the ledger and describes landed content as modified derivatives. HumanLayer notice identifies the exact copied show-me file. Each has one `## License` section and one fenced `text` block; its raw enclosed bytes must equal the corresponding nonempty pinned LICENSE fixture. See [contracts/notices.md](contracts/notices.md).

## Derivative file credit

One header represents a sorted nonempty set of upstream paths. It relates a selected authored file to landed rows, the Matt pin, and the Matt notice. `SKILL.md` adds the matching single quoted-string metadata value. Header syntax and selection rules are in [contracts/credits.md](contracts/credits.md).

## Fixture cases

- `mattpocock-LICENSE.txt`: immutable raw bytes from the baseline fork commit.
- `humanlayer-LICENSE.txt`: immutable raw bytes from the exact HumanLayer commit, added in slice 2.
- `inventory.json`: independent source path/bucket/disposition/owner evidence.
- `valid-ledger.json`: a complete canonical 38-row zero-landed ledger, including the final slice-appropriate transitive state.
- `credit-cases.json`: named synthetic repo-relative destinations/file contents and expected source sets for Markdown with/without frontmatter, SKILL.md, TOML, and Python. Includes shared-file source cases and allowed Python prefixes.

The test constructs targeted negative variants from these independent valid cases in memory. It materializes destination files under a temporary root and asserts diagnostics and positive checked-file counts. No test reads feature planning artifacts, and no fixture expected license is copied from a notice under test.

## Lifecycle

There is no runtime state machine. Static delivery rows begin `planned`; their owning later EDA spec changes them to `landed` only when destination files and credits satisfy validation. IGNORE rows have no status. File regeneration copies authored data without changing its semantic state. Changing a fixture source pin or owner map is an explicit reviewed evidence update, not an automatic acceptance of a changed ledger.
