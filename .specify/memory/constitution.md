<!--
  Sync Impact Report
  ==================
  Version change: 1.2.0 → 2.0.0
  Bump rationale: MAJOR. Principle I drops `commands/` from the required
    layout and moves typesafe-jev tests out of `tests/<plugin>/`; Principle
    VI replaces the master-plan requirement. Both are incompatible
    redefinitions under the versioning policy below.
  Modified principles:
    - I. Plugin Structure Compliance (commands/ removed; Codex surfaces and
      typesafe-jev layout added)
    - II. Cross-Platform Runtime & Script Safety (Go toolchain exception for
      typesafe-jev)
    - III. Semantic Versioning (Claude and Codex manifests; the one sanctioned
      runner-manifest hand edit)
    - IV. Test Coverage Before Merge (CI suite adds Layers 6 and 7; ruff and
      mypy when Python changes)
    - V. Conventional Commits (required lowercase scope; types from the live
      title gate)
    - VI. KISS, Simplicity & YAGNI (PRD, technical roadmap, and roadmap MOC
      replace the master plan)
  Added principles:
    - VII. Generated Artifact Contract
    - VIII. Two-Host Parity
    - IX. Fail-Closed Gates and Red-First Fixes
    - X. Public-Repository Privacy
  Added sections: None
  Removed sections: None
  Modified sections:
    - Quality Gates (rows for Principles VII–X; CI suite and lint rows)
    - Development Workflow (stack squash merges, review ruleset, artifact sync)
  Templates requiring updates:
    - .specify/templates/plan-template.md — ✅ No update needed
      (Constitution Check section is dynamically populated from principles)
    - .specify/templates/spec-template.md — ✅ No update needed
      (principle-agnostic template)
    - .specify/templates/tasks-template.md — ✅ No update needed
      (principle-agnostic template)
  Follow-up TODOs: None
-->

# Racecraft Plugins Public Constitution

## Core Principles

### I. Plugin Structure Compliance

Every plugin MUST follow the Claude Code and Codex plugin layouts it ships:

- `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` manifests with
  required fields: `name` (kebab-case), `version` (semver), and
  `description` (non-empty)
- `agents/` — Claude subagent definitions as `.md` files with valid
  frontmatter; `codex-agents/` — their Codex twins as `.toml` files
- `skills/` — skill directories with `SKILL.md` entry points;
  `codex-skills/` — Codex overlays of those skills
- `hooks/` — Claude event hooks with valid `hooks.json`;
  `codex-hooks.json` — Codex hooks
- speckit-pro's repository-only tests MUST live under top-level
  `tests/speckit-pro/`, outside the install-facing plugin directory
- typesafe-jev ships from `typesafe-jev/plugin/` with no generated payload;
  its Go source and Go tests live in `typesafe-jev/cmd/evaluate/`

Plugin names MUST be kebab-case matching the pattern
`^[a-z][a-z0-9]*(-[a-z0-9]+)*$`.

**Quality gate**: `python3 tests/speckit-pro/run-all.py --layer 1`; for
typesafe-jev, `python3 scripts/check-go-module.py check`

### II. Cross-Platform Runtime & Script Safety

Active repository tooling MUST run on Python 3.11+ standard library without
requiring Bash, `jq`, PowerShell helper scripts, or package installation.
Python entry points MUST use structured parsers, platform-safe path APIs,
argument arrays, `shell=False`, explicit return-code handling, and
deterministic UTF-8 I/O.

Go is the one sanctioned exception, and only for `typesafe-jev/`. The
scripts and tests that build, check, and release it MUST stay Python.

Repository-authored Bash is permitted only as bounded GitHub Actions dispatch
or sentinel control-flow glue under `.github/workflows/`; it MUST NOT implement
domain validation, packaging, installation, release, or plugin runtime behavior.
The fixed vendored `.specify/**` allowlist is historical upstream tooling,
MUST remain excluded from release-readiness evidence, and MUST NOT be
broadened or substituted.

**Quality gate**: repository Bash-confinement and active-path guards through
`python3 tests/speckit-pro/run-all.py --layer 4`

### III. Semantic Versioning

