# Feedback-sweep deny-set corpus

Eight documents, frozen. `../../../test-feedback-sweep-parse.py` reads them.

## What they are

The planning documents of SPEC-80 slice 1, copied verbatim from
`specs/spec-808-feedback-sweep/` at commit `32043c45a60e7c38d15f0958bc4874f0362ea505`
when that spec was archived on 2026-08-25.

## Why they are real prose and not a written fixture

They carry the deny-set's own negative examples — text that *looks* like a
secret and is not. A scanning rule loosened back to a substring match fires here
before it fires on a reviewer's amendment. A fixture written to pass could not
do that, because whoever wrote it would write around the very rules it exists to
catch. These documents were authored with no knowledge of what the rules would
become, and that is the whole property.

## Do not refresh them

Drift from any later spec is not decay, it is the point. Refreshing from current
prose would replace text written in ignorance of the rules with text written by
someone who knows them, which is the failure above. They are frozen.

They are also not a spec: nothing here is a live planning artifact, and no
archive procedure should treat this directory as one.

## Verifying the copy is untouched

```text
git diff 32043c45a60e7c38d15f0958bc4874f0362ea505:specs/spec-808-feedback-sweep/spec.md \
  tests/speckit-pro/unit/fixtures/feedback-sweep/corpus/spec.md
```

The same holds for `plan.md`, `tasks.md`, `data-model.md`, `research.md`,
`quickstart.md`, and both files under `contracts/`. An empty diff means the
corpus still says what it said when it was captured; a non-empty one means
someone edited the negative examples, which silently weakens the deny-set.

`quickstart.md` doubles as slice 1's acceptance record, cited from
`docs/ai/specs/.process/SPEC-80-workflow.md`.
