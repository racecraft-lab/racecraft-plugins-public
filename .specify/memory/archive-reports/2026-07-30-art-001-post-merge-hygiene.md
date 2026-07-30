# Archival Report - ART-001 Artifact Brand Kit and Gallery Foundation

## Mode

- **archiveMode**: merged-spec cleanup sweep
- **dryRun**: false
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none

## Provenance

ART-001 shipped in one PR with one follow-up correctness fix. Both are merged.

- **Source spec path**:
  `specs/art-001-brand-kit-gallery-foundation/`
- **PR URLs**:
  https://github.com/racecraft-lab/racecraft-plugins-public/pull/407 (feature)
  and
  https://github.com/racecraft-lab/racecraft-plugins-public/pull/409 (follow-up
  fix)
- **PR titles**:
  `feat(speckit-pro): add the artifact gallery brand kit, routing catalog, and
  validation` and
  `fix(speckit-pro): scan artifact script bodies for external references and
  prohibited constructs`
- **Merged at**: `2026-07-30T13:12:39Z` (#407) and `2026-07-30T14:43:55Z` (#409)
- **Merge commits**: `c4498dd0ce0a85618b8e923108682c4818c083f6` (#407) and
  `a6cc2b21bad2fa0514eacc4032f296ddd332cc3c` (#409)
- **Head branches**: `art-001-brand-kit-gallery-foundation` (#407) and
  `fix/gallery-script-reference-scan` (#409)
- **Base branch**: `main` for both
- **Cleanup branch**: `chore/archive-art-001-post-merge`
- **Workflow preserved**:
  `docs/ai/specs/.process/ART-001-workflow.md`
- **Design concept preserved**:
  `docs/ai/specs/.process/ART-001-design-concept.md`
- **Acceptance harness preserved**:
  `docs/ai/specs/.process/ART-001-acceptance-harness.html` (relocated by this
  cleanup; see Harness Relocation)
- **CI runs**:
  [#407 PR Checks](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/30542845550),
  [#407 Container Preflight](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/30542847785),
  [#409 PR Checks](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/30551286389),
  and
  [#409 Container Preflight](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/30551293196)
- **CI / metadata gates**: 19 pass and 1 skip on each PR. Every required check
  passed — title, release-note, workflow, docs, artifact-consistency, plugin,
  full-suite, CodeQL, and Linux amd64/arm64 container checks. Windows x64
  advisory smoke passed on both; Windows ARM64 advisory smoke skipped on both in
  its normal unlabelled runner state.
- **Argos build/review URL**: N/A
- **Metadata gates**: pass
- **Artifact manifest**: the shipped gallery payload is covered by the runner
  manifest and `.sha256` regenerated in #407; committed repository evidence is
  otherwise canonical
- **Screenshot retention**: N/A
- **Expiration risk**: committed source and process evidence has no artifact
  retention dependency

## Feature Summary

ART-001 shipped the Racecraft brand kit and the gallery foundation that the four
template-port specs consume: `brand-kit.css`, `brand-voice.md`, `manifest.json`,
`theme-toggle.html`, the single-file-SPA contract `SPA-CONTRACT.md`, and the MIT
attribution `UPSTREAM-NOTICE.md`.

Unlike the CAR and G56R specs archived before it, ART-001 changes the shipped
plugin payload. `speckit-pro/artifact-gallery/` materializes into both
`dist/claude/` and `dist/codex/`, and the runner payload-completeness gate plus
regenerated installed-cache proofs enforce that the directory arrives intact. The
generated artifact contract was therefore part of its merge; this cleanup changes
no payload byte.

The run's highest-value output was verification rather than code. Seven defects
were found after the implementation was written, each of which would have shipped
green. The most serious was a fail-silent gap in the payload builder: without a
two-line fix the entire gallery directory would have been absent from every
payload while the suite stayed green.

PR #409 followed up by extending the gallery validator to scan artifact script
bodies for external references and prohibited constructs, closing a hole in the
single-file-SPA contract that the original validator did not cover.

## Manual Acceptance Evidence

ART-001's manual obligations were discharged **before** merge, which is the
opposite of the CAR-004 and G56R-004 situation. The preserved workflow file
records:

> Manual acceptance evidence (T026, T027) — 2026-07-29. **Result: 12 of 12
> passed. M1–M12, no failures, none unrun.**

The run was performed by the maintainer against the acceptance harness loaded
from disk over `file://`. The harness embeds the canonical `GALLERY-HEAD` region
and the `BRAND-KIT` token block byte-identically to their source files, verified
at build time and re-verified after both surface corrections, so the run
exercised the shipped kit rather than a copy of it. T026 covered M1–M6 (SC-001,
SC-005, SC-006; FR-004) at 6/6; T027 covered M7–M12 (SC-010, SC-011; FR-022,
FR-023, FR-024) at 6/6.

**Recorded discrepancy.** The feature `retrospective.md` disagreed with itself.
Its narrative section stated the twelve scenarios ran and passed, "That closes
T026 and T027," and moved eight requirements from partial to implemented. Its
task-execution section, not updated in the same revision, still listed "2 open:
T026 and T027." The workflow record above and the merge both proceeded on the
closed reading, and the roadmap row was the stale one. This archive records the
discrepancy rather than silently reconciling it; the underlying retrospective
text is recoverable at the merge commit.

## Known Gap Carried Forward

ART-001 ships zero gallery artifacts of its own — it is the foundation, and the
four port specs are what produce artifacts — so roughly half of its validation
surface runs against synthetic fixtures rather than a real shipped artifact. The
spec states this per requirement row instead of letting a green suite imply live
coverage, which is the correct handling, not a defect.

The retrospective's own recommendation is to re-run the twelve manual scenarios
against a real shipped artifact once one exists. That closure belongs to ART-002,
which is the first port spec, and is not claimed here.

## Harness Relocation

`.process/acceptance-harness.html` was forward-looking evidence rather than
exhaust, on two independent grounds:

1. It is the only artifact behind the 12-of-12 manual result. Deleting it would
   leave the evidence claim unbacked.
2. The roadmap directs a later spec to reuse it. At
   `html-artifacts-technical-roadmap.md` the UAT-walkthrough section states that
   "a working reference implementation of both kinds already exists" at that
   path and instructs the implementer to "reuse its clipboard-failure and
   live-state handling rather than re-deriving them."

Two files outside the spec folder pointed at it — the roadmap line above and the
preserved `ART-001-workflow.md` — so removal without relocation would have left
two dangling pointers in live documents.

It was moved to `docs/ai/specs/.process/ART-001-acceptance-harness.html`
alongside the workflow and design-concept records it belongs with. Git records
the move as a rename, so it keeps exactly one home, and both references were
repointed.

No contract relocation was required. The gallery source, the payload
materializations, the payload gate, the installed-cache proofs, and the validator
were all authored outside `specs/**`. After the harness move, a repository-wide
search for the bare directory name found no live code, test, script, workflow, or
docs-site reader.

`quickstart.md`, `retrospective.md`, and `.process/changed-files.txt` are run
exhaust — a validation guide for merged work and two run records — and were
removed with the folder.

## Canonical Shipped Artifacts

- `speckit-pro/artifact-gallery/brand-kit.css`
- `speckit-pro/artifact-gallery/brand-voice.md`
- `speckit-pro/artifact-gallery/manifest.json`
- `speckit-pro/artifact-gallery/theme-toggle.html`
- `speckit-pro/artifact-gallery/SPA-CONTRACT.md`
- `speckit-pro/artifact-gallery/UPSTREAM-NOTICE.md`
- `dist/claude/speckit-pro/artifact-gallery/` and
  `dist/codex/speckit-pro/artifact-gallery/` (the same six files, materialized)
- `speckit-pro/speckit_pro_runner/gates/payloads.py`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` and
  `speckit-pro-runner.sha256` (plus both `dist/` copies)
- `tests/speckit-pro/unit/test-artifact-gallery.py`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/` (installed-cache
  proofs and cache tree, regenerated to include the gallery)
- `tests/speckit-pro/suite-manifest.json` (one entry added)
- `docs-site/src/content/docs/reference/tests.md`
- `docs/ai/specs/.process/ART-001-workflow.md`
- `docs/ai/specs/.process/ART-001-design-concept.md`
- `docs/ai/specs/.process/ART-001-acceptance-harness.html`

## Recovery Commands

`a6cc2b21` (#409) is the later merge and carries the final state of the spec
folder.

```text
git show a6cc2b21bad2fa0514eacc4032f296ddd332cc3c:specs/art-001-brand-kit-gallery-foundation/spec.md
git show a6cc2b21bad2fa0514eacc4032f296ddd332cc3c:specs/art-001-brand-kit-gallery-foundation/plan.md
git show a6cc2b21bad2fa0514eacc4032f296ddd332cc3c:specs/art-001-brand-kit-gallery-foundation/tasks.md
git show a6cc2b21bad2fa0514eacc4032f296ddd332cc3c:specs/art-001-brand-kit-gallery-foundation/research.md
git show a6cc2b21bad2fa0514eacc4032f296ddd332cc3c:specs/art-001-brand-kit-gallery-foundation/data-model.md
git show a6cc2b21bad2fa0514eacc4032f296ddd332cc3c:specs/art-001-brand-kit-gallery-foundation/quickstart.md
git show a6cc2b21bad2fa0514eacc4032f296ddd332cc3c:specs/art-001-brand-kit-gallery-foundation/retrospective.md
git show a6cc2b21bad2fa0514eacc4032f296ddd332cc3c:specs/art-001-brand-kit-gallery-foundation/SPEC-MOC.md
git show a6cc2b21bad2fa0514eacc4032f296ddd332cc3c:specs/art-001-brand-kit-gallery-foundation/contracts/gallery-validation-contract.md
git show a6cc2b21bad2fa0514eacc4032f296ddd332cc3c:specs/art-001-brand-kit-gallery-foundation/contracts/routing-catalog-contract.md
git show a6cc2b21bad2fa0514eacc4032f296ddd332cc3c:specs/art-001-brand-kit-gallery-foundation/checklists/accessibility.md
git show a6cc2b21bad2fa0514eacc4032f296ddd332cc3c:specs/art-001-brand-kit-gallery-foundation/checklists/data-integrity.md
git show a6cc2b21bad2fa0514eacc4032f296ddd332cc3c:specs/art-001-brand-kit-gallery-foundation/checklists/requirements.md
git show a6cc2b21bad2fa0514eacc4032f296ddd332cc3c:specs/art-001-brand-kit-gallery-foundation/checklists/security.md
git show a6cc2b21bad2fa0514eacc4032f296ddd332cc3c:specs/art-001-brand-kit-gallery-foundation/.process/changed-files.txt
git checkout a6cc2b21bad2fa0514eacc4032f296ddd332cc3c -- specs/art-001-brand-kit-gallery-foundation
```

The acceptance harness is **not** in this list because it was not deleted. It is
live at `docs/ai/specs/.process/ART-001-acceptance-harness.html`.

## Changed Files and Impact

| Artifact | Change |
|---|---|
| `.specify/memory/{spec,plan,changelog}.md` | Append shipped behavior, architecture, provenance, manual-acceptance evidence, the recorded retrospective discrepancy, and cleanup state |
| `.specify/memory/archive-reports/2026-07-30-art-001-post-merge-hygiene.md` | This report |
| `.specify/autopilot-state.json` | Move project archive state to ART-001 |
| `docs/ai/specs/.process/autopilot-state.json` | Mark ART-001 completed/archived and record the applied sweep |
| `docs/ai/specs/.process/ART-001-acceptance-harness.html` | Preserve the forward-looking harness from the feature `.process/` directory |
| `docs/ai/specs/.process/ART-001-workflow.md` | Repoint the manual-acceptance harness reference |
| `docs/ai/specs/html-artifacts-technical-roadmap.md` | Repoint the reference-implementation pointer; mark ART-001 complete/archived, ART-002 through ART-006 ready, and ART-009 blocked by ART-006 alone |
| `docs/ai/specs/html-artifacts-roadmap-MOC.md` | Frontmatter status; generated index zone regenerated |
| `specs/art-001-brand-kit-gallery-foundation/` | Remove completed active spec residue |

## Cleanup Decision

- **cleanupApplied**: true
- **cleanupOperation**: `git mv` the acceptance harness to
  `docs/ai/specs/.process/`, repoint its two external references, then
  `git rm -r specs/art-001-brand-kit-gallery-foundation` after merge provenance
  and a tree-wide live-reader scan
- **cleanupBranch**: `chore/archive-art-001-post-merge`
- **blockedBy**: none
- **Stacking note**: this cleanup branches from
  `chore/archive-car-005-post-merge` (PR #414), because both cleanups append to
  the same three `.specify/memory/` files and rewrite the same two
  `autopilot-state.json` files. Merge #414 first.
- **Downstream state**: ART-002 through ART-006 are ready. ART-002 through
  ART-005 have their ART-001 dependency satisfied by PR #407; ART-006 never
  depended on it. ART-009 remains blocked, now by ART-006 alone.

## Verification Commands

- `python3 -m json.tool .specify/autopilot-state.json`
- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- SpecKit runner operation `generate-spec-index-write` in apply mode
- SpecKit runner helper `generate-spec-index-check`
- final `find specs -mindepth 1 -maxdepth 4 -print` audit
- stale active-path scan across `tests/`, `speckit-pro/`, `scripts/`,
  `.github/`, `docs-site/`, `docs/`, and `.specify/`
- `python3 tests/speckit-pro/run-all.py --layer 1`
- `python3 tests/speckit-pro/run-all.py`
- release-readiness runner gate for
  `docs(art-001): archive post-merge state`
- `python3 scripts/compose-release-notes.py --validate-pr`
- `git diff --check`

## Verification Results

All checks ran from the cleanup branch after the harness relocation and the
active-spec removal, and before commit.

| Check | Result |
|---|---|
| Active spec inventory | `specs/.gitkeep` only |
| `.specify/autopilot-state.json` | valid JSON |
| `docs/ai/specs/.process/autopilot-state.json` | valid JSON |
| `generate-spec-index-write` (apply) | one write applied to `docs/ai/specs/html-artifacts-roadmap-MOC.md` |
| `generate-spec-index-check` after regen | exit 0 — index current, all in-scope maps up to date |
| Stale active-path scan outside archive/process evidence | zero live code, test, script, workflow, or docs-site references |
| Dangling harness pointers | zero; both external references repointed |
| `python3 tests/speckit-pro/run-all.py --layer 1` | 1428/1428 |
| `python3 tests/speckit-pro/run-all.py` | 7008/7008 (L1 1428, L4 5394, L5 186) |
| ART-001 focused owner within the full suite | 468/468 `test-artifact-gallery` |
| Release-readiness title gate | pass for `docs(art-001): archive post-merge state` |
| Release-note validation | pass — non-releasable conventional-commit type |
| `git diff --check` | clean |

Docs reference generation was not required: this cleanup changed no tracked
`.md`, `.py`, or `.sh` under `tests/speckit-pro/`, no plugin inventory, and no
generated docs reference page. The existing reference page remains the merged
PR #407 artifact and the full suite validates its structural contract. No payload
byte changed, so the generated artifact contract is untouched by this cleanup.

## Constitution Compliance

PASS by scope. The cleanup preserves durable evidence — including the one
forward-looking artifact, by relocation rather than deletion — changes no plugin
version or runtime payload, adds no active Bash or `jq` dependency, retains all
merged source through immutable git provenance, and leaves the full
Python-authoritative suite as the completion gate.
