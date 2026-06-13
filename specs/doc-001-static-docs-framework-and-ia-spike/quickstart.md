# Quickstart: Validate DOC-001 planning artifacts

This guide validates the DOC-001 research spike. It does not build or run a docs site.

## Prerequisites

- Worktree: `.worktrees/001-static-docs-framework-and-ia-spike`
- Branch: `doc-001-static-docs-framework-and-ia-spike`
- Feature directory: `specs/doc-001-static-docs-framework-and-ia-spike`

## Scenario 1: Validate the research recommendation

1. Open `docs/ai/research/interactive-documentation-framework-spike.md`.
2. Confirm exactly one default stack is recommended.
3. Confirm Docusaurus/MDX, VitePress, Astro/Starlight, and repo-native fallback are all evaluated.
4. Confirm every non-selected candidate has a rejection or deferral reason.
5. Confirm current framework/platform claims include the initial retrieval date `2026-06-12` and the Astro/Starlight decision update date `2026-06-13` where applicable.
6. Confirm the report defines what DOC-002 should do if Astro/Starlight hits a true GitHub Pages hard blocker.

**Expected result**: The report recommends Astro/Starlight for DOC-002 and records the community-plugin tradeoff for versioning and internal link validation.

## Scenario 2: Validate the IA skeleton

1. In the research report, find the IA skeleton table.
2. Confirm it includes the 11 required route labels: Start, Install: Claude Code, Install: Codex, First Run, Choose Your Path, Reference, Troubleshooting, Security & Trust, Contribute & Release, Spec Kit Lifecycle, and Glossary.
3. Confirm each route includes path, label, primary Diataxis mode, optional secondary modes, audience, purpose, source evidence, success criterion, shell owner DOC, and full content owner DOC.
4. Confirm `shell_owner_doc` is DOC-002 for every route.

**Expected result**: DOC-002 can create the route shell without reopening IA selection.

## Scenario 3: Validate research-only scope

Run:

```bash
git diff --name-only origin/main...HEAD
```

Confirm the PR diff is limited to the interactive-documentation source PRD/roadmap/traceability files, `docs/ai/research/interactive-documentation-framework-spike.md`, DOC-001 process notes under `docs/ai/specs/.process/`, and DOC-001 SpecKit artifacts under `specs/doc-001-static-docs-framework-and-ia-spike/`.

**Expected result**: No package files, lockfiles, site config, CI workflows, README migrations, marketplace files, generated payloads, prototype components, or plugin behavior files changed.

## Scenario 4: Validate DOC-002 handoff

1. In the research report, find "DOC-002 Consumption".
2. Confirm it tells DOC-002 to create the Astro/Starlight shell and not to re-run stack selection unless a new blocker appears.
3. Confirm package manager and command roles are listed as report-only recommendations.
4. Confirm setup, install, preview, build, minimum validation/test, and deployment roles are separated clearly enough for DOC-002 to define actual package scripts.

**Expected result**: DOC-002 has a concrete stack, route shell, command-role baseline, and fallback rule if a true selected-stack blocker appears.

## Optional Repository Checks

For structural confidence after planning-only changes:

```bash
bash tests/speckit-pro/run-all.sh --layer 1
```

For default deterministic verification:

```bash
bash tests/speckit-pro/run-all.sh
```

These checks are optional for DOC-001 because no plugin structure or runtime behavior changes are introduced.
