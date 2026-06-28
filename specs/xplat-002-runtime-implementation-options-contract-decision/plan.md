# Implementation Plan: Runtime Implementation Options and Contract Decision

**Branch**: `codex/xplat-002-runtime-implementation-options-contract-decision` | **Date**: 2026-06-26 | **Spec**: `specs/xplat-002-runtime-implementation-options-contract-decision/spec.md`

**Input**: Feature specification from `specs/xplat-002-runtime-implementation-options-contract-decision/spec.md`

## Summary

XPLAT-002 is a research and decision spike that historically compared
JavaScript/TypeScript, Python, and small per-platform binary runner options
against the XPLAT-001 runtime rubric, then produced one selected runtime
decision and one `speckit-pro-runner` command contract for XPLAT-004. The
amended decision selects a Python standard-library runner aligned with official
Spec Kit / `specify` prerequisites. Compiled per-platform binaries are rejected
historical evidence only, not a fallback, compatibility adapter, or downstream
implementation input. The plan uses a gate-first weighted evidence matrix,
lightweight non-mutating probes where invocation behavior is uncertain, and
explicit handoff notes for XPLAT-003 and XPLAT-004. It does not build the
runner, port helper behavior, change active installed invocation paths, or
update public native-platform support claims.

## Technical Context

**Language/Version**: Historical decision-stage evidence covered
JavaScript/TypeScript, Python, and small per-platform binary runner options.
The amended selected runtime is Python 3.11+ standard library through the
official Spec Kit / `specify` prerequisite boundary.

**Primary Dependencies**: No new runtime dependency is planned in the Plan
phase. Candidate evaluation must record dependency/bootstrap footprint and
evidence-backed versus assumed artifact shape for each runtime family, and must
treat installed-cache no-install behavior as a pass/fail gate.

**Storage**: Checked-in Markdown decision artifacts, contract documents, and
optional lightweight probe evidence only; no database, browser storage, or
runtime service state.

**Testing**: Markdown/static validation, marker scans, git diff hygiene,
candidate probe commands recorded in the decision evidence, installed Claude
and Codex plugin-cache invocation evidence or host-specific evidence gaps, and
the relevant deterministic shell suite when source maps or helper scripts are
touched.

**Target Platform**: Installed Claude and Codex plugin cache paths, with native
Windows, macOS, and Linux behavior evaluated through official/runtime
documentation and bounded local or installed-cache probes.

**Project Type**: Plugin marketplace decision spike and CLI command-contract
definition for future installed plugin helper ports.

**Performance Goals**: First-run reliability from a populated installed cache;
deterministic JSON stdin/stdout and stderr separation; subprocess timeouts and
diagnostics that support fixture parity. No throughput or latency optimization
is in scope.

**Constraints**: One decision spike; preserve the historical candidate evidence
while selecting one canonical runtime and command contract; no compiled binary
fallback, compatibility adapter, or downstream implementation input; no
per-user dependency installation, network package restoration, `npm install`,
`pip install`, `uv`, `brew`, or equivalent after cache population; no shell,
`.sh`, `jq`, globbing, redirection, or shell interpolation fallback in the
selected contract; dependency or artifact assumptions are recorded as XPLAT-003
implications, not accepted security controls; no public native-platform
support-claim edits.

**Scale/Scope**: One feature directory with Plan artifacts and later decision
evidence. Active runtime surfaces are source skills/hooks/agents/scripts and
generated Claude/Codex payloads identified by XPLAT-001, but this spec records
decision and handoff evidence only.

**Reviewability Budget**: Setup gate warning accepted: 250 projected reviewable
LOC, 4 production files, 10 total files, 2 primary surfaces (`docs/process`,
`harness/adapter`), no blockers. The warning is recorded because two primary
surfaces exceed the warn threshold of one primary surface.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Plan Assessment | Status |
|---|---|---|
| I. Plugin Structure Compliance | The Plan phase adds only feature-directory planning artifacts and the command-required agent context pointer. It does not change plugin manifests, installed runtime behavior, generated payload invocation paths, or public support-claim surfaces. | Pass |
| II. Script Safety | No shipped runtime helper or durable mutating script is created in Plan. If implementation adds probe commands as durable artifacts, they must be non-mutating, quoted, and syntax-checkable. | Pass |
| III. Semantic Versioning | No plugin version or release automation file is changed. | Pass |
| IV. Test Coverage Before Merge | Implementation must verify decision evidence, marker cleanup, spec-map freshness if affected, diff hygiene, and any committed probe script syntax. No runner tests are required before a runner exists. | Pass |
| V. Conventional Commits | No commit is created in this phase. Any later PR title or commit must follow repository conventional commit rules. | Pass |
| VI. KISS, Simplicity & YAGNI | The design uses a simple evidence matrix and one command contract. It explicitly avoids speculative runner abstractions, helper ports, and public claim updates. | Pass |

**Reviewability gate**: Warn/pass. Two primary surfaces were recorded during
setup, with no blockers. The accepted warning does not split this decision
spike because the scaffold estimate is `status=ok`, `suggested_slices=1`, and
implementation, supply-chain controls, helper ports, generated-payload cutover,
and release UAT remain assigned to later XPLAT specs.

## Project Structure

### Documentation (this feature)

