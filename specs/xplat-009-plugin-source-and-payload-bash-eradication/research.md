# Research: Plugin Source and Payload Bash Eradication

## Decision 1: Keep One Workflow With Two Vertical Slices

**Decision**: Keep XPLAT-009 as one workflow with two vertical slices:
source cleanup first, payload/cache proof and guards second.

**Rationale**: XPLAT-009 is the dependency that unblocks XPLAT-010. The setup
reviewability warning is real, but the accepted Design Concept already chose
two PR-ready slices over child specs. Slice 1 and Slice 2 have separate
verification boundaries and rollback points.

**Rejected alternatives**:

- Child specs: lower per-review size but duplicate guard and payload proof work.
- Single aggregate slice: simpler coordination but ignores the accepted
  reviewability warning.

## Decision 2: Use the Live 35-Script Source Baseline

**Decision**: Treat the live worktree scan as authoritative. At Plan time,
`speckit-pro/` contains 35 `.sh` files:

```text
speckit-pro/codex-skills/install/scripts/install-codex-agents.sh
speckit-pro/scripts/install-curated-set.sh
speckit-pro/skills/speckit-autopilot/scripts/aggregate-crl.sh
speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh
speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh
speckit-pro/skills/speckit-autopilot/scripts/confidence-gate.sh
speckit-pro/skills/speckit-autopilot/scripts/count-markers.sh
speckit-pro/skills/speckit-autopilot/scripts/detect-commands.sh
speckit-pro/skills/speckit-autopilot/scripts/detect-presets.sh
speckit-pro/skills/speckit-autopilot/scripts/detect-stack-manager.sh
speckit-pro/skills/speckit-autopilot/scripts/estimate-reviewable-loc.sh
speckit-pro/skills/speckit-autopilot/scripts/final-reviewability-backstop.sh
speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh
speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh
speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh
speckit-pro/skills/speckit-autopilot/scripts/lib/moc-frontmatter.sh
speckit-pro/skills/speckit-autopilot/scripts/lib/moc-id-normalize.sh
speckit-pro/skills/speckit-autopilot/scripts/lib/specify-cli.sh
speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh
speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh
speckit-pro/skills/speckit-autopilot/scripts/o5-topology.sh
speckit-pro/skills/speckit-autopilot/scripts/parse-consensus-categories.sh
speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh
speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh
speckit-pro/skills/speckit-autopilot/scripts/resolve-confidence-mode.sh
speckit-pro/skills/speckit-autopilot/scripts/restack.sh
speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh
speckit-pro/skills/speckit-autopilot/scripts/validate-agent-install.sh
speckit-pro/skills/speckit-autopilot/scripts/validate-gate.sh
speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh
speckit-pro/skills/speckit-autopilot/scripts/validate-pr-workflow-contract.sh
speckit-pro/skills/speckit-autopilot/scripts/validate-uat-runbook.sh
speckit-pro/skills/speckit-coach/scripts/ensure-reviewability-preset.sh
speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh
speckit-pro/skills/speckit-coach/scripts/project-fixup.sh
```

**Rationale**: Scaffold-time counts are historical setup evidence. The active
implementation must remove what exists in the current worktree.

**Implications**:

- Delete-only classification is allowed only when no active skill, runtime,
  test, registry, or workflow owner remains.
- Each active behavior must be owned by a Python runner/helper/gate operation
  before the `.sh` file is deleted.

## Decision 3: Active Behavior Ownership Uses Python Operation IDs

**Decision**: Active registries and active outputs expose Python helper or gate
operation IDs after shell removal. Legacy script names may remain only as
inactive provenance or historical allowlist entries excluded from release
readiness.

**Current ownership groups**:

| Script family | Current Python owner | Plan decision |
|---|---|---|
| Read-only helper scripts such as `check-prerequisites`, `detect-commands`, `detect-presets`, `count-markers`, `validate-gate`, `reviewability-gate`, `estimate-reviewable-loc`, `resolve-confidence-mode`, `confidence-gate`, `o5-topology`, `atomicity-route`, `plan-layers`, `validate-pr-workflow-contract`, and read-only `validate-pr-packet` | `speckit_pro_runner.helpers.registry` helper IDs with matching operation IDs | Remove active script paths from current registry outputs and keep the Python helper IDs authoritative. |
| Suite and release gates | `suite-gate/*`, `release-readiness/*`, `payload-gate/payload-completeness`, `install-verification/*`, and `active-path-guard/*` | Keep gate operation IDs active and remove active guidance that dispatches plugin scripts. |
| Mutation helpers with deferred or command-plan status, including PR body, final reviewability, multi-PR emission, restack, UAT skeleton, structure migration, process relocation, and spec-index writes | `speckit_pro_runner.helpers.registry` mutation helper records | Promote active behavior to bounded Python semantics where still live; otherwise mark as inactive provenance or delete-only with release-readiness exclusion. |
| Install helpers `install-curated-set` and Codex agent installer | Existing install helper records plus install-health repair paths | Port active install behavior or remove active guidance before deleting scripts; real-home writes stay bounded and explicit. |
| Shell libraries under `scripts/lib/` | No standalone active operation | Delete after dependent active scripts are ported or deleted. |

