# PRD: Racecraft Identity System

**Status**: Active — not yet implemented
**Source**: Approved logo, plugin-metadata, and launch-version research from 2026-07-16
**Created**: 2026-07-16
**Last updated**: 2026-07-16
**Target window**: Soft launch in the first week of August 2026

---

## 1. Problem

> How can Racecraft present one credible identity across its public repository,
> documentation, and SpecKit Pro product without breaking the plugin's existing
> release history?

Racecraft Plugins already ships a mature dual-runtime product, but its visible
identity is fragmented. The repository README has no logo, the documentation
uses legacy Racecraft assets, SpecKit Pro has no product mark, colors and names
drift across surfaces, and the Claude and Codex manifests do not fully use the
metadata their platforms support. The first public launch needs a coherent
system that is distinguishable at small sizes, safe to package, accessible,
and maintainable as source rather than a collection of one-off exports.

## 2. Goals & Non-goals

### 2.1 Goals

- Establish Racecraft as the parent identity, Racecraft Plugins as the public
  repository/docs identity, and SpecKit Pro by Racecraft as the product identity.
- Design first for hands-on founders, technical leads, and staff engineers who
  are standardizing serious agentic software delivery.
- Express one core promise: turn product intent into reviewable, reliable agent
  execution across Claude Code and Codex.
- Produce human-approved, original SVG masters and deterministic platform exports.
- Make the identity work in light, dark, monochrome, favicon, social-card,
  repository, documentation, Codex plugin, and Codex skill contexts.
- Use only supported Claude Code and Codex metadata fields and package every
  referenced asset inside the correct generated payload.
- Add repeatable SVG safety, optimization, accessibility, render, and packaging checks.
- Preserve the existing SpecKit Pro release lineage and ship compatible launch
  work through the normal ascending SemVer and Release Please flow.

### 2.2 Non-goals (out of scope)

- Resetting the existing `speckit-pro` identity to `1.0.0`, deleting or moving
  published tags, or rewriting historical changelog entries.
- Renaming the repository slug, marketplace IDs, or plugin ID.
- Redesigning SpecKit Pro workflow behavior or the SpecKit SDD methodology.
- Adding unsupported image fields to Claude Code manifests.
- Creating a unique illustration system for every individual skill in this roadmap.
- Completing final legal trademark clearance; this roadmap prepares candidates
  and evidence for human clearance.
- Attaching `plugins.racecraft.co` or removing the staging `noindex` guard;
  those remain the `DOC-012` launch-gate responsibility.

## 3. Acceptance Criteria

### 3.1 Brand brief and concept exploration *(→ BRAND-001)*

- **AC-1.1**: A one-page brief defines the audience, product promise, brand
  architecture, personality, prohibited motifs, palette strategy, typography,
  required contexts, originality standard, and scoring rubric.
- **AC-1.2**: Four structurally distinct identity families are delivered as
  real SVG geometry with rendered light, dark, monochrome, 16 px, 24 px,
  32 px, README, docs-header, and plugin-list comparisons.
- **AC-1.3**: Each concept has a private author rationale, provenance record,
  declared weakness, and identical comparison contexts so later review is fair.

### 3.2 Independent critique and human selection *(→ BRAND-002)*

- **AC-2.1**: An independent critique scores every family for silhouette,
  distinctiveness, balance, small-size clarity, theme behavior, originality,
  and brand fit without using the author's rationale.
- **AC-2.2**: A human selects one family and the selection record preserves
  the rationale, rejected alternatives, and any trademark-review concerns.
- **AC-2.3**: No concept advances to canonical production until the blind
  scoring packet, selection decision, and unresolved trademark flags are recorded.

### 3.3 Canonical SVG master production *(→ BRAND-003)*

- **AC-3.1**: The selected family is refined into a coherent Racecraft parent,
  Racecraft Plugins repository/docs, and SpecKit Pro by Racecraft product system.
- **AC-3.2**: Canonical Racecraft symbol/wordmark, Racecraft Plugins lockup,
  and SpecKit Pro symbol/lockup masters exist as path-based SVGs with stable
  `viewBox` values and documented provenance.
