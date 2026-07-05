# Research: Python Tooling and Release-Gate Migration

## Decision 1: Classify Commands By Invocation Role

**Decision**: Classify files by how they are invoked, not by extension alone.
Active runner, workflow, release, install-verification, payload, and reachable
helper entrypoints are XPLAT-007 gates. Fixture files, Bash-reference manifests,
and historical evidence are temporary parity or archive evidence unless a
runner, workflow, or release check executes them. Installed Claude/Codex skill,
hook, generated release payload, public docs, update, autoheal, and native UAT
surfaces are XPLAT-008.

**Rationale**: The clarified spec requires the active-path guard to fail only
reachable active gate paths while still reporting nonblocking shell mentions.
Invocation-role classification avoids both false positives in archives and
false negatives in workflow or helper paths.

**Alternatives considered**:

- File-extension-only classification: rejected because fixtures and archives
  contain `.sh` text that is not active.
- Whole-repo no-shell failure: rejected because it would force broad historical
  rewrites outside XPLAT-007.

## Decision 2: Make Runner JSON-Envelope Operations Authoritative

**Decision**: Active migrated gates use `python -m speckit_pro_runner` request
envelopes as the authoritative command surface. The operation returns one JSON
response on stdout, line-delimited JSON diagnostics on stderr, and the existing
status-to-exit-code mapping. Standalone Python commands are allowed only for
unit/eval harnesses or explicitly justified non-authoritative wrappers that
reuse the same runner implementation.

**Rationale**: XPLAT-004 established the runner envelope and XPLAT-005/XPLAT-006
proved helper dispatch, typed paths, diagnostics, modes, and promotion records.
Using that surface for active gates gives one contract for tests, release
checks, install verification, and guardrails.

**Alternatives considered**:

- Dedicated Python scripts per retired Bash file: rejected because it would
  create multiple active command families and weaken release-contract review.
- Thin Bash wrappers around Python: rejected because active transition Bash
  entrypoints are explicitly out of scope.

## Decision 3: Promote Gates Only With Fixture And Bash-Reference Evidence

**Decision**: Each migrated gate needs golden fixture evidence and
source-checkout Bash-reference comparison before becoming Python-authoritative.
Promotion records name the prior Bash path, Python operation, fixture request,
failure classes, stdout/stderr/exit comparison mode, artifact hash or diff
result, rollback path, and Bash-reference retirement classification.

**Rationale**: The existing read-only and mutation fixture trees already use
request fixtures, Bash-reference manifests, contract schemas, promotion records,
and bounded subprocess policies. XPLAT-007 extends that pattern from helper
ports to active gate and release-readiness promotion.

**Alternatives considered**:

- Golden fixtures only: rejected for gates with current Bash behavior because
  reviewers need proof that pass/fail meaning did not drift.
- Keeping Bash comparison in release gates forever: rejected because Bash
  references are migration evidence, not long-term active release gates.

## Decision 4: Guard Scans Broadly But Blocks Only Active Paths

**Decision**: The no-shell/no-jq guard scans tracked text and emits classified
findings. It blocks only active repo-local gate and release paths:
`tests/speckit-pro/**` runner-invoked gates, `scripts/*` release helpers,
reachable `speckit-pro/**/scripts/**`, and plugin release/test workflows.
Nonblocking classifications include archive/provenance, consumer Spec Kit
helpers, temporary parity evidence, generated payload mirrors, docs out of
scope, CI dispatch glue, and XPLAT-008 cutover surfaces.

**Rationale**: The guard must be strong enough to prevent active Bash
reintroduction without turning XPLAT-007 into a broad cleanup of historical
process files.

**Alternatives considered**:

- Only scanning files declared in the implementation diff: rejected because
  stale active Bash references could remain elsewhere.
- Failing every Bash mention: rejected because the design concept explicitly
  preserves archive and parity evidence where it is not active.

## Decision 5: Test Payload Evidence Is Not Release Payload Cutover

