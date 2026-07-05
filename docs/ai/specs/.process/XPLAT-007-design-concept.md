# Design Concept: XPLAT-007 Python Tooling and Release-Gate Migration

**Spec ID:** XPLAT-007
**Spec Name:** Python Tooling and Release-Gate Migration
**Branch:** `codex/xplat-007-python-tooling-and-release-gate-migration`
**Created:** 2026-07-04
**Source Roadmap:** `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`

## Setup Context

XPLAT-007 starts after XPLAT-004 shipped the Python 3.11+ standard-library
runner foundation, XPLAT-005 shipped read-only helper ports, and XPLAT-006
shipped mutation helper contracts, install inventory/doctor proof, generated
PR-body output, deferred command-plan diagnostics, and Layer 4
mutation-helper gates.

The roadmap marks XPLAT-007 ready after XPLAT-006 and assigns it the active
repo-local migration work that must happen before active Claude/Codex cutover:
tests, evals, payload builders, install-verification scripts, release checks,
release-readiness gates, and active helper tooling must move to Python
standard-library commands. XPLAT-008 remains responsible for active
Claude/Codex skill, hook, install-guidance, generated release payload, public
docs, native installed-plugin UAT, update, autoheal, and public release claims.

The setup reviewability gate returned `status=warn`, `pass=true`,
`reviewable_loc=250`, `production_files=4`, `total_files=10`, and warned that
two primary surfaces (`docs/process` and `harness/adapter`) exceed the
one-surface warning threshold. The accepted setup direction is one XPLAT-007
workflow with three internal implementation slices.

## Goals

- Replace active repo-local Bash-backed tests, evals, helper tooling, payload
  builders, install-verification scripts, release checks, and
  release-readiness gates with Python 3.11+ standard-library commands.
- Make the runner module command surface the primary entrypoint for migrated
  repo-local gates where practical, reusing the XPLAT runner contracts and
  helper registry instead of adding unrelated command families.
- Establish Python-authoritative verification for Layer 1 structural checks,
  Layer 4 helper tests, AI-eval runners, tool-scoping checks,
  integration/parity suites, payload/release helpers, install verification, and
  the top-level test runner.
- Use golden fixtures plus source-checkout Bash-reference comparisons while
  each gate is being migrated; promote Python as authoritative only after
  parity is accepted.
- Add deterministic guardrails that fail if active build, test, eval, payload,
  install-verification, repository-helper, or release-readiness paths still
  require Bash, `.sh`, `jq`, Git Bash, WSL, PowerShell helper scripts, shell
  interpolation, or shell-only parsing.
- Remove active repo-local Bash command paths after Python replacements are
  accepted. Preserve only inactive historical/parity evidence when needed for
  provenance and reviewability.
- Rebuild test payloads as migration evidence, but do not perform generated
  release-payload cutover or active Claude/Codex invocation switching.
- Keep platform proof to source-checkout fixtures, Windows-style path fixtures,
  and local macOS smoke. Native installed-plugin UAT remains XPLAT-008.

## Non-Goals

- Do not update active Claude Code or Codex skill invocation paths, hook
  behavior, install guidance, public docs, release notes, or public platform
  support claims.
- Do not rebuild or publish release payloads for active Claude/Codex cutover.
  XPLAT-007 may rebuild test payloads as evidence only.
- Do not run full native Windows/macOS/Linux installed-plugin UAT.
- Do not change GitHub Spec Kit's generated `.specify/scripts/bash/` helpers in
  consumer projects.
- Do not rewrite historical/archive provenance solely to remove prior Bash
  mentions. The active-code-only boundary means current executable paths move;
  archive history can remain unless it is used by an active gate.
- Do not treat a thin local Bash wrapper as an acceptable transition state for
  active repo-local commands.

## Accepted Slice Strategy

| Slice | Focus | Acceptance Boundary |
|---|---|---|
| Slice 1 | Test/eval runner gates | Port the top-level runner and active Layer 1, Layer 4, AI-eval, tool-scoping, integration, and parity gates to Python commands; keep Bash comparison only as migration evidence until promotion |
| Slice 2 | Payload, install, and release helpers | Port payload builders, local plugin refresh, marketplace/version sync, install verification, and release-readiness checks to Python commands; rebuild test payloads only |
| Slice 3 | Active-path guardrails and cleanup | Add deterministic no-shell/no-jq active-path guards, remove active Bash command paths, verify remaining shell is not used by active repo-local gates, and record XPLAT-008 handoff gaps |

Split into child specs only if Specify, Plan, or Tasks proves these three
slices cannot stay within the roadmap reviewability budget.

## Grill Me Q&A Log

### Q1. How should XPLAT-007 be sliced for reviewability?

**Accepted answer:** One workflow, three slices.

