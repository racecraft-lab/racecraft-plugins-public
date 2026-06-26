---
topic: "SEO and AI discoverability for the docs site"
slug: "doc-014-seo-and-ai-discoverability"
date: "2026-06-25"
mode: "setup"
spec_id: "DOC-014"
source_input:
  type: "topic"
  ref: "DOC-014 scope from interactive-documentation-technical-roadmap.md"
question_count: 10
stop_reason: "natural"
---

# Design Concept: SEO and AI discoverability for the docs site

> **Source:** DOC-014 scope, `interactive-documentation-technical-roadmap.md`
> **Date:** 2026-06-25
> **Questions asked:** 10
> **Stop reason:** natural (all critical branches walked, design converged)

DOC-014 makes the Astro/Starlight docs site indexable, shareable, and discoverable
across classic search and AI answer engines, with correct metadata for the eventual
production domain. The roadmap's "Research basis" section had already settled most
of the technical defaults (robots.txt 3-tier taxonomy, llms.txt purpose, JSON-LD
types, what NOT to chase). This interview resolved the genuinely open decisions —
grounded in (a) an inventory of the proven sibling site's SEO artifacts under
`../../../landing-page/website/` and (b) cited 2026 SEO/GEO best-practice research.

## Goals

- Win **answer-engine citation** (ChatGPT Search, Perplexity, Google AI Overviews,
  Claude) via crawler access + entity clarity — not via `llms.txt`.
- Serve **coding-agent retrieval** (Cursor, Claude Code, Copilot) — the one surface
  `llms.txt` (and now per-page `.md`) measurably serves.
- **Allow AI training crawlers** (GPTBot, Google-Extended, CCBot, anthropic-ai,
  ClaudeBot) in addition to the citation/retrieval tier, taking a max-discoverability
  posture for a free OSS dev-tool. This deliberately **diverges from the sibling**,
  which blocks them. (Q1)
- Author `description:` frontmatter on all ~19 content pages now and add a
  presence-requiring `validate-docs-quality.mjs` rule; add an explicit
  "refresh meta descriptions" task to DOC-015's scope so the editorial pass revisits
  them. (Q2)
- Provide agent-readable content via the Starlight-native `starlight-llms-txt`
  (llms.txt + llms-full.txt + llms-small.txt) **and** a per-page raw Markdown
  variant for targeted single-page retrieval. (Q3, Q4)
- Emit JSON-LD `@graph` — Organization (`@id` + `sameAs` → GitHub org) + WebSite +
  `SoftwareApplication` per plugin page (`offers.price: 0`) + an optional Person/author
  entity — justified as Google/Bing rich-results + entity disambiguation, **not** as
  an LLM-citation lever. (Q5)
- Generate **per-page dynamic Open Graph cards** at build time (astro-og-canvas /
  starlight-og). (Q6)
- Wire sitemap `<lastmod>` and a visible "Last updated" stamp to **git commit date**
  (Starlight built-in `lastUpdated`, frontmatter override allowed) — never build time. (Q7)
- Document the **AI-discoverability success metric and its measurement source** (GSC
  Generative AI performance reports + a GA4 AI-referrer channel group) with **no
  numeric target** yet — the site is not indexed until launch. (Q9)
- Ship as **one spec, no split** (~250-300 reviewable LOC, within the ~400 ceiling). (Q10)

## Non-goals

- **Blocking AI training crawlers** — deliberately allowed; reversed from the sibling's
  protective posture (Q1).
- **Hardcoding the production domain or env-driving `site` now** — keep the github.io
  staging `site`; DOC-012 owns the one-line flip at launch; rely on Starlight's built-in
  canonical (do not add `astro-seo`, which would double-emit canonical) (Q8).
- **A numeric success-metric target** — deferred to post-launch once a baseline exists;
  DOC-018 owns analytics activation (Q9).
