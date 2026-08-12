# Specification Quality Checklist: Final-PR Template Set — Slice 1, the PR Write-up Artifact

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-12
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

Three `[NEEDS CLARIFICATION]` markers remain deliberately, which is the command's
maximum. All three are held open for `/speckit-clarify` and `/speckit-plan`
rather than guessed here.

1. **FR-017 — the `implementation-notes` source vocabulary.** The fixed decision
   declares that slot's source as a path under a feature's process directory. The
   fill-region validation splits `Source:` on commas and requires exact
   membership in a closed set of five bare filenames, none of which is
   `implementation-notes.md`. A guess here would either invent a vocabulary
   extension the contract has not recorded, or silently drop a decision the
   interview fixed. Clarify settles which. The rendering decision itself (only
   eventful entries, append order, under the task identifier) is fixed and is not
   reopened.

2. **FR-020 / FR-039 — which slots hold a repeated list.** The design concept
   defers per-slot granularity until the upstream source has been read, on the
   recorded ground that slot shapes must not be invented before it, and the
   upstream file is fetched at implement time. This decides which regions owe two
   anchored sample items and which rows the list-slot literal gains. Guessing it
   would fix the shape of two regions on no evidence.

3. **Reviewability Notes — how slice 1 clears the size boundary.** The budget was
   re-measured at Phase 0 against the four shipped templates individually rather
   than fitted to one aggregate figure, and the projection moved from ~750 to
   roughly 1000–1200, which exceeds the 800 block threshold. The predictor is the
   `exports` declaration, not slot count and not upstream size: the only shipped
   template under the block declares no exports, while all three carrying both
   export kinds land between 1003 and 1222. `pr-writeup` carries both, so its
   comparators are `module-map` (1003) and `code-approaches` (1026). Neither
   standing remedy fits. The valid exception classes are only `refactor`, `infra`,
   and `upgrade`, none of which describes a net-new artifact; and re-slicing is
   unavailable, because a self-contained HTML artifact cannot be divided across
   two pull requests and still render from the local-file scheme. The resolution
   is the operator's call at Plan, and this planning run terminates at G6.5 before
   any code is written, so nothing is sunk before the ruling.

One further item from the design concept's open questions is recorded in the spec
as a **deferral rather than a marker**, because it has a named owner and a settled
resolution path: the serialized payload shape of the two exports resolves at Plan,
reusing the shipped "walk the non-empty notes with item anchors" shape
(Assumptions).

**Scope was not reduced to chase the size number.** Six fill regions and both
export kinds are fixed interview decisions, and the catalog entry shipped in
ART-001 already promises both. Dropping either would resolve the projection by
breaking a commitment, so the spec records the overage and hands it on.

Both remaining open questions in the design concept concern slices 2 and 3 and
are out of this spec's scope by construction.

Items marked incomplete require spec updates before `/speckit-plan`.
