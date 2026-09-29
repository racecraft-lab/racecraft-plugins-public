Priority: major

## Summary

PR packet validation disagrees with its neighbors on both sides. finalize-run accepts multi-line human-UAT fields that the packet normalizer later rejects, so a run finalized as complete_with_deferred can fail at the top-PR body refresh. The packet schema accepts an uppercase title scope that the live PR-title gate rejects.

## Evidence

- **pr-emission-and-stack-1-001** (major): finalize-run accepts human_uat fields that contain newlines (it only strips and caps length at 240), then hands them unchanged to pr-packet-output as deferred_items. normalize_deferred_items rejects any newline, so a run that finalizes as complete_with_deferred can fail at the top-PR body refresh. The same item/reason/finish shape is declared twice (UAT_FIELDS and DEFERRED_ITEM_FIELDS). Confirmed by calling _records with a two-line item, which returned it intact.
  - `speckit-pro/speckit_pro_runner/helpers/run_finalization.py:47`, `speckit-pro/speckit_pro_runner/helpers/run_finalization.py:62-63`, `speckit-pro/speckit_pro_runner/helpers/run_finalization.py:80-88`, `speckit-pro/speckit_pro_runner/helpers/pr_emission.py:35-36`, `speckit-pro/speckit_pro_runner/helpers/pr_emission.py:1014-1029`
- **pr-emission-and-stack-1-004** (major): The packet schema accepts an uppercase ticket-style title scope ([A-Z]+-[A-Z0-9-]+), and pr-packet-output builds titles from any title_scope string. The live PR-title gate and the release gate accept only [a-z0-9-]+. A packet can pass packet validation and still fail validate-pr-title. The draft-packet contract records this split and leaves it in place. The lowercase rule then lives only in skill prose (post-implementation.md) and the archive-cleanup skill.
  - `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json:303-306`, `speckit-pro/speckit_pro_runner/helpers/pr_emission.py:833-842`, `speckit-pro/speckit_pro_runner/gates/release.py:109`, `tests/speckit-pro/layer6-integration/performance-fixtures/draft-pr-emission/source/contracts/draft-packet-mode.md:1-309`
- **pr-emission-and-stack-2-008** (minor): The packet schema pattern, its pinned fixture copy and the release gate regex disagree: the schema and fixture accept uppercase ticket scopes such as feat(FEATURE-001), which validate-pr-title rejects (confirmed by running the gate). phase-execution.md only tells the agent to prefer lowercase.
  - `tests/speckit-pro/unit/fixtures/pr-packet-title-patterns.json:2`, `tests/speckit-pro/unit/fixtures/pr-packet-title-patterns.json:3`, `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json:305`, `speckit-pro/speckit_pro_runner/gates/release.py:109`

## Proposed fix

- pr-emission-and-stack-1-001: Keep one definition of the deferred-item shape and its one-line rule in a shared module, and have finalize-run reject multi-line item, reason and finish before it reports a finalized outcome.
- pr-emission-and-stack-1-004: Make the schema value and scope patterns, and normalize_generated_title, enforce the same lowercase-scope rule as the gate, ideally from one shared pattern.
- pr-emission-and-stack-2-008: Narrow the schema scope pattern to the gate's lowercase form, or have the gate accept the schema's scopes. Derive the fixture from one source.

## Acceptance

- [ ] Regression tests that fail before the fix: finalize-run rejects a multi-line item, reason or finish; the packet schema rejects feat(FEATURE-001).
- [ ] The deferred-item shape and the title-scope pattern each have one source shared by the schema, normalizer and gate.
- [ ] The pinned title-pattern fixture derives from that source.
- [ ] Runner trust metadata and dist/ are regenerated.

## Related

- Overlaps files changed by the open stop-policy stack: #838, #847, #848. Land after that stack merges.
- Overlaps files changed by open PR #685.

Found by the 2026-09 coherence audit.
