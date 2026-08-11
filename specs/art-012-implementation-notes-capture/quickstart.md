# Quickstart: Verifying Implementation-Notes Capture (ART-012)

**Feature**: ART-012 | **Plan**: `specs/art-012-implementation-notes-capture/plan.md`

How to prove this feature works, end to end, from a clean worktree. Formats live
in `specs/art-012-implementation-notes-capture/contracts/`; entity rules live in
`specs/art-012-implementation-notes-capture/data-model.md`. This file is the run
guide.

## Prerequisites

Run everything from the repository root of the feature worktree, on branch
`art-012-implementation-notes-capture`.

* Python 3.11 or newer on `PATH`. Nothing else to install: the test suite is
  standard library and needs no bootstrap.
* Node 22.12 or newer and `pnpm`, **only** for the docs-site step. That surface
  needs `pnpm --dir docs-site install --frozen-lockfile` once per worktree.

## Baseline

Record the starting test count before changing anything:

```bash
python3 tests/speckit-pro/run-all.py
```

Expected at the start of this feature: **7226 passed, 0 failed** (Layer 1 1447,
Layer 4 5593, Layer 5 186). Do not recompute this number in a later session
against a tree that already contains this feature's additions; read it from
`docs/ai/specs/.process/ART-012-workflow.md`, which is where it is recorded.

The finish line is the same command passing with zero failures and a **higher**
total.

## Scenario 1: The reporting field is in all four touchpoints

Covers FR-001, US2, SC-003.

```bash
grep -n 'Deviations/Edge cases/Surprises' \
  speckit-pro/skills/speckit-autopilot/references/tdd-protocol.md \
  speckit-pro/agents/implement-executor.md \
  speckit-pro/codex-agents/implement-executor.toml
```

Expected: the exact line
`**Deviations/Edge cases/Surprises:** None (or describe)` in all three files,
plus one further hit in `speckit-pro/agents/implement-executor.md` where the
Terminal Deliverable sentence now names five fields instead of four. Four hits
across three files.

Scope the grep to those three files rather than sweeping `speckit-pro/`. A
tree-wide search also matches both phase-execution documents, which name the
field on purpose because the orchestrator reads it out of the summary. Those
hits are Scenario 2's subject, not extra copies of the template.

Then confirm nothing else grew a copy of the block:

```bash
grep -rln 'Task Result: <TASK_ID>' speckit-pro/
```

Expected: exactly those three files. A fourth would be a copy that silently
skips the field.

## Scenario 2: Both platforms describe the same record

Covers FR-002, FR-003, FR-004, FR-005, US1.

```bash
grep -n 'implementation-notes.md' \
  speckit-pro/skills/speckit-autopilot/references/phase-execution.md \
  speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md
```

Expected in **both** files: the record path, the
`# Implementation Notes: <SPEC_ID>` header, the `### <TASK_ID>` entry heading,
the create-if-absent rule, the additive-only rule, and the fail-open rule with
its four properties: the gap names the attempt or lifecycle step plus the
operation that failed, the write is never retried, the fallback is exactly one
level deep, and the blast radius is the single entry that failed. The
Claude file additionally describes the two-branch cadence; the Codex file keeps
its own per-result cadence. Wording differs there by design, per FR-005.

## Scenario 3: The automated contract check passes

Covers every rule in both contract files.

```bash
python3 tests/speckit-pro/unit/test-implementation-notes-record.py
```

Expected: all assertions pass. This is the test that would have caught a partial
fix, so run it against the tree *before* the source edits once, and confirm it
fails for a real reason, not an import error.

Confirm it is wired into the suite, not just runnable by hand:

```bash
python3 -c "import json; m=json.load(open('tests/speckit-pro/suite-manifest.json')); print([s['label'] for L in m['layers'] if L['id']=='4' for s in L['scripts'] if 'implementation-notes' in s['path']])"
```

Expected: a single label, not an empty list. An unregistered test is invisible to
the runner.

## Scenario 4: Generated payloads match source

Covers the repository's generated-artifact contract. Skipping this is the most
likely way to finish the feature and still fail CI.

```bash
python3 scripts/refresh-release-artifacts.py
git status --short dist/
```

Expected: the five production files' payload copies show as modified under both
`dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`. Never hand-edit them.

One command covers both generated surfaces here, and it is **not**
`python3 scripts/build-plugin-payloads.py` on its own: that builder rebuilds the
payloads only and leaves the installed-cache fixtures and the proof hashes
stale. `refresh-release-artifacts.py` rebuilds both payloads, content-syncs
`tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/{claude,codex}/speckit-pro/`,
and refreshes the `source_payload_tree_hash` values in both
`docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` and its mirror
`tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof.json`,
which must stay byte-identical JSON. It is idempotent: a second run on the same
source makes no further change.

If a file copy looks unchanged when it should not be, the copy compared
timestamps rather than contents. Compare by checksum.

## Scenario 5: The docs reference is current

Adding a test file changes the generated test reference page.

```bash
pnpm --dir docs-site install --frozen-lockfile   # once per worktree
pnpm --dir docs-site reference:generate
git status --short docs-site/src/content/docs/reference/
```

Expected: `tests.md` shows as modified, listing the new test.

## Full gate

```bash
python3 tests/speckit-pro/run-all.py
```

Expected: zero failures, total above 7226.

What each layer catches if a step above was skipped:

| Skipped step | Failure |
|---|---|
| Payload rebuild | Layer 1 `validate-plugin-payload`, `validate-payload-completeness`, `validate-payload-conformance` |
| Installed-cache refresh or hash update | Layer 4 gates test, reporting a stale `source_payload_tree_hash` |
| Suite-manifest registration | The new test simply never runs, and the total does not rise |
| Docs reference regeneration | The docs validation step reports a stale generated page |

## Manual acceptance

The scenarios above verify the contract as written. To watch it work, run
autopilot's implement phase for any spec with several tasks and read
`specs/<that-feature>/.process/implementation-notes.md`:

* It exists and carries its header, even if the phase was interrupted before any
  task finished.
* It holds one `### <TASK_ID>` entry per collected attempt, including research
  and verification attempts, whose entries read `None`.
* A retried task has two entries, and the first is unchanged.
* Resuming the phase appends after the existing entries and writes no second
  header.

## Path hygiene

Every path written into any artifact under
`specs/art-012-implementation-notes-capture/` is repository-relative. Absolute
paths containing a home directory fail the repository privacy scan. Check before
committing:

```bash
grep -rnE '/(Users|home)/' specs/art-012-implementation-notes-capture/
```

Expected: no output.