- **Prose rewrites / answer-first restructuring / voice-tone** — owned by DOC-015 / DOC-019.
- **Analytics activation and 404/legal/launch-hygiene** — owned by DOC-018.
- **`FAQPage` / `HowTo` schema as a rich-result play** — sunset (FAQ retired May 2026,
  HowTo desktop 2023); not shipped.
- **`Accept: text/markdown` content negotiation** — no crawler honors it on Astro static;
  per-page `.md` uses distinct build-time URLs instead (Q4).
- **Splitting into 2 slices** — the natural seam exists but the single-spec total is within
  the ceiling and the pieces share the astro.config + head surface (Q10).

## Design Tree (Q&A log)

### Q1. Should robots.txt ALLOW or BLOCK AI training crawlers (GPTBot, Google-Extended, CCBot, anthropic-ai, ClaudeBot)?

**Branch:** Crawler policy / robots.txt

**Recommended answer:** Allow training bots (max discoverability)
> Training and citation crawlers are **separate user-agents**, so blocking training
> buys nothing for answer-engine citation, while allowing it plausibly gets this free
> OSS dev-tool into base-model recommendations. Grounded in OpenAI/Anthropic/Cloudflare
> bot docs (2025-26): GPTBot is training-only; OAI-SearchBot is search/citation-only;
> blocking Google-Extended does not remove a site from AI Overviews. The citation tier
> (OAI-SearchBot, ChatGPT-User, Claude-SearchBot, Claude-User, PerplexityBot,
> Perplexity-User) is allowed either way.

**Alternatives offered:**
- Block training bots (match sibling): protective default; the sibling's `seo-robots-txt`
  blocks exactly these five. Costs nothing on citation but forgoes base-model presence.
- Granular (allow some, block others): more nuanced, harder to justify/maintain.

**User's answer:** Allow training bots (max discoverability)

**Notes:** Deliberately diverges from the sibling site, which blocks the training tier.
The robots.txt is still a 3-tier endpoint (training-allow now joins citation-allow +
default-allow `*` + `Sitemap:` directive).

---

### Q2. How should DOC-014 handle `description:` authoring vs. the presence-requiring validation rule (0 of ~19 pages have one today)?

**Branch:** Metadata / content frontmatter + cross-spec sequencing

**Recommended answer:** Author all now + enforcing rule (refresh later as natural follow-up)
> DOC-014 is the SEO/metadata spec, so shipping meta descriptions is its job, and the
> presence-requiring validator only passes if they exist. The roadmap's "author after
> prose so they don't go stale" note is honored by a refresh during DOC-015/DOC-019.

**Alternatives offered:**
- Defer authoring to DOC-015 (rule warn-only now): honors the note literally, but
  warn-only rules are easy to ignore and split one concern across two specs.

**User's answer:** Author now + flag explicit refresh task in DOC-015
> Author all ~19 descriptions now + enforcing rule, AND add an explicit "refresh meta
> descriptions" task to DOC-015's scope so the editorial pass deliberately revisits them.

**Notes:** Most robust against staleness. Requires a coordination note in both the
DOC-014 and DOC-015 roadmap entries / scopes.

---

### Q3. Use the Starlight-native llms.txt plugin, or port the sibling's `@4hse/astro-llms-txt`?

**Branch:** Agent retrieval / llms.txt implementation

**Recommended answer:** Use Starlight-native `starlight-llms-txt`
> Purpose-built for Starlight by the Astro-docs maintainer (delucis); generates
> llms.txt + llms-full.txt + llms-small.txt against Starlight's own content model with
> no DOM-selector retuning and no Tailwind-v4 jsdom patch. The sibling's `@4hse`
> integration assumes the landing-page DOM (custom `mainSelector`/`ignoreSelectors` +
> a Tailwind patch) and would need rework anyway. (Sibling inventory + 2026 research)

