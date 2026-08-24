# Contract: `check-artifact-freshness` runner helper

**Registration**: one `HelperEntry` in
`speckit-pro/speckit_pro_runner/helpers/registry.py`.
**Implementation**: `speckit-pro/speckit_pro_runner/helpers/read_only.py`.
**Mode**: `read_only`. **Promotion**: `python_authoritative`.
**Comparison**: `python_only` — new behavior with no deleted `.sh` predecessor,
so there is no bash reference to compare against and no `source_script` to
record.

## Invariants, in force on every surface

1. **Read-only.** The helper writes no file, deletes no file, and takes no
   commit. It reports; the orchestrator acts (FR-004, FR-012a).
2. **Offline.** It never invokes `git`, never invokes `gh`, and never reaches
   the network (FR-004). Every git fact arrives as request data (FR-004a).
3. **One read path.** The workflow file it is given is the only path any
   surface reads (FR-004). No surface reads `specs/<feature>/artifacts/`, the
   gallery manifest, or any planning artifact.
4. **Standard library only.** Python 3.11+, no third-party import, no Bash, no
   `jq`, no subprocess (FR-028).
5. **Deterministic.** The same request produces the same envelope every time,
   which is what lets fixtures replace a live sweep (SC-005).
6. **No CLI arguments are derived.** The whole request arrives on stdin. The
   argument-derivation branch returns `[]`, following `sweep-pr-feedback`.
7. **It never selects and never decides.** Page selection stays with the
   emission machinery (FR-004); the stop-or-proceed decision stays with the
   orchestrator.

## Request envelope

```json
{
  "schema_version": "1.0",
  "helper_id": "check-artifact-freshness",
  "operation": "check-artifact-freshness",
  "mode": "read_only",
  "inputs": { "named_surface": "verdict", "...": "per surface, below" }
}
```

`named_surface` is one of `verdict`, `removal_diff`, `corroborate_refresh`. An
**absent** or explicit-`null` value means `verdict`, following
`sweep_pr_feedback`'s rule that a caller assembling the object programmatically
writes the key with a null where a caller writing it by hand omits it. The
empty string is a value outside the three and is an input error, so the test is
`is None` rather than truthiness. **A fourth value is a malformed request**, not
a surface to discover: the set is closed in the module.

`workflow_file` is the only path input and is the only key registered in
`path_keys_by_helper`.

---

## Surface 1 — `verdict` (default)

### Inputs

| Key | Type | Required | Rule |
|---|---|---|---|
| `workflow_file` | string | yes | Repo-relative path. Resolved and boundary-checked by the shared prologue. |
| `artifacts_observation` | object | yes | See `data-model.md` §2. |

### Behavior

1. Read the workflow file. Unreadable is an input error (exit 2, one-line
   `error:` diagnostic), the same shape `sweep_parse` uses for the same case.
2. Validate `artifacts_observation`. **`ok` must be the JSON literal `true`.**
   Any other value is an unusable observation and returns the
   `undeterminable` verdict with reason `unusable_observation` — **not** an
   input error, because FR-023 forbids a failed gather from blocking the run.
3. Read the `Feedback Sweep Log` through the shipped heading-anchored table
   read: anchor on the heading text, break `inside` on any line starting with
   `#`, find the header row by column name, skip the table rule row.
4. For each row whose `Class` casefolds to `amended`, extract `#` and `Commit`
   under the dual-anchoring rule (`data-model.md` §1).
5. Join each `Commit` cell text **verbatim** against
   `artifacts_observation.amended_commits[].cell`.
6. Return one verdict from the closed four, in the precedence order
   `no_pages` → `stale` → `undeterminable` → `current`.

### Output

Per `data-model.md` §3. `pages` echoes the supplied inventory unchanged.

### Failure modes

| Condition | Result |
|---|---|
| `workflow_file` missing, blank, or unreadable | input error, exit 2 |
| `artifacts_observation` absent or not an object | input error, exit 2 |
| `artifacts_observation.ok` is not the literal `true` | verdict `undeterminable`, exit 0 |
| `artifacts_dir_state` outside the closed three | input error, exit 2 |
| no `Feedback Sweep Log` heading | zero `amended` rows; verdict decided by directory state alone |
| a row is malformed | that row is undeterminable and surfaced; the other rows still evaluate |

**The asymmetry is deliberate.** A malformed *request* is the caller's defect
and returns exit 2. A failed or unusable *observation* is a fact about the
world, and FR-023 says it may not block the run, so it returns a verdict that
acts on nothing.

---

## Surface 2 — `removal_diff`

### Inputs

| Key | Type | Required | Rule |
|---|---|---|---|
| `observed_pages` | array of strings | yes | Filename stems, the pre-regeneration inventory. |
| `reselected_pages` | array of strings | yes | Manifest re-selection's page ids, carrying **both** `generated` and `gap` outcomes. |

### Behavior

Return the members of `observed_pages` absent from `reselected_pages`, matched
by the manifest entry id kept as the filename stem. Reads no file. **Deletes
nothing** — the system performs the deletion, stages it in the FR-018 commit,
and reports each removal as its own outcome (FR-012, FR-012a).

Order is the order of `observed_pages`, so the output is stable and diffable.

