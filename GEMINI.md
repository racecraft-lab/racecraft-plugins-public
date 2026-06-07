# Racecraft Plugins Public Development Guidelines

Auto-generated from feature plans on archival. Last updated: 2026-06-05

## Active Technologies

- Bash (macOS/Linux) + `jq` for JSON; Python 3 only where existing scripts already
  use it. No compiled runtime — this is a Claude Code plugin marketplace.
- `git` + GitHub linguist (`linguist-generated` collapse mechanism reads each
  repository's own root `.gitattributes`).

## Project Structure

```text
.gitattributes                      # repo-root collapse rule: **/.process/** linguist-generated=true
.specify/memory/                    # distilled project memory (spec.md, plan.md, changelog.md, constitution.md)
speckit-pro/                        # the shipped plugin — copied verbatim into every consumer's install
├── skills/                         # Claude skills (speckit-scaffold-spec, speckit-coach, speckit-autopilot, ...)
└── codex-skills/                   # Codex mirrors of Claude skills (kept in parity)
tests/speckit-pro/                  # 5-layer shell test suite (run-all.sh) — sibling of the plugin, never shipped
docs/ai/specs/                      # roadmaps + design concepts; scaffold exhaust → docs/ai/specs/.process/
specs/<NNN>/                        # per-feature spec dirs; per-feature exhaust → specs/<NNN>/.process/
```

## Commands

- `bash tests/speckit-pro/run-all.sh` — default deterministic layers (1, 4, 5).
- `bash tests/speckit-pro/run-all.sh --layer 1` — structural validation only.
- `.specify/scripts/bash/check-prerequisites.sh --json --paths-only` — resolve repo paths.

## Code Style

- Shell scripts start with `#!/usr/bin/env bash` + `set -euo pipefail`; quote all
  variables; pass `bash -n`. Prefer plain bash + `jq` — no new dependency, no new
  abstraction layer, no flags "for future flexibility" for a single call site.
- Every prose redirect in a Claude skill MUST be mirrored identically into its
  Codex counterpart (parity is enforced by `validate-codex-skills.sh` + Layer-8).

## Recent Changes

- **007 Artifact relocation — tiering, .process/, collapse** [Source: specs/007-artifact-relocation]:
  CONTRACT-vs-EXHAUST taxonomy; redirected speckit-pro-authored exhaust
  (design-concept doc, workflow file, UAT runbook) into `.process/`; repo-root +
  consumer `linguist-generated` collapse rule for `.process/`; gate excludes
  `/.process/` from diff-mode reviewable-LOC; Layer-1 lint guards collapse scope.

## Gotchas

- **The `/.process/` segment is the single anchor** for the collapse rule, the gate
  exclusion, AND the lint. They are intentionally kept in separate places (the gate
  does NOT parse `.gitattributes`); a cross-file lint guards them against drift.
- **Collapse is generated-only — never `-diff`.** Relocated artifacts stay diffable
  and loadable on demand (FR-008). Broadening any collapse rule beyond `.process/`
  fails the lint.
- **linguist reads each repo's own root `.gitattributes`.** A plugin-only rule
  collapses only the plugin's PRs — consuming projects need the rule written into
  their own repo root (the idempotent scaffold ensure-step does this).
- **Consumer `.gitattributes` append must be safe-write**: fixed-string whole-line
  presence check (`grep -qxF`), normalize trailing newline before appending, write
  to a SAME-DIRECTORY temp file then atomic `mv` (cross-device `mv` on macOS is not
  atomic), `trap` to clean up the temp.
- **New-specs-only**: never migrate/mutate an existing `specs/<NNN>/` directory or
  the pre-existing non-`.process/` files in `docs/ai/specs/` (legacy
  `SPEC-*-workflow.md`, roadmaps, the pipeline-verification runbook). Legacy
  relocation is a separate, later retro-migration spec.
- **Reviewability surface budget**: the gate's `surface_for_path()` shards a change
  into ≥2 surfaces by filename. A genuinely single-logical-surface change can clear
  the resulting blocker with a ratified `split exception` phrase in an in-scope `.md`.

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
