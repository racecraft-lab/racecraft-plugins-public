# Issue #571 Acceptance Fixture

This is a disposable evidence fixture for desktop artifact-review delivery.
**DO NOT MERGE.** It contains no production change and no claim of completed
manual acceptance.

## Initial checkpoint

- Planning record: `spec.md`, `plan.md`, and `tasks.md` are seeded test
  preconditions, not evidence that the full SpecKit phases ran.
- Generated pages: four shipped draft-PR templates are filled and fingerprinted
  in the workflow handoff.
- Planned gap: `architecture-viewer` has no shipped template in the active
  gallery, so no replacement HTML page is created.
- Browser observation: pending until the parent inspects each page through the
  permitted local preview route and supplies the actual rendered title, visible
  body text, locator, and timestamp.
- Human approval: pending; no approval is implied by generation.
- Manual UAT: pending; no UAT result is implied by browser rendering.

The parent may update this report with observed evidence after the draft PR
identity bookkeeping commit. The workflow's `Artifact Review Handoff` section
remains the sole machine-readable handoff record.

## Generation receipt

The fixture author ran a deterministic byte-level check over all four selected
pages. It passed the following checks for each page: output bytes differ from
the shipped template; every declared `FILL` marker appears once and in order;
every fill region differs from its shipped source region; and no rendered page
contains an element with `class="sample-notice"`, `class="notice"`, or
`class="note"`. A negative check confirmed that the untouched shipped
implementation-plan template still contains its sample banner and is rejected;
another confirmed that no architecture-viewer output exists.

The real resolver invocation was:

```text
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner <<'JSON'
{"schema_version":"1.0","request_id":"issue-571-resolve","helper_id":"resolve-autopilot-stage","operation":"resolve-autopilot-stage","mode":"read_only","inputs":{"workflow_file":"specs/desktop-review-acceptance/workflow.md","autopilot_args":["specs/desktop-review-acceptance/workflow.md"]}}
JSON
```

The request was supplied on stdin and not written to the feature directory. It
returned exit code 0 with `planning_complete: true`,
`stage: plan`, `artifact_review.status: pending`,
`artifact_review.resume_action: preview`, `generated: 4`,
`verified: 0`, and `generation_gaps: ["architecture-viewer"]`.
