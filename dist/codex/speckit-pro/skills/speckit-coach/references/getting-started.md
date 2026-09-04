# Getting Started with SpecKit & SDD

## Compact onboarding

For a new repository, use the maintained installer for the active host:
`/speckit-pro:speckit-install` on Claude or `$speckit-install` on Codex. It
selects the integration and verifies the installed state. For an existing
`.specify/` installation, inspect it first and use the upgrade workflow instead
of reinitializing it.

Create a constitution before the first feature, then follow
`constitution → specify → clarify (as needed) → plan → checklist (as needed) →
tasks → analyze (as needed) → implement`. Each phase should leave a reviewable
artifact before the next phase begins.

## Pre-spec scoping with Grill Me

Use Grill Me for a human-in-the-loop interview before the workflow exists. It
can scope a raw brief standalone, or `speckit-scaffold-spec` runs it for a
roadmap item before it creates the workflow file. Grill Me does not replace
clarification inside a workflow and is never called by autopilot or its phase
agents.

## Troubleshooting and recovery

- If a specification is vague, return to it and resolve its open questions;
  do not plan around ambiguity.
- If a plan conflicts with the constitution, change the plan or record a
  justified exception in the live artifact.
- If analysis finds a blocking inconsistency, fix the named artifact and rerun
  the relevant validation before implementation.
- If requirements change, update the affected specification and revisit
  downstream planning and tasks; do not patch code around a stale contract.
- If an installation is dirty or an upgrade reports modified files, preserve
  them and use the upgrade workflow's reviewed backup path.

## Team workflow

Review the constitution and feature specification before implementation starts.
Keep implementation, requirement changes, and verification evidence traceable
to the feature artifacts. A pull request should identify the artifact changes,
the checks actually run, and any intentional deviations rather than claiming a
gate passed without evidence.

For command-specific inputs, artifacts, and gates, read
[Command guide](./command-guide.md). For current preset or extension lifecycle
guidance, read [Presets & extensions guide](./presets-extensions-guide.md).
