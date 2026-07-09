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
slice. Refined 2026-06-28 after XPLAT-003 user-journey analysis clarified that
the release gate must prove install completeness, first-use success, update, and
autoheal behavior across Claude Code and Codex, not only native Windows runtime
execution. Refined again on 2026-06-28 after the runtime decision was reopened:
the active implementation path is now a Python 3.11+ standard-library runner
aligned with official Spec Kit / `specify` prerequisites, and the Bash
deprecation scope includes active helper tooling, build, test, eval, payload,
install-verification, and release-readiness paths. Bash may remain only as
GitHub CI/CD dispatch glue that calls Python gates and contains no validation,
packaging, install, or runtime logic.
Updated 2026-06-29 after XPLAT-003 merged in PR #267 and was archived;
XPLAT-004 became ready to scaffold from the archived Python-only
security/control model. Updated 2026-06-30 after XPLAT-004 scaffold started on
`codex/xplat-004-cross-platform-runner-foundation`; the setup design concept
accepted a two-slice implementation plan inside one workflow. Updated
2026-07-01 after XPLAT-004 merged in PR #274 and the active spec folder was
archived; XPLAT-005 became ready to scaffold. Updated again on 2026-07-01 after
XPLAT-005 scaffold started on `codex/xplat-005-read-only-helper-port`; the setup
design concept accepted one workflow with two internal slices. Updated
2026-07-03 after XPLAT-005 merged in PR #276 and the active spec folder was
archived; XPLAT-006 became ready to scaffold from the read-only helper registry
and parity fixture pattern. Updated after PR #280 to split the final
Python-only goal into XPLAT-007 for Python tooling/release-gate migration and
XPLAT-008 for Claude/Codex cutover, install/update/autoheal UAT, and public
release readiness. Updated again on 2026-07-03 after XPLAT-006 scaffold started
on `codex/xplat-006-mutation-install-pr-emission-helper-port`; the setup design
concept accepted one workflow with three internal slices. Updated 2026-07-04
after XPLAT-006 merged in PR #281 and the active spec folder was archived;
XPLAT-007 became ready to scaffold from the Python runner helper contracts,
fixture tree, install inventory, and deferred-live-mutation boundaries. Updated
again on 2026-07-04 after XPLAT-007 scaffold started on
`codex/xplat-007-python-tooling-and-release-gate-migration`; the setup design
concept accepted one workflow with three internal slices. Updated 2026-07-05
after XPLAT-007 merged across PRs #284, #285, #286, and #287 and the active
spec folder was archived; XPLAT-008 became ready for installed Claude/Codex
cutover, native UAT, update/autoheal, and public release readiness. Updated
again on 2026-07-05 after XPLAT-008 scaffold started on
`codex/xplat-008-claude-codex-cutover-universal-install-release-gate`; the
setup design concept accepted one workflow with three internal slices. Updated
2026-07-07 after XPLAT-008 merged across PRs #289, #290, and #291, followed by
readiness fix PR #292, and the active spec folder was archived. A follow-up
audit found that generated and installed payloads contain zero `.sh` files, but
the source plugin still contains 35 Bash scripts and active generated/source
agent instructions still reference Bash. The roadmap now adds XPLAT-009 for
plugin source/payload Bash eradication and XPLAT-010 for repository-wide Bash
confinement. Public native Windows/macOS/Linux release claims remain blocked
until the preserved XPLAT-008 UAT matrix has six passing operator rows and the
zero-Bash backstop gates are complete. Updated again on 2026-07-07 after
XPLAT-009 scaffold started on
`codex/xplat-009-plugin-source-and-payload-bash-eradication`; the setup accepted
one workflow with two vertical slices for plugin-source Bash removal and
payload/cache zero-Bash proof.

---

## Roadmap Overview

The release-blocker work is decomposed into **10 specifications** across **10
dependency tiers**:

| Tier | Specs | Purpose | Parallelization |
|---|---|---|---|
| 1 | XPLAT-001 | Inventory active runtime dependencies and define evaluation constraints | Sequential |
| 2 | XPLAT-002 | Research runtime implementation options and choose the contract | Sequential after inventory |
| 3 | XPLAT-003 | Research and choose the supply-chain security / consumer-trust model | Sequential after runtime decision |
| 4 | XPLAT-004 | Build the cross-platform runner foundation and parity harness | Sequential after runtime and security decisions |
| 5 | XPLAT-005 | Port read-only/advisory helpers with fixture parity | Sequential after runner foundation |
| 6 | XPLAT-006 | Port mutation, install, and PR-emission helpers | Complete / archived after PR #281 |
| 7 | XPLAT-007 | Replace active repo-local Bash helpers, tests, evals, payload builders, release checks, install verification, and release-readiness gates with Python commands | Complete / archived after PRs #284-#287 |
| 8 | XPLAT-008 | Cut over Claude/Codex surfaces, rebuild payloads, and prove universal install/full-use/update/autoheal release readiness | Complete / archived after PRs #289-#292; public native-platform claims remain blocked by pending operator UAT |
| 9 | XPLAT-009 | Remove remaining Bash script files and active Bash instructions from plugin source and generated payloads | In Progress; scaffolded on `codex/xplat-009-plugin-source-and-payload-bash-eradication` with a two-slice workflow |
| 10 | XPLAT-010 | Confine repository Bash usage to GitHub CI/CD workflow dispatch glue only | Blocked until XPLAT-009 completes |

**Execution Order:** XPLAT-001 -> XPLAT-002 -> XPLAT-003 -> XPLAT-004 -> XPLAT-005 -> XPLAT-006 -> XPLAT-007 -> XPLAT-008 -> XPLAT-009 -> XPLAT-010

**Dependency Constraints:**

- XPLAT-002 requires XPLAT-001 because the runtime decision must be based on the
  actual active installed-runtime surface, not an assumed helper list.
- XPLAT-003 requires XPLAT-002 because the supply-chain model depends on the
  selected Python runtime, packaging model, and generated runner-file
  categories.
