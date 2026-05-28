# UAT Runbook: 006a-uat-skeleton

| Field | Value |
|-------|-------|
| Spec | 006a-uat-skeleton |
| Branch | 006a-uat-skeleton |
| PR | **PR:** <set on PR open> |
| Generated from | 2026-05-28T19:54:57Z |



## Env Setup

Run these from the repository root before walking the acceptance tests.

| Command | Value |
|---------|-------|
| BUILD | _not available for this project_ |
| TYPECHECK | _not available for this project_ |
| LINT | `shellcheck speckit-pro/skills/speckit-autopilot/scripts/*.sh` |
| LINT_FIX | _not available for this project_ |
| UNIT_TEST | `cd speckit-pro && bash tests/run-all.sh --layer 4` |
| INTEGRATION_TEST | `cd speckit-pro && bash tests/run-all.sh` |
| SINGLE_FILE_INTEGRATION | _not available for this project_ |

## Per-Story Acceptance Tests

<a id="us-1"></a>
### User Story 1 - Reviewer sees a UAT Runbook in the PR body (Priority: P1)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

<a id="us-2"></a>
### User Story 2 - Reviewer of an infrastructure spec sees an FR/SC-keyed runbook (Priority: P1)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

<a id="us-3"></a>
### User Story 3 - Autopilot resume regenerates the runbook deterministically (Priority: P2)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

<a id="us-4"></a>
### User Story 4 - Self-Review findings echoed for offline review (Priority: P2)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.



## FR Coverage Matrix

| Story | Acceptance test |
|-------|-----------------|
| [User Story 1 - Reviewer sees a UAT Runbook in the PR body (Priority: P1)](#us-1) | see the Per-Story Acceptance Tests block above |
| [User Story 2 - Reviewer of an infrastructure spec sees an FR/SC-keyed runbook (Priority: P1)](#us-2) | see the Per-Story Acceptance Tests block above |
| [User Story 3 - Autopilot resume regenerates the runbook deterministically (Priority: P2)](#us-3) | see the Per-Story Acceptance Tests block above |
| [User Story 4 - Self-Review findings echoed for offline review (Priority: P2)](#us-4) | see the Per-Story Acceptance Tests block above |


## Negative-Path Tests


- **Zero user stories**: spec has no `### User Story` headings — runbook falls back to FR/SC keying with an explanatory header note (US2, FR-003).
- **Duplicate FR/SC IDs**: an ID such as FR-005 appears twice (as in SPEC-004) — the runbook keeps the first-seen entry and the script writes a stderr warning naming the duplicate ID (FR-004).
- **Unresolved clarification markers in the source spec**: when a parsed US/FR/SC/Edge bullet carries a clarification marker (bare or colon-question form), the runbook reproduces that bullet with an unresolved-clarification annotation rather than dropping it silently. Propagation is scoped to the bullets the script parses, not to arbitrary prose elsewhere in `spec.md` (FR-005).
- **Unreadable or missing spec**: the script exits with a distinct error code and does not produce a partial runbook (FR-006).
- **PROJECT_COMMANDS not supplied**: when the autopilot does not pass build/test/lint commands, the Env Setup section emits explicit unknown-value placeholders rather than failing (FR-008).
- **Missing Self-Review source**: workflow file absent or heading missing — Self-Review Findings degrades to a stub line, no failure (FR-009).
- **No Rollback heading in spec or plan**: the Rollback section emits a synthesized fallback stanza (FR-012).
- **Runbook at or over the size threshold**: the PR body shows an opening excerpt plus a relative link instead of the full inline content (FR-013).

## Self-Review Findings

Post-implementation self-check (4 questions, mirroring the autopilot Self-Review pattern).
1. **Did all tests run and pass?** Yes — full suite green at 1467/1467 (L1 parity 334+389, L4 572 including the newly-registered `test-generate-uat-skeleton` at 60/60, L5 172). `shellcheck` and `bash -n` clean on both scripts.
2. **Are all requirements traced to code and tests?** Yes — FR-001..FR-015 each map to at least one task and assertion; SC-001..SC-005 map to verification commands (tasks.md traceability table). Smoke run against spec 004 confirms SC-001 (5 real user stories; the traceability sub-heading is correctly excluded).
3. **Were the gates validated?** G1-G7 all pass via `validate-gate.sh`; G6.5 confidence gate soft-skipped (advisory, no consensus emit).
4. **Known gaps / risks?** (a) Reviewable LOC 862 exceeds the 800 line — production code is 389 (under budget); the overage is constitution-mandated Layer 4 test coverage, accepted under the roadmap's ratified split exception. (b) FR-009 Self-Review echo caps at 40 lines (the reused helper's behavior — spec-conformant). (c) Matrix `<a id>` anchors rely on GitHub markdown rendering (not locally verifiable). (d) LLM-authored narrative test steps are deferred to SPEC-006b.
---

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations
