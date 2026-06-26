# Build-Performance Requirements Quality Checklist: SEO and AI Discoverability

**Purpose**: Unit-test the *requirements themselves* for the build-time and output-size cost of the new SEO/AI-discoverability surfaces (per-page dynamic Open Graph cards via `astro-og-canvas`/`canvaskit-wasm`, per-page `.md` endpoint, `starlight-llms-txt` digests, git-dated sitemap `serialize()`) for completeness, clarity, consistency, and measurability — before implementation, and ahead of DOC-017's runtime Lighthouse budget.
**Created**: 2026-06-25
**Feature**: [spec.md](../spec.md)
**Focus**: build-time cost of dynamic OG (canvaskit-wasm/Skia) over ~19 pages · build output size of per-page PNG cards · per-file `git log` cost in the sitemap `serialize()` (O(pages) git calls) · render-blocking-asset boundary (OG/llms/.md are off-page routes, not page assets) · scaling bound as the content-page set grows
**Depth**: Standard (PR-reviewer gate; static-site build cost, no runtime perf target in this feature) · **Audience**: Reviewer validating the spec/plan before implementation

<!--
  Scope note: this is a STATIC docs site. "Performance" here means BUILD-TIME cost
  and BUILD-OUTPUT size, not server/runtime latency. The spec/plan deliberately set
  "Performance Goals: N/A (build-time generation; no runtime perf target)" and defer
  the runtime Lighthouse budget to DOC-017. These items therefore test whether the
  BUILD-cost expectations are written down clearly enough to review, NOT whether a
  runtime SLO exists. Items are kept proportionate (KISS/YAGNI) — no speculative
  runtime SLOs are demanded of a static site.
-->

## Build-Time Cost — Are the Cost Expectations Specified?

- [ ] CHK001 Is the build-time generation model stated as a requirement/constraint (all new outputs — OG cards, per-page `.md`, llms.txt digests, sitemap — are produced at `astro build` with `prerender = true`, none at request time)? [Completeness, Spec §plan "Performance Goals", §research D3/D5/D6]
- [x] CHK002 Is the per-page Open Graph card generation cost (CanvasKit/Skia render once per content page) acknowledged as a build-cost requirement, with a stated expectation that it stays within reasonable bounds for the current ~19-page set? [Resolved — plan "Performance Goals" + spec Assumptions "Build-time cost, not runtime cost"; OG = one-time WASM load + ~19 small renders, within bounds, scales linearly]
- [x] CHK003 Is the one-time `canvaskit-wasm` initialization/load cost during the build distinguished from the per-card render cost, so a reviewer knows the OG cost is "fixed WASM load + N small renders" rather than unbounded? [Resolved — plan "Performance Goals" states "a one-time CanvasKit/Skia WASM load plus one small PNG render per content page"]
- [x] CHK004 Is the per-page `.md` endpoint's build cost characterized as trivial (raw `body` passthrough, no rendering) rather than left unquantified? [Resolved — plan "Performance Goals" + research D3; "a raw-`body` passthrough per page (no rendering), trivially cheap"]
- [x] CHK005 Is the `starlight-llms-txt` digest generation (three text tiers over the whole content model) acknowledged as a build-time text pass with no stated cost concern? [Resolved — plan "Performance Goals"; "three build-time text passes over the content model; bounded text output"]

## Sitemap `serialize()` — Per-File Git-Lookup Cost

