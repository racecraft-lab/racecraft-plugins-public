import { expect, test } from '@playwright/test';

// DOC-014 C1 / FR-001, FR-002, FR-003, FR-004, FR-004a, FR-024.
//
// The crawler-access policy is a single authoritative `/robots.txt` produced by
// the `src/pages/robots.txt.ts` endpoint (the static `public/robots.txt` is
// removed so it cannot shadow this route). It is served at the configured base
// path in preview/production, so the spec fetches it relative to `baseURL`
// (which already ends in `/racecraft-plugins-public/`), matching the smoke
// spec's route convention.
//
// This site takes a DELIBERATE max-discoverability posture: the AI-training tier
// is ALLOWED — the INVERSE of the sibling marketing site, which `Disallow: /`s
// exactly these five user-agents. The assertions below lock that inversion in.

const CITATION_TIER = Object.freeze([
  'OAI-SearchBot',
  'ChatGPT-User',
  'Claude-SearchBot',
  'Claude-User',
  'PerplexityBot',
  'Perplexity-User',
]);

const TRAINING_TIER = Object.freeze([
  'GPTBot',
  'Google-Extended',
  'CCBot',
  'anthropic-ai',
  'ClaudeBot',
]);

// `https://racecraft-lab.github.io/racecraft-plugins-public` on staging; this is
// `site` + `base` from astro.config.mjs and flips automatically at the DOC-012
// launch. The Sitemap directive must point under this absolute prefix.
const SITE_BASE = 'https://racecraft-lab.github.io/racecraft-plugins-public';

/**
 * Parse robots.txt into a map of user-agent (lower-cased) → array of directive
 * lines ("Allow: /", "Disallow: /", …) that apply to that group. A blank line
 * ends a group. `User-agent:` lines may stack (multiple agents share one block).
 */
function parseRobots(text) {
  const groups = new Map();
  let currentAgents = [];

  for (const rawLine of text.split('\n')) {
    const line = rawLine.trim();
    if (line === '') {
      currentAgents = [];
      continue;
    }
    const uaMatch = /^User-agent:\s*(.+)$/i.exec(line);
    if (uaMatch) {
      const agent = uaMatch[1].trim().toLowerCase();
      currentAgents.push(agent);
      if (!groups.has(agent)) groups.set(agent, []);
      continue;
    }
    const directiveMatch = /^(Allow|Disallow):\s*(.*)$/i.exec(line);
    if (directiveMatch && currentAgents.length > 0) {
      for (const agent of currentAgents) {
        groups.get(agent).push(`${directiveMatch[1]}: ${directiveMatch[2]}`.trim());
      }
    }
  }

  return groups;
}

test.describe('DOC-014 robots.txt crawler-access policy (C1)', () => {
  let body;
  let groups;

  test.beforeAll(async ({ request, baseURL }) => {
    const response = await request.get(new URL('robots.txt', baseURL).toString());
    expect(response.status(), 'robots.txt must return HTTP 200').toBe(200);
    expect(
      response.headers()['content-type'] ?? '',
      'robots.txt must be served as text/plain; charset=utf-8',
    ).toContain('text/plain');
    body = await response.text();
    groups = parseRobots(body);
  });

  for (const agent of CITATION_TIER) {
    test(`citation-tier ${agent} is allowed to fetch every page`, () => {
      const directives = groups.get(agent.toLowerCase());
      expect(directives, `${agent} must have its own User-agent group`).toBeDefined();
      expect(directives, `${agent} must be allowed at /`).toContain('Allow: /');
      expect(directives, `${agent} must not be disallowed at /`).not.toContain('Disallow: /');
    });
  }

  for (const agent of TRAINING_TIER) {
    test(`training-tier ${agent} is ALLOWED (inverse of the sibling)`, () => {
      const directives = groups.get(agent.toLowerCase());
      expect(directives, `${agent} must have its own User-agent group`).toBeDefined();
      expect(directives, `${agent} must be allowed at / (deliberate divergence)`).toContain('Allow: /');
      expect(
        directives,
        `${agent} MUST NOT be disallowed — that would re-block the training tier (FR-024)`,
      ).not.toContain('Disallow: /');
    });
  }

  test('default (unnamed) crawler is allowed', () => {
    const directives = groups.get('*');
    expect(directives, 'a "User-agent: *" group must exist').toBeDefined();
    expect(directives, 'the default group must allow /').toContain('Allow: /');
    expect(directives, 'the default group must not disallow /').not.toContain('Disallow: /');
  });

  test('NO training-tier user-agent carries Disallow: / (C1 inversion guard)', () => {
    for (const agent of TRAINING_TIER) {
      const directives = groups.get(agent.toLowerCase()) ?? [];
      expect(directives, `${agent} must not be blocked`).not.toContain('Disallow: /');
    }
  });

  test('a Sitemap directive is advertised under SITE_BASE', () => {
    const sitemapLine = body
      .split('\n')
      .map((line) => line.trim())
      .find((line) => /^Sitemap:/i.test(line));
    expect(sitemapLine, 'robots.txt must advertise a Sitemap location').toBeDefined();
    const sitemapUrl = sitemapLine.replace(/^Sitemap:\s*/i, '').trim();
    expect(sitemapUrl, 'Sitemap line must not be blank').not.toBe('');
    expect(sitemapUrl, 'Sitemap URL must be absolute under SITE_BASE').toContain(SITE_BASE);
  });
});
