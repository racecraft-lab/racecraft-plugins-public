Priority: major

## Summary

The reference-page generator hard-codes hook prose that no longer matches hooks.json and codex-hooks.json, filters speckit-pro/scripts so no Python script is listed, and lists two of the three integration manifests. reference:check passes because it compares output to the same generator. Separately, validateSafetyBoundaries asserts that constants are non-empty, so it can never fail.

## Evidence

- **docs-002** (major): The hooks page generator hard-codes prose that no longer matches the hook files. It says Claude hooks are SessionStart, PreToolUse and SubagentStop with four handlers (hooks.json also has Stop and six handlers, two of them workflow-guard). It says Codex has a UserPromptSubmit hook that executes no command, but codex-hooks.json now ships live PreToolUse (lockfile) and Stop (unpushed) command handlers. The generated page therefore states events from data and contradicting prose side by side, and speckit-pro/README.md describes the two live Codex guards correctly.
  - `docs-site/scripts/generate-reference-pages.mjs:378`, `docs-site/scripts/generate-reference-pages.mjs:384`, `docs-site/scripts/generate-reference-pages.mjs:399`, `docs-site/scripts/generate-reference-pages.mjs:404`, `speckit-pro/codex-hooks.json:8-27`, `speckit-pro/hooks/hooks.json:1`
- **docs-003** (major): buildScriptsPage lists speckit-pro/scripts with the filter /\.(sh|json|mjs|js)$/, which excludes .py. The directory holds six Python scripts (workflow-guard-hook, sweep-isolation-hook, agent-memory-ignore, crap-score, mutation-score, ubiquitous-language-lint) and one JSON file, so the generated Plugin Scripts group inventories only curated-set.json. reference:check passes because it compares output to the same buggy generator.
  - `docs-site/scripts/generate-reference-pages.mjs:494`, `speckit-pro/scripts/workflow-guard-hook.py:1`, `speckit-pro/scripts/sweep-isolation-hook.py:1`
- **docs-015** (minor): validateSafetyBoundaries asserts that constants defined a few hundred lines earlier are non-empty, so it can never fail, and DOCUMENTED_SAFETY_BOUNDARIES is used nowhere else (no other reader, no check of the docs against it). The check reports a pass while verifying nothing.
  - `docs-site/scripts/validate-docs-quality.mjs:41`, `docs-site/scripts/validate-docs-quality.mjs:551-557`
- **docs-016** (minor): The manifests page reads a hard-coded list that includes .specify/integrations/claude.manifest.json and speckit.manifest.json but omits codex.manifest.json, which exists. The page claims to separate Claude Code and Codex manifests.
  - `docs-site/scripts/generate-reference-pages.mjs:452`, `speckit-pro/.codex-plugin/plugin.json:1`

## Proposed fix

- docs-002: Compute the handler counts and per-event descriptions from the parsed hook JSON, and rewrite the Codex record to describe the PreToolUse and Stop guards. Regenerate the reference pages.
- docs-003: Include py in the speckit-pro/scripts filter (the root and autopilot groups already do) and regenerate reference/scripts.md.
- docs-015: Drop the check and the constant, or validate the documented boundaries against SafeInstallAids and the safe-aids validator forbidden patterns.
- docs-016: Enumerate .specify/integrations/*.manifest.json instead of listing two of the three.

## Acceptance

- [ ] Hook counts and event descriptions are computed from the parsed hook JSON.
- [ ] The scripts page lists every .py script in speckit-pro/scripts.
- [ ] The manifests page enumerates .specify/integrations/*.manifest.json.
- [ ] validateSafetyBoundaries either checks the documented boundaries against a real source or is removed. A test shows it can fail.
- [ ] pnpm --dir docs-site reference:generate is rerun and the regenerated pages are committed. reference:check and validate pass.

## Related

- None.

Found by the 2026-09 coherence audit.
