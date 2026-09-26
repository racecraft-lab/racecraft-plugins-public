# SPEC Workflow

## Workflow Overview

| Phase | Command | Status | Notes |
|---|---|---|---|
| Specify | `$speckit-specify` | Pending | Pending |
| Clarify | `$speckit-clarify` | Pending | Pending |
| Plan | `$speckit-plan` | Pending | Pending |
| Checklist | `$speckit-checklist` | Pending | Pending |
| Tasks | `$speckit-tasks` | Pending | Pending |
| Analyze | `$speckit-analyze` | Pending | Pending |
| Confidence Gate | G6.5 | Pending | Run the pre-implementation confidence gate after Analyze and before task execution |
| Implement | `$speckit-implement` | Pending | Pending |
| Post | Autopilot post-implementation items | Pending | Pending |

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|---|---|---|
| G1 | After Specify | Pending |
| G2 | After Clarify | Pending |
| G3 | After Plan | Pending |
| G4 | After Checklist | Pending |
| G5 | After Tasks | Pending |
| G6 | After Analyze | Pending |
| G6.5 | After Analyze Consensus | Pre-implementation confidence gate records pass, advisory no-data, or advisory fail disposition before implementation begins |
| G7 | After Implementation | Pending |

## Phase 1: Specify

## Phase 2: Clarify

## Phase 3: Plan

## Phase 4: Domain Checklists

## Phase 5: Tasks

## Phase 6: Analyze

## Phase 6.5: Confidence Gate

### Confidence Gate Command

```text
python3 speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py --workflow docs/ai/specs/.process/SPEC-workflow.md --state docs/ai/specs/.process/autopilot-state.json
```

## Phase 7: Implement

## Post-Implementation Checklist

| Item | Status | Evidence |
|---|---|---|
| Post: Doctor Extension Check | Pending | Pending |
| Post: Verify Implementation | Pending | Pending |
| Post: Verify Tasks Phantom Check | Pending | Pending |
| Post: Code Review | Pending | Pending |
| Post: Integration Suite | Pending | Pending |
| Post: Reviewability Diff Gate | Pending | Pending |
| Post: UAT Runbook Generation | Pending | Pending |
| Post: PR Body Generation | Pending | Pending |
| Post: PR Creation | Pending | Pending |
| Post: Review Remediation | Pending | Pending |
| Post: Retrospective | Pending | Pending |
