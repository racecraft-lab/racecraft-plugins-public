# Archival Report - ART-004 Gallery Completion: Design and Prototyping

## Mode

- **archiveMode**: merged-spec cleanup, single spec
- **dryRun**: false
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none — no ART-004 run is in flight

## Provenance

All dates are UTC. ART-004 shipped as one pull request and no ART-004 pull
request remains open.

- **Source spec path**: `specs/art-004-gallery-completion-design-prototyping/`
- **Cleanup branch**: `art-004-post-merge-hygiene`
- **Merged by**: `fgabelmannjr`

| PR | Title | Head branch | Merged at | Merge commit | Size |
|---|---|---|---|---|---|
| [#450](https://github.com/racecraft-lab/racecraft-plugins-public/pull/450) | `feat(art-004): complete design gallery artifacts` | `art-004-gallery-completion-design-prototyping` | `2026-08-18T23:35:40Z` | `97b255d39828425120a96a5d9e313d574ebbf8a9` | 94 files, +43193 −449 |

The final feature head was `ecabf297dce87ee5652e876ed0e60f0ff5996b43`.
The cleanup branch was cut from the merge commit in a dedicated clean worktree;
the unrelated dirty ART-005 files in the primary checkout were never read as
archive inputs and were not modified.

- **Branch commits**: 31
- **CI outcome**: 19 pass, 2 expected skips, 0 failures in the deduplicated
  `gh pr checks` view. `gh pr checks 450` exited 0
- **Required run URLs**:
  - PR Checks: <https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/32193679758>
  - Container Preflight: <https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/32193679737>
  - CodeQL: <https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/32192319748>
- **Review**: two threads, both resolved. They represented the same unused
  source declaration through two generated payloads. Commit `37fcc4d4f` removed
  it at source and regenerated the mirrors. Zero unresolved threads, zero issue
  comments, and no actionable review finding remained
- **Argos build/review URL**: not applicable; this repository runs no visual
  regression service
- **Screenshot retention**: no ART-004 screenshot is committed
- **Expiration risk**: none for committed evidence

## Feature Summary

ART-004 completed the design/prototyping portion of the artifact gallery and
absorbed the complete ART-020 keyboard-scroll repair.

| Part | Result |
|---|---|
| Read-only ports | `design-system`, `animation-prototype`, `interaction-prototype`, `svg-illustrations` |
| Decision/export ports | `visual-designs`, `component-variants` |
| Existing templates repaired | `code-approaches`, `implementation-plan`, `module-map` |
| Durable guard | manifest-driven Layer 4 keyboard-scroll checks, negative fixture, and per-capability non-vacuity floors |
| Routing | exactly six manifest statuses changed from `planned` to `shipped`; all non-status fields stayed byte-identical |

All 60 tasks, 17 functional requirements, and 9 success criteria completed.
The retrospective records 100% spec adherence, zero critical or significant
findings, one resolved minor finding, and no proposed spec changes.

## Acceptance Result

Manual `file://` UAT was completed before merge and is preserved at
`docs/ai/specs/.process/ART-004-manual-uat.md`.

- Chromium and Safari covered the three repaired templates and all eleven real
  keyboard-scroll regions
- Chromium and Safari covered the four read-only ports
- Chromium, WebKit, and Safari covered both decision/export ports, including
  exact prompt and Markdown payloads, invalid input, clipboard refusal and
  fallback, stale settlement, keyboard operation, reduced motion, contrast,
  semantics, and narrow viewports
- Two genuine findings were remediated: module-map needed a zero-minimum content
  track, and interaction-prototype needed zero-minimum mobile tracks and wrapping
- The consolidated matrix passed after remediation for all nine artifacts

Automated implementation evidence at merge was 7628/7628: Layer 1 1468/1468,
Layer 4 5968/5968, Layer 5 192/192, privacy 10/10. Release payloads and generated
reference pages matched their source.

## Canonical Shipped Artifacts

These live outside `specs/**` and are unaffected by cleanup.

### Source templates and routing

- `speckit-pro/artifact-gallery/templates/design-system.html`
- `speckit-pro/artifact-gallery/templates/animation-prototype.html`
- `speckit-pro/artifact-gallery/templates/interaction-prototype.html`
- `speckit-pro/artifact-gallery/templates/svg-illustrations.html`
- `speckit-pro/artifact-gallery/templates/visual-designs.html`
- `speckit-pro/artifact-gallery/templates/component-variants.html`
- `speckit-pro/artifact-gallery/templates/code-approaches.html`
- `speckit-pro/artifact-gallery/templates/implementation-plan.html`
- `speckit-pro/artifact-gallery/templates/module-map.html`
- `speckit-pro/artifact-gallery/manifest.json`

### Durable tests and generated consumers

- `tests/speckit-pro/unit/test-artifact-gallery.py`
- `tests/speckit-pro/unit/test-artifact-fill-regions.py`
- generated `dist/claude/**` and `dist/codex/**` payloads
- installed-cache fixtures and release proofs
- generated docs reference pages

### Historical process evidence

- `docs/ai/specs/.process/ART-004-design-concept.md`
- `docs/ai/specs/.process/ART-004-workflow.md`
- `docs/ai/specs/.process/ART-004-manual-uat.md`
- `docs/ai/specs/.process/ART-004-retrospective.md`
- `docs/ai/specs/.process/ART-004-verify-tasks-report.md`

## Evidence Relocation

Three files were evidence rather than disposable planning output and were moved
with `git mv` before the active folder was removed.

| Original | Durable path | Reason |
|---|---|---|
| `quickstart.md` | `docs/ai/specs/.process/ART-004-manual-uat.md` | contains the completed cross-browser UAT matrix and remediation evidence |
| `retrospective.md` | `docs/ai/specs/.process/ART-004-retrospective.md` | final adherence and findings record |
| `verify-tasks-report.md` | `docs/ai/specs/.process/ART-004-verify-tasks-report.md` | machine-readable 60/60 verification record |

The workflow and process state were repointed. Line-addressable UAT citations
retain the same line numbers because the file bytes were moved unchanged.

## Live-Reader Scan

The pre-mutation scan covered the full joined path, the bare directory name,
each evidence filename, and every tracked file in the target.

| Match | Nature | Action |
|---|---|---|
| `docs/ai/specs/.process/ART-004-workflow.md` | durable UAT, retrospective, and verify-tasks citations plus historical spec paths | durable citations repointed; historical paths retained as history |
| `docs/ai/specs/.process/autopilot-state.json` | live report paths plus historical feature, branch, implementation-note, and packet identity | report paths repointed; state marked archived; historical identity retained |
| `docs/ai/specs/html-artifacts-technical-roadmap.md` | active status and ART-020 disposition | reconciled to Complete / Archived and shipped |
| `docs/ai/specs/html-artifacts-roadmap-MOC.md` | generated backlink into the active spec | regenerated, never hand-edited |

No live code, test, script, workflow, or docs-site reader opens any removed
planning file. The feature/branch, implementation-note, and PR-packet strings in
`autopilot-state.json` are historical identity fields; the new `archive` block
records that their source folder was removed and points at durable evidence.

`implementation-notes.md`, the contracts, checklists, planning documents, and
tracked PR-packet outputs are recoverable run history. The merged GitHub pull
request remains the canonical packet/body record, so they were not relocated.

## Reviewability Outcome

The initial combined Plan gate blocked at 865 reviewable LOC, nine production
files, and eleven total authored surfaces. It was not overridden.

| Approved slice | Reviewable LOC | Result |
|---|---:|---|
| Keyboard foundation | 160 | pass |
| Four read-only ports | 590 | warn |
| Two decision/export ports | 520 | warn |

The operator explicitly approved those three slices. Every result was
non-blocking and the topology stayed unchanged through merge.

## Recovery Commands

Every deleted tracked artifact is available from the merge commit:

```text
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/.process/implementation-notes.md
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/.process/pr-packets/art-004.json
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/.process/pr-packets/art-004/body.md
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/.process/pr-packets/art-004/validation.json
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/SPEC-MOC.md
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/checklists/accessibility.md
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/checklists/error-handling.md
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/checklists/requirements.md
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/checklists/ux.md
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/contracts/decision-export-contract.md
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/contracts/gallery-artifact-contract.md
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/contracts/keyboard-scroll-guard-contract.md
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/contracts/reviewability-slice-1-keyboard-foundation.md
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/contracts/reviewability-slice-2-read-only-ports.md
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/contracts/reviewability-slice-3-decision-ports.md
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/data-model.md
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/plan.md
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/research.md
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/spec.md
git show 97b255d39828425120a96a5d9e313d574ebbf8a9:specs/art-004-gallery-completion-design-prototyping/tasks.md
git checkout 97b255d39828425120a96a5d9e313d574ebbf8a9 -- specs/art-004-gallery-completion-design-prototyping
```

The UAT, retrospective, and verify-tasks files are absent from this deletion
list because they were moved, not deleted.

## Known Gaps Carried Forward

None. The deferred UAT-skeleton helper did not erase acceptance evidence: the
real executed matrix is preserved. ART-020's full scope is shipped, not deferred.

## Changed Files and Impact

| Surface | Change |
|---|---|
| `.specify/memory/{spec,plan,changelog}.md` | ART-004 shipped behavior, topology, acceptance, and cleanup appended |
| `.specify/memory/archive-reports/2026-08-18-art-004-post-merge-hygiene.md` | this report |
| `docs/ai/specs/.process/ART-004-{manual-uat,retrospective,verify-tasks-report}.md` | durable evidence relocated |
| `docs/ai/specs/.process/ART-004-workflow.md` | evidence citations repointed |
| `docs/ai/specs/.process/autopilot-state.json` | merged and archived state recorded |
| `docs/ai/specs/html-artifacts-technical-roadmap.md` | ART-004 archived; ART-020 shipped disposition recorded |
| `docs/ai/specs/html-artifacts-roadmap-MOC.md` | generated dead backlink removed |
| `specs/art-004-gallery-completion-design-prototyping/**` | 20 tracked planning/run-exhaust files removed; 3 evidence files relocated |

No `speckit-pro/` source or generated payload input changed, so
`refresh-release-artifacts.py` is not required.

## Constitution Compliance

No conflict. This archive changes documentation and project memory only. It
adds no runtime, Bash, `jq`, dependency, version, manifest, or generated-payload
change.

## Cleanup Decision

- **cleanupApplied**: true
- **cleanupOperation**: preserve three durable evidence files with `git mv`,
  repoint live citations, then `git rm -r` the single merged ART-004 active spec
  directory
- **cleanupBranch**: `art-004-post-merge-hygiene`
- **blockedBy**: none

| # | Gate | Result |
|---|---|---|
| 1 | Cleanup explicitly requested | pass |
| 2 | Target is not an active current run | pass |
| 3 | Merged, with PR URL and merge commit | pass; #450, `97b255d3` |
| 4 | Archive completed in this run | pass |
| 5 | Recovery commands per deleted artifact | pass |
| 6 | Worktree clean before cleanup | pass |
| 7 | Active branch is a safe base | pass with recorded deviation below |
| 8 | No history rewrite or reliance on post-merge mutation | pass |

**Gate 7 deviation.** The extension names `main` as the normal cleanup branch.
This repository forbids direct commits to `main`, so the archive uses a dedicated
branch cut from current `origin/main` at the ART-004 merge commit. It contains no
feature work and matches the established post-merge hygiene precedent.

## Verification Commands

All final checks passed after the removal:

- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json` — valid
- runner `generate-spec-index-write` in apply mode — one generated MOC updated
- runner `generate-spec-index-check` — index current, exit 0
- `pnpm --dir docs-site reference:check` — reference pages current
- `find specs -mindepth 1 -maxdepth 4 -print` — only `.gitkeep` and the
  incomplete BRAND-001 planning package remain
- stale active-path and relocated-evidence scan — no dangling live citation
- `git diff --check` — clean
- `python3 tests/speckit-pro/run-all.py --layer 1` — 1468/1468
- `python3 tests/speckit-pro/run-all.py` — 7628/7628: Layer 1 1468, Layer 4
  5968, Layer 5 192; toolchain preflight passed
- release-readiness `validate-pr-title` evidence for
  `docs(art-004): archive post-merge state` — pass, blocking false

## Defaults Applied

- The agent-knowledge step was skipped because repository agent-file hygiene
  forbids release history and implementation transcripts in `AGENTS.md`.
- `.specify/feature.json` did not exist; no replacement was invented.
- BRAND-001 is incomplete and remained untouched. ART-005 is unrelated work and
  remained untouched.
- No scope modifiers were passed, so all applicable archival memory and index
  surfaces were updated.
