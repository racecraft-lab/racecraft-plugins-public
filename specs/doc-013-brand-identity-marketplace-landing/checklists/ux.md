# UX Checklist: Brand identity and marketplace landing page

**Purpose**: Validate that the landing-page UX requirements (marketplace-entry-point framing, benefit-led headline, single primary call-to-action, ~3 scannable value cards, above-the-fold comprehension, narrow-viewport readability, and plain-English anti-hype tone) are complete, clear, measurable, and consistent — before implementation. Unit tests for the requirements, not the implementation.
**Created**: 2026-06-23
**Feature**: [spec.md](../spec.md)

## Requirement Completeness — Marketplace Entry-Point Framing

- [ ] CHK001 - Is the requirement that the home route render as a marketplace landing (splash layout) rather than a standard documentation article stated as a testable requirement, not only as narrative? [Completeness, Spec §FR-001]
- [ ] CHK002 - Are the mandatory hero elements (logo/mark, benefit headline, value-prop body, primary CTA, secondary CTA) each enumerated as required content rather than implied? [Completeness, Spec §FR-002]
- [ ] CHK003 - Is the value proposition required to communicate what the plugin is (spec-driven development) in plain language, distinct from a feature list? [Clarity, Spec §FR-002]

## Requirement Completeness — Call-to-Action Hierarchy

