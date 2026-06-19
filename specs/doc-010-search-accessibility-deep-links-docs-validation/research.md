# Phase 0 Research: DOC-010

## Decision: Keep Starlight Search And Existing Routes

**Rationale**: The docs site already uses Astro/Starlight with `starlight-links-validator`, and the resolved scope keeps six logical routes: `/`, `/choose-your-path/`, `/spec-kit-lifecycle/`, `/glossary/`, `/reference/skills/`, and `/contribute-and-release/`. Findability is improved through stable headings, glossary terms, support-ready cross-links, and deterministic anchor validation.

**Alternatives considered**: Adding a new search plugin or a new docs-quality route was rejected because it increases dependency and content scope without a current blocker.

## Decision: Extend Existing Validators With One Focused Docs Quality Validator

**Rationale**: `docs-site/scripts/generate-reference-pages.mjs` already owns generated reference determinism, and `docs-site/scripts/validate-doc006-safe-aids.mjs` already protects safe-aid source-backed behavior. DOC-010 should add or pair one focused `validate-docs-quality.mjs` script for headings, anchors, source-update guidance, and high-value support link conventions rather than creating a large new suite.

**Alternatives considered**: A broad validator framework was rejected as oversized for a final docs hardening slice. Prose-only process guidance was rejected because it would not catch anchor or support-link drift before review.

## Decision: Add Minimal Playwright Smoke Coverage

**Rationale**: Browser evidence is useful for reviewer confidence, but DOC-010 must stay smoke-level. Playwright should cover the six logical routes on desktop and mobile, rely on config `baseURL` for `/racecraft-plugins-public`, sample representative deep links, run one search smoke from `/`, and focus interactive checks on `/choose-your-path/` and `/spec-kit-lifecycle/`.

**Alternatives considered**: A full visual snapshot suite and an accessibility-tooling stack were rejected because they exceed the slice budget and risk noisy review artifacts.

## Decision: Include `validate:smoke` In The Single Docs Validation Path

**Rationale**: The local `pnpm --dir docs-site validate` command should be the one maintainer/contributor path for generated reference checks, Astro checks, build/link validation, docs quality validation, safe-aids validation, and minimal browser smoke. Focused subcommands remain available for quick local iteration.

**Alternatives considered**: Leaving smoke manual-only was rejected because PR evidence would be weaker. Running smoke outside `validate` was rejected because it creates two validation paths.

## Decision: Add A Job-Level `validate-docs` PR Checks Gate

**Rationale**: CI must distinguish docs-site changes, generated-reference source changes, and docs-validation contract changes while preserving plugin matrix semantics. Job-level changed-file detection avoids workflow-level `paths` filters that can leave required checks pending or skip unrelated PR metadata validation.

**Alternatives considered**: Workflow-level path filters were rejected by clarified scope. Running docs validation on every PR was rejected as unnecessary CI cost.

## Decision: Treat Accessibility Automation As Guardrails

**Rationale**: Static source validators and smoke tests can catch missing labels, unreachable controls, broken focus targets, and fallback regressions, but they cannot certify accessibility. Manual keyboard, screen-reader-oriented, and responsive review evidence belongs in existing PR packet sections.

**Alternatives considered**: Automation-only accessibility claims were rejected as overclaiming. Manual-only review was rejected because it would not protect future regressions.

## Decision: Keep CI Non-Networked And Non-Destructive

**Rationale**: Validation must avoid live plugin installs, analytics, browser-side local command execution, and local-user-file inspection. Playwright may build and preview the checked-in docs site, but it must not invoke live marketplace/plugin install flows.

**Alternatives considered**: Live install validation was rejected as outside DOC-010 and risky for CI.
