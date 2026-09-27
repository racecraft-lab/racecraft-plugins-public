# Research: Attribution Foundation

## Evidence boundary

The completed spec's three Clarify sessions and the design concept's superseding provenance note are the authoritative scoping evidence. Research broker searches during Plan returned `search_unavailable` because no Tavily key was available. Documentation queries returned `fetch_failed`/`rate_limited`; zero fresh official-source chunks were obtained. No alternative research tool was used by this phase executor. The coordinator separately supplied live official-document verification: Python 3.11 json documents ordered object_pairs_hook and parse_constant rejection of NaN/Infinity; Agent Skills requires metadata string keys and values; Claude Code accepts free-form metadata without acting on its contents. This coordinator-supplied evidence is distinct from the zero worker-broker chunks. It supports the selected interfaces; it does not verify the implementation. Other upstream links below retain the completed Clarify evidence boundary.

A local Python 3.11 experiment passed duplicate-key rejection through `object_pairs_hook`, non-finite rejection through `parse_constant`, explicit JSON byte serialization, and `Path.read_bytes()` preservation of CRLF versus LF. It changed no repository source. Detailed metadata parsing and full validator behavior remain implementation/TDD obligations.

## Decision 1: Exact holder-specific MIT sources

**Decision**: Matt notice uses the fork's `LICENSE` at `c55ee46073ed923f86ce59a5eb3b6d895095d1b7` (`speckit-pro-baseline`); HumanLayer notice uses `humanlayer/skills` `LICENSE` at `bba9d13ab34f0a87f1cc33df4dd196372393ddfc`, paired with `plugins/show-me/skills/show-me/SKILL.md` at the same commit.

**Rationale**: Clarify Session 1 located the exact copied work and records the operator's MIT decision. Two holders retain separate notices. Freeze raw file bytes during implementation; neither a search snippet nor a generic MIT template is a license-byte fixture.

**Alternatives considered**: The separate `humanlayer/humanlayer` Apache license and repository-head fallback are superseded, not viable source pins for this copy.

**Recorded primary evidence**: [upstream pr](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/in-progress/pr/SKILL.md), [credits](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/in-progress/pr/CREDITS.md), [exact show-me](https://github.com/humanlayer/skills/blob/bba9d13ab34f0a87f1cc33df4dd196372393ddfc/plugins/show-me/skills/show-me/SKILL.md), [HumanLayer LICENSE](https://github.com/humanlayer/skills/blob/bba9d13ab34f0a87f1cc33df4dd196372393ddfc/LICENSE), [fork LICENSE](https://github.com/racecraft-lab/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/LICENSE).

## Decision 2: Closed canonical JSON, ordinary text merges

**Decision**: Root contains only `entries`. Explicitly validate required and allowed fields, exact types, disposition branches, ownership, path order, bucket counts, and raw formatting. Parse ordered pairs to reject duplicate JSON keys before building mappings. Reject non-finite constants. Serialize ordered fields with two-space indentation, UTF-8, LF, and one final newline; compare to original bytes.

**Rationale**: Closed inputs prevent malformed zero-landed states from escaping checks. The local stdlib experiment verifies the parser hooks and byte behavior. A fixed row/key order makes independent row edits reviewable without altering the generated merge driver.

**Alternatives considered**: Markdown ledger (weak machine interface and adjacent-row conflicts), JSON Schema dependency (unneeded), generated merge driver (drops independently authored row updates), normalizing input before checking it (conceals malformed formatting).

**Documentation references**: [Python json](https://docs.python.org/3.11/library/json.html), [pathlib](https://docs.python.org/3.11/library/pathlib.html).

## Decision 3: Independent frozen inventory and owner map

**Decision**: Extract the exact 38 `skills/<bucket>/<name>/SKILL.md` paths from the pinned tree; join to the roadmap Disposition Summary to freeze path, bucket, disposition, and owner in `inventory.json`. Freeze a separate complete valid zero-landed ledger fixture. Do not derive expected paths or owners from the mutable ledger under test.

**Rationale**: Session 2 establishes 18/7/4/9 bucket counts and 14 IGNORE owners. Count checks supplement exact set/order checks. Duplicate names or unmatched mapping rows fail extraction rather than invite inference.

**Alternatives considered**: Count-only checks, broad EDA identifier regexes, and runtime roadmap/spec reads fail to prove exact coverage or survive spec archival.

**Recorded primary evidence**: [pinned upstream tree](https://api.github.com/repos/mattpocock/skills/git/trees/c55ee46073ed923f86ce59a5eb3b6d895095d1b7?recursive=1); `docs/ai/specs/engineering-discipline-adoption-technical-roadmap.md`, Disposition Summary.

## Decision 4: Byte-exact license sections

**Decision**: Locate the sole `## License` section and its sole fenced `text` block using raw bytes. Compare only enclosed bytes, retaining the final license newline. Missing/duplicate sections or blocks and any altered byte fail.

**Rationale**: Session 3 specifies the exact extraction contract. The existing Quint test's `seen > 0` guard is the local non-vacuity precedent; the gallery's substring license assertion is insufficient. Keep surrounding source prose editable without weakening license content equality.

**Alternatives considered**: Substring checks, stripped text, newline-normalizing text reads, or retyping an MIT template.

## Decision 5: File header and quoted metadata, no host assumption

**Decision**: Check one ordered file-level header in Markdown/TOML/Python, plus matching quoted YAML `metadata.credits` in derivative SKILL.md files. A small stdlib recognizer extracts this designated mapping/scalar; it must support the specified quoted forms, reject duplicates/ambiguity, and compare decoded identifiers to the header. It does not claim to validate all YAML or replace existing skill-contract validators.

**Rationale**: Session 3 explicitly makes credits a string; host display is outside the requirement. The expected identifiers use fixed repository/commit/path components and sorted `; ` joins. Place Markdown comments after frontmatter to preserve loader entry syntax. Parser behavior is proved through targeted implementation fixtures rather than claimed verified now.

**Alternatives considered**: Section-level markers (operator declined), metadata arrays (violates string contract), host-visible display guarantees (unsupported), general YAML dependency (outside stdlib scope).

**Recorded primary evidence**: [Agent Skills metadata specification](https://agentskills.io/specification), cited by Clarify Session 3 and live-verified separately by the coordinator; [Claude Code metadata](https://code.claude.com/docs/en/skills), likewise coordinator-verified. [YAML quoted scalar specification](https://yaml.org/spec/1.2.2/#73-flow-scalar-styles) is a reference for later broker verification, not a fetched source in this phase.

## Decision 6: Complete fixtures and ordered slices

**Decision**: Slice 1 proves zero-landed inventory/schema and positive synthetic landed Markdown/TOML/Python cases; slice 2 adds the pinned HumanLayer license and exact required `pr` entry. Keep synthetic file content in one `credit-cases.json` and materialize cases in temporary repository-shaped trees. Negative tests mutate one guarded condition at a time and assert its diagnostic.

**Rationale**: A legitimate zero-real-landed state still checks 38 rows and the Matt notice. Each positive synthetic landed case selects files and asserts a nonzero checked count; an empty eligible directory fails. Slice-2-only linkage does not create a missing notice requirement in the independently reviewable first slice.

**Alternatives considered**: Defer credit checks until real derivatives (vacuity), reject zero real landed rows (breaks foundation), skip malformed required sources when absent (fails closed-contract purpose), one large PR (contradicts Q8).

## Open design questions

None. Source-byte harvesting, complete positive/negative validator execution, final slice totals, and regenerated packaging are unperformed implementation verification. Broker availability remains a recorded limitation and must not be described as a successful documentation search.
