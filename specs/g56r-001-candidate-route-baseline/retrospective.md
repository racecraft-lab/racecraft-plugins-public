---
feature: G56R-001
branch: g56r-001-candidate-route-baseline
date: 2026-07-16
completion_rate: 100
spec_adherence: 100
critical_findings: 0
---

# Retrospective: G56R-001 Candidate Route Baseline

## Executive Summary

G56R-001 originally completed as a documentation-only research spike with one
canonical report. The 2026-07-16 evidence-parity amendment preserves that
report and adds one schema-v2 planning manifest governed by the shared CAR/G56R
contract. Neither phase changes runtime, agent, installer, payload, cache,
fixture payload, platform-specific/runtime schema, helper script, generated
artifact, or version behavior.

## 2026-07-16 Evidence-Parity Amendment

- Revalidated 21 current official OpenAI documentation pages across the shared
  research matrix and recorded canonical URLs, timestamps, body hashes, bounded
  extracts, and claim bindings.
- Added a schema-v2 Codex planning manifest with the same structure as CAR-001:
  12 role contracts, 23 candidate routes, 12 fixtures, and complete
  traceability and decision records.
- Preserved all 25 legacy source facts with explicit dispositions. The two
  Apps-SDK-scoped facts remain historical but are withdrawn as Codex route
  authority because their source is outside the strict Codex allowlist.
- Kept all candidates provisional and all runtime capability, qualification,
  preference, and fallback claims deferred.
- Validation passed: parity validator 8/8, Layer 1 1428/1428, full suite
  2811/2811, and docs reference pages current.

## Requirement Coverage

| Area | Result |
|---|---|
| Official-source ledger | Complete; 9 records |
| Effort-surface records | Complete; 5 records |
| Project-input inventory | Complete; 16 stable records |
| Role contracts | Complete; 12 records |
| Candidate route records | Complete; 23 provisional, comparator, and parity records |
| Fixture backlog | Complete; 3 current and 9 missing records |
| G56R-002 handoff | Complete; capability questions, telemetry needs, invalidation rules, and strict go/no-go decision |
| No-runtime boundary | Preserved |
| Current schema-v2 official-source ledger | Complete; 21 records |
| Historical dispositions | Complete; 25 of 25 legacy facts |
| Shared structural parity | Complete; shared schema and record shape |

## Success Criteria Assessment

| Criterion | Result |
|---|---|
| SC-001 exact counts | Met |
| SC-002 source bindings | Met |
| SC-003 role contract fields | Met |
| SC-004 fixture counts and labels | Met |
| SC-005 go/no-go decision | Met |
| SC-006 unresolved marker search | Met |

## Architecture Drift

| Planned architecture | Actual result | Drift |
|---|---|---|
| One canonical implementation report under `docs/ai/research/` | One report created at `docs/ai/research/codex-agent-route-candidates.md`; the dated parity amendment adds one governed machine companion while preserving the report as canonical human evidence | Accepted packaging supersession; runtime production files remain zero |
| Planning artifacts under the feature directory | Feature specs, checklists, tasks, verify-tasks report, and retrospective remain under the feature directory | None |
| No runtime or payload changes | No runtime or payload changes were made; one unit-test guard allowlist admits the new research report path | None |

## Significant Deviations

The dependent PR diff is 25 docs/process/test-guard files rather than the
initial one-report implementation estimate. The expansion is intentional
review and evidence-parity remediation and remains within the documented
reviewability backstop because it adds no runtime, installer, payload, cache,
fixture payload, platform-specific/runtime schema, helper script, generated
artifact, or version changes.

## Process Notes

- Agent thread capacity was exhausted during earlier phases, so several
  executor and consensus steps ran in the parent session with explicit
  degradation notes.
- The full suite initially failed only because workflow state contained raw
  local path and agent-run identifiers. The state was redacted to symbolic
  labels, the focused privacy scan passed, and the full suite passed on rerun.
- RepoPrompt reviews later ran successfully through `rpce-cli` and returned
  findings. This branch remediates the report, workflow state, checklist set,
  roadmap, data model, contract, and verification records before the final
  clean review pass.

## Constitution Compliance

No constitution violations found.

## Proposed Spec Changes

Accepted and applied: replace the report-only packaging constraint with one
canonical human report plus one shared-schema planning manifest. No product
requirement, role contract, candidate boundary, or runtime scope changed.

## Lessons Learned

- For documentation-only specs, setup reviewability evidence should target the
  plan and declared implementation surface; post-review records also need an
  actual branch-diff backstop when remediation expands process files.
- Workflow state should avoid raw local paths and agent-run identifiers because
  repository privacy scanning treats them as sensitive.
- PR creation remains dependent on a packet-owned PR artifact; without that
  packet, autopilot must stop before GitHub side effects.

## Follow-Up

- G56R-002 should refresh official documentation before consuming this snapshot.
- Merge the shared evidence foundation PR #362 before dependent PR #360.
- Refresh official OpenAI documentation before G56R-002 consumes the manifest.
