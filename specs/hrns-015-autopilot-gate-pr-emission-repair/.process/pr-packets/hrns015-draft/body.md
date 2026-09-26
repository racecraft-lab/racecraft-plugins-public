# chore(speckit-pro): Plan autopilot gate and PR emission repair

## Artifacts

- [Specification](https://github.com/racecraft-lab/racecraft-plugins-public/blob/hrns-015-autopilot-gate-pr-emission-repair/specs/hrns-015-autopilot-gate-pr-emission-repair/spec.md) · [Plan](https://github.com/racecraft-lab/racecraft-plugins-public/blob/hrns-015-autopilot-gate-pr-emission-repair/specs/hrns-015-autopilot-gate-pr-emission-repair/plan.md) · [33 tasks](https://github.com/racecraft-lab/racecraft-plugins-public/blob/hrns-015-autopilot-gate-pr-emission-repair/specs/hrns-015-autopilot-gate-pr-emission-repair/tasks.md)
- [Implementation Plan](https://github.com/racecraft-lab/racecraft-plugins-public/blob/hrns-015-autopilot-gate-pr-emission-repair/specs/hrns-015-autopilot-gate-pr-emission-repair/artifacts/implementation-plan.html)
- [Spec Explainer](https://github.com/racecraft-lab/racecraft-plugins-public/blob/hrns-015-autopilot-gate-pr-emission-repair/specs/hrns-015-autopilot-gate-pr-emission-repair/artifacts/spec-explainer.html)
- [Code Approaches](https://github.com/racecraft-lab/racecraft-plugins-public/blob/hrns-015-autopilot-gate-pr-emission-repair/specs/hrns-015-autopilot-gate-pr-emission-repair/artifacts/code-approaches.html)
- [Module Map](https://github.com/racecraft-lab/racecraft-plugins-public/blob/hrns-015-autopilot-gate-pr-emission-repair/specs/hrns-015-autopilot-gate-pr-emission-repair/artifacts/module-map.html)
- Architecture viewer: generation gap; the selected planned entry has no shipped template.

Preview is unverified; the [workflow](https://github.com/racecraft-lab/racecraft-plugins-public/blob/hrns-015-autopilot-gate-pr-emission-repair/docs/ai/specs/.process/HRNS-015-workflow.md) records isolated observation outcomes.

## Resume

Stage: plan. The plan-only review handoff is complete.

The 19-increment allocation is proposed; owner acceptance remains pending after the previously ratified five-PR direction. T002 blocks behavior tasks until actual per-PR diffs, generated outputs, reviewable LOC, and marker fingerprints qualify. H3–H7 remain open.

G6 implementation qualification is unqualified; the installed helper falsely passed ([issue #682](https://github.com/racecraft-lab/racecraft-plugins-public/issues/682)). G6.5 returned an advisory warning: 0.43 versus 0.90, from mean 0.93 minus five open HIGH deductions. Exact autonomy validation passed privately; public replay is limited by the privacy contract conflict ([issue #683](https://github.com/racecraft-lab/racecraft-plugins-public/issues/683)).

Resume after owner review and qualification with: `$speckit-autopilot docs/ai/specs/.process/HRNS-015-workflow.md --stage implement`
