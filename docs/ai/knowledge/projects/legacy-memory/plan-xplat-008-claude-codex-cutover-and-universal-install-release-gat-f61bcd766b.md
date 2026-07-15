---
type: "speckit-legacy-memory-record"
title: "XPLAT-008 Claude/Codex Cutover and Universal Install Release Gate"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-f61bcd766b6e9b68"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-008 Claude/Codex Cutover and Universal Install Release Gate

[Source: specs/xplat-008-claude-codex-cutover-universal-install-release-gate]

XPLAT-008 implemented the installed Claude/Codex runtime cutover, generated
payload release checks, public docs claim alignment, UAT matrix validation,
release-readiness aggregation, and bounded install-health repair behavior on
top of the XPLAT-004 runner, XPLAT-005 helper registry, XPLAT-006 mutation and
install helpers, and XPLAT-007 gate substrate.

### Technical Approach

- Route active Claude/Codex installed-runtime surfaces through direct
  `python -m speckit_pro_runner` JSON-envelope invocation instead of shell
  helper execution.
- Keep active no-shell/no-jq guard scope focused on installed-runtime source,
  generated payloads, install guidance, and release gates while allowing
  archive/provenance text, fixture text, minimal CI dispatch glue, and upstream
  Spec Kit generated helpers.
- Rebuild generated Claude and Codex payloads from source and compare them
  against source-derived payload inventories, not against the existing `dist/**`
  tree as source of truth.
- Preserve the release-readiness packet, UAT matrix, and partial Codex/macOS
  installed-cache UAT evidence under `docs/ai/specs/.process/` after active
  spec cleanup.
- Preserve XPLAT-008 contract schemas under
  `tests/speckit-pro/unit/fixtures/installed-plugin-release/contracts/` so
  Layer 4 gates no longer depend on active `specs/**` content.

### Testing Strategy

XPLAT-008 verification uses focused Python standard-library Layer 4 gate tests,
payload completeness runner requests, active-runtime guard requests, UAT matrix
requests, install-health repair requests, release-readiness expected-failure
and ready-fixture requests, docs-site validation, generated payload rebuilds,
runner manifest/checksum validation, SpecKit index checks, JSON validation,
diff hygiene, and the default deterministic suite.

### Cleanup Notes

`specs/xplat-008-claude-codex-cutover-universal-install-release-gate` was
removed from active `specs/**` in the post-merge cleanup after PR #292 merged.
Recovery commands and provenance are recorded in the XPLAT-008 archive report.
The release lane remains held by real operator UAT: do not publish native
Windows/macOS/Linux Claude or Codex support claims until
`docs/ai/specs/.process/XPLAT-008-uat-matrix.md` has six passing rows and the
release-readiness gate is rerun against that evidence.
