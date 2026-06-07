# Contract: Version-gated lint behavior

Behavior contract for the two Layer-1 lints. Owned by FR-009 .. FR-016 + FR-019. Both lints are runtime-agnostic bash scripts under `speckit-pro/tests/layer1-structural/`, wired into `tests/run-all.sh`, exercised by committed fixtures, and dogfooded against this repo's real spec trees.

## Shared preconditions (both lints)

- **MOC identification (v1)**: a file is a MOC iff its filename is exactly `SPEC-MOC.md`.
- **Version gate**: a spec is checkable iff its `SPEC-MOC.md` carries `structureVersion >= 1` (the v1 shipped version). The literal `1` is hardcoded in each lint with a "keep in sync" comment (mirrors the scaffold's stamped literal; no shared version file).
- **Exempt → SKIP (no violation)**: spec dir with no `SPEC-MOC.md`; or a marker with no `structureVersion`; or `structureVersion < 1`; or a `structureVersion` that is not a bare integer (a quoted string `"1"`, a decimal `1.0`, or non-numeric text is treated identically to absence — the gate fires only on an unambiguous integer `>= 1`); or a marker with no `---` frontmatter fence / unparseable frontmatter (no readable `structureVersion` → treated as absent, FR-021); or an UNREADABLE marker (permission denied → skipped with a stderr warning, never a content violation, FR-021/FR-023). `.process/**` is exempt. The version-gate read MUST be **total** — a garbled marker never crashes the lint into an undistinguished nonzero exit.
- **Exempt-before-content invariant (FR-023)**: the exempt/skip decision is evaluated BEFORE any read of a spec's body content, so a grandfathered legacy spec can NEVER cause a nonzero exit regardless of its content (load-bearing safety property behind SC-002).
- **Scan roots (dogfooded)**: `docs/ai/specs/` and `specs/` at repo root. Repo root is resolved from the test dir via the established idiom `REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"`. A scan root that does not exist or is empty is SKIPPED (not an error) — the lints scan whichever trees exist, so they run cleanly in a consuming project lacking one or both (FR-022).
- **Exit semantics (3-way enum, FR-020)**: `0` = clean (no violations among checkable specs, including a scan that finds zero version-gated specs); `1` = one or more content violations in a version-gated spec (hard fail); `2` = internal/operational error that prevented completion. Under `set -euo pipefail`, an unexpected runtime failure MUST be trapped and mapped to `2`, never silently surfaced as a content violation (`1`).

## Division of labor (no overlap, no gap)

| Concern | Owner |
|---------|-------|
| `up:` is **present, non-empty, well-formed** relative `[]()` link (not a wikilink) | **orphan lint** (FR-009) |
| `up:` requirement applies to **MOC files only** (not `spec.md`/`plan.md`/`tasks.md`/`contracts/**`) | **orphan lint** (FR-010) |
| `up:` target **resolves** to an existing file | **stale-index lint** (FR-011) |
| **every** relative `[]()` target resolves (the `up:` value + any body links) | **stale-index lint** (FR-011) |
| any `[[wikilink]]` inside a MOC is a violation in its own right | **stale-index lint** (FR-012) |
| `spec_id` namespace-matches the containing directory; an absent/empty `spec_id` in a version-gated marker is itself a violation | **spec_id check** (FR-019) — see `id-normalization-grammar.md` |

Net effect: a dangling `up:` is caught by stale-index (resolution), and a missing/malformed `up:` is caught by orphan (presence/form). Together they guarantee "every version-marked map reaches its parent" end-to-end.

## Orphan lint (`validate-moc-orphan.sh`)

- For each version-gated `SPEC-MOC.md`: assert `up:` is present, non-empty, and a well-formed relative `[]()` link (reject `[[wikilink]]` form here too as "not well-formed relative link"). Does NOT resolve the target (that is stale-index's job).
- Does NOT require `up:` on non-MOC docs. `.process/**` exempt.

## Stale-index lint (`validate-moc-stale-index.sh`)

- For each version-gated MOC: collect every relative `[]()` link target — **including the frontmatter `up:` value** plus any body links — and assert each resolves to an existing file (resolved relative to the MOC file's own directory). A target that exists but is NOT a regular readable file (a directory, or a broken symlink) is treated as NOT resolving — a violation — distinct from an absent target (FR-011).
- Assert no `[[wikilink]]` appears anywhere in the MOC; any wikilink is a violation.

## Output (FR-024)

- A content violation (`exit 1`) MUST report the offending spec/file path AND which rule failed (orphan: missing/ill-formed `up:`; stale-index: the specific unresolved link or the wikilink; `spec_id`: mismatch or absent join key) so the failure is actionable.
- An internal/operational error (`exit 2`) MUST report to **stderr** in a form distinct from content violations — the two failure classes are never conflated.

## Acceptance mapping

- US2 AC-1 → orphan lint fails on version-marked MOC with no valid `up:`.
- US2 AC-2 → stale-index fails on version-marked MOC with a non-resolving relative link.
- US2 AC-3 → stale-index fails on version-marked MOC containing a `[[wikilink]]`.
- US2 AC-4 → no-marker (or no-`structureVersion`) spec is silently skipped.
- US2 AC-5 → orphan does NOT require `up:` on non-MOC docs.
- US2 AC-6/7 → `spec_id` check distinguishes `(prsg,002)` from `(spec,002)`, and `013a` from `013a1`.
- US2 AC-8 → full run is green on first adoption (all legacy specs lack the marker → skipped).
