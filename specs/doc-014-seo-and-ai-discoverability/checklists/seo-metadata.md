# SEO & AI-Discoverability Requirements Quality Checklist: SEO and AI Discoverability

**Purpose**: Unit-test the SEO / AI-discoverability *requirements themselves* (crawler-access taxonomy, structured data, canonical, meta descriptions, freshness, social cards, deliberate divergences) for completeness, clarity, consistency, and measurability before implementation.
**Created**: 2026-06-25
**Feature**: [spec.md](../spec.md)
**Focus**: robots.txt 3-tier taxonomy & ordering · JSON-LD @graph cross-reference invariants · canonical single-source · meta-description presence gate · deliberate divergences (training ALLOWED, per-page dynamic OG, per-page .md + llms.txt)
**Depth**: Release gate (launch-blocking SEO baseline) · **Audience**: Reviewer + author validating the spec

## Crawler-Access Policy — Requirement Completeness & Ordering

- [ ] CHK001 Are the citation-tier user-agents enumerated by exact name in a requirement (not just "the citation tier"), so the policy is unambiguously verifiable? [Clarity, Spec §FR-001]
- [ ] CHK002 Are the training-tier user-agents enumerated by exact name in a requirement? [Clarity, Spec §FR-002]
- [x] CHK003 Is the *ordering* of the three robots tiers (training-allow, then citation-allow, then default `*`-allow, then `Sitemap:`) specified as a requirement, or is order left implementation-defined? [Resolved §FR-004a — all three tiers + Sitemap required for completeness; tier order recorded as an output-stability concern, not a crawler-precedence requirement (Google: most-specific group wins regardless of position)]
- [ ] CHK004 Is the default/unnamed-crawler allow rule specified independently of the named tiers? [Completeness, Spec §FR-003]
- [ ] CHK005 Is the sitemap-advertisement requirement specified as an *absolute* URL derived from the configured site value (not a hardcoded host)? [Clarity, Spec §FR-004]
- [ ] CHK006 Is the requirement that no training-tier user-agent receives a `Disallow` (the inverse of the sibling site) stated as an explicit negative requirement, not just implied by the allow? [Consistency, Spec §FR-024]
- [x] CHK007 Is there a requirement that the static `public/robots.txt` must not shadow the dynamic policy endpoint (i.e., a single authoritative source for the policy)? [Resolved §FR-004a — single authoritative source; any pre-existing static policy file that would override the route MUST be removed]

## Deliberate Divergences — Are They Pinned So They Are Not "Fixed" Back?

- [ ] CHK008 Is the allow-training decision recorded as deliberate in a durable artifact (not only in prose) so a future maintainer does not revert it to a blocking default? [Completeness, Spec §FR-005]
- [ ] CHK009 Is the divergence from the sibling marketing site (which blocks training) explicitly named as intentional in the requirements? [Clarity, Spec §US2]
- [ ] CHK010 Is the per-page dynamic Open Graph card requirement stated such that a single site-wide static image would *fail* the requirement (divergence preserved, not silently reduced)? [Clarity, Spec §FR-019]
- [ ] CHK011 Are BOTH agent-readable surfaces required to coexist — the whole-site digest AND the per-page text variant — with neither substituting for the other? [Consistency, Spec §FR-006, §FR-007]
- [ ] CHK012 Is the per-page-text-variant-vs-whole-site-digest overlap addressed so both remain individually fetchable and non-conflicting at build time? [Coverage, Spec Edge Cases]

## Structured Data — @graph Cross-Reference Invariants

- [x] CHK013 Is the WebSite-publisher-equals-Organization-`@id` cross-reference stated as a requirement, or only as a verification step in the contracts? [Resolved §FR-013 — WebSite publisher identifier MUST equal the Organization identifier so consumers resolve a single publishing Organization]
- [ ] CHK014 Is the SoftwareApplication free/zero-price requirement quantified (offers.price 0) rather than described only as "free"? [Clarity, Spec §FR-014]
- [ ] CHK015 Is the scope of the SoftwareApplication entity specified (which page(s) emit it) so it is neither omitted nor over-emitted site-wide? [Clarity, Spec §FR-014]
- [ ] CHK016 Are the entity identifiers (`@id`) and their derivation from the configured site value specified, so identifiers finalize automatically at the launch flip? [Completeness, Gap]
- [ ] CHK017 Is the Organization-to-source-host-org linkage (sameAs) specified with a concrete target so entity disambiguation is verifiable? [Clarity, Spec §FR-013]
- [ ] CHK018 Is the author/Person entity's source-host-profile linkage specified, and is the absence of PII in the identifier addressed? [Completeness, Spec §FR-015]
- [ ] CHK019 Is the prohibition on sunset rich-result types (FAQPage / HowTo) stated as a requirement the structured data must not violate? [Coverage, Spec §FR-028]
- [ ] CHK020 Does a requirement constrain the structured data's *justification* to classic-search rich results + entity disambiguation, explicitly NOT an answer-engine citation lever? [Clarity, Spec §FR-016]

