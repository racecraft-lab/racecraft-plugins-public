# Phase 1 Data Model: Draft-PR Emission (ART-007)

**Branch**: `art-007-draft-pr-emission` | **Date**: 2026-08-17

Six entities, drawn from the spec's Key Entities section. None of them is a
database record: this feature's state lives in a committed Markdown table, a
committed JSON packet, files on disk, and one in-memory helper result. Field
types below describe the JSON shape where the entity is machine-readable and the
Markdown shape where it is not.

---

## 1. Draft artifact set

The pages written into `specs/<branch>/artifacts/` for one plan stage.

| Field | Type | Rules |
| --- | --- | --- |
| `entry_id` | string | A gallery manifest `id` whose entry has `stage: "draft-pr"`. One of `implementation-plan`, `spec-explainer`, `code-approaches`, `module-map`. |
| `output_path` | string | `specs/<branch>/artifacts/<entry_id>.html`. Repo-relative, always. |
| `selected_by` | string | `always` or the signal name that fired: `competing_approaches`, `brownfield_change`. |
| `filled_slots` | string list | The `FILL:<slot>` names populated. Must equal the template's slot inventory for a page counted as generated. |
| `outcome` | enum | `generated` or `gap`. |
| `gap_reason` | string, null | Non-empty exactly when `outcome` is `gap`. |

**Cardinality**: zero to four pages. Zero is legal and must still open the PR
(FR-004, SC-003).

**Selection rule** (FR-002, routed from `speckit-pro/artifact-gallery/manifest.json`):

| Entry | Selected when |
| --- | --- |
| `implementation-plan` | always |
| `spec-explainer` | always |
| `code-approaches` | the feature carries `competing_approaches` |
| `module-map` | the feature carries `brownfield_change` |

**Validation**: an `output_path` outside `specs/<branch>/artifacts/` is rejected.
Templates are read-only inputs; a run that would write into
`speckit-pro/artifact-gallery/` is a defect.

**Not marked generated**: these files carry no `merge=generated` attribute and
are ordinary tracked files (research D9.3).

---

## 2. Draft review packet

The existing PR packet, in its new third mode. Stored at
`specs/<branch>/.process/pr-packets/<packet-id>.json` — the canonical path the
packet helpers already enforce.

**Delta from the shipped contract only** (full field list lives in the shipped
schema; the contract file `contracts/draft-packet-mode.md` carries the exact
edits):

| Field | Shipped rule | Draft-mode rule |
| --- | --- | --- |
| `mode` | `enum: ["single", "split"]` | gains `"draft"` |
| `verification_evidence` | required, `minItems: 1` | not required in draft mode |
| `scope_evidence.changed_files` | required, `minItems: 1` | not required in draft mode |
| `uat.how_to_uat` | required, `minLength: 1` | not required in draft mode |
| `required_headings` | the eight implementation headings | the two FR-008 blocks |
| `split_slice` | required iff `mode == "split"`, forbidden otherwise | unchanged; draft mode must not carry it |
| `generated_title.value` | conventional-commit pattern | unchanged, and constrained to a lowercase scope (research D4) |
| `protected_body_fingerprint` | sha256 over the normalised body | unchanged |

**State transitions**:

```text
(absent) --emit--> draft --ART-010 upgrade--> single
                     |
                     +--FR-012 split--> split (first slice keeps this packet)
```

The packet identity is stable across every transition. That is what preserves the
review thread FR-012 protects.

**Invariant (SC-008)**: for `mode` values `single` and `split`, every validation
outcome is byte-identical before and after this feature.

---

## 3. Draft-PR record

One scalar row on the workflow file, the single authoritative answer to "which
pull request belongs to this feature".

**Location**: `## Specification Context` → `### Basic Information`, the same
`| Field | Value |` table that carries `Branch` and `Stage`. Never the
`## Workflow Overview` table, whose rows are phase status records (FR-009).

**Shape**:

```text
| **Draft PR** | [#438](https://github.com/<owner>/<repo>/pull/438) |
```

With a shortfall note (FR-004):

```text
| **Draft PR** | [#438](https://github.com/<owner>/<repo>/pull/438) — 2 of 3 artifacts generated |
```

