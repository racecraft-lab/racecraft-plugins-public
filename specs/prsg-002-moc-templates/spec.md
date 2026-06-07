# Feature Specification: MOC templates + scaffold-time skeleton + version-gated lints

**Feature Branch**: `prsg-002-moc-templates`

**Created**: 2026-06-06

**Status**: Draft

**Input**: User description: "MOC templates + scaffold-time skeleton + version-gated lints (PRSG-002). Provide roadmap-MOC and spec-MOC template shapes carrying a frontmatter join-key contract; have speckit-scaffold-spec write a minimal SPEC-MOC.md on every new spec; add two version-gated Layer-1 lints (orphan + stale-index) plus namespace-aware ID normalization — without red-failing CI on the pre-existing legacy specs."

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
-->

### User Story 1 - Templates + scaffold-time skeleton (Priority: P1)

As a plugin maintainer, when I scaffold a brand-new spec, I want a minimal navigation marker (`SPEC-MOC.md`) created automatically and pointed at its parent roadmap, and I want reusable template shapes (a roadmap map and a spec map) that carry the agreed frontmatter join-key contract, so that every new spec is born parent-linked and version-marked and can never become unreachable when its artifacts are later collapsed or relocated.

**Why this priority**: The skeleton writer is the root of the whole navigation spine. Without a marker file written at creation, there is nothing for the enforcement lints (US2) to gate on, and new specs would be silently grandfathered just like legacy ones. The templates carry the contract that every downstream spec (PRSG-003/004) builds on. This story stands alone: even with no lints, every new spec gains a parent link from day one.

**Independent Test**: Scaffold a fresh spec and confirm a minimal `SPEC-MOC.md` appears in its directory carrying `up:`, `structureVersion: 1`, and `spec_id`, with `up:` resolving to the existing technical roadmap file. Separately, confirm the two template shapes exist and carry the full frontmatter contract. Delivers value (a connected map for the new spec) regardless of whether US2 lints are present.

**Acceptance Scenarios**:

1. **Given** a new spec being scaffolded, **When** scaffolding completes, **Then** a `SPEC-MOC.md` file exists in the spec directory containing at minimum a non-empty `up:`, `structureVersion: 1`, and a `spec_id` matching the spec.
2. **Given** a new spec being scaffolded, **When** the `SPEC-MOC.md` is written, **Then** its `up:` value is a relative link that points to the existing `*-technical-roadmap.md` file (not a wikilink, not a dangling path).
3. **Given** the marker file is always written, **When** the spec will ultimately have only a single slice, **Then** the minimal `SPEC-MOC.md` is still written (the marker is written regardless of slice count because it is the version-gate carrier).
4. **Given** a maintainer authoring a roadmap-level or spec-level map, **When** they open the provided templates, **Then** a roadmap-MOC template and a spec-MOC template are available, each carrying the frontmatter join-key contract fields `up`, `related`, `status`, `rank`, `spec_id`, and `structureVersion`.
5. **Given** the scaffold-time skeleton writer change, **When** the equivalent skeleton behavior is needed in the Codex runtime, **Then** the Codex counterpart of the scaffold skill reflects the same skeleton-writing behavior (runtime parity), while the templates and lint scripts remain a single shared copy.

---

### User Story 2 - Version-gated lints + namespace-aware ID normalization (Priority: P2)

As a plugin maintainer or reviewer, I want two automated checks — one that flags a map with no valid parent link (orphan) and one that flags a map link that does not resolve, including any wikilink (stale-index) — that fire only for specs carrying the version marker, plus an ID-matching rule that correctly joins document IDs to directory names across both the `SPEC-` and `PRSG-` naming conventions, so that the navigation spine is provably connected for every new spec while the pre-existing legacy specs stay green and CI does not red-fail on the first upgrade.

**Why this priority**: The lints turn the contract from advisory into enforced, but they depend on US1 having written the marker file they gate on. Version-gating is the load-bearing safety property: it is what lets the contract apply to new specs from creation without breaking the existing repository. Namespace-aware ID normalization is what actually validates the headline join (it is enforced via the `spec_id` check).

