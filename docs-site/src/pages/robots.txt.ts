import type { APIRoute } from 'astro';
import { base, site } from 'astro:config/server';

/**
 * Crawler-access policy endpoint (DOC-014, C1 / FR-001..FR-005, FR-024).
 *
 * Emits a single authoritative `/robots.txt` with three tiers, all `Allow: /`:
 *   1. AI-training tier  — GPTBot, Google-Extended, CCBot, anthropic-ai, ClaudeBot
 *   2. Answer-engine citation tier — OAI-SearchBot, ChatGPT-User, Claude-SearchBot,
 *      Claude-User, PerplexityBot, Perplexity-User
 *   3. Default `User-agent: *`
 * plus an absolute `Sitemap:` directive derived from `site` + `base`.
 *
 * DELIBERATE DIVERGENCE FROM THE SIBLING (FR-002, FR-005, FR-024): the sibling
 * marketing-site `robots.txt` `Disallow: /`s exactly the five training-tier
 * user-agents below. This docs site takes the opposite, max-discoverability
 * posture and ALLOWS them — for a free/OSS developer tool, base-model
 * familiarity is upside at no cost to citation (training and citation crawlers
 * are separate user-agents). This allow is INTENTIONAL; do not "fix" it back to a
 * blocking default. The formal record of this decision also lives in the
 * success-metric doc (FR-005).
 *
 * `prerender = true` — produced at build time and served as a static file, so it
 * has no request-time/runtime failure path (FR-001). The `Sitemap:` URL derives
 * from `site` + `base` (NOT `astro:env`); if that derivation cannot produce a
 * valid absolute URL the route THROWS to fail the build, rather than emit a
 * policy with a blank `Sitemap:` line (plan implementation note).
 *
 * @see specs/doc-014-seo-and-ai-discoverability/contracts/build-output-contracts.md C1
 */
export const prerender = true;

/** AI-training tier — ALLOWED here (the inverse of the sibling's block). */
const TRAINING_TIER = [
  'GPTBot',
  'Google-Extended',
  'CCBot',
  'anthropic-ai',
  'ClaudeBot',
];

/** Answer-engine citation tier — allowed so cited pages can be fetched. */
const CITATION_TIER = [
  'OAI-SearchBot',
  'ChatGPT-User',
  'Claude-SearchBot',
  'Claude-User',
  'PerplexityBot',
  'Perplexity-User',
];

/**
 * Build the absolute sitemap URL from `site` + `base`. Throws (failing the
 * build) if `site` is unset or the join is not a valid absolute URL — never
 * returns a blank/relative value.
 */
function sitemapUrl(): string {
  if (!site) {
    throw new Error(
      'robots.txt: `site` is not configured; cannot derive an absolute Sitemap URL.',
    );
  }
  // `base` is normalized by Astro (defaults to "/"); join it onto `site` and
  // resolve `sitemap-index.xml` against the result so the path always includes
  // the configured base segment.
  const normalizedBase = base.endsWith('/') ? base : `${base}/`;
  const url = new URL('sitemap-index.xml', new URL(normalizedBase, site));
  return url.toString();
}

export const GET: APIRoute = () => {
  const lines: string[] = [];

  // Tier 1: AI-training crawlers — ALLOW (deliberate inverse of the sibling).
  for (const agent of TRAINING_TIER) {
    lines.push(`User-agent: ${agent}`);
    lines.push('Allow: /');
    lines.push('');
  }

  // Tier 2: answer-engine citation crawlers — ALLOW.
  for (const agent of CITATION_TIER) {
    lines.push(`User-agent: ${agent}`);
    lines.push('Allow: /');
    lines.push('');
  }

  // Tier 3: default — ALLOW all other crawlers.
  lines.push('User-agent: *');
  lines.push('Allow: /');
  lines.push('');

  // Absolute sitemap location derived from site + base (throws on failure).
  lines.push(`Sitemap: ${sitemapUrl()}`);
  lines.push('');

  return new Response(lines.join('\n'), {
    status: 200,
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
};
