# Performance Checklist: Brand identity and marketplace landing page

**Purpose**: Validate that the font-payload-hygiene requirements (lean self-hosted weight set, woff2 format, `font-display: swap`, preload-only-critical, no external font host, no invisible-text flash) are complete, clear, measurable, and consistent — before implementation. This is a LIGHT-TOUCH domain: it keeps the brand payload lean so it does not regress Core Web Vitals ahead of DOC-017, which owns any performance/Lighthouse budget. Unit tests for the requirements, not the implementation.
**Created**: 2026-06-23
**Feature**: [spec.md](../spec.md)

**Scope boundary**: A performance/Lighthouse budget, Core-Web-Vitals thresholds, and any CWV metric are explicitly OUT OF SCOPE for DOC-013 and owned by DOC-017 (Spec §FR-017, §SC-007). Items below test font-payload hygiene only; they MUST NOT introduce a perf budget or CWV threshold.

## Requirement Completeness — Lean Font Weight Set

- [ ] CHK001 - Is the exact shipped weight set enumerated (display 400+700, body 400+600, monospace 400) so "lean weight set actually used" is testable rather than vague? [Clarity, Spec §FR-007]
- [ ] CHK002 - Is it stated that the extra weights present in the brand source (Space Grotesk 300/500/600, Geist 500/700/800, Fira Code 500/600) are NOT shipped, so the lean-set requirement has an explicit exclusion boundary? [Completeness, Spec §FR-007]
- [ ] CHK003 - Is the per-family role-to-weight mapping (display=headings/nav, body=body/UI, mono=code) documented so the shipped weights are traceable to a use? [Traceability, Spec §FR-007]

## Requirement Completeness — Font Format & Self-Hosting

- [x] CHK004 - Is the required web-font file format (woff2 — the compressed web format) named in a normative requirement, rather than only in plan.md/research.md, so shipping an uncompressed/legacy format (ttf/woff) that bloats the payload is prohibited by the spec? [Resolved → Spec §FR-007 + §SC-005: each shipped face MUST be woff2 (modern, widest-support, best compression); uncompressed/legacy TTF/OTF/WOFF MUST NOT be shipped; SC-005 measures "exactly five woff2 faces, no uncompressed/legacy format." Grounded in web.dev Best-practices-for-fonts (use only WOFF2; self-hosting should apply WOFF2 compression)]
- [ ] CHK005 - Is "self-hosted with no dependency on an external font host" stated as a measurable requirement (no Google Fonts / no third-party font-CDN request at runtime) rather than an implied preference? [Completeness, Spec §FR-008]
- [ ] CHK006 - Is the no-external-font-host obligation also asserted as a measurable success outcome (no external font-host request), not only as a design constraint? [Measurability, Spec §SC-005]

## Requirement Completeness — Preload Scope (floor AND ceiling)

- [ ] CHK007 - Are the specific files to preload identified (display bold = Space Grotesk 700, body regular = Geist 400) so the critical-preload requirement is unambiguous? [Clarity, Spec §FR-008]
- [x] CHK008 - Does the spec constrain preloading to ONLY the two critical above-the-fold files — i.e., is there an explicit ceiling forbidding the remaining three faces (Space Grotesk 400, Geist 600, Fira Code 400) from being preloaded — so over-preloading (every preload competes with other critical resources for bandwidth) is prohibited, not merely the floor (these two MUST be preloaded)? [Resolved → Spec §FR-008 + §SC-005: preloading MUST be limited to exactly the two critical faces (Space Grotesk 700 + Geist 400); the remaining three faces MUST NOT be preloaded because each preload contends for early bandwidth and over-preloading prioritizes everything (and therefore nothing); FR-008 also requires `crossorigin` on each preload. Grounded in web.dev preload-critical-assets / optimize-web-fonts (avoid preloading too many; if too many are prioritized, effectively none are; specify crossorigin even for self-hosted fonts)]
- [ ] CHK009 - Is the rationale for preloading only above-the-fold fonts (preloaded fonts contend for early bandwidth; over-preloading delays other critical resources) captured so the preload-only-critical rule is not mistaken for an arbitrary limit? [Completeness]

## Requirement Completeness — Font-Display & Fallback (no invisible text)

- [ ] CHK010 - Is `font-display: swap` required for every `@font-face` (all five faces), not only the preloaded pair, so no face can introduce an invisible-text period? [Coverage, Spec §FR-008]
- [ ] CHK011 - Is "body text remains visible during font load via a system fallback stack" stated so the swap behavior is tied to an immediate-visibility outcome (no FOIT / invisible-text flash)? [Completeness, Spec §FR-008]
- [ ] CHK012 - Is a system-font fallback required to lead each font stack (e.g. `system-ui` before the brand family) so text renders immediately if a brand face fails to load? [Coverage, Spec §Edge Cases]
- [ ] CHK013 - Is the layout required to remain unbroken when the brand typefaces are unavailable (fallback does not break the layout)? [Edge Case, Spec §Edge Cases]

## Requirement Clarity & Measurability

- [ ] CHK014 - Can SC-005 ("only the lean weight set is shipped, served locally with no external font-host request") be objectively verified given the enumerated five files and the no-external-host rule? [Measurability, Spec §SC-005]
- [ ] CHK015 - Is the count of shipped font files bounded (exactly five woff2 faces) so "lean" is a checkable number rather than a judgment call? [Measurability, Spec §FR-007]

## Requirement Consistency

- [ ] CHK016 - Do the lean-weight-set requirements stay consistent across spec FR-007, FR-008, SC-005, and the research font-sourcing decision (same five files, same two preloads, all `swap`)? [Consistency]
- [ ] CHK017 - Is the preload set (Space Grotesk 700 + Geist 400) consistent between FR-008 and the plan/research, with no conflicting or additional preloaded faces? [Consistency, Spec §FR-008]

## Scope Boundary — Performance Budget Exclusion (DOC-017)

- [ ] CHK018 - Is a performance/Lighthouse budget and any Core-Web-Vitals threshold explicitly excluded from this slice and named as DOC-017, so font-payload hygiene is not conflated with a perf budget? [Consistency, Spec §FR-017]
- [ ] CHK019 - Does the spec keep all font-related requirements framed as payload hygiene (which/how many files, format, swap, preload-only-critical) WITHOUT asserting any timing/CWV/Lighthouse metric that belongs to DOC-017? [Boundary, Spec §SC-007]

## Dependencies & Assumptions

- [ ] CHK020 - Is the assumption that the lean woff2 set is ported verbatim from the sibling `landing-page/website` project (already subset, no new subsetting toolchain added) documented so the payload-size basis is traceable? [Assumption, Spec §Assumptions]
- [ ] CHK021 - Is the decision NOT to add a font-subsetting/build step (KISS / no new dependency) recorded so the lean-payload approach is justified rather than an unexplained omission? [Assumption]

## Notes

- This checklist tests requirement quality (completeness/clarity/consistency/measurability) for font-payload hygiene, not implementation behavior, and not a performance budget (DOC-017).
- Gap-tagged items flag font-payload-hygiene requirements that were missing or under-specified in spec.md / plan.md; remediated items are marked `[x]` with a `[Resolved → Spec §FR-XXX: …]` citation.
