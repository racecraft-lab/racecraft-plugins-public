# Phase 0 Research: Artifact relocation — tiering, .process/, collapse

**Status**: All unknowns resolved before planning. Zero open `[NEEDS CLARIFICATION]`.

This feature was scoped against a four-agent grounding pass over the actual plugin
source. The authoritative research — the Q&A design tree, the evidence-backed
implementation map (file:line citations), and the locked decisions — lives in:

> **`docs/ai/specs/PRSG-001-design-concept.md`**

This file is a pointer, not a duplicate, to avoid split-brain between the design
concept and the plan. The decisions it resolved (each with source evidence):

| Decision | Resolution | Why |
|----------|-----------|-----|
| Q1 — redirect target / glob coverage | Dual `.process/` anchor: `docs/ai/specs/.process/` (scaffold exhaust) + `specs/<NNN>/.process/` (per-feature), one `**/.process/**` rule | The two scaffold-authored files land in `docs/ai/specs/`, a different tree from `specs/<NNN>/`; the roadmap's literal `specs/*/.process/**` glob would never match them. |
| Q2 — reach into consuming projects | Static repo-root `.gitattributes` **and** an idempotent consumer-side ensure-step | linguist reads each repo's own `.gitattributes`; a plugin-only file collapses only the plugin's PRs. |
| Q3 — is the UAT runbook EXHAUST? | EXHAUST — move to `.process/`, repoint `generate-pr-body.sh` | It is speckit-pro-authored (`generate-uat-skeleton.sh`) and its content is mirrored into the PR body, so the standalone file can collapse without losing review visibility. |
| Q4/Q5 — extension-authored exhaust | Out of scope; the installed `archive` extension owns post-merge cleanup | Those files are written by external SpecKit extensions, not speckit-pro prose/scripts; a `git mv` sweep would duplicate `archive` and risk moving a file an extension still expects. |

**Grounding-confirmed implementation anchors** (re-verified in this worktree during
planning):

- Gate `is_excluded_generated()` — `speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh:48–57`
  (dead-code arm at L54). It is called only by `reviewable_loc_from_numstat` (L67–79,
  diff-mode); `is_production_file` (L59–66) is a separate filter, so the new arm moves
  only diff-mode `reviewable_loc`, never `production_files`/`total_files`.
- PR-body UAT read path + link — `generate-pr-body.sh:179,188`.
- Consumer ensure-step model — `ensure-reviewability-preset.sh:13` (`PROJECT_ROOT="${1:-$PWD}"`).
- UAT generator output + git add — `post-implementation.md:564,590`.
- L1 lint model — `tests/layer1-structural/validate-pr-checks-sentinel.sh`;
  register the new lint in `tests/run-all.sh` (L1 array, ~L137–143).

No further research tasks were generated because no dependency, integration, or
technology choice remained unresolved.
