# UAT Runbook: doc-013-brand-identity-marketplace-landing

| Field | Value |
|-------|-------|
| Spec | doc-013-brand-identity-marketplace-landing |
| Branch | doc-013-brand-identity-marketplace-landing |
| PR | **PR:** <set on PR open> |
| Generated from | 2026-06-24T03:11:08Z |



## Env Setup

You need Node 22 or later. If you use nvm, run `nvm use v22.22.2` first.

From the repository root, install dependencies and build the site:

```
pnpm --dir docs-site install
pnpm --dir docs-site build
pnpm --dir docs-site preview
```

Then open `http://localhost:4321/racecraft-plugins-public/` in your browser. Leave that tab open — every acceptance step below refers to it.

To run the full automated check (build + link validation + type check) in one pass: `pnpm --dir docs-site validate`.

## Per-Story Acceptance Tests

<a id="us-1"></a>
### User Story 1 - Branded marketplace landing page (Priority: P1)

**Goal:** confirm the home route looks like a product landing page, not a documentation article.

1. Open `http://localhost:4321/racecraft-plugins-public/` in your browser.
2. Look at what is visible before you scroll. You should see, all on the first screen without scrolling:
   - A logo or brand mark image (the Racecraft icon/mark).
   - A headline that states a reader benefit — something like "From spec to a reviewable pull request." It should NOT just name the product or a feature.
   - A short plain-English paragraph describing what the plugin does for you.
   - A primary call-to-action button. It should be the most visually prominent button on the screen and should be **red** (brand red, approximately `#dc143c`) with white text.
   - A secondary call-to-action (such as "View on GitHub") that is clearly less prominent — for example, shown as an outline or minimal button rather than a solid filled button.
3. Confirm there is NO standard documentation sidebar layout, no "On this page" navigation, and no documentation article heading. The page should feel like a splash/marketing page.
4. Click the primary call-to-action button. Confirm it takes you to a getting-started or first-workflow tutorial page within the docs site (not to an external site, not to a 404).
5. Return to the home route (`/racecraft-plugins-public/`). Click the secondary "View on GitHub" button. Confirm it opens the GitHub repository (`github.com/racecraft-lab/racecraft-plugins-public` or similar). Close that tab and return.
6. Scroll down past the hero area. You should see approximately three value-proposition cards (two to four is acceptable). Each card should have a short benefit-led title and a brief plain-English description. Read the card text: confirm it describes a user-facing benefit in plain language with no unexplained jargon, no superlatives such as "revolutionary" or "game-changing", and no marketing fluff.
7. Narrow your browser window to a mobile width (approximately 375–430 px wide, or use browser DevTools device emulation). Reload the page. Confirm:
   - The logo/mark, headline, value-prop text, and primary button are all still visible without horizontal scrolling.
   - Nothing is cut off or overflowing sideways.
   - The value-prop cards stack vertically and remain readable.

- [ ] All seven steps above passed. The landing page presents a branded hero layout with the mark, a benefit headline, plain-English value prop, a red primary CTA (→ getting-started tutorial), a subordinate secondary CTA (→ GitHub), approximately three plain-English value cards, and no horizontal scroll on mobile.

<a id="us-2"></a>
### User Story 2 - Consistent, accessible site-wide brand identity (Priority: P2)

**Goal:** confirm the Racecraft brand (colors, typefaces, logo, favicon) is applied consistently across all pages and both light/dark modes, with accessible contrast throughout.

**Colors and typefaces (light mode)**

