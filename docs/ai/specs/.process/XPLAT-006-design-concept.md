# Design Concept: XPLAT-006 Mutation, Install, and PR-Emission Helper Port

**Spec ID:** XPLAT-006
**Spec Name:** Mutation, Install, and PR-Emission Helper Port
**Branch:** `codex/xplat-006-mutation-install-pr-emission-helper-port`
**Created:** 2026-07-03
**Source Roadmap:** `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`

## Setup Context

XPLAT-006 starts after XPLAT-004 shipped the Python 3.11+ standard-library
runner foundation and XPLAT-005 shipped the read-only helper registry, fixture
parity pattern, and Python helper tests. The roadmap marks XPLAT-006 ready and
assigns it the state-mutating helper migration: file-writing helpers, install
and repair helpers, PR packet/body helpers, split-PR state, restack operations,
structure migration, process-artifact relocation, and coach/preset helpers that
write files.

The setup reviewability gate returned `status=warn`, `pass=true`,
`reviewable_loc=250`, `production_files=4`, `total_files=10`, and warned that
two primary surfaces (`docs/process` and `harness/adapter`) exceed the
one-surface warning threshold. The accepted setup direction is one XPLAT-006
workflow with three internal implementation slices.

## Goals

- Port mutation-capable plugin helpers onto the XPLAT runner while preserving
  current JSON stdout schemas, human-readable diagnostics, and exit-code
  behavior.
- Establish safe mutation primitives for dry-run/apply behavior, atomic writes,
  dirty-worktree checks, partial-failure reporting, rollback notes, and typed
  path boundaries.
- Add manifest-driven install completeness and doctor/preflight behavior that
  verifies bundled Claude/Codex agents, runner files, generated payload files,
  and safe repair cases from source-controlled inventory.
- Port PR-emission, restack, migration, relocation, UAT, and final-reviewability
  helper behavior with deterministic fake-repo and fake-CLI fixtures.
- Harden Codex autopilot phase tracking so a workflow/state pair cannot silently
  omit Phase 6.5, collapse later phase families, or drop canonical Post items
  without a deterministic Python validation failure.
- Use golden fixtures plus source-checkout Bash-reference comparison before
  promoting Python behavior for each Bash-backed mutation helper.
- Keep live repository, user-local, and GitHub mutations behind explicit
  approval and dry-run proof; default test coverage uses temporary fixtures and
  fake `gh`, `specify`, and Codex/Claude homes.
- Preserve active Claude/Codex cutover, generated-payload selection/cutover, public
  release docs, and native installed-cache UAT for later XPLAT specs, except
  for the explicit autopilot phase-coverage hardening source/payload mirror.

## Non-Goals

- Do not update active Claude Code or Codex invocation paths, hook behavior,
  generated-payload selection/cutover behavior, install guidance, or public
  documentation claims; phase-coverage hardening may update autopilot
  instructions and generated mirrors without changing invocation behavior.
- Do not replace repo-local Bash test/eval/build/payload/release gates; that is
  XPLAT-007.
- Do not run full native Windows/macOS/Linux installed-plugin UAT; that remains
  XPLAT-008.
- Do not re-port XPLAT-005 read-only helper modes. XPLAT-006 owns deferred
  write/apply modes and mutation-capable helpers only.
- Do not require live GitHub mutation, live plugin installation, or writes to
  the real user home as part of deterministic test coverage.
- Do not make public native-platform support claims.
- Do not treat updated instructions as sufficient hardening without a validator
  and failing regression fixtures.

## Accepted Slice Strategy

| Slice | Focus | Acceptance Boundary |
|---|---|---|
| Slice 1 | Mutation safety foundation | Add runner mutation mode contracts, dry-run/apply request and response shapes, atomic write helpers, dirty-worktree and path-boundary guards, failure classes, and fake-repo fixture harnesses before porting high-risk helpers |
| Slice 2 | Install completeness and doctor/preflight | Port install-curated-set, install-codex-agents, coach/preset write helpers, and manifest-driven doctor behavior using fake homes and generated inventory fixtures |
| Slice 3 | PR-emission, restack, migration, relocation, and autopilot hardening | Port generate-pr-body, generate-uat-skeleton, final-reviewability-backstop, multi-pr-emission, restack, migrate-structure, relocate-process-artifacts, deferred write modes, and deterministic Codex autopilot phase-coverage validation after Slice 1 and Slice 2 primitives are accepted |

Split into child specs only if Specify, Plan, or Tasks prove the three-slice
workflow cannot stay within the roadmap reviewability budget.

Clarify session 1 resolved the helper/mode matrix without adding clarification
markers: Slice 1 remains shared mutation foundation only; Slice 2 owns
install/doctor/coach/preset writes; Slice 3 owns PR-emission, restack,
migration, relocation, generated write modes, and `detect-stack-manager`
support. XPLAT-005 read-only modes are already accepted and are not re-ported;
XPLAT-007 owns active repo-local gate migration and XPLAT-008 owns active
Claude/Codex cutover, generated-payload selection/cutover, installed-cache/native UAT,
update/autoheal proof, and public support claims.

## Grill Me Q&A Log

### Q1. How should XPLAT-006 be scoped for reviewability?

**Accepted answer:** One workflow, three slices.

Use one XPLAT-006 workflow and branch, but separate review order into mutation
safety foundation, install/doctor behavior, and PR/restack/relocation behavior.

