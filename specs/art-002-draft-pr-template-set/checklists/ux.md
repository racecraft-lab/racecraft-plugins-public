# UX Checklist: Draft-PR Template Set (ART-002)

**Purpose**: Validate that the reader-facing requirements in `spec.md` and
`plan.md` are complete, unambiguous, consistent, and measurable — before any
template is authored. These items test the requirements, not an implementation.

**Created**: 2026-08-10

**Feature**: [spec.md](../spec.md)

**Depth**: Thorough | **Audience**: Reviewer / PM at the plan gate

**Focus areas** (from the workflow's enriched prompt): sample content that reads
as fictional and representative at once; objection capture tied structurally to
its item; export content rules; theme control, brand mark, and offline typeface
degradation; and above all what an export emits when the reader recorded nothing.

**Reading the marks**: `[x]` means the requirement set already answers the
question. An unchecked item names a defect in the requirements. Items closed
during this pass carry `[Resolved]` and name the requirement that now answers
them.

## The three readers

Each item is written against one of the readers `spec.md` names: the **reviewing
operator** who records and carries out a conclusion, the **gallery browser**
choosing a template from a rendered document, and the **authoring agent**
(ART-007) that fills the slots.

## Sample content: fictional and representative at once

- [x] CHK001 Is the obligation to ship worked example content in every slot stated as a requirement rather than left to authoring taste? [Completeness, Spec §FR-014]
- [x] CHK002 Is the reason sample content exists — a gallery browser judging from a rendered document, and a render check exercising real layout — recorded so a later editor cannot trade it away? [Traceability, Spec §FR-014, §SC-004]
- [x] CHK003 Is the risk of sample content being read as the project's own data identified as an edge case? [Edge Case, Spec §Edge Cases]
- [x] CHK004 Is "plainly fictional" given a criterion a reviewer can apply without judgement, so two reviewers reach the same verdict? [Resolved — Measurability, Spec §FR-014, §SC-004]
- [x] CHK005 Do the requirements say whether the four templates share one invented subject or each invent their own, given a browser compares them side by side? [Resolved — Completeness, Spec §FR-014]
- [x] CHK006 Is there a requirement that the rendered document itself tells a first-time reader the content is sample content, given the slot inventory is an HTML comment they never see? [Resolved — Coverage, Spec §FR-014]
- [x] CHK007 Is the placement of any unfilled-state notice constrained so a fill removes it, rather than leaving a "sample content" claim standing on a filled artifact? [Resolved — Consistency, Spec §FR-014, §FR-015]
- [x] CHK008 Are requirements defined for what happens when a slot ships with no sample content? [Edge Case, Spec §Edge Cases, §SC-004]
- [x] CHK009 Is feature-specific content outside a slot forbidden, so nothing fictional survives a fill in a position the agent never replaces? [Completeness, Spec §FR-015, §Edge Cases]

## Objection capture tied to its item

- [x] CHK010 Is the tie between an objection and the item it attaches to required to be structural rather than restated by the reader in prose? [Clarity, Spec §FR-016]
- [x] CHK011 Is the starting state of an objection field fixed, rather than left as an authoring choice? [Completeness, Spec §FR-018, §Clarifications Session 2]
- [x] CHK012 Is the rejected alternative — always-revealed fields — recorded with its reason, so a later editor does not reintroduce it? [Traceability, Spec §FR-018]
- [x] CHK013 Is there a requirement that a reader can tell which items already carry an objection without opening each disclosure? [Coverage, Spec §FR-018]
- [x] CHK014 Is "carries a note" defined against whitespace-only input, so an export cannot emit a blank objection as a recorded one? [Resolved — Ambiguity, Spec §FR-018]
- [x] CHK015 Is the moment the disclosure's state text refreshes specified, so a reader who types and never collapses is not shown stale text? [Resolved — Ambiguity, Spec §FR-018]
- [x] CHK016 Are the controls serving the same function across the items of one list required to be identified consistently? [Consistency, Spec §FR-017a]
- [x] CHK017 Is the insertion position of a mounted capture control fixed relative to its anchor, so reading order and tab order follow visible order? [Clarity, Spec §FR-016a]
- [x] CHK018 Is the upstream accordion behavior that force-closes sibling disclosures identified as a hazard to in-progress input? [Edge Case, Plan §The Shared Behavior Decision, Contract §Capture shapes]
- [x] CHK019 Are requirements defined for the single-choice control's grouping and its visible group label, rather than leaving grouping implicit? [Completeness, Spec §FR-017]
- [x] CHK020 Is the optionality of the code-approaches reason field stated together with what an export does when it is absent? [Completeness, Spec §FR-017, Contract §The absent reason]

## What an export emits

- [x] CHK021 Is the empty-state export wording fixed per export kind rather than left to each of three independent implementations? [Clarity, Spec §FR-018, Contract §Empty-state bodies]
- [x] CHK022 Do the requirements state that an empty export must explicitly deny approval, and record why the denial is part of the text? [Completeness, Spec §FR-018, Contract §Empty-state bodies]
- [x] CHK023 Is it stated that an export lists only recorded items, with no line, placeholder, or count for an untouched one? [Clarity, Spec §FR-018]
- [x] CHK024 Are the coordinates that name an item in an export enumerated, rather than described as "enough context"? [Measurability, Spec §FR-018, Contract §The item reference line]
- [x] CHK025 Is the header line that names the feature and the artifact given a fixed form, given the empty-state bodies beside it are pinned verbatim for exactly that reason? [Resolved — Consistency, Contract §The header line, Spec §FR-022]
- [x] CHK026 Is the prohibition on exporting a value the reader could not see in the rendered document stated? [Completeness, Spec §FR-023]
- [x] CHK027 Is the derivation of an export from live state, never from an authored value, stated as a requirement? [Clarity, Spec §FR-021]
- [x] CHK028 Are requirements defined for the clipboard failure path — one cause-neutral message, a selectable focused field, and no reported success? [Coverage, Exception Flow, Spec §FR-025]
- [x] CHK029 Is the success message required to name what the produced text actually carries, so it cannot imply a conclusion the text does not contain? [Clarity, Spec §FR-024, Contract §Feedback]
- [x] CHK030 Do the requirements differentiate the two export controls for the reader, given they sit side by side and their destinations are named only in a contract the reader never opens? [Resolved — Clarity, Spec §FR-019]
- [x] CHK031 Is the wording constraint that feedback text must not name the local-file scheme recorded with its reason? [Traceability, Spec §Assumptions, Contract §Wording that must not name a scheme]

## Recovery, loss, and state

- [x] CHK032 Are requirements defined for what becomes of a reader's recorded work on reload or tab close, and for whether the artifact says so? [Resolved — Recovery Flow, Spec §FR-018a, §Edge Cases]
- [x] CHK033 Is the absence of persistence stated as a deliberate decision rather than left as an unstated consequence of the single-file rule? [Assumption, Plan §Technical Context, Spec §FR-018a]
- [x] CHK034 Are requirements defined for the browser refusing storage, and is it clear that only persistence degrades and never the control? [Edge Case, Spec §Edge Cases, §FR-035]
- [x] CHK035 Is the state transition for a second approach selection replacing the first specified, together with what an export then carries? [Coverage, Spec §US3 scenario 5, Contract §Capture shapes]

## Theme, brand mark, and offline degradation

- [x] CHK036 Is the prohibition on authoring, replacing, wrapping, or reading the theme control stated, with the attribute a template reads instead? [Clarity, Spec §FR-035]
- [x] CHK037 Do the requirements decide whether these four templates opt into the brand mark, rather than leaving an opt-in undecided on a feature whose purpose is a branded artifact? [Resolved — Completeness, Spec §FR-035]
- [x] CHK038 Is the placement of an opt-in brand mark constrained so a fill cannot delete it? [Resolved — Consistency, Spec §FR-035, §FR-015]
- [x] CHK039 Is offline degradation bounded to typeface substitution, with every control still working and no error reported? [Measurability, Spec §FR-006, §SC-001]
- [x] CHK040 Is the reduced-motion obligation extended to motion a template adds beyond what the kit declares? [Coverage, Spec §FR-034]

## The gallery browser and the port's residue

- [x] CHK041 Is the gallery browser named as a reader with a stated job, so requirements can be traced to them? [Traceability, Spec §User Scenarios]
- [x] CHK042 Are requirements defined for what must stay coherent after a dropped upstream region is removed — no orphaned heading, no caption without its figure, no in-page link into a dropped region? [Resolved — Edge Case, Spec §Edge Cases]
- [x] CHK043 Is each of the ten dropped regions accounted for against a stated reason rather than dropped silently? [Traceability, Spec §Assumptions, Plan §Per-Template Port Worksheet]
- [x] CHK044 Are the three authored-fresh regions identified, so nobody looks for an upstream counterpart that does not exist? [Completeness, Spec §Assumptions]
- [x] CHK045 Is the read-only declaration of the spec explainer stated structurally — no export, no input field, no script of its own — rather than as a judgement? [Consistency, Spec §FR-020]

## Acceptance criteria quality

- [x] CHK046 Can SC-002's "single action and under 30 seconds" be measured by an operator without help? [Measurability, Spec §SC-002]
- [x] CHK047 Does SC-004 measure both halves of FR-014 — that no slot is an empty frame, and that its content reads as fictional? [Resolved — Measurability, Spec §SC-004]
- [x] CHK048 Does SC-005 state the empty-recorded case as a measurable zero rather than as prose? [Measurability, Spec §SC-005]
- [x] CHK049 Are the manual browser checks required to be recorded as numbered steps with observable results, one set per template? [Acceptance Criteria, Spec §FR-038, Quickstart §Manual acceptance]
- [x] CHK050 Does the acceptance runbook exercise the empty-export path separately from the recorded-export path? [Coverage, Quickstart §Manual acceptance steps 9–10]

## Notes

- Traceability: 50 of 50 items carry a reference to a requirement, a contract
  section, a clarification session, or a resolution marker.
- Eight distinct gaps opened in this pass, raised by 14 of the 50 items. All
  eight are closed: seven by amending `spec.md` (FR-014a, a new FR-018 bullet,
  FR-018a, FR-019, FR-035, SC-004, and two new edge cases), one by pinning the
  export header line in `contracts/export-payload-contract.md`. The four new
  authored elements are carried into `plan.md`'s port worksheet and into
  `quickstart.md`'s acceptance steps, so each is checkable at acceptance rather
  than only stated. Each closed item names the requirement that now answers it.
- No item asks whether an implementation behaves correctly. Behavior is the
  acceptance runbook's job, and `quickstart.md` already carries it.
