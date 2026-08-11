# Accessibility Checklist: Draft-PR Template Set (ART-002)

**Purpose**: Validate that the accessibility requirements in `spec.md` and
`plan.md` are complete, unambiguous, consistent, and measurable — before any
template is authored. This is a unit test for the requirements text, not for a
rendered document.

**Created**: 2026-08-10

**Feature**: [spec.md](../spec.md)

**Depth**: Standard. **Audience**: reviewer at the plan gate. **Focus areas**,
taken verbatim from the workflow prompt: inline objection disclosures and their
fields; the code-approaches single-choice control and reason field; export
controls, their success reporting and their clipboard-failure path; colour
pairings drawn only from the audited brand-kit table; and the module map's
distinguished path as the color-is-not-the-only-carrier case.

**Normative source**: `speckit-pro/artifact-gallery/SPA-CONTRACT.md` governs.
Where an item below asks whether the spec restates an obligation, the question is
whether an implementer reading `spec.md` alone would reach the same behavior the
contract requires.

## Keyboard operation and focus order

- [x] CHK001 Are keyboard reachability and operability stated for every class of
      control the templates carry — objection disclosure, objection field,
      single-choice control, reason field, export control? [Coverage, Spec §FR-016,
      §FR-017, §FR-018, §FR-024]
- [x] CHK002 Is the focus-visible obligation stated once and applied to every
      interactive element rather than per control? [Consistency, Spec §FR-033]
- [x] CHK003 Are the two focus anti-patterns named explicitly — no positive tab
      order, no focus trap — rather than left to the reader to infer from "normal
      order"? [Clarity, Spec §FR-033]
- [x] CHK004 Is the relationship between visible order, reading order, and tab
      order specified for controls the template mounts at load rather than ships in
      markup? [Completeness, Spec §FR-016a]
- [x] CHK005 Is the suppression case bounded — is it stated that an indicator may
      be replaced only by an equivalent, never simply removed? [Clarity,
      Spec §FR-033]
- [x] CHK006 Is keyboard reachability stated as a verifiable outcome rather than an
      aspiration, with a success criterion that can be counted? [Measurability,
      Spec §SC-008, §US1 Acceptance 5]

## Programmatic labels and exposed state

- [x] CHK007 Does the spec require the accessible name of a mounted objection field
      to identify **which item** it attaches to, so a reader listing the document's
      fields can tell N identically-labelled fields apart? [Resolved, Spec §FR-017a]
      — FR-017a now says consistent is not identical: the shared part of the name
      comes from the routine, the distinguishing part from the item's visible label.
      Evidence: WCAG 2.4.6 Headings and Labels (AA) is tested by listing the
      document's form fields; W3C APG *Providing Accessible Names and Descriptions*
      recommends a per-item name precisely to distinguish repeated items.
- [x] CHK008 Is the tension between "identified consistently" and "distinguishable
      from one another" resolved rather than left for the implementer to trade off?
      [Ambiguity resolved, Spec §FR-017a]
- [x] CHK009 Is the single-choice control's exposed state requirement stated in
      terms of native semantics rather than a visual treatment? [Clarity,
      Spec §FR-017]
- [x] CHK010 Is the group label requirement for the single-choice control stated as
      *the group's accessible name*, and required to be visible? [Completeness,
      Spec §FR-017]
- [x] CHK011 Is the reason field's optionality stated in a way that also fixes what
      an export says when it is empty, so "optional" cannot be read as "omit
      silently"? [Consistency, Spec §FR-017, contracts/export-payload-contract.md
      §The absent reason]
- [x] CHK012 Does the spec address the documented gap where a native disclosure's
      expanded/collapsed state is announced unreliably, and where restyling the
      default marker degrades that announcement further? [Resolved, Spec §FR-018]
      — FR-018 gains a bullet separating the note text from the open/closed state,
      forbidding removal of the default marker without an equally visible
      replacement, and keeping the note text in the control's accessible name.
      Evidence: scottohara.me *The details and summary elements, again* (2022) —
      VoiceOver, JAWS and NVDA all announce the toggled state inconsistently once
      the marker is removed; a11ysupport.io `summary_element` records iOS VoiceOver
      conveying no expanded state at all; Deque and Hassell Inclusion both record
      NVDA + Firefox reading the initial state but not the change.
- [x] CHK013 Is the note-presence indicator required to live in the disclosure
      control's own text — so it is conveyed when the control takes focus, without
      the reader opening it? [Clarity, Spec §FR-018]
