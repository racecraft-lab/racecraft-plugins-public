# Contract: Upstream Attribution Ledger

**Consumers**: Attribution test and EDA-002–EDA-011 maintainers. **Requirements**: FR-002–FR-008, FR-015–FR-016.

## Closed shape

Root is exactly an object with the key `entries`, whose value is an array of 38 objects. Reject missing/extra root keys, invalid JSON, duplicate keys at any object level, non-finite values, non-object rows, and wrong field types before landed checks.

Every row requires `upstream_path`, `bucket`, `disposition`, `destination`, `owner_spec`, `not_ported`, and `transitive_sources`. Add exactly `status` for ABSORB/NEW, or exactly `ignore_reason` for IGNORE. Reject every other key and contradictory conditional keys.

| Condition | Rule |
| --- | --- |
| Path | Exact frozen `skills/<bucket>/<skill>/SKILL.md`; each appears once |
| Bucket | engineering/productivity/misc/in-progress; equals pinned path component |
| ABSORB or NEW | Nonempty repository-relative destination; planned/landed status; no ignore_reason |
| IGNORE | Null destination; no status; nonblank explanatory ignore_reason |
| Ownership | Exact frozen path-to-owner mapping; delivery EDA-002–EDA-010, IGNORE EDA-001, no EDA-011 row |
| Partial absorption | Nonblank explanatory not_ported for exactly ask-matt/wayfinder/triage; null elsewhere |
| Transitive sources | Array of closed six-string-field objects; final initial pr has its one pinned source; others empty |

Substantive reason/omission text means an actual explanatory statement, with deterministic rejection of missing, empty, whitespace-only, or wrong-type values. Review verifies that the prose explains the roadmap decision; the test does not invent an LLM-based semantic grader.

Repository-relative path strings use forward slashes, name a file/directory beneath the supplied repository root, and do not contain parent traversal or absolute paths, home prefixes, or temporary prefixes. Planned paths are not required to exist. Resolved landed paths must remain within the repository. Later specs own any new destination contents.

## Canonical bytes

- UTF-8 without a byte-order mark, LF line endings, two-space indentation, one final newline, no trailing spaces.
- Rows sorted lexicographically by full upstream_path.
- Present row keys ordered: upstream_path, bucket, disposition, destination, owner_spec, status or ignore_reason, not_ported, transitive_sources.
- Transitive object keys ordered: project, commit, path, license, holder, notice_path.
- Root key order consists solely of entries.
- Canonical serialization uses the specified order and UTF-8 literal text, with JSON string escaping performed by the standard-library serializer. Comparison is against original bytes, not a normalized text copy.

Ordinary text merge behavior applies. The ledger must never acquire the generated merge driver. A change to one row must preserve the order and formatting of all other rows.

## Frozen membership and ownership

Exact inventory equality and ordering are required in addition to length 38. Assert nonzero inventory and row counts before success. Bucket totals 18/7/4/9 corroborate the exact inventory; a substituted path must fail even when the total remains 38. The ownership/disposition mapping in [data-model.md](../data-model.md) is frozen alongside tree paths. Reject a valid-looking but wrong owner identifier even at zero landed rows.

## Slice-2 pr source

The complete initial pr row contains exactly one transitive object:

| Key | Value |
| --- | --- |
| project | humanlayer/skills |
| commit | bba9d13ab34f0a87f1cc33df4dd196372393ddfc |
| path | plugins/show-me/skills/show-me/SKILL.md |
| license | MIT |
| holder | HumanLayer |
| notice_path | speckit-pro/skills/speckit-coach/references/upstream/humanlayer-show-me/UPSTREAM-NOTICE.md |

Require this record and its valid notice in slice 2 regardless of status. Reject missing/empty/duplicate records, unknown fields, wrong types, wrong pins, different repositories or source paths, altered license/holder identifiers, and missing or wrong notice paths. Initial other rows must have empty arrays. Slice 1 checks the array schema but leaves linkage establishment/enforcement to slice 2, as FR-014–FR-016 explicitly require.

## Failure contract

The test exits nonzero on each defect. A schema error names the input file and row index/path where available, plus the field. Inventory errors identify missing/extra/duplicate/out-of-order paths; byte-format errors identify the ledger. No malformed input is silently coerced, skipped, or rewritten by validation. Negative tests assert the targeted diagnostic, not merely an arbitrary exception.
