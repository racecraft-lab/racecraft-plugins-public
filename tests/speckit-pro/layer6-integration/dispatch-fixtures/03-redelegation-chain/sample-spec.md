# SPEC-FIXTURE-003 — Export file format

> Layer 6 redelegation-chain test fixture spec. Intentionally surfaces a
> codebase-and-domain ambiguity so the Clarify phase generates an
> unresolved consensus item, exercising the orchestrator → clarify →
> analysts → synthesizer chain. The wording avoids every consensus
> security keyword, so `[codebase, domain]` routing stays two analysts
> and the ordinary agreement bar applies.

## Feature

Add a report-export step to a hypothetical web application. Users request
a report and receive it as a downloadable file.

## Requirements

- The exported file must be readable by common command-line tools.
- Exporting a large report must not load it into memory at once.
- The chosen format must be configurable behind a single function
  boundary so future migrations are not invasive.

## Open question (intentional, for the fixture)

The spec does not specify whether to use **JSON Lines** (the existing
pattern in the codebase) or **Parquet** (the current widely preferred
default for large columnar exports). This is the exact ambiguity that the
Clarify phase should surface and tag with `[codebase, domain]` so the
consensus protocol fans out to both analysts.

## Non-goals

- Scheduled exports
- Report layout and styling
- Delivery by email