- [x] CHK014 Is it stated that the spec-explainer's disclosure deliberately carries
      no state text, so its omission reads as a decision rather than an oversight?
      [Consistency, Spec §FR-027]

## Export controls, success reporting, and the failure path

- [x] CHK015 Is "reports its success in text" bound to a fixed set of messages
      rather than left to each of three independent implementations? [Measurability,
      Spec §FR-024, contracts/export-payload-contract.md §Feedback]
- [x] CHK016 Is the success message required to name what the produced text
      actually carries, so it cannot imply a conclusion the text does not contain?
      [Clarity, Spec §FR-024]
- [x] CHK017 Does the spec state how a **repeated identical** status message
      reaches a reader who invokes the same export twice in succession — the case a
      live region does not re-announce because its text did not change?
      [Resolved, Spec §FR-024] — FR-024 now requires clearing the region before
      writing the message afresh, and requires the region to exist from load.
      Evidence: htmhell.dev *ARIA Live Regions*; EqualWeb Academy live-regions
      lesson ("clear the region before re-writing so an identical repeat message is
      announced again"; "create the live region in the DOM before you write into
      it"); nvaccess/nvda issue 14591 for the injected-region case.
- [x] CHK018 Is the failure message fixed as one cause-neutral string across every
      failure mode, and is the reason for cause-neutrality recorded? [Clarity,
      Spec §FR-025]
- [x] CHK019 Is the revealed fallback field required to be focusable and not
      disabled, rather than merely visible? [Completeness, Spec §FR-025]
- [x] CHK020 Does the spec give the revealed fallback field an accessible name, and
      does it resolve the conflict between moving focus into that field and
      announcing the failure message in a status region at the same moment?
      [Resolved, Spec §FR-025] — FR-025 now requires the field to carry its own
      programmatic label and to take the failure message as its description, so the
      focus move itself conveys the failure. Evidence: htmhell.dev *ARIA Live
      Regions* ("focus change and live regions firing at the same time are prone to
      conflicts"); the ARIA specification, quoted by Sara Soueidan — "authors SHOULD
      ensure an element with role `status` does not receive focus as a result of
      change in status"; WCAG 3.3.2 Labels or Instructions (A) for the label.
- [x] CHK021 Are requirements defined for the empty-record export path — what the
      text says and what the status region says — so neither can read as approval?
      [Coverage, Spec §FR-018, §FR-023, contracts/export-payload-contract.md
      §Empty-state bodies]
- [x] CHK022 Is the status region's placement and lifetime specified — present from
      load, beside the export controls, outside every fill region — rather than
      created on demand? [Completeness, contracts/export-payload-contract.md
      §Feedback]
- [x] CHK023 Is the prohibition on a second, deprecated copy attempt justified in
      terms of the reporting obligation rather than stated as a bare rule?
      [Clarity, Spec §FR-025]

## Colour: audited pairings and prohibited tokens

- [x] CHK024 Is the source of truth for colour pairings named as the brand kit's
      published audit, with introducing an unaudited pairing prohibited outright?
      [Completeness, Spec §FR-031]
- [x] CHK025 Is the deliberately faint boundary token prohibited for any boundary
      that carries meaning, in both themes? [Clarity, Spec §FR-031,
      brand-kit.css rule 1]
- [x] CHK026 Does the spec state that a token's **audited role** binds its use —
      that the red primitive is cleared for large text and non-text only, and that
      red body copy takes the functional danger token instead? [Resolved,
      Spec §FR-031] — FR-031 now binds the audited role as tightly as the ratio,
      names the danger token for red body copy, quantifies large text, and closes
      the un-audited-fill case. Evidence: SPA-CONTRACT.md §Color pairings ("for red
      body copy use `--rc-danger-text` … `--rc-brand-red` is audited for large text
      and non-text use only"); brand-kit.css audit rows — brand red "large text +
      non-text on all four", danger text "AA body on all four"; WCAG 1.4.3 and
      1.4.11 for the two floors.
- [x] CHK027 Is it stated that no upstream colour value survives the port, with the
      dark-theme consequence given as the reason rather than left as a style
      preference? [Clarity, Spec §FR-030]
- [x] CHK028 Are both themes in scope for every pairing requirement, rather than
      only the theme the author happens to develop in? [Coverage, Spec §FR-030,
      §FR-031]
- [x] CHK029 Are diagram strokes and diagram text covered by the pairing
      requirement, given that a stroke is a non-text pairing at a different floor
      from body text? [Coverage, Spec §FR-030, §FR-031]
- [x] CHK030 Where a remedy replaces a fill (the inverted persistence node), do
      FR-031 and FR-032 agree on which pairings the replacement may use?
      [Consistency resolved, Spec §FR-031] — FR-031's closing sentence now names
      FR-032's remedy as the case it binds.

## Colour is never the only carrier

- [x] CHK031 Is the distinguished path in the module map required to carry its
      meaning by a non-colour carrier, with colour excluded rather than merely
      supplemented? [Clarity, Spec §FR-029]
- [x] CHK032 Are **all** the places upstream carries meaning in colour alone
      enumerated, each with a named remedy, rather than covered by a general rule?
      [Completeness, Spec §FR-032]
- [x] CHK033 Is the already-compliant case (the dashed edge and its caption) called
      out as compliant, so a later reader does not "fix" it? [Clarity, Spec §FR-032]
- [x] CHK034 Is the monochrome outcome stated as an objectively checkable
      criterion? [Measurability, Spec §SC-010, §US4 Acceptance 2, quickstart step 15]
- [x] CHK035 Is the code-approaches trade-off marker remedy specified to survive a
      single row lifted out of its table, rather than relying on column position
      alone? [Coverage, Spec §FR-032]

## Diagrams: name, text equivalent, and who owns them

- [x] CHK036 Is an accessible name required for each diagram, with the reason both
      upstream sources fail recorded? [Completeness, Spec §FR-030a]
- [x] CHK037 Does the spec place the diagram's text equivalent inside the same fill
      region as the drawing? "Outside the drawing" plus FR-015's rule that every
      feature-specific region is a slot leaves the text equivalent stale after
      filling if it sits outside the marker pair. [Conflict resolved,
      Spec §FR-030a] — FR-030a now defines "outside the drawing" as outside the
      drawing element and inside the same fill region, and gives the reason.
      Evidence: spec §FR-015 ("every feature-specific region is a slot") and the
      Edge Cases entry on feature-specific content outside a slot; spec Assumptions
      ("the authoring agent replaces whole delimited regions rather than merging
      into them"); §FR-036's note that no marker pair goes inside a drawing.
- [x] CHK038 Is the decision not to place a marker pair inside a drawing stated with
      its reason, so the text-equivalent placement question is not answered by
      analogy? [Clarity, Spec §FR-036]

## Motion, theme, and the inherited blocks

- [x] CHK039 Is the reduced-motion obligation scoped correctly — the kit covers what
      the kit declares, the template covers what it adds? [Clarity, Spec §FR-034]
- [x] CHK040 Are the specific upstream transitions that must be dropped or guarded
      identified by source rather than left to a sweep? [Completeness, Spec §FR-034]
- [x] CHK041 Is the theme control's accessibility inherited rather than re-authored,
      with reading the stored value prohibited? [Consistency, Spec §FR-035]

## Document structure and the handoff to ART-007

- [x] CHK042 Does the spec state the document-level obligations that neither
      canonical block supplies — a declared page language and a page title — for
      four files opened directly from a filesystem? [Resolved, Spec §FR-035a] —
      new FR-035a. Evidence: `speckit-pro/artifact-gallery/theme-toggle.html`
      carries the policy meta, the typeface link, and the theme script between its
      GALLERY-HEAD markers and nothing else, so neither obligation is inherited;
      SPA-CONTRACT.md §Accessibility obligations names neither; WCAG 3.1.1 Language
      of Page (A) and 2.4.2 Page Titled (A).
- [x] CHK043 Does the spec constrain heading structure across the four documents,
      and require a filled slot to preserve the heading rank the shipped slot
      carried, given that ART-007 replaces whole regions? [Resolved,
      Spec §FR-035b] — new FR-035b: one top-level heading, no skipped rank, and the
      shipped sample content models the ranks a filled region keeps. It adds no
      inventory field, because FR-012 fixes the line at three labels. Evidence:
      WCAG 1.3.1 Info and Relationships (A) and 2.4.6 Headings and Labels (AA);
      SPA-CONTRACT.md §Typefaces ("heading rank rides on semantic heading level,
      size, and weight"); spec Assumptions on wholesale region replacement.
- [x] CHK044 Is the manual acceptance pass required to record keyboard reachability
      and the assistive-technology reads as numbered steps with observable results?
      [Measurability, Spec §FR-038, quickstart steps 4, 13, 15, 16]

## Notes

- Items are written as questions about the requirements text. A checked box means
  the requirement is present, clear, and consistent — not that any behavior was
  observed.
- Gap-marked items are remediated in `spec.md`; each remediation is recorded in the
  autopilot run summary with its evidence.
