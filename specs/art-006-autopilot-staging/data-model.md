# Phase 1 Data Model: Autopilot Staging

The feature adds no database and no new file. It adds one field to two files that
already exist, and a status value to entries in a list that already exists. This
document fixes the vocabulary, the authority order, and the write cadence, so the
Tasks phase has something unambiguous to decompose.

## Entities

### Stage

A closed enumeration. Exactly three literal lowercase tokens, used identically
for the invocation argument value and for the recorded entry — no aliases, no
alternate casing, no long-form spellings (spec.md:157-164).

| Token | Phase range | Terminal step |
|---|---|---|
| `plan` | Specify, Clarify, Plan, Checklist, Tasks, Analyze | G6.5 confidence gate, then the stage-boundary commit |
| `implement` | Implement, then the post-implementation steps | Post: Retrospective |
| `full` | All seven phases end to end | Post: Retrospective |

Any other value is rejected at opening preparation with a message naming the
accepted values (FR-007). There is no fourth token for "no run yet" — that state
is expressed by the entry's **absence** (FR-008a).

**Consumed downstream** by ART-007 through ART-012, which is why the spelling is
a cross-spec contract rather than local prose (spec.md:161-164).

### Workflow file — the authoritative durable store

Path: `docs/ai/specs/.process/<SPEC-ID>-workflow.md`. Survives archiving of
`specs/<id>/`, which is why it, and not the state file, holds per-spec history.

| Field | Location | Type | Required | Meaning |
|---|---|---|---|---|
| `Stage` | `\| **Stage** \| <token> \|` row in `### Basic Information` | Stage token | **No** | The last *resolved* stage of the most recent run. Not stage completion. |
| Phase status rows | `## Workflow Overview` table, column 3 | closed status vocabulary | Yes | Per-phase completion; the input to auto-detection. |
| Gate evidence | Anywhere outside the two tables above | free text matched by the gate-record patterns | Yes | `G1`–`G7`, `G6.5` PASS records. |

**Absence of `Stage` is legal and is not an error.** Fifty-six of the fifty-seven
workflow files in the tree carry no entry (spec.md:206-210), so a
required-everywhere rule would fail the suite against pre-existing files on the
day it ships. Absence resolves through ordinary auto-detection.

The `### Basic Information` table is a scalar `| Field | Value |` table, already
parsed for `Branch` by `speckit-pro/skills/speckit-status/SKILL.md:96`. The
`## Workflow Overview` table is not a candidate: two validators read its row
shape (`validate-workflow-status-evidence.py:238-261`,
`validate-autopilot-phase-coverage.py:3878-3921`).

### Session state file — the derived mirror

Path: `<workflow-dir>/autopilot-state.json`. A single-slot, current-in-flight
pointer for one run. Overwritten by the next run, so it is **never** per-spec
history (`speckit-pro/skills/speckit-autopilot/contracts/autopilot-state-status.schema.json`).

| Field | Type | Contract status today | Change |
|---|---|---|---|
| `workflow_file` | string | in use, guard-referenced | unchanged |
| `spec_id`, `feature_dir`, `branch` | string | in use | rewritten on slot reclaim |
| `status` | closed enum | **in the schema** | unchanged |
| `plan` | array of `{step, status}` | in use | out-of-stage entries take `skipped:` |
| `stage` | Stage token | **written today, absent from the schema** | **added to the schema** |
| `prior_run_note` | string | **written today, absent from the schema** | **added to the schema** |

`stage` and `prior_run_note` are both already present in the live state file at
`docs/ai/specs/.process/autopilot-state.json`. They are undocumented, which is
exactly what FR-012a forbids for the field that notes a reclaimed predecessor.
Adding them to `autopilot-state-status.schema.json` is what makes them part of
the contract. The schema object declares no `additionalProperties: false`, so the
addition is backward-compatible with every state file on disk, and
`validate_state_status` (`validate-autopilot-phase-coverage.py:3930-3945`) begins
closing the stage vocabulary as a side effect.

### Phase status entry

One row per phase in `## Workflow Overview`. The closed vocabulary is published
by the guard and mirrored by the CI validator — the two are asserted equal at
`validate-workflow-status-evidence.py:311-333`, so neither may drift alone.

- **Terminal**: `Complete`, `✅ Complete`, `Skipped`, `✅ Skipped`, `⏭ Skipped`,
  `⏭️ Skipped`
- **Open**: `Pending`, `⏳ Pending`, `In Progress`, `🔄 In Progress`, `Blocked`,
  `⚠ Blocked`, `⚠️ Blocked`

`Confidence Gate` is advisory — the main phase loop never drives it — so it is
excluded from the **ordering** rule (`validate-workflow-status-evidence.py:80-81`,
`ADVISORY_PHASES`). That exclusion is scoped to ordering and does not carry over:
per FR-006a the row **is** part of the planning-complete predicate that drives
auto-detection. The row is a first-class named phase in the same module's
`PHASE_GATE_IDS` map (`:68-77`, `"Confidence Gate": "6.5"`), so reading it costs
no new parsing.

### Canonical task entry

