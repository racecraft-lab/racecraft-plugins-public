# Implementation Plan: PRSG-009 multi-PR emission

**Branch**: `prsg-009-multi-pr-emission` | **Date**: 2026-06-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/prsg-009-multi-pr-emission/spec.md`

## Summary

PRSG-009 changes the post-implementation autopilot flow from one flattened PR to
one ordered PR per PRSG-008 layer-plan slice. The design reuses the existing
`plan-layers.sh` output as the only slice source, adds deterministic emission and
restack script surfaces, extends PR body and PRS rendering contracts for slice
metadata, and preserves Claude/Codex reference parity.

## Technical Context

**Language/Version**: Bash scripts with Markdown reference documentation.

**Primary Dependencies**: `git`, `gh`, `jq`; optional `gh-stack` only for safely
detected restack/sync operations on an existing stack.

**Storage**: Filesystem JSON/Markdown state: `docs/ai/specs/.process/autopilot-state.json`,
`specs/prsg-009-multi-pr-emission/.process/prs.json`, per-slice emission evidence
under `specs/prsg-009-multi-pr-emission/.process/emission/<slice_id>/`, and
generated `SPEC-MOC.md` PRS rows. JSON state writers render candidates to a
same-directory temp file, validate with `jq` plus required schema/invariant
checks, then atomically replace the target path.

**Testing**: Shell test harness:
`bash tests/speckit-pro/run-all.sh --layer 1`,
`bash tests/speckit-pro/run-all.sh --layer 4`, and
`bash tests/speckit-pro/run-all.sh`. Developer-local coverage adds a Layer 3
functional eval case for the multi-PR emission fixture and Layer 8 parity for
Claude/Codex mirrored references.

**Target Platform**: Local macOS/Linux shell environments used by the
`speckit-pro` plugin.

**Project Type**: Claude/Codex plugin marketplace with skill reference files and
Bash helper scripts.

**Performance Goals**: Deterministic, idempotent resume/reconciliation over a
small layer-plan input. Each slice operation must fail fast before `gh pr create`
when verification fails or reconciliation is ambiguous.

**Constraints**: Reuse PRSG-008 layer-plan output; do not add new slicing,
routing, or atomicity heuristics; use explicit `gh pr create --base --head
--body-file`; keep full regression verification separate from per-slice scoped
verification; do not modify `.github/workflows/pr-checks.yml`; preserve Claude
and Codex parity for mirrored references.

**Scale/Scope**: One active feature spec, usually 1-6 layer-plan slices, one PR
per slice, and bounded JSON/Markdown evidence per slice.

**Reviewability Budget**: Primary surface `docs/process`; secondary surfaces
`harness/adapter` and `seed/config`; projected reviewable LOC 350-650 excluding
generated distribution mirrors; projected production files 6; projected total
files 10-12; budget result is warning accepted because the emission, resume,
PRS, and restack contracts are coupled.

## Declared File Operations

- MODIFIED speckit-pro/skills/speckit-autopilot/references/post-implementation.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh
- NEW speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh
- NEW speckit-pro/skills/speckit-autopilot/scripts/restack.sh

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Result | Evidence |
|-----------|--------|----------|
| I. Plugin Structure Compliance | PASS | Changes stay inside the existing `speckit-pro` skill/reference/script and repo-root test surfaces. No plugin manifest or directory layout changes are planned. |
| II. Script Safety | PASS | New/modified scripts will use `#!/usr/bin/env bash`, `set -euo pipefail`, quoted variables, `jq` for JSON, deterministic stderr, and Layer 4 script tests. |
| III. Semantic Versioning | PASS | No manual version edits. Release-please remains responsible for version changes after a conventional PR merge. |
| IV. Test Coverage Before Merge | PASS | Layer 1 covers structural/parity impact; Layer 4 covers `generate-pr-body.sh`, `generate-spec-index.sh`, `multi-pr-emission.sh`, and `restack.sh`; default verify remains the final regression gate. |
| V. Conventional Commits | PASS | Implementation PR title can use `feat(speckit-pro): emit one pull request per review slice`. |
| VI. KISS, Simplicity & YAGNI | PASS | PRSG-009 consumes PRSG-008 output directly, adds no new slicing heuristics, keeps `gh-stack` optional, and keeps restack mutation behind explicit `--apply`. |

**Reviewability decision**: Warning accepted. The planned production-file count
is at the warning boundary, but splitting the spec would separate emission,
resume, PRS rendering, and restack contracts that must share one state model.
Deferred deeper atomicity backstops remain in PRSG-010.

Reviewability-Exception: infra

The Tasks gate exception is scoped to SpecKit workflow infrastructure: shell
tooling, fixtures, reviewer docs, and Claude/Codex parity mirrors must remain
coordinated against the same durable emission-state contract.

