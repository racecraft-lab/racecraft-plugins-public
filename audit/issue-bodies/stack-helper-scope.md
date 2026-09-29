Priority: major

## Summary

Parity fixture 04 and Codex autopilot eval 7 both say detect-stack-manager-plan is out of scope and must not be invoked. Both hosts' Post guidance runs it in dry_run, stack-manager.md documents its request, and the registry lists it as a dispatchable helper. The fixture and the eval therefore reward a wrong answer, and fixture 04's env files set variables no shipped code reads.

## Evidence

- **pr-emission-and-stack-2-001** (major): Parity fixture 04 states that detect-stack-manager-plan is registered out_of_scope and must not be invoked, and dry-run pins active_stack_manager_helper_call=false as a required invariant. Both hosts' Post guidance runs the helper in dry_run (step 7b), stack-manager.md documents its request, and the registry lists it as a mutation helper.
  - `tests/speckit-pro/layer7-parity/04-stack-manager-guidance/workflow.md:7`, `tests/speckit-pro/layer7-parity/04-stack-manager-guidance/workflow.md:14`, `tests/speckit-pro/layer7-parity/04-stack-manager-guidance/expected-equivalence.json:51`, `speckit-pro/skills/speckit-autopilot/references/post-implementation.md:528`, `speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md:336`
- **seam-001** (major): Codex autopilot eval 7 expects the answer to say detect-stack-manager-plan is out of scope and not an active installed helper call, and the native catalog copy in legacy-selection.json repeats that expectation. Both hosts' Post guidance runs it in dry_run and the registry lists it as a golden_only, dispatchable mutation helper, so the eval rewards a wrong answer. This is the eval-side twin of pr-emission-and-stack-2-001 (parity fixture 04); functional-evals-1 did not record it.
  - `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json:84`, `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json:96`, `tests/speckit-pro/evals/fixtures/functional/legacy-selection.json:5837`, `speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md:336`, `speckit-pro/skills/speckit-autopilot/references/post-implementation.md:528`, `speckit-pro/speckit_pro_runner/helpers/registry.py:636-643`
- **pr-emission-and-stack-2-002** (minor): Fixture 04's env files set SPECKIT_AGENT_TEAMS and SPECKIT_PRSG_014_STACK_MANAGER, which no shipped code or guidance reads. Fixtures 01 to 03 and agent-teams-integration.md use CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS, so fixture 04's teams and fallback paths do not differ in live mode.
  - `tests/speckit-pro/layer7-parity/04-stack-manager-guidance/env-teams.json:5`, `tests/speckit-pro/layer7-parity/04-stack-manager-guidance/env-fallback.json:5`, `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md:78`

## Proposed fix

- pr-emission-and-stack-2-001: Rewrite the fixture's helper claim and invariant to match the shipped contract, or retire fixture 04 as the audit doc already holds it, so CI stops enforcing a false contract.
- seam-001: Rewrite eval 7's expected_output and its expectation line (and the legacy-selection.json copy) to say the orchestrator runs detect-stack-manager-plan in dry_run per stack-manager.md, and keep final-reviewability-backstop as the only deferred helper named there.
- pr-emission-and-stack-2-002: Use CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS like the sibling fixtures, or drop fixture 04 with finding 001.

## Acceptance

- [ ] Eval 7 and the legacy-selection.json copy describe the dry_run call per stack-manager.md.
- [ ] Fixture 04's invariant matches the shipped contract, or the fixture is retired.
- [ ] Fixture 04 uses CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS like fixtures 01 to 03, or is dropped.
- [ ] Layer 3 native catalog and Layer 7 dry-run pass.

## Related

- Overlaps files changed by the open stop-policy stack: #845, #849, #850, #851. Land after that stack merges.
- Overlaps files changed by the in-progress fix for #832.
- Depends on #854

Found by the 2026-09 coherence audit.