Use one XPLAT-007 workflow and branch, but separate review order into
test/eval runner gates, payload/install/release helper migration, and active
shell guardrails/cleanup.

### Q2. Which XPLAT-007 slice should come first?

**Accepted answer:** Test/eval runner gates.

Port the active test runner and Layer gates first so later payload and release
work has a Python-authoritative verification base.

### Q3. What should be the primary Python command surface for migrated gates?

**Accepted answer:** Runner module commands.

Expose repo-local gates through `python -m speckit_pro_runner` operations where
practical, reusing existing contracts and helper registry. If planning proves a
small standalone Python command is safer for a release/build helper, the plan
must justify it and keep the public command shape Python-only.

### Q4. What parity bar should XPLAT-007 require before replacing a Bash gate?

**Accepted answer:** Python plus Bash comparison.

Use golden fixtures and source-checkout Bash-reference comparisons until Python
is promoted as authoritative for each migrated gate. After promotion, Bash
comparison moves out of active release gates or remains only as inactive
historical evidence.

### Q5. What shell usage should remain allowed after XPLAT-007?

**Accepted answer:** No shell anywhere for active repo-local command paths.

The workflow should target zero active repo-local shell scripts or
shell-specific command paths. If platform tooling has unavoidable shell runner
mechanics, those mechanics must invoke Python directly and contain no
validation, packaging, install, release, or runtime logic. This is stricter
than the roadmap's minimum CI-dispatch allowance.

### Q6. Which payload and release tooling should XPLAT-007 include?

**Accepted answer:** Full repo-local release gates.

Include payload build tooling, local plugin refresh, marketplace/version sync,
install verification, and release-readiness checks inside XPLAT-007.

### Q7. How should XPLAT-007 handle generated Claude/Codex payloads?

**Accepted answer:** Rebuild test payloads.

Generate or refresh test payloads as migration evidence, but leave generated
release payload rebuilds, active payload selection, and installed plugin cutover
to XPLAT-008.

### Q8. What platform proof belongs in XPLAT-007?

**Accepted answer:** Source-checkout fixtures plus local smoke.

Use deterministic Windows-style path fixtures and local macOS source-checkout
smoke. Installed-cache launch proof and native Windows/macOS/Linux matrix UAT
remain XPLAT-008.

### Q9. What should happen to existing Bash scripts once Python replacements are accepted?

**Accepted answer:** Delete active references and update active docs only if
they are part of active gate evidence.

The first answer asked to delete all references and update documentation, but
the follow-up historical-boundary answer narrowed the scaffold to active code
only. Use the latest answer as controlling: remove active Bash command paths and
defer broad public documentation cleanup to XPLAT-008 unless a current repo-local
gate or maintainer runbook must change for XPLAT-007 verification.

### Q10. Should XPLAT-007 rewrite historical/archive Bash references too?

**Accepted answer:** Active code only.

Do not rewrite archive/provenance history solely for wording. Historical Bash
mentions can remain when they are not active command paths and not used by
release-readiness gates.

## Open Questions For Clarify

- Exact gate inventory: which files under `tests/speckit-pro/**`,
  `scripts/**`, `speckit-pro/skills/**/scripts/**`,
  `speckit-pro/codex-skills/**/scripts/**`, `speckit-pro/scripts/**`, and
  `.github/workflows/**` are active release gates, temporary parity fixtures,
  inactive historical evidence, or XPLAT-008 cutover surfaces?
- Runner command taxonomy: which migrated commands should be registry-backed
  `python -m speckit_pro_runner` operations, and which, if any, need narrowly
  justified standalone Python commands?
- Bash comparison retirement rule: for each migrated gate, what exact fixture
  and comparison evidence promotes Python as authoritative and allows the Bash
  reference to leave active gates?
- No-shell guard definition: how should the active-path guard distinguish
  active repo-local command paths from archive/provenance text, vendored
  Spec Kit consumer helpers, and CI platform mechanics?
- Test payload boundary: which generated payload fixtures should be rebuilt as
  evidence without creating a release-payload cutover or public support claim?
- Documentation boundary: which active maintainer docs/runbooks must change so
  XPLAT-007 commands are usable, while public install/runtime docs stay for
  XPLAT-008?
- Platform proof boundary: which local smoke commands and Windows-style path
  fixtures prove source-checkout Python gates without implying installed-cache
  native UAT?

## Downstream Handoff

- XPLAT-008 should receive Python-authoritative repo-local gates, release
  helpers, install-verification checks, payload-builder commands, active-path
  Bash/jq guardrails, and test payload evidence from XPLAT-007.
- XPLAT-008 remains responsible for active Claude/Codex skill, agent, hook,
  generated release payload, install guidance, public docs, release notes,
  installed-cache launch proof, native Windows/macOS/Linux UAT, update, safe
  repair, autoheal, and public release readiness.
