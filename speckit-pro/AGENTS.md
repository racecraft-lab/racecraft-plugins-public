# Plugin Source Instructions

This directory is plugin source. Some subdirectories ship to every installer, so
keep changes intentional and scoped.

## What This Is

SpecKit Pro wraps GitHub Spec Kit so an agent takes a rough idea to a reviewed
pull request: PRD and roadmap, a scaffolded spec, then an autopilot that runs
Specify, Clarify, Plan, Checklist, Tasks, Analyze, Implement, and a PR. One
workflow ships for Claude Code and Codex.

## How the Parts Fit

- Skills (`skills/`, with Codex overlays in `codex-skills/`) hold the workflow
  prose; `speckit-autopilot` orchestrates it and dispatches the named agents in
  `agents/`. Each paired role's Codex twin in `codex-agents/` is generated
  from its `agents/*.md` source, where Codex-only text sits inside
  `<!-- host:codex: reason -->` blocks. Edit the source, never the TOML.
- Decisions that must be deterministic (gates, stage resolution, ledgers, PR
  packets) live in the Python runner, `speckit_pro_runner/`; skills call a
  runner helper by id (`helpers/registry.py`) instead of restating its logic.
- A behavior change ships for both hosts in the same change.
- This repository builds speckit-pro with speckit-pro. A live autopilot run
  executes the installed, cached plugin, not these source files, so a source
  fix reaches a run only after a release and a cache refresh.

## Local Rules

- Read nearby manifests, skill files, and code before assuming structure.
- Do not add stray Markdown files under `agents/`; agent definitions need the
  expected frontmatter.
- Keep shipped Python runtime code on Python 3.11+ standard library.
- Put a new runner helper in its own module under
  `speckit-pro/speckit_pro_runner/helpers/` and add that path to the root
  `mypy.ini`; `read_only.py` and `mutation.py` sit outside the type-check
  ratchet.
- If a source change can affect packaged output, run or account for the release
  artifact generator before finishing.
- Do not duplicate long workflow, test, or release procedures here; use root
  `AGENTS.md` and the repository docs as the source of truth.
