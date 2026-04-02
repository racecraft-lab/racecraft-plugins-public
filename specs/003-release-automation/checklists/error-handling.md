# Error Handling Checklist: Release Automation

**Purpose**: Validate that error-handling, failure-mode, and recovery requirements are complete, clear, and consistent in the Release Automation spec and plan
**Created**: 2026-04-01
**Feature**: [specs/003-release-automation/spec.md](../spec.md)

## Requirement Completeness

- [x] CHK001 - Are failure-mode requirements defined for the release-please action step itself (e.g., network timeout, API rate limit, malformed config)? [Completeness, Spec Edge Cases -- added release-please failure edge case]
- [x] CHK002 - Is it specified that a release-please action failure must not block future pushes to main (i.e., the failure is non-fatal to the repository's merge workflow)? [Completeness, Spec FR-014]
- [x] CHK003 - Are failure-mode requirements defined for the `sync-marketplace-versions.sh` script covering all known failure causes (missing jq, malformed JSON, missing plugin.json)? [Completeness, Spec Edge Cases]
- [x] CHK004 - Is the requirement that sync script failure is surfaced clearly in the GitHub Actions log explicitly stated with expected log output behavior? [Clarity, Spec Edge Cases + FR-012]
- [x] CHK005 - Are failure-mode requirements defined for the git push of the sync commit (e.g., permission denied, branch protection block)? [Completeness, Spec Edge Cases]
- [x] CHK006 - Is the behavior specified when release-please runs but no releasable conventional commits exist since the last release (clean no-op)? [Completeness, Spec Edge Cases]
- [x] CHK007 - Are the specific commit types that are releasable vs. non-releasable explicitly enumerated? [Clarity, Spec Edge Cases]

## Requirement Clarity

- [x] CHK008 - Is "surfaced clearly in the Actions log" quantified -- does the spec define what constitutes sufficient error visibility (e.g., step failure status, error message format, exit code)? [Clarity, Spec FR-012 -- `continue-on-error: false` means step failure = workflow failure = red X in UI]
- [x] CHK009 - Is the distinction between "workflow step fails" and "workflow run fails" clearly defined for the sync step? [Clarity, Spec FR-012 -- explicit that sync failure marks entire workflow run as failed]
- [ ] CHK010 - Is the phrase "deterministic failure modes" in the edge cases section clarified with the exhaustive list of what qualifies as deterministic vs. transient? [Clarity, Spec Edge Cases]
- [x] CHK011 - Is it unambiguous whether the sync step should use `continue-on-error: false` (default) or `continue-on-error: true` in the workflow? [Clarity, Spec FR-012]

## Requirement Consistency

- [x] CHK012 - Are the error-handling requirements for the sync step consistent between the Edge Cases section and FR-004? FR-004 specifies the conditional trigger but does not mention failure behavior; Edge Cases describe failure behavior but do not reference FR-004. [Consistency, Spec FR-004 + FR-012 + Edge Cases -- FR-012 now bridges this gap]
- [x] CHK013 - Is the recovery path for sync failure (manual re-run via GitHub Actions UI) consistent with the recovery path for branch protection failure (dependency on SPEC-004)? Both are manual but via different mechanisms. [Consistency, Spec Edge Cases -- different mechanisms are appropriate for different root causes]
- [x] CHK014 - Is the error-handling stance consistent across all workflow steps -- release-please failure vs. sync failure vs. push failure? Are they all "fail visibly, no retry" or are there differences? [Consistency, Spec Edge Cases + FR-014 -- all follow "fail visibly, no automatic retry, resumable on next trigger"]

## Scenario Coverage

- [ ] CHK015 - Is the behavior specified when `actions/checkout` fails before the release-please step can run? [Completeness, Exception Flow -- standard GitHub Actions infrastructure; over-specification risk]
- [x] CHK016 - Is the behavior specified when the sync script succeeds but the subsequent git commit or git push fails (partial completion scenario)? [Completeness, Spec Edge Cases -- added partial completion edge case]
- [x] CHK017 - Does the spec define what happens when a release is created but the sync step fails -- specifically, is marketplace.json guaranteed to be re-synced on the next release? [Completeness, Spec Edge Cases -- added self-healing sync edge case]
- [x] CHK018 - Is the recovery flow documented for when marketplace.json is left out of sync after a failed sync step? Does the spec guarantee the next successful release will re-sync? [Completeness, Spec Edge Cases -- self-healing property documented]
- [x] CHK019 - Is the behavior specified when the GitHub Actions runner environment is missing the `jq` dependency? [Completeness, Spec Assumptions -- covered by sync script failure edge case (jq not available)]
- [x] CHK020 - Are concurrent/parallel workflow run scenarios addressed -- what happens if two workflow runs overlap (e.g., rapid pushes to main)? [Coverage, Spec Edge Cases -- batching behavior documented]

## Edge Case Coverage

- [ ] CHK021 - Is the behavior specified when `release-please-config.json` or `.release-please-manifest.json` is missing or malformed? [Completeness, Edge Case -- covered by Assumptions section (SPEC-001 prerequisite) but no explicit failure behavior]
- [x] CHK022 - Is the behavior specified when `marketplace.json` is already in sync (idempotent run of the sync script)? [Completeness, Spec Edge Cases]
- [ ] CHK023 - Is the behavior specified when the `speckit-pro--release_created` output is missing or has an unexpected value (not `true`/`false`)? [Completeness, Edge Case -- GitHub Actions platform concern, low risk]
- [ ] CHK024 - Is the behavior specified when the GITHUB_TOKEN is expired or lacks sufficient permissions beyond `contents: write`? [Completeness, Edge Case -- partially covered by `contents: write` edge case]

## Recovery & Resilience Requirements

- [x] CHK025 - Are retry requirements explicitly defined (or explicitly excluded) for each failure mode? The spec says "no automatic retry" for sync failures -- is this stance documented for all other failure modes? [Completeness, Spec Edge Cases -- release-please failure edge case now also states no retry, resumable on next push]
- [x] CHK026 - Is the manual recovery procedure (re-run via GitHub Actions UI) specified with sufficient detail for a maintainer to follow? [Clarity, Spec Edge Cases]
- [x] CHK027 - Does the spec define whether a failed sync step leaves any partial state (e.g., uncommitted file changes in the workspace) that could affect subsequent runs? [Completeness, Spec Edge Cases -- added partial completion edge case confirming ephemeral workspace]
- [x] CHK028 - Is the self-healing property documented -- that the sync script is idempotent and registry-driven, so a future successful release will automatically correct any out-of-sync marketplace.json? [Completeness, Spec Edge Cases -- self-healing property documented]

## Non-Functional Requirements

- [x] CHK029 - Are timeout requirements defined for the workflow or individual steps (e.g., maximum allowed execution time before a step is considered failed)? [NFR, Spec FR-013]
- [ ] CHK030 - Are logging/observability requirements defined beyond "clear error in the GitHub Actions log" (e.g., structured output, notification on failure)? [NFR -- intentionally deferred; GitHub Actions built-in notifications are sufficient for this scope]

## Dependencies & Assumptions

- [x] CHK031 - Is the dependency on SPEC-004 for branch protection exemption clearly documented with what happens when SPEC-004 is not yet implemented (sync push fails)? [Completeness, Spec Assumptions + Edge Cases]
- [x] CHK032 - Is the assumption that `jq` is pre-installed on `ubuntu-latest` runners validated or documented as a risk if GitHub changes the runner image? [Assumption, Spec Assumptions]

## Notes

- Items marked `[x]` have been validated as addressed in spec.md and/or plan.md
- Items remaining `[ ]` are either (a) intentionally deferred as over-specification or (b) low-risk platform-level concerns
- The user's key concern -- that a failed sync step should not leave marketplace.json permanently out of sync -- is addressed by CHK017, CHK018, and CHK028 via the self-healing sync edge case added to spec.md
- New requirements FR-012, FR-013, FR-014 were added to spec.md to close error-handling gaps
- Plan.md updated with Error Handling Design section documenting failure isolation, visibility, self-healing sync, and push independence
