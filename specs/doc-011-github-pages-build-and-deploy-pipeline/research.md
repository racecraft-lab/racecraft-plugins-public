# Research: GitHub Pages Build-And-Deploy Pipeline

## Decision: Use standard GitHub Pages Actions

**Rationale**: DOC-011 needs a deploy-ready staging path, and GitHub Pages has a standard Actions deployment path using `actions/configure-pages`, `actions/upload-pages-artifact`, and `actions/deploy-pages`. This satisfies the roadmap without adding a custom deploy script or mutating repository Pages settings.

**Alternatives considered**: A custom deploy script was rejected as unnecessary and harder to maintain. GitHub API/CLI Pages setup was rejected because repository Pages source settings may require admin access and should remain manual operator setup.

## Decision: Trigger on `main` pushes with broad explicit paths plus `workflow_dispatch`

**Rationale**: The user chose broad repo paths to reduce missed docs-impacting deploys. The workflow should use explicit `push.paths` for rendered docs, docs-site config and validation files, generated-reference inputs, plugin manifests, plugin source surfaces, root scripts, generated payload directories, marketplace manifests, and workflow files. Fixture-heavy paths under `tests/speckit-pro/**` should be excluded after the positive test pattern to avoid publishing no-op staging artifacts.

**Alternatives considered**: Triggering on every `main` push was simpler but would deploy on clearly unrelated changes. A docs-site-only filter was cleaner but could miss generated-reference updates from plugin source, payload, or marketplace changes.

## Decision: Use Node 22 with Corepack pnpm 10.25.0

**Rationale**: `docs-site/package.json` declares `packageManager: pnpm@10.25.0`, and existing workflows already activate pnpm through Corepack. Node >=22.12 is the runtime requirement from the workflow prompt.

**Alternatives considered**: Installing a global pnpm version directly was rejected because Corepack keeps the workflow aligned to the package metadata. Using an older Node version was rejected because the prompt and docs-site baseline require Node 22.

## Decision: Gate deployment on `pnpm --dir docs-site validate`

**Rationale**: `validate` already composes reference freshness, Astro check/build, Starlight link validation through `pnpm build`, safe-aids validation, docs-quality validation, and Playwright smoke preview. Reusing it keeps DOC-011 aligned with DOC-010 and avoids inventing a weaker deploy gate.

**Alternatives considered**: `pnpm --dir docs-site build` only was rejected because it skips reference, quality, safe-aids, link, and smoke coverage. A separate deploy-specific validation script was rejected as unnecessary.

## Decision: Install only Chromium for Playwright smoke validation

**Rationale**: The existing PR Checks workflow installs Chromium before full docs validation. DOC-011 should mirror the minimum browser setup needed by `validate:smoke:preview`.

**Alternatives considered**: Installing all Playwright browsers was rejected as slower and broader than the current smoke requirement. Skipping browser install was rejected because the validation command includes Playwright.

## Decision: Upload `docs-site/dist` as the Pages artifact

**Rationale**: `astro.config.mjs` does not override Astro's default output directory, and `pnpm --dir docs-site validate` already runs the build path through `validate:links`. The Pages artifact should therefore be `docs-site/dist`.

**Alternatives considered**: Uploading the full `docs-site/` directory was rejected because Pages should receive static output, not source. Adding a custom output directory was rejected because DOC-011 does not need a config migration.

## Decision: Protect staging with both noindex meta and `robots.txt`

**Rationale**: The roadmap requires the staging GitHub Pages URL to remain previewable but not indexed until DOC-012. A global Starlight `head` meta tag with `noindex, nofollow` is the primary page-level indexing guard. `docs-site/public/robots.txt` with `User-agent: *` and `Disallow: /` provides crawler policy/signaling.

**Alternatives considered**: Robots-only protection was rejected because project Pages paths do not make `robots.txt` the strongest guarantee and because robots blocks crawling while noindex blocks indexing when crawlers can see the page. No guard was rejected because it violates the public-exposure policy.

## Decision: Keep DOC-012 as the launch boundary

**Rationale**: DOC-011 deploys a staging URL using the current GitHub Pages project-site assumptions. DOC-012 owns custom domain, base-path migration, and removal of the noindex/robots guard.

**Alternatives considered**: Combining deploy and launch was rejected because later branding, SEO, accessibility, performance, editorial, and launch hygiene specs remain pending.