- [x] CHK006 Is the cost of sourcing each page's `<lastmod>` from git (one `git log -1 --pretty=%cI <file>` per page = O(pages) subprocess invocations) surfaced as a requirement/assumption rather than left implicit? [Resolved — plan Constraints + Implementation notes "Sitemap git dates — batch, do NOT call `git log` per page"; the per-file path is named as the documented O(pages) slow path (withastro/astro#16803)]
- [x] CHK007 Is there a stated expectation about whether ~19 per-file `git log` calls are acceptable as-is, or whether a single history walk / batched lookup / cache is warranted, so the implementer is not left to guess? [Resolved — plan now REQUIRES a single bulk `git log` walk (slug→date map) rather than per-file invocation; matches Starlight `lastUpdated`'s bulk walk (D7)]
- [x] CHK008 Is the interaction between `fetch-depth: 0` (full history, required for accurate dates per §research D8) and the per-file `git log` cost addressed, so the freshness requirement and the build-cost requirement are reconciled rather than in tension? [Resolved — plan Constraints reconciles them: full history (D8) is required for accuracy, and the single bulk walk keeps the cost flat over that full history]
- [x] CHK009 Is the git-lookup cost requirement scoped to build only (CI/local build), with an explicit note that it adds zero runtime/served cost? [Resolved — plan Implementation notes "build-only cost (zero served/runtime cost)"; spec Assumptions reiterate build-time-not-runtime]

## Build-Output Size

- [x] CHK010 Is the build-output-size impact of one PNG OG card per content page acknowledged (N additional image artifacts in `docs-site/dist`), with a stated expectation that it stays within reasonable bounds? [Resolved — plan "Performance Goals"; "Output = ~19 small PNGs in `dist`", within bounds, scales linearly]
- [x] CHK011 Is the output-size impact of the per-page `.md` duplicates and the three llms.txt digests acknowledged as bounded text artifacts (proportional to content), not an open-ended concern? [Resolved — plan "Performance Goals"; per-page `.md` "bounded text proportional to content" and digests "bounded text output"]
- [x] CHK012 Is the OG card image format/dimensions constrained (a single card size per page) so output size is predictable rather than implementation-defined? [Resolved — plan "Performance Goals" specifies "one small PNG render per content page"; single PNG card per page (research D5), so output size is predictable]

## Render-Blocking / Page-Asset Boundary

- [x] CHK013 Is it stated as a requirement (or explicit non-concern) that the OG card is referenced only in `<head>` meta (`og:image`/`twitter:image`) and is NOT a render-blocking or on-page-loaded asset? [Resolved — plan "Performance Goals"; cards "referenced only in `<head>` ... not render-blocking or on-page-loaded assets (contracts C6)"]
- [x] CHK014 Is it stated that the per-page `.md` variant and the llms.txt digests are separate fetchable routes, not assets loaded by the rendered HTML page (so they add no page-weight)? [Resolved — plan "Performance Goals"; per-page `.md` and digests are "separate fetchable route[s], not ... asset[s] the rendered HTML loads (contracts C4/C5)"]
- [x] CHK015 Is the no-new-render-blocking-asset expectation stated as a constraint the feature must not violate, given DOC-017 will later gate runtime Lighthouse? [Resolved — plan Constraints "the feature MUST NOT add new render-blocking or on-page-loaded assets ... so DOC-017 inherits a clean perf baseline"; spec Assumptions echo this]

## Scaling & Boundary Conditions

- [x] CHK016 Is the cost model's behavior as the content-page set grows (OG renders, per-page `.md`, git lookups all scale linearly with page count) characterized, so growth from ~19 toward the ~26+ range does not silently breach an unstated bound? [Resolved — plan "Performance Goals" + spec Assumptions state cost "scale[s] linearly as that set grows"; the bulk git walk keeps the sitemap cost flat rather than O(pages)]
- [x] CHK017 Are the 3 MDX pages (which emit raw `body` including imports/JSX for `.md`, and still need an OG card) confirmed to carry the same per-page build cost as the 16 Markdown pages, with no special-case cost? [Resolved — research D3 (MDX `.md` emits raw `body`, acceptable) + plan "Performance Goals" (per-page passthrough/render is uniform); no special-case cost for the 3 MDX pages]
- [x] CHK018 Is a build-failure/degradation expectation stated if OG generation fails for a page (does the build fail loudly, or silently skip a card), so the cost/robustness boundary is defined rather than ambiguous? [Resolved — plan "Performance Goals" "Build-failure posture": generation runs inside `astro build`, so a failure fails the build loudly (CI catches it), not a silent missing card; spec Assumptions reiterate]

## Relationship to the Deferred Runtime Budget (DOC-017)

- [x] CHK019 Is the boundary between THIS feature (build-time cost, no runtime target) and DOC-017 (runtime Lighthouse budget) stated, so a reviewer does not expect a runtime SLO here nor assume runtime perf is out of mind entirely? [Resolved — plan "Performance Goals" + spec Assumptions name DOC-017 as the owner of the runtime Lighthouse budget; this feature asserts build-time cost only]
- [x] CHK020 Is there a stated expectation that this feature must not REGRESS build or runtime performance ahead of DOC-017 (additive build outputs only; no new on-page assets), so DOC-017 inherits a clean baseline? [Resolved — plan Constraints + spec Assumptions: additive build outputs only, no new render-blocking/on-page assets, so "DOC-017 inherits a clean perf baseline"]

## Notes

- Check items off as completed: `[x]`
- This is a STATIC site: every item tests a BUILD-TIME cost or BUILD-OUTPUT-size requirement, never a runtime SLO. The spec/plan correctly set "Performance Goals: N/A (build-time generation)"; these items test whether the *build-cost* expectations are written clearly enough to review.
- Gap-marked items flag a build-cost expectation that is currently implicit (the cost is real but unstated in spec/plan/research). The executor resolves each by either confirming it is adequately specified or adding a proportionate cost note/constraint to spec.md or plan.md — without inventing speculative runtime SLOs (KISS/YAGNI).
- Traceability: every item references a spec/plan/research/contracts section or a quality marker.
