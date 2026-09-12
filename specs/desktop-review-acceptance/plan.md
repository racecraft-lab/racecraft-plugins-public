# Plan: Desktop Artifact Review Acceptance

## Chosen approach

Use a durable workflow handoff beside a small, realistic planning record. The
workflow is the single source for stage and artifact-review status; the HTML
pages remain generated outputs under the feature directory. This keeps the
fixture close to the current resolver contract while leaving the production
gallery untouched.

## Competing approaches

### A. Single acceptance report

Put page names, hashes, and stage notes in one report. This is easy to read but
duplicates workflow state and gives the resolver no durable record to inspect.

### B. Workflow handoff with generated pages (chosen)

Keep the exact handoff JSON in the workflow, fingerprint planning inputs and
template bytes, and link each page to its own pending preview disposition. The
report can explain scope, but it does not become a second state store.

The durable workflow wins because it is the contract consumed by
`resolve-autopilot-stage`; it also makes future browser observations appendable
without changing generation evidence.

## Architecture map

The fixture exercises existing brownfield boundaries without modifying them:

1. `speckit_pro_runner/helpers/read_only.py` parses workflow overview rows and
   resolves the requested stage.
2. `speckit_pro_runner/artifact_review.py` validates hashes, selected outcomes,
   and pending or verified preview records.
3. `artifact-gallery/manifest.json` selects the two always-on pages plus the
   signal-routed pages; the planned architecture-viewer row has no template.
4. `specs/desktop-review-acceptance/artifacts/` contains the four rendered
   pages used for review.

## Phases

1. Seed `spec.md`, `plan.md`, and `tasks.md` with the scope and routing signals.
2. Render and validate four selected gallery templates from their marked fill
   regions; retain the architecture-viewer gap.
3. Write the workflow handoff with byte hashes and all preview dispositions
   pending. Validate it through the real resolver.
4. Parent performs browser observation after draft-PR identity bookkeeping;
   this fixture author records only evidence supplied by the parent.

## Verification boundary

Generation checks prove file identity, filled markers, and source hashes. They
do not prove that a browser rendered a page, that a human approved it, or that
UAT ran. Those remain explicit pending preconditions until observed.
