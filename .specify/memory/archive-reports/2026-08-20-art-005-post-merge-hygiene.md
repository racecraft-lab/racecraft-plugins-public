# Archival Report - ART-005 Gallery Completion: Knowledge, Reports and Editors

## Mode

- **archiveMode**: merged-spec cleanup, ART sweep
- **dryRun**: false
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none — no ART-005 run is in flight

## Provenance

All dates are UTC. ART-005 shipped as seven stacked pull requests. Every pull
request is merged, and no ART-005 implementation pull request remains open.

- **Source spec path**: `specs/art-005-gallery-completion-knowledge-reports-editors/`
- **Cleanup branch**: `codex/art-005-post-merge-hygiene`
- **Cleanup base**: current `main` at `8aed3ac447e314293b9b33e779c89a099d993f23`
- **Final merged by**: `fgabelmannjr`

| PR | Title | Final head | Merged at | Merge commit |
|---|---|---|---|---|
| [#444](https://github.com/racecraft-lab/racecraft-plugins-public/pull/444) | `feat(artifact-gallery): Add slide deck reader` | `cbb3f2f60cba00b58f08129436519dfbccff32b1` | `2026-08-20T01:40:03Z` | `75651a99e6efe0cb8d37608eda14e86674b97920` |
| [#446](https://github.com/racecraft-lab/racecraft-plugins-public/pull/446) | `feat(artifact-gallery): Add concept explainer` | `a03d5fdb670cb3908033bb00d7cd6471123e2875` | `2026-08-20T02:38:39Z` | `7ff4c94cbdadf1bef8136336410015c59d83dd1a` |
| [#447](https://github.com/racecraft-lab/racecraft-plugins-public/pull/447) | `feat(artifact-gallery): Add status report` | `d4028b76df9542ddf335f98d81cccc4ab3bfc488` | `2026-08-20T02:54:59Z` | `29c9af9533f2ba6f76574089db7a3f55a4f4ee76` |
| [#448](https://github.com/racecraft-lab/racecraft-plugins-public/pull/448) | `feat(artifact-gallery): Add incident report` | `543d6cae446a1f5fed6596b0e4f59b5cc484e26f` | `2026-08-20T03:04:49Z` | `abc9e8245626838d014c81a25ed39db570488460` |
| [#452](https://github.com/racecraft-lab/racecraft-plugins-public/pull/452) | `feat(artifact-gallery): Add triage board` | `5d09b2f1750e916bb1934a297e3639303bfae059` | `2026-08-20T03:56:42Z` | `8f8052a85a745241dbd43a670cf0cb352dde207f` |
| [#454](https://github.com/racecraft-lab/racecraft-plugins-public/pull/454) | `feat(artifact-gallery): Add feature flags` | `70f46e8595306db62d296608345c4562e3f62520` | `2026-08-20T12:40:52Z` | `16a34888d44f756377ba1205dadaf0ecc45d93d6` |
| [#455](https://github.com/racecraft-lab/racecraft-plugins-public/pull/455) | `feat(artifact-gallery): Add prompt tuner` | `edb68964ad0838604c13ea3a6398833b9e66a8e2` | `2026-08-20T14:02:04Z` | `c133211f630c3c2214d05ed22f5185e0e3202424` |

The final cumulative recovery boundary is
`c133211f630c3c2214d05ed22f5185e0e3202424`. The cleanup ran in a dedicated
clean checkout. Unrelated modified and untracked files in the primary worktree
were not used as inputs and were not modified.

- **CI outcome**: the workflow record confirms all required checks passed on
  all seven exact remote code heads, with only the expected Windows ARM64
  advisory job skipped. A live read of final PR #455 returned 21 successful
  checks, 1 skipped advisory and no other conclusion
- **Required run URLs for the final PR**:
  - PR Checks: <https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/32370113351>
  - Container Preflight: <https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/32370113363>
  - CodeQL: <https://github.com/racecraft-lab/racecraft-plugins-public/runs/96428641910>
- **Review**: five blocking findings on Slices 5-7 were repaired at source and
  merged forward. The final workflow record reports no unresolved actionable
  finding
- **Argos build/review URL**: not applicable; this repository runs no visual
  regression service
- **Screenshot retention**: the exact-head Playwright session captured 14
  responsive screenshots transiently, but none is committed. Durable evidence
  is the narrative and normalized JSON record preserved below
- **Expiration risk**: transient screenshots are not durable; archival claims
  rely on committed observations and automated evidence, not screenshot access

## Feature Summary

ART-005 completed the knowledge/report/editor portion of the artifact gallery.

| Part | Result |
|---|---|
| Read-only ports | `slide-deck`, `concept-explainer`, `status-report`, `incident-report` |
| Stateful editors | `triage-board`, `feature-flags`, `prompt-tuner` |
| Editor exports | deterministic current-state Markdown or fenced JSON, with explicit issue order and clipboard fallback |
| Routing | exactly seven declared manifest rows are `shipped`; four readers export nothing and three editors retain `markdown` |
| Shared boundaries | `SPA-CONTRACT.md`, brand kit, theme toggle, undeclared templates, version manifests and export vocabulary unchanged |

All 119 tasks, 24 functional requirements and 12 success criteria completed.
The retrospective records 100% spec adherence, zero critical or significant
findings and no proposed spec change.

## Acceptance Result

Manual direct `file://` UAT is preserved at
`docs/ai/specs/.process/ART-005-uat-results.md` and
`docs/ai/specs/.process/ART-005-uat-results.json`.

- 252 total rows: 177 pass, 75 evidence-backed not applicable, 0 fail
- Chrome 151 on macOS 26.6.2 at 360 and 1280 CSS px
- online and offline reload, light/dark persistence, reduced motion, keyboard
  focus, semantic/color-independent cues and console/page-error capture
- current-state, deterministic order, invalid/empty/duplicate/special-value,
  clipboard refusal/fallback and stale-attempt observations for all editors
- connected-browser inventory was unavailable, so the operator-authorized
  Playwright MCP fallback supplied browser interaction

The normalized record is bound to source checkpoint
`f85ed14c89a5f71bb041e49930647dbc93ec8560`; the narrative also records a
seven-PR exact-head revalidation on 2026-08-19. Final review remediation later
changed only tests for `triage-board`, and changed `feature-flags` and
`prompt-tuner` to enforce schema field order plus small CSS token/syntax repairs.
Those final source/test trees match their exact PR heads and merge commits and
passed exact-head CI plus the post-archive 7659/7659 suite. The full 252-row
browser matrix was not rerun after those final two source deltas. This is a
recorded provenance limit, not an unreported exact-final-head browser claim.

Automated implementation evidence before merge was 7656/7656: focused gallery
586/586, focused fill regions 84/84, Layer 1 1469/1469 and Layer 4 5995/5995.
Generated release parity and docs reference checks were current.

## Canonical Shipped Artifacts

These live outside `specs/**` and are unaffected by cleanup.

### Source templates and routing

- `speckit-pro/artifact-gallery/templates/slide-deck.html`
- `speckit-pro/artifact-gallery/templates/concept-explainer.html`
- `speckit-pro/artifact-gallery/templates/status-report.html`
- `speckit-pro/artifact-gallery/templates/incident-report.html`
- `speckit-pro/artifact-gallery/templates/triage-board.html`
- `speckit-pro/artifact-gallery/templates/feature-flags.html`
- `speckit-pro/artifact-gallery/templates/prompt-tuner.html`
- `speckit-pro/artifact-gallery/manifest.json`

### Durable tests and generated consumers

- `tests/speckit-pro/unit/test-artifact-gallery.py`
- `tests/speckit-pro/unit/test-artifact-fill-regions.py`
- generated `dist/claude/**` and `dist/codex/**` gallery payloads
- installed-cache mirrors, fixtures and release proofs
- generated docs reference pages

### Historical process evidence

- `docs/ai/specs/.process/ART-005-design-concept.md`
- `docs/ai/specs/.process/ART-005-workflow.md`
- `docs/ai/specs/.process/ART-005-uat-runbook.md`
- `docs/ai/specs/.process/ART-005-uat-results.md`
- `docs/ai/specs/.process/ART-005-uat-results.json`
- `docs/ai/specs/.process/ART-005-retrospective.md`
- `docs/ai/specs/.process/ART-005-verify-tasks-report.md`

## Evidence Relocation

Five files were durable evidence rather than disposable planning output and
were moved with `git mv` before the active folder was removed.

| Original | Durable path | Reason |
|---|---|---|
| `.process/uat-runbook.md` | `docs/ai/specs/.process/ART-005-uat-runbook.md` | executable seven-template browser procedure |
| `.process/uat-results.md` | `docs/ai/specs/.process/ART-005-uat-results.md` | narrative 252-row closeout and exact-head revalidation |
| `.process/uat-results.json` | `docs/ai/specs/.process/ART-005-uat-results.json` | normalized machine-readable acceptance evidence |
| `retrospective.md` | `docs/ai/specs/.process/ART-005-retrospective.md` | final adherence, findings and lessons record |
| `verify-tasks-report.md` | `docs/ai/specs/.process/ART-005-verify-tasks-report.md` | 119/119 phantom-completion audit |

Top-level self-references and live workflow/state citations were repointed.
Historical per-slice path ledgers inside the UAT narrative remain unchanged so
they continue to describe the exact branch diffs they measured.

## Live-Reader Scan

The pre- and post-mutation scans covered the full joined path, evidence paths,
bare feature directory and every tracked file in the target.

| Match | Nature | Action |
|---|---|---|
| `ART-005-workflow.md` | live evidence citations, PR statuses and historical planning paths | evidence repointed, PRs marked merged, historical paths retained as history |
| `ART-005-design-concept.md` | active-run UAT path decision | durable archive paths recorded |
| `autopilot-state.json` | live report paths plus historical feature/plan identity | reports repointed, state marked archived, archive block added |
| `ART-005-uat-results.md` | top-level self-links plus historical branch ledgers | self-links repointed; ledgers retained |
| `ART-005-verify-tasks-report.md` | historical feature scope label | retained as historical identity |
| `html-artifacts-technical-roadmap.md` | active status and seven-slice projection | reconciled to Complete / Archived and realized topology |
| `html-artifacts-roadmap-MOC.md` | generated backlink into the active spec | regenerated, never hand-edited |

No live code, test, script, workflow or docs-site reader opens a removed
planning file. Historical `feature_dir`, `plan_file`, branch/source checkpoint
and implementation-note strings in `autopilot-state.json` remain identity
fields; the `archive` block records removal and durable evidence.

## Reviewability Outcome

The operator explicitly selected seven sequential stacked slices, one template
per slice. The topology stayed unchanged through `gh-stack` stack #457 and
merge.

| Slice | Artifact | Reviewable LOC | Declared ceiling | 800 stop | Result |
|---:|---|---:|---:|---:|---|
| 1 | `slide-deck` | 666 | 670 | 134 below | pass |
| 2 | `concept-explainer` | 534 | 535 | 266 below | pass |
| 3 | `status-report` | 377 | 560 | 423 below | pass |
| 4 | `incident-report` | 420 | 620 | 380 below | pass |
| 5 | `triage-board` | 695 | 785 | 105 below | pass |
| 6 | `feature-flags` | 779 | 780 | 21 below | pass |
| 7 | `prompt-tuner` | 692 | 790 | 108 below | pass |

Physical-path size findings came only from required generated or control-plane
evidence. No correctness blocker or typed exception remained.

## Recovery Commands

Every deleted tracked artifact is available from the final cumulative merge:

```text
git show c133211f630c3c2214d05ed22f5185e0e3202424:specs/art-005-gallery-completion-knowledge-reports-editors/.process/implementation-notes.md
git show c133211f630c3c2214d05ed22f5185e0e3202424:specs/art-005-gallery-completion-knowledge-reports-editors/SPEC-MOC.md
git show c133211f630c3c2214d05ed22f5185e0e3202424:specs/art-005-gallery-completion-knowledge-reports-editors/checklists/accessibility.md
git show c133211f630c3c2214d05ed22f5185e0e3202424:specs/art-005-gallery-completion-knowledge-reports-editors/checklists/data-integrity.md
git show c133211f630c3c2214d05ed22f5185e0e3202424:specs/art-005-gallery-completion-knowledge-reports-editors/checklists/error-handling.md
git show c133211f630c3c2214d05ed22f5185e0e3202424:specs/art-005-gallery-completion-knowledge-reports-editors/checklists/requirements.md
git show c133211f630c3c2214d05ed22f5185e0e3202424:specs/art-005-gallery-completion-knowledge-reports-editors/checklists/ux.md
git show c133211f630c3c2214d05ed22f5185e0e3202424:specs/art-005-gallery-completion-knowledge-reports-editors/contracts/editor-export-contract.md
git show c133211f630c3c2214d05ed22f5185e0e3202424:specs/art-005-gallery-completion-knowledge-reports-editors/contracts/gallery-template-contract.md
git show c133211f630c3c2214d05ed22f5185e0e3202424:specs/art-005-gallery-completion-knowledge-reports-editors/contracts/slice-topology-contract.md
git show c133211f630c3c2214d05ed22f5185e0e3202424:specs/art-005-gallery-completion-knowledge-reports-editors/contracts/uat-evidence-contract.md
git show c133211f630c3c2214d05ed22f5185e0e3202424:specs/art-005-gallery-completion-knowledge-reports-editors/data-model.md
git show c133211f630c3c2214d05ed22f5185e0e3202424:specs/art-005-gallery-completion-knowledge-reports-editors/plan.md
git show c133211f630c3c2214d05ed22f5185e0e3202424:specs/art-005-gallery-completion-knowledge-reports-editors/quickstart.md
git show c133211f630c3c2214d05ed22f5185e0e3202424:specs/art-005-gallery-completion-knowledge-reports-editors/research.md
git show c133211f630c3c2214d05ed22f5185e0e3202424:specs/art-005-gallery-completion-knowledge-reports-editors/spec.md
git show c133211f630c3c2214d05ed22f5185e0e3202424:specs/art-005-gallery-completion-knowledge-reports-editors/tasks.md
git checkout c133211f630c3c2214d05ed22f5185e0e3202424 -- specs/art-005-gallery-completion-knowledge-reports-editors
```

The five durable evidence files are absent from this deletion list because they
were moved, not deleted. Their original bytes are also available from the same
merge commit.

## Known Gaps Carried Forward

No product or specification gap is carried forward. The only evidence limit is
the explicitly recorded lack of a second 252-row browser run after the final
field-order and CSS remediation on Slices 6-7. Exact final source/test trees,
required CI and the full post-archive suite are green; the archive does not
promote that automated evidence into an exact-final-head browser claim.

## Changed Files and Impact

| Surface | Change |
|---|---|
| `.specify/memory/{spec,plan,changelog}.md` | ART-005 shipped behavior, topology, acceptance and cleanup appended |
| `.specify/memory/archive-reports/2026-08-20-art-005-post-merge-hygiene.md` | this report |
| `docs/ai/specs/.process/ART-005-{uat-runbook,uat-results,retrospective,verify-tasks-report}.*` | five durable evidence files relocated and self-links repointed |
| `docs/ai/specs/.process/ART-005-design-concept.md` | archival UAT locations recorded |
| `docs/ai/specs/.process/ART-005-workflow.md` | evidence citations and merged stack state reconciled |
| `docs/ai/specs/.process/autopilot-state.json` | merged and archived state recorded |
| `docs/ai/specs/html-artifacts-technical-roadmap.md` | ART-005 archived and realized topology recorded |
| `docs/ai/specs/html-artifacts-roadmap-MOC.md` | generated dead backlink removed |
| `specs/art-005-gallery-completion-knowledge-reports-editors/**` | 17 tracked planning/run-exhaust files removed; 5 evidence files relocated |

No `speckit-pro/` source or generated payload input changed, so
`refresh-release-artifacts.py` is not required.

## Constitution Compliance

No constitution file exists. This archive changes documentation and project
memory only. It adds no runtime, active Bash or `jq` dependency, version,
manifest, lockfile or generated release-payload change.

## Cleanup Decision

- **cleanupApplied**: true
- **cleanupOperation**: preserve five durable evidence files with `git mv`,
  repoint live citations, then `git rm -r` the single merged ART-005 active spec
  directory
- **cleanupBranch**: `codex/art-005-post-merge-hygiene`
- **blockedBy**: none

| # | Gate | Result |
|---|---|---|
| 1 | Cleanup explicitly requested | pass |
| 2 | Target is not an active current run | pass |
| 3 | Merged, with PR URLs and merge commits | pass; #444/#446/#447/#448/#452/#454/#455, final `c133211f` |
| 4 | Archive completed in this run | pass |
| 5 | Recovery commands per deleted artifact | pass; 17 commands plus full-directory recovery |
| 6 | Worktree clean before cleanup | pass |
| 7 | Active branch is a safe base | pass with recorded deviation below |
| 8 | No history rewrite or reliance on post-merge mutation | pass |

**Gate 7 deviation.** The extension names `main` as the normal cleanup branch.
This repository lands changes through pull requests, so the archive uses a
dedicated branch cut from current `main`. It contains only ART-005 post-merge
hygiene and one generator-owned MOC update.

## Verification Commands

All final checks passed after the removal:

- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json` — valid
- `python3 -m json.tool docs/ai/specs/.process/ART-005-uat-results.json` — valid
- runner `generate-spec-index-write` in apply mode — one generated MOC updated
- runner `generate-spec-index-check` — index current, exit 0
- `pnpm --dir docs-site reference:check` — reference pages current
- `find specs -mindepth 1 -maxdepth 4 -print` — only `.gitkeep` and incomplete
  BRAND-001 remain
- stale active-path and relocated-evidence scan — no dangling live citation
- exact final PR-head to merge-commit source/test comparisons — no diff for
  Slices 5, 6 or 7
- `python3 tests/speckit-pro/unit/test-generate-spec-index.py` — 18/18
- `git diff --check` — clean
- `python3 tests/speckit-pro/run-all.py --layer 1` — 1469/1469
- `python3 tests/speckit-pro/run-all.py` — 7659/7659: Layer 1 1469, Layer 4
  5998, Layer 5 192; toolchain preflight passed
- live release-readiness gate for `docs(art-005): archive post-merge state` —
  `validate-pr-title` pass, blocking false

## Defaults Applied

- The agent-knowledge step was skipped because repository agent-file hygiene
  forbids release history and implementation transcripts in `AGENTS.md`.
- `.specify/feature.json` did not exist; no replacement was invented. The
  feature-bound prerequisite helper therefore had no active directory to bind,
  and the explicit `ART` sweep plus live merge provenance selected ART-005.
- BRAND-001 is incomplete and remained untouched. No other active ART spec
  directory exists on current `main`.
- No scope modifiers were passed, so all applicable archival memory and index
  surfaces were updated.
