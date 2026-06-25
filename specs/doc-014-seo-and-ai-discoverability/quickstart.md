# Quickstart / Validation Guide: SEO and AI Discoverability (DOC-014)

**Feature**: `doc-014-seo-and-ai-discoverability`
**Date**: 2026-06-25

This guide proves the discoverability surface end-to-end. It is a validation
runbook, not an implementation guide — see `contracts/build-output-contracts.md`
and `data-model.md` for the shapes, and `tasks.md` (after `/speckit-tasks`) for
the implementation steps.

All commands run from the repo root and are scoped with `pnpm --dir docs-site …`.
Node `>=22.12` and `pnpm@10.25.0` (via Corepack) are required.

---

## Prerequisites (Implement phase)

The doc-014 worktree's `docs-site/node_modules` is **not** installed, and this
feature adds new direct dependencies. Before anything else:

```bash
# Add the new direct deps (exact versions per research.md):
#   starlight-llms-txt@0.10.0, astro-og-canvas@0.11.1, canvaskit-wasm,
#   @astrojs/sitemap@3.7.3 (promote from transitive)
# then install (regenerates pnpm-lock.yaml, which CI installs with --frozen-lockfile):
pnpm --dir docs-site install
pnpm --dir docs-site exec playwright install --with-deps chromium
```

> The regenerated `docs-site/pnpm-lock.yaml` MUST be committed — the deploy
> workflow installs with `--frozen-lockfile` and fails on a stale lockfile.

---

## One-command gate (mirrors CI)

```bash
pnpm --dir docs-site validate
```

This chain (`reference:check && check && validate:links && validate:safe-aids &&
validate:quality && validate:smoke:preview`) builds the site, runs the quality
gate (now including the meta-description presence rule), and runs the Playwright
suite (now including the new SEO specs once `playwright.config.mjs` `testMatch`
is broadened to a glob). A green run is the headline success signal.

---

## Per-surface checks

### US1 / US2 — crawler-access policy (SC-001, SC-002)
```bash
pnpm --dir docs-site build
grep -A1 -E 'User-agent: (GPTBot|OAI-SearchBot)' docs-site/dist/robots.txt   # expect "Allow: /"
grep -E '^Sitemap: ' docs-site/dist/robots.txt                               # expect the SITE_BASE sitemap URL
test ! -f docs-site/public/robots.txt && echo "static robots removed OK"
```
Expected: every training- and citation-tier agent shows `Allow: /`; default `*`
shows `Allow: /`; a `Sitemap:` line is present; no `Disallow: /` on any training
agent.

### US3 — agent-readable content (SC-005)
```bash
ls docs-site/dist/llms.txt docs-site/dist/llms-full.txt docs-site/dist/llms-small.txt   # all exist, non-empty
ls docs-site/dist/glossary.md docs-site/dist/troubleshooting.md                          # per-page .md variants exist
```
Expected: three non-empty digests; one `.md` per content page (one-to-one with
`getCollection('docs')`).

### US4 — page metadata, structured data, freshness (SC-003, SC-004, SC-006, SC-007)
```bash
# Meta-description presence gate (fails if any of the 19 pages lacks one):
pnpm --dir docs-site validate:quality

# Structured data + canonical (built HTML):
grep -o 'application/ld+json' docs-site/dist/index.html | head -1   # JSON-LD present
grep -c 'rel="canonical"' docs-site/dist/glossary/index.html        # exactly 1

# Sitemap lastmod is git-dated ISO, not build time:
grep -o '<lastmod>[^<]*</lastmod>' docs-site/dist/sitemap-0.xml | head
```
Expected: quality gate passes (all descriptions present); each page has one
canonical and a JSON-LD `@graph` (Organization `@id` == WebSite `publisher`
`@id`; SoftwareApplication `offers.price` `0` on the landing page; Person
present); `<lastmod>` values are valid ISO dates from git history.

### US5 — per-page social cards (SC-008)
```bash
ls docs-site/dist/og/                                  # one card per page
grep -o 'property="og:image"[^>]*' docs-site/dist/index.html   # head references the per-page card
```
Expected: a titled card per page; `og:image`/`twitter:image` head tags reference
the per-page card.

### US6 — success metric (SC-009)
Read the success-metric documentation artifact and confirm it (a) defines
"AI-discoverable" as an observable measure, (b) names GSC Generative AI reports +
the GA4 AI-referrer channel group, (c) records the allow-training divergence, and
(d) asserts no numeric target.

---

## Targeted e2e (the new SEO specs)

```bash
pnpm --dir docs-site validate:smoke:preview     # runs all Playwright specs incl. SEO
# or a single new spec while iterating:
pnpm --dir docs-site exec playwright test seo-robots-txt
```

The new specs (Chromium-only) cover: robots-txt (training ALLOWED — inverse of
the sibling), schema-org (Org `@id` == WebSite publisher `@id`;
SoftwareApplication `offers.price` 0; Person present), llms-txt (3 files,
200 + non-empty), and sitemap (`<lastmod>` valid ISO from git, not build time).

---

## CI freshness check (SC-007 in the deploy job)

The deploy workflow's `actions/checkout` gets `fetch-depth: 0` so per-file git
dates resolve. Without it, every `<lastmod>` and "Last updated" stamp would
collapse to the single deploy commit and SC-007 would fail in CI while passing
locally. Confirm the workflow validates green after the change.

---

## Negative checks (boundaries)

- DOC-011 `noindex, nofollow` head meta still present in built HTML (FR-029).
- No `astro-seo` in `docs-site/package.json` (FR-027 — single canonical source).
- No `FAQPage` / `HowTo` in any emitted JSON-LD (FR-028).
- `site` remains `https://racecraft-lab.github.io`; no hardcoded production
  domain anywhere in the diff (FR-012, SC-010).
