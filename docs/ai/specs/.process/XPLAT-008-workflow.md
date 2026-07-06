# SpecKit Workflow: XPLAT-008 - Claude/Codex Cutover and Universal Install Release Gate

**Template Version**: 1.0.0
**Created**: 2026-07-05
**Purpose**: Prepare XPLAT-008 for autonomous execution from the cross-platform plugin runtime roadmap and the setup Grill Me decisions.

---

## How to Use This Workflow

Run this workflow from the XPLAT-008 worktree:

```text
$speckit-autopilot docs/ai/specs/.process/XPLAT-008-workflow.md
```

This file is already populated for XPLAT-008. Do not replace it with the
generic workflow template.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`$speckit-scaffold-spec XPLAT-008`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/XPLAT-008-design-concept.md
```

Re-read it before each phase. The design concept is the source of truth for the
accepted scope:

- One XPLAT-008 workflow with three internal implementation slices.
- Active Claude/Codex installed-runtime surfaces first, then generated payload,
  release, and public docs gates, then native UAT/update/autoheal evidence.
- Installed surfaces invoke the Python runner directly, with explicit
  interpreter discovery and no active shell or `jq` dependency.
- No-shell/no-jq guards fail active runtime paths only; archive prose, CI
  dispatch glue, and upstream Spec Kit generated bash helpers are allowed.
- Rebuild and gate both generated Claude and Codex payloads from source.
- Public docs and release notes must claim only implemented and UAT-proven
  support and must describe the XPLAT-003 trust model without overclaiming.
- Completion requires filled native Windows, macOS, and Linux UAT for both
  Claude and Codex, including install, first use, scaffold/status, autopilot
  dry-run, update, and repair.
- Doctor/autoheal should refresh trusted missing or stale install artifacts and
  print exact manual remediation for unsafe gaps.

> Grill Me is human-in-the-loop only. It is not part of the autopilot loop.
> Once this workflow begins, clarifications happen via `$speckit-clarify` and
> consensus, never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|---|---|---|---|
| Specify | `$speckit-specify` | Complete | Generated `spec.md` with 4 user stories, 22 functional requirements, 12 acceptance scenarios, 8 success criteria, and no active clarification markers |
| Clarify | `$speckit-clarify` | Pending | Resolve active surface inventory, interpreter discovery, payload contract, UAT evidence, autoheal trust boundary, and public claim wording |
| Plan | `$speckit-plan` | Pending | Produce the technical plan for three vertical slices and record reviewability warning handling |
| Checklist | `$speckit-checklist` | Pending | Run integration, security, reliability, and release-readiness checklists |
| Tasks | `$speckit-tasks` | Pending | Generate tasks ordered by active surface cutover, payload/release/docs gates, then UAT/update/autoheal |
| Analyze | `$speckit-analyze` | Complete | 4 findings remediated; structured release/UAT contracts aligned; G6 marker counter clean |
| Confidence Gate | G6.5 | Pending | Record the pre-Implement confidence score in advisory mode before implementation starts |
| Implement | `$speckit-implement` | Pending | Execute the accepted slices with tests, payload evidence, UAT runbooks, and release-readiness gates |
| Post | Post | Pending | Run verification, reviewability, UAT runbook, PR packet, PR creation, review remediation, and retrospective items |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|---|---|---|
| G1 | After Specify | User stories cover active Claude/Codex surface cutover, generated payload completeness, public docs and trust claims, full UAT matrix, update, and safe repair without unresolved clarification markers |
| G2 | After Clarify | Active runtime inventory, interpreter discovery, no-shell guard scope, payload contract, UAT artifact path, autoheal trust boundary, and public claim wording are explicit |
| G3 | After Plan | Plan records the reviewability warning, accepted three-slice strategy, Python runner invocation model, payload gate design, UAT runbook model, and safe repair boundaries |
| G4 | After Checklist | Integration, security, reliability, and release-readiness gaps are remediated or explicitly out of scope |
| G5 | After Tasks | Tasks map to the accepted three slices and include tests, generated payload evidence, docs updates, UAT runbook completion, update proof, and autoheal proof |
| G6 | After Analyze | No critical drift remains between roadmap, design concept, spec, plan, tasks, XPLAT-003 trust model, and XPLAT-007 Python gate handoff |
| G6.5 | Confidence Gate | Advisory pre-Implement confidence evidence is recorded before implementation starts |
| G7 | After Implementation | Native Windows/macOS/Linux Claude and Codex UAT pass; payload, install, update, autoheal, no-shell, and release-readiness gates pass; public docs match implemented controls |

---

## Prerequisites

### Worktree and Branch

- Worktree: `.worktrees/xplat-008-claude-codex-cutover-universal-install-release-gate`
- Branch: `codex/xplat-008-claude-codex-cutover-universal-install-release-gate`
- Contract marker: `specs/xplat-008-claude-codex-cutover-universal-install-release-gate/SPEC-MOC.md`
- Design concept: `docs/ai/specs/.process/XPLAT-008-design-concept.md`
- Workflow: `docs/ai/specs/.process/XPLAT-008-workflow.md`

Expected branch is
`codex/xplat-008-claude-codex-cutover-universal-install-release-gate`.
Preset resolution should use `.specify/presets/speckit-pro-reviewability/`
unless a deliberate higher-priority override exists.

### Grounded Source Truth

- Roadmap: `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`
- Roadmap MOC: `docs/ai/specs/cross-platform-plugin-runtime-roadmap-MOC.md`
- Product requirement: `docs/prd-cross-platform-plugin-runtime.md`
- XPLAT-003 trust model handoff:
  `.specify/memory/archive-reports/2026-06-29-xplat-003-post-merge-hygiene.md`
- XPLAT-004 runner package: `speckit-pro/speckit_pro_runner/`
- XPLAT-005 read-only helper registry and fixtures:
  `speckit-pro/speckit_pro_runner/helpers/` and
  `tests/speckit-pro/layer4-scripts/fixtures/read-only-helpers/`
- XPLAT-006 install inventory, doctor proof, mutation helper contracts, and
  deferred live-mutation boundaries:
  `speckit-pro/speckit_pro_runner/helpers/install.py`,
  `speckit-pro/speckit_pro_runner/install_inventory.json`, and
  `tests/speckit-pro/layer4-scripts/fixtures/mutation-helpers/`
- XPLAT-007 Python-authoritative gate handoff:
  `docs/ai/specs/.process/XPLAT-007-design-concept.md`,
  `speckit-pro/speckit_pro_runner/gates/`, and
  `tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/`
- Active Claude surfaces: `speckit-pro/skills/**`, `speckit-pro/agents/**`,
  `speckit-pro/hooks/hooks.json`, and `speckit-pro/README.md`
- Active Codex surfaces: `speckit-pro/codex-skills/**`,
  `speckit-pro/codex-agents/**`, and `speckit-pro/codex-hooks.json`
- Generated payloads: `dist/claude/speckit-pro/**` and
  `dist/codex/speckit-pro/**`
- Public docs: `docs-site/src/content/docs/install/**`,
  `docs-site/src/content/docs/security-and-trust.md`,
  `docs-site/src/content/docs/troubleshooting.md`, and
  `docs-site/src/content/docs/first-run.md`
- Project constitution: `.specify/memory/constitution.md`
- Design concept source: `docs/ai/specs/.process/XPLAT-008-design-concept.md`

### Phase 0 Preflight Results

| Check | Result | Evidence |
|---|---|---|
| Codex agent install | Pass | `validate-agent-install.sh --surface codex --autoheal` reported `ok: codex: 10 bundled agents installed` |
| SpecKit CLI | Pass | `command -v specify` resolved to a user-local `specify` executable |
| Remote | Pass | `git remote -v` detected `origin` |
| Branch/worktree | Pass | Created worktree on `codex/xplat-008-claude-codex-cutover-universal-install-release-gate` from `origin/main` at `2953e447` |
| Reviewability setup gate | Warn/pass | `reviewability-gate.sh setup docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md` returned `status: warn`, `pass: true`, `reviewable_loc: 250`, `production_files: 4`, `total_files: 10`, warning: primary surfaces `docs/process` and `harness/adapter` exceed one-surface warning threshold |
| Grill Me | Complete | 9 picker questions; accepted three internal slices, active surfaces first, direct Python runner invocation, active-runtime guard scope, payload rebuild and gates, implemented-only claims, full UAT matrix, safe autoheal, and three-slice sizing decision |
| Size estimate | Warn/advisory | `estimate-spec-size.sh --user-stories 3 --files 20 --frs 9 --new-vs-modify modify` returned `estimated_loc: 505`, `suggested_slices: 2`, `status: warn`; accepted three internal slices |
| Preset resolution | Pass | `specify preset resolve spec-template`, `plan-template`, and `tasks-template` resolve to `speckit-pro-reviewability v1.0.0` |

### Constitution Validation

| Principle | XPLAT-008 Requirement | Verification |
|---|---|---|
| Plugin Structure Compliance | Claude/Codex skills, agents, hooks, generated payloads, and plugin manifests keep the standard plugin layout | Layer 1 structural validation and generated payload completeness gate |
| Script Safety | Active installed-runtime guidance avoids Bash, `.sh`, `jq`, shell interpolation, and platform-specific command languages | No-shell/no-jq active-runtime guard and installed-plugin UAT |
| Semantic Versioning | Do not edit plugin versions manually; release-please owns version updates | Diff review and release-readiness gate |
| Test Coverage Before Merge | New or changed gates and helpers include focused tests and fixture evidence before payload/public docs claims land | Python runner gates, Layer 1, Layer 4, docs validation, payload gates, and UAT runbooks |
| Conventional Commits | Setup and implementation commits use conventional commit format | Commit and PR title review |
| KISS, Simplicity & YAGNI | Prefer direct runner invocation, explicit checks, and bounded autoheal over broad reinstall or speculative abstractions | Plan complexity table, task review, and G6 analysis |

---

## Specification Context

### Basic Information

| Field | Value |
|---|---|
| Spec ID | XPLAT-008 |
| Name | Claude/Codex Cutover and Universal Install Release Gate |
| Branch | `codex/xplat-008-claude-codex-cutover-universal-install-release-gate` |
| Feature directory | `specs/xplat-008-claude-codex-cutover-universal-install-release-gate` |
| Dependencies | XPLAT-006 and XPLAT-007 complete/archived; Python runner, helper ports, install inventory, and Python-authoritative gates exist |
| Enables | Public release readiness for native Windows, macOS, and Linux installed plugin workflows |
| Priority | P1 |

### Success Criteria Summary

- [ ] Active Claude and Codex skills, agents, hooks, and install guidance invoke
  the cross-platform Python runner directly without Bash, Git Bash, WSL,
  PowerShell-specific commands, `jq`, shell interpolation, or Unix-only path
  assumptions.
- [ ] Generated Claude and Codex payloads are rebuilt from source and gated for
  release version, bundled agents, hooks, runner files, and XPLAT-003
  manifest/checksum metadata.
- [ ] Active-runtime no-shell/no-jq guard fails when installed plugin guidance,
  generated payloads, or release gates reintroduce shell-only runtime behavior,
  while allowing archive prose, CI dispatch glue, and upstream Spec Kit bash
  helpers.
- [ ] Public docs and release notes explain the implemented XPLAT-003 trust
  model and claim only support proven by implementation and UAT.
- [ ] Native Windows, macOS, and Linux UAT runbooks are filled for Claude and
  Codex, covering install, bundled-agent verification, first use,
  scaffold/status, autopilot dry-run, update, and safe repair.
- [ ] Doctor/autoheal detects stale or incomplete installs, safely refreshes
  trusted missing or stale artifacts, and prints exact manual remediation for
  unsafe gaps.
- [ ] A release-readiness guard blocks publication on active shell runtime
  dependencies, incomplete payloads, missing bundled agents, stale metadata, or
  incomplete UAT runbooks.

### Accepted Three-Slice Plan

| Slice | Scope | Explicit Boundary |
|---|---|---|
| Slice 1 | Active Claude/Codex skill, agent, hook, and install-guidance cutover to direct Python runner invocation; active-runtime no-shell/no-jq guard seed | Do not publish public platform claims or rely on generated payloads until gates and UAT evidence exist |
| Slice 2 | Rebuild generated Claude/Codex payloads, add payload completeness gates, update public install/trust/troubleshooting/first-run docs, and wire release-readiness checks | Do not mark release-ready until native UAT/update/repair rows are filled |
| Slice 3 | Native Windows/macOS/Linux Claude and Codex UAT, latest-tag update proof, safe doctor/autoheal repair proof, final release-readiness guard, and public release handoff | Do not accept smoke-only or placeholder UAT evidence |

---

## Phase 1: Specify

**When to run:** At the start of XPLAT-008. Focus on what installed plugin
behavior users must get, what must be proven before public release, and which
historical/runtime surfaces are deliberately outside the guard. Output:
`specs/xplat-008-claude-codex-cutover-universal-install-release-gate/spec.md`.

### Specify Prompt

```text
$speckit-specify

## Feature: Claude/Codex Cutover and Universal Install Release Gate

### Problem Statement
SpecKit Pro now has a Python runner foundation, helper ports, install inventory,
and Python-authoritative repo-local gates, but installed Claude and Codex plugin
surfaces still need to be cut over to the runner and proven on native Windows,
macOS, and Linux. XPLAT-008 must switch active installed-runtime guidance,
rebuild generated payloads, document the implemented trust model, prove update
and safe repair, and block public release when the proof is incomplete.

### Users
- Claude Code users installing SpecKit Pro from the public marketplace.
- Codex users installing the generated Codex payload and bundled custom agents.
- Maintainers who need release-readiness gates that block incomplete payloads,
  stale install surfaces, unsafe public claims, or missing native UAT evidence.
- Reviewers who need clear evidence that XPLAT-003, XPLAT-006, and XPLAT-007
  handoffs are enforced in the installed plugin path.

### User Stories
1. As a Claude or Codex user on native Windows, macOS, or Linux, I can install
   SpecKit Pro and run the first-use scaffold/status/autopilot-dry-run journey
   without Bash, Git Bash, WSL, PowerShell-specific commands, or `jq`.
2. As a release maintainer, I can rebuild and verify generated Claude and Codex
   payloads from source, including version metadata, bundled agents, hooks,
   runner files, and XPLAT-003 manifest/checksum records.
3. As a maintainer, I can run doctor/update/autoheal checks that detect stale or
   incomplete installs, safely repair trusted gaps, and provide exact manual
   remediation for unsafe gaps.
4. As a reviewer, I can inspect filled native UAT runbooks and public docs that
   match the implemented support and consumer-trust model.

### Constraints
- Follow the design concept decisions in
  `docs/ai/specs/.process/XPLAT-008-design-concept.md`.
- Use Python 3.11+ standard-library runner behavior as the installed-runtime
  substrate.
- Active installed-runtime surfaces must not rely on Bash, `.sh`, `jq`, shell
  interpolation, Git Bash, WSL, or PowerShell-specific command language.
- No-shell/no-jq guards apply to active runtime paths, generated payloads, and
  release gates. Archive/provenance text, CI dispatch glue, and upstream Spec
  Kit generated bash helpers are out of scope.
- Public docs and release notes must not claim native support before the UAT
  matrix passes and must not claim cryptographic guarantees beyond XPLAT-003's
  implemented controls.
- Safe autoheal must be bounded to trusted missing or stale artifacts; unsafe
  gaps must print manual remediation.

### Out of Scope
- Creating child specs during setup.
- Replacing GitHub Actions YAML or minimal CI dispatch glue that only invokes
  Python gates and contains no validation, packaging, install, or runtime logic.
- Changing GitHub Spec Kit's generated `.specify/scripts/bash/` helpers in
  consumer projects.
- Rewriting archive/provenance history solely to remove old Bash wording.
- Claiming cryptographic guarantees that were not implemented.
```

### Specify Results

| Metric | Value |
|---|---|
| Functional Requirements | 22 |
| User Stories | 4 |
| Acceptance Criteria | 12 |

### Files Generated

- [x] `specs/xplat-008-claude-codex-cutover-universal-install-release-gate/spec.md`
- [x] `specs/xplat-008-claude-codex-cutover-universal-install-release-gate/checklists/requirements.md`

### SpecKit Traceability Markers

Use these markers in `spec.md` for traceability through later phases:

| Marker | Purpose |
|---|---|
| `[US1]`, `[US2]`, `[US3]`, `[US4]` | User story references for installed first-use, payload gates, repair/update, and release evidence |
| `[FR-001]` | Functional requirement reference |
| `[NEEDS CLARIFICATION]` | Flag for Clarify phase; none should remain after G2 |
| `[P]` | Parallel-safe task marker |
| `[Gap]` | Missing coverage item from checklists or analyze |

---

## Phase 2: Clarify

**When to run:** After Specify, before Plan. XPLAT-008 has platform, payload,
repair, and public-claim ambiguity that should be resolved before tasks are
generated.

### Clarify Prompts

#### Session 1: Active Surface Inventory

```text
$speckit-clarify

Focus on active installed-runtime inventory for XPLAT-008:
- Classify each `speckit-pro/skills/**`, `speckit-pro/codex-skills/**`,
  `speckit-pro/agents/**`, `speckit-pro/codex-agents/**`,
  `speckit-pro/hooks/hooks.json`, `speckit-pro/codex-hooks.json`,
  install guidance, generated payload file, and release gate as active runtime,
  docs surface, release gate, archive/provenance, CI dispatch glue, or upstream
  Spec Kit helper.
- Identify which active surfaces currently mention Bash, `.sh`, `jq`, shell
  interpolation, Git Bash, WSL, PowerShell, or Unix-only paths.
- Decide the required direct Python runner invocation contract for each active
  installed-runtime surface.
```

#### Session 2: Payload, Release, and Trust Contract

```text
$speckit-clarify

Focus on generated payload and release-readiness contracts for XPLAT-008:
- Define the expected Claude and Codex payload inventory: version, skills,
  agents, hooks, runner files, manifest/checksum metadata, and install
  guidance.
- Decide how release-readiness gates compare source against
  `dist/claude/speckit-pro/**` and `dist/codex/speckit-pro/**`.
- Identify the exact XPLAT-003 trust claims that public docs and release notes
  may state after implementation.
- Specify which stale metadata, incomplete payload, or unsupported claim should
  block release.
```

#### Session 3: UAT, Update, and Autoheal

```text
$speckit-clarify

Focus on native installed-plugin UAT, update, and safe repair for XPLAT-008:
- Define the durable UAT runbook path and required Claude/Codex rows for native
  Windows, macOS, and Linux.
- Specify install, bundled-agent verification, first use, scaffold/status,
  autopilot dry-run, latest-tag update, incomplete-install repair, and expected
  result fields.
- Decide interpreter discovery order and failure messaging for Windows,
  macOS, and Linux installed plugin caches.
- Define which install gaps can be autohealed from trusted checksums and which
  must print manual remediation only.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---|---|---|---|
| 1 | Active surface inventory | 5 | Accepted active-runtime guard scope, argv-style runner invocation, source-derived payload manifest, feature-local UAT matrix, and bounded autoheal trust boundary; consensus refined interpreter discovery to Windows `py -V:3` -> `py -3` -> `python` -> `python3`, macOS/Linux `python3` -> `python` |
| 2 | Payload/release/trust contract | 5 | Accepted source-derived Claude/Codex payload inventory, temp/staging rebuild comparison with explicit transforms, blocking version consistency across source/dist/marketplace/release evidence, seeded release blockers, and implemented-only trust/support claims |
| 3 | UAT/update/autoheal | 5 | Accepted feature-local `.process/uat-matrix.md` plus optional detail files, six Claude/Codex by platform rows with install-to-repair fields, structured matrix fill-state release gate, prior interpreter discovery order with diagnostics, and checksum-backed repair only |

### Consensus Resolution Log

| # | Type | Question/Gap/Finding | Categories | Round | Outcome | Resolution | Analysts Used |
|---|---|---|---|---|---|---|---|
| 1 | Clarify | Per-platform interpreter discovery order | [codebase, domain] | 1 | both-agree with refinement | Use argv-style probing; Windows `py -V:3` -> `py -3` -> `python` -> `python3`, macOS/Linux `python3` -> `python`; accept only Python >=3.11 and record executable/version | codebase-analyst, domain-researcher |
| 2 | Clarify | Real installed-cache repair boundary | [codebase, security] | 1 | 3/3 | Enable automatic repair only for bounded manifest/checksum-backed refreshes; unsafe drift remains manual remediation | codebase-analyst, spec-context-analyst, domain-researcher |
| 3 | Clarify | Public trust and support claim boundary | [codebase, spec-context, domain] | 2 | 3/3 | Claim only implemented and verified controls; deny signing, SBOMs, provenance attestations, reproducible-build guarantees, audits/certifications, vulnerability-free status, marketplace-enforced verification, and cryptographic trust-chain claims unless separately implemented and evidenced | codebase-analyst, spec-context-analyst, domain-researcher |
| 4 | Clarify | Structured native UAT matrix and repair boundary | [codebase, spec-context, domain] | 3 | 3/3 | Require six Claude/Codex by Windows/macOS/Linux rows in `.process/uat-matrix.md`; gate missing, placeholder, smoke-only, failing, or unsupported-claim rows; limit autoheal to bounded checksum-backed installed-cache refreshes and route unsafe drift to exact manual remediation | codebase-analyst, spec-context-analyst, domain-researcher |
| 5 | Checklist | Integration README guidance scope | [codebase] | 1 | agree | Keep root `README.md` and `speckit-pro/README.md` in public install/update/trust/support guidance scope, limited to active public claims rather than unrelated README prose | codebase-analyst |
| 6 | Checklist | Security install-health repair schema binding | [domain] | 1 | gap-remediated | Tightened `install-health-repair.schema.json` so trusted autoheal records require non-null source identity, release channel/tag, expected digest, and safe paths; unsafe findings require manual remediation rather than autoheal | domain-researcher |
| 7 | Checklist | Reliability runtime/update/repair coverage | [codebase] | 1 | agree | No missed reliability gap found across interpreter diagnostics, update proof, doctor/autoheal outcomes, native UAT rows, or installed-cache failure messaging | codebase-analyst |
| 8 | Checklist | Release-readiness blocker coverage | [spec-context] | 1 | agree | No missed pre-Tasks release blocker found across payload completeness, stale metadata, public claims, UAT matrix, update/repair evidence, PR traceability, or nondeterministic/stale `dist/**` output | spec-context-analyst |

---

## Phase 3: Plan

**When to run:** After spec and clarification are approved. Output:
`specs/xplat-008-claude-codex-cutover-universal-install-release-gate/plan.md`.

### Plan Prompt

```text
$speckit-plan

## Tech Stack
- Runtime substrate: Python 3.11+ standard-library runner via
  `speckit-pro/speckit_pro_runner/`.
- Plugin surfaces: Claude skills/agents/hooks under `speckit-pro/skills/`,
  `speckit-pro/agents/`, and `speckit-pro/hooks/hooks.json`; Codex skills,
  agents, and hooks under `speckit-pro/codex-skills/`,
  `speckit-pro/codex-agents/`, and `speckit-pro/codex-hooks.json`.
- Generated payloads: `dist/claude/speckit-pro/**` and
  `dist/codex/speckit-pro/**`, rebuilt from source.
- Public docs: Astro/Starlight docs under `docs-site/src/content/docs/**`.
- Verification: Python runner gates, Layer 1 structural validation, focused
  Layer 4 tests, docs validation where docs change, payload completeness gate,
  active-runtime no-shell/no-jq guard, release-readiness guard, and manual UAT
  runbooks.

## Constraints
- Preserve the accepted three-slice strategy from
  `docs/ai/specs/.process/XPLAT-008-design-concept.md`.
- Record the setup reviewability warning and explain why three internal slices
  are sufficient unless Plan or Tasks proves child specs are required.
- Prefer direct Python runner invocation and explicit file inventories over
  broad abstractions or full reinstall behavior.
- Keep shell allowance narrow: archive/provenance text, CI dispatch glue, and
  upstream Spec Kit generated bash helpers only.
- Public docs must describe implemented support and the XPLAT-003 trust model
  without future-facing or cryptographic overclaims.

## Architecture Notes
- Slice 1 should establish active installed-runtime invocation and guard seeds
  before payload and UAT work.
- Slice 2 should rebuild generated payloads and add completeness/release/docs
  gates against the actual source-to-dist contract.
- Slice 3 should fill native UAT runbooks, prove latest-tag update and safe
  repair, and finalize release-readiness blocking behavior.
- Use the design concept Q&A as the source of truth for why child specs,
  shell dispatch, repo-wide purge, staged UAT, and full reinstall were rejected.
```

### Plan Results

| Artifact | Status | Notes |
|---|---|---|
| `plan.md` | Complete | Technical context, three-slice execution flow, constitution check, accepted reviewability warning, and projected implementation footprint |
| `research.md` | Complete | Direct runner invocation, interpreter discovery, active guard scope, payload contract, UAT evidence, bounded autoheal, and public trust wording decisions |
| `data-model.md` | Complete | Installed runtime surfaces, interpreter records, payload inventory/results, native UAT rows, repair actions, and release gate records |
| `contracts/` | Complete | Five JSON schemas: runner invocation, payload completeness, release-readiness, UAT matrix, and install health/repair |
| `quickstart.md` | Complete | Maintainer workflow for three implementation slices, verification commands, UAT/update/repair evidence, and final release gate |

---

## Phase 4: Domain Checklists

**When to run:** After Plan. Validate both `spec.md` and `plan.md`.

### Recommended Domains

1. **integration** - Active Claude/Codex installed surfaces, generated payloads,
   runner invocation, release gates, and docs must agree on one runtime path.
2. **security** - Public trust claims, manifest/checksum metadata, install-cache
   repair, and no overclaiming need requirement-level validation.
3. **reliability** - Update, doctor, autoheal, platform interpreter discovery,
   and safe failure messaging are release-critical.
4. **release-readiness** - This custom domain should validate payload
   completeness, UAT runbook fill state, public docs, and final publication
   blockers.

### Enriched Checklist Prompts

#### 1. Integration Checklist

```text
$speckit-checklist integration

Focus on XPLAT-008 requirements:
- Active Claude and Codex skills, agents, hooks, install guidance, generated
  payloads, and release gates invoke or validate the same Python runner path.
- Source-to-dist payload rebuild requirements identify every required file and
  metadata record.
- Public docs, README guidance, and generated payload behavior are consistent.
- Pay special attention to: drift between source plugin surfaces and committed
  `dist/**` payloads.
```

#### 2. Security Checklist

```text
$speckit-checklist security

Focus on XPLAT-008 requirements:
- XPLAT-003 manifest/checksum metadata is included and validated where claimed.
- Autoheal only refreshes trusted missing or stale artifacts and never hides
  unsafe install-cache drift.
- Public docs and release notes avoid unimplemented cryptographic guarantees.
- Pay special attention to: consumer-trust wording that could overstate the
  implemented controls.
```

#### 3. Reliability Checklist

```text
$speckit-checklist reliability

Focus on XPLAT-008 requirements:
- Interpreter discovery and failure messaging are defined for native Windows,
  macOS, and Linux installed plugin caches.
- Update and repair paths have explicit success and failure outcomes.
- UAT runbooks cover install, first use, scaffold/status, autopilot dry-run,
  latest-tag update, and incomplete-install repair for both Claude and Codex.
- Pay special attention to: stale or incomplete installs that cannot be safely
  autohealed.
```

#### 4. Release-Readiness Checklist

```text
$speckit-checklist release-readiness

Focus on XPLAT-008 requirements:
- Release-readiness gates block active shell runtime dependencies, incomplete
  generated payloads, missing bundled agents, stale version metadata, and
  incomplete UAT runbooks.
- UAT evidence is readable, filled, and release-reviewable with no placeholder
  rows or empty expected-result fields.
- Docs and release notes match the implemented support matrix and trust model.
- Pay special attention to: release paths that pass source-checkout gates but
  fail installed-plugin proof.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|---|---|---|---|
| integration | 20 | 1 found, 1 remediated | FR-001-FR-005, FR-009-FR-011, FR-019, FR-020, SC-001-SC-005, SC-007-SC-008 |
| security | 20 | 0 initial; 1 consensus gap remediated | FR-007, FR-011, FR-016-FR-017, FR-019, SC-005-SC-007 |
| reliability | 20 | 0 | FR-012-FR-018, SC-001, SC-004, SC-006 |
| release-readiness | 20 | 0 | FR-007-FR-008, FR-014, FR-019-FR-021, SC-003-SC-008 |
| Total | 80 | 1 found and remediated during checklist execution; 1 consensus gap remediated | FR-001-FR-022, SC-001-SC-008 |

---

## Phase 5: Tasks

**When to run:** After checklists complete and true gaps are resolved. Output:
`specs/xplat-008-claude-codex-cutover-universal-install-release-gate/tasks.md`.

### Tasks Prompt

```text
$speckit-tasks

## Task Structure
- Organize tasks by the accepted three slices, not by broad technical layer.
- Every task should reference user stories and functional requirements from
  `spec.md`.
- Mark parallel-safe tasks with [P] only when file ownership and dependencies
  are actually independent.
- Include tests or deterministic verification before changing active runtime
  guidance, payloads, docs, or release-readiness gates.

## Required Slice Ordering
1. Active installed-runtime surface cutover:
   - Inventory and classify active Claude/Codex runtime surfaces.
   - Wire direct Python runner invocation and interpreter discovery.
   - Seed active-runtime no-shell/no-jq guard coverage.
2. Payload, release, and docs gates:
   - Rebuild generated Claude and Codex payloads from source.
   - Add payload completeness and release-readiness gates.
   - Update public install, first-run, troubleshooting, security/trust, README,
     and release-note guidance to match implemented controls.
3. Native UAT, update, and safe repair:
   - Fill release-reviewable UAT runbooks for Claude and Codex on native
     Windows, macOS, and Linux.
   - Prove latest-tag update behavior.
   - Prove safe doctor/autoheal repair for trusted gaps and exact manual
     remediation for unsafe gaps.

## Constraints
- Reference `docs/ai/specs/.process/XPLAT-008-design-concept.md`, `spec.md`,
  and `plan.md` in task-generation rationale.
- Use Non-goals to avoid child-spec setup, shell wrappers, repo-wide historical
  purge, future-facing claims, smoke-only UAT, or full reinstall behavior.
- Keep generated payload tasks tied to source rebuild commands and completeness
  gates; do not hand-edit `dist/**` as source of truth.
```

### Tasks Results

| Metric | Value |
|---|---|
| Total Tasks | 47 |
| Phases | 4 implementation phases across the accepted three slices plus polish/release packet |
| Parallel Opportunities | 15 `[P]` tasks |
| User Stories Covered | 4 (`US1`-`US4`) |

---

## Atomicity Route

After Tasks, run the read-only atomicity classifier and record the decision here.
This route is intentionally blank during scaffold.

| Field | Value | Meaning |
|---|---|---|
| Route | `one-navigable-PR` | One coherent PR with ordered review sections and release gate evidence |
| Releasable | `true` | No destructive migration or concurrency-sensitive cutover detector fired |
| Signals | `change-shape:modify-heavy` | Modify-heavy cross-surface release-readiness work |
| Warnings | none | Atomicity classifier returned no release-safety warnings |

To produce the decision:

```text
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/xplat-008-claude-codex-cutover-universal-install-release-gate
```

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch drift before
implementation.

### Analyze Prompt

```text
$speckit-analyze

Focus on XPLAT-008 cross-artifact consistency:
1. Constitution alignment: plugin structure, no manual version edits, test
   coverage, conventional commits, and KISS/YAGNI.
2. Design concept drift: confirm spec, plan, tasks, and checklists preserve the
   accepted three-slice strategy, active surfaces first, direct Python runner,
   active-runtime guard scope, payload rebuild/gate boundary, implemented-only
   public claims, full UAT matrix, and safe autoheal behavior.
3. Prior XPLAT handoffs: verify XPLAT-003 trust metadata, XPLAT-006 install
   inventory/doctor proof, and XPLAT-007 Python gates are reused rather than
   reinvented.
4. Release-readiness gaps: ensure payload completeness, bundled agents, hooks,
   runner files, version metadata, public docs, update, autoheal, and UAT
   runbooks all have tasks and objective acceptance checks.
5. Guard boundary: flag any task that rewrites archive/provenance history or
   upstream Spec Kit generated bash helpers solely to satisfy active-runtime
   no-shell goals.
```

### Analyze Severity Levels

| Severity | Meaning | Action Required |
|---|---|---|
| CRITICAL | Blocks implementation, violates constitution, or breaks release-readiness proof | Must fix before G6 gate |
| HIGH | Significant gap that could invalidate installed-plugin proof | Should fix before implementation |
| MEDIUM | Improvement opportunity or ambiguity | Review and decide |
| LOW | Minor inconsistency | Note for future |

### Analysis Results

| ID | Severity | Issue | Resolution |
|---|---|---|---|
| A1 | HIGH | `uat-matrix.schema.json` required six rows but did not enforce the exact Claude/Codex by Windows/macOS/Linux row set required by FR-012, Clarify Session 3, Research Decision 7, and release-readiness CHK011 | Added one-and-only-one `contains`/`minContains`/`maxContains` constraints for all six product/platform rows |
| A2 | HIGH | `release-readiness.schema.json` allowed string evidence references to substitute for the structured aggregate payload/UAT/repair/public-claim records described by the data model and T018 | Replaced required string-only `evidence` with structured `payload_results`, `uat_rows`, `repair_actions`, `public_claim_results`, `runner_invocations`, and `traceability`; retained optional `evidence_refs` |
| A3 | MEDIUM | `PayloadCompletenessResult` in `data-model.md` used `expected_items` and omitted `actual_files`, while the payload contract and release-readiness aggregate use expected/actual generated file records | Renamed the field to `expected_files` and added required `actual_files` |
| A4 | LOW | `RunnerInvocationRecord.operation` in `data-model.md` used `autopilot_dry_run`, while runner operation values and the runner invocation schema use hyphenated operation IDs | Aligned the operation enum to `autopilot-dry-run`; kept the UAT row field `autopilot_dry_run` unchanged |
| A5 | MEDIUM | Analyze consensus found `runner_invocations` was required by `release-readiness.schema.json` but missing from the `ReleaseReadinessGateRecord` data model, and the embedded release-readiness runner invocation shape drifted from the standalone runner invocation contract | Added `runner_invocations` to the data model, aligned the embedded release-readiness runner invocation shape to `runner-invocation.schema.json`, and added `runner_invocation_ids` links to UAT rows |

---

## Phase 6.5: Confidence Gate

**When to run:** After Analyze and before implementation. The Analyze consensus
step must emit the canonical pre-Implement confidence block that
`confidence-gate.sh` reads.

📊 Confidence: 0.93

- Task understanding: 0.96
- Approach clarity: 0.93
- Requirements alignment: 0.94
- Risk assessment: 0.91
- Completeness: 0.92

### Confidence Gate Prompt

```text
Run the pre-Implement confidence gate for XPLAT-008 in advisory mode:

bash speckit-pro/skills/speckit-autopilot/scripts/confidence-gate.sh \
  docs/ai/specs/.process/XPLAT-008-workflow.md \
  --threshold 0.90 \
  --mode advisory

Record the result in this workflow and in `autopilot-state.json`. If no data is
available, log the missing emit and continue because the default mode is
advisory. If a score is below threshold, record the lowest criterion before
Phase 7 starts.
```

### Confidence Gate Results

| Metric | Value |
|---|---|
| Mode | advisory |
| Threshold | 0.90 |
| Composite Score | 0.93 |
| Lowest Criterion | Risk assessment 0.91 |
| Decision | Pass; proceed to Phase 7 |

---

## Phase 7: Implement

**When to run:** After tasks and analysis are approved.

### Implement Prompt

```text
$speckit-implement

## Approach: TDD-First

For each task, follow this cycle:
1. RED: Add or update the failing test, fixture, payload gate, docs check, UAT
   fill-state check, or release-readiness assertion that defines expected
   behavior.
2. GREEN: Implement the smallest source change that makes the check pass.
3. REFACTOR: Remove active shell runtime paths and simplify duplicated logic
   while tests still pass.
4. VERIFY: Run focused gates, then broader deterministic gates before PR.

## Pre-Implementation Setup

1. Verify the active branch is
   `codex/xplat-008-claude-codex-cutover-universal-install-release-gate`.
2. Read `docs/ai/specs/.process/XPLAT-008-design-concept.md`, `spec.md`,
   `plan.md`, and `tasks.md`.
3. Run the current Python gate baseline before editing:
   `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-default-suite.json`.
4. Use focused tests for each active runtime, payload, docs, UAT, update, and
   repair change before running the broader suite.

## Implementation Notes

- Keep source plugin files as the source of truth; rebuild generated payloads
  rather than hand-editing `dist/**`.
- Treat public docs as release evidence: update them only to claims backed by
  implementation and UAT.
- Keep autoheal bounded to trusted missing or stale artifacts. Unsafe gaps must
  produce exact manual remediation.
- Preserve archive/provenance text unless an active release gate consumes it.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|---|---|---|---|
| Slice 1 - Active surface cutover | Fill after Tasks | 0 | Pending |
| Slice 2 - Payload/release/docs gates | Fill after Tasks | 0 | Pending |
| Slice 3 - UAT/update/autoheal | Fill after Tasks | 0 | Pending |
| Polish and release packet | Fill after Tasks | 0 | Pending |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in `tasks.md`
- [ ] Spec index check passes:
  `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"`
- [ ] Python runner default suite passes:
  `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-default-suite.json`
- [ ] Active-runtime no-shell/no-jq guard passes
- [ ] Generated Claude and Codex payload completeness gates pass
- [ ] Release-readiness guard passes
- [ ] Docs validation passes when docs-site files change
- [ ] Native Windows/macOS/Linux Claude and Codex UAT runbooks are filled and readable
- [ ] Latest-tag update proof is recorded
- [ ] Safe repair/autoheal proof is recorded
- [ ] PR packet includes summary, affected plugin paths, test commands, and UAT evidence

### Canonical Post Items

| Item | Status | Notes |
|---|---|---|
| Post: Doctor Extension Check | Pending | Run or skip with explicit extension evidence |
| Post: Verify Implementation | Pending | Run or skip with explicit extension evidence |
| Post: Verify Tasks Phantom Check | Pending | Run or skip with explicit extension evidence |
| Post: Code Review | Pending | Independent diff review before PR creation |
| Post: Integration Suite | Pending | Full deterministic verification after implementation |
| Post: Reviewability Diff Gate | Pending | Final diff gate before PR packet generation |
| Post: Self-Review | Pending | Four-question audit before UAT runbook generation |
| Post: UAT Runbook Generation | Pending | Generate and author the feature UAT runbook |
| Post: PR Body Generation | Pending | Generate and validate the PR packet/body |
| Post: PR Creation | Pending | Push branch and open the PR from packet fields |
| Post: Review Remediation | Pending | Monitor and resolve review feedback |
| Post: Retrospective | Pending | Final post item; run or skip with explicit extension evidence |

---

## Project Structure Reference

```text
racecraft-plugins-public/
|-- speckit-pro/
|   |-- skills/
|   |-- codex-skills/
|   |-- agents/
|   |-- codex-agents/
|   |-- hooks/
|   |-- codex-hooks.json
|   `-- speckit_pro_runner/
|-- dist/
|   |-- claude/speckit-pro/
|   `-- codex/speckit-pro/
|-- docs-site/src/content/docs/
|-- docs/ai/specs/.process/
|-- specs/xplat-008-claude-codex-cutover-universal-install-release-gate/
`-- tests/speckit-pro/
```

---

Template based on the shared SpecKit workflow template at
`skills/speckit-coach/templates/workflow-template.md`, populated for XPLAT-008
with roadmap scope and setup Grill Me decisions.
