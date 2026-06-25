# Cross-Platform Plugin Runtime Implementation Roadmap

**Replace Bash-backed installed plugin workflows with a truly cross-platform
runtime path across Claude Code and Codex.**

This document defines the **SPEC catalog** for the cross-platform plugin runtime
release blocker. Each SPEC is prepared for implementation with
`$speckit-scaffold-spec XPLAT-###`, which reads this roadmap as its input.

**Source PRD:** [../../prd-cross-platform-plugin-runtime.md](../../prd-cross-platform-plugin-runtime.md)
**Roadmap MOC:** [cross-platform-plugin-runtime-roadmap-MOC.md](cross-platform-plugin-runtime-roadmap-MOC.md)
**Spec ID prefix:** `XPLAT-###`
**Status:** Pending. Added 2026-06-24 after native-Windows install analysis found
that the plugin can install but core Claude/Codex workflows break when they hit
Bash-backed helper execution.

---

## Roadmap Overview

The release-blocker work is decomposed into **5 specifications** across **5
dependency tiers**:

| Tier | Specs | Purpose | Parallelization |
|---|---|---|---|
| 1 | XPLAT-001 | Inventory active Bash dependencies and select the runtime contract | Sequential |
| 2 | XPLAT-002 | Build the cross-platform runner foundation and parity harness | Sequential after runtime decision |
| 3 | XPLAT-003 | Port read-only/advisory helpers with fixture parity | Sequential after runner foundation |
| 4 | XPLAT-004 | Port mutation, install, and PR-emission helpers | Can overlap late XPLAT-003 only after shared runner APIs are stable |
| 5 | XPLAT-005 | Cut over Claude/Codex surfaces, rebuild payloads, and prove native Windows release readiness | Sequential release gate |

**Execution Order:** XPLAT-001 -> XPLAT-002 -> XPLAT-003 -> XPLAT-004 -> XPLAT-005

**Dependency Constraints:**

- XPLAT-002 requires XPLAT-001 because the runner must implement one selected
  runtime contract, not re-open the language/runtime decision.
- XPLAT-003 requires XPLAT-002 because parity tests need the final runner command
  shape and shared JSON/path library.
- XPLAT-004 requires XPLAT-002 and should reuse XPLAT-003 test patterns, but can
  start once the runner's mutation-safe file APIs are stable.
- XPLAT-005 requires XPLAT-003 and XPLAT-004 because no active Claude/Codex
  surface should switch until every plugin-runtime helper has a replacement.

## Reviewability Contract

Every implementation spec must fit a human review budget before setup and again
before PR creation.

- Warn above 400 reviewable production LOC, 6 production files, or 15 total
  files. Touching more than one primary surface is a warning unless the spec
  records why a split would be less safe.
- Block above 800 reviewable production LOC, 8 production files, or 25 total
  files, unless the roadmap/spec records a typed exception.
- Primary surfaces are schema/migration, API, UI, scheduler/runtime,
  harness/adapter, seed/config, and docs/process.
- PR descriptions are review packets. They must include what changed, why,
  non-goals, review order, scope budget, traceability, verification evidence,
  known gaps, and rollback/flag notes.

## Non-Negotiable Product Constraint

After XPLAT-005, installed Claude and Codex plugin workflows MUST NOT require
Bash, Git Bash, WSL, PowerShell, or `jq` as the implementation substrate on
native Windows, macOS, or Linux. Shells may still exist in a user's environment,
but SpecKit Pro cannot depend on them for installed plugin runtime behavior.

Repository-only maintainer scripts and GitHub Actions are outside this lane
unless an active installed plugin skill, agent, hook, or generated payload
invokes them.

---

## Dependency Graph

```text
XPLAT-001 Runtime Inventory and Architecture Contract
    |
    v
XPLAT-002 Cross-Platform Runner Foundation
    |
    v
XPLAT-003 Read-Only Helper Port
    |
    v
XPLAT-004 Mutation, Install, and PR-Emission Helper Port
    |
    v
XPLAT-005 Claude/Codex Cutover and Native Windows Release Gate
    |
    v
PUBLIC RELEASE UNBLOCKED
```

