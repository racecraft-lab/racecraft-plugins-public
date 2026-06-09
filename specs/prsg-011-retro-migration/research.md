# Research: PRSG-011 Retro-migration

## Decision 1: Repo Marker Gates Legacy Roadmap Rows

**Decision**: Treat `.specify/structure-version.json` with integer
`structureVersion >= 1` as the high-water marker that allows roadmap-MOC INDEX
rendering to include completed or archived historical specs without per-spec
stamps.

**Rationale**: The marker is a repo-level state key, so Tier-0 can backfill
navigation without mutating historical spec files. This preserves the legacy
exemption signal for historical specs while giving future generator runs the
same durable behavior.

**Rejected alternative**: Patch roadmap-MOC INDEX rows directly in
`migrate-structure.sh`. That would duplicate generated-zone rendering and make
future generator runs a second source of truth.

## Decision 2: Reuse Existing MOC Helpers

**Decision**: Source `moc-id-normalize.sh` for `moc_normalize` and
`moc_id_match`, and source `moc-frontmatter.sh` for frontmatter reads and
version gating.

**Rationale**: `moc_id_match` already compares namespace plus exact opaque
number-suffix, which prevents false joins such as PRSG-013A vs PRSG-013A1.
`moc_is_gated` already implements the bare integer `structureVersion >= 1`
gate. Reusing both keeps the migration logic aligned with existing lints and
templates.

**Rejected alternative**: Add a new ID-normalization wrapper during planning.
The known requirements fit the existing helper signatures.

## Decision 3: Compact JSON Reports Are the Operator Contract

**Decision**: Both migration scripts emit one deterministic compact JSON report
per invocation. Apply modes also print the backup path inside the JSON report.

**Rationale**: Fixture tests can compare byte-stable output when item arrays are
sorted and timestamps are test-overridable. JSON also lets operators and future
skills distinguish pending, applied, skipped, protected, dirty-blocked, backup,
recovery, and no-op states without parsing prose.

**Rejected alternative**: Human-readable line logs as the primary output. Logs
are easier to read manually but harder to assert for deterministic behavior and
complete state categories.

## Decision 4: Clean-Tree Check Precedes Every Apply Backup

**Decision**: Mutation modes run
`git status --porcelain=v1 --untracked-files=all` and fail on any output before
backup creation, marker writes, generated-zone updates, stamps, or moves.

**Rationale**: This preserves user work and matches the operator-safe contract.
The forced backup is still non-skippable, but only after the tree is eligible
for mutation.

**Rejected alternative**: Create a backup before checking dirty state. That
would produce unnecessary backups and blur the "no mutation on dirty tree"
guarantee.

## Decision 5: Tier-2 Uses Dual PROCESS Anchors

**Decision**: Spec-root PROCESS artifacts move to `<spec-dir>/.process/`, while
matching docs-side scaffold artifacts move from `docs/ai/specs/` to
`docs/ai/specs/.process/`.

**Rationale**: The spec root and docs process artifacts have different anchors.
Moving both through one explicit Tier-2 apply keeps CONTRACT files visible while
normalizing thawed process history.

**Rejected alternative**: Move every matching file into the spec root
`.process/`. That would misplace docs-side workflow/design artifacts and break
the existing docs process layout.

## Decision 6: Scaffold and Autopilot Suggestions Are Static

**Decision**: Scaffold and autopilot inspect target spec state and active-feature
state directly, then print the exact relocation dry-run command and clean-tree
apply follow-up when a thawed legacy spec has relocatable PROCESS artifacts.
They never execute the codemod.

**Rationale**: Operators need discovery, but automatic file moves inside
scaffold/autopilot are too risky. Static detection keeps behavior explainable
and testable in Layer 3 and Layer 8.

**Rejected alternative**: Let scaffold/autopilot call
`relocate-process-artifacts.sh --dry-run` to decide whether to suggest apply.
The spec requires no automatic codemod execution, including dry-run.

## Decision 7: One Spec With Two Ordered Internal Increments

**Decision**: Keep PRSG-011 as one spec and preserve two internal vertical
increments: Tier-1/Tier-0 migration first, Tier-2 relocation and suggestions
second.

**Rationale**: The repo marker and generator changes establish the state key
that the Tier-2 path and operator suggestions depend on. Keeping them together
preserves traceability for one migration feature while acknowledging the
accepted reviewability warning.

**Rejected alternative**: Split before planning. The split would create an
artificial boundary between the marker/backfill contract and the relocation
contract it unlocks.

## Decision 8: Candidate Eligibility Before Normalization

**Decision**: Apply a deterministic SpecKit candidate eligibility predicate
before Tier-0 row rendering, Tier-2 move discovery, or scaffold/autopilot
suggestion emission. `prsg` and `spec` namespace candidates plus legacy
numeric/spec candidates that join to the roadmap-MOC spine stay eligible.
Non-SpecKit alpha namespaces and date-first legacy namespaces are reported as
`skipped_out_of_scope` with stable reasons.

**Rationale**: `moc_normalize` is intentionally total, so unrelated names can
still normalize to a namespace/suffix pair. A separate eligibility predicate
preserves the existing normalizer and lint behavior while preventing unrelated
legacy namespaces from becoming migration candidates by accident.

**Rejected alternative**: Change `moc_normalize` to reject non-SpecKit or
date-first inputs. That would broaden the impact beyond PRSG-011 and risk
breaking existing MOC lint and generator callers that rely on total
normalization.