**Alternatives offered:**
- Port the sibling's `@4hse/astro-llms-txt`: matches the roadmap's literal "port the
  sibling" wording, but is strictly more porting work for a docs site with no upside.

**User's answer:** Use Starlight-native `starlight-llms-txt`

**Notes:** Diverges from the roadmap's literal "port `astro-llms-txt`" instruction;
the intent (ship llms.txt tiers documented as a coding-agent retrieval aid) is preserved.

---

### Q4. Beyond llms.txt, expose a raw per-page Markdown variant (`/page.md`) for coding agents?

**Branch:** Agent retrieval / per-page Markdown (the roadmap's flagged open decision)

**Recommended answer:** Yes — add per-page `.md` via a Starlight plugin
> This product's docs ARE consumed by coding agents (Claude Code/Codex), so per-page
> `.md` is squarely on-target. Cheap at ~20 pages via `starlight-md-txt` /
> `astro-markdown-for-agents`; serves targeted single-page retrieval that bulk
> llms-full.txt doesn't. Build-time distinct `.md` URLs (Astro static can't do
> Accept-header negotiation). Cloudflare names Claude Code + OpenCode as agents already
> sending `Accept: text/markdown`. (Cloudflare/Mintlify, 2026)

**Alternatives offered:**
- No — llms.txt tiers only for v1 (stay in budget / KISS; partial overlap with llms-full.txt).
- Defer to a dedicated later spec.

**User's answer:** Yes — add per-page `.md` via a Starlight plugin

**Notes:** Resolves the roadmap's "Open decision (resolve at scaffold time)". Distinct
from `Accept: text/markdown` content negotiation (out of scope — no crawler honors it).

---

### Q5. Which JSON-LD schema types should DOC-014 ship?

**Branch:** Structured data / entity infrastructure

**Recommended answer:** Organization + WebSite + SoftwareApplication per plugin page
> Exactly the roadmap's set. Organization (`@id` + `sameAs` → GitHub org) + WebSite
> injected globally via Starlight `head:`; SoftwareApplication (`offers.price: 0` — the
> most on-point free/OSS rich result, still live in 2026) per plugin page via a
> `Head.astro` override. All justified as Google/Bing rich-results + entity
> disambiguation, NOT LLM citation (LLMs strip JSON-LD and read visible HTML). Skip
> FAQPage/HowTo (sunset).

**Alternatives offered:**
- Minimal — Organization + WebSite only (forgoes the SoftwareApplication rich result).

**User's answer:** Also add an optional Person/author entity (E-E-A-T)
> The roadmap set plus a Person entity (`sameAs` → GitHub) for author disambiguation /
> E-E-A-T. The roadmap calls Person "optional"; the sibling scopes Person to its About
> page only.

**Notes:** Final set = Organization + WebSite + SoftwareApplication (per plugin page,
currently just speckit-pro) + Person/author. Under Starlight, injection must be redone
(global `head:` + `Head.astro` override / route-data); the sibling's schema factory
functions port, the layout-based injection does not.
> **RESOLVED (Clarify S2, 2026-06-25):** injection mechanism = **route-data middleware**
> (`routeMiddleware` + ported `src/lib/schema.ts`), NOT a `Head.astro` override — Starlight
> 0.40 docs call Head-override "a last resort" and recommend route middleware (added v0.32).
> The entity set is unchanged. "Plugin page" for SoftwareApplication resolves to the landing
> page `index.mdx` (allowlist-matched). Person identity pending Clarify-S2 consensus.

---

### Q6. Static OG card or per-page dynamic OG cards?

**Branch:** Social / Open Graph images

**Recommended answer:** Single static branded OG card
> One branded `og-default.png` referenced site-wide via Starlight `head:` — cheap, zero
> new build deps, within the ~150-LOC budget, exactly what the proven sibling ships;
> honors the constitution's KISS/YAGNI. OG images are a share-quality nicety, not a
> discoverability gate. (Recommended on budget/KISS grounds, diverging from the external
> research, which favored per-page dynamic.)

