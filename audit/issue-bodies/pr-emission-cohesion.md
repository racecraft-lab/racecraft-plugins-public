Priority: minor

## Summary

helpers/pr_emission.py (1,149 lines) holds five jobs and sits in a 20-file import cycle. The registry routes 11 helper ids to its dispatcher, which implements 7, so promoting a deferred helper would fail at dispatch. build_packet_body hard-codes the UAT heading, and open PR #685 adds a second fence scanner beside the existing one in read_only.py.

## Evidence

- **pr-emission-and-stack-1-005** (minor): The registry routes 11 helper ids to run_pr_emission_helper, but the dispatcher implements only 7. final-reviewability-backstop, validate-pr-workflow-contract-write, relocate-process-artifacts and plan-layers-marker-plan fall through to an input_error. They are unreachable today only because their promotion status is deferred, so promoting one breaks at dispatch. The id list lives in two places.
  - `speckit-pro/speckit_pro_runner/helpers/pr_emission.py:59-77`, `speckit-pro/speckit_pro_runner/helpers/registry.py:788-800`
- **pr-emission-and-stack-1-006** (minor): pr_emission.py (1149 lines) holds five jobs: the dispatcher for the read-only stack-manager helper, UAT-skeleton rendering, the TBD PR-body scaffold, command-plan capture for the deferred emission helpers, and PR-packet normalization and validation. The deps scan also places it in a 20-file import cycle with run_finalization.
  - `speckit-pro/speckit_pro_runner/helpers/pr_emission.py:59-77`, `speckit-pro/speckit_pro_runner/helpers/pr_emission.py:80-160`, `speckit-pro/speckit_pro_runner/helpers/pr_emission.py:423-476`, `speckit-pro/speckit_pro_runner/helpers/pr_emission.py:479-654`
- **pr-emission-and-stack-1-007** (minor): build_packet_body is a single and split layout builder. It hardcodes '## UAT Runbook' and repeats how_to_uat under both How To UAT and UAT Runbook instead of using uat.uat_runbook_heading. When a draft packet omits body it is still called, emits the wrong headings and fails with a generic body-structure error. The draft contract says this fallback is never reached in draft mode.
  - `speckit-pro/speckit_pro_runner/helpers/pr_emission.py:566-604`, `speckit-pro/speckit_pro_runner/helpers/pr_emission.py:944-1011`, `tests/speckit-pro/layer6-integration/performance-fixtures/draft-pr-emission/source/contracts/draft-packet-mode.md:258`
- **pr-emission-and-stack-1-009** (minor): Open PR 685 adds a hand-written CommonMark fence scanner of about 50 lines inline in normalize_packet_input, next to the existing _fenced_markdown_lines in read_only.py. The host parser and the packet normalizer now hold two fence-aware scanners. Introduced by open PR #685.
  - `speckit-pro/speckit_pro_runner/helpers/pr_emission.py:574-604`

## Proposed fix

- pr-emission-and-stack-1-005: Derive the routed id set from one table, or have the dispatcher raise a registry-level error for an id the registry routes but the module does not implement.
- pr-emission-and-stack-1-006: Split UAT skeleton rendering and packet normalization into their own helper modules, and register detect-stack-manager-plan directly instead of through the PR-emission dispatcher.
- pr-emission-and-stack-1-007: Reject a draft packet without inputs.body with a specific message before any builder runs, and drive the UAT heading from the uat record.
- pr-emission-and-stack-1-009: Move the release-note fence handling into read_only.py beside _fenced_markdown_lines and call one scanner.

## Acceptance

- [ ] A regression test that fails before the fix: every id the registry routes to the dispatcher is implemented or raises a registry-level error.
- [ ] UAT skeleton rendering and packet normalization live in their own modules.
- [ ] A draft packet without inputs.body fails with a specific message; the UAT heading comes from the uat record.
- [ ] One fence-aware scanner is shared.
- [ ] Runner trust metadata and dist/ are regenerated.

## Related

- Overlaps files changed by open PR #685.
- Depends on #873

Found by the 2026-09 coherence audit.
