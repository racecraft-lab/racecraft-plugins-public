<!-- speckit-pro-review-packet-source: specs/doc-006-safe-interactive-selector-and-validation-aids/.process/pr-packet.json -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Add a static-first `choose-your-path` selector, repository metadata checker, payload diagram, and first-run checklist for safe plugin installation guidance.
<!-- speckit-pro-editable:summary:end -->

Source: feature specification defines safe selector, checker, diagram, and checklist behavior.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Converted the Choose Your Path docs page to MDX and rendered safe install aids through a Starlight-compatible Astro component.
- Added source-derived repository metadata reads for Claude and Codex manifests, marketplace versions, generated payloads, and expected success signals.
- Added focused validation for selector data, checker rows, fallback content, command safety, and built HTML output.
<!-- speckit-pro-editable:what_changed:end -->

Source: implementation and validation artifacts define the reviewed behavior.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
Users can choose the right install path and inspect repository consistency without the browser running commands, reading local config, installing plugins, or mutating state.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Review `docs-site/src/content/docs/choose-your-path.mdx` for the final page structure and static fallback content.
2. Review `docs-site/src/components/SafeInstallAids.astro` for selector controls, checker output, payload diagram, and checklist rendering.
3. Review `docs-site/src/data/safe-install-aids.ts` for bounded read-only metadata sourcing from checked-in repository files.
4. Review `docs-site/scripts/validate-doc006-safe-aids.mjs` for focused validation coverage.

## How To UAT

Run the focused docs validator, docs-site validation, link validation, and full SpecKit suite. Then inspect the built `choose-your-path` page for selector options, checker rows, fallback tables, and command-safety copy.

## UAT Runbook

Use `specs/doc-006-safe-interactive-selector-and-validation-aids/.process/uat-runbook.md` for manual per-story review. The runbook covers install-path selection, repository metadata consistency, safe first-run checkpoints, no-script fallback behavior, and mismatch handoffs.

## Verification

- `node docs-site/scripts/validate-doc006-safe-aids.mjs`
- `pnpm --dir docs-site validate`
- `pnpm --dir docs-site validate:links`
- `pnpm --dir docs-site validate && pnpm --dir docs-site validate:links`
- `bash speckit-pro/skills/speckit-autopilot/scripts/validate-gate.sh G7 specs/doc-006-safe-interactive-selector-and-validation-aids`
- `bash tests/speckit-pro/layer4-scripts/test-privacy-scan.sh`
- `bash tests/speckit-pro/run-all.sh`

Source: generated PR packet.

## Scope

- Source feature: `specs/doc-006-safe-interactive-selector-and-validation-aids/spec.md`.
- Main docs surface: `docs-site/src/content/docs/choose-your-path.mdx`.
- Implementation scope: docs-site component, docs-site metadata helper, focused validator, and DOC-006 process evidence.
- Reviewability: final size-only gate exceeded the single-PR LOC threshold, and the marker evidence is retained for review. Because all marker checkpoints collapsed to one completed implementation state, live split emission would create unsafe duplicate or empty slice branches; this PR records the supported hazard-collapsed aggregate route.
- Traceability: source feature, implementation tasks, verification report, UAT runbook, marker plan, and changed-file scope are recorded in the packet metadata.
- Non-goals: live doctor command, browser-side shell execution, user-local JSON checker, config mutation, full troubleshooting matrix, search/deep-link hardening, and docs CI hardening.

## Known Gaps

Full troubleshooting, trust, update, rollback, and cache-diagnosis coverage remains assigned to the later troubleshooting slice. Search, deep links, and broader accessibility hardening remain assigned to the later docs-hardening slice.
