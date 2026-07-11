# UAT Runbook: prsg-012-reviewer-ready-pr-packet-contract

| Field | Value |
|-------|-------|
| Spec | prsg-012-reviewer-ready-pr-packet-contract |
| Branch | prsg-012-reviewer-ready-pr-packet-contract |
| PR | Pending until PR is opened |
| Generated from | 2026-06-12T19:36:21Z |

## Env Setup

From the repository root, run `bash tests/speckit-pro/run-all.sh --layer 4` to check the script behavior used by this packet workflow. No browser setup is required for this shell-only packet workflow.

## Per-Story Acceptance Tests

### User Story 1 - Specific conventional PR titles (Priority: P1)

1. Generate a single packet for this fixture.
   Expected: the packet title is a conventional commit title with the `PRSG-012` scope and a readable action phrase.
2. Open the rendered body file recorded by the packet.
   Expected: the Summary describes the reviewer-visible change instead of a branch name or packet id.

- [ ] The reviewer can confirm the generated title and Summary are specific.

### User Story 2 - Structured reviewer body (Priority: P1)

1. Open the rendered body.
   Expected: the H2 sections appear in this order: Summary, What Changed, Why It Matters, How To Review, How To UAT, Verification, Scope, Known Gaps.
2. Inspect the editable marker pairs in Summary, What Changed, and Why It Matters.
   Expected: each editable block has exactly one start marker and one end marker.

- [ ] The reviewer can scan the body without hunting through generated metadata files.

### User Story 3 - Pre-create validation block (Priority: P1)

1. Run packet validation against the generated packet.
   Expected: validation writes the feature-local validation result path from packet metadata.
2. Inspect the validation result path.
   Expected: the result belongs under `.process/pr-packets/<packet-id>/validation.json`.

- [ ] The reviewer can find validation evidence before PR creation.

### User Story 4 - Safe prose refinement (Priority: P2)

1. Edit only the editable Summary, What Changed, and Why It Matters prose.
   Expected: protected body fingerprint validation still passes.
2. Edit a protected governance or evidence line.
   Expected: protected body fingerprint validation fails.

- [ ] The reviewer can refine prose without changing protected packet evidence.

## FR Coverage Matrix

| Behavior | Acceptance check |
|----------|------------------|
| Titles are specific and conventional. | User Story 1, steps 1-2 |
| Bodies keep required reviewer sections and editable markers. | User Story 2, steps 1-2 |
| Validation evidence is available before PR creation. | User Story 3, steps 1-2 |
| Editable prose can change without weakening protected evidence. | User Story 4, steps 1-2 |

## Negative-Path Tests

1. Generate a packet with a body that duplicates a required H2 heading.
   Expected: packet validation rejects the body heading order.
2. Generate a packet whose body contains stale template text or hidden TODO comments.
   Expected: packet validation rejects placeholder content.
3. Generate a packet with the UAT Runbook heading but no actionable runbook content.
   Expected: packet validation rejects the skeleton or absent-runbook fallback.

## Self-Review Findings

1. Focused Layer 4 packet-generation and packet-validation checks cover this fixture.
2. The UAT path is shell-only; no browser or service account is required.
3. No follow-up marker is required for this fixture.

## Sign-off

Advisory only; these checkboxes block nothing.

- [ ] Reviewer completed the acceptance checks above.
- [ ] Reviewer confirmed the negative-path expectations above.
- [ ] Reviewer is satisfied the PR body is review-ready.

## Rollback

Revert the packet-generation change and regenerate the PR packet fixture.
