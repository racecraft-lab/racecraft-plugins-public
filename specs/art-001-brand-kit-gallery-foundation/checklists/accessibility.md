# Accessibility Requirements Quality Checklist: Artifact Brand Kit & Gallery Foundation

**Purpose**: Validate that the accessibility requirements in `spec.md` and
`plan.md` (read together with `research.md`, `data-model.md`, `quickstart.md`,
and both `contracts/` files) are complete, unambiguous, internally consistent,
and objectively verifiable — before any template port inherits them.
**Created**: 2026-07-28
**Feature**: [spec.md](../spec.md)

**Depth**: formal release gate. **Audience**: PR reviewer.

**Why this domain carries unusual weight here**: the brand token block and the
theme-toggle block are embedded *verbatim* into all 21 planned artifacts
(FR-002, FR-003). A defect specified into either block reaches every template
with no per-template remedy, so items touching those two blocks are treated as
blocking rather than advisory.

**Contrast method**: every ratio quoted below was recomputed from the token hex
values using the WCAG 2.x relative-luminance and contrast-ratio formulas, not
copied from the artifacts under review. Ratios are unrounded to two decimals.
The method was cross-checked against an independently recorded figure in
`docs-site/src/styles/brand.css` (3.30:1 for `#3c89c6` on `#f1f0ec`) and agrees.

## Palette Contrast — Completeness of the Per-Theme Audit