**Alternatives offered:**
- Static now, per-page dynamic as a fast-follow.

**User's answer:** Per-page dynamic OG cards now
> Auto-generate a titled card per page at build time (astro-og-canvas + Starlight
> component override per HiDeoo's recipe, or the `starlight-og` plugin). Better share
> quality when individual doc pages are posted to social. 2026-recommended.

**Notes:** Chosen over the budget-minimal recommendation. Adds a new dependency + a
build-time OG route + LOC — the main swing factor pushing DOC-014 above its original
~150-LOC estimate (see Q10 slice-sizing).

---

### Q7. How should sitemap `<lastmod>` and the "Last updated" stamp be sourced?

**Branch:** Sitemap / freshness signal

**Recommended answer:** Git commit date (Starlight `lastUpdated`), frontmatter override allowed
> Use Starlight's built-in git-based `lastUpdated` and feed the same value into the
> sitemap via a `serialize` function; allow a frontmatter override for pages that need
> to pin a date. Google trusts lastmod only when "verifiably accurate" against real
> changes — git commit date is exactly that, and it powers the visible "Last updated"
> stamp for free. Never build time. (Google Search Central, 2026)

**Alternatives offered:**
- Frontmatter `lastUpdated` only: controlled but goes stale silently.
- Keep @astrojs/sitemap build-time default: Google distrusts it; roadmap rules it out.

**User's answer:** Git commit date (Starlight `lastUpdated`), frontmatter override allowed

**Notes:** The sibling currently inherits the build-time default; DOC-014 corrects this.

---

### Q8. How should canonical / `site` be handled while the site is on the noindex'd staging URL?

**Branch:** Canonical URLs / domain handling

**Recommended answer:** Keep staging `site`; let DOC-012 flip it; rely on Starlight's built-in canonical
> Starlight auto-emits `<link rel=canonical>` from `site` + `base`, so canonical +
> sitemap URLs finalize automatically when DOC-012 changes `site` to plugins.racecraft.co.
> Don't hardcode the prod domain now (wrong canonicals on the noindex'd staging site)
> and don't add `astro-seo` (it double-emits canonical alongside Starlight). (Sibling
> portability note + roadmap)

**Alternatives offered:**
- Make `site` env-driven (staging vs prod): YAGNI — DOC-012 already owns a one-line flip.
- Set `site` to plugins.racecraft.co now: advertises 404 URLs until launch; contradicts
  the deliberate DOC-012-owns-the-flip sequencing.

**User's answer:** Keep staging `site`; let DOC-012 flip it; rely on Starlight's built-in canonical

**Notes:** Current `astro.config.mjs`: `site: 'https://racecraft-lab.github.io'`,
`base: '/racecraft-plugins-public'`. Confirms reliance on Starlight's built-in canonical;
do not introduce `astro-seo`.

---

### Q9. What should DOC-014 deliver for the AI-discoverability success metric?

**Branch:** Success metric / verifiability

**Recommended answer:** Document the metric definition + measurement source (no numeric target)
> DOC-014 ships a written definition of "AI-discoverable" (URL-level impressions in AI
> Overviews/AI Mode via GSC + a GA4 channel group for chatgpt.com/perplexity.ai/
> claude.ai/gemini) and where it's measured, so the goal is verifiable. No numeric
> target — the site isn't indexed yet, so any threshold would be invented. DOC-018 wires
> activation; targets come post-launch with a real baseline.

**Alternatives offered:**
- Define + set an initial target threshold: forces accountability, but zero baseline
  makes the number a guess.
- Defer the metric entirely to DOC-018: leaves DOC-014's own goal unverifiable.

**User's answer:** Document the metric definition + measurement source (no numeric target)

**Notes:** Coordinate with DOC-018, which owns analytics activation.

---