- **AC-3.3**: Simplified small-size, light, dark, and monochrome masters exist
  with recorded minimum sizes and font-license or outlined-letterform notes.

### 3.4 Deterministic SVG pipeline *(→ BRAND-004)*

- **AC-4.1**: A repository-owned Python 3.11+ command validates SVG XML against
  an explicit allowlist and rejects scripts, events, DTDs, `foreignObject`,
  animation, external references, embedded raster data, and remote fonts.
- **AC-4.2**: The export flow optimizes SVGs without dropping `viewBox` or
  accessibility IDs and produces required deterministic raster derivatives.
- **AC-4.3**: Source and optimized renders are compared and fail verification
  when their visual output differs beyond the approved threshold.
- **AC-4.4**: Asset manifests record source, output, dimensions, color variant,
  minimum display size, and provenance for every generated export.

### 3.5 Repository and documentation presentation *(→ BRAND-005)*

- **AC-5.1**: The README uses an accessible light/dark responsive lockup and
  immediately explains the relationship between Racecraft Plugins and SpecKit Pro.
- **AC-5.2**: Starlight uses verified light/dark header assets, an accessible
  favicon set, and intentional product identity on SpecKit Pro-specific surfaces.
- **AC-5.3**: Open Graph cards and the 1280×640 GitHub social-preview image use
  the approved system and remain readable at their rendered sizes.
- **AC-5.4**: Brand tokens, site names, schema/logo references, and the web
  manifest no longer drift unintentionally between legacy crimson, blue,
  orange, and indigo treatments.
- **AC-5.5**: Docs validation and real-page light/dark screenshot checks pass.

### 3.6 Plugin presentation and packaging *(→ BRAND-006)*

- **AC-6.1**: The Codex plugin uses supported `brandColor`, `composerIcon`,
  `logo`, `logoDark`, and screenshot metadata with resolvable packaged assets.
- **AC-6.2**: Applicable Codex `agents/openai.yaml` sidecars use supported
  `icon_small`, `icon_large`, and `brand_color` metadata with paths that resolve
  from the installed payload.
- **AC-6.3**: Claude Code plugin and marketplace metadata use supported
  `displayName`, description, homepage, repository, keywords, category, and
  tags without unsupported logo/icon fields or strict-validation warnings.
- **AC-6.4**: The payload builder includes the canonical asset locations and
  source, Claude, Codex, dist, installed-cache, and generated-reference parity checks pass.
- **AC-6.5**: Codex starter prompts conform to the current three-prompt limit.

### 3.7 Launch readiness and versioned rollout *(→ BRAND-007)*

- **AC-7.1**: The repository description, homepage, README, social preview,
  documentation metadata, and marketplace presentation consistently describe
  both Claude Code and Codex support.
- **AC-7.2**: Fresh Claude Code and Codex installations load the expected
  branded payload without missing-asset or manifest errors.
- **AC-7.3**: Upgrades from the latest public `2.19.x` release succeed without
  uninstalling, clearing caches, or changing plugin identity.
- **AC-7.4**: Release Please, the plugin manifests, runner manifest,
  marketplaces, generated artifacts, reference docs, and changelog agree on
  an ascending launch version.
- **AC-7.5**: Compatible work releases as `2.20.0`; `3.0.0` is used only if
  the completed implementation introduces a documented breaking public contract.
- **AC-7.6**: The launch is marketed as SpecKit Pro GA, Public Launch, or
  Launch Edition rather than as a technical `1.0.0` reset.

## 4. Migration Path

- **Phase 1 (BRAND-001) — Concept exploration**: approve the brief and produce
  four structurally distinct families in identical comparison contexts.
- **Phase 2 (BRAND-002) — Critique and selection**: blind-score the families,
  record trademark flags, and hold the human selection gate.
- **Phase 3 (BRAND-003) — Canonical masters**: refine the selected family into
  parent, repository/docs, product, and small-size source masters.
