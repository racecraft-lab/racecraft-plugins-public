# Racecraft Interactive Documentation Roadmap — Product Companion

**Target PRD:** [docs/prd-interactive-documentation.md](prd-interactive-documentation.md)  
**Date:** 2026-06-12 (companion role since 2026-06-19)  
**Status:** DOC-001 through DOC-011 shipped and archived; DOC-012 through DOC-021 pending (production readiness + content/IA excellence). Custom-domain go-live is sequenced last.
**Intended downstream consumer:** Spec-Driven Development autopilot  
**Authoritative SPEC catalog:** [docs/ai/specs/interactive-documentation-technical-roadmap.md](ai/specs/interactive-documentation-technical-roadmap.md)

---

> **This file is the product-review companion, not the catalog.** To avoid the dual-roadmap drift the PRD warns about, the full DOC SPEC catalog, tier overview, dependency graph, and execution/launch sequencing now live in exactly one place — the [SpecKit technical roadmap](ai/specs/interactive-documentation-technical-roadmap.md). This companion keeps only the product-level framing that is not duplicated there.

## 1. Autopilot-Ready Property

Every user-visible PRD feature group has exactly one roadmap SPEC with stable IDs, explicit acceptance criteria, likely source files, validation steps, dependencies, risks, and no unresolved product decision that blocks scoping. Open questions are scoped to the SPEC that should resolve them.

## 2. Spec catalog, tiers, and sequencing → see the SpecKit technical roadmap

The authoritative catalog of every DOC spec (DOC-001 through DOC-021), the dependency tiers, the dependency graph, and the execution/launch order live in **[docs/ai/specs/interactive-documentation-technical-roadmap.md](ai/specs/interactive-documentation-technical-roadmap.md)**. Snapshot as of 2026-06-23:

- **Shipped and archived — content + IA plus staging deploy foundation:** DOC-001 through DOC-011.
- **Pending — production readiness (Tier 7):** DOC-012 (custom domain — runs last), DOC-014 (SEO), DOC-015 (editorial), DOC-016 (accessibility), DOC-017 (performance), DOC-018 (launch hygiene). DOC-013 (brand identity + landing page) shipped via PR #246.
- **Pending — content & IA excellence (Tier 8):** DOC-019 (voice & ELI5 tone), DOC-020 (per-page value & right-sizing), DOC-021 (task-based IA & wayfinding).
- **Launch policy:** DOC-011 shipped the staging deploy workflow and search-engine `noindex` guard; the custom-domain go-live (DOC-012) is sequenced **dead last**, so the site is not overtly public until launch-ready.

## 3. Validation Strategy

- Markdown linting for all docs content.
- Link checking for local links and official-source links, with an allowlist/retry policy for external flakiness.
- Static site build in CI after DOC-002.
- Command snippet review and safe validation only; no browser-triggered local shell execution.
- Marketplace JSON validity and source-path checks using existing repo validation where possible.
- Plugin manifest consistency checks across source, `dist/claude`, `dist/codex`, and both marketplace files.
- Generated payload consistency checks with `bash scripts/build-plugin-payloads.sh` when source/plugin docs change.
- Existing shell suite: `bash tests/speckit-pro/run-all.sh` for plugin-impacting changes; layer-specific runs for narrow edits.
- Accessibility checks for keyboard focus, labels, contrast, static fallback, and no JS-required critical path.
- Responsive viewport checks after static site exists.
- Manual smoke test for Claude Code install path.
- Manual smoke test for Codex install path.

## 4. Cut List

> Note: these were the v1 cut decisions. Several are now scheduled in the production-readiness catalog — analytics in DOC-018, landing/branding in DOC-013, and hosting/deploy in DOC-011/DOC-012 — so treat the entries below as historical context, not current exclusions.

- Full analytics instrumentation: deferred until hosting/framework is chosen.
- Live browser-based plugin execution: excluded for safety and environment variance.
- Auto-modifying Claude/Codex config from docs: excluded; docs provide commands and checks only.
- Full marketing site beyond the docs landing page: deferred until install-to-first-run is reliable.
- New local doctor command: deferred; v1 uses safe selectors/checkers and existing validation scripts.
- Unconfirmed official behavior: recorded as validation tasks or open questions, not requirements.

## 5. References

- Source PRD: [docs/prd-interactive-documentation.md](prd-interactive-documentation.md)
- Traceability matrix: [docs/traceability-interactive-documentation.md](traceability-interactive-documentation.md)
- Authoritative SPEC catalog: [docs/ai/specs/interactive-documentation-technical-roadmap.md](ai/specs/interactive-documentation-technical-roadmap.md)
- Roadmap-MOC home note: [docs/ai/specs/interactive-documentation-roadmap-MOC.md](ai/specs/interactive-documentation-roadmap-MOC.md)
