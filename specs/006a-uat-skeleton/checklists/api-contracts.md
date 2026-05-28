# API Contracts Checklist: Deterministic UAT Runbook Skeleton + PR Body Integration

**Purpose**: Unit-test the *requirements writing* for the script's contract surface — argv positionals, exit-code taxonomy, the `UAT_PROJECT_COMMANDS` env var, the `--workflow-file` flag, the load-bearing `## UAT Runbook` heading, and the runtime-agnostic guarantee. The script IS the API this spec ships; if the contract is under-specified, every future autopilot run (Claude Code and Codex) inherits the ambiguity.
**Created**: 2026-05-28
**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md) · [contracts/generate-uat-skeleton-cli.md](../contracts/generate-uat-skeleton-cli.md)
**Domain**: api-contracts · **Audience**: PR reviewer · **Depth**: formal release gate

**Note**: These are "unit tests for the English." Each item is a yes/no quality assertion about the spec/plan/contract — not an implementation task. A checked box means the requirement text already answers the question; an unchecked gap-marked item means the requirement text does not, and the item is escalated for consensus.

## Positional Argument Contract

- [x] CHK001 - Is the positional contract for `argv[1]` (spec path) and `argv[2]` (output path) explicitly specified, including that the feature directory derives from `dirname argv[1]`? [Completeness, Spec §FR-001, Contract §Positional arguments]
- [x] CHK002 - Is it stated that NO third positional argument is accepted (no `--feature-dir` / `--spec-id`), and that an extra positional is a usage error? [Clarity, Contract §Positional arguments]
- [x] CHK003 - Are both positionals documented as required (missing `argv[1]` or `argv[2]` → exit 2)? [Completeness, Contract §Exit codes]
- [x] CHK004 - Is the relationship between `argv[2]` (output path) and the feature-dir-derived `uat-runbook.md` name consistent across spec, plan, and contract (the autopilot passes `<feature-dir>/uat-runbook.md` as `argv[2]`)? [Consistency, Spec §FR-013, Contract §Consumer contract]

## Exit-Code Taxonomy

- [x] CHK005 - Is the full exit-code taxonomy (0 success / 2 usage error / 1 unreadable-or-missing spec) enumerated with one condition per code? [Completeness, Spec §FR-006, Contract §Exit codes]
- [x] CHK006 - Is exit-code *precedence* specified when two failure conditions co-occur (argv/usage validation → 2 happens before the spec-readability check → 1)? [Clarity, Contract §Exit codes]
- [x] CHK007 - Is it stated that a missing `--workflow-file` source and an unset `UAT_PROJECT_COMMANDS` are NEVER errors (they degrade to stub/placeholder and still exit 0)? [Consistency, Spec §FR-009, Spec §FR-008, Contract §Exit codes]
- [x] CHK008 - Are the output-stream requirements specified (stdout silent on success; diagnostics and warnings to stderr only), matching `generate-pr-body.sh`? [Completeness, Spec §FR-006, Contract §Output streams]
- [x] CHK009 - Is the stderr warning *style* specified as plain/unprefixed (no machine-readable tag), with the rationale that no consumer greps a tag? [Clarity, Spec §FR-004, Contract §Output streams]

## Environment Variable Contract (`UAT_PROJECT_COMMANDS`)

- [x] CHK010 - Is `UAT_PROJECT_COMMANDS` specified as an optional JSON string that the Env Setup section formats without re-running detection? [Completeness, Spec §FR-008, Contract §Environment variables]
- [x] CHK011 - Is the **unset** behavior specified (Env Setup emits an explicit unknown-value placeholder rather than failing)? [Completeness, Spec §FR-008, Spec §Edge Cases]
- [x] CHK012 - Is the **set-but-malformed** (non-`jq`-parseable) behavior specified as a fail-soft fall back to the same placeholders rather than a crash? [Completeness, Spec §FR-008, Contract §Environment variables]
- [x] CHK013 - Is the JSON **key schema** the Env Setup section reads documented (which keys map to which Env Setup rows), so the formatter is unambiguous? [Completeness, Spec §FR-008]
- [x] CHK014 - Is the distinction between an *unset* env var and a *present key whose value is the literal `N/A`* defined, so the placeholder vs. pass-through behavior is unambiguous? [Clarity, Spec §FR-008]

## Flag Contract (`--workflow-file`)

