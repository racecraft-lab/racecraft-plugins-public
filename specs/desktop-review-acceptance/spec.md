# Desktop Artifact Review Acceptance

## Problem

Issue #571 needs a small, reviewable feature record that can drive the shipped
draft-PR artifact gallery. The acceptance fixture must show four real filled
pages and preserve the distinction between generated HTML, rendered browser
observation, human approval, and UAT.

## Scope

- Create one realistic planning record for a desktop artifact-review checkpoint.
- Select the two always-on draft-PR pages plus the pages routed by the
  `competing_approaches` and `brownfield_change` signals.
- Record the architecture-viewer entry as a planned repository gap because its
  manifest row has no shipped template.
- Keep all observation and approval claims pending until the parent records
  direct browser evidence.

## Feature signals

- `competing_approaches`: the plan compares a compact single-file checkpoint
  with a durable workflow handoff and chooses the latter.
- `brownfield_change`: the fixture describes the existing resolver, workflow
  parser, and artifact-review module that a reviewer must understand.

## User stories

1. As a reviewer, I want an implementation-plan page that summarizes the
   checkpoint so I can understand the shape of the acceptance fixture quickly.
2. As a maintainer, I want a spec-explainer page that states scope and explicit
   non-goals so generated evidence is not mistaken for UAT.
3. As an engineer, I want the competing approaches and touched modules shown
   together so the chosen handoff contract is easy to review.
4. As an operator, I want every page's generation and preview status recorded
   separately so a pending observation never reads as a pass.

## Acceptance criteria

- Four pages are generated from the shipped templates with every marked region
  filled and no sample banner.
- The durable handoff fingerprints the three planning inputs, manifest, and all
  four used templates from their actual bytes.
- The architecture-viewer template is recorded as a generation gap with a
  precise reason, separate from preview status.
- Initial preview dispositions are `pending` with no invented observation.
- The resolver reports planning complete, `Implement` pending, and an
  artifact-review resume action of `preview`.

## Out of scope

- Production source or test changes.
- A live provider matrix, permission changes, or GitHub mutations by this
  fixture author.
- Human approval, manual UAT, or claims about browser rendering before direct
  parent observation.