Plugins MUST use `MAJOR.MINOR.PATCH` versioning matching the pattern
`^[0-9]+\.[0-9]+\.[0-9]+$`. Breaking changes MUST bump MAJOR. New features
MUST bump MINOR. Bug fixes MUST bump PATCH.

Release-please owns every version: `.release-please-manifest.json`, both
plugin manifests, and the marketplace entries it keeps in step. Manual version
edits are prohibited, with one sanctioned exception: after merging a release
into a branch that also changed speckit-pro's runner manifest, set its
`plugin_version` to the `.codex-plugin/plugin.json` version before
regenerating artifacts.

**Quality gate**: Layer 1 `validate-plugin` semantic-version check and CI
`artifact-consistency`

### IV. Test Coverage Before Merge

All new Python helpers, gates, and repository tools MUST have corresponding
Layer 4 unit coverage under `tests/speckit-pro/unit/`. All new plugin
components (agents, skills, hooks, manifests, and generated payloads) MUST
pass Layer 1 structural validation. Layer membership and dispatch MUST remain
declared in `tests/speckit-pro/suite-manifest.json`.

No implementation is complete until the CI suite passes with zero failures:
the default suite (Layers 1, 4, 5) plus Layers 6 and 7. When Python changes,
ruff and mypy MUST also pass locally, because the `mypy-ratchet` job is not a
required check and CI will not stop a regression.

**Quality gate**: the CI-suite runner request in `AGENTS.md` (Layers 1, 4,
5, 6, 7 — zero failures); `scripts/run-python-lint.py run ruff` and `run mypy`

### V. Conventional Commits

Every PR title MUST match `<type>(<lowercase-scope>): <plain English
description>`, because squash merge makes the PR title the commit subject on
`main`. The live title gate accepts the types `feat`, `fix`, `chore`,
`docs`, `test`, and `refactor`, and requires a scope.

The scope names the affected area: a plugin (`speckit-pro`,
`typesafe-jev`) or a repository surface (for example `repo`, `ci`, `deps`,
`formal`). This convention drives automated changelog generation and version
bumps via release-please. Only `feat` and `fix` PRs fill the `release-note`
fence, which is required unless the PR is labeled `release-note/skip`.

**Quality gate**: CI `validate-pr-title` and `validate-release-note` jobs

### VI. KISS, Simplicity & YAGNI

**KISS (Keep It Simple):** Every solution MUST use the simplest approach that
solves the problem. Prefer flat over nested, explicit over implicit, and
readable over clever. If a reviewer cannot understand the code in 30 seconds,
it is too complex. Tooling MUST prefer straightforward sequential logic over
clever one-liners. JSON manipulation MUST use a structured parser such as
Python's standard-library `json` module, not `jq` or chained text-processing
substitutions.