---

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|---|---|---|---|---|
| XPLAT-001 | Runtime Inventory and Architecture Contract | Pending | — | Scaffold first; public release remains blocked until this lane completes |
| XPLAT-002 | Cross-Platform Runner Foundation | Pending | — | Blocked by XPLAT-001 runtime decision |
| XPLAT-003 | Read-Only Helper Port | Pending | — | Blocked by XPLAT-002 runner foundation |
| XPLAT-004 | Mutation, Install, and PR-Emission Helper Port | Pending | — | Blocked by XPLAT-002; should reuse XPLAT-003 parity harness |
| XPLAT-005 | Claude/Codex Cutover and Native Windows Release Gate | Pending | — | Blocked by XPLAT-003 and XPLAT-004 |

**Status Legend:** Pending | In Progress | Complete | Blocked

---

## Specification Sections

### XPLAT-001: Runtime Inventory and Architecture Contract

**Priority:** P1 | **Depends On:** None | **Enables:** XPLAT-002, XPLAT-003, XPLAT-004, XPLAT-005

**Status:** Pending. This is the first spec to scaffold.

**Goal:** Produce a complete active-runtime inventory and select the one
cross-platform implementation contract that all later specs must follow.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 0-120 |
Production files: 0 |
Total files: 2-4 |
Budget result: within budget (architecture/inventory spike)

**Scope:**

- Inventory all active Bash, `.sh`, `jq`, shell-quoting, Unix-path, `chmod`, and
  line-ending assumptions reachable from installed Claude and Codex plugin
  workflows.
- Classify references as active runtime, generated payload, public docs,
  repository-only maintainer tooling, tests/fixtures, or historical/archive.
- Select one canonical implementation strategy for the plugin runtime. Candidate
  strategies include JavaScript/TypeScript, Python, or small per-platform
  binaries; Bash and PowerShell may be compatibility adapters only, not the
  primary implementation.
- Define the command contract: entrypoint name, argument parsing, JSON stdin/stdout
  envelopes, exit-code mapping, stderr diagnostics, path normalization, subprocess
  execution rules, and prerequisite reporting.
- Define the enforcement allowlist that XPLAT-005 will use to prevent active
  Bash runtime dependencies from returning.

**Out of Scope:**

- Porting helpers.
- Editing active Claude/Codex skill invocations.
- Rebuilding generated payloads.
- Making public docs claim Windows support before XPLAT-005 passes.

**Key Files To Audit:**

- `speckit-pro/skills/**`
- `speckit-pro/codex-skills/**`
- `speckit-pro/agents/**`
- `speckit-pro/codex-agents/**`
- `speckit-pro/hooks/**`
- `speckit-pro/codex-hooks.json`
- `speckit-pro/scripts/**`
- `dist/claude/speckit-pro/**`
- `dist/codex/speckit-pro/**`
- `docs-site/src/content/docs/**`
- `speckit-pro/README.md`

**Done When:**

- A maintainer can point to the runtime contract and know exactly what XPLAT-002
  must build.
- Every active Bash dependency has an owner spec: XPLAT-003, XPLAT-004, or
  XPLAT-005.

---

### XPLAT-002: Cross-Platform Runner Foundation

**Priority:** P1 | **Depends On:** XPLAT-001 | **Enables:** XPLAT-003, XPLAT-004, XPLAT-005

**Status:** Pending.

**Goal:** Build the shared runner, support library, and parity harness that make
future helper ports consistent and testable.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 250-400 |
Production files: 3-6 |
Total files: 8-14 |
Budget result: within budget if the runner stays minimal; split if helper logic
starts landing here.

**Scope:**

- Add the selected runtime's source layout under `speckit-pro/` with one stable
  plugin entrypoint for helper execution.
- Implement shared modules for path handling, JSON envelope construction,
  process execution without a shell, filesystem reads/writes, and platform
  detection.
