<!--
  uat-runbook-template.md — fixed-order skeleton for the deterministic UAT runbook.
  Rendered by generate-uat-skeleton.sh (FR-010). The eight section headers below are
  emitted in this exact order on every run; the script substitutes each {{...}} token
  with deterministic content parsed from spec.md. Do not reorder the sections — the
  FR Coverage Matrix and SC-005's `## UAT Runbook` embed depend on this order.
-->
# UAT Runbook: {{SPEC_ID}}

| Field | Value |
|-------|-------|
| Spec | {{SPEC_ID}} |
| Branch | {{BRANCH}} |
| PR | {{PR_PLACEHOLDER}} |
| Generated from | {{SPEC_TIMESTAMP}} |

{{HEADER_NOTE}}

## Env Setup

Run these from the repository root before walking the acceptance tests.

{{ENV_SETUP}}

## Per-Story Acceptance Tests

{{PER_STORY}}

## FR Coverage Matrix

{{FR_MATRIX}}

## Negative-Path Tests

{{NEGATIVE_PATH}}

## Self-Review Findings

{{SELF_REVIEW}}

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

{{ROLLBACK}}
