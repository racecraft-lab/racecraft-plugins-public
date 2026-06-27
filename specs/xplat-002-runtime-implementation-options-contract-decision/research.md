# Research: Runtime Implementation Options and Contract Decision

## Decision: Use a gate-first weighted evidence matrix

**Rationale**: XPLAT-001 provides six must-have runtime gates and eight weighted
criteria. XPLAT-002 must first determine whether each candidate can satisfy the
installed-cache, native platform, path, JSON, subprocess, and packaging gates.
Only candidates that remain viable after gates should receive 0-5 weighted
criterion ratings.

**Alternatives considered**:

- Weighted scoring only: rejected because a high score could hide a hard
  installed-cache or native-platform failure.
- Narrative comparison only: rejected because reviewers need repeatable
  evidence and tie-breaker rationale.

## Decision: Evaluate exactly three selectable runtime families

**Rationale**: The selectable candidates are JavaScript/TypeScript, Python, and
small per-platform binary runner options. Temporary compatibility adapters may
be recorded, but they are migration records rather than a fourth selectable
runtime family.

**Alternatives considered**:

- Favor JavaScript/TypeScript first: rejected because it would preselect a
  likely winner before applying the XPLAT-001 rubric.
- Defer runtime selection to XPLAT-004: rejected because XPLAT-004 must receive
  one stable runtime and contract.

## Decision: Use official/runtime documentation plus bounded probes

**Rationale**: Candidate evidence must come from runtime/toolchain maintainers,
official plugin platform documentation, or repo-local source/manifests. When
invocation behavior is uncertain, implementation should add lightweight,
non-mutating probes for runtime availability, installed Claude plugin-cache
invocation, installed Codex plugin-cache invocation, JSON stdin/stdout behavior,
stderr/exit separation, path handling, and shell-free subprocess or
missing-command behavior.

Installed-cache invocation evidence is host-specific: installed Claude and
installed Codex plugin-cache probes, or explicit host-specific evidence gaps,
are required before actual installed-cache invocation can pass. Repo-local and
generated payload probes are useful setup evidence, but they cannot substitute
for cache invocation evidence because platform/plugin packaging separates
marketplace or repo sources from the installed plugin payload that executes at
runtime.

**Alternatives considered**:

- Documentation only: rejected because installed-cache behavior is the primary
  release risk.
- Full native UAT in this spec: rejected because release-readiness UAT belongs
  to XPLAT-007 after implementation and cutover.

## Decision: Make no-post-cache-install reliability a pass/fail gate

**Rationale**: The public plugin payload must run after cache population without
per-user dependency installation or network package restoration. A candidate
that requires `npm install`, `pip install`, `uv`, `brew`, or equivalent setup
after install cannot be the selected runtime model for this decision. Because
XPLAT-002 does not build `speckit-pro-runner`, this gate selects a viable
runtime model only; actual Claude/Codex installed-cache invocation proof remains
an XPLAT-004 acceptance item.

**Alternatives considered**:

- Allow common system runtimes with remediation text: rejected as the default
  because the XPLAT release blocker is first-run reliability for installed
  workflows.
- Prefer maintainer ergonomics as the tie-breaker: rejected because user
  install reliability outranks implementation convenience when candidates are
  otherwise close.

## Decision: Require structured fallback plans for unrun probes

**Rationale**: XPLAT-002 may not be able to run every host/runtime probe from a
single local environment, but missing probes must remain reviewable evidence
gaps rather than implied reliability passes. Each unrun required probe should
record the missing probe, host/runtime scope, reason unavailable, substitute
official or repo-local evidence consulted, gate or scoring effect, owner, and
expiry/removal or follow-up condition.

**Alternatives considered**:

- Treat unrun probes as neutral: rejected because it can let source-only or
  documentation-only evidence pass actual installed-cache invocation silently.
- Block the decision on every unavailable local host: rejected because native
  release-readiness UAT belongs to XPLAT-007, but the gap still needs an owner
  and scoring effect.

## Decision: Define close-candidate tie-breakers objectively

**Rationale**: The XPLAT-001 rubric has explicit weights, so "otherwise close"
must be measurable before install reliability is used as the tie-breaker.
Candidates are close only when they have no selection-blocking gate failures and
their weighted totals differ by five points or less, or when the leading score
depends only on maintainer ergonomics or compatibility-adapter criteria while
reliability criteria are tied or favor another candidate. Close candidates are
then compared in this order: installed Claude cache probe status, installed
Codex cache probe status, post-cache setup burden, offline behavior after cache
population, first-run/bootstrap failure diagnostics, and runtime-info/preflight
completeness.

**Alternatives considered**:

- Use narrative judgment for close candidates: rejected because reviewers could
  not reproduce the selection from evidence records.
- Let maintainer ergonomics break close ties first: rejected because the setup
  decision explicitly accepted user install reliability as the tie-breaker.
- Force a winner when reliability inputs remain tied: rejected because an
  unresolved tie should be visible for consensus instead of hidden in rationale.

## Decision: Define one `speckit-pro-runner` command contract

**Rationale**: XPLAT-004 needs a precise command target. The contract uses the
canonical entrypoint `speckit-pro-runner`, defaulting to the payload-relative
path `scripts/speckit-pro-runner` unless XPLAT-004 deliberately creates a
`bin/` convention. Helper execution uses one versioned JSON request on stdin,
one versioned JSON response on stdout, and deterministic line-delimited JSON
diagnostics on stderr.

Helper dispatch is part of the process boundary: `helper_id`, `operation`, and
`mode` resolve to runner-owned implementations under the installed plugin
payload/cache root. Source checkout paths may appear as evidence, but the
contract must not rely on them for installed Claude or Codex invocation.

