# Quickstart: DOC-010 Validation

## Prerequisites

- Node and pnpm available for the docs-site package.
- Dependencies installed for `docs-site/`.
- Work from the repository root.

## Local Validation Path

Run the full DOC-010 docs validation path:

```bash
pnpm --dir docs-site validate
```

Expected coverage:

- Generated reference drift check via `reference:check`.
- Astro type/content check via `check`.
- Astro build and Starlight link validation via `build`.
- Focused safe-aids validation.
- Focused docs quality validation for support anchors, source-update guidance, and deterministic link conventions.
- Minimal Playwright smoke via `validate:smoke`.

## Focused Iteration Commands

```bash
pnpm --dir docs-site reference:check
pnpm --dir docs-site check
pnpm --dir docs-site build
pnpm --dir docs-site validate:quality
pnpm --dir docs-site validate:safe-aids
pnpm --dir docs-site validate:smoke
```

Expected behavior:

- `validate:smoke` builds or previews the local docs site deterministically and shuts down its preview server.
- Playwright uses its configured `baseURL` for `/racecraft-plugins-public`.
- Screenshots/reports are local or CI artifacts, not committed files.

## Browser Smoke Review

Confirm Playwright covers both desktop and mobile for:

- `/`
- `/choose-your-path/`
- `/spec-kit-lifecycle/`
- `/glossary/`
- `/reference/skills/`
- `/contribute-and-release/`

Confirm assertions include:

- One search smoke starting from `/`.
- Representative deep-link samples.
- Focused interactive checks for `SafeInstallAids` on `/choose-your-path/`.
- Focused lifecycle/fallback checks on `/spec-kit-lifecycle/`.

## Manual Evidence

Record reviewer-visible evidence in the PR packet:

- Keyboard-only pass for primary interactive aid controls.
- Screen-reader-oriented label/state inspection.
- Desktop and mobile responsive review notes.
- Static fallback review for the install aid and lifecycle flow.
- Known gaps or deferred work, if any.

## CI Expectations

The `validate-docs` gate should:

- Run when docs-site content/config/scripts, generated-reference source inputs, or docs-validation contracts change.
- Avoid workflow-level `paths` filters.
- Preserve existing plugin matrix detection and `validate-plugins` semantics.
- Upload one artifact named `docs-site-smoke-evidence` with 7-day retention when smoke evidence exists.
- Leave plugin matrix jobs unforced for docs-site-only changes unless the PR also touches plugin or generated-reference source inputs.

## Forbidden In Automated Validation

- Live plugin install commands.
- Networked marketplace checks beyond dependency installation handled by the CI environment.
- Browser-side local command execution.
- Local user file or user JSON inspection.
- Analytics.
- Destructive cleanup commands.
