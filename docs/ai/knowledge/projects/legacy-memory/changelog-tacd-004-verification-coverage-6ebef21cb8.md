---
type: "speckit-legacy-memory-record"
title: "TACD-004 Verification Coverage"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-6ebef21cb853d3a2"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# TACD-004 Verification Coverage

### Provenance

| PR | Title | Merged at | Merge commit |
|----|-------|-----------|--------------|
| #240 | `fix(speckit-pro): restore empty Claude skill payloads and add vendor-neutral checks` | 2026-06-20T21:36:55Z | `b95d721f107dd1a17cee88671dc48da791e8e54c` |

### Summary

TACD-004 locked the vendor-neutral optional-tool contract with a Layer 5
named-tool guard (and full removal of the named MCP assertions), Layer 1
pointer-coverage and target-resolution guards against `dist/**`, and rewritten
Claude/Codex functional evals with behavior-observable scenarios. It also fixed
the `strip_codex_guard` payload-build defect and added a body-completeness
guard, restoring all 8 truncated Claude skill bodies.

### Canonical Artifacts

- `scripts/build-plugin-payloads.sh`
- `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh`
- `tests/speckit-pro/layer1-structural/validate-capability-pointer.sh`
- `tests/speckit-pro/layer1-structural/validate-capability-resolution.sh`
- `tests/speckit-pro/layer1-structural/validate-payload-completeness.sh`
- `tests/speckit-pro/layer3-functional/evals/` and `codex-evals/` (autopilot + coach)
- `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`

### Recovery Commands

```text
git show b95d721f107dd1a17cee88671dc48da791e8e54c:specs/tacd-004-verification-coverage/spec.md
git show b95d721f107dd1a17cee88671dc48da791e8e54c:specs/tacd-004-verification-coverage/plan.md
git show b95d721f107dd1a17cee88671dc48da791e8e54c:specs/tacd-004-verification-coverage/tasks.md
git checkout b95d721f107dd1a17cee88671dc48da791e8e54c -- specs/tacd-004-verification-coverage
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-06-22-tacd-004-post-merge-hygiene.md`.
