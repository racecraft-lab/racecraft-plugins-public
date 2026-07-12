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

No entry below is a runner invocation. Both operations are registered but have
no authoritative request.

| Surface | Operation | Promotion Status | Authoritative Request | Guidance |
|---------|-----------|------------------|-----------------------|----------|
| Claude upgrade | `migrate-structure` | deferred | none | report capability gap; leave repository structure unchanged |
| Codex upgrade | `migrate-structure` | deferred | none | report capability gap; leave repository structure unchanged |
| Claude scaffold/autopilot | `relocate-process-artifacts` | deferred | none | report eligible candidate and gap; leave PROCESS artifacts unchanged |
| Codex scaffold/autopilot | `relocate-process-artifacts` | deferred | none | report eligible candidate and gap; leave PROCESS artifacts unchanged |

## Tier-2 Suggestion Matrix

| Case | Action | Reason |
|------|--------|--------|
| thawed eligible legacy spec with PROCESS files | report deferred candidate; no command | thawed_relocatable_process |
| spec named by `.specify/feature.json` | suppress suggestion | frozen/in-flight |
| `SPEC-MOC.md` already carries `structureVersion: 1` | suppress suggestion | already-current |
| PROCESS artifacts already under `.process/` | suppress suggestion | already-normalized |
| no root PROCESS allow-list or matching docs-side scaffold artifact | suppress suggestion | no-candidate |
| first dash segment all-alpha and not `prsg` or `spec` | suppress suggestion | non_speckit_namespace |
| date-first legacy namespace | suppress suggestion | date_named_legacy_namespace |

## No Auto-Run Guard

| Surface | Forbidden |
|---------|-----------|
| scaffold | must not invoke retired `relocate-process-artifacts.sh`, the deferred operation, or an invented replacement |
| autopilot | must not invoke retired `relocate-process-artifacts.sh`, the deferred operation, or an invented replacement |
