# Archival Report - ART-006 Autopilot Staging

## Mode

- **archiveMode**: merged-spec cleanup sweep
- **dryRun**: false
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none — no run is in flight

## Provenance

ART-006 shipped in one PR with no follow-up fix.

- **Source spec path**: `specs/art-006-autopilot-staging/`
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/422
- **PR title**: `feat(art-006): let autopilot stop after planning and resume
  into implementation later`
- **Merged at**: `2026-08-09T17:50:51Z`
- **Merge commit**: `5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff`
- **Head branch**: `art-006-autopilot-staging`
- **Base branch**: `main`
- **Merged by**: `fgabelmannjr`
- **Cleanup branch**: `chore/archive-art-006-post-merge`
- **Workflow preserved**: `docs/ai/specs/.process/ART-006-workflow.md`
- **Design concept preserved**: `docs/ai/specs/.process/ART-006-design-concept.md`
- **Retrospective preserved**: `docs/ai/specs/.process/ART-006-retrospective.md`
- **CI / metadata gates**: 17 pass, 2 skip, 1 fail at merge. Every **required**
  check passed — `validate-pr-title`, `validate-release-note`,
  `validate-plugins`, `container-preflight-linux-amd64`, and
  `container-preflight-linux-arm64` — and `mergeStateStatus` was `CLEAN`. The one
  failure is `Analyze (actions)`, a stale default-setup CodeQL run stranded by the
  2026-08-06 GitHub Actions outage (incident `qcvjkzcs7j74`, Actions and Pages
  `major_outage`). Those runs carry `event: dynamic` and the API refuses to retry
  them; only a new commit re-triggers one. It is not a required check. See
  **Recorded CI Anomaly**.
- **Argos build/review URL**: N/A
- **Metadata gates**: pass
- **Artifact manifest**: the runner manifest and `.sha256` were regenerated in
  #422 and are covered by the payload gates; committed repository evidence is
  otherwise canonical
- **Screenshot retention**: N/A
- **Expiration risk**: committed source and process evidence has no artifact
  retention dependency

## Feature Summary

ART-006 gave the autopilot first-class stages — `plan`, `implement`, `full` — on
both the Claude and Codex distributions. A planning run now works through
specification, clarification, planning, checklists, task generation and analysis,
closes with the confidence gate, records the stage, commits that boundary, and
stops. A later `--stage implement` run — in a new session, possibly a different
working copy — resumes without redoing planning work. A bare invocation resolves
its own stage from the workflow file and reports the choice and its basis before
any phase work begins. Gate semantics are unchanged; only stage ownership of the
pre-implement confidence gate was decided.

Stage resolution exists **once**, as the registered runner operation
`resolve-autopilot-stage` that both distributions reach by operation identifier,
rather than as two prose descriptions that can drift. That siting was a Round 2
consensus tiebreak: the phase-coverage guard is a consistency checker over
already-resolved inputs, not a resolver, and may import the resolver as a library.

The run's highest-value output was verification rather than code. The feature
exists to prevent one failure — resolving the wrong stage silently — and **three
independent routes to it were found and closed**, only one of which was visible
when the specification was written:

1. A refused strict-mode confidence gate left the resolved stage reading `plan`
   while the phase loop's row scan independently selected the implementation
   row, because the shipped scan matches `⏳ Pending` or `🔄 In Progress` and a
   `⚠️ Blocked` row matches neither arm. Both halves looked correct alone.
2. An unreadable or unparseable workflow file degraded to a default that reads
   every planning row as incomplete, re-planning finished work.
3. An explicitly named implementation stage crossed a refused boundary with no
   diagnostic.

The checklist phase raised 20 defects across three domains and remediated all 20.
Two were implementation-blocking and would have shipped green: a Codex rejection
step sited in a reference document that has **no opening-preparation section**,
so it would have run *after* phase work began; and an exit-code table folding a
request-layer `unsupported_path` diagnostic into exit 2, which would have taught
the golden fixtures to assert a code the runner never emits.

## Recorded CI Anomaly

The merge carries one failed check, and this archive records rather than
reconciles it.

`Analyze (actions)` failed on 2026-08-06 during a declared GitHub Actions major
outage. Every failing job that day died at "Set up job" with
`Failed to resolve action download info. Error: Service Unavailable`, before any
repository code executed. A cascade effect made `validate-plugins` report
*"Generated artifacts drift from source"* with `DETECT_RESULT: abandoned` and
`ARTIFACT_RESULT: abandoned` — drift was never detected; its upstream jobs were
killed. Local verification at the time showed `refresh-release-artifacts.py` to be
a clean no-op.

After the outage cleared on 2026-08-09 the failed runs were re-run and all
required checks returned green. `Analyze (actions)` could not be re-run because
GitHub's default-setup CodeQL runs are not retryable through the API. It is not a
required check and `mergeStateStatus` was `CLEAN`.

## Known Gaps Carried Forward

Two defects were found during ART-006 and **deliberately not fixed** in it, both
now tracked on the roadmap as ready specs with no dependencies:

