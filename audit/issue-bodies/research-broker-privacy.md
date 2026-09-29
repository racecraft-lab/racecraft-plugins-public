Priority: major

## Summary

The research broker's spec-text privacy guard is silently off in any repository that is itself a plugin marketplace root, because project_root treats every such directory as the plugin's own root. This breaks the fail-closed rule for a privacy guard. The contract describes a narrower exception.

## Evidence

- **brokers-and-verification-009** (major, adjusted from minor in review): project_root returns None for any directory that holds .claude-plugin or .codex-plugin. In a repository that is itself a marketplace root (this one), the spec_text_detected outbound check is silently off, even with CLAUDE_PROJECT_DIR set. The contract only says the check is off when neither the variable nor the git root names a project. Confirmed by calling project_root with the repository root.
  - `speckit-pro/speckit_pro_runner/research_broker.py:225-242`, `docs/ai/specs/research-broker-contract.md:112-117`

## Proposed fix

- brokers-and-verification-009: Skip the check only when the candidate is the running plugin's own root, or state the marketplace-root exception in the contract.

## Acceptance

- [ ] A regression test that fails before the fix: with CLAUDE_PROJECT_DIR set to a marketplace root that is not the running plugin root, the spec_text_detected check runs.
- [ ] The contract in docs/ai/specs/research-broker-contract.md matches the behavior.
- [ ] Runner trust metadata and dist/ are regenerated.

## Related

- None.

Found by the 2026-09 coherence audit.
