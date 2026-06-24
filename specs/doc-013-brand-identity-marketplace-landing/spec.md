# Feature Specification: Brand identity and marketplace landing page

**Feature Branch**: `doc-013-brand-identity-marketplace-landing`

**Created**: 2026-06-23

**Status**: Draft

**Input**: User description: "Apply Racecraft visual identity to the speckit-pro docs site (Astro + Starlight) and turn the stock-Starlight landing route into a real marketplace landing page (logo, hero, value prop, primary CTA), with consistent brand colors, typography, logo, and favicons across light and dark mode, staying WCAG AA accessible."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Branded marketplace landing page (Priority: P1)

A visitor evaluating the plugin marketplace arrives at the documentation home route. Instead of a generic documentation page, they see a branded marketplace entry point: the product logo, a benefit-led headline, a short plain-English value proposition for spec-driven development, a small set of scannable value-prop cards, one clear primary call-to-action that starts them on the fastest guided path to a working result, and a secondary call-to-action to view the project source. From the landing page alone they understand what the plugin is and how to begin.

**Why this priority**: This is the front door for marketplace evaluation. A visitor's first impression and their decision to start (or leave) is made here. It delivers standalone value even if the broader site-wide brand pass (Story 2) were deferred, because the landing route is the highest-traffic, highest-stakes surface for newcomers.

**Independent Test**: Load the documentation home route and confirm it renders as a splash-style landing page (not a standard documentation article) with a logo/mark, a headline, a value-prop body, value-prop cards, a primary CTA that links to the getting-started / first-workflow tutorial, and a secondary "View on GitHub" CTA. Verify the page communicates the product purpose without scrolling past the first screen.

**Acceptance Scenarios**:

1. **Given** a first-time visitor opens the documentation home route, **When** the page loads, **Then** they see a branded splash layout with the product mark, a benefit headline, a short value-prop, a primary CTA, and a secondary CTA — not a generic documentation article with a sidebar-style body.
2. **Given** the landing page is displayed, **When** the visitor reads the call-to-action area, **Then** the primary CTA leads to the getting-started / first-workflow tutorial and the secondary CTA leads to the project's GitHub repository.
3. **Given** the landing page is displayed, **When** the visitor scans the value-prop area, **Then** approximately three concise value-proposition cards summarize what the plugin offers in plain, anti-hype language.
4. **Given** a visitor on a narrow (mobile-width) viewport, **When** the landing page loads, **Then** the hero, cards, and CTAs remain readable and usable without horizontal scrolling.

---

### User Story 2 - Consistent, accessible site-wide brand identity (Priority: P2)

Any reader navigating the documentation site — landing page or any interior article — experiences a consistent Racecraft visual identity: brand colors applied to accents and links, the brand typography (display, body, and monospace typefaces), the wordmark in the site header, and the brand favicon set in the browser tab. The identity is coherent in both light and dark mode, and all text and interactive elements meet WCAG AA contrast.

**Why this priority**: This generalizes the brand from the landing page to the whole site, making the documentation feel like a single branded product rather than stock tooling. It depends on the same brand assets as Story 1 but covers every route, so it is prioritized just below the highest-stakes landing surface.

**Independent Test**: Navigate to several interior documentation routes in both light and dark mode and confirm brand accent color on links/active navigation, brand typefaces in headings/body/code, the wordmark in the header, and the brand favicon in the browser tab — with no broken or unstyled fallback — and verify text/interactive contrast meets WCAG AA in both modes.

**Acceptance Scenarios**:

1. **Given** any documentation route in light mode, **When** it renders, **Then** links and active navigation use the brand accent (blue family), headings and body use the brand display and body typefaces, code uses the brand monospace typeface, the header shows the wordmark, and the browser tab shows the brand favicon.
2. **Given** any documentation route in dark mode, **When** it renders, **Then** the reading surface is a soft dark-gray (not pure black), the brand accent and typography remain applied, the dark-variant wordmark is shown in the header, and contrast remains legible.
3. **Given** a reader toggles between light and dark mode, **When** the theme changes, **Then** the correct light/dark variants of the wordmark and accent treatment are used with no unstyled flash of the wrong theme's assets.
4. **Given** any text or interactive element on the site, **When** its contrast is measured against its background, **Then** it meets the WCAG AA contrast ratio in both light and dark mode (4.5:1 normal text / 3:1 large text / 3:1 non-text), with link-sized brand-blue text using the AA-safe darker blue and brand red never used as failing normal-size text (see the contrast-pair table in §Key Entities / research token map for the enumerated foreground-background pairs and their measured ratios).
5. **Given** a reader who has enabled reduced-motion in their environment, **When** the site renders any animated entrance, **Then** motion is suppressed or reduced in line with the reduced-motion preference.
6. **Given** a keyboard-only reader tabbing through links, navigation, and the call-to-action buttons, **When** an element receives focus, **Then** a visible focus indicator appears that meets ≥3:1 contrast against its surface in both light and dark mode.

