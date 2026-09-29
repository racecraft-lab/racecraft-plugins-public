# Finding record format

Each lane records findings as JSON objects, one per finding, in
`audit/findings/<lane-id>.json` (a list). The ledger row for each affected file
lists the finding IDs in `verdict`.

| Field | Type | Rule |
| --- | --- | --- |
| `id` | string | Lane-prefixed and unique: `<lane-id>-NNN`, for example `runner-core-007`. |
| `lane` | string | The lane that recorded it. Must match a lane id in `lanes.json`. |
| `severity` | `blocking` \| `major` \| `minor` | `blocking` only for what AGENTS.md "Code Review Rules" treats as blocking. `major`: a real contradiction or defect that is not blocking. `minor`: substantive but low impact. |
| `kind` | `coherence` \| `cohesion` | Coherence: files disagree (one source per contract, Claude and Codex parity, prose versus runner, evals versus behavior, stale claims). Cohesion: one file mixes concerns, duplicates logic, sits in the wrong layer, or is dead or orphaned. |
| `files` | list of strings | Each entry is `path:line` or `path:start-end`, repo-relative. At least one. Findings without file:line evidence are rejected. |
| `ripwire_command` | string | The exact ripwire command that showed it, one argument per flag. |
| `summary` | string | What is wrong, in one or two short sentences. |
| `proposed_fix` | string | The change that would resolve it. The audit does not apply it. |
| `in_flight_status` | `fixed-in-flight` \| `still-open` \| `introduced-by-branch` \| null | Set only when a touched file has a non-empty `in_flight` list in the ledger. Check against `git diff origin/main...origin/<branch>`. Null otherwise. |

Example:

```json
{
  "id": "runner-core-007",
  "lane": "runner-core",
  "severity": "major",
  "kind": "coherence",
  "files": ["speckit-pro/skills/example/SKILL.md:42", "speckit-pro/speckit_pro_runner/helpers/registry.py:118"],
  "ripwire_command": "ripwire . --uses=example_helper",
  "summary": "The skill names a helper id the registry no longer defines.",
  "proposed_fix": "Rename the skill reference to the registered id.",
  "in_flight_status": null
}
```

## Not recorded

Style and naming nits, wording-only edits, formatting, and refactoring
preferences are not recorded. AGENTS.md calls these minor and adds none on
re-review. Do not report what CI already enforces, generated payloads, generated
reference pages, vendored content, lockfiles, or archived specs.

## Ledger verdicts

A lane records, per file, `verdict` (`"clean"` or a list of finding IDs),
`verdict_lane` (its own lane id) and `checks_run` (the ripwire commands it ran
on that file). `coverage_check.py` fails when any row lacks a verdict or when
`verdict_lane` differs from the row's `lane`.
