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
helpers to a replacement runtime, change active Claude/Codex invocation paths,
perform broad generated payload rebuilds, or claim native Windows support. If
review remediation corrects an existing shipped helper, generated payload edits
stay limited to synchronized copies of that helper.

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
| Plugin Structure Compliance | XPLAT-001 must not change installed invocation paths, active skill/agent/hook contracts, or port helpers to a replacement runtime. If review remediation corrects an existing shipped helper, generated payload edits stay limited to synchronized copies of that helper. | Pass: planned changes are a Markdown research report plus roadmap progress/handoff note; post-review generator remediation follows the narrow sync exception. |
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

### Row Aggregation and Match-Summary Rules

The report may use aggregate or match-summary rows to keep PR review concise,
but aggregation is a presentation choice only; it does not reduce the 100%
scan coverage requirement.

- Prefer individual rows for proven active runtime, unproven active runtime,
  `follow-up-exception`, generated payload rows with source links, and
  mixed-mode helper findings when row-level ownership or trace evidence would
  otherwise be blurred.
- Aggregate only matches that share the same recorded scan command or pattern
  family, `classification`, `active_runtime_status`, `runtime_relevance`,
  `owner_bucket`, `follow_up_spec`, invocation mode if applicable, and
  rationale.
- Each aggregate row must include a stable row id, matched token or pattern
  family, match count, included path set or path pattern, representative
  evidence excerpt, scan command reference, and grouping rationale.
- Do not aggregate matches across different owner buckets, follow-up specs,
  active-runtime proof states, invocation modes, exception rationales, or
  source-of-truth boundaries.
- Summary counts must count represented matches, not just table rows, so
  aggregate rows reconcile to rerun scan output and SC-001 remains verifiable.
- If review or verification finds one match inside an aggregate row that needs
  a different classification, active runtime status, owner bucket,
  follow-up spec, invocation trace, or rationale, split that match into its own
  row.
- These rules are satisfied in Markdown tables and summary counts; XPLAT-001
  still does not require JSON, CSV, or a contract artifact.

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

The report's supply-chain rubric must include a `release_boundary` column or
equivalent sectioning that separates:

- `first-release-gate-question`: evidence XPLAT-003 must explicitly evaluate
  before deciding first public release requirements.
- `deferred-hardening-evidence`: evidence that may inform later hardening and
  must not be treated as a release blocker unless XPLAT-003 promotes it.
- `not-claimed-guarantee`: unsupported guarantee language that must remain
  absent from the report and public docs until implemented by a later XPLAT
  spec.

This boundary is a handoff label, not a control selection. XPLAT-003 decides
which supply-chain controls are required for first release, which belong to
release automation, and which remain deferred hardening.

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

### Static Verification Failure Remediation

If a static verification step fails, remediation stays within the XPLAT-001
docs/process scope and must not port helpers to a replacement runtime, change
installed invocation paths, perform broad generated payload rebuilds, or
introduce runtime probes.

- **Uncovered scan result**: add or correct the inventory row, or add an
  explicit exclusion with rationale, then update summary counts by
  classification, active runtime status, owner bucket, and follow-up spec.
- **Missing or stale invocation trace**: downgrade the row to
  `unproven-active-runtime` with an evidence gap, or replace the trace with a
  static caller-to-callee source citation before marking it
  `proven-active-runtime`.
- **Docs, test, fixture, archive, or repository-only reference promoted to an
  active blocker**: split the row or reclassify it to the matching non-active
  bucket unless a separate installed-runtime trace proves active relevance.
- **Generated payload source mismatch**: keep the `dist/**` row as a
  `generated-payload-reference`, link it to the authoritative source row when
  known, and defer payload rebuild or cutover wording to XPLAT-007.
- **Spec-index drift**: regenerate the SPEC-MOC index with
  `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh "$PWD"`
  and rerun the `--check` command before closing verification.
- **Diff hygiene failure**: use the file and line reported by
  `git diff --check` to remove whitespace or conflict-marker issues, then rerun
  `git diff --check`.

## Review Packet Notes

The eventual PR packet must lead reviewers through:

1. `docs/ai/research/cross-platform-runtime-inventory.md` summary counts.
2. Active-runtime rows and invocation traces.
3. Runtime rubric boundaries for XPLAT-002.
4. Supply-chain rubric boundaries for XPLAT-003.
5. Roadmap handoff notes and deferred work.

Rollback is file-level: remove the research report and revert the roadmap status
note. No runtime feature flag is needed because no installed behavior changes.
