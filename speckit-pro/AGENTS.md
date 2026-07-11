# speckit-pro Plugin Guidelines

Everything in the allowlisted subdirectories of this directory ships to every plugin consumer on the next release. Treat every edit here as a public product change.

## What ships

The payload builder copies an explicit allowlist, not the whole directory. Claude payload: `.claude-plugin/`, `agents/`, `commands/`, `hooks/`, `skills/`, `scripts/`, `speckit_pro_runner/`, `README.md`, `CHANGELOG.md`. Codex payload: `.codex-plugin/`, `codex-agents/`, `codex-hooks.json`, `codex-skills/` (merged with `skills/`), plus the shared items. Anything inside an allowlisted directory ships wholesale; files at this directory's root that are not on the list (including this one) do not ship.

## Hard rules

- Never add a stray `.md` file inside `agents/` — the payload conformance validator treats every `agents/*.md` as an agent definition and fails CI when it lacks agent frontmatter.
- Any change to shipped bytes changes the payload tree hash and requires the payload/proof regeneration ritual before release readiness passes. Docs-only edits outside the allowlist do not.
- `speckit_pro_runner/**/*.py` is hash-manifested (trust metadata); Python 3.11+ standard library only.
- New skills: `skills/<name>/SKILL.md` (+ optional `references/`, `scripts/`), mirrored under `codex-skills/<name>/` when a Codex counterpart exists. Validate with `python3 tests/speckit-pro/run-all.py --layer 1`.
