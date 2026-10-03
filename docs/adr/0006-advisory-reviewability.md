# Reviewability reports advise without blocking a run

Status: accepted

Numeric reviewability limits are advisory on Claude Code and Codex. Exceeding a size threshold produces a warning and, where useful, a split recommendation; it never requires a split or stops scaffold, autopilot planning, implementation, or PR emission. Warnings remain visible in the review artifacts and draft PR. Value-unit enforcement belongs to the separate [Value unit: actor, outcome, acceptance step, surface](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1025) decision.

When a roadmap declares slices, assess each slice separately and show whole-SPEC totals as context. Without declared slices, assess the SPEC. Do not treat a whole-SPEC estimate as an estimate for an individual slice. Existing LOC, file and primary-surface thresholds remain advisory reference points with their current strictly-greater-than comparisons; this decision does not retune their values.

For each metric and unit, warnings use the largest available comparable heuristic, roadmap or plan estimate. Retain the contributing figures, their sources and their scope, and label estimates as estimates. A low heuristic never reduces a larger declared estimate. This is a conservative rule for combining estimates, not proof that the estimate is a lower bound on actual work.

Missing, unreadable or malformed required size evidence goes through the existing retry ladder (ADR 0004). If repair is exhausted, the reviewability report remains unknown, the failing evidence check is recorded as blocked, and autopilot continues. Put that unresolved evidence visibly in the review artifacts and draft PR; never substitute zero or report a pass. Exceeding a valid size estimate alone does not enter the retry ladder.

## Considered Options

- **Keep numeric size blocks.** Rejected: the setup gate stops on parent estimates while later planning sizing already continues with an advisory result. Numeric counts cannot establish whether a SPEC delivers a coherent user-visible outcome.
- **Assess only whole-SPEC totals.** Rejected: declared review slices need separate assessments; aggregate size remains useful context.
- **Prefer a single estimator over declared evidence.** Rejected: the heuristic can undercount and must not erase a larger comparable estimate.
- **Immediately leave invalid evidence unknown.** Rejected: use the existing repair path first, then expose the remaining uncertainty without stopping the run.

## Consequences

- Replace numeric reviewability stop instructions and blocking outcomes with advisory reports across both hosts. Strict evidence validation and the retry ladder remain.
- Parse declared slices and their budgets structurally, and preserve estimate provenance and scope. The current broad parent-field parser does not satisfy this contract.
- Future validation must cover threshold boundaries, separate slice assessment, conflicting estimates, missing and malformed evidence, exhausted repairs that continue, and identical reports from equivalent normalized inputs on both hosts.
- Report layout and schema are implementation details. The separate value-unit decision defines the real scope constraint.
- This records the planning decision for [Reviewability block tier: keep or advisory](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1011); the current runner behavior still needs implementation.
