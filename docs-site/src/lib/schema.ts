/**
 * Schema.org JSON-LD factory functions (DOC-014, D2).
 *
 * Ported in substance from the sibling landing-page `src/lib/schema.ts`, but:
 *  - NO `schema-dts` typing dependency (plain typed object literals — FR-027/D2 YAGNI);
 *  - every `@id`/`url` derives from a passed-in `siteBase` (`${site}${base}`), so there
 *    is NO hardcoded production domain and the graph finalizes automatically at the
 *    DOC-012 launch flip (FR-012);
 *  - NO PII in any `@id` fragment (Person `@id` is `#person`, not an email/name);
 *  - `FAQPage`/`HowTo` factories are intentionally NOT ported (FR-028 sunset).
 *
 * The route-data middleware (`src/routeData.ts`, WP4) computes `siteBase` from the
 * Astro config and composes these via `buildGraph()` into one `@graph` per page.
 *
 * @see specs/doc-014-seo-and-ai-discoverability/data-model.md §3
 * @see specs/doc-014-seo-and-ai-discoverability/contracts/build-output-contracts.md C2
 */

// ─── Schema shapes (plain typed object literals; no schema-dts) ──────────────

export interface OrganizationSchema {
  '@type': 'Organization';
  '@id': string;
  name: string;
  url: string;
  logo: { '@type': 'ImageObject'; url: string };
  sameAs: string[];
}

export interface WebSiteSchema {
  '@type': 'WebSite';
  '@id': string;
  url: string;
  name: string;
  publisher: { '@id': string };
}

export interface SoftwareApplicationSchema {
  '@type': 'SoftwareApplication';
  '@id': string;
  name: string;
  applicationCategory: string;
  operatingSystem: string;
  offers: { '@type': 'Offer'; price: string; priceCurrency: string };
}

export interface PersonSchema {
  '@type': 'Person';
  '@id': string;
  name: string;
  worksFor: { '@id': string };
  sameAs: string[];
}

export type SchemaItem =
  | OrganizationSchema
  | WebSiteSchema
  | SoftwareApplicationSchema
  | PersonSchema;

export interface Graph {
  '@context': 'https://schema.org';
  '@graph': SchemaItem[];
}

/** Application metadata for a page that maps to a plugin/product. */
export interface PluginPageMeta {
  name: string;
  applicationCategory: string;
  operatingSystem: string;
  /** Price as a string; '0' for free / OSS. */
  price: string;
  priceCurrency: string;
  /** `@id` fragment for the SoftwareApplication node (no PII). */
  idFragment: string;
}

// ─── Factory functions (all derive from `siteBase`) ─────────────────────────

/** Organization — site-level, included on every page (FR-013). */
export function buildOrganizationSchema(siteBase: string): OrganizationSchema {
  return {
    '@type': 'Organization',
    '@id': `${siteBase}#organization`,
    name: 'Racecraft Lab',
    // Trailing slash to match Starlight's canonical homepage URL (trailingSlash: 'always').
    url: `${siteBase}/`,
    logo: { '@type': 'ImageObject', url: `${siteBase}/favicon.svg` },
    sameAs: ['https://github.com/racecraft-lab'],
  };
}

/**
 * WebSite — site-level, included on every page (FR-013).
 * `publisher['@id']` MUST equal the Organization `@id` (C2 cross-reference invariant).
 */
export function buildWebSiteSchema(siteBase: string): WebSiteSchema {
  return {
    '@type': 'WebSite',
    '@id': `${siteBase}#website`,
    url: `${siteBase}/`,
    name: 'Racecraft Public Plugins',
    publisher: { '@id': `${siteBase}#organization` },
  };
}

/** SoftwareApplication — landing page only, gated by `pluginPages` (FR-014). */
export function buildSoftwareApplicationSchema(
  siteBase: string,
  meta: PluginPageMeta
): SoftwareApplicationSchema {
  return {
    '@type': 'SoftwareApplication',
    '@id': `${siteBase}#${meta.idFragment}`,
    name: meta.name,
    applicationCategory: meta.applicationCategory,
    operatingSystem: meta.operatingSystem,
    offers: {
      '@type': 'Offer',
      price: meta.price,
      priceCurrency: meta.priceCurrency,
    },
  };
}

/**
 * Person — site-level, included on every page (FR-015).
 * `@id` is `#person` (NO PII in the fragment); `worksFor` → Organization `@id`.
 */
export function buildPersonSchema(siteBase: string): PersonSchema {
  return {
    '@type': 'Person',
    '@id': `${siteBase}#person`,
    name: 'Fredrick Gabelmann',
    worksFor: { '@id': `${siteBase}#organization` },
    sameAs: ['https://github.com/fgabelmannjr'],
  };
}

/** Compose schema items into a single `@graph` JSON-LD object. */
export function buildGraph(items: SchemaItem[]): Graph {
  return {
    '@context': 'https://schema.org',
    '@graph': items,
  };
}

/**
 * Allowlist of pages that carry a SoftwareApplication node, keyed by Starlight
 * collection slug. The landing page (`index.mdx`) has slug `''` and maps to
 * SpecKit Pro. This is the ONLY current entry; add a key here to surface another
 * plugin/product page (FR-014).
 */
export const pluginPages: Record<string, PluginPageMeta> = {
  '': {
    name: 'SpecKit Pro',
    applicationCategory: 'DeveloperApplication',
    operatingSystem: 'macOS, Linux',
    price: '0',
    priceCurrency: 'USD',
    idFragment: 'software-speckit-pro',
  },
};
