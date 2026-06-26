# Error-Handling Requirements Quality Checklist: SEO and AI Discoverability

**Purpose**: Unit-test the *requirements themselves* for the build-time failure and edge-case behavior of the new SEO/AI-discoverability surfaces (sitemap `<lastmod>` from git, visible `lastUpdated`, per-page Open Graph cards, per-page `.md`, the `robots.txt` endpoint, the meta-description gate) for completeness, clarity, consistency, and coverage — before implementation. The driving question for every item is: *when a generation step has missing input or fails, do the requirements say what happens, and is the answer "fail loud / valid output", never "silently wrong"?*
**Created**: 2026-06-25
**Feature**: [spec.md](../spec.md)
**Focus**: no-git-history `<lastmod>` and visible `lastUpdated` for a new/uncommitted page (frontmatter override / spec-valid fallback, NEVER build time per FR-017) · OG / per-page-`.md` generation failure for one page not silently shipping a broken/missing artifact · `robots.txt` endpoint always emitting a valid response · missing `description:` and missing `lastUpdated` edge cases
**Depth**: Standard (PR-reviewer gate; STATIC site, build-time generation — no runtime error paths to invent, KISS/YAGNI) · **Audience**: Reviewer validating the spec/plan before implementation

<!--
  Scope note: this is a STATIC docs site. Every "error" here is a BUILD-TIME
  condition (missing git history, a generation throw, missing frontmatter), not a
  served/runtime fault — the outputs are static artifacts with no request-time
  failure surface. The established posture (performance.md CHK018; plan
  "Performance Goals → Build-failure posture") is that a generation failure FAILS
  THE BUILD LOUDLY (CI catches it), never silently ships a missing/broken artifact.
  These items test whether each surface's failure/edge behavior is WRITTEN DOWN to
  that standard, and specifically whether the one genuine data-edge — a page with no
  git commit history yet — has a defined, FR-017-safe (non-build-time) answer. No
  speculative runtime error handling is demanded of a static endpoint that cannot
  fail at request time.
-->

## Freshness — No-Git-History `<lastmod>` (the genuine edge case)

