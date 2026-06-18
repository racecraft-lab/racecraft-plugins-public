# Archival Report: TACD-002 Post-Merge Hygiene

## Mode

- archiveMode: single-feature
- dryRun: false
- applyCleanupRequested: true
- dryRunProvenanceOnly: false
- safeToApplyCleanup: true

## Sweep Summary

| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/tacd-002-capability-discovery-directive-and-agent-updates` | merged | cleanup applied | TACD-002 shipped through merged PRs #221-#226. The durable behavior now lives in source guidance, generated payloads, tests, and process records; residual tracked content under `specs/**` is recoverable workflow/spec evidence only. |

## Cleanup Preconditions

- Requested mode: `--apply-cleanup`
- Installed extension: `archive` v1.1.0 from `.specify/extensions/archive/extension.yml`
- Extension command contract: `.specify/extensions/archive/commands/archive.md`
- Execution note: Codex executed the installed archive contract directly through the `speckit-archive-cleanup` plugin skill.
- Cleanup branch: `codex/tacd-002-post-merge-hygiene`, based on updated `origin/main`
- Worktree state before archival edits: clean
- `.specify/feature.json`: absent
- Current target exclusion: none; TACD-002 was archived after PRs #221-#226 merged.
- Extension hooks: no `before_archive` or `after_archive` hooks are configured in `.specify/extensions.yml`.

## Provenance

| PR | Title | Merged at | Merge commit | Tree reference | Scope |
|----|-------|-----------|--------------|----------------|-------|
| #221 | `feat(TACD-002): Add capability discovery foundation` | 2026-06-18T17:19:33Z | `b63dfc95525eb64f9f221d7f2513c9ab9c36b314` | `46e1c2b3f1a7d83b06815c7b34f1dc7531df53cf` | shared directive foundation and source guidance setup |
| #222 | `feat(TACD-002): Update agent capability selection` | 2026-06-18T17:42:02Z | `da9a7c5cd6ba567f1530e396cfc69527948bf7a7` | `8c2005f42f187542de7a20c10707759b436d0777` | Claude and Codex agent capability-first selection |
| #223 | `feat(TACD-002): Document fallback evidence behavior` | 2026-06-18T17:54:57Z | `2060789358cdf4cd946d423238ee2be1f7f90675` | `a93e16d3ae648c5c13a8cc305a7c783d7119321d` | fallback evidence and confidence behavior |
| #224 | `feat(TACD-002): Align Claude and Codex guidance` | 2026-06-18T19:01:30Z | `4203e1011a1d67220e0e82115108759446fa04cf` | `55cb7f67ac1c8aa0e4e127bc65e6f382a8c61194` | Claude/Codex semantic parity and metadata classification |
| #225 | `feat(TACD-002): Refresh generated capability payloads` | 2026-06-18T19:22:08Z | `12ff3667a36906552bb47ee11b7b53239d42f391` | `0e35350187cd7196412a8ab14287a492e1cd1984` | generated Claude and Codex payload refresh |
| #226 | `feat(TACD-002): Emit ordered slice PRs` | 2026-06-18T20:04:52Z | `130abd2b6329e774207c84ab798cfb5b6dab7131` | `0ec46aa6307a8cc8f4f63d729b2a729123c2a62e` | marker-emission hardening and ordered slice PR creation |

- Source spec path:
  - `specs/tacd-002-capability-discovery-directive-and-agent-updates`
- Source workflow:
  - `docs/ai/specs/.process/TACD-002-workflow.md`
- Design concept:
  - `docs/ai/specs/.process/TACD-002-design-concept.md`
- Canonical shipped artifacts:
  - `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`
  - `speckit-pro/agents/*.md`
  - `speckit-pro/codex-agents/*.toml`
  - `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh`
  - `speckit-pro/skills/speckit-autopilot/references/post-implementation.md`
  - `speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md`
  - `tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh`
  - `tests/speckit-pro/layer4-scripts/test-reviewability-marker-guidance.sh`
  - `dist/claude/speckit-pro/`
  - `dist/codex/speckit-pro/`
- CI evidence:
  - PRs #221-#226 merged to `main`; final local implementation evidence recorded `bash tests/speckit-pro/run-all.sh`: `3067/3067` passed before PR creation.
- Screenshot retention: N/A; TACD-002 changed agent/runtime guidance, scripts, payloads, and tests, not visual UI.
- Expiration risk: Low for committed artifacts; GitHub Actions logs may expire according to GitHub retention policy.

## Feature Summary

TACD-002 applies the TACD-001 tool-agnostic capability-discovery decision to
active SpecKit Pro runtime guidance. It adds the shared
`capability-discovery.md` directive, updates six Claude agents and six Codex
agents so they select by capability need, records fallback evidence and
confidence wording, preserves exact named IDs only as metadata or generated
runtime evidence, refreshes generated Claude/Codex payloads from source, and
hardens marker PR emission so branch prefixes, source feature directories,
public titles, and changed-file scope validation no longer block ordered slice
PR creation.

## Recovery Commands

```text
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/spec.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/plan.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/tasks.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/SPEC-MOC.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/research.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/data-model.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/quickstart.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/contracts/capability-discovery-guidance.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/checklists/llm-integration.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/checklists/error-handling.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/checklists/integration.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/.process/uat-runbook.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:docs/ai/specs/.process/TACD-002-workflow.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:docs/ai/specs/.process/TACD-002-design-concept.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:speckit-pro/skills/speckit-autopilot/references/capability-discovery.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh
git checkout 130abd2b6329e774207c84ab798cfb5b6dab7131 -- specs/tacd-002-capability-discovery-directive-and-agent-updates
```

## Changed Files

| File | Change Summary |
|------|----------------|
| `.specify/memory/spec.md` | Appended distilled TACD-002 feature record |
| `.specify/memory/plan.md` | Appended TACD-002 archive hygiene plan record |
| `.specify/memory/changelog.md` | Appended TACD-002 provenance and recovery commands |
| `.specify/memory/archive-reports/2026-06-18-tacd-002-post-merge-hygiene.md` | Recorded archive and cleanup evidence |
| `AGENTS.md` | Added TACD-002 archive cleanup note |
| `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md` | Marked TACD-002 archived and TACD-003 ready to scaffold |
| `docs/ai/specs/tool-agnostic-capability-discovery-roadmap-MOC.md` | Replaced active TACD-002 spec link with archive/report guidance |
| `docs/ai/specs/.process/autopilot-state.json` | Replaced active TACD-002 state with completed archive state |
| `specs/tacd-002-capability-discovery-directive-and-agent-updates` | Removed residual active spec evidence |

## Post-Cleanup Verification

- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
  passed.
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh .`
  regenerated roadmap MOC generated zones after the active TACD-002 spec folder
  was removed.
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`
  passed with all in-scope maps up to date.
- `find specs -mindepth 1 -maxdepth 4 -print` returned only active DOC-008,
  active DOC-009, and `specs/.gitkeep` after cleanup.
- `git diff --check` passed.
- `bash tests/speckit-pro/run-all.sh` passed `3067/3067`.
  - Layer 1 structural: `573/573`.
  - Layer 1 Codex structural: `451/451`.
  - Layer 4 script unit: `1853/1853`.
  - Layer 5 tool scoping: `190/190`.

## Feature Status

TACD-002 is complete and archived. TACD-003 is unblocked and ready to scaffold
from the implemented capability-discovery directive and the updated roadmap
handoffs.

## Constitution Compliance

PASS. Cleanup is post-merge, provenance-backed, history-preserving, and gated by
recorded recovery commands. TACD-002 behavior changes remain in committed
source/generator/test artifacts; TACD-003 prerequisite/user-facing messaging and
TACD-004 enforcement remain separate roadmap specs.

## Cleanup Decision

- cleanupApplied: true
- cleanupCommand: `git rm -r specs/tacd-002-capability-discovery-directive-and-agent-updates`
- blockedBy: None

## Defaults Applied

- `.specify/feature.json` was absent and not recreated.
- Historical process evidence under `docs/ai/specs/.process/` was retained.
- The merged TACD-002 active spec path contained specification, planning,
  checklist, marker-plan, PR-packet, reviewability, and UAT evidence; this
  archive records recovery commands before removing that active source folder.

## Scoping

The cleanup removes only completed TACD-002 process/spec evidence from active
`specs/**`. The shared capability directive, runtime guidance, generated
payloads, tests, workflow file, design concept, roadmap, and archive report
remain in durable repository paths.
