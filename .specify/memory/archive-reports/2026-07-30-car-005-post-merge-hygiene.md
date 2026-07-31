# Archival Report - CAR-005 Model Availability, Fallback, and Recovery Simulation

## Mode

- **archiveMode**: merged-spec cleanup sweep
- **dryRun**: false
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none

## Provenance

CAR-005 shipped as a two-PR stacked chain. Both halves are merged.

- **Source spec path**:
  `specs/car-005-availability-fallback-recovery/`
- **PR URLs**:
  https://github.com/racecraft-lab/racecraft-plugins-public/pull/411 (slice 1)
  and
  https://github.com/racecraft-lab/racecraft-plugins-public/pull/412 (slice 2)
- **PR titles**:
  `feat(car-005): add a reference simulator that pins what happens when an
  agent's model is unavailable` and
  `feat(car-005): extend the route-fallback simulator with structural rejection
  and recovery cases`
- **Merged at**: `2026-07-30T20:53:03Z` (#411) and `2026-07-30T21:19:49Z` (#412)
- **Merge commits**: `3ba89fa4bee8b1cc6402b47a473181d3f96eed12` (#411) and
  `e31475fa7cb36aed83b76bc63d423bcb10557b97` (#412)
- **Head branches**: `car-005-slice-1` (#411) and
  `car-005-availability-fallback-recovery` (#412); both deleted on merge
- **Base branches**: `main` (#411); `car-005-slice-1` at open, auto-retargeted
  to `main` when #411 squash-merged (#412)
- **Cleanup branch**: `chore/archive-car-005-post-merge`
- **Workflow preserved**:
  `docs/ai/specs/.process/CAR-005-workflow.md`
- **Design concept preserved**:
  `docs/ai/specs/.process/CAR-005-design-concept.md`
- **Operator runbook preserved**: none authored; CAR-005 has no live or
  operator-only surface (see Runbook Decision)
- **CI runs**:
  [#411 PR Checks](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/30574830002),
  [#411 Container Preflight](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/30574828524),
  [#412 PR Checks](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/30581755842),
  and
  [#412 Container Preflight](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/30581755890)
- **CI / metadata gates**: every required check passed on both PRs — title,
  release-note, workflow, docs, artifact-consistency, plugin, full-suite,
  CodeQL, and Linux amd64/arm64 container checks. Windows x64 advisory smoke
  passed on both; Windows ARM64 advisory smoke was skipped on both in its normal
  unlabelled runner state.
- **Argos build/review URL**: N/A
- **Metadata gates**: pass
- **Artifact manifest**: N/A; committed repository evidence is canonical
- **Screenshot retention**: N/A
- **Expiration risk**: committed source and process evidence has no artifact
  retention dependency

## Feature Summary

CAR-005 shipped a synthetic reference simulator that pins what a session
preflight does when an agent's preferred model is unavailable, before any real
route policy exists. Three closed JSON Schema contracts, an eighteen-case replay
corpus, one standard-library module, and one durable Layer 4 owner enforce
resolution, rejection, budget, override, helper, and replay semantics.

Resolution is bounded and report-only. A `no_safe_route` outcome names the
unresolved agent, every attempted route, each rejection reason, and remediation
whose actions include rolling back to the previous plugin release; no shipped
agent file is read for mutation or written. Budget exhaustion enumerates all
three classes on the terminal diagnostic and on no other. Optional-helper
unavailability is recorded as structured state rather than a diagnostic, and
required-agent resolution does not fail because of it.

The five reason codes are frozen. `effort_unsupported` and the mapping of
`undetermined` to probe-unavailable are deliberate **preflight qualification**
divergences from runtime behaviour rather than mirrors of it, because the
runtime silently degrades an unsupported effort (PF-2) and the fail-open
direction was a live defect caught during this run.

Slice 2 held the append-only seam it promised: it changed no schema file and no
`tests/speckit-pro/suite-manifest.json` entry, and appended only at the tail of
`cases[]` without altering a slice-1 case, input, or pinned report.

Post-merge review remediation on the stack fixed override half-application,
empty and unknown override dictionaries, unenforced budget caps, and a repeated
route in the fallback chain. The stacked chain briefly showed add/add conflicts
on #412 after #411 squash-merged and flattened slice-1 ancestry; that was
resolved by merging `origin/main` and taking the branch content, which was
verified byte-identical to slice-1's tip beforehand.

## Known Gap Carried Forward

`tests/speckit-pro/layer6-efficiency/lib/claude_route_fallback.py` declares
`POLICY_SCHEMA_PATH` and `SNAPSHOT_SCHEMA_PATH` alongside `REPORT_SCHEMA_PATH`
but loads only the report schema. Neither declared contract is read anywhere in
the module, so `resolve()` validates the report it emits and never the policy or
snapshot it accepts. Three consequences ship:

- a snapshot violating its own `additionalProperties: false` resolves clean
  instead of failing closed;
- a policy missing a declared budget member raises a bare `KeyError` rather than
  a contract error; and
- `load_corpus`'s docstring claims fail-closed enforcement of the properties
  FR-033b's append-only seam rule and SC-007's read-one-case guarantee lean on,
  which overstates the member-presence and `case_id` checks it actually
  performs.

All eighteen committed corpus policies and snapshots were validated against both
declared contracts before this archive and violate neither, so the corpus is
correct by authoring discipline rather than by any check, and closing the gap
changes no pinned report. This is a defect in the accept path, not a wrong
result.

The fix is to load both contracts at import and validate `policy` and `snapshot`
in `resolve()` and per case in `load_corpus`. It is deliberately not folded into
this cleanup: the archive commit changes no shipped behavior, and both CAR-005
slices are already on `main`, so the correction is an ordinary follow-up change
against `main` rather than a restack. CAR-006 inherits the gap until it lands.

## Parity Note

PF-1 through PF-4 — the grounded platform facts verified against the live Claude
Code documentation (CLI 2.1.220) during this run — are platform behaviour, not
Claude-specific design, and are recorded in the Claude roadmap only. A
Codex-side edit is a deliberate joint two-platform landing under the shared
parity contract, so G56R-005 onward should carry the same section. That debt is
recorded in the roadmap's Grounded Platform Facts section, not closed here.

## Runbook Decision

No relocation was required, and unlike CAR-004 and G56R-004 no runbook was
preserved. Those two features each carried an unrun, subscription-authenticated
operator procedure that existed nowhere else; CAR-005 has no live surface at all
— zero production files, every claim deterministic and re-runnable from the
committed suite.

The feature `quickstart.md` is a per-slice validation guide for slices that are
now merged. Its slice-diff commands name branches GitHub deleted on merge, and
its failure-triage table maps symptoms to causes that the shipped tests already
assert. It is planning exhaust, recoverable at the merge commit, so it was
removed with the rest of the folder rather than moved.

No contract relocation was required either. All three schemas, the corpus, the
simulator, and the test owner were authored directly under `tests/speckit-pro/`.
A repository-wide search for the bare directory name found no live code, test,
script, workflow, or docs-site reader before removal.

## Canonical Shipped Artifacts

- `tests/speckit-pro/layer6-efficiency/contracts-claude/route-resolution-report.schema.json`
- `tests/speckit-pro/layer6-efficiency/contracts-claude/route-policy.schema.json`
- `tests/speckit-pro/layer6-efficiency/contracts-claude/environment-snapshot-projection.schema.json`
- `tests/speckit-pro/layer6-efficiency/fixtures-fallback/fallback-scenario-corpus.json`
- `tests/speckit-pro/layer6-efficiency/lib/claude_route_fallback.py`
- `tests/speckit-pro/unit/test-route-fallback-simulation.py`
- `tests/speckit-pro/suite-manifest.json` (one entry added in slice 1; unchanged
  by slice 2)
- `docs-site/src/content/docs/reference/tests.md`
- `docs/ai/specs/.process/CAR-005-workflow.md`
- `docs/ai/specs/.process/CAR-005-design-concept.md`

## Recovery Commands

Both merge commits contain the full spec folder; `e31475fa` is the later of the
two and is the single-commit recovery source.

```text
git show e31475fa7cb36aed83b76bc63d423bcb10557b97:specs/car-005-availability-fallback-recovery/spec.md
git show e31475fa7cb36aed83b76bc63d423bcb10557b97:specs/car-005-availability-fallback-recovery/plan.md
git show e31475fa7cb36aed83b76bc63d423bcb10557b97:specs/car-005-availability-fallback-recovery/tasks.md
git show e31475fa7cb36aed83b76bc63d423bcb10557b97:specs/car-005-availability-fallback-recovery/research.md
git show e31475fa7cb36aed83b76bc63d423bcb10557b97:specs/car-005-availability-fallback-recovery/data-model.md
git show e31475fa7cb36aed83b76bc63d423bcb10557b97:specs/car-005-availability-fallback-recovery/quickstart.md
git show e31475fa7cb36aed83b76bc63d423bcb10557b97:specs/car-005-availability-fallback-recovery/SPEC-MOC.md
git show e31475fa7cb36aed83b76bc63d423bcb10557b97:specs/car-005-availability-fallback-recovery/checklists/data-integrity.md
git show e31475fa7cb36aed83b76bc63d423bcb10557b97:specs/car-005-availability-fallback-recovery/checklists/error-handling.md
git show e31475fa7cb36aed83b76bc63d423bcb10557b97:specs/car-005-availability-fallback-recovery/checklists/llm-integration.md
git show e31475fa7cb36aed83b76bc63d423bcb10557b97:specs/car-005-availability-fallback-recovery/.process/slice-1-pr-packet.md
git show e31475fa7cb36aed83b76bc63d423bcb10557b97:specs/car-005-availability-fallback-recovery/.process/slice-2-pr-packet.md
git checkout e31475fa7cb36aed83b76bc63d423bcb10557b97 -- specs/car-005-availability-fallback-recovery
```

## Changed Files and Impact

| Artifact | Change |
|---|---|
| `.specify/memory/{spec,plan,changelog}.md` | Append shipped behavior, architecture, provenance, the carried-forward gap, and cleanup state |
| `.specify/memory/archive-reports/2026-07-30-car-005-post-merge-hygiene.md` | This report |
| `.specify/autopilot-state.json` | Move project archive state to CAR-005 |
| `docs/ai/specs/.process/autopilot-state.json` | Mark CAR-005 completed/archived and record the applied sweep |
| `docs/ai/specs/claude-agent-routing-technical-roadmap.md` | Mark CAR-005 complete/archived with the carried-forward gap, and CAR-006 ready |
| `docs/ai/specs/claude-agent-routing-roadmap-MOC.md` | Frontmatter status; generated index zone regenerated |
| `specs/car-005-availability-fallback-recovery/` | Remove completed active spec residue |

## Cleanup Decision

- **cleanupApplied**: true
- **cleanupOperation**: `git rm -r specs/car-005-availability-fallback-recovery`
  after both merge provenances and a tree-wide live-reader scan; no relocation
  preceded it
- **cleanupBranch**: `chore/archive-car-005-post-merge`
- **blockedBy**: none
- **Downstream state**: CAR-006 is ready because PRs #411 and #412 provide the
  canonical contracts, corpus, simulator, and test owner it consumes. It
  inherits the unvalidated-accept-path gap recorded above. CAR-012 remains the
  separate cross-platform reconciliation joint change with G56R-012.

## Verification Commands

- `python3 -m json.tool .specify/autopilot-state.json`
- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- SpecKit runner operation `generate-spec-index-write` in apply mode
- SpecKit runner helper `generate-spec-index-check`
- final `find specs -mindepth 1 -maxdepth 4 -print` audit
- stale active-path scan across `tests/`, `speckit-pro/`, `scripts/`,
  `.github/`, and `docs-site/`
- `python3 tests/speckit-pro/run-all.py --layer 1`
- `python3 tests/speckit-pro/run-all.py`
- release-readiness runner gate for
  `docs(car-005): archive post-merge state`
- `python3 scripts/compose-release-notes.py --validate-pr`
- `git diff --check`

## Verification Results

All checks ran from the cleanup branch after the active-spec removal and before
commit.

| Check | Result |
|---|---|
| Active spec inventory | `specs/.gitkeep` plus `specs/art-001-brand-kit-gallery-foundation` |
| `.specify/autopilot-state.json` | valid JSON |
| `docs/ai/specs/.process/autopilot-state.json` | valid JSON |
| `generate-spec-index-check` before regen | exit 1 — stale, `claude-agent-routing-roadmap-MOC.md` |
| `generate-spec-index-write` (apply) | one write applied to `docs/ai/specs/claude-agent-routing-roadmap-MOC.md` |
| `generate-spec-index-check` after regen | exit 0 — index current, all in-scope maps up to date |
| Stale active-path scan outside archive/process evidence | zero live code, test, script, workflow, or docs-site references |
| `python3 tests/speckit-pro/run-all.py --layer 1` | 1428/1428 |
| `python3 tests/speckit-pro/run-all.py` | 7008/7008 (L1 1428, L4 5394, L5 186) |
| CAR-005 focused owner within the full suite | 1195/1195 `test-route-fallback-simulation` |
| Release-readiness title gate | pass for `docs(car-005): archive post-merge state` |
| Release-note validation | pass — non-releasable conventional-commit type |
| `git diff --check` | clean |

Docs reference generation was not required: this cleanup changed no tracked
`.md`, `.py`, or `.sh` under `tests/speckit-pro/`, no plugin inventory, and no
generated docs reference page. The existing reference page remains the merged
PR #411 artifact and the full suite validates its structural contract.

## Outstanding Non-CAR-005 Observation

`specs/art-001-brand-kit-gallery-foundation` remains in the active spec
inventory and its PR #407 merged on 2026-07-30. It belongs to the separate HTML
artifacts roadmap and was not evaluated, relocated, or removed by this sweep. It
is a candidate for its own archive pass.

## Constitution Compliance

PASS by scope. The cleanup preserves durable evidence, changes no plugin version
or runtime payload, adds no active Bash or `jq` dependency, retains all merged
source through immutable git provenance, and leaves the full
Python-authoritative suite as the completion gate.