Never truncated per stage (spec.md:265-266). An entry outside the resolved stage
keeps its **byte-identical canonical name** and takes `skipped: <reason>` in its
**status** field. Four constraints, three of them verified against the shipped
validator:

1. Status field only. The coverage guard matches post-implementation checkpoints
   by exact name equality, so a `skipped:`-prefixed *name* reads as a missing
   checkpoint and fails every planning-stage run at the pre-final audit.
2. The marker text must not contain `pending` in any casing; the guard flags any
   string value containing it case-insensitively.
3. The shape reuses the established `skipped: <reason>` spelling already used for
   absent extensions (`references/task-list-canonical.md:3`, `:56`; Codex
   `SKILL.md:627`).
4. A planning-stage run marks the Implement phase **and every `Post:` entry**.
   The post-implementation family is where the audit actually blocks.

## Authority order

One rule, stated once, with no exception for this field:

```text
workflow file  Stage row        →  AUTHORITATIVE
autopilot-state.json  stage     →  MIRROR (repaired from the workflow file)
```

On disagreement the workflow file wins and the mirror is corrected
(spec.md:194-196). This clause is recorded on its own in the store-precedence
documentation at `speckit-pro/skills/speckit-autopilot/SKILL.md:661-680`. It is
**not** added to the two-item list at `:672-680`, which enumerates the fields for
which the *state file* wins — the opposite direction.

## State transitions

### Write cadence — at most twice per run

```text
opening preparation   → resolve stage → write workflow Stage row
                                      → write state mirror        (same edit turn)
                                      → both land in the SAME commit

  ...phases run; the Stage row is NOT refreshed on phase transitions...

plan stage only:
  G6.5 resolves        → if the resolved stage changed, write it again
                       → stage-boundary commit (after the gate, always non-empty)
```

The two stores are written in the same edit turn and land in the same commit, so
an interrupted run cannot leave a *committed* disagreement (FR-008b). The
terminal commit is non-empty regardless of whether `Stage` changed, because the
confidence-gate row always advances off its pending state — so the conditional
second write needs no empty-commit escape hatch (spec.md:217-220).

### Resolution

```text
                    ┌─ explicit --stage <token> present ─→ that token   (source: argv)
invocation argv ────┤
                    └─ absent ─→ read workflow ## Workflow Overview
                                   ├─ predicate satisfied ─→ implement
                                   └─ otherwise           ─→ plan
                                                          (source: auto-detect)

predicate = every one of these rows reads a TERMINAL status:
    Specify, Clarify, Plan, Checklist, Tasks, Analyze, Confidence Gate
  · an ABSENT Confidence Gate row does not block (legacy files)
  · a PRESENT but non-terminal Confidence Gate row does block
```

An explicitly named stage always overrides auto-detection, including when the two
disagree (FR-006). The resolution and its basis are reported before any phase
work begins.

The `Confidence Gate` row is in the predicate on purpose (FR-006a). A strict-mode
gate stop leaves the six planning rows terminal but that row **blocked**, so the
boundary the gate refused stays closed to a later bare invocation; crossing it
then requires an explicit `--stage implement`, which is the operator decision the
gate's own stop guidance describes.

### Slot reclaim

```text
ANY stage, state slot names a DIFFERENT specification
  → record the predecessor's status verbatim in the predecessor note
  → rewrite workflow_file, spec_id, feature_dir, branch, status, stage, plan
     FROM THE TARGET WORKFLOW FILE
  → report the reclaim; if the predecessor read `in_progress`, say so
  → THEN run the coverage guard
```

The trigger is any stage, not just `implement` (FR-012a): the guard's
workflow-identity check is inert for all of them, and neither distribution
documents state-file initialisation against a foreign slot. Recording the
predecessor's `status` (FR-012b) is what separates reclaiming a finished run from
reclaiming one still recorded `in_progress`. Neither case blocks — the state file
holds no liveness evidence — but only one of them is worth reporting.

Reclaiming is normal operation, not an error: the state file is defined as a
per-run pointer, and the previous specification's durable record is its own
workflow file. Ordering matters and is not merely a preference — the guard cannot
be relied on to catch a mismatched slot, because its workflow-identity check is
inert under the invocation the phase loop issues (spec.md:144-149, and
research.md "Known defect").

## Validation rules

| Rule | Where enforced | Failure mode |
|---|---|---|
| `Stage` value is one of three literals when present | Layer 1 CI validator + state schema | test failure / guard error |
| Absent `Stage` is legal | both | must **not** error |
| Mirror equals authority when both present | phase-coverage guard, `stage_mirror_errors` registered in the `status-evidence` tuple of `RULE_PROBLEM_KEYS` | guard exit 1 |
| Recorded stage vs. phase evidence contradiction | Layer 1 CI validator, tree-wide | test failure |
| Unrecognised or conflicting `--stage` | `resolve-autopilot-stage`, exit 2 | run STOPs before Phase 0 |
| Out-of-stage entries keep canonical names | new unit test, planning-stage fixture | test failure |

The in-run rule and the CI rule are two **different** checks, not the same check
twice: one asserts mirror freshness during a run, the other asserts at-rest
self-consistency across every workflow file in the tree whether or not an agent
invokes anything (FR-014). Neither is a new third validator.
