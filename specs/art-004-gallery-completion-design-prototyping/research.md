# Research: ART-004 Gallery Completion - Design & Prototyping

## Decisions

### R1. Runtime and packaging

**Decision**: Build each artifact as one browser-native HTML file with inline CSS and JavaScript.

**Rationale**: Direct `file://` use, offline readability, no sibling assets, no build step, and no persistence are required. Local behavior in each file keeps the review surface understandable inside each ordered slice.

**Alternatives considered**: Shared runtime and framework builds were rejected because they violate the single-file/offline contract and add nonessential dependency surface.

### R2. Source reproducibility

**Decision**: Use pinned upstream commit `58c305be97f47b26b678f2c07dec01d4242268ec` for all six new ports.

**Rationale**: The recorded answer "Pin one commit" keeps attribution, source-size evidence, and reproduction stable.

**Alternatives considered**: Tracking upstream `main` was rejected as drift-prone. Vendoring upstream originals was rejected because the repo ships branded derivatives only.

### R3. Fidelity rule

**Decision**: Use "Functional fidelity": keep every distinct section, state, motion timing, decision surface, and interaction; compact only repeated sample groups allowed by the spec.

**Rationale**: The user-visible behavior is preserved without forcing literal sample volume through review gates.

**Alternatives considered**: Literal fidelity was rejected for repeated sample overhead. Minimal reinterpretation was rejected because it would drop required acceptance evidence.

### R4. Approved review topology

**Decision**: Preserve the original "One combined slice" as historical evidence, then execute the user's 2026-08-17 recovery approval: "approve three slices".

**Rationale**: The combined Plan gate blocked at 865 reviewable LOC and 9 production files. The recorded fallback was "Stop and split", and the approved split keeps fidelity and ART-020 ownership intact.

**Alternatives considered**: Reducing fidelity or removing ART-020 from ART-004 was rejected because both contradict recorded decisions.

### R5. Slice boundaries

**Decision**: Use three serial slices: keyboard foundation, read-only ports, and decision ports.

**Rationale**: Slice 1 lands the keyboard-scroll repair and guard first. Slice 2 ships four read-only ports without export logic. Slice 3 ships the two exportable decision artifacts. Shared manifest, test, payload, proof, and generated-doc paths are assigned serially and are not parallel-safe.

**Alternatives considered**: Seven one-template slices were safer but not the approved topology. Three equal LOC slices were rejected because the split must follow actual capability boundaries.

### R6. Export semantics

**Decision**: `visual-designs` exports "One direction" plus rationale. `component-variants` exports "Base variant" plus rationale while still showing all required component states.

**Rationale**: These are the only two decision artifacts. The durable output is the chosen conclusion, rationale, and live context.

**Alternatives considered**: Exporting all options or freeform notes was rejected because it does not produce one actionable conclusion.

### R7. ART-020 ownership

**Decision**: "Absorb ART-020" and "Mark superseded".

**Rationale**: ART-004 owns the five existing-container repairs, accessible names, global guard, negative fixture, UAT, and generated-artifact updates. ART-020 stays as provenance, not an execution path.

**Alternatives considered**: Running ART-020 separately or removing it from ART-004 was rejected by the recorded ownership and fallback decisions.

### R8. Verification and release

**Decision**: Use Layer 1/Layer 4 validation, manual `file://` UAT, `scripts/refresh-release-artifacts.py`, `pnpm --dir docs-site reference:generate`, and generated-artifact consistency checks.

**Rationale**: Authored gallery bytes affect source, dist payloads, installed-cache mirrors, proof JSON, release-readiness evidence, and generated docs reference pages. Generated files must be derived, not edited.

**Alternatives considered**: Browser automation inside the repository suite was rejected because the suite remains Python standard library only.

### R9. Read-only affordance adaptation

**Decision**: For artifacts whose manifest row declares `exports: []`, the Racecraft port preserves upstream informational content but omits active, disabled, or placeholder export/download controls. For `svg-illustrations`, preserve Queue, Retry, Fan-out/Fan-in, captions, palette rules, and inline SVG markup while omitting upstream `Download SVG` controls.

