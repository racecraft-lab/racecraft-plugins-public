# Research: Gate Repair

## R1: Delivery shape

- Decision: Deliver the repair in 4 slices: verdict model, gate checks, stage transition, and PR emission.
- Rationale: Each slice stays reviewable on its own.
- Alternatives considered: One pull request; per-gate pull requests.

## R2: Verdict storage

- Decision: Keep verdicts in the workflow file.
- Rationale: The workflow file is the durable run record.
- Alternatives considered: A separate verdict ledger.