## Canonical & Site-Value Derivation

- [ ] CHK021 Is "exactly one canonical URL per page" stated as a measurable requirement (zero or duplicate canonicals fail)? [Measurability, Spec §FR-011]
- [ ] CHK022 Is the single-canonical-source rule expressed as a negative requirement forbidding a second emitter alongside the platform built-in? [Consistency, Spec §FR-027]
- [ ] CHK023 Is the requirement that canonical AND sitemap URLs derive from the single configured site value (and finalize automatically at the launch flip) stated, with the production domain explicitly not hardcoded? [Clarity, Spec §FR-012]
- [ ] CHK024 Is the staging-host behavior of canonical/sitemap URLs during the noindex window addressed so reviewers do not flag staging URLs as a defect? [Coverage, Spec Edge Cases]

## Meta Descriptions — Presence Gate

- [ ] CHK025 Is "non-empty, page-appropriate meta description on every content page" stated as a requirement covering the full current content-page set? [Completeness, Spec §FR-009]
- [ ] CHK026 Is the quality gate's behavior on a missing description specified as a hard FAILURE (presence enforced, not advisory/warn-only)? [Measurability, Spec §FR-010]
- [ ] CHK027 Is the authored-vs-generated split for descriptions reconciled so generated pages are not silently exempt from the presence gate? [Consistency, Gap]
- [ ] CHK028 Is the coordination note with the downstream editorial refresh recorded so authored descriptions are not treated as final? [Assumption, Spec Assumptions]
- [ ] CHK029 Is the today-zero baseline (0% of pages have descriptions) captured so the success criterion is anchored to a real starting point? [Measurability, Spec §SC-003]

## Freshness Signal

- [ ] CHK030 Is the sitemap last-modified date required to come from real source change history (never build time), with an explicit per-page date-pin override allowed? [Clarity, Spec §FR-017]
- [ ] CHK031 Is the visible "last updated" date required to be consistent with the sitemap freshness signal (same source), not an independent value? [Consistency, Spec §FR-018]
- [x] CHK032 Is the CI prerequisite for accurate per-page dates (full git history rather than a shallow clone) surfaced as a requirement/assumption rather than left implicit? [Resolved — Assumptions §"Full change history available at build"; shallow checkout would collapse dates to one build commit, so the deploy pipeline MUST provide full history]

## Social Cards

- [ ] CHK033 Is the per-page-titled social card stated such that a generic site-wide card fails the requirement? [Clarity, Spec §FR-019]
- [ ] CHK034 Is build-time production of one card per content page specified (no orphans, none missing)? [Completeness, Spec §FR-020]

## Success Metric & Scope Boundaries

- [ ] CHK035 Is "AI-discoverable" required to be defined as a concrete observable measure with named measurement source(s)? [Measurability, Spec §FR-021, §FR-022]
- [ ] CHK036 Is the no-numeric-target decision stated as a deliberate deferral (not an omission), with the reason (no pre-launch baseline) recorded? [Clarity, Spec §FR-023]
- [ ] CHK037 Are the negative/scope-boundary requirements (no prose rewrite, no analytics, no 404/legal, no domain flip, noindex guard preserved) each stated with an owning/deferred feature named? [Coverage, Spec §FR-025, §FR-026]
- [ ] CHK038 Is the staging noindex guard explicitly required to remain in place and not be weakened by this feature? [Consistency, Spec §FR-029]
- [ ] CHK039 Is the reliance on request-header content negotiation explicitly excluded for the per-page text variant (distinct build-time URL required instead)? [Coverage, Spec §FR-028, Edge Cases]

## Agent-Readable Content Coverage

- [ ] CHK040 Is one-to-one correspondence between per-page text variants and rendered content pages stated (no orphaned variants, no page without a variant)? [Completeness, Spec §FR-008]
- [ ] CHK041 Is the whole-site digest required to include at minimum both a concise index digest and a full-content digest (not a single tier)? [Completeness, Spec §FR-006]

## Notes

- Check items off as completed: `[x]`
- Gap-marked items flag a requirement that may be missing or located only outside spec.md (e.g., in plan/research/contracts); the executor resolves each by either confirming it is adequately specified or adding it to the spec. All such items in this checklist were resolved into spec.md (see the `[Resolved ...]` annotations).
- Traceability: every item references a spec section or a quality marker.
