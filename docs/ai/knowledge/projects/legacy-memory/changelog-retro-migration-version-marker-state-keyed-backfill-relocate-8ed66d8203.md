---
type: "speckit-legacy-memory-record"
title: "Retro-migration: version marker + state-keyed backfill/relocate"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-8ed66d820368c6f6"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Retro-migration: version marker + state-keyed backfill/relocate

[Source: specs/prsg-011-retro-migration]

- **Feature**: Retro-migration: version marker + state-keyed backfill/relocate
- **Roadmap ID**: PRSG-011 (PR-size governance roadmap)
- **Branch**: `prsg-011-retro-migration`
- **Spec path**: `specs/prsg-011-retro-migration/`
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/132
- **Merge commit**: `6916ec43d2d4e3972d7e12425a05158f0b48ae3b`
- **Tree reference**: N/A (merge commit recorded above)
- **CI run URL**: https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27210286401
- **Argos build/review URL**: N/A (no visual artifacts)
- **Metadata gates**: validate-plugins=pass; test(speckit-pro)=pass; detect=pass; CodeQL=pass; validate-pr-title=fail on merged title
- **Artifact manifest**: specs/prsg-011-retro-migration/SPEC-MOC.md
- **Task completion**: 34 / 34 tasks complete
- **Archived**: 2026-06-09
- **Status**: Completed
- **Cleanup decision**: `safeToApplyCleanup=false`; source folder retained during this hygiene pass so cleanup can be handled together with the PRSG-007 test dependency.

### Summary of added behavior

Added deterministic migration tooling for existing SpecKit projects:
`migrate-structure.sh` for repo-level marker/backfill, `relocate-process-artifacts.sh`
for explicit Tier-2 PROCESS relocation, generator updates for legacy backfill,
and scaffold/autopilot/upgrade guidance that suggests but never auto-runs
relocation. The implementation mirrors the archive extension's dry-run/apply,
clean-tree, backup, and recovery-command safety pattern.

### Recovery Commands (raw spec artifacts)

```text
git show 6916ec43d2d4e3972d7e12425a05158f0b48ae3b:specs/prsg-011-retro-migration/spec.md
git show 6916ec43d2d4e3972d7e12425a05158f0b48ae3b:specs/prsg-011-retro-migration/plan.md
git show 6916ec43d2d4e3972d7e12425a05158f0b48ae3b:specs/prsg-011-retro-migration/tasks.md
git show 6916ec43d2d4e3972d7e12425a05158f0b48ae3b:specs/prsg-011-retro-migration/contracts/migrate-structure-cli.md
git show 6916ec43d2d4e3972d7e12425a05158f0b48ae3b:specs/prsg-011-retro-migration/contracts/relocate-process-artifacts-cli.md
git show 6916ec43d2d4e3972d7e12425a05158f0b48ae3b:specs/prsg-011-retro-migration/.process/uat-runbook.md
```

To recover the entire directory at the merge commit:

```text
git checkout 6916ec43d2d4e3972d7e12425a05158f0b48ae3b -- specs/prsg-011-retro-migration
```

---