**PR review packet source**: The slice packet generated during emission supplies
review order, branch/base refs, declared file scope, scoped verification
evidence, traceability, known gaps, and restack/rollback notes. Full regression
evidence is stored once before emission and referenced by each slice packet via
`full_verification_evidence`; the full suite is not rerun for every slice PR.
If a slice has no declared scoped tests or no applicable project command, its
packet still carries a required `no_scoped_tests` scoped-verification record with
an explicit no-op rationale and evidence path.

## API Contract Decisions

- **Layer-plan input**: PRSG-009 consumes only PRSG-008 `plan-layers.sh` JSON
  matching the vendored schema fixture at
  `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/contracts/plan-layers.schema.json`.
  The emitter maps `increments[].id` to `slice_id`, `order` to review order,
  `depends_on` to stack dependency evidence, `files[]` to declared file scope,
  `tests[]` to declared scoped tests, and `advisory_size` to review-scope
  context. `invalid_plan` and `input_error` block before branch creation;
  `ok` with warnings proceeds only after copying warnings to emission evidence.
- **Slice PR body**: `generate-pr-body.sh` keeps its current positional
  invocation. When `--slice-packet <json-file>` is present, the script validates
  the packet before writing output; invalid packet input exits 2 with a
  deterministic `generate-pr-body.sh: invalid slice packet:` stderr line.
  Valid packets add reviewer-visible sections for slice summary, review order,
  scope, verification, traceability, restack/rollback, known gaps, and full
  regression evidence.
- **Spec MOC PRS v2 rendering**: schemaVersion 2 rows render as a link-free
  Markdown table with columns `Order`, `Slice`, `PR`, `Status`, `Branch`,
  `Base`, `SHA`, `Scope`, and `Verification`. The renderer keeps schema v1
  plain-row compatibility.
- **Restack CLI**: `restack.sh` is dry-run by default and mutates only with
  `--apply`. Exit codes are fixed as `0` success, `1` conflicts, `2` input
  error, `3` dirty worktree, and `4` `git`/`gh` failure. JSON stdout carries
  matching `status` and `exit_code`; stderr uses
  `restack.sh: <status>: <message>` diagnostics.
- **Scaffold-spec topology boundary**: PRSG-009 records the roadmap
  `speckit-scaffold-spec` branch-topology bullet as an explicit no-op audit.
  Scaffold setup remains responsible for one initial feature worktree branch;
  Style B slice branches are planned and emitted only by post-implementation
  `multi-pr-emission.sh` after full implementation and verification. This keeps
  PRSG-009 out of PRSG-010 review-routing/backstop behavior.

## State Management Decisions

- **Slice identity invariants**: `multi-pr-emission.sh` validates the
  `multi_pr_emission.slices[]` collection before branch or PR mutation. The
  tuple fields `slice_id`, `review_order`, and `expected_branch` must each be
  unique across the slice set. Any duplicate is invalid state and blocks with a
  deterministic input/state error instead of trying to guess which slice owns
  the branch or PR.
- **Candidate state writes**: `autopilot-state.json` and schema v2
  `.process/prs.json` updates are written to same-directory temp files, checked
  with `jq` for parseability, checked against available schema and uniqueness
  invariants, and moved into place only after validation passes. This follows
  the repo's existing same-directory temp plus rename pattern and avoids leaving
  a partial JSON target when an interruption or validation failure occurs.
- **Workflow evidence rows**: after a successful slice PR, workflow evidence
  records `slice_id`, review order, expected branch/base, head SHA, PR number or
  URL, PR state, scoped verification evidence path, PRS manifest path, Spec MOC
  regeneration evidence, and the resulting `next_slice_id`. After a failed
  scoped verification, workflow evidence records the failed command, exit
  status, evidence path, stdout/stderr tail, head SHA, declared tests, retry
  policy, and the blocked `next_slice_id`.
- **Scoped verification no-op evidence**: slices with no declared scoped tests or
  no applicable project command do not silently skip slice evidence. They produce
  a required `no_scoped_tests` scoped-verification record, exit status `0`, and a
  bounded evidence file explaining why no scoped command protects that slice.
- **Slice gate isolation**: a later slice failure leaves already-opened earlier
  slice PRs and their PRS/workflow records intact. The emitter records the failed
  slice, keeps `next_slice_id` on that slice, and does not roll back or relabel
  earlier successful slices.
- **Resume precedence**: resume first derives expected local/remote branches and
  GitHub PR matches from the layer plan and state. GitHub lookup by expected
  head/base across `open`, `closed`, `merged`, and `all` states is the source of
  truth for PR existence. `autopilot-state.json` remains the source for
  orchestration-only fields such as retry policy and evidence paths. Missing or
  stale `.process/prs.json`, `SPEC-MOC.md`, or workflow evidence is backfilled
  from reconciled state before any later slice starts.