### Q2. Which helper group should XPLAT-006 port first?

**Accepted answer:** Mutation safety foundation.

Start with dry-run/apply envelopes, atomic write rules, path boundaries,
dirty-worktree checks, failure classes, and fixture harnesses so higher-risk
helpers do not each invent their own mutation semantics.

### Q3. What install and doctor scope belongs in XPLAT-006?

**Accepted answer:** Manifest-driven doctor.

Verify expected bundled agents, runner files, generated payload files, stale
release indicators, and safe repair cases from source-controlled manifests or
generated inventory. Avoid stale hardcoded expected-agent lists.

### Q4. What parity bar should XPLAT-006 require before promoting a mutation helper?

**Accepted answer:** Fixtures plus Bash comparison.

Use deterministic fake repositories and fake user homes plus source-checkout
Bash-reference comparisons for dry-run, apply, no-op, invalid-input,
missing-prerequisite, dirty-worktree, and partial-failure paths.

### Q5. How should XPLAT-006 handle live repo, user-local, or GitHub mutations?

**Accepted answer:** Fake by default.

Default all deterministic coverage to temp repos, fake `gh`, fake `specify`,
and fake Codex/Claude homes. Live mutation is allowed only behind explicit
operator approval and after dry-run evidence exists.

### Q6. Should XPLAT-006 change active Claude/Codex invocations?

**Accepted answer:** No active cutover.

XPLAT-006 ports helpers, doctor contracts, fixtures, Python gates, and the
autopilot phase-coverage hardening needed by this PR. Active skill invocation
paths, hook behavior, generated-payload selection, install-guidance, and
public-doc switching remain XPLAT-008 after XPLAT-007 makes repo-local gates
Python-authoritative.

### Q7. How should XPLAT-006 handle helpers that have both read-only and write/apply modes?

**Accepted answer:** Write modes only.

Rely on XPLAT-005 for already accepted read-only validation modes. XPLAT-006
owns deferred write/apply behavior and must label each mixed-mode helper
unambiguously so the implementation does not duplicate XPLAT-005.

### Q8. What platform proof belongs in XPLAT-006?

**Accepted answer:** Source checkout proof.

Use local macOS source-checkout mutation fixtures plus Windows-style path
fixtures to prove runner path handling and write safety. Installed-cache launch
proof and native matrix UAT remain XPLAT-008.

### Q9. What autopilot phase-coverage hardening is required?

**Accepted answer:** Python validator plus regression proof.

Add a Python standard-library validator that checks the workflow file and
`autopilot-state.json` for Phase 6.5, every canonical phase family, the full
Post list, valid ordering, duplicate plan steps, and multiple `in_progress`
items. The PR packet must include focused test output for passing and failing
fixtures instead of assuming instruction text is enough.

## Open Questions For Clarify

- Exact helper and mode matrix: resolved by Clarify session 1. Slice 1 is
  shared mutation foundation only; Slice 2 owns install/doctor/coach/preset
  writes; Slice 3 owns PR/restack/migration/relocation/generated write modes
  plus `detect-stack-manager` support; XPLAT-005 read-only modes are not
  re-ported.
- Mutation request model: resolved by Clarify session 2. Mutation helpers keep
  the stable runner envelope and report mutation details under `data.mutation`,
  including mode, planned/applied/skipped operations, path evidence, dirty state,
  failure operation, rollback notes, and remediation actions.
- Manifest source: resolved by Clarify session 3. Use a committed generated
  inventory under `speckit-pro/speckit_pro_runner/` for expected Claude/Codex
  agents, runner files, generated payload files, checksums, plugin versions,
  marketplace versions, runner metadata, and release metadata.
- Doctor safe-repair boundary: resolved by Clarify session 3. Doctor/preflight
  is read-only by default; repair is a separate apply-mode operation after
  dry-run evidence and approval, and safe repair is limited to fake or explicitly
  approved declared boundaries.
- Atomic write policy: resolved by Clarify session 2. File writes generate
  complete content before opening the target, use same-directory temporary files,
  validate and flush/fsync before `os.replace`, and report partial failure rather
  than promising global rollback.
- PR/GitHub boundary: resolved by Clarify session 4. Candidate PR emission is
  dry-run command capture, fake PR/restack fixtures may exercise apply paths,
  live GitHub/repo mutation requires structured approval evidence after dry-run
  and clean-worktree checks, `detect-stack-manager` emits decisions only, and
  known gaps must distinguish unpromoted helpers, deferred XPLAT-007/XPLAT-008
  cutover, and live-coverage limits.
- Platform fixture set: partially resolved by Clarify sessions 2 and 3 for path,
  symlink, dirty-worktree, no-op, line-ending, complete install, missing agent,
  stale cache, downgrade refusal, missing runner file, checksum mismatch,
  malformed inventory, missing fake CLI, real-home refusal, fake PR/restack
  apply, dry-run command capture, approval rejection, and autopilot
  phase-coverage regression fixtures.

## Downstream Handoff

- XPLAT-007 should remove Bash from active repo-local tests, evals, payload
  builders, install verification, release checks, and release-readiness gates
  after XPLAT-006 ports mutation helper behavior.
- XPLAT-008 remains responsible for active Claude/Codex cutover,
  generated-payload selection/cutover, installed-cache launch proof, native Windows/macOS/Linux
  UAT, update/autoheal proof, public release docs, and public platform claims.
