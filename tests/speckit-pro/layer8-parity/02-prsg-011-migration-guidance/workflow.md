# SPEC-PARITY-02 Workflow - PRSG-011 Migration Guidance

## Overview

Synthetic workflow used by Layer 8 parity fixture 02. The fixture records the
operator-facing guidance that must stay equivalent across Claude Code and Codex
surfaces.

| Field | Value |
|-------|-------|
| Spec Directory | specs/parity-02-prsg-011-migration-guidance |
| Branch | parity-02-prsg-011-migration-guidance |
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

## Migration Guidance Contract

| Surface | Dry Run | Apply | Guarantee |
|---------|---------|-------|-----------|
| Claude upgrade | `speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh --dry-run --repo-root .` | `speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh --apply --repo-root .` | repository migration only; no Tier-2 auto-run |
| Codex upgrade | `speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh --dry-run --repo-root .` | `speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh --apply --repo-root .` | repository migration only; no Tier-2 auto-run |
| Claude scaffold/autopilot | `speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh --dry-run --spec specs/prsg-011-legacy --repo-root .` | `speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh --apply --spec specs/prsg-011-legacy --repo-root .` | suggestion only; never invokes relocation |
| Codex scaffold/autopilot | `speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh --dry-run --spec specs/prsg-011-legacy --repo-root .` | `speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh --apply --spec specs/prsg-011-legacy --repo-root .` | suggestion only; never invokes relocation |

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
| scaffold | must not invoke `relocate-process-artifacts.sh --dry-run` |
| scaffold | must not invoke `relocate-process-artifacts.sh --apply` |
| autopilot | must not invoke `relocate-process-artifacts.sh --dry-run` |
| autopilot | must not invoke `relocate-process-artifacts.sh --apply` |
