# The canary checks plan quality and reports the plan-stage target

Status: accepted (amends ADR 0016)

Decision ticket: [Quality floor: how the canary proves faster planning kept plan quality](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1159), part of [Wayfinder: speckit-pro planning performance](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1144).

The planning speed-ups (ADRs 0018 to 0022) remove most consensus, move executors to faster models, trim clarify and run checklist domains in parallel. Each could quietly cost a catch, and the five canary variants (ADR 0016) prove only that the promise held. So every canary receipt now also carries plan-quality assertions, which gate like the others:

- **Artifact checks.** Every functional requirement traces to at least one task. At the end of planning there are zero `[Gap]` markers, zero open analyze findings and zero `[NEEDS CLARIFICATION]` markers, or each remaining one is blocked-for-UAT through the retry ladder and listed. The receipt also records decisions-list counts, including low-confidence items and consensus rounds by kind.
- **Planted catches.** The base SPEC carries a small set of known traps, modelled on what planning really caught on the fixture: for example, a test method that would pass wrongly, or a done-gate that fails on parallel red tests. The receipt asserts the plan fixed each one. Adding them is a reviewed fixture PR with a new tag, which re-baselines the budget (ADR 0016).

- **Hooks fire once.** The base fixture registers one mandatory and one optional Spec Kit extension hook, each appending to a counter. The receipt asserts each fired exactly once per phase ([Hook double dispatch](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1175)).

The plan-stage target (at most 30 minutes and 15M tokens per host on the base variant) is reported, not gated. The validator owns the limits and computes `target_met` from the measured plan-stage time and tokens; a receipt carries neither the limits nor a claimed result. On Codex, the token total is the sum of the root thread and child agents' rollouts, and the target reads that sum, never the stage's claimed total. The target counts as met after three consecutive green base-variant runs per host under it. A reviewed PR then sets the plan-stage budget no higher than the target, so planning cannot drift back above it.

## Considered Options

- **Artifact checks only.** Rejected: a plan could pass them while missing a trap a phase used to catch.
- **Planted catches only.** Rejected: they miss structural regressions such as an untraced requirement.
- **A variant per planning path.** Not needed: ADR 0021 keeps one path.
- **Gate the target from the start.** Rejected: every canary would be red until the work lands, blocking the health releases that deliver it.
- **Report the target forever.** Rejected: nothing would stop drift once it is met.

## Consequences

- The receipt schema and validator in `tests/speckit-pro/layer6-integration/` gain the quality assertions, the target fields and Codex child-token sums.
- The planted traps must stay unknown to the plugin. Prompts and references never describe them; only the fixture and the validator know them.
- A missed planted catch is a canary failure like any other, and gets a reproducer test (ADR 0016).