- XPLAT-004 requires XPLAT-002 and XPLAT-003 because the runner must implement
  one selected runtime contract and the first-release security controls.
- XPLAT-005 requires XPLAT-004 because parity tests need the final runner command
  shape and shared JSON/path library.
- XPLAT-006 required XPLAT-004 and reused XPLAT-005 test patterns; it is now
  complete and archived after PR #281.
- XPLAT-007 requires XPLAT-006 because active repo-local Bash helpers, tests,
  evals, payload builders, install-verification scripts, and release gates
  cannot become Python-authoritative until every plugin-runtime helper has a
  runner-side contract, fixture boundary, and migration handoff.
- XPLAT-008 required XPLAT-006 and XPLAT-007 because no active Claude/Codex
  surface could switch and no public release claim could ship until every
  plugin-runtime helper and release gate had a Python path. It is now complete
  and archived after PRs #289-#292; public native-platform claims still require
  passing operator UAT rows in `docs/ai/specs/.process/XPLAT-008-uat-matrix.md`.
- XPLAT-009 requires XPLAT-008 because the plugin source/payload cleanup must
  preserve the installed Claude/Codex cutover contract and release-readiness
  gates that XPLAT-008 established.
- XPLAT-010 requires XPLAT-009 because repository-wide Bash confinement should
  not start until plugin source and generated payloads are already Bash-free.

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

After XPLAT-008, installed Claude and Codex plugin workflows MUST NOT require
Bash, Git Bash, WSL, PowerShell, or `jq` as the implementation substrate on
native Windows, macOS, or Linux. Shells may still exist in a user's environment,
but SpecKit Pro cannot depend on them for installed plugin runtime behavior.

The selected implementation substrate is Python 3.11+ standard-library code
through the official Spec Kit / `specify` prerequisite boundary. Active plugin
helper tooling, build, test, eval, payload-generation, install-verification, and
release-readiness gates are inside this lane. Historical/archive references may
remain as prose only. Shell may remain only as GitHub CI/CD dispatch glue that
invokes Python gates and contains no validation, packaging, install, or runtime
logic.

After XPLAT-009, `speckit-pro/` and generated `dist/**/speckit-pro` payloads
must contain zero Bash script files and zero active Bash/`jq` instructions. After
XPLAT-010, the whole repository must confine Bash to GitHub CI/CD workflow
dispatch glue only.

## Python Confidence And Proof Boundary

The Python decision has high planning confidence because official Spec Kit /
`specify` already requires Python 3.11+, and the selected runner uses only
standard-library behavior. Current confidence is:

- High, approximately 90%, that Python is the right universal dependency for
  SpecKit Pro because it matches the upstream Spec Kit prerequisite.
- High, approximately 85-90%, that a Python stdlib runner will behave
  consistently once the interpreter is launched.
- Medium, approximately 65-75%, that the full current Claude/Codex plugin user
  journey works across all target platforms before implementation, because
  installed-cache launch, generated payload cutover, and native UAT are not yet
  complete.

The remaining risk is not Python itself. The risk is platform-specific
interpreter discovery and installed plugin invocation: Windows may need
`py -3.11`, `python`, or `python3`; macOS/Linux usually use `python3` but PATH
can vary; launcher permissions, line endings, path handling, and executable
lookup must be proven from installed Claude and Codex plugin caches. XPLAT-004
must prove the runner launch path, and XPLAT-008 must prove the full user
journey before any public native Windows/macOS/Linux claim.

## Consumer Trust Constraint

After XPLAT-008, public docs and release notes MUST accurately state how the
runner files are packaged, what dependencies they include, what consumers can
verify locally, and which security guarantees are intentionally not claimed.
Supply-chain guarantees must be implemented before they are marketed.

## Journey-Aligned Release Bar

The XPLAT lane is complete only when the user journey works end to end. Runtime
replacement is necessary but not sufficient.

- A new user can install the latest tagged SpecKit Pro release for Claude Code,
  Codex, or both without installing Bash, Git Bash, WSL, PowerShell-specific
  shims, `jq`, Go, Rust, Zig, or another implementation runtime beyond official
  Spec Kit / `specify` prerequisites.
- Claude Code and Codex installs contain 100 percent of expected skills,
  bundled agents, hooks, generated payload files, runner source or launcher
  files, manifest entries, and local verification metadata.
- The first documented workflows succeed: scaffold/status, agent availability
  checks, autopilot dry-run, PR-packet/UAT generation paths, and safe no-op
  validation paths.
- Scaffold/status/autopilot call a shared doctor/preflight contract before
  meaningful work. The doctor must detect stale plugin versions, missing bundled
  agents, missing runner files, missing generated payload files, and
  unsupported platform claims; it auto-repairs only safe gaps and gives exact
  remediation for unsafe gaps.
- Active helper tooling, build, test, eval, payload-generation,
  install-verification, and release-readiness gates run through Python
  standard-library tooling and do not require Bash, Git Bash, WSL, PowerShell
  helper scripts, or `jq`.
- The update path verifies that Claude Code and Codex are both on the latest
  tagged plugin release and that generated payloads match the release manifest.
- UAT evidence is readable and complete. Runbooks must not ship placeholder PR
  fields, raw implementation anchors, empty expected-result sections, or
  unfilled platform/product rows.

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
XPLAT-007 Python Tooling and Release-Gate Migration
    |
    v
XPLAT-008 Claude/Codex Cutover and Universal Install Release Gate
    |
    v
XPLAT-009 Plugin Source and Payload Bash Eradication
    |
    v
XPLAT-010 Repository Bash Confinement and CI Dispatch Guard
    |
    v
