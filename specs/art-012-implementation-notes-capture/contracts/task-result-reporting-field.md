# Contract: Task Result Reporting Field

**Feature**: ART-012 | **Covers**: FR-001, US2, SC-003 | **Consumers**: every
implementation executor, and the orchestrator that reads the returned summary

This is the exact text the implementation must produce, in every authored copy
of the `## Task Result: <TASK_ID>` block. The Layer 4 test asserts against these
strings.

## The line

```text
**Deviations/Edge cases/Surprises:** None (or describe)
```

It is the **last line** of the Task Result block, immediately after
`**Errors:** None (or describe)`, separated by one blank line like every other
field in the block.

The shape deliberately mirrors the existing `**Errors:**` line. The field name
already enumerates the three things being asked for, so no longer hint is
needed, and matching the neighbouring line's shape is what the repository's
style rules ask for.

## Resulting block

```text
## Task Result: <TASK_ID>

**TDD Evidence:**
- Tests written: N
- RED verified: N failed (real assertion errors)
- GREEN verified: N passed
- REFACTOR: tests stayed green / N/A

**Test commands used:**
- Unit/contract: <command>
- Integration: <command> (if applicable)

**Files created/modified:**
- path/to/file (created/modified)

**Errors:** None (or describe)

**Deviations/Edge cases/Surprises:** None (or describe)
```

Every line above `**Deviations/Edge cases/Surprises:**` keeps its exact existing
text and position in each file. The three copies differ from each other today in
their TDD Evidence and Test commands wording; this contract does not harmonise
them, it only appends the new line to each.

## Where it lands: four touchpoints, three files

| # | File | Touchpoint | Current anchor |
|---|---|---|---|
| 1 | `speckit-pro/skills/speckit-autopilot/references/tdd-protocol.md` | Summary Format template | `**Errors:**` at `:139`, block ends `:140` |
| 2 | `speckit-pro/agents/implement-executor.md` | Summary Format template | `**Errors:**` at `:157`, block ends `:158` |
| 3 | `speckit-pro/agents/implement-executor.md` | Terminal Deliverable enumeration | `:164` |
| 4 | `speckit-pro/codex-agents/implement-executor.toml` | Summary Format template | `**Errors:**` at `:139`, block ends `:140` |

Touchpoint 3 is prose, not a template. It currently reads, in part:

```text
the complete structured Task Result above (TDD Evidence / Test commands used / Files created/modified / Errors)
```

It must name five fields after this change, ending with
`Deviations/Edge cases/Surprises`. Leaving it at four ships an agent whose hard
`MUST` contradicts its own template. This is the one partial fix that passes CI
green and still violates FR-001, because no Layer 1 test diffs Summary Format
content across platforms.

## Values

| Situation | Value |
|---|---|
| The executor has something to report | Its own text: deviations from plan, edge cases discovered, surprises. Free prose, may span lines. |
| The executor has nothing to report | The literal word `None`. Never an omitted line, never an empty value. |

One combined field. Not three separate mandatory fields, and not a second
`## Implementation Notes: <TASK_ID>` block. An executor learns no second
reporting format.

## Platform parity

Identical on both supported platforms. This is the half of the feature where
identical wording *is* required and *is* achievable: the field is a static
template line, not a description of dispatch mechanics. FR-005's
"parity on the record, not the wording" carve-out applies to the orchestrator's
append instructions, never to this field.

## What the Layer 4 test asserts

1. All three files contain the exact line
   `**Deviations/Edge cases/Surprises:** None (or describe)`.
2. In each file, that line follows the file's `**Errors:**` line and is the last
   field of the Task Result block.
3. `speckit-pro/agents/implement-executor.md`'s Terminal Deliverable enumeration
   names `Deviations/Edge cases/Surprises` alongside the four existing fields.
4. The set of files carrying a `## Task Result: <TASK_ID>` block **under
   `speckit-pro/`** is still exactly these three, so a fourth copy added later
   cannot silently skip the field.

   **Two discriminators are required, and neither is sufficient alone.**

   *Scope to `speckit-pro/`*, the authored plugin source. A tree-wide search
   also matches the generated payload copies under `dist/` and the
   installed-cache fixture copies under
   `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/`,
   which are regenerated from these three and are never authored. Measured on
   the implemented tree: 12 files tree-wide against 3 scoped.

   *Anchor at line start.* Match `^## Task Result: <TASK_ID>` as an actual
   Markdown heading, not the bare substring. A file that CARRIES the template
   writes the heading at column 0; a file that merely NAMES the block writes it
   backticked inside a sentence. Two files name it without carrying it, both
   because of FR-006, which is the requirement that teammates send that block:
   `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` and
   `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md`.
   Those two must NOT grow the reporting field. Measured on the implemented
   tree: a scoped substring search returns 5 files, a scoped line-anchored
   search returns 3.

   > **Revision note, 2026-08-11.** This item originally specified scoping
   > alone, and was written before FR-006 existed. FR-006 necessarily causes
   > other documents to name the block, which made a scoped substring search
   > report 5 rather than 3. The item's intent is unchanged; only the mechanism
   > is sharper. Caught during implementation, before the check was authored.