| Field | Type | Rules |
| --- | --- | --- |
| `number` | integer | Parsed from the link text, which is `#<number>`. |
| `url` | string | The link target. The pull request's canonical URL. |
| `gap_note` | string, null | Free prose after the link in the same cell. Optional. |

**States**:

| State | Meaning | Legal |
| --- | --- | --- |
| absent | no pull request has been opened | yes, and never an error (FR-009) |
| present | a pull request exists at that identity | yes |

**Write rules**:

- Written only after creation or refresh succeeds.
- Carried by the separate bookkeeping commit, never folded into the
  stage-boundary commit (FR-013).
- Left unchanged under `pr_closed` and `pr_missing` (FR-011).
- Never shipped as a placeholder in the scaffold template (FR-009). HTML comments
  are blanked before the table is parsed, so a commented-out example row would
  not be read as evidence anyway.

**Parsing**: mirrors the shipped `Stage` row reader — same table, same
`strip("*` ")` cell handling, casefold comparison against `draft pr`.

---

## 4. Artifacts index

The table in the pull request description mapping each artifact to its purpose
and a command that opens it locally.

| Column | Source |
| --- | --- |
| Artifact | the gallery entry's `title` |
| Purpose | the gallery entry's `when_to_use`, trimmed to one line |
| Open | a copy-paste command naming `specs/<branch>/artifacts/<entry_id>.html` |

**Gap row** — one per page that failed, and one covering the whole set when zero
pages were produced:

| Artifact | Purpose | Open |
| --- | --- | --- |
| Module Map | *(not generated)* | Gap: template fill failed |

**Rules**: the index lists 100% of generated artifacts (SC-002). A run with zero
generated artifacts emits a table containing only gap rows; it is never omitted
and never empty.

---

## 5. Stop report

The plan stage's terminal message to the operator. Printed prose, not a stored
artifact, composed in the same one-line style Step 0.6c already uses.

**Four shapes, selected by outcome**:

| Outcome | Carries |
| --- | --- |
| emitted (gate pass or warn) | the PR URL, the artifact index, resume instructions |
| gate blocked (strict mode) | the blocked gate's name in place of a URL; no PR |
| creation failed | that the PR could not be opened, and the resume path; artifacts are already committed |
| corroboration discrepancy | the status, the recorded identity, and the manual resume path for that status |

**Rule (SC-006)**: the stop report alone is sufficient. The operator needs no
follow-up action to hand off for review.

---

## 6. Corroboration outcome

The result of comparing the draft-PR record against the live pull request.
Returned inside the stage-resolution result; never stored on its own.

| Field | Type | Rules |
| --- | --- | --- |
| `status` | enum | Exactly one of `match`, `no_record`, `skipped`, `pr_closed`, `pr_missing`, `identity_mismatch`. |
| `recorded` | object, null | `{number, url}` from the `Draft PR` row. Null when the row is absent. |
| `observed` | object, null | `{number, url, state}` from the observation. Null when nothing was observed for the recorded number. |
| `merged` | boolean, null | Meaningful only under `pr_closed`. Null otherwise. |
| `reason` | string, null | Populated only under `skipped`. Names why the check could not run. |

**Discrepancy partition**: `pr_closed`, `pr_missing`, and `identity_mismatch` are
discrepancies. `match`, `no_record`, and `skipped` are not.

**Classification precedence** — first match wins, evaluated only against a
successful, parseable observation:

1. An open pull request on the head branch whose number differs from the
   recorded number → `identity_mismatch`.
2. A recorded number that is open but whose live URL differs from the recorded
   URL → `identity_mismatch`.
3. A recorded number whose live state is closed or merged → `pr_closed`,
   carrying `merged`.
4. A recorded number absent from the observation → `pr_missing`.
5. Anything else → `match`.

**Preconditions**: `no_record` when the row is absent — no observation is taken
and no classification runs. `skipped` for every unsuccessful or unparseable
observation, with the reason recorded.

**Durability**: always reported on the envelope and on one run-report line.
Recorded durably in the workflow file only for the three discrepancy statuses,
written in the same edit turn as the `Stage` row so it lands in the same commit.

**Authority**: the workflow file wins in every outcome. Corroboration never
changes the resolved stage, never blocks resolution, never stops the run, and
never mutates GitHub — no reopen, no second pull request.