**Rationale**: The local gallery contract treats an empty export list as read-only behavior. Retaining upstream download buttons would contradict the catalog export declaration and create an unavailable-control UX in the read-only artifact.

**Alternatives considered**: Keeping active downloads was rejected because the manifest declares no exports. Keeping disabled download controls was rejected because a disabled export-looking control still implies unavailable export behavior in a read-only artifact.

### R10. Accessibility interaction semantics

**Decision**: Require every ART-004 interactive control to be keyboard operable,
visibly focused, free of traps, in logical source-order focus sequence, and
named with programmatic role/state/value semantics. Safari UAT must record
whether Tab or Option-Tab is the active route to webpage controls.

**Rationale**: The keyboard-scroll repair is insufficient if only the horizontal
containers are accessible. Decision controls, sliders, theme/background controls,
task/easing controls, reorder or linked-screen controls, copy buttons, fallback
textarea, and reset paths all affect review outcomes and therefore need the same
keyboard and semantic contract. Safari is called out because project roadmap
evidence identifies Safari keyboard reachability as the affected ART-020 failure
mode, and Apple's Safari documentation makes keyboard reachability dependent on
the active Tab/Option-Tab setting.

**Alternatives considered**: Limiting keyboard assertions to horizontal-scroll
containers was rejected because it would leave stateful controls outside the
manual UAT and PR evidence. Positive `tabindex` was rejected because the feature
requires source-order focus rather than custom focus ordering.

**Primary sources**: W3C/WAI WCAG 2.2 Understanding 2.1.1 Keyboard, 2.1.2 No
Keyboard Trap, 2.4.3 Focus Order, 2.4.7 Focus Visible, 3.3.2 Labels or
Instructions, and 4.1.2 Name, Role, Value; WHATWG HTML `tabindex`; Apple Safari
keyboard shortcuts and gestures; local `docs/ai/specs/html-artifacts-technical-roadmap.md`
ART-020 problem statement.

### R11. Accessible presentation, status, and motion

**Decision**: Treat the canonical ART-001 brand kit as the accessibility source
of truth for theme contrast, focus indicators, color-use rules, and
reduced-motion defaults, then require ART-004 to preserve those constraints in
both light and dark themes. Export feedback uses a polite atomic status region,
and color is never the only way to convey selected, active, invalid,
disabled/loading, drag insertion, SVG/palette, or theme/background meaning.

**Rationale**: ART-004 ports visual, component, animation, interaction, and SVG
artifacts; the accessible contract must cover visual meaning as well as input
mechanics. The audited gallery contract already records WCAG AA pairings and
reduced-motion behavior, so reusing that source avoids inventing per-artifact
color systems while keeping status and motion behavior measurable in UAT.

**Alternatives considered**: Per-port color overrides were rejected because they
would require new contrast evidence. Silent DOM-only status updates were
rejected because copy, invalid-input, fallback, and stale-attempt outcomes must
be perceivable without moving focus except when the fallback textarea is needed.

**Primary sources**: W3C/WAI WCAG Understanding 1.4.1 Use of Color, 1.4.3
Contrast Minimum, 1.4.11 Non-text Contrast, and 4.1.3 Status Messages; MDN
`prefers-reduced-motion`; local `speckit-pro/artifact-gallery/SPA-CONTRACT.md`
audited contrast, focus, color-use, and reduced-motion rules.

### R12. Clipboard refusal and stale fallback handling

**Decision**: Treat an unavailable Clipboard API, missing or non-callable
`writeText`, synchronous clipboard exception, rejected write promise, denied
permission, and local-file security restriction as the same refusal outcome.
The refusal path reveals the exact live payload in the fallback textarea, while
export-bearing state changes, resets, and invalid attempts hide and clear any
previously revealed fallback before presenting newer status.

**Rationale**: ART-004 must work directly from `file://`, where browser security
behavior varies and clipboard writes cannot be assumed. The existing shipped
export pattern already handles no-clipboard and rejected-write paths with the
same focused fallback, and its comments identify stale fallback text beside a
newer status as a failure mode.

