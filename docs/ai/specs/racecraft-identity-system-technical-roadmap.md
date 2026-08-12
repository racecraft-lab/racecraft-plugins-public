# Racecraft Identity System Implementation Roadmap

This roadmap defines the cross-surface identity, asset pipeline, integration,
plugin packaging, and version-safe rollout required for the Racecraft Plugins
and SpecKit Pro public launch.

**Source PRD:** [../../prd-racecraft-identity-system.md](../../prd-racecraft-identity-system.md)
**Active scaffold branch (BRAND-001):** `brand-001-racecraft-identity-system`
**Roadmap-MOC:** [racecraft-identity-system-roadmap-MOC.md](racecraft-identity-system-roadmap-MOC.md)

Each later BRAND spec receives its own dedicated branch and worktree during
scaffold; the active BRAND-001 branch is not reused as a roadmap-wide branch.

---

## Roadmap Overview

The effort is decomposed into seven independently reviewable specifications
across six dependency tiers:

| Tier | Specs | Purpose | Parallelization |
|---|---|---|---|
| 1 | BRAND-001 | Brand brief and four original concept families | Parallel concept production after brief approval |
| 2 | BRAND-002 | Rationale-blind critique and human selection | Sequential human selection gate |
| 3 | BRAND-003 | Selected-family refinement and canonical SVG masters | Sequential after selection |
| 4 | BRAND-004 | SVG safety, optimization, export, and render-verification pipeline | Sequential after approved masters |
| 5 | BRAND-005, BRAND-006 | Repository/docs integration and plugin packaging | Parallel after BRAND-004 |
| 6 | BRAND-007 | Cross-surface launch readiness and versioned rollout | Requires both integrations |

**Execution order:** BRAND-001 → BRAND-002 → BRAND-003 → BRAND-004 → BRAND-005 / BRAND-006 → BRAND-007 → DOC-012 public cutover

**Dependency constraints:**

- BRAND-002 requires the comparable concept packet from BRAND-001.
- BRAND-003 requires the recorded human selection from BRAND-002.
- BRAND-004 requires the canonical source masters from BRAND-003.
- BRAND-005 and BRAND-006 can proceed in parallel after BRAND-004 establishes
  canonical exports and validation contracts.
- BRAND-007 requires repository/docs and plugin/package integrations to be complete.
- DOC-012 remains a separate, final custom-domain and indexing cutover after
  BRAND-007 and the other pending DOC launch gates are ready.

## Reviewability Contract

Every spec must fit the repository reviewability thresholds before setup and
again before PR creation. Deterministic generated payload mirrors remain part
of the review packet but must not hide the smaller authored change.

- Warn above 400 reviewable production LOC, 6 production files, or 15 total files.
- Block above 800 reviewable production LOC, 8 production files, or 25 total files.
- A block-sized slice may proceed only with an exact typed pragma on its own
  line: `Reviewability-Exception: refactor`, `Reviewability-Exception: infra`,
  or `Reviewability-Exception: upgrade`.
- Prefer another vertical split over an exception. BRAND-006 may evaluate an
  `infra` exception only if deterministic generated mirrors—not authored
  complexity—are the sole cause of a total-file block.

## Dependency Graph

```text
BRAND-001  Brief + concept exploration
    |
    v
BRAND-002  Blind critique + selection
    |
    v
BRAND-003  Canonical SVG masters
    |
    v
BRAND-004  Deterministic SVG pipeline
    |
    +-----------------------+
    |                       |
    v                       v
BRAND-005               BRAND-006
Repo + docs             Plugin + packaging
    |                       |
    +-----------+-----------+
                |
                v
           BRAND-007
        Launch readiness
                |
                v
       DOC-012 public cutover
```

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|---|---|---|---|---|
| BRAND-001 | Brand brief and concept exploration | ⏳ Pending | `.process/BRAND-001-workflow.md` | Scaffolded 2026-07-16 and parked; all seven phases still pending. Unblocked and ready for autopilot from Phase 1 |
| BRAND-002 | Rationale-blind critique and human selection | ⏳ Pending | — | Blocked by BRAND-001 |
| BRAND-003 | Canonical SVG master production | ⏳ Pending | — | Blocked by BRAND-002 |
| BRAND-004 | Deterministic SVG validation and export pipeline | ⏳ Pending | — | Blocked by BRAND-003 |
| BRAND-005 | Repository and documentation presentation | ⏳ Pending | — | Blocked by BRAND-003/004 |
| BRAND-006 | Plugin presentation and payload packaging | ⏳ Pending | — | Blocked by BRAND-003/004 |
| BRAND-007 | Launch readiness and versioned rollout | ⏳ Pending | — | Blocked by BRAND-005/006 |

