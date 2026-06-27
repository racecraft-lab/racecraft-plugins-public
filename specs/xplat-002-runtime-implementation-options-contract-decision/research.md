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
non-mutating probes for runtime availability, source or installed-cache
invocation, JSON stdin/stdout behavior, stderr/exit separation, path handling,
and shell-free subprocess or missing-command behavior.

**Alternatives considered**:

- Documentation only: rejected because installed-cache behavior is the primary
  release risk.
- Full native UAT in this spec: rejected because release-readiness UAT belongs
  to XPLAT-007 after implementation and cutover.

## Decision: Make installed-cache reliability a pass/fail gate

**Rationale**: The public plugin payload must run after cache population without
per-user dependency installation or network package restoration. A candidate
that requires `npm install`, `pip install`, `uv`, `brew`, or equivalent setup
after install cannot be the selected runtime for this decision.

**Alternatives considered**:

- Allow common system runtimes with remediation text: rejected as the default
  because the XPLAT release blocker is first-run reliability for installed
  workflows.
- Prefer maintainer ergonomics as the tie-breaker: rejected because user
  install reliability outranks implementation convenience when candidates are
  otherwise close.

## Decision: Define one `speckit-pro-runner` command contract

**Rationale**: XPLAT-004 needs a precise command target. The contract uses the
canonical entrypoint `speckit-pro-runner`, defaulting to the payload-relative
path `scripts/speckit-pro-runner` unless XPLAT-004 deliberately creates a
`bin/` convention. Helper execution uses one versioned JSON request on stdin,
one versioned JSON response on stdout, and deterministic line-delimited JSON
diagnostics on stderr.

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
`legacy_exit_code` only when parity requires them.

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

## Decision: Hand supply-chain implications to XPLAT-003 only

**Rationale**: XPLAT-002 records a per-candidate supply-chain implication matrix
covering dependency footprint, manifest and lockfile behavior, generated
artifact shape, build/release path, scanning path, checksum/signature/SBOM/
provenance feasibility, local verification ideas, offline/update behavior,
trust root, native/build-time dependencies, execution risk, maintenance posture,
and evidence gaps. XPLAT-003 chooses actual controls.

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
| JavaScript/TypeScript | Installed-cache invocation, native behavior, paths, JSON, subprocess, packaging | XPLAT-001 weights totaling 100 | Official runtime/toolchain docs, plugin platform docs or repo manifests, bounded probes when uncertain | Selected or rejected with rationale |
| Python | Same gates | Same weights | Same evidence standard | Selected or rejected with rationale |
| Small per-platform binary runner | Same gates | Same weights | Same evidence standard | Selected or rejected with rationale |

## Probe Plan

Implementation should record probe results or evidence gaps for:

1. Runtime availability and version reporting.
2. Source and installed-cache or generated-payload invocation path.
3. JSON stdin/stdout success and malformed input behavior.
4. Stderr-only diagnostic emission and process exit separation.
5. Path-with-spaces and Windows separator handling.
6. Structured argv subprocess success, nonzero, timeout, and missing-command
   behavior with shell disabled.

All probes must be non-mutating and must not become shipped runner behavior.
