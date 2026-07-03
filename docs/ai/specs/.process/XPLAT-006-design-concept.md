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
- Use golden fixtures plus source-checkout Bash-reference comparison before
  promoting Python behavior for each Bash-backed mutation helper.
- Keep live repository, user-local, and GitHub mutations behind explicit
  approval and dry-run proof; default test coverage uses temporary fixtures and
  fake `gh`, `specify`, and Codex/Claude homes.
- Preserve active Claude/Codex cutover, generated-payload switching, public
  release docs, and native installed-cache UAT for later XPLAT specs.

## Non-Goals

- Do not update active Claude Code or Codex skill, hook, generated payload,
  install, or public documentation invocation paths.
- Do not replace repo-local Bash test/eval/build/payload/release gates; that is
  XPLAT-007.
- Do not run full native Windows/macOS/Linux installed-plugin UAT; that remains
  XPLAT-008.
- Do not re-port XPLAT-005 read-only helper modes. XPLAT-006 owns deferred
  write/apply modes and mutation-capable helpers only.
- Do not require live GitHub mutation, live plugin installation, or writes to
  the real user home as part of deterministic test coverage.
- Do not make public native-platform support claims.

## Accepted Slice Strategy

| Slice | Focus | Acceptance Boundary |
|---|---|---|
| Slice 1 | Mutation safety foundation | Add runner mutation mode contracts, dry-run/apply request and response shapes, atomic write helpers, dirty-worktree and path-boundary guards, failure classes, and fake-repo fixture harnesses before porting high-risk helpers |
| Slice 2 | Install completeness and doctor/preflight | Port install-curated-set, install-codex-agents, coach/preset write helpers, and manifest-driven doctor behavior using fake homes and generated inventory fixtures |
| Slice 3 | PR-emission, restack, migration, and relocation | Port generate-pr-body, generate-uat-skeleton, final-reviewability-backstop, multi-pr-emission, restack, migrate-structure, relocate-process-artifacts, and deferred write modes after Slice 1 and Slice 2 primitives are accepted |

Split into child specs only if Specify, Plan, or Tasks prove the three-slice
workflow cannot stay within the roadmap reviewability budget.

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

XPLAT-006 ports helpers, doctor contracts, fixtures, and Python gates. Active
skill, hook, generated-payload, install-guidance, and public-doc switching
remains XPLAT-008 after XPLAT-007 makes repo-local gates Python-authoritative.

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

## Open Questions For Clarify

- Exact helper and mode matrix: confirm which helpers are in Slice 2 versus
  Slice 3, and which mixed-mode write paths are deferred or out of scope.
- Mutation request model: decide how `mode`, `dry_run`, `apply`, planned
  operations, applied operations, rollback notes, and partial-failure records
  are represented in runner responses.
- Manifest source: decide the canonical source-controlled inventory for
  expected Claude/Codex agents, runner files, generated payload files, and
  release metadata.
- Doctor safe-repair boundary: define which missing or stale install states are
  auto-repairable and which require manual remediation.
- Atomic write policy: specify temp-file, fsync/rename, backup, and rollback
  behavior for helpers that currently promise safe writes or dry-run/apply
  semantics.
- PR/GitHub boundary: define which PR-emission and restack tests use fake `gh`,
  which paths can remain dry-run only, and what explicit approval is required
  for any live mutation.
- Platform fixture set: decide which Windows-style paths, spaces, symlinks,
  line endings, and permission cases belong in deterministic fixtures.

## Downstream Handoff

- XPLAT-007 should remove Bash from active repo-local tests, evals, payload
  builders, install verification, release checks, and release-readiness gates
  after XPLAT-006 ports mutation helper behavior.
- XPLAT-008 remains responsible for active Claude/Codex cutover, generated
  payload propagation, installed-cache launch proof, native Windows/macOS/Linux
  UAT, update/autoheal proof, public release docs, and public platform claims.
