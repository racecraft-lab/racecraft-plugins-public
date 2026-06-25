# Implementation Plan: Runtime Inventory and Constraints

**Branch**: `codex/xplat-001-runtime-inventory-constraints` | **Date**: 2026-06-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/xplat-001-runtime-inventory-constraints/spec.md`

## Summary

XPLAT-001 produces a source-traceable inventory report and non-scoring runtime
and supply-chain rubrics for the cross-platform plugin runtime lane. The work is
a static docs/process spike: use repo-local scans and invocation-trace review to
classify Bash, `.sh`, `jq`, shell quoting, Unix-path, `chmod`, and line-ending
assumptions across tracked text files, then publish one Markdown report under
`docs/ai/research/` without changing installed runtime behavior.

## Technical Context

**Language/Version**: Markdown report artifacts plus repo-local shell/ripgrep
commands used as transient verification inputs.

**Primary Dependencies**: Existing Git repository metadata, tracked text files,
`rg`/Git scans, and existing SpecKit Pro helper scripts. No new runtime
dependency is planned.

**Storage**: Checked-in Markdown only. No database, browser storage, generated
JSON, or CSV artifact is planned.

**Testing**: Static verification only: rerun documented scan commands, verify
invocation traces in the report, run
`speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"`,
and run `git diff --check`.

**Target Platform**: Repository review workflow for installed Claude Code and
Codex plugin surfaces; no native Windows/macOS/Linux runtime probe in this spec.

**Project Type**: Claude Code and Codex plugin marketplace docs/process spike.

**Performance Goals**: The inventory must cover 100% of scoped scan matches or
explain exclusions; no runtime performance requirement is introduced.

**Constraints**: Do not score or select runtime/security candidates, port
helpers, change active Claude/Codex invocations, rebuild generated payloads, or
claim native Windows support.

**Scale/Scope**: Whole-repo tracked-text scan, including hidden tracked paths,
`dist/**`, public docs, tests, fixtures, and archive reports. Exclude `.git/`,
binary assets, untracked files, vendor caches, and non-text inputs with
rationale.

**Reviewability Budget**: Primary surface: docs/process. Secondary surface:
harness/adapter evidence only when documenting scan or traceability method.
Projected reviewable LOC: 250. Projected production files: 4. Projected total
files: 10. Budget result: warning accepted because setup identified two primary
surfaces (`docs/process`, `harness/adapter`) where the warn threshold is one.
Split decision: keep one spike because XPLAT-001 only inventories and defines
rubrics; implementation, runtime choice, supply-chain choice, cutover, and UAT
belong to later XPLAT specs.

## Declared File Operations

- NEW docs/ai/research/cross-platform-runtime-inventory.md
- MODIFIED docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Result |
|-----------|------|--------|
| Plugin Structure Compliance | XPLAT-001 must not change installed plugin runtime behavior, generated payloads, active skill invocations, agents, or hooks. | Pass: planned changes are a Markdown research report plus roadmap progress/handoff note. |
| Script Safety | Scan commands are transient review inputs, not a new automation layer or shipped helper. | Pass: no new helper script is planned; any command used must be recorded in the report. |
| Test Coverage Before Merge | Static checks must verify report coverage, traceability, spec-index freshness, and diff hygiene. | Pass: verification plan uses rerun scans, invocation-trace review, spec-index check, and `git diff --check`. |
| Conventional Commits | Commit/PR review packet must explain scope, non-goals, review order, budget, traceability, verification, known gaps, and rollback. | Pass: PR packet requirements remain in `spec.md` and will be carried into tasks. |
| KISS, Simplicity, YAGNI | Prefer repo-local scans and Markdown tables; avoid JSON/CSV and automation unless clearly necessary. | Pass: no machine-readable artifact is planned because Markdown tables satisfy review and handoff needs. |

Reviewability warning recorded: setup returned `status: warn` with
`primary_surface_count: 2` for `docs/process` and `harness/adapter`. The warning
does not block this phase because the actual slice remains a docs/process spike
and the secondary surface is only evidence classification, not helper
implementation.

## Project Structure

### Documentation (this feature)

```text
specs/xplat-001-runtime-inventory-constraints/
|-- SPEC-MOC.md
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
`-- checklists/
    `-- requirements.md
```

### Source and Report Targets (repository root)

```text
docs/
|-- ai/
|   |-- research/
|   |   `-- cross-platform-runtime-inventory.md
|   `-- specs/
|       |-- cross-platform-plugin-runtime-technical-roadmap.md
|       `-- .process/
|           |-- XPLAT-001-design-concept.md
|           `-- XPLAT-001-workflow.md
`-- prd-cross-platform-plugin-runtime.md

speckit-pro/
|-- skills/
|-- codex-skills/
|-- agents/
|-- codex-agents/
|-- hooks/
|-- scripts/
`-- codex-hooks.json

dist/
|-- claude/speckit-pro/
`-- codex/speckit-pro/

