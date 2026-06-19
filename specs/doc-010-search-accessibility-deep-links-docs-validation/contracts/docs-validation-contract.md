# Contract: Docs Validation Path

## Owner

`docs-site/package.json`

## Public Commands

| Command | Required behavior |
|---------|-------------------|
| `pnpm --dir docs-site validate` | Runs the complete DOC-010 validation set, including `validate:smoke`. |
| `pnpm --dir docs-site reference:check` | Fails when generated reference pages drift from checked-in source inputs. |
| `pnpm --dir docs-site check` | Runs Astro content/type checks. |
| `pnpm --dir docs-site build` | Builds the Starlight site and runs configured link validation. |
| `pnpm --dir docs-site validate:safe-aids` | Runs focused safe-aids validation. |
| `pnpm --dir docs-site validate:quality` | Runs focused support-heading, deep-link, glossary, source-update, and docs-quality validation. |
| `pnpm --dir docs-site validate:smoke` | Runs minimal Playwright browser smoke. |

## Inputs

- `docs-site/src/content/docs/**`
- `docs-site/src/components/SafeInstallAids.astro`
- `docs-site/src/components/LifecycleFlow.astro`
- `docs-site/scripts/generate-reference-pages.mjs`
- `docs-site/scripts/validate-doc006-safe-aids.mjs`
- `docs-site/scripts/validate-docs-quality.mjs`
- Generated reference source inputs allowlisted by the reference generator and safe-aids validator.

## Outputs

- Zero exit code when all deterministic checks pass.
- Non-zero exit code with actionable file/path messages for stale generated pages, missing anchors, unsafe aid regressions, broken links, or smoke failures.
- No committed browser artifacts.

## Invariants

- Deterministic validation owns complete internal link and anchor coverage.
- Playwright samples representative deep links only.
- Validation must not run live plugin install commands.
- Validation must not inspect local user files or accept local user JSON.
- Validation must not add analytics or destructive cleanup.
