# Contract: The `Draft PR` Workflow-File Row

**Owner surface**:
`speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md`
(Claude protocol home),
`speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md`
(Codex protocol home), and the reader in
`speckit-pro/speckit_pro_runner/helpers/read_only.py`.

Satisfies FR-009, and supplies the recorded identity FR-011 corroborates.

---

## 1. Placement

The row lives in `## Specification Context` → `### Basic Information`, the scalar
`| Field | Value |` table that already carries `Branch` and `Stage`.

It does **not** go in `## Workflow Overview`. That table's rows are phase status
records with `Phase | Command | Status | Notes` columns; a pull-request identity
is neither a phase nor a status, and adding it there would break every reader
that treats those rows as phase records.

---

## 2. Grammar

```text
| **Draft PR** | [#<number>](<url>) |
| **Draft PR** | [#<number>](<url>) — <gap note> |
```

| Part | Rule |
| --- | --- |
| key | `Draft PR`, compared case-insensitively after stripping `*`, backticks, and spaces |
| value | begins with one Markdown link; link text is `#<number>`, link target is the pull request URL |
| gap note | optional free prose after the link, in the same cell |

The number and the URL are one linked reference, not two columns. Readers take
the number from the link text and the URL from the link target.

---

## 3. States

| State | Meaning | Legal? |
| --- | --- | --- |
| row absent | no pull request has been opened for this feature | yes — never an error, never reported as one |
| row present | a pull request exists at that identity | yes |

The absent state is the same shape the shipped `Stage` row already uses for "no
run yet". Consumers must treat a missing row as information, not as a fault.

**The scaffold workflow template ships no placeholder row.** This follows the
`Stage` precedent exactly: `Stage` appears nowhere in
`speckit-pro/skills/speckit-coach/templates/workflow-template.md`, and neither
will `Draft PR`. A commented-out example would not help either — HTML comments
are blanked before the table is parsed, so it could never be read as evidence.

---

## 4. Write rules

| Rule | Detail |
| --- | --- |
| when | only after creation or refresh succeeds |
| which commit | the separate bookkeeping commit of FR-013, never the stage-boundary commit |
| repair | when a pull request exists but the row is missing or wrong, the row is written or repaired |
| leave alone | under `pr_closed` and `pr_missing`, the row is left exactly as found |
| sole store | this row is the only place the identity is stored — no state-file mirror |

The last rule is the inherited OQ-4 decision: the workflow file is authoritative,
and a second sink would introduce the status-versus-evidence drift the coverage
guard and the tree-wide CI gate already fail on.

---

## 5. Reader

A new `workflow_draft_pr_row(lines)` sits beside the shipped
`workflow_recorded_stage(lines)` and reuses `workflow_table_rows` and
`AUTOPILOT_BASIC_INFO_HEADING` unchanged. It returns the parsed
`{number, url, gap_note}` or `None` when the row is absent.

The two readers differ only in the key they match. That is three near-duplicate
lines rather than a premature generic `workflow_scalar_row(lines, key)`
abstraction, which is the trade the constitution's KISS and YAGNI principle asks
for until a third caller exists.

---

## 6. Documentation obligations

| File | Change |
| --- | --- |
| `speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md` | a `## The `Draft PR` Entry` section modelled on the adjacent `## The `Stage` Entry` — placement, grammar, states, write rules |
| `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md` | the same rules, in the Codex mirror's own voice, beside where it already documents the `Stage` row |
| `speckit-pro/skills/speckit-coach/templates/workflow-template.md` | **no change** |

The asymmetry is not an oversight. The Codex mirror
`workflow-file-protocol-codex.md` carries no `Stage` entry section at all; Codex
documents the `Stage` row inside `phase-execution-codex.md`. Following each
platform's existing home keeps both readable and costs one file per platform.

---

## 7. Test obligations

| Obligation | Where |
| --- | --- |
| A present row parses to the right number, URL, and gap note | `tests/speckit-pro/unit/test-autopilot-stage-resolution.py` |
| An absent row returns `None` and is not an error | same |
| A commented-out row is not read as present | same |
| A row with a gap note after the link still parses the identity | same |
| A malformed value yields `None` rather than a traceback | same |