PUBLIC RELEASE HELD BY XPLAT-008 UAT MATRIX AND ZERO-BASH BACKSTOP GATES
```

---

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|---|---|---|---|---|
| XPLAT-001 | Runtime Inventory and Constraints | Complete / Archived | `.process/XPLAT-001-workflow.md` | Archived in `.specify/memory/archive-reports/2026-06-29-completed-active-specs-post-merge-hygiene.md`; inventory report remains `docs/ai/research/cross-platform-runtime-inventory.md` |
| XPLAT-002 | Runtime Implementation Options and Contract Decision | Complete / Archived | `.process/XPLAT-002-workflow.md` | Archived in `.specify/memory/archive-reports/2026-06-29-completed-active-specs-post-merge-hygiene.md`; Python stdlib runner decision carried forward |
| XPLAT-003 | Supply-Chain Security and Consumer Trust Model | Complete / Archived | `.process/XPLAT-003-workflow.md` | Archived in `.specify/memory/archive-reports/2026-06-29-xplat-003-post-merge-hygiene.md`; active spec folder removed after PR #267 |
| XPLAT-004 | Cross-Platform Runner Foundation | Complete / Archived | `.process/XPLAT-004-workflow.md` | Archived in `.specify/memory/archive-reports/2026-07-01-xplat-004-post-merge-hygiene.md`; runner source, metadata, contract fixtures, and tests landed in PR #274 |
| XPLAT-005 | Read-Only Helper Port | Complete / Archived | `.process/XPLAT-005-workflow.md` | Archived in `.specify/memory/archive-reports/2026-07-03-xplat-005-post-merge-hygiene.md`; read-only helper registry, Python-authoritative records, parity fixtures, and Layer 4 gates landed in PR #276 |
| XPLAT-006 | Mutation, Install, and PR-Emission Helper Port | Complete / Archived | `.process/XPLAT-006-workflow.md` | Archived in `.specify/memory/archive-reports/2026-07-04-xplat-006-post-merge-hygiene.md`; mutation primitives, install inventory/doctor proof, PR-body/command-plan fixtures, phase-coverage hardening, and Layer 4 mutation-helper gates landed in PR #281 |
| XPLAT-007 | Python Tooling and Release-Gate Migration | Complete / Archived | `.process/XPLAT-007-workflow.md` | Archived in `.specify/memory/archive-reports/2026-07-05-xplat-007-post-merge-hygiene.md`; Python gate package, CI dispatch, promotion records, and Layer 4 gate tests landed across PRs #284-#287 |
| XPLAT-008 | Claude/Codex Cutover and Universal Install Release Gate | Complete / Archived | `.process/XPLAT-008-workflow.md` | Archived in `.specify/memory/archive-reports/2026-07-07-xplat-008-post-merge-hygiene.md`; active Claude/Codex cutover, payload rebuild, public docs claim alignment, release-readiness gates, and safe repair controls landed across PRs #289-#292; public native-platform claims remain blocked by `docs/ai/specs/.process/XPLAT-008-uat-matrix.md` |
| XPLAT-009 | Plugin Source and Payload Bash Eradication | In Progress | `.process/XPLAT-009-workflow.md` | Resume with `$speckit-autopilot` against `docs/ai/specs/.process/XPLAT-009-workflow.md`; two accepted slices remove active plugin-source Bash first, then rebuild payloads and prove generated/installed-cache zero-Bash guards |
| XPLAT-010 | Repository Bash Confinement and CI Dispatch Guard | In Progress | `.process/XPLAT-010-workflow.md` | Run `$speckit-autopilot` against `docs/ai/specs/.process/XPLAT-010-workflow.md`; scaffolded 2026-07-08 on branch `xplat-010-repository-bash-confinement` with an accepted 13-PR split and a public-release-notes scope addition (design concept Q9/Q10) |

**Status Legend:** Pending | Ready | In Progress | In Review | Complete | Complete / Archived | Blocked

---

## Specification Sections

### XPLAT-001: Runtime Inventory and Constraints

**Priority:** P1 | **Depends On:** None | **Enables:** XPLAT-002, XPLAT-003, XPLAT-004, XPLAT-005, XPLAT-006, XPLAT-007, XPLAT-008

**Status:** Complete / Archived. Scaffolded and implemented on 2026-06-25 in
branch `codex/xplat-001-runtime-inventory-constraints`; merged through PR #263
on 2026-06-26 at `a7f9ca97`; workflow file is
`docs/ai/specs/.process/XPLAT-001-workflow.md`; durable report is
`docs/ai/research/cross-platform-runtime-inventory.md`; active spec artifacts
are archived in
`.specify/memory/archive-reports/2026-06-29-completed-active-specs-post-merge-hygiene.md`.

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
  active test/eval gate, active build/release gate, GitHub CI/CD dispatch glue,
  temporary parity fixture, or historical/archive.
- Require static caller-to-callee invocation-trace evidence before marking any
  finding as a proven active installed-runtime dependency.
- Map every active runtime dependency to an owner category: read-only helper,
  mutation/helper, cutover guidance, GitHub CI/CD dispatch exception, or
  follow-up exception.
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
- Making public docs claim Windows support before XPLAT-008 passes.

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
- XPLAT-003 has a clear security/trust evaluation rubric and runner-file list.
- Every active Bash dependency has a provisional owner spec: XPLAT-005,
  XPLAT-006, XPLAT-007, active-gate migration, or GitHub CI/CD dispatch
  exception.

**Completion Handoff:**

- Inventory represented 21,162 scan hits across the scoped runtime-assumption
  families: shell substrate, script-file references, JSON query usage, shell
  quoting/operators, Unix paths, file-mode changes, and newline policy.
- Active installed-runtime rows map to XPLAT-005 read-only helper work,
  XPLAT-006 mutation/install/PR-emission helper work, XPLAT-007 test/eval,
  payload, install-verification, and release-gate migration, and XPLAT-008 final
  cutover guidance.
- XPLAT-002 should use the non-scoring runtime rubric in the report.
- XPLAT-003 should use the non-scoring supply-chain rubric in the report.
- XPLAT-001 did not port helpers to a replacement runtime, change active
  installed invocation paths, score candidates, or select controls. Post-PR
  review remediation synchronized generated payload copies of the existing
  spec-index helper only.

---

### XPLAT-002: Runtime Implementation Options and Contract Decision

**Priority:** P1 | **Depends On:** XPLAT-001 | **Enables:** XPLAT-004, XPLAT-005, XPLAT-006, XPLAT-007, XPLAT-008

**Status:** Complete / Archived. PR #266 merged on 2026-06-27 at `fff4d6b5`.
Scaffolded on 2026-06-26 in branch
`codex/xplat-002-runtime-implementation-options-contract-decision`; workflow
file is `docs/ai/specs/.process/XPLAT-002-workflow.md`; design concept is
`docs/ai/specs/.process/XPLAT-002-design-concept.md`; active spec artifacts are
archived in
`.specify/memory/archive-reports/2026-06-29-completed-active-specs-post-merge-hygiene.md`.

**Goal:** Research and evaluate implementation options, then select the one
runtime contract that all later specs must implement. The amended and current
contract is Python 3.11+ standard-library source; compiled per-platform binaries
are rejected historical candidates, not XPLAT fallbacks.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 0-120 |
Production files: 0 |
Total files: 2-5 |
Budget result: within budget (decision record and probes)

**Scope:**

- Record the historical comparison of JavaScript/TypeScript, Python, and small
  per-platform binaries, then lock the Python standard-library source contract.
- Evaluate each candidate against the XPLAT-001 rubric: platform behavior,
  Claude/Codex invocation reliability, installed-cache pathing, packaging,
  dependency management, update path, performance, diagnostics, and maintainer
  ergonomics.
- Run smoke probes or gather documented platform evidence where invocation
  mechanics are uncertain.
- Select one canonical runtime strategy and document rejected options.
- State that compiled binaries are not an allowed compatibility adapter or
  downstream fallback within XPLAT.
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

**Priority:** P1 | **Depends On:** XPLAT-002 | **Enables:** XPLAT-004, XPLAT-007, XPLAT-008

**Status:** Complete / Archived. Implemented on 2026-06-27 in branch
`codex/xplat-003-supply-chain-security-and-consumer-trust-model`; workflow file
is `docs/ai/specs/.process/XPLAT-003-workflow.md`; design concept is
`docs/ai/specs/.process/XPLAT-003-design-concept.md`; merged through PR #267 on
2026-06-29 at `1ab96b38`. Durable decision artifacts are archived in
`.specify/memory/` and recoverable through
`.specify/memory/archive-reports/2026-06-29-xplat-003-post-merge-hygiene.md`;
the active `specs/xplat-003-supply-chain-security-and-consumer-trust-model/`
folder was removed after merge.

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
  generated runner files.
- XPLAT-008 knows which release/docs claims are allowed.
- Deferred supply-chain hardening is explicit and justified.

---

### XPLAT-004: Cross-Platform Runner Foundation

**Priority:** P1 | **Depends On:** XPLAT-002, XPLAT-003 | **Enables:** XPLAT-005, XPLAT-006, XPLAT-007, XPLAT-008

**Status:** Complete / Archived. Scaffolded on 2026-06-30 in branch
`codex/xplat-004-cross-platform-runner-foundation` and merged through PR #274
on 2026-07-01 at `cef3ed260dabf73833d3de82f82cacdb2c7758fa`; workflow file is
`docs/ai/specs/.process/XPLAT-004-workflow.md`; design concept is
`docs/ai/specs/.process/XPLAT-004-design-concept.md`; archive report is
`.specify/memory/archive-reports/2026-07-01-xplat-004-post-merge-hygiene.md`.

**Goal:** Build the minimal source-checkout Python 3.11+ standard-library
runner foundation, runtime-info/preflight surface, contract smoke fixtures, and
source integrity metadata that make future helper ports consistent and testable.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 350-420 |
Production files: 3-6 |
Total files: 8-14 |
Budget result: warning accepted through two planned reviewable slices inside one
XPLAT-004 workflow. Split or trim if real helper behavior, generated payload
propagation, active cutover, or native installed-cache proof starts landing
here.

**Scope:**

- Add the Python runner source layout under `speckit-pro/speckit_pro_runner/`
  with the stable module entrypoint `<python> -m speckit_pro_runner`.
- Implement shared runner primitives for JSON envelope
  validation/construction, strict diagnostics/remediation, typed path rendering,
  shell-disabled fixture subprocess records, platform detection, plugin-root
  detection, and bounded source metadata checks.
- Implement `runtime-info` and `preflight` operations that return runtime,
  platform, architecture, plugin root, Python and `specify` prerequisite status,
  runner identity, source-checkout context, metadata pointers, and runtime
  version as structured JSON.
- Verify official Spec Kit prerequisites: Python 3.11+ and a working `specify`
  command. The runner must fail closed with deterministic diagnostics and
  remediation when either is missing or unsupported.
- Add a Python standard-library Layer 4 runner test entrypoint and compact
  contract fixture matrix for envelope validation, diagnostics, typed paths,
  subprocess result records, runtime-info, and preflight behavior.
- Keep contract fixtures synthetic. They must not run old Bash helpers, port
  real helper behavior, or compare old/new production helper output.
- Implement the XPLAT-003 first-release controls assigned to runner source:
  runner identity, checksum file, manifest metadata, and source metadata
  verification behavior.
- Add deterministic Windows/Linux source-checkout runbook fixture guidance with
  explicit non-claim language. Installed-cache launch proof, native matrix UAT,
  release-readiness, and public platform claims remain XPLAT-008.
- Document the future Claude/Codex invocation contract for downstream cutover
  without editing active skills, hooks, generated payloads, install behavior, or
  public docs.

**Out of Scope:**

- Porting existing helper behavior beyond `runtime-info`, `preflight`, and
  synthetic contract smoke fixtures.
- Running old Bash helpers and new runner helpers in parity; real helper parity
  belongs to XPLAT-005 and XPLAT-006.
- Implementing general filesystem read/write helper APIs or mutation semantics
  beyond source metadata checks and fixture files.
- Removing Bash helpers or Bash-only release gates.
- Updating active Claude Code or Codex skills, hooks, generated payloads,
  install behavior, or public docs to invoke the runner.
- Copying runner files into `dist/**`.
- Proving installed-cache execution on native Windows, macOS, or Linux.
- Making public native-platform support claims.
- Implementing release automation controls that XPLAT-003 assigns outside the
  runner foundation.

**Canonical Shipped Artifacts:**

- `speckit-pro/speckit_pro_runner/**`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py`
- `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.sh`
- `tests/speckit-pro/layer4-scripts/fixtures/speckit-pro-runner/**`
- `tests/speckit-pro/run-all.sh`
- `docs/ai/specs/.process/XPLAT-004-workflow.md`
- `docs/ai/specs/.process/XPLAT-004-design-concept.md`

**Done When:**

- The Python runner executes from a source checkout through
  `<python> -m speckit_pro_runner` with JSON stdin, one JSON stdout response,
  and line-delimited JSON stderr diagnostics.
- `runtime-info` and `preflight` report source-checkout runtime, platform,
  plugin-root, prerequisite, runner identity, and metadata information, and
  fail closed for missing Python 3.11+, missing `specify`, missing plugin root,
  or invalid runner metadata.
- Contract smoke fixtures cover envelope validation, diagnostics, typed paths,
  subprocess result records, runtime-info, and preflight without running old
  Bash helpers or porting real production helpers.
- A Python standard-library runner unit/contract test entrypoint exists so
  downstream helper ports can reuse the runner test pattern.
- Runner source checksum and manifest metadata exist, validate, and are checked
  by preflight.
- Windows/Linux runbook fixtures clearly identify `source_checkout` context and
  state that installed-cache launch proof, native UAT, release-readiness, and
  public platform claims remain XPLAT-008 responsibilities.
- No active skill, hook, generated payload, install behavior, or public
  documentation claim has been switched to the runner.

---

### XPLAT-005: Read-Only Helper Port

**Priority:** P1 | **Depends On:** XPLAT-004 | **Enables:** XPLAT-006, XPLAT-007, XPLAT-008

**Status:** Complete / Archived. XPLAT-005 merged in PR #276 on 2026-07-03 and
the active `specs/xplat-005-read-only-helper-port/` folder was removed in the
post-merge archive cleanup. Workflow and design concept files remain preserved
under `docs/ai/specs/.process/`; recovery commands are recorded in
`.specify/memory/archive-reports/2026-07-03-xplat-005-post-merge-hygiene.md`.

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
- Port the corresponding Layer 4/unit fixtures into Python standard-library
  tests so the Python tests become the release gate after parity is accepted.
- Keep the Bash helpers only as temporary reference implementations until
  XPLAT-007.

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
- Read-only helper release gates use Python tests; Bash fixtures are retained
  only as temporary migration evidence and must be removed from active gates by
  XPLAT-007.

---

### XPLAT-006: Mutation, Install, and PR-Emission Helper Port

**Priority:** P1 | **Depends On:** XPLAT-004, XPLAT-005 | **Enables:** XPLAT-007, XPLAT-008

**Status:** Complete / Archived. Merged in PR #281 on 2026-07-04 and archived in
`.specify/memory/archive-reports/2026-07-04-xplat-006-post-merge-hygiene.md`;
workflow file is `docs/ai/specs/.process/XPLAT-006-workflow.md`; design concept
is `docs/ai/specs/.process/XPLAT-006-design-concept.md`. XPLAT-006 delivered
runner-side mutation primitives, install inventory/doctor proof, generated
PR-body output, deferred command-plan diagnostics for live mutation, registry
handoff records, phase-coverage hardening, and Layer 4 mutation-helper gates.
It preserved active Claude/Codex invocation cutover and public native-platform
claims for XPLAT-008, and active repo-local Bash gate migration for XPLAT-007.

**Goal:** Completed. Port the state-mutating helper substrate and reviewable
handoff evidence after the runner and read-only parity patterns stabilized.

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
- Port install-completeness and repair helpers that verify the expected Claude
  Code and Codex bundled-agent set from a generated inventory or manifest,
  rather than from a stale hardcoded list.
- Add the shared doctor/preflight contract used by scaffold/status/autopilot to
  detect stale releases, missing bundled agents, missing runner files,
  missing generated payload files, and unsafe repair cases before workflow
  execution continues.
- Preserve atomic write and dry-run/apply semantics where the Bash helper
  currently promises them.
- Preserve PR packet, workflow-contract, split-PR, restack, install, and
  relocation JSON schemas.
- Add parity fixtures for success, no-op, dry-run, invalid input,
  missing-prerequisite, dirty-worktree, and partial-failure cases.
- Port mutation-helper unit and integration-style tests that validate shipped
  behavior to Python standard-library gates before the Bash helpers are removed.
- Keep live network or GitHub mutation behind the same approval and dry-run
  boundaries as today.

**Out of Scope:**

- Active skill cutover.
- Public release docs.
- Replacing GitHub CI/CD dispatch glue that only invokes Python gates and
  contains no validation, packaging, install, or runtime logic.

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
- `doctor` / install-completeness repair helpers if introduced by XPLAT-004
- coach fixup/preset helpers that write files

**Done When:**

- Every mutation-capable installed-runtime helper has a runner equivalent.
- Claude Code and Codex install helpers verify the complete expected bundled
  agent and generated-payload set from a source-controlled manifest or generated
  inventory.
- Scaffold/status/autopilot have a shared doctor/preflight contract with
  deterministic safe-repair and manual-remediation outcomes.
- Fixture parity covers destructive and dry-run paths before active cutover.
- Mutation-helper release gates have Python Layer 4 tests and preserved
  contract fixtures; Bash tests are retained only as temporary migration
  evidence and must be removed from active gates by XPLAT-007.

---

### XPLAT-007: Python Tooling and Release-Gate Migration

**Priority:** P1 | **Depends On:** XPLAT-006 | **Enables:** XPLAT-008

**Status:** Complete / Archived. XPLAT-007 shipped across PR #284, PR #285,
PR #286, and PR #287 on 2026-07-05 and is archived in
`.specify/memory/archive-reports/2026-07-05-xplat-007-post-merge-hygiene.md`;
workflow file is `docs/ai/specs/.process/XPLAT-007-workflow.md`; design concept
is `docs/ai/specs/.process/XPLAT-007-design-concept.md`. The active spec
folder was removed from `specs/**` after preserving contract schemas under
`tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/contracts/`.

**Goal:** Replace active repo-local Bash helpers, tests, evals, payload builders,
install-verification scripts, and release-readiness gates with Python
standard-library commands before active Claude/Codex cutover.

**Reviewability Budget:** Primary surfaces: harness/adapter + docs/process |
Projected reviewable LOC: 400-800 |
Production files: 6-8 |
Total files: 12-25 |
Budget result: likely warn; split into test/eval gate, payload/release helper,
and CI-dispatch guard slices if a single workflow exceeds review budget.

**Scope:**

- Replace active Bash-based test/eval/build/release-readiness gates for shipped
  plugin behavior with Python standard-library commands, including the payload
  builder, marketplace/version sync checks, Layer 1 structural checks, Layer 4
  helper tests, AI-eval runners, tool-scoping checks, integration/parity suites,
  and the top-level test runner.
- Replace active repo-local Bash helpers, tests, evals, payload builders,
  install-verification scripts, and release scripts with Python commands. Bash
  may remain only as GitHub CI/CD dispatch glue that invokes those Python gates.
- Add deterministic guards that fail if active test/eval/build/payload/release
  paths call Bash, `jq`, Git Bash, WSL, PowerShell helper scripts, or shell-only
  parsing.
- Add a CI dispatch allowlist proving any remaining shell snippets live only in
  GitHub CI/CD dispatch glue and contain no validation, packaging, install, or
  runtime logic.
- Preserve temporary Bash parity evidence only as archived historical evidence
  after Python gates become authoritative.

**Out of Scope:**

- Active Claude/Codex skill, agent, hook, and install-guidance cutover.
- Rebuilding generated Claude/Codex payloads for release.
- Public release docs, release notes, or platform support claims.
- Native Windows/macOS/Linux installed-plugin UAT.
- Changing GitHub Spec Kit's own generated `.specify/scripts/bash/` helpers in
  consumer projects.

**Key Files Likely To Change:**

- `tests/speckit-pro/**`
- `scripts/build-plugin-payloads.py` -> Python standard-library replacement
- `scripts/refresh-local-plugin.sh` -> Python standard-library replacement
- `scripts/sync-marketplace-versions.sh` -> Python standard-library replacement
- `speckit-pro/skills/**/scripts/**`
- `speckit-pro/codex-skills/**/scripts/**`
- `speckit-pro/scripts/**`
- `.github/workflows/**` only where workflow steps must call Python gates instead
  of Bash implementations

**Done When:** Complete.

- Active repo-local helpers, tests, evals, payload builders,
  install-verification scripts, and release scripts use Python commands.
- The active test/eval/build/release-readiness suite for shipped plugin behavior
  has no Bash-only gate.
- A guard fails if active repo-local release paths reintroduce Bash, `.sh`, `jq`,
  shell interpolation, or Unix-only assumptions outside historical/archive prose
  and GitHub CI/CD dispatch glue.
- Remaining shell is limited to GitHub CI/CD dispatch glue that only invokes
  Python gates.

---

### XPLAT-008: Claude/Codex Cutover and Universal Install Release Gate

**Priority:** P1 | **Depends On:** XPLAT-006, XPLAT-007 | **Enables:** Public release readiness

**Status:** Complete / Archived. XPLAT-008 merged across PRs #289, #290, and
#291, followed by readiness fix PR #292. The active spec folder was archived
after preserving release-readiness and UAT evidence under
`docs/ai/specs/.process/`. The implementation shipped installed Claude/Codex
cutover, generated payload rebuilds, public docs claim alignment, native UAT
matrix gating, update/repair blockers, and safe repair controls. Public native
Windows/macOS/Linux support claims remain blocked until all six native operator
UAT rows pass in `docs/ai/specs/.process/XPLAT-008-uat-matrix.md`.

**Goal:** Switch active Claude and Codex plugin runtime surfaces to the
cross-platform runner and prove public-release readiness with complete
Claude/Codex installs, universal first-use journeys, update/repair behavior,
native Windows UAT, and accurate consumer-trust documentation.

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
- Add generated-payload gates proving Claude Code and Codex payloads contain the
  same release version, every expected bundled agent, every expected hook, every
  required runner file, and the release manifest/checksum metadata assigned
  by XPLAT-003.
- Remove Bash and `jq` from installed plugin runtime prerequisites.
- Add deterministic guards that fail when active installed-runtime guidance
  reintroduces `bash`, `.sh`, `jq`, shell interpolation, or Unix-only path
  assumptions outside the XPLAT-001 allowlist.
- Add or update docs so Windows users see the supported native path, any
  explicitly supported WSL path is labeled as optional, and macOS/Linux users see
  the same install-to-first-use journey.
- Document the implemented XPLAT-003 security model in public docs and release
  notes without overstating guarantees.
- Capture manual UAT evidence for Claude and Codex on native Windows, macOS, and
  Linux covering install, bundled-agent verification, scaffold/status,
  autopilot dry-run, update to the latest tagged release, and safe repair of an
  intentionally incomplete install.
- Require UAT runbooks to be filled, readable, and release-reviewable, with no
  placeholder PR fields, raw HTML anchors, empty expected-result sections, or
  unfilled platform/product rows.

**Out of Scope:**

- Replacing GitHub Actions YAML or minimal shell wrappers that only dispatch to
  Python gates and contain no plugin validation logic.
- Replacing Python tooling, test, eval, payload, release, and install-verification
  gates already owned by XPLAT-007.
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

**Done When:**

- Native Windows, macOS, and Linux UAT all pass for installed Claude and Codex
  plugin workflows without Bash, Git Bash, WSL, PowerShell-specific commands, or
  `jq`.
- Claude Code and Codex installs are proven 100 percent complete for skills,
  bundled agents, hooks, generated payloads, runner files, and XPLAT-003
  verification metadata.
- Scaffold/status/autopilot doctor checks detect stale or incomplete installs
  and either autoheal safe gaps or produce exact manual remediation steps.
- Users can update both Claude Code and Codex installs to the latest tagged
  release and rerun the first-use workflows successfully.
- A release-readiness guard blocks publication if active runtime Bash
  dependencies, incomplete generated payloads, missing bundled agents, stale
  version metadata, or incomplete UAT runbooks are detected.
- XPLAT-007's Python tooling and release-gate migration is complete and remains
  enforced during release validation.
- Public docs and release notes match the implemented consumer-trust model.

---

### XPLAT-009: Plugin Source and Payload Bash Eradication

**Priority:** P1 | **Depends On:** XPLAT-008 | **Enables:** XPLAT-010, public Bash-free release readiness

**Status:** In Progress. Scaffolded on 2026-07-07 in branch
`codex/xplat-009-plugin-source-and-payload-bash-eradication`; workflow file is
`docs/ai/specs/.process/XPLAT-009-workflow.md`; design concept is
`docs/ai/specs/.process/XPLAT-009-design-concept.md`. A 2026-07-07
post-XPLAT-008 audit found that generated payloads and the installed Codex cache
contain zero `.sh` files, but `speckit-pro/` still contains 35 Bash scripts and
active generated/source agent instructions still reference Bash. The accepted
setup uses one workflow with two vertical slices: active plugin-source Bash
removal first, then payload rebuild, installed-cache proof, and zero-Bash guards.

**Goal:** Remove every remaining Bash script file and active Bash/`jq`
instruction from plugin source and generated Claude/Codex payloads while
preserving the installed-runtime behavior shipped by XPLAT-008.

**Reviewability Budget:** Primary surfaces: harness/adapter + docs/process |
Projected reviewable LOC: 300-700 |
Production files: 6-8 |
Total files: 12-25 |
Budget result: likely warn because the cleanup spans helper ports, agent
guidance, generated payloads, and release guards; split only if the scaffold
finds a clean helper-family boundary that avoids duplicated gate work.

**Scope:**

- Port or remove the remaining plugin Bash scripts under
  `speckit-pro/skills/speckit-autopilot/scripts/`,
  `speckit-pro/skills/speckit-coach/scripts/`,
  `speckit-pro/codex-skills/install/scripts/`, and `speckit-pro/scripts/`.
- Replace active source and generated agent instructions that still call Bash
  helpers with Python runner operations or equivalent no-shell guidance.
- Remove stale Bash-reference parity concepts from active release gates where
  they imply a live fallback rather than archived provenance.
- Rebuild Claude and Codex payloads from the updated source surfaces.
- Add or tighten deterministic guards proving zero `.sh` files in `speckit-pro/`
  and zero `.sh` files in generated `dist/**/speckit-pro` payloads.
- Add an active-instruction guard that blocks Bash, `.sh`, `jq`, shell
  interpolation, or Unix-only assumptions in plugin source and generated
  payloads outside historical/archive prose.
- Preserve GitHub workflow dispatch glue as out of scope for this spec.

**Out of Scope:**

- Repository-wide shell harness cleanup under `tests/**`, top-level `scripts/**`,
  hooks outside the plugin package, and `.specify/**`; XPLAT-010 owns that.
- Completing the XPLAT-008 native operator UAT matrix.
- Replacing GitHub Actions workflow YAML or CI/CD dispatch snippets.
- Rewriting historical/archive prose that describes prior Bash behavior.

**Key Files Likely To Change:**

- `speckit-pro/skills/speckit-autopilot/scripts/**`
- `speckit-pro/skills/speckit-coach/scripts/**`
- `speckit-pro/codex-skills/install/scripts/**`
- `speckit-pro/scripts/**`
- `speckit-pro/agents/**`
- `speckit-pro/codex-agents/**`
- `speckit-pro/speckit_pro_runner/helpers/**`
- `speckit-pro/speckit_pro_runner/gates/**`
- `dist/claude/speckit-pro/**`
- `dist/codex/speckit-pro/**`
- `tests/speckit-pro/layer4-scripts/fixtures/**`

**Done When:**

- `find speckit-pro -type f -name '*.sh'` returns zero files.
- `find dist/claude/speckit-pro dist/codex/speckit-pro -type f -name '*.sh'`
  returns zero files after payload rebuild.
- The installed Claude/Codex plugin cache produced from the rebuilt payloads
  contains zero Bash script files.
- Active source and generated plugin instructions contain no Bash or `jq`
  invocation path outside a narrow historical/archive allowlist.
- Focused runner/helper tests and release-readiness gates pass with the new
  no-shell guard enabled.

---

### XPLAT-010: Repository Bash Confinement and CI Dispatch Guard

**Priority:** P1 | **Depends On:** XPLAT-009 | **Enables:** public Bash-free release readiness

**Status:** In Progress. Scaffolded 2026-07-08 on branch
`xplat-010-repository-bash-confinement` (XPLAT-009 merged via PR #297 and
released in speckit-pro 2.18.0). The repo-wide scan still finds many `.sh`
files outside `.github/workflows/`, including active test harnesses, top-level
helper scripts, hooks, and SpecKit process helpers. Design concept and workflow
file live under `docs/ai/specs/.process/`; an operator scope addition covers
public-readable GitHub Release notes (design concept Q10/Q11).

**Goal:** Enforce the strict repository policy that Bash may remain only as
GitHub CI/CD workflow dispatch glue. All active repo-local validation,
packaging, install, helper, hook, payload, release, and test/eval behavior must
run through Python gates or another approved non-shell path. Add containerized
Linux architecture preflight coverage and direct Windows runner smoke coverage
as CI hardening, while preserving XPLAT-008 native operator UAT as the release
claim gate.

**Reviewability Budget:** Primary surfaces: harness/adapter + seed/config +
docs/process |
Projected reviewable LOC: 400-800 |
Production files: 6-8 |
Total files: 15-25 |
Budget result: likely warn and may need typed split exceptions because the
current test harness and process helper scripts are broad.

**Scope:**

- Port or remove repo-local `.sh` files and Bash-shebang executables outside
  `.github/workflows/`, including `tests/speckit-pro/**`, top-level
  `scripts/**`, `.claude/hooks/**`, and committed `.specify/**` helper surfaces
  that participate in active release behavior.
- Update GitHub workflows so any remaining shell is limited to CI/CD dispatch
  and calls Python gates rather than embedding validation, packaging, install,
  release, or runtime logic.
- Add a local and GitHub Actions Linux container preflight path for
  `linux/amd64` and `linux/arm64` that runs the Python runner, no-shell guard,
  and relevant release-readiness checks without relying on Bash.
- Add direct-runner smoke coverage for Windows x64 and Windows
  ARM64 runner labels when available, focused on interpreter discovery,
  runner `runtime-info`/`preflight`, and no Bash/`jq` release-gate behavior.
- Add a repo-wide guard proving no `.sh` files and no active Bash/`jq`
  invocations exist outside the workflow dispatch boundary.
- Document any non-active upstream-generated exceptions with a narrow allowlist
  and ensure they cannot satisfy release readiness.
- Document that GitHub job containers are Linux-runner only, Windows containers
  have host/image compatibility constraints, and any Windows container
  experiment is preflight-only rather than native installed-plugin UAT.
- Compose public-readable GitHub Release notes: each feat/fix PR carries a
  consumer-facing release-note block (required CI check with a skip label for
  changes with no consumer-visible effect), and a Python stdlib composer
  rewrites the GitHub Release body with plain-English Highlights while keeping
  the conventional-commit list as an appendix and `CHANGELOG.md` as the
  machine ledger (operator scope addition, 2026-07-08).

**Out of Scope:**

- Plugin source and generated payload cleanup already completed by XPLAT-009.
- Native operator UAT rows already tracked by XPLAT-008 evidence.
- Treating Docker, QEMU, or Windows containers as proof of native Claude/Codex
  installed-plugin behavior.
- Third-party upstream repositories or consumer-project generated files outside
  this plugin repository.

**Key Files Likely To Change:**

- `tests/speckit-pro/**`
- `scripts/**`
- `.claude/hooks/**`
- `.specify/**`
- `.github/workflows/**`
- `speckit-pro/speckit_pro_runner/gates/**`
- `docs/ai/specs/.process/**`
- `containers/**` or another documented container-preflight fixture path if
  XPLAT-010 introduces one.

**Done When:**

- A repo-wide scan excluding `.github/workflows/` finds zero `.sh` files and
  zero Bash-shebang scripts, including extensionless executables, or any
  remaining non-active upstream-generated exception is documented, allowlisted,
  and excluded from release behavior.
- GitHub workflow shell snippets contain only dispatch glue and no embedded
  plugin validation, packaging, install, release, or runtime logic.
- Active tests, evals, payload builders, release-readiness checks,
  install-verification paths, hooks, and helper tools run without Bash or `jq`.
- Linux container preflight evidence exists for `linux/amd64` and `linux/arm64`
  using the same Python runner/release-gate entrypoints used by CI.
- Windows x64 and Windows ARM64 direct-runner smoke evidence exists when those
  runner labels are available; unavailable or public-preview runner behavior is
  recorded without converting container evidence into native UAT evidence.
- CI fails on new Bash scripts, active Bash invocations, or `jq` dependencies
  outside the workflow dispatch boundary.
- The XPLAT-008 native UAT matrix still remains the only release-satisfying
  evidence for full Claude/Codex installed-plugin journeys on native hosts.
- GitHub Releases published after this spec open with composed plain-English
  Highlights sourced from PR release-note blocks, and feat/fix PRs missing
  both the block and the skip label fail a required check.

---

## Release Blocker Statement

SpecKit Pro should not be marketed as a public, cross-platform Claude/Codex
plugin until XPLAT-008 native operator UAT is complete and the XPLAT-009/XPLAT-010
zero-Bash backstop gates pass. Before then, native Windows support and
Bash-free release readiness are implementation gaps, not documentation problems.
A complete public claim also requires proven Claude/Codex install completeness,
latest-tag update behavior, doctor/autoheal behavior, filled UAT runbooks, zero
plugin Bash scripts, and repository Bash confinement to GitHub CI/CD workflow
dispatch glue. Consumer trust is specified by XPLAT-003 and implemented through
the runner/release gates, but it remains incomplete until the remaining Bash
surfaces are removed or confined.

## References

- 2026-07-07 audit: `find speckit-pro -type f -name '*.sh'` found 35 plugin
  source Bash scripts across `speckit-pro/skills/speckit-autopilot/scripts/`,
  `speckit-pro/skills/speckit-coach/scripts/`,
  `speckit-pro/codex-skills/install/scripts/`, and `speckit-pro/scripts/`.
- 2026-07-07 audit: generated Claude/Codex payloads under
  `dist/claude/speckit-pro` and `dist/codex/speckit-pro` contained zero `.sh`
  files, and the installed Codex cache for version 2.17.0 also contained zero
  `.sh` files.
- 2026-07-07 audit: active source and generated agent instructions still
  referenced Bash helper commands, including marker-counting guidance in
  analyze/checklist executor agents and UAT runbook author guidance.
- 2026-07-07 audit: a repo-wide scan excluding `.github/workflows/` still found
  many `.sh` files outside the plugin source tree, so repository-wide Bash
  confinement is intentionally split into XPLAT-010.
- GitHub Actions workflow syntax documents that job containers, Docker
  container actions, and service containers require Linux runners; hosted
  container jobs must use Ubuntu runners.
- GitHub-hosted runner reference lists Linux ARM64 and Windows ARM64 runner
  labels as public preview, so XPLAT-010 should record runner availability in
  evidence rather than assuming stable coverage.
- Docker multi-platform build documentation supports `linux/amd64` and
  `linux/arm64` targets through `buildx`; QEMU emulation is the easiest setup
  path but can be slower than native nodes.
- Microsoft Windows container compatibility documentation records Windows
  host/image compatibility constraints, so Windows container experiments cannot
  substitute for native Windows installed-plugin UAT.
