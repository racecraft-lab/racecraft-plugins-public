# Specification Quality Checklist: Final-PR Template Set — Slice 2, the Annotated Diff Artifact

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-13
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [ ] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Items marked incomplete require spec updates before `/speckit-clarify` or `/speckit-plan`

### The three open markers are deliberate, not omissions

Three `[NEEDS CLARIFICATION]` markers remain, and each is held open on the design
concept's own instruction rather than for want of a reasonable default. The
concept's Open Questions assign the slot inventory to a dedicated Clarify session
on the stated ground that **slot names must not be invented before the upstream
source is read**, and the upstream file is fetched read-only at implement time.
Guessing here would produce a confident inventory that the first real read
contradicts, which is the failure this sequencing exists to prevent.

The three map one-to-one onto the three Clarify sessions the workflow already
declares:

| Marker | Requirement | Resolved by |
|---|---|---|
| Slot inventory beyond `hunks` and `feature-header`, each slot's `Source:`, and whether the closed source-artifact set needs a member | FR-011 | Clarify session 1 |
| The diff rendering model: annotation attachment, clean-hunk rendering, line-number addressability, wide-hunk containment | FR-019c | Clarify session 3 |
| What a hunk's anchor slug and visible label derive from, and what happens when two hunks would collide | FR-023b | Clarify sessions 1 and 2 |

### What is already closed and must not be re-opened

- `hunks` is a list slot carrying **exactly two** hunks, one annotated and one
  clean (design concept Q2 and Q6). FR-020 and FR-020a state it, and FR-020a
  records why a floor and a cap coincide at the same number here when they did
  not on slice 1.
- Severity is optional, marks findings only, and comes from a closed set of three
  words (Q9). FR-019a.
- Port fidelity keeps the upstream mechanism and drops non-stage sections (Q3).
  FR-018.
- Colour may never be the sole carrier of the added/removed/context distinction.
  FR-019, stated as its own requirement rather than folded into the general
  accessibility rule at FR-033, because a unified diff is the one place where the
  conventional rendering *is* the violation.
- The invocation-currency guard is scoped by **effect**, at four check sites.
  FR-027a and FR-027b.
- The artifact's title must equal its catalog entry's title byte for byte.
  FR-010a. Nothing in the suite asserts this; slice 1 shipped it wrong through a
  green suite.

### Declaration hygiene verified

The gate's parser was **run**, not read. `reviewable LOC` occurs exactly once in
the file, in the last line of the Reviewability Budget section, and the parser
returns 755. Production files returns 1, total files returns 13, primary surface
returns `docs/process`. No prose after the declaration repeats the phrase.