1. From the home route, click into any interior documentation article (for example, the getting-started guide or any reference page).
2. Look at the links on the page. They should appear in a **blue** color (approximately `#2a6a99` in light mode) — not red, not gray, not the default browser blue.
3. Look at the active item in the left-hand navigation sidebar. Its highlight or underline should also be blue, not red.
4. Look at the page headings (H1, H2, H3). They should be set in a sans-serif display typeface called **Space Grotesk** — proportionally spaced, geometric, and noticeably different from a system font like Arial or Helvetica. (You can verify by right-clicking a heading → Inspect → checking the computed font-family, but visual confirmation is sufficient: does it look like a distinct branded typeface rather than the browser default?)
5. Look at the body paragraph text. It should be set in **Geist**, a clean sans-serif. Again, visual confirmation is sufficient: does it look like a distinct typeface rather than the browser default system font?
6. Find any code block or inline code snippet. It should appear in **Fira Code**, a monospace typeface with slightly styled characters (ligatures optional). Confirm it is not the browser default `Courier New` or `monospace`.
7. Look at the site header (top of the page). It should show the **Racecraft wordmark** (the word "Racecraft" in the brand style, with the red mark/icon), not a plain text title like "speckit-pro docs".
8. Look at the browser tab. The **favicon** should be a small Racecraft brand icon (the mark/icon), not a generic document icon or blank.

**Dark mode**