**Rejected alternatives**:

- Keeping `.sh` path strings in active registry output: violates the Phase 2
  clarification and lets active behavior appear shell-owned.
- Python wrappers around `.sh` files: fails the source zero-Bash target.

## Decision 4: Add One Cross-Surface Zero-Bash Guard

**Decision**: Add a single runner operation,
`active-path-guard/zero-bash-guard`, to scan source roots, generated payload
roots, and installed-cache proof records or roots.

**Rationale**: Existing `active-path-guard` and `active-runtime-guard` establish
the classification surface, but XPLAT-009 needs one request that spans plugin
source, generated payloads, and installed-cache proof. The operation returns a
runner envelope with bounded findings and release-readiness-compatible counts.

**Failure shape**:

- `status`: `ok` when no blocking finding exists, otherwise `validation_failure`
- `blocking_count`: total blocking findings
- `classified_counts`: counts by category and classification
- `findings`: bounded list with surface, path, line, category, pattern, reason,
  classification, active role, and remediation
- diagnostic code: `zero_bash_guard_blocked`

**Rejected alternatives**:

- Changed-files-only scan: can miss retained scripts or stale payload/cache
  proof.
- Independent shell scans: not reusable by runner release readiness and would
  reintroduce shell dependency.

## Decision 5: Historical Allowlist Entries Are Release-Readiness Excluded

**Decision**: Historical/archive prose may mention Bash only through explicit
allowlist entries requiring path, reason, scope, category, and release-readiness
exclusion.

**Allowed categories**:

- `historical_archive`: archived or historical narrative not used as current
  runtime guidance
- `negative_policy`: wording that explicitly prohibits or rejects shell fallback
- `inactive_provenance`: legacy name retained only to explain migration or
  traceability

**Rationale**: Historical prose can remain useful, but it must not mask active
release behavior or satisfy proof. The allowlist contract makes that explicit.

## Decision 6: Payload Rebuild Uses Payload-Completeness Apply Mode

**Decision**: Claude and Codex payloads are rebuilt with
`payload-gate/payload-completeness` in apply mode. Manual edits under `dist/**`
are not authoritative.

**Required proof**:

- source root and generated root records
- transform records
- file-tree hashes
- read-only payload-completeness result after apply mode
- zero missing, extra, mismatched, or path-leaking files
- zero generated `.sh` files and zero unallowlisted active Bash or `jq` guidance

**Rejected alternatives**:

- Hand-editing generated payloads: creates source/dist drift.
- Zero `.sh` count alone: does not prove source-derived completeness.

## Decision 7: Installed-Cache Proof Is Bounded and Source-Derived

**Decision**: Required installed-cache proof is produced by extracting or copying
rebuilt payloads into a bounded fixture or temporary root and scanning that root
with the zero-Bash guard. Mutable real user cache scans may be attached as
supplemental UAT context only.

**Rationale**: Real user caches are mutable and environment-specific. Release
readiness needs deterministic proof derived from the rebuilt payload.

**Proof minimum**:

- product or surface
- installed root
- source payload tree or hash
- file inventory
- `.sh` count
- active-guidance finding counts
- `source_derived: true`
- allowlist exclusion state

## Decision 8: XPLAT-008 Native UAT Remains Out of Scope

**Decision**: XPLAT-009 preserves XPLAT-008 native UAT status as known release
context but does not complete native operator UAT rows or expand public native
platform claims.

**Rationale**: XPLAT-009 is a source/payload/cache Bash-eradication phase.
Completing native UAT would duplicate XPLAT-008 and widen the scope beyond the
accepted Design Concept.

## Unresolved Items

None for Plan. Exact task IDs and per-file deletion ordering are deferred to
`tasks.md`, where they can be sequenced test-first by slice.
