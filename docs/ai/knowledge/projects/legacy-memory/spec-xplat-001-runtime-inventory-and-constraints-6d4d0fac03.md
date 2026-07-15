---
type: "speckit-legacy-memory-record"
title: "XPLAT-001 Runtime Inventory and Constraints"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-6d4d0fac03d4a099"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-001 Runtime Inventory and Constraints

[Source: specs/xplat-001-runtime-inventory-constraints]

XPLAT-001 shipped a source-traceable runtime inventory and non-scoring runtime
and supply-chain rubrics for the cross-platform plugin runtime lane. The main
reviewable artifact is `docs/ai/research/cross-platform-runtime-inventory.md`.
It represented 21,162 scoped scan hits across shell substrate, script-file
references, JSON query usage, shell quoting/operators, Unix paths, file-mode
changes, and newline policy. It classified active installed-runtime findings,
generated payload references, public-doc claims, tests/fixtures, repository-only
tooling, and historical/archive material without selecting a replacement
runtime or changing installed invocation paths.

Cleanup note: archived on 2026-06-29 after PR #263 merged at
`a7f9ca97548ebe4b50cf84a19828d745471756a0`. The active
`specs/xplat-001-runtime-inventory-constraints/` folder was removed; recovery
commands are recorded in
`.specify/memory/archive-reports/2026-06-29-completed-active-specs-post-merge-hygiene.md`.
