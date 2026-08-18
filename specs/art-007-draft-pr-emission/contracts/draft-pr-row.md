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

**The separator is excluded from the note.** In the second form the ` — ` between
the link and the note is grammar, not content: a gap note of
`2 of 4 artifacts missing` renders as `— 2 of 4 artifacts missing` and parses
back without the em dash. Only the em dash form is specified. A hyphen, an en
dash, or prose following the link with no separator at all is **undefined** —
readers may treat it however they like, and writers must not emit it.

**The link target admits no whitespace and no parentheses**, which is what keeps
a gap note's own punctuation out of the URL. A note may itself contain
parentheses or a second Markdown link — `— selection failed (no pages chosen)` is
legal — so a reader that captures the target greedily swallows the note and
corrupts the identity rather than merely losing the note. An empty target,
`[#438]()`, is malformed.

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
| whole value | every write rewrites the whole cell from the current run's outcome, so a stale gap note never survives a refresh that no longer fell short |
| leave alone | under **every** discrepancy — `pr_closed`, `pr_missing`, and `identity_mismatch` — the row is left exactly as found. FR-011 states this for all three; naming only the first two, as this row previously did, reads as licensing a rewrite in the third |
| sole store | this row is the only place the identity is stored — no state-file mirror |
| independent of `Stage` | writing this row neither counts against nor re-triggers the `Stage` row's own write cadence, and needs no state-file write, because this identity has no mirror |

The last rule is the inherited OQ-4 decision: the workflow file is authoritative,
and a second sink would introduce the status-versus-evidence drift the coverage
guard and the tree-wide CI gate already fail on.

---

## 5. Reader

A new `workflow_draft_pr_row(lines)` sits beside the shipped
`workflow_recorded_stage(lines)` and reuses `workflow_table_rows` and
`AUTOPILOT_BASIC_INFO_HEADING` unchanged.

**Signature and return shape**, stated here because §2's grammar alone does not
fix the types:

```python
def workflow_draft_pr_row(lines: list[str]) -> dict[str, Any] | None
```

| Case | Returns |
| --- | --- |
| row present | `{"number": int, "url": str, "gap_note": str | None}` — all three keys always present |
| row present, no note | the same, with `gap_note` as `None` |
| row absent | `None` |
| value malformed | `None`, never a raise |

`number` is an **integer**, matching the `Draft PR Record` entity in
`data-model.md`. This is load-bearing rather than cosmetic: FR-011's
corroboration compares the recorded number against the number a `--json` query
returns, and a string would silently never match, producing a permanent
`identity_mismatch` on a healthy pull request.

**The reader takes lines that are already comment-blanked.** Callers apply
`HTML_COMMENT_RE` before calling, exactly as `workflow_stage_signals` already
does for the `Stage` row. The reader must not blank again — that is what
"reuses `workflow_table_rows` unchanged" means, and it is why a commented-out row
is not read as present.

The two readers differ only in the key they match and in parsing a linked value
rather than a bare scalar. Keep them as siblings rather than introducing a
generic `workflow_scalar_row(lines, key)`, which is the trade the constitution's
KISS and YAGNI principle asks for until a third caller exists. That is an
anti-abstraction instruction, not a line budget: the linked value needs a match
and a record build, so this reader is legitimately longer than
`workflow_recorded_stage`.

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