9. Find the light/dark mode toggle in the site header or sidebar and switch to **dark mode**.
10. Look at the main reading area background. It should be a **soft dark gray** — something like a very dark charcoal, noticeably lighter than true black. It should NOT look pitch-black (#000000 or pure black). (If you want to verify: inspect the background color; it should be in the range approximately `#121212`–`#1e1e1e`, target `#1a1a1a`.)
11. Look at the site header. The wordmark should now be the **white/light variant** — white text with the red mark — not the dark-text version that is readable on the light background.
12. Look at the body text. It should be a near-white color (approximately `#e6e6e6`), clearly legible against the soft dark background, but not blinding pure white.
13. Links should still appear blue — a lighter blue (approximately `#7cb3dd`) suitable for the dark background. Confirm they are still distinctly blue and clearly legible.
14. Verify the favicon is still visible in the browser tab in dark mode (some browsers show a light/dark favicon variant; at minimum the icon should remain visible).

**Toggle behavior**

15. Switch back to light mode. Confirm the wordmark switches back to the dark (black-text + red-mark) version with no unstyled flash or momentarily wrong variant.

**Keyboard focus**

16. Press Tab on your keyboard to move focus through the navigation links and buttons. Each focused element (link, button, nav item) should show a visible **blue focus ring** — a noticeable outline in approximately `#3c89c6`. Confirm the ring is clearly visible against both the light page background in light mode and the dark background in dark mode.

**Reduced motion**

17. In your operating system settings, enable "Reduce Motion" (on macOS: System Settings → Accessibility → Display → Reduce Motion; on Windows: System Settings → Accessibility → Visual effects → Animation effects off). Reload the page. If the landing page hero had any entrance animation (e.g. a fade-in), it should NOT play. The page should simply appear at rest.

- [ ] All steps above passed. Interior routes show blue links and active-nav, Space Grotesk headings, Geist body text, Fira Code in code blocks, the Racecraft wordmark in the header, and the brand favicon in the tab. Dark mode shows a soft dark-gray surface (not pure black), the white wordmark variant, near-white body text, and light-blue links. The light/dark toggle switches wordmark variants cleanly. Tab focus shows a visible blue ring. With Reduce Motion enabled, entrance animations do not play.



## FR Coverage Matrix

| Requirement | What it promises | Step that proves it |
|-------------|-----------------|---------------------|
| Landing splash layout (FR-001) | Home route renders as a hero layout, not a docs article | US1 step 3 |
| Above-the-fold comprehension (FR-001a) | Mark + headline + value-prop + primary CTA all visible before scrolling, on desktop and mobile | US1 steps 2 and 7 |
| Landing content set (FR-002) | Mark, benefit headline, plain-English value prop, primary CTA, secondary CTA all present | US1 steps 2 and 3 |
| CTA destinations (FR-003) | Primary CTA → getting-started tutorial; secondary CTA → GitHub | US1 steps 4 and 5 |
| CTA hierarchy (FR-003a) | Primary is dominant/filled (red); secondary is visually subordinate | US1 step 2 |
| Value-prop cards (FR-004) | 2–4 cards with benefit-led titles in plain language | US1 step 6 |
| Anti-hype copy (FR-004a) | No superlatives, no jargon, concrete benefit language | US1 step 6 |
| Blue links / red hero accent (FR-005) | Links and active-nav use blue; red limited to logo mark and hero primary button | US2 steps 2, 3, and 13 |
| Red contrast safety (FR-005a) | Red appears only as white-on-red CTA fill or in the logo mark, never as normal-size text | US1 step 2 (red button with white label); US2 steps 2 and 3 (links are blue, not red) |
| AA-safe link blue (FR-006) | Link blue meets WCAG AA against the page background in both modes | US2 step 2 (light mode blue links) and step 13 (dark mode blue links) |
| Brand typefaces (FR-007 / FR-008) | Space Grotesk headings, Geist body, Fira Code monospace; self-hosted, no external font request | US2 steps 4, 5, and 6 |
| Wordmark in header (FR-009) | Site header shows the Racecraft wordmark (not plain text) with correct light/dark variant | US2 steps 7 and 11 |
| Hero logomark (FR-010) | Logomark image shown in hero with correct light/dark variant | US1 step 2 |
| Favicon and theme color (FR-011) | Brand favicon visible in browser tab | US2 step 8 |
| Consistent across all routes (FR-012) | Brand applied to interior routes, not only the landing page | US2 steps 1–8 (performed on an interior route) |
| Soft dark-gray surface in dark mode (FR-013) | Dark mode reading surface is not pure black | US2 step 10; SC-004 |
| WCAG AA contrast (FR-014) | Text and interactive elements meet contrast thresholds in both modes | US2 steps 2, 12, 13, and 16 |
| Visible keyboard focus ring (FR-014a) | Focused elements show a visible blue ring in both modes | US2 step 16 |
| Reduced-motion (FR-015) | Entrance animations suppressed under reduced-motion preference | US2 step 17; SC-008 |
| Dark-mode surface range SC-004 | Soft dark reading surface (#121212–#1e1e1e), true black only on hero block | US2 step 10 |
| Contrast enumeration SC-003 | Foreground-background pairs meet thresholds (see PR verification evidence) | US2 steps 2, 12, 13, and 16 |
| Build and validation pass SC-008 | `pnpm --dir docs-site validate` exits 0 | Env Setup validation command |


## Negative-Path Tests

Try each of these to confirm the site handles edge cases safely:

- **Fonts blocked or slow to load**: In browser DevTools, go to the Network tab and block requests matching `/fonts/` (or throttle to "Slow 3G"). Reload the page. Body text should appear immediately using a system font fallback (no invisible or blank text while the brand fonts load). The layout should not collapse or overflow.

- **Wrong theme variant**: Switch to dark mode and look at the site header. The wordmark must be the white/light variant — if the dark-text wordmark appears on a dark background, it will be nearly invisible. Confirm it is NOT dark-text-on-dark-background. Then switch to light mode and confirm the dark-text wordmark returns — the white-text variant must NOT appear on the light background.

- **Reduced-motion preference**: Enable OS "Reduce Motion" as described in US2 step 17, then reload. Any hero entrance animation (fade-in, slide-up, etc.) must NOT play. The page should appear static.

- **Mobile viewport / no horizontal scroll**: Resize to approximately 375 px wide (or use DevTools device emulation for iPhone SE). Scroll only vertically. No content should require horizontal scrolling on the landing page or any interior documentation route.

- **Hype-check the copy**: Read every word visible on the landing page. If you see any of the following, that is a failure: "revolutionary", "game-changing", "effortless", "magical", "10x", "supercharge", "world-class", "AI-powered" used as a boast, or any term a first-time visitor would not know. The copy should be plain, concrete, and confidence-based — not breathless.

## Self-Review Findings

**Self-Review:** <not available — workflow file not provided>

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations
