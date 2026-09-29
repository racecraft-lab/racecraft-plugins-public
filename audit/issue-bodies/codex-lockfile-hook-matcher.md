Priority: minor

## Summary

The lockfile PreToolUse hook is documented as matched to the shell tool, and hooks.json uses matcher Bash. codex-hooks.json declares no matcher, so the Codex hook runs on every tool call. The matcher-exemption test feeds a synthetic manifest line that the real file does not contain.

## Evidence

- **brokers-and-verification-012** (minor): The hook docstring and the Codex guide say the lockfile PreToolUse hook is 'matched to the shell tool by the hook manifest'. hooks.json has matcher Bash, but codex-hooks.json declares none, so the Codex hook runs for every tool call. The matcher-exemption test feeds a synthetic codex-hooks.json matcher line that the real file does not contain.
  - `speckit-pro/codex-hooks.json:8-18`, `speckit-pro/hooks/hooks.json:37-47`, `speckit-pro/scripts/workflow-guard-hook.py:3-6`, `tests/speckit-pro/unit/test-workflow-guard-hook.py:208-221`

## Proposed fix

- brokers-and-verification-012: Add the shell-tool matcher to codex-hooks.json, or correct the docstring and guide and drop the synthetic case.

## Acceptance

- [ ] codex-hooks.json matches the shell tool, or the docstring and guide state the real scope.
- [ ] The exemption test reads the real codex-hooks.json and fails before the fix.
- [ ] dist/ is regenerated.

## Related

- None.

Found by the 2026-09 coherence audit.