**Alternatives considered**: Retrying automatically was rejected because the
artifact cannot distinguish permission refusal, user-agent policy, inactive
page, or absent interface. Leaving old fallback text visible after state changes
was rejected because it can look like the current export while naming a prior
selection or rationale.

**Primary sources**: W3C Clipboard API `writeText` and clipboard-write
permission algorithms; MDN Clipboard `writeText` secure-context and
`NotAllowedError` documentation; MDN same-origin policy notes for `file://`
opaque origins; local `speckit-pro/artifact-gallery/templates/pr-writeup.html`
export fallback implementation.

### R13. Offline typeface failure

**Decision**: Require ART-004 artifacts to use the canonical brand-kit font
stacks through their system and generic fallbacks, and prohibit font-only glyphs
as the sole carrier of control, status, or artifact meaning.

**Rationale**: The gallery contract already permits only typeface substitution
as the visible offline difference, and the brand kit's stacks end in generic
families so text remains readable when brand fonts are unavailable. CSS font
selection is a prioritized family list with generic-family fallback, so this is
the smallest requirement that turns "optional typeface substitution" into a
measurable error-handling rule.

**Alternatives considered**: Requiring the brand fonts to be embedded was
rejected because it adds generated asset bytes and contradicts the existing
canonical head/typeface contract. Allowing icon-font-only meaning was rejected
because missing private-use glyphs can erase the only visible state or label.

**Primary sources**: CSS Fonts Module Level 4 `font-family` and generic-family
fallback rules; MDN `font-family` fallback guidance; local
`speckit-pro/artifact-gallery/SPA-CONTRACT.md` typeface-stack and offline
readability rules.

### R14. Manifest and generated-artifact drift failures

**Decision**: Treat missing or extra manifest rows, non-status field changes,
wrong status-flip counts, and stale, missing, extra, truncated, rewritten, or
byte-mismatched generated outputs as blocking validation failures.

**Rationale**: ART-004 changes payload-affecting gallery source. Repository
rules require generated payloads, installed-cache proofs, and generated
reference pages to be derived from source, and existing gallery tests already
report payload absence, stale copies, truncation, and byte mismatches.

**Alternatives considered**: Recording drift as review guidance was rejected
because the manifest and generated outputs are release-routing surfaces; a
warning would allow a misleading export or catalog state to ship.

**Primary sources**: local `.specify/memory/constitution.md` Principles II and
IV; local `AGENTS.md` generated-artifact contract; local
`tests/speckit-pro/unit/test-artifact-gallery.py` Group F payload reach checks;
local `scripts/refresh-release-artifacts.py` isolated check-mode drift report.

## Source Inventory

| Artifact | Slice | Upstream source | Required fill regions | Export behavior |
|---|---:|---|---|---|
| `design-system` | 2 | `05-design-system.html` | `feature-header`, `color`, `typography`, `spacing`, `shape`, `components` | Read-only |
| `animation-prototype` | 2 | `07-prototype-animation.html` | `feature-header`, `completion-stage`, `easing-controls`, `keyframes`, `css-snippet` | Read-only |
| `interaction-prototype` | 2 | `08-prototype-interaction.html` | `feature-header`, `views`, `interaction-notes`, `open-questions` | Read-only |
| `svg-illustrations` | 2 | `10-svg-illustrations.html` | `feature-header`, `illustrations`, `palette-rules` | Read-only |
| `visual-designs` | 3 | `02-exploration-visual-designs.html` | `feature-header`, `design-brief`, `background-toggle`, `directions` | Prompt and Markdown decision export |
| `component-variants` | 3 | `06-component-variants.html` | `feature-header`, `variant-controls`, `variants`, `snippet-preview` | Prompt and Markdown decision export |

## Size Reconciliation

The six pinned sources total 3,098 planning lines. Local `wc -l` against the pinned cache reports 3,092 newline-terminated lines. The active Plan uses the required planning baseline and assigns review estimates by capability:

- Slice 1: 160 reviewable LOC, 3 production files, no new upstream source lines.
- Slice 2: 590 reviewable LOC, 4 production files, 1,976 required planning source lines.
- Slice 3: 520 reviewable LOC, 2 production files, 1,122 required planning source lines plus export behavior.
