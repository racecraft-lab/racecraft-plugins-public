# UAT Runbook: doc-014-seo-and-ai-discoverability

| Field | Value |
|-------|-------|
| Spec | doc-014-seo-and-ai-discoverability |
| Branch | doc-014-seo-and-ai-discoverability |
| PR | **PR:** <set on PR open> |
| Generated from | 2026-06-26T01:35:43Z |



## Env Setup

This is a static Astro/Starlight docs site under `docs-site/`. To get a working copy running locally:

1. From the repo root, install dependencies (first time only): `pnpm --dir docs-site install`
2. Build the site: `pnpm --dir docs-site build`
3. Start the preview server: `pnpm --dir docs-site preview` — it serves at `http://127.0.0.1:4321/racecraft-plugins-public/`
4. (Optional) Run all automated checks in one pass: `pnpm --dir docs-site validate` — this runs the type-check, build, link validation, docs quality gate, and the Playwright end-to-end suite.

All URLs in the steps below are relative to the local preview base `http://127.0.0.1:4321/racecraft-plugins-public/`. On the live staging site they are under `https://racecraft-lab.github.io/racecraft-plugins-public/`.

## Per-Story Acceptance Tests

<a id="us-1"></a>
### User Story 1 - Citation crawler can fetch any page (Priority: P1)

An answer-engine citation bot (the kind ChatGPT, Perplexity, and Claude use to fetch pages they cite) must be explicitly allowed to read every page on the site.

1. Open `http://127.0.0.1:4321/racecraft-plugins-public/robots.txt` in a browser or fetch it with `curl http://127.0.0.1:4321/racecraft-plugins-public/robots.txt`.
2. Look for a `User-agent:` block (or individual `User-agent:` lines) covering each of these citation-tier bots: `OAI-SearchBot`, `ChatGPT-User`, `Claude-SearchBot`, `Claude-User`, `PerplexityBot`, `Perplexity-User`.
3. Confirm each of those agents has `Allow: /` and no `Disallow: /` line anywhere in the file.
4. Confirm the file contains a `Sitemap:` line with a full URL (starting with `https://`).
5. Confirm there is also a `User-agent: *` block with `Allow: /` — this covers any unnamed crawler.

Expected: Every citation-tier bot listed above is explicitly allowed. The sitemap URL is present. No `Disallow: /` appears anywhere in the file. Unnamed crawlers are also allowed.

- [ ] Citation crawler access confirmed as described above.

---

<a id="us-2"></a>
### User Story 2 - AI training crawler can fetch any page (Priority: P2)

AI training crawlers (the kind used to gather text for model training) must also be explicitly allowed. This is a deliberate choice for this open-source project and should be documented as intentional.

1. Open `robots.txt` as in Story 1 above.
2. Look for `User-agent:` entries covering each of these training-tier bots: `GPTBot`, `Google-Extended`, `CCBot`, `anthropic-ai`, `ClaudeBot`.
3. Confirm each has `Allow: /` and no `Disallow: /`.
4. Look for a comment or note in the file (or in a nearby doc) explaining that allowing the training tier is a deliberate decision — not an oversight — for this free, open-source project. (The spec requires this be recorded somewhere so a future maintainer does not "fix" it back to blocking.)

Expected: All five training-tier bots are permitted. The deliberate allow-training decision is recorded.

- [ ] Training crawler access confirmed as described above.

---

<a id="us-3"></a>
### User Story 3 - Coding agent retrieves whole-site and single-page content (Priority: P2)

A coding assistant (such as Cursor, Claude Code, or Copilot) can fetch the documentation as plain text — either the whole site at once or one page at a time — without scraping rendered HTML.

1. Open `http://127.0.0.1:4321/racecraft-plugins-public/llms.txt` — confirm the page loads and contains readable text (a concise site index, not an error or empty page).
2. Open `http://127.0.0.1:4321/racecraft-plugins-public/llms-full.txt` — confirm it loads and contains fuller documentation content in plain text.
3. Open `http://127.0.0.1:4321/racecraft-plugins-public/llms-small.txt` — confirm it loads and is non-empty.
4. Open a per-page Markdown variant for a content page. Try `http://127.0.0.1:4321/racecraft-plugins-public/glossary.md` (or substitute another content page slug with `.md` appended). Confirm the response is the Markdown source for that page, not a rendered HTML page.
5. Confirm the per-page `.md` URL corresponds to an actual content page that also renders as HTML — there should be no orphaned `.md` files for pages that do not exist.

Expected: All three whole-site digest URLs return non-empty plain-text content. The per-page `.md` URL returns that page's raw Markdown. No `.md` variant exists for a page that has no HTML counterpart.

- [ ] Whole-site and per-page agent-readable content confirmed as described above.

---

<a id="us-4"></a>
### User Story 4 - Search engine reads correct metadata for every page (Priority: P1)