**Independent Test**: Run the lints against fixtures. Confirm a version-marked map missing `up:` fails; a version-marked map with a non-resolving relative link fails; a version-marked map containing a `[[wikilink]]` fails; and a directory with no marker file is silently skipped. Confirm ID normalization joins `prsg-002-...` to `PRSG-002` and `013a-slug` to a `spec`-namespace ID, while `PRSG-002` does NOT match `SPEC-002` and `013a` does NOT match `013a1`.

**Acceptance Scenarios**:

1. **Given** a spec whose `SPEC-MOC.md` has `structureVersion >= 1`, **When** that map file has no valid `up:`, **Then** the orphan lint reports a violation and exits with a nonzero status.
2. **Given** a spec whose `SPEC-MOC.md` has `structureVersion >= 1`, **When** a map file contains a relative link whose target file does not exist, **Then** the stale-index lint reports a violation and exits with a nonzero status.
3. **Given** a spec whose `SPEC-MOC.md` has `structureVersion >= 1`, **When** a map file contains a `[[wikilink]]`, **Then** the stale-index lint treats the wikilink itself as a violation and exits with a nonzero status.
4. **Given** a spec directory that contains no `SPEC-MOC.md` (or whose marker carries no `structureVersion`), **When** the lints run, **Then** that spec is silently skipped and contributes no violation (legacy specs are grandfathered).
5. **Given** the orphan lint in v1, **When** it evaluates non-MOC documents (`spec.md`, `plan.md`, `tasks.md`, files under `contracts/`) inside a version-gated spec, **Then** it does NOT require those documents to carry `up:` (the `up:` requirement applies to MOC files only).
6. **Given** a doc ID `PRSG-002` and directories `prsg-002-moc-templates` and `002-pr-checks-workflow`, **When** ID normalization runs, **Then** `PRSG-002` matches `prsg-002-moc-templates` (namespace `prsg`, number `002`) and does NOT match `002-pr-checks-workflow` (which normalizes to namespace `spec`, number `002`).
7. **Given** a directory name with no alpha prefix such as `013a-slug`, **When** ID normalization runs, **Then** it is assigned the legacy `spec` namespace and its number-suffix `013a` is compared by exact segment, so `013a` does NOT match `013a1`.
8. **Given** all current spec trees in this repository (`docs/ai/specs/` and `specs/`) on first adoption of this feature, **When** the lints run as part of the test suite, **Then** the run is green because every pre-existing legacy spec lacks the version marker and is skipped.

---

### Edge Cases

- **No-marker spec under a version-gated repo**: A spec directory with no `SPEC-MOC.md` is exempt from both lints — silently skipped, never a violation.
- **Marker present but `structureVersion` absent or below the gate**: Treated as not-gated for any lint whose shipped version exceeds the marker's value; v1 lints fire only when `structureVersion >= 1`.
- **Marker present but `structureVersion` malformed**: A non-integer value (quoted string `"1"`, decimal `1.0`, or non-numeric text) is treated identically to absence — not-gated, silently skipped (FR-013). The gate fires only on an unambiguous integer `>= 1`.
- **Version-gated marker missing/empty `spec_id`**: An absent or empty `spec_id` in a version-gated `SPEC-MOC.md` is itself a violation (FR-019), distinct from a present-but-mismatched value — a marker with no join key cannot satisfy the directory join.
- **Degenerate normalization inputs**: An empty value, an all-alpha value with no following segment (`prsg`), or a trailing-/leading-dash value (`prsg-`) normalizes to an empty number-suffix, which never matches a well-formed directory's number-suffix (FR-017) — the grammar is total and never undefined.
- **`spec_id` does not match its directory**: The `spec_id` check is what validates the join; a marker whose `spec_id` does not normalize-match its containing directory is a violation in a version-gated spec.
- **Collision-prone IDs**: `SPEC-002` and `PRSG-002` both exist in the repository; normalization must keep them distinct (different namespaces) so a link or join never silently resolves to the wrong spec.
- **Exact-segment number suffix**: `013a` must not match `013a1`; the number-suffix comparison is exact-segment, not prefix/substring.
- **Wikilink inside a MOC**: A `[[wikilink]]` is a violation by itself, independent of whether a same-named target file happens to exist — the contract is relative `[]()` links only.
- **`up:` target moves**: When the parent (`*-technical-roadmap.md`) is later repointed to a roadmap-MOC home note (a future spec), the stale-index lint must still pass because the new target also resolves; v1 simply requires the current `up:` to resolve.
- **Marker with no/unparseable frontmatter**: A `SPEC-MOC.md` with no `---` frontmatter fence, or an unparseable frontmatter block, yields no readable `structureVersion` → treated as not-gated → silently skipped (FR-021); the parse is total and never crashes the lint.
- **Unreadable marker (permission denied)**: A `SPEC-MOC.md` that cannot be read cannot establish gating → during a tree scan it is exempt/skipped with a stderr warning, never a content violation (FR-021/FR-023) — preserving the never-red-fail-on-legacy property.
- **Link target is a directory or broken symlink**: A relative target that exists but is not a regular readable file is treated as not resolving (a stale-index violation), distinct from an absent target (FR-011).
- **Missing/empty scan root or zero gated specs**: A scan root that does not exist or is empty is skipped (not an error); a scan with zero version-gated specs exits `0` — so the lints run cleanly in a consuming project lacking one or both trees (FR-022).
- **Internal error vs content violation**: An operational failure (unreadable required input, trapped `set -euo pipefail` error) exits `2` and reports to stderr; a content violation exits `1` with the offending file + failed rule — the two are never conflated (FR-020/FR-024).