**Status legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

## Specification Sections

### BRAND-001: Brand brief and concept exploration

**Priority:** P1 | **Depends On:** None | **Enables:** BRAND-002

**Goal:** Define the Racecraft identity system and produce four original,
structurally distinct SVG concept families in identical comparison contexts.

**Reviewability Budget:** Primary surfaces: docs/process, visual/assets |
Projected reviewable LOC: 0 production LOC |
Production files: 0 |
Total files: 23-25 including scaffold and generated workflow artifacts |
Budget result: expected warning below the 25-file block; no exception authorized

**Scope:**

- Author `brand/brief.md` with audience, promise, hierarchy, personality,
  prohibited motifs, palette/typography strategy, originality standard,
  required applications, minimum sizes, and scoring rubric.
- Encode the approved direction: evolutionary continuity, abstract precision,
  shared geometry with Racecraft crimson and SpecKit Pro indigo accents,
  first-touch product endorsement, existing type with custom details, and
  confident precision at small sizes.
- Produce four structurally distinct original SVG identity families; do not
  trace or imitate an existing company or open-source mark.
- Render each family in the same light, dark, monochrome, 16/24/32 px symbol,
  README, docs-header, and plugin-list comparison contexts.
- Preserve a private author rationale, provenance statement, and known weakness
  for every family so BRAND-002 can critique the artwork without seeing rationale.

**Out of Scope:**

- Independent critique or human selection (BRAND-002).
- Refinement and canonical master production (BRAND-003).
- Production export automation and sanitization (BRAND-004).
- README, Starlight, favicon, or social-card replacement (BRAND-005).
- Claude/Codex manifest and payload integration (BRAND-006).
- Final trademark clearance, version changes, or releases.

**Key Decisions:**

- **Brand architecture decision (2026-07-16):** Racecraft is the parent;
  Racecraft Plugins is the repository/docs identity; SpecKit Pro by Racecraft
  is the endorsed product identity. The endorsement is required on first-touch
  surfaces, while compact product marks may stand alone where space is constrained.
- **Continuity decision (2026-07-16):** evolve recognizable Racecraft cues
  rather than starting from zero or preserving the existing mark unchanged.
- **Metaphor decision (2026-07-16):** favor abstract apex, racing-line, gate,
  and specification geometry over literal motorsport or generic code symbols.
- **Color decision (2026-07-16):** join Racecraft crimson and SpecKit Pro
  indigo through shared neutrals and geometry rather than forcing one accent.
- **Typography decision (2026-07-16):** start from the existing self-hosted
  type system and customize only distinctive letterform or lockup details.
- **Tone decision (2026-07-16):** prioritize confident precision, negative
  space, and small-size clarity over decorative speed effects.
- **Audience decision (2026-07-16):** design first for hands-on founders,
  technical leads, and staff engineers standardizing serious agentic delivery.
- **Promise decision (2026-07-16):** Racecraft turns product intent into
  reviewable, reliable agent execution across Claude Code and Codex.
- **Reviewability decision (2026-07-16):** split the original identity scope
  into BRAND-001 concept exploration, BRAND-002 selection, and BRAND-003 masters.
- **Version policy decision (2026-07-16):** preserve the existing public
  lineage; compatible launch work targets `2.20.0`, and `3.0.0` is reserved
  for a documented breaking contract.

**Key Files:**

- `brand/brief.md`
- `brand/README.md`
- `brand/concepts/`
- `brand/review/author-rationales.md`
- `docs/ai/specs/.process/BRAND-001-design-concept.md`

### BRAND-002: Rationale-blind critique and human selection

**Priority:** P1 | **Depends On:** BRAND-001 | **Enables:** BRAND-003

**Goal:** Evaluate all four families independently, preserve comparable
evidence, and record one explicit human selection for canonical refinement.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 0 production LOC |
Production files: 0 |
Total files: 3-8 |
Budget result: expected within setup thresholds

**Scope:**

- Give a critic the shared brief and comparison packet without author rationales.
- Score silhouette, distinctiveness, balance, small-size clarity, light/dark
  behavior, originality risk, parent/product fit, and practical versatility.
- Record the critic's strongest argument for and against each family.
- Hold a human selection gate and preserve the chosen family, rejected
  alternatives, rationale, required refinements, and trademark-review flags.

**Out of Scope:**

- Drawing additional concept families unless the human gate rejects all four.
- Refining the selected family or producing canonical masters (BRAND-003).
- Representing the critique as final legal trademark clearance.

