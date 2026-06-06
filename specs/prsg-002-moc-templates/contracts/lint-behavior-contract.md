# Contract: Version-gated lint behavior

Behavior contract for the two Layer-1 lints. Owned by FR-009 .. FR-016 + FR-019. Both lints are runtime-agnostic bash scripts under `speckit-pro/tests/layer1-structural/`, wired into `tests/run-all.sh`, exercised by committed fixtures, and dogfooded against this repo's real spec trees.

## Shared preconditions (both lints)

- **MOC identification (v1)**: a file is a MOC iff its filename is exactly `SPEC-MOC.md`.
- **Version gate**: a spec is checkable iff its `SPEC-MOC.md` carries `structureVersion >= 1` (the v1 shipped version). The literal `1` is hardcoded in each lint with a "keep in sync" comment (mirrors the scaffold's stamped literal; no shared version file).
- **Exempt → SKIP (no violation)**: spec dir with no `SPEC-MOC.md`; or a marker with no `structureVersion`; or `structureVersion < 1`. `.process/**` is exempt.
- **Scan roots (dogfooded)**: `docs/ai/specs/` and `specs/` at repo root. Repo root is resolved from the test dir via the established idiom `REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"`.
- **Exit semantics**: any violation in a version-gated spec → exit nonzero (hard fail). No violations among checkable specs → exit success.

## Division of labor (no overlap, no gap)

| Concern | Owner |
|---------|-------|
| `up:` is **present, non-empty, well-formed** relative `[]()` link (not a wikilink) | **orphan lint** (FR-009) |
| `up:` requirement applies to **MOC files only** (not `spec.md`/`plan.md`/`tasks.md`/`contracts/**`) | **orphan lint** (FR-010) |
| `up:` target **resolves** to an existing file | **stale-index lint** (FR-011) |
| **every** relative `[]()` target resolves (the `up:` value + any body links) | **stale-index lint** (FR-011) |
| any `[[wikilink]]` inside a MOC is a violation in its own right | **stale-index lint** (FR-012) |
| `spec_id` namespace-matches the containing directory | **spec_id check** (FR-019) — see `id-normalization-grammar.md` |

Net effect: a dangling `up:` is caught by stale-index (resolution), and a missing/malformed `up:` is caught by orphan (presence/form). Together they guarantee "every version-marked map reaches its parent" end-to-end.

## Orphan lint (`validate-moc-orphan.sh`)

- For each version-gated `SPEC-MOC.md`: assert `up:` is present, non-empty, and a well-formed relative `[]()` link (reject `[[wikilink]]` form here too as "not well-formed relative link"). Does NOT resolve the target (that is stale-index's job).
- Does NOT require `up:` on non-MOC docs. `.process/**` exempt.

## Stale-index lint (`validate-moc-stale-index.sh`)

- For each version-gated MOC: collect every relative `[]()` link target — **including the frontmatter `up:` value** plus any body links — and assert each resolves to an existing file (resolved relative to the MOC file's own directory).
- Assert no `[[wikilink]]` appears anywhere in the MOC; any wikilink is a violation.

## Acceptance mapping

- US2 AC-1 → orphan lint fails on version-marked MOC with no valid `up:`.
- US2 AC-2 → stale-index fails on version-marked MOC with a non-resolving relative link.
- US2 AC-3 → stale-index fails on version-marked MOC containing a `[[wikilink]]`.
- US2 AC-4 → no-marker (or no-`structureVersion`) spec is silently skipped.
- US2 AC-5 → orphan does NOT require `up:` on non-MOC docs.
- US2 AC-6/7 → `spec_id` check distinguishes `(prsg,002)` from `(spec,002)`, and `013a` from `013a1`.
- US2 AC-8 → full run is green on first adoption (all legacy specs lack the marker → skipped).