**YAGNI (You Aren't Gonna Need It):** No speculative features. No
abstractions for one-time operations. No wrapper layers unless migration is
planned and documented. Three similar lines of code are better than a
premature abstraction.

**Plugin scope:** Plugins MUST do one thing well; scope creep requires
explicit justification in the owning roadmap. A new plugin MUST have a PRD, a
technical roadmap, and a roadmap MOC under `docs/ai/specs/` before its
directory is created.

**Quality gate**: Plan review of the PRD and roadmap for new plugins; code
review for complexity justification

### VII. Generated Artifact Contract

Generated artifacts are a pure function of the source tree. `dist/` payloads,
marketplace versions, runner manifests and hashes, and generated reference
pages MUST be regenerated, never hand-edited, and MUST be committed with the
source change that produces them. Merges MUST regenerate these artifacts
rather than hand-resolve them.

**Quality gate**: `python3 scripts/refresh-release-artifacts.py --check` (CI
`artifact-consistency`); `pnpm --dir docs-site reference:check` when reference
inputs change

### VIII. Two-Host Parity

Every behavior change to speckit-pro MUST ship for Claude Code and Codex
together, in the same change: the Claude skill or agent and its Codex overlay
or TOML twin. Both hosts MUST carry the same set of agents. A difference
between hosts is permitted only where a host lacks the capability, and MUST
be documented at the point of difference.

**Quality gate**: Layer 7 parity fixtures and Layer 1 mirror contracts

### IX. Fail-Closed Gates and Red-First Fixes

Gates, validators, and helpers that judge evidence MUST fail closed: missing,
unreadable, or unparseable evidence yields a failure or an explicit unknown,
never a pass. A check MUST NOT pass on nothing.

A bug fix MUST start red: a test that fails on the bug, observed failing
before the fix makes it pass. When code and a document state the same
contract (a request shape, threshold, or path), a test MUST execute the
document's example, or one MUST be derived from the other.

**Quality gate**: code review (a check that passes on nothing is a blocking
finding) and the regression test in the fixing change

### X. Public-Repository Privacy

This repository is public. Committed files, PR titles and bodies, branch
names, and commit messages MUST NOT contain local home paths, host temporary
paths, raw UUIDs or native session identifiers, non-allowlisted emails, or
names of private infrastructure. Use repository-relative paths and
placeholders. Sensitive execution records MUST live outside the working tree
and be published only as portable receipts.

**Quality gate**: `tests/speckit-pro/unit/test-privacy-scan.py` (scans tracked
and untracked files)

## Quality Gates

*GATE: All gates MUST pass before implementation is considered complete.*

| Gate | Principle | Command |
|------|-----------|---------|
| Structural validation | I. Plugin Structure | `python3 tests/speckit-pro/run-all.py --layer 1` |
| Go module checks | I. Plugin Structure | `python3 scripts/check-go-module.py check` |
| Runtime and script safety | II. Cross-Platform Safety | `python3 tests/speckit-pro/run-all.py --layer 4` |
| Version format | III. Semantic Versioning | Layer 1 `validate-plugin` |
| Test coverage | IV. Test Coverage | CI suite: Layers 1, 4, 5, 6, 7 |
| Python lint | IV. Test Coverage | `scripts/run-python-lint.py run ruff` and `run mypy` |
| Commit and release-note format | V. Conventional Commits | CI `validate-pr-title`, `validate-release-note` |
| KISS + scope justification | VI. KISS/Simplicity | Roadmap review + code review |
| Generated artifacts | VII. Generated Artifacts | `python3 scripts/refresh-release-artifacts.py --check` |
| Host parity | VIII. Two-Host Parity | Layer 7 parity fixtures |
| Fail-closed checks | IX. Fail-Closed Gates | Code review + regression test |
| Privacy | X. Privacy | `tests/speckit-pro/unit/test-privacy-scan.py` |

## Development Workflow

- All changes arrive on `main` through a PR opened with `gh-stack`, even a
  single PR
- A stack merges with `gh stack merge <stack> --squash`, one squash commit per
  PR, so release-please lists each change; a single merge commit for a stack
  collapses the release notes and is not used
- The `main` ruleset requires a PR with 1 approval, a code-owner review, and
  resolved review threads; the admin role is exempt
- Branch protection requires `validate-plugins`, `validate-pr-title`,
  `validate-release-note`, `container-preflight-linux-amd64`, and
  `container-preflight-linux-arm64`; required checks are non-strict
- Layers 2 and 3 (AI evals) run locally before merge, not in CI
- Release-please opens the release PR; `scripts/refresh-release-artifacts.py`
  keeps marketplace versions, payloads, and runner hashes in step, and CI
  `artifact-consistency` verifies them

## Governance

This constitution supersedes all other development practices for this
repository. All PRs and code reviews MUST verify compliance with the
principles above. `AGENTS.md` carries the runnable commands and day-to-day
agent rules; where the two disagree, this constitution wins and `AGENTS.md`
MUST be corrected.

**Amendment procedure:**
1. Document the rationale for the change
2. Assess backward compatibility with existing specs and plans
3. Update the constitution with version bump (see below)
4. Propagate changes to dependent templates if needed

**Versioning policy:**
- MAJOR bump: Principle removed or incompatibly redefined
- MINOR bump: New principle added or existing principle expanded
- PATCH bump: Clarification, wording, or typo fix

**Complexity tracking:** When a principle violation is justified, document it
in the plan's Complexity Tracking table with the violation, rationale, and why
the simpler alternative was rejected.

**Version**: 2.0.0 | **Ratified**: 2026-03-24 | **Last Amended**: 2026-09-26
