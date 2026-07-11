# Repository Guidelines

## Working in This Repo

Four rules, in priority order. These exist because plugin/marketplace edits have high blast radius (every install consumer gets the change on `/plugin marketplace update`) and most defects here come from doing too much, not too little.

### 1. Surface assumptions before editing
- State them in chat before touching files. If a plugin manifest, release config, or CI workflow change is ambiguous, ask — don't infer.
- If a request has multiple reasonable interpretations (e.g., "fix the release" could mean bump version, re-trigger workflow, or patch the script), list them and let the user pick.
- If a simpler approach exists (e.g., a `chore:` empty commit vs. a code change), say so before implementing the larger one.
- If something is unclear, stop and name what's confusing — don't push through on a guess.

### 2. Simplest change that solves it
- No features beyond what was asked. No new abstractions for one-call-site code. No new test layers, scripts, or helpers unless a second use exists or is explicitly asked for.
- No flags/options "for future flexibility" — add them when a second caller actually appears. No error handling for scenarios that cannot occur.
- For repo-local gates, prefer `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < <request.json>` over new shell or `jq` logic. Do not add active repository Bash outside the bounded workflow-dispatch and fixed vendored `.specify/**` boundaries.
- If you write 200 lines where 50 would do, rewrite it. The test: "Would a senior engineer say this is overcomplicated?"