docs-site/src/content/docs/
tests/speckit-pro/
```

**Structure Decision**: Keep plan-phase artifacts under the feature directory.
The durable output is one Markdown report at
`docs/ai/research/cross-platform-runtime-inventory.md`; roadmap status/handoff
updates remain in
`docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`. No
`contracts/` artifact is planned because XPLAT-001 defines a human-reviewable
row schema and rubrics, not an API or machine-checked interchange format.

## Complexity Tracking

No constitution violations require a complexity exception. The only warning is
the recorded reviewability warning for two primary surfaces; the split decision
is to keep one inventory/rubric spike because separating scan evidence from
rubrics would force duplicate traceability review without reducing runtime risk.

## Phase 0 Research

Research is recorded in [research.md](./research.md). Decisions:

- Use deterministic repo-local scans, not a new persistent scanner.
- Use `docs/ai/research/cross-platform-runtime-inventory.md` as the durable
  report target.
- Use Markdown tables with summary counts; omit JSON/CSV until a later spec
  proves an automation benefit.
- Keep candidate runtime/security evidence lists separate from scoring.
- Treat active runtime status as a proof axis separate from source
  classification.

## Phase 1 Design

Design is recorded in [data-model.md](./data-model.md) and
[quickstart.md](./quickstart.md). The row schema includes:

- `id`
- `evidence`
- `classification`
- `active_runtime_status`
- `runtime_relevance`
- `owner_bucket`
- `follow_up_spec`
- `invocation_trace`
- `rationale`
- `exclusion_or_exception_detail`

The report must include summary counts by classification, active runtime
status, owner bucket, and follow-up spec. Active generated payload rows must map
to `xplat-007-cutover-guidance` with source links; generated payloads are not
authoritative edit targets.

## Inventory Method

1. Establish the tracked-text universe with Git, excluding `.git/`, binary
   assets, untracked files, vendor caches, and any non-text input with stated
   rationale.
2. Run scoped searches for Bash, `.sh`, `jq`, shell quoting, Unix paths,
   `chmod`, and line-ending assumptions. Record the exact commands in the
   report.
3. Group matches by physical/source classification:
   `source-reference`, `generated-payload-reference`, `public-docs-claim`,
   `tests-fixtures`, `historical-or-archive`, `repository-only-exclusion`, or
   `explicit-exclusion`.
4. For candidate active rows, trace caller-to-callee evidence from installed
   skills, agents, hooks, generated payloads, or other installed plugin
   surfaces.
5. Assign `active_runtime_status` as `proven-active-runtime`,
   `unproven-active-runtime`, or `not-active-runtime`.
6. Assign owner buckets only from the accepted set:
   `xplat-005-read-only-helper`, `xplat-006-mutation-helper`,
   `xplat-007-cutover-guidance`, `repository-only-exclusion`,
   `public-docs-claim`, `generated-payload-reference`,
   `historical-or-archive`, or `follow-up-exception`.

## Runtime Rubric Scope

The runtime rubric must be a non-scoring template for XPLAT-002. It includes
pass/fail must-have gates and weighted criteria totaling 100 points across:

- Native Windows/macOS/Linux behavior.
- Installed-cache invocation reliability.
- Dependency footprint and bootstrap burden.
- Packaging/distribution model.
- Offline behavior and update path.
- Diagnostics and error reporting.
- Maintainer ergonomics.
- Compatibility adapters and migration cost.

Candidate runtime names may appear only as evidence targets. XPLAT-001 must not
include scores, sample scoring, rankings, or a winner.

## Supply-Chain Rubric Scope

The supply-chain rubric must be a non-scoring template for XPLAT-003. It
includes pass/fail must-have gates and weighted criteria totaling 100 points
across:

- Dependency policy and lockfile discipline.
- Generated payload integrity.
- Vulnerability scanning.
- Provenance or attestation options.
- Checksums/signatures.
- SBOM feasibility.
- Consumer-local verification.
- Release automation and documentation truthfulness.

Controls may appear only as evidence targets. XPLAT-001 must not select the
required security model or control set.

## Verification Plan

Static verification only:

1. Re-run every scan command recorded in the report and confirm the report
   covers the result set or explains exclusions.
2. Review every `proven-active-runtime` row for a static caller-to-callee
   invocation trace.
3. Review docs-only and repository-only rows to confirm they were not promoted
   to active runtime without invocation evidence.
4. Run
   `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"`.
5. Run `git diff --check`.
6. Run the smallest relevant repo validation command only if implementation
   changes files outside docs/process planning/report artifacts.

## Review Packet Notes

The eventual PR packet must lead reviewers through:

1. `docs/ai/research/cross-platform-runtime-inventory.md` summary counts.
2. Active-runtime rows and invocation traces.
3. Runtime rubric boundaries for XPLAT-002.
4. Supply-chain rubric boundaries for XPLAT-003.
5. Roadmap handoff notes and deferred work.

Rollback is file-level: remove the research report and revert the roadmap status
note. No runtime feature flag is needed because no installed behavior changes.