**Key Files:**

- `brand/review/blind-critique.md`
- `brand/review/selection-record.md`
- `brand/review/trademark-flags.md`

### BRAND-003: Canonical SVG master production

**Priority:** P1 | **Depends On:** BRAND-002 | **Enables:** BRAND-004

**Goal:** Refine the selected family into coherent, editable, path-based SVG
masters for Racecraft, Racecraft Plugins, and SpecKit Pro by Racecraft.

**Reviewability Budget:** Primary surface: visual/assets |
Projected reviewable LOC: 0 production LOC |
Production files: 0 |
Total files: 8-14 |
Budget result: expected within setup thresholds

**Scope:**

- Apply the recorded refinements without reopening the selected core concept.
- Produce canonical Racecraft symbol and wordmark, Racecraft Plugins lockup,
  SpecKit Pro symbol and endorsed lockup, and simplified small-size masters.
- Use stable `viewBox` values, path-based geometry, shared construction rules,
  and explicit light, dark, and monochrome master variants.
- Document provenance, font licensing or outlined-letterform treatment,
  minimum sizes, protected space, and remaining trademark-review flags.

**Out of Scope:**

- Automated sanitization, optimization, or raster export (BRAND-004).
- README/docs or plugin integration (BRAND-005 and BRAND-006).
- Final trademark clearance or registration.

**Key Files:**

- `brand/source/racecraft/`
- `brand/source/racecraft-plugins/`
- `brand/source/speckit-pro/`
- `brand/source/provenance.md`

### BRAND-004: Deterministic SVG validation and export pipeline

**Priority:** P1 | **Depends On:** BRAND-003 | **Enables:** BRAND-005, BRAND-006

**Goal:** Turn approved masters into secure, reproducible, platform-ready
exports with deterministic verification.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 300-400 |
Production files: 3-5 |
Total files: 10-18 |
Budget result: expected within budget or warning below block thresholds

**Scope:**

- Add a Python 3.11+ standard-library SVG allowlist validator.
- Reject active content, external dependencies, embedded raster images,
  unsafe references, non-deterministic IDs, and missing `viewBox` values.
- Define and document the approved optimizer configuration and preservation rules.
- Add deterministic render/export orchestration for SVG and required PNG/ICO outputs.
- Compare source and optimized renders and emit a machine-readable asset manifest.
- Add focused unit and fixture coverage and register tests in the suite manifest.

**Out of Scope:**

- Selecting or redrawing the brand family.
- Integrating exports into docs or plugin manifests.
- Accepting arbitrary user-uploaded SVG at runtime.

**Key Files:**

- `scripts/` repository-owned asset tooling
- `tests/speckit-pro/unit/` focused asset-tool tests and fixtures
- `brand/exports/`
- `brand/asset-manifest.json`

### BRAND-005: Repository and documentation presentation

**Priority:** P1 | **Depends On:** BRAND-003, BRAND-004 | **Enables:** BRAND-007

**Goal:** Apply the validated identity across GitHub and Starlight without
regressing accessibility, theme behavior, links, or generated metadata.

**Reviewability Budget:** Primary surface: docs/UI |
Projected reviewable LOC: 50-120 |
Production files: 1-3 |
Total files: 12-22 |
Budget result: expected warning below block thresholds

**Scope:**

- Add the responsive light/dark Racecraft Plugins lockup to the README.
- Replace/rationalize Starlight header assets, hero mark, favicon set, web
  manifest, organization schema logo, and Open Graph imagery.
- Apply the SpecKit Pro product lockup where product-specific identity is useful.
- Normalize intentional parent/product colors and names while preserving AA contrast.
- Generate a 1280×640 GitHub social-preview PNG and document the Settings upload step.
- Add light/dark, desktop/mobile, and minimum-size screenshot verification.

**Out of Scope:**

- Domain/DNS/indexing cutover (DOC-012).
- Content voice and IA rewrites (DOC-019 through DOC-021).
- Plugin payload metadata (BRAND-006).

**Key Files:**

- `README.md`
- `docs-site/astro.config.mjs`
- `docs-site/src/assets/`
- `docs-site/public/`
- `docs-site/src/pages/og/[...slug].ts`
- `docs-site/src/styles/brand.css`

### BRAND-006: Plugin presentation and payload packaging

**Priority:** P1 | **Depends On:** BRAND-003, BRAND-004 | **Enables:** BRAND-007

**Goal:** Use the supported Claude Code and Codex presentation contracts and
prove every referenced asset survives generated-payload installation.