- [x] CHK015 - Is `--workflow-file <path>` specified as an optional flag whose sole effect is echoing the extracted `## Self-Review` block into the runbook? [Completeness, Spec §FR-009, Contract §Flags]
- [x] CHK016 - Are all three degraded inputs for the flag enumerated (flag absent, file unreadable, file lacks the `## Self-Review` heading) with the same stub-line outcome and exit 0? [Coverage, Spec §FR-009, Contract §Flags]
- [x] CHK017 - Is the asymmetry between a flag (`--workflow-file`) and an env var (`UAT_PROJECT_COMMANDS`) intentional and recorded, rather than an accidental inconsistency? [Consistency, Spec §Assumptions, Design Concept Q2/Q3]
- [x] CHK018 - Is it stated that NO `--force` flag exists (overwrite is unconditional per FR-007, so no toggle is needed)? [Clarity, Contract §Flags, Spec §FR-007]
- [x] CHK019 - Is the exact stub-line text for the absent-Self-Review case specified, so the contract is testable verbatim? [Measurability, Contract §Flags]

## PR-Body Heading Contract (`## UAT Runbook`)

- [x] CHK020 - Is the literal `## UAT Runbook` (H2) heading specified as load-bearing, and is the downstream dependency on the exact string named (SC-005 greps for it)? [Completeness, Spec §FR-013, Spec §SC-005]
- [x] CHK021 - Is the heading level disambiguated (H2 `##`, distinct from the existing review-packet H1 `#` sections) so the new section is not pattern-matched against the wrong family? [Clarity, Plan §FR-013 Wiring]
- [x] CHK022 - Are the two size-dependent PR-body rendering paths specified with the exact threshold (under 50,000 chars → full embed via a non-truncating read; at/over → first 60 lines + relative link)? [Completeness, Spec §FR-013, Plan §Decision 2]
- [x] CHK023 - Is the under-threshold "full content" mechanism explicitly distinguished from `extract_heading_section` (which strips blank lines and caps at 40 lines), so the requirement cannot be satisfied by the wrong helper? [Clarity, Spec §FR-013, Plan §Decision 2]
- [x] CHK024 - Is the standalone-`generate-pr-body.sh` case (runbook file absent) specified as a fail-open stub note under the heading, never an abort? [Coverage, Plan §FR-013 Wiring]

## Runtime-Agnostic Guarantee (Claude Code + Codex)

- [x] CHK025 - Is it specified that both autopilot variants invoke the SAME shared script by path, with no runtime-specific behavior in the contract? [Consistency, Contract §header, Plan §Codex Parity]
- [x] CHK026 - Is the lockstep surface for FR-014 reconciled against repository reality (single-copy script/template under `skills/`; Codex calls it by path; no `scripts/`/`templates/` dir in `codex-skills/`)? [Consistency, Spec §FR-014, Plan §Codex Parity]
- [x] CHK027 - Is it stated that no new agent files are introduced, preserving the Layer 1 Codex parity invariant? [Completeness, Spec §FR-014, Spec §Constraints]

## Acceptance-Criteria Quality

- [x] CHK028 - Is each contract-bearing requirement (argv, exit codes, env, flag, heading) traceable to a measurable verification command or Layer 4 fixture? [Measurability, Plan §Traceability]
- [x] CHK029 - Is the success criterion for the heading objectively checkable (a grep for the literal `## UAT Runbook`) rather than a subjective "section appears"? [Measurability, Spec §SC-005]
- [x] CHK030 - Are the side-effect boundaries specified (writes exactly one file = `argv[2]`; does not touch git, does not create a PR, does not modify the spec)? [Completeness, Contract §Side effects]

## Notes

- Items CHK013 and CHK014 surfaced a real under-specification in FR-008: the spec named `UAT_PROJECT_COMMANDS` as "a JSON string" but did not enumerate the key schema the Env Setup formatter reads, nor distinguish an unset env var from a present `N/A` value. Resolved in-place by extending FR-008 to pin the canonical key set (sourced from `detect-commands.sh`) and the unset-vs-`N/A` distinction. CHK012's malformed-JSON fallback, previously only in the contract, was lifted into FR-008 for spec/contract consistency.
- All other contract dimensions were already specified across spec.md, plan.md, and the CLI contract. Zero unresolved gap-marked items remain in this domain.
