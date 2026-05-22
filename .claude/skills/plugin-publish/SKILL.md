---
name: plugin-publish
description: Stage, commit, push, and open a PR for plugin changes. Validates the commit message against conventional-commits (required by validate-pr-title CI check), runs Layer 1 structural tests first, and reminds the user to run /plugin marketplace update after merge. Triggers on "publish plugin", "push plugin changes", "ship this plugin", "release this branch".
license: MIT
disable-model-invocation: true
---

# plugin-publish

User-invocable. Stops Claude from auto-running this — it has side effects (push, PR).

## What this does

Walks through the publish flow documented in `CLAUDE.md`, but enforces the parts that are easy to forget:

1. **Pre-flight check** — `bash speckit-pro/tests/run-all.sh --layer 1` must pass (fast, ~5s, catches missing frontmatter / invalid JSON).
2. **Detect remote** — `git remote -v` (per global CLAUDE.md "Git Operations" rule — don't assume `origin`).
3. **Stage selectively** — list candidate files, ask user which to include. NEVER `git add -A` or `git add .`.
4. **Commit with conventional-commits prefix** — required types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`. Validate before writing.
5. **Push and open PR** — `gh pr create` with the same prefix in the title (the `validate-pr-title` CI check enforces this).
6. **Remind user** — after PR is merged (squash-only), tell them to run:
   ```
   /plugin marketplace update racecraft-plugins-public
   ```

## When NOT to use

- For a release (release-please handles version bumps automatically — do not manually edit `plugin.json` versions)
- For docs-only PRs touching `CLAUDE.md` or `README.md` (the `detect` CI job skips test matrix anyway; just commit + push, no skill needed)
- For the marketplace.json/release-please-config.json triplet — those have their own PreToolUse guard hook

## Hard rules

- Never merge the PR (only humans merge — see global memory)
- Never use `--no-verify` to skip hooks
- Never push to `main` directly (branch protection blocks it; use a feature branch + PR)
- Conventional-commit title format: `<type>(<scope>): <description>` (scope optional)

## Output

When complete, report:

- Branch name pushed
- PR URL
- The marketplace-update command the user needs to run post-merge
