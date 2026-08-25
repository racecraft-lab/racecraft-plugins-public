# Archival Report - G56R-006 Capability-aware Resolver, Materializer, Installer, and Strict Override

## Mode

- **archiveMode**: merged-spec cleanup, ALL sweep
- **dryRun**: false
- **applyCleanupRequested**: true
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none — `.specify/feature.json` is absent and PR #503 is merged

## Provenance

All dates UTC.

- **Source spec path**: `specs/g56r-006-resolver-materializer-installer-strict-override/`
- **Workflow file**: `docs/ai/specs/.process/G56R-006-workflow.md` (preserved)
- **Cleanup branch**: `archive-art017-g56r006`
- **Cleanup base**: `main` at `062d5dd94`

| PR | Title | Merged at | Merge commit |
|---|---|---|---|
| [#503](https://github.com/racecraft-lab/racecraft-plugins-public/pull/503) | `feat(g56r-006): Add capability-aware agent installation` | `2026-08-25T14:52:56Z` | `609f99e1732424ffd68adfbd17d6f41d37f0fba4` |

This is a same-day archive: the pull request merged roughly an hour before the
cleanup ran.

## Feature Summary

G56R-006 added capability-aware agent installation: ordered preferred/fallback
resolution from one snapshot binding, bounded probe evidence, a strict
per-agent override that permits no fallback, and an atomic installer whose
required-agent miss produces an exact zero-mutation response. 53/53 tasks,
100% spec adherence, 0 critical findings, no proposed spec changes.

## Acceptance Result

The retrospective records 53/53 tasks and zero critical findings, and is
preserved at `docs/ai/specs/.process/G56R-006-retrospective.md`.

**No manual UAT exists, and none was expected.** The spec places live UAT,
real-home mutation and Claude installation explicitly out of scope
(`G56R-006-workflow.md:166`), so acceptance rests on the automated evidence and
the dry-run install path rather than on a browser or real-home run. This is a
scope decision recorded at Specify, not an omission at archive.

## Canonical Shipped Artifacts

Outside `specs/**` and unaffected:

- the route-aware resolver, materializer and installer under `speckit-pro/`
- the route-policy manifest schema and the route-aware install contract
- `tests/speckit-pro/unit/test-route-fallback-simulation.py`,
  `test-codex-route-fallback-recovery.py`, `test-policy-control-contracts.py`
  and the rest of the G56R suite
- generated payloads, installed-cache proofs and docs reference pages

### Historical process evidence

- `docs/ai/specs/.process/G56R-006-workflow.md`
- `docs/ai/specs/.process/G56R-006-retrospective.md` (relocated)
- `docs/ai/specs/.process/G56R-006-release-readiness-result.json`

## Evidence Relocation

| Original | Durable path | Reason |
|---|---|---|
| `retrospective.md` | `docs/ai/specs/.process/G56R-006-retrospective.md` | the workflow file's `Post: Retrospective` row cites it by path, and the G56R-005 precedent relocates retrospectives |

`verify-tasks-report.md`, `quickstart.md`, `research.md`, `data-model.md`, the
`contracts/` and `checklists/` sets, the `.process/pr-packets/` tree,
`implementation-notes.md` and `SPEC-MOC.md` are run exhaust for merged work and
were removed with the folder. G56R-005's cleanup made the same call on the same
file types.

## Live-Reader Scan

Run before any mutation.

| Match | Nature | Action |
|---|---|---|
| `docs/ai/specs/.process/G56R-006-workflow.md` | the `Post: Retrospective` row plus historical planning paths | row repointed; historical paths retained |
| `docs/ai/specs/.process/autopilot-state.json` | this run's own identity and its plan-step file lists | status advanced, archive block added, identity fields retained |
| `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md` | "is in progress" | reconciled to shipped and archived |
| `docs/ai/specs/codex-gpt-5-6-agent-routing-roadmap-MOC.md` | frontmatter status and a generated backlink | status line corrected; backlink **regenerated** |
| `docs/ai/specs/.process/G56R-006-release-readiness-result.json` | historical file list from the run | retained as the record |
| `tests/**`, `speckit-pro/**`, `scripts/**`, `.github/**` | **no match** | none needed |

## The State File Was Updated Here, And Was Not An Hour Ago

`autopilot-state.json` is a single-slot pointer to the current run. The archive
rule keys on one question: does it still point at the spec being archived?

For ART-008 in PR #505 the answer was no — G56R-006 had reclaimed the slot — so
that cleanup deliberately left the file byte-identical to `main` and said so.
Here the answer is yes: the slot holds G56R-006, and G56R-006 is what this
report archives. So the status advances to `completed_archived` and an `archive`
block is added.

Same rule, opposite outcomes, one day apart. The rule is about the pointer's
current subject, never about which spec happens to be in hand.

## Recovery Commands

```text
git show 609f99e1732424ffd68adfbd17d6f41d37f0fba4:specs/g56r-006-resolver-materializer-installer-strict-override/spec.md
git show 609f99e1732424ffd68adfbd17d6f41d37f0fba4:specs/g56r-006-resolver-materializer-installer-strict-override/plan.md
git show 609f99e1732424ffd68adfbd17d6f41d37f0fba4:specs/g56r-006-resolver-materializer-installer-strict-override/tasks.md
git show 609f99e1732424ffd68adfbd17d6f41d37f0fba4:specs/g56r-006-resolver-materializer-installer-strict-override/verify-tasks-report.md
git show 609f99e1732424ffd68adfbd17d6f41d37f0fba4:specs/g56r-006-resolver-materializer-installer-strict-override/contracts/route-policy-manifest.schema.md
```

Restore the whole folder with `git restore --source=609f99e17 --` and the path.

## Cleanup Decision

`safeToApplyCleanup=true`. PR #503 is merged, provenance and recovery commands
are recorded, no live reader remains, and the suite is green.

## Downstream State

G56R-007 through G56R-010 were blocked by G56R-006 and are now unblocked; they
may run in parallel, serializing shared regeneration. G56R-011 remains blocked
by that cohort.
