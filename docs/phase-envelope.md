# Phase envelope

A phase driver returns one fixed result, the phase envelope. The runner owns
its contract (`ENVELOPE_SCHEMA` in `helpers/phase_envelope.py`) and the
`verify-phase-envelope` read-only helper that checks it against the disk.

The envelope holds the phase, a status (`pass`, `fail`, `blocked`), the next
action, changed artifact paths, gate ids with results, counts, one blocker line
of at most 240 characters and a usage receipt. The serialized envelope may not
exceed 2,048 UTF-8 bytes; an envelope over the cap fails before any other check.

The helper never trusts a claim. It checks, in order, and returns the first
mismatch: the contract, every artifact path (repository-relative, present,
non-empty, no links out; a directory must hold an entry), that the phase's own gate is claimed, that every file a claimed gate reads
(its sources, the workflow, and every file G4 reports it judged) is present, non-empty and valid UTF-8
whatever the driver listed, every claimed
gate re-run through `validate-gate` against the files on disk, that a `pass`
status carries no failed gate, that the driver did not report a failure, and
that the `markers` and `task_count` counts equal what the gate reports. A gate
whose evidence is missing, unreadable or not a boolean verdict fails the phase.
A claimed failure that the disk contradicts is also a mismatch.

A pass is `{verdict, phase, next_action}`. A mismatch is `expected_failure`
with `{verdict: "fail", mismatch: {code, detail}}`.

## Known limits

- Only nested mode (ADR 0026) returns and consumes an envelope: the
  `phase-executor` driver returns one and the autopilot calls the helper before
  it advances. Flat mode never calls it.
- The runner answers `advance` (true only on a pass) on every verified
  answer. The autopilot's `autopilot-state.json` write is still the model's, so
  the rule that a failed phase does not advance is a runner answer plus skill
  text, and no runner code blocks a model that ignores it.
- Re-verification covers the gates `validate-gate` decides from files. It does
  not re-derive a driver's usage receipt, which the runner cannot observe.
- Directory artifacts are checked through an opened descriptor, not against a
  historical inode identity. A populated, confined replacement before opening
  satisfies the present/non-empty contract; replacement after opening cannot
  redirect the listing to another directory.
- When trusted descriptor reads are unavailable, directory artifacts fail
  closed as `artifact_missing`. The descriptor cleanup tests require that
  platform capability; they do not exercise the unsupported-platform fallback.
