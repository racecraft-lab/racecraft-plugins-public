---
type: "speckit-legacy-memory-record"
title: "XPLAT-008 Claude/Codex Cutover and Universal Install Release Gate"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-5f5dee559373f2c0"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-008 Claude/Codex Cutover and Universal Install Release Gate

### Provenance

| Spec | PR | Title | Merged at | Merge commit |
|------|----|-------|-----------|--------------|
| XPLAT-008 | #289 | `feat(speckit-pro): Update Active Installed-Runtime Surface Cutover` | 2026-07-07T00:54:54Z | `59c18b2dcf79284182f6f5932e61716db0d58090` |
| XPLAT-008 | #290 | `feat(speckit-pro): Update Payload, Release, and Public Docs Gates` | 2026-07-07T01:14:33Z | `1793128875dd0a31e9fafd606eaa55e92123d63e` |
| XPLAT-008 | #291 | `feat(speckit-pro): Update Native UAT, Update, and Safe Repair` | 2026-07-07T01:25:47Z | `66defab977c166bff8726724cdb728b95eec0165` |
| XPLAT-008 | #292 | `fix(release): unblock XPLAT-008 readiness gate` | 2026-07-07T02:00:33Z | `9507fd452a3e344c1912b449f3bb4f2c38437b38` |

### Summary

XPLAT-008 shipped active Claude/Codex installed-runtime cutover to the Python
runner, generated Claude and Codex payload rebuilds, payload completeness and
release-readiness gates, public docs and README claim alignment, UAT matrix
validation, install-health repair controls, partial Codex/macOS installed-cache
UAT evidence, and a deterministic release block for incomplete native operator
UAT.

The implementation is archived, but public native Windows/macOS/Linux support
claims remain blocked until all six operator UAT rows pass in
`docs/ai/specs/.process/XPLAT-008-uat-matrix.md`.

### Canonical Artifacts

- `speckit-pro/speckit_pro_runner/gates/release.py`
- `speckit-pro/speckit_pro_runner/gates/payloads.py`
- `speckit-pro/speckit_pro_runner/gates/active_path_guard.py`
- `speckit-pro/speckit_pro_runner/helpers/install.py`
- `dist/claude/speckit-pro/`
- `dist/codex/speckit-pro/`
- `docs-site/src/content/docs/install/claude-code.md`
- `docs-site/src/content/docs/install/codex.md`
- `docs-site/src/content/docs/security-and-trust.md`
- `docs-site/src/content/docs/troubleshooting.md`
- `docs-site/src/content/docs/update-and-rollback.md`
- `docs/ai/specs/.process/XPLAT-008-workflow.md`
- `docs/ai/specs/.process/XPLAT-008-design-concept.md`
- `docs/ai/specs/.process/XPLAT-008-release-readiness.md`
- `docs/ai/specs/.process/XPLAT-008-uat-matrix.md`
- `docs/ai/specs/.process/XPLAT-008-uat-codex-macos.md`
- `tests/speckit-pro/unit/fixtures/installed-plugin-release/`

### Recovery Commands

```text
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/spec.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/plan.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/tasks.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/research.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/data-model.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/quickstart.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:docs/ai/specs/.process/XPLAT-008-workflow.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:docs/ai/specs/.process/XPLAT-008-design-concept.md
git checkout 9507fd452a3e344c1912b449f3bb4f2c38437b38 -- specs/xplat-008-claude-codex-cutover-universal-install-release-gate
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-07-07-xplat-008-post-merge-hygiene.md`.

---
