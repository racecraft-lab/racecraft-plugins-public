# Contract: Browser Smoke

## Owner

`docs-site/tests/docs-smoke.spec.mjs` and `docs-site/playwright.config.mjs`

## Route Set

Playwright MUST cover these logical routes:

- `/`
- `/choose-your-path/`
- `/spec-kit-lifecycle/`
- `/glossary/`
- `/reference/skills/`
- `/contribute-and-release/`

The Playwright configuration owns the deployed base path, including `/racecraft-plugins-public`.

## Viewports

- Desktop viewport.
- Mobile viewport.

## Required Assertions

- Each route loads with a visible, route-appropriate heading or landmark.
- One search smoke starts from `/` and verifies at least one known support-oriented result link.
- Representative deep links resolve to intended page sections.
- `/choose-your-path/` exposes usable install-aid controls and copyable guidance without local file inspection.
- `/spec-kit-lifecycle/` exposes lifecycle flow content or static fallback content on both viewports.

## Artifact Contract

- CI uploads one artifact named `docs-site-smoke-evidence` with 7-day retention.
- Artifact may contain Playwright report, screenshots, traces, or compact output.
- Artifact files are not committed.

## Non-Goals

- Full visual regression snapshots.
- Complete accessibility certification.
- Live plugin install validation.
- Analytics or production telemetry.
