# Plugin Source Instructions

This directory is plugin source. Some subdirectories ship to every installer, so
keep changes intentional and scoped.

## Local Rules

- Read nearby manifests, skill files, and code before assuming structure.
- Do not add stray Markdown files under `agents/`; agent definitions need the
  expected frontmatter.
- Keep shipped Python runtime code on Python 3.11+ standard library.
- If a source change can affect packaged output, run or account for the release
  artifact generator before finishing.
- Do not duplicate long workflow, test, or release procedures here; use root
  `AGENTS.md` and the repository docs as the source of truth.
