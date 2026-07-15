---
type: "speckit-legacy-memory-record"
title: "XPLAT-010 Repository Bash Confinement and CI Dispatch Guard"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-24aaee7305373bc4"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-010 Repository Bash Confinement and CI Dispatch Guard

### Provenance

XPLAT-010 merged as the complete no-gap PR stack #311 through #328 on
2026-07-11. The final merge commit and complete recovery source is
`ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29`; all 18 review branches were
deleted. Exact PR titles, merged-at timestamps, merge commits, and head branches
are recorded in
`.specify/memory/archive-reports/2026-07-11-xplat-010-post-merge-hygiene.md`.

### Summary

XPLAT-010 replaced active repository Bash orchestration, validators, helpers,
hooks, replay/parity/evaluation runners, and release tooling with Python 3.11+
standard-library entrypoints. It made the suite manifest authoritative, added
the repository Bash-confinement gate and fixed release-excluded vendored
`.specify/**` allowlist, restored `estimate-spec-size`, added Linux container
and advisory Windows preflight, and shipped deterministic consumer release-note
validation and Highlights composition.

The final neutral-PATH deterministic suite passed `2512/2512`. T108 completed
with hosted relevant-path, docs-only, failure-propagation, manual-main, and four
PR-trigger canaries. T117 completed when non-strict `main` branch protection
required exactly the three PR checks plus both Linux container sentinels.
Public native-platform claims remain blocked by the XPLAT-008 operator UAT
matrix, not by XPLAT-010.

### Canonical Artifacts

- `tests/speckit-pro/suite-manifest.json`
- `tests/speckit-pro/run-all.py`
- `tests/speckit-pro/run-layer-scripts.py`
- `tests/speckit-pro/unit/`
- `tests/speckit-pro/parity/bash-to-python/`
- `speckit-pro/speckit_pro_runner/gates/active_path_guard.py`
- `speckit-pro/speckit_pro_runner/gates/release.py`
- `scripts/release_note_policy.py`
- `scripts/compose-release-notes.py`
- `.github/workflows/pr-checks.yml`
- `.github/workflows/container-preflight.yml`
- `.github/workflows/release.yml`
- `docs/ai/specs/.process/XPLAT-010-*`

### Recovery Commands

```text
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/spec.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/plan.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/tasks.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/research.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/data-model.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/quickstart.md
git checkout ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29 -- specs/xplat-010-repository-bash-confinement
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-07-11-xplat-010-post-merge-hygiene.md`.
