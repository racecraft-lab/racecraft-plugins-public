# Archival Report: DOC-008 and DOC-009 Post-Merge Hygiene

## Mode

- archiveMode: multi-feature
- dryRun: false
- applyCleanupRequested: true
- dryRunProvenanceOnly: false
- safeToApplyCleanup: true

## Sweep Summary

| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/doc-008-troubleshooting-security-trust-update-rollback` | merged | cleanup applied | DOC-008 shipped through merged PR #220. Canonical durable content now lives in the docs-site troubleshooting, security/trust, update/rollback, install, and reference routes; residual tracked content under `specs/**` is recoverable workflow/spec evidence only. |
| `specs/doc-009-maintainer-contributor-release-workflow` | merged | cleanup applied | DOC-009 shipped through merged PR #219. Canonical durable content now lives in the docs-site contributor/release workflow route; residual tracked content under `specs/**` is recoverable workflow/spec evidence only. |

## Cleanup Preconditions

- Requested mode: `--apply-cleanup`
- Installed extension: `archive` v1.1.0 from `.specify/extensions/archive/extension.yml`
- Extension command contract: `.specify/extensions/archive/commands/archive.md`
- Execution note: Codex executed the installed archive contract directly through the `speckit-archive-cleanup` plugin skill.
- Cleanup branch: `codex/doc-specs-post-merge-hygiene`, based on updated `origin/main`
- Worktree state before archival edits: clean
- `.specify/feature.json`: absent
- Current target exclusion: none; DOC-008 and DOC-009 were archived after PRs #220 and #219 merged.
- Extension hooks: no `before_archive` or `after_archive` hooks are configured in `.specify/extensions.yml`.

## Provenance

| Spec | PR | Title | Merged at | Merge commit | Tree reference | Task completion |
|------|----|-------|-----------|--------------|----------------|-----------------|
| DOC-008 | #220 | `docs(DOC-008): Add troubleshooting, Security, Trust, Update, and Rollback` | 2026-06-18T15:16:34Z | `a27fc5dcb2b295fd7ea2d3250d2df58692a7408b` | `0ec6e8b0dd3fecdc39233208bf0623d6d63c2954` | 40 / 40 |
| DOC-009 | #219 | `docs(DOC-009): document maintainer contributor release workflow` | 2026-06-18T16:37:02Z | `2686caa2a12dbaf460c33f37f054f40765fb2b35` | `4175b9ee51fd256943945ffb157f22c97faa7496` | 23 / 23 |

- Source spec paths:
  - `specs/doc-008-troubleshooting-security-trust-update-rollback`
  - `specs/doc-009-maintainer-contributor-release-workflow`
- Source workflows:
  - `docs/ai/specs/.process/DOC-008-workflow.md`
  - `docs/ai/specs/.process/DOC-009-workflow.md`
- Design concepts:
  - `docs/ai/specs/.process/DOC-008-design-concept.md`
  - `docs/ai/specs/.process/DOC-009-design-concept.md`
- Canonical shipped docs:
  - `docs-site/src/content/docs/troubleshooting.md`
  - `docs-site/src/content/docs/security-and-trust.md`
  - `docs-site/src/content/docs/update-and-rollback.md`
  - `docs-site/src/content/docs/install/claude-code.md`
  - `docs-site/src/content/docs/install/codex.md`
  - `docs-site/src/content/docs/reference.md`
  - `docs-site/src/content/docs/contribute-and-release.md`
- Screenshot retention: N/A; DOC-008 and DOC-009 were static documentation slices and produced no durable screenshot artifact in this cleanup.
- Expiration risk: Low for committed artifacts; GitHub Actions logs may expire according to GitHub retention policy.

## Feature Summary

DOC-008 completed the trust and maintenance support tier for users evaluating
or recovering a SpecKit Pro installation. It expanded troubleshooting into a
source-backed symptom matrix, clarified security/trust boundaries without
claiming an audit or certification, added update and rollback guidance, and
linked install/reference routes to the new recovery content.

DOC-009 completed the maintainer and contributor release workflow page. It
deepened the existing `/contribute-and-release` route with a source-of-truth
map, change-type matrix, release-readiness commands, payload and marketplace
sync guidance, version ownership, PR title/body expectations, current PR
Checks behavior, release automation observations, and the DOC-010 handoff for
future docs-site CI hardening.

Together, DOC-008 and DOC-009 complete the remaining trust and maintenance
content tier after DOC-007. DOC-010 is now ready to scaffold as the final docs
quality hardening slice.

## Recovery Commands

```text
git show a27fc5dcb2b295fd7ea2d3250d2df58692a7408b:specs/doc-008-troubleshooting-security-trust-update-rollback/spec.md
git show a27fc5dcb2b295fd7ea2d3250d2df58692a7408b:specs/doc-008-troubleshooting-security-trust-update-rollback/plan.md
git show a27fc5dcb2b295fd7ea2d3250d2df58692a7408b:specs/doc-008-troubleshooting-security-trust-update-rollback/tasks.md
git show a27fc5dcb2b295fd7ea2d3250d2df58692a7408b:specs/doc-008-troubleshooting-security-trust-update-rollback/SPEC-MOC.md
git show a27fc5dcb2b295fd7ea2d3250d2df58692a7408b:specs/doc-008-troubleshooting-security-trust-update-rollback/research.md
git show a27fc5dcb2b295fd7ea2d3250d2df58692a7408b:specs/doc-008-troubleshooting-security-trust-update-rollback/data-model.md
git show a27fc5dcb2b295fd7ea2d3250d2df58692a7408b:specs/doc-008-troubleshooting-security-trust-update-rollback/quickstart.md
git show a27fc5dcb2b295fd7ea2d3250d2df58692a7408b:docs/ai/specs/.process/DOC-008-workflow.md
git show a27fc5dcb2b295fd7ea2d3250d2df58692a7408b:docs/ai/specs/.process/DOC-008-design-concept.md
git checkout a27fc5dcb2b295fd7ea2d3250d2df58692a7408b -- specs/doc-008-troubleshooting-security-trust-update-rollback

git show 2686caa2a12dbaf460c33f37f054f40765fb2b35:specs/doc-009-maintainer-contributor-release-workflow/spec.md
git show 2686caa2a12dbaf460c33f37f054f40765fb2b35:specs/doc-009-maintainer-contributor-release-workflow/plan.md
git show 2686caa2a12dbaf460c33f37f054f40765fb2b35:specs/doc-009-maintainer-contributor-release-workflow/tasks.md
git show 2686caa2a12dbaf460c33f37f054f40765fb2b35:specs/doc-009-maintainer-contributor-release-workflow/SPEC-MOC.md
git show 2686caa2a12dbaf460c33f37f054f40765fb2b35:specs/doc-009-maintainer-contributor-release-workflow/research.md
git show 2686caa2a12dbaf460c33f37f054f40765fb2b35:specs/doc-009-maintainer-contributor-release-workflow/quickstart.md
git show 2686caa2a12dbaf460c33f37f054f40765fb2b35:specs/doc-009-maintainer-contributor-release-workflow/retrospective.md
git show 2686caa2a12dbaf460c33f37f054f40765fb2b35:specs/doc-009-maintainer-contributor-release-workflow/verify-tasks-report.md
git show 2686caa2a12dbaf460c33f37f054f40765fb2b35:docs/ai/specs/.process/DOC-009-workflow.md
git show 2686caa2a12dbaf460c33f37f054f40765fb2b35:docs/ai/specs/.process/DOC-009-design-concept.md
git checkout 2686caa2a12dbaf460c33f37f054f40765fb2b35 -- specs/doc-009-maintainer-contributor-release-workflow
```

## Changed Files

| File | Change Summary |
|------|----------------|
| `.specify/memory/spec.md` | Appended distilled DOC-008 and DOC-009 feature records |
| `.specify/memory/plan.md` | Appended DOC-008/DOC-009 archive hygiene plan record |
| `.specify/memory/changelog.md` | Appended DOC-008/DOC-009 provenance and recovery commands |
| `.specify/memory/archive-reports/2026-06-18-doc-008-009-post-merge-hygiene.md` | Recorded archive and cleanup evidence |
| `AGENTS.md` | Added DOC-008/DOC-009 archive cleanup notes |
| `docs/traceability-interactive-documentation.md` | Marked DOC-008 and DOC-009 completed and DOC-010 ready |
| `docs/roadmap-interactive-documentation.md` | Marked DOC-008 and DOC-009 completed and archived |
| `docs/ai/specs/interactive-documentation-technical-roadmap.md` | Marked DOC-008 and DOC-009 archived and DOC-010 ready to scaffold |
| `docs/ai/specs/interactive-documentation-roadmap-MOC.md` | Refreshed roadmap status and regenerated active-spec index after cleanup |
| `docs/ai/specs/tool-agnostic-capability-discovery-roadmap-MOC.md` | Cleared stale generated DOC active-spec index rows after the shared generator refresh |
| `docs/ai/specs/.process/autopilot-state.json` | Replaced stale archive state with completed DOC-008/DOC-009 archive state |
| `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh` | Hardened empty active-spec discovery so roadmap-MOC regeneration succeeds when `specs/**` contains only `.gitkeep` |
| `dist/claude/speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh` | Mirrored the source generator hardening into the Claude payload copy |
| `dist/codex/speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh` | Mirrored the source generator hardening into the Codex payload copy |
| `tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh` | Added regression coverage for roadmap-MOC regeneration with zero active spec directories |
| `specs/doc-008-troubleshooting-security-trust-update-rollback` | Removed completed active spec folder |
| `specs/doc-009-maintainer-contributor-release-workflow` | Removed completed active spec folder |

## Post-Cleanup Verification

- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`: passed
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh .`: regenerated `interactive-documentation-roadmap-MOC.md` and `tool-agnostic-capability-discovery-roadmap-MOC.md`
- `bash tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh`: 90/90 passed
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`: passed
- `find specs -mindepth 1 -maxdepth 4 -print`: only `specs/.gitkeep` remains
- `git diff --check`: passed
- `bash tests/speckit-pro/run-all.sh`: 3070/3070 passed

## Feature Status

DOC-008 and DOC-009 are complete and archived. DOC-010 is now ready to scaffold
as the final interactive documentation quality hardening spec.

## Constitution Compliance

PASS. Cleanup is post-merge, provenance-backed, history-preserving, and gated by
recorded recovery commands. DOC-008 and DOC-009 shipped static docs-site
content; no manifests, hooks, release automation, or CI behavior is changed by
this cleanup. The shared spec-index generator and its generated payload copies
are hardened only for the zero-active-spec archive cleanup state exposed by
this sweep.

## Cleanup Decision

- cleanupApplied: true
- cleanupCommand: `git rm -r specs/doc-008-troubleshooting-security-trust-update-rollback specs/doc-009-maintainer-contributor-release-workflow`
- blockedBy: None

## Defaults Applied

- `.specify/feature.json` was absent and not recreated.
- Historical workflow/process artifacts under `docs/ai/specs/.process/` were retained.
- DOC-008 and DOC-009 active spec paths contained specification, planning,
  checklist, review-packet, retrospective, and validation evidence; this report
  records recovery commands before removing those active source folders.

## Scoping

The cleanup removes only completed DOC-008 and DOC-009 planning evidence from
active `specs/**`. The shipped docs-site pages, generated reference pages,
workflow files, design concepts, roadmap records, and archive report remain in
durable repository paths. The generator/test change is limited to making empty
active-spec discovery deterministic after the final active spec folders are
archived.