- [x] CHK001 Is the behavior of the sitemap `<lastmod>` specified for a content page that has NO git commit history yet (newly added/uncommitted, or absent from history on a shallow→deep clone), given the mandated bulk `git log` walk omits such a page from its slug→date map? [Resolved — spec Edge Cases "Page with no change history yet" + §FR-017 now define the resolution order; plan Implementation notes "Sitemap `<lastmod>` for a page with no commit history" specifies the `serialize()` behavior (bulk walk omits the file; honor frontmatter date else leave `lastmod` undefined → element omitted)]
- [x] CHK002 Is the no-history fallback required to be FR-017-safe — i.e., it MUST NOT fall back to build time (and MUST NOT inherit `@astrojs/sitemap`'s build-time `lastmod` default) for a page missing from the git map? [Resolved — §FR-017 "the no-history fallback MUST NOT be build/deploy time"; plan Implementation notes "MUST NOT default to `new Date()` / build time, and MUST NOT let `@astrojs/sitemap`'s build-time `lastmod` option fill it in (do not set the integration's top-level `lastmod` option)"]
- [x] CHK003 Is the frontmatter date override stated as the FIRST-CHOICE source for a page with no commit history (honor an explicit authored date if present, before any omission/fallback)? [Resolved — spec Edge Cases + §FR-017 order step (1) "if the page pins an explicit frontmatter date, use it"; plan Implementation notes step (1) honors the frontmatter date first]
- [x] CHK004 Is the chosen no-history fallback when no frontmatter date exists stated unambiguously as ONE deterministic behavior (omit the `<lastmod>` element for that entry — valid per the sitemap protocol — rather than emit a wrong date), so the implementer is not left to guess between omit / build-time / today? [Resolved — spec Edge Cases + §FR-017 step (2) "the sitemap entry ... MUST omit its `<lastmod>` element entirely (which the sitemap protocol permits)"; plan Implementation notes step (2) "leave the entry's `lastmod` **undefined** so `@astrojs/sitemap` omits the `<lastmod>` element"]

## Freshness — Missing/No-History Visible `lastUpdated` Stamp

- [x] CHK005 Is the behavior of the visible "last updated" stamp specified for a page with no git commit history (Starlight's per-file commit-date lookup THROWS on a file with no timestamp; the bulk path omits it), so the build outcome is defined rather than an unhandled throw? [Resolved — spec §FR-018 "frontmatter date if pinned, otherwise no stamp ... MUST NOT show build/deploy time"; plan Implementation notes "prefer a frontmatter `lastUpdated`/date on a new page; absent one, the stamp is simply not shown ... the per-file path is NOT used for these — the frontmatter override is the supported remedy"]
- [x] CHK006 Is the visible-stamp no-history behavior reconciled with the sitemap `<lastmod>` no-history behavior, so the visible date and the freshness signal stay consistent (SC-007) for an uncommitted page rather than diverging? [Resolved — spec Edge Cases + §FR-018 require the visible stamp to follow "the same resolution order" as §FR-017 "so the visible date and the sitemap `<lastmod>` never diverge"; plan Implementation notes "keeps the visible date and the sitemap `<lastmod>` consistent on the no-history path (FR-017, FR-018, SC-007)"]
- [x] CHK007 Is the frontmatter date override available as the remedy for both the sitemap `<lastmod>` and the visible `lastUpdated` of a page with no commit history (a single authored date drives both)? [Resolved — research D6 + D7 both honor a frontmatter date override drawn from the same source; spec §FR-017 grants the per-page pin and §FR-018 requires the visible date be consistent with it]
- [x] CHK008 Is the CI prerequisite that the build has FULL git history (not a shallow clone) stated as an assumption/requirement, so the no-history path is the genuine new-page case and not silently triggered for every page by a depth-1 checkout? [Resolved — Assumptions §"Full change history available at build" + research D8 (`fetch-depth: 0`); a shallow checkout would collapse all dates and is explicitly disallowed]

## Build-Failure Posture — Generation Failures Do Not Ship Silently

- [x] CHK009 Is it stated that a per-page Open Graph card generation failure FAILS THE BUILD LOUDLY (caught in CI) rather than silently shipping a missing/broken card? [Resolved — spec Assumptions "A generation failure surfaces as a build failure (caught in CI), not a silently missing card"; plan "Performance Goals → Build-failure posture"; performance.md CHK018]
- [x] CHK010 Is the same build-fail-loud (never-silent) posture stated for the per-page `.md` endpoint and the `starlight-llms-txt` digests, so a generation failure on those surfaces is also caught at build time rather than emitting a missing/empty artifact? [Resolved — spec Edge Cases "Generation failure for a single page must not ship silently" names per-page text variant + digests; plan "Build-failure posture (all generated surfaces, never silent)" now enumerates OG cards, per-page `.md`, `starlight-llms-txt` digests, sitemap, and JSON-LD graph]
- [x] CHK011 Is the build-fail-loud posture tied to a deterministic gate (the `astro build` step inside `pnpm --dir docs-site validate`, run by the `validate-docs` CI job) so "loud" is verifiable, not aspirational? [Resolved — plan "Build-failure posture" "'Loud' is verifiable because that `astro build` is the step inside `pnpm --dir docs-site validate` that the `validate-docs` CI job runs — a failed generation is a non-zero build, not a degraded output"]

## `robots.txt` Endpoint — Always a Valid Response

- [x] CHK012 Is the `robots.txt` endpoint's successful output contract specified (HTTP 200, `text/plain; charset=utf-8`, all three tiers + a `Sitemap:` line), so "a valid response" is concretely defined rather than vague? [Resolved — contracts C1 + data-model §2: HTTP 200, `text/plain; charset=utf-8`, training+citation+default tiers and `Sitemap:` required, in order]
- [x] CHK013 Is it stated that the `robots.txt` endpoint is statically generated at build time (`prerender = true`) with no request-time/runtime failure path, so "always emits a valid response" is guaranteed structurally rather than by runtime error handling? [Resolved — plan "Build-failure posture" "The `robots.txt` endpoint and per-page `.md` are `prerender = true`, so they are produced at build time and served as static files with no request-time/runtime failure path — 'always emits a valid response' is a structural property of static generation, not runtime error handling (FR-001)"]
- [x] CHK014 Is the failure behavior defined if the `Sitemap:` absolute URL cannot be derived from `site`+`base` at build time (build fails loudly vs. emits a policy with a missing/blank Sitemap line)? [Resolved — plan Implementation notes "`robots.txt` Sitemap line derivation": if the derivation cannot produce a valid absolute URL "the endpoint MUST fail the build ... rather than emit a policy with a blank/missing `Sitemap:` line"]
- [x] CHK015 Is the single-authoritative-source requirement stated so a stale static `public/robots.txt` cannot shadow the endpoint and serve a stale/blocking policy (a silent-wrong-output failure mode)? [Resolved §FR-004a — single authoritative source; any pre-existing static policy file that would override the route MUST be removed; contracts C1 requires `public/robots.txt` absent]

## Missing `description:` — Hard Failure, Not Silent Skip

- [x] CHK016 Is a missing or empty `description` on any content page required to be a HARD build FAILURE (the quality gate fails; presence enforced, not advisory/warn-only)? [Resolved §FR-010 + contracts C9: `validateMetaDescriptions` globs `src/content/docs/**/*.{md,mdx}` and fails non-zero on any missing/empty description; SC-003]
- [x] CHK017 Is the gate's coverage stated to include BOTH the 12 hand-authored and the 7 generator-emitted pages, so a generated page cannot silently slip past the presence gate without a description? [Resolved — research D9 (generator emits `description:` in `renderPage()` frontmatter) + contracts C9 (glob covers all of `src/content/docs/**`); seo-metadata.md CHK027]
- [x] CHK018 Is the gate's failure behavior characterized clearly enough to distinguish a missing-`description` FAILURE from the (separate, deferred) question of description QUALITY, so reviewers do not expect quality scoring here (presence only)? [Resolved — §FR-010 enforces "presence ... not advisory" (the gate fails only on missing/empty, not on quality); spec Assumptions "Coordination with the editorial feature" defers description REFRESH/quality to DOC-015, and §FR-025 keeps prose/editorial out of scope — so the gate is presence-only by construction]

## Cross-Cutting Coverage & Boundaries

- [x] CHK019 Across all generated surfaces (sitemap, OG cards, per-page `.md`, llms.txt digests, structured data), is there a single stated principle that NO surface degrades silently — every failure either fails the build or emits a spec-valid output — so the error posture is consistent rather than per-surface ad hoc? [Resolved — spec Edge Cases "Generation failure for a single page must not ship silently" states the principle ("No generated discoverability surface may degrade silently") across all surfaces; plan "Build-failure posture (all generated surfaces, never silent)" enumerates them under one posture]
- [x] CHK020 Is it confirmed that this feature introduces no runtime/served error surface (all outputs are static build artifacts), so the checklist correctly demands build-time/edge behavior and not runtime error handling (KISS/YAGNI)? [Resolved — spec Assumptions "Build-time cost, not runtime cost" + data-model §"State / lifecycle: None ... produced deterministically at `astro build` time"; every surface is `prerender = true`]

## Notes

- Check items off as completed: `[x]`
- This is a STATIC site: every item tests a BUILD-TIME failure or data-edge requirement (missing git history, a generation throw, missing frontmatter), never a runtime SLO or served-error path. No speculative runtime error handling is demanded.
- Gap-marked items flag a failure/edge behavior that is currently implicit or undefined in spec/plan/research/contracts. The executor resolves each by either confirming it is adequately specified or adding a proportionate requirement/constraint to spec.md or plan.md. The genuine new behavior to resolve is the no-git-history `<lastmod>` / `lastUpdated` fallback (CHK001–CHK006); the rest are confirmations or small explicitness additions consistent with the already-established build-fail-loud posture.
- Traceability: every item references a spec/plan/research/contracts section or a quality marker.