- Implement a preflight/helper-discovery command that returns runtime,
  platform, executable availability, plugin root, and missing prerequisites as
  structured JSON.
- Add a parity harness that can run old Bash helpers and new runner helpers over
  fixtures while Bash still exists.
- Document how Claude and Codex skills will invoke the runner after cutover.

**Out of Scope:**

- Porting existing helper behavior except tiny smoke/preflight helpers needed to
  prove the runner contract.
- Removing Bash helpers.
- Updating public install docs.

**Key Files Likely To Change:**

- `speckit-pro/<selected-runtime-source>/**`
- `speckit-pro/.claude-plugin/plugin.json`
- `speckit-pro/.codex-plugin/plugin.json`
- `tests/speckit-pro/**`
- `speckit-pro/README.md` only if needed for maintainer-facing development notes

**Done When:**

- The runner executes on native Windows, macOS, and Linux.
- The parity harness can compare old/new helper output deterministically.
- No active skill has been switched yet; this spec only creates the safe runway.

---

### XPLAT-003: Read-Only Helper Port

**Priority:** P1 | **Depends On:** XPLAT-002 | **Enables:** XPLAT-005 and reduces XPLAT-004 risk

**Status:** Pending.

**Goal:** Port all read-only and advisory plugin helpers to the new runner while
preserving current JSON and exit semantics.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 400-800 |
Production files: 6-8 |
Total files: 12-25 |
Budget result: likely warn; split into XPLAT-003a/003b if the XPLAT-001
inventory shows this cannot land reviewably.

**Scope:**

- Port prerequisite, detection, counting, validation, reviewability, topology,
  routing, layer-planning, and spec-index generation helpers that do not mutate
  user state.
- Preserve stdout JSON schemas, stderr diagnostics, and documented exit-code
  behavior.
- Replace ad hoc shell parsing, `jq`, `grep`, `sed`, shell arrays, and process
  substitution with structured runtime APIs.
- Add fixture parity for success, missing input, malformed input, and
  platform-specific path cases.
- Keep the Bash helpers as temporary reference implementations until XPLAT-005.

**Out of Scope:**

- Helpers that write PR packets, emit split PR state, install agents, relocate
  artifacts, or mutate repository/user-local state.
- Updating Claude/Codex active invocations.

**Likely Helper Set:**

- `check-prerequisites`
- `detect-commands`
- `detect-presets`
- `count-markers`
- `validate-gate`
- `resolve-confidence-mode`
- `confidence-gate`
- `reviewability-gate`
- `estimate-reviewable-loc`
- `atomicity-route`
- `plan-layers`
- `o5-topology`
- `generate-spec-index`
- `validate-pr-workflow-contract`
- `validate-pr-packet` if XPLAT-001 classifies it as read-only validation

**Done When:**

- All read-only helpers have runner equivalents with fixture parity.
- Native Windows fixture runs pass without Bash or `jq`.

---

### XPLAT-004: Mutation, Install, and PR-Emission Helper Port

**Priority:** P1 | **Depends On:** XPLAT-002, XPLAT-003 | **Enables:** XPLAT-005

**Status:** Pending.

**Goal:** Port the state-mutating helpers after the runner and read-only parity
patterns are stable.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 400-800 |
Production files: 6-8 |
Total files: 12-25 |
Budget result: likely warn; split into install/migration and PR-emission slices
if XPLAT-001 inventory shows the combined scope is too large.

**Scope:**

- Port helpers that write files, update state, install Codex agents, manage the
  curated set, migrate or relocate process artifacts, generate PR bodies, emit
  split-PR state, or perform restack planning/apply operations.
- Preserve atomic write and dry-run/apply semantics where the Bash helper
  currently promises them.
- Preserve PR packet, workflow-contract, split-PR, restack, install, and
  relocation JSON schemas.
- Add parity fixtures for success, no-op, dry-run, invalid input,
  missing-prerequisite, dirty-worktree, and partial-failure cases.
