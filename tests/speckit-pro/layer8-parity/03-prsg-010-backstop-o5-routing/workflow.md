# SPEC-PARITY-03 Workflow - PRSG-010 Backstop, O5, And Routing

## Overview

Synthetic workflow used by Layer 8 parity fixture 03. The fixture records the
operator-facing PRSG-010 behavior that must stay equivalent across Claude Code
and Codex surfaces.

| Field | Value |
|-------|-------|
| Spec Directory | specs/parity-03-prsg-010-backstop-o5-routing |
| Branch | parity-03-prsg-010-backstop-o5-routing |
| Status | Static guidance parity input |

## Workflow Overview

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Specify | Complete | synthetic fixture |
| Phase 2: Clarify | Complete | no clarifications |
| Phase 3: Plan | Complete | static guidance only |
| Phase 4: Checklist | Complete | no gaps |
| Phase 5: Tasks | Complete | no implementation tasks |
| Phase 6: Analyze | Complete | no findings |
| Phase 7: Implement | Complete | no code changes |

## Final Backstop Contract

| Surface | Stop Boundary | State | Packet |
|---------|---------------|-------|--------|
| Claude autopilot | before PR body, `gh pr create`, or `multi-pr-emission.sh` | `final_reviewability_gate.status=block` and `pr_created=false` | JSON re-slicing packet with PRSG-007/008/009 operator steps |
| Codex autopilot | before PR body, `gh pr create`, or `multi-pr-emission.sh` | `final_reviewability_gate.status=block` and `pr_created=false` | JSON re-slicing packet with PRSG-007/008/009 operator steps |

## Exception Education Contract

| Surface | Accepted Classes | Rejected Provenance |
|---------|------------------|---------------------|
| Claude templates | `refactor`, `infra`, `upgrade` | generated zones, templates, `.process`, PR bodies, code fences |
| Codex templates | `refactor`, `infra`, `upgrade` | generated zones, templates, `.process`, PR bodies, code fences |

## O5 Contract

| Surface | Default Path | O5 Shape | Rollup |
|---------|--------------|----------|--------|
| Claude scaffold/status | PRSG-007/008/009 split planning first | parent manifest plus flat sibling child specs | topology-first `o5-topology.sh` rollup |
| Codex scaffold/status | PRSG-007/008/009 split planning first | parent manifest plus flat sibling child specs | topology-first `o5-topology.sh` rollup |

## Contextual Routing Contract

| Evidence | Signal Or Hint | Route Effect |
|----------|----------------|--------------|
| high-confidence flag guard | `context:flag-system:guarded-cutover` | one-navigable unless additive split is proven |
| high-confidence release-held cutover | `context:release-cadence:release-held-cutover` | single-atomic without automatic releasable false |
| all in-tree consumers with coexistence | `context:consumer-locality:all-in-tree`, `strategy:branch-by-abstraction` | branch-by-abstraction |
| weak or conflicting context | `hint:flag-system:weak`, `hint:release-cadence:weak`, `hint:consumer-locality:weak`, `hint:contextual-probe:conflict` | conservative existing route |