- [x] CHK001 - Is the audit stated as covering both themes independently rather than inferring one from the other? [Completeness] [Spec §FR-005] **Pass** — FR-005 requires the two themes audited independently, and now also symmetrically.
- [x] CHK002 - Is the dark-theme audit table complete for every token the light table audits? The light table carries a `--rc-brand-red` row; the dark table has none, so the token is unaudited in dark. Recomputed, `#dc143c` on the four dark surfaces measures 3.49 / **2.94** / 3.69 / 3.34 — the pairing with `--rc-surface-raised` `#1F2937` falls **below the 3:1 non-text floor**, so the omission conceals a real failure. [Gap → Resolved] [Spec §FR-005; data-model.md "Dark theme"] **Resolved:** `data-model.md` dark table now carries the `--rc-brand-red` row (3.34–3.69 on surface/sunken/muted) and prohibits the raised pairing at 2.94, naming `--rc-danger-text` (5.38) as the replacement. FR-005 now requires the audit be symmetric across themes, so an absent row is a defect rather than an implied pass. Recorded in research.md R13. **Superseded by research.md R14:** the prohibition no longer exists. The dark raised surface was itself the cause — `#1F2937`, borrowed from the upstream navigation background — and it is now the neutral `#242424`, against which brand red measures 3.11. The dark table's `--rc-brand-red` row reads 3.11–3.69 across all four surfaces with no exception. The finding this item raised stands; only its resolution changed.
- [x] CHK003 - Is `--rc-border-strong` audited against every surface it may pair with? The table records one value ("3.41 on `--rc-surface`") where every other row gives a four-surface range. Recomputed across all four light surfaces: 3.41 / 3.68 / 3.23 / **2.93** — the pairing with `--rc-surface-muted` `#E8E5DF` falls **below 3:1**, and this is the token designated to carry *every* boundary that conveys meaning. [Gap → Resolved] [Spec §FR-005; data-model.md "Audited AA contrast pairings"] **Resolved:** the token is re-valued to `#847F72`, which clears 3:1 on all four light surfaces (3.18–3.99); prohibition was rejected because this token exists to carry meaningful boundaries and a per-surface ban would trap the author it serves. Dark `#6B7280` re-measured and stands (3.04–3.81, later 3.21–3.81 once research.md R14 corrected the dark raised surface, which had been holding this token to the tightest ratio in the kit). FR-005 now requires every token be measured against every surface it may pair with. **Superseded by research.md R15:** the light darkening is reverted. The cause was the muted surface, not the token — this item and CHK004 had each hit `#E8E5DF` independently without noticing they shared one cause. With muted corrected to `#EDEBE6`, the original brand value `#8A8578` clears 3:1 on all four light surfaces (3.09–3.68) and is restored.
- [x] CHK004 - Are the two already-resolved failures numerically correct as recorded? Recomputed: `--rc-accent` `#3C89C6` on `#E8E5DF` = **2.99**; `--rc-border-subtle` `#E0DED9` on `#F7F6F4` = **1.24**. Both match exactly. **Pass.** [Spec §FR-005; research.md R8] **Superseded by research.md R15:** the accent figure was arithmetically correct, but its resolution was not the cheapest available. `#E8E5DF` was itself one step too dark; corrected to `#EDEBE6` the accent reaches 3.16 and the prohibition is removed. The `--rc-border-subtle` figure stands at 1.24 and remains decorative-only by design.
- [x] CHK005 - Is that resolution *completely* specified, or does a requirement still assert something the accepted design knowingly violates? FR-005 states that **every** pairing the kit defines MUST meet AA, while the accepted resolution deliberately retains two pairings that do not and governs them by usage rules instead. The requirement admits no such category, so the fix and the requirement contradict each other. [Gap → Resolved] [Conflict] [Spec §FR-005 vs. data-model.md constraints 1–2] **Resolved:** FR-005 rewritten. The obligation now applies to pairings the kit **permits**, and any pairing below its threshold MUST be explicitly prohibited by a usage rule naming the replacement token; a pairing that neither passes nor carries a rule is a defect. SC-007 updated to match.
- [x] CHK006 - Is every token whose ratio the audit asserts actually assigned a value in the artifacts? `--rc-border-subtle` is credited with "1.69 (dark)" but its dark hex appears nowhere, so that figure cannot be independently checked. [Gap → Resolved] [data-model.md constraint 2] **Resolved:** dark `--rc-border-subtle` is defined as `#404040` and the range recomputed to 1.42–1.78, replacing the unreproducible 1.69. FR-005 now requires every token the audit names to have a defined value in both themes. A rounding error was also corrected (`--rc-danger-text` light maximum is 6.07, not 6.05).
- [x] CHK007 - Is "large text" defined, given that two tokens (`--rc-accent`, `--rc-brand-red`) are permitted **only** at large-text and non-text sizes? Without the threshold a port cannot objectively decide whether a given use is permitted. [Gap → Resolved] [Spec §SC-007] **Resolved:** FR-005 defines large text as at least 24px, or 18.66px when bold, and states both thresholds numerically (4.5:1 normal, 3:1 large and non-text) with the governing criteria named.
- [x] CHK008 - Are the contrast thresholds stated numerically rather than as a bare conformance level? [Clarity] [Spec §SC-007] **Now yes** — FR-005 states 4.5:1 normal / 3:1 large and non-text with the governing criteria named, rather than the bare level.
- [x] CHK009 - Is the audit's authority location unambiguous — one table restated in the shipped kit, rather than two independently editable copies? [Consistency] [data-model.md; plan.md §Implementation Sequence step 1] **Pass** — one table in `data-model.md`, restated in the shipped `brand-kit.css` comment; plan step 1 keeps it above the start marker so ports do not embed it.

## Use of Color — the Brand-Red "Punctuation-Only" Rule

- [x] CHK010 - Is the brand-red rule specified in a form that constrains *meaning*, not only *quantity* and *contrast*? The artifacts reserve red for "punctuation-level emphasis" and bind it to non-text and large-text roles — a frequency constraint and a contrast constraint. Nothing states that red must not be the sole visual means of conveying information, indicating an action, or distinguishing an element, and no redundant non-color cue is required anywhere. The strings "sole", "color alone", and "use of color" appear zero times across the feature. [Gap → Resolved] [Spec §FR-001] **Resolved:** FR-021 added. Brand red may not be the sole visual means of conveying information, indicating an action, prompting a response, or distinguishing an element; meaning carried by red must also be available without color. FR-021 states explicitly that the punctuation-level reservation is a quantity rule that does not by itself satisfy this, and that the two must be documented as distinct.
- [x] CHK011 - Is the distinction between the contrast obligation and the use-of-color obligation drawn, so that clearing a ratio is not mistaken for satisfying both? [Clarity] [Spec §FR-001, §SC-007] **Now yes** — FR-021 states that the punctuation rule and the use-of-color rule are distinct and that neither discharges the other.
- [x] CHK012 - Is a separate AA-body-safe red specified for the case where red is used as body copy, so the punctuation rule does not silently push authors into a failing pairing? **Pass** — `--rc-danger-text` covers it at 4.82–6.07 light and 5.38–6.75 dark (recomputed). [Completeness] [data-model.md §Entity 4]

