---
type: "speckit-legacy-memory-record"
title: "XPLAT-009 Plugin Source and Payload Bash Eradication"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-52d0207ff99800bc"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-009 Plugin Source and Payload Bash Eradication

### Provenance

| Spec | PR | Title | Merged at | Merge commit |
|------|----|-------|-----------|--------------|
| XPLAT-009 | #295 | `docs(xplat): plan Bash eradication backstop` | 2026-07-07T14:40:51Z | `bb744db61fe569514c5b856bc4b20cbf478fd8d0` |
| XPLAT-009 | #297 | `feat(xplat): eradicate plugin Bash runtime surface` | 2026-07-08T20:05:01Z | `7bc6be1a9faaa3113f8db903188ddb49a445e7ce` |
| XPLAT-009 | #299 | `fix(runner): resolve python interpreter and home directory on windows` | 2026-07-08T22:44:29Z | `fa7cd5671a40350e8a3feb9a13ebc3900591eef1` |

### Summary

XPLAT-009 removed the remaining plugin-source Bash substrate while preserving
the XPLAT-008 installed-runtime contract of direct Python 3.11+
`speckit_pro_runner` invocation. The merged implementation ported active
plugin-source script behavior to Python runner/helper/gate operations, deleted
the remaining live `.sh` files under `speckit-pro/`, replaced active Bash
instructions in skills and agent guidance, rebuilt generated Claude and Codex
payloads from source, and proved source, generated payloads, and a bounded
installed-cache artifact pass one Python-backed zero-Bash guard with a
reviewable historical allowlist. It shipped in speckit-pro 2.18.0; PR #299
followed up with a Windows interpreter/home-directory resolution fix. Repo-wide
Bash confinement outside the plugin package was completed by XPLAT-010.

### Canonical Artifacts

- `speckit-pro/speckit_pro_runner/gates/active_path_guard.py`
- `speckit-pro/speckit_pro_runner/gates/registry.py`
- `speckit-pro/speckit_pro_runner/gates/release.py`
- `speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `speckit-pro/speckit_pro_runner/helpers/registry.py`
- `dist/claude/speckit-pro/`
- `dist/codex/speckit-pro/`
- `scripts/refresh-release-artifacts.py`
- `docs/ai/specs/.process/XPLAT-009-workflow.md`
- `docs/ai/specs/.process/XPLAT-009-design-concept.md`
- `docs/ai/specs/.process/XPLAT-009-source-inventory.md`
- `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`
- `docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json`
- `docs/ai/specs/.process/XPLAT-009-zero-bash-guard-result.json`
- `docs/ai/specs/.process/XPLAT-009-release-readiness-result.json`
- `docs/ai/specs/.process/XPLAT-009-retrospective.md`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/contracts/`

### Recovery Commands

```text
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/spec.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/plan.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/tasks.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/research.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/data-model.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/quickstart.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/SPEC-MOC.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/contracts/historical-allowlist-entry.schema.json
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/contracts/installed-cache-proof.schema.json
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/contracts/zero-bash-guard-request.schema.json
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/contracts/zero-bash-guard-result.schema.json
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/.process/uat-runbook.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/.process/final-reviewability/gate-state.json
git checkout 7bc6be1a9faaa3113f8db903188ddb49a445e7ce -- specs/xplat-009-plugin-source-and-payload-bash-eradication
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-07-08-xplat-009-post-merge-hygiene.md`.

---