**Decision**: XPLAT-007 may rebuild isolated Claude/Codex test payload evidence
under fixture or temporary output roots and record fingerprints. It must not
select, publish, or cut over generated release payloads.

**Rationale**: Release payload rebuild and active Claude/Codex invocation
selection are XPLAT-008 responsibilities. XPLAT-007 only needs enough payload
evidence to prove the Python builder and release checks work without Bash.

**Alternatives considered**:

- Rebuilding `dist/**` release payloads now: rejected because it would couple
  gate migration to installed cutover and public release readiness.
- Deferring all payload builder work: rejected because XPLAT-008 needs
  Python-authoritative payload evidence before it can cut over.

## Decision 6: CI Shell Is Dispatch Glue Only

**Decision**: CI workflows may retain shell mechanics only when a `run:` step
directly invokes `python -m speckit_pro_runner` or non-plugin docs tooling and
contains no plugin validation, packaging, install, release, `jq`, loop, or
parsing logic. Existing plugin `pr-checks.yml` and `release.yml` Bash/`jq` logic
is blocking until migrated to runner operations.

**Rationale**: GitHub Actions runs commands through a shell by default. XPLAT-007
does not need to replace the platform runner, but it must remove validation and
release logic from shell snippets.

**Alternatives considered**:

- Ban all workflow `run:` shell snippets: rejected as unnecessary platform
  churn when the shell only dispatches Python.
- Keep existing shell validation in CI: rejected because CI is an active
  release-readiness surface.

## Decision 7: Platform Proof Is Source-Checkout Only

**Decision**: XPLAT-007 platform proof is local macOS source-checkout smoke plus
deterministic Windows-style path, fake-home, traversal, backslash, line-ending,
and normalization fixtures. Installed-cache launch proof, native
Windows/macOS/Linux UAT, update, autoheal, and public platform claims remain
XPLAT-008.

**Rationale**: Session 4 clarification superseded older wording that assigned
installed-cache/native UAT proof to XPLAT-007. The accepted boundary is enough
to prove repo-local Python gates without implying installed plugin readiness.

**Alternatives considered**:

- Native matrix UAT in XPLAT-007: rejected because active Claude/Codex cutover
  and generated release payload selection have not happened yet.
- No platform fixtures: rejected because path and fake-home behavior are core
  risk areas for Python gate migration.

## Decision 8: Supersede Older XPLAT-004 Fixture Wording If Touched

**Decision**: Older XPLAT-004 platform runbook fixture text that says
installed-cache launch proof, native UAT, release-readiness, or public claim
audit remain XPLAT-007 scope is superseded by the post-PR #280 split and the
XPLAT-007 clarify consensus. If XPLAT-007 touches that fixture, annotate it to
state source-checkout proof only and defer installed-cache/native UAT to
XPLAT-008.

**Rationale**: The fixture is preserved historical evidence from XPLAT-004, but
the roadmap and clarify decisions now split final cutover into XPLAT-008.

**Alternatives considered**:

- Rewrite all old fixture wording now: rejected because broad historical
  rewrites are out of scope.
- Treat older wording as active scope: rejected because it conflicts with the
  current roadmap and clarify outcome.

## Decision 9: Keep One Workflow With Three Internal Slices

**Decision**: Continue as one XPLAT-007 workflow with the accepted review order:
test/eval gates, payload/install/release helpers, then active-path guardrails
and cleanup. The setup reviewability result remains `status=warn`,
`pass=true`, two primary surfaces, no blockers.

**Rationale**: Splitting now would separate the migration proof from the guard
and handoff evidence reviewers need. A split remains available before
implementation if tasks exceed the roadmap block thresholds.

**Alternatives considered**:

- Split immediately into three child specs: rejected because dependencies are
  sequential and the guard must validate the whole active path.
- Collapse slices into one undifferentiated implementation pass: rejected
  because test/eval gates must be authoritative before payload and release work.
