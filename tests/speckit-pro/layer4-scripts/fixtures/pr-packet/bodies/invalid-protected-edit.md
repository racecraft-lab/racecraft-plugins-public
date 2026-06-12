<!-- speckit-pro-review-packet-source: tests/speckit-pro/layer4-scripts/fixtures/pr-packet/invalid-protected-edit.json -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Adds a reviewer-ready PR packet fixture for the single-PR validation path.
<!-- speckit-pro-editable:summary:end -->

Source: feature specification defines tampered reviewer packet sections.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Added a schema-shaped single packet fixture.
- Added a rendered Markdown body fixture for that packet.
<!-- speckit-pro-editable:what_changed:end -->

Source: schema contract defines editable field markers.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
The validator needs a complete passing example before implementation can make the contract green.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Inspect the packet JSON for the single mode, explicit target, generated title, validation path, scope evidence, and verification evidence.
2. Inspect this body for the required reviewer headings, source markers, editable regions, and known-gap language.

## How To UAT

Run the Layer 4 packet validation fixture once the validator task lands. Until then, inspect the fixture shape and JSON syntax.

## UAT Runbook

Manual UAT is not required for this fixture-only task. The compatibility heading remains present so downstream PR body checks keep the same anchor.

## Verification

- `jq empty tests/speckit-pro/layer4-scripts/fixtures/pr-packet/valid-single.json`
- Expected result: JSON parses successfully.

Source: quickstart defines single-packet validation evidence.

## Scope

- Reviewable LOC: fixture-only evidence.
- Changed files: the single packet JSON and rendered body Markdown fixtures.
- Non-goals: validator behavior, PR creation behavior, split-packet behavior, and workflow event writing.
- Traceability: single-packet contract evidence maps to the packet JSON and this rendered body.

## Known Gaps

No known gaps for this fixture. Validator behavior is intentionally deferred to later tasks.