- [ ] CHK004 - Are the primary-CTA target (getting-started / first-workflow tutorial) and secondary-CTA target (project GitHub) each specified unambiguously? [Completeness, Spec §FR-003]
- [x] CHK005 - Is the constraint that the landing hero present exactly one primary call-to-action (and at most one secondary), with no additional competing CTAs in the hero, stated as a requirement? [Resolved → Spec §FR-003a: hero MUST present exactly one primary + at most one secondary CTA and MUST NOT introduce additional competing CTAs in the hero; grounded in NN/g/CXL decision-fatigue guidance]
- [x] CHK006 - Is the secondary CTA required to be visually subordinate to (not competing with) the primary CTA, with a measurable distinction rather than the word "distinguished"? [Resolved → Spec §FR-003a: secondary MUST be visually subordinate (primary filled/dominant, secondary lower-emphasis), with the framework's `hero.actions` `variant: 'primary' | 'secondary' | 'minimal'` named as the enforcing mechanism]
- [ ] CHK007 - Can "clearly distinguished primary call-to-action" (SC-001) be objectively verified, e.g., via a stated visual-precedence rule the primary must satisfy over the secondary? [Resolved → Spec §SC-001 now verifies "clearly distinguished" against the FR-003a precedence rule (primary dominant/filled, secondary subordinate) rather than by judgment]

## Requirement Completeness — Value-Prop Cards

- [x] CHK008 - Is the number of value-prop cards bounded with an acceptable range rather than only the soft word "approximately three"? [Resolved → Spec §FR-004: "three by default, and in all cases within the range of two to four"]
- [x] CHK009 - Are the value-prop cards required to be scannable (concise, benefit-led titles/blurbs) with criteria a reviewer can apply, not just "concise"? [Resolved → Spec §FR-004: each card MUST be scannable = short benefit-led title + brief plain-English blurb]
- [x] CHK010 - Is each card's content required to express a user benefit rather than an internal feature/jargon label? [Resolved → Spec §FR-004: each card MUST express a user-facing benefit rather than an internal feature label or jargon term]

## Requirement Clarity — Benefit-Led & Anti-Hype Tone

- [x] CHK011 - Is "benefit-led headline" defined with a measurable/testable criterion (a reader-facing outcome or value, not a feature or component name) so it can be objectively checked? [Resolved → Spec §FR-002: headline MUST state a reader-facing value/outcome ("what the reader gets"), NOT merely name the product/feature/component; grounded in CXL benefit-vs-feature guidance]
- [x] CHK012 - Is "plain-English, anti-hype" copy defined with objective acceptance criteria (e.g., banned marketing-hype/superlative patterns, no unexplained jargon) rather than left as an undefined adjective? [Resolved → Spec §FR-004a: anti-hype made testable = (a) no hype/unsubstantiated superlatives, (b) no unexplained internal jargon/acronyms, (c) concrete capability/outcome over fluff; anchored to brand-guide §6]
- [ ] CHK013 - Is the verbal-tone reference (brand guide §6: pragmatic, transparent, anti-hype) cited as the authoritative source the landing copy must satisfy, so the tone requirement is traceable? [Resolved → Spec §FR-004a now cites brand-guide §6 as the authoritative tone source the landing copy MUST satisfy (in addition to §Assumptions)]
- [ ] CHK014 - Is the boundary with the deferred verbal-voice system (DOC-019) stated so the tone requirement here is scoped to landing copy direction and not a full voice system? [Consistency, Spec §FR-004a / §FR-017 — FR-004a explicitly scopes itself to landing-copy direction and defers a full voice system to DOC-019]

## Requirement Completeness — Above-the-Fold Comprehension

- [x] CHK015 - Does the spec enumerate which elements must co-appear within the first screen (logo/mark, headline, value-prop, primary CTA) so "no scrolling" comprehension is testable rather than asserted? [Resolved → Spec §FR-001a: enumerates the above-the-fold set {logo/mark, benefit headline, short value-prop, primary CTA} that MUST appear before scrolling; secondary CTA MAY fall at/just below the fold]
- [x] CHK016 - Is above-the-fold comprehension required on narrow (mobile-width) viewports — where vertical space is tightest — and not only on desktop? [Resolved → Spec §FR-001a: the above-the-fold comprehension obligation MUST hold on narrow mobile-width viewports as well as desktop; SC-001 updated to state both]
- [ ] CHK017 - Can SC-001 ("identify what the plugin is and where to start within the first screen") be objectively verified given the above-the-fold element set is defined? [Resolved → Spec §SC-001 now references the FR-001a element set and requires it on desktop + mobile, making the check reproducible]

## Requirement Completeness — Narrow-Viewport Readability

- [ ] CHK018 - Are narrow-viewport requirements for the hero, value-prop cards, and CTAs (readable and operable, no horizontal scroll) stated for all three element groups? [Completeness, Spec §FR-004, §Edge Cases]
- [ ] CHK019 - Is the card layout's responsive behavior (cards reflow to a single column when horizontal space is insufficient) captured as an expectation rather than left implicit? [Coverage, Spec §Edge Cases]

## Requirement Consistency

- [ ] CHK020 - Are the landing-page UX requirements (FR-001–FR-004), the acceptance scenarios (US1 #1–#4), and the success criterion (SC-001) consistent on the same hero element set and CTA targets with no conflicts? [Consistency, Spec §FR-002]
- [ ] CHK021 - Is the "plain-English, anti-hype" direction stated consistently across FR-002, FR-004, and Assumptions (same meaning, no drift between "plain", "concise", and "anti-hype")? [Consistency, Spec §FR-004]
- [ ] CHK022 - Is the primary-CTA target consistent between the spec (getting-started / first-workflow tutorial), the plan, and the research-resolved slug (`/racecraft-plugins-public/first-run/`) with no divergence? [Consistency, Spec §FR-003]

## Dependencies & Assumptions

- [ ] CHK023 - Is the assumption that final hero copy (headline, tagline, ~3 card titles/blurbs) is authored during this feature — with direction fixed — documented so the tone/benefit requirements have a clear owner and phase? [Assumption, Spec §Assumptions]
- [ ] CHK024 - Is the dependency on the framework's native splash/hero/CardGrid landing capabilities (no bespoke components) documented so the marketplace-framing requirement is achievable within the reviewability budget? [Assumption, Spec §Assumptions]

## Notes

- This checklist tests requirement quality (completeness/clarity/consistency/measurability), not implementation behavior.
- Gap-tagged items flag UX requirements that were missing or under-specified in spec.md / plan.md. After remediation, each such item is marked `[x]` with a `[Resolved → …]` citation to the new/updated requirement.
- Items without a Gap tag are quality references confirming an already-adequate requirement; they are not defects.
