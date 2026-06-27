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
Bash-backed helper execution. Refined 2026-06-25 after roadmap audit split the
runtime decision and supply-chain security model out of the first implementation
slice.

---

## Roadmap Overview

The release-blocker work is decomposed into **7 specifications** across **7
dependency tiers**:

| Tier | Specs | Purpose | Parallelization |
|---|---|---|---|
| 1 | XPLAT-001 | Inventory active runtime dependencies and define evaluation constraints | Sequential |
| 2 | XPLAT-002 | Research runtime implementation options and choose the contract | Sequential after inventory |
| 3 | XPLAT-003 | Research and choose the supply-chain security / consumer-trust model | Sequential after runtime decision |
| 4 | XPLAT-004 | Build the cross-platform runner foundation and parity harness | Sequential after runtime and security decisions |
| 5 | XPLAT-005 | Port read-only/advisory helpers with fixture parity | Sequential after runner foundation |
| 6 | XPLAT-006 | Port mutation, install, and PR-emission helpers | Can overlap late XPLAT-005 only after shared runner APIs are stable |
| 7 | XPLAT-007 | Cut over Claude/Codex surfaces, rebuild payloads, and prove native Windows release readiness | Sequential release gate |

**Execution Order:** XPLAT-001 -> XPLAT-002 -> XPLAT-003 -> XPLAT-004 -> XPLAT-005 -> XPLAT-006 -> XPLAT-007

**Dependency Constraints:**

- XPLAT-002 requires XPLAT-001 because the runtime decision must be based on the
  actual active installed-runtime surface, not an assumed helper list.
- XPLAT-003 requires XPLAT-002 because the supply-chain model depends on the
  selected runtime, packaging model, and generated artifact categories.
- XPLAT-004 requires XPLAT-002 and XPLAT-003 because the runner must implement
  one selected runtime contract and the first-release security controls.
- XPLAT-005 requires XPLAT-004 because parity tests need the final runner command
  shape and shared JSON/path library.
- XPLAT-006 requires XPLAT-004 and should reuse XPLAT-005 test patterns, but can
  start once the runner's mutation-safe file APIs are stable.
- XPLAT-007 requires XPLAT-005 and XPLAT-006 because no active Claude/Codex
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

## Audit Findings Resolved

This roadmap originally combined inventory, runtime evaluation, and runtime
contract selection into XPLAT-001. That made the first spec too broad and risked
locking a public runtime strategy before enough evidence existed. The corrected
sequence now separates:

- XPLAT-001: inventory and evaluation rubric only.
- XPLAT-002: implementation-option research and runtime contract decision.
- XPLAT-003: supply-chain security and consumer-trust model.

The runner foundation now starts only after both public-contract decisions are
recorded.

## Non-Negotiable Product Constraint

After XPLAT-007, installed Claude and Codex plugin workflows MUST NOT require
Bash, Git Bash, WSL, PowerShell, or `jq` as the implementation substrate on
native Windows, macOS, or Linux. Shells may still exist in a user's environment,
but SpecKit Pro cannot depend on them for installed plugin runtime behavior.

Repository-only maintainer scripts and GitHub Actions are outside this lane
unless an active installed plugin skill, agent, hook, or generated payload
invokes them.

## Consumer Trust Constraint

After XPLAT-007, public docs and release notes MUST accurately state how the
runtime artifacts are built, what dependencies they include, what consumers can
verify locally, and which security guarantees are intentionally not claimed.
Supply-chain guarantees must be implemented before they are marketed.

---

## Dependency Graph

```text
XPLAT-001 Runtime Inventory and Constraints
    |
    v
XPLAT-002 Runtime Implementation Options and Contract Decision
    |
    v
XPLAT-003 Supply-Chain Security and Consumer Trust Model
    |
    v
XPLAT-004 Cross-Platform Runner Foundation
    |
    v
XPLAT-005 Read-Only Helper Port
    |
    v
XPLAT-006 Mutation, Install, and PR-Emission Helper Port
    |
    v
XPLAT-007 Claude/Codex Cutover and Native Windows Release Gate
    |
    v
PUBLIC RELEASE UNBLOCKED
```