**Alternatives considered**:

- Helper-specific CLI arguments: rejected because shell quoting and argument
  parsing are part of the current portability problem.
- Library-first internal API: rejected because installed Claude and Codex
  payloads need a stable command entrypoint and fixtureable process boundary.

## Decision: Use a shared exit-code and diagnostic map

**Rationale**: The runner contract must map outcomes consistently:
`0=ok`, `1=expected helper/domain failure`, `2=input envelope/usage/schema
error`, `3=missing prerequisite`, `4=subprocess failure or timeout`, and
`5=unexpected internal failure`. Legacy helper-specific codes are preserved in
`legacy_exit_code` only when parity requires them. Fixture authors also need
stable diagnostic codes for malformed JSON, missing fields, missing
prerequisites, subprocess nonzero, timeout, stderr-only failure, and internal
failure so stdout/stderr/exit assertions can be built from the contract text.

**Alternatives considered**:

- Preserve every legacy helper exit code as the process exit code: rejected
  because it prevents a shared command contract and makes cross-helper fixture
  parity harder.
- Collapse all failures to one nonzero code: rejected because users and tests
  need clear missing-prerequisite, input, subprocess, and internal-failure
  distinctions.

## Decision: Model compatibility adapters as temporary owner-first records

**Rationale**: Compatibility adapter records are migration notes, not runtime
candidates. IDs use owner-first values such as
`xplat-005-compat-<legacy-helper-or-surface-slug>` and include explicit
`owner_spec`, `removal_spec`, and `removal_condition` fields so temporary
compatibility does not become permanent architecture.

**Alternatives considered**:

- Treat adapters as a runtime family: rejected because they would only delegate
  to existing shell behavior and would not satisfy the replacement-runtime
  decision.
- Omit adapters until implementation: rejected because XPLAT-004 needs
  traceable migration boundaries.

## Decision: Hand XPLAT-004 a row-derived implementation input bundle

**Rationale**: XPLAT-001 rows are the authoritative inventory of active runtime
surfaces, owner buckets, and invocation-mode boundaries. XPLAT-004 needs those
rows normalized into build inputs instead of inferring work from repository path
searches. The input bundle maps XPLAT-001 row IDs to runner helper IDs,
operations, modes, adapter records, fixture expectations, and explicit
exclusions.

**Alternatives considered**:

- Let XPLAT-004 re-scan the source tree: rejected because it can recreate the
  source-checkout assumption and drift from XPLAT-001 owner decisions.
- Hand off only prose summaries: rejected because adapter and fixture parity
  work need row-level traceability.

## Decision: Hand supply-chain implications to XPLAT-003 only

**Rationale**: XPLAT-002 records a per-candidate supply-chain implication matrix
covering dependency footprint, manifest and lockfile behavior, generated
artifact shape, build/release path, scanning path, checksum/signature/SBOM/
provenance feasibility, local verification ideas, offline/update behavior,
trust root, native/build-time dependencies, execution risk, maintenance posture,
assumption status, and evidence gaps. The matrix distinguishes evidence-backed
facts from assumptions for vendored packages, embedded runtimes, native binaries,
generated payload artifacts, lockfiles/manifests, and package-manager behavior.
Unknown or unverified assumptions stay as XPLAT-003 evidence gaps; XPLAT-003
chooses actual controls.

**Alternatives considered**:

- Select first-release controls in XPLAT-002: rejected because the roadmap
  assigns the security/control decision to XPLAT-003.
- Ignore rejected candidates in the supply-chain matrix: rejected because
  rejection rationale and future audits need the same implication visibility.

## Decision: Keep public support claims out of scope

**Rationale**: XPLAT-002 may record decision, target, candidate-evidence, and
handoff wording only. README, docs-site pages, marketplace metadata, changelog,
release notes, and similar public support-claim surfaces stay unchanged until
XPLAT-007 validates native release readiness.

**Alternatives considered**:

- Publish a public preview caveat: rejected because it is unnecessary for a
  decision spike and could be confused with support readiness.
- Update support claims with the selected runtime: rejected because no runner,
  cutover, or native UAT exists yet.

## Evidence Matrix Shape

| Candidate Family | Must-Have Gates | Weighted Criteria | Required Evidence | Decision Output |
|---|---|---|---|---|
| JavaScript/TypeScript | Installed-cache invocation, native behavior, paths, JSON, subprocess, packaging | XPLAT-001 weights totaling 100 | Official runtime/toolchain docs, plugin platform docs or repo manifests, installed Claude/Codex cache probes or host-specific evidence gaps when uncertain | Selected or rejected with rationale |
| Python | Same gates | Same weights | Same evidence standard | Selected or rejected with rationale |
| Small per-platform binary runner | Same gates | Same weights | Same evidence standard | Selected or rejected with rationale |

## Probe Plan

Implementation should record probe results or evidence gaps for:

1. Runtime availability and version reporting.
2. Installed Claude plugin-cache invocation path and installed Codex
   plugin-cache invocation path, plus any supplemental source or generated
   payload invocation path used to explain setup.
3. JSON stdin/stdout success and malformed input behavior.
4. Stderr-only diagnostic emission and process exit separation.
5. Path-with-spaces and Windows separator handling.
6. Structured argv subprocess success, nonzero, timeout, and missing-command
   behavior with shell disabled.

If a required local probe cannot be run, record a structured evidence-gap
fallback plan with the missing probe, host/runtime scope, reason unavailable,
substitute evidence consulted, gate or scoring effect, owner, and expiry/removal
or follow-up condition. Installed-cache evidence gaps cannot be scored as
installed-cache probe passes.

All probes must be non-mutating and must not become shipped runner behavior.