## Theme Toggle — Keyboard, Name, Role, State

*This block ships verbatim into all 21 artifacts. Findings here are blocking.*

- [x] CHK013 - Are keyboard-operability requirements defined for the theme control? A search of the whole feature returns **zero** occurrences of "keyboard", "tabindex", "assistive", or "screen reader". Story 3 and SC-005 say only that the reviewer "activates" the control, which does not distinguish pointer from keyboard. [Gap → Resolved] [Spec §FR-003, §FR-004, US3-AS2] **Resolved:** FR-022 added — the control must be keyboard reachable in normal focus order and activatable without a pointer. SC-010 makes it measurable; quickstart M7 gives it a manual verification path.
- [x] CHK014 - Are the control's name, role, and state required to be programmatically determinable — an accessible name, a control role, and an exposed indication of which theme is active? "aria", "role", and "accessible name" appear **zero** times across the feature, so nothing obliges the shared snippet to expose any of them, and nothing fixes the semantic element so each port would inherit it. [Gap → Resolved] [Spec §FR-003, §FR-004] **Resolved:** FR-022 requires a programmatically determinable name, role, and current state, fixed in the canonical snippet rather than left to ports. `data-model.md` Entity 5 now carries the per-obligation table, including that the state must change between positions and that a glyph-only state cue fails under FR-021. Check I4 asserts the constructs are inside the copied region; M8 verifies behavior.
- [x] CHK015 - Is the propagation risk itself acknowledged in the requirements — that a defect in this one snippet reaches every artifact with no per-template remedy? [Completeness] [Spec §FR-003; plan.md §Risks] **Now yes** — FR-022 states the constraint is fixed in the canonical snippet because it reaches all artifacts, and plan.md carries a matching risk row.
- [x] CHK016 - Is the storage-unavailable path specified as a *silent* degradation with no surfaced error, rather than merely "best effort"? **Pass.** [Clarity] [Spec §FR-004, US3-AS3]
- [x] CHK017 - Is the first-paint ordering requirement (theme applied before body parse, no flash) placed in the shared snippet rather than left to each port? **Pass.** [Consistency] [research.md R7; plan.md §Risks]

## Rendering Over `file://` — Origin-Dependent Assumptions

- [x] CHK018 - Are the requirements explicit that `localStorage` may **throw** on a local-file document rather than merely return empty, so the specified handling covers the throwing case? **Pass** — recorded in research.md R7 and carried by US3-AS3. [Clarity] [Spec §FR-004]
- [x] CHK019 - Is the theme override required to remain effective for the session when storage is refused, so refusal degrades persistence only and not the feature? **Pass.** [Completeness] [Spec §FR-004, US3-AS3]
- [x] CHK020 - Are the browser-observable outcomes the automated suite cannot assert enumerated with an evidence expectation rather than assumed? **Pass.** [Traceability] [quickstart.md §8; contracts/gallery-validation-contract.md "Not validated"]
- [x] CHK021 - Do the requirements cover native UI surfaces (form-control widgets, scrollbars, default canvas) under a **manual** theme override? `color-scheme: light dark` is specified "so form controls and scrollbars follow", but that declaration tracks the user/OS preference — it does not track an in-page `data-theme` override, so a reviewer who forces the opposite theme gets page tokens from one theme and native widgets from the other. [Gap → Resolved] [data-model.md §Entity 4] **Resolved:** FR-004 extended — native form controls, scrollbars, and the default canvas must follow the **chosen** theme. The requirement states explicitly that declaring support for both schemes is insufficient because it resolves against the OS preference, and that the scheme must be set per override direction. Check I3 asserts both overrides are present; M10 verifies.
- [x] CHK022 - Is honoring both `data-theme` directions (not only the dark override) stated, so a dark-OS reviewer can reach the light rendering? **Pass** — research.md R7 requires both. [Completeness]

## Typography Fallback — Offline Readability

