Priority: major

## Summary

Agent roster, sandbox and profile facts, and skill rosters, are restated by hand across Layer 1 and Layer 5 validators and native tests, although agent_inventory.json and the skill directories already hold them. The copies already differ, and a new skill added to both trees skips the frontmatter checks. Every roster change needs several hand edits.

## Evidence

- **structural-layers-2-002** (major): Agent roster, sandbox and profile facts are restated by hand in five places (CODEX_SANDBOX_POLICY, _check_profile, two capability EXCLUSIONS pairs, CC_ONLY_AGENTS) although AGENT_INVENTORY already holds them. The two CC exclusion sets already differ. PR 851 adds one role and must edit six lists.
  - `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py:112`, `tests/speckit-pro/layer1-structural/validate-agent-contracts.py:347`, `tests/speckit-pro/layer1-structural/validate-skill-contracts.py:563`, `tests/speckit-pro/layer1-structural/validate-skill-contracts.py:612`, `tests/speckit-pro/layer1-structural/validate-skill-contracts.py:836`
- **release-tooling-011** (minor): REQUIRED_SKILLS names ten codex-skills but omits speckit-install and speckit-upgrade, which exist in skills/ and codex-skills/. The check would not notice either being dropped. The file also mixes speckit-pro manifests, typesafe-jev provenance and versions, and the curated-set catalog.
  - `tests/speckit-pro/layer1-structural/validate-plugin-metadata.py:65`
- **structural-layers-2-003** (major): Three hand-kept skill rosters exist and none is compared to the skills/ and codex-skills/ directories. A new skill added to both trees gets parity and pointer checks only, and skips the frontmatter, name and description checks in test_skills and test_codex_skills.
  - `tests/speckit-pro/layer1-structural/validate-skill-contracts.py:26`, `tests/speckit-pro/layer1-structural/validate-skill-contracts.py:278`, `tests/speckit-pro/layer1-structural/validate-plugin-metadata.py:65`
- **native-eval-harness-011** (minor): Tests hard-code derived facts: the Codex agent roster size (13, versus 13 files in codex-agents/), and catalog totals (216, 109). Every catalog or roster change needs a hand edit, and open PRs already bump them (14, 232). test-native-functional-catalog also keeps a fallback to a catalog-functional.json shard that does not exist.
  - `tests/speckit-pro/unit/test-native-eval-adapters.py:2564`, `tests/speckit-pro/unit/test-native-eval-adapters.py:2623`, `tests/speckit-pro/unit/test-native-functional-catalog.py:21-22`, `tests/speckit-pro/unit/test-native-functional-catalog.py:878`, `tests/speckit-pro/unit/test-native-trigger-catalog.py:98`
- **autopilot-and-agents-010** (minor): The memory scope matrix omits formal-model-author and artifact-preview-observer, which the inventory lists with memory none. The matrix and the inventory are two sources for one contract and nothing compares them.
  - `speckit-pro/skills/speckit-autopilot/references/subagent-memory-policy.md:8-16`, `speckit-pro/speckit_pro_runner/agent_inventory.json:1`
- **structural-layers-2-006** (minor): A layer 1 structural validator pins layer 3 eval JSON content by numeric eval id (106, 18, 14, 19, 15, 4). The speckit-coach eval 4 assertions also sit inside _check_autopilot_skill, a Codex autopilot helper. PR 851 already had to rewrite them.
  - `tests/speckit-pro/layer1-structural/validate-skill-contracts.py:470`, `tests/speckit-pro/layer1-structural/validate-skill-contracts.py:499`
- **structural-layers-2-010** (minor): Frontmatter field and TOML instruction extractors are copied per validator (_field twice at 0.97 clone similarity, _extract_developer_instructions and _toml_prose) although lib/structural_helpers.py exists. The copies differ: layer 1 strips quotes, layer 5 does not.
  - `tests/speckit-pro/layer1-structural/validate-agent-contracts.py:132`, `tests/speckit-pro/layer1-structural/validate-skill-contracts.py:32`, `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py:169`, `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py:185`
- **structural-layers-2-012** (minor): validate-agent-contracts.py also owns the AGENTS.md, CLAUDE.md, GEMINI.md and Copilot wrapper and size-budget checks (repo instruction hygiene), which is a different concern from plugin agent definitions.
  - `tests/speckit-pro/layer1-structural/validate-agent-contracts.py:31`, `tests/speckit-pro/layer1-structural/validate-agent-contracts.py:113`
- **structural-layers-2-013** (minor): APPROVED_EQUIVALENTS is an empty frozenset and _approved_equivalent can never return true, so the escape hatch is dead code that reads as a live policy.
  - `tests/speckit-pro/layer1-structural/validate-skill-contracts.py:565`, `tests/speckit-pro/layer1-structural/validate-skill-contracts.py:573`

## Proposed fix

- structural-layers-2-002: Derive the sandbox, profile, Claude-only, Codex-only and exemption sets from AGENT_INVENTORY (or one shared test helper) and delete the hand-kept copies.
- release-tooling-011: Derive the roster from skills/ (or the agent inventory) and split typesafe-jev and curated-set checks into their own files.
- structural-layers-2-003: Assert each roster equals the discovered directory set, or iterate the discovered set with per-skill policy tables.
- native-eval-harness-011: Derive the counts from speckit-pro/codex-agents and the catalog, and delete the shard fallback.
- autopilot-and-agents-010: Add the two roles or derive the matrix from the inventory and test it.
- structural-layers-2-006: Move eval-content pins next to the eval fixtures (layer 3 unit tests) and key them by stable case id.
- structural-layers-2-010: Move the extractors into structural_helpers.py and import them.
- structural-layers-2-012: Move collect_errors and its constants to their own validator.
- structural-layers-2-013: Delete the constant and the helper, or record a real equivalent.

## Acceptance

- [ ] Rosters derive from AGENT_INVENTORY and the discovered skills/ and codex-skills/ directories.
- [ ] A regression test that fails before the fix: a skill directory missing from the roster, or a new agent role, is caught without editing lists.
- [ ] The memory-scope matrix covers every inventory role, or derives from the inventory.
- [ ] Shared extractors live in lib/structural_helpers.py; dead APPROVED_EQUIVALENTS is removed; eval-content pins move to Layer 3 tests.

## Related

- Overlaps files changed by the open stop-policy stack: #845, #847, #849, #850, #851, #852. Land after that stack merges.
- Overlaps files changed by open PR #685.
- Overlaps files changed by the in-progress fix for #832.
- Overlaps files changed by open PR #853.

Found by the 2026-09 coherence audit.
