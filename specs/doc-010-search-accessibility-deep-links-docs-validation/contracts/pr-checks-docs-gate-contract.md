# Contract: PR Checks Docs Gate

## Owner

`.github/workflows/pr-checks.yml`

## Stable Gate Name

`validate-docs`

## Trigger Model

- Workflow remains triggered for pull requests and workflow dispatch.
- Do not use workflow-level `paths` filters.
- Use job-level changed-file detection to decide whether docs validation should run or skip successfully.

## Changed-File Surfaces

| Surface | Examples | Expected validation |
|---------|----------|---------------------|
| Rendered docs-site | `docs-site/src/content/docs/**`, `docs-site/src/components/**`, `docs-site/astro.config.mjs` | Full `pnpm --dir docs-site validate`. |
| Generated-reference source | plugin manifests, skills, agents, hooks, scripts, README, tests, dist manifests, source allowlists | Reference drift and docs validation relevant to generated pages. |
| Docs-validation contract | docs-site validation scripts, Playwright config/spec, docs-site package scripts, PR Checks docs-gate logic | Full or focused docs validation sufficient to prove contract behavior. |
| Plugin-only | plugin runtime/test changes outside docs surfaces | Preserve existing plugin matrix semantics; do not force docs validation unless the source is also a generated-reference input. |

## Required CI Behavior

- `validate-docs` exits successfully with a clear skip message when no docs validation surface changed.
- Docs validation installs docs-site dependencies using pnpm and runs non-destructive local validation.
- The job uploads `docs-site-smoke-evidence` with short retention when smoke artifacts exist.
- Existing `detect`, `test`, `validate-pr-title`, and `validate-plugins` semantics remain intact.

## Forbidden CI Behavior

- Workflow-level path filtering.
- Live plugin marketplace install commands.
- Browser-side local command execution.
- Local user file or user JSON inspection.
- Analytics.