Every page must carry a meta description, a single canonical URL, structured data describing the site and its author, and a freshness date based on when the page was actually last changed.

**Check 4a — Meta description and canonical URL**

1. Open any content page, for example `http://127.0.0.1:4321/racecraft-plugins-public/glossary/`.
2. Right-click the page and choose "View Page Source" (or use your browser's developer tools, Elements tab).
3. Search the HTML for `<meta name="description"`. Confirm it is present and its `content` attribute is a non-empty sentence describing that page (not a generic site description and not blank).
4. Search for `<link rel="canonical"`. Confirm exactly one such tag is present. Confirm its `href` starts with `https://racecraft-lab.github.io/racecraft-plugins-public/` (the staging host) — it must not contain a production domain that is not yet live.
5. Repeat for at least two other content pages to confirm descriptions are page-specific, not copied.

**Check 4b — Structured data**

1. Still in page source, search for `<script type="application/ld+json"`.
2. Copy the JSON block and paste it into a JSON viewer (or the browser console). Confirm the `@graph` array contains:
   - An `Organization` entity (with a stable `@id` URL and a link to the project's GitHub organization).
   - A `WebSite` entity whose `publisher` field's `@id` matches the `Organization` entity's `@id` (they point at the same thing).
   - A `Person` entity for "Fredrick Gabelmann" linked to a source-host profile.
3. On a plugin page (for example `http://127.0.0.1:4321/racecraft-plugins-public/` or a page describing a specific plugin), also confirm a `SoftwareApplication` entity is present in `@graph` with `offers.price` set to `"0"`.

**Check 4c — Freshness signal**

1. Open `http://127.0.0.1:4321/racecraft-plugins-public/sitemap-index.xml`. It should reference a `sitemap-0.xml` file.
2. Open `http://127.0.0.1:4321/racecraft-plugins-public/sitemap-0.xml`.
3. Find a few `<url>` entries. Each should have a `<lastmod>` value. Confirm these look like real past dates (for example `2026-06-20`) — not today's build date repeated for every page. Pages that were last changed at different times should show different dates.
4. Navigate to one of those pages in the browser. Scroll to the bottom (or look near the page title area, depending on the theme). Confirm a visible "Last updated" or similar date is shown, and it matches the date in `sitemap-0.xml` for that page.

Expected: Every content page has a unique, non-empty meta description and exactly one canonical URL pointing at the staging host. The structured-data graph contains Organization, WebSite, Person, and (on plugin pages) SoftwareApplication with a free price. Sitemap dates reflect real past commit dates, not the build time. Each page shows a matching visible date.

- [ ] Page metadata, structured data, and freshness signal confirmed as described above.

---

<a id="us-5"></a>
### User Story 5 - Shared page renders a social card (Priority: P3)

When someone shares a link to a specific documentation page on social media, a preview card specific to that page should appear — not one generic image for the whole site.

1. Open any content page in your browser and view its page source.
2. Search for `og:image` — confirm a `<meta property="og:image">` tag is present. Note its `content` URL; it should look like `.../og/<slug>.png` (a URL specific to this page).
3. Search for `twitter:image` — confirm a `<meta name="twitter:image">` tag is present and points at the same per-page card URL.
4. Open that card URL directly in a browser tab. Confirm a PNG image loads and is titled or labelled for that specific page (not a blank image and not the same generic image as every other page).
5. Repeat for one other content page to confirm each page has its own distinct card URL and image.

Expected: Every content page references its own per-page social card image. Opening that image URL shows a titled card relevant to that page.

- [ ] Per-page social cards confirmed as described above.

---

<a id="us-6"></a>
### User Story 6 - Maintainer can verify the discoverability goal (Priority: P3)

The repository documents what "AI-discoverable" means and how to measure it, so the goal is concrete and verifiable after launch.

1. Open the file `docs/ai/specs/doc-014-ai-discoverability-success-metric.md` from the repo root (this is a source file, not a rendered page — open it in a text editor or GitHub's file viewer).
2. Confirm the document defines "AI-discoverable" as a concrete, observable measure (for example: referral traffic from AI tools, or appearance in cited sources) — not as a vague aspiration.
3. Confirm the document names the specific places where that measure is observed after launch, such as Google Search Console's Generative AI reports and a Google Analytics 4 segment filtering for AI-origin referrers.
4. Confirm the document does NOT assert a numeric target (for example, no "must reach X visits from AI sources by date Y"). The target should be explicitly deferred to after a post-launch baseline exists.

Expected: The metric document defines what "AI-discoverable" means in observable terms, names where to measure it, and makes clear no numeric target is set yet.

- [ ] Discoverability success metric document confirmed as described above.

---



## FR Coverage Matrix

The table below maps each key requirement to the specific check in this runbook that proves it.

| What must be true | Where to verify it |
|---|---|
| Citation-tier bots (OAI-SearchBot, ChatGPT-User, Claude-SearchBot, Claude-User, PerplexityBot, Perplexity-User) are all allowed | Story 1, steps 1–3 |
| Training-tier bots (GPTBot, Google-Extended, CCBot, anthropic-ai, ClaudeBot) are all allowed | Story 2, steps 1–3 |
| Allow-training decision is recorded as deliberate | Story 2, step 4 |
| Default/unnamed crawlers are allowed | Story 1, step 5 |
| Sitemap URL is advertised in robots.txt | Story 1, step 4 |
| Whole-site index digest (llms.txt) is fetchable and non-empty | Story 3, step 1 |
| Whole-site full-content digest (llms-full.txt) is fetchable and non-empty | Story 3, step 2 |
| Per-page Markdown variant is fetchable at a distinct URL | Story 3, step 4 |
| No orphaned per-page variants (every .md has a matching HTML page) | Story 3, step 5 |
| Every content page has a non-empty, page-specific meta description | Story 4, Check 4a, steps 3 and 5 |
| Every content page has exactly one canonical URL, pointing at the staging host | Story 4, Check 4a, step 4 |
| Structured-data graph includes Organization and WebSite entities with matching publisher reference | Story 4, Check 4b, step 2 |
| Plugin pages include a SoftwareApplication entity marked as free | Story 4, Check 4b, step 3 |
| Person/author entity is present in the structured-data graph | Story 4, Check 4b, step 2 |
| Sitemap lastmod dates are real past dates from change history, not build time | Story 4, Check 4c, steps 2–3 |
| Visible "last updated" date on each page matches the sitemap date | Story 4, Check 4c, step 4 |
| Every content page references a per-page social card image | Story 5, steps 2–3 |
| Each social card image is titled for its specific page | Story 5, step 4 |
| "AI-discoverable" is concretely defined in a source document | Story 6, step 2 |
| Measurement sources are named (GSC Generative AI + GA4 AI-referrer segment) | Story 6, step 3 |
| No numeric target is asserted in the metric document | Story 6, step 4 |


## Negative-Path Tests

These checks confirm the feature handles unusual or incomplete states safely.

- **Staging noindex stays in place:** While the preview server is running, fetch `http://127.0.0.1:4321/racecraft-plugins-public/` and view page source. Confirm that the existing noindex meta tag (or `X-Robots-Tag: noindex` header) is still present and has NOT been removed by this feature. The crawler-access policy (robots.txt) allowing bots is separate from the search-engine index instruction — both must coexist.

- **Canonical URL uses the staging host, not a future production domain:** In Story 4 Check 4a step 4 above, confirm the canonical URL says `racecraft-lab.github.io/racecraft-plugins-public/` — not a `racecraft.co` or other production domain. Hardcoding the production domain now would advertise URLs that return 404 until launch.

- **Only one canonical link per page:** In page source, search for all occurrences of `canonical` (case-insensitive). Confirm exactly one `<link rel="canonical">` tag appears — no second source has introduced a duplicate.

- **Missing description causes a build failure, not a silent pass:** If you remove the `description` frontmatter field from any content page and re-run `pnpm --dir docs-site validate`, the command should exit with a non-zero status and print an error identifying the page with the missing description. It should not silently produce an output with an empty description field. (Restore the description after testing.)

- **A page with no git commit history omits its sitemap date rather than using today's build date:** If a new content page exists in the source tree but has never been committed to git, its entry in `sitemap-0.xml` should either be absent or lack a `<lastmod>` element entirely — it must not show today's date (the build date). Similarly, the page itself should show no visible "last updated" date rather than the build timestamp. (This edge case applies only to files that genuinely have no git history; all existing committed pages are unaffected.)

- **Both llms-full.txt and per-page .md variants are independently fetchable:** Open `llms-full.txt` and a per-page `.md` URL in the same browser session and confirm both load without error. They may overlap in content, but neither should break the other's build or request.

- **A build failure for any single page's generated output fails the whole build:** The build and validation steps (`pnpm --dir docs-site validate`) should not complete successfully if a social card image or a per-page Markdown variant failed to generate for any content page. A missing card or missing text variant must be a visible build error, not a silently skipped page.

## Self-Review Findings

**Self-Review:** <not available — workflow file not provided>

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

This feature is purely additive — it adds new endpoints, metadata, and build outputs but does not modify existing page content. To roll back: revert the merge commit with `git revert <SHA>`. This removes all new SEO endpoints (robots.txt policy, llms.txt digests, per-page .md variants, social cards, structured data, sitemap freshness wiring) and restores the previous metadata state. The staging noindex guard is not touched by this feature, so it remains in force regardless. See plan.md for the full list of changed files.
