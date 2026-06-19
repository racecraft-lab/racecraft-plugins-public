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

### User Story 2 Evidence

Recorded for T019 against the checklist above:

- Keyboard-oriented review: `SafeInstallAids.astro` keeps native radio inputs,
  native copy buttons, explicit arrow, Home, and End key handling, and visible
  `:focus-visible` treatment. `LifecycleFlow.astro` now exposes
  keyboard-reachable links to the related static tables before the ordered
  lifecycle content.
- Screen-reader-oriented review: the install aid keeps a `fieldset`/`legend`,
  label text from checked-in selector records, `aria-describedby` links to
  visible status text, and polite selector/copy status updates. The lifecycle
  flow now connects its heading to summary and fallback text and exposes phase
  facts in description lists.
- Responsive review: install-aid cards keep equal-height tracks and contained
  table scrolling. The lifecycle flow wraps long artifact names, keeps link
  labels visible, and switches to a one-column layout below 48rem.
- Static fallback review: `choose-your-path.mdx` now includes an install aid
  static fallback checklist with platform/scope, source/payload, copyable
  guidance, and manual-only safety boundaries. The install aid table and
  lifecycle ordered list remain available without JavaScript.
- Known gap: this is reviewer-visible manual/source evidence for US2, not the
  later compact browser smoke artifact. Browser smoke remains owned by US4.

### PR Packet Evidence

Recorded for T040:

- Review order: inspect `docs-site/tests/docs-smoke.spec.mjs` first for the
  bounded browser contract, then `.github/workflows/pr-checks.yml` for the
  smoke artifact upload, then this quickstart and `tasks.md` for evidence and
  traceability.
- Scope budget: final DOC-010 Phase 7 changes stay inside the declared
  docs/process, UI, and harness/adapter surfaces. No plugin runtime payloads,
  generated reference pages, package lockfiles, workflow state, or autopilot
  state were edited.
- Traceability: T028-T031 cover route, viewport, search, deep-link,
  SafeInstallAids, and LifecycleFlow smoke assertions for FR-002, FR-004,
  FR-005, FR-006, FR-010, and FR-011. T032 covers the 7-day CI artifact
  contract for FR-013. T033-T039 record the validation bundle. T040 records
  reviewer-facing PR evidence.
- Validation output: `pnpm --dir docs-site validate:smoke` passed with
  20 Playwright tests across `desktop-chromium` and `mobile-chromium`.
  `pnpm --dir docs-site reference:check` passed with reference pages current.
  `pnpm --dir docs-site validate:quality` passed.
  `pnpm --dir docs-site validate:safe-aids` passed.
  `pnpm --dir docs-site validate` passed with
  Astro check reporting 0 errors, 0 warnings, and 0 hints, all internal links
  valid, and the same 20 smoke tests passing. `git diff --check` passed.
  `bash tests/speckit-pro/run-all.sh --layer 1` passed 1024/1024 checks.
- Manual accessibility evidence: US2 source/manual evidence remains above.
  US4 browser smoke adds representative route heading/landmark checks, desktop
  and mobile viewport checks, search result discovery, sampled deep links,
  visible install-aid controls and status text, static fallback visibility,
  and lifecycle fallback/phase evidence. This remains representative smoke
  evidence, not a full accessibility certification.
- Compact smoke artifact summary: CI sets `DOCS_SITE_SMOKE_ARTIFACT_DIR` to
  the runner temp `docs-site-smoke-evidence` directory, then uploads
  `docs-site-smoke-evidence` with `retention-days: 7` and
  `if-no-files-found: ignore`. Passing local smoke runs produced no committed
  artifact files, screenshots, videos, or traces.
- Known gaps: no broad visual snapshot suite, no full accessibility audit, no
  production telemetry check, and no live plugin install validation were added.
  The first unapproved local smoke run was blocked by sandbox localhost
  permissions on `127.0.0.1:4321`; approved local-server reruns passed.
- Automation-safety notes: smoke navigation stays on the configured local
  docs-site baseURL and the six DOC-010 logical routes. Tests do not execute
  browser-side local commands, inspect local user files or user JSON, install
  plugins, submit analytics, follow external marketplace flows, or perform
  destructive behavior. Copy buttons are asserted as visible guidance only.
- Rollback/fallback notes: if smoke artifacts become noisy, rollback is limited
  to the Playwright smoke spec and the upload-artifact step. Static docs,
  SafeInstallAids fallback content, LifecycleFlow fallback content, focused
  validators, and generated-reference validation continue to provide the
  non-browser fallback path.

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
