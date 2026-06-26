# UAT Runbook: xplat-001-runtime-inventory-constraints

| Field | Value |
|-------|-------|
| Spec | xplat-001-runtime-inventory-constraints |
| Branch | codex/xplat-001-runtime-inventory-constraints |
| PR | [PR #263](https://github.com/racecraft-lab/racecraft-plugins-public/pull/263) |
| Generated from | 2026-06-25T23:34:26Z |

## Env Setup

Run these from the repository root. This spec is a static report and handoff
change, so there is no app build or runtime smoke test to run. The useful checks
are the report reconciliation commands and the repository shell suite.

- Open `docs/ai/research/cross-platform-runtime-inventory.md`.
- Open `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`.
- Optional verification command: `bash tests/speckit-pro/run-all.sh`.
- Optional hygiene command: `git diff --check`.

## Per-Story Acceptance Tests

<a id="us-1"></a>
### User Story 1 - Review Runtime Inventory (Priority: P1)

1. Open the inventory report.
2. Confirm the scan boundary says the report excludes itself from source scans.
3. Confirm the scan result summary totals 21,162 represented scan hits.
4. Confirm the inventory rows separate source, generated payload, public docs,
   tests/fixtures, historical/archive, repo-only, and explicit exclusions.
5. Confirm proven active rows include invocation-trace evidence and that
   docs-only, generated docs, tests, archive, and repo-only rows are not promoted
   to active runtime without a trace.

Expected result: a reviewer can understand which Bash/Unix assumptions are real
installed-runtime concerns and which are non-runtime text matches.

<a id="us-2"></a>
### User Story 2 - Use Runtime Evaluation Rubric (Priority: P2)

1. In the inventory report, find `Runtime Evaluation Rubric for XPLAT-002`.
2. Confirm the must-have gates cover installed-cache invocation, native
   platform behavior, filesystem/path behavior, JSON handling, subprocess
   behavior, stdout, stderr, exit-code mapping, packaging, and update path.
3. Confirm the weighted criteria add to 100.
4. Confirm candidate runtime names appear only as evidence targets.

Expected result: XPLAT-002 can compare runtime options without XPLAT-001
scoring, ranking, or selecting a runtime.

<a id="us-3"></a>
### User Story 3 - Use Supply-Chain Evaluation Rubric (Priority: P3)

1. In the inventory report, find `Supply-Chain Evaluation Rubric for XPLAT-003`.
2. Confirm the must-have gates cover maintainer verification, consumer-local
   verification, truthful guarantees, generated payload integrity, and
   provenance evidence.
3. Confirm the weighted criteria add to 100.
4. Confirm each artifact/control target is labeled as a first-release gate
   question, deferred hardening evidence, or not-claimed guarantee.
5. Confirm the section does not require a specific security model or control
   set.

Expected result: XPLAT-003 can choose supply-chain controls later without
XPLAT-001 implying mandatory controls.

## FR Coverage Matrix

| Requirement | Acceptance path |
|-------------|-----------------|
| FR-001 to FR-007 | [User Story 1](#us-1): scan boundary, inventory rows, invocation traces, and summary counts |
| FR-008 | [User Story 2](#us-2): runtime gates, weights, and candidate evidence targets |
| FR-009 | [User Story 3](#us-3): supply-chain gates, weights, and artifact/control evidence targets |
| FR-010 to FR-012 | Report non-goals, verification notes, and absence of runtime changes |
| FR-013 to FR-014 | Markdown report location plus roadmap handoff notes |

## Negative-Path Tests

Review these in the inventory report:

- A text match appears in generated payload and source files: the report must classify both locations and identify which source is authoritative for follow-up.
- A text match appears only in public documentation: the report must classify it as a public-docs claim unless an invocation trace proves installed-runtime behavior.
- A public docs claim mentions an installed prerequisite such as `jq`: the docs row remains a public-docs claim and may link to a separate active-runtime finding only when static invocation-trace evidence proves that runtime dependency.
- A text match appears only in tests, fixtures, or archive reports: the report must classify it separately and avoid treating it as an active runtime blocker.
- A helper is repository-only today but may become installed-runtime later: the report must record current classification, rationale, and follow-up owner rather than inventing implementation work.
- A helper has both read-only and write/apply behavior: the report must classify each traced installed invocation by invoked mode, not by the helper's maximum capability, and create separate rows when both modes are traced or materially relevant.
- An invocation trace is ambiguous or incomplete: the report must mark the finding as unproven active runtime and document the evidence gap.
- Runtime or security candidates are named in source material: the report may list them as evaluation targets, but must not score, rank, or select them.

## Self-Review Findings

1. **Tests executed?** Yes for the checks applicable to this static docs/process
   spike. `BUILD`, `TYPECHECK`, `LINT`, `UNIT_TEST`, and
   `INTEGRATION_TEST` were detected as `N/A` during preflight. The equivalent
   static verification ran and passed after the latest `origin/main` merge:
   scan-count reconciliation, `generate-spec-index.sh --check "$PWD"`, `git
   diff --check`, G7, and the full repository suite
   `bash tests/speckit-pro/run-all.sh` (`3624/3624` passed locally).
2. **Edge cases?** Acceptance coverage is artifact-based because XPLAT-001 has
   no runtime implementation. The inventory report covers generated/source
   duplicate references, docs-only claims, tests/fixtures/archive references,
   repository-only helpers, mixed read/write helper ownership, ambiguous trace
   handling, and non-scoring candidate/control mentions. No native runtime probe
   or executable edge-case test is required by this spec.
3. **Requirements matched?** All 14 functional requirements trace to completed
   tasks and implementation evidence: FR-001 through FR-007 map to T001-T018
   and the inventory rows/counts; FR-008 maps to T019-T021; FR-009 maps to
   T022-T025; FR-010 through FR-012 map to report non-goals and verification;
   FR-013 and FR-014 map to the Markdown report and roadmap handoff. Evidence
   commits include `e2fee750`, `4110db0b`, and `8053485b`, with G7 passing.
4. **Follow-up & tidiness?** No `[TODO]`, `[DEFERRED]`, or `[OUT-OF-SCOPE]`
   markers were found in the spec, plan, tasks, workflow, report, or roadmap
   handoff paths. The diff contains no helper ports, active invocation changes,
   debug logging, commented-out code, temporary fixtures, or orphaned files.
   Generated payload edits are limited to synchronized copies of the existing
   spec-index helper remediation.
---

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

Revert the XPLAT-001 branch commits for this report, roadmap handoff, and
post-review spec-index remediation. No runtime behavior, database, or migration
state is changed; generated payload sync reverts with the branch commits.
