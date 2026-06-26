# DOC-014 — "AI-discoverable" success metric

This document defines what "AI-discoverable" means for the SpecKit Pro docs site
and where that measure is observed after launch. It is the verification artifact
for DOC-014's headline goal (spec FR-021, FR-022, FR-023; success criterion
SC-009). It deliberately asserts **no numeric target** — see *Why no numeric
target* below.

## Definition

**"AI-discoverable"** = the docs site is *fetchable, parseable, and attributable*
by AI answer engines and coding agents, observed as **measurable referral and
citation traffic from AI surfaces**. Concretely, the goal is met when, after
launch, the production docs domain shows a non-zero and growing volume of:

- **Citations / referrals from AI answer engines** — ChatGPT (incl. ChatGPT
  Search), Perplexity, Google AI Overviews / AI Mode, and Claude — i.e. those
  engines fetch a docs page, and users arrive from them.
- **Retrieval by coding agents** — requests to the agent-readable surfaces this
  feature ships (`llms.txt` / `llms-full.txt` / `llms-small.txt` and the per-page
  `.md` variants).

This is an *observable* measure (traffic and citations you can read in a report),
not a vanity proxy. It does not claim that any single on-page artifact (JSON-LD,
llms.txt, a meta description) *causes* a citation; it measures the outcome those
artifacts collectively enable by making the site fetchable and entity-clear.

## Where it is measured (measurement sources)

| Source | What it shows | Notes |
|--------|---------------|-------|
| **Google Search Console — "Generative AI" / AI-surface performance reports** | Impressions and clicks attributed to Google's AI Overviews / AI Mode for the property | The authoritative first-party source for Google AI-surface visibility once the production domain is verified in GSC. |
| **GA4 — an "AI referrers" channel group / segment** | Sessions whose referrer is an AI answer engine — `chatgpt.com`, `perplexity.ai`, `claude.ai`, `gemini.google.com` (extend as engines appear) | A custom channel group / regex segment over `session_source` isolates AI-driven referrals from classic search and direct. |
| **Server / CDN request logs for the agent surfaces** (secondary) | Hits to `/llms.txt`, `/llms-full.txt`, `/llms-small.txt`, and `/<page>.md` | Confirms coding-agent retrieval of the surfaces DOC-014 ships, distinct from human/search traffic. |

Activating analytics (GA4, GSC property verification, log access) is **owned by
DOC-018**, not DOC-014. This document defines the metric so the goal is
verifiable; DOC-018 turns on the instrumentation that populates it.

## Why no numeric target

The site is served from a `noindex` staging URL until the launch feature
(DOC-012) flips it to the production domain and removes the guard. Until then it
is not indexed and has **no traffic baseline**, so any numeric target (e.g. "N
AI referrals/month") would be invented, not derived. The honest target is
therefore deferred: **establish a post-launch baseline first, then set a target
against it.** Asserting a number now would be measurement theater.

## Deliberate decision recorded here: AI training crawlers are ALLOWED

DOC-014 takes a **max-discoverability posture** and *allows* the AI-training
crawler tier (`GPTBot`, `Google-Extended`, `CCBot`, `anthropic-ai`, `ClaudeBot`)
in `robots.txt`, **inverting** the sibling marketing site, which blocks them
(spec FR-002, FR-005, FR-024). This is intentional and recorded so a future
maintainer does not "fix" it back to a blocking default:

- For a free, open-source developer tool, appearing in base-model knowledge is
  plausible upside at no cost to citation — training and citation crawlers are
  *separate* user-agents, so allowing training does not change citation behavior.
- The answer-engine **citation** tier (`OAI-SearchBot`, `ChatGPT-User`,
  `Claude-SearchBot`, `Claude-User`, `PerplexityBot`, `Perplexity-User`) and the
  default `*` are allowed as well; only the staging `noindex` meta guard (kept by
  this feature) prevents *indexing* while on the staging URL.

If the project ever decides to stop contributing content to model training, the
single change is to move the training tier from `Allow` to `Disallow` in
`docs-site/src/pages/robots.txt.ts` (and update the corresponding assertion in
`docs-site/scripts/validate-docs-quality.mjs`).

## How the on-page work supports the metric (not a citation lever claim)

DOC-014 ships the *infrastructure* that makes the above measurable: crawler
access (robots.txt), agent-readable content (llms.txt + per-page `.md`), correct
metadata (descriptions, one canonical), a structured-data entity graph
(Organization / WebSite / SoftwareApplication / Person), per-page social cards,
and a git-accurate freshness signal. Per spec FR-016, the **JSON-LD is justified
as a classic-search rich-results and entity-disambiguation mechanism — NOT as an
answer-engine/LLM citation lever** (LLMs strip `<script type="application/ld+json">`
and read visible HTML). The metric measures the *outcome* this infrastructure
enables; it does not attribute citations to any single tag.
