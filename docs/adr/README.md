# Architecture decision records

Each record states one decision, why it was made, and what it changes. Records
are numbered in the order they were made. A later record can amend or replace
an earlier one; its status says so.

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-progress-without-host-task-tools.md) | Autopilot progress never uses host task-list tools | Accepted |
| [0002](0002-fix-vehicle-until-canary-green.md) | speckit-pro does not drive its own repair until the canary is green | Accepted |
| [0003](0003-host-parity-release-gate.md) | Codex parity is a release gate | Accepted |
| [0004](0004-retry-ladder.md) | The retry ladder replaces corrective budgets and replan epochs | Accepted |
| [0005](0005-formal-methods-and-verification-docker-are-opt-in.md) | Formal methods and verification docker are opt-in and never stop a run | Accepted |
| [0006](0006-advisory-reviewability.md) | Reviewability reports advise without blocking a run | Accepted |
| [0007](0007-quality-gates-scaffold-proposes-autopilot-defaults.md) | Scaffold proposes the quality-gates file; autopilot runs on unratified defaults without it | Accepted |
| [0008](0008-readiness-contract.md) | Scaffold owns readiness preparation; autopilot reads evidence without a setup stop | Accepted |
| [0009](0009-value-unit.md) | Every SPEC declares one value unit; outgrowing it is recorded, never a stop | Accepted |
| [0010](0010-stop-policy-enforcement.md) | The runner enforces the stop policy; only harm halts end a run early | Accepted |
| [0011](0011-security-interrupt.md) | Security interrupts require runner receipts and consent to one bounded action | Accepted |
| [0012](0012-blocked-for-uat.md) | Blocked-for-UAT preserves incomplete work and its evidence for human review | Accepted |
| [0013](0013-plan-approval-record.md) | Plan approval follows a human interview and binds the full planning revision | Accepted |
| [0014](0014-security-items-during-implement.md) | Implement skips security-blocked work and continues verified independent work | Accepted |
| [0015](0015-local-plan-approval-authority.md) | A protected local authority captures and enforces plan approval | Deferred; [ADR 0017](0017-recorded-plan-approval.md) covers plan approval for now |
| [0016](0016-canary-release-gate.md) | A private canary, weekly or on demand, gates every release | Accepted |
| [0017](0017-recorded-plan-approval.md) | The health program uses recorded plan approval; a protected authority is follow-on work | Accepted |
| [0018](0018-runner-phase-brief.md) | The runner briefs each planning phase; prose no longer drives dispatch | Accepted |
| [0019](0019-runner-builds-artifact-pages.md) | The runner builds artifact pages; a model writes only their prose | Accepted |
| [0020](0020-plan-stage-routing-uses-runner-rules.md) | Plan-stage routing uses runner rules; the decision model waits for HRNS-024 and HRNS-027 | Accepted |
| [0021](0021-one-planning-path.md) | Every SPEC takes one planning path, with each phase trimmed | Accepted |
| [0022](0022-consensus-for-security-and-low-confidence-only.md) | Plan-stage consensus runs only for security and low-confidence items | Accepted |
| [0023](0023-canary-plan-quality-and-target.md) | The canary checks plan quality and reports the plan-stage target | Accepted (amends ADR 0016) |
| [0024](0024-native-spec-kit-coverage.md) | Native Spec Kit v1.1.0 coverage: what speckit-pro adopts, rejects or defers | Accepted |
| [0025](0025-trigger-drafts-bind-at-check-time.md) | Bind trigger campaign templates at check time | Accepted |
| [0026](0026-plan-stage-phase-drivers.md) | Run each planning phase in a phase driver | Accepted |
| [0027](0027-canary-drives-the-real-scaffold-grill.md) | The canary drives the real scaffold grill through an operator agent | Accepted |
