# Racecraft Plugins Public Development Guidelines

Auto-generated from feature plans on archival. Last updated: 2026-07-15

## Project Structure

```text
.gitattributes                      # repo-root collapse rule: **/.process/** linguist-generated=true
.specify/memory/                    # distilled project memory (spec.md, plan.md, changelog.md, constitution.md)
speckit-pro/                        # the shipped plugin — copied verbatim into every consumer's install
├── skills/                         # Claude skills (speckit-scaffold-spec, speckit-coach, speckit-autopilot, ...)
└── codex-skills/                   # Codex mirrors of Claude skills (kept in parity)
tests/speckit-pro/                  # manifest-driven Python test suite — sibling of the plugin, never shipped
docs/ai/specs/                      # roadmaps + design concepts; scaffold exhaust → docs/ai/specs/.process/
specs/<NNN>/                        # per-feature spec dirs; per-feature exhaust → specs/<NNN>/.process/
```

## Commands

- `python3 tests/speckit-pro/run-all.py` — default deterministic layers (1, 4, 5).
- `python3 tests/speckit-pro/run-all.py --layer 1` — structural validation only.
- `python3 tests/speckit-pro/check-toolchain.py --mode tests` — verify the test toolchain.

## Code Style

- Python entrypoints use `#!/usr/bin/env python3`, the Python 3.11+ standard
  library, argument arrays, and `shell=False` for subprocesses. Keep new tooling
  inside the manifest-driven Python surface.
- Every prose redirect in a Claude skill MUST be mirrored identically into its
  Codex counterpart (parity is enforced by `validate-codex-skills.py` + Layer 8).

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
- **CAR-001 archive boundary**: the Claude routing baseline is complete and
  archived. The canonical artifacts are
  `docs/ai/research/claude-agent-route-candidates.md` and
  `docs/ai/research/claude-agent-route-candidate-manifest.json`; do not recover
  active `specs/car-001-candidate-route-baseline/` unless intentionally
  reconstructing archived spec evidence from PR #350.

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