---

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|---|---|---|---|---|
| XPLAT-001 | Runtime Inventory and Constraints | Complete | `.process/XPLAT-001-workflow.md` | Inventory report: `docs/ai/research/cross-platform-runtime-inventory.md` |
| XPLAT-002 | Runtime Implementation Options and Contract Decision | In Review (PR #266 pending merge) | `.process/XPLAT-002-workflow.md` | PR #266 selects the Go native runtime model and runner contract; downstream work remains blocked until merge |
| XPLAT-003 | Supply-Chain Security and Consumer Trust Model | Pending | — | Blocked by XPLAT-002 runtime decision; must finish before runner foundation |
| XPLAT-004 | Cross-Platform Runner Foundation | Pending | — | Blocked by XPLAT-002 runtime decision and XPLAT-003 security model |
| XPLAT-005 | Read-Only Helper Port | Pending | — | Blocked by XPLAT-004 runner foundation |
| XPLAT-006 | Mutation, Install, and PR-Emission Helper Port | Pending | — | Blocked by XPLAT-004; should reuse XPLAT-005 parity harness |
| XPLAT-007 | Claude/Codex Cutover and Native Windows Release Gate | Pending | — | Blocked by XPLAT-005 and XPLAT-006 |

**Status Legend:** Pending | In Progress | In Review | Complete | Blocked

---

## Specification Sections

### XPLAT-001: Runtime Inventory and Constraints

**Priority:** P1 | **Depends On:** None | **Enables:** XPLAT-002, XPLAT-003, XPLAT-004, XPLAT-005, XPLAT-006, XPLAT-007

**Status:** Complete. Scaffolded and implemented on 2026-06-25 in branch `codex/xplat-001-runtime-inventory-constraints`; workflow file is `docs/ai/specs/.process/XPLAT-001-workflow.md`; durable report is `docs/ai/research/cross-platform-runtime-inventory.md`.

**Goal:** Produce a complete active-runtime inventory and a decision rubric for
runtime and supply-chain choices. Do not choose or implement the replacement
runtime in this spec.

**Reviewability Budget:** Primary surface: docs/process |
Secondary surface: harness/adapter evidence only if needed |
Projected reviewable LOC: 250 |
Production files: 4 |
Total files: 10 |
Budget result: warning accepted because setup identified two review surfaces,
while XPLAT-001 remains one inventory/rubric spike with no runtime
implementation.

**Scope:**

- Run a whole-repo tracked-text scan for Bash, `.sh`, `jq`, shell-quoting,
  Unix-path, `chmod`, and line-ending assumptions, including generated payloads,
  public docs, tests, fixtures, and historical/archive references.
- Classify references as active runtime, generated payload, public docs,
  repository-only maintainer tooling, tests/fixtures, or historical/archive.
- Require static caller-to-callee invocation-trace evidence before marking any
  finding as a proven active installed-runtime dependency.
- Map every active runtime dependency to an owner category: read-only helper,
  mutation/helper, cutover guidance, repository-only exclusion, or follow-up
  exception.
- Produce a runtime evaluation rubric covering native Windows/macOS/Linux
  behavior, installed-cache invocation, dependency footprint, packaging,
  offline behavior, diagnostics, maintainability, and compatibility adapters.
- Produce a supply-chain evaluation rubric covering dependency policy,
  lockfiles, generated payload integrity, vulnerability scanning, provenance,
  checksums/signatures, SBOMs, and consumer-local verification.

**Out of Scope:**

- Selecting the runtime.
- Selecting the supply-chain security approach.
- Porting helpers.
- Editing active Claude/Codex skill invocations.
- Rebuilding generated payloads.
- Making public docs claim Windows support before XPLAT-007 passes.

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
- Release/versioning files such as `.release-please-manifest.json`,
  `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, and
  plugin manifests.

**Done When:**

- A maintainer can see the full active runtime surface and no longer has to
  infer which Bash references matter.
- XPLAT-002 has a clear runtime evaluation rubric and candidate evidence list.
- XPLAT-003 has a clear security/trust evaluation rubric and artifact list.
- Every active Bash dependency has a provisional owner spec: XPLAT-005,
  XPLAT-006, XPLAT-007, or repository-only exclusion.

**Completion Handoff:**

- Inventory represented 21,162 scan hits across the scoped runtime-assumption
  families: shell substrate, script-file references, JSON query usage, shell
  quoting/operators, Unix paths, file-mode changes, and newline policy.
- Active installed-runtime rows map to XPLAT-005 read-only helper work,
  XPLAT-006 mutation/install/PR-emission helper work, and XPLAT-007 generated
  payload cutover guidance.
- XPLAT-002 should use the non-scoring runtime rubric in the report.
- XPLAT-003 should use the non-scoring supply-chain rubric in the report.
- XPLAT-001 did not port helpers to a replacement runtime, change active
  installed invocation paths, score candidates, or select controls. Post-PR
  review remediation synchronized generated payload copies of the existing
  spec-index helper only.

---

### XPLAT-002: Runtime Implementation Options and Contract Decision

**Priority:** P1 | **Depends On:** XPLAT-001 | **Enables:** XPLAT-004, XPLAT-005, XPLAT-006, XPLAT-007

**Status:** In Review (PR #266 pending merge). Scaffolded on 2026-06-26 in branch `codex/xplat-002-runtime-implementation-options-contract-decision`; workflow file is `docs/ai/specs/.process/XPLAT-002-workflow.md`; design concept is `docs/ai/specs/.process/XPLAT-002-design-concept.md`.

**Goal:** Research and evaluate implementation options, then select the one
runtime contract that all later specs must implement.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 0-120 |
Production files: 0 |
Total files: 2-5 |
Budget result: within budget (decision record and probes)

**Scope:**

- Compare credible implementation strategies including JavaScript/TypeScript,
  Python, and small per-platform binaries.
- Evaluate each candidate against the XPLAT-001 rubric: platform behavior,
  Claude/Codex invocation reliability, installed-cache pathing, packaging,
  dependency management, update path, performance, diagnostics, and maintainer
  ergonomics.
- Run smoke probes or gather documented platform evidence where invocation
  mechanics are uncertain.
- Select one canonical runtime strategy and document rejected options.
- Define the command contract: entrypoint name, helper dispatch, argument
  parsing, JSON stdin/stdout envelopes, exit-code mapping, stderr diagnostics,
  path normalization, subprocess execution rules, prerequisite reporting, and
  runtime version reporting.
- Name temporary compatibility adapters, if any, and the spec that removes them.

**Out of Scope:**

- Building the runner.
- Porting helper behavior.
- Rewriting public docs beyond the decision record.
- Selecting supply-chain controls beyond noting runtime-specific implications
  for XPLAT-003.

**Candidate Evidence To Capture:**

- Runtime availability and invocation behavior in installed Claude and Codex
  plugin caches.
- Native Windows/macOS/Linux filesystem and subprocess behavior.
- Dependency/bootstrap requirements for a first-time public user.
- How generated Claude and Codex payloads would package or point to runtime
  artifacts.
- Failure modes and diagnosability when prerequisites are missing.

**Done When:**

- XPLAT-004 can build without reopening the runtime language/package decision.
- The selected command contract is precise enough for fixture parity tests.
- Rejected options are documented with enough rationale to avoid churn later.

---

### XPLAT-003: Supply-Chain Security and Consumer Trust Model

**Priority:** P1 | **Depends On:** XPLAT-002 | **Enables:** XPLAT-004, XPLAT-007

**Status:** Pending.

**Goal:** Choose the security and provenance approach for the new runtime so
consumers can understand what they are installing and what the project verifies
before release.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 0-140 |
Production files: 0 |
Total files: 2-5 |
Budget result: within budget (decision record and policy)

**Scope:**

- Evaluate runtime-specific dependency risk and packaging risk after XPLAT-002
  narrows the candidate set.
- Choose first-release requirements for dependency pinning/lockfiles,
  reproducible or repeatable builds, generated payload integrity, vulnerability
  scanning, and release verification.
- Evaluate SBOMs, provenance/attestations, artifact checksums/signatures, and
  dependency update cadence. Decide which controls are required before public
  release and which are follow-up hardening.
- Define what consumers can verify locally after plugin installation.
- Define what maintainers must verify in CI before publishing a release.
- Identify docs/release-note wording that is allowed, and wording that would
  overclaim the implemented guarantees.

**Out of Scope:**

- Implementing CI/release changes.
- Building the runner.
- Selecting the runtime independent of XPLAT-002.
- Formal third-party security audit procurement.

**Security Questions To Answer:**

- What is the minimal trustworthy first-release bar for this plugin marketplace?
- Are checksums/signatures useful if plugin installation does not verify them
  automatically?
- Should generated Claude/Codex payloads include embedded integrity metadata?
- Should the project produce an SBOM, provenance attestation, both, or neither
  for the first public release?
- Which controls belong in release automation versus local plugin runtime
  preflight?

**Done When:**

- XPLAT-004 knows which security controls must be built into the runner and
  generated runtime artifacts.
- XPLAT-007 knows which release/docs claims are allowed.
- Deferred supply-chain hardening is explicit and justified.

---

### XPLAT-004: Cross-Platform Runner Foundation

**Priority:** P1 | **Depends On:** XPLAT-002, XPLAT-003 | **Enables:** XPLAT-005, XPLAT-006, XPLAT-007

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
  platform, executable availability, plugin root, missing prerequisites, and
  runtime version as structured JSON.
- Add a parity harness that can run old Bash helpers and new runner helpers over
  fixtures while Bash still exists.
- Implement the XPLAT-003 first-release controls that apply to runtime source,
  dependencies, and generated runtime artifacts.
- Document how Claude and Codex skills will invoke the runner after cutover.

**Out of Scope:**

- Porting existing helper behavior except tiny smoke/preflight helpers needed to
  prove the runner contract.
- Removing Bash helpers.
- Updating public install docs.
- Implementing release automation controls that XPLAT-003 assigns outside the
  runner foundation.

**Key Files Likely To Change:**

- `speckit-pro/<selected-runtime-source>/**`
- `speckit-pro/.claude-plugin/plugin.json`
- `speckit-pro/.codex-plugin/plugin.json`
- `tests/speckit-pro/**`
- `speckit-pro/README.md` only if needed for maintainer-facing development notes

**Done When:**

- The runner executes on native Windows, macOS, and Linux.
- The parity harness can compare old/new helper output deterministically.
- First-release supply-chain controls assigned to the runner are in place.
- No active skill has been switched yet; this spec only creates the safe runway.

---

### XPLAT-005: Read-Only Helper Port

**Priority:** P1 | **Depends On:** XPLAT-004 | **Enables:** XPLAT-007 and reduces XPLAT-006 risk

**Status:** Pending.

**Goal:** Port all read-only and advisory plugin helpers to the new runner while
preserving current JSON and exit semantics.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 400-800 |
Production files: 6-8 |
Total files: 12-25 |
Budget result: likely warn; split into XPLAT-005a/005b if the XPLAT-001
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
- Keep the Bash helpers as temporary reference implementations until XPLAT-007.

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

### XPLAT-006: Mutation, Install, and PR-Emission Helper Port

**Priority:** P1 | **Depends On:** XPLAT-004, XPLAT-005 | **Enables:** XPLAT-007

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

### XPLAT-007: Claude/Codex Cutover and Native Windows Release Gate

**Priority:** P1 | **Depends On:** XPLAT-005, XPLAT-006 | **Enables:** Public release readiness

**Status:** Pending.

**Goal:** Switch active Claude and Codex plugin runtime surfaces to the
cross-platform runner and prove public-release readiness with native Windows UAT
and accurate consumer-trust documentation.

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
- Document the implemented XPLAT-003 security model in public docs and release
  notes without overstating guarantees.
- Capture manual UAT evidence for Claude and Codex on native Windows, macOS, and
  Linux.

**Out of Scope:**

- Replacing GitHub Actions.
- Replacing repository maintainer scripts not shipped into the installed plugin.
- Changing GitHub Spec Kit's own generated `.specify/scripts/bash/` helpers in
  consumer projects.
- Claiming cryptographic guarantees that were not implemented.

**Key Files Likely To Change:**

- `speckit-pro/skills/**`
- `speckit-pro/codex-skills/**`
- `speckit-pro/agents/**`
- `speckit-pro/codex-agents/**`
- `speckit-pro/hooks/**`
- `speckit-pro/codex-hooks.json`
- `speckit-pro/README.md`
- `docs-site/src/content/docs/install/**`
- `docs-site/src/content/docs/security-and-trust.md`
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
- Public docs and release notes match the implemented consumer-trust model.

---

## Release Blocker Statement

SpecKit Pro should not be marketed as a public, cross-platform Claude/Codex
plugin until XPLAT-007 is complete. Before then, native Windows support is not a
documentation problem; it is an implementation gap. Consumer trust also remains a
planning gap until XPLAT-003 is complete and an implementation gap until its
required controls are wired into XPLAT-004 and XPLAT-007.

## References

- Current active Claude autopilot startup invokes Bash helpers from
  `speckit-pro/skills/speckit-autopilot/SKILL.md`.
- Current active Codex autopilot startup resolves the same shared script
  directory from `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`.
- Current plugin README lists `jq` as a validation-script prerequisite.
- Current helper scripts under `speckit-pro/skills/**/scripts/`,
  `speckit-pro/codex-skills/**/scripts/`, and `speckit-pro/scripts/` are Bash.