- **ART-014 — Phase-Guard Enforcement Repair.** The shipped workflow-identity
  check is inert twice over. `_authorized_workflow_text`
  (`validate-autopilot-phase-coverage.py:1298`) returns no errors unless the state
  carries a `pr-marker-plan.v2` schema **and** `--expected-head-commit` was
  supplied, so a normal run never compares the two paths; and its errors land in
  `workflow_checkpoint_errors`, absent from the `status-evidence` tuple the
  autopilot always invokes. Verified by execution: aimed at a state file naming a
  different specification, the guard exits `0` and reports `pass`. ART-006's own
  mirror check was registered and proven to move the exit code precisely so it
  would not inherit this. Broader finding: 11 of the guard's 19 problem keys
  cannot move the exit code under the scoped rule, most deliberately so.
- **ART-015 — Spec-Size Re-Estimation Trigger.** `estimate-spec-size` is accurate
  when fed current signals and is only ever fed scoping-time ones. ART-006 was
  estimated at 3 stories / 12 files / 14 FRs → 382, one slice. Fed its final
  signals — 3 / 17 / 25 — the same operation returns 565 with `status: warn`.
  Nothing re-invoked it.

## Reviewability Outcome

Recorded because the merged diff exceeded its declared line budget and the PR
says so openly rather than defending it.

| Bucket | Files | Added lines |
|---|---|---|
| Logic — Python and JSON | 4 | 338 |
| Skill and reference prose | 7 | 530 |
| Authored tests | 6 | 1131 |
| **Human-reviewable total** | **17** | **1999** |

Declared position was 459 lines across 17 files, against 400 warn / 800 block and
15 warn / 25 block. The **file count matched the declaration exactly**; only the
line count exceeded its block threshold. Logic alone is 338 lines, under the warn
line, and 992 of the 1131 test lines are a single table-driven fixture file. The
maintainer reviewed the composition and accepted one slice.

An earlier revision of the workflow record reported 29 files and claimed both
thresholds were exceeded; twelve regenerated `installed-cache-proof*.json`
fixtures had been miscounted as authored tests. That correction is recorded in the
preserved workflow file rather than silently applied.

## Canonical Shipped Artifacts

- `speckit-pro/speckit_pro_runner/helpers/read_only.py` (the
  `resolve-autopilot-stage` operation, `workflow_stage_signals`,
  `parse_stage_args`)
