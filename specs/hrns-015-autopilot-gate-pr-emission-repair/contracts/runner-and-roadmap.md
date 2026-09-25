# Runner and Roadmap Contract Deltas

These are changes within the existing runner request/result envelope. `schema_version`, `helper_id`, `operation`, `mode`, and `inputs` retain the registry's established shape; implementation fixtures must use the exact registered operation and mode. This document defines the new inputs and observable results, not a second request protocol.

## Reviewability setup

| Field | Contract |
| --- | --- |
| `inputs.spec_id` | Required nonempty case-sensitive ID. Missing value is invalid request; no default or last-entry fallback. |
| `inputs.target` | Existing trusted roadmap path. The selected authored heading is exactly `### <spec_id>:` through the next peer-level entry. |
| Required entry fields | Reviewable LOC, production files, total files, and primary surfaces must all exist in the selected section. |
| Exception | Only a line-anchored `Reviewability-Exception` with accepted class `refactor`, `infra`, or `upgrade` in the selected authored section. |
| Split | `Slices:` ordered IDs plus `Slice Budgets:` Markdown table with `Slice`, `Estimated LOC`, `Production files`, `Total files` columns. |

For a missing selected section or required field, the result is `status: block`, `pass: false`, exit 1, with a blocker naming the spec ID and exact missing field. A valid exception returns `status: exception`, `pass: true`, and `exception_class` set to the exact accepted class. A malformed, mis-cased, placeholder, or unsupported candidate in the selected authored section is recorded under `exceptions.rejected` with a named reason and cannot override the ordinary budget result; an over-block budget remains `status: block`, `pass: false`, exit 1. Other sections and generated text cannot supply an exception. A valid split has one unique numeric row per ID, no extras, aggregate reported totals, and every slice below the block lines. Reject duplicate, missing, extra, malformed, placeholder, or at-block rows. Preserve the existing top-level result fields: on a complete split, `reviewable_loc`, `production_files`, and `total_files` are the row sums. Add `slice_results` in declared order; each result names `slice_id`, those three counts, `status`, `pass`, `warnings`, and `blockers`. Invalid or over-line rows produce top-level `status: block`, `pass: false`, exit 1 and name the offending slice/field. A caller without a `Slices:` declaration retains the existing non-split response shape. Greenfield uses 1.5x only for LOC warn/block thresholds. Issue #637's `multi`, `pragma`, and `nobudget` reproductions are contract fixtures, with selected authored section, primary surfaces, greenfield, and aggregation cases added.

## Size estimate and commands

`estimate-spec-size` accepts optional `inputs.required_refactor_files` as an integer or integer string normalized by the existing size-signal policy. It counts additional refactor files not already in `inputs.files`. Existing estimate/modify behavior runs first, then 40 LOC per distinct required refactor file is added; suggested slices and status use the result. Missing/invalid signal behaves as zero; `spike` takes precedence. Existing response keys (`estimated_loc`, `suggested_slices`, `status`) remain.

`.specify/quality-gates.json` gains an optional `commands` object whose keys are limited to the existing quality slots `COMPLEXITY`, `MUTATION`, `DEPENDENCY_RULES`, and `DEPENDENCY_AUDIT`, each with a nonblank command string. A declaration overrides detection only for its quality slot. The string-valued `detect-commands.commands` map returns the effective command; an additive `command_sources` map and the corresponding quality `gates` record report `declared`. A non-object `commands` value, unknown key, or blank/non-string command invalidates the config, fails G0 with a nonzero exit and a diagnostic naming the field, and never silently falls back to detection as a green result. Omitted `commands` and undeclared slots retain normal detection and existing response fields. The approved `thresholds` and `basis` stay intact.

## Marker and index outputs

G4 and `count-markers gaps/all` count each visible exact Gap-token tag once; G1/G2/G3 and `count-markers clarifications/all` use the same code-visibility exclusion for count and detail. Other marker classes retain existing behavior.

The spec-index source set is Git-index members at the source checkout, including staged additions and excluding untracked candidates everywhere. `scripts/refresh-release-artifacts.py` plain run regenerates the index after its existing outputs. `--check` compares an isolated generated result and exits nonzero with changed tracked index paths if stale. The existing required artifact-consistency job owns this check; no new workflow step is introduced.

## Host request examples

Both hosts must publish complete tested envelopes for the named live failure sites: status `generate-spec-index-check` and `o5-topology`; scaffold reviewability and worktree placement; and phase index writing. Use registered fixture envelopes as the source of field/mode names, including `tests/speckit-pro/unit/fixtures/read-only-helpers/requests/` and the lifecycle contract at `validate-spec-lifecycle-contracts.py`. The rest of the bare-call sweep belongs to HRNS-019.

## Roadmap link contract

A new roadmap template links to `docs/ai/specs/.process/<SPEC-ID>-workflow.md`, relative to the roadmap's containing directory. Scaffold writes that target. On update, resolve an existing legacy link relative to its containing roadmap; preserve it only if it reaches an existing workflow file. Otherwise repair it to the actual scaffold output. Issue #638's generated-template and existing-roadmap cases are required fixtures.