**Reviewability Budget:** Primary surface: harness/adapter + seed/config |
Projected reviewable LOC: 120-250 |
Production files: 3-6 |
Total files: 20-40 including deterministic mirrors |
Budget result: must split again unless generated mirrors alone justify a reviewed `infra` exception

**Scope:**

- Add Codex plugin `composerIcon`, `logo`, `logoDark`, screenshots, and aligned
  `brandColor` fields using only documented manifest properties.
- Add supported icon and brand-color metadata to applicable Codex skills;
  verify whether shared in-root assets or per-skill assets are required.
- Reduce Codex starter prompts to the supported three entries.
- Improve supported Claude plugin/marketplace naming and discovery metadata
  without adding unsupported image fields.
- Extend the payload allowlist/build path for canonical assets.
- Regenerate, inventory, and verify Claude/Codex dist, installed-cache fixtures,
  reference docs, proof hashes, and source/dist parity.

**Out of Scope:**

- Changing skill behavior, commands, hooks, or agent routing.
- Renaming plugin or marketplace identifiers.
- Version edits outside Release Please.

**Key Files:**

- `speckit-pro/.codex-plugin/plugin.json`
- `speckit-pro/.claude-plugin/plugin.json`
- `speckit-pro/codex-skills/*/agents/openai.yaml`
- `speckit-pro/speckit_pro_runner/gates/payloads.py`
- `.agents/plugins/marketplace.json`
- `.claude-plugin/marketplace.json`
- generated `dist/**`, installed-cache, and reference artifacts

### BRAND-007: Launch readiness and versioned rollout

**Priority:** P1 | **Depends On:** BRAND-005, BRAND-006 | **Enables:** DOC-012 public cutover

**Goal:** Prove the coherent identity and plugin payload across public metadata,
fresh installs, upgrades, and the existing release system before the soft launch.

**Reviewability Budget:** Primary surface: docs/process + seed/config |
Projected reviewable LOC: 0-50 |
Production files: 0-2 |
Total files: 6-15 excluding the separately generated Release Please PR |
Budget result: expected within budget

**Scope:**

- Reconcile repository description/homepage, README, marketplace presentation,
  docs metadata, social-preview upload instructions, and dual-runtime claims.
- Canary fresh Claude Code and Codex installs from the generated payloads.
- Canary upgrades from the latest public `2.19.x` release with no cache cleanup,
  uninstall, identity change, or user data loss.
- Run release artifact, manifest parity, reference, docs, structural, unit, and
  full repository verification.
- Confirm Release Please owns the launch bump and every version-bearing source
  and generated file agrees.
- Release compatible work as `2.20.0`; require an explicit breaking-contract
  decision before allowing `3.0.0`.
- Hand off to DOC-012 only after all other public-launch gates are ready.

**Out of Scope:**

- In-place `1.0.0` reset, tag deletion/movement, or changelog rewriting.
- Custom domain, DNS, or removal of staging indexing guards.

**Key Files:**

- `docs-site/src/content/docs/contribute-and-release.md`
- `docs/ai/specs/cicd-release-pipeline-verification.md`
- repository Settings runbook/evidence
- release and UAT evidence artifacts

## Environment & Deployment Context

| Resource | Detail |
|---|---|
| Source plugin | `speckit-pro/` is authoritative; generated payloads are rebuilt, not hand-edited. |
| Documentation | Astro and Starlight under `docs-site/` (see `docs-site/package.json` for pinned versions). |
| Existing identity | Legacy wordmarks/marks/favicons exist; no SpecKit Pro-specific mark exists. |
| Release automation | Release Please owns source versions and refreshes generated artifacts. |
| Validation | Python-authoritative SpecKit Pro suite plus docs reference and site validation. |
| Public cutover | DOC-012 owns `plugins.racecraft.co` and removal of staging indexing guards. |

## References

- [Source PRD](../../prd-racecraft-identity-system.md)
- [Interactive Documentation roadmap](interactive-documentation-technical-roadmap.md)
- [Project constitution](../../../.specify/memory/constitution.md)
- [Project standards](../../../AGENTS.md)
- [Claude Code plugin reference](https://code.claude.com/docs/en/plugins-reference)
- [Codex plugin specification](https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/plugin-creator/references/plugin-json-spec.md)
- [Codex skill metadata](https://github.com/openai/skills/blob/main/skills/.system/skill-creator/references/openai_yaml.md)
- [Starlight logo configuration](https://starlight.astro.build/reference/configuration/#logo)
- [Semantic Versioning](https://semver.org/)