### Q10. Keep DOC-014 as one spec, or split it?

**Branch:** Slice-sizing (mandatory)

**Recommended answer:** Keep as one spec (no split)
> The interview's choices grew the estimate from ~150 to ~250-300 reviewable LOC
> (per-page OG + per-page .md + Person + 19 descriptions are the swing factors), still
> under the ~400-LOC ceiling, and the roadmap already documented "no split required."
> The pieces are tightly coupled SEO work touching the same astro.config + head surface;
> splitting creates artificial seams and two PRs that both edit astro.config. Estimator:
> 290 LOC / 1 slice / ok under the realistic "modify" framing (580 / 2 / warn only if
> every new dependency counts as fully net-new).

**Alternatives offered:**
- Decide at the autopilot atomicity gate: keep one spec, let the post-Tasks classifier
  recommend a split-PR stack.
- Split into 2 vertical slices now (A: crawler/agent access [robots.txt + llms.txt +
  per-page .md]; B: metadata [descriptions + JSON-LD + OG + sitemap lastmod + metric]).

**User's answer:** Keep as one spec (no split)

**Notes:** Advisory estimate recorded; the post-Tasks atomicity classifier may still
recommend a split-PR emission at PR time — that is a separate, downstream decision.

## Open Questions

- **What:** Whether per-page dynamic OG generation should use `astro-og-canvas` +
  a Starlight component override (HiDeoo recipe) or the `starlight-og` plugin.
  **Why deferred:** Implementation-detail choice between two equivalent build-time
  approaches; both satisfy the per-page-card decision (Q6).
  **Suggested next step:** Resolve during `/speckit-plan` based on which integrates
  more cleanly with the existing brand assets and `passthroughImageService` config.
  **RESOLVED (Clarify S3 consensus, 2026-06-25, 2/2 high-confidence):** `astro-og-canvas`
  v0.11.1 + an `OGImageRoute` endpoint `src/pages/og/[...slug].ts` (static `prerender`) +
  `og:image`/`twitter:image` injected by the same route-data middleware. `starlight-og` is
  proven non-existent (4 negative signals). The card uses a build-only `.ttf` face + PNG logo
  (canvaskit/skia rejects woff2/SVG); `passthroughImageService` is orthogonal (canvas render path).
- **What:** Which Starlight per-page-`.md` plugin to adopt (`starlight-md-txt` vs
  `astro-markdown-for-agents`) and whether it composes cleanly with `starlight-llms-txt`.
  **Why deferred:** Plugin-selection detail; the decision to ship per-page `.md` is
  settled (Q4).
  **RESOLVED (Clarify S1 consensus, 2026-06-25, 2/2 high-confidence):** Adopt **NO plugin** —
  serve per-page `.md` from a **custom Astro endpoint** `src/pages/[...slug].md.ts` that reads
  `getCollection('docs')` and returns each page's raw `body` as `text/markdown`. `astro-markdown-for-agents`
  does not exist as a current package; `starlight-dot-md` (3★, Starlight 0.40 compat unverified) and
  `starlight-md-txt` (`.md.txt` URL, unverifiable) both lose to a ~15-line dependency-free endpoint that
  composes trivially (the links-validator validates HTML only; `starlight-llms-txt` emits only `.txt`).
  This honors KISS/YAGNI and guarantees FR-008 via `getCollection`.
- **What:** Whether the post-Tasks atomicity classifier recommends a split-PR emission
  despite the single-spec decision.
  **Why deferred:** The classifier inspects structural seams that only exist after Tasks.
  **Suggested next step:** Honor the classifier's `atomicity-route.sh` output at PR-emission
  time; the A/B seam (crawler-access vs metadata) is the documented fallback split.

## Recommended Next Step

Setup mode — scaffolding has already happened. Run the populated workflow:

```text
/speckit-pro:speckit-autopilot docs/ai/specs/.process/DOC-014-workflow.md
```
