# Repository Guidelines

## Project Structure & Module Organization

This repository is a Claude Code plugin marketplace. The registry lives in `.claude-plugin/marketplace.json`. Each plugin gets its own top-level directory; today that is `speckit-pro/`.

Inside `speckit-pro/`:

- `commands/` contains slash-command docs with required YAML frontmatter.
- `skills/` contains skill folders such as `speckit-autopilot/` and `speckit-coach/`, each with a `SKILL.md` entry point plus optional `references/` and `scripts/`.
- `agents/` contains sub-agent definitions.
- `hooks/` contains plugin hook configuration.
- `tests/` contains the 5-layer shell test suite.

## Build, Test, and Development Commands

There is no compiled build step. Work is validated through shell scripts and repository structure checks.

- `cd speckit-pro && bash tests/run-all.sh` runs the default deterministic layers: 1, 4, and 5.
- `cd speckit-pro && bash tests/run-all.sh --layer 1` runs structural validation only.
- `cd speckit-pro && bash tests/run-all.sh --layer 4` runs script unit tests.
- `cd speckit-pro && bash tests/run-all.sh --all` includes AI-eval layers when prerequisites are installed.

For marketplace updates, commit and push changes, then refresh the marketplace in Claude Code with `/plugin marketplace update racecraft-plugins-public`.

## Coding Style & Naming Conventions

Use Bash and Markdown consistently with the existing codebase: 2-space indentation in Markdown lists/tables where needed, and shell scripts starting with `#!/usr/bin/env bash` plus `set -euo pipefail`.

Name plugins and skill directories in kebab-case, for example `speckit-autopilot`. Keep command filenames aligned with command names, for example `commands/autopilot.md`. Command docs must start and end frontmatter with `---` and include `description:` and `allowed-tools:`.

## Testing Guidelines

Tests are shell-based. Structural tests verify manifests, command frontmatter, hooks, skills, and agents. Script tests cover helper scripts such as `skills/.../scripts/validate-gate.sh`.

Add or update tests when changing command schemas, hook config, skill layout, or script behavior. Prefer the smallest relevant layer during development, then rerun `bash tests/run-all.sh` before opening a PR.

## Commit & Pull Request Guidelines

Follow the repo’s existing Conventional Commit pattern: `feat(skills): ...`, `fix(agents): ...`, `chore(evals): ...`. Keep scopes specific to the area changed.

PRs should include a brief summary, affected plugin paths, test commands run, and sample output or screenshots when user-facing command behavior changes.
