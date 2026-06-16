# Platform Separation Review

Reviewed `docs-site/src/content/docs/first-run.md`,
`docs-site/src/content/docs/spec-kit-lifecycle.mdx`, and
`docs-site/src/components/LifecycleFlow.astro`.

## Result

- Claude Code and Codex command surfaces are shown in separate table columns.
- Claude Code examples consistently use `/speckit-pro:<skill>`.
- Codex examples consistently use `$speckit-*`.
- Platform-neutral lifecycle text is explanatory and does not collapse the two
  invocation syntaxes into one mixed example.

## Status

Pass.