- **Closed PR handling**: a matching closed-but-unmerged PR is terminal for that
  slice until an operator records an explicit retry/reset policy. Resume records
  the slice as `closed`, does not recreate the PR, and does not advance
  `next_slice_id` past it. A matching merged PR may advance after merge SHA and
  reviewer navigation are persisted.
- **PR creation failure after branch creation**: after a slice branch is created
  or pushed, a non-zero `gh pr create` result is treated as an uncertain mutation
  until reconciliation proves otherwise. The emitter queries expected head/base
  across all PR states. One match is backfilled as `pr_opened`; zero matches keep
  the slice at `branch_created` or `verified` with `last_error.phase =
  "pr_create"` and `next_slice_id` unchanged; multiple matches block as
  reconciliation failure. No duplicate PR is created on retry.
- **Post-PR reviewer surface failure**: if `.process/prs.json`,
  `SPEC-MOC.md` regeneration, or workflow evidence persistence fails after a PR
  exists, the PR record remains the source for `pr_opened` state and later slices
  are blocked. Resume backfills the missing PRS/MOC/workflow surface before
  continuing. MOC writes use the existing `generate-spec-index.sh` same-directory
  temp plus rename pattern, so a failed write leaves the prior map intact.
- **Restack failure recovery**: `restack.sh` records failures as recovery
  evidence with status, exit code, failed operation when known, stdout/stderr
  evidence, and retry policy. Conflict, input-error, dirty-worktree, and git/gh
  failures leave declared slice file scope unchanged. A successful applied
  restack retargets the first remaining unmerged slice onto the integration base
  at the accepted merge point, retargets each later remaining slice onto the
  immediately preceding remaining slice branch, and must be followed by
  `DEFAULT_VERIFY` before merge evidence is current.

## Project Structure

### Documentation (this feature)

```text
specs/prsg-009-multi-pr-emission/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── multi-pr-emission-state.schema.json
│   ├── prs-v2.schema.json
│   ├── restack-output.schema.json
│   └── slice-packet.schema.json
└── tasks.md              # Created by /speckit-tasks, not this phase
```

### Source Code (repository root)

```text
speckit-pro/
├── skills/speckit-autopilot/
│   ├── references/post-implementation.md
│   └── scripts/
│       ├── generate-pr-body.sh
│       ├── generate-spec-index.sh
│       ├── multi-pr-emission.sh
│       └── restack.sh
└── codex-skills/speckit-autopilot/
    └── references/post-implementation-codex.md

tests/speckit-pro/
├── layer1-structural/
│   └── validate-codex-parity.sh
└── layer4-scripts/
    ├── test-generate-pr-body.sh
    ├── test-generate-spec-index.sh
    ├── test-multi-pr-emission.sh
    └── test-restack.sh
```

**Structure Decision**: Keep behavior in the existing autopilot reference and
script surfaces. Add only two new script helpers: `multi-pr-emission.sh` for the
slice emission/resume contract and `restack.sh` for deterministic dry-run-first
restack behavior.

## Complexity Tracking

No constitution-blocking violations. The reviewability warning is accepted in
the Constitution Check because the affected state contracts are coupled.

## Phase 0 Research

See [research.md](research.md).

## Phase 1 Design

See [data-model.md](data-model.md), [quickstart.md](quickstart.md), and the
contract schemas under [contracts/](contracts/).

## Verification Gates

| Gate | Command | Purpose |
|------|---------|---------|
| Structural | `bash tests/speckit-pro/run-all.sh --layer 1` | Validate plugin structure, script presence, and Codex parity. |
| Script unit | `bash tests/speckit-pro/run-all.sh --layer 4` | Validate PR body packets, PRS v2 rendering, state uniqueness failures, candidate-write validation, empty/no-applicable scoped-test no-op evidence, later-slice failure isolation, emission stop/resume idempotency, `gh pr create` failure after branch creation, post-PR PRS/MOC persistence failure, closed-PR blocking, and restack exit/failure recovery contracts. |
| Layer 3 functional eval | Developer-local PRSG-009 case in `tests/speckit-pro/layer3-functional/` | Validate the end-to-end multi-PR emission behavior on a fixture spec: N ordered PRs from the PRSG-008 layer plan, no legacy flattened PR fallback, and no new slicing heuristics. |
| Default verify | `bash tests/speckit-pro/run-all.sh` | Final deterministic regression across Layers 1, 4, and 5. |
| Layer 8 parity | `bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run` | Run only if implementation changes dispatch/parity fixture surfaces. |
| Layer 7 integration | Not planned | Only required if dispatch graph behavior changes. |

## Post-Design Constitution Check

PASS. Phase 1 artifacts preserve the same boundaries: no workflow CI edits, no
new slicing heuristics, no manual version changes, and no additional production
surfaces beyond the six declared files.