---

### Edge Cases

- **Web fonts not yet loaded / fail to load**: Text MUST remain visible immediately using a system fallback stack (no invisible text while fonts load), and the layout MUST NOT break when the brand typefaces are unavailable.
- **Theme variant mismatch**: When the visitor's theme is dark, the light wordmark variant MUST be used (and vice versa) so the mark never disappears against a same-color background; the same applies to the favicon's light/dark behavior where supported.
- **Reduced-motion preference**: Any entrance animation MUST respect the reduced-motion preference and degrade to no/least motion.
- **Narrow viewport**: The landing hero, value-prop cards, and CTAs MUST remain readable and operable on small screens without horizontal scroll.
- **Brand value ambiguity**: When a brand value in the brand guide is ambiguous or conflicts, the live `landing-page/website` source CSS is authoritative and MUST be re-checked before the value is applied.
- **Missing or undecided hero copy**: Final hero wording (headline, tagline, card titles/blurbs) is drafted during this feature against the brand guide's verbal-tone reference; direction (plain-English, anti-hype) is fixed even though exact wording is authored here.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The documentation home route MUST render as a marketplace landing page using a splash-style layout (full-width hero, not the standard documentation article layout), built from the documentation framework's native landing capabilities rather than bespoke custom page components.
- **FR-001a**: The landing page MUST present, within the first screen (above the fold, before any scrolling), the co-appearing set of {logo/mark, benefit headline, short value proposition, primary call-to-action} so a first-time visitor can identify what the plugin is and where to start without scrolling. This above-the-fold comprehension obligation MUST hold on narrow (mobile-width) viewports as well as desktop, where vertical space is tightest; the secondary call-to-action MAY fall at or just below the fold but the four primary comprehension elements MUST NOT. (Rationale: users spend the majority of viewing time above the fold and decide whether to continue based on what is visible without scrolling — NN/g above-the-fold findings.)
- **FR-002**: The landing page MUST present a logo/mark, a benefit-led headline, a short plain-English value proposition for spec-driven development, a primary call-to-action, and a secondary call-to-action. The headline MUST be benefit-led — it MUST state a reader-facing value or outcome of spec-driven development in plain language, NOT merely name the product, a feature, or a component (the testable distinction: "what the reader gets" rather than "what the thing is"). The value proposition MUST be a plain-English description of what the plugin is for, distinct from a feature list.
- **FR-003**: The landing page primary call-to-action MUST link to the getting-started / first-workflow tutorial, and the secondary call-to-action MUST link to the project's GitHub repository.
- **FR-003a**: The landing hero MUST present exactly one primary call-to-action and at most one secondary call-to-action, and MUST NOT introduce additional competing calls-to-action in the hero (a single, unambiguous primary conversion path). The secondary call-to-action MUST be visually subordinate to the primary — the primary rendered as the dominant, filled/emphasized action and the secondary as a lower-emphasis treatment (e.g., the framework's outline/minimal hero-action variant) so the two never carry equal visual weight. (Rationale: multiple competing CTAs create decision fatigue and reduce conversion; a secondary CTA is acceptable only when visually subordinate — NN/g and CXL CTA-hierarchy guidance. The framework's `hero.actions` `variant: 'primary' | 'secondary' | 'minimal'` provides the enforcing mechanism.)
- **FR-004**: The landing page MUST include a small set of concise value-proposition cards — three by default, and in all cases within the range of two to four — summarizing the plugin's value in plain, anti-hype language. Each card MUST be scannable (a short benefit-led title plus a brief plain-English blurb) and MUST express a user-facing benefit rather than an internal feature label or jargon term.
- **FR-004a**: All landing-page copy (headline, value proposition, and card titles/blurbs) MUST satisfy the brand guide's verbal-tone reference (§6: pragmatic, transparent, anti-hype). "Anti-hype, plain-English" is made testable as: (a) NO marketing-hype or unsubstantiated superlatives (e.g., "revolutionary", "game-changing", "the best", "effortless", "magical", "supercharge", "10x", "world-class", "AI-powered" used as a boast); (b) NO unexplained internal jargon or acronyms in visitor-facing copy (terms a first-time visitor would not know MUST be plain-language or omitted); and (c) the value stated as a concrete, verifiable capability or outcome rather than aspirational fluff. This is landing-copy direction only; a full verbal-voice/tone system is out of scope and deferred to DOC-019 (see FR-017).
- **FR-005**: The site MUST apply the Racecraft brand color palette so that links and active navigation use the blue accent family, while red is reserved as punctuation for the logo mark, the browser theme color, and the hero's primary call-to-action — red MUST NOT be used as the general site link/navigation accent.
- **FR-005a**: Brand red (`#dc143c`) used as punctuation MUST NOT be used for normal-size foreground text against the warm-neutral base (`#f1f0ec`) or against the true-black hero block, because that pairing fails WCAG AA normal-text contrast (measured `#dc143c` on `#f1f0ec` = 4.38:1 and on `#0a0a0a` = 3.97:1, both below the 4.5:1 normal-text threshold). Red punctuation is permitted only where it satisfies a passing pattern: (a) the hero primary call-to-action rendered as white text on a red fill (`#ffffff` on `#dc143c` = 4.99:1, AA-pass), (b) red used only at large-text size/weight or as a non-text graphical accent (≥3:1), or (c) red baked into the logo mark, which is exempt under the WCAG logotype exception. The contrast obligation for the hero CTA label applies to the label/background pair actually rendered, not merely to body/link text.
- **FR-006**: Brand-blue used for link-sized text MUST use the AA-safe darker blue so that link text meets WCAG AA contrast against its background. The applicable numeric thresholds are WCAG 2.2 AA: 4.5:1 for normal-size text, 3:1 for large text (≥24px regular or ≥18.66px / 14pt bold), and 3:1 for non-text/UI-component and focus-indicator contrast. The AA-safe link blue MUST meet 4.5:1 in BOTH modes: light link text `#2a6a99` on the warm base `#f1f0ec` measures 5.09:1, and dark link text `#7cb3dd` on the soft-dark surface `#1a1a1a` measures 7.75:1 — both AA-pass. The non-text blue accent `#3c89c6` (focus ring / active-nav block) MUST meet the 3:1 non-text threshold and MUST NOT be used as normal-size link text (it measures only 3.76:1 on white, failing the 4.5:1 text threshold — the reason the AA-safe `#2a6a99` exists).
- **FR-007**: The site MUST self-host the brand typefaces (display, body, and monospace), shipping only the lean weight set actually used: the display typeface at regular and bold, the body typeface at regular and semibold, and the monospace typeface at regular. Each shipped face MUST be in the compressed web-font format **woff2** (the modern, widest-support format with the best compression — uncompressed or legacy formats such as TTF/OTF/WOFF MUST NOT be shipped, because they enlarge the payload for no compatibility gain). This yields exactly five woff2 faces; the additional weights present in the brand source (Space Grotesk 300/500/600, Geist 500/700/800, Fira Code 500/600) MUST NOT be shipped.
- **FR-008**: Self-hosted fonts MUST load with a swap behavior (`font-display: swap` on every `@font-face`) so body text remains visible during font load using a system fallback, and ONLY the most critical above-the-fold weights — the display bold (Space Grotesk 700) and the body regular (Geist 400) — MUST be preloaded. Preloading MUST be limited to exactly those two faces: the remaining three faces (Space Grotesk 400, Geist 600, Fira Code 400) MUST NOT be preloaded, because each preload contends for early bandwidth with other critical resources and over-preloading prioritizes everything (and therefore nothing). Each font preload MUST carry the `crossorigin` attribute (without it a self-hosted font preload is ignored and the font is fetched twice). Fonts MUST be served locally with no dependency on an external font host (no third-party font CDN request at runtime).
- **FR-009**: The site header MUST display the brand wordmark (with distinct light and dark variants) in place of the plain text title, while preserving an accessible text name of the site for assistive technology and keeping the header logo functioning as the home link.
- **FR-010**: The landing hero MUST use the brand logomark image, with the correct variant shown for light and dark mode. The hero logomark MUST provide alt text that gives assistive-technology users an equivalent (the framework's `hero.image` `alt` field), and its role MUST be decided explicitly: if the logomark is purely decorative beside an adjacent text headline that already conveys the brand, it MAY use an empty/decorative alt to avoid redundancy; otherwise it MUST carry a meaningful brand name. The mark MUST NOT be left with an unset/auto alt.
- **FR-011**: The site MUST set the brand favicon set and the brand browser theme color so the brand mark appears in the browser tab and platform UI.
- **FR-012**: The brand identity (colors, typography, logo, favicons) MUST be applied consistently across both light and dark mode and across all documentation routes, not only the landing page.
- **FR-013**: In dark mode, the primary reading surface MUST be a soft dark-gray within the documented soft-dark range `#121212`–`#1e1e1e` (target `#1a1a1a`) rather than true black, to avoid halation/eye-strain on the reading surface; true black (`#0a0a0a`) MUST be reserved for the decorative hero block only and MUST NOT be used as the reading background on any route.
- **FR-014**: All text and interactive elements MUST meet WCAG AA contrast in both light and dark mode (4.5:1 normal text, 3:1 large text, 3:1 non-text/UI). Dark-mode body text MUST use a near-white (e.g. `#e6e6e6`) rather than pure `#ffffff` on the soft-dark surface to avoid excessive contrast, while headings MAY use full white.
- **FR-014a**: All keyboard-operable interactive elements (links, navigation, the primary and secondary call-to-action) MUST have a visible keyboard focus indicator (WCAG 2.2 SC 2.4.7 Focus Visible), and that focus indicator MUST meet the 3:1 non-text contrast threshold against its adjacent surface in BOTH light and dark mode (the blue focus ring `#3c89c6` measures 3.30:1 on `#f1f0ec` and 4.63:1 on `#1a1a1a`, both ≥3:1 — AA-pass).
- **FR-015**: Any entrance animation introduced MUST respect the user's reduced-motion preference.
- **FR-016**: Brand values MUST be sourced from the feature's brand guide, and where a value is ambiguous it MUST be reconciled against the authoritative live `landing-page/website` source CSS before being applied.
- **FR-017**: The implementation MUST stay within the declared reviewability budget (see Reviewability Budget) and MUST NOT expand scope into per-component restyling, a performance/Lighthouse budget, a verbal-voice/tone system, or domain/base-path cutover (those are tracked as separate follow-up specs).

### Reviewability Notes *(if applicable)*

- No typed reviewability exceptions are claimed for this feature. The change is a net-new brand/styling slice; binary font and favicon assets are declared (non-reviewable) artifacts under the budget and are not counted toward reviewable LOC.

### Reviewability Budget *(mandatory)*

- **Primary surface**: UI (docs-site brand styling + landing route)
- **Secondary surfaces, if any**: seed/config (documentation framework configuration for logo, favicon, custom styles, and font preload); binary assets (woff2 fonts, SVG logos, favicon image set) declared as non-reviewable artifacts
- **Projected reviewable LOC**: ~80 reviewable CSS lines plus a small landing-route content file and a handful of configuration lines (binary font/favicon assets excluded); design-concept estimator reported ~395 LOC total across the slice
- **Projected production files**: 1–2 primary production files (brand stylesheet + landing route content), plus configuration edits
- **Projected total files**: 6–8 text/config files, plus binary font and favicon/logo assets
- **Budget result**: within budget
- **Split decision**: Remains a single vertical slice. Size signals (2 user stories, ~6–8 files, ~17 functional requirements, net-new) and the shared estimator (`suggested_slices: 1`, `status: ok`) all indicate one thin end-to-end slice — brand tokens + fonts + logo + landing hero delivered together. No split.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence (e.g., FR-005/FR-006 → brand stylesheet + contrast check; FR-001–FR-004 → landing route content; FR-009–FR-011 → framework configuration).
- Verification evidence MUST include the documentation site build and validation passing, and a recorded WCAG AA contrast check (an enumerated table of foreground-background pairs with measured ratios) covering link text, body text, the non-text blue accent, the keyboard focus ring, and red punctuation, in both light and dark mode — confirming each pair meets its threshold (4.5:1 text / 3:1 large / 3:1 non-text) and that red appears only in a passing pattern.
- Deferred work MUST name the follow-up spec: per-component restyle (DOC-016), performance/Lighthouse budget (DOC-017), verbal-voice/tone system (DOC-019), and custom domain / base-path cutover (DOC-012).

### Key Entities *(include if feature involves data)*

- **Brand color token set**: The named brand colors (brand red, brand blue, AA-safe darker blue, warm-neutral base/surfaces, neutral text scale) and their mapping to site accent, link, surface, and theme-color roles for light and dark mode.
- **Brand typeface set**: The display, body, and monospace typefaces, the specific shipped weights, and their role assignment (headings/nav, body/UI, code).
- **Brand logo assets**: The light and dark wordmark variants (header), the logomark/icon (hero image), and the favicon/browser-icon set derived from the mark.
- **Landing page content**: The hero headline, tagline/value-prop body, primary and secondary CTA targets, and the ~3 value-prop card titles and blurbs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time visitor landing on the documentation home route can identify what the plugin is and where to start within the first screen (no scrolling) — on both desktop and narrow (mobile-width) viewports — via the above-the-fold element set defined in FR-001a (logo/mark, benefit headline, short value-prop, and primary call-to-action). The primary call-to-action is clearly distinguished from the secondary by carrying greater visual weight per the CTA-hierarchy rule in FR-003a (primary dominant/filled, secondary subordinate), so "clearly distinguished" is verified against that precedence rule rather than by judgment.
- **SC-002**: 100% of documentation routes display the brand accent on links/active navigation, the brand typefaces in headings/body/code, the brand wordmark in the header, and the brand favicon in the browser tab, in both light and dark mode.
- **SC-003**: 100% of brand-accent text and interactive elements meet or exceed the WCAG AA contrast ratio in both light and dark mode, verified against an enumerated set of foreground-background pairs (link text, body text, non-text blue accent, focus ring, and red punctuation) each recorded with its measured ratio and threshold (4.5:1 text / 3:1 large / 3:1 non-text), so the check is reproducible rather than judgment-based. Red punctuation is verified to appear only in a passing pattern (white-on-red CTA fill, large/non-text accent, or logo-mark logotype) and never as failing normal-size red text.
- **SC-004**: In dark mode, the primary reading surface is a soft dark-gray within the documented `#121212`–`#1e1e1e` range (target `#1a1a1a`), and true black (`#0a0a0a`) is not used as the reading background on any route — it appears only on the decorative hero block.
- **SC-005**: Body text remains visible throughout font loading (no invisible-text flash), and only the lean weight set (display regular+bold, body regular+semibold, monospace regular) is shipped — exactly five woff2 faces, no uncompressed/legacy format, served locally with no external font-host request, and with only the two critical above-the-fold faces (Space Grotesk 700 + Geist 400) preloaded (the other three faces are not preloaded).
- **SC-006**: The landing primary call-to-action resolves to the getting-started / first-workflow tutorial and the secondary call-to-action resolves to the project GitHub repository, with no broken links.
- **SC-007**: The implemented change stays within the declared reviewability budget (~80 reviewable CSS lines; 1–2 primary production files; 6–8 total text/config files plus binary assets) and introduces no scope from the named out-of-scope follow-up specs.
- **SC-008**: The documentation site build and validation pass after the change, and entrance animations (if any) are suppressed under a reduced-motion preference.

## Assumptions

- The exact brand values (color hex values, typeface weights, logo viewboxes, favicon set, theme color, and background color) are those captured in the feature's `brand-guide.md`; where the guide is ambiguous, the live `landing-page/website` source CSS is authoritative and is re-checked before porting.
- The source brand assets (the lean woff2 weight set and the wordmark/mark SVGs) already exist in the sibling `landing-page/website` project and are ported into the documentation site rather than re-created.
- The landing route is built with the documentation framework's native splash/hero/card capabilities (no bespoke custom page components), consistent with the keep-it-simple principle and the reviewability budget.
- The getting-started / first-workflow tutorial target for the primary CTA is the existing first-run / getting-started route in the documentation site.
- Final hero copy (headline, tagline, and the ~3 card titles/blurbs) is authored during this feature against the brand guide's verbal-tone reference; the direction (plain-English, anti-hype value prop for spec-driven development) is fixed, the exact wording is produced here.
- The optional lab grid/dot texture from the brand guide is omitted from the documentation landing unless the page reads as visually plain during implementation.
- Out of scope and deferred to named follow-up specs: per-component accessibility restyle beyond tokens (DOC-016), performance budget / Lighthouse CI (DOC-017), verbal-voice / tone system (DOC-019), and custom domain / base-path cutover (DOC-012).
- The site currently has a minimal `public/` directory containing only a `robots.txt`; brand assets (fonts, favicons) are added alongside it without disturbing existing files.
