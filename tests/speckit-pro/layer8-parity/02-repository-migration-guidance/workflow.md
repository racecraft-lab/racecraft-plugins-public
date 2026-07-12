# SPEC-PARITY-02 Workflow - PRSG-011 Migration Guidance

## Overview

Synthetic workflow used by Layer 8 parity fixture 02. The fixture records the
operator-facing guidance that must stay equivalent across Claude Code and Codex
surfaces.

| Field | Value |
|-------|-------|
| Spec Directory | specs/parity-02-repository-migration-guidance |
| Branch | parity-02-repository-migration-guidance |
| Status | Static guidance parity input |

## Workflow Overview

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Specify | Complete | synthetic fixture |
| Phase 2: Clarify | Complete | no clarifications |
| Phase 3: Plan | Complete | static guidance only |
| Phase 4: Checklist | Complete | no gaps |
| Phase 5: Tasks | Complete | no implementation tasks |
| Phase 6: Analyze | Complete | no findings |
| Phase 7: Implement | Complete | no code changes |

## Legacy Input Scenario

The synthetic legacy repository contains old operator notes that name the
retired paths `speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh`
and `speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh`.
These strings are fixture input and historical provenance only. Neither path
exists as a current command, and neither may be recommended or invoked.

## Migration Guidance Contract

Every entry below means invoke `[resolved_python, "-m", "speckit_pro_runner"]`
with one JSON request on stdin. `helper_id` and `operation` use the same value;
the row supplies the request `mode` and bounded `inputs`.

| Surface | Dry Run | Apply | Guarantee |
|---------|---------|-------|-----------|
| Claude upgrade | `helper_id=migrate-structure; mode=dry_run; inputs.repo_root=.` | `helper_id=migrate-structure; mode=apply; inputs.repo_root=.` | repository migration only; no Tier-2 auto-run |
| Codex upgrade | `helper_id=migrate-structure; mode=dry_run; inputs.repo_root=.` | `helper_id=migrate-structure; mode=apply; inputs.repo_root=.` | repository migration only; no Tier-2 auto-run |
| Claude scaffold/autopilot | `helper_id=relocate-process-artifacts; mode=dry_run; inputs.spec=specs/prsg-011-legacy; inputs.repo_root=.` | `helper_id=relocate-process-artifacts; mode=apply; inputs.spec=specs/prsg-011-legacy; inputs.repo_root=.` | static suggestion only; never auto-runs relocation |
| Codex scaffold/autopilot | `helper_id=relocate-process-artifacts; mode=dry_run; inputs.spec=specs/prsg-011-legacy; inputs.repo_root=.` | `helper_id=relocate-process-artifacts; mode=apply; inputs.spec=specs/prsg-011-legacy; inputs.repo_root=.` | static suggestion only; never auto-runs relocation |

## Tier-2 Suggestion Matrix

| Case | Action | Reason |
|------|--------|--------|
| thawed eligible legacy spec with PROCESS files | suggest dry-run and clean-tree apply follow-up | thawed_relocatable_process |
| spec named by `.specify/feature.json` | suppress suggestion | frozen/in-flight |
| `SPEC-MOC.md` already carries `structureVersion: 1` | suppress suggestion | already-current |
| PROCESS artifacts already under `.process/` | suppress suggestion | already-normalized |
| no root PROCESS allow-list or matching docs-side scaffold artifact | suppress suggestion | no-candidate |
| first dash segment all-alpha and not `prsg` or `spec` | suppress suggestion | non_speckit_namespace |
| date-first legacy namespace | suppress suggestion | date_named_legacy_namespace |

## No Auto-Run Guard

| Surface | Forbidden |
|---------|-----------|
| scaffold | must not invoke retired `relocate-process-artifacts.sh` or auto-run helper mode `dry_run` |
| scaffold | must not invoke retired `relocate-process-artifacts.sh` or auto-run helper mode `apply` |
| autopilot | must not invoke retired `relocate-process-artifacts.sh` or auto-run helper mode `dry_run` |
| autopilot | must not invoke retired `relocate-process-artifacts.sh` or auto-run helper mode `apply` |