- `speckit-pro/speckit_pro_runner/helpers/registry.py` (operation registration)
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` and
  `speckit-pro-runner.sha256` (plus both `dist/` copies)
- `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`
  (`stage_mirror_errors` and its `RULE_PROBLEM_KEYS` registration)
- `speckit-pro/skills/speckit-autopilot/contracts/autopilot-state-status.schema.json`
- `speckit-pro/skills/speckit-autopilot/SKILL.md` and its `references/`
  (`phase-execution.md`, `task-list-canonical.md`, `workflow-file-protocol.md`)
- `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` and its `references/`
  (`phase-execution-codex.md`, `task-list-canonical-codex.md`)
- `dist/claude/**` and `dist/codex/**` materializations of the above
- `tests/speckit-pro/unit/test-autopilot-stage-resolution.py`
- `tests/speckit-pro/unit/fixtures/read-only-helpers/requests/resolve-autopilot-stage.json`
  and `fixture-manifest.json`
- `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py`
- `tests/speckit-pro/layer1-structural/validate-workflow-status-evidence.py`
- `tests/speckit-pro/suite-manifest.json` (one entry added)
- `docs-site/src/content/docs/reference/tests.md`
- `docs/ai/specs/.process/ART-006-workflow.md`
- `docs/ai/specs/.process/ART-006-design-concept.md`
- `docs/ai/specs/.process/ART-006-retrospective.md`

## Live-Reader Scan

A tree-wide scan for the **bare directory name** was run before removal, because
path references assembled from `Path` components do not appear in joined-path
greps — the failure mode that left CAR-003 pointing a live Layer 6 library at its
spec contracts.

Three matches were found outside the spec folder and all three are safe:

| Match | Verdict |
|---|---|
| `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1509` | Writes the string into a **temporary directory's** `.specify/feature.json` as an opaque `feature_directory` value; never reads the real folder. Its sibling case uses `specs/car-005-availability`, already archived — established local precedent. |
| `tests/speckit-pro/unit/test-autopilot-stage-resolution.py` | References `docs/ai/specs/.process/ART-006-workflow.md`, which is **preserved**, and `"ART-006"` as an argv token value. |
| `tests/speckit-pro/unit/fixtures/read-only-helpers/requests/resolve-autopilot-stage.json` | References the same preserved workflow file. |

No live code, test, script, workflow, or docs-site reader depends on
`specs/art-006-autopilot-staging/`.

`quickstart.md`, `research.md`, `data-model.md`, the two `contracts/` files, and
the three `checklists/` files are run exhaust and were removed with the folder.
No contract relocation was required: every shipped surface was authored outside
`specs/**`.

## Recovery Commands

```text
git show 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff:specs/art-006-autopilot-staging/spec.md
git show 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff:specs/art-006-autopilot-staging/plan.md
git show 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff:specs/art-006-autopilot-staging/tasks.md
git show 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff:specs/art-006-autopilot-staging/research.md
git show 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff:specs/art-006-autopilot-staging/data-model.md
git show 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff:specs/art-006-autopilot-staging/quickstart.md
git show 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff:specs/art-006-autopilot-staging/SPEC-MOC.md
git show 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff:specs/art-006-autopilot-staging/contracts/stage-invocation.md
git show 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff:specs/art-006-autopilot-staging/contracts/scaffold-autopilot-chain.md
git show 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff:specs/art-006-autopilot-staging/checklists/requirements.md
git show 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff:specs/art-006-autopilot-staging/checklists/state-management.md
git show 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff:specs/art-006-autopilot-staging/checklists/error-handling.md
git show 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff:specs/art-006-autopilot-staging/checklists/api-contracts.md
git checkout 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff -- specs/art-006-autopilot-staging
```

## Changed Files and Impact

| Artifact | Change |
|---|---|
| `.specify/memory/{spec,plan,changelog}.md` | Append shipped behavior, architecture, provenance, the recorded CI anomaly, and cleanup state |
| `.specify/memory/archive-reports/2026-08-09-art-006-post-merge-hygiene.md` | This report |
| `docs/ai/specs/.process/autopilot-state.json` | Mark ART-006 completed/archived and record the applied sweep |
| `docs/ai/specs/html-artifacts-technical-roadmap.md` | Mark ART-006 complete/archived; clear the "in progress on `art-006-autopilot-staging`" prose; unblock ART-007, ART-009, ART-011, ART-012 |
| `docs/ai/specs/html-artifacts-roadmap-MOC.md` | Frontmatter status; generated index zone regenerated |
| `specs/art-006-autopilot-staging/` | Remove completed active spec residue |

## Cleanup Decision

- **cleanupApplied**: true
- **cleanupOperation**: `git rm -r specs/art-006-autopilot-staging` after merge
  provenance and a tree-wide live-reader scan on the bare directory name
- **cleanupBranch**: `chore/archive-art-006-post-merge`
- **blockedBy**: none
- **Stacking note**: none. The previous archive cleanups (#414, #415) are merged,
  so this branches directly from `main` and no `.specify/memory/` append conflicts
  with an open branch.
- **Downstream state**: ART-006's completion unblocks ART-007, ART-009, ART-011
  and ART-012. ART-002 through ART-005 were already ready. ART-014 and ART-015 are
  new, ready, and dependency-free.

## Verification Commands

- `find specs -mindepth 1 -maxdepth 4 -print` audit
- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- SpecKit runner operation `generate-spec-index-write` in apply mode
- SpecKit runner helper `generate-spec-index-check`
- tree-wide stale active-path scan on the bare directory name
- `python3 tests/speckit-pro/run-all.py --layer 1`
- `python3 tests/speckit-pro/run-all.py`
- release-readiness runner gate for `docs(art-006): archive post-merge state`
- `python3 scripts/compose-release-notes.py --validate-pr`
- `git diff --check`

## Verification Results

All checks ran from the cleanup branch after the active-spec removal and before
commit.

| Check | Result |
|---|---|
| Active spec inventory | `specs/.gitkeep` only |
| `docs/ai/specs/.process/autopilot-state.json` | valid JSON; `status: completed_archived` |
| `generate-spec-index-write` (apply) | exit 0 — one write applied to `html-artifacts-roadmap-MOC.md` |
| `generate-spec-index-check` after regen | exit 0 — index current |
| Generated MOC zone | dropped the removed `SPEC-MOC.md` entry; the curated roadmap-section link at line 43 correctly remains |
| Live-reader scan on the bare directory name | three matches, all verified safe by reading them; zero live dependencies on the removed folder |
| `python3 tests/speckit-pro/run-all.py --layer 1` | 1447/1447 |
| `python3 tests/speckit-pro/run-all.py` | 7226/7226 (L1 1447, L4 5593, L5 186) — unchanged from pre-cleanup, so the removal broke nothing |
| Release-readiness title gate | pass for `docs(art-006): archive post-merge state` |
| Release-note validation | pass — non-releasable conventional-commit type |
| `git diff --check` | clean |

Docs reference generation was not required: this cleanup changed no tracked
`.md`, `.py`, or `.sh` under `tests/speckit-pro/`, no plugin inventory, and no
generated docs reference page. No payload byte changed, so the generated artifact
contract is untouched.

## Constitution Compliance

PASS by scope. The cleanup preserves durable evidence — workflow, design concept
and retrospective all remain under `docs/ai/specs/.process/` — changes no plugin
version or runtime payload, adds no active Bash or `jq` dependency, retains all
merged source through immutable git provenance, and leaves the full
Python-authoritative suite as the completion gate.
