# Data Model: DOC-010

## Documentation Page

**Description**: Existing Astro/Starlight content page that provides install, recovery, troubleshooting, reference, glossary, lifecycle, or release workflow guidance.

**Fields**:

- `route`: Logical route without the deployed base path.
- `sourcePath`: Checked-in docs-site Markdown, MDX, or Astro source path.
- `supportTopics`: High-value topics discoverable from navigation, search, or shared links.
- `stableAnchors`: Anchor IDs exposed for support and reviewer links.
- `sourceUpdateGuidance`: Maintenance note for external platform claims, when applicable.

**Validation rules**:

- Route must remain one of the DOC-010 logical routes unless the spec is revised.
- Support-heavy headings must expose stable anchors or document an intentional exception.
- External platform claims touched by DOC-010 must include source-update guidance or be removed.

## Deep Link Anchor

**Description**: Shareable target for headings, glossary terms, troubleshooting entries, generated reference sections, or release workflow details.

**Fields**:

- `id`: Anchor ID generated or declared by Starlight/Astro content.
- `ownerPage`: Documentation Page that owns the anchor.
- `supportPurpose`: Install, recovery, troubleshooting, reference, glossary, lifecycle, or release workflow.
- `validationOwner`: Deterministic validator responsible for detecting stale or broken links.

**Validation rules**:

- Anchor must resolve during deterministic docs validation.
- Playwright samples representative anchors only; full coverage belongs to deterministic validation.
- Renames require an intentional source update rather than silent drift.

## Interactive Aid

**Description**: Existing docs component that helps users understand installation or lifecycle guidance.

**Fields**:

- `componentPath`: Astro component path.
- `route`: Page where the component appears.
- `controls`: Interactive controls exposed to keyboard and assistive technology users.
- `fallbackContent`: Static content that preserves the essential guidance.
- `manualEvidence`: Reviewer-visible accessibility and responsive review notes.

**Validation rules**:

- Controls must have meaningful labels and visible focus.
- Primary actions must be reachable by keyboard.
- Dynamic behavior must not replace the static guidance.
- Copy behavior must remain copyable guidance only and must not inspect local files.

## Static Fallback

**Description**: Non-dynamic rendering path that communicates the same essential guidance when interactivity is unavailable.

**Fields**:

- `ownerAid`: Interactive Aid that owns the fallback.
- `contentSummary`: Essential install or lifecycle guidance retained without JavaScript.
- `route`: Page containing the fallback.

**Validation rules**:

- Fallback must be visible in source-rendered content.
- Fallback must avoid pointer-only instructions.
- Fallback must not depend on browser local storage or local user files.

## Validation Path

**Description**: Local and CI command sequence that protects docs quality.

**Fields**:

- `localCommand`: `pnpm --dir docs-site validate`.
- `focusedCommands`: `reference:check`, `check`, `build`, `validate:quality`, `validate:safe-aids`, and `validate:smoke`.
- `ciGate`: `validate-docs`.
- `changedFileSurface`: docs-site, generated-reference source, or docs-validation contract.
- `forbiddenActions`: Networked installs, destructive commands, analytics, browser-side local commands, and local-user-file inspection.

**Validation rules**:

- The combined command must include `validate:smoke`.
- The CI gate must use job-level changed-file detection.
- Plugin-only changes must not change plugin matrix semantics.

## Generated Reference Source Input

**Description**: Checked-in source file or directory read by generated reference or safe-aids validation.

**Fields**:

- `path`: Repository-relative source path.
- `consumer`: Reference generator, safe-aids validator, or docs quality validator.
- `detectionSurface`: CI changed-file category that should trigger docs validation.

**Validation rules**:

- Source paths must stay explicitly allowlisted rather than broad all-repo globs.
- Generated reference pages must remain deterministic and checkable.

## Browser Smoke Evidence

**Description**: Compact Playwright output for key routes and viewports.

**Fields**:

- `routes`: Six logical DOC-010 routes.
- `viewports`: Desktop and mobile.
- `checks`: Search smoke, sampled deep links, and focused interactive checks.
- `artifactName`: `docs-site-smoke-evidence`.
- `retention`: Short retention in CI.

**Validation rules**:

- Screenshots/reports are artifacts only and are not committed.
- Base path belongs in Playwright configuration.
- Smoke must stay representative, not exhaustive.

## External Platform Claim

**Description**: Documentation assertion about Claude Code, Codex, marketplace behavior, GitHub PR Checks, release tooling, or Starlight search behavior.

**Fields**:

- `claimText`: Human-readable claim in docs content.
- `sourcePath`: Checked-in source or docs page containing the claim.
- `updateGuidance`: How maintainers should refresh the claim when platform behavior changes.

**Validation rules**:

- Claims touched by DOC-010 must include source-update guidance or be removed.
- Automated validation can check presence of guidance, but not certify external platform truth.
