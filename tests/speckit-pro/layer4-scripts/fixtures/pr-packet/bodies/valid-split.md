<!-- speckit-pro-review-packet-source: tests/speckit-pro/layer4-scripts/fixtures/pr-packet/valid-split.json -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Adds a reviewer-ready PR packet fixture for the split-PR validation path.
<!-- speckit-pro-editable:summary:end -->

Source: feature specification defines split packet validation before each PR create attempt.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Added a schema-shaped split packet fixture with explicit slice identity.
- Added a rendered Markdown body fixture for the split packet.
<!-- speckit-pro-editable:what_changed:end -->

Source: split source boundary section defines the public title description for this packet.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
The validator needs a complete passing split example before implementation can make split PR emission green.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Inspect the packet JSON for split mode, explicit target, split slice evidence, generated title, validation path, scope evidence, and verification evidence.
2. Inspect this body for the required reviewer headings, source markers, editable regions, split/source traceability, and known-gap language.

## How To UAT

Run the Layer 4 packet validation fixture once the validator task lands. Until then, inspect the split fixture shape, JSON syntax, and rendered body evidence.

## UAT Runbook

Manual UAT is not required for this fixture-only task. The compatibility heading remains present so downstream PR body checks keep the same anchor for split packets.

## Verification

- `jq empty tests/speckit-pro/layer4-scripts/fixtures/pr-packet/valid-split.json`
- Expected result: JSON parses successfully.

Source: quickstart defines split-packet validation evidence.

## Scope

- Reviewable LOC: fixture-only evidence.
- Changed files: the split packet JSON and rendered body Markdown fixtures.
- Split evidence: `split_slice.slice_id` maps to the packet identity, and `split_slice.source_boundary.section` maps to the generated title description.
- Traceability: split-packet contract evidence maps to the packet JSON, this rendered body, and the planned source packet path.
- Non-goals: validator behavior, PR creation behavior, resume behavior, and workflow event writing.

## Known Gaps

No known gaps for this fixture. Validator behavior and split PR emission wiring are intentionally deferred to later tasks.
