# feat(g56r-005): Add model availability fallback and recovery simulation

## Summary

<!-- speckit-pro-editable:summary:start -->
Adds deterministic Codex-local evidence for model availability fallback, service reroute attribution, bounded recovery, and fake-home safety, plus a manual-UAT remediation for safe static review-artifact titles.
<!-- speckit-pro-editable:summary:end -->

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Added closed schemas, a reviewed source-roster-bound scenario corpus, a pure resolver, reroute attribution/scoring, fake-home recovery, and bounded sequential execution.
- Added 33 focused feature tests and repository suite registration.
- Added safe static document-title fill slots to the four draft-stage templates and updated both Claude and Codex artifact authors to forbid repository-derived title scripts.
- Recorded manual browser and behavioral UAT, regenerated the four G56R-005 pages, shipped payloads, references, and spec index.
<!-- speckit-pro-editable:what_changed:end -->

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
G56R-006 can build production routing against deterministic fail-closed evidence, while reviewers receive correct no-JavaScript metadata without violating the gallery's generated-content safety contract.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

- Review the route-policy and report schemas, corpus, resolver, and focused tests.
- Review the document-title fill-region regression and Claude/Codex artifact-author rules.
- Open the four generated HTML artifacts and inspect the manual UAT runbook.
- Confirm the generated payload, reference, spec-index, and release-consistency evidence.

## How To UAT

Follow specs/g56r-005-model-availability-fallback-recovery/.process/uat-runbook.md. It covers all four HTML pages at desktop and mobile widths, theme/disclosure/copy interactions, preferred/fallback routing, service reroute scoring, fake-home rollback, bounded execution, and deterministic replay.

## UAT Runbook

Follow specs/g56r-005-model-availability-fallback-recovery/.process/uat-runbook.md. It covers all four HTML pages at desktop and mobile widths, theme/disclosure/copy interactions, preferred/fallback routing, service reroute scoring, fake-home rollback, bounded execution, and deterministic replay.

## Verification

- Manual browser and deterministic behavioral UAT passed after UAT-001 remediation; zero findings remain open.
- Static-title fill-region contract passed 90/90; artifact gallery validation passed 587/587.
- Focused G56R-005 fallback-recovery suite passed 33/33.
- Full deterministic suite passed 7663/7663: L1 1469, L4 6002, L5 192.
- Docs reference, spec index, release-artifact consistency, and git diff checks pass.

## Scope

- Deterministic G56R-005 contracts, fixtures, simulation runtime, focused tests, and planning evidence.
- Artifact-generation remediation limited to four draft templates, Claude/Codex artifact-author instructions, generated pages, and required shipped payloads.

## Known Gaps

- The Codex task/worktree binding bug remains tracked as TODO-CODEX-WORKTREE-BINDING and is outside G56R-005 feature behavior.
- Live model/service reroute smoke was intentionally not run because this spec makes no live availability claim.
