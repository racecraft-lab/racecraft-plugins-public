<!--
  Sync Impact Report
  ==================
  Version change: 1.1.0 → 1.2.0
  Modified principles:
    - I. Plugin Structure Compliance (repository-only tests clarified)
    - II. Script Safety → Cross-Platform Runtime & Script Safety
    - IV. Test Coverage Before Merge (Python-authoritative suite)
    - VI. KISS, Simplicity & YAGNI (structured JSON guidance)
  Added sections: None
  Removed sections: None
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

Every plugin MUST follow the standard Claude Code plugin directory layout:

- `.claude-plugin/plugin.json` manifest with required fields: `name`
  (kebab-case), `version` (semver), and `description` (non-empty)
- `commands/` — slash command definitions with YAML frontmatter
  (`description:` and `allowed-tools:` fields required)
- `agents/` — subagent definitions as `.md` files
- `skills/` — skill directories with `SKILL.md` entry points
- `hooks/` — event hooks with valid `hooks.json`
- repository-only tests MUST live under top-level `tests/<plugin>/`, outside the
  install-facing plugin directory

Plugin names MUST be kebab-case matching the pattern
`^[a-z][a-z0-9]*(-[a-z0-9]+)*$`.

**Quality gate**: `python3 tests/speckit-pro/run-all.py --layer 1`

### II. Cross-Platform Runtime & Script Safety

Active repository tooling MUST run on Python 3.11+ without requiring Bash,
`jq`, PowerShell helper scripts, or package installation. Python entry points
MUST use structured parsers, platform-safe path APIs, argument arrays,
`shell=False`, explicit return-code handling, and deterministic UTF-8 I/O.

Repository-authored Bash is permitted only as bounded GitHub Actions dispatch
or sentinel control-flow glue under `.github/workflows/`; it MUST NOT implement
domain validation, packaging, installation, release, or plugin runtime behavior.
The fixed vendored
`.specify/**` allowlist is historical upstream tooling, MUST remain excluded
from release-readiness evidence, and MUST NOT be broadened or substituted.

**Quality gate**: repository Bash-confinement and active-path guards through
`python3 tests/speckit-pro/run-all.py --layer 4`

### III. Semantic Versioning

Plugins MUST use `MAJOR.MINOR.PATCH` versioning matching the pattern
`^[0-9]+\.[0-9]+\.[0-9]+$`. The `version` field in
`.claude-plugin/plugin.json` is the single source of truth — per
Anthropic documentation, `plugin.json` always takes precedence over
`marketplace.json`. Breaking changes MUST bump MAJOR. New features
MUST bump MINOR. Bug fixes MUST bump PATCH.

Version management is automated via release-please. Manual version
edits are prohibited except during initial plugin creation.

**Quality gate**: Layer 1 `validate-plugin` semantic-version check

### IV. Test Coverage Before Merge

All new Python helpers, gates, and repository tools MUST have corresponding
Layer 4 unit coverage under `tests/speckit-pro/unit/`. All new plugin
components (commands, agents, skills, hooks, manifests, and generated
payloads) MUST pass Layer 1 structural validation. Layer membership and
dispatch MUST remain declared in `tests/speckit-pro/suite-manifest.json`.
No implementation is complete until the Python-authoritative default suite
passes with zero failures.

**Quality gate**: `python3 tests/speckit-pro/run-all.py` (Layers 1, 4, 5 — zero failures)

### V. Conventional Commits

All commits MUST follow the format `type(scope): description`.

Valid types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`.

Scopes MUST map to plugin directory names (e.g., `speckit-pro`).
Unscoped commits are permitted for repo-wide changes (e.g.,
`chore: update CI workflow`). This convention drives automated
changelog generation and version bumps via release-please.

PR titles MUST be valid conventional commits because squash merge
uses the PR title as the commit message on `main`.

**Quality gate**: CI `validate-pr-title` job

### VI. KISS, Simplicity & YAGNI

**KISS (Keep It Simple):** Every solution MUST use the simplest
approach that solves the problem. Prefer flat over nested, explicit
over implicit, and readable over clever. If a reviewer cannot
understand the code in 30 seconds, it is too complex. Tooling MUST prefer
straightforward sequential logic over clever one-liners. JSON manipulation
MUST use a structured parser such as Python's standard-library `json` module,
not `jq` or chained text-processing substitutions.

**YAGNI (You Aren't Gonna Need It):** No speculative features. No
abstractions for one-time operations. No wrapper layers unless
migration is planned and documented. Three similar lines of code
are better than a premature abstraction.

**Plugin scope:** Plugins MUST do one thing well — scope creep
requires explicit justification in the master plan. New plugins
MUST have a clear purpose documented in the master plan at
`docs/ai/specs/` before directory creation.

**Quality gate**: Plan review — master plan entry required for new plugins;
code review for complexity justification

## Quality Gates

*GATE: All gates MUST pass before implementation is considered complete.*

| Gate | Principle | Command |
|------|-----------|---------|
| Structural validation | I. Plugin Structure | `python3 tests/speckit-pro/run-all.py --layer 1` |
| Runtime and script safety | II. Cross-Platform Safety | `python3 tests/speckit-pro/run-all.py --layer 4` |
| Version format | III. Semantic Versioning | Layer 1 `validate-plugin` |
| Test coverage | IV. Test Coverage | `python3 tests/speckit-pro/run-all.py` |
| Commit format | V. Conventional Commits | CI `validate-pr-title` |
| KISS + scope justification | VI. KISS/Simplicity | Master plan review + code review |

## Development Workflow

- All changes arrive on `main` via PR; normal integration uses squash merge
- A temporary merge-commit exception for a dependent PR stack MUST be explicitly
  authorized, preserve bottom-to-top ancestry, and restore squash-only settings
  immediately after the stack lands
- Branch protection requires `validate-plugins`, `validate-pr-title`,
  `validate-release-note`, `container-preflight-linux-amd64`, and
  `container-preflight-linux-arm64`; required checks are non-strict
- Layers 2/3 (AI evals) are run locally before merge, not in CI
- Release-please automates version bumps and changelog generation
- `marketplace.json` versions are synced from `plugin.json` by CI

## Governance

This constitution supersedes all other development practices for
this repository. All PRs and code reviews MUST verify compliance
with the principles above.

**Amendment procedure:**
1. Document the rationale for the change
2. Assess backward compatibility with existing specs and plans
3. Update the constitution with version bump (see below)
4. Propagate changes to dependent templates if needed

**Versioning policy:**
- MAJOR bump: Principle removed or incompatibly redefined
- MINOR bump: New principle added or existing principle expanded
- PATCH bump: Clarification, wording, or typo fix

**Complexity tracking:** When a principle violation is justified,
document it in the plan's Complexity Tracking table with the
violation, rationale, and why the simpler alternative was rejected.

**Version**: 1.2.0 | **Ratified**: 2026-03-24 | **Last Amended**: 2026-07-11