- **Phase 4 (BRAND-004) — Deterministic SVG pipeline**: make the selected
  masters safe and reproducibly exportable before integration.
- **Phase 5 (BRAND-005) — Repository and docs presentation**: apply the
  validated system to GitHub and Starlight.
- **Phase 6 (BRAND-006) — Plugin presentation and packaging**: apply supported
  Claude/Codex metadata and prove installed-payload asset resolution.
- **Phase 7 (BRAND-007) — Launch readiness**: canary fresh installs and
  upgrades, reconcile public metadata, and release through the existing pipeline.

## 5. Constraints

- The repository constitution requires Python 3.11+ standard-library tooling,
  ascending SemVer, Release Please ownership, generated-payload parity, and the
  Python-authoritative test suite.
- AI-produced SVG is untrusted source until allowlist, optimization, render,
  accessibility, and human-review gates pass.
- Release exports cannot depend on installed fonts, external URLs, network
  access, embedded raster data, or host-specific rendering behavior.
- Codex UI assets must be inside the plugin archive. Codex skill icon paths are
  relative to their skill directories. Claude Code exposes no supported logo
  or icon manifest field.
- Generated payloads and reference pages are rebuilt from source; they are not
  edited directly.
- `DOC-012` remains the final public-domain/indexing cutover.

## 6. Open Questions

- **OQ-1 (BRAND-002):** Which candidates, if any, require a human trademark
  knockout search before they can enter final selection?
- **OQ-2 (BRAND-004):** Which renderer provides deterministic cross-platform
  raster exports without adding an unnecessary production dependency?
- **OQ-3 (BRAND-006):** Can all Codex skills safely reference shared
  plugin-root icons, or must the build place copies under each skill's
  `assets/` directory? Resolve against the current validator and installed payload.
- **OQ-4 (BRAND-007):** Does the final implementation change any public
  installation or compatibility contract enough to require `3.0.0`?

## 7. SPEC Catalog Crosswalk

| Feature (§3) | Acceptance Criteria | SPEC | Depends on | Priority |
|---|---|---|---|---|
| Brand brief and concept exploration | AC-1.* | BRAND-001 | — | P1 |
| Independent critique and human selection | AC-2.* | BRAND-002 | BRAND-001 | P1 |
| Canonical SVG master production | AC-3.* | BRAND-003 | BRAND-002 | P1 |
| Deterministic SVG pipeline | AC-4.* | BRAND-004 | BRAND-003 | P1 |
| Repository and documentation presentation | AC-5.* | BRAND-005 | BRAND-003, BRAND-004 | P1 |
| Plugin presentation and packaging | AC-6.* | BRAND-006 | BRAND-003, BRAND-004 | P1 |
| Launch readiness and versioned rollout | AC-7.* | BRAND-007 | BRAND-005, BRAND-006 | P1 |

## 8. Success Criteria

1. All AC-1.1 through AC-7.6 pass with reviewable evidence.
2. Racecraft Plugins and SpecKit Pro are visibly related, distinguishable, and
   recognizable in their smallest supported contexts.
3. Every referenced asset resolves in source, docs, generated payload, fresh
   install, and upgrade scenarios.
4. No existing release or tag is removed, moved, or redefined.
5. Each implementation spec lands within its reviewability budget or records a
   narrowly justified typed exception for deterministic generated artifacts.

## 9. References

- **Technical roadmap:** `docs/ai/specs/racecraft-identity-system-technical-roadmap.md`
- **Constitution:** `.specify/memory/constitution.md`
- **Project standards:** `AGENTS.md`
- **Existing docs roadmap:** `docs/ai/specs/interactive-documentation-technical-roadmap.md`
- **Claude plugin reference:** https://code.claude.com/docs/en/plugins-reference
- **Codex plugin specification:** https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/plugin-creator/references/plugin-json-spec.md
- **Codex skill metadata:** https://github.com/openai/skills/blob/main/skills/.system/skill-creator/references/openai_yaml.md
- **Semantic Versioning:** https://semver.org/