### 3. Surgical edits
- Touch only what the request requires. Don't reformat adjacent JSON, reorder keys in `plugin.json` / `marketplace.json`, or "clean up" comments you didn't author.
- When editing one plugin's files, don't drift into another plugin's files unless the task explicitly spans them.
- Remove only the imports/blocks your change orphans — leave pre-existing dead code alone (mention it, don't delete it).
- Match existing style in shell scripts, YAML, and Markdown even if you'd write it differently.
- The test: every changed line should trace directly to the user's request.

### 4. Verifiable success criteria
- Translate every task into a check before coding: "edit X" → "after edit, `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/run-default-suite.json` passes" or "`gh pr view <N>` shows green".
- For workflow / release changes, the success check is "the next release PR from release-please reflects this" — say that out loud before editing.
- For multi-step work, list the steps + their verification commands up front, then loop on them.

Tradeoff: these bias toward caution over speed. For a one-line `chore:` edit, use judgment.

## Project Structure & Module Organization

This repository is a Claude Code and Codex plugin marketplace. The Claude Code
registry lives in `.claude-plugin/marketplace.json`. Each plugin gets its own
top-level directory; today that is `speckit-pro/`.

Inside `speckit-pro/`:

- `commands/` contains Claude Code slash-command docs with required YAML
  frontmatter. Install-facing usage should still prefer current plugin skill
  wording, for example `/speckit-pro:<skill>`.
- `skills/` contains skill folders such as `speckit-autopilot/` and `speckit-coach/`, each with a `SKILL.md` entry point plus optional `references/` and `scripts/`.
- `agents/` contains sub-agent definitions.
- `hooks/` contains plugin hook configuration.
- `speckit_pro_runner/` contains the Python 3.11+ installed runtime and gates.

Repository-only validation lives under `tests/speckit-pro/`, outside the shipped
plugin. `tests/speckit-pro/suite-manifest.json` is the source of truth for layer
membership, dispatch, execution mode, and default selection.

## Build, Test, and Development Commands

There is no compiled build step. Work is validated through Python 3.11+
standard-library tooling and repository structure checks. Run commands from the
repository root.

- `python3 tests/speckit-pro/run-all.py` runs the toolchain preflight and default deterministic Layers 1, 4, and 5.
- `python3 tests/speckit-pro/run-all.py --layer 1` runs structural validation only.
- `python3 tests/speckit-pro/run-all.py --layer 4` runs the `Unit Tests` layer under `tests/speckit-pro/unit/`.
- `python3 tests/speckit-pro/run-all.py --integration` runs Layer 7 replay fixtures; add `--live` only for an intentional live integration run.
- `python3 tests/speckit-pro/check-toolchain.py --mode tests` prints the direct test-toolchain report; `docs` and `all` modes cover docs tooling.

`--all` implies live mode: it executes Layers 1, 4, 5, and live Layer 7,
prints manual command plans for live-only Layers 2, 3, and 6, and does not select
gate-only Layer 8. Do not describe it as the full deterministic suite.

For marketplace updates, commit and push changes, then refresh the marketplace in Claude Code with `/plugin marketplace update racecraft-plugins-public`.

## Coding Style & Naming Conventions

Use Python and Markdown consistently with the existing codebase: Python 3.11+
standard library, `#!/usr/bin/env python3` for executable Python files, argument
arrays and `shell=False` for subprocesses, and 2-space indentation in Markdown
lists/tables where needed. Repository-local Bash is confined to bounded workflow
dispatch glue and the fixed vendored `.specify/**` allowlist; do not introduce a
new Bash or `jq` runtime dependency. `.specify/**` is vendored upstream
SpecKit content — refresh it through the SpecKit install/upgrade tooling rather
than hand-editing it.

Name plugins and skill directories in kebab-case, for example `speckit-autopilot`. Keep command filenames aligned with command names, for example `commands/autopilot.md`. Command docs must start and end frontmatter with `---` and include `description:` and `allowed-tools:`.

## Testing Guidelines

The suite is manifest-driven and Python-authoritative. Layer 1 verifies
manifests, command frontmatter, hooks, skills, agents, payloads, and workflow
contracts. The `Unit Tests` layer uses `tests/speckit-pro/unit/` for repository
helpers and runner behavior; Layer 5 verifies agent tool scoping.

Add or update tests when changing command schemas, hook config, skill layout, or
helper behavior. Prefer the smallest relevant layer during development, then
rerun `python3 tests/speckit-pro/run-all.py` before opening a PR.

## Commit & Pull Request Guidelines

Follow the repo’s existing Conventional Commit pattern: `feat(skills): ...`, `fix(agents): ...`, `chore(evals): ...`. Keep scopes specific to the area changed.

PRs should include a brief summary, affected plugin paths, test commands run, and sample output or screenshots when user-facing command behavior changes.

Use the repository PR template. `feat` and `fix` PRs require exactly one
non-empty fenced `release-note` block unless `release-note/skip` applies. The
Release workflow refreshes generated release artifacts on the release PR branch;
do not hand-edit generated payloads, installed-cache proofs, or generated
reference pages.

## Active Technologies

- Repository validation and release gates: Python 3.11+ standard library — the manifest-driven suite under `tests/speckit-pro/` and the shipped runner `speckit-pro/speckit_pro_runner/`. Tracked Bash is confined to bounded GitHub workflow dispatch glue and the fixed vendored `.specify/**` allowlist.
- Docs site: Astro 6.4.6 + Starlight 0.40.0, pnpm 10.25.0, Node >= 22.12, JavaScript ESM, with committed generated reference pages.
- Release automation: release-please v5, deterministic release-note validation and composition, GitHub Actions with SHA-pinned actions.
- Public native Windows/macOS/Linux support claims remain blocked by the preserved XPLAT-008 operator UAT matrix.

## Recent Changes
- xplat-008-claude-codex-cutover-universal-install-release-gate: Shipped active Claude/Codex installed-runtime cutover, generated Claude/Codex payload rebuilds, public docs and README claim alignment, release-readiness/UAT/update/repair gates, partial Codex/macOS installed-cache evidence, and safe repair controls across PRs #289-#292; public native-platform claims remain blocked by pending operator UAT rows preserved under `docs/ai/specs/.process/`.
- xplat-009-plugin-source-and-payload-bash-eradication: Shipped plugin-source Bash removal, active-instruction cleanup, generated Claude/Codex payload rebuilds, the zero-Bash guard with installed-cache proof and historical allowlist, and seeded regression coverage via PR #297 (speckit-pro 2.18.0), with Windows interpreter/home resolution fixed in PR #299; repository-wide Bash confinement was completed by XPLAT-010.
- xplat-010-repository-bash-confinement: Shipped manifest-driven Python repository validation, purpose-based parity fixtures, repository Bash confinement, Linux container and advisory Windows preflight, restored spec-size estimation, and deterministic release-note validation/Highlights across PRs #311-#328; T108/T117 hosted evidence is complete, while native platform claims remain held by XPLAT-008 UAT.

Keep this file well under 32 KiB: Codex reads the root plus nested AGENTS.md files under a 32,768-byte default budget (`project_doc_max_bytes`) and silently stops adding files past it. Per-spec history belongs in `.specify/memory/archive-reports/`, not here.