## Requirements *(mandatory)*

### Functional Requirements

**Templates and contract (US1)**

- **FR-001**: The feature MUST provide a roadmap-MOC template shape and a spec-MOC template shape, each carrying the frontmatter join-key contract fields: `up`, `related`, `status`, `rank`, `spec_id`, and `structureVersion`.
- **FR-002**: The templates MUST be placed where the scaffold skill already reads its other templates from, and the spec-MOC template MUST be consumable by the scaffold skill via the same token-substitution mechanism it already uses (no new preset, no project-local template copy).
- **FR-003**: The frontmatter contract MUST treat `up`, `structureVersion`, and `spec_id` as the load-bearing (enforced) fields in v1, while `status`, `rank`, and `related` are carried in the templates but remain optional and unenforced in v1.

**Scaffold-time skeleton (US1)**

- **FR-004**: The scaffold skill MUST write a minimal `SPEC-MOC.md` into the spec's CONTRACT directory `specs/<branch-name>/` (the namespace-prefixed, branch-named directory per the resolved `spec_id`↔dir convention), creating that directory if it does not yet exist, on EVERY new spec at creation time. The marker is a CONTRACT artifact — it is NOT redirected to `.process/` and NOT written to `docs/ai/specs/`.
- **FR-005**: The minimal `SPEC-MOC.md` MUST carry a non-empty `up:`, `structureVersion: 1`, and a `spec_id` identifying the spec.
- **FR-006**: The minimal `SPEC-MOC.md` MUST be written regardless of how many slices the spec will ultimately have (single-slice specs receive the marker too), because the marker is the version-gate carrier. A spec is only fleshed into a full navigation map when it later splits into multiple slices; that fleshing-out is out of scope for v1.
- **FR-007**: The `up:` value written by the scaffold skill MUST be a relative link (`[]()` style, never a wikilink) that points to the existing `*-technical-roadmap.md` for the spec. From the contract directory `specs/<branch-name>/`, this resolves as `../../docs/ai/specs/<roadmap-filename>.md` (for PRSG-002's own marker: `../../docs/ai/specs/pr-size-governance-technical-roadmap.md`).
- **FR-008**: The scaffold-time skeleton-writing behavior MUST be mirrored in the Codex counterpart of the scaffold skill so both runtimes write the marker; the MOC templates and the lint scripts MUST remain a single shared, runtime-agnostic copy each (not duplicated per runtime).

**Version-gated lints (US2)**

- **FR-009**: The feature MUST provide an orphan lint that reports a violation when a MOC file in a version-gated spec lacks a valid `up:`. A `up:` is "valid" for the orphan lint when it is present, non-empty, and a well-formed relative `[]()` link (not a `[[wikilink]]`); resolution of the `up:` target is owned by the stale-index lint (FR-011), not the orphan lint (clear division of labor, no overlap, no gap).
- **FR-010**: The orphan lint's `up:` requirement MUST apply ONLY to MOC files; non-MOC documents (`spec.md`, `plan.md`, `tasks.md`, files under `contracts/`) MUST NOT be required to carry `up:` in v1, and `.process/**` exhaust MUST be exempt. In v1, a file is recognized as a MOC by the exact filename `SPEC-MOC.md`; the roadmap-MOC instance filename is defined later by PRSG-004 and is out of scope here.
- **FR-011**: The feature MUST provide a stale-index lint that reports a violation when a relative link in a MOC file does not resolve to an existing target file. The relative links it resolves MUST include the MOC's frontmatter `up:` value as well as any body `[]()` links — so a dangling `up:` in a version-gated MOC is itself a stale-index violation (this is what guarantees the "every map reaches its parent" property end-to-end). A relative target that exists on disk but is NOT a regular readable file (e.g., a directory, or a broken symlink whose target is missing) MUST be treated as not resolving — a violation — distinct from a target that is simply absent.
- **FR-012**: The stale-index lint MUST treat any `[[wikilink]]` inside a MOC file as a violation in its own right, independent of whether a same-named target exists.
- **FR-013**: Each lint MUST fire ONLY when the spec's `SPEC-MOC.md` carries `structureVersion >= 1`; a spec with no marker file, or a marker without `structureVersion`, MUST be silently skipped and contribute no violation. A `structureVersion` value that is not a bare integer (e.g., a quoted string `"1"`, a decimal `1.0`, or non-numeric text) MUST be treated identically to absence — the spec is NOT gated and is silently skipped — so a malformed value can never silently bypass an enforced check on a spec that should have been gated, and can never red-fail CI on a legacy marker (the gate "fires" only on an unambiguous integer `>= 1`).
- **FR-014**: Each lint MUST hard-fail (exit with a nonzero status) when it finds a violation in a version-gated spec, and exit success when there are no violations among the specs it is allowed to check.
- **FR-015**: The lints MUST run as part of the project's deterministic structural test layer and MUST scan this repository's real spec trees (`docs/ai/specs/` and `specs/`), with committed fixtures exercising the lint logic; the same lint scripts MUST be runnable in any consuming project's checks.
- **FR-016**: The version-gate literal value MUST be `1` for v1, expressed as an integer; it MUST be hardcoded in the lint script(s) and stamped by the scaffold skill, each carrying a "keep in sync" comment, with no shared version file or semver string introduced.

**Namespace-aware ID normalization (US2)**

- **FR-017**: ID normalization MUST join a document ID to a directory name by reducing each to a pair of `(namespace, number-suffix)`: lowercase the value, detect an optional leading alpha prefix (e.g., `spec-`, `prsg-`), and treat a value with no alpha prefix as belonging to the legacy `spec` namespace. The extraction grammar MUST be: split the lowercased name on `-`; if the first dash-delimited segment is all-alpha it is the namespace and the next segment is the number-suffix, otherwise the namespace is `spec` and the first segment is the number-suffix. The number-suffix MUST be compared as an opaque whole segment (byte-equality of the full segment); implementations MUST NOT sub-parse trailing letters from digits (no `[0-9]+[a-z]*` capture that would truncate `013a1` to `013a`). The grammar MUST be total: it MUST yield a defined `(namespace, number-suffix)` pair for ANY input, including degenerate ones (an empty value, a value that is only `-`, a value with a leading or trailing dash, or an all-alpha value with no following segment). When the rule would select a missing or empty number-suffix segment (e.g., an all-alpha value `prsg`, or a trailing-dash value `prsg-`), the number-suffix is the empty string; an empty number-suffix can never equal a well-formed directory's number-suffix, so such a value never produces a false match.
- **FR-018**: A match MUST require BOTH parts to agree: the namespaces MUST be equal AND the number-suffix MUST match by exact-segment comparison. Consequently `PRSG-002` MUST NOT match `SPEC-002` (different namespaces) and `013a` MUST NOT match `013a1` (different number-suffix segments). Real-tree examples the dogfooded lint will scan: `006a-uat-skeleton` normalizes to `(spec, 006a)`, `prsg-002-moc-templates` to `(prsg, 002)`, and bare id `PRSG-002` to `(prsg, 002)` (so the marker's `spec_id` matches its directory).
- **FR-019**: The `spec_id` field in a version-gated `SPEC-MOC.md` MUST be validated against its containing directory using this namespace-aware normalization; a mismatch is a violation (this is the check that validates the headline ID-join feature). A `spec_id` that is ABSENT or EMPTY in a version-gated marker MUST itself be a violation (distinct from a present-but-mismatched value): a version-gated marker that carries no join key cannot satisfy the directory join, so it MUST hard-fail rather than silently pass. Both the `spec_id` value and the containing directory name MUST be reduced with the SAME normalization grammar (FR-017) before comparison (symmetric normalization — neither side is compared raw).

**Error handling & robustness (US2)**

- **FR-020** (exit-code contract): Each lint MUST expose a defined THREE-WAY exit-code enumeration so that a content VIOLATION is distinguishable from an INTERNAL/operational error: `0` = clean (no violations among the checkable specs); `1` = one or more content violations in a version-gated spec; `2` = an internal/operational error that prevented the lint from completing its checks. Because the scripts run under `set -euo pipefail`, an unexpected runtime failure MUST be trapped and mapped to the internal-error code (`2`) — it MUST NOT surface as the content-violation code (`1`). This makes "the lint found a problem in the docs" and "the lint itself broke" two separately diagnosable outcomes.
- **FR-021** (total, safe marker parsing): The version-gate read MUST be total and MUST never crash the lint. A `SPEC-MOC.md` that exists but has NO frontmatter fence, or whose frontmatter is unparseable, yields no readable integer `structureVersion` and MUST therefore be treated identically to an absent marker — NOT gated, silently skipped (consistent with FR-013) — never an undistinguished crash. A `SPEC-MOC.md` that is UNREADABLE (permission denied) likewise cannot establish that the spec is gated; during a tree scan it MUST be treated as exempt/skipped with a warning emitted to stderr, and MUST NOT produce a content violation (this preserves the never-red-fail-on-legacy property — see FR-023).
- **FR-022** (scan-root robustness): A configured scan root (`docs/ai/specs/` or `specs/`) that does not exist or is empty MUST be skipped, not treated as an error — the lints scan whichever of the two trees exist, so they run cleanly in any consuming project where one or both trees are absent (FR-015). A scan that finds ZERO version-gated specs MUST exit `0` (success on an empty checkable set), never error.
- **FR-023** (exempt-before-content invariant): The exempt/skip decision for a spec MUST be evaluated BEFORE any read of that spec's body content. A spec with no `SPEC-MOC.md`, or a marker with no readable integer `structureVersion`, is skipped before its content is examined — so a grandfathered legacy spec can NEVER cause a nonzero exit regardless of its body content. This is the load-bearing safety property behind SC-002.
- **FR-024** (actionable output): A content violation MUST report, in the lint's output, the offending spec/file path AND which rule failed (orphan: missing or ill-formed `up:`; stale-index: the specific unresolved link or the wikilink found; `spec_id`: mismatched or absent join key). Internal/operational errors (exit `2`) MUST be reported to stderr in a form distinct from content violations, so a nonzero exit is actionable and the two failure classes are never conflated.

### Key Entities *(include if feature involves data)*

- **MOC (Map of Content) file**: A markdown file (`SPEC-MOC.md` at spec level; roadmap-MOC at roadmap level) carrying navigation frontmatter and relative links. Identified as a MOC by the exact filename `SPEC-MOC.md` in v1 (the roadmap-MOC instance filename is defined by PRSG-004). Carries the join-key contract fields.
- **Frontmatter join-key contract**: The set of fields `up`, `related`, `status`, `rank`, `spec_id`, `structureVersion`. `up` is the parent link; `spec_id` is the join key to a directory; `structureVersion` is the version-gate marker; the rest are carried for downstream specs.
- **Normalized ID**: A `(namespace, number-suffix)` pair derived from a doc ID or a directory name, used to join documents to directories without cross-namespace collision.
- **Version gate**: The condition `structureVersion >= <lint's shipped version>` (v1 = 1) that determines whether a spec is subject to a given lint; absence of the marker means exempt.
- **Spec tree**: A scanned directory of specs (`docs/ai/specs/`, `specs/`) over which the lints operate.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every newly scaffolded spec is reachable from a parent roadmap immediately upon creation — 100% of new specs carry a parent-linked navigation marker with no extra manual step.
- **SC-002**: Adopting this feature on the existing repository produces zero new check failures on the pre-existing legacy specs (the first upgrade does not red-fail CI), while the checks are fully active for every new spec.
- **SC-003**: A broken navigation link or a missing parent link in a version-marked map is caught automatically before merge in 100% of cases, rather than discovered later as an unreachable document.
- **SC-004**: Document-to-directory ID joins are unambiguous across both naming conventions — collision-prone pairs such as `PRSG-002` and `SPEC-002` are never matched to each other, and near-miss suffixes such as `013a` and `013a1` are never matched.
- **SC-005**: A reviewer can navigate from a spec's map to its parent and follow every link in the map to an existing target, with no dangling or wikilink references in any version-marked map.

## Assumptions

- **Single-MOC marker per spec**: The scaffold-written marker is `SPEC-MOC.md` in the spec directory; "fleshing it out" into a richer multi-slice navigation map is deferred to the decomposition specs and is out of scope here.
- **`spec_id` carries the namespace**: `spec_id` values use the project's existing conventions (`PRSG-...`, legacy unprefixed). The directory and the `spec_id` are joined via the namespace-aware normalization of FR-017/FR-018 (match requires the same `(namespace, number-suffix)` pair).
- **RESOLVED — `spec_id` carries the roadmap identity; contract dirs are namespace-prefixed** (maintainer decision, 2026-06-06): The design concept (Q3) assumed PRSG specs live in `prsg-NNN-slug` directories. This was confirmed as the go-forward convention: `SPEC-MOC.md`'s `spec_id` carries the **roadmap identity** (`PRSG-002`), and the contract directory is named to namespace-match it — `specs/prsg-002-moc-templates/` (the branch name), NOT a sequential number. Under FR-018, `PRSG-002` → `(prsg, 002)` and `prsg-002-moc-templates` → `(prsg, 002)` **match**, so the dogfooded lints stay green on this spec with no special-casing. No roadmap-id↔directory mapping layer is needed; the namespace-aware normalizer of FR-017/FR-018 works exactly as specified. Going forward, scaffolded contract dirs are branch-named (`prsg-NNN-slug` / `spec-NNN-slug`) to match their `spec_id`. Pre-existing legacy numeric dirs (`001-…`, and PRSG-001's `007-…`) carry no `SPEC-MOC.md`, so they are grandfathered/exempt under the version gate and are unaffected.
- **Parent target exists**: A `*-technical-roadmap.md` already exists for the spec at scaffold time, so the written `up:` resolves immediately (no dangling link to trip the stale-index lint).
- **MOC identification**: In v1 a file is recognized as a MOC by the exact filename `SPEC-MOC.md`, so the orphan lint can scope the `up:` requirement to MOC files only. The roadmap-MOC instance filename convention is defined by PRSG-004.
- **Scaffold owns early contract-dir creation**: The scaffold skill creates `specs/<branch-name>/` (named from the branch, NOT from `create-new-feature.sh`'s sequential numbering) and writes `SPEC-MOC.md` there at scaffold time. This is safe because the autopilot Specify phase skips `create-new-feature.sh` when already on a feature branch, so there is no collision with a later auto-numbered directory. Naming the directory from the branch (not a sequential number) is exactly what makes `spec_id` namespace-match its directory under FR-018 — `create-new-feature.sh`'s default numbering would produce `(spec, NNN)` and break the join.
- **Repository dogfoods the contract**: The lints scan this repo's real spec trees, so the version-gating safety property is validated against actual legacy specs, not only fixtures.
- **Hardcoded version literal is acceptable at N=1**: The `structureVersion` literal `1` is copied into both the lint script(s) and the scaffold skill with a "keep in sync" comment, mirroring the repo's existing "copied verbatim, keep in sync" pattern; a shared version file is deliberately avoided.
- **Out of scope (deferred to other specs)**: Generated MOC content — the down-link index, backlinks, and status integration — belongs to PRSG-003; the PRD-derived roadmap-MOC home note belongs to PRSG-004; retro-migration/backfill of legacy specs and relocation of existing top-level exhaust into `.process/` belongs to PRSG-011; requiring `up:` on non-MOC docs and wikilink support are both excluded from v1.
- **Global ID uniqueness is NOT a v1 goal**: The `spec_id` check (FR-019) validates a per-spec join — each version-gated directory against ITS OWN marker's `spec_id`. Detecting two distinct scanned directories that normalize to the same `(namespace, number-suffix)` pair (a cross-directory duplicate-ID collision) is deliberately NOT enforced in v1; the namespace-prefixed branch-named directory convention makes such a clash a process error to be caught at scaffold/review time, not a lint surface here.
