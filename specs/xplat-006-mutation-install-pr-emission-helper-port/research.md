# Research: XPLAT-006 Mutation, Install, and PR-Emission Helper Port

## Decision 1: Keep One Workflow With Three Internal Slices

**Decision**: Keep XPLAT-006 as one workflow and organize implementation into
Slice 1 mutation safety, Slice 2 install/doctor, and Slice 3 PR-emission,
restack, relocation, mixed writes, and autopilot phase-coverage hardening.

**Rationale**: The accepted design concept treats these helper groups as one
roadmap dependency for XPLAT-007. The reviewability warning is known and
non-blocking at setup, and the three-slice order gives reviewers a stable path
through safety primitives before high-risk helpers.

**Alternatives considered**:
- Split immediately into separate specs. Rejected because it would fragment the
  promotion boundary and make XPLAT-007 gate migration depend on multiple
  partially overlapping PR packets.
- Port helpers independently. Rejected because mutation safety semantics would
  diverge across helpers.

## Decision 2: Add Mutation-Capable Runner Modes Beside Read-Only Helpers

**Decision**: Extend the runner helper registry with explicit mutation-capable
modules and modes instead of routing write/apply behavior through the XPLAT-005
`read_only` module.

**Rationale**: XPLAT-005 already accepted read-only/advisory behavior. Mutation
helpers need dry-run/apply, approval evidence, boundary checks, atomic writes,
dirty-worktree gating, and partial-failure reporting that do not belong in a
read-only abstraction.

**Alternatives considered**:
- Add write flags to `read_only.py`. Rejected because it would blur accepted
  XPLAT-005 behavior and make safety review harder.
- Build a generic mutation framework first. Rejected as premature beyond the
  shared request/result, path, atomic-write, and promotion-record primitives.

## Decision 3: Use a Stable Request and Result Contract

**Decision**: Define `Mutation Helper Request` and `Mutation Helper Result`
schemas. Keep the runner envelope stable and put mutation-specific details under
`data.mutation`.

**Rationale**: The existing runner envelope is the compatibility boundary.
Mutation-specific data needs a predictable location for planned operations,
applied operations, skipped/no-op operations, dirty state, failure operation,
rollback notes, and remediation actions.

**Alternatives considered**:
- Emit helper-specific result shapes. Rejected because PR packet traceability
  and promotion comparison need one reviewer-visible model.
- Change the top-level runner envelope. Rejected because XPLAT-004 established
  that contract.

## Decision 4: Default to Fake State and Require Structured Live Approval

**Decision**: Deterministic tests use fake repositories, fake `gh`, fake
`specify`, fake Claude homes, fake Codex homes, fake plugin caches, and temp
boundaries. Live repo, user-local, plugin-cache, network, or GitHub mutation is
blocked unless structured approval evidence references prior dry-run output.

**Rationale**: XPLAT-006 must prove mutation behavior without relying on real
user state or network side effects. Boolean flags and mode names are not enough
to authorize live mutation.

**Alternatives considered**:
- Allow live apply in normal tests. Rejected because it would make tests
  non-deterministic and unsafe.
- Accept a simple `--yes` flag for live mutation. Rejected because approval must
  be auditable and tied to specific dry-run evidence.

## Decision 5: Use Source-Controlled Install Inventory

**Decision**: Generate and commit an install inventory under
`speckit-pro/speckit_pro_runner/` that records expected Claude agents, Codex
agents, runner files, generated payload files, versions, manifests, and checksums.

**Rationale**: Doctor/preflight cannot depend on stale hardcoded bundled-agent
lists or live network discovery. A committed inventory gives deterministic
fixtures and reviewable source truth.

**Alternatives considered**:
- Discover install expectations from live plugin caches. Rejected because cache
  state is mutable user-local state.
- Keep expected-agent lists in tests only. Rejected because doctor/preflight
  needs the same source truth as the implementation.

## Decision 6: Promote Helpers Only After Golden and Bash-Reference Proof

**Decision**: A Bash-backed helper becomes Python-authoritative only after a
promotion record names golden fixture ids, Bash-reference comparison ids,
normalized fields, authoritative Python command, status, rollback guidance, and
deferred follow-up if any.

**Rationale**: Current Bash behavior is still shipped behavior until XPLAT-007.
Promotion records make parity review explicit and prevent tests from silently
becoming authoritative before comparison is accepted.

**Alternatives considered**:
- Trust Python tests alone. Rejected because parity with current helper behavior
  is a core success criterion.
- Compare against installed plugin behavior. Rejected because XPLAT-008 owns
  installed-cache proof.

## Decision 7: Ship Autopilot Phase-Coverage Validator as Proof, Not Prose

**Decision**: Keep `validate-autopilot-phase-coverage.py` as a Python
standard-library validator and require deterministic Layer 4 tests for a passing
workflow/state pair plus failures for missing Phase 6.5, missing Post items,
collapsed later phases, and malformed state JSON.

**Rationale**: The design concept explicitly rejects instruction-only
hardening. The validator must fail before a run advances if canonical phases or
post-implementation items are missing.

**Alternatives considered**:
- Rely on autopilot instructions and manual review. Rejected because prior
  failures can come from collapsed plan state, not missing prose.
- Validate only workflow Markdown. Rejected because `autopilot-state.json` is
  the durable execution state and can drift independently.

## Decision 8: Defer Active Cutover and Public Claims

**Decision**: XPLAT-006 does not change active Claude/Codex invocation paths,
hooks, generated-payload selection/cutover, install guidance, public docs,
repo-local release gates, native matrix UAT, installed-cache launch proof,
update/autoheal proof, or public platform support claims. The only allowed
skill/payload changes are the autopilot phase-coverage hardening source and
generated mirror.

**Rationale**: XPLAT-007 owns repo-local gate migration, and XPLAT-008 owns
active Claude/Codex cutover and native installed-plugin proof. Keeping the
boundary explicit protects users from premature public claims.

**Alternatives considered**:
- Switch generated-payload selection as helpers are ported. Rejected because
  promotion evidence must precede active cutover.
- Add public support docs in this spec. Rejected because native matrix UAT is
  explicitly out of scope.
