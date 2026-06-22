# Archival Report: TACD-004 Post-Merge Hygiene

## Mode

- archiveMode: single-feature
- dryRun: false
- applyCleanupRequested: true
- dryRunProvenanceOnly: false
- safeToApplyCleanup: true

## Sweep Summary

| Spec | Eligibility | Cleanup Mode | Reason |
|------|-------------|--------------|--------|
| `specs/tacd-004-verification-coverage` | merged | cleanup applied | TACD-004 shipped through merged PR #240. The durable behavior now lives in the payload-build fix, the deterministic verification guards, rewritten evals, regenerated payloads, and process records; residual tracked content under `specs/**` is recoverable workflow/spec evidence only. |

## Cleanup Preconditions

- Requested mode: `--apply-cleanup`
- Installed extension: `archive` v1.1.0 from `.specify/extensions/archive/extension.yml`
- Pinned source: `racecraft-lab/spec-kit-archive` @ `v1.1.0` (commit `08ee0e919a72ccb254758a2b6f51d58196490ea7`)
- Cleanup branch: `tacd-004-archive-cleanup`, based on `origin/main`
- Cleanup PR: https://github.com/racecraft-lab/racecraft-plugins-public/pull/242
- Worktree state before archival edits: clean
- `.specify/feature.json`: absent (not created)
- Current target exclusion: none; TACD-004 was archived after PR #240 merged.
- Extension hooks: no `before_archive` or `after_archive` hooks are configured in `.specify/extensions.yml`.

## Provenance

| PR | Title | Merged at | Merge commit | Scope |
|----|-------|-----------|--------------|-------|
| #240 | `fix(speckit-pro): restore empty Claude skill payloads and add vendor-neutral checks` | 2026-06-20T21:36:55Z | `b95d721f107dd1a17cee88671dc48da791e8e54c` | Claude payload-build `strip_codex_guard` fix, regenerated `dist/**`, body-completeness guard, named-tool Layer 5 guard + named-MCP removal, Layer 1 pointer-coverage and target-resolution guards, and vendor-neutral eval rewrites with behavior-observable scenarios |

- Source spec path:
  - `specs/tacd-004-verification-coverage`
- Source workflow:
  - `docs/ai/specs/.process/TACD-004-workflow.md`
- Design concept:
  - `docs/ai/specs/.process/TACD-004-design-concept.md`
- Canonical shipped artifacts:
  - `scripts/build-plugin-payloads.sh` (`strip_codex_guard` section-boundary fix)
  - `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh` (named-tool guard; named-MCP assertions removed)
  - `tests/speckit-pro/layer1-structural/validate-capability-pointer.sh`
  - `tests/speckit-pro/layer1-structural/validate-capability-resolution.sh`
  - `tests/speckit-pro/layer1-structural/validate-payload-completeness.sh`
  - `tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json`
  - `tests/speckit-pro/layer3-functional/evals/speckit-coach-evals.json`
  - `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json`
  - `tests/speckit-pro/layer3-functional/codex-evals/speckit-coach-evals.json`
  - `dist/claude/speckit-pro/`
  - `dist/codex/speckit-pro/`
- CI evidence:
  - PR #240 merged with required checks green: detect, validate-pr-title, test (speckit-pro), and validate-plugins.
- Screenshot retention: N/A; TACD-004 changed a build script, deterministic shell/JSON test surfaces, and generated payloads, not visual UI.
- Expiration risk: Low for committed artifacts; GitHub Actions logs may expire according to GitHub retention policy.

## Feature Summary

TACD-004 is the final spec in the Tool-Agnostic Capability Discovery roadmap. It
locks the vendor-neutral contract established by TACD-001/002/003 with
deterministic checks plus functional eval coverage, and repairs a Claude
payload-build defect in the same slice.

The named-tool guard in Layer 5 now fails when active Claude/Codex agent guidance
reintroduces a hardcoded named optional-tool preference outside the
TACD-001 category allowlist, and the previously-required named MCP assertions
(`mcp__tavily-mcp__*`, `mcp__context7__*`, `mcp__RepoPrompt__*`) were removed
from the scoping contract entirely. Two new Layer 1 validators prove every
capability-dependent agent points to the shared `capability-discovery.md`
directive and that the pointer resolves from the installed `dist/claude/**` and
`dist/codex/**` payload layouts. All four functional eval files were rewritten to
assert both the absence of a preferred named set and an affirmative
capability-first answer, with behavior-observable scenarios validated against
committed fixtures (no live run gates merge).

Separately, `strip_codex_guard` in `scripts/build-plugin-payloads.sh` was
truncating the Claude `SKILL.md` body for every skill whose guard-block
terminator phrase wrapped across two source lines, so 8 of 10 Claude skills
installed with empty bodies. The fix replaces the magic-terminator scan with a
section-boundary scan (strip from `## Codex Skill-Selection Guard` to the next
heading or EOF), `dist/` was rebuilt so all skill bodies are restored, and a
deterministic body-completeness guard fails if any `dist/claude` `SKILL.md` is
truncated relative to its source minus the guard section.

