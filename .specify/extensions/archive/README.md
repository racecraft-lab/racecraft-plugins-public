# Spec-Kit Archive

A Spec-Kit extension for archiving merged feature specs into project memory,
recording review provenance, and safely clearing completed specs from active
`specs/**` only when cleanup gates pass.

## Overview

The `speckit.archive.run` command is a post-merge archival and Archive Sweep
tool. It consolidates finalized feature specifications, plans, technical
decisions, and task evidence into `.specify/memory/`, then reports whether a
completed spec can safely leave active `specs/**`.

This Racecraft fork keeps the original memory-consolidation behavior and adds:

- Archive Sweep mode for pre-autopilot discovery of previously merged specs.
- Current-target exclusion so the spec currently being implemented is never
  archived or cleaned up in the same run.
- Dry-run/apply separation for provenance-only checks versus file edits.
- Gated cleanup with `safeToApplyCleanup` and `dryRunProvenanceOnly` outcomes.
- Recovery commands such as
  `git show <merge-sha>:specs/<feature>/spec.md`.
- CI, Argos, metadata-gate, artifact-manifest, and screenshot-retention
  provenance fields.
- A no-history-rewrite policy. Cleanup must happen through normal tracked file
  changes and must not rely on post-merge CI mutating `main`.

## Installation

Install the Racecraft fork from a pinned tag:

```bash
specify extension add archive --from https://github.com/racecraft-lab/spec-kit-archive/archive/refs/tags/v1.1.0.zip
```

You can also pin a specific commit archive when a project requires exact source
provenance:

```bash
specify extension add archive --from https://github.com/racecraft-lab/spec-kit-archive/archive/<commit-sha>.zip
```

## Usage

Archive one merged feature into project memory:

```bash
/speckit.archive.run specs/007-invoice-settings --pr-url https://github.com/org/repo/pull/123 --merge-sha <sha> --ci-url <url> --argos-url <url>
```

Run Archive Sweep before starting the next spec:

```bash
/speckit.archive.run --sweep --current-target specs/008-next-feature --dry-run
```

Apply cleanup only when every gate passes:

```bash
/speckit.archive.run specs/007-invoice-settings --merge-sha <sha> --apply-cleanup
```

Scope modifiers are still supported:

- `--spec-only`: update only `.specify/memory/spec.md`
- `--plan-only`: update only `.specify/memory/plan.md`
- `--changelog-only`: update only `.specify/memory/changelog.md`
- `--agent-only`: update only the agent knowledge file

## Safety Model

Cleanup never runs by default. A completed spec can leave active `specs/**` only
when all of these are true:

- `--apply-cleanup` was provided.
- The target is not the current active spec.
- The feature is already merged and has a PR URL plus merge commit or tree
  reference.
- The archive report includes raw recovery commands.
- The worktree is clean and on a safe base branch.
- The operation does not rewrite git history.
- The operation does not depend on post-merge CI mutating `main`.

If any gate fails, the command reports `safeToApplyCleanup=false` and
`dryRunProvenanceOnly=true`.

## Workflow

1. Resolve repository and feature paths with the core SpecKit prerequisite
   script.
2. Record branch, worktree, remote, and mode evidence.
3. Run Archive Sweep when requested, excluding the current target.
4. Analyze feature artifacts and constitution compliance.
5. Produce an impact map before edits.
6. Merge non-conflicting content into `.specify/memory/`.
7. Record PR, merge/tree, CI, Argos, metadata, artifact, and screenshot
   provenance.
8. Print recovery commands for raw artifact retrieval.
9. Apply cleanup only when explicitly requested and safe.

## Provenance Output

Reports include:

- source spec path
- PR URL
- merge commit or tree reference
- CI run URL
- Argos build or review URL
- metadata gate outcomes
- artifact manifest references
- screenshot retention and expiration risk
- cleanup mode and blocked gates
- `git show` recovery commands

Generated screenshots are treated as review artifacts by default. Preserve their
Argos/CI provenance and manifest references rather than committing large binary
payloads into durable project memory.
