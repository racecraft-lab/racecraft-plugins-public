# Data Model: MOC templates + scaffold-time skeleton + version-gated lints

This feature has no runtime data store. The "entities" are document/file shapes and the derived values the lints compute over them. They are recorded here because the lints validate them and the templates carry them.

---

## Entity: MOC (Map of Content) file

A markdown file carrying navigation frontmatter and relative links.

- **Identification (v1)**: a file is recognized as a MOC by the **exact filename `SPEC-MOC.md`** (spec-level). The roadmap-MOC instance filename is defined later by PRSG-004 and is out of scope here.
- **Location (spec-level)**: `specs/<branch-name>/SPEC-MOC.md` — a CONTRACT artifact. NOT in `.process/`, NOT in `docs/ai/specs/`.
- **Fields**: the frontmatter join-key contract (below) plus optional body content with relative `[]()` links.
- **Lifecycle**: written minimally by `speckit-scaffold-spec` at spec creation; fleshed into a richer navigation map only when a spec later splits into multiple slices (deferred — out of v1 scope).

## Entity: Frontmatter join-key contract

The set of fields every MOC template carries.

| Field | Type | v1 status | Meaning / validation rule |
|-------|------|-----------|---------------------------|
| `up` | relative `[]()` link | **ENFORCED** | Parent link. Orphan lint: MUST be present, non-empty, and a well-formed relative `[]()` link (NOT a `[[wikilink]]`). Stale-index lint: its target MUST resolve to an existing file. |
| `structureVersion` | integer | **ENFORCED** | Version-gate marker. Presence (and value `>= shipped lint version`) determines whether a spec is subject to a given lint. v1 literal = `1`. |
| `spec_id` | string (e.g., `PRSG-002`) | **ENFORCED** | Join key to the containing directory. MUST namespace-match its directory under the ID-normalization grammar; mismatch = violation in a version-gated spec. |
| `status` | string | carried, unenforced | Reserved for PRSG-003/004. Present in templates; no lint reads it in v1. |
| `rank` | number/string | carried, unenforced | Reserved for PRSG-003/004. |
| `related` | list of relative links | carried, unenforced | Reserved for PRSG-003/004. (Body/`related` links, when present in a MOC, are still resolved by the stale-index lint as relative `[]()` targets — but no lint *requires* `related` to exist in v1.) |

**Load-bearing set (v1)**: `up`, `structureVersion`, `spec_id`. The other three are carried so downstream specs need no template change.

## Entity: Normalized ID

A `(namespace, number-suffix)` pair derived from a doc ID or a directory name, used to join documents to directories without cross-namespace collision.

- **Derivation grammar**:
  1. Lowercase the value.
  2. Split on `-`.
  3. If the first segment is **all-alpha**, it is the `namespace` and the next segment is the `number-suffix`.
  4. Otherwise `namespace = "spec"` and the first segment is the `number-suffix`.
- **Comparison**: number-suffix compared as an **opaque whole segment** (byte-equality of the full segment; no `[0-9]+[a-z]*` sub-parse). A match requires `namespace` equal AND `number-suffix` equal.
- **Examples**:
  - `prsg-002-moc-templates` → `(prsg, 002)`
  - `PRSG-002` → `(prsg, 002)` → **matches** the directory above
  - `002-pr-checks-workflow` → `(spec, 002)` → does NOT match `(prsg, 002)`
  - `SPEC-002` → `(spec, 002)` → does NOT match `(prsg, 002)`
  - `006a-uat-skeleton` → `(spec, 006a)`
  - `013a` → `(spec, 013a)`; `013a1` → `(spec, 013a1)` → do NOT match each other

## Entity: Version gate

The condition that determines whether a spec is subject to a given lint.

- **Condition**: `structureVersion >= <lint's shipped version>` (v1 lints: shipped version = `1`).
- **Exempt (silently skipped, never a violation)** — decided BEFORE any body-content read (FR-023):
  - a spec directory with no `SPEC-MOC.md`, OR
  - a `SPEC-MOC.md` whose frontmatter carries no `structureVersion`, a non-bare-integer `structureVersion`, or `structureVersion < 1`, OR
  - a `SPEC-MOC.md` with no `---` fence / unparseable frontmatter (no readable `structureVersion`), OR
  - an UNREADABLE `SPEC-MOC.md` (permission denied → skip + stderr warning). The version-gate read is **total** and never crashes the lint (FR-021).
- **Consequence**: pre-existing legacy specs (which have no marker) are grandfathered — the first adoption of this feature does not red-fail CI (SC-002).

## Entity: Spec tree

A scanned directory of specs over which the lints operate.

- **Trees scanned (this repo, dogfooded)**: `docs/ai/specs/` and `specs/` (repo-root paths; the lints resolve repo root from the test dir).
- **Per-spec unit**: an immediate child directory; the lint looks for `SPEC-MOC.md` in it to decide gating.
- **Reusability**: the same lint scripts are runnable in any consuming project's checks against that project's equivalent trees.

---

## State / control flow (per lint, per version-gated MOC)

```text
resolve REPO_ROOT; for each scan root in { docs/ai/specs/, specs/ }:
    if scan root missing or empty            -> SKIP this root (not an error; FR-022)

for each spec directory under the scanned trees:
    # exempt/skip decided BEFORE any body-content read (FR-023) -> legacy never red-fails
    if no SPEC-MOC.md                        -> SKIP (exempt)
    if SPEC-MOC.md unreadable                 -> SKIP + stderr warning (exempt; FR-021)
    if no ---fence / unparseable frontmatter  -> SKIP (no readable structureVersion; FR-021)
    if structureVersion absent                -> SKIP (exempt)
    if structureVersion not a bare integer    -> SKIP (malformed treated as absence; gate fires only on integer >= 1)
    if structureVersion < 1                   -> SKIP (not gated for v1 lints)
    else (version-gated):
        orphan lint:
            up present & non-empty & well-formed relative []() link?  else VIOLATION
        stale-index lint:
            every relative []() target (incl. up: value + body links) resolves to an existing REGULAR file?
                (a directory or broken symlink at the path = NOT resolving = VIOLATION; FR-011)  else VIOLATION
            any [[wikilink]] present?  -> VIOLATION
        spec_id check (FR-019):
            spec_id absent or empty?  -> VIOLATION (no join key)
            normalize(spec_id) == normalize(dirname)?  else VIOLATION   (both sides normalized, same grammar)

exit codes (FR-020):
    0  clean: no violations among checkable specs (INCLUDING zero version-gated specs found)
    1  one or more content violations in a version-gated spec  (report file + failed rule; FR-024)
    2  internal/operational error (trapped set -euo pipefail failure) -> stderr; NEVER reported as 1
```