- [x] CHK023 - Is the mechanism guaranteeing text is never invisible while fonts load specified precisely enough to implement and check? The artifacts say fonts are "loaded as linked web fonts with swap behavior", but for a hosted font stylesheet the swap behavior is controlled by a parameter on the font request; omit it and the served stylesheet defaults to a blocking behavior with an invisible-text period — exactly what the Edge Case forbids. No requirement pins that parameter, and the external-reference scanner checks hosts only, never the request itself. [Gap → Resolved] [Spec §FR-001, §SC-006, Edge Cases] **Resolved:** FR-024 added, making the font request parameter itself the requirement and mandating automated enforcement. Check E4 added. Verified first-hand against the live endpoint: the request without the display parameter returns a stylesheet containing zero `font-display` declarations; with it, every `@font-face` carries `font-display: swap`.
- [x] CHK024 - Are the fallback stacks themselves specified, and is it stated what carries hierarchy when the brand faces are absent? Nothing names the fallbacks, so nothing stops the display and body stacks resolving to the same face offline — the outcome the in-repo precedent already produces, where both collapse to `system-ui`. SC-006's claim that "the only observable difference is typeface substitution" is unreconciled with that collapse. [Gap → Resolved] [Ambiguity] [Spec §FR-001, §SC-006; data-model.md §Entity 4] **Resolved:** FR-024 requires each role's fallback stack be distinguishable from the others', and requires the spec to state what carries the distinction where two roles would otherwise resolve to the same face. `data-model.md` records that hierarchy rides on semantic level, size, and weight rather than typeface identity, which is what makes SC-006's claim true rather than aspirational. SC-011 added.
- [x] CHK025 - Is offline readability stated as a requirement on all content and controls rather than on text alone? [Coverage] [Spec §SC-006, US3-AS4] **Pass** — US3-AS4 covers all content, layout, and behavior, not text alone.

## Focus Visibility and Reduced Motion

- [x] CHK026 - Is there a requirement that interactive elements actually *receive* a visible focus indicator, and that its contrast obligation holds against the surfaces it appears on? FR-001 requires the token set to *cover* "focus-visible treatment"; nothing requires an artifact to apply it or forbids suppressing it, and the contrast obligation exists only as two numbers in a design artifact. The chosen ring color is itself sound — recomputed at 5.37 / 5.80 / 5.09 / 4.61 light and 7.75 / 6.54 / 8.20 / 7.42 dark, clearing 3:1 everywhere — so what is missing is the requirement, not the value. [Gap → Resolved] [Spec §FR-001; data-model.md "Focus ring"] **Resolved:** FR-023 requires every interactive element to carry the focus-visible treatment and prohibits suppressing it without an equivalent replacement, and puts the indicator's own contrast under FR-005's audit. Check I2 asserts the rule is inside the copied region.
- [x] CHK027 - Is "reduced-motion handling" defined with observable behavior and given a verification path? It is named as a token-family member and raised as an Edge Case, but no success criterion or acceptance scenario references it, and the manual scenario table — which exists precisely because the suite drives no browser — has no reduced-motion row. [Gap → Resolved] [Coverage] [Spec §FR-001, §Edge Cases; quickstart.md §8] **Resolved:** FR-023 defines the behavior (animation, transition, and smooth-scroll reduced to effectively instant, explicitly including the cross-theme transition) and requires a named manual scenario. Quickstart M9 added; check I1 asserts the at-rule is inside the copied region. Assumptions record honestly that this is above the AA floor — the nearest criterion, 2.3.3, is AAA.
- [x] CHK028 - Is the theme *switch* itself covered by the motion rule, given that a cross-theme color transition is the most likely animation in the shared kit? [Coverage] [Spec §FR-001] **Now yes** — FR-023 names the cross-theme transition explicitly as covered.

## Attribution Headers (FR-020) — Structural Interference