### Failure modes

| Condition | Result |
|---|---|
| either array absent, not an array, or carrying a non-string | input error, exit 2 |
| `reselected_pages` empty | legal: every observed page is a removal. This is the whole-set-gap case, and FR-023 keeps it from blocking. |
| a stem appears in `reselected_pages` and not in `observed_pages` | ignored; that is a new page the author dispatch writes |

---

## Surface 3 — `corroborate_refresh`

### Inputs

| Key | Type | Required | Rule |
|---|---|---|---|
| `workflow_file` | string | yes | Same single read path. |
| `pr_observation` | object | no | The entry gate's five-field query result. Absent or unusable yields `skipped`, exactly as at the entry gate. |

### Behavior

Read the workflow file, blank its HTML comment spans, read the `Draft PR` row
with the shipped `workflow_draft_pr_row`, and classify it against
`pr_observation` with the shipped `corroborate_draft_pr`. **Both functions are
called verbatim; this surface adds no branch of its own.** That literal reuse is
the requirement: FR-034 assigns each status the behavior the ART-007 contract
already gives it, and that guarantee holds only when the same code decides the
status in both places.

The observation's query shape is fixed by FR-033a and is the entry gate's:

```text
gh pr list --head <branch> --state all --json number,url,state,isDraft,headRefName
```

`--state all` is load-bearing: it is what makes a closed pull request
distinguishable from an absent one, a distinction the reused create-or-refresh
machinery's own existence test cannot produce on its own.

### Output

Per `data-model.md` §5: the five-key corroboration record, all keys present on
every status.

### Failure modes

| Condition | Result |
|---|---|
| `workflow_file` missing or unreadable | input error, exit 2 |
| no `Draft PR` row | status `no_record` |
| `Draft PR` row malformed | status `no_record` — the shipped reader returns `None` on a malformed value rather than raising, because the workflow file is operator-edited prose |
| `pr_observation` absent, `ok` not literal `true`, or array malformed | status `skipped`, with the reason the request carried or a supplied default |

---

## Registration checklist

Five touch points, all measured against the `sweep-pr-feedback` precedent:

| Touch point | Location | Shape |
|---|---|---|
| Allowed path inputs | `read_only.py` near `:260` | `"check-artifact-freshness": {"workflow_file"}` |
| Argument derivation | `read_only.py` near `:356` | returns `[]`; the request arrives on stdin and no field is interpolated into a command |
| Dispatch table | `read_only.py` near `:5419` | `"check-artifact-freshness": check_artifact_freshness` |
| Registry entry | `registry.py` near `:196` | `HelperEntry(..., None, "python_authoritative", "python_only", authoritative_request(...))` |
| Inventory | `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` | append to `EXPECTED_HELPERS` (`:55-74`), add to `NO_BASH_ANCESTOR` (`:86`), add a `HELPER_CASES` entry |

**Two order-sensitive hazards.**
`tests/speckit-pro/unit/fixtures/read-only-helpers/fixture-manifest.json` is
compared for **exact list equality** against `EXPECTED_HELPERS` (`:396`), so the
new entry must sit in the same position in both. The same test asserts the
bash-reference id list equals `EXPECTED_HELPERS` minus `NO_BASH_ANCESTOR`
(`:397`), so omitting the `NO_BASH_ANCESTOR` addition fails that assertion
rather than the one a reader would expect.

## Layer 4 coverage obligations (FR-031, FR-033a)

Driven by fixtures, following the pattern
`tests/speckit-pro/unit/test-feedback-sweep-parse.py` established. Every case
below must be able to fail:

**Verdict surface**
- each of the four verdicts, reached on its own condition
- precedence: `no_pages` over a log full of `amended` rows; `stale` over a
  co-occurring undeterminable row
- FR-007a: pages present, `last_artifacts_commit` null, one joinable row → `stale`
- FR-008: an `amended` commit equal to the artifacts commit → `current`, with
  the abbreviated-cell / full-sha pairing that string equality would get wrong
- FR-009: an older row plus a newer row → `stale`; two older rows → `current`
- FR-006: missing, empty, unresolvable, and unmatched cells, each surfaced with
  its own reason and its own row `#`
- **the dual-anchoring case**: a `Disposition` carrying an escaped `\|`, whose
  row therefore splits into nine cells, and whose `Commit` a left-anchored read
  would get wrong. This is the regression test the hazard exists for.
- `ok` as `1`, as `"true"`, and absent → `undeterminable`, never exit 2
- a workflow file with no `Feedback Sweep Log` heading

**Removal-diff surface**
- a deselected page → one removal
- a `gap` page present in `reselected_pages` → **no** removal
- empty `reselected_pages` → every observed page removed
- a stem only in `reselected_pages` → ignored

**Corroboration surface**
- all six statuses, reached through the shipped classifier
- a `Draft PR` row inside an HTML comment → `no_record`, proving the blanking
- `ok` short of literal `true` → `skipped`, with the request's reason preserved

**Declaration**: one entry in `tests/speckit-pro/suite-manifest.json`, plus the
request fixture at
`tests/speckit-pro/unit/fixtures/read-only-helpers/requests/check-artifact-freshness.json`.
