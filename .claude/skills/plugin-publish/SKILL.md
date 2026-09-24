---
name: plugin-publish
description: Stage, commit, push, and open a PR for plugin changes. Validates the commit message against conventional-commits (required by validate-pr-title CI check), runs Layer 1 structural tests first, and reminds the user to run /plugin marketplace update after merge. Triggers on "publish plugin", "push plugin changes", "ship this plugin", "release this branch".
license: MIT
disable-model-invocation: true
---

# plugin-publish

User-invocable. Stops Claude from auto-running this — it has side effects (push, PR).

## What this does

Walks through the publish flow in the root `AGENTS.md` (Commands, Pull Requests, Definition Of Done) and enforces the parts that are easy to forget:

1. **Pre-flight check** — `python3 tests/speckit-pro/run-all.py --layer 1` must pass (catches missing frontmatter and invalid JSON).
2. **Detect remote** — run `git remote -v`; do not assume the remote is named `origin`.
3. **Stage selectively** — list candidate files, ask user which to include. NEVER `git add -A` or `git add .`.
4. **Commit with conventional-commits prefix** — required types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`. Validate before writing.
5. **Push and open the PR** — follow the Pull Requests section of the root `AGENTS.md`, which opens every PR with the `gh-stack` skill. Validate the final title with the release-readiness gate first. For `feat` and `fix` PRs, fill the `release-note` fence or apply the `release-note/skip` label.
6. **Remind user** — after PR is merged (squash-only), tell them to run:
   ```
   /plugin marketplace update racecraft-plugins-public
   ```

## When NOT to use

- For a release (release-please handles version bumps automatically — do not manually edit `plugin.json` versions)
- For docs-only PRs; commit and open the PR directly.
- For version fields in `release-please-config.json`, `.release-please-manifest.json`, or the marketplace registries: release automation owns them (see the Release Automation section of `docs-site/src/content/docs/contribute-and-release.md`).

## Hard rules

- Never merge the PR; a human reviews and merges it.
- Never use `--no-verify` to skip hooks
- Never push to `main` directly (branch protection blocks it; use a feature branch + PR)
- PR title format: `<type>(<lowercase-scope>): <description>`. The scope is required: the `validate-pr-title` CI job rejects a title without one.

## Output

When complete, report:

- Branch name pushed
- PR URL
- The marketplace-update command the user needs to run post-merge
