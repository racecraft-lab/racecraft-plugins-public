# SPEC-FIXTURE-TASKS — Trivial feature for L7 Tasks-phase smoke

> L7 fixture spec for the Tasks-phase dispatch test. Plan-phase output
> is inlined below to keep the fixture self-contained.

## Feature

Add a `--quiet` flag to a hypothetical CLI tool. When set, the tool
suppresses non-error output.

## Plan summary (provided as if /speckit.plan had run)

- Add CLI flag parsing entry for `--quiet`.
- Wrap the tool's standard print path in a quiet-mode guard.
- Tests: one for normal output, one for quiet mode.

## Acceptance

- `tool --quiet` exits 0 with no stdout.
- `tool` prints normal output.