```text
specs/xplat-002-runtime-implementation-options-contract-decision/
├── SPEC-MOC.md
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── speckit-pro-runner-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
docs/ai/research/
└── cross-platform-runtime-inventory.md

docs/ai/specs/.process/
├── XPLAT-002-design-concept.md
└── XPLAT-002-workflow.md

speckit-pro/
├── skills/
├── codex-skills/
├── agents/
├── codex-agents/
├── hooks/
├── codex-hooks.json
└── scripts/

dist/
├── claude/speckit-pro/
└── codex/speckit-pro/
```

**Structure Decision**: Keep Plan outputs under the XPLAT-002 feature
directory. Use XPLAT-001 and the design concept as read-only source evidence.
Do not alter source runtime surfaces, generated payloads, README, docs-site
pages, marketplace metadata, changelog, release notes, or public support-claim
surfaces in this phase.

## Phase 0 Research Plan

Research resolves planning decisions and preserves the historical candidate
evidence that led to the amended Python runtime selection. The implementation
phase of XPLAT-002 collected the candidate evidence; the 2026-06-28 amendment
marks compiled binaries as rejected historical evidence only.

1. Preserve the XPLAT-001 must-have gate results for JavaScript/TypeScript,
   Python, and the rejected small per-platform binary path before scoring
   weighted criteria.
2. Record documentation evidence from runtime/toolchain maintainers, official
   plugin platform documentation, or repo-local source/manifests for each
   candidate family.
3. Use lightweight, non-mutating probes only where invocation behavior is
   uncertain: runtime availability/version, installed Claude plugin-cache
   invocation, installed Codex plugin-cache invocation, JSON stdin/stdout,
   stderr/exit separation, path-with-spaces, and shell-free subprocess or
   missing-command behavior. Source and generated-payload probes may supplement
   setup evidence, but they do not replace host-specific installed-cache
   evidence or evidence gaps.
4. When a required probe cannot be run locally, record a structured fallback
   plan with the missing probe, host/runtime scope, reason unavailable,
   substitute official or repo-local evidence consulted, gate or scoring effect,
   owner, and expiry/removal or follow-up condition. Do not score an evidence
   gap as an installed-cache probe pass.
5. Treat no-post-cache-install reliability as a pass/fail gate for runtime-model
   selection and the tie-breaker when candidates are objectively close. Actual
   installed-cache invocation proof remains downstream because the Python runner
   source is intentionally out of XPLAT-002 scope. Close means no selection-blocking gate
   failures plus either weighted totals within five points or a lead based only
   on maintainer ergonomics or compatibility-adapter criteria while reliability
   criteria are tied or favor another candidate.
6. Apply close-candidate reliability tie-breakers from measurable evidence in
   this order before maintainer preference: installed Claude cache probe status,
   installed Codex cache probe status, post-cache setup burden, offline behavior,
   first-run/bootstrap failure diagnostics, and runtime-info/preflight
   completeness. Record the comparison as unresolved if those inputs do not
   produce a winner.
7. Record documentation/probe conflicts explicitly. Installed-cache probe
   evidence controls invocation-reliability scoring; official documentation
   controls general runtime claims.
8. Record a per-candidate supply-chain implication matrix for XPLAT-003 without
   selecting controls.

## Phase 1 Design Plan

1. Model runtime candidates, evidence records, rubric results, command
   envelopes, path values, subprocess results, runtime-info responses,
   compatibility adapter records, supply-chain implications, and handoff items.
2. Define the `speckit-pro-runner` command contract as the stable handoff shape:
   JSON request on stdin, one JSON response on stdout, line-delimited JSON
   diagnostics on stderr, explicit exit-code categories, typed paths,
   shell-disabled subprocess execution, installed-payload helper dispatch,
   runtime-info/preflight reporting, and fixture-level status/exit/diagnostic
   assertions for malformed envelopes and subprocess failures.
3. Define temporary compatibility adapter records as migration evidence only,
   using owner-first IDs such as `xplat-005-compat-<legacy-helper-or-surface-slug>`
   with explicit `owner_spec`, `removal_spec`, and `removal_condition` fields.
4. Define an XPLAT-004 implementation input bundle that maps XPLAT-001 row IDs,
   owner buckets, active invocation modes, runner helper IDs, operations/modes,
   adapter records, fixture expectations, and explicit exclusions without
   requiring source-checkout paths.
5. Define quickstart validation around artifact review, marker scans, diff
   hygiene, and candidate probe evidence review. Do not add runner implementation
   commands.

## Post-Design Constitution Check

| Principle | Design Assessment | Status |
|---|---|---|
| I. Plugin Structure Compliance | Generated artifacts are planning documents and one contract document under the feature directory. | Pass |
| II. Script Safety | No durable script is added. Future probe scripts, if any, must be non-mutating and syntax-checked. | Pass |
| III. Semantic Versioning | No versioned plugin metadata is changed. | Pass |
| IV. Test Coverage Before Merge | Quickstart names static and focused checks appropriate for a decision spike. | Pass |
| V. Conventional Commits | No commit is created by Plan. | Pass |
| VI. KISS, Simplicity & YAGNI | One matrix, one contract, and one downstream handoff path avoid speculative implementation structure. | Pass |

No unjustified constitution violations remain.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| None | N/A | N/A |
