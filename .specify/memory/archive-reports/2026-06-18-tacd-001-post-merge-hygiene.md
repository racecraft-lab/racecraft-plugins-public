# Archival Report: TACD-001 Post-Merge Hygiene

## Mode

- archiveMode: single-feature
- dryRun: false
- applyCleanupRequested: true
- dryRunProvenanceOnly: false
- safeToApplyCleanup: true

## Sweep Summary

| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/tacd-001-platform-mechanics-spike` | merged | cleanup applied | TACD-001 shipped through merged PRs #211-#214; PR #216 adopted the spike decisions into the PRD and roadmap; the canonical durable report lives at `docs/ai/research/tool-agnostic-capability-discovery-spike.md`; residual tracked content under `specs/**` is recoverable workflow/spec evidence only. |

## Cleanup Preconditions

- Requested mode: `--apply-cleanup`
- Installed extension: `archive` v1.1.0 from `.specify/extensions/archive/extension.yml`
- Extension command contract: `.specify/extensions/archive/commands/archive.md`
- Execution note: Codex executed the installed archive contract directly through the `speckit-archive-cleanup` plugin skill.
- Cleanup branch: `codex/tacd-001-post-merge-hygiene`, based on updated `origin/main`
- Worktree state before archival edits: clean
- `.specify/feature.json`: absent
- Current target exclusion: none; TACD-001 was archived after PRs #211-#214 and #216 merged.
- Extension hooks: no `before_archive` or `after_archive` hooks are configured in `.specify/extensions.yml`.

## Provenance

| PR | Title | Merged at | Merge commit | Tree reference | Scope |
|----|-------|-----------|--------------|----------------|-------|
| #211 | `feat(speckit-pro): Add platform mechanics spike foundation` | 2026-06-17T22:47:15Z | `2104432cb8d92c0088b99f02e0922d5ebf433a98` | `ab754c7e7fdd61281c97e8d4ca140a414cec9a85` | TACD-001 scaffold/foundation artifacts |
| #212 | `feat(speckit-pro): Document runtime capability mechanics` | 2026-06-18T00:03:52Z | `e9d3c08af55658b97452c86c294bae0b340a3bc4` | `7fd0642c4f076ab5a0d0830987c1833e15b6daf1` | runtime mechanics evidence and spike report development |
| #213 | `feat(speckit-pro): Classify active and historical references` | 2026-06-18T01:04:12Z | `dfa18a20691b86724cc05008c2b3fae93a0d9127` | `60a3970fd64cfbe3c6f1f61421cbe6532ecf56f6` | active-vs-historical reference classification |
| #214 | `feat(speckit-pro): Recommend directive home and handoffs` | 2026-06-18T01:11:16Z | `46d01dcf081a8c416c692db497daea5cae11a801` | `61f2a4a2118edc6b8eeca93c285741119a183eac` | directive-home recommendation and TACD-002/TACD-003/TACD-004 handoffs |
| #216 | `docs(TACD): Adopt platform spike decisions` | 2026-06-18T01:34:18Z | `62dc58a46419ed09c1aa506974ef8c7fbab998ee` | `060dd16f5186049ce8455a50c77a88a2e78ed441` | PRD and technical-roadmap adoption of TACD-001 decisions |

- Source spec path:
  - `specs/tacd-001-platform-mechanics-spike`
- Source workflow:
  - `docs/ai/specs/.process/TACD-001-workflow.md`
- Design concept:
  - `docs/ai/specs/.process/TACD-001-design-concept.md`
- Canonical shipped report and planning records:
  - `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
  - `docs/prd-tool-agnostic-capability-discovery.md`
  - `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md`
  - `docs/ai/specs/tool-agnostic-capability-discovery-roadmap-MOC.md`
- CI evidence:
  - PR #214 checks passed: CodeQL, validate-plugins, Analyze actions/javascript-typescript/python, detect, validate-pr-title.
  - PR #216 checks passed: CodeQL, validate-plugins, Analyze actions/javascript-typescript/python, detect, validate-pr-title.
- Screenshot retention: N/A; TACD-001 was a report-only spike with no visual artifacts.
- Expiration risk: Low for committed artifacts; GitHub Actions logs may expire according to GitHub retention policy.

## Feature Summary

TACD-001 answered the platform-risk questions for moving SpecKit Pro from named
optional MCP preferences to installed-capability discovery. The spike report
audits active Claude and Codex references, classifies active vs historical
named-tool text, records source-backed and environment-specific capability
mechanics, recommends a shared capability-discovery reference with
runtime-specific pointers and approved equivalents, defines TACD-004 allowlist
categories, and hands behavior changes to TACD-002/TACD-003/TACD-004.

## Recovery Commands

```text
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/spec.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/plan.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/tasks.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/SPEC-MOC.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/research.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/data-model.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/quickstart.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/checklists/integration.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/checklists/llm-integration.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/checklists/error-handling.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/checklists/requirements.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:docs/ai/research/tool-agnostic-capability-discovery-spike.md
git show 62dc58a46419ed09c1aa506974ef8c7fbab998ee:docs/prd-tool-agnostic-capability-discovery.md
git show 62dc58a46419ed09c1aa506974ef8c7fbab998ee:docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md
git checkout 46d01dcf081a8c416c692db497daea5cae11a801 -- specs/tacd-001-platform-mechanics-spike
```

## Changed Files

| File | Change Summary |
|------|----------------|
| `.specify/memory/spec.md` | Appended distilled TACD-001 feature record |
| `.specify/memory/plan.md` | Appended TACD-001 archive hygiene plan record |
| `.specify/memory/changelog.md` | Appended TACD-001 provenance and recovery commands |
| `.specify/memory/archive-reports/2026-06-18-tacd-001-post-merge-hygiene.md` | Recorded archive and cleanup evidence |
| `AGENTS.md` | Added TACD-001 archive cleanup note |
| `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md` | Marked TACD-001 archived and TACD-002 ready to scaffold from the report |
| `docs/ai/specs/tool-agnostic-capability-discovery-roadmap-MOC.md` | Replaced active TACD-001 spec link with the canonical spike report link |
| `docs/ai/specs/.process/autopilot-state.json` | Replaced active TACD-001 state with completed archive state |
| `specs/tacd-001-platform-mechanics-spike` | Removed residual active spec evidence |

## Post-Cleanup Verification

- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh .`
  regenerated roadmap MOC generated zones after the active TACD-001 spec folder
  was removed.
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`
  passed with all in-scope maps up to date.
- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
  passed.
- `find specs -mindepth 1 -maxdepth 4 -print` returned only `specs/.gitkeep`
  after cleanup.
- `git diff --check` passed.
- `bash tests/speckit-pro/run-all.sh` passed `3041/3041`.
  - Layer 1 structural: `573/573`.
  - Layer 1 Codex structural: `451/451`.
  - Layer 4 script unit: `1827/1827`.
  - Layer 5 tool scoping: `190/190`.

## Feature Status

TACD-001 is complete and archived. TACD-002 is ready to scaffold from the
archived spike report and roadmap handoffs.

## Constitution Compliance

PASS. Cleanup is post-merge, provenance-backed, history-preserving, and gated by
recorded recovery commands. TACD-001 remains report-only; behavior changes stay
with TACD-002, TACD-003, and TACD-004.

## Cleanup Decision

- cleanupApplied: true
- cleanupCommand: `git rm -r specs/tacd-001-platform-mechanics-spike`
- blockedBy: None

## Defaults Applied

- `.specify/feature.json` was absent and not recreated.
- Historical process evidence under `docs/ai/specs/.process/` was retained.
- The merged TACD-001 active spec path contained specification, planning,
  checklist, marker, checkpoint, and MOC evidence; this archive records recovery
  commands before removing that active source folder.

## Scoping

The cleanup removes only completed TACD-001 process/spec evidence from active
`specs/**`. The canonical spike report, PRD, technical roadmap, roadmap MOC,
workflow file, and design concept remain in `docs/**`.