- Keep live network or GitHub mutation behind the same approval and dry-run
  boundaries as today.

**Out of Scope:**

- Active skill cutover.
- Public release docs.
- Replacing repository-only release scripts unless they are invoked by installed
  plugin runtime behavior.

**Likely Helper Set:**

- `generate-pr-body`
- `generate-uat-skeleton`
- `final-reviewability-backstop`
- `multi-pr-emission`
- `restack`
- `detect-stack-manager` if it remains mutation-adjacent
- `migrate-structure`
- `relocate-process-artifacts`
- `install-curated-set`
- `install-codex-agents`
- coach fixup/preset helpers that write files

**Done When:**

- Every mutation-capable installed-runtime helper has a runner equivalent.
- Fixture parity covers destructive and dry-run paths before active cutover.

---

### XPLAT-005: Claude/Codex Cutover and Native Windows Release Gate

**Priority:** P1 | **Depends On:** XPLAT-003, XPLAT-004 | **Enables:** Public release readiness

**Status:** Pending.

**Goal:** Switch active Claude and Codex plugin runtime surfaces to the
cross-platform runner and prove public-release readiness with native Windows UAT.

**Reviewability Budget:** Primary surfaces: docs/process + seed/config |
Projected reviewable LOC: 250-500 |
Production files: 4-8 |
Total files: 10-25 |
Budget result: likely warn because it touches both runtime guidance and docs;
split only if generated payload rebuilds make the review packet too large.

**Scope:**

- Update active Claude skills, Codex skills, agents, hooks, and install guidance
  to invoke the runner instead of Bash helpers.
- Rebuild Claude and Codex generated payloads from source.
- Remove Bash and `jq` from installed plugin runtime prerequisites.
- Add deterministic guards that fail when active installed-runtime guidance
  reintroduces `bash`, `.sh`, `jq`, shell interpolation, or Unix-only path
  assumptions outside the XPLAT-001 allowlist.
- Add or update docs so Windows users see the supported native path, not a WSL or
  Git Bash workaround.
- Capture manual UAT evidence for Claude and Codex on native Windows, macOS, and
  Linux.

**Out of Scope:**

- Replacing GitHub Actions.
- Replacing repository maintainer scripts not shipped into the installed plugin.
- Changing GitHub Spec Kit's own generated `.specify/scripts/bash/` helpers in
  consumer projects.

**Key Files Likely To Change:**

- `speckit-pro/skills/**`
- `speckit-pro/codex-skills/**`
- `speckit-pro/agents/**`
- `speckit-pro/codex-agents/**`
- `speckit-pro/hooks/**`
- `speckit-pro/codex-hooks.json`
- `speckit-pro/README.md`
- `docs-site/src/content/docs/install/**`
- `docs-site/src/content/docs/troubleshooting.md`
- `docs-site/src/content/docs/first-run.md`
- `dist/claude/speckit-pro/**`
- `dist/codex/speckit-pro/**`
- `tests/speckit-pro/**`

**Done When:**

- Native Windows, macOS, and Linux UAT all pass for installed Claude and Codex
  plugin workflows without Bash, Git Bash, WSL, PowerShell-specific commands, or
  `jq`.
- A release-readiness guard blocks publication if active runtime Bash
  dependencies are reintroduced.

---

## Release Blocker Statement

SpecKit Pro should not be marketed as a public, cross-platform Claude/Codex
plugin until XPLAT-005 is complete. Before then, native Windows support is not a
documentation problem; it is an implementation gap.

## References

- Current active Claude autopilot startup invokes Bash helpers from
  `speckit-pro/skills/speckit-autopilot/SKILL.md`.
- Current active Codex autopilot startup resolves the same shared script
  directory from `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`.
- Current plugin README lists `jq` as a validation-script prerequisite.
- Current helper scripts under `speckit-pro/skills/**/scripts/`,
  `speckit-pro/codex-skills/**/scripts/`, and `speckit-pro/scripts/` are Bash.