- [x] CHK029 - Do the attribution headers carry any accessibility obligation? They are specified as HTML comments; comment nodes are not rendered and are not exposed to the accessibility tree, so they impose no naming, ordering, or alternative-text duty. **Pass — no gap; the design is correct as written.** [Spec §FR-020]
- [x] CHK030 - Do the attribution headers risk interfering with document structure? They are required "near the top of the file", which does not pin them relative to the doctype. [Spec §FR-020] **Pass, no change needed** — verified against the HTML Standard's "initial" insertion mode: a comment token before the DOCTYPE is inserted as a Document child and parsing continues, so the following DOCTYPE is still processed and no quirks-mode switch occurs. A leading attribution comment is harmless in any browser implementing the current parsing algorithm; only legacy IE behaved otherwise. "Near the top" therefore needs no further constraint.
- [x] CHK031 - Is the attribution requirement mechanically checkable rather than reliant on reviewer judgment? **Pass** — check group G enumerates each required element. [Measurability] [contracts/gallery-validation-contract.md Group G]

## Inheritance — What the Contract Passes to the Port Specs

- [x] CHK032 - Does the enumerated content of the single-file contract include the accessibility obligations every artifact must meet? FR-010's list covers inline-ness, filesystem rendering, catalog shape, trigger forms, routing, and signal meanings — and no accessibility duty at all. The contract is the one place an obligation reaches all four port specs; anything absent from it is re-litigated per port, or lost. [Gap → Resolved] [Spec §FR-010] **Resolved:** FR-010's enumerated contract content now includes the accessibility obligations every artifact inherits, each cross-referenced to its requirement, with the reason stated — the contract is the only place an obligation reaches all four port specs at once.
- [x] CHK033 - Is the accessibility surface traceable — does the coverage map route each accessibility requirement to a verification path, automated or named-manual? [Traceability] [quickstart.md §"Requirement coverage map"] **Now yes** — the coverage map routes FR-021 through FR-024 and SC-010/SC-011 to checks E4/I1–I4 and manual scenarios M7–M12.
- [x] CHK034 - Are the applicable conformance criteria identified specifically enough to check, rather than by conformance *level* alone? "WCAG AA" appears as a level throughout; no success criterion is named by number anywhere in the feature. [Clarity] [Spec §FR-005, §SC-007] **Now yes** — Assumptions enumerates the governing criteria by number and level (1.4.1 A, 1.4.3 AA, 1.4.11 AA, 2.1.1 A, 2.4.7 AA, 4.1.2 A) and records that reduced motion is above the AA floor.

## Second-pass result

Re-evaluated after remediation. **34 items, 14 gaps found, 14 resolved, 0
remaining.** Every item carrying a gap marker on the first pass now records what
closed it and against which artifact; items resolved by an edit are tagged
`[Gap → Resolved]` so the original finding stays legible rather than being
overwritten.

Artifacts edited to close the 14: `spec.md` (FR-004, FR-005, FR-010 amended;
FR-021–FR-024 and SC-010/SC-011 added; SC-007 and Assumptions updated),
`data-model.md` (both audit tables completed and recomputed, two token values
changed, Entity 4 and Entity 5 extended), `plan.md` (risks, reviewability
arithmetic, implementation sequence), `research.md` (R13 added, R8 amended),
`quickstart.md` (M7–M12, coverage map), and
`contracts/gallery-validation-contract.md` (check E4, check group I, manual
inventory).

Two of the 14 were latent **contrast failures**, not merely documentation gaps:
brand red at 2.94 on the dark raised surface, and the meaningful-boundary border
at 2.93 on the light muted surface. Both sat in a pairing the original audit
never measured. Both are now resolved and recorded.

The first was initially resolved by prohibiting the pairing. That was later
superseded (research R14): the dark raised surface was itself the cause — a
blue-grey borrowed from the upstream navigation background — and correcting it to
a neutral `#242424` lifted every dark foreground at once, including the
meaningful-boundary token from 3.04 to 3.21. Brand red now carries no
prohibition in either theme.

## Notes

- An item tagged with the gap marker indicates a missing, imprecise, or
  self-contradicting **requirement** — not an implementation defect.
- Blocking set: CHK002, CHK003, CHK005, CHK010, CHK013, CHK014, CHK021, CHK023,
  CHK032. Each either conceals a computed contrast failure, omits an obligation
  from a block copied verbatim into 21 artifacts, or leaves a requirement
  asserting something the accepted design knowingly violates.
- CHK004, CHK012, CHK016–CHK020, CHK022, CHK029, and CHK031 are recorded
  **passes**, kept in the list because each was raised as an explicit review
  question and a silent omission would read as an unexamined item.