## Recovery Commands

```text
git show b95d721f107dd1a17cee88671dc48da791e8e54c:specs/tacd-004-verification-coverage/spec.md
git show b95d721f107dd1a17cee88671dc48da791e8e54c:specs/tacd-004-verification-coverage/plan.md
git show b95d721f107dd1a17cee88671dc48da791e8e54c:specs/tacd-004-verification-coverage/tasks.md
git show b95d721f107dd1a17cee88671dc48da791e8e54c:specs/tacd-004-verification-coverage/SPEC-MOC.md
git show b95d721f107dd1a17cee88671dc48da791e8e54c:specs/tacd-004-verification-coverage/research.md
git show b95d721f107dd1a17cee88671dc48da791e8e54c:specs/tacd-004-verification-coverage/quickstart.md
git show b95d721f107dd1a17cee88671dc48da791e8e54c:specs/tacd-004-verification-coverage/checklists/requirements.md
git show b95d721f107dd1a17cee88671dc48da791e8e54c:specs/tacd-004-verification-coverage/checklists/integration.md
git show b95d721f107dd1a17cee88671dc48da791e8e54c:specs/tacd-004-verification-coverage/checklists/reliability.md
git show b95d721f107dd1a17cee88671dc48da791e8e54c:specs/tacd-004-verification-coverage/checklists/maintainability.md
git show b95d721f107dd1a17cee88671dc48da791e8e54c:specs/tacd-004-verification-coverage/.process/uat-runbook.md
git show b95d721f107dd1a17cee88671dc48da791e8e54c:docs/ai/specs/.process/TACD-004-workflow.md
git show b95d721f107dd1a17cee88671dc48da791e8e54c:docs/ai/specs/.process/TACD-004-design-concept.md
git checkout b95d721f107dd1a17cee88671dc48da791e8e54c -- specs/tacd-004-verification-coverage
```

## Changed Files

| File | Change Summary |
|------|----------------|
| `.specify/memory/spec.md` | Appended distilled TACD-004 feature record |
| `.specify/memory/plan.md` | Appended TACD-004 archive hygiene plan record |
| `.specify/memory/changelog.md` | Appended TACD-004 provenance and recovery commands |
| `.specify/memory/archive-reports/2026-06-22-tacd-004-post-merge-hygiene.md` | Recorded archive and cleanup evidence |
| `AGENTS.md` | Added TACD-004 archive cleanup notes |
| `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md` | Marked TACD-004 complete and archived; roadmap feature-complete |
| `docs/ai/specs/tool-agnostic-capability-discovery-roadmap-MOC.md` | Replaced active TACD-004 spec link with archive/report guidance; refreshed generated index |
| `docs/ai/specs/interactive-documentation-roadmap-MOC.md` | Refreshed generated spec index output after active spec cleanup |
| `docs/ai/specs/.process/autopilot-state.json` | Replaced DOC-010 archive state with completed TACD-004 archive state |
| `specs/tacd-004-verification-coverage` | Removed residual active spec evidence |

## Post-Cleanup Verification

- PASS: `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- PASS: `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh .`
- PASS: `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check .`
- PASS: `find specs -mindepth 1 -maxdepth 4 -print` returned only `specs/.gitkeep`.
- PASS: stale active spec path scan found only intentional references — archive report, project memory, recovery commands, the `autopilot-state.json` archive record, and preserved `.process/` workflow evidence. The previously-active `CLAUDE.md` "Current SpecKit plan" pointer to the removed spec was updated to a no-active-plan note in this cleanup PR.
- PASS: `git diff --check`
- PASS: `bash tests/speckit-pro/run-all.sh`

## Feature Status

TACD-004 is complete and archived. The Tool-Agnostic Capability Discovery
roadmap is feature-complete: all four specs (TACD-001 through TACD-004) have
shipped and been archived.

## Constitution Compliance

PASS. Cleanup is post-merge, provenance-backed, history-preserving, and gated by
recorded recovery commands. TACD-004 behavior changes remain in committed
source/generator/test artifacts and regenerated payloads.

## Cleanup Decision

- cleanupApplied: true
- cleanupCommand: `git rm -r specs/tacd-004-verification-coverage`
- blockedBy: None

## Defaults Applied

- `.specify/feature.json` was absent and not recreated.
- Historical process evidence under `docs/ai/specs/.process/` was retained.
- The merged TACD-004 active spec path contained specification, planning,
  checklist, MOC, UAT runbook, and task evidence; this archive records recovery
  commands before removing that active source folder.

## Scoping

The cleanup removes only completed TACD-004 process/spec evidence from active
`specs/**`. The payload-build fix, deterministic verification guards, rewritten
evals, regenerated payloads, workflow file, design concept, roadmap, and archive
report remain in durable repository paths.
