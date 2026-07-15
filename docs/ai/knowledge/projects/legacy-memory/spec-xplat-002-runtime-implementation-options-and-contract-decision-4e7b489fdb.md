---
type: "speckit-legacy-memory-record"
title: "XPLAT-002 Runtime Implementation Options and Contract Decision"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-4e7b489fdbc8bc90"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-002 Runtime Implementation Options and Contract Decision

[Source: specs/xplat-002-runtime-implementation-options-contract-decision]

XPLAT-002 shipped the amended runtime implementation decision and
`speckit-pro-runner` command contract. Python 3.11+ standard-library source is
the selected XPLAT implementation substrate because it aligns with official
Spec Kit / `specify` prerequisites. JavaScript/TypeScript and small
per-platform binaries remain historical rejected evidence only; compiled
binaries are not a fallback, compatibility adapter, or downstream
implementation input. The contract covers JSON stdin/stdout, deterministic
stderr diagnostics, exit-code categories, typed path values, shell-disabled
subprocess execution, and `runtime-info`/preflight behavior for XPLAT-004.

Cleanup note: archived on 2026-06-29 after PR #266 merged at
`fff4d6b5e7f4bf5ca85b2e55225417152b70b45f`. The active
`specs/xplat-002-runtime-implementation-options-contract-decision/` folder was
removed; recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-29-completed-active-specs-post-merge-hygiene.md`.
