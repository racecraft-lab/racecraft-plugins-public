# Accessibility Checklist: Brand identity and marketplace landing page

**Purpose**: Validate that the accessibility requirements (WCAG AA contrast, dark-mode surfaces, logo/image semantics, reduced-motion, font-loading) are complete, clear, measurable, and consistent — before implementation. Unit tests for the requirements, not the implementation.
**Created**: 2026-06-23
**Feature**: [spec.md](../spec.md)

## Requirement Completeness — Contrast

- [ ] CHK001 - Are the numeric WCAG AA contrast thresholds (4.5:1 normal text, 3:1 large text, 3:1 non-text/UI) stated in the spec's testable requirements rather than only the word "AA"? [Clarity, Spec §FR-014]
- [ ] CHK002 - Is the AA-safe darker blue for link-sized text defined with a measurable target ratio against its background in BOTH light and dark mode? [Measurability, Spec §FR-006]
- [ ] CHK003 - Are the non-text accent (focus ring / active-nav block) contrast requirements separated from text-link contrast requirements, each with the correct threshold (3:1 non-text vs 4.5:1 text)? [Completeness, Spec §FR-005]
- [x] CHK004 - Are contrast requirements for brand red `#dc143c` used as punctuation (logo mark, hero CTA) against its specific backgrounds (warm base `#f1f0ec`, true-black hero block) defined? [Resolved → Spec §FR-005a: records `#dc143c` = 4.38:1 on `#f1f0ec` and 3.97:1 on `#0a0a0a` (both fail AA normal text), permits red only as white-on-red CTA fill (4.99:1), large/non-text accent (≥3:1), or logo-mark logotype exception]
- [x] CHK005 - Is the contrast obligation for the hero primary-CTA label (red treatment) specified, or only for body/link text? [Resolved → Spec §FR-005a: CTA label contrast obligation applies to the rendered label/background pair (white-on-red fill 4.99:1 AA-pass)]
- [x] CHK006 - Are large-text vs normal-text contrast distinctions defined for headings rendered in the display typeface (so 3:1 large-text relief is applied only where the size/weight qualifies)? [Resolved → Spec §FR-006: large text defined as ≥24px regular / ≥18.66px (14pt) bold at the 3:1 threshold, distinct from 4.5:1 normal text]

## Requirement Completeness — Dark Mode Surfaces

- [ ] CHK007 - Is the "soft dark-gray" reading-surface range that SC-004 calls "the documented soft-dark range" actually documented with concrete bounds (e.g. `#121212`–`#1e1e1e`) in the spec? [Clarity, Spec §SC-004]
- [ ] CHK008 - Is the single sanctioned use of true black scoped unambiguously to the decorative hero block only, with a requirement that no reading surface on any route uses true black? [Consistency, Spec §FR-013]
- [ ] CHK009 - Is the halation/eye-strain rationale for avoiding pure-black reading surfaces captured so the soft-dark requirement is not mistaken for an arbitrary aesthetic choice? [Completeness]
- [ ] CHK010 - Are dark-mode body and heading foreground colors required to be near-white (not pure `#ffffff` body) to avoid excessive contrast on the soft-dark surface, or is this left unspecified? [Coverage]

## Requirement Completeness — Logo, Image & Link Semantics

- [ ] CHK011 - Is an accessible text name for the site preserved when the wordmark image replaces the plain-text title (so assistive tech still announces the site)? [Completeness, Spec §FR-009]
- [ ] CHK012 - Is the header logo required to remain a functional home link with an accessible name? [Completeness, Spec §FR-009]
- [x] CHK013 - Is alternative text (alt) required for the hero logomark image so screen-reader users receive an equivalent, and is its decorative-vs-informative role decided? [Resolved → Spec §FR-010: hero `hero.image` `alt` required; decorative-vs-informative role decided explicitly (empty alt if redundant beside headline, else meaningful brand name; never unset/auto)]
- [ ] CHK014 - Are the correct light/dark wordmark and hero-image variants required per theme so the mark never renders same-color-on-same-color (invisible) against its background? [Consistency, Spec §FR-010]

## Requirement Completeness — Motion & Font Loading

- [ ] CHK015 - Is every entrance/hero animation required to honor `prefers-reduced-motion: reduce` by suppressing or reducing motion? [Coverage, Spec §FR-015]
- [ ] CHK016 - Is "no invisible-text flash during font load" specified via a swap behavior plus a system fallback stack so text is visible immediately? [Completeness, Spec §FR-008]
- [ ] CHK017 - Is the layout required to remain unbroken when the brand typefaces are unavailable (fallback metrics)? [Edge Case, Spec §Edge Cases]

## Requirement Completeness — Keyboard & Focus

- [x] CHK018 - Are visible keyboard-focus-indicator requirements (focus-visible) defined for all interactive elements (links, nav, the two CTAs), including the focus-indicator contrast threshold? [Resolved → Spec §FR-014a: visible focus indicator required (WCAG 2.2 SC 2.4.7) for links/nav/both CTAs at the 3:1 non-text threshold]
- [x] CHK019 - Is the focus indicator required to remain perceivable in both light and dark mode (e.g., the blue focus ring meets the 3:1 non-text threshold against each surface)? [Resolved → Spec §FR-014a: focus ring `#3c89c6` measured 3.30:1 on `#f1f0ec` and 4.63:1 on `#1a1a1a`, both ≥3:1 AA-pass; Acceptance Scenario US2.6 added]

## Requirement Clarity & Measurability

- [ ] CHK020 - Can SC-003 ("100% of brand-accent text and interactive elements meet or exceed WCAG AA") be objectively verified given the thresholds and the specific color pairs are enumerated somewhere authoritative? [Measurability, Spec §SC-003]
- [ ] CHK021 - Are the exact foreground/background color pairs that gate AA enumerated (link text, body text, non-text accent, red punctuation) so the contrast check is reproducible rather than judgment-based? [Clarity]
- [ ] CHK022 - Is the verification evidence requirement (a recorded WCAG AA contrast check in both modes) specified as a release-gate artifact in the PR packet? [Completeness, Spec §PR Review Packet]

## Requirement Consistency

- [ ] CHK023 - Do the contrast requirements stay consistent across spec FR-006/FR-014, SC-003, and the recorded token map (no conflicting ratios or colors)? [Consistency]
- [ ] CHK024 - Is the "red is punctuation, blue is the accent" rule stated consistently so red is never wired into the link/nav accent token while still being allowed on mark/theme-color/hero CTA? [Consistency, Spec §FR-005]
- [ ] CHK025 - Are light-mode and dark-mode accessibility obligations stated symmetrically (every text/interactive contrast, surface, and motion rule applies in both modes)? [Consistency, Spec §FR-012]

## Dependencies & Assumptions

- [ ] CHK026 - Is the assumption that brand hex values come from `brand-guide.md` (reconciled against the live source CSS when ambiguous) documented so AA-relevant values are traceable? [Assumption, Spec §Assumptions]
- [ ] CHK027 - Is the dark-hero logomark legibility check (the `#111827` mark on the `#0a0a0a` hero block) captured as an explicit acceptance/verification item rather than an unstated risk? [Coverage, Gap]

## Notes

- This checklist tests requirement quality (completeness/clarity/consistency/measurability), not implementation behavior.
- Gap-tagged items flag accessibility requirements that were missing or under-specified in spec.md / plan.md; all such items in this checklist were remediated and are now marked Resolved with a citation to the new requirement.
